"""
Sales module with step-by-step chatbot for sales entry, GST calculation, invoice generation, and Tally posting
Provides interactive sales entry workflow with GST computation and Tally integration
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

from database.db import db
from tally.voucher import tally_voucher
from tally.ledger import tally_ledger
from invoice.generator import invoice_generator
from utils.constants import HSN_CODES, GST_RATE_SLABS, STATE_CODES
from utils.helpers import (
    format_indian_currency, 
    calculate_gst, 
    validate_gstin, 
    is_same_state,
    get_financial_year,
    format_date_indian,
    parse_date
)
import config


class SalesModule:
    """Manager for sales operations with chatbot-style interaction"""
    
    def __init__(self):
        """Initialize sales module"""
        self.db = db
    
    def create_sales_entry(self, customer_name: str, customer_gstin: str,
                          customer_address: str, items: List[Dict],
                          invoice_date: Optional[str] = None,
                          generate_pdf: bool = True,
                          post_to_tally: bool = True) -> Dict:
        """
        Create complete sales entry with GST calculation, invoice generation, and Tally posting
        
        Args:
            customer_name: Customer name
            customer_gstin: Customer GSTIN (optional)
            customer_address: Customer address
            items: List of items with keys: name, hsn, quantity, unit, rate, gst_rate
            invoice_date: Invoice date (DD-MM-YYYY format, default: today)
            generate_pdf: Generate PDF invoice
            post_to_tally: Post to Tally
            
        Returns:
            Dict with invoice details and status
        """
        try:
            # Parse and validate date
            if invoice_date:
                date_obj = parse_date(invoice_date)
                if not date_obj:
                    return {"error": "Invalid date format"}
                invoice_date_str = format_date_indian(date_obj)
                tally_date = date_obj.strftime("%Y%m%d")
            else:
                date_obj = datetime.now()
                invoice_date_str = format_date_indian(date_obj)
                tally_date = date_obj.strftime("%Y%m%d")
            
            # Validate GSTIN if provided
            if customer_gstin and not validate_gstin(customer_gstin):
                return {"error": "Invalid GSTIN format"}
            
            # Generate invoice number
            fy = get_financial_year(date_obj)
            invoice_no = self.db.get_next_invoice_number(config.INVOICE_PREFIX, fy)
            
            # Calculate totals and GST
            company_gstin = config.COMPANY_INFO.get("gstin", "")
            is_intra_state = is_same_state(company_gstin, customer_gstin) if customer_gstin else True
            
            subtotal = 0
            total_cgst = 0
            total_sgst = 0
            total_igst = 0
            processed_items = []
            
            for item in items:
                item_amount = item['quantity'] * item['rate']
                subtotal += item_amount
                
                # Calculate GST for this item
                gst_calc = calculate_gst(item_amount, item.get('gst_rate', 18), is_intra_state)
                
                total_cgst += gst_calc['cgst']
                total_sgst += gst_calc['sgst']
                total_igst += gst_calc['igst']
                
                processed_items.append({
                    "name": item['name'],
                    "hsn": item.get('hsn', ''),
                    "quantity": item['quantity'],
                    "unit": item.get('unit', 'Pcs'),
                    "rate": item['rate'],
                    "amount": item_amount,
                    "gst_rate": item.get('gst_rate', 18)
                })
            
            total_amount = subtotal + total_cgst + total_sgst + total_igst
            
            # Save to database
            sale_id = self.db.insert_sale(
                invoice_no=invoice_no,
                customer_name=customer_name,
                customer_gstin=customer_gstin or "",
                items=processed_items,
                subtotal=subtotal,
                cgst=total_cgst,
                sgst=total_sgst,
                igst=total_igst,
                total=total_amount,
                date=invoice_date_str
            )
            
            result = {
                "success": True,
                "invoice_no": invoice_no,
                "invoice_date": invoice_date_str,
                "customer_name": customer_name,
                "subtotal": subtotal,
                "cgst": total_cgst,
                "sgst": total_sgst,
                "igst": total_igst,
                "total": total_amount,
                "sale_id": sale_id
            }
            
            # Generate PDF invoice
            if generate_pdf:
                try:
                    invoice_data = {
                        "invoice_no": invoice_no,
                        "invoice_date": invoice_date_str,
                        "customer_name": customer_name,
                        "customer_address": customer_address,
                        "customer_gstin": customer_gstin or "",
                        "items": processed_items,
                        "subtotal": subtotal,
                        "cgst": total_cgst,
                        "sgst": total_sgst,
                        "igst": total_igst,
                        "total": total_amount
                    }
                    pdf_path = invoice_generator.generate_invoice(invoice_data)
                    result["pdf_path"] = pdf_path
                except Exception as e:
                    result["pdf_error"] = f"Failed to generate PDF: {str(e)}"
            
            # Post to Tally (only if enabled and requested)
            if post_to_tally and config.TALLY_ENABLED:
                try:
                    success = self._post_to_tally(
                        date=tally_date,
                        party=customer_name,
                        invoice_no=invoice_no,
                        items=processed_items,
                        subtotal=subtotal,
                        cgst=total_cgst,
                        sgst=total_sgst,
                        igst=total_igst,
                        total=total_amount
                    )
                    result["tally_posted"] = success
                    if success:
                        self.db.cursor.execute(
                            "UPDATE sales SET tally_synced = 1 WHERE id = ?",
                            (sale_id,)
                        )
                        self.db.connection.commit()
                except Exception as e:
                    result["tally_error"] = f"Failed to post to Tally: {str(e)}"
                    # Continue anyway - data is saved in SQLite
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to create sales entry: {str(e)}"}
    
    def _post_to_tally(self, date: str, party: str, invoice_no: str,
                      items: List[Dict], subtotal: float, cgst: float,
                      sgst: float, igst: float, total: float) -> bool:
        """
        Post sales voucher to Tally
        
        Args:
            date: Date in YYYYMMDD format
            party: Party name
            invoice_no: Invoice number
            items: List of items
            subtotal: Subtotal amount
            cgst: CGST amount
            sgst: SGST amount
            igst: IGST amount
            total: Total amount
            
        Returns:
            True if successful
        """
        # Prepare ledger entries
        ledger_entries = []
        
        # Sales ledger (Credit)
        ledger_entries.append({
            "ledger": "Sales",
            "amount": subtotal,
            "is_debit": False
        })
        
        # GST ledgers (Credit)
        if cgst > 0:
            ledger_entries.append({
                "ledger": "Output CGST",
                "amount": cgst,
                "is_debit": False
            })
        
        if sgst > 0:
            ledger_entries.append({
                "ledger": "Output SGST",
                "amount": sgst,
                "is_debit": False
            })
        
        if igst > 0:
            ledger_entries.append({
                "ledger": "Output IGST",
                "amount": igst,
                "is_debit": False
            })
        
        # Create required ledgers if they don't exist
        for entry in ledger_entries:
            if not tally_ledger.ledger_exists(entry['ledger']):
                if "CGST" in entry['ledger'] or "SGST" in entry['ledger'] or "IGST" in entry['ledger']:
                    tally_ledger.create_ledger(entry['ledger'], "Duties & Taxes")
                else:
                    tally_ledger.create_ledger(entry['ledger'], "Sales Accounts")
        
        # Create sales voucher
        narration = f"Sales Invoice {invoice_no}"
        return tally_voucher.create_sales_voucher(
            date=date,
            party=party,
            ledger_entries=ledger_entries,
            narration=narration,
            invoice_no=invoice_no
        )
    
    def get_sales_list(self, limit: int = 50) -> List[Dict]:
        """
        Get list of sales entries
        
        Args:
            limit: Number of records to fetch
            
        Returns:
            List of sales records
        """
        return self.db.get_sales(limit=limit)
    
    def get_sales_summary(self, from_date: Optional[str] = None,
                         to_date: Optional[str] = None) -> Dict:
        """
        Get sales summary for a period
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            
        Returns:
            Dict with sales summary
        """
        try:
            query = "SELECT * FROM sales WHERE 1=1"
            params = []
            
            if from_date:
                query += " AND date >= ?"
                params.append(from_date)
            
            if to_date:
                query += " AND date <= ?"
                params.append(to_date)
            
            self.db.cursor.execute(query, params)
            sales = [dict(row) for row in self.db.cursor.fetchall()]
            
            total_sales = sum(s['total'] for s in sales)
            total_cgst = sum(s['cgst'] for s in sales)
            total_sgst = sum(s['sgst'] for s in sales)
            total_igst = sum(s['igst'] for s in sales)
            count = len(sales)
            
            return {
                "count": count,
                "total_sales": total_sales,
                "total_cgst": total_cgst,
                "total_sgst": total_sgst,
                "total_igst": total_igst,
                "total_gst": total_cgst + total_sgst + total_igst,
                "average_sale": total_sales / count if count > 0 else 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def search_sales(self, customer_name: Optional[str] = None,
                    invoice_no: Optional[str] = None) -> List[Dict]:
        """
        Search sales records
        
        Args:
            customer_name: Customer name to search
            invoice_no: Invoice number to search
            
        Returns:
            List of matching sales records
        """
        try:
            query = "SELECT * FROM sales WHERE 1=1"
            params = []
            
            if customer_name:
                query += " AND customer_name LIKE ?"
                params.append(f"%{customer_name}%")
            
            if invoice_no:
                query += " AND invoice_no LIKE ?"
                params.append(f"%{invoice_no}%")
            
            query += " ORDER BY date DESC"
            
            self.db.cursor.execute(query, params)
            return [dict(row) for row in self.db.cursor.fetchall()]
        except Exception as e:
            return []
    
    def get_hsn_suggestions(self, search_term: str) -> List[Dict]:
        """
        Get HSN code suggestions based on search term
        
        Args:
            search_term: Search term
            
        Returns:
            List of matching HSN codes with descriptions
        """
        results = []
        search_lower = search_term.lower()
        
        for hsn, details in HSN_CODES.items():
            if (search_lower in hsn.lower() or 
                search_lower in details['description'].lower()):
                results.append({
                    "hsn": hsn,
                    "description": details['description'],
                    "rate": details['rate']
                })
        
        return results[:10]  # Limit to 10 results
    
    def validate_sale_data(self, customer_name: str, items: List[Dict]) -> Tuple[bool, str]:
        """
        Validate sales entry data
        
        Args:
            customer_name: Customer name
            items: List of items
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not customer_name or len(customer_name.strip()) < 2:
            return False, "Customer name is required"
        
        if not items or len(items) == 0:
            return False, "At least one item is required"
        
        for i, item in enumerate(items):
            if not item.get('name'):
                return False, f"Item {i+1}: Name is required"
            
            if not item.get('quantity') or item['quantity'] <= 0:
                return False, f"Item {i+1}: Quantity must be greater than 0"
            
            if not item.get('rate') or item['rate'] <= 0:
                return False, f"Item {i+1}: Rate must be greater than 0"
            
            gst_rate = item.get('gst_rate', 18)
            if gst_rate not in GST_RATE_SLABS:
                return False, f"Item {i+1}: Invalid GST rate. Must be one of {GST_RATE_SLABS}"
        
        return True, ""


# Global instance
sales_module = SalesModule()
