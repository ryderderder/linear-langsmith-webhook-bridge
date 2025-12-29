"""
Configuration management for the webhook bridge.
"""

import os
from typing import List, Optional


class Config:
    """
    Application configuration loaded from environment variables.
    """
    
    # LangSmith Configuration
    LANGSMITH_API_KEY: str = os.getenv('LANGSMITH_API_KEY', '')
    LANGSMITH_API_URL: str = os.getenv('LANGSMITH_API_URL', '')
    LANGSMITH_AGENT_ID: str = os.getenv('LANGSMITH_AGENT_ID', '')
    
    # Linear Configuration
    LINEAR_SIGNING_SECRET: Optional[str] = os.getenv('LINEAR_SIGNING_SECRET')
    LINEAR_EVENT_FILTER: Optional[List[str]] = (
        os.getenv('LINEAR_EVENT_FILTER', '').split(',') 
        if os.getenv('LINEAR_EVENT_FILTER') 
        else None
    )
    
    # Security
    WEBHOOK_SECRET_TOKEN: Optional[str] = os.getenv('WEBHOOK_SECRET_TOKEN')
    
    # Application Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'production')
    
    # Flask Settings
    SECRET_KEY: str = os.getenv('SECRET_KEY', os.urandom(32).hex())


def validate_config() -> None:
    """
    Validate that all required configuration is present.
    
    Raises:
        ValueError: If required configuration is missing
    """
    required_vars = [
        ('LANGSMITH_API_KEY', Config.LANGSMITH_API_KEY),
        ('LANGSMITH_API_URL', Config.LANGSMITH_API_URL),
        ('LANGSMITH_AGENT_ID', Config.LANGSMITH_AGENT_ID),
    ]
    
    missing = [name for name, value in required_vars if not value]
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    
    # Validate URL format
    if not Config.LANGSMITH_API_URL.startswith(('http://', 'https://')):
        raise ValueError(
            "LANGSMITH_API_URL must start with http:// or https://"
        )
