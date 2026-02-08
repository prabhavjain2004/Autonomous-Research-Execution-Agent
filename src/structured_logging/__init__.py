"""
Structured logging module for observability and debugging.

Note: This module is named 'structured_logging' instead of 'logging' to avoid
conflicts with Python's standard library logging module.
"""

from .structured_logger import StructuredLogger, LogLevel

__all__ = ["StructuredLogger", "LogLevel"]
