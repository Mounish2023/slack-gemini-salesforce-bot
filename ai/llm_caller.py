import os
from typing import Dict, List, Iterator, Any

from google import genai
from dotenv import load_dotenv

load_dotenv()

DEFAULT_SYSTEM_CONTENT = """
You're an assistant in a Slack workspace.
Users in the workspace will ask you to help them write something or to think better about a specific topic.
You'll respond to those questions in a professional way.
When you include markdown text, convert them to Slack compatible ones.
When a prompt has Slack's special syntax like <@USER_ID> or <#CHANNEL_ID>, you must keep them as-is in your response.
"""


def call_llm(
    messages_in_thread: List[Dict[str, str]],
    system_content: str = DEFAULT_SYSTEM_CONTENT,
    tools: List[Dict[str, Any]] = None,
):
    """
    Call Google Gemini API with message thread and return streaming response.
    
    Args:
        messages_in_thread: List of message dicts with 'role' and 'content' keys
        system_content: System prompt to prepend to the conversation
    
    Returns:
        Iterator of GenerateContentResponse objects for streaming
    """
    # Convert OpenAI-style messages to Gemini format
    # Gemini uses dict format: {'role': 'user'|'model', 'parts': [{'text': '...'}]}
    gemini_contents = []
    
    # Add system content as the first user/model exchange
    if system_content:
        gemini_contents.append({
            'role': 'user',
            'parts': [{'text': system_content}]
        })
        gemini_contents.append({
            'role': 'model',
            'parts': [{'text': "Understood. I'll assist users in the Slack workspace professionally."}]
        })
    
    # Convert remaining messages to Gemini format
    for msg in messages_in_thread:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        # Map roles: 'assistant' -> 'model', 'user' stays 'user'
        # Skip 'system' role if any (already handled above)
        if role == "system":
            continue
        elif role == "assistant":
            gemini_role = "model"
        else:
            gemini_role = "user"
        
        gemini_contents.append({
            'role': gemini_role,
            'parts': [{'text': content}]
        })
    
    # Use context manager to ensure client stays open during streaming
    with genai.Client(api_key=os.environ.get("GOOGLE_API_KEY")) as client:
        # Generate streaming response
        response_stream = client.models.generate_content_stream(
            model="gemini-2.0-flash-exp",
            contents=gemini_contents,
            config={'tools': tools} if tools else None,
        )
        
        # Consume and cache all chunks immediately while client is alive
        cached_chunks = []
        for chunk in response_stream:
            cached_chunks.append(chunk)
    
    # Return a generator that yields the cached chunks
    # Client is now safely closed after stream consumption
    return iter(cached_chunks)
