import asyncio
import json
from typing import AsyncGenerator
from .ai_graph import run_agent_stream

async def process_chat_stream(message: str, thread_id: str = "default") -> AsyncGenerator[str, None]:
    """
    Generates a streaming response from the LangGraph Agent.
    All output is JSON-formatted for SSE compatibility.
    """
    try:
        # thread_id is now passed from the frontend
        async for text_chunk in run_agent_stream(message, thread_id):
            if text_chunk:
                yield text_chunk

    except Exception as e:
        # 返回 JSON 格式的错误信息
        error_json = json.dumps({"type": "error", "content": str(e)})
        yield error_json + "\n"
