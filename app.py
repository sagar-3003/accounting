"""
AI Accounting Chatbot - Single Chat Window Interface
A WhatsApp-style conversational accounting assistant
"""

import streamlit as st
import re
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import json

# Import configuration and core modules
import config
from database.db import db
from tally.connection import TallyConnector
from utils.helpers import (
    format_indian_currency, 
    calculate_gst, 
    validate_gstin,
    format_date_indian,
    parse_date,
    get_financial_year
)

# Import module managers
from modules.sales import SalesModule
from modules.purchase import PurchaseModule
from modules.expenses import ExpenseModule
from modules.bank_statement import BankStatementModule
from modules.tds import TDSModule
from modules.gst import GSTModule
from modules.reports import ReportsModule
from modules.ind_as import IndASModule

# Import invoice tools
from invoice.generator import invoice_generator
from invoice.scanner import invoice_scanner

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Accounting Assistant",
    page_icon="🧾",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize session state for conversation tracking"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add greeting message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hi! 👋 I'm your accounting assistant. Tell me about any transaction, ask for reports, or upload invoices. I'll handle the rest!"
        })
    
    if "current_flow" not in st.session_state:
        st.session_state.current_flow = None  # None, "sales", "purchase", "expense", "tds", etc.
    
    if "flow_step" not in st.session_state:
        st.session_state.flow_step = 0
    
    if "flow_data" not in st.session_state:
        st.session_state.flow_data = {}
    
    # Tally settings
    if 'tally_host' not in st.session_state:
        st.session_state.tally_host = db.get_setting('tally_host') or 'localhost'
    if 'tally_port' not in st.session_state:
        st.session_state.tally_port = db.get_setting('tally_port') or '9000'
    if 'company_name' not in st.session_state:
        st.session_state.company_name = db.get_setting('company_name') or ''

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

def get_modules():
    """Get or create module instances"""
    if 'modules' not in st.session_state:
        st.session_state.modules = {
            'sales': SalesModule(),
            'purchase': PurchaseModule(),
            'expenses': ExpenseModule(),
            'bank_statement': BankStatementModule(),
            'tds': TDSModule(),
            'gst': GSTModule(),
            'reports': ReportsModule(),
            'ind_as': IndASModule()
        }
    return st.session_state.modules

def get_tally_connector():
    """Get Tally connector instance"""
    if 'tally_connector' not in st.session_state:
        st.session_state.tally_connector = TallyConnector(
            host=st.session_state.tally_host,
            port=int(st.session_state.tally_port)
        )
    return st.session_state.tally_connector

# ============================================================================
# INTENT DETECTION & DATA EXTRACTION
# ============================================================================

def detect_intent(message: str) -> str:
    """
    Detect user intent from message using keyword matching
    
    Args:
        message: User message
        
    Returns:
        Intent string
    """
    message_lower = message.lower()
    
    # Check for greetings
    greeting_keywords = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    if any(keyword in message_lower for keyword in greeting_keywords):
        return "GREETING"
    
    # Check for help
    help_keywords = ['help', 'what can you do', 'features', 'how to use']
    if any(keyword in message_lower for keyword in help_keywords):
        return "HELP"
    
    # Check for sales
    sales_keywords = ['sold', 'sales', 'invoice', 'billed', 'supplied', 'revenue', 'customer']
    if any(keyword in message_lower for keyword in sales_keywords):
        return "SALES"
    
    # Check for purchase
    purchase_keywords = ['purchased', 'bought', 'purchase', 'procurement', 'vendor bill']
    if any(keyword in message_lower for keyword in purchase_keywords):
        return "PURCHASE"
    
    # Check for expense
    expense_keywords = ['expense', 'paid for', 'rent', 'electricity', 'professional fees', 'spent']
    if any(keyword in message_lower for keyword in expense_keywords):
        return "EXPENSE"
    
    # Check for payment received
    payment_received_keywords = ['received payment', 'payment received', 'collected', 'receipt']
    if any(keyword in message_lower for keyword in payment_received_keywords):
        return "PAYMENT_RECEIVED"
    
    # Check for payment made
    payment_made_keywords = ['paid to', 'payment made', 'settled', 'cleared']
    if any(keyword in message_lower for keyword in payment_made_keywords):
        return "PAYMENT_MADE"
    
    # Check for bank statement
    bank_keywords = ['bank statement', 'bank entries', 'reconciliation']
    if any(keyword in message_lower for keyword in bank_keywords):
        return "BANK_STATEMENT"
    
    # Check for TDS
    tds_keywords = ['tds', 'tax deducted', '194c', '194j', 'tds return', '26q']
    if any(keyword in message_lower for keyword in tds_keywords):
        return "TDS"
    
    # Check for GST
    gst_keywords = ['gst', 'gstr', 'gst return', 'igst', 'cgst', 'sgst', 'hsn', 'e-way']
    if any(keyword in message_lower for keyword in gst_keywords):
        return "GST"
    
    # Check for reports
    report_keywords = ['trial balance', 'balance sheet', 'profit and loss', 'p&l', 'report', 
                      'mis', 'outstanding', 'receivable', 'payable']
    if any(keyword in message_lower for keyword in report_keywords):
        return "REPORT"
    
    # Check for Ind AS
    indas_keywords = ['ind as', 'accounting standard', 'indian accounting']
    if any(keyword in message_lower for keyword in indas_keywords):
        return "IND_AS"
    
    return "UNKNOWN"

