"""
Expense tracking module with OCR, creditor aging, payment reminders
Handles expense management with automated tracking and reminders
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from database.db import db
from tally.voucher import tally_voucher
from tally.ledger import tally_ledger
from invoice.scanner import invoice_scanner
from utils.constants import EXPENSE_CATEGORIES
from utils.helpers import (
    format_indian_currency,
    format_date_indian,
    parse_date,
    calculate_due_date
)
import config


class ExpenseModule:
    """Manager for expense tracking and creditor management"""
    
    def __init__(self):
        """Initialize expense module"""
        self.db = db
        self.scanner = invoice_scanner
    
    def create_expense(self, vendor_name: str, amount: float, category: str,
                      description: str, expense_date: Optional[str] = None,
                      due_date: Optional[str] = None,
                      post_to_tally: bool = True) -> Dict:
        """
        Create expense entry
        
        Args:
            vendor_name: Vendor/payee name
            amount: Expense amount
            category: Expense category
            description: Expense description
            expense_date: Expense date (DD-MM-YYYY, default: today)
            due_date: Payment due date (DD-MM-YYYY, default: 30 days from expense date)
            post_to_tally: Post to Tally
            
        Returns:
            Dict with expense details and status
        """
        try:
            # Parse and validate date
            if expense_date:
                date_obj = parse_date(expense_date)
                if not date_obj:
                    return {"error": "Invalid expense date format"}
                expense_date_str = format_date_indian(date_obj)
                tally_date = date_obj.strftime("%Y%m%d")
            else:
                date_obj = datetime.now()
                expense_date_str = format_date_indian(date_obj)
                tally_date = date_obj.strftime("%Y%m%d")
            
            # Calculate due date
            if due_date:
                due_date_obj = parse_date(due_date)
                if not due_date_obj:
                    return {"error": "Invalid due date format"}
                due_date_str = format_date_indian(due_date_obj)
            else:
                due_date_obj = calculate_due_date(date_obj, 30)
                due_date_str = format_date_indian(due_date_obj)
            
            # Validate category
            if category not in EXPENSE_CATEGORIES:
                return {"error": f"Invalid category. Must be one of: {', '.join(EXPENSE_CATEGORIES)}"}
            
            # Save to database
            expense_id = self.db.insert_expense(
                vendor_name=vendor_name,
                amount=amount,
                category=category,
                description=description,
                date=expense_date_str,
                due_date=due_date_str
            )
            
            result = {
                "success": True,
                "expense_id": expense_id,
                "vendor_name": vendor_name,
                "amount": amount,
                "category": category,
                "description": description,
                "expense_date": expense_date_str,
                "due_date": due_date_str,
                "status": "pending"
            }
            
            # Post to Tally as Journal entry (Expense Dr, Creditor Cr) - only if enabled
            if post_to_tally and config.TALLY_ENABLED:
                try:
                    success = self._post_expense_to_tally(
                        date=tally_date,
                        vendor=vendor_name,
                        category=category,
                        amount=amount,
                        description=description
                    )
                    result["tally_posted"] = success
                    if success:
                        self.db.cursor.execute(
                            "UPDATE expenses SET tally_synced = 1 WHERE id = ?",
                            (expense_id,)
                        )
                        self.db.connection.commit()
                except Exception as e:
                    result["tally_error"] = f"Failed to post to Tally: {str(e)}"
                    # Continue anyway - data is saved in SQLite
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to create expense: {str(e)}"}
    
    def _post_expense_to_tally(self, date: str, vendor: str, category: str,
                              amount: float, description: str) -> bool:
        """
        Post expense to Tally as journal voucher
        
        Args:
            date: Date in YYYYMMDD format
            vendor: Vendor name
            category: Expense category
            amount: Expense amount
            description: Description
            
        Returns:
            True if successful
        """
        try:
            # Ensure ledgers exist
            if not tally_ledger.ledger_exists(vendor):
                tally_ledger.create_ledger(vendor, "Sundry Creditors")
            
            if not tally_ledger.ledger_exists(category):
                tally_ledger.create_ledger(category, "Indirect Expenses")
            
            # Create journal entries
            entries = [
                {
                    "ledger": category,
                    "amount": amount,
                    "is_debit": True
                },
                {
                    "ledger": vendor,
                    "amount": amount,
                    "is_debit": False
                }
            ]
            
            narration = f"Expense: {description}"
            return tally_voucher.create_journal_voucher(
                date=date,
                entries=entries,
                narration=narration
            )
        except Exception as e:
            print(f"Error posting expense to Tally: {e}")
            return False
    
    def mark_expense_paid(self, expense_id: int, payment_date: Optional[str] = None,
                         post_to_tally: bool = True,
                         payment_mode: str = "Bank") -> Dict:
        """
        Mark expense as paid
        
        Args:
            expense_id: Expense ID
            payment_date: Payment date (DD-MM-YYYY, default: today)
            post_to_tally: Post payment to Tally
            payment_mode: Payment mode (Bank/Cash)
            
        Returns:
            Dict with status
        """
        try:
            # Get expense details
            self.db.cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            expense = self.db.cursor.fetchone()
            
            if not expense:
                return {"error": "Expense not found"}
            
            expense = dict(expense)
            
            if expense['payment_status'] == 'paid':
                return {"error": "Expense already marked as paid"}
            
            # Parse payment date
            if payment_date:
                date_obj = parse_date(payment_date)
                if not date_obj:
                    return {"error": "Invalid payment date format"}
                payment_date_str = format_date_indian(date_obj)
                tally_date = date_obj.strftime("%Y%m%d")
            else:
                date_obj = datetime.now()
                payment_date_str = format_date_indian(date_obj)
                tally_date = date_obj.strftime("%Y%m%d")
            
            # Update database
            self.db.update_expense_payment(expense_id, payment_date_str)
            
            result = {
                "success": True,
                "expense_id": expense_id,
                "payment_date": payment_date_str,
                "amount": expense['amount']
            }
            
            # Post payment to Tally
            if post_to_tally:
                try:
                    bank_ledger = "Bank" if payment_mode == "Bank" else "Cash"
                    success = tally_voucher.create_payment_voucher(
                        date=tally_date,
                        party=expense['vendor_name'],
                        amount=expense['amount'],
                        bank_ledger=bank_ledger,
                        narration=f"Payment for {expense['category']}: {expense['description']}"
                    )
                    result["tally_posted"] = success
                except Exception as e:
                    result["tally_error"] = f"Failed to post to Tally: {str(e)}"
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to mark expense as paid: {str(e)}"}
    
    def get_pending_expenses(self, overdue_only: bool = False) -> List[Dict]:
        """
        Get pending expenses
        
        Args:
            overdue_only: Return only overdue expenses
            
        Returns:
            List of pending expense records
        """
        try:
            expenses = self.db.get_expenses(status='pending')
            
            if overdue_only:
                today = datetime.now()
                overdue = []
                for exp in expenses:
                    due_date = parse_date(exp['due_date'])
                    if due_date and due_date < today:
                        exp['days_overdue'] = (today - due_date).days
                        overdue.append(exp)
                return overdue
            
            # Add days until due
            for exp in expenses:
                due_date = parse_date(exp['due_date'])
                if due_date:
                    days_until_due = (due_date - datetime.now()).days
                    exp['days_until_due'] = days_until_due
            
            return expenses
        except Exception as e:
            return []
    
    def get_creditor_aging(self) -> Dict:
        """
        Get creditor aging analysis
        
        Returns:
            Dict with aging buckets
        """
        try:
            creditors = self.db.get_creditors(status='pending')
            today = datetime.now()
            
            aging = {
                "current": [],        # Not due yet
                "0-30": [],          # 0-30 days overdue
                "31-60": [],         # 31-60 days overdue
                "61-90": [],         # 61-90 days overdue
                "90+": []            # More than 90 days overdue
            }
            
            totals = {
                "current": 0,
                "0-30": 0,
                "31-60": 0,
                "61-90": 0,
                "90+": 0
            }
            
            for creditor in creditors:
                due_date = parse_date(creditor['due_date'])
                if not due_date:
                    continue
                
                days_overdue = (today - due_date).days
                creditor['days_overdue'] = days_overdue
                amount = creditor['amount']
                
                if days_overdue < 0:
                    aging["current"].append(creditor)
                    totals["current"] += amount
                elif days_overdue <= 30:
                    aging["0-30"].append(creditor)
                    totals["0-30"] += amount
                elif days_overdue <= 60:
                    aging["31-60"].append(creditor)
                    totals["31-60"] += amount
                elif days_overdue <= 90:
                    aging["61-90"].append(creditor)
                    totals["61-90"] += amount
                else:
                    aging["90+"].append(creditor)
                    totals["90+"] += amount
            
            return {
                "aging": aging,
                "totals": totals,
                "grand_total": sum(totals.values())
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_payment_reminders(self, days_ahead: int = 7) -> List[Dict]:
        """
        Get payment reminders for upcoming due dates
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of expenses due within specified days
        """
        try:
            expenses = self.db.get_expenses(status='pending')
            today = datetime.now()
            cutoff_date = today + timedelta(days=days_ahead)
            
            reminders = []
            for exp in expenses:
                due_date = parse_date(exp['due_date'])
                if due_date and today <= due_date <= cutoff_date:
                    days_until_due = (due_date - today).days
                    exp['days_until_due'] = days_until_due
                    reminders.append(exp)
            
            # Sort by due date
            reminders.sort(key=lambda x: x['due_date'])
            
            return reminders
        except Exception as e:
            return []
    
    def get_expense_summary(self, from_date: Optional[str] = None,
                           to_date: Optional[str] = None) -> Dict:
        """
        Get expense summary by category
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            
        Returns:
            Dict with expense summary by category
        """
        try:
            query = "SELECT * FROM expenses WHERE 1=1"
            params = []
            
            if from_date:
                query += " AND date >= ?"
                params.append(from_date)
            
            if to_date:
                query += " AND date <= ?"
                params.append(to_date)
            
            self.db.cursor.execute(query, params)
            expenses = [dict(row) for row in self.db.cursor.fetchall()]
            
            # Summarize by category
            by_category = {}
            total_amount = 0
            paid_amount = 0
            pending_amount = 0
            
            for exp in expenses:
                category = exp['category']
                amount = exp['amount']
                
                if category not in by_category:
                    by_category[category] = 0
                
                by_category[category] += amount
                total_amount += amount
                
                if exp['payment_status'] == 'paid':
                    paid_amount += amount
                else:
                    pending_amount += amount
            
            return {
                "by_category": by_category,
                "total_amount": total_amount,
                "paid_amount": paid_amount,
                "pending_amount": pending_amount,
                "count": len(expenses)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def scan_expense_bill(self, file_path: str) -> Dict:
        """
        Scan expense bill and extract data
        
        Args:
            file_path: Path to bill file (PDF or image)
            
        Returns:
            Dict with extracted bill data
        """
        try:
            extracted_data = self.scanner.scan_file(file_path)
            
            if "error" in extracted_data:
                return extracted_data
            
            # Format the data for expense entry
            result = {
                "success": True,
                "vendor_name": extracted_data.get("vendor_name", ""),
                "amount": extracted_data.get("total_amount", 0),
                "invoice_no": extracted_data.get("invoice_no", ""),
                "date": extracted_data.get("invoice_date", ""),
                "raw_text": extracted_data.get("raw_text", "")
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to scan expense bill: {str(e)}"}


# Global instance
expense_module = ExpenseModule()
