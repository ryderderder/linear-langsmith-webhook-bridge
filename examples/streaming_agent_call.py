#!/usr/bin/env python3
"""
Example of calling a LangSmith agent with streaming responses.
This is the pattern used by the webhook bridge.
"""

import os
from dotenv import load_dotenv
from langgraph_sdk import get_client

load_dotenv()

# Configuration from environment
agent_id = os.getenv("LANGSMITH_AGENT_ID")
api_key = os.getenv("LANGSMITH_API_KEY")
api_url = os.getenv("LANGSMITH_API_URL")

# Initialize client
client = get_client(
    url=api_url,
    api_key=api_key,
    headers={
        "X-Auth-Scheme": "langsmith-api-key",
    },
)


async def run_agent_with_streaming():
    """
    Example: create a thread and stream the agent's response.
    """
    # 1) Create a new thread
    thread = await client.threads.create()
    thread_id = thread["thread_id"]
    print(f"Created thread: {thread_id}")
    
    # 2) Stream the agent's response
    print("Agent response: ", end="", flush=True)
    
    response_chunks = []
    async for chunk in client.runs.stream(
        thread_id=thread_id,
        assistant_id=agent_id,
        input={
            "messages": [
                {"type": "human", "content": "Tell me a short joke!"}
            ]
        },
        stream_mode="events"
    ):
        # Extract content from streaming chunks
        if chunk.get("event") == "on_chat_model_stream":
            if "data" in chunk and "chunk" in chunk["data"]:
                content = chunk["data"]["chunk"].get("content")
                if content:
                    response_chunks.append(content)
                    print(content, end="", flush=True)
    
    print("\n")  # New line after streaming completes
    
    full_response = "".join(response_chunks)
    print(f"\nFull response ({len(full_response)} chars): {full_response}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_agent_with_streaming())
