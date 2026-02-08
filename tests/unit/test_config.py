"""
Unit tests for configuration module.
"""

import os
import pytest
from config import Config


class TestConfig:
    """Test suite for Config class."""
    
    def test_config_loads_defaults(self):
        """Test that config loads with default values."""
        assert Config.DATABASE_PATH == os.getenv("DATABASE_PATH", "./data/agent_memory.db")
        assert Config.LOG_DIR == os.getenv("LOG_DIR", "./logs")
        assert Config.LOG_LEVEL == os.getenv("LOG_LEVEL", "INFO")
    
    def test_config_timeout_values(self):
        """Test that timeout values are integers."""
        assert isinstance(Config.TIMEOUT_PLANNING, int)
        assert isinstance(Config.TIMEOUT_TOOL_EXECUTION, int)
        assert isinstance(Config.TIMEOUT_OBSERVATION, int)
        assert isinstance(Config.TIMEOUT_REFLECTION, int)
        assert isinstance(Config.TIMEOUT_CONFIDENCE_EVALUATION, int)
        assert isinstance(Config.TIMEOUT_REPLANNING, int)
        assert isinstance(Config.TIMEOUT_ERROR_RECOVERY, int)
    
    def test_config_confidence_thresholds(self):
        """Test that confidence thresholds are valid."""
        assert 0 <= Config.CONFIDENCE_THRESHOLD_PROCEED <= 100
        assert 0 <= Config.CONFIDENCE_THRESHOLD_CRITICAL <= 100
        assert Config.MAX_RETRY_ATTEMPTS >= 0
    
    def test_config_rate_limit_delay(self):
        """Test that rate limit delay is a positive float."""
        assert isinstance(Config.RATE_LIMIT_DELAY, float)
        assert Config.RATE_LIMIT_DELAY > 0
    
    def test_get_state_timeouts(self):
        """Test that get_state_timeouts returns correct dictionary."""
        timeouts = Config.get_state_timeouts()
        
        assert isinstance(timeouts, dict)
        assert "PLANNING" in timeouts
        assert "TOOL_EXECUTION" in timeouts
        assert "OBSERVATION" in timeouts
        assert "REFLECTION" in timeouts
        assert "CONFIDENCE_EVALUATION" in timeouts
        assert "REPLANNING" in timeouts
        assert "ERROR_RECOVERY" in timeouts
        
        # All values should be positive integers
        for key, value in timeouts.items():
            assert isinstance(value, int)
            assert value > 0
    
    def test_display_config(self):
        """Test that display_config returns formatted string."""
        config_str = Config.display_config()
        
        assert isinstance(config_str, str)
        assert "Application Configuration" in config_str
        assert "Database Path" in config_str
        assert "Log Directory" in config_str
        
        # Secrets should be masked
        if Config.OPENROUTER_API_KEY:
            assert Config.OPENROUTER_API_KEY not in config_str
            assert "***" in config_str
    
    def test_validate_missing_api_key(self, monkeypatch):
        """Test that validate raises error when API key is missing."""
        # Temporarily remove API key
        monkeypatch.setattr(Config, "OPENROUTER_API_KEY", "")
        
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY is required"):
            Config.validate()
    
    def test_validate_email_escalation_config(self, monkeypatch):
        """Test that validate checks email escalation configuration."""
        # Set API key first (required)
        monkeypatch.setattr(Config, "OPENROUTER_API_KEY", "test-key")
        # Enable email escalation without proper config
        monkeypatch.setattr(Config, "ESCALATION_EMAIL_ENABLED", True)
        monkeypatch.setattr(Config, "ESCALATION_EMAIL_FROM", "")
        monkeypatch.setattr(Config, "ESCALATION_EMAIL_TO", "")
        
        with pytest.raises(ValueError, match="email addresses are not configured"):
            Config.validate()
    
    def test_validate_webhook_escalation_config(self, monkeypatch):
        """Test that validate checks webhook escalation configuration."""
        # Set API key first (required)
        monkeypatch.setattr(Config, "OPENROUTER_API_KEY", "test-key")
        # Enable webhook escalation without proper config
        monkeypatch.setattr(Config, "ESCALATION_WEBHOOK_ENABLED", True)
        monkeypatch.setattr(Config, "ESCALATION_WEBHOOK_URL", "")
        
        with pytest.raises(ValueError, match="webhook URL is not configured"):
            Config.validate()
    
    def test_boolean_env_vars(self, monkeypatch):
        """Test that boolean environment variables are parsed correctly."""
        # Test true values
        monkeypatch.setenv("ESCALATION_EMAIL_ENABLED", "true")
        assert os.getenv("ESCALATION_EMAIL_ENABLED", "false").lower() == "true"
        
        # Test false values
        monkeypatch.setenv("ESCALATION_EMAIL_ENABLED", "false")
        assert os.getenv("ESCALATION_EMAIL_ENABLED", "false").lower() == "false"
