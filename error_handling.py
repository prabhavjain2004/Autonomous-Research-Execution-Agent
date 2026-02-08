"""
Error Handling and Recovery Module

This module provides custom exception hierarchy, exponential backoff utilities,
and error context logging for robust error handling throughout the system.
"""

import time
import traceback
from typing import Dict, Any, Optional, Callable
from enum import Enum


class ErrorSeverity(Enum):
    """Severity levels for errors"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Custom Exception Hierarchy

class AgentSystemError(Exception):
    """Base exception for all agent system errors"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize agent system error
        
        Args:
            message: Error message
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.severity = ErrorSeverity.MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "severity": self.severity.value,
            "traceback": traceback.format_exc()
        }


class ConfigurationError(AgentSystemError):
    """Error in system configuration"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, context)
        self.severity = ErrorSeverity.CRITICAL


class ToolExecutionError(AgentSystemError):
    """Error during tool execution"""
    
    def __init__(self, tool_name: str, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(f"Tool '{tool_name}' failed: {message}", context)
        self.tool_name = tool_name
        self.severity = ErrorSeverity.MEDIUM


class RateLimitError(AgentSystemError):
    """Rate limit exceeded error"""
    
    def __init__(self, service: str, retry_after: Optional[float] = None, context: Optional[Dict[str, Any]] = None):
        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(message, context)
        self.service = service
        self.retry_after = retry_after
        self.severity = ErrorSeverity.MEDIUM


class ModelError(AgentSystemError):
    """Error from LLM model"""
    
    def __init__(self, model_name: str, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(f"Model '{model_name}' error: {message}", context)
        self.model_name = model_name
        self.severity = ErrorSeverity.HIGH


class AgentExecutionError(AgentSystemError):
    """Error during agent execution"""
    
    def __init__(self, agent_name: str, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(f"Agent '{agent_name}' failed: {message}", context)
        self.agent_name = agent_name
        self.severity = ErrorSeverity.HIGH


class MemorySystemError(AgentSystemError):
    """Error in memory/database operations"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(f"Memory system error: {message}", context)
        self.severity = ErrorSeverity.HIGH


class ValidationError(AgentSystemError):
    """Data validation error"""
    
    def __init__(self, field: str, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(f"Validation failed for '{field}': {message}", context)
        self.field = field
        self.severity = ErrorSeverity.LOW


class TimeoutError(AgentSystemError):
    """Operation timeout error"""
    
    def __init__(self, operation: str, timeout: float, context: Optional[Dict[str, Any]] = None):
        super().__init__(f"Operation '{operation}' timed out after {timeout}s", context)
        self.operation = operation
        self.timeout = timeout
        self.severity = ErrorSeverity.MEDIUM


class ConfidenceError(AgentSystemError):
    """Low confidence error requiring intervention"""
    
    def __init__(self, agent_name: str, confidence: float, threshold: float, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Agent '{agent_name}' confidence ({confidence:.2f}) below threshold ({threshold:.2f})",
            context
        )
        self.agent_name = agent_name
        self.confidence = confidence
        self.threshold = threshold
        self.severity = ErrorSeverity.MEDIUM


# Exponential Backoff Utility

class ExponentialBackoff:
    """
    Exponential backoff calculator for retry logic
    
    Implements exponential backoff with jitter to prevent thundering herd problem.
    """
    
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize exponential backoff
        
        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential calculation
            jitter: Whether to add random jitter
        """
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if exponential_base <= 1:
            raise ValueError("exponential_base must be > 1")
        
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number
        
        Args:
            attempt: Attempt number (0-indexed)
        
        Returns:
            Delay in seconds
        """
        if attempt < 0:
            raise ValueError("attempt must be non-negative")
        
        # Calculate exponential delay
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # Cap at max_delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
        
        return delay
    
    def sleep(self, attempt: int):
        """
        Sleep for calculated delay
        
        Args:
            attempt: Attempt number (0-indexed)
        """
        delay = self.calculate_delay(attempt)
        time.sleep(delay)


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    backoff: Optional[ExponentialBackoff] = None,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Any:
    """
    Retry a function with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        backoff: ExponentialBackoff instance (creates default if None)
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called on each retry with (exception, attempt)
    
    Returns:
        Result of successful function call
    
    Raises:
        Last exception if all retries exhausted
    """
    if backoff is None:
        backoff = ExponentialBackoff()
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            
            if attempt >= max_retries:
                # No more retries
                break
            
            # Call retry callback if provided
            if on_retry:
                on_retry(e, attempt)
            
            # Sleep with backoff
            backoff.sleep(attempt)
    
    # All retries exhausted
    raise last_exception


# Error Context Logging

class ErrorContext:
    """
    Context manager for capturing and logging error context
    
    Usage:
        with ErrorContext(logger, operation="data_processing") as ctx:
            ctx.add("input_size", len(data))
            process_data(data)
    """
    
    def __init__(self, logger, operation: str):
        """
        Initialize error context
        
        Args:
            logger: Logger instance
            operation: Name of the operation
        """
        self.logger = logger
        self.operation = operation
        self.context = {"operation": operation}
        self.start_time = None
    
    def add(self, key: str, value: Any):
        """Add context information"""
        self.context[key] = value
    
    def __enter__(self):
        """Enter context"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and log if error occurred"""
        if exc_type is not None:
            # Error occurred
            duration = time.time() - self.start_time
            self.context["duration"] = duration
            self.context["error_type"] = exc_type.__name__
            self.context["error_message"] = str(exc_val)
            
            # Log error with context
            if self.logger:
                import traceback
                self.logger.log_error(
                    error_type=exc_type.__name__,
                    error_message=str(exc_val),
                    stack_trace=traceback.format_exc() if exc_tb else "",
                    context=self.context
                )
        
        # Don't suppress exception
        return False


def handle_rate_limit(
    func: Callable,
    service: str,
    max_retries: int = 3,
    logger = None
) -> Any:
    """
    Handle rate limiting with exponential backoff
    
    Args:
        func: Function to execute
        service: Name of the service
        max_retries: Maximum number of retries
        logger: Optional logger
    
    Returns:
        Result of successful function call
    
    Raises:
        RateLimitError if all retries exhausted
    """
    backoff = ExponentialBackoff(base_delay=2.0, max_delay=120.0)
    
    def on_retry(exception, attempt):
        if logger:
            logger.log_decision(
                agent_name="error_handler",
                decision=f"Rate limit hit for {service}, retrying (attempt {attempt + 1}/{max_retries})",
                reasoning=str(exception)
            )
    
    try:
        return retry_with_backoff(
            func=func,
            max_retries=max_retries,
            backoff=backoff,
            exceptions=(RateLimitError,),
            on_retry=on_retry
        )
    except RateLimitError as e:
        # All retries exhausted
        if logger:
            import traceback
            logger.log_error(
                error_type="RateLimitExhausted",
                error_message=f"Rate limit for {service} exceeded after {max_retries} retries",
                stack_trace=traceback.format_exc(),
                context={"service": service}
            )
        raise


def safe_execute(
    func: Callable,
    default_value: Any = None,
    logger = None,
    operation: str = "operation"
) -> Any:
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        default_value: Value to return on error
        logger: Optional logger
        operation: Name of the operation
    
    Returns:
        Function result or default_value on error
    """
    try:
        return func()
    except Exception as e:
        if logger:
            import traceback
            logger.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                context={"operation": operation}
            )
        return default_value
