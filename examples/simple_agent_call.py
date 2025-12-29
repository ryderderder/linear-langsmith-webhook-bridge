#!/usr/bin/env python3
"""
Simple example of calling a LangSmith agent.
This demonstrates the basic SDK usage pattern.
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


async def run_agent():
    """
    Simple example: create a thread and send a message to the agent.
    """
    # 1) Create a new thread
    thread = await client.threads.create()
    thread_id = thread["thread_id"]
    print(f"Created thread: {thread_id}")
    
    # 2) Trigger a run with a user message
    run = await client.runs.create(
        thread_id,
        agent_id,
        input={
            "messages": [
                {"type": "human", "content": "Hello from Python!"}
            ]
        },
    )
    
    print(f"Run created: {run}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_agent())
