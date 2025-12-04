"""
Test script for Salesforce client_credentials authentication
"""
import os
from dotenv import load_dotenv
from salesforce.client import SalesforceClient

# Load environment variables
load_dotenv()

def test_client_credentials():
    """Test client_credentials authentication"""
    print("=" * 60)
    print("Testing Salesforce Client with client_credentials grant type")
    print("=" * 60)
    
    # Test 1: Manual authentication
    print("\n1. Testing manual authentication...")
    try:
        client = SalesforceClient()
        token_data = client.authenticate_client_credentials()
        print(f"✓ Authentication successful!")
        print(f"  Instance URL: {token_data.get('instance_url')}")
        print(f"  Token type: {token_data.get('token_type')}")
        print(f"  Access token: {token_data.get('access_token')[:20]}...")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return
    
    # Test 2: Auto authentication
    print("\n2. Testing auto-authentication...")
    try:
        client2 = SalesforceClient(auto_auth=True)
        print(f"✓ Auto-authentication successful!")
        print(f"  Instance URL: {client2.instance_url}")
    except Exception as e:
        print(f"✗ Auto-authentication failed: {e}")
    
    # Test 3: Get accounts
    print("\n3. Testing get_accounts...")
    try:
        accounts = client.get_accounts(limit=5)
        print(f"✓ Retrieved {len(accounts)} accounts:")
        for acc in accounts:
            print(f"  - {acc.get('Name', 'N/A')} (ID: {acc.get('Id', 'N/A')})")
    except Exception as e:
        print(f"✗ Failed to get accounts: {e}")
    
    # Test 4: Search accounts
    print("\n4. Testing search_accounts...")
    try:
        search_results = client.search_accounts("Test", limit=3)
        print(f"✓ Found {len(search_results)} accounts matching 'Test'")
        for acc in search_results:
            print(f"  - {acc.get('Name', 'N/A')}")
    except Exception as e:
        print(f"✗ Search failed: {e}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_client_credentials()
