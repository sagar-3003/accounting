# AI Accounting Chatbot - Modules Documentation

## Overview

This directory contains the core business logic modules for the AI Accounting Chatbot. Each module is designed to handle specific accounting operations with production-ready error handling, type hints, and comprehensive docstrings.

## Modules

### 1. Sales Module (`sales.py`)

**Purpose:** Handle sales entry with step-by-step chatbot interaction, GST calculation, invoice generation, and Tally posting.

**Key Features:**
- Interactive sales entry workflow
- Automatic GST calculation (CGST+SGST or IGST)
- PDF invoice generation using ReportLab
- Tally integration for sales vouchers
- HSN code suggestions
- Sales summary and reporting

**Main Methods:**
- `create_sales_entry()` - Create complete sales entry
- `get_sales_list()` - Retrieve sales records
- `get_sales_summary()` - Get sales analytics
- `search_sales()` - Search sales by customer/invoice
- `get_hsn_suggestions()` - Get HSN code suggestions
- `validate_sale_data()` - Validate sales entry data

**Usage Example:**
```python
from modules.sales import sales_module

result = sales_module.create_sales_entry(
    customer_name="ABC Corp",
    customer_gstin="27AAAAA0000A1ZX",
    customer_address="Mumbai, Maharashtra",
    items=[{
        "name": "Laptop",
        "hsn": "8471",
        "quantity": 2,
        "unit": "Pcs",
        "rate": 50000,
        "gst_rate": 18
    }],
    generate_pdf=True,
    post_to_tally=True
)
```

### 2. Purchase Module (`purchase.py`)

**Purpose:** Handle purchase invoice processing with OCR capabilities and Tally integration.

**Key Features:**
- Invoice scanning from PDF/images
- OCR-based data extraction
- Purchase entry with GST
- Automatic creditor creation
- Tally integration for purchase vouchers

**Main Methods:**
- `scan_invoice()` - Scan and extract invoice data
- `create_purchase_entry()` - Create purchase entry
- `get_purchase_list()` - Retrieve purchase records
- `get_purchase_summary()` - Get purchase analytics
- `search_purchases()` - Search by vendor/invoice
- `create_from_scanned_data()` - Create entry from OCR data

**Usage Example:**
```python
from modules.purchase import purchase_module

# Scan invoice
scanned = purchase_module.scan_invoice("/path/to/invoice.pdf")

# Create purchase entry
result = purchase_module.create_purchase_entry(
    vendor_name="XYZ Suppliers",
    vendor_gstin="27BBBBB0000B1ZX",
    invoice_no="INV-001",
    items=[{
        "name": "Office Supplies",
        "quantity": 100,
        "rate": 50,
        "gst_rate": 18
    }],
    post_to_tally=True
)
```

### 3. Expenses Module (`expenses.py`)

**Purpose:** Track expenses with OCR, creditor aging analysis, and payment reminders.

**Key Features:**
- Expense entry with categories
- Due date tracking
- Creditor aging analysis
- Payment reminders
- Expense summary by category
- Tally integration

**Main Methods:**
- `create_expense()` - Create expense entry
- `mark_expense_paid()` - Mark expense as paid
- `get_pending_expenses()` - Get pending/overdue expenses
- `get_creditor_aging()` - Get aging analysis
- `get_payment_reminders()` - Get upcoming due dates
- `get_expense_summary()` - Get expense analytics
- `scan_expense_bill()` - Scan expense bills

**Usage Example:**
```python
from modules.expenses import expense_module

# Create expense
result = expense_module.create_expense(
    vendor_name="Utility Company",
    amount=5000,
    category="Utilities (Electricity, Water)",
    description="Electricity bill for Jan 2025",
    post_to_tally=True
)

# Get creditor aging
aging = expense_module.get_creditor_aging()
```

### 4. Bank Statement Module (`bank_statement.py`)

**Purpose:** Import and classify bank transactions from statements.

**Key Features:**
- PDF statement import with OCR
- CSV import with flexible column mapping
- Automatic transaction classification
- Bank reconciliation
- Summary by category
- Tally posting capability

**Main Methods:**
- `import_from_pdf()` - Import from PDF statement
- `import_from_csv()` - Import from CSV file
- `get_transactions()` - Retrieve transactions
- `get_bank_summary()` - Get summary by category
- `reclassify_transaction()` - Manually reclassify
- `post_to_tally()` - Post transaction to Tally
- `reconcile()` - Bank reconciliation

**Usage Example:**
```python
from modules.bank_statement import bank_statement_module

# Import from PDF
result = bank_statement_module.import_from_pdf(
    "/path/to/statement.pdf",
    auto_classify=True
)

# Reconcile
recon = bank_statement_module.reconcile(
    from_date="01-01-2025",
    to_date="31-01-2025",
    opening_balance=100000,
    closing_balance=150000
)
```

### 5. TDS Module (`tds.py`)

