"""
Helper functions for the AI Accounting Chatbot
Indian currency formatting, date helpers, validators, etc.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dateutil import parser as date_parser


def format_indian_currency(amount: float) -> str:
    """
    Format amount in Indian currency style (₹1,23,456.00)
    
    Args:
        amount: Amount to format
        
    Returns:
        Formatted currency string
    """
    if amount < 0:
        sign = "-"
        amount = abs(amount)
    else:
        sign = ""
    
    # Convert to string with 2 decimal places
    amount_str = f"{amount:.2f}"
    integer_part, decimal_part = amount_str.split(".")
    
    # Indian numbering system: last 3 digits, then groups of 2
    if len(integer_part) <= 3:
        formatted = integer_part
    else:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        
        # Add commas every 2 digits from right to left
        formatted_remaining = ""
        for i, digit in enumerate(reversed(remaining)):
            if i > 0 and i % 2 == 0:
                formatted_remaining = "," + formatted_remaining
            formatted_remaining = digit + formatted_remaining
        
        formatted = formatted_remaining + "," + last_three
    
    return f"{sign}₹{formatted}.{decimal_part}"


def get_financial_year(date: Optional[datetime] = None) -> str:
    """
    Get financial year in format YYYY-YY (e.g., 2025-26)
    Financial year runs from April 1 to March 31
    
    Args:
        date: Date to get financial year for (default: today)
        
    Returns:
        Financial year string
    """
    if date is None:
        date = datetime.now()
    
    if date.month >= 4:  # April to December
        fy_start = date.year
        fy_end = date.year + 1
    else:  # January to March
        fy_start = date.year - 1
        fy_end = date.year
    
    return f"{fy_start}-{str(fy_end)[-2:]}"


def get_quarter(date: Optional[datetime] = None) -> str:
    """
    Get quarter (Q1, Q2, Q3, Q4) for financial year
    Q1: Apr-Jun, Q2: Jul-Sep, Q3: Oct-Dec, Q4: Jan-Mar
    
    Args:
        date: Date to get quarter for (default: today)
        
    Returns:
        Quarter string (Q1, Q2, Q3, or Q4)
    """
    if date is None:
        date = datetime.now()
    
    month = date.month
    
    if 4 <= month <= 6:
        return "Q1"
    elif 7 <= month <= 9:
        return "Q2"
    elif 10 <= month <= 12:
        return "Q3"
    else:  # Jan-Mar
        return "Q4"


def parse_date(date_string: str) -> Optional[datetime]:
    """
    Parse date from various formats (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, etc.)
    
    Args:
        date_string: Date string to parse
        
    Returns:
        datetime object or None if parsing fails
    """
    try:
        # Try dateutil parser (handles most formats)
        return date_parser.parse(date_string, dayfirst=True)
    except:
        # Try common Indian formats manually
        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d.%m.%Y",
            "%Y-%m-%d",
            "%d %B %Y",
            "%d %b %Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except:
                continue
        
        return None


def validate_gstin(gstin: str) -> bool:
    """
    Validate GSTIN format
    Format: 22AAAAA0000A1Z5 (15 characters)
    
    Args:
        gstin: GSTIN to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not gstin or len(gstin) != 15:
        return False
    
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    return bool(re.match(pattern, gstin.upper()))


def validate_pan(pan: str) -> bool:
    """
    Validate PAN format
    Format: AAAAA0000A (10 characters)
    
    Args:
        pan: PAN to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not pan or len(pan) != 10:
        return False
    
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    return bool(re.match(pattern, pan.upper()))


def extract_state_from_gstin(gstin: str) -> Optional[Tuple[str, str]]:
    """
    Extract state code and name from GSTIN
    
    Args:
        gstin: GSTIN string
        
    Returns:
        Tuple of (state_code, state_name) or None if invalid
    """
    from utils.constants import STATE_CODES
    
    if not validate_gstin(gstin):
        return None
    
    state_code = gstin[:2]
    state_name = STATE_CODES.get(state_code)
    
    if state_name:
        return (state_code, state_name)
    return None


def generate_invoice_number(prefix: str, db) -> str:
    """
    Generate next invoice number in format PREFIX/FY/NNN
    
    Args:
        prefix: Invoice prefix (e.g., INV, PUR)
        db: Database instance
        
    Returns:
        Generated invoice number
    """
    fy = get_financial_year()
    return db.get_next_invoice_number(prefix, fy)


def calculate_due_date(invoice_date: datetime, credit_days: int = 30) -> datetime:
    """
    Calculate due date from invoice date
    
    Args:
        invoice_date: Invoice date
        credit_days: Credit period in days
        
    Returns:
        Due date
    """
    return invoice_date + timedelta(days=credit_days)


def format_date_indian(date: datetime) -> str:
    """
    Format date in Indian style (DD-MM-YYYY)
    
    Args:
        date: Date to format
        
    Returns:
        Formatted date string
    """
    return date.strftime("%d-%m-%Y")


def get_month_name(month: int) -> str:
    """
    Get month name from month number
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Month name
    """
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    if 1 <= month <= 12:
        return months[month - 1]
    return ""


def calculate_gst(amount: float, gst_rate: float, is_intra_state: bool = True) -> dict:
    """
    Calculate GST breakdown
    
    Args:
        amount: Taxable amount
        gst_rate: GST rate percentage
        is_intra_state: True for CGST+SGST, False for IGST
        
    Returns:
        Dict with GST breakdown
    """
    gst_amount = (amount * gst_rate) / 100
    
    if is_intra_state:
        # CGST + SGST (split equally)
        cgst = gst_amount / 2
        sgst = gst_amount / 2
        igst = 0
    else:
        # IGST
        cgst = 0
        sgst = 0
        igst = gst_amount
    
    return {
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "igst": round(igst, 2),
        "total_gst": round(gst_amount, 2),
        "total_amount": round(amount + gst_amount, 2)
    }


def words_to_number(amount: float) -> str:
    """
    Convert amount to words (Indian style)
    
    Args:
        amount: Amount to convert
        
    Returns:
        Amount in words
    """
    # Simple implementation for common amounts
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", 
             "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    
    def convert_below_thousand(n):
        if n == 0:
            return ""
        elif n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + " " + ones[n % 10]
        else:
            return ones[n // 100] + " Hundred " + convert_below_thousand(n % 100)
    
    if amount == 0:
        return "Zero Rupees Only"
    
    # Split into rupees and paise
    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))
    
    result = ""
    
    # Convert rupees
    if rupees >= 10000000:  # Crores
        crores = rupees // 10000000
        result += convert_below_thousand(crores) + " Crore "
        rupees %= 10000000
    
    if rupees >= 100000:  # Lakhs
        lakhs = rupees // 100000
        result += convert_below_thousand(lakhs) + " Lakh "
        rupees %= 100000
    
    if rupees >= 1000:  # Thousands
        thousands = rupees // 1000
        result += convert_below_thousand(thousands) + " Thousand "
        rupees %= 1000
    
    if rupees > 0:
        result += convert_below_thousand(rupees) + " "
    
    result += "Rupees"
    
    if paise > 0:
        result += " and " + convert_below_thousand(paise) + " Paise"
    
    result += " Only"
    
    return result.strip()


def is_same_state(gstin1: str, gstin2: str) -> bool:
    """
    Check if two GSTINs belong to the same state
    
    Args:
        gstin1: First GSTIN
        gstin2: Second GSTIN
        
    Returns:
        True if same state, False otherwise
    """
    if not gstin1 or not gstin2:
        return True  # Default to intra-state if GSTIN not provided
    
    return gstin1[:2] == gstin2[:2]
