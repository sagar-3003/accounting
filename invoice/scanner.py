"""
OCR-based invoice scanner using pytesseract
Extracts data from invoice images and PDFs
"""

import os
import re
from typing import Dict, Optional, List
from PIL import Image
import pytesseract
import pdfplumber


class InvoiceScanner:
    """Scan and extract data from invoices using OCR"""
    
    def __init__(self):
        """Initialize invoice scanner"""
        pass
    
    def scan_image(self, image_path: str) -> Dict:
        """
        Extract text from invoice image using OCR
        
        Args:
            image_path: Path to invoice image
            
        Returns:
            Dict with extracted invoice data
        """
        try:
            # Open image
            image = Image.open(image_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            # Parse extracted text
            return self._parse_invoice_text(text)
        except Exception as e:
            return {
                "error": f"Failed to scan image: {str(e)}",
                "raw_text": ""
            }
    
    def scan_pdf(self, pdf_path: str) -> Dict:
        """
        Extract text from invoice PDF
        
        Args:
            pdf_path: Path to invoice PDF
            
        Returns:
            Dict with extracted invoice data
        """
        try:
            text = ""
            
            # Extract text from PDF
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # Parse extracted text
            return self._parse_invoice_text(text)
        except Exception as e:
            return {
                "error": f"Failed to scan PDF: {str(e)}",
                "raw_text": ""
            }
    
    def scan_file(self, file_path: str) -> Dict:
        """
        Auto-detect file type and extract invoice data
        
        Args:
            file_path: Path to invoice file
            
        Returns:
            Dict with extracted invoice data
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return self.scan_pdf(file_path)
        elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return self.scan_image(file_path)
        else:
            return {
                "error": "Unsupported file format",
                "raw_text": ""
            }
    
    def _parse_invoice_text(self, text: str) -> Dict:
        """
        Parse invoice text and extract structured data
        
        Args:
            text: Raw OCR text
            
        Returns:
            Dict with parsed invoice data
        """
        result = {
            "raw_text": text,
            "vendor_name": None,
            "invoice_no": None,
            "invoice_date": None,
            "total_amount": None,
            "gstin": None,
            "items": []
        }
        
        # Extract vendor/supplier name (usually in first few lines)
        lines = text.split('\n')
        if lines:
            # Try to find company name (often the first non-empty line)
            for line in lines[:10]:
                line = line.strip()
                if len(line) > 3 and not any(kw in line.lower() for kw in ['invoice', 'bill', 'date', 'gstin']):
                    if not result["vendor_name"]:
                        result["vendor_name"] = line
                        break
        
        # Extract invoice number
        invoice_patterns = [
            r'invoice\s*(?:no|number|#)[\s:]*([A-Z0-9\-/]+)',
            r'bill\s*(?:no|number|#)[\s:]*([A-Z0-9\-/]+)',
            r'ref[\s:]*([A-Z0-9\-/]+)'
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["invoice_no"] = match.group(1).strip()
                break
        
        # Extract date
        date_patterns = [
            r'date[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'dated[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["invoice_date"] = match.group(1).strip()
                break
        
        # Extract GSTIN
        gstin_pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b'
        match = re.search(gstin_pattern, text)
        if match:
            result["gstin"] = match.group(0)
        
        # Extract total amount
        total_patterns = [
            r'total[\s:]*(?:rs\.?|₹)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)',
            r'grand\s*total[\s:]*(?:rs\.?|₹)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)',
            r'amount\s*payable[\s:]*(?:rs\.?|₹)?[\s]*(\d+(?:,\d+)*(?:\.\d{2})?)'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    result["total_amount"] = float(amount_str)
                    break
                except:
                    pass
        
        # Try to extract line items (simplified)
        # Look for patterns like: item name qty rate amount
        item_pattern = r'([A-Za-z\s]+?)\s+(\d+)\s+(?:rs\.?|₹)?\s*(\d+(?:\.\d{2})?)\s+(?:rs\.?|₹)?\s*(\d+(?:\.\d{2})?)'
        matches = re.findall(item_pattern, text, re.IGNORECASE)
        
        for match in matches:
            try:
                result["items"].append({
                    "name": match[0].strip(),
                    "quantity": int(match[1]),
                    "rate": float(match[2]),
                    "amount": float(match[3])
                })
            except:
                pass
        
        return result
    
    def extract_bank_statement_data(self, file_path: str) -> List[Dict]:
        """
        Extract transaction data from bank statement PDF
        
        Args:
            file_path: Path to bank statement PDF
            
        Returns:
            List of transaction dicts
        """
        try:
            transactions = []
            
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # Try to extract table
                    tables = page.extract_tables()
                    
                    for table in tables:
                        for row in table:
                            if row and len(row) >= 4:
                                # Try to parse transaction row
                                try:
                                    # Common bank statement format: Date, Description, Debit, Credit, Balance
                                    transaction = {
                                        "date": row[0] if row[0] else "",
                                        "description": row[1] if len(row) > 1 and row[1] else "",
                                        "debit": self._parse_amount(row[2]) if len(row) > 2 else 0,
                                        "credit": self._parse_amount(row[3]) if len(row) > 3 else 0,
                                        "balance": self._parse_amount(row[4]) if len(row) > 4 else 0
                                    }
                                    
                                    if transaction["date"] and (transaction["debit"] > 0 or transaction["credit"] > 0):
                                        transactions.append(transaction)
                                except:
                                    pass
            
            return transactions
        except Exception as e:
            return []
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        try:
            if not amount_str or amount_str.strip() == "":
                return 0.0
            
            # Remove currency symbols and commas
            amount_str = str(amount_str).replace('₹', '').replace('Rs', '').replace(',', '').strip()
            
            # Handle negative amounts in parentheses
            if amount_str.startswith('(') and amount_str.endswith(')'):
                amount_str = '-' + amount_str[1:-1]
            
            return float(amount_str)
        except:
            return 0.0


# Global instance
invoice_scanner = InvoiceScanner()
