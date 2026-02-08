"""
Unit tests for error handling module
"""

import pytest
import time
from unittest.mock import Mock

from error_handling import (
    AgentSystemError, ConfigurationError, ToolExecutionError, RateLimitError,
    ModelError, AgentExecutionError, MemorySystemError, ValidationError,
    TimeoutError, ConfidenceError, ErrorSeverity,
    ExponentialBackoff, retry_with_backoff, ErrorContext,
    handle_rate_limit, safe_execute
)


class TestCustomExceptions:
    """Tests for custom exception hierarchy"""
    
    def test_agent_system_error(self):
        """Test base AgentSystemError"""
        error = AgentSystemError("Test error", {"key": "value"})
        
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.context == {"key": "value"}
        assert error.severity == ErrorSeverity.MEDIUM
        
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "AgentSystemError"
        assert error_dict["message"] == "Test error"
        assert error_dict["context"] == {"key": "value"}
    
    def test_configuration_error(self):
        """Test ConfigurationError"""
        error = ConfigurationError("Invalid config")
        
        assert "Invalid config" in str(error)
        assert error.severity == ErrorSeverity.CRITICAL
    
    def test_tool_execution_error(self):
        """Test ToolExecutionError"""
        error = ToolExecutionError("web_search", "Connection failed")
        
        assert "web_search" in str(error)
        assert "Connection failed" in str(error)
        assert error.tool_name == "web_search"
        assert error.severity == ErrorSeverity.MEDIUM
    
    def test_rate_limit_error(self):
        """Test RateLimitError"""
        error = RateLimitError("api_service", retry_after=30.0)
        
        assert "api_service" in str(error)
        assert "30" in str(error)
        assert error.service == "api_service"
        assert error.retry_after == 30.0
    
    def test_model_error(self):
        """Test ModelError"""
        error = ModelError("gpt-4", "API error")
        
        assert "gpt-4" in str(error)
        assert "API error" in str(error)
        assert error.model_name == "gpt-4"
        assert error.severity == ErrorSeverity.HIGH
    
    def test_agent_execution_error(self):
        """Test AgentExecutionError"""
        error = AgentExecutionError("research_agent", "Execution failed")
        
        assert "research_agent" in str(error)
        assert "Execution failed" in str(error)
        assert error.agent_name == "research_agent"
    
    def test_memory_system_error(self):
        """Test MemorySystemError"""
        error = MemorySystemError("Database connection lost")
        
        assert "Database connection lost" in str(error)
        assert error.severity == ErrorSeverity.HIGH
    
    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError("email", "Invalid format")
        
        assert "email" in str(error)
        assert "Invalid format" in str(error)
        assert error.field == "email"
        assert error.severity == ErrorSeverity.LOW
    
    def test_timeout_error(self):
        """Test TimeoutError"""
        error = TimeoutError("api_call", 30.0)
        
        assert "api_call" in str(error)
        assert "30" in str(error)
        assert error.operation == "api_call"
        assert error.timeout == 30.0
    
    def test_confidence_error(self):
        """Test ConfidenceError"""
        error = ConfidenceError("analyst_agent", 0.45, 0.50)
        
        assert "analyst_agent" in str(error)
        assert "0.45" in str(error)
        assert "0.50" in str(error)
        assert error.agent_name == "analyst_agent"
        assert error.confidence == 0.45
        assert error.threshold == 0.50


