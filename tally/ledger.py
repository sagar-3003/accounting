"""
Tally ledger operations
Create, read, and manage ledgers in Tally
"""

import xml.etree.ElementTree as ET
from typing import Optional, List, Dict
from tally.connection import tally_connector


class TallyLedger:
    """Manager for Tally ledger operations"""
    
    def __init__(self, connector=None):
        """Initialize with Tally connector"""
        self.connector = connector or tally_connector
    
    def ledger_exists(self, name: str) -> bool:
        """
        Check if a ledger exists in Tally
        
        Args:
            name: Ledger name
            
        Returns:
            True if ledger exists, False otherwise
        """
        try:
            ledger = self.get_ledger(name)
            return ledger is not None
        except:
            return False
    
    def get_ledger(self, name: str) -> Optional[Dict]:
        """
        Get ledger details from Tally
        
        Args:
            name: Ledger name
            
        Returns:
            Dict with ledger details or None if not found
        """
        try:
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>LedgerMaster</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                                <LEDGERNAME>{name}</LEDGERNAME>
                            </STATICVARIABLES>
                        </DESC>
                    </BODY>
                </ENVELOPE>
            """
            response = self.connector.send_request(xml_request)
            
            root = ET.fromstring(response)
            ledger_elem = root.find('.//LEDGER')
            
            if ledger_elem is not None:
                return {
                    "name": ledger_elem.find('NAME').text if ledger_elem.find('NAME') is not None else None,
                    "parent": ledger_elem.find('PARENT').text if ledger_elem.find('PARENT') is not None else None,
                    "opening_balance": ledger_elem.find('OPENINGBALANCE').text if ledger_elem.find('OPENINGBALANCE') is not None else "0"
                }
            return None
        except Exception as e:
            return None
    
    def list_ledgers(self, group: Optional[str] = None) -> List[str]:
        """
        List all ledgers or ledgers under a specific group
        
        Args:
            group: Parent group name (optional)
            
        Returns:
            List of ledger names
        """
        try:
            xml_request = """
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Collection</TYPE>
                        <ID>All Ledgers</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            </STATICVARIABLES>
                        </DESC>
                    </BODY>
                </ENVELOPE>
            """
            response = self.connector.send_request(xml_request)
            
            root = ET.fromstring(response)
            ledgers = []
            
            for ledger in root.findall('.//LEDGER'):
                name_elem = ledger.find('NAME')
                parent_elem = ledger.find('PARENT')
                
                if name_elem is not None:
                    if group is None:
                        ledgers.append(name_elem.text)
                    elif parent_elem is not None and parent_elem.text == group:
                        ledgers.append(name_elem.text)
            
            return ledgers
        except Exception as e:
            return []
    
    def create_ledger(self, name: str, parent_group: str, 
                     opening_balance: float = 0, gstin: str = "") -> bool:
        """
        Create a new ledger in Tally
        
        Args:
            name: Ledger name
            parent_group: Parent group (e.g., "Sundry Debtors")
            opening_balance: Opening balance (default: 0)
            gstin: GSTIN for the party (optional)
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            # Check if ledger already exists
            if self.ledger_exists(name):
                return True  # Already exists, no need to create
            
            # Prepare opening balance
            dr_cr = "Dr" if opening_balance >= 0 else "Cr"
            balance = abs(opening_balance)
            
            # Build XML request
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Import</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>All Masters</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <IMPORTDUPS>@@DUPS</IMPORTDUPS>
                            </STATICVARIABLES>
                        </DESC>
                        <DATA>
                            <TALLYMESSAGE>
                                <LEDGER NAME="{name}" ACTION="Create">
                                    <NAME.LIST>
                                        <NAME>{name}</NAME>
                                    </NAME.LIST>
                                    <PARENT>{parent_group}</PARENT>
                                    <OPENINGBALANCE>{balance}</OPENINGBALANCE>
                                    <ISBILLWISEON>Yes</ISBILLWISEON>
                                    <ISCOSTCENTRESON>No</ISCOSTCENTRESON>
            """
            
            # Add GSTIN if provided
            if gstin:
                xml_request += f"""
                                    <PARTYGSTIN>{gstin}</PARTYGSTIN>
                                    <GSTREGISTRATIONTYPE>Regular</GSTREGISTRATIONTYPE>
                """
            
            xml_request += f"""
                                </LEDGER>
                            </TALLYMESSAGE>
                        </DATA>
                    </BODY>
                </ENVELOPE>
            """
            
            response = self.connector.send_request(xml_request)
            
            # Check if creation was successful
            return "CREATED" in response.upper() or self.ledger_exists(name)
        except Exception as e:
            return False
    
    def update_ledger_opening_balance(self, name: str, opening_balance: float) -> bool:
        """
        Update ledger opening balance
        
        Args:
            name: Ledger name
            opening_balance: New opening balance
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            ledger = self.get_ledger(name)
            if not ledger:
                return False
            
            balance = abs(opening_balance)
            
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Import</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>All Masters</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <IMPORTDUPS>@@DUPS</IMPORTDUPS>
                            </STATICVARIABLES>
                        </DESC>
                        <DATA>
                            <TALLYMESSAGE>
                                <LEDGER NAME="{name}" ACTION="Alter">
                                    <NAME.LIST>
                                        <NAME>{name}</NAME>
                                    </NAME.LIST>
                                    <OPENINGBALANCE>{balance}</OPENINGBALANCE>
                                </LEDGER>
                            </TALLYMESSAGE>
                        </DATA>
                    </BODY>
                </ENVELOPE>
            """
            
            response = self.connector.send_request(xml_request)
            return "ALTERED" in response.upper() or "ACCEPTED" in response.upper()
        except Exception as e:
            return False


# Global instance
tally_ledger = TallyLedger()
