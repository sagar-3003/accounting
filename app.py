"""
Main Streamlit Application for AI Accounting Chatbot
Entry point with sidebar navigation and all module pages
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd

# Import configuration and core modules
from config import Config, SIDEBAR_PAGES, COMPANY_INFO, FINANCIAL_YEAR, DEFAULT_GST_STATE
from database.db import db
from tally.connection import tally_connector
from utils.helpers import format_indian_currency, format_date_indian, get_financial_year, get_quarter

# Import module managers
from modules.sales import SalesModule
from modules.purchase import PurchaseModule
from modules.expenses import ExpensesModule
from modules.bank_statement import BankStatementModule
from modules.tds import TDSModule
from modules.gst import GSTModule
from modules.reports import ReportsModule
from modules.ind_as import IndASModule

# Set page configuration
st.set_page_config(
    page_title="AI Accounting Chatbot",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for all modules
def init_session_state():
    """Initialize session state variables for all modules"""
    # Sales module state
    if 'sales_messages' not in st.session_state:
        st.session_state.sales_messages = []
    if 'sales_step' not in st.session_state:
        st.session_state.sales_step = 'start'
    if 'sales_data' not in st.session_state:
        st.session_state.sales_data = {}
    
    # Purchase module state
    if 'purchase_messages' not in st.session_state:
        st.session_state.purchase_messages = []
    if 'purchase_step' not in st.session_state:
        st.session_state.purchase_step = 'start'
    if 'purchase_data' not in st.session_state:
        st.session_state.purchase_data = {}
    
    # Expenses module state
    if 'expenses_messages' not in st.session_state:
        st.session_state.expenses_messages = []
    if 'expenses_step' not in st.session_state:
        st.session_state.expenses_step = 'start'
    if 'expenses_data' not in st.session_state:
        st.session_state.expenses_data = {}
    
    # Bank statement module state
    if 'bank_messages' not in st.session_state:
        st.session_state.bank_messages = []
    if 'bank_step' not in st.session_state:
        st.session_state.bank_step = 'start'
    if 'bank_data' not in st.session_state:
        st.session_state.bank_data = {}
    
    # TDS module state
    if 'tds_messages' not in st.session_state:
        st.session_state.tds_messages = []
    if 'tds_step' not in st.session_state:
        st.session_state.tds_step = 'start'
    if 'tds_data' not in st.session_state:
        st.session_state.tds_data = {}
    
    # GST module state
    if 'gst_selected_option' not in st.session_state:
        st.session_state.gst_selected_option = None
    
    # Settings
    if 'tally_host' not in st.session_state:
        st.session_state.tally_host = db.get_setting('tally_host') or 'localhost'
    if 'tally_port' not in st.session_state:
        st.session_state.tally_port = db.get_setting('tally_port') or '9000'
    if 'company_name' not in st.session_state:
        st.session_state.company_name = db.get_setting('company_name') or ''
    if 'financial_year' not in st.session_state:
        st.session_state.financial_year = db.get_setting('financial_year') or FINANCIAL_YEAR
    if 'default_gst_state' not in st.session_state:
        st.session_state.default_gst_state = db.get_setting('default_gst_state') or DEFAULT_GST_STATE

# Initialize module instances
def get_modules():
    """Get or create module instances"""
    if 'modules' not in st.session_state:
        st.session_state.modules = {
            'sales': SalesModule(),
            'purchase': PurchaseModule(),
            'expenses': ExpensesModule(),
            'bank_statement': BankStatementModule(),
            'tds': TDSModule(),
            'gst': GSTModule(),
            'reports': ReportsModule(),
            'ind_as': IndASModule()
        }
    return st.session_state.modules


def show_home_page():
    """Display the Home/Dashboard page"""
    st.title("🏠 AI Accounting Chatbot Dashboard")
    
    # Tally connection status
    st.subheader("Tally Connection Status")
    try:
        tally_status = tally_connector.test_connection()
        if tally_status['connected']:
            st.success(f"🟢 Connected to Tally at {tally_status['url']}")
            if tally_status['company']:
                st.info(f"📊 Active Company: **{tally_status['company']}**")
        else:
            st.warning(f"🔴 Disconnected - {tally_status.get('error', 'Unable to connect to Tally')}")
            st.info("💡 You can still use the app in offline mode. Data will be stored locally.")
    except Exception as e:
        st.error(f"❌ Error checking Tally connection: {str(e)}")
    
    st.divider()
    
    # Quick stats
    st.subheader("Quick Stats")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Today's sales count
        today = datetime.now().strftime("%Y-%m-%d")
        sales_today = len([s for s in db.get_sales(limit=100) if s.get('date', '').startswith(today)])
        st.metric("Today's Sales", sales_today)
    
    with col2:
        # Pending payments (expenses)
        pending_expenses = db.get_expenses(status='pending')
        pending_amount = sum(e.get('amount', 0) for e in pending_expenses)
        st.metric("Pending Payments", format_indian_currency(pending_amount))
    
    with col3:
        # Overdue creditors
        creditors = db.get_creditors(status='pending')
        overdue_count = 0
        today_date = datetime.now().date()
        for creditor in creditors:
            due_date_str = creditor.get('due_date', '')
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    if due_date < today_date:
                        overdue_count += 1
                except:
                    pass
        st.metric("Overdue Creditors", overdue_count)
    
    st.divider()
    
    # Recent activity
    st.subheader("Recent Activity")
    
    # Get recent sales
    recent_sales = db.get_sales(limit=5)
    if recent_sales:
        st.write("**Recent Sales:**")
        sales_df = pd.DataFrame(recent_sales)
        if not sales_df.empty:
            display_cols = ['invoice_no', 'customer_name', 'total', 'date']
            existing_cols = [col for col in display_cols if col in sales_df.columns]
            if existing_cols:
                st.dataframe(sales_df[existing_cols], use_container_width=True)
    
    # Get recent expenses
    recent_expenses = db.get_expenses(limit=5)
    if recent_expenses:
        st.write("**Recent Expenses:**")
        expenses_df = pd.DataFrame(recent_expenses)
        if not expenses_df.empty:
            display_cols = ['vendor_name', 'amount', 'category', 'payment_status', 'date']
            existing_cols = [col for col in display_cols if col in expenses_df.columns]
            if existing_cols:
                st.dataframe(expenses_df[existing_cols], use_container_width=True)


def show_sales_page():
    """Display the Sales page with chat interface"""
    modules = get_modules()
    sales_module = modules['sales']
    
    st.title("💰 Sales Entry")
    
    # Chat interface
    st.subheader("Sales Assistant")
    
    # Display chat messages
    for message in st.session_state.sales_messages:
        with st.chat_message(message['role']):
            st.write(message['content'])
    
    # Start conversation
    if st.session_state.sales_step == 'start':
        st.session_state.sales_messages.append({
            'role': 'assistant',
            'content': "Hello! I'll help you create a sales invoice. Let's start with the customer name. What is the customer's name?"
        })
        st.session_state.sales_step = 'customer_name'
        st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Your response..."):
        # Add user message
        st.session_state.sales_messages.append({
            'role': 'user',
            'content': prompt
        })
        
        # Process based on current step
        if st.session_state.sales_step == 'customer_name':
            st.session_state.sales_data['customer_name'] = prompt
            st.session_state.sales_messages.append({
                'role': 'assistant',
                'content': f"Great! Customer name: {prompt}. Now, please provide the customer's GSTIN (or type 'skip' if not applicable)."
            })
            st.session_state.sales_step = 'customer_gstin'
        
        elif st.session_state.sales_step == 'customer_gstin':
            if prompt.lower() == 'skip':
                st.session_state.sales_data['customer_gstin'] = ''
                st.session_state.sales_data['customer_address'] = ''
            else:
                st.session_state.sales_data['customer_gstin'] = prompt
                st.session_state.sales_data['customer_address'] = ''
            
            st.session_state.sales_messages.append({
                'role': 'assistant',
                'content': "Now let's add items. Please provide item details in format: 'Item Name, Quantity, Rate, HSN Code' (e.g., 'Laptop, 2, 50000, 8471'). Type 'done' when finished adding items."
            })
            st.session_state.sales_step = 'items'
            st.session_state.sales_data['items'] = []
        
        elif st.session_state.sales_step == 'items':
            if prompt.lower() == 'done':
                if len(st.session_state.sales_data.get('items', [])) > 0:
                    st.session_state.sales_messages.append({
                        'role': 'assistant',
                        'content': "Is this an intra-state transaction (within same state) or inter-state? Type 'intra' or 'inter'."
                    })
                    st.session_state.sales_step = 'gst_type'
                else:
                    st.session_state.sales_messages.append({
                        'role': 'assistant',
                        'content': "Please add at least one item before proceeding."
                    })
            else:
                # Parse item
                try:
                    parts = [p.strip() for p in prompt.split(',')]
                    if len(parts) >= 3:
                        item = {
                            'name': parts[0],
                            'quantity': float(parts[1]),
                            'rate': float(parts[2]),
                            'hsn': parts[3] if len(parts) > 3 else '',
                            'unit': 'Pcs',
                            'gst_rate': 18  # Default GST rate
                        }
                        st.session_state.sales_data['items'].append(item)
                        st.session_state.sales_messages.append({
                            'role': 'assistant',
                            'content': f"Item added: {item['name']} - Qty: {item['quantity']}, Rate: {format_indian_currency(item['rate'])}. Add another item or type 'done' to proceed."
                        })
                    else:
                        st.session_state.sales_messages.append({
                            'role': 'assistant',
                            'content': "Invalid format. Please use: 'Item Name, Quantity, Rate, HSN Code'"
                        })
                except Exception as e:
                    st.session_state.sales_messages.append({
                        'role': 'assistant',
                        'content': f"Error parsing item: {str(e)}. Please try again."
                    })
        
        elif st.session_state.sales_step == 'gst_type':
            gst_type = prompt.lower()
            st.session_state.sales_data['is_intra_state'] = gst_type == 'intra'
            st.session_state.sales_messages.append({
                'role': 'assistant',
                'content': f"GST type set to: {'Intra-state (CGST+SGST)' if gst_type == 'intra' else 'Inter-state (IGST)'}. What is the invoice date? (DD-MM-YYYY or type 'today')"
            })
            st.session_state.sales_step = 'date'
        
        elif st.session_state.sales_step == 'date':
            if prompt.lower() == 'today':
                invoice_date = datetime.now().strftime("%d-%m-%Y")
            else:
                invoice_date = prompt
            st.session_state.sales_data['date'] = invoice_date
            
            # Generate invoice
            try:
                result = sales_module.create_sales_entry(
                    customer_name=st.session_state.sales_data['customer_name'],
                    customer_gstin=st.session_state.sales_data.get('customer_gstin', ''),
                    customer_address=st.session_state.sales_data.get('customer_address', ''),
                    items=st.session_state.sales_data['items'],
                    invoice_date=invoice_date,
                    generate_pdf=True,
                    post_to_tally=False  # Default to not posting to Tally
                )
                
                if 'error' in result:
                    st.session_state.sales_messages.append({
                        'role': 'assistant',
                        'content': f"❌ Error: {result['error']}"
                    })
                else:
                    invoice_summary = f"""