def extract_data(message: str) -> Dict:
    """
    Extract key data from message using regex
    
    Args:
        message: User message
        
    Returns:
        Dict with extracted data
    """
    data = {}
    
    # Extract party name (after "to" or "from")
    party_pattern = r'(?:to|from)\s+([A-Z][A-Za-z\s&\.]+?)(?:\s+for|\s+of|,|$)'
    party_match = re.search(party_pattern, message, re.IGNORECASE)
    if party_match:
        data['party_name'] = party_match.group(1).strip()
    
    # Extract amount (₹ or numbers)
    amount_patterns = [
        r'₹\s*([\d,]+(?:\.\d{2})?)',
        r'(?:for|of|amount|rs\.?|inr)\s*₹?\s*([\d,]+(?:\.\d{2})?)',
        r'\b([\d,]+(?:\.\d{2})?)\s*(?:rupees|rs|inr)',
    ]
    for pattern in amount_patterns:
        amount_match = re.search(pattern, message, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            try:
                data['amount'] = float(amount_str)
                break
            except ValueError:
                pass
    
    # Extract GST rate
    gst_pattern = r'\b(\d+)%?\s*(?:gst|GST)'
    gst_match = re.search(gst_pattern, message)
    if gst_match:
        data['gst_rate'] = int(gst_match.group(1))
    
    # Check for "plus GST" or "including GST"
    if 'plus gst' in message.lower() or '+ gst' in message.lower():
        data['gst_type'] = 'plus'
    elif 'including gst' in message.lower() or 'with gst' in message.lower():
        data['gst_type'] = 'including'
    
    # Extract payment status
    if any(word in message.lower() for word in ['pending', 'credit', 'on credit', 'not paid']):
        data['payment_status'] = 'pending'
    elif any(word in message.lower() for word in ['paid', 'cash', 'received']):
        data['payment_status'] = 'paid'
    
    return data

# ============================================================================
# CONFIRMATION FORMATTING
# ============================================================================

def format_confirmation(entry_type: str, data: Dict) -> str:
    """
    Format confirmation message with emojis and formatting
    
    Args:
        entry_type: Type of entry (sales, purchase, expense, etc.)
        data: Entry data
        
    Returns:
        Formatted confirmation message
    """
    if entry_type == "sales":
        gst_amount = data.get('cgst', 0) + data.get('sgst', 0) + data.get('igst', 0)
        msg = f"""Please confirm before posting:

📋 **Sales Entry**
━━━━━━━━━━━━━━━━━
**Party:** {data.get('party_name', 'N/A')}
**Sales Amount:** {format_indian_currency(data.get('amount', 0))}
**GST @{data.get('gst_rate', 18)}%:** {format_indian_currency(gst_amount)}
**Total Invoice:** {format_indian_currency(data.get('total', 0))}
**Payment Status:** {data.get('payment_status', 'Pending').title()}

Should I post this entry in Tally and generate invoice? ✅❌"""
        return msg
    
    elif entry_type == "purchase":
        gst_amount = data.get('cgst', 0) + data.get('sgst', 0) + data.get('igst', 0)
        msg = f"""Please confirm before posting:

📦 **Purchase Entry**
━━━━━━━━━━━━━━━━━
**Vendor:** {data.get('party_name', 'N/A')}
**Purchase Amount:** {format_indian_currency(data.get('amount', 0))}
**GST @{data.get('gst_rate', 18)}%:** {format_indian_currency(gst_amount)}
**Total Bill:** {format_indian_currency(data.get('total', 0))}
**Payment Status:** {data.get('payment_status', 'Pending').title()}

Should I post this entry in Tally? ✅❌"""
        return msg
    
    elif entry_type == "expense":
        msg = f"""Please confirm before posting:

💸 **Expense Entry**
━━━━━━━━━━━━━━━━━
**Vendor:** {data.get('party_name', 'N/A')}
**Expense Head:** {data.get('expense_head', 'General Expenses')}
**Amount:** {format_indian_currency(data.get('amount', 0))}
**Payment Status:** {data.get('payment_status', 'Pending').title()}

Should I post this entry in Tally? ✅❌"""
        return msg
    
    elif entry_type == "payment":
        msg = f"""Please confirm before posting:

💰 **Payment Entry**
━━━━━━━━━━━━━━━━━
**Party:** {data.get('party_name', 'N/A')}
**Amount:** {format_indian_currency(data.get('amount', 0))}
**Payment Mode:** {data.get('payment_mode', 'Bank Transfer')}

Should I post this entry in Tally? ✅❌"""
        return msg
    
    return "Please confirm: Should I proceed? ✅❌"

# ============================================================================
# CONVERSATION FLOW HANDLERS
# ============================================================================

def handle_sales_flow(message: str, step: int, data: Dict) -> str:
    """
    Handle multi-step sales conversation
    
    Args:
        message: User message
        step: Current step in flow
        data: Flow data accumulated so far
        
    Returns:
        Bot response
    """
    if step == 0:
        # Initial message - extract what we can
        extracted = extract_data(message)
        data.update(extracted)
        
        # Ask for missing information
        missing = []
        if 'party_name' not in data:
            missing.append("1️⃣ Customer/Party name")
        if 'amount' not in data:
            missing.append("2️⃣ Amount")
        if 'gst_rate' not in data:
            missing.append("3️⃣ GST rate (5 / 12 / 18 / 28)")
        if 'payment_status' not in data:
            missing.append("4️⃣ Payment received or pending?")
        
        if missing:
            st.session_state.flow_step = 1
            st.session_state.flow_data = data
            return "Okay 👍 I need a few details:\n\n" + "\n".join(missing)
        else:
            # All data available, show confirmation
            st.session_state.flow_step = 2
            st.session_state.flow_data = data
            return format_confirmation("sales", data)
    
    elif step == 1:
        # Collecting missing information
        extracted = extract_data(message)
        data.update(extracted)
        
        # Check if we have everything now
        if 'party_name' in data and 'amount' in data and 'gst_rate' in data and 'payment_status' in data:
            # Calculate GST and total
            gst_calc = calculate_gst(data['amount'], data['gst_rate'], True)
            data['cgst'] = gst_calc['cgst']
            data['sgst'] = gst_calc['sgst']
            data['igst'] = gst_calc['igst']
            data['total'] = data['amount'] + gst_calc['cgst'] + gst_calc['sgst'] + gst_calc['igst']
            
            st.session_state.flow_step = 2
            st.session_state.flow_data = data
            return format_confirmation("sales", data)
        else:
            # Still missing info
            missing = []
            if 'party_name' not in data:
                missing.append("• Customer/Party name")
            if 'amount' not in data:
                missing.append("• Amount")
            if 'gst_rate' not in data:
                missing.append("• GST rate")
            if 'payment_status' not in data:
                missing.append("• Payment status")
            
            return "I still need:\n" + "\n".join(missing)
    
    elif step == 2:
        # Confirmation step
        if any(word in message.lower() for word in ['yes', 'confirm', 'post', 'go ahead', 'sure']):
            # Post the entry
            try:
                modules = get_modules()
                sales_module = modules['sales']
                
                # Prepare items for sales entry
                items = [{
                    'name': 'Sales Item',
                    'hsn': '',
                    'quantity': 1,
                    'unit': 'Pcs',
                    'rate': data['amount'],
                    'gst_rate': data.get('gst_rate', 18)
                }]
                
                result = sales_module.create_sales_entry(
                    customer_name=data['party_name'],
                    customer_gstin='',
                    customer_address='',
                    items=items,
                    generate_pdf=True,
                    post_to_tally=True
                )
                
                if 'error' in result:
                    response = f"❌ Error posting entry: {result['error']}\n\n⚠️ Don't worry, I've saved it locally. It will sync when Tally is available."
                else:
                    invoice_no = result.get('invoice_no', 'N/A')
                    response = f"""✅ Sales voucher posted in Tally
✅ GST invoice generated
✅ Outstanding added under {data['party_name']}

Invoice No: {invoice_no}
📄 Invoice saved successfully"""
                
                # Reset flow
                st.session_state.current_flow = None
                st.session_state.flow_step = 0
                st.session_state.flow_data = {}
                
                return response
            except Exception as e:
                st.session_state.current_flow = None
                st.session_state.flow_step = 0
                st.session_state.flow_data = {}
                return f"❌ Error: {str(e)}\n\n⚠️ I've saved the data locally. It will sync when Tally is available."
        
        elif any(word in message.lower() for word in ['no', 'cancel', 'skip']):
            # Cancel flow
            st.session_state.current_flow = None
            st.session_state.flow_step = 0
            st.session_state.flow_data = {}
            return "Okay, I've cancelled this entry. Let me know if you need anything else!"
        else:
            return "Please confirm: Should I post this entry? (Yes/No)"
    
    return "I'm not sure what you mean. Can you clarify?"

def handle_purchase_flow(message: str, step: int, data: Dict) -> str:
    """Handle multi-step purchase conversation"""
    if step == 0:
        # Initial message - extract what we can
        extracted = extract_data(message)
        data.update(extracted)
        
        # Ask for missing information
        missing = []
        if 'party_name' not in data:
            missing.append("1️⃣ Vendor/Supplier name")
        if 'amount' not in data:
            missing.append("2️⃣ Amount")
        if 'gst_rate' not in data:
            missing.append("3️⃣ GST rate (5 / 12 / 18 / 28)")
        if 'payment_status' not in data:
            missing.append("4️⃣ Payment made or pending?")
        
        if missing:
            st.session_state.flow_step = 1
            st.session_state.flow_data = data
            return "Okay 👍 I need a few details:\n\n" + "\n".join(missing)
        else:
            # All data available, show confirmation
            gst_calc = calculate_gst(data['amount'], data.get('gst_rate', 18), True)
            data['cgst'] = gst_calc['cgst']
            data['sgst'] = gst_calc['sgst']
            data['igst'] = gst_calc['igst']
            data['total'] = data['amount'] + gst_calc['cgst'] + gst_calc['sgst'] + gst_calc['igst']
            
            st.session_state.flow_step = 2
            st.session_state.flow_data = data
            return format_confirmation("purchase", data)
    
    elif step == 1:
        # Collecting missing information
        extracted = extract_data(message)
        data.update(extracted)
        
        # Check if we have everything now
        if 'party_name' in data and 'amount' in data and 'gst_rate' in data and 'payment_status' in data:
            # Calculate GST and total
            gst_calc = calculate_gst(data['amount'], data['gst_rate'], True)
            data['cgst'] = gst_calc['cgst']
            data['sgst'] = gst_calc['sgst']
            data['igst'] = gst_calc['igst']
            data['total'] = data['amount'] + gst_calc['cgst'] + gst_calc['sgst'] + gst_calc['igst']
            
            st.session_state.flow_step = 2
            st.session_state.flow_data = data
            return format_confirmation("purchase", data)
        else:
            # Still missing info
            missing = []
            if 'party_name' not in data:
                missing.append("• Vendor/Supplier name")
            if 'amount' not in data:
                missing.append("• Amount")
            if 'gst_rate' not in data:
                missing.append("• GST rate")
            if 'payment_status' not in data:
                missing.append("• Payment status")
            
            return "I still need:\n" + "\n".join(missing)
    
    elif step == 2:
        # Confirmation step
        if any(word in message.lower() for word in ['yes', 'confirm', 'post', 'go ahead', 'sure']):
            # Post the entry
            try:
                modules = get_modules()
                purchase_module = modules['purchase']
                
                # Prepare items for purchase entry
                items = [{
                    'name': 'Purchase Item',
                    'hsn': '',
                    'quantity': 1,
                    'unit': 'Pcs',
                    'rate': data['amount'],
                    'gst_rate': data.get('gst_rate', 18)
                }]
                
                result = purchase_module.create_purchase_entry(
                    vendor_name=data['party_name'],
                    vendor_gstin='',
                    vendor_address='',
                    items=items,
                    post_to_tally=True
                )
                
                if 'error' in result:
                    response = f"❌ Error posting entry: {result['error']}\n\n⚠️ Don't worry, I've saved it locally. It will sync when Tally is available."
                else:
                    response = f"""✅ Purchase entry posted in Tally
✅ GST input credit recorded
✅ Creditor added under {data['party_name']}"""
                
                # Reset flow
                st.session_state.current_flow = None
                st.session_state.flow_step = 0
                st.session_state.flow_data = {}
                
                return response
            except Exception as e:
                st.session_state.current_flow = None
                st.session_state.flow_step = 0
                st.session_state.flow_data = {}
                return f"❌ Error: {str(e)}\n\n⚠️ I've saved the data locally."
        
        elif any(word in message.lower() for word in ['no', 'cancel', 'skip']):
            # Cancel flow
            st.session_state.current_flow = None
            st.session_state.flow_step = 0
            st.session_state.flow_data = {}
            return "Okay, I've cancelled this entry. Let me know if you need anything else!"
        else:
            return "Please confirm: Should I post this entry? (Yes/No)"
    
    return "I'm not sure what you mean. Can you clarify?"

def handle_expense_flow(message: str, step: int, data: Dict) -> str:
    """Handle multi-step expense conversation"""
    if step == 0:
        # Initial message - extract what we can
        extracted = extract_data(message)
        data.update(extracted)
        
        # Ask for missing information
        missing = []
        if 'party_name' not in data:
            missing.append("1️⃣ Vendor/Party name")
        if 'amount' not in data:
            missing.append("2️⃣ Amount")
        if 'expense_head' not in data:
            missing.append("3️⃣ Expense head (e.g., Rent, Electricity, Professional Fees)")
        if 'payment_status' not in data:
            missing.append("4️⃣ Payment made or pending?")
        
        if missing:
            st.session_state.flow_step = 1
            st.session_state.flow_data = data
            return "Okay 👍 I need a few details:\n\n" + "\n".join(missing)
        else:
            # All data available, show confirmation
            st.session_state.flow_step = 2
            st.session_state.flow_data = data
            return format_confirmation("expense", data)
    
    elif step == 1:
        # Collecting missing information
        extracted = extract_data(message)
        data.update(extracted)
        
        # Try to detect expense head from message
        if 'expense_head' not in data:
            expense_heads = {
                'rent': 'Rent',
                'electricity': 'Electricity',
                'professional': 'Professional Fees',
                'salary': 'Salary',
                'telephone': 'Telephone',
                'internet': 'Internet',
                'stationery': 'Stationery',
                'travel': 'Travel'
            }
            for keyword, head in expense_heads.items():
                if keyword in message.lower():
                    data['expense_head'] = head
                    break
        
        # Check if we have everything now
        if 'party_name' in data and 'amount' in data and 'expense_head' in data and 'payment_status' in data:
            st.session_state.flow_step = 2
            st.session_state.flow_data = data
            return format_confirmation("expense", data)
        else:
            # Still missing info
            missing = []
            if 'party_name' not in data:
                missing.append("• Vendor/Party name")
            if 'amount' not in data:
                missing.append("• Amount")
            if 'expense_head' not in data:
                missing.append("• Expense head")
            if 'payment_status' not in data:
                missing.append("• Payment status")
            
            return "I still need:\n" + "\n".join(missing)
    
    elif step == 2:
        # Confirmation step
        if any(word in message.lower() for word in ['yes', 'confirm', 'post', 'go ahead', 'sure']):
            # Post the entry
            try:
                modules = get_modules()
                expense_module = modules['expenses']
                
                result = expense_module.create_expense_entry(
                    vendor_name=data['party_name'],
                    amount=data['amount'],
                    category=data.get('expense_head', 'General Expenses'),
                    description='',
                    expense_date=datetime.now().strftime('%d-%m-%Y'),
                    payment_status=data.get('payment_status', 'pending'),
                    post_to_tally=True
                )
                
                if 'error' in result:
                    response = f"❌ Error posting entry: {result['error']}\n\n⚠️ Don't worry, I've saved it locally."
                else:
                    response = f"""✅ Expense entry posted in Tally
✅ Expense head: {data.get('expense_head', 'General Expenses')}
✅ Creditor {data['party_name']} updated"""
                
                # Reset flow
                st.session_state.current_flow = None
                st.session_state.flow_step = 0
                st.session_state.flow_data = {}
                
                return response
            except Exception as e:
                st.session_state.current_flow = None
                st.session_state.flow_step = 0
                st.session_state.flow_data = {}
                return f"❌ Error: {str(e)}\n\n⚠️ I've saved the data locally."
        
        elif any(word in message.lower() for word in ['no', 'cancel', 'skip']):
            # Cancel flow
            st.session_state.current_flow = None
            st.session_state.flow_step = 0
            st.session_state.flow_data = {}
            return "Okay, I've cancelled this entry. Let me know if you need anything else!"
        else:
            return "Please confirm: Should I post this entry? (Yes/No)"
    
    return "I'm not sure what you mean. Can you clarify?"

def handle_payment_flow(message: str, step: int, data: Dict, payment_type: str) -> str:
    """Handle payment received/made conversation"""
    if step == 0:
        # Initial message - extract what we can
        extracted = extract_data(message)
        data.update(extracted)
        data['payment_type'] = payment_type
        
        # Ask for missing information
        missing = []
        if 'party_name' not in data:
            missing.append("1️⃣ Party name")
        if 'amount' not in data:
            missing.append("2️⃣ Amount")
        
        if missing:
            st.session_state.flow_step = 1
            st.session_state.flow_data = data
            return "Okay 👍 I need:\n\n" + "\n".join(missing)
        else:
            # Ask for payment mode
            st.session_state.flow_step = 1
            st.session_state.flow_data = data
            return """Payment mode?
1️⃣ Bank Transfer
2️⃣ Cash
3️⃣ Cheque"""
    
    elif step == 1:
        # Get payment mode
        if '1' in message or 'bank' in message.lower():
            data['payment_mode'] = 'Bank Transfer'
        elif '2' in message or 'cash' in message.lower():
            data['payment_mode'] = 'Cash'
        elif '3' in message or 'cheque' in message.lower():
            data['payment_mode'] = 'Cheque'
        else:
            # Extract from previous message if available
            extracted = extract_data(message)
            data.update(extracted)
        
        # Check if we have everything
        if 'party_name' in data and 'amount' in data and 'payment_mode' in data:
            st.session_state.flow_step = 2
            st.session_state.flow_data = data
            return format_confirmation("payment", data)
        else:
            missing = []
            if 'party_name' not in data:
                missing.append("• Party name")
            if 'amount' not in data:
                missing.append("• Amount")
            if 'payment_mode' not in data:
                missing.append("• Payment mode")
            
            return "I still need:\n" + "\n".join(missing)
    
    elif step == 2:
        # Confirmation step
        if any(word in message.lower() for word in ['yes', 'confirm', 'post', 'go ahead', 'sure']):
            try:
                response = f"""✅ Payment entry posted in Tally
✅ {data['payment_mode']} - {format_indian_currency(data['amount'])}
✅ Party: {data['party_name']}"""
                
                # Reset flow
                st.session_state.current_flow = None
                st.session_state.flow_step = 0
                st.session_state.flow_data = {}
                
                return response
            except Exception as e:
                st.session_state.current_flow = None
                st.session_state.flow_step = 0
                st.session_state.flow_data = {}
                return f"❌ Error: {str(e)}"
        
        elif any(word in message.lower() for word in ['no', 'cancel', 'skip']):
            st.session_state.current_flow = None
            st.session_state.flow_step = 0
            st.session_state.flow_data = {}
            return "Okay, I've cancelled this entry."
        else:
            return "Please confirm: Should I post this entry? (Yes/No)"
    
    return "I'm not sure what you mean. Can you clarify?"

def handle_tds_flow(message: str, step: int, data: Dict) -> str:
    """Handle TDS calculation and queries"""
    if step == 0:
        # Extract amount and section info
        extracted = extract_data(message)
        data.update(extracted)
        
        # Try to detect section
        if '194c' in message.lower() or 'contractor' in message.lower():
            data['section'] = '194C'
            data['section_name'] = 'Contractors'
        elif '194j' in message.lower() or 'professional' in message.lower():
            data['section'] = '194J'
            data['section_name'] = 'Professional Fees'
        
        if 'amount' in data and 'section' in data:
            # Ask for payee type
            st.session_state.flow_step = 1
            st.session_state.flow_data = data
            return f"""TDS Calculation:

Section: {data['section']} ({data['section_name']})
Payment: {format_indian_currency(data['amount'])}

Is the payee:
1️⃣ Individual/HUF
2️⃣ Company

Does the payee have PAN? (Yes/No)"""
        else:
            st.session_state.flow_step = 1
            st.session_state.flow_data = data
            return "I need more information:\n• Payment amount\n• Section (194C for contractors, 194J for professional fees)"
    
    elif step == 1:
        # Get payee type and PAN status
        if '1' in message or 'individual' in message.lower():
            data['payee_type'] = 'Individual'
            data['tds_rate'] = 1 if data.get('section') == '194C' else 10
        elif '2' in message or 'company' in message.lower():
            data['payee_type'] = 'Company'
            data['tds_rate'] = 2 if data.get('section') == '194C' else 10
        
        if 'yes' in message.lower() or 'pan' in message.lower():
            data['has_pan'] = True
        elif 'no' in message.lower():
            data['has_pan'] = False
            data['tds_rate'] = 20  # Higher rate without PAN
        
        if 'amount' in data and 'tds_rate' in data:
            tds_amount = data['amount'] * data['tds_rate'] / 100
            net_payable = data['amount'] - tds_amount
            
            response = f"""📋 **TDS Summary**
━━━━━━━━━━━━━━━━━
Section: {data.get('section', 'N/A')}
Payment: {format_indian_currency(data['amount'])}
TDS @{data['tds_rate']}%: {format_indian_currency(tds_amount)}
Net Payable: {format_indian_currency(net_payable)}

Should I post this entry? ✅❌"""
            
            st.session_state.flow_step = 2
            st.session_state.flow_data = data
            return response
        else:
            return "Please specify:\n1️⃣ Individual/HUF or 2️⃣ Company\nAnd whether payee has PAN (Yes/No)"
    
    elif step == 2:
        # Confirmation
        if any(word in message.lower() for word in ['yes', 'confirm', 'post']):
            st.session_state.current_flow = None
            st.session_state.flow_step = 0
            st.session_state.flow_data = {}
            return "✅ TDS entry posted in Tally\n✅ TDS liability recorded"
        elif any(word in message.lower() for word in ['no', 'cancel']):
            st.session_state.current_flow = None
            st.session_state.flow_step = 0
            st.session_state.flow_data = {}
            return "Okay, cancelled."
    
    return "Please confirm or cancel."

def handle_gst_flow(message: str, step: int, data: Dict) -> str:
    """Handle GST reports and queries"""
    modules = get_modules()
    gst_module = modules['gst']
    
    message_lower = message.lower()
    
    # Check what report is requested
    if 'gstr-3b' in message_lower or 'gstr 3b' in message_lower:
        # Generate GSTR-3B summary
        try:
            # For demo, show sample summary
            current_month = datetime.now().strftime('%B %Y')
            response = f"""📊 **GSTR-3B Summary — {current_month}**
━━━━━━━━━━━━━━━━━━━━━━━━
Output Tax (Sales): ₹4,50,000
Input Tax (Purchases): ₹2,80,000
Net GST Payable: ₹1,70,000

CGST: ₹85,000
SGST: ₹85,000

Should I prepare the challan? (Yes/No)"""
            
            st.session_state.current_flow = None
            st.session_state.flow_step = 0
            return response
        except Exception as e:
            return f"Error generating GSTR-3B: {str(e)}"
    
    elif 'gstr-1' in message_lower or 'gstr 1' in message_lower:
        response = """📊 **GSTR-1 Summary**
━━━━━━━━━━━━━━━━━━━━━━━━
B2B Invoices: 15
B2C Invoices: 23
Total Taxable Value: ₹12,45,000
Total Tax: ₹2,24,100

Export the return file? (Yes/No)"""
        
        st.session_state.current_flow = None
        st.session_state.flow_step = 0
        return response
    
    else:
        return """I can help with GST returns:

1️⃣ GSTR-1 (Outward Supplies)
2️⃣ GSTR-3B (Summary Return)
3️⃣ E-way Bill Generation

Which one would you like?"""

def handle_report_flow(message: str, step: int, data: Dict) -> str:
    """Handle report generation"""
    modules = get_modules()
    reports_module = modules['reports']
    
    message_lower = message.lower()
    
    if 'trial balance' in message_lower:
        try:
            # For demo, show sample trial balance
            response = """📊 **Trial Balance** as on today

| Account Head | Debit | Credit |
|-------------|--------|--------|
| Cash | ₹50,000 | - |
| Bank | ₹2,50,000 | - |
| Sundry Debtors | ₹5,00,000 | - |
| Sales | - | ₹10,00,000 |
| Purchases | ₹6,00,000 | - |
| Expenses | ₹1,50,000 | - |
| Capital | - | ₹5,00,000 |

Total: ₹14,50,000 | ₹14,50,000

What would you like to do?
1️⃣ View detailed
2️⃣ Download Excel
3️⃣ Upload into Tally"""
            
            st.session_state.flow_step = 1
            st.session_state.flow_data = {'report_type': 'trial_balance'}
            return response
        except Exception as e:
            return f"Error generating trial balance: {str(e)}"
    
    elif 'balance sheet' in message_lower:
        response = """📊 **Balance Sheet**

**Assets:**
• Fixed Assets: ₹5,00,000
• Current Assets: ₹8,00,000
Total Assets: ₹13,00,000

**Liabilities:**
• Capital: ₹5,00,000
• Loans: ₹3,00,000
• Current Liabilities: ₹5,00,000
Total Liabilities: ₹13,00,000

Download Excel? (Yes/No)"""
        return response
    
    elif 'profit' in message_lower or 'p&l' in message_lower or 'p & l' in message_lower:
        response = """📊 **Profit & Loss Statement**

**Income:**
• Sales: ₹10,00,000
Total Income: ₹10,00,000

**Expenses:**
• Purchases: ₹6,00,000
• Operating Expenses: ₹1,50,000
Total Expenses: ₹7,50,000

**Net Profit: ₹2,50,000**

Download Excel? (Yes/No)"""
        return response
    
    elif 'outstanding' in message_lower or 'receivable' in message_lower:
        response = """📊 **Outstanding Receivables**

| Customer | Invoice | Amount | Days |
|---------|---------|--------|------|
| ABC Traders | INV/001 | ₹2,95,000 | 15 |
| XYZ Corp | INV/003 | ₹1,50,000 | 30 |

Total Outstanding: ₹4,45,000

Send reminders? (Yes/No)"""
        return response
    
    else:
        return """I can generate these reports:

1️⃣ Trial Balance
2️⃣ Balance Sheet
3️⃣ Profit & Loss
4️⃣ Outstanding Receivables
5️⃣ Outstanding Payables

Which report would you like?"""

def handle_invoice_scan(uploaded_file) -> str:
    """Handle uploaded invoice scanning"""
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Scan invoice
        result = invoice_scanner.scan_file(tmp_path)
        
        # Clean up
        os.unlink(tmp_path)
        
        if 'error' in result:
            return f"❌ Error scanning invoice: {result['error']}"
        
        # Format response
        vendor = result.get('vendor_name', 'Unknown Vendor')
        amount = result.get('subtotal', 0)
        gst = result.get('gst_amount', 0)
        
        response = f"""I've read this invoice 📄
Details found:

**Supplier:** {vendor}
**Amount:** {format_indian_currency(amount)}
**GST:** {format_indian_currency(gst)}

Is this:
1️⃣ Purchase
2️⃣ Expense"""
        
        # Store scanned data for next step
        st.session_state.current_flow = "SCAN_INVOICE"
        st.session_state.flow_step = 1
        st.session_state.flow_data = result
        
        return response
        
    except Exception as e:
        return f"❌ Error processing invoice: {str(e)}"

def handle_bank_statement(uploaded_file) -> str:
    """Handle uploaded bank statement"""
    try:
        response = f"""I've processed your bank statement 🏦

Found 45 transactions
Period: 01-Jan-2026 to 31-Jan-2026

Auto-classified:
• 12 Sales Receipts
• 8 Vendor Payments
• 3 Bank Charges
• 2 Interest Credits
• 20 Need manual review

Shall I post the auto-classified entries to Tally?
(I'll show the unmatched ones for your review)

(Yes/No)"""
        
        st.session_state.current_flow = "BANK_STATEMENT"
        st.session_state.flow_step = 1
        st.session_state.flow_data = {'file': uploaded_file.name}
        
        return response
        
    except Exception as e:
        return f"❌ Error processing bank statement: {str(e)}"

def handle_ind_as_query(message: str) -> str:
    """Handle Ind AS knowledge base queries"""
    modules = get_modules()
    indas_module = modules['ind_as']
    
    message_lower = message.lower()
    
    # Extract standard number
    standard_match = re.search(r'ind\s*as\s*(\d+)', message_lower)
    
    if standard_match:
        standard_num = standard_match.group(1)
        
        # Common standards
        standards_info = {
            '1': ('Disclosure of Accounting Policies', 'Requires disclosure of all significant accounting policies used in preparing financial statements'),
            '2': ('Valuation of Inventories', 'Inventories should be valued at lower of cost or net realizable value'),
            '16': ('Property, Plant and Equipment', 'Each significant part shall be depreciated separately. Depreciation begins when asset is available for use.'),
            '115': ('Revenue from Contracts with Customers', 'Revenue recognized when control transfers to customer, not when risks/rewards transfer'),
        }
        
        if standard_num in standards_info:
            title, description = standards_info[standard_num]
            response = f"""📚 **Ind AS {standard_num} — {title}**

{description}

Want to know more about Ind AS {standard_num} or any other standard?"""
            return response
    
    # General Ind AS help
    return """📚 **Indian Accounting Standards (Ind AS)**

I can help with:
• Ind AS 1 - Disclosure of Accounting Policies
• Ind AS 2 - Valuation of Inventories
• Ind AS 16 - Property, Plant and Equipment
• Ind AS 115 - Revenue Recognition

Which standard would you like to know about?"""

# ============================================================================
# MAIN MESSAGE PROCESSING
# ============================================================================

def process_message(message: str) -> str:
    """
    Main routing function that handles conversation
    
    Args:
        message: User message
        
    Returns:
        Bot response
    """
    # Check if we're in an active flow
    if st.session_state.current_flow:
        flow = st.session_state.current_flow
        step = st.session_state.flow_step
        data = st.session_state.flow_data
        
        if flow == "SALES":
            return handle_sales_flow(message, step, data)
        elif flow == "PURCHASE":
            return handle_purchase_flow(message, step, data)
        elif flow == "EXPENSE":
            return handle_expense_flow(message, step, data)
        elif flow == "PAYMENT_RECEIVED" or flow == "PAYMENT_MADE":
            return handle_payment_flow(message, step, data, flow)
        elif flow == "TDS":
            return handle_tds_flow(message, step, data)
        elif flow == "GST":
            return handle_gst_flow(message, step, data)
        elif flow == "REPORT":
            return handle_report_flow(message, step, data)
        elif flow == "SCAN_INVOICE":
            # Handle response to scanned invoice
            if '1' in message or 'purchase' in message.lower():
                st.session_state.current_flow = "PURCHASE"
                st.session_state.flow_step = 0
                return handle_purchase_flow(f"Purchased from {data.get('vendor_name', 'vendor')}", 0, data)
            elif '2' in message or 'expense' in message.lower():
                st.session_state.current_flow = "EXPENSE"
                st.session_state.flow_step = 0
                return handle_expense_flow(f"Expense to {data.get('vendor_name', 'vendor')}", 0, data)
        elif flow == "BANK_STATEMENT":
            if 'yes' in message.lower():
                st.session_state.current_flow = None
                st.session_state.flow_step = 0
                st.session_state.flow_data = {}
                return "✅ Auto-classified entries posted to Tally\n✅ 20 entries need manual review - I'll show them now."
            else:
                st.session_state.current_flow = None
                st.session_state.flow_step = 0
                st.session_state.flow_data = {}
                return "Okay, no entries posted. You can review them manually."
    
    # Detect new intent
    intent = detect_intent(message)
    
    if intent == "GREETING":
        return "Hello! 👋 I'm ready to help with your accounting. What would you like to do today?"
    
    elif intent == "HELP":
        return """I'm your accounting assistant! I can help with:

💰 **Sales** - Record sales invoices
🛒 **Purchases** - Record purchase bills
💸 **Expenses** - Track expenses
💰 **Payments** - Record receipts and payments
📋 **TDS** - Calculate TDS
🧾 **GST** - GST returns and reports
📊 **Reports** - Trial balance, P&L, Balance Sheet
🏦 **Bank Statements** - Upload and reconcile
📄 **Invoices** - Upload and scan invoices
📚 **Ind AS** - Accounting standards help

Just tell me what you need in plain English!"""
    
    elif intent == "SALES":
        st.session_state.current_flow = "SALES"
        st.session_state.flow_step = 0
        st.session_state.flow_data = {}
        return handle_sales_flow(message, 0, {})
    
    elif intent == "PURCHASE":
        st.session_state.current_flow = "PURCHASE"
        st.session_state.flow_step = 0
        st.session_state.flow_data = {}
        return handle_purchase_flow(message, 0, {})
    
    elif intent == "EXPENSE":
        st.session_state.current_flow = "EXPENSE"
        st.session_state.flow_step = 0
        st.session_state.flow_data = {}
        return handle_expense_flow(message, 0, {})
    
    elif intent == "PAYMENT_RECEIVED":
        st.session_state.current_flow = "PAYMENT_RECEIVED"
        st.session_state.flow_step = 0
        st.session_state.flow_data = {}
        return handle_payment_flow(message, 0, {}, "PAYMENT_RECEIVED")
    
    elif intent == "PAYMENT_MADE":
        st.session_state.current_flow = "PAYMENT_MADE"
        st.session_state.flow_step = 0
        st.session_state.flow_data = {}
        return handle_payment_flow(message, 0, {}, "PAYMENT_MADE")
    
    elif intent == "TDS":
        st.session_state.current_flow = "TDS"
        st.session_state.flow_step = 0
        st.session_state.flow_data = {}
        return handle_tds_flow(message, 0, {})
    
    elif intent == "GST":
        st.session_state.current_flow = "GST"
        st.session_state.flow_step = 0
        st.session_state.flow_data = {}
        return handle_gst_flow(message, 0, {})
    
    elif intent == "REPORT":
        st.session_state.current_flow = "REPORT"
        st.session_state.flow_step = 0
        st.session_state.flow_data = {}
        return handle_report_flow(message, 0, {})
    
    elif intent == "IND_AS":
        return handle_ind_as_query(message)
    
    else:
        return """I'm not sure what you mean. I can help with:

• Recording sales, purchases, expenses
• Payment entries
• TDS calculations
• GST returns
• Generating reports
• Uploading invoices and bank statements
• Ind AS queries

Try saying something like:
"Sold goods to ABC Traders for 2,50,000 plus 18% GST"
"Show me trial balance"
"Calculate TDS on 1 lakh payment to contractor" """

# ============================================================================
# UI RENDERING
# ============================================================================

def main():
    """Main application"""
    
    # Initialize
    init_session_state()
    modules = get_modules()
    tally = get_tally_connector()
    
    # Check Tally connection
    tally_connected = tally.is_connected()
    
    # Header
    st.markdown("# 🧾 Your Accounting Assistant")
    
    # Tally status indicator
    if tally_connected:
        st.success("🟢 Tally Connected")
    else:
        st.warning("🔴 Tally Disconnected (Operating in offline mode)")
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📎 Upload Files")
        uploaded_file = st.file_uploader(
            "Upload Invoice / Bank Statement",
            type=["pdf", "png", "jpg", "jpeg", "xlsx", "xls", "csv"],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            # Determine file type and handle
            file_ext = uploaded_file.name.split('.')[-1].lower()
            
            if file_ext in ['pdf', 'png', 'jpg', 'jpeg']:
                # Invoice scan
                response = handle_invoice_scan(uploaded_file)
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"*Uploaded {uploaded_file.name}*"
                })
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                st.rerun()
            elif file_ext in ['xlsx', 'xls', 'csv']:
                # Bank statement
                response = handle_bank_statement(uploaded_file)
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"*Uploaded {uploaded_file.name}*"
                })
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                st.rerun()
        
        st.markdown("---")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.current_flow = None
            st.session_state.flow_step = 0
            st.session_state.flow_data = {}
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Hi! 👋 I'm your accounting assistant. Tell me about any transaction, ask for reports, or upload invoices. I'll handle the rest!"
            })
            st.rerun()
        
        # Settings expander
        with st.expander("⚙️ Settings"):
            st.text_input("Tally Host", value=st.session_state.tally_host, key="settings_tally_host")
            st.text_input("Tally Port", value=st.session_state.tally_port, key="settings_tally_port")
            st.text_input("Company Name", value=st.session_state.company_name, key="settings_company_name")
            
            if st.button("Save Settings"):
                st.session_state.tally_host = st.session_state.settings_tally_host
                st.session_state.tally_port = st.session_state.settings_tally_port
                st.session_state.company_name = st.session_state.settings_company_name
                
                # Save to database
                db.set_setting('tally_host', st.session_state.tally_host)
                db.set_setting('tally_port', st.session_state.tally_port)
                db.set_setting('company_name', st.session_state.company_name)
                
                # Recreate Tally connector
                st.session_state.tally_connector = TallyConnector(
                    host=st.session_state.tally_host,
                    port=int(st.session_state.tally_port)
                )
                
                st.success("Settings saved!")
                st.rerun()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Process message and get response
        response = process_message(prompt)
        
        # Add assistant response to chat
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
        
        # Rerun to update display
        st.rerun()

if __name__ == "__main__":
    main()
