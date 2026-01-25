#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试 AI Agent 工具调用
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai_graph import run_agent_stream


async def test_agent():
    """测试 Agent 是否正确调用工具"""

    print("\n" + "="*60)
    print("  AI Agent Tool Invocation Test")
    print("="*60)

    test_questions = [
        "这周几节课",
        "今天有什么课",
        "查看王五的课程",
    ]

    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"  User: {question}")
        print(f"{'='*60}")

        tool_calls = []
        token_count = 0

        async for chunk in run_agent_stream(question, "test-session"):
            chunk = chunk.strip()
            if not chunk:
                continue

            try:
                # Parse JSON response
                if chunk.startswith("{"):
                    data = json.loads(chunk)
                    if data.get("type") == "tool":
                        tool_name = data.get("name")
                        tool_calls.append(tool_name)
                        print(f"  [TOOL] {tool_name}")
                    elif data.get("type") == "token":
                        token_count += 1
            except:
                pass

        print(f"\n  Tokens received: {token_count}")
        print(f"  Tools called: {len(tool_calls)}")

        if tool_calls:
            print(f"  OK - Tools were invoked")
        else:
            print(f"  WARNING - No tools were invoked!")

    print(f"\n{'='*60}")
    print("  Test Complete")
    print(f"{'='*60}")


if __name__ == "__main__":
    import json
    asyncio.run(test_agent())
