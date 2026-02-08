"""
Reports module for MIS reports, Trial Balance, Balance Sheet, P&L
Provides comprehensive financial reporting capabilities
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import json

from database.db import db
from tally.reports import tally_reports
from utils.helpers import (
    format_indian_currency,
    format_date_indian,
    parse_date,
    get_financial_year,
    get_month_name
)


class ReportsModule:
    """Manager for financial reports and MIS"""
    
    def __init__(self):
        """Initialize reports module"""
        self.db = db
        self.tally_reports = tally_reports
    
    def get_trial_balance(self, from_date: str, to_date: str,
                         from_tally: bool = False) -> Dict:
        """
        Get trial balance
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            from_tally: Fetch from Tally (True) or database (False)
            
        Returns:
            Dict with trial balance data
        """
        try:
            if from_tally:
                # Fetch from Tally
                date_obj_from = parse_date(from_date)
                date_obj_to = parse_date(to_date)
                
                if not date_obj_from or not date_obj_to:
                    return {"error": "Invalid date format"}
                
                tally_from = date_obj_from.strftime("%Y%m%d")
                tally_to = date_obj_to.strftime("%Y%m%d")
                
                df = self.tally_reports.get_trial_balance(tally_from, tally_to)
                
                if df.empty:
                    return {"error": "No data received from Tally"}
                
                # Convert to dict
                ledgers = df.to_dict('records')
                total_debit = df['Debit'].sum()
                total_credit = df['Credit'].sum()
                
                return {
                    "success": True,
                    "from_date": from_date,
                    "to_date": to_date,
                    "source": "Tally",
                    "ledgers": ledgers,
                    "total_debit": total_debit,
                    "total_credit": total_credit,
                    "difference": abs(total_debit - total_credit)
                }
            else:
                # Calculate from database
                return self._calculate_trial_balance_from_db(from_date, to_date)
                
        except Exception as e:
            return {"error": f"Failed to get trial balance: {str(e)}"}
    
    def _calculate_trial_balance_from_db(self, from_date: str, to_date: str) -> Dict:
        """Calculate trial balance from database transactions"""
        try:
            ledgers = {}
            
            # Get sales
            self.db.cursor.execute(
                "SELECT * FROM sales WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            sales = [dict(row) for row in self.db.cursor.fetchall()]
            
            for sale in sales:
                # Debtors (Debit)
                if sale['customer_name'] not in ledgers:
                    ledgers[sale['customer_name']] = {"debit": 0, "credit": 0}
                ledgers[sale['customer_name']]['debit'] += sale['total']
                
                # Sales (Credit)
                if 'Sales' not in ledgers:
                    ledgers['Sales'] = {"debit": 0, "credit": 0}
                ledgers['Sales']['credit'] += sale['subtotal']
                
                # GST Output (Credit)
                if sale['cgst'] > 0:
                    if 'Output CGST' not in ledgers:
                        ledgers['Output CGST'] = {"debit": 0, "credit": 0}
                    ledgers['Output CGST']['credit'] += sale['cgst']
                    
                    if 'Output SGST' not in ledgers:
                        ledgers['Output SGST'] = {"debit": 0, "credit": 0}
                    ledgers['Output SGST']['credit'] += sale['sgst']
                
                if sale['igst'] > 0:
                    if 'Output IGST' not in ledgers:
                        ledgers['Output IGST'] = {"debit": 0, "credit": 0}
                    ledgers['Output IGST']['credit'] += sale['igst']
            
            # Get purchases
            self.db.cursor.execute(
                "SELECT * FROM purchases WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            purchases = [dict(row) for row in self.db.cursor.fetchall()]
            
            for purchase in purchases:
                # Creditors (Credit)
                if purchase['vendor_name'] not in ledgers:
                    ledgers[purchase['vendor_name']] = {"debit": 0, "credit": 0}
                ledgers[purchase['vendor_name']]['credit'] += purchase['total']
                
                # Purchase (Debit)
                if 'Purchase' not in ledgers:
                    ledgers['Purchase'] = {"debit": 0, "credit": 0}
                ledgers['Purchase']['debit'] += purchase['subtotal']
                
                # GST Input (Debit)
                if purchase['cgst'] > 0:
                    if 'Input CGST' not in ledgers:
                        ledgers['Input CGST'] = {"debit": 0, "credit": 0}
                    ledgers['Input CGST']['debit'] += purchase['cgst']
                    
                    if 'Input SGST' not in ledgers:
                        ledgers['Input SGST'] = {"debit": 0, "credit": 0}
                    ledgers['Input SGST']['debit'] += purchase['sgst']
                
                if purchase['igst'] > 0:
                    if 'Input IGST' not in ledgers:
                        ledgers['Input IGST'] = {"debit": 0, "credit": 0}
                    ledgers['Input IGST']['debit'] += purchase['igst']
            
            # Get expenses
            self.db.cursor.execute(
                "SELECT * FROM expenses WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            expenses = [dict(row) for row in self.db.cursor.fetchall()]
            
            for expense in expenses:
                # Expense (Debit)
                category = expense['category']
                if category not in ledgers:
                    ledgers[category] = {"debit": 0, "credit": 0}
                ledgers[category]['debit'] += expense['amount']
                
                # Creditor (Credit) - if not paid
                if expense['payment_status'] == 'pending':
                    vendor = expense['vendor_name']
                    if vendor not in ledgers:
                        ledgers[vendor] = {"debit": 0, "credit": 0}
                    ledgers[vendor]['credit'] += expense['amount']
            
            # Convert to list
            ledger_list = []
            total_debit = 0
            total_credit = 0
            
            for ledger_name, amounts in ledgers.items():
                debit = amounts['debit']
                credit = amounts['credit']
                
                ledger_list.append({
                    "Ledger": ledger_name,
                    "Debit": round(debit, 2),
                    "Credit": round(credit, 2)
                })
                
                total_debit += debit
                total_credit += credit
            
            return {
                "success": True,
                "from_date": from_date,
                "to_date": to_date,
                "source": "Database",
                "ledgers": ledger_list,
                "total_debit": round(total_debit, 2),
                "total_credit": round(total_credit, 2),
                "difference": round(abs(total_debit - total_credit), 2)
            }
        except Exception as e:
            return {"error": f"Failed to calculate trial balance: {str(e)}"}
    
    def get_balance_sheet(self, as_on_date: str, from_tally: bool = False) -> Dict:
        """
        Get balance sheet
        
        Args:
            as_on_date: Date (DD-MM-YYYY)
            from_tally: Fetch from Tally (True) or database (False)
            
        Returns:
            Dict with balance sheet data
        """
        try:
            if from_tally:
                # Fetch from Tally
                date_obj = parse_date(as_on_date)
                if not date_obj:
                    return {"error": "Invalid date format"}
                
                tally_date = date_obj.strftime("%Y%m%d")
                result = self.tally_reports.get_balance_sheet(tally_date)
                
                if not result or ("assets" not in result):
                    return {"error": "No data received from Tally"}
                
                total_assets = sum(a['amount'] for a in result['assets'])
                total_liabilities = sum(l['amount'] for l in result['liabilities'])
                
                return {
                    "success": True,
                    "as_on_date": as_on_date,
                    "source": "Tally",
                    "assets": result['assets'],
                    "liabilities": result['liabilities'],
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "difference": abs(total_assets - total_liabilities)
                }
            else:
                # Calculate from database (simplified)
                return self._calculate_balance_sheet_from_db(as_on_date)
                
        except Exception as e:
            return {"error": f"Failed to get balance sheet: {str(e)}"}
    
    def _calculate_balance_sheet_from_db(self, as_on_date: str) -> Dict:
        """Calculate simplified balance sheet from database"""
        try:
            # Assets
            assets = []
            
            # Debtors (Outstanding sales)
            self.db.cursor.execute("SELECT SUM(total) as total FROM sales WHERE date <= ?", (as_on_date,))
            total_sales = self.db.cursor.fetchone()[0] or 0
            assets.append({"name": "Sundry Debtors", "amount": total_sales})
            
            # Liabilities
            liabilities = []
            
            # Creditors (Outstanding purchases + expenses)
            self.db.cursor.execute("SELECT SUM(total) as total FROM purchases WHERE date <= ?", (as_on_date,))
            total_purchases = self.db.cursor.fetchone()[0] or 0
            
            self.db.cursor.execute(
                "SELECT SUM(amount) as total FROM expenses WHERE date <= ? AND payment_status = 'pending'",
                (as_on_date,)
            )
            total_expenses = self.db.cursor.fetchone()[0] or 0
            
            liabilities.append({"name": "Sundry Creditors", "amount": total_purchases + total_expenses})
            
            # Capital (balancing figure)
            total_assets_amount = sum(a['amount'] for a in assets)
            total_liabilities_amount = sum(l['amount'] for l in liabilities)
            capital = total_assets_amount - total_liabilities_amount
            
            liabilities.append({"name": "Capital", "amount": capital})
            
            return {
                "success": True,
                "as_on_date": as_on_date,
                "source": "Database (Simplified)",
                "assets": assets,
                "liabilities": liabilities,
                "total_assets": total_assets_amount,
                "total_liabilities": total_assets_amount,  # Always balanced
                "difference": 0
            }
        except Exception as e:
            return {"error": f"Failed to calculate balance sheet: {str(e)}"}
    
    def get_profit_loss(self, from_date: str, to_date: str,
                       from_tally: bool = False) -> Dict:
        """
        Get profit & loss statement
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            from_tally: Fetch from Tally (True) or database (False)
            
        Returns:
            Dict with P&L data
        """
        try:
            if from_tally:
                # Fetch from Tally
                date_obj_from = parse_date(from_date)
                date_obj_to = parse_date(to_date)
                
                if not date_obj_from or not date_obj_to:
                    return {"error": "Invalid date format"}
                
                tally_from = date_obj_from.strftime("%Y%m%d")
                tally_to = date_obj_to.strftime("%Y%m%d")
                
                result = self.tally_reports.get_profit_loss(tally_from, tally_to)
                
                if not result or ("income" not in result):
                    return {"error": "No data received from Tally"}
                
                total_income = sum(i['amount'] for i in result['income'])
                total_expenses = sum(e['amount'] for e in result['expenses'])
                net_profit = total_income - total_expenses
                
                return {
                    "success": True,
                    "from_date": from_date,
                    "to_date": to_date,
                    "source": "Tally",
                    "income": result['income'],
                    "expenses": result['expenses'],
                    "total_income": total_income,
                    "total_expenses": total_expenses,
                    "net_profit": net_profit
                }
            else:
                # Calculate from database
                return self._calculate_profit_loss_from_db(from_date, to_date)
                
        except Exception as e:
            return {"error": f"Failed to get profit & loss: {str(e)}"}
    
    def _calculate_profit_loss_from_db(self, from_date: str, to_date: str) -> Dict:
        """Calculate P&L from database"""
        try:
            income = []
            expenses = []
            
            # Sales (Income)
            self.db.cursor.execute(
                "SELECT SUM(subtotal) as total FROM sales WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            total_sales = self.db.cursor.fetchone()[0] or 0
            income.append({"name": "Sales", "amount": total_sales})
            
            # Purchases (Expenses)
            self.db.cursor.execute(
                "SELECT SUM(subtotal) as total FROM purchases WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            total_purchases = self.db.cursor.fetchone()[0] or 0
            expenses.append({"name": "Purchase", "amount": total_purchases})
            
            # Other Expenses
            self.db.cursor.execute(
                "SELECT category, SUM(amount) as total FROM expenses WHERE date >= ? AND date <= ? GROUP BY category",
                (from_date, to_date)
            )
            for row in self.db.cursor.fetchall():
                expenses.append({"name": row[0], "amount": row[1]})
            
            total_income = sum(i['amount'] for i in income)
            total_expenses = sum(e['amount'] for e in expenses)
            net_profit = total_income - total_expenses
            
            return {
                "success": True,
                "from_date": from_date,
                "to_date": to_date,
                "source": "Database",
                "income": income,
                "expenses": expenses,
                "total_income": round(total_income, 2),
                "total_expenses": round(total_expenses, 2),
                "net_profit": round(net_profit, 2),
                "net_profit_percentage": round((net_profit / total_income * 100), 2) if total_income > 0 else 0
            }
        except Exception as e:
            return {"error": f"Failed to calculate profit & loss: {str(e)}"}
    
    def get_mis_report(self, from_date: str, to_date: str) -> Dict:
        """
        Get Management Information System (MIS) report
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            
        Returns:
            Dict with comprehensive MIS data
        """
        try:
            # Get P&L
            pl = self._calculate_profit_loss_from_db(from_date, to_date)
            
            # Get sales summary
            self.db.cursor.execute(
                "SELECT COUNT(*) as count, SUM(total) as total, AVG(total) as avg FROM sales WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            sales_row = self.db.cursor.fetchone()
            sales_summary = {
                "count": sales_row[0] or 0,
                "total": sales_row[1] or 0,
                "average": sales_row[2] or 0
            }
            
            # Get purchase summary
            self.db.cursor.execute(
                "SELECT COUNT(*) as count, SUM(total) as total, AVG(total) as avg FROM purchases WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            purchase_row = self.db.cursor.fetchone()
            purchase_summary = {
                "count": purchase_row[0] or 0,
                "total": purchase_row[1] or 0,
                "average": purchase_row[2] or 0
            }
            
            # Get expense summary
            self.db.cursor.execute(
                "SELECT COUNT(*) as count, SUM(amount) as total FROM expenses WHERE date >= ? AND date <= ?",
                (from_date, to_date)
            )
            expense_row = self.db.cursor.fetchone()
            expense_summary = {
                "count": expense_row[0] or 0,
                "total": expense_row[1] or 0
            }
            
            # Outstanding debtors
            self.db.cursor.execute(
                "SELECT COUNT(DISTINCT customer_name) as count, SUM(total) as total FROM sales WHERE date <= ?",
                (to_date,)
            )
            debtor_row = self.db.cursor.fetchone()
            debtors = {
                "count": debtor_row[0] or 0,
                "total": debtor_row[1] or 0
            }
            
            # Outstanding creditors
            self.db.cursor.execute(
                "SELECT COUNT(*) as count, SUM(amount) as total FROM creditors WHERE status = 'pending'"
            )
            creditor_row = self.db.cursor.fetchone()
            creditors = {
                "count": creditor_row[0] or 0,
                "total": creditor_row[1] or 0
            }
            
            # Key ratios
            gross_profit = pl.get('total_income', 0) - purchase_summary['total']
            gross_margin = (gross_profit / pl.get('total_income', 1)) * 100 if pl.get('total_income', 0) > 0 else 0
            
            current_ratio = debtors['total'] / creditors['total'] if creditors['total'] > 0 else 0
            
            return {
                "success": True,
                "period": f"{from_date} to {to_date}",
                "profit_loss": pl,
                "sales": sales_summary,
                "purchases": purchase_summary,
                "expenses": expense_summary,
                "debtors": debtors,
                "creditors": creditors,
                "ratios": {
                    "gross_profit": round(gross_profit, 2),
                    "gross_margin_percentage": round(gross_margin, 2),
                    "net_profit_margin": pl.get('net_profit_percentage', 0),
                    "current_ratio": round(current_ratio, 2)
                }
            }
        except Exception as e:
            return {"error": f"Failed to generate MIS report: {str(e)}"}
    
    def get_monthly_comparison(self, year: int, months: List[int]) -> Dict:
        """
        Get month-wise comparison report
        
        Args:
            year: Year (e.g., 2025)
            months: List of months to compare (e.g., [1, 2, 3])
            
        Returns:
            Dict with monthly comparison
        """
        try:
            comparison = []
            
            for month in months:
                # Get date range
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                from_date = f"01-{month:02d}-{year}"
                to_date = f"{last_day:02d}-{month:02d}-{year}"
                
                # Get monthly data
                pl = self._calculate_profit_loss_from_db(from_date, to_date)
                
                comparison.append({
                    "month": get_month_name(month),
                    "month_number": month,
                    "year": year,
                    "income": pl.get('total_income', 0),
                    "expenses": pl.get('total_expenses', 0),
                    "net_profit": pl.get('net_profit', 0),
                    "margin": pl.get('net_profit_percentage', 0)
                })
            
            # Calculate totals and averages
            total_income = sum(m['income'] for m in comparison)
            total_expenses = sum(m['expenses'] for m in comparison)
            total_profit = sum(m['net_profit'] for m in comparison)
            avg_income = total_income / len(comparison) if comparison else 0
            avg_expenses = total_expenses / len(comparison) if comparison else 0
            avg_profit = total_profit / len(comparison) if comparison else 0
            
            return {
                "success": True,
                "year": year,
                "months": comparison,
                "summary": {
                    "total_income": round(total_income, 2),
                    "total_expenses": round(total_expenses, 2),
                    "total_profit": round(total_profit, 2),
                    "average_income": round(avg_income, 2),
                    "average_expenses": round(avg_expenses, 2),
                    "average_profit": round(avg_profit, 2)
                }
            }
        except Exception as e:
            return {"error": f"Failed to generate monthly comparison: {str(e)}"}
    
    def get_top_customers(self, from_date: str, to_date: str, limit: int = 10) -> List[Dict]:
        """
        Get top customers by sales
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            limit: Number of top customers
            
        Returns:
            List of top customers
        """
        try:
            self.db.cursor.execute("""
                SELECT customer_name, COUNT(*) as invoice_count, SUM(total) as total_sales
                FROM sales
                WHERE date >= ? AND date <= ?
                GROUP BY customer_name
                ORDER BY total_sales DESC
                LIMIT ?
            """, (from_date, to_date, limit))
            
            customers = []
            for row in self.db.cursor.fetchall():
                customers.append({
                    "customer_name": row[0],
                    "invoice_count": row[1],
                    "total_sales": round(row[2], 2)
                })
            
            return customers
        except Exception as e:
            return []
    
    def get_top_vendors(self, from_date: str, to_date: str, limit: int = 10) -> List[Dict]:
        """
        Get top vendors by purchase
        
        Args:
            from_date: Start date (DD-MM-YYYY)
            to_date: End date (DD-MM-YYYY)
            limit: Number of top vendors
            
        Returns:
            List of top vendors
        """
        try:
            self.db.cursor.execute("""
                SELECT vendor_name, COUNT(*) as invoice_count, SUM(total) as total_purchase
                FROM purchases
                WHERE date >= ? AND date <= ?
                GROUP BY vendor_name
                ORDER BY total_purchase DESC
                LIMIT ?
            """, (from_date, to_date, limit))
            
            vendors = []
            for row in self.db.cursor.fetchall():
                vendors.append({
                    "vendor_name": row[0],
                    "invoice_count": row[1],
                    "total_purchase": round(row[2], 2)
                })
            
            return vendors
        except Exception as e:
            return []


# Global instance
reports_module = ReportsModule()