✅ Invoice created successfully!

**Invoice Number:** {result.get('invoice_no', 'N/A')}
**Customer:** {result.get('customer_name', 'N/A')}
**Subtotal:** {format_indian_currency(result.get('subtotal', 0))}
**CGST:** {format_indian_currency(result.get('cgst', 0))}
**SGST:** {format_indian_currency(result.get('sgst', 0))}
**IGST:** {format_indian_currency(result.get('igst', 0))}
**Total:** {format_indian_currency(result.get('total', 0))}

Invoice saved to database. Type 'new' to create another invoice.
                    """
                    st.session_state.sales_messages.append({
                        'role': 'assistant',
                        'content': invoice_summary
                    })
                    
                    # Show download button if PDF generated
                    if result.get('pdf_path'):
                        try:
                            with open(result['pdf_path'], 'rb') as f:
                                st.download_button(
                                    label="📥 Download Invoice PDF",
                                    data=f.read(),
                                    file_name=f"{result.get('invoice_no', 'invoice').replace('/', '_')}.pdf",
                                    mime="application/pdf"
                                )
                        except:
                            pass
                    
                    st.session_state.sales_step = 'done'
            except Exception as e:
                st.session_state.sales_messages.append({
                    'role': 'assistant',
                    'content': f"❌ Error creating invoice: {str(e)}"
                })
        
        elif st.session_state.sales_step == 'done':
            if prompt.lower() == 'new':
                # Reset for new invoice
                st.session_state.sales_data = {}
                st.session_state.sales_step = 'customer_name'
                st.session_state.sales_messages.append({
                    'role': 'assistant',
                    'content': "Let's create a new invoice! What is the customer's name?"
                })
        
        st.rerun()
    
    # Sales Register
    st.divider()
    st.subheader("Sales Register")
    sales_records = db.get_sales(limit=20)
    if sales_records:
        sales_df = pd.DataFrame(sales_records)
        display_cols = ['invoice_no', 'customer_name', 'subtotal', 'cgst', 'sgst', 'igst', 'total', 'date']
        existing_cols = [col for col in display_cols if col in sales_df.columns]
        if existing_cols:
            st.dataframe(sales_df[existing_cols], use_container_width=True)
    else:
        st.info("No sales records found.")


def show_purchases_page():
    """Display the Purchases page with file upload"""
    modules = get_modules()
    purchase_module = modules['purchase']
    
    st.title("🛒 Purchase Entry")
    
    st.subheader("Upload Purchase Invoice")
    uploaded_file = st.file_uploader(
        "Upload invoice image or PDF",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        help="Upload a purchase invoice for OCR extraction"
    )
    
    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        # In a real implementation, would call purchase_module.process_invoice()
        st.info("📄 OCR extraction would happen here. For now, please enter data manually.")
    
    # Manual entry form
    st.subheader("Manual Purchase Entry")
    
    with st.form("purchase_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            vendor_name = st.text_input("Vendor Name")
            vendor_gstin = st.text_input("Vendor GSTIN (optional)")
            invoice_no = st.text_input("Invoice Number")
        
        with col2:
            invoice_date = st.date_input("Invoice Date", value=date.today())
            total_amount = st.number_input("Total Amount", min_value=0.0, step=0.01)
        
        submit_button = st.form_submit_button("Save Purchase")
        
        if submit_button and vendor_name and invoice_no:
            # Basic entry - in real implementation would use purchase_module
            try:
                # Create a simple purchase record
                db.insert_purchase(
                    invoice_no=invoice_no,
                    vendor_name=vendor_name,
                    vendor_gstin=vendor_gstin,
                    items=[],
                    subtotal=total_amount,
                    cgst=0,
                    sgst=0,
                    igst=0,
                    total=total_amount,
                    date=invoice_date.strftime("%Y-%m-%d")
                )
                st.success("✅ Purchase entry saved!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Purchase Register
    st.divider()
    st.subheader("Purchase Register")
    purchase_records = db.get_purchases(limit=20)
    if purchase_records:
        purchase_df = pd.DataFrame(purchase_records)
        display_cols = ['invoice_no', 'vendor_name', 'subtotal', 'cgst', 'sgst', 'igst', 'total', 'date']
        existing_cols = [col for col in display_cols if col in purchase_df.columns]
        if existing_cols:
            st.dataframe(purchase_df[existing_cols], use_container_width=True)
    else:
        st.info("No purchase records found.")


def show_expenses_page():
    """Display the Expenses page"""
    modules = get_modules()
    expenses_module = modules['expenses']
    
    st.title("💸 Expenses Management")
    
    # File upload for expense invoices
    st.subheader("Upload Expense Invoice")
    uploaded_file = st.file_uploader(
        "Upload expense invoice",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        key='expense_upload'
    )
    
    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")
        st.info("📄 OCR extraction would happen here. For now, please enter data manually.")
    
    # Manual expense entry
    st.subheader("Add Expense")
    
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            vendor_name = st.text_input("Vendor/Party Name")
            amount = st.number_input("Amount", min_value=0.0, step=0.01)
            category = st.selectbox("Category", [
                "Office Rent", "Utilities", "Salaries", "Professional Fees",
                "Travel", "Supplies", "Marketing", "Other"
            ])
        
        with col2:
            expense_date = st.date_input("Expense Date", value=date.today())
            due_date = st.date_input("Due Date", value=date.today())
            description = st.text_area("Description")
        
        submit_button = st.form_submit_button("Save Expense")
        
        if submit_button and vendor_name and amount > 0:
            try:
                db.insert_expense(
                    vendor_name=vendor_name,
                    amount=amount,
                    category=category,
                    description=description,
                    date=expense_date.strftime("%Y-%m-%d"),
                    due_date=due_date.strftime("%Y-%m-%d")
                )
                st.success("✅ Expense saved!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Expense list and aging
    st.divider()
    st.subheader("Expense Register")
    
    tab1, tab2 = st.tabs(["All Expenses", "Creditor Aging"])
    
    with tab1:
        expenses = db.get_expenses(limit=50)
        if expenses:
            expenses_df = pd.DataFrame(expenses)
            display_cols = ['vendor_name', 'amount', 'category', 'payment_status', 'date', 'due_date']
            existing_cols = [col for col in display_cols if col in expenses_df.columns]
            if existing_cols:
                st.dataframe(expenses_df[existing_cols], use_container_width=True)
        else:
            st.info("No expense records found.")
    
    with tab2:
        # Show overdue expenses
        pending_expenses = db.get_expenses(status='pending')
        if pending_expenses:
            today_date = datetime.now().date()
            overdue = []
            
            for expense in pending_expenses:
                due_date_str = expense.get('due_date', '')
                if due_date_str:
                    try:
                        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                        if due_date < today_date:
                            days_overdue = (today_date - due_date).days
                            expense['days_overdue'] = days_overdue
                            overdue.append(expense)
                    except:
                        pass
            
            if overdue:
                st.warning(f"⚠️ {len(overdue)} overdue payment(s) found!")
                overdue_df = pd.DataFrame(overdue)
                display_cols = ['vendor_name', 'amount', 'due_date', 'days_overdue']
                existing_cols = [col for col in display_cols if col in overdue_df.columns]
                if existing_cols:
                    st.dataframe(overdue_df[existing_cols], use_container_width=True)
            else:
                st.success("✅ No overdue payments")
        else:
            st.info("No pending expenses")


def show_bank_statement_page():
    """Display the Bank Statement page"""
    modules = get_modules()
    bank_module = modules['bank_statement']
    
    st.title("🏦 Bank Statement Import")
    
    st.subheader("Upload Bank Statement")
    uploaded_file = st.file_uploader(
        "Upload bank statement (PDF or Excel)",
        type=['pdf', 'xlsx', 'xls', 'csv'],
        key='bank_upload'
    )
    
    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        # In real implementation, would parse the file
        st.info("📄 Bank statement parsing would happen here.")
        
        # Sample data for demonstration
        sample_data = {
            'date': ['2025-01-15', '2025-01-16', '2025-01-17'],
            'description': ['Payment received', 'Salary payment', 'Electricity bill'],
            'debit': [0, 50000, 1500],
            'credit': [25000, 0, 0],
            'balance': [125000, 75000, 73500]
        }
        df = pd.DataFrame(sample_data)
        
        st.subheader("Parsed Transactions")
        st.info("Review and edit transactions before posting to Tally")
        edited_df = st.data_editor(df, use_container_width=True)
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("✅ Confirm & Post"):
                st.success("Transactions posted to database!")
                # In real implementation: bank_module.post_transactions(edited_df)
    
    # Bank transactions register
    st.divider()
    st.subheader("Bank Transactions Register")
    transactions = db.get_bank_transactions(limit=20)
    if transactions:
        trans_df = pd.DataFrame(transactions)
        display_cols = ['date', 'description', 'debit', 'credit', 'balance']
        existing_cols = [col for col in display_cols if col in trans_df.columns]
        if existing_cols:
            st.dataframe(trans_df[existing_cols], use_container_width=True)
    else:
        st.info("No bank transactions found.")


def show_tds_page():
    """Display the TDS page with chat interface"""
    modules = get_modules()
    tds_module = modules['tds']
    
    st.title("📋 TDS Management")
    
    # Chat interface for TDS entry
    st.subheader("TDS Entry Assistant")
    
    # Display chat messages
    for message in st.session_state.tds_messages:
        with st.chat_message(message['role']):
            st.write(message['content'])
    
    # Start conversation
    if st.session_state.tds_step == 'start':
        st.session_state.tds_messages.append({
            'role': 'assistant',
            'content': "Hello! I'll help you record a TDS entry. Let's start. What is the party/payee name?"
        })
        st.session_state.tds_step = 'party_name'
        st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Your response...", key='tds_input'):
        # Add user message
        st.session_state.tds_messages.append({
            'role': 'user',
            'content': prompt
        })
        
        # Process based on current step
        if st.session_state.tds_step == 'party_name':
            st.session_state.tds_data['party_name'] = prompt
            st.session_state.tds_messages.append({
                'role': 'assistant',
                'content': f"Party name: {prompt}. What is their PAN number?"
            })
            st.session_state.tds_step = 'party_pan'
        
        elif st.session_state.tds_step == 'party_pan':
            st.session_state.tds_data['party_pan'] = prompt
            st.session_state.tds_messages.append({
                'role': 'assistant',
                'content': "What is the TDS section? (e.g., 194C for Contractors, 194J for Professional Fees, 194A for Interest)"
            })
            st.session_state.tds_step = 'section'
        
        elif st.session_state.tds_step == 'section':
            st.session_state.tds_data['section'] = prompt
            st.session_state.tds_messages.append({
                'role': 'assistant',
                'content': "What is the gross payment amount?"
            })
            st.session_state.tds_step = 'amount'
        
        elif st.session_state.tds_step == 'amount':
            try:
                amount = float(prompt)
                st.session_state.tds_data['payment_amount'] = amount
                
                # Calculate TDS based on section (simplified)
                tds_rates = {
                    '194C': 1.0,  # Contractors
                    '194J': 10.0,  # Professional fees
                    '194A': 10.0,  # Interest
                    '194H': 5.0,   # Commission
                }
                section = st.session_state.tds_data.get('section', '194J')
                tds_rate = tds_rates.get(section, 10.0)
                tds_amount = amount * tds_rate / 100
                net_payable = amount - tds_amount
                
                st.session_state.tds_data['tds_rate'] = tds_rate
                st.session_state.tds_data['tds_amount'] = tds_amount
                st.session_state.tds_data['net_payable'] = net_payable
                
                # Save to database
                try:
                    today = datetime.now()
                    db.insert_tds_entry(
                        party_name=st.session_state.tds_data['party_name'],
                        party_pan=st.session_state.tds_data['party_pan'],
                        section=section,
                        payment_amount=amount,
                        tds_rate=tds_rate,
                        tds_amount=tds_amount,
                        net_payable=net_payable,
                        date=today.strftime("%Y-%m-%d"),
                        quarter=get_quarter(today),
                        financial_year=get_financial_year(today)
                    )
                    
                    summary = f"""
