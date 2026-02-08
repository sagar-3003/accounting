"""
Purchase module for invoice scanning, OCR extraction, Tally posting
Handles purchase invoice processing with OCR capabilities
"""

from datetime import datetime
from typing import Dict, List, Optional
import json

from database.db import db
from tally.voucher import tally_voucher
from tally.ledger import tally_ledger
from invoice.scanner import invoice_scanner
from utils.constants import HSN_CODES, GST_RATE_SLABS
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


class PurchaseModule:
    """Manager for purchase operations with OCR scanning"""
    
    def __init__(self):
        """Initialize purchase module"""
        self.db = db
        self.scanner = invoice_scanner
    
    def scan_invoice(self, file_path: str) -> Dict:
        """
        Scan and extract data from purchase invoice
        
        Args:
            file_path: Path to invoice file (PDF or image)
            
        Returns:
            Dict with extracted invoice data
        """
        try:
            extracted_data = self.scanner.scan_file(file_path)
            
            if "error" in extracted_data:
                return extracted_data
            
            # Format the data for display
            result = {
                "success": True,
                "vendor_name": extracted_data.get("vendor_name", ""),
                "invoice_no": extracted_data.get("invoice_no", ""),
                "invoice_date": extracted_data.get("invoice_date", ""),
                "gstin": extracted_data.get("gstin", ""),
                "total_amount": extracted_data.get("total_amount", 0),
                "items": extracted_data.get("items", []),
                "raw_text": extracted_data.get("raw_text", "")
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to scan invoice: {str(e)}"}
    
    def create_purchase_entry(self, vendor_name: str, vendor_gstin: str,
                             invoice_no: str, items: List[Dict],
                             invoice_date: Optional[str] = None,
                             post_to_tally: bool = True) -> Dict:
        """
        Create purchase entry with GST calculation and Tally posting
        
        Args:
            vendor_name: Vendor/supplier name
            vendor_gstin: Vendor GSTIN
            invoice_no: Invoice/bill number from vendor
            items: List of items with keys: name, hsn, quantity, unit, rate, gst_rate
            invoice_date: Invoice date (DD-MM-YYYY format, default: today)
            post_to_tally: Post to Tally
            
        Returns:
            Dict with purchase details and status
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
            if vendor_gstin and not validate_gstin(vendor_gstin):
                return {"error": "Invalid GSTIN format"}
            
            # Calculate totals and GST
            company_gstin = config.COMPANY_INFO.get("gstin", "")
            is_intra_state = is_same_state(company_gstin, vendor_gstin) if vendor_gstin else True
            
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
            purchase_id = self.db.insert_purchase(
                invoice_no=invoice_no,
                vendor_name=vendor_name,
                vendor_gstin=vendor_gstin or "",
                items=processed_items,
                subtotal=subtotal,
                cgst=total_cgst,
                sgst=total_sgst,
                igst=total_igst,
                total=total_amount,
                date=invoice_date_str
            )
            
            # Also add to creditors
            try:
                from datetime import timedelta
                due_date = (date_obj + timedelta(days=30)).strftime("%d-%m-%Y")
                self.db.insert_creditor(
                    vendor_name=vendor_name,
                    invoice_no=invoice_no,
                    amount=total_amount,
                    due_date=due_date
                )
            except Exception:
                pass  # Non-critical
            
            result = {
                "success": True,
                "invoice_no": invoice_no,
                "invoice_date": invoice_date_str,
                "vendor_name": vendor_name,
                "subtotal": subtotal,
                "cgst": total_cgst,
                "sgst": total_sgst,
                "igst": total_igst,
                "total": total_amount,
                "purchase_id": purchase_id
            }
            
            # Post to Tally (only if enabled and requested)
            if post_to_tally and config.TALLY_ENABLED:
                try:
                    success = self._post_to_tally(
                        date=tally_date,
                        party=vendor_name,
                        ref_no=invoice_no,
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
                            "UPDATE purchases SET tally_synced = 1 WHERE id = ?",
                            (purchase_id,)
                        )
                        self.db.connection.commit()
                except Exception as e:
                    result["tally_error"] = f"Failed to post to Tally: {str(e)}"
                    # Continue anyway - data is saved in SQLite
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to create purchase entry: {str(e)}"}
    
    def _post_to_tally(self, date: str, party: str, ref_no: str,
                      items: List[Dict], subtotal: float, cgst: float,
                      sgst: float, igst: float, total: float) -> bool:
        """
        Post purchase voucher to Tally
        
        Args:
            date: Date in YYYYMMDD format
            party: Party name
            ref_no: Reference/invoice number
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
        
        # Purchase ledger (Debit)
        ledger_entries.append({
            "ledger": "Purchase",
            "amount": subtotal,
            "is_debit": True
        })
        
        # GST Input ledgers (Debit)
        if cgst > 0:
            ledger_entries.append({
                "ledger": "Input CGST",
                "amount": cgst,
                "is_debit": True
            })
        
        if sgst > 0:
            ledger_entries.append({
                "ledger": "Input SGST",
                "amount": sgst,
                "is_debit": True
            })
        
        if igst > 0:
            ledger_entries.append({
                "ledger": "Input IGST",
                "amount": igst,
                "is_debit": True
            })
        
        # Create required ledgers if they don't exist
        for entry in ledger_entries:
            if not tally_ledger.ledger_exists(entry['ledger']):
                if "CGST" in entry['ledger'] or "SGST" in entry['ledger'] or "IGST" in entry['ledger']:
                    tally_ledger.create_ledger(entry['ledger'], "Duties & Taxes")
                else:
                    tally_ledger.create_ledger(entry['ledger'], "Purchase Accounts")
        
        # Create purchase voucher
        narration = f"Purchase as per Invoice {ref_no}"
        return tally_voucher.create_purchase_voucher(
            date=date,
            party=party,
            ledger_entries=ledger_entries,
            narration=narration,
            ref_no=ref_no
        )
    
    def get_purchase_list(self, limit: int = 50) -> List[Dict]:
        """
        Get list of purchase entries
        
        Args:
            limit: Number of records to fetch
            
        Returns:
            List of purchase records
        """
        return self.db.get_purchases(limit=limit)
    
    def get_purchase_summary(self, from_date: Optional[str] = None,
                            to_date: Optional[str] = None) -> Dict:
        """
        Get purchase summary for a period
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            
        Returns:
            Dict with purchase summary
        """
        try:
            query = "SELECT * FROM purchases WHERE 1=1"
            params = []
            
            if from_date:
                query += " AND date >= ?"
                params.append(from_date)
            
            if to_date:
                query += " AND date <= ?"
                params.append(to_date)
            
            self.db.cursor.execute(query, params)
            purchases = [dict(row) for row in self.db.cursor.fetchall()]
            
            total_purchases = sum(p['total'] for p in purchases)
            total_cgst = sum(p['cgst'] for p in purchases)
            total_sgst = sum(p['sgst'] for p in purchases)
            total_igst = sum(p['igst'] for p in purchases)
            count = len(purchases)
            
            return {
                "count": count,
                "total_purchases": total_purchases,
                "total_cgst": total_cgst,
                "total_sgst": total_sgst,
                "total_igst": total_igst,
                "total_gst": total_cgst + total_sgst + total_igst,
                "average_purchase": total_purchases / count if count > 0 else 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def search_purchases(self, vendor_name: Optional[str] = None,
                        invoice_no: Optional[str] = None) -> List[Dict]:
        """
        Search purchase records
        
        Args:
            vendor_name: Vendor name to search
            invoice_no: Invoice number to search
            
        Returns:
            List of matching purchase records
        """
        try:
            query = "SELECT * FROM purchases WHERE 1=1"
            params = []
            
            if vendor_name:
                query += " AND vendor_name LIKE ?"
                params.append(f"%{vendor_name}%")
            
            if invoice_no:
                query += " AND invoice_no LIKE ?"
                params.append(f"%{invoice_no}%")
            
            query += " ORDER BY date DESC"
            
            self.db.cursor.execute(query, params)
            return [dict(row) for row in self.db.cursor.fetchall()]
        except Exception as e:
            return []
    
    def create_from_scanned_data(self, scanned_data: Dict,
                                 post_to_tally: bool = True) -> Dict:
        """
        Create purchase entry from scanned invoice data
        
        Args:
            scanned_data: Data extracted from OCR
            post_to_tally: Post to Tally
            
        Returns:
            Dict with purchase details and status
        """
        try:
            vendor_name = scanned_data.get("vendor_name", "Unknown Vendor")
            invoice_no = scanned_data.get("invoice_no", "")
            invoice_date = scanned_data.get("invoice_date", "")
            vendor_gstin = scanned_data.get("gstin", "")
            items = scanned_data.get("items", [])
            
            # If items are empty, create a single item with total amount
            if not items:
                total_amount = scanned_data.get("total_amount", 0)
                if total_amount > 0:
                    # Reverse calculate subtotal (assuming 18% GST)
                    subtotal = total_amount / 1.18
                    items = [{
                        "name": "Purchase as per invoice",
                        "quantity": 1,
                        "rate": subtotal,
                        "unit": "Pcs",
                        "gst_rate": 18
                    }]
            
            if not items:
                return {"error": "No items found in scanned invoice"}
            
            return self.create_purchase_entry(
                vendor_name=vendor_name,
                vendor_gstin=vendor_gstin,
                invoice_no=invoice_no,
                items=items,
                invoice_date=invoice_date if invoice_date else None,
                post_to_tally=post_to_tally
            )
            
        except Exception as e:
            return {"error": f"Failed to create purchase from scanned data: {str(e)}"}


# Global instance
purchase_module = PurchaseModule()
