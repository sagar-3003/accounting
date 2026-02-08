# AI Accounting Chatbot with Tally Integration

An intelligent, conversational accounting assistant built with Streamlit that seamlessly integrates with Tally Prime/ERP 9. This chatbot simplifies accounting tasks through natural language interactions, automates data entry, and provides real-time insights into your business finances.

## 🌟 Features

### 📊 Core Modules

1. **Sales Module** 💰
   - Conversational invoice generation
   - Automatic GST calculation (CGST/SGST/IGST)
   - PDF invoice generation with professional templates
   - Direct posting to Tally
   - Sales register and reporting

2. **Purchase Module** 🛒
   - OCR-powered invoice scanning
   - Automatic data extraction from images/PDFs
   - Purchase register management
   - Vendor management
   - Tally integration

3. **Expenses Module** 💸
   - Expense tracking and categorization
   - Payment status monitoring
   - Creditor aging analysis
   - Overdue payment reminders
   - Due date management

4. **Bank Statement Module** 🏦
   - PDF/Excel bank statement import
   - Automatic transaction parsing
   - Bank reconciliation support
   - Transaction categorization
   - Tally voucher generation

5. **TDS Module** 📋
   - TDS calculation by section (194C, 194J, 194A, etc.)
   - Party and PAN management
   - Quarterly TDS register
   - TDS certificate generation support
   - Financial year tracking

6. **GST Module** 🧾
   - GST Calculator
   - GSTR-1 Summary (Outward Supplies)
   - GSTR-3B Summary (Monthly Return)
   - HSN Code lookup
   - E-way Bill requirement checker

7. **Reports Module** 📊
   - MIS Reports (Management Information System)
   - Trial Balance
   - Balance Sheet
   - Profit & Loss Account
   - Customizable date ranges
   - Export capabilities

8. **Ind AS Module** 📚
   - Complete Indian Accounting Standards knowledge base
   - Search functionality across all standards
   - Detailed standard information
   - Key principles and disclosure requirements
   - Quick reference guide

### 🎯 Key Capabilities

- **Conversational Interface**: Chat-based interactions for intuitive data entry
- **Tally Integration**: Real-time synchronization with Tally Prime/ERP 9
- **Offline Mode**: Works without Tally connection, syncs when available
- **OCR Support**: Extract data from scanned invoices and documents
- **Indian Compliance**: Built for Indian GST, TDS, and accounting standards
- **Multi-format Support**: Handle PDFs, Excel files, and images
- **Professional Invoicing**: Generate GST-compliant invoices with customizable templates

## 📸 Screenshots

_Screenshots will be added here once the application is deployed_

## 🔧 Prerequisites

Before installing the application, ensure you have:

1. **Python 3.10 or higher**
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Tally Prime or Tally ERP 9**
   - With HTTP server enabled (instructions below)
   - Running on port 9000 (default)

3. **Tesseract OCR** (for invoice scanning)
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install tesseract-ocr
   ```
   
   **macOS:**
   ```bash
   brew install tesseract
   ```
   
   **Windows:**
   - Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
   - Add to PATH environment variable

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sagar-3003/accounting.git
   cd accounting
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Enable Tally HTTP Server** (see instructions below)

## 🔌 Enabling Tally HTTP Server

To enable communication between the chatbot and Tally:

1. **Open Tally Prime / Tally ERP 9**

2. **Press F12** (Configure)

3. Navigate to **Advanced Configuration**

4. Go to **TallyPrime Server** or **Tally.NET Server**

5. Enable the following settings:
   - **Enable TallyPrime Server**: Yes
   - **Enable HTTP Server**: Yes
   - **Port**: 9000 (default, can be changed)

6. Click **Yes** to accept the configuration

7. **Restart Tally** for changes to take effect

8. **Verify connection**: 
   - Open browser and navigate to `http://localhost:9000`
   - You should see Tally's XML interface

> **Note**: Keep Tally running while using the chatbot for real-time integration.

## ▶️ Running the Application

1. **Start the Streamlit app**
   ```bash
   streamlit run app.py
   ```

2. **Access the application**
   - The app will automatically open in your default browser
   - Default URL: `http://localhost:8501`

3. **Configure settings**
   - Navigate to ⚙️ Settings page
   - Enter your Tally connection details
   - Test the connection
   - Save settings

## 📖 Usage Guide

### Initial Setup

1. **Configure Tally Connection**
   - Go to Settings page
   - Enter Tally Host (default: localhost)
   - Enter Tally Port (default: 9000)
   - Click "Test Connection"
   - Save settings if connection successful

