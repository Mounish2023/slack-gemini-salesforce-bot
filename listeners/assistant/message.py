# listeners/assistant/message.py
from logging import Logger
from typing import Dict, List

from slack_bolt import BoltContext, Say, SetStatus
from slack_sdk import WebClient

import os
import asyncio
import json

# Google Gemini SDK (new official package)
from google import genai
from google.genai import types

# Your MCP client
from salesforce.mcp_client import MCPClient

from ..views.feedback_block import create_feedback_block

# Configure Gemini once
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
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
        # client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        # ----- Load MCP tools -----
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

        # ----- Track conversation state ourselves -----
        conversation: List[types.Content] = []
        conversation.extend(history)
        conversation.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_query)]
            )
        )

        # ----- Tool / generation loop -----
        while True:
            import re
            import json

            # inside your while True after calling generate_content(...)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=config,
                contents=conversation,
            )

            parts = response.candidates[0].content.parts
#  response.candidates[0].content.parts[0].function_call:
            # collect function_call parts, stream any other text parts immediately
            function_calls = []
            for part in parts:
                if hasattr(part, "function_call") and part.function_call:
                    function_calls.append(part.function_call)
                # elif hasattr(part, "text") and part.text:
                #     # THIS is the important change — stream actual text parts (final answer will be here)
                #     streamer.append(markdown_text=part.text)

            # if model didn't request any tool, we're done (we already streamed final text parts)
            if not function_calls:
                streamer.append(markdown_text=part.text)
                break

            # # helper to parse fc.args safely
            # def _parse_fc_args(fc_args):
            #     if isinstance(fc_args, dict):
            #         return fc_args
            #     if isinstance(fc_args, str):
            #         # try plain json
            #         try:
            #             return json.loads(fc_args)
            #         except Exception:
            #             # try to extract JSON inside fenced blocks
            #             m = re.search(r'```(?:json)?\s*(\{.*\})\s*```', fc_args, re.S) or \
            #                 re.search(r'~~~\s*(?:json)?\s*(\{.*\})', fc_args, re.S)
            #             if m:
            #                 try:
            #                     return json.loads(m.group(1))
            #                 except Exception:
            #                     pass
            #             # fallback: raw
            #             return {"__raw_args__": fc_args}
            #     try:
            #         return dict(fc_args)
            #     except Exception:
            #         return {"__raw_args__": str(fc_args)}

            tool_parts = []
            for fc in function_calls:
                tool_name = fc.name
                # args = _parse_fc_args(fc.args)
                args = fc.args

                # streamer.append(
                #     markdown_text=(
                #         f"\nCalling `{tool_name}` with arguments:\n"
                #         f"```json\n{json.dumps(args, indent=2)}\n```"
                #     )
                # )

                try:
                    result = await mcp_client.session.call_tool(tool_name, args)
                    # Create a function response part
                    function_response_part = types.Part.from_function_response(
                        name=tool_name,
                        response={"result": result},
                    )   
                    conversation.append(response.candidates[0].content) # Append the content from the model's response.
                    conversation.append(types.Content(role="user", parts=[function_response_part])) # Append the function response

                    # client = genai.Client()
                    final_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        config=config,
                        contents=conversation,
                    )
                    streamer.append(final_response.text)
                    # tool_output = final_response.candidates[0].content if hasattr(final_response.candidates[0], "content") else str(final_response.candidates[0])
                except Exception as e:
                    tool_output = f"Tool error: {str(e)}"
                    logger.exception(f"Tool {tool_name} failed")

                # tool_parts.append(
                #     types.Part(
                #         function_response=types.FunctionResponse(
                #             name=tool_name,
                #             response={"content": tool_output},
                #         )
                #     )
                # )

            # # append tool responses so the model can consume them next loop
            # conversation.append(
            #     types.Content(
            #         role="tool",
            #         parts=tool_parts,
            #     )
            # )
            # loop continues — next generate_content call will produce the model's post-tool final answer,
            # which will be streamed above because we stream non-function_call parts.


    except Exception as e:
        logger.exception("Error in Gemini + MCP tool loop")
        streamer.append(
            markdown_text=f":warning: Something went wrong: {e}"
        )


def message(
    client: WebClient,
    context: BoltContext,
    logger: Logger,
    payload: dict,
    say: Say,
    set_status: SetStatus,
):
    """Synchronous entry point – we spawn an async task safely"""
    try:
        channel_id = payload["channel"]
        team_id = context.team_id
        thread_ts = payload.get("thread_ts") or payload["ts"]
        user_id = context.user_id

        set_status(status="thinking...", loading_messages=[
            "Spinning up Salesforce tools...",
            "Waking up the AI...",
            "Connecting to your org...",
        ])

        # === Get thread history ===
        replies = client.conversations_replies(
            channel=context.channel_id,
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

        # === Start MCP + Gemini ===
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
                # await mcp_client.cleanup()
                pass

        # Run the async task
        asyncio.run(main_task())

    except Exception as e:
        logger.exception(f"Unhandled error in message handler: {e}")
        say(f":warning: Oops! Something broke: {e}")