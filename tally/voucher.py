"""
Tally voucher operations
Create various types of vouchers in Tally
"""

from datetime import datetime
from typing import List, Dict, Optional
from tally.connection import tally_connector
from tally.ledger import tally_ledger


class TallyVoucher:
    """Manager for Tally voucher operations"""
    
    def __init__(self, connector=None):
        """Initialize with Tally connector"""
        self.connector = connector or tally_connector
    
    def create_sales_voucher(self, date: str, party: str, ledger_entries: List[Dict],
                            narration: str, invoice_no: str) -> bool:
        """
        Create a sales voucher in Tally
        
        Args:
            date: Voucher date (YYYYMMDD format)
            party: Party ledger name
            ledger_entries: List of dicts with 'ledger', 'amount', 'is_debit' keys
            narration: Voucher narration
            invoice_no: Invoice/reference number
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            # Ensure party ledger exists
            if not tally_ledger.ledger_exists(party):
                tally_ledger.create_ledger(party, "Sundry Debtors")
            
            # Build ledger entries XML
            ledger_xml = ""
            for entry in ledger_entries:
                dr_cr = "Yes" if entry.get('is_debit', False) else "No"
                amount = abs(entry['amount'])
                
                ledger_xml += f"""
                    <ALLLEDGERENTRIES.LIST>
                        <LEDGERNAME>{entry['ledger']}</LEDGERNAME>
                        <ISDEEMEDPOSITIVE>{dr_cr}</ISDEEMEDPOSITIVE>
                        <AMOUNT>{-amount if not entry.get('is_debit', False) else amount}</AMOUNT>
                    </ALLLEDGERENTRIES.LIST>
                """
            
            # Party entry (Debit - Sundry Debtor)
            total_amount = sum([e['amount'] for e in ledger_entries if not e.get('is_debit', False)])
            
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Import</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>Vouchers</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <IMPORTDUPS>@@DUPS</IMPORTDUPS>
                            </STATICVARIABLES>
                        </DESC>
                        <DATA>
                            <TALLYMESSAGE>
                                <VOUCHER VCHTYPE="Sales" ACTION="Create">
                                    <DATE>{date}</DATE>
                                    <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                                    <REFERENCE>{invoice_no}</REFERENCE>
                                    <NARRATION>{narration}</NARRATION>
                                    <PARTYLEDGERNAME>{party}</PARTYLEDGERNAME>
                                    <PERSISTEDVIEW>Invoice Voucher View</PERSISTEDVIEW>
                                    <ALLLEDGERENTRIES.LIST>
                                        <LEDGERNAME>{party}</LEDGERNAME>
                                        <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                                        <AMOUNT>{total_amount}</AMOUNT>
                                    </ALLLEDGERENTRIES.LIST>
                                    {ledger_xml}
                                </VOUCHER>
                            </TALLYMESSAGE>
                        </DATA>
                    </BODY>
                </ENVELOPE>
            """
            
            response = self.connector.send_request(xml_request)
            return "CREATED" in response.upper() or "ACCEPTED" in response.upper()
        except Exception as e:
            print(f"Error creating sales voucher: {e}")
            return False
    
    def create_purchase_voucher(self, date: str, party: str, ledger_entries: List[Dict],
                               narration: str, ref_no: str) -> bool:
        """
        Create a purchase voucher in Tally
        
        Args:
            date: Voucher date (YYYYMMDD format)
            party: Party ledger name
            ledger_entries: List of dicts with 'ledger', 'amount', 'is_debit' keys
            narration: Voucher narration
            ref_no: Reference/invoice number
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            # Ensure party ledger exists
            if not tally_ledger.ledger_exists(party):
                tally_ledger.create_ledger(party, "Sundry Creditors")
            
            # Build ledger entries XML
            ledger_xml = ""
            for entry in ledger_entries:
                dr_cr = "Yes" if entry.get('is_debit', False) else "No"
                amount = abs(entry['amount'])
                
                ledger_xml += f"""
                    <ALLLEDGERENTRIES.LIST>
                        <LEDGERNAME>{entry['ledger']}</LEDGERNAME>
                        <ISDEEMEDPOSITIVE>{dr_cr}</ISDEEMEDPOSITIVE>
                        <AMOUNT>{amount if entry.get('is_debit', False) else -amount}</AMOUNT>
                    </ALLLEDGERENTRIES.LIST>
                """
            
            # Party entry (Credit - Sundry Creditor)
            total_amount = sum([e['amount'] for e in ledger_entries if e.get('is_debit', False)])
            
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Import</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>Vouchers</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <IMPORTDUPS>@@DUPS</IMPORTDUPS>
                            </STATICVARIABLES>
                        </DESC>
                        <DATA>
                            <TALLYMESSAGE>
                                <VOUCHER VCHTYPE="Purchase" ACTION="Create">
                                    <DATE>{date}</DATE>
                                    <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
                                    <REFERENCE>{ref_no}</REFERENCE>
                                    <NARRATION>{narration}</NARRATION>
                                    <PARTYLEDGERNAME>{party}</PARTYLEDGERNAME>
                                    <ALLLEDGERENTRIES.LIST>
                                        <LEDGERNAME>{party}</LEDGERNAME>
                                        <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                                        <AMOUNT>{-total_amount}</AMOUNT>
                                    </ALLLEDGERENTRIES.LIST>
                                    {ledger_xml}
                                </VOUCHER>
                            </TALLYMESSAGE>
                        </DATA>
                    </BODY>
                </ENVELOPE>
            """
            
            response = self.connector.send_request(xml_request)
            return "CREATED" in response.upper() or "ACCEPTED" in response.upper()
        except Exception as e:
            print(f"Error creating purchase voucher: {e}")
            return False
    
    def create_payment_voucher(self, date: str, party: str, amount: float,
                              bank_ledger: str, narration: str) -> bool:
        """
        Create a payment voucher in Tally
        
        Args:
            date: Voucher date (YYYYMMDD format)
            party: Party ledger name
            amount: Payment amount
            bank_ledger: Bank/Cash ledger name
            narration: Voucher narration
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Import</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>Vouchers</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <IMPORTDUPS>@@DUPS</IMPORTDUPS>
                            </STATICVARIABLES>
                        </DESC>
                        <DATA>
                            <TALLYMESSAGE>
                                <VOUCHER VCHTYPE="Payment" ACTION="Create">
                                    <DATE>{date}</DATE>
                                    <VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
                                    <NARRATION>{narration}</NARRATION>
                                    <ALLLEDGERENTRIES.LIST>
                                        <LEDGERNAME>{party}</LEDGERNAME>
                                        <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                                        <AMOUNT>{amount}</AMOUNT>
                                    </ALLLEDGERENTRIES.LIST>
                                    <ALLLEDGERENTRIES.LIST>
                                        <LEDGERNAME>{bank_ledger}</LEDGERNAME>
                                        <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                                        <AMOUNT>{-amount}</AMOUNT>
                                    </ALLLEDGERENTRIES.LIST>
                                </VOUCHER>
                            </TALLYMESSAGE>
                        </DATA>
                    </BODY>
                </ENVELOPE>
            """
            
            response = self.connector.send_request(xml_request)
            return "CREATED" in response.upper() or "ACCEPTED" in response.upper()
        except Exception as e:
            print(f"Error creating payment voucher: {e}")
            return False
    
    def create_receipt_voucher(self, date: str, party: str, amount: float,
                              bank_ledger: str, narration: str) -> bool:
        """
        Create a receipt voucher in Tally
        
        Args:
            date: Voucher date (YYYYMMDD format)
            party: Party ledger name
            amount: Receipt amount
            bank_ledger: Bank/Cash ledger name
            narration: Voucher narration
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Import</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>Vouchers</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <IMPORTDUPS>@@DUPS</IMPORTDUPS>
                            </STATICVARIABLES>
                        </DESC>
                        <DATA>
                            <TALLYMESSAGE>
                                <VOUCHER VCHTYPE="Receipt" ACTION="Create">
                                    <DATE>{date}</DATE>
                                    <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
                                    <NARRATION>{narration}</NARRATION>
                                    <ALLLEDGERENTRIES.LIST>
                                        <LEDGERNAME>{bank_ledger}</LEDGERNAME>
                                        <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                                        <AMOUNT>{amount}</AMOUNT>
                                    </ALLLEDGERENTRIES.LIST>
                                    <ALLLEDGERENTRIES.LIST>
                                        <LEDGERNAME>{party}</LEDGERNAME>
                                        <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                                        <AMOUNT>{-amount}</AMOUNT>
                                    </ALLLEDGERENTRIES.LIST>
                                </VOUCHER>
                            </TALLYMESSAGE>
                        </DATA>
                    </BODY>
                </ENVELOPE>
            """
            
            response = self.connector.send_request(xml_request)
            return "CREATED" in response.upper() or "ACCEPTED" in response.upper()
        except Exception as e:
            print(f"Error creating receipt voucher: {e}")
            return False
    
    def create_journal_voucher(self, date: str, entries: List[Dict], narration: str) -> bool:
        """
        Create a journal voucher in Tally
        
        Args:
            date: Voucher date (YYYYMMDD format)
            entries: List of dicts with 'ledger', 'amount', 'is_debit' keys
            narration: Voucher narration
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            # Build ledger entries XML
            ledger_xml = ""
            for entry in entries:
                dr_cr = "Yes" if entry.get('is_debit', False) else "No"
                amount = abs(entry['amount'])
                
                ledger_xml += f"""
                    <ALLLEDGERENTRIES.LIST>
                        <LEDGERNAME>{entry['ledger']}</LEDGERNAME>
                        <ISDEEMEDPOSITIVE>{dr_cr}</ISDEEMEDPOSITIVE>
                        <AMOUNT>{amount if entry.get('is_debit', False) else -amount}</AMOUNT>
                    </ALLLEDGERENTRIES.LIST>
                """
            
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Import</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>Vouchers</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <IMPORTDUPS>@@DUPS</IMPORTDUPS>
                            </STATICVARIABLES>
                        </DESC>
                        <DATA>
                            <TALLYMESSAGE>
                                <VOUCHER VCHTYPE="Journal" ACTION="Create">
                                    <DATE>{date}</DATE>
                                    <VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>
                                    <NARRATION>{narration}</NARRATION>
                                    {ledger_xml}
                                </VOUCHER>
                            </TALLYMESSAGE>
                        </DATA>
                    </BODY>
                </ENVELOPE>
            """
            
            response = self.connector.send_request(xml_request)
            return "CREATED" in response.upper() or "ACCEPTED" in response.upper()
        except Exception as e:
            print(f"Error creating journal voucher: {e}")
            return False
    
    def create_contra_voucher(self, date: str, from_ledger: str, to_ledger: str,
                             amount: float, narration: str) -> bool:
        """
        Create a contra voucher in Tally
        
        Args:
            date: Voucher date (YYYYMMDD format)
            from_ledger: Source bank/cash ledger
            to_ledger: Destination bank/cash ledger
            amount: Transfer amount
            narration: Voucher narration
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Import</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>Vouchers</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <IMPORTDUPS>@@DUPS</IMPORTDUPS>
                            </STATICVARIABLES>
                        </DESC>
                        <DATA>
                            <TALLYMESSAGE>
                                <VOUCHER VCHTYPE="Contra" ACTION="Create">
                                    <DATE>{date}</DATE>
                                    <VOUCHERTYPENAME>Contra</VOUCHERTYPENAME>
                                    <NARRATION>{narration}</NARRATION>
                                    <ALLLEDGERENTRIES.LIST>
                                        <LEDGERNAME>{to_ledger}</LEDGERNAME>
                                        <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                                        <AMOUNT>{amount}</AMOUNT>
                                    </ALLLEDGERENTRIES.LIST>
                                    <ALLLEDGERENTRIES.LIST>
                                        <LEDGERNAME>{from_ledger}</LEDGERNAME>
                                        <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                                        <AMOUNT>{-amount}</AMOUNT>
                                    </ALLLEDGERENTRIES.LIST>
                                </VOUCHER>
                            </TALLYMESSAGE>
                        </DATA>
                    </BODY>
                </ENVELOPE>
            """
            
            response = self.connector.send_request(xml_request)
            return "CREATED" in response.upper() or "ACCEPTED" in response.upper()
        except Exception as e:
            print(f"Error creating contra voucher: {e}")
            return False


# Global instance
tally_voucher = TallyVoucher()
