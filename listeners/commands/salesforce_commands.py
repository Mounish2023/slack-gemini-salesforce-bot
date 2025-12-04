# """
# Slack slash commands for Salesforce integration
# """
# import logging
# from slack_bolt import Ack
# from salesforce.client import SalesforceClient

# logger = logging.getLogger(__name__)


# def handle_sf_accounts_command(ack: Ack, command, client):
#     """
#     Handle /sf-accounts slash command
#     Fetches and displays Salesforce account details
#     """
#     ack()
    
#     try:
#         sf_client = SalesforceClient()
        
#         # Parse command text for parameters
#         text = command.get("text", "").strip()
#         limit = 5
        
#         if text.isdigit():
#             limit = min(int(text), 20)  # Cap at 20 accounts
        
#         # Fetch accounts
#         accounts = sf_client.get_accounts(limit=limit)
        
#         # Build response blocks
#         blocks = [
#             {
#                 "type": "header",
#                 "text": {
#                     "type": "plain_text",
#                     "text": f"📊 Salesforce Accounts (Top {limit})"
#                 }
#             },
#             {
#                 "type": "divider"
#             }
#         ]
        
#         if accounts:
#             for idx, account in enumerate(accounts, 1):
#                 # Account header
#                 blocks.append({
#                     "type": "section",
#                     "text": {
#                         "type": "mrkdwn",
#                         "text": f"*{idx}. {account.get('Name', 'Unknown')}*"
#                     }
#                 })
                
#                 # Account details
#                 blocks.append({
#                     "type": "section",
#                     "fields": [
#                         {
#                             "type": "mrkdwn",
#                             "text": f"*ID:*\n`{account.get('Id', 'N/A')}`"
#                         },
#                         {
#                             "type": "mrkdwn",
#                             "text": f"*Type:*\n{account.get('Type', 'N/A')}"
#                         },
#                         {
#                             "type": "mrkdwn",
#                             "text": f"*Industry:*\n{account.get('Industry', 'N/A')}"
#                         },
#                         {
#                             "type": "mrkdwn",
#                             "text": f"*Phone:*\n{account.get('Phone', 'N/A')}"
#                         },
#                         {
#                             "type": "mrkdwn",
#                             "text": f"*Website:*\n{account.get('Website', 'N/A')}"
#                         },
#                         {
#                             "type": "mrkdwn",
#                             "text": f"*Location:*\n{account.get('BillingCity', 'N/A')}, {account.get('BillingState', '')}"
#                         }
#                     ]
#                 })
                
#                 # Action buttons for each account
#                 blocks.append({
#                     "type": "actions",
#                     "block_id": f"account_actions_{account.get('Id')}",
#                     "elements": [
#                         {
#                             "type": "button",
#                             "text": {
#                                 "type": "plain_text",
#                                 "text": "View Details"
#                             },
#                             "value": account.get('Id'),
#                             "action_id": f"view_account_{account.get('Id')}"
#                         },
#                         {
#                             "type": "button",
#                             "text": {
#                                 "type": "plain_text",
#                                 "text": "Get Contacts"
#                             },
#                             "value": account.get('Id'),
#                             "action_id": f"get_contacts_{account.get('Id')}"
#                         },
#                         {
#                             "type": "button",
#                             "text": {
#                                 "type": "plain_text",
#                                 "text": "Get Opportunities"
#                             },
#                             "value": account.get('Id'),
#                             "action_id": f"get_opportunities_{account.get('Id')}"
#                         }
#                     ]
#                 })
                
#                 blocks.append({"type": "divider"})
#         else:
#             blocks.append({
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": "❌ No accounts found in Salesforce."
#                 }
#             })
        
#         # Send response
#         client.chat_postMessage(
#             channel=command["channel_id"],
#             blocks=blocks,
#             text=f"Salesforce Accounts (Top {limit})"
#         )
        
#     except Exception as e:
#         logger.error(f"Error in /sf-accounts command: {e}", exc_info=True)
#         client.chat_postMessage(
#             channel=command["channel_id"],
#             text=f"❌ Error fetching Salesforce accounts: {str(e)}\n\nPlease ensure your Salesforce credentials are properly configured."
#         )


# def handle_sf_search_command(ack: Ack, command, client):
#     """
#     Handle /sf-search slash command
#     Searches for Salesforce accounts
#     """
#     ack()
    
#     try:
#         search_term = command.get("text", "").strip()
        
#         if not search_term:
#             client.chat_postMessage(
#                 channel=command["channel_id"],
#                 text="⚠️ Please provide a search term. Usage: `/sf-search <search term>`"
#             )
#             return
        
#         sf_client = SalesforceClient()
#         accounts = sf_client.search_accounts(search_term, limit=10)
        
#         blocks = [
#             {
#                 "type": "header",
#                 "text": {
#                     "type": "plain_text",
#                     "text": f"🔍 Search Results for '{search_term}'"
#                 }
#             },
#             {
#                 "type": "divider"
#             }
#         ]
        
#         if accounts:
#             for account in accounts:
#                 blocks.append({
#                     "type": "section",
#                     "fields": [
#                         {
#                             "type": "mrkdwn",
#                             "text": f"*Name:*\n{account.get('Name', 'N/A')}"
#                         },
#                         {
#                             "type": "mrkdwn",
#                             "text": f"*Type:*\n{account.get('Type', 'N/A')}"
#                         },
#                         {
#                             "type": "mrkdwn",
#                             "text": f"*Industry:*\n{account.get('Industry', 'N/A')}"
#                         },
#                         {
#                             "type": "mrkdwn",
#                             "text": f"*Phone:*\n{account.get('Phone', 'N/A')}"
#                         }
#                     ]
#                 })
#                 blocks.append({
#                     "type": "actions",
#                     "elements": [
#                         {
#                             "type": "button",
#                             "text": {
#                                 "type": "plain_text",
#                                 "text": "View Full Details"
#                             },
#                             "value": account.get('Id'),
#                             "action_id": f"view_account_{account.get('Id')}"
#                         }
#                     ]
#                 })
#                 blocks.append({"type": "divider"})
#         else:
#             blocks.append({
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": f"No accounts found matching '{search_term}'"
#                 }
#             })
        
#         client.chat_postMessage(
#             channel=command["channel_id"],
#             blocks=blocks,
#             text=f"Search results for '{search_term}'"
#         )
        
#     except Exception as e:
#         logger.error(f"Error in /sf-search command: {e}", exc_info=True)
#         client.chat_postMessage(
#             channel=command["channel_id"],
#             text=f"❌ Error searching Salesforce: {str(e)}"
#         )


# def register(app):
#     """Register Salesforce slash commands"""
#     app.command("/sf-accounts")(handle_sf_accounts_command)
#     app.command("/sf-search")(handle_sf_search_command)
    
#     logger.info("Salesforce command handlers registered")
