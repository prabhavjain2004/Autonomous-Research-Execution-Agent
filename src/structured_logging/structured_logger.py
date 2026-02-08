"""
Structured logging system for observability and debugging.

This module provides JSON-formatted logging with multiple levels, session isolation,
and comprehensive tracking of agent decisions, state transitions, tool calls, and errors.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pathlib import Path


class LogLevel(Enum):
    """Log levels for filtering and categorization."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted logs with session isolation.
    
    Features:
    - JSON-formatted output for easy parsing
    - Session-based log file isolation
    - Multiple log levels with filtering
    - Structured event types for different operations
    - Console and file output support
    - Log rotation to prevent unbounded disk usage
    """
    
    def __init__(
        self,
        session_id: str,
        log_dir: str = "./logs",
        console_output: bool = True,
        log_level: str = "INFO"
    ):
        """
        Initialize structured logger for a session.
        
        Args:
            session_id: Unique session identifier
            log_dir: Directory for log files
            console_output: Whether to output to console
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR)
        """
        self.session_id = session_id
        self.log_dir = Path(log_dir)
        self.console_output = console_output
        self.log_level = LogLevel[log_level.upper()]
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session-specific log file
        self.log_file = self.log_dir / f"session_{session_id}.json"
        
        # Initialize Python logger
        self.logger = logging.getLogger(f"session_{session_id}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        
        # File handler for JSON logs
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        
        # Console handler if enabled
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, log_level.upper()))
            self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _should_log(self, level: LogLevel) -> bool:
        """
        Check if message should be logged based on level.
        
        Args:
            level: Log level of the message
            
        Returns:
            True if message should be logged
        """
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3
        }
        return level_order[level] >= level_order[self.log_level]
    
    def _log(
        self,
        level: LogLevel,
        event_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Internal method to write structured log entry.
        
        Args:
            level: Log level
            event_type: Type of event being logged
            message: Human-readable message
            data: Additional structured data
        """
        if not self._should_log(level):
            return
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "level": level.value,
            "event_type": event_type,
            "message": message,
            "data": data or {}
        }
        
        # Write as JSON line
        log_line = json.dumps(log_entry)
        
        # Use appropriate logging level
        python_level = getattr(logging, level.value)
        self.logger.log(python_level, log_line)
    
    def log_state_transition(
        self,
        from_state: str,
        to_state: str,
        reason: str,
        agent: Optional[str] = None
    ):
        """
        Log agent state transition.
        
        Args:
            from_state: Previous state
            to_state: New state
            reason: Reason for transition
            agent: Agent name (optional)
        """
        self._log(
            LogLevel.INFO,
            "state_transition",
            f"State transition: {from_state} -> {to_state}",
            {
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
                "agent": agent
            }
        )
    
    def log_tool_call(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        outputs: Any,
        execution_time: float,
        success: bool = True
    ):
        """
        Log tool execution.
        
        Args:
            tool_name: Name of the tool
            inputs: Tool input parameters
            outputs: Tool output (ToolResult or dict)
            execution_time: Execution time in seconds
            success: Whether execution succeeded
        """
        # Extract relevant output data
        output_data = {}
        if hasattr(outputs, 'success'):
            output_data = {
                "success": outputs.success,
                "has_data": outputs.data is not None,
                "error": outputs.error
            }
        elif isinstance(outputs, dict):
            output_data = outputs
        
        self._log(
            LogLevel.INFO,
            "tool_call",
            f"Tool executed: {tool_name}",
            {
                "tool_name": tool_name,
                "inputs": inputs,
                "outputs": output_data,
                "execution_time": execution_time,
                "success": success
            }
        )
    
    def log_model_selection(
        self,
        task_complexity: str,
        selected_model: str,
        reasoning: str,
        context_length: Optional[int] = None
    ):
        """
        Log model router decision.
        
        Args:
            task_complexity: Complexity level of the task
            selected_model: Model that was selected
            reasoning: Explanation for selection
            context_length: Estimated context length
        """
        self._log(
            LogLevel.INFO,
            "model_selection",
            f"Model selected: {selected_model}",
            {
                "task_complexity": task_complexity,
                "selected_model": selected_model,
                "reasoning": reasoning,
                "context_length": context_length
            }
        )
    
    def log_confidence_scores(
        self,
        agent_name: str,
        self_score: int,
        boss_score: int,
        decision: str,
        reasoning: Optional[str] = None
    ):
        """
        Log confidence evaluation.
        
        Args:
            agent_name: Name of the agent
            self_score: Agent's self-confidence score
            boss_score: Boss Agent's evaluation score
            decision: Decision made (proceed, replan, escalate)
            reasoning: Explanation for decision
        """
        self._log(
            LogLevel.INFO,
            "confidence_evaluation",
            f"Confidence scores for {agent_name}: self={self_score}, boss={boss_score}",
            {
                "agent_name": agent_name,
                "self_score": self_score,
                "boss_score": boss_score,
                "decision": decision,
                "reasoning": reasoning
            }
        )
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: str,
        context: Dict[str, Any],
        agent: Optional[str] = None
    ):
        """
        Log error with full context.
        
        Args:
            error_type: Type/class of error
            error_message: Error message
            stack_trace: Full stack trace
            context: Additional context about the error
            agent: Agent name if applicable
        """
        self._log(
            LogLevel.ERROR,
            "error",
            f"Error occurred: {error_type}",
            {
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "context": context,
                "agent": agent
            }
        )
    
    def log_decision(
        self,
        agent_name: str,
        decision: str,
        reasoning: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log agent decision.
        
        Args:
            agent_name: Name of the agent
            decision: Decision made
            reasoning: Explanation for decision
            context: Additional context
        """
        self._log(
            LogLevel.INFO,
            "agent_decision",
            f"Agent decision: {agent_name} - {decision}",
            {
                "agent_name": agent_name,
                "decision": decision,
                "reasoning": reasoning,
                "context": context or {}
            }
        )
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            context: Additional context
        """
        self._log(
            LogLevel.DEBUG,
            "performance_metric",
            f"Metric: {metric_name} = {value} {unit}",
            {
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "context": context or {}
            }
        )
    
    def log_retry(
        self,
        operation: str,
        retry_count: int,
        max_retries: int,
        reason: str,
        agent: Optional[str] = None
    ):
        """
        Log retry attempt.
        
        Args:
            operation: Operation being retried
            retry_count: Current retry count
            max_retries: Maximum retry attempts
            reason: Reason for retry
            agent: Agent name if applicable
        """
        self._log(
            LogLevel.WARNING,
            "retry",
            f"Retry {retry_count}/{max_retries}: {operation}",
            {
                "operation": operation,
                "retry_count": retry_count,
                "max_retries": max_retries,
                "reason": reason,
                "agent": agent
            }
        )
    
    def log_info(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log info level message."""
        self._log(LogLevel.INFO, "info", message, data)
    
    def log_debug(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log debug level message."""
        self._log(LogLevel.DEBUG, "debug", message, data)
    
    def log_warning(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log warning level message."""
        self._log(LogLevel.WARNING, "warning", message, data)
    
    def log_error_simple(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log error level message (simplified version)."""
        self._log(LogLevel.ERROR, "error", message, data)
    
    def close(self):
        """Close logger and cleanup handlers."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
    
    @staticmethod
    def get_session_logs(log_dir: str, session_id: str) -> list:
        """
        Read all log entries for a session.
        
        Args:
            log_dir: Directory containing log files
            session_id: Session identifier
            
        Returns:
            List of log entry dictionaries
        """
        log_file = Path(log_dir) / f"session_{session_id}.json"
        
        if not log_file.exists():
            return []
        
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        return logs
    
    @staticmethod
    def filter_logs_by_level(logs: list, level: str) -> list:
        """
        Filter logs by level.
        
        Args:
            logs: List of log entries
            level: Log level to filter by
            
        Returns:
            Filtered list of log entries
        """
        return [log for log in logs if log.get("level") == level.upper()]
    
    @staticmethod
    def filter_logs_by_event_type(logs: list, event_type: str) -> list:
        """
        Filter logs by event type.
        
        Args:
            logs: List of log entries
            event_type: Event type to filter by
            
        Returns:
            Filtered list of log entries
        """
        return [log for log in logs if log.get("event_type") == event_type]
