"""
Salesforce REST API Client
Handles OAuth authentication and API requests to Salesforce
"""
import os
import logging
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class SalesforceClient:
    """Client for interacting with Salesforce REST API"""
    
    def __init__(self, auto_auth: bool = False):
        """Initialize Salesforce client with OAuth credentials from environment
        
        Args:
            auto_auth: If True, automatically authenticate using client_credentials grant type
        """
        self.client_id = os.environ.get("SALESFORCE_CLIENT_ID")
        self.client_secret = os.environ.get("SALESFORCE_CLIENT_SECRET")
        # self.redirect_uri = os.environ.get("SALESFORCE_REDIRECT_URI")
        self.instance_url = os.environ.get("SALESFORCE_INSTANCE_URL")
        self.access_token = None
        # self.refresh_token = os.environ.get("SALESFORCE_REFRESH_TOKEN")
        # print(self.client_id)
        # print(self.client_secret)
        # print(self.instance_url)
        if not all([self.client_id, self.client_secret]):
            logger.warning("Salesforce credentials not fully configured")
        
        # Auto-authenticate using client_credentials if requested
        if auto_auth and self.client_id and self.client_secret:
            try:
                self.authenticate_client_credentials()
            except Exception as e:
                logger.error(f"Auto-authentication failed: {e}")
    
    def authenticate_client_credentials(self) -> Dict[str, Any]:
        """
        Authenticate using client_credentials grant type (server-to-server OAuth)
        This flow is designed for server-to-server authentication and provides
        long-lived access tokens without requiring user interaction.
        
        Returns:
            Dictionary containing access_token, instance_url, and other token details
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("SALESFORCE_CLIENT_ID and SALESFORCE_CLIENT_SECRET are required")
        
        # Use instance_url if set, otherwise use default login URL
        base_url = self.instance_url or os.environ.get("SALESFORCE_INSTANCE_URL", "https://orgfarm-f2b8e19683-dev-ed.develop.my.salesforce.com")
        # Remove /services/oauth2/token if already in instance_url
        if "/services/oauth2/token" in base_url:
            token_url = base_url
        else:
            token_url = f"{base_url}/services/oauth2/token"
        
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        logger.info(f"Authenticating with client_credentials grant type to {token_url}")
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        
        token_data = response.json()
        
        # Store tokens
        self.access_token = token_data.get("access_token")
        self.instance_url = token_data.get("instance_url")
        
        logger.info(f"Successfully authenticated with client_credentials. Instance: {self.instance_url}")
        return token_data
    
    def get_api_version(self) -> str:
        """Get the latest API version, defaults to v59.0"""
        return os.environ.get("SALESFORCE_API_VERSION", "v59.0")
    
    def get_accounts(self, limit: int = 10, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve Salesforce accounts
        
        Args:
            limit: Maximum number of accounts to retrieve
            fields: List of fields to retrieve (defaults to common fields)
            
        Returns:
            List of account dictionaries
        """
        if fields is None:
            fields = ["Id", "Name", "Type", "Industry", "Phone", "Website", "BillingCity", "BillingState"]
        
        fields_str = ", ".join(fields)
        query = f"SELECT {fields_str} FROM Account LIMIT {limit}"
        
        endpoint = f"/services/data/{self.get_api_version()}/query"
        params = {"q": query}
        
        response = self._make_request("GET", endpoint, params=params)
        return response.get("records", [])
    
    def get_account_by_id(self, account_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Retrieve a specific Salesforce account by ID
        
        Args:
            account_id: Salesforce Account ID
            fields: List of fields to retrieve
            
        Returns:
            Account dictionary
        """
        if fields:
            fields_str = ",".join(fields)
            endpoint = f"/services/data/{self.get_api_version()}/sobjects/Account/{account_id}?fields={fields_str}"
        else:
            endpoint = f"/services/data/{self.get_api_version()}/sobjects/Account/{account_id}"
        
        return self._make_request("GET", endpoint)
    
    def search_accounts(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for accounts by name or other fields
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching accounts
        """
        # Using SOSL (Salesforce Object Search Language)
        search_query = f"FIND {{{search_term}}} IN ALL FIELDS RETURNING Account(Id, Name, Type, Industry, Phone, Website) LIMIT {limit}"
        
        endpoint = f"/services/data/{self.get_api_version()}/search"
        params = {"q": search_query}
        
        response = self._make_request("GET", endpoint, params=params)
        search_records = response.get("searchRecords", [])
        
        # Extract just the Account records
        return [record for record in search_records]
    
    def create_account(self, account_data: Dict[str, Any]) -> str:
        """
        Create a new Salesforce account
        
        Args:
            account_data: Dictionary containing account fields (e.g., {"Name": "Acme Corp", "Type": "Customer"})
            
        Returns:
            ID of the created account
        """
        endpoint = f"/services/data/{self.get_api_version()}/sobjects/Account"
        
        response = self._make_request("POST", endpoint, json=account_data)
        return response.get("id")
    
    def update_account(self, account_id: str, account_data: Dict[str, Any]) -> bool:
        """
        Update an existing Salesforce account
        
        Args:
            account_id: Salesforce Account ID
            account_data: Dictionary containing fields to update
            
        Returns:
            True if successful
        """
        endpoint = f"/services/data/{self.get_api_version()}/sobjects/Account/{account_id}"
        
        self._make_request("PATCH", endpoint, json=account_data)
        return True
    
    def delete_account(self, account_id: str) -> bool:
        """
        Delete a Salesforce account
        
        Args:
            account_id: Salesforce Account ID
            
        Returns:
            True if successful
        """
        endpoint = f"/services/data/{self.get_api_version()}/sobjects/Account/{account_id}"
        
        self._make_request("DELETE", endpoint)
        return True
    
    def get_account_opportunities(self, account_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get opportunities associated with an account
        
        Args:
            account_id: Salesforce Account ID
            limit: Maximum number of opportunities to retrieve
            
        Returns:
            List of opportunity dictionaries
        """
        query = f"SELECT Id, Name, StageName, Amount, CloseDate FROM Opportunity WHERE AccountId = '{account_id}' LIMIT {limit}"
        
        endpoint = f"/services/data/{self.get_api_version()}/query"
        params = {"q": query}
        
        response = self._make_request("GET", endpoint, params=params)
        return response.get("records", [])
    
    def get_account_contacts(self, account_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get contacts associated with an account
        
        Args:
            account_id: Salesforce Account ID
            limit: Maximum number of contacts to retrieve
            
        Returns:
            List of contact dictionaries
        """
        query = f"SELECT Id, Name, Email, Phone, Title FROM Contact WHERE AccountId = '{account_id}' LIMIT {limit}"
        
        endpoint = f"/services/data/{self.get_api_version()}/query"
        params = {"q": query}
        
        response = self._make_request("GET", endpoint, params=params)
        return response.get("records", [])
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an authenticated HTTP request to Salesforce API
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint path (e.g., /services/data/v59.0/query)
            **kwargs: Additional arguments to pass to requests (params, json, etc.)
            
        Returns:
            JSON response from Salesforce
        """
        if not self.access_token:
            # Try to authenticate if we don't have a token
            if self.client_id and self.client_secret:
                self.authenticate_client_credentials()
            else:
                raise ValueError("No access token. Please authenticate first.")
        
        if not self.instance_url:
            raise ValueError("Instance URL not configured")
        
        url = f"{self.instance_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        
        # DELETE requests may not return JSON
        if method == "DELETE":
            return {}
        
        return response.json()
