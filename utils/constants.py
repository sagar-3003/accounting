"""
Constants for the AI Accounting Chatbot
Tax rates, TDS sections, HSN codes, state codes, and other fixed values
"""

# GST Rates by HSN code ranges
GST_RATES = {
    "0%": ["Exempt items", "Fresh vegetables", "Fresh fruits", "Milk", "Bread"],
    "5%": ["Coffee", "Tea", "Edible oils", "Coal", "Medicines", "Transport services"],
    "12%": ["Butter", "Ghee", "Computers", "Processed food", "Umbrellas"],
    "18%": ["Most goods and services", "IT services", "Telecom services", "Financial services"],
    "28%": ["Luxury goods", "AC", "Refrigerators", "Cars", "Motorcycles", "Tobacco"]
}

# Common HSN codes with descriptions and rates
HSN_CODES = {
    "1001": {"description": "Wheat", "rate": 0},
    "0901": {"description": "Coffee", "rate": 5},
    "0902": {"description": "Tea", "rate": 5},
    "0405": {"description": "Butter and Ghee", "rate": 12},
    "1507": {"description": "Soyabean oil", "rate": 5},
    "2710": {"description": "Petroleum oils", "rate": 18},
    "3004": {"description": "Medicines", "rate": 5},
    "4901": {"description": "Printed books", "rate": 0},
    "6109": {"description": "T-shirts", "rate": 5},
    "6203": {"description": "Men's suits", "rate": 12},
    "7113": {"description": "Jewellery", "rate": 3},
    "8414": {"description": "Air conditioning machines", "rate": 28},
    "8415": {"description": "Refrigerators", "rate": 28},
    "8471": {"description": "Computers", "rate": 18},
    "8517": {"description": "Telephones", "rate": 18},
    "8703": {"description": "Cars", "rate": 28},
    "8711": {"description": "Motorcycles", "rate": 28},
    "9403": {"description": "Furniture", "rate": 18},
    "9801": {"description": "IT services", "rate": 18},
    "9973": {"description": "Consulting services", "rate": 18},
    "9997": {"description": "Hotel services", "rate": 18},
    "9998": {"description": "Restaurant services", "rate": 5},
}

# TDS Sections with descriptions and rates
TDS_SECTIONS = {
    "194C": {
        "description": "Payment to contractors",
        "rate_individual": 1.0,
        "rate_company": 2.0,
        "threshold_single": 30000,
        "threshold_aggregate": 100000
    },
    "194J": {
        "description": "Professional or technical services",
        "rate_individual": 10.0,
        "rate_company": 10.0,
        "threshold_single": 30000,
        "threshold_aggregate": 30000
    },
    "194H": {
        "description": "Commission or brokerage",
        "rate_individual": 5.0,
        "rate_company": 5.0,
        "threshold_single": 15000,
        "threshold_aggregate": 15000
    },
    "194I": {
        "description": "Rent",
        "rate_individual": 10.0,  # For plant and machinery
        "rate_company": 10.0,
        "threshold_single": 240000,
        "threshold_aggregate": 240000
    },
    "194IA": {
        "description": "Payment for purchase of immovable property",
        "rate_individual": 1.0,
        "rate_company": 1.0,
        "threshold_single": 5000000,
        "threshold_aggregate": 5000000
    },
    "194IB": {
        "description": "Payment of rent by individuals/HUF",
        "rate_individual": 5.0,
        "rate_company": 5.0,
        "threshold_single": 50000,
        "threshold_aggregate": 600000
    },
    "194A": {
        "description": "Interest other than on securities",
        "rate_individual": 10.0,
        "rate_company": 10.0,
        "threshold_single": 40000,  # For senior citizens: 50000
        "threshold_aggregate": 40000
    },
    "194B": {
        "description": "Winnings from lottery or crossword puzzle",
        "rate_individual": 30.0,
        "rate_company": 30.0,
        "threshold_single": 10000,
        "threshold_aggregate": 10000
    },
    "194D": {
        "description": "Insurance commission",
        "rate_individual": 5.0,
        "rate_company": 10.0,
        "threshold_single": 15000,
        "threshold_aggregate": 15000
    },
    "194M": {
        "description": "Payment to contractors by non-filers",
        "rate_individual": 5.0,
        "rate_company": 5.0,
        "threshold_single": 50000000,
        "threshold_aggregate": 50000000
    },
    "194N": {
        "description": "Cash withdrawal exceeding specified limit",
        "rate_individual": 2.0,
        "rate_company": 2.0,
        "threshold_single": 10000000,  # 1 crore
        "threshold_aggregate": 10000000
    },
    "194O": {
        "description": "Payment for e-commerce transactions",
        "rate_individual": 1.0,
        "rate_company": 1.0,
        "threshold_single": 500000,
        "threshold_aggregate": 500000
    },
    "194Q": {
        "description": "Payment for purchase of goods",
        "rate_individual": 0.1,
        "rate_company": 0.1,
        "threshold_single": 5000000,
        "threshold_aggregate": 5000000
    }
}

