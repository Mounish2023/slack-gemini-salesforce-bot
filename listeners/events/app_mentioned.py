# listeners/events/app_mentioned.py
from logging import Logger
from typing import List
import os
import asyncio
import json

from slack_bolt import Say
from slack_sdk import WebClient

# Google Gemini SDK
from google import genai
from google.genai import types

# MCP client
from salesforce.mcp_client import MCPClient

from ..views.feedback_block import create_feedback_block

# Configure Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

UNSUPPORTED_SCHEMA_KEYS = {
    "additional_properties",
    "additionalProperties",
    "unevaluatedProperties",
    "$schema",
    "$ref",
    "definitions",
    "examples",
    "default",
}

def sanitize_schema(schema: dict) -> dict:
    """Recursively remove fields Gemini does not support."""
    if isinstance(schema, dict):
        cleaned = {}
        for k, v in schema.items():
            if k in UNSUPPORTED_SCHEMA_KEYS:
                continue
            cleaned[k] = sanitize_schema(v)
        return cleaned
    elif isinstance(schema, list):
        return [sanitize_schema(i) for i in schema]
    else:
        return schema


async def _run_gemini_with_tools(
    user_query: str,
    history: List[types.Content],
    mcp_client: MCPClient,
    streamer,
    logger: Logger,
):
    try:
        # Load MCP tools
        resp = await mcp_client.session.list_tools()

        function_declarations = []
        for tool in resp.tools:
            schema = tool.inputSchema
            if isinstance(schema, str):
                schema = json.loads(schema)

            schema = sanitize_schema(schema)

            function_declarations.append({
                "name": tool.name,
                "description": tool.description or "No description available",
                "parameters": schema,
            })

        gemini_tool = types.Tool(function_declarations=function_declarations)
        config = types.GenerateContentConfig(tools=[gemini_tool])

        # Track conversation state
        conversation: List[types.Content] = []
        conversation.extend(history)
        conversation.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_query)]
            )
        )

        # Tool / generation loop
        while True:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=config,
                contents=conversation,
            )

            parts = response.candidates[0].content.parts
            
            # Collect function_call parts
            function_calls = []
            for part in parts:
                if hasattr(part, "function_call") and part.function_call:
                    function_calls.append(part.function_call)

            # If model didn't request any tool, we're done
            if not function_calls:
                streamer.append(markdown_text=part.text)
                break

            # Execute tool calls
            for fc in function_calls:
                tool_name = fc.name
                args = fc.args

                try:
                    result = await mcp_client.session.call_tool(tool_name, args)
                    # Create a function response part
                    function_response_part = types.Part.from_function_response(
                        name=tool_name,
                        response={"result": result},
                    )   
                    conversation.append(response.candidates[0].content)
                    conversation.append(types.Content(role="user", parts=[function_response_part]))

                    final_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        config=config,
                        contents=conversation,
                    )
                    streamer.append(final_response.text)
                except Exception as e:
                    tool_output = f"Tool error: {str(e)}"
                    logger.exception(f"Tool {tool_name} failed")

    except Exception as e:
        logger.exception("Error in Gemini + MCP tool loop")
        streamer.append(
            markdown_text=f":warning: Something went wrong: {e}"
        )


def app_mentioned_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    """
    Handles the event when the app is mentioned in a Slack conversation
    and generates an AI response using Gemini with Salesforce MCP tools.

    Args:
        client: Slack WebClient for making API calls
        event: Event payload containing mention details (channel, user, text, etc.)
        logger: Logger instance for error tracking
        say: Function to send messages to the thread from the app
    """
    try:
        channel_id = event.get("channel")
        team_id = event.get("team")
        text = event.get("text")
        thread_ts = event.get("thread_ts") or event.get("ts")
        user_id = event.get("user")

        client.assistant_threads_setStatus(
            channel_id=channel_id,
            thread_ts=thread_ts,
            status="thinking...",
            loading_messages=[
                "Spinning up Salesforce tools...",
                "Waking up the AI...",
                "Connecting to your org...",
            ],
        )

        # Get thread history
        replies = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            inclusive=True,
            limit=20,
        )

        messages_in_thread = []
        for msg in replies["messages"]:
            role = "user" if not msg.get("bot_id") else "model"
            messages_in_thread.append({"role": role, "content": msg["text"]})

        # Build Gemini history (exclude latest message)
        history = [
            types.Content(role=msg["role"], parts=[types.Part(text=msg["content"])])
            for msg in messages_in_thread[:-1]
        ]
        user_query = messages_in_thread[-1]["content"]

        # Start MCP + Gemini
        async def main_task():
            mcp_client = MCPClient()
            server_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../salesforce/salesforce_mcp_server.py")
            )
            await mcp_client.connect_to_server(server_path)

            streamer = client.chat_stream(
                channel=channel_id,
                recipient_team_id=team_id,
                recipient_user_id=user_id,
                thread_ts=thread_ts,
            )

            try:
                await _run_gemini_with_tools(
                    user_query=user_query,
                    history=history,
                    mcp_client=mcp_client,
                    streamer=streamer,
                    logger=logger,
                )

                feedback_block = create_feedback_block()
                streamer.stop(blocks=feedback_block)
            finally:
                pass

        # Run the async task
        asyncio.run(main_task())

    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        say(f":warning: Something went wrong! ({e})")
