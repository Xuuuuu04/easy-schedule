import asyncio
import json
from typing import AsyncGenerator
from .ai_graph import run_agent_stream

async def process_chat_stream(message: str, thread_id: str) -> AsyncGenerator[str, None]:
    """
    Generates a streaming response from the LangGraph Agent.
    All output is NDJSON-formatted (Newline Delimited JSON).
    
    Format:
    {"type": "token", "content": "..."}      - Text generation chunk
    {"type": "tool_start", "name": "..."}    - Tool execution started
    {"type": "tool_end", "name": "..."}      - Tool execution finished
    {"type": "error", "content": "..."}      - Error message
    """
    try:
        async for chunk_json in run_agent_stream(message, thread_id):
            if chunk_json:
                yield chunk_json

    except Exception as e:
        # Standardized error format
        import traceback
        print(f"Error in chat stream: {e}")
        print(traceback.format_exc())
        
        error_payload = {
            "type": "error", 
            "content": "抱歉，我遇到了一些问题，请稍后再试。", 
            "debug": str(e)
        }
        yield json.dumps(error_payload, ensure_ascii=False) + "\n"
