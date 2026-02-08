"""
Configuration file for AI Accounting Chatbot
Manages Tally connection settings, database paths, and application settings
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database configuration
DATABASE_PATH = os.path.join(BASE_DIR, "accounting.db")

# Tally configuration
TALLY_HOST = "localhost"
TALLY_PORT = 9000
TALLY_TIMEOUT = 30  # seconds

# Application settings
APP_NAME = "AI Accounting Chatbot"
APP_VERSION = "1.0.0"
FINANCIAL_YEAR = "2025-26"
DEFAULT_GST_STATE = "Maharashtra"  # Change as per company location
DEFAULT_STATE_CODE = "27"  # Maharashtra

# Invoice settings
INVOICE_PREFIX = "INV"
INVOICE_OUTPUT_DIR = os.path.join(BASE_DIR, "generated_invoices")

# Create output directory if it doesn't exist
os.makedirs(INVOICE_OUTPUT_DIR, exist_ok=True)

# Company information (update these with actual company details)
COMPANY_INFO = {
    "name": "Your Company Name",
    "address": "Company Address Line 1\nCompany Address Line 2",
    "gstin": "27XXXXX0000X1ZX",
    "pan": "XXXXX0000X",
    "email": "info@yourcompany.com",
    "phone": "+91-1234567890",
}

# UI Configuration
SIDEBAR_PAGES = [
    ("🏠 Home", "home"),
    ("💰 Sales", "sales"),
    ("🛒 Purchases", "purchases"),
    ("💸 Expenses", "expenses"),
    ("🏦 Bank Statement", "bank_statement"),
    ("📋 TDS", "tds"),
    ("🧾 GST", "gst"),
    ("📊 Reports", "reports"),
    ("📚 Ind AS", "ind_as"),
    ("⚙️ Settings", "settings"),
]
