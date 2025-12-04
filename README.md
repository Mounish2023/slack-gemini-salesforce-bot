# Slack Gemini Salesforce Bot

A powerful Slack bot that integrates Google Gemini AI with Salesforce using the Model Context Protocol (MCP). This bot enables natural language interactions with your Salesforce data directly from Slack, providing intelligent responses and automated CRM operations.

## 🌟 Features

- **AI-Powered Conversations**: Uses Google Gemini 2.5 Flash for intelligent, context-aware responses
- **Salesforce Integration**: Full CRUD operations for Salesforce accounts, contacts, and opportunities
- **MCP Architecture**: Leverages Model Context Protocol for robust tool integration
- **Slack Assistant**: Native Slack assistant interface with suggested prompts and thread support
- **Real-time Streaming**: Streams AI responses in real-time for better user experience
- **Feedback System**: Built-in thumbs up/down feedback mechanism for response quality

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Slack     │────────▶│  Bolt Python │────────▶│   Gemini    │
│   User      │         │   Bot App    │         │   AI Model  │
└─────────────┘         └──────────────┘         └─────────────┘
                               │                         │
                               │                         │
                               ▼                         ▼
                        ┌──────────────┐         ┌─────────────┐
                        │  MCP Client  │────────▶│ MCP Server  │
                        └──────────────┘         └─────────────┘
                                                         │
                                                         ▼
                                                  ┌─────────────┐
                                                  │  Salesforce │
                                                  │     API     │
                                                  └─────────────┘
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Slack workspace with admin access
- Google Gemini API key
- Salesforce Connected App with OAuth credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/slack-gemini-salesforce-bot.git
   cd slack-gemini-salesforce-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Copy `env_template.txt` to `.env` and fill in your credentials:
   ```bash
   cp env_template.txt .env
   ```

   Required variables:
   ```bash
   # Slack Configuration
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   SLACK_APP_TOKEN=xapp-your-app-token
   
   # Salesforce Configuration
   SALESFORCE_CLIENT_ID=your_salesforce_consumer_key
   SALESFORCE_CLIENT_SECRET=your_salesforce_consumer_secret
   SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
   
   # Google Gemini
   GOOGLE_API_KEY=your_google_api_key
   ```

### Slack App Setup

1. Create a new Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Enable Socket Mode and generate an App-Level Token
3. Add the following bot token scopes:
   - `app_mentions:read`
   - `assistant:write`
   - `im:history`
   - `chat:write`
4. Subscribe to bot events:
   - `assistant_thread_started`
   - `message.im`
   - `app_mention`
5. Install the app to your workspace

### Salesforce Connected App Setup

1. In Salesforce Setup, create a new Connected App:
   - Enable OAuth Settings
   - Enable "Client Credentials Flow"
   - Select required OAuth scopes (at minimum: `api`, `refresh_token`)
2. Note your Consumer Key (Client ID) and Consumer Secret
3. Configure your instance URL

### Running the Bot

```bash
python app.py
```

The bot will start and connect to Slack via Socket Mode.

## 💬 Usage

### Starting a Conversation

1. Open the bot's direct message in Slack
2. The assistant will greet you with suggested prompts
3. Ask questions or request Salesforce operations

### Example Interactions

**Retrieve Accounts:**
```
@bot Show me the top 5 accounts
```

**Search for Accounts:**
```
@bot Find accounts related to "Acme"
```

**Get Account Details:**
```
@bot Get details for account ID 001XXXXXXXXXX
```

**Create an Account:**
```
@bot Create a new account named "TechCorp" in the Technology industry
```

**Update an Account:**
```
@bot Update account 001XXXXXXXXXX to change the phone number to 555-1234
```

**Get Related Records:**
```
@bot Show me all opportunities for account 001XXXXXXXXXX
@bot List contacts for account 001XXXXXXXXXX
```

## 🛠️ Available Salesforce Operations

The bot supports the following operations through natural language:

| Operation | Description |
|-----------|-------------|
| `get_accounts` | Retrieve a list of accounts with customizable fields and limit |
| `get_account_by_id` | Get detailed information for a specific account |
| `search_accounts` | Search accounts using SOSL |
| `create_account` | Create a new account with specified fields |
| `update_account` | Update existing account fields |
| `delete_account` | Delete an account (use with caution) |
| `get_account_opportunities` | Retrieve opportunities for an account |
| `get_account_contacts` | Retrieve contacts for an account |

## 📁 Project Structure

```
slack-gemini-salesforce-bot/
├── app.py                          # Main application entry point
├── requirements.txt                # Python dependencies
├── manifest.json                   # Slack app manifest
├── .env                           # Environment variables (not in repo)
├── ai/
│   └── llm_caller.py              # Gemini AI integration
├── listeners/
│   ├── __init__.py                # Listener registration
│   ├── actions/                   # Action handlers
│   ├── assistant/                 # Assistant message handlers
│   ├── events/                    # Event handlers
│   ├── commands/                  # Slash command handlers
│   └── views/                     # UI components
└── salesforce/
    ├── client.py                  # Salesforce REST API client
    ├── mcp_client.py              # MCP client wrapper
    ├── salesforce_mcp_server.py   # MCP server implementation
    └── README.md                  # Salesforce MCP documentation
```

## 🔐 Security Considerations

- **Never commit `.env` files** - Contains sensitive credentials
- **Use environment variables** for all secrets
- **Client credentials flow** provides server-to-server authentication without user interaction
- **Token management** is handled automatically by the Salesforce client
- **Validate user inputs** before passing to Salesforce API

## 🐛 Troubleshooting

### Authentication Issues

**Error: "SALESFORCE_CLIENT_ID and SALESFORCE_CLIENT_SECRET are required"**
- Verify your `.env` file exists and contains the required variables
- Ensure `python-dotenv` is installed

**Error: "Authentication failed: 403"**
- Check that your client ID and secret are correct
- Verify your Connected App has client credentials flow enabled
- Confirm your user has API access

### Connection Issues

**Bot doesn't respond in Slack**
- Verify Socket Mode is enabled in your Slack app
- Check that your `SLACK_APP_TOKEN` is correct
- Ensure bot event subscriptions are configured

**Salesforce API errors**
- Verify your instance URL is correct
- Check your Salesforce API version (default: v59.0)
- Ensure your user has appropriate permissions

## 🧪 Testing

Run the Salesforce client tests:

```bash
python tests/test_salesforce_client.py
```

This will test:
- Client credentials authentication
- Account retrieval
- Account search
- Error handling

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Slack Bolt for Python](https://slack.dev/bolt-python/)
- Powered by [Google Gemini AI](https://ai.google.dev/)
- Integrates with [Salesforce REST API](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/)
- Uses [Model Context Protocol (MCP)](https://github.com/anthropics/mcp)

## 📧 Support

For issues, questions, or contributions, please open an issue on GitHub or contact the maintainers.

---

Made with ❤️ by [Mounish Sunkara](https://github.com/yourusername)