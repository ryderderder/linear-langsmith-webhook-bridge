#!/usr/bin/env python3
"""
Test script to verify LangSmith agent connection.
Run this before deploying to ensure your credentials are correct.

Usage:
    python test_langsmith_connection.py
"""

import os
import asyncio
from dotenv import load_dotenv
from langgraph_sdk import get_client

# Load environment variables
load_dotenv()

# Configuration
AGENT_ID = os.getenv("LANGSMITH_AGENT_ID")
API_KEY = os.getenv("LANGSMITH_API_KEY")
API_URL = os.getenv("LANGSMITH_API_URL")

# Validate configuration
if not all([AGENT_ID, API_KEY, API_URL]):
    print("❌ Error: Missing required environment variables")
    print("Please set: LANGSMITH_AGENT_ID, LANGSMITH_API_KEY, LANGSMITH_API_URL")
    exit(1)

print("🔧 Testing LangSmith Connection")
print(f"API URL: {API_URL}")
print(f"Agent ID: {AGENT_ID}")
print("-" * 50)

# Initialize client
client = get_client(
    url=API_URL,
    api_key=API_KEY,
    headers={
        "X-Auth-Scheme": "langsmith-api-key",
    },
)


async def test_agent_simple():
    """Test basic agent invocation without streaming."""
    print("\n📤 Test 1: Simple agent invocation")
    try:
        # Create a new thread
        thread = await client.threads.create()
        thread_id = thread["thread_id"]
        print(f"✅ Thread created: {thread_id}")
        
        # Trigger a run with a test message
        run = await client.runs.create(
            thread_id,
            AGENT_ID,
            input={
                "messages": [
                    {"type": "human", "content": "Hello! This is a test message from the webhook bridge setup script."}
                ]
            },
        )
        print(f"✅ Run created: {run}")
        print("✅ Simple invocation successful!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_agent_streaming():
    """Test agent invocation with streaming (as used in the webhook bridge)."""
    print("\n📤 Test 2: Streaming agent invocation")
    try:
        # Create a new thread
        thread = await client.threads.create()
        thread_id = thread["thread_id"]
        print(f"✅ Thread created: {thread_id}")
        
        # Trigger a streaming run
        print("📥 Streaming response...")
        response_chunks = []
        
        async for chunk in client.runs.stream(
            thread_id=thread_id,
            assistant_id=AGENT_ID,
            input={
                "messages": [
                    {"type": "human", "content": "Say 'hello' back to confirm you're working!"}
                ]
            },
            stream_mode="events"
        ):
            # Collect response chunks
            if chunk.get("event") == "on_chat_model_stream":
                if "data" in chunk and "chunk" in chunk["data"]:
                    content = chunk["data"]["chunk"].get("content")
                    if content:
                        response_chunks.append(content)
                        print(".", end="", flush=True)
        
        response_text = "".join(response_chunks)
        print(f"\n✅ Received response: {response_text[:100]}..." if len(response_text) > 100 else f"\n✅ Received response: {response_text}")
        print("✅ Streaming invocation successful!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests."""
    print("\n" + "="*50)
    print("🧪 Running LangSmith Agent Tests")
    print("="*50)
    
    test1_passed = await test_agent_simple()
    test2_passed = await test_agent_streaming()
    
    print("\n" + "="*50)
    print("📊 Test Results")
    print("="*50)
    print(f"Simple invocation: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Streaming invocation: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Your LangSmith connection is working correctly.")
        print("You can now deploy the webhook bridge with confidence.")
    else:
        print("\n⚠️  Some tests failed. Please check:")
        print("1. Your LANGSMITH_API_KEY is correct and has proper permissions")
        print("2. Your LANGSMITH_API_URL is correct")
        print("3. Your LANGSMITH_AGENT_ID matches an existing agent")
        print("4. The agent is deployed and accessible")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