# Expense categories
EXPENSE_CATEGORIES = [
    "Rent",
    "Salary & Wages",
    "Travel & Conveyance",
    "Professional Fees",
    "Office Supplies",
    "Utilities (Electricity, Water)",
    "Telephone & Internet",
    "Insurance",
    "Repairs & Maintenance",
    "Advertising & Marketing",
    "Legal & Professional Charges",
    "Bank Charges & Interest",
    "Depreciation",
    "Printing & Stationery",
    "Fuel & Petrol",
    "Freight & Courier",
    "Others"
]

# State codes for GST
STATE_CODES = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman and Diu",
    "26": "Dadra and Nagar Haveli",
    "27": "Maharashtra",
    "28": "Andhra Pradesh (Old)",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh (New)",
    "38": "Ladakh"
}

# Tally parent groups
TALLY_PARENT_GROUPS = {
    "ASSETS": [
        "Bank Accounts",
        "Cash-in-Hand",
        "Current Assets",
        "Fixed Assets",
        "Investments",
        "Sundry Debtors"
    ],
    "LIABILITIES": [
        "Capital Account",
        "Current Liabilities",
        "Loans (Liability)",
        "Sundry Creditors",
        "Duties & Taxes"
    ],
    "INCOME": [
        "Direct Income",
        "Indirect Income",
        "Sales Accounts"
    ],
    "EXPENSES": [
        "Direct Expenses",
        "Indirect Expenses",
        "Purchase Accounts"
    ]
}

# GST rate slabs
GST_RATE_SLABS = [0, 0.25, 3, 5, 12, 18, 28]

# Default units of measurement
UNITS_OF_MEASUREMENT = [
    "Pcs",
    "Kg",
    "Gms",
    "Ltr",
    "Mtr",
    "Sq.Mtr",
    "Box",
    "Pack",
    "Set",
    "Dozen",
    "Ton"
]

# Voucher types in Tally
TALLY_VOUCHER_TYPES = [
    "Sales",
    "Purchase",
    "Payment",
    "Receipt",
    "Contra",
    "Journal",
    "Debit Note",
    "Credit Note"
]

# Financial year quarters
QUARTERS = {
    "Q1": ["April", "May", "June"],
    "Q2": ["July", "August", "September"],
    "Q3": ["October", "November", "December"],
    "Q4": ["January", "February", "March"]
}

# Bank transaction keywords for classification
BANK_KEYWORDS = {
    "sales_receipt": ["NEFT", "RTGS", "IMPS", "UPI", "PAYMENT RECEIVED", "TRANSFER FROM"],
    "payment": ["PAYMENT TO", "TRANSFER TO", "EMI", "BILL PAY"],
    "bank_charges": ["CHARGES", "FEE", "COMMISSION"],
    "interest": ["INTEREST", "INT CREDIT"],
    "salary": ["SALARY", "PAYROLL", "WAGES"]
}
