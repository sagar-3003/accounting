"""
Tally reports module
Fetch financial reports from Tally
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import pandas as pd
from tally.connection import tally_connector


class TallyReports:
    """Manager for fetching reports from Tally"""
    
    def __init__(self, connector=None):
        """Initialize with Tally connector"""
        self.connector = connector or tally_connector
    
    def get_trial_balance(self, from_date: str, to_date: str) -> pd.DataFrame:
        """
        Get trial balance from Tally
        
        Args:
            from_date: Start date (YYYYMMDD format)
            to_date: End date (YYYYMMDD format)
            
        Returns:
            DataFrame with trial balance
        """
        try:
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Collection</TYPE>
                        <ID>Trial Balance</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                                <SVFROMDATE>{from_date}</SVFROMDATE>
                                <SVTODATE>{to_date}</SVTODATE>
                            </STATICVARIABLES>
                        </DESC>
                    </BODY>
                </ENVELOPE>
            """
            response = self.connector.send_request(xml_request)
            
            root = ET.fromstring(response)
            data = []
            
            for ledger in root.findall('.//LEDGER'):
                name_elem = ledger.find('NAME')
                dr_elem = ledger.find('DEBIT')
                cr_elem = ledger.find('CREDIT')
                
                if name_elem is not None:
                    data.append({
                        "Ledger": name_elem.text,
                        "Debit": float(dr_elem.text) if dr_elem is not None else 0,
                        "Credit": float(cr_elem.text) if cr_elem is not None else 0
                    })
            
            return pd.DataFrame(data)
        except Exception as e:
            return pd.DataFrame()
    
    def get_balance_sheet(self, date: str) -> Dict[str, List[Dict]]:
        """
        Get balance sheet from Tally
        
        Args:
            date: Date (YYYYMMDD format)
            
        Returns:
            Dict with 'assets' and 'liabilities' lists
        """
        try:
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Collection</TYPE>
                        <ID>Balance Sheet</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                                <SVTODATE>{date}</SVTODATE>
                            </STATICVARIABLES>
                        </DESC>
                    </BODY>
                </ENVELOPE>
            """
            response = self.connector.send_request(xml_request)
            
            root = ET.fromstring(response)
            result = {
                "assets": [],
                "liabilities": []
            }
            
            # Parse assets
            for item in root.findall('.//ASSET'):
                name_elem = item.find('NAME')
                amount_elem = item.find('AMOUNT')
                
                if name_elem is not None:
                    result["assets"].append({
                        "name": name_elem.text,
                        "amount": float(amount_elem.text) if amount_elem is not None else 0
                    })
            
            # Parse liabilities
            for item in root.findall('.//LIABILITY'):
                name_elem = item.find('NAME')
                amount_elem = item.find('AMOUNT')
                
                if name_elem is not None:
                    result["liabilities"].append({
                        "name": name_elem.text,
                        "amount": float(amount_elem.text) if amount_elem is not None else 0
                    })
            
            return result
        except Exception as e:
            return {"assets": [], "liabilities": []}
    
    def get_profit_loss(self, from_date: str, to_date: str) -> Dict[str, List[Dict]]:
        """
        Get profit & loss statement from Tally
        
        Args:
            from_date: Start date (YYYYMMDD format)
            to_date: End date (YYYYMMDD format)
            
        Returns:
            Dict with 'income' and 'expenses' lists
        """
        try:
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Collection</TYPE>
                        <ID>Profit and Loss</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                                <SVFROMDATE>{from_date}</SVFROMDATE>
                                <SVTODATE>{to_date}</SVTODATE>
                            </STATICVARIABLES>
                        </DESC>
                    </BODY>
                </ENVELOPE>
            """
            response = self.connector.send_request(xml_request)
            
            root = ET.fromstring(response)
            result = {
                "income": [],
                "expenses": []
            }
            
            # Parse income
            for item in root.findall('.//INCOME'):
                name_elem = item.find('NAME')
                amount_elem = item.find('AMOUNT')
                
                if name_elem is not None:
                    result["income"].append({
                        "name": name_elem.text,
                        "amount": float(amount_elem.text) if amount_elem is not None else 0
                    })
            
            # Parse expenses
            for item in root.findall('.//EXPENSE'):
                name_elem = item.find('NAME')
                amount_elem = item.find('AMOUNT')
                
                if name_elem is not None:
                    result["expenses"].append({
                        "name": name_elem.text,
                        "amount": float(amount_elem.text) if amount_elem is not None else 0
                    })
            
            return result
        except Exception as e:
            return {"income": [], "expenses": []}
    
    def get_ledger_report(self, ledger_name: str, from_date: str, to_date: str) -> pd.DataFrame:
        """
        Get ledger report from Tally
        
        Args:
            ledger_name: Ledger name
            from_date: Start date (YYYYMMDD format)
            to_date: End date (YYYYMMDD format)
            
        Returns:
            DataFrame with ledger transactions
        """
        try:
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Collection</TYPE>
                        <ID>Ledger Vouchers</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                                <LEDGERNAME>{ledger_name}</LEDGERNAME>
                                <SVFROMDATE>{from_date}</SVFROMDATE>
                                <SVTODATE>{to_date}</SVTODATE>
                            </STATICVARIABLES>
                        </DESC>
                    </BODY>
                </ENVELOPE>
            """
            response = self.connector.send_request(xml_request)
            
            root = ET.fromstring(response)
            data = []
            
            for voucher in root.findall('.//VOUCHER'):
                date_elem = voucher.find('DATE')
                type_elem = voucher.find('VOUCHERTYPENAME')
                ref_elem = voucher.find('REFERENCE')
                narration_elem = voucher.find('NARRATION')
                amount_elem = voucher.find('AMOUNT')
                
                data.append({
                    "Date": date_elem.text if date_elem is not None else "",
                    "Type": type_elem.text if type_elem is not None else "",
                    "Reference": ref_elem.text if ref_elem is not None else "",
                    "Narration": narration_elem.text if narration_elem is not None else "",
                    "Amount": float(amount_elem.text) if amount_elem is not None else 0
                })
            
            return pd.DataFrame(data)
        except Exception as e:
            return pd.DataFrame()


# Global instance
tally_reports = TallyReports()
