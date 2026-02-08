"""
TDS (Tax Deducted at Source) computation module
Handles TDS calculation by section with all TDS sections from constants
"""

from datetime import datetime
from typing import Dict, List, Optional
import json

from database.db import db
from tally.voucher import tally_voucher
from tally.ledger import tally_ledger
from utils.constants import TDS_SECTIONS
from utils.helpers import (
    format_indian_currency,
    format_date_indian,
    parse_date,
    get_quarter,
    get_financial_year,
    validate_pan
)
import config


class TDSModule:
    """Manager for TDS computation and compliance"""
    
    def __init__(self):
        """Initialize TDS module"""
        self.db = db
    
    def calculate_tds(self, section: str, payment_amount: float,
                     party_type: str = "individual") -> Dict:
        """
        Calculate TDS for a payment
        
        Args:
            section: TDS section (e.g., "194C", "194J")
            payment_amount: Payment amount
            party_type: "individual" or "company"
            
        Returns:
            Dict with TDS calculation details
        """
        try:
            if section not in TDS_SECTIONS:
                return {"error": f"Invalid TDS section. Valid sections: {', '.join(TDS_SECTIONS.keys())}"}
            
            section_data = TDS_SECTIONS[section]
            
            # Get applicable rate
            if party_type.lower() == "company":
                tds_rate = section_data['rate_company']
            else:
                tds_rate = section_data['rate_individual']
            
            # Calculate TDS
            tds_amount = (payment_amount * tds_rate) / 100
            net_payable = payment_amount - tds_amount
            
            return {
                "success": True,
                "section": section,
                "description": section_data['description'],
                "payment_amount": payment_amount,
                "tds_rate": tds_rate,
                "tds_amount": round(tds_amount, 2),
                "net_payable": round(net_payable, 2),
                "threshold_single": section_data['threshold_single'],
                "threshold_aggregate": section_data['threshold_aggregate']
            }
        except Exception as e:
            return {"error": f"Failed to calculate TDS: {str(e)}"}
    
    def create_tds_entry(self, party_name: str, party_pan: str, section: str,
                        payment_amount: float, party_type: str = "individual",
                        payment_date: Optional[str] = None,
                        post_to_tally: bool = True) -> Dict:
        """
        Create TDS entry with calculation
        
        Args:
            party_name: Party name
            party_pan: Party PAN
            section: TDS section
            payment_amount: Payment amount
            party_type: "individual" or "company"
            payment_date: Payment date (DD-MM-YYYY, default: today)
            post_to_tally: Post to Tally
            
        Returns:
            Dict with TDS entry details
        """
        try:
            # Validate PAN
            if not validate_pan(party_pan):
                return {"error": "Invalid PAN format"}
            
            # Calculate TDS
            tds_calc = self.calculate_tds(section, payment_amount, party_type)
            if "error" in tds_calc:
                return tds_calc
            
            # Parse date
            if payment_date:
                date_obj = parse_date(payment_date)
                if not date_obj:
                    return {"error": "Invalid date format"}
                payment_date_str = format_date_indian(date_obj)
                tally_date = date_obj.strftime("%Y%m%d")
            else:
                date_obj = datetime.now()
                payment_date_str = format_date_indian(date_obj)
                tally_date = date_obj.strftime("%Y%m%d")
            
            # Get quarter and financial year
            quarter = get_quarter(date_obj)
            financial_year = get_financial_year(date_obj)
            
            # Save to database
            tds_id = self.db.insert_tds_entry(
                party_name=party_name,
                party_pan=party_pan,
                section=section,
                payment_amount=payment_amount,
                tds_rate=tds_calc['tds_rate'],
                tds_amount=tds_calc['tds_amount'],
                net_payable=tds_calc['net_payable'],
                date=payment_date_str,
                quarter=quarter,
                financial_year=financial_year
            )
            
            result = {
                "success": True,
                "tds_id": tds_id,
                "party_name": party_name,
                "party_pan": party_pan,
                "section": section,
                "description": tds_calc['description'],
                "payment_amount": payment_amount,
                "tds_rate": tds_calc['tds_rate'],
                "tds_amount": tds_calc['tds_amount'],
                "net_payable": tds_calc['net_payable'],
                "payment_date": payment_date_str,
                "quarter": quarter,
                "financial_year": financial_year
            }
            
            # Post to Tally (only if enabled and requested)
            if post_to_tally and config.TALLY_ENABLED:
                try:
                    success = self._post_to_tally(
                        date=tally_date,
                        party=party_name,
                        section=section,
                        payment_amount=payment_amount,
                        tds_amount=tds_calc['tds_amount'],
                        net_payable=tds_calc['net_payable']
                    )
                    result["tally_posted"] = success
                    if success:
                        self.db.cursor.execute(
                            "UPDATE tds_register SET tally_synced = 1 WHERE id = ?",
                            (tds_id,)
                        )
                        self.db.connection.commit()
                except Exception as e:
                    result["tally_error"] = f"Failed to post to Tally: {str(e)}"
                    # Continue anyway - data is saved in SQLite
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to create TDS entry: {str(e)}"}
    
    def _post_to_tally(self, date: str, party: str, section: str,
                      payment_amount: float, tds_amount: float,
                      net_payable: float) -> bool:
        """
        Post TDS entry to Tally
        
        Args:
            date: Date in YYYYMMDD format
            party: Party name
            section: TDS section
            payment_amount: Payment amount
            tds_amount: TDS amount
            net_payable: Net payable amount
            
        Returns:
            True if successful
        """
        try:
            # Ensure ledgers exist
            if not tally_ledger.ledger_exists(party):
                tally_ledger.create_ledger(party, "Sundry Creditors")
            
            tds_ledger = f"TDS Payable - {section}"
            if not tally_ledger.ledger_exists(tds_ledger):
                tally_ledger.create_ledger(tds_ledger, "Duties & Taxes")
            
            # Create payment voucher with TDS
            # Debit: Party (full amount)
            # Credit: Bank (net payable)
            # Credit: TDS Payable (TDS amount)
            entries = [
                {
                    "ledger": party,
                    "amount": payment_amount,
                    "is_debit": True
                },
                {
                    "ledger": "Bank",
                    "amount": net_payable,
                    "is_debit": False
                },
                {
                    "ledger": tds_ledger,
                    "amount": tds_amount,
                    "is_debit": False
                }
            ]
            
            narration = f"Payment with TDS under section {section}"
            return tally_voucher.create_journal_voucher(
                date=date,
                entries=entries,
                narration=narration
            )
        except Exception as e:
            print(f"Error posting TDS to Tally: {e}")
            return False
    
    def get_tds_register(self, quarter: Optional[str] = None,
                        financial_year: Optional[str] = None,
                        section: Optional[str] = None) -> List[Dict]:
        """
        Get TDS register entries
        
        Args:
            quarter: Filter by quarter (Q1, Q2, Q3, Q4)
            financial_year: Filter by financial year (e.g., "2025-26")
            section: Filter by TDS section
            
        Returns:
            List of TDS entries
        """
        try:
            query = "SELECT * FROM tds_register WHERE 1=1"
            params = []
            
            if quarter:
                query += " AND quarter = ?"
                params.append(quarter)
            
            if financial_year:
                query += " AND financial_year = ?"
                params.append(financial_year)
            
            if section:
                query += " AND section = ?"
                params.append(section)
            
            query += " ORDER BY date DESC"
            
            self.db.cursor.execute(query, params)
            return [dict(row) for row in self.db.cursor.fetchall()]
        except Exception as e:
            return []
    
    def get_quarterly_summary(self, quarter: str, financial_year: str) -> Dict:
        """
        Get quarterly TDS summary
        
        Args:
            quarter: Quarter (Q1, Q2, Q3, Q4)
            financial_year: Financial year (e.g., "2025-26")
            
        Returns:
            Dict with quarterly summary by section
        """
        try:
            entries = self.get_tds_register(quarter=quarter, financial_year=financial_year)
            
            by_section = {}
            total_payment = 0
            total_tds = 0
            
            for entry in entries:
                section = entry['section']
                if section not in by_section:
                    by_section[section] = {
                        "description": TDS_SECTIONS[section]['description'],
                        "payment_amount": 0,
                        "tds_amount": 0,
                        "count": 0
                    }
                
                by_section[section]['payment_amount'] += entry['payment_amount']
                by_section[section]['tds_amount'] += entry['tds_amount']
                by_section[section]['count'] += 1
                
                total_payment += entry['payment_amount']
                total_tds += entry['tds_amount']
            
            return {
                "quarter": quarter,
                "financial_year": financial_year,
                "by_section": by_section,
                "total_payment": total_payment,
                "total_tds": total_tds,
                "entry_count": len(entries)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_party_tds_summary(self, party_pan: str,
                             financial_year: Optional[str] = None) -> Dict:
        """
        Get TDS summary for a specific party
        
        Args:
            party_pan: Party PAN
            financial_year: Financial year (optional)
            
        Returns:
            Dict with party TDS summary
        """
        try:
            query = "SELECT * FROM tds_register WHERE party_pan = ?"
            params = [party_pan]
            
            if financial_year:
                query += " AND financial_year = ?"
                params.append(financial_year)
            
            query += " ORDER BY date DESC"
            
            self.db.cursor.execute(query, params)
            entries = [dict(row) for row in self.db.cursor.fetchall()]
            
            if not entries:
                return {"error": "No TDS entries found for this party"}
            
            total_payment = sum(e['payment_amount'] for e in entries)
            total_tds = sum(e['tds_amount'] for e in entries)
            
            by_section = {}
            for entry in entries:
                section = entry['section']
                if section not in by_section:
                    by_section[section] = {
                        "payment_amount": 0,
                        "tds_amount": 0,
                        "count": 0
                    }
                
                by_section[section]['payment_amount'] += entry['payment_amount']
                by_section[section]['tds_amount'] += entry['tds_amount']
                by_section[section]['count'] += 1
            
            return {
                "party_name": entries[0]['party_name'],
                "party_pan": party_pan,
                "financial_year": financial_year or "All",
                "total_payment": total_payment,
                "total_tds": total_tds,
                "by_section": by_section,
                "entry_count": len(entries),
                "entries": entries
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_threshold(self, section: str, party_pan: str,
                       new_payment: float) -> Dict:
        """
        Check if TDS threshold is crossed
        
        Args:
            section: TDS section
            party_pan: Party PAN
            new_payment: New payment amount
            
        Returns:
            Dict with threshold status
        """
        try:
            if section not in TDS_SECTIONS:
                return {"error": "Invalid TDS section"}
            
            section_data = TDS_SECTIONS[section]
            threshold_single = section_data['threshold_single']
            threshold_aggregate = section_data['threshold_aggregate']
            
            # Get current financial year
            fy = get_financial_year()
            
            # Get aggregate payments for this party in current FY
            self.db.cursor.execute("""
                SELECT SUM(payment_amount) as total
                FROM tds_register
                WHERE party_pan = ? AND section = ? AND financial_year = ?
            """, (party_pan, section, fy))
            
            result = self.db.cursor.fetchone()
            aggregate_so_far = result[0] if result and result[0] else 0
            
            new_aggregate = aggregate_so_far + new_payment
            
            # Check thresholds
            tds_applicable = False
            reason = ""
            
            if new_payment >= threshold_single:
                tds_applicable = True
                reason = f"Single payment threshold ({format_indian_currency(threshold_single)}) crossed"
            elif new_aggregate >= threshold_aggregate:
                tds_applicable = True
                reason = f"Aggregate threshold ({format_indian_currency(threshold_aggregate)}) crossed"
            
            return {
                "success": True,
                "section": section,
                "tds_applicable": tds_applicable,
                "reason": reason,
                "new_payment": new_payment,
                "aggregate_so_far": aggregate_so_far,
                "new_aggregate": new_aggregate,
                "threshold_single": threshold_single,
                "threshold_aggregate": threshold_aggregate
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_all_sections(self) -> List[Dict]:
        """
        Get list of all TDS sections with details
        
        Returns:
            List of TDS sections
        """
        sections = []
        for section_code, details in TDS_SECTIONS.items():
            sections.append({
                "section": section_code,
                "description": details['description'],
                "rate_individual": details['rate_individual'],
                "rate_company": details['rate_company'],
                "threshold_single": details['threshold_single'],
                "threshold_aggregate": details['threshold_aggregate']
            })
        
        return sections


# Global instance
tds_module = TDSModule()
