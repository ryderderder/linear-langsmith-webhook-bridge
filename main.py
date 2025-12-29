#!/usr/bin/env python3
"""
Linear to LangSmith Webhook Bridge
Production-ready webhook receiver that triggers LangSmith agents from Linear events.
"""

import os
import hmac
import hashlib
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from langgraph_sdk import get_client
from dotenv import load_dotenv

from config import Config, validate_config
from utils import setup_logging, format_linear_event

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Setup logging
logger = setup_logging()

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://"
)

# Validate configuration on startup
try:
    validate_config()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Initialize LangSmith client
try:
    client = get_client(
        url=Config.LANGSMITH_API_URL,
        api_key=Config.LANGSMITH_API_KEY,
        headers={"X-Auth-Scheme": "langsmith-api-key"}
    )
    logger.info("LangSmith client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LangSmith client: {e}")
    raise


def verify_linear_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify the Linear webhook signature.
    
    Args:
        payload: Raw request body
        signature: Signature from Linear-Signature header
        secret: Webhook signing secret
    
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not secret:
        return False
    
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False


def require_webhook_auth(f):
    """
    Decorator to validate webhook authentication.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check secret token if configured
        if Config.WEBHOOK_SECRET_TOKEN:
            token = request.args.get('token')
            if token != Config.WEBHOOK_SECRET_TOKEN:
                logger.warning(f"Invalid webhook token from {request.remote_addr}")
                return jsonify({"error": "Unauthorized"}), 401
        
        # Verify Linear signature if configured
        if Config.LINEAR_SIGNING_SECRET:
            signature = request.headers.get('Linear-Signature')
            if not verify_linear_signature(
                request.get_data(),
                signature,
                Config.LINEAR_SIGNING_SECRET
            ):
                logger.warning(f"Invalid Linear signature from {request.remote_addr}")
                return jsonify({"error": "Invalid signature"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


async def trigger_langsmith_agent(
    event_type: str,
    event_data: Dict[str, Any],
    webhook_id: str
) -> Dict[str, Any]:
    """
    Trigger the LangSmith agent with Linear event data.
    
    Args:
        event_type: Type of Linear event (e.g., 'Issue', 'Comment')
        event_data: Event payload from Linear
        webhook_id: Unique identifier for this webhook delivery
    
    Returns:
        Response from the agent
    """
    try:
        # Create a new thread for this interaction
        thread = await client.threads.create()
        thread_id = thread["thread_id"]
        
        logger.info(f"Created thread {thread_id} for webhook {webhook_id}")
        
        # Format the event for the agent
        formatted_message = format_linear_event(event_type, event_data)
        
        # Prepare input for the agent (using correct message format)
        agent_input = {
            "messages": [{
                "type": "human",
                "content": formatted_message
            }],
            "metadata": {
                "webhook_id": webhook_id,
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Triggering agent {Config.LANGSMITH_AGENT_ID} with event {event_type}")
        
        # Stream the agent's response
        agent_response = []
        async for chunk in client.runs.stream(
            thread_id=thread_id,
            assistant_id=Config.LANGSMITH_AGENT_ID,
            input=agent_input,
            stream_mode="events"
        ):
            # Collect response chunks
            if chunk.get("event") == "on_chat_model_stream":
                if "data" in chunk and "chunk" in chunk["data"]:
                    content = chunk["data"]["chunk"].get("content")
                    if content:
                        agent_response.append(content)
        
        response_text = "".join(agent_response)
        
        logger.info(
            f"Agent completed for webhook {webhook_id}. "
            f"Response length: {len(response_text)} chars"
        )
        
        return {
            "success": True,
            "thread_id": thread_id,
            "response": response_text
        }
    
    except Exception as e:
        logger.error(f"Error triggering agent for webhook {webhook_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.
    """
    return jsonify({
        "status": "healthy",
        "service": "linear-langsmith-webhook-bridge",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route('/webhook/linear', methods=['POST'])
@limiter.limit("50 per minute")
@require_webhook_auth
def handle_linear_webhook():
    """
    Main webhook endpoint for Linear events.
    """
    webhook_id = request.headers.get('Linear-Delivery', 'unknown')
    
    try:
        # Parse webhook payload
        payload = request.get_json()
        
        if not payload:
            logger.warning(f"Empty payload received from {request.remote_addr}")
            return jsonify({"error": "Empty payload"}), 400
        
        # Extract event details
        action = payload.get('action', 'unknown')
        event_type = payload.get('type', 'unknown')
        data = payload.get('data', {})
        
        logger.info(
            f"Received Linear webhook {webhook_id}: "
            f"type={event_type}, action={action}"
        )
        
        # Filter events if configured
        if Config.LINEAR_EVENT_FILTER:
            if event_type not in Config.LINEAR_EVENT_FILTER:
                logger.info(f"Skipping filtered event type: {event_type}")
                return jsonify({
                    "status": "filtered",
                    "message": f"Event type {event_type} not in filter"
                }), 200
        
        # Trigger agent asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                trigger_langsmith_agent(event_type, data, webhook_id)
            )
        finally:
            loop.close()
        
        if result["success"]:
            return jsonify({
                "status": "success",
                "webhook_id": webhook_id,
                "thread_id": result["thread_id"],
                "message": "Agent triggered successfully"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "webhook_id": webhook_id,
                "error": result["error"]
            }), 500
    
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON payload from {request.remote_addr}")
        return jsonify({"error": "Invalid JSON"}), 400
    
    except Exception as e:
        logger.error(f"Unexpected error handling webhook {webhook_id}: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": "Internal server error"
        }), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Handle rate limit exceeded.
    """
    logger.warning(f"Rate limit exceeded from {request.remote_addr}")
    return jsonify({
        "error": "Rate limit exceeded",
        "message": str(e.description)
    }), 429


@app.errorhandler(500)
def internal_error_handler(e):
    """
    Handle internal server errors.
    """
    logger.error(f"Internal server error: {e}", exc_info=True)
    return jsonify({
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting webhook bridge on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
