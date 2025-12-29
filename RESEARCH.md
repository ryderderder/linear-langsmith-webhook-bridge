# Research-Informed Updates

This document summarizes the documentation research conducted and how it informed the repository improvements.

## Research Summary

### Linear API/Webhooks Documentation

**Sources:**
- [Linear Webhook Documentation](https://developers.linear.app/docs/graphql/webhooks)
- [Linear API and Webhooks](https://linear.app/docs/api-and-webhooks)
- Multiple implementation examples and best practices guides

**Key Findings:**

1. **Webhook Delivery Mechanism**
   - Linear sends HTTP POST requests to your configured URL (the "callback URL")
   - Must be publicly accessible HTTPS (non-localhost)
   - Expects HTTP 200 response within 5 seconds
   - Retries failed deliveries: 1 minute, 1 hour, 6 hours (max 3 attempts)
   - Webhook may be disabled after 3 consecutive failures

2. **Security Implementation**
   - Uses HMAC-SHA256 for signature verification
   - Signature is **hexadecimal-encoded** (not base64)
   - Signing secret provided on webhook detail page in Linear
   - Must verify against **raw request body** (before JSON parsing)
   - Header: `Linear-Signature: <hex_digest>`

3. **Payload Structure**
   - Follows GraphQL entity schema
   - Common fields: `action`, `type`, `data`, `createdAt`, `updatedFrom`, `webhookTimestamp`
   - Event types: Issue, Comment, Project, Cycle, Label, IssueLabel, Reaction
   - Includes `webhookTimestamp` for replay attack protection

4. **HTTP Headers Sent by Linear**
   ```
   Linear-Signature: <hmac_sha256_hex>
   Linear-Delivery: <uuid>
   Linear-Event: <event_type>
   Content-Type: application/json; charset=utf-8
   ```

5. **Rate Limits**
   - API key authentication: 1,500 requests/hour per user
   - Complexity-based: 250,000 points/hour per user

### LangSmith Documentation

**Sources:**
- [LangSmith Agent Builder Documentation](https://docs.langchain.com/langsmith/agent-builder)
- [LangGraph SDK Reference](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)
- LangSmith alerting and automation documentation

**Key Findings:**

1. **Agent Builder Architecture**
   - Agents are called via SDK/API, **not through webhooks**
   - No webhook endpoints for triggering agents
   - Authentication via Personal Access Token (PAT)
   - Header required: `X-Auth-Scheme: langsmith-api-key`

2. **Message Format**
   - Correct format: `{"type": "human", "content": "..."}`
   - Not: `{"role": "user", "content": "..."}` (this was fixed in main.py)

3. **LangSmith Webhooks (Different Purpose)**
   - LangSmith **has** webhooks, but they're **OUTGOING**
   - Used for: alerts, automation rules, prompt syncing
   - LangSmith sends data TO other services
   - Not relevant for our use case (we need to call agents)

4. **SDK Usage Patterns**
   - Simple invocation: `client.runs.create()`
   - Streaming: `client.runs.stream()` with `stream_mode="events"`
   - Thread-based conversations
   - Async execution supported

## Repository Improvements Made

### 1. Fixed Message Format

**Before:**
```python
{"role": "user", "content": "..."}
```

**After:**
```python
{"type": "human", "content": "..."}
```

This matches the LangSmith SDK specification exactly.

### 2. Corrected Security Implementation

**Verified:**
- HMAC-SHA256 with hexadecimal encoding (`.hexdigest()`)
- Signature verification using raw request body
- Constant-time comparison with `hmac.compare_digest()`
- Proper header name: `Linear-Signature`

### 3. Added Comprehensive Documentation

**New Files:**
- `ARCHITECTURE.md` - Detailed explanation of webhook flow and why we need a bridge
- Research-based clarifications in README.md

**Key Clarifications:**
- Explained why LangSmith agents can't receive webhooks directly
- Documented Linear's retry behavior and timeouts
- Clarified "callback URL" terminology
- Added security best practices from official docs

### 4. Added Test Script

Based on SDK documentation, created `test_langsmith_connection.py`:
- Tests both simple and streaming invocations
- Validates message format
- Provides clear feedback on configuration issues

### 5. Added Example Scripts

Created `examples/` directory with:
- Simple SDK usage example
- Streaming response example
- Both using correct message format

### 6. Updated Environment Variables

Clarified in `.env.example`:
```bash
# Get from Linear webhook detail page (after creation)
LINEAR_SIGNING_SECRET=lin_whsec_xxxxxxxxxxxx

# Must be PAT with X-Auth-Scheme: langsmith-api-key
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxx
```

## Technical Accuracy Improvements

### Webhook Verification

**Based on Linear docs:**
```python
# Correct implementation (as in our code)
signature = hmac.new(
    secret.encode('utf-8'),
    payload,           # Raw bytes
    hashlib.sha256
).hexdigest()          # Hex, not base64!

# Compare with Linear-Signature header
return hmac.compare_digest(signature, header_signature)
```

### Callback URL Setup

**Accurate instructions added:**
1. Deploy bridge first (get HTTPS URL)
2. Create webhook in Linear with this URL
3. Copy signing secret FROM Linear (not generated by us)
4. Add secret to bridge environment
5. Test delivery through Linear's interface

### Rate Limit Documentation

**Accurate numbers from APIs:**
- Linear: 1,500 req/hour per user (API key auth)
- Our bridge: 50 req/min per IP, 100/hour overall
- LangSmith: Plan-dependent (noted in docs)

## Architecture Clarification

### What We Initially Missed

The documentation research revealed important distinctions:

1. **LangSmith's webhooks are OUTGOING**: For sending alerts/notifications
2. **Agent Builder uses SDK**: No webhook URLs for triggering agents
3. **Bridge is required**: Can't connect Linear → LangSmith directly

### Corrected Architecture Diagram

```
┌──────────┐         ┌─────────────┐         ┌──────────────┐
│  Linear  │─POST───>│   Bridge    │─SDK───>│  LangSmith   │
│ Webhooks │         │ (This Repo) │  Call  │    Agent     │
└──────────┘         └─────────────┘         └──────────────┘
   OUTGOING             Middleware              SDK Invoked
```

Not:
```
Linear → LangSmith (Direct - this doesn't exist)
```

## Files Updated Based on Research

1. **main.py**
   - Fixed message format to `{"type": "human", ...}`
   - Verified signature verification algorithm
   - Confirmed header names and structure

2. **README.md**
   - Added architecture explanation
   - Clarified "callback URL" terminology
   - Added webhook retry behavior
   - Included signing secret setup process

3. **ARCHITECTURE.md** (NEW)
   - Comprehensive technical documentation
   - Explains why bridge is needed
   - Documents both API behaviors
   - Security implementation details

4. **test_langsmith_connection.py** (NEW)
   - Based on SDK documentation
   - Tests correct message format
   - Validates credentials before deployment

5. **examples/** (NEW)
   - Simple and streaming examples
   - Both using correct SDK patterns
   - Documentation for each approach

## Validation

All improvements were validated against:
- Official Linear webhook documentation
- LangSmith Agent Builder documentation
- LangGraph SDK reference
- Security best practices for HMAC verification
- Real-world implementation examples

## Future Considerations

Based on research, potential future enhancements:

1. **Timestamp Validation**: Use `webhookTimestamp` to prevent replay attacks
2. **IP Whitelisting**: Linear doesn't publish webhook IPs, rely on signature instead
3. **Webhook Payload Types**: Add TypeScript-style types for better type safety
4. **Enhanced Logging**: Include more Linear-specific headers in logs
5. **Metrics**: Track delivery IDs, response times, retry patterns

## References

All updates were informed by:
- https://developers.linear.app/docs/graphql/webhooks
- https://docs.langchain.com/langsmith/agent-builder
- https://hookdeck.com/webhooks/guides/how-to-implement-sha256-webhook-signature-verification
- https://github.com/linear/linear (official Linear repo)
- LangGraph SDK documentation

---

**Last Updated**: December 29, 2025
**Research Date**: December 29, 2025