**Purpose:** TDS computation by section with all TDS sections from constants.

**Key Features:**
- 13 TDS sections supported (194A, 194C, 194J, etc.)
- Rate calculation (individual/company)
- Threshold checking
- Quarterly TDS register
- Party-wise TDS summary
- Financial year tracking
- Tally integration

**Main Methods:**
- `calculate_tds()` - Calculate TDS for payment
- `create_tds_entry()` - Create TDS entry
- `get_tds_register()` - Get TDS register
- `get_quarterly_summary()` - Get quarterly summary
- `get_party_tds_summary()` - Party-wise summary
- `check_threshold()` - Check if threshold crossed
- `get_all_sections()` - List all TDS sections

**Usage Example:**
```python
from modules.tds import tds_module

# Calculate TDS
result = tds_module.calculate_tds(
    section="194J",
    payment_amount=100000,
    party_type="individual"
)

# Create TDS entry
entry = tds_module.create_tds_entry(
    party_name="Consultant",
    party_pan="AAAAA0000A",
    section="194J",
    payment_amount=100000,
    party_type="individual",
    post_to_tally=True
)
```

### 6. GST Module (`gst.py`)

**Purpose:** GST computation, GSTR-1/3B helpers, and compliance reporting.

**Key Features:**
- GST calculation (CGST+SGST or IGST)
- GSTR-1 generation (B2B, B2C)
- GSTR-3B generation (summary return)
- HSN-wise summary
- State-wise sales analysis
- GSTIN validation
- GST liability calculation

**Main Methods:**
- `calculate_gst()` - Calculate GST breakdown
- `get_gstr1_data()` - Generate GSTR-1 data
- `get_gstr3b_data()` - Generate GSTR-3B data
- `get_gst_liability_summary()` - GST liability
- `validate_gstin_details()` - Validate GSTIN
- `get_state_wise_sales()` - State-wise analysis

**Usage Example:**
```python
from modules.gst import gst_module

# Generate GSTR-1
gstr1 = gst_module.get_gstr1_data(month=1, year=2025)

# Generate GSTR-3B
gstr3b = gst_module.get_gstr3b_data(month=1, year=2025)

# Get GST liability
liability = gst_module.get_gst_liability_summary(
    from_date="01-01-2025",
    to_date="31-01-2025"
)
```

### 7. Reports Module (`reports.py`)

**Purpose:** Generate MIS reports, Trial Balance, Balance Sheet, and P&L statements.

**Key Features:**
- Trial Balance (from Tally or database)
- Balance Sheet
- Profit & Loss Statement
- MIS (Management Information System) report
- Monthly comparison reports
- Top customers/vendors analysis
- Key financial ratios

**Main Methods:**
- `get_trial_balance()` - Get trial balance
- `get_balance_sheet()` - Get balance sheet
- `get_profit_loss()` - Get P&L statement
- `get_mis_report()` - Get comprehensive MIS
- `get_monthly_comparison()` - Month-wise comparison
- `get_top_customers()` - Top customers by sales
- `get_top_vendors()` - Top vendors by purchase

**Usage Example:**
```python
from modules.reports import reports_module

# Get Trial Balance
tb = reports_module.get_trial_balance(
    from_date="01-04-2024",
    to_date="31-03-2025",
    from_tally=True
)

# Get MIS Report
mis = reports_module.get_mis_report(
    from_date="01-01-2025",
    to_date="31-01-2025"
)

# Get monthly comparison
comparison = reports_module.get_monthly_comparison(
    year=2025,
    months=[1, 2, 3]
)
```

## Integration Points

All modules integrate with:

1. **Database Layer** (`database/db.py`) - SQLite operations
2. **Tally Layer** (`tally/`) - Tally XML integration
3. **Invoice Layer** (`invoice/`) - PDF generation and OCR
4. **Utils Layer** (`utils/`) - Helper functions and constants

## Error Handling

All modules follow consistent error handling:
- Return dicts with `{"success": True, ...}` on success
- Return dicts with `{"error": "message"}` on failure
- All exceptions are caught and handled gracefully
- Database transactions are properly committed/rolled back

## Type Hints and Documentation

- All functions have type hints for parameters and return values
- Comprehensive docstrings following Google style
- Parameter descriptions and return value documentation
- Example usage in docstrings where helpful

## Testing

Run tests with:
```bash
python3 -m pytest tests/
```

## Production Considerations

1. **Database**: SQLite is used for development. Consider PostgreSQL/MySQL for production.
2. **Tally Connection**: Ensure Tally is running with ODBC server enabled (port 9000).
3. **File Uploads**: Handle file uploads securely with size limits.
4. **OCR Dependencies**: Tesseract OCR must be installed on the system.
5. **PDF Generation**: ReportLab generates production-ready invoices.
6. **Error Logging**: Add proper logging for production deployment.

## License

Copyright © 2025 AI Accounting Chatbot. All rights reserved.
