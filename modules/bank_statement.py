"""
Bank statement import and classification module
Handles bank statement parsing and automatic transaction classification
"""

from datetime import datetime
from typing import Dict, List, Optional
import csv
import json

from database.db import db
from tally.voucher import tally_voucher
from invoice.scanner import invoice_scanner
from utils.constants import BANK_KEYWORDS
from utils.helpers import (
    format_indian_currency,
    format_date_indian,
    parse_date
)


class BankStatementModule:
    """Manager for bank statement import and classification"""
    
    def __init__(self):
        """Initialize bank statement module"""
        self.db = db
        self.scanner = invoice_scanner
    
    def import_from_pdf(self, file_path: str, auto_classify: bool = True) -> Dict:
        """
        Import bank transactions from PDF statement
        
        Args:
            file_path: Path to bank statement PDF
            auto_classify: Automatically classify transactions
            
        Returns:
            Dict with import status and transactions
        """
        try:
            # Extract transactions using OCR
            transactions = self.scanner.extract_bank_statement_data(file_path)
            
            if not transactions:
                return {"error": "No transactions found in PDF"}
            
            # Process and classify transactions
            imported_count = 0
            for txn in transactions:
                if auto_classify:
                    category, voucher_type = self._classify_transaction(txn['description'])
                    txn['category'] = category
                    txn['voucher_type'] = voucher_type
                else:
                    txn['category'] = "Uncategorized"
                    txn['voucher_type'] = "Journal"
                
                # Save to database
                try:
                    self.db.insert_bank_transaction(
                        date=txn['date'],
                        description=txn['description'],
                        debit=txn['debit'],
                        credit=txn['credit'],
                        balance=txn['balance'],
                        category=txn['category'],
                        voucher_type=txn['voucher_type']
                    )
                    imported_count += 1
                except Exception:
                    pass  # Skip duplicates
            
            return {
                "success": True,
                "imported_count": imported_count,
                "total_transactions": len(transactions),
                "transactions": transactions
            }
            
        except Exception as e:
            return {"error": f"Failed to import from PDF: {str(e)}"}
    
    def import_from_csv(self, file_path: str, auto_classify: bool = True,
                       date_column: str = "Date",
                       description_column: str = "Description",
                       debit_column: str = "Debit",
                       credit_column: str = "Credit",
                       balance_column: str = "Balance") -> Dict:
        """
        Import bank transactions from CSV file
        
        Args:
            file_path: Path to CSV file
            auto_classify: Automatically classify transactions
            date_column: Name of date column
            description_column: Name of description column
            debit_column: Name of debit column
            credit_column: Name of credit column
            balance_column: Name of balance column
            
        Returns:
            Dict with import status
        """
        try:
            transactions = []
            imported_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        date_str = row.get(date_column, "")
                        description = row.get(description_column, "")
                        debit = self._parse_amount(row.get(debit_column, "0"))
                        credit = self._parse_amount(row.get(credit_column, "0"))
                        balance = self._parse_amount(row.get(balance_column, "0"))
                        
                        if not date_str or not description:
                            continue
                        
                        # Classify transaction
                        if auto_classify:
                            category, voucher_type = self._classify_transaction(description)
                        else:
                            category = "Uncategorized"
                            voucher_type = "Journal"
                        
                        # Save to database
                        self.db.insert_bank_transaction(
                            date=date_str,
                            description=description,
                            debit=debit,
                            credit=credit,
                            balance=balance,
                            category=category,
                            voucher_type=voucher_type
                        )
                        
                        transactions.append({
                            "date": date_str,
                            "description": description,
                            "debit": debit,
                            "credit": credit,
                            "balance": balance,
                            "category": category
                        })
                        
                        imported_count += 1
                    except Exception:
                        pass  # Skip invalid rows
            
            return {
                "success": True,
                "imported_count": imported_count,
                "transactions": transactions
            }
            
        except Exception as e:
            return {"error": f"Failed to import from CSV: {str(e)}"}
    
    def _classify_transaction(self, description: str) -> tuple:
        """
        Automatically classify transaction based on description
        
        Args:
            description: Transaction description
            
        Returns:
            Tuple of (category, voucher_type)
        """
        description_lower = description.lower()
        
        # Check for sales receipts
        for keyword in BANK_KEYWORDS['sales_receipt']:
            if keyword.lower() in description_lower:
                return ("Sales Receipt", "Receipt")
        
        # Check for payments
        for keyword in BANK_KEYWORDS['payment']:
            if keyword.lower() in description_lower:
                return ("Payment", "Payment")
        
        # Check for bank charges
        for keyword in BANK_KEYWORDS['bank_charges']:
            if keyword.lower() in description_lower:
                return ("Bank Charges", "Payment")
        
        # Check for interest
        for keyword in BANK_KEYWORDS['interest']:
            if keyword.lower() in description_lower:
                return ("Interest Income", "Receipt")
        
        # Check for salary
        for keyword in BANK_KEYWORDS['salary']:
            if keyword.lower() in description_lower:
                return ("Salary Payment", "Payment")
        
        return ("Uncategorized", "Journal")
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        try:
            if not amount_str or str(amount_str).strip() == "":
                return 0.0
            
            # Remove currency symbols and commas
            amount_str = str(amount_str).replace('₹', '').replace('Rs', '').replace(',', '').strip()
            
            # Handle negative amounts in parentheses
            if amount_str.startswith('(') and amount_str.endswith(')'):
                amount_str = '-' + amount_str[1:-1]
            
            return float(amount_str)
        except:
            return 0.0
    
    def get_transactions(self, from_date: Optional[str] = None,
                        to_date: Optional[str] = None,
                        category: Optional[str] = None) -> List[Dict]:
        """
        Get bank transactions
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            category: Filter by category
            
        Returns:
            List of transactions
        """
        try:
            query = "SELECT * FROM bank_transactions WHERE 1=1"
            params = []
            
            if from_date:
                query += " AND date >= ?"
                params.append(from_date)
            
            if to_date:
                query += " AND date <= ?"
                params.append(to_date)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY date DESC"
            
            self.db.cursor.execute(query, params)
            return [dict(row) for row in self.db.cursor.fetchall()]
        except Exception as e:
            return []
    
    def get_bank_summary(self, from_date: Optional[str] = None,
                        to_date: Optional[str] = None) -> Dict:
        """
        Get bank transaction summary
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            
        Returns:
            Dict with summary
        """
        try:
            transactions = self.get_transactions(from_date, to_date)
            
            total_debit = sum(t['debit'] for t in transactions)
            total_credit = sum(t['credit'] for t in transactions)
            
            # Summary by category
            by_category = {}
            for txn in transactions:
                category = txn['category']
                if category not in by_category:
                    by_category[category] = {
                        "debit": 0,
                        "credit": 0,
                        "count": 0
                    }
                
                by_category[category]['debit'] += txn['debit']
                by_category[category]['credit'] += txn['credit']
                by_category[category]['count'] += 1
            
            return {
                "total_debit": total_debit,
                "total_credit": total_credit,
                "net_change": total_credit - total_debit,
                "transaction_count": len(transactions),
                "by_category": by_category
            }
        except Exception as e:
            return {"error": str(e)}
    
    def reclassify_transaction(self, transaction_id: int, category: str,
                              voucher_type: str) -> Dict:
        """
        Reclassify a transaction
        
        Args:
            transaction_id: Transaction ID
            category: New category
            voucher_type: New voucher type
            
        Returns:
            Dict with status
        """
        try:
            self.db.cursor.execute("""
                UPDATE bank_transactions 
                SET category = ?, tally_voucher_type = ?
                WHERE id = ?
            """, (category, voucher_type, transaction_id))
            self.db.connection.commit()
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "category": category,
                "voucher_type": voucher_type
            }
        except Exception as e:
            return {"error": f"Failed to reclassify transaction: {str(e)}"}
    
    def post_to_tally(self, transaction_id: int) -> Dict:
        """
        Post bank transaction to Tally
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Dict with status
        """
        try:
            # Get transaction details
            self.db.cursor.execute(
                "SELECT * FROM bank_transactions WHERE id = ?",
                (transaction_id,)
            )
            txn = self.db.cursor.fetchone()
            
            if not txn:
                return {"error": "Transaction not found"}
            
            txn = dict(txn)
            
            if txn['tally_synced']:
                return {"error": "Transaction already synced to Tally"}
            
            # Parse date
            date_obj = parse_date(txn['date'])
            if not date_obj:
                return {"error": "Invalid date format"}
            
            tally_date = date_obj.strftime("%Y%m%d")
            
            # Post based on voucher type
            success = False
            if txn['tally_voucher_type'] == "Receipt" and txn['credit'] > 0:
                # Receipt voucher
                success = tally_voucher.create_receipt_voucher(
                    date=tally_date,
                    party=txn['category'],
                    amount=txn['credit'],
                    bank_ledger="Bank",
                    narration=txn['description']
                )
            elif txn['tally_voucher_type'] == "Payment" and txn['debit'] > 0:
                # Payment voucher
                success = tally_voucher.create_payment_voucher(
                    date=tally_date,
                    party=txn['category'],
                    amount=txn['debit'],
                    bank_ledger="Bank",
                    narration=txn['description']
                )
            
            if success:
                self.db.cursor.execute(
                    "UPDATE bank_transactions SET tally_synced = 1 WHERE id = ?",
                    (transaction_id,)
                )
                self.db.connection.commit()
                
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "tally_posted": True
                }
            else:
                return {"error": "Failed to post to Tally"}
            
        except Exception as e:
            return {"error": f"Failed to post to Tally: {str(e)}"}
    
    def reconcile(self, from_date: str, to_date: str,
                 opening_balance: float, closing_balance: float) -> Dict:
        """
        Reconcile bank statement
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            opening_balance: Opening balance
            closing_balance: Closing balance from statement
            
        Returns:
            Dict with reconciliation status
        """
        try:
            transactions = self.get_transactions(from_date, to_date)
            
            total_debit = sum(t['debit'] for t in transactions)
            total_credit = sum(t['credit'] for t in transactions)
            
            calculated_closing = opening_balance + total_credit - total_debit
            difference = closing_balance - calculated_closing
            
            return {
                "success": True,
                "opening_balance": opening_balance,
                "total_credit": total_credit,
                "total_debit": total_debit,
                "calculated_closing": calculated_closing,
                "statement_closing": closing_balance,
                "difference": difference,
                "reconciled": abs(difference) < 0.01,
                "transaction_count": len(transactions)
            }
        except Exception as e:
            return {"error": f"Failed to reconcile: {str(e)}"}


# Global instance
bank_statement_module = BankStatementModule()
