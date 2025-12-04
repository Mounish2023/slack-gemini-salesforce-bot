# Salesforce MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with Salesforce accounts, opportunities, and contacts.

## Features

- **Server-to-Server Authentication**: Uses OAuth 2.0 client_credentials grant type
- **8 Comprehensive Tools**: Full CRUD operations for Salesforce accounts
- **Automatic Authentication**: Handles token management automatically
- **Error Handling**: Proper error handling and logging throughout

## Available Tools

### Account Management

1. **get_accounts** - Retrieve a list of Salesforce accounts
   - Parameters: `limit` (int), `fields` (array)
   - Returns: List of accounts with details

2. **get_account_by_id** - Get a specific account by ID
   - Parameters: `account_id` (string), `fields` (array)
   - Returns: Detailed account information

3. **search_accounts** - Search accounts using SOSL
   - Parameters: `search_term` (string), `limit` (int)
   - Returns: Matching accounts

4. **create_account** - Create a new account
   - Parameters: `account_data` (object with Name, Type, Industry, etc.)
   - Returns: Created account ID

5. **update_account** - Update an existing account
   - Parameters: `account_id` (string), `account_data` (object)
   - Returns: Success confirmation

6. **delete_account** - Delete an account
   - Parameters: `account_id` (string)
   - Returns: Success confirmation

### Related Data

7. **get_account_opportunities** - Get opportunities for an account
   - Parameters: `account_id` (string), `limit` (int)
   - Returns: List of opportunities with stage, amount, close date

8. **get_account_contacts** - Get contacts for an account
   - Parameters: `account_id` (string), `limit` (int)
   - Returns: List of contacts with name, email, phone, title

## Setup

### Prerequisites

```bash
pip install -r requirements.txt
```

### Environment Variables

Add these to your `.env` file:

```bash
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
```

### Running the Server

```bash
# Run directly
python -m salesforce.salesforce_mcp_server

# Or from the salesforce directory
cd salesforce
python salesforce_mcp_server.py
```

## Usage Examples

### With MCP Client

```python
from mcp import ClientSession

async with ClientSession(server_url="stdio:python -m salesforce.salesforce_mcp_server") as session:
    # List available tools
    tools = await session.list_tools()
    
    # Call a tool
    result = await session.call_tool("get_accounts", {
        "limit": 10,
        "fields": ["Id", "Name", "Industry", "Phone"]
    })
    print(result)
```

### Direct Client Usage

```python
from salesforce.client import SalesforceClient

# Auto-authenticate and get accounts
client = SalesforceClient(auto_auth=True)
accounts = client.get_accounts(limit=10)

for account in accounts:
    print(f"{account['Name']} - {account['Industry']}")
```

## Authentication Flow

The server uses the **client_credentials** OAuth 2.0 grant type:

1. Server starts and initializes `SalesforceClient` with `auto_auth=True`
2. Client makes POST request to `/services/oauth2/token` with:
   - `grant_type=client_credentials`
   - `client_id` from environment
   - `client_secret` from environment
3. Salesforce returns long-lived access token and instance URL
4. Token is automatically used for all subsequent API requests
5. If token expires, client automatically re-authenticates

## Error Handling

All tools include comprehensive error handling:

- **Authentication Errors**: Logged with details about missing credentials
- **API Errors**: Salesforce API errors are caught and returned as text
- **Validation Errors**: Input validation with helpful error messages
- **Network Errors**: Connection issues are logged and reported

## Logging

The server logs important events:

```
INFO: Starting Salesforce MCP Server...
INFO: Authenticating with client_credentials grant type to https://...
INFO: Successfully authenticated with client_credentials. Instance: https://...
INFO: Salesforce client initialized successfully
```

## Security Notes

- Never commit your `.env` file to version control
- Client credentials should be stored securely
- Use environment variables for all sensitive data
- The access token is stored in memory only and never logged

## Development

### Testing

```bash
# Run the test script
python test_salesforce_client.py
```

### Adding New Tools

1. Add the tool definition in `list_tools()`
2. Implement the handler in `call_tool()`
3. Use the existing `SalesforceClient` methods or add new ones

## Troubleshooting

**"SALESFORCE_CLIENT_ID and SALESFORCE_CLIENT_SECRET are required"**
- Make sure `.env` file exists and contains the required variables
- Check that `python-dotenv` is installed

**"Authentication failed: 403"**
- Verify your client_id and client_secret are correct
- Ensure your Salesforce Connected App has client_credentials flow enabled

**"No access token available"**
- The client will automatically authenticate on first API call
- Check your network connection to Salesforce instance

## License

See the main repository LICENSE file.
