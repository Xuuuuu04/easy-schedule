import asyncio
import sys
import os

# Add current directory to sys.path to ensure backend module is found
sys.path.append(os.getcwd())

from backend.ai_graph import run_agent_stream

async def test_context():
    print("--- Test Start ---")
    thread_id = "test_thread_1"
    
    # Turn 1: Set Context
    print("User: My name is Alice.")
    response_text_1 = ""
    async for chunk in run_agent_stream("My name is Alice.", thread_id=thread_id):
        # chunk is a json string
        import json
        data = json.loads(chunk)
        if data["type"] == "token":
            response_text_1 += data["content"]
            print(data["content"], end="", flush=True)
    print("\n")
    
    # Turn 2: Query Context
    print("User: What is my name?")
    response_text_2 = ""
    async for chunk in run_agent_stream("What is my name?", thread_id=thread_id):
        import json
        data = json.loads(chunk)
        if data["type"] == "token":
            response_text_2 += data["content"]
            print(data["content"], end="", flush=True)
    print("\n")
    
    if "Alice" in response_text_2:
        print("✅ SUCCESS: Context preserved.")
    else:
        print("❌ FAILURE: Context lost.")

if __name__ == "__main__":
    asyncio.run(test_context())
