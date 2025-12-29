# Linear to LangSmith Webhook Bridge

Production-ready webhook receiver that triggers LangSmith agents when Linear events occur.

## Features

✅ **Secure Webhook Verification**
- Linear signature verification using HMAC-SHA256
- Optional secret token authentication
- Rate limiting to prevent abuse

✅ **Production Ready**
- Comprehensive error handling and logging
- Health check endpoint for monitoring
- Configurable event filtering
- Async agent execution

✅ **Easy Deployment**
- Deploy to Replit, Railway, or any Python hosting
- Environment-based configuration
- Simple setup process

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/ryderderder/linear-langsmith-webhook-bridge.git
cd linear-langsmith-webhook-bridge
cp .env.example .env
```

### 2. Get Your LangSmith Credentials

1. Open your LangSmith Agent Builder
2. Navigate to your agent
3. Click the settings icon → "View code snippets"
4. Copy:
   - Agent ID
   - API URL
   - API Key (create a Personal Access Token if needed)

### 3. Configure Environment Variables

Edit `.env` with your credentials:

```env
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxx
LANGSMITH_API_URL=https://your-deployment.langsmith.com
LANGSMITH_AGENT_ID=your-agent-id
LINEAR_SIGNING_SECRET=lin_whsec_xxxxxxxxxxxx
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Test Your LangSmith Connection (Recommended)

Before deploying, verify your credentials work:

```bash
python test_langsmith_connection.py
```

This will:
- ✅ Test basic agent invocation
- ✅ Test streaming agent responses (as used in production)
- ✅ Verify all credentials are correct

**Expected output:**
```
🧪 Running LangSmith Agent Tests
==================================================
📤 Test 1: Simple agent invocation
✅ Thread created: thread-xyz
✅ Run created: {...}
✅ Simple invocation successful!

📤 Test 2: Streaming agent invocation
✅ Thread created: thread-abc
📥 Streaming response...
✅ Received response: Hello! This is...
✅ Streaming invocation successful!

📊 Test Results
==================================================
Simple invocation: ✅ PASS
Streaming invocation: ✅ PASS

🎉 All tests passed! Your LangSmith connection is working correctly.
```

If tests fail, check:
- API key has correct permissions
- Agent ID matches your agent
- API URL is correct and includes `https://`

### 6. Run Locally (Testing)

```bash
python main.py
```

The server will start on `http://localhost:8080`

### 7. Deploy to Production

#### Option A: Deploy to Replit

