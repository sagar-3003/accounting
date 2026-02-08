"""
Tally stock/inventory operations
Create and manage stock items in Tally
"""

import xml.etree.ElementTree as ET
from typing import Optional, List, Dict
from tally.connection import tally_connector


class TallyStock:
    """Manager for Tally stock operations"""
    
    def __init__(self, connector=None):
        """Initialize with Tally connector"""
        self.connector = connector or tally_connector
    
    def create_stock_group(self, name: str, parent: str = "Primary") -> bool:
        """
        Create a stock group in Tally
        
        Args:
            name: Stock group name
            parent: Parent group (default: "Primary")
            
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
                                <STOCKGROUP NAME="{name}" ACTION="Create">
                                    <NAME.LIST>
                                        <NAME>{name}</NAME>
                                    </NAME.LIST>
                                    <PARENT>{parent}</PARENT>
                                </STOCKGROUP>
                            </TALLYMESSAGE>
                        </DATA>
                    </BODY>
                </ENVELOPE>
            """
            
            response = self.connector.send_request(xml_request)
            return "CREATED" in response.upper() or "ACCEPTED" in response.upper()
        except Exception as e:
            return False
    
    def create_stock_item(self, name: str, group: str, unit: str,
                         opening_qty: float = 0, opening_rate: float = 0,
                         hsn: str = "") -> bool:
        """
        Create a stock item in Tally
        
        Args:
            name: Stock item name
            group: Stock group name
            unit: Unit of measurement (e.g., "Pcs", "Kg")
            opening_qty: Opening quantity (default: 0)
            opening_rate: Opening rate per unit (default: 0)
            hsn: HSN/SAC code (optional)
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            opening_value = opening_qty * opening_rate
            
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
                                <STOCKITEM NAME="{name}" ACTION="Create">
                                    <NAME.LIST>
                                        <NAME>{name}</NAME>
                                    </NAME.LIST>
                                    <PARENT>{group}</PARENT>
                                    <BASEUNITS>{unit}</BASEUNITS>
                                    <OPENINGBALANCE>{opening_qty}</OPENINGBALANCE>
                                    <OPENINGVALUE>{opening_value}</OPENINGVALUE>
                                    <OPENINGRATE>{opening_rate}</OPENINGRATE>
            """
            
            if hsn:
                xml_request += f"""
                                    <GSTDETAILS.LIST>
                                        <HSNCODE>{hsn}</HSNCODE>
                                    </GSTDETAILS.LIST>
                """
            
            xml_request += """
                                </STOCKITEM>
                            </TALLYMESSAGE>
                        </DATA>
                    </BODY>
                </ENVELOPE>
            """
            
            response = self.connector.send_request(xml_request)
            return "CREATED" in response.upper() or "ACCEPTED" in response.upper()
        except Exception as e:
            return False
    
    def get_stock_summary(self) -> List[Dict]:
        """
        Get stock summary from Tally
        
        Returns:
            List of dicts with stock item details
        """
        try:
            xml_request = """
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Collection</TYPE>
                        <ID>StockSummary</ID>
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
            stock_items = []
            
            for item in root.findall('.//STOCKITEM'):
                name_elem = item.find('NAME')
                qty_elem = item.find('CLOSINGBALANCE')
                value_elem = item.find('CLOSINGVALUE')
                
                if name_elem is not None:
                    stock_items.append({
                        "name": name_elem.text,
                        "quantity": float(qty_elem.text) if qty_elem is not None else 0,
                        "value": float(value_elem.text) if value_elem is not None else 0
                    })
            
            return stock_items
        except Exception as e:
            return []
    
    def stock_item_exists(self, name: str) -> bool:
        """
        Check if a stock item exists in Tally
        
        Args:
            name: Stock item name
            
        Returns:
            True if exists, False otherwise
        """
        try:
            xml_request = f"""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>StockItemMaster</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                                <STOCKITEMNAME>{name}</STOCKITEMNAME>
                            </STATICVARIABLES>
                        </DESC>
                    </BODY>
                </ENVELOPE>
            """
            response = self.connector.send_request(xml_request)
            
            root = ET.fromstring(response)
            item_elem = root.find('.//STOCKITEM')
            
            return item_elem is not None
        except Exception as e:
            return False
    
    def update_stock(self, item: str, qty: float, rate: float) -> bool:
        """
        Update stock quantity and rate
        
        Args:
            item: Stock item name
            qty: New quantity
            rate: New rate
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            value = qty * rate
            
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
                                <STOCKITEM NAME="{item}" ACTION="Alter">
                                    <NAME.LIST>
                                        <NAME>{item}</NAME>
                                    </NAME.LIST>
                                    <OPENINGBALANCE>{qty}</OPENINGBALANCE>
                                    <OPENINGVALUE>{value}</OPENINGVALUE>
                                    <OPENINGRATE>{rate}</OPENINGRATE>
                                </STOCKITEM>
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
tally_stock = TallyStock()
