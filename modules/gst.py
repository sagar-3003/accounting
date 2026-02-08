"""
GST (Goods and Services Tax) computation module
GST calculation, GSTR-1, GSTR-3B helpers
"""

from datetime import datetime
from typing import Dict, List, Optional
import json
from collections import defaultdict

from database.db import db
from utils.constants import GST_RATE_SLABS, HSN_CODES, STATE_CODES
from utils.helpers import (
    format_indian_currency,
    format_date_indian,
    parse_date,
    validate_gstin,
    extract_state_from_gstin,
    is_same_state,
    get_month_name
)
import config


class GSTModule:
    """Manager for GST computation and reporting"""
    
    def __init__(self):
        """Initialize GST module"""
        self.db = db
    
    def calculate_gst(self, taxable_value: float, gst_rate: float,
                     supplier_gstin: str, recipient_gstin: str) -> Dict:
        """
        Calculate GST breakdown
        
        Args:
            taxable_value: Taxable amount
            gst_rate: GST rate percentage
            supplier_gstin: Supplier GSTIN
            recipient_gstin: Recipient GSTIN
            
        Returns:
            Dict with GST breakdown
        """
        try:
            if gst_rate not in GST_RATE_SLABS:
                return {"error": f"Invalid GST rate. Must be one of: {GST_RATE_SLABS}"}
            
            # Check if intra-state or inter-state
            is_intra = is_same_state(supplier_gstin, recipient_gstin)
            
            gst_amount = (taxable_value * gst_rate) / 100
            
            if is_intra:
                # CGST + SGST
                cgst = gst_amount / 2
                sgst = gst_amount / 2
                igst = 0
                gst_type = "Intra-State (CGST + SGST)"
            else:
                # IGST
                cgst = 0
                sgst = 0
                igst = gst_amount
                gst_type = "Inter-State (IGST)"
            
            return {
                "success": True,
                "taxable_value": taxable_value,
                "gst_rate": gst_rate,
                "gst_type": gst_type,
                "cgst": round(cgst, 2),
                "sgst": round(sgst, 2),
                "igst": round(igst, 2),
                "total_gst": round(gst_amount, 2),
                "total_amount": round(taxable_value + gst_amount, 2)
            }
        except Exception as e:
            return {"error": f"Failed to calculate GST: {str(e)}"}
    
    def get_gstr1_data(self, month: int, year: int) -> Dict:
        """
        Generate GSTR-1 data (Outward supplies)
        
        Args:
            month: Month (1-12)
            year: Year (e.g., 2025)
            
        Returns:
            Dict with GSTR-1 data
        """
        try:
            # Get date range for the month
            from_date = f"01-{month:02d}-{year}"
            if month == 12:
                to_date = f"31-{month:02d}-{year}"
            else:
                # Get last day of month
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                to_date = f"{last_day:02d}-{month:02d}-{year}"
            
            # Get all sales for the month
            query = "SELECT * FROM sales WHERE date >= ? AND date <= ?"
            self.db.cursor.execute(query, (from_date, to_date))
            sales = [dict(row) for row in self.db.cursor.fetchall()]
            
            # Categorize sales
            b2b = []  # B2B (Business to Business) - with GSTIN
            b2c_large = []  # B2C Large (invoice value > 2.5 lakhs)
            b2c_small = []  # B2C Small (invoice value <= 2.5 lakhs)
            
            total_taxable = 0
            total_cgst = 0
            total_sgst = 0
            total_igst = 0
            
            for sale in sales:
                items = json.loads(sale['items_json'])
                
                sale_data = {
                    "invoice_no": sale['invoice_no'],
                    "invoice_date": sale['date'],
                    "customer_name": sale['customer_name'],
                    "customer_gstin": sale['customer_gstin'],
                    "taxable_value": sale['subtotal'],
                    "cgst": sale['cgst'],
                    "sgst": sale['sgst'],
                    "igst": sale['igst'],
                    "total": sale['total'],
                    "items": items
                }
                
                total_taxable += sale['subtotal']
                total_cgst += sale['cgst']
                total_sgst += sale['sgst']
                total_igst += sale['igst']
                
                # Categorize
                if sale['customer_gstin'] and len(sale['customer_gstin']) == 15:
                    # B2B
                    b2b.append(sale_data)
                elif sale['total'] > 250000:
                    # B2C Large
                    b2c_large.append(sale_data)
                else:
                    # B2C Small
                    b2c_small.append(sale_data)
            
            # Summarize by HSN
            hsn_summary = self._get_hsn_summary(sales)
            
            return {
                "success": True,
                "month": get_month_name(month),
                "year": year,
                "b2b": {
                    "invoices": b2b,
                    "count": len(b2b)
                },
                "b2c_large": {
                    "invoices": b2c_large,
                    "count": len(b2c_large)
                },
                "b2c_small": {
                    "invoices": b2c_small,
                    "count": len(b2c_small)
                },
                "hsn_summary": hsn_summary,
                "totals": {
                    "invoice_count": len(sales),
                    "taxable_value": total_taxable,
                    "cgst": total_cgst,
                    "sgst": total_sgst,
                    "igst": total_igst,
                    "total_gst": total_cgst + total_sgst + total_igst,
                    "total_value": total_taxable + total_cgst + total_sgst + total_igst
                }
            }
        except Exception as e:
            return {"error": f"Failed to generate GSTR-1: {str(e)}"}
    
    def get_gstr3b_data(self, month: int, year: int) -> Dict:
        """
        Generate GSTR-3B data (Summary return)
        
        Args:
            month: Month (1-12)
            year: Year (e.g., 2025)
            
        Returns:
            Dict with GSTR-3B data
        """
        try:
            # Get date range for the month
            from_date = f"01-{month:02d}-{year}"
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            to_date = f"{last_day:02d}-{month:02d}-{year}"
            
            # Get outward supplies (sales)
            self.db.cursor.execute(
                "SELECT * FROM sales WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            sales = [dict(row) for row in self.db.cursor.fetchall()]
            
            # Get inward supplies (purchases)
            self.db.cursor.execute(
                "SELECT * FROM purchases WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            purchases = [dict(row) for row in self.db.cursor.fetchall()]
            
            # Calculate outward supplies
            outward_taxable = sum(s['subtotal'] for s in sales)
            outward_cgst = sum(s['cgst'] for s in sales)
            outward_sgst = sum(s['sgst'] for s in sales)
            outward_igst = sum(s['igst'] for s in sales)
            
            # Calculate inward supplies (ITC - Input Tax Credit)
            itc_cgst = sum(p['cgst'] for p in purchases)
            itc_sgst = sum(p['sgst'] for p in purchases)
            itc_igst = sum(p['igst'] for p in purchases)
            
            # Calculate net tax liability
            net_cgst = outward_cgst - itc_cgst
            net_sgst = outward_sgst - itc_sgst
            net_igst = outward_igst - itc_igst
            
            # Interest and late fee (if any)
            interest = 0
            late_fee = 0
            
            # Total tax payable
            total_tax_payable = net_cgst + net_sgst + net_igst + interest + late_fee
            
            return {
                "success": True,
                "month": get_month_name(month),
                "year": year,
                "outward_supplies": {
                    "taxable_value": outward_taxable,
                    "cgst": outward_cgst,
                    "sgst": outward_sgst,
                    "igst": outward_igst,
                    "total_tax": outward_cgst + outward_sgst + outward_igst
                },
                "input_tax_credit": {
                    "cgst": itc_cgst,
                    "sgst": itc_sgst,
                    "igst": itc_igst,
                    "total_itc": itc_cgst + itc_sgst + itc_igst
                },
                "net_tax_liability": {
                    "cgst": max(0, net_cgst),
                    "sgst": max(0, net_sgst),
                    "igst": max(0, net_igst),
                    "interest": interest,
                    "late_fee": late_fee,
                    "total_payable": max(0, total_tax_payable)
                },
                "summary": {
                    "sales_count": len(sales),
                    "purchase_count": len(purchases),
                    "total_sales": sum(s['total'] for s in sales),
                    "total_purchases": sum(p['total'] for p in purchases)
                }
            }
        except Exception as e:
            return {"error": f"Failed to generate GSTR-3B: {str(e)}"}
    
    def _get_hsn_summary(self, sales: List[Dict]) -> List[Dict]:
        """
        Generate HSN-wise summary
        
        Args:
            sales: List of sales records
            
        Returns:
            List of HSN summaries
        """
        hsn_data = defaultdict(lambda: {
            "quantity": 0,
            "taxable_value": 0,
            "cgst": 0,
            "sgst": 0,
            "igst": 0,
            "rate": 0
        })
        
        for sale in sales:
            items = json.loads(sale['items_json'])
            
            for item in items:
                hsn = item.get('hsn', 'NA')
                qty = item.get('quantity', 0)
                amount = item.get('amount', 0)
                gst_rate = item.get('gst_rate', 0)
                
                hsn_data[hsn]['quantity'] += qty
                hsn_data[hsn]['taxable_value'] += amount
                hsn_data[hsn]['rate'] = gst_rate
                
                # Proportional GST
                item_gst = (amount * gst_rate) / 100
                
                if sale['igst'] > 0:
                    hsn_data[hsn]['igst'] += item_gst
                else:
                    hsn_data[hsn]['cgst'] += item_gst / 2
                    hsn_data[hsn]['sgst'] += item_gst / 2
        
        # Convert to list
        result = []
        for hsn, data in hsn_data.items():
            result.append({
                "hsn": hsn,
                "description": HSN_CODES.get(hsn, {}).get('description', 'Unknown'),
                "quantity": data['quantity'],
                "taxable_value": round(data['taxable_value'], 2),
                "cgst": round(data['cgst'], 2),
                "sgst": round(data['sgst'], 2),
                "igst": round(data['igst'], 2),
                "rate": data['rate']
            })
        
        return result
    
    def get_gst_liability_summary(self, from_date: str, to_date: str) -> Dict:
        """
        Get GST liability summary for a period
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            
        Returns:
            Dict with GST liability
        """
        try:
            # Get sales
            self.db.cursor.execute(
                "SELECT * FROM sales WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            sales = [dict(row) for row in self.db.cursor.fetchall()]
            
            # Get purchases
            self.db.cursor.execute(
                "SELECT * FROM purchases WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            purchases = [dict(row) for row in self.db.cursor.fetchall()]
            
            # Output tax
            output_cgst = sum(s['cgst'] for s in sales)
            output_sgst = sum(s['sgst'] for s in sales)
            output_igst = sum(s['igst'] for s in sales)
            output_total = output_cgst + output_sgst + output_igst
            
            # Input tax credit
            input_cgst = sum(p['cgst'] for p in purchases)
            input_sgst = sum(p['sgst'] for p in purchases)
            input_igst = sum(p['igst'] for p in purchases)
            input_total = input_cgst + input_sgst + input_igst
            
            # Net liability
            net_cgst = max(0, output_cgst - input_cgst)
            net_sgst = max(0, output_sgst - input_sgst)
            net_igst = max(0, output_igst - input_igst)
            net_total = net_cgst + net_sgst + net_igst
            
            return {
                "success": True,
                "period": f"{from_date} to {to_date}",
                "output_tax": {
                    "cgst": output_cgst,
                    "sgst": output_sgst,
                    "igst": output_igst,
                    "total": output_total
                },
                "input_tax_credit": {
                    "cgst": input_cgst,
                    "sgst": input_sgst,
                    "igst": input_igst,
                    "total": input_total
                },
                "net_liability": {
                    "cgst": net_cgst,
                    "sgst": net_sgst,
                    "igst": net_igst,
                    "total": net_total
                }
            }
        except Exception as e:
            return {"error": f"Failed to get GST liability: {str(e)}"}
    
    def validate_gstin_details(self, gstin: str) -> Dict:
        """
        Validate and extract GSTIN details
        
        Args:
            gstin: GSTIN to validate
            
        Returns:
            Dict with GSTIN details
        """
        try:
            if not validate_gstin(gstin):
                return {"error": "Invalid GSTIN format"}
            
            state_info = extract_state_from_gstin(gstin)
            if not state_info:
                return {"error": "Invalid state code in GSTIN"}
            
            state_code, state_name = state_info
            pan = gstin[2:12]
            entity_number = gstin[12:13]
            
            return {
                "success": True,
                "gstin": gstin,
                "valid": True,
                "state_code": state_code,
                "state_name": state_name,
                "pan": pan,
                "entity_number": entity_number
            }
        except Exception as e:
            return {"error": f"Failed to validate GSTIN: {str(e)}"}
    
    def get_state_wise_sales(self, from_date: str, to_date: str) -> Dict:
        """
        Get state-wise sales summary
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            
        Returns:
            Dict with state-wise sales
        """
        try:
            # Get sales
            self.db.cursor.execute(
                "SELECT * FROM sales WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            sales = [dict(row) for row in self.db.cursor.fetchall()]
            
            state_summary = defaultdict(lambda: {
                "count": 0,
                "taxable_value": 0,
                "cgst": 0,
                "sgst": 0,
                "igst": 0,
                "total": 0
            })
            
            company_gstin = config.COMPANY_INFO.get('gstin', '')
            company_state = company_gstin[:2] if company_gstin else ''
            
            for sale in sales:
                if sale['customer_gstin']:
                    state_code = sale['customer_gstin'][:2]
                    state_name = STATE_CODES.get(state_code, "Unknown")
                else:
                    # Assume same state if no GSTIN
                    state_code = company_state
                    state_name = STATE_CODES.get(state_code, "Unknown")
                
                state_summary[state_name]['count'] += 1
                state_summary[state_name]['taxable_value'] += sale['subtotal']
                state_summary[state_name]['cgst'] += sale['cgst']
                state_summary[state_name]['sgst'] += sale['sgst']
                state_summary[state_name]['igst'] += sale['igst']
                state_summary[state_name]['total'] += sale['total']
            
            return {
                "success": True,
                "period": f"{from_date} to {to_date}",
                "state_wise": dict(state_summary)
            }
        except Exception as e:
            return {"error": f"Failed to get state-wise sales: {str(e)}"}


# Global instance
gst_module = GSTModule()
