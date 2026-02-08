"""
Base tool interface for all tools in the system.

This module defines the abstract base class that all tools must implement,
ensuring consistent interfaces, validation, and error handling.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from models.data_models import ToolResult
from structured_logging import StructuredLogger


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    All tools must implement:
    - validate_input: Check input parameters before execution
    - execute: Perform the tool's operation
    
    Tools automatically handle errors gracefully and return structured results.
    """
    
    def __init__(self, logger: Optional[StructuredLogger] = None):
        """
        Initialize tool with optional logger.
        
        Args:
            logger: Structured logger for observability
        """
        self.logger = logger
    
    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """
        Validate tool input parameters.
        
        This method should check that all required parameters are present
        and have valid values before execution begins.
        
        Args:
            **kwargs: Tool-specific input parameters
            
        Returns:
            True if inputs are valid, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute tool operation.
        
        This method performs the tool's main functionality and returns
        a structured ToolResult.
        
        Args:
            **kwargs: Tool-specific input parameters
            
        Returns:
            ToolResult with success status, data, and optional error
        """
        pass
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ToolResult:
        """
        Handle tool execution error gracefully.
        
        This method ensures that errors are logged and returned as structured
        ToolResult objects rather than propagating exceptions.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
            
        Returns:
            ToolResult with success=False and error message
        """
        error_message = str(error)
        error_type = type(error).__name__
        
        if self.logger:
            import traceback
            self.logger.log_error(
                error_type=error_type,
                error_message=error_message,
                stack_trace=traceback.format_exc(),
                context=context or {}
            )
        
        return ToolResult(
            success=False,
            data=None,
            error=f"{error_type}: {error_message}",
            metadata=context or {}
        )
    
    def run(self, **kwargs) -> ToolResult:
        """
        Run tool with validation and error handling.
        
        This is the main entry point that wraps execute() with validation
        and error handling.
        
        Args:
            **kwargs: Tool-specific input parameters
            
        Returns:
            ToolResult from execution or error handling
        """
        try:
            # Validate inputs
            if not self.validate_input(**kwargs):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Input validation failed",
                    metadata={"inputs": kwargs}
                )
            
            # Execute tool
            result = self.execute(**kwargs)
            
            # Validate result
            if not result.validate():
                return ToolResult(
                    success=False,
                    data=None,
                    error="Tool returned invalid result",
                    metadata={"inputs": kwargs}
                )
            
            return result
            
        except Exception as e:
            return self.handle_error(e, context={"inputs": kwargs})
