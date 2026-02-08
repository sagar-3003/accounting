"""Modules package for AI Accounting Chatbot"""

from modules.sales import sales_module, SalesModule
from modules.purchase import purchase_module, PurchaseModule
from modules.expenses import expense_module, ExpenseModule
from modules.bank_statement import bank_statement_module, BankStatementModule
from modules.tds import tds_module, TDSModule
from modules.gst import gst_module, GSTModule
from modules.reports import reports_module, ReportsModule

__all__ = [
    'sales_module',
    'SalesModule',
    'purchase_module',
    'PurchaseModule',
    'expense_module',
    'ExpenseModule',
    'bank_statement_module',
    'BankStatementModule',
    'tds_module',
    'TDSModule',
    'gst_module',
    'GSTModule',
    'reports_module',
    'ReportsModule',
]
