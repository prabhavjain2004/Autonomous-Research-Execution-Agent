"""
Configuration module for loading environment variables and application settings.

This module provides a centralized configuration management system that loads
settings from environment variables with sensible defaults. All secrets and
configuration parameters are loaded from the environment, following the
twelve-factor app methodology.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Application configuration loaded from environment variables.
    
    All configuration values are loaded from environment variables to avoid
    hardcoded secrets and enable easy deployment across different environments.
    """
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./data/agent_memory.db")
    
    # Logging Configuration
    LOG_DIR: str = os.getenv("LOG_DIR", "./logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # State Machine Timeouts (seconds)
    TIMEOUT_PLANNING: int = int(os.getenv("TIMEOUT_PLANNING", "30"))
    TIMEOUT_TOOL_EXECUTION: int = int(os.getenv("TIMEOUT_TOOL_EXECUTION", "120"))
    TIMEOUT_OBSERVATION: int = int(os.getenv("TIMEOUT_OBSERVATION", "20"))
    TIMEOUT_REFLECTION: int = int(os.getenv("TIMEOUT_REFLECTION", "30"))
    TIMEOUT_CONFIDENCE_EVALUATION: int = int(os.getenv("TIMEOUT_CONFIDENCE_EVALUATION", "20"))
    TIMEOUT_REPLANNING: int = int(os.getenv("TIMEOUT_REPLANNING", "30"))
    TIMEOUT_ERROR_RECOVERY: int = int(os.getenv("TIMEOUT_ERROR_RECOVERY", "10"))
    
    # Confidence Thresholds
    CONFIDENCE_THRESHOLD_PROCEED: int = int(os.getenv("CONFIDENCE_THRESHOLD_PROCEED", "80"))
    CONFIDENCE_THRESHOLD_CRITICAL: int = int(os.getenv("CONFIDENCE_THRESHOLD_CRITICAL", "60"))
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "2"))
    
    # Tool Configuration
    RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "2.5"))
    WEB_SCRAPER_TIMEOUT: int = int(os.getenv("WEB_SCRAPER_TIMEOUT", "30"))
    PYTHON_EXECUTOR_TIMEOUT: int = int(os.getenv("PYTHON_EXECUTOR_TIMEOUT", "10"))
    
    # Output Configuration
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./outputs")
    
    # UI Configuration
    UI_HOST: str = os.getenv("UI_HOST", "0.0.0.0")
    UI_PORT: int = int(os.getenv("UI_PORT", "8000"))
    
    # Escalation Configuration
    ESCALATION_EMAIL_ENABLED: bool = os.getenv("ESCALATION_EMAIL_ENABLED", "false").lower() == "true"
    ESCALATION_EMAIL_SMTP_HOST: str = os.getenv("ESCALATION_EMAIL_SMTP_HOST", "smtp.gmail.com")
    ESCALATION_EMAIL_SMTP_PORT: int = int(os.getenv("ESCALATION_EMAIL_SMTP_PORT", "587"))
    ESCALATION_EMAIL_FROM: str = os.getenv("ESCALATION_EMAIL_FROM", "")
    ESCALATION_EMAIL_TO: str = os.getenv("ESCALATION_EMAIL_TO", "")
    ESCALATION_EMAIL_PASSWORD: str = os.getenv("ESCALATION_EMAIL_PASSWORD", "")
    
    ESCALATION_WEBHOOK_ENABLED: bool = os.getenv("ESCALATION_WEBHOOK_ENABLED", "false").lower() == "true"
    ESCALATION_WEBHOOK_URL: str = os.getenv("ESCALATION_WEBHOOK_URL", "")
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration values are set.
        
        Raises:
            ValueError: If required configuration values are missing.
        """
        if not cls.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is required. Please set it in your .env file or environment."
            )
        
        if cls.ESCALATION_EMAIL_ENABLED:
            if not cls.ESCALATION_EMAIL_FROM or not cls.ESCALATION_EMAIL_TO:
                raise ValueError(
                    "Email escalation is enabled but email addresses are not configured. "
                    "Please set ESCALATION_EMAIL_FROM and ESCALATION_EMAIL_TO."
                )
        
        if cls.ESCALATION_WEBHOOK_ENABLED:
            if not cls.ESCALATION_WEBHOOK_URL:
                raise ValueError(
                    "Webhook escalation is enabled but webhook URL is not configured. "
                    "Please set ESCALATION_WEBHOOK_URL."
                )
    
    @classmethod
    def get_state_timeouts(cls) -> dict:
        """
        Get all state machine timeout values as a dictionary.
        
        Returns:
            Dictionary mapping state names to timeout values in seconds.
        """
        return {
            "PLANNING": cls.TIMEOUT_PLANNING,
            "TOOL_EXECUTION": cls.TIMEOUT_TOOL_EXECUTION,
            "OBSERVATION": cls.TIMEOUT_OBSERVATION,
            "REFLECTION": cls.TIMEOUT_REFLECTION,
            "CONFIDENCE_EVALUATION": cls.TIMEOUT_CONFIDENCE_EVALUATION,
            "REPLANNING": cls.TIMEOUT_REPLANNING,
            "ERROR_RECOVERY": cls.TIMEOUT_ERROR_RECOVERY,
        }
    
    @classmethod
    def display_config(cls) -> str:
        """
        Display current configuration (with secrets masked).
        
        Returns:
            String representation of configuration with sensitive values masked.
        """
        config_lines = [
            "=== Application Configuration ===",
            f"OpenRouter API Key: {'*' * 8 if cls.OPENROUTER_API_KEY else 'NOT SET'}",
            f"Database Path: {cls.DATABASE_PATH}",
            f"Log Directory: {cls.LOG_DIR}",
            f"Log Level: {cls.LOG_LEVEL}",
            f"Confidence Threshold: {cls.CONFIDENCE_THRESHOLD_PROCEED}",
            f"Max Retry Attempts: {cls.MAX_RETRY_ATTEMPTS}",
            f"Rate Limit Delay: {cls.RATE_LIMIT_DELAY}s",
            f"UI Host: {cls.UI_HOST}:{cls.UI_PORT}",
            f"Email Escalation: {'Enabled' if cls.ESCALATION_EMAIL_ENABLED else 'Disabled'}",
            f"Webhook Escalation: {'Enabled' if cls.ESCALATION_WEBHOOK_ENABLED else 'Disabled'}",
            "================================",
        ]
        return "\n".join(config_lines)


# Create a singleton instance for easy import
config = Config()