2. **Set Company Details**
   - Update company information in `config.py`
   - Set financial year
   - Configure default GST state

### Module-Wise Usage

#### 💰 Sales Module

1. Navigate to Sales page
2. Start conversation with the chatbot
3. Provide customer details when asked
4. Add items (name, quantity, rate, HSN)
5. Select GST type (Intra/Inter state)
6. Specify invoice date
7. Review and confirm
8. Download generated PDF invoice
9. View sales register

**Example Conversation:**
```
Bot: What is the customer's name?
You: ABC Company Ltd

Bot: What is the customer's GSTIN?
You: 27AABCU9603R1ZX

Bot: Now let's add items...
You: Laptop, 2, 50000, 8471

Bot: Add another item or type 'done'
You: done
```

#### 🛒 Purchase Module

1. Upload purchase invoice (image/PDF)
2. Review OCR-extracted data
3. Edit if needed
4. Confirm and save
5. View purchase register

#### 💸 Expenses Module

1. Upload expense invoice OR enter manually
2. Fill expense details
3. Set due date
4. Track payment status
5. Monitor overdue payments in Creditor Aging tab

#### 🏦 Bank Statement Module

1. Upload bank statement (PDF/Excel)
2. Review parsed transactions
3. Categorize transactions
4. Edit if needed
5. Confirm to post to database

#### 📋 TDS Module

1. Start TDS entry conversation
2. Provide party name and PAN
3. Specify TDS section
4. Enter payment amount
5. System calculates TDS automatically
6. Review quarterly summary

#### 🧾 GST Module

**GST Calculator:**
- Enter base amount
- Select GST rate (5%, 12%, 18%, 28%)
- Choose transaction type (Intra/Inter state)
- View calculated CGST/SGST/IGST

**GSTR-1/3B Summary:**
- View compiled sales/purchase data
- Export for filing
- Monitor GST liability

#### 📊 Reports Module

1. Select report type
2. Choose date range
3. Select data source (Local DB / Tally)
4. Generate report
5. Export if needed

#### 📚 Ind AS Module

1. Use search bar for quick lookup
2. OR select standard from dropdown
3. View objectives, key principles, and disclosure requirements

## 📁 Project Structure

```
accounting/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation
│
├── database/
│   ├── __init__.py
│   └── db.py                   # SQLite database manager
│
├── tally/
│   ├── __init__.py
│   ├── connection.py           # Tally HTTP connection
│   ├── voucher.py              # Voucher creation
│   ├── ledger.py               # Ledger management
│   ├── stock.py                # Stock item management
│   └── reports.py              # Report fetching
│
├── modules/
│   ├── __init__.py
│   ├── sales.py                # Sales module
│   ├── purchase.py             # Purchase module
│   ├── expenses.py             # Expenses module
│   ├── bank_statement.py       # Bank statement module
│   ├── tds.py                  # TDS module
│   ├── gst.py                  # GST module
│   ├── reports.py              # Reports module
│   └── ind_as.py               # Ind AS knowledge base
│
├── invoice/
│   ├── __init__.py
│   ├── generator.py            # PDF invoice generation
│   └── scanner.py              # OCR invoice scanning
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py              # Helper functions
│   └── constants.py            # Constants (HSN codes, states, etc.)
│
└── templates/
    └── invoice_template.html   # Invoice HTML template
```

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Database**: SQLite (local data storage)
- **Integration**: Tally XML over HTTP
- **OCR**: Tesseract OCR, pytesseract
- **PDF Processing**: pdfplumber, reportlab
- **Image Processing**: Pillow
- **Data Processing**: pandas, openpyxl
- **Templating**: Jinja2
- **HTTP**: requests

## 🔐 Security Considerations

- All data stored locally in SQLite database
- No cloud dependencies for sensitive data
- Tally connection over local network only
- PAN and GSTIN validation built-in
- Configurable access controls

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Tally Solutions for the excellent accounting software
- Streamlit for the amazing web framework
- The Python community for all the wonderful libraries

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: [Your contact information]

## 🗺️ Roadmap

- [ ] Multi-company support
- [ ] Advanced OCR with AI models
- [ ] WhatsApp integration for invoice sending
- [ ] Email integration
- [ ] Advanced analytics dashboard
- [ ] Mobile app
- [ ] Voice-based data entry
- [ ] Integration with banking APIs
- [ ] Advanced tax planning features
- [ ] Cloud sync option

---

**Made with ❤️ for Indian Businesses**