✅ TDS entry recorded successfully!

**Party:** {st.session_state.tds_data['party_name']}
**PAN:** {st.session_state.tds_data['party_pan']}
**Section:** {section}
**Gross Amount:** {format_indian_currency(amount)}
**TDS Rate:** {tds_rate}%
**TDS Amount:** {format_indian_currency(tds_amount)}
**Net Payable:** {format_indian_currency(net_payable)}

Type 'new' to record another TDS entry.
                    """
                    st.session_state.tds_messages.append({
                        'role': 'assistant',
                        'content': summary
                    })
                    st.session_state.tds_step = 'done'
                except Exception as e:
                    st.session_state.tds_messages.append({
                        'role': 'assistant',
                        'content': f"❌ Error saving TDS entry: {str(e)}"
                    })
            except ValueError:
                st.session_state.tds_messages.append({
                    'role': 'assistant',
                    'content': "Invalid amount. Please enter a numeric value."
                })
        
        elif st.session_state.tds_step == 'done':
            if prompt.lower() == 'new':
                # Reset for new entry
                st.session_state.tds_data = {}
                st.session_state.tds_step = 'party_name'
                st.session_state.tds_messages.append({
                    'role': 'assistant',
                    'content': "Let's record a new TDS entry! What is the party/payee name?"
                })
        
        st.rerun()
    
    # TDS Register
    st.divider()
    st.subheader("TDS Register")
    
    col1, col2 = st.columns(2)
    with col1:
        quarter_filter = st.selectbox("Filter by Quarter", ["All", "Q1", "Q2", "Q3", "Q4"])
    with col2:
        fy_filter = st.text_input("Financial Year", value=FINANCIAL_YEAR)
    
    tds_entries = db.get_tds_entries(
        quarter=quarter_filter if quarter_filter != "All" else None,
        financial_year=fy_filter
    )
    
    if tds_entries:
        tds_df = pd.DataFrame(tds_entries)
        display_cols = ['party_name', 'party_pan', 'section', 'payment_amount', 'tds_amount', 'net_payable', 'date']
        existing_cols = [col for col in display_cols if col in tds_df.columns]
        if existing_cols:
            st.dataframe(tds_df[existing_cols], use_container_width=True)
        
        # Quarterly summary
        if not tds_df.empty and 'tds_amount' in tds_df.columns:
            total_tds = tds_df['tds_amount'].sum()
            st.metric("Total TDS Deducted", format_indian_currency(total_tds))
    else:
        st.info("No TDS entries found.")


def show_gst_page():
    """Display the GST page"""
    modules = get_modules()
    gst_module = modules['gst']
    
    st.title("🧾 GST Management")
    
    # Sub-options
    option = st.radio(
        "Select GST Option",
        ["GST Calculator", "GSTR-1 Summary", "GSTR-3B Summary", "HSN Lookup", "E-way Bill Check"],
        horizontal=True
    )
    
    if option == "GST Calculator":
        st.subheader("GST Calculator")
        
        col1, col2 = st.columns(2)
        with col1:
            base_amount = st.number_input("Base Amount", min_value=0.0, step=0.01)
            gst_rate = st.selectbox("GST Rate", [0, 5, 12, 18, 28])
        
        with col2:
            transaction_type = st.radio("Transaction Type", ["Intra-State (CGST+SGST)", "Inter-State (IGST)"])
        
        if base_amount > 0:
            is_intra = transaction_type.startswith("Intra")
            from utils.helpers import calculate_gst
            gst_calc = calculate_gst(base_amount, gst_rate, is_intra)
            
            st.divider()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("CGST", format_indian_currency(gst_calc['cgst']))
            with col2:
                st.metric("SGST", format_indian_currency(gst_calc['sgst']))
            with col3:
                st.metric("IGST", format_indian_currency(gst_calc['igst']))
            
            st.metric("Total Amount (incl. GST)", format_indian_currency(gst_calc['total_amount']))
    
    elif option == "GSTR-1 Summary":
        st.subheader("GSTR-1 Summary (Outward Supplies)")
        
        # Get sales data for the period
        sales_records = db.get_sales(limit=100)
        if sales_records:
            sales_df = pd.DataFrame(sales_records)
            
            # Summary metrics
            total_sales = sales_df['total'].sum() if 'total' in sales_df.columns else 0
            total_cgst = sales_df['cgst'].sum() if 'cgst' in sales_df.columns else 0
            total_sgst = sales_df['sgst'].sum() if 'sgst' in sales_df.columns else 0
            total_igst = sales_df['igst'].sum() if 'igst' in sales_df.columns else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sales", format_indian_currency(total_sales))
            with col2:
                st.metric("CGST", format_indian_currency(total_cgst))
            with col3:
                st.metric("SGST", format_indian_currency(total_sgst))
            with col4:
                st.metric("IGST", format_indian_currency(total_igst))
            
            st.dataframe(sales_df, use_container_width=True)
        else:
            st.info("No sales data available for GSTR-1")
    
    elif option == "GSTR-3B Summary":
        st.subheader("GSTR-3B Summary (Monthly Return)")
        
        # Combined view of sales and purchases
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Outward Supplies (Sales)**")
            sales_records = db.get_sales(limit=100)
            if sales_records:
                sales_df = pd.DataFrame(sales_records)
                total_sales = sales_df['total'].sum() if 'total' in sales_df.columns else 0
                output_cgst = sales_df['cgst'].sum() if 'cgst' in sales_df.columns else 0
                output_sgst = sales_df['sgst'].sum() if 'sgst' in sales_df.columns else 0
                output_igst = sales_df['igst'].sum() if 'igst' in sales_df.columns else 0
                
                st.metric("Total Sales", format_indian_currency(total_sales))
                st.write(f"CGST: {format_indian_currency(output_cgst)}")
                st.write(f"SGST: {format_indian_currency(output_sgst)}")
                st.write(f"IGST: {format_indian_currency(output_igst)}")
            else:
                st.info("No sales data")
        
        with col2:
            st.write("**Inward Supplies (Purchases)**")
            purchase_records = db.get_purchases(limit=100)
            if purchase_records:
                purchase_df = pd.DataFrame(purchase_records)
                total_purchases = purchase_df['total'].sum() if 'total' in purchase_df.columns else 0
                input_cgst = purchase_df['cgst'].sum() if 'cgst' in purchase_df.columns else 0
                input_sgst = purchase_df['sgst'].sum() if 'sgst' in purchase_df.columns else 0
                input_igst = purchase_df['igst'].sum() if 'igst' in purchase_df.columns else 0
                
                st.metric("Total Purchases", format_indian_currency(total_purchases))
                st.write(f"CGST: {format_indian_currency(input_cgst)}")
                st.write(f"SGST: {format_indian_currency(input_sgst)}")
                st.write(f"IGST: {format_indian_currency(input_igst)}")
            else:
                st.info("No purchase data")
        
        st.divider()
        st.subheader("Net GST Liability")
        net_cgst = output_cgst - input_cgst if 'output_cgst' in locals() and 'input_cgst' in locals() else 0
        net_sgst = output_sgst - input_sgst if 'output_sgst' in locals() and 'input_sgst' in locals() else 0
        net_igst = output_igst - input_igst if 'output_igst' in locals() and 'input_igst' in locals() else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Net CGST", format_indian_currency(max(0, net_cgst)))
        with col2:
            st.metric("Net SGST", format_indian_currency(max(0, net_sgst)))
        with col3:
            st.metric("Net IGST", format_indian_currency(max(0, net_igst)))
    
    elif option == "HSN Lookup":
        st.subheader("HSN Code Lookup")
        hsn_search = st.text_input("Search HSN Code or Description")
        
        if hsn_search:
            from utils.constants import HSN_CODES
            results = []
            for hsn, desc in HSN_CODES.items():
                if hsn_search.lower() in hsn.lower() or hsn_search.lower() in desc.lower():
                    results.append({'HSN Code': hsn, 'Description': desc})
            
            if results:
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.info("No matching HSN codes found")
    
    elif option == "E-way Bill Check":
        st.subheader("E-way Bill Requirement Check")
        
        col1, col2 = st.columns(2)
        with col1:
            invoice_value = st.number_input("Invoice Value", min_value=0.0, step=0.01)
        with col2:
            distance = st.number_input("Distance (km)", min_value=0, step=1)
        
        if invoice_value > 50000:
            st.warning("⚠️ E-way bill is required (Invoice value > ₹50,000)")
            st.info(f"Valid for: {min(distance // 100 + 1, 15)} day(s)")
        else:
            st.success("✅ E-way bill not required (Invoice value ≤ ₹50,000)")


def show_reports_page():
    """Display the Reports page"""
    modules = get_modules()
    reports_module = modules['reports']
    
    st.title("📊 Reports")
    
    # Report type selection
    report_type = st.selectbox(
        "Select Report Type",
        ["MIS Report", "Trial Balance", "Balance Sheet", "P&L Account"]
    )
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=date(2025, 4, 1))
    with col2:
        end_date = st.date_input("To Date", value=date.today())
    
    # Data source
    data_source = st.radio("Data Source", ["Local Database", "Fetch from Tally"], horizontal=True)
    
    if report_type == "MIS Report":
        st.subheader("Management Information System (MIS) Report")
        
        # Sample MIS data
        st.write("**Key Metrics**")
        col1, col2, col3, col4 = st.columns(4)
        
        sales_records = db.get_sales()
        total_sales = sum(s.get('total', 0) for s in sales_records) if sales_records else 0
        
        purchase_records = db.get_purchases()
        total_purchases = sum(p.get('total', 0) for p in purchase_records) if purchase_records else 0
        
        expense_records = db.get_expenses()
        total_expenses = sum(e.get('amount', 0) for e in expense_records) if expense_records else 0
        
        gross_profit = total_sales - total_purchases
        net_profit = gross_profit - total_expenses
        
        with col1:
            st.metric("Total Sales", format_indian_currency(total_sales))
        with col2:
            st.metric("Total Purchases", format_indian_currency(total_purchases))
        with col3:
            st.metric("Total Expenses", format_indian_currency(total_expenses))
        with col4:
            st.metric("Net Profit", format_indian_currency(net_profit))
    
    elif report_type == "Trial Balance":
        st.subheader("Trial Balance")
        
        if data_source == "Fetch from Tally":
            if st.button("🔄 Fetch from Tally"):
                try:
                    # In real implementation: reports_module.get_trial_balance_from_tally()
                    st.info("This would fetch trial balance from Tally")
                except Exception as e:
                    st.error(f"Error fetching from Tally: {str(e)}")
        else:
            st.info("Local trial balance display - would calculate from database")
            
            # Sample trial balance structure
            sample_tb = {
                'Ledger': ['Sales Account', 'Purchase Account', 'Cash', 'Bank', 'Capital'],
                'Debit': [0, 150000, 50000, 200000, 0],
                'Credit': [300000, 0, 0, 0, 400000]
            }
            df = pd.DataFrame(sample_tb)
            st.dataframe(df, use_container_width=True)
            
            # Upload option
            if st.button("📤 Upload to Tally"):
                st.info("This would upload the trial balance data to Tally")
    
    elif report_type == "Balance Sheet":
        st.subheader("Balance Sheet")
        st.info("Balance sheet display - would fetch from Tally or calculate locally")
        
        # Sample structure
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Liabilities**")
            liabilities = {
                'Particulars': ['Capital', 'Reserves', 'Loans', 'Creditors'],
                'Amount': [500000, 100000, 200000, 50000]
            }
            st.dataframe(pd.DataFrame(liabilities), use_container_width=True)
        
        with col2:
            st.write("**Assets**")
            assets = {
                'Particulars': ['Fixed Assets', 'Investments', 'Debtors', 'Cash/Bank'],
                'Amount': [400000, 150000, 100000, 200000]
            }
            st.dataframe(pd.DataFrame(assets), use_container_width=True)
    
    elif report_type == "P&L Account":
        st.subheader("Profit & Loss Account")
        
        sales_records = db.get_sales()
        total_revenue = sum(s.get('total', 0) for s in sales_records) if sales_records else 0
        
        purchase_records = db.get_purchases()
        total_cogs = sum(p.get('total', 0) for p in purchase_records) if purchase_records else 0
        
        expense_records = db.get_expenses()
        total_expenses = sum(e.get('amount', 0) for e in expense_records) if expense_records else 0
        
        gross_profit = total_revenue - total_cogs
        net_profit = gross_profit - total_expenses
        
        # Display P&L
        pl_data = {
            'Particulars': [
                'Revenue (Sales)',
                'Less: Cost of Goods Sold',
                'Gross Profit',
                'Less: Operating Expenses',
                'Net Profit'
            ],
            'Amount': [
                format_indian_currency(total_revenue),
                format_indian_currency(total_cogs),
                format_indian_currency(gross_profit),
                format_indian_currency(total_expenses),
                format_indian_currency(net_profit)
            ]
        }
        st.dataframe(pd.DataFrame(pl_data), use_container_width=True)


def show_ind_as_page():
    """Display the Ind AS page"""
    modules = get_modules()
    ind_as_module = modules['ind_as']
    
    st.title("📚 Indian Accounting Standards (Ind AS)")
    
    # Search bar
    search_query = st.text_input("🔍 Search across standards", placeholder="Search for keywords...")
    
    if search_query:
        # Search functionality
        results = ind_as_module.search_standards(search_query)
        if results:
            st.subheader(f"Search Results for '{search_query}'")
            for result in results:
                with st.expander(f"Ind AS {result['number']}: {result['title']}"):
                    st.write(f"**Objective:** {result['objective']}")
        else:
            st.info("No matching standards found")
    
    st.divider()
    
    # Standard selector
    standard_list = ind_as_module.get_all_standards()
    standard_options = [f"Ind AS {s['number']}: {s['title']}" for s in standard_list]
    
    selected_standard = st.selectbox("Select Standard", [""] + standard_options)
    
    if selected_standard:
        # Extract standard number
        std_number = selected_standard.split(":")[0].replace("Ind AS ", "").strip()
        standard_details = ind_as_module.get_standard_details(std_number)
        
        if standard_details:
            st.subheader(f"Ind AS {standard_details['number']}: {standard_details['title']}")
            
            st.write("**Objective:**")
            st.info(standard_details['objective'])
            
            st.write("**Key Principles:**")
            for principle in standard_details['key_principles']:
                st.write(f"• {principle}")
            
            st.write("**Disclosure Requirements:**")
            for disclosure in standard_details['disclosure_requirements']:
                st.write(f"• {disclosure}")


def show_settings_page():
    """Display the Settings page"""
    st.title("⚙️ Settings")
    
    st.subheader("Tally Configuration")
    
    with st.form("settings_form"):
        tally_host = st.text_input("Tally Host", value=st.session_state.tally_host)
        tally_port = st.text_input("Tally Port", value=st.session_state.tally_port)
        company_name = st.text_input("Company Name", value=st.session_state.company_name)
        
        financial_years = ["2023-24", "2024-25", "2025-26", "2026-27"]
        fy_index = financial_years.index(st.session_state.financial_year) if st.session_state.financial_year in financial_years else 2
        financial_year = st.selectbox("Financial Year", financial_years, index=fy_index)
        
        from utils.constants import STATE_CODES
        state_names = list(STATE_CODES.values())
        state_index = state_names.index(st.session_state.default_gst_state) if st.session_state.default_gst_state in state_names else 0
        default_gst_state = st.selectbox("Default GST State", state_names, index=state_index)
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_button = st.form_submit_button("🔌 Test Connection")
        
        with col2:
            save_button = st.form_submit_button("💾 Save Settings")
        
        if test_button:
            try:
                # Update connector with new settings
                from tally.connection import TallyConnector
                test_connector = TallyConnector(host=tally_host, port=int(tally_port))
                result = test_connector.test_connection()
                
                if result['connected']:
                    st.success(f"✅ Connected to Tally at {result['url']}")
                    if result['company']:
                        st.info(f"Active Company: {result['company']}")
                else:
                    st.error(f"❌ Connection failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        if save_button:
            try:
                # Save to database
                db.set_setting('tally_host', tally_host)
                db.set_setting('tally_port', tally_port)
                db.set_setting('company_name', company_name)
                db.set_setting('financial_year', financial_year)
                db.set_setting('default_gst_state', default_gst_state)
                
                # Update session state
                st.session_state.tally_host = tally_host
                st.session_state.tally_port = tally_port
                st.session_state.company_name = company_name
                st.session_state.financial_year = financial_year
                st.session_state.default_gst_state = default_gst_state
                
                st.success("✅ Settings saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error saving settings: {str(e)}")
    
    st.divider()
    
    st.subheader("How to Enable Tally HTTP Server")
    st.markdown("""
    1. Open Tally Prime / Tally ERP 9
    2. Press **F12** (Configure)
    3. Go to **Advanced Configuration**
    4. Enable **TallyPrime Server** or **Tally.NET Server**
    5. Set Port to **9000** (default)
    6. Enable **HTTP Server**
    7. Click **Yes** to accept
    8. Restart Tally for changes to take effect
    
    Once enabled, Tally will listen on http://localhost:9000
    """)


def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()
    
    # Sidebar navigation
    st.sidebar.title("🧾 AI Accounting Chatbot")
    st.sidebar.divider()
    
    # Navigation menu
    page_names = [page[0] for page in SIDEBAR_PAGES]
    selected_page = st.sidebar.radio("Navigation", page_names)
    
    st.sidebar.divider()
    
    # Version info
    st.sidebar.caption(f"Version 1.0.0")
    st.sidebar.caption(f"FY: {st.session_state.financial_year}")
    
    # Route to appropriate page
    page_mapping = {
        "🏠 Home": show_home_page,
        "💰 Sales": show_sales_page,
        "🛒 Purchases": show_purchases_page,
        "💸 Expenses": show_expenses_page,
        "🏦 Bank Statement": show_bank_statement_page,
        "📋 TDS": show_tds_page,
        "🧾 GST": show_gst_page,
        "📊 Reports": show_reports_page,
        "📚 Ind AS": show_ind_as_page,
        "⚙️ Settings": show_settings_page
    }
    
    # Display selected page
    page_function = page_mapping.get(selected_page)
    if page_function:
        page_function()
    else:
        st.error(f"Page '{selected_page}' not found")


if __name__ == "__main__":
    main()
