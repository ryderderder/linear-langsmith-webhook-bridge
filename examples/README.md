# LangSmith SDK Examples

Simple examples demonstrating how to use the LangSmith SDK to call agents.

## Prerequisites

Make sure you've configured your environment variables in `.env`:
```env
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxx
LANGSMITH_API_URL=https://your-deployment.langsmith.com
LANGSMITH_AGENT_ID=your-agent-id
```

## Examples

### 1. Simple Agent Call (`simple_agent_call.py`)

The most basic example - creates a thread and sends a single message.

```bash
python examples/simple_agent_call.py
```

**What it does:**
- Creates a new conversation thread
- Sends a message: "Hello from Python!"
- Uses `client.runs.create()` for simple, non-streaming execution

**Use case:** When you just need to trigger an agent and don't need to see the response in real-time.

---

### 2. Streaming Agent Call (`streaming_agent_call.py`)

Shows how to stream agent responses in real-time (as used in the webhook bridge).

```bash
python examples/streaming_agent_call.py
```

**What it does:**
- Creates a new conversation thread
- Streams the agent's response as it's generated
- Uses `client.runs.stream()` with `stream_mode="events"`
- Displays response chunks as they arrive

**Use case:** When you want to see the agent's response progressively, like in the webhook bridge production code.

---

## Message Format

Both examples use the correct message format for LangSmith SDK:

```python
{
    "messages": [
        {"type": "human", "content": "Your message here"}
    ]
}
```

**Not** `{"role": "user", ...}` - that's a different format!

## Authentication

The examples use the same authentication headers as the production webhook bridge:

```python
headers={"X-Auth-Scheme": "langsmith-api-key"}
```

This tells LangSmith you're using a Personal Access Token (PAT) for authentication.

## Next Steps

- Run `test_langsmith_connection.py` in the root directory for comprehensive testing
- Check out `main.py` to see how these patterns are used in production
- Read the main README for full deployment instructions
