"""
PDF invoice generator using reportlab
Generates professional invoices with GST details
"""

import os
from datetime import datetime
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas
import config
from utils.helpers import format_indian_currency, words_to_number


class InvoiceGenerator:
    """Generate PDF invoices"""
    
    def __init__(self):
        """Initialize invoice generator"""
        self.output_dir = config.INVOICE_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_invoice(self, invoice_data: Dict) -> str:
        """
        Generate a PDF invoice
        
        Args:
            invoice_data: Dict with invoice details
                {
                    "invoice_no": str,
                    "invoice_date": str,
                    "customer_name": str,
                    "customer_address": str,
                    "customer_gstin": str,
                    "items": [
                        {
                            "name": str,
                            "hsn": str,
                            "quantity": float,
                            "unit": str,
                            "rate": float,
                            "amount": float
                        }
                    ],
                    "subtotal": float,
                    "cgst": float,
                    "sgst": float,
                    "igst": float,
                    "total": float
                }
        
        Returns:
            Path to generated PDF file
        """
        # Generate filename
        filename = f"{invoice_data['invoice_no'].replace('/', '_')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF
        pdf = SimpleDocTemplate(filepath, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = styles['Heading1']
        title_style.alignment = 1  # Center
        elements.append(Paragraph("TAX INVOICE", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Company details
        company_info = config.COMPANY_INFO
        company_text = f"""
        <b>{company_info['name']}</b><br/>
        {company_info['address']}<br/>
        GSTIN: {company_info['gstin']}<br/>
        PAN: {company_info['pan']}<br/>
        Email: {company_info['email']}<br/>
        Phone: {company_info['phone']}
        """
        elements.append(Paragraph(company_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Invoice info table
        info_data = [
            ['Invoice No:', invoice_data['invoice_no'], 'Date:', invoice_data['invoice_date']],
        ]
        info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Customer details
        customer_text = f"""
        <b>Bill To:</b><br/>
        {invoice_data['customer_name']}<br/>
        {invoice_data.get('customer_address', '')}<br/>
        GSTIN: {invoice_data.get('customer_gstin', 'N/A')}
        """
        elements.append(Paragraph(customer_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Items table
        items_data = [['#', 'Item Description', 'HSN', 'Qty', 'Unit', 'Rate', 'Amount']]
        
        for i, item in enumerate(invoice_data['items'], 1):
            items_data.append([
                str(i),
                item['name'],
                item.get('hsn', ''),
                str(item['quantity']),
                item.get('unit', 'Pcs'),
                format_indian_currency(item['rate']),
                format_indian_currency(item['amount'])
            ])
        
        items_table = Table(items_data, colWidths=[0.4*inch, 2.5*inch, 0.8*inch, 0.6*inch, 0.6*inch, 1.2*inch, 1.2*inch])
        items_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Totals table
        totals_data = [
            ['Subtotal:', format_indian_currency(invoice_data['subtotal'])],
        ]
        
        if invoice_data.get('cgst', 0) > 0:
            totals_data.append(['CGST:', format_indian_currency(invoice_data['cgst'])])
            totals_data.append(['SGST:', format_indian_currency(invoice_data['sgst'])])
        
        if invoice_data.get('igst', 0) > 0:
            totals_data.append(['IGST:', format_indian_currency(invoice_data['igst'])])
        
        totals_data.append(['Total:', format_indian_currency(invoice_data['total'])])
        
        totals_table = Table(totals_data, colWidths=[5*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Amount in words
        amount_words = words_to_number(invoice_data['total'])
        elements.append(Paragraph(f"<b>Amount in words:</b> {amount_words}", styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Terms & conditions
        terms_text = """
        <b>Terms & Conditions:</b><br/>
        1. Payment due within 30 days<br/>
        2. Interest @18% p.a. will be charged on delayed payments<br/>
        3. Subject to local jurisdiction
        """
        elements.append(Paragraph(terms_text, styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Signature
        signature_text = """
        <br/><br/>
        For {}<br/>
        <br/><br/>
        Authorized Signatory
        """.format(company_info['name'])
        elements.append(Paragraph(signature_text, styles['Normal']))
        
        # Build PDF
        pdf.build(elements)
        
        return filepath
    
    def generate_simple_invoice(self, invoice_no: str, date: str, customer_name: str,
                               items: List[Dict], total: float) -> str:
        """
        Generate a simple invoice (minimal details)
        
        Args:
            invoice_no: Invoice number
            date: Invoice date
            customer_name: Customer name
            items: List of items
            total: Total amount
            
        Returns:
            Path to generated PDF file
        """
        invoice_data = {
            "invoice_no": invoice_no,
            "invoice_date": date,
            "customer_name": customer_name,
            "customer_address": "",
            "customer_gstin": "",
            "items": items,
            "subtotal": total,
            "cgst": 0,
            "sgst": 0,
            "igst": 0,
            "total": total
        }
        
        return self.generate_invoice(invoice_data)


# Global instance
invoice_generator = InvoiceGenerator()