class TestExponentialBackoff:
    """Tests for ExponentialBackoff"""
    
    def test_initialization(self):
        """Test backoff initialization"""
        backoff = ExponentialBackoff(
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=2.0,
            jitter=True
        )
        
        assert backoff.base_delay == 2.0
        assert backoff.max_delay == 120.0
        assert backoff.exponential_base == 2.0
        assert backoff.jitter is True
    
    def test_initialization_invalid_base_delay(self):
        """Test that invalid base_delay raises error"""
        with pytest.raises(ValueError, match="base_delay must be positive"):
            ExponentialBackoff(base_delay=0)
    
    def test_initialization_invalid_max_delay(self):
        """Test that invalid max_delay raises error"""
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            ExponentialBackoff(base_delay=10.0, max_delay=5.0)
    
    def test_initialization_invalid_exponential_base(self):
        """Test that invalid exponential_base raises error"""
        with pytest.raises(ValueError, match="exponential_base must be > 1"):
            ExponentialBackoff(exponential_base=1.0)
    
    def test_calculate_delay_first_attempt(self):
        """Test delay calculation for first attempt"""
        backoff = ExponentialBackoff(base_delay=1.0, jitter=False)
        delay = backoff.calculate_delay(0)
        
        assert delay == 1.0
    
    def test_calculate_delay_exponential_growth(self):
        """Test exponential growth of delays"""
        backoff = ExponentialBackoff(base_delay=1.0, exponential_base=2.0, jitter=False)
        
        assert backoff.calculate_delay(0) == 1.0
        assert backoff.calculate_delay(1) == 2.0
        assert backoff.calculate_delay(2) == 4.0
        assert backoff.calculate_delay(3) == 8.0
    
    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at max_delay"""
        backoff = ExponentialBackoff(base_delay=1.0, max_delay=10.0, jitter=False)
        
        # After enough attempts, should cap at max_delay
        delay = backoff.calculate_delay(10)
        assert delay == 10.0
    
    def test_calculate_delay_with_jitter(self):
        """Test that jitter adds randomness"""
        backoff = ExponentialBackoff(base_delay=10.0, jitter=True)
        
        # With jitter, delay should be between 50% and 100% of calculated value
        delay = backoff.calculate_delay(0)
        assert 5.0 <= delay <= 10.0
    
    def test_calculate_delay_negative_attempt(self):
        """Test that negative attempt raises error"""
        backoff = ExponentialBackoff()
        
        with pytest.raises(ValueError, match="attempt must be non-negative"):
            backoff.calculate_delay(-1)
    
    def test_sleep(self):
        """Test sleep method"""
        backoff = ExponentialBackoff(base_delay=0.01, jitter=False)
        
        start = time.time()
        backoff.sleep(0)
        duration = time.time() - start
        
        # Should sleep for approximately base_delay
        assert duration >= 0.01


class TestRetryWithBackoff:
    """Tests for retry_with_backoff"""
    
    def test_successful_first_attempt(self):
        """Test successful execution on first attempt"""
        mock_func = Mock(return_value="success")
        
        result = retry_with_backoff(mock_func, max_retries=3)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_exception(self):
        """Test retry on exception"""
        mock_func = Mock(side_effect=[Exception("Error 1"), Exception("Error 2"), "success"])
        
        result = retry_with_backoff(
            mock_func,
            max_retries=3,
            backoff=ExponentialBackoff(base_delay=0.01)
        )
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_max_retries_exhausted(self):
        """Test that exception is raised when max retries exhausted"""
        mock_func = Mock(side_effect=Exception("Persistent error"))
        
        with pytest.raises(Exception, match="Persistent error"):
            retry_with_backoff(
                mock_func,
                max_retries=2,
                backoff=ExponentialBackoff(base_delay=0.01)
            )
        
        assert mock_func.call_count == 3  # Initial + 2 retries
    
    def test_on_retry_callback(self):
        """Test that on_retry callback is called"""
        mock_func = Mock(side_effect=[Exception("Error"), "success"])
        mock_callback = Mock()
        
        retry_with_backoff(
            mock_func,
            max_retries=2,
            backoff=ExponentialBackoff(base_delay=0.01),
            on_retry=mock_callback
        )
        
        assert mock_callback.called
        assert mock_callback.call_count == 1
    
    def test_specific_exceptions(self):
        """Test catching only specific exceptions"""
        mock_func = Mock(side_effect=ValueError("Wrong type"))
        
        # Should not catch ValueError if only Exception is specified
        with pytest.raises(ValueError):
            retry_with_backoff(
                mock_func,
                max_retries=2,
                exceptions=(TypeError,),
                backoff=ExponentialBackoff(base_delay=0.01)
            )


class TestErrorContext:
    """Tests for ErrorContext"""
    
    def test_error_context_no_error(self):
        """Test error context when no error occurs"""
        mock_logger = Mock()
        
        with ErrorContext(mock_logger, "test_operation") as ctx:
            ctx.add("key", "value")
            pass
        
        # Logger should not be called if no error
        assert not mock_logger.log_error.called
    
    def test_error_context_with_error(self):
        """Test error context when error occurs"""
        mock_logger = Mock()
        
        try:
            with ErrorContext(mock_logger, "test_operation") as ctx:
                ctx.add("input_size", 100)
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Logger should be called with error context
        assert mock_logger.log_error.called
        call_args = mock_logger.log_error.call_args
        assert call_args[1]["error_type"] == "ValueError"
        assert call_args[1]["error_message"] == "Test error"
        assert call_args[1]["context"]["operation"] == "test_operation"
        assert call_args[1]["context"]["input_size"] == 100
    
    def test_error_context_duration_tracking(self):
        """Test that error context tracks duration"""
        mock_logger = Mock()
        
        try:
            with ErrorContext(mock_logger, "test_operation") as ctx:
                time.sleep(0.01)
                raise Exception("Test")
        except Exception:
            pass
        
        call_args = mock_logger.log_error.call_args
        assert "duration" in call_args[1]["context"]
        assert call_args[1]["context"]["duration"] > 0


class TestHandleRateLimit:
    """Tests for handle_rate_limit"""
    
    def test_handle_rate_limit_success(self):
        """Test successful execution without rate limit"""
        mock_func = Mock(return_value="success")
        
        result = handle_rate_limit(mock_func, "test_service")
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_handle_rate_limit_retry(self):
        """Test retry on rate limit"""
        mock_func = Mock(side_effect=[
            RateLimitError("test_service"),
            "success"
        ])
        mock_logger = Mock()
        
        result = handle_rate_limit(mock_func, "test_service", logger=mock_logger)
        
        assert result == "success"
        assert mock_func.call_count == 2
        assert mock_logger.log_decision.called
    
    def test_handle_rate_limit_exhausted(self):
        """Test rate limit exhausted after max retries"""
        mock_func = Mock(side_effect=RateLimitError("test_service"))
        mock_logger = Mock()
        
        with pytest.raises(RateLimitError):
            handle_rate_limit(mock_func, "test_service", max_retries=2, logger=mock_logger)
        
        assert mock_logger.log_error.called


class TestSafeExecute:
    """Tests for safe_execute"""
    
    def test_safe_execute_success(self):
        """Test successful execution"""
        mock_func = Mock(return_value="success")
        
        result = safe_execute(mock_func)
        
        assert result == "success"
    
    def test_safe_execute_with_error(self):
        """Test execution with error returns default"""
        mock_func = Mock(side_effect=Exception("Error"))
        
        result = safe_execute(mock_func, default_value="default")
        
        assert result == "default"
    
    def test_safe_execute_logs_error(self):
        """Test that errors are logged"""
        mock_func = Mock(side_effect=ValueError("Test error"))
        mock_logger = Mock()
        
        safe_execute(mock_func, logger=mock_logger, operation="test_op")
        
        assert mock_logger.log_error.called
        call_args = mock_logger.log_error.call_args
        assert call_args[1]["error_type"] == "ValueError"
        assert call_args[1]["context"]["operation"] == "test_op"
