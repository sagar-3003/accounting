"""
Database module for SQLite operations
Handles all database schema creation and CRUD operations
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import config


class Database:
    """SQLite database manager for the accounting application"""
    
    def __init__(self, db_path: str = config.DATABASE_PATH):
        """Initialize database connection"""
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self.initialize_db()
    
    def connect(self) -> None:
        """Create database connection"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
    
    def close(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def initialize_db(self) -> None:
        """Create all required tables if they don't exist"""
        self.connect()
        
        # Sales table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT UNIQUE,
                customer_name TEXT,
                customer_gstin TEXT,
                items_json TEXT,
                subtotal REAL,
                cgst REAL,
                sgst REAL,
                igst REAL,
                total REAL,
                date TEXT,
                tally_synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Purchases table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT,
                vendor_name TEXT,
                vendor_gstin TEXT,
                items_json TEXT,
                subtotal REAL,
                cgst REAL,
                sgst REAL,
                igst REAL,
                total REAL,
                date TEXT,
                tally_synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Expenses table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_name TEXT,
                amount REAL,
                category TEXT,
                description TEXT,
                date TEXT,
                due_date TEXT,
                payment_status TEXT DEFAULT 'pending',
                payment_date TEXT,
                tally_synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Bank transactions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bank_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                description TEXT,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0,
                balance REAL,
                category TEXT,
                tally_voucher_type TEXT,
                tally_synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # TDS register table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tds_register (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                party_name TEXT,
                party_pan TEXT,
                section TEXT,
                payment_amount REAL,
                tds_rate REAL,
                tds_amount REAL,
                net_payable REAL,
                date TEXT,
                quarter TEXT,
                financial_year TEXT,
                tally_synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Creditors table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS creditors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_name TEXT,
                invoice_no TEXT,
                amount REAL,
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                reminder_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Settings table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        self.connection.commit()
    
    # Sales operations
    def insert_sale(self, invoice_no: str, customer_name: str, customer_gstin: str,
                    items: List[Dict], subtotal: float, cgst: float, sgst: float,
                    igst: float, total: float, date: str) -> int:
        """Insert a new sales record"""
        self.cursor.execute("""
            INSERT INTO sales (invoice_no, customer_name, customer_gstin, items_json,
                              subtotal, cgst, sgst, igst, total, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice_no, customer_name, customer_gstin, json.dumps(items),
              subtotal, cgst, sgst, igst, total, date))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_sales(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all sales records"""
        query = "SELECT * FROM sales ORDER BY date DESC"
        if limit:
            query += f" LIMIT {limit}"
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_next_invoice_number(self, prefix: str, financial_year: str) -> str:
        """Generate next invoice number"""
        self.cursor.execute("""
            SELECT invoice_no FROM sales 
            WHERE invoice_no LIKE ? 
            ORDER BY id DESC LIMIT 1
        """, (f"{prefix}/{financial_year}/%",))
        result = self.cursor.fetchone()
        
        if result:
            last_no = int(result[0].split('/')[-1])
            next_no = last_no + 1
        else:
            next_no = 1
        
        return f"{prefix}/{financial_year}/{next_no:03d}"
    
    # Purchase operations
    def insert_purchase(self, invoice_no: str, vendor_name: str, vendor_gstin: str,
                       items: List[Dict], subtotal: float, cgst: float, sgst: float,
                       igst: float, total: float, date: str) -> int:
        """Insert a new purchase record"""
        self.cursor.execute("""
            INSERT INTO purchases (invoice_no, vendor_name, vendor_gstin, items_json,
                                  subtotal, cgst, sgst, igst, total, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice_no, vendor_name, vendor_gstin, json.dumps(items),
              subtotal, cgst, sgst, igst, total, date))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_purchases(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all purchase records"""
        query = "SELECT * FROM purchases ORDER BY date DESC"
        if limit:
            query += f" LIMIT {limit}"
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]
    
    # Expense operations
    def insert_expense(self, vendor_name: str, amount: float, category: str,
                      description: str, date: str, due_date: str) -> int:
        """Insert a new expense record"""
        self.cursor.execute("""
            INSERT INTO expenses (vendor_name, amount, category, description, date, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (vendor_name, amount, category, description, date, due_date))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_expenses(self, status: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Get expense records"""
        query = "SELECT * FROM expenses"
        if status:
            query += f" WHERE payment_status = '{status}'"
        query += " ORDER BY date DESC"
        if limit:
            query += f" LIMIT {limit}"
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_expense_payment(self, expense_id: int, payment_date: str) -> None:
        """Mark expense as paid"""
        self.cursor.execute("""
            UPDATE expenses 
            SET payment_status = 'paid', payment_date = ?
            WHERE id = ?
        """, (payment_date, expense_id))
        self.connection.commit()
    
    # Bank transaction operations
    def insert_bank_transaction(self, date: str, description: str, debit: float,
                                credit: float, balance: float, category: str,
                                voucher_type: str) -> int:
        """Insert a bank transaction"""
        self.cursor.execute("""
            INSERT INTO bank_transactions (date, description, debit, credit, balance,
                                          category, tally_voucher_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, description, debit, credit, balance, category, voucher_type))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_bank_transactions(self, limit: Optional[int] = None) -> List[Dict]:
        """Get bank transactions"""
        query = "SELECT * FROM bank_transactions ORDER BY date DESC"
        if limit:
            query += f" LIMIT {limit}"
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]
    
    # TDS operations
    def insert_tds_entry(self, party_name: str, party_pan: str, section: str,
                        payment_amount: float, tds_rate: float, tds_amount: float,
                        net_payable: float, date: str, quarter: str, 
                        financial_year: str) -> int:
        """Insert a TDS entry"""
        self.cursor.execute("""
            INSERT INTO tds_register (party_name, party_pan, section, payment_amount,
                                     tds_rate, tds_amount, net_payable, date, quarter,
                                     financial_year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (party_name, party_pan, section, payment_amount, tds_rate, tds_amount,
              net_payable, date, quarter, financial_year))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_tds_entries(self, quarter: Optional[str] = None, 
                       financial_year: Optional[str] = None) -> List[Dict]:
        """Get TDS entries"""
        query = "SELECT * FROM tds_register WHERE 1=1"
        params = []
        
        if quarter:
            query += " AND quarter = ?"
            params.append(quarter)
        if financial_year:
            query += " AND financial_year = ?"
            params.append(financial_year)
        
        query += " ORDER BY date DESC"
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    # Creditor operations
    def insert_creditor(self, vendor_name: str, invoice_no: str, amount: float,
                       due_date: str) -> int:
        """Insert a creditor record"""
        self.cursor.execute("""
            INSERT INTO creditors (vendor_name, invoice_no, amount, due_date)
            VALUES (?, ?, ?, ?)
        """, (vendor_name, invoice_no, amount, due_date))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_creditors(self, status: Optional[str] = None) -> List[Dict]:
        """Get creditor records"""
        query = "SELECT * FROM creditors"
        if status:
            query += f" WHERE status = '{status}'"
        query += " ORDER BY due_date ASC"
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_creditor_status(self, creditor_id: int, status: str) -> None:
        """Update creditor payment status"""
        self.cursor.execute("""
            UPDATE creditors SET status = ? WHERE id = ?
        """, (status, creditor_id))
        self.connection.commit()
    
    # Settings operations
    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value"""
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value"""
        self.cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
        self.connection.commit()
    
    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings"""
        self.cursor.execute("SELECT key, value FROM settings")
        return {row[0]: row[1] for row in self.cursor.fetchall()}


# Global database instance
db = Database()
