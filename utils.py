"""
Utility functions for the webhook bridge.
"""

import logging
import sys
from typing import Dict, Any
from datetime import datetime

from config import Config


def setup_logging() -> logging.Logger:
    """
    Configure application logging.
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('webhook_bridge')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    
    # Console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


def format_linear_event(event_type: str, event_data: Dict[str, Any]) -> str:
    """
    Format Linear event data into a readable message for the agent.
    
    Args:
        event_type: Type of Linear event
        event_data: Event payload data
    
    Returns:
        Formatted message string
    """
    try:
        # Common fields
        event_id = event_data.get('id', 'unknown')
        
        if event_type == 'Issue':
            return format_issue_event(event_data)
        elif event_type == 'Comment':
            return format_comment_event(event_data)
        elif event_type == 'Project':
            return format_project_event(event_data)
        else:
            # Generic format for unknown event types
            return (
                f"New {event_type} event (ID: {event_id})\n\n"
                f"Event data: {event_data}"
            )
    
    except Exception as e:
        logging.error(f"Error formatting Linear event: {e}")
        return f"Linear {event_type} event received with data: {event_data}"


def format_issue_event(data: Dict[str, Any]) -> str:
    """
    Format an Issue event into a readable message.
    """
    title = data.get('title', 'Untitled')
    description = data.get('description', 'No description')
    state = data.get('state', {}).get('name', 'Unknown')
    priority = data.get('priority', 'None')
    assignee = data.get('assignee', {}).get('name', 'Unassigned')
    team = data.get('team', {}).get('name', 'Unknown team')
    identifier = data.get('identifier', '')
    url = data.get('url', '')
    
    message = f"""📋 Linear Issue Updated

**Issue:** {identifier} - {title}
**Team:** {team}
**Status:** {state}
**Priority:** {priority}
**Assignee:** {assignee}

**Description:**
{description}

**Link:** {url}
"""
    
    return message


def format_comment_event(data: Dict[str, Any]) -> str:
    """
    Format a Comment event into a readable message.
    """
    body = data.get('body', 'No content')
    author = data.get('user', {}).get('name', 'Unknown user')
    issue = data.get('issue', {})
    issue_title = issue.get('title', 'Unknown issue')
    issue_identifier = issue.get('identifier', '')
    url = data.get('url', '')
    
    message = f"""💬 New Comment on Linear Issue

**Issue:** {issue_identifier} - {issue_title}
**Author:** {author}

**Comment:**
{body}

**Link:** {url}
"""
    
    return message


def format_project_event(data: Dict[str, Any]) -> str:
    """
    Format a Project event into a readable message.
    """
    name = data.get('name', 'Untitled project')
    description = data.get('description', 'No description')
    state = data.get('state', 'Unknown')
    lead = data.get('lead', {}).get('name', 'No lead')
    url = data.get('url', '')
    
    message = f"""🎯 Linear Project Updated

**Project:** {name}
**Lead:** {lead}
**State:** {state}

**Description:**
{description}

**Link:** {url}
"""
    
    return message
