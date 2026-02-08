"""
Tally connection manager
Handles XML over HTTP communication with Tally ERP/Prime
"""

import requests
import xml.etree.ElementTree as ET
from typing import Optional
import config


class TallyConnector:
    """
    Manager for Tally ERP/Prime XML over HTTP connections
    """
    
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize Tally connector
        
        Args:
            host: Tally host (default: from config)
            port: Tally port (default: from config)
        """
        self.host = host or config.TALLY_HOST
        self.port = port or config.TALLY_PORT
        self.url = f"http://{self.host}:{self.port}"
        self.timeout = config.TALLY_TIMEOUT
    
    def is_connected(self) -> bool:
        """
        Check if Tally is reachable
        
        Returns:
            True if connected, False otherwise
        """
        try:
            response = self.send_request("""
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Collection</TYPE>
                        <ID>List of Companies</ID>
                    </HEADER>
                    <BODY>
                        <DESC>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            </STATICVARIABLES>
                        </DESC>
                    </BODY>
                </ENVELOPE>
            """)
            return bool(response)
        except Exception as e:
            return False
    
    def send_request(self, xml: str) -> str:
        """
        Send XML request to Tally and get response
        
        Args:
            xml: XML request string
            
        Returns:
            XML response string
            
        Raises:
            ConnectionError: If unable to connect to Tally
            TimeoutError: If request times out
        """
        try:
            headers = {'Content-Type': 'application/xml'}
            response = requests.post(
                self.url,
                data=xml.encode('utf-8'),
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Unable to connect to Tally at {self.url}. "
                                "Please ensure Tally is running and HTTP access is enabled.")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request to Tally timed out after {self.timeout} seconds.")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error communicating with Tally: {str(e)}")
    
    def get_company_name(self) -> Optional[str]:
        """
        Get the currently active company name in Tally
        
        Returns:
            Company name or None if not available
        """
        try:
            xml_request = """
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Data</TYPE>
                        <ID>CurrentCompany</ID>
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
            response = self.send_request(xml_request)
            
            # Parse response
            root = ET.fromstring(response)
            company = root.find('.//CURRENTCOMPANYNAME')
            if company is not None:
                return company.text
            
            # Fallback: try to get from company list
            xml_request = """
                <ENVELOPE>
                    <HEADER>
                        <VERSION>1</VERSION>
                        <TALLYREQUEST>Export</TALLYREQUEST>
                        <TYPE>Collection</TYPE>
                        <ID>List of Companies</ID>
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
            response = self.send_request(xml_request)
            root = ET.fromstring(response)
            
            # Get first company that's loaded
            for company in root.findall('.//COMPANY'):
                name_elem = company.find('NAME')
                loaded_elem = company.find('LOADED')
                if name_elem is not None and loaded_elem is not None:
                    if loaded_elem.text == 'Yes':
                        return name_elem.text
            
            return None
        except Exception as e:
            return None
    
    def test_connection(self) -> dict:
        """
        Test Tally connection and return status info
        
        Returns:
            Dict with connection status and details
        """
        result = {
            "connected": False,
            "url": self.url,
            "company": None,
            "error": None
        }
        
        try:
            if self.is_connected():
                result["connected"] = True
                result["company"] = self.get_company_name()
            else:
                result["error"] = "Unable to connect to Tally"
        except Exception as e:
            result["error"] = str(e)
        
        return result


# Global connector instance
tally_connector = TallyConnector()