1. Go to [Replit](https://replit.com)
2. Import from GitHub: `ryderderder/linear-langsmith-webhook-bridge`
3. Add Secrets (Environment Variables):
   - Click "Secrets" (🔒) in the left sidebar
   - Add each variable from `.env.example`
4. Click "Run" - Replit will automatically install dependencies
5. Copy your Replit URL (e.g., `https://your-repl.your-username.repl.co`)

#### Option B: Deploy to Railway

1. Go to [Railway](https://railway.app)
2. "New Project" → "Deploy from GitHub repo"
3. Select your forked repository
4. Add environment variables in Railway dashboard
5. Railway will auto-deploy and provide a URL

### 8. Configure Linear Webhook

1. In Linear, go to **Settings** → **API** → **Webhooks**
2. Click **Create Webhook**
3. Configure:
   - **URL**: `https://your-deployment-url.com/webhook/linear?token=YOUR_SECRET_TOKEN`
   - **Events**: Select events you want (Issues, Comments, Projects, etc.)
   - **Secret**: Copy the signing secret to your `LINEAR_SIGNING_SECRET` env var
4. Click **Create**
5. Test with "Send test delivery"

## Configuration Options

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LANGSMITH_API_KEY` | Your LangSmith API key | `lsv2_pt_...` |
| `LANGSMITH_API_URL` | Your agent's API URL | `https://xxx.langsmith.com` |
| `LANGSMITH_AGENT_ID` | Your agent's ID | `agent-xxx` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LINEAR_SIGNING_SECRET` | Linear webhook signing secret (recommended) | None |
| `LINEAR_EVENT_FILTER` | Comma-separated event types to process | All events |
| `WEBHOOK_SECRET_TOKEN` | Additional URL token for security | None |
| `LOG_LEVEL` | Logging verbosity (DEBUG/INFO/WARNING/ERROR) | INFO |
| `PORT` | Server port | 8080 |

### Event Filtering

To only trigger your agent for specific Linear events:

```env
# Only process issues and comments
LINEAR_EVENT_FILTER=Issue,Comment

# Process all events (leave empty)
LINEAR_EVENT_FILTER=
```

Supported event types:
- `Issue` - Issue created, updated, deleted
- `Comment` - Comments on issues
- `Project` - Project changes
- `Cycle` - Cycle changes
- `Label` - Label changes

## API Endpoints

### `POST /webhook/linear`

Receives Linear webhook events and triggers your LangSmith agent.

**Query Parameters:**
- `token` (optional): Secret token for additional authentication

**Headers:**
- `Linear-Signature`: HMAC signature for verification
- `Linear-Delivery`: Unique webhook delivery ID

**Response:**
```json
{
  "status": "success",
  "webhook_id": "delivery-id",
  "thread_id": "langsmith-thread-id",
  "message": "Agent triggered successfully"
}
```

### `GET /health`

Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "linear-langsmith-webhook-bridge",
  "timestamp": "2025-12-29T07:00:00.000Z"
}
```

## Security Best Practices

1. **Always use HTTPS** - Replit and Railway provide this automatically
2. **Enable signature verification** - Set `LINEAR_SIGNING_SECRET`
3. **Use secret token** - Add `?token=SECRET` to your webhook URL
4. **Rate limiting** - Built-in protection (50 req/min per IP)
5. **Keep secrets safe** - Never commit `.env` to git

## Event Formatting

The bridge formats Linear events into readable messages for your agent:

### Issue Event
```
📋 Linear Issue Updated

Issue: ENG-123 - Fix login bug
Team: Engineering
Status: In Progress
Priority: High
Assignee: John Doe

Description:
Users are unable to log in with SSO...

Link: https://linear.app/your-team/issue/ENG-123
```

### Comment Event
```
💬 New Comment on Linear Issue

Issue: ENG-123 - Fix login bug
Author: Jane Smith

Comment:
I've investigated this and found the root cause...

Link: https://linear.app/...
```

## Monitoring and Logs

### View Logs

**Replit:**
- Check the Console tab

**Railway:**
- Go to your deployment → "Logs" tab

### Log Levels

Set `LOG_LEVEL` to control verbosity:
- `DEBUG` - Detailed information for debugging
- `INFO` - General operational information (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages only

### Example Log Output

```
[2025-12-29 07:00:00] INFO [webhook_bridge] Configuration validated successfully
[2025-12-29 07:00:01] INFO [webhook_bridge] LangSmith client initialized successfully
[2025-12-29 07:00:02] INFO [webhook_bridge] Starting webhook bridge on port 8080
[2025-12-29 07:01:15] INFO [webhook_bridge] Received Linear webhook abc123: type=Issue, action=update
[2025-12-29 07:01:16] INFO [webhook_bridge] Created thread thread-xyz for webhook abc123
[2025-12-29 07:01:18] INFO [webhook_bridge] Agent completed for webhook abc123. Response length: 245 chars
```

## Troubleshooting

### Webhook Not Triggering

1. Check webhook URL is correct and accessible
2. Verify Linear signing secret matches
3. Check event filters aren't blocking the event
4. Review logs for error messages

### Agent Not Responding

1. **Run the test script first**: `python test_langsmith_connection.py`
2. Verify LangSmith credentials are correct
3. Check agent ID matches your Agent Builder agent
4. Ensure API URL includes `https://`
5. Test the agent directly in Agent Builder

### Authentication Errors

1. Regenerate your LangSmith API key
2. Verify `LINEAR_SIGNING_SECRET` is set correctly
3. Check `WEBHOOK_SECRET_TOKEN` matches URL parameter

### Rate Limiting

If you hit rate limits (429 errors):
- Default: 100 requests per hour
- Endpoint: 50 requests per minute
- Wait for the limit window to reset
- Contact Anthropic for higher limits if needed

## Development

### Local Development with Ngrok

1. Install [ngrok](https://ngrok.com/)
2. Start your local server: `python main.py`
3. In another terminal: `ngrok http 8080`
4. Use the ngrok URL for Linear webhook

### Testing

```bash
# Test LangSmith connection
python test_langsmith_connection.py

# Test health endpoint
curl http://localhost:8080/health

# Test webhook endpoint (with mock data)
curl -X POST http://localhost:8080/webhook/linear?token=YOUR_TOKEN \
  -H "Content-Type: application/json" \
  -d '{"type":"Issue","action":"update","data":{"title":"Test Issue"}}'
```

## Support

- **LangSmith Docs**: https://docs.langchain.com/langsmith/agent-builder
- **Linear API Docs**: https://developers.linear.app/docs/graphql/webhooks
- **Issues**: https://github.com/ryderderder/linear-langsmith-webhook-bridge/issues

## License

MIT License - feel free to use and modify for your needs.
