"""
Unit tests for structured logging system.

Tests each log method, log level filtering, file creation, and log rotation.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from uuid import uuid4

from structured_logging import StructuredLogger, LogLevel
from models.data_models import ToolResult


class TestStructuredLogger:
    """Tests for StructuredLogger."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def logger(self, temp_log_dir):
        """Create logger instance for tests."""
        session_id = str(uuid4())
        logger = StructuredLogger(
            session_id=session_id,
            log_dir=temp_log_dir,
            console_output=False,
            log_level="DEBUG"
        )
        yield logger
        logger.close()
    
    def test_logger_initialization(self, temp_log_dir):
        """Test logger initialization creates log file."""
        session_id = str(uuid4())
        logger = StructuredLogger(
            session_id=session_id,
            log_dir=temp_log_dir,
            console_output=False
        )
        
        # Check log file was created
        log_file = Path(temp_log_dir) / f"session_{session_id}.json"
        assert log_file.exists()
        
        logger.close()
    
    def test_log_state_transition(self, logger, temp_log_dir):
        """Test logging state transitions."""
        logger.log_state_transition(
            from_state="IDLE",
            to_state="PLANNING",
            reason="New task received",
            agent="boss_agent"
        )
        
        # Read log file
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 1
        
        log = logs[0]
        assert log["event_type"] == "state_transition"
        assert log["level"] == "INFO"
        assert log["data"]["from_state"] == "IDLE"
        assert log["data"]["to_state"] == "PLANNING"
        assert log["data"]["reason"] == "New task received"
        assert log["data"]["agent"] == "boss_agent"
    
    def test_log_tool_call(self, logger, temp_log_dir):
        """Test logging tool calls."""
        tool_result = ToolResult(
            success=True,
            data={"results": ["item1", "item2"]},
            metadata={"count": 2}
        )
        
        logger.log_tool_call(
            tool_name="web_search",
            inputs={"query": "test query"},
            outputs=tool_result,
            execution_time=1.5,
            success=True
        )
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 1
        
        log = logs[0]
        assert log["event_type"] == "tool_call"
        assert log["data"]["tool_name"] == "web_search"
        assert log["data"]["execution_time"] == 1.5
        assert log["data"]["success"] is True
    
    def test_log_model_selection(self, logger, temp_log_dir):
        """Test logging model selection."""
        logger.log_model_selection(
            task_complexity="COMPLEX",
            selected_model="qwen-4b",
            reasoning="Complex reasoning task requires larger model",
            context_length=5000
        )
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 1
        
        log = logs[0]
        assert log["event_type"] == "model_selection"
        assert log["data"]["selected_model"] == "qwen-4b"
        assert log["data"]["task_complexity"] == "COMPLEX"
        assert log["data"]["context_length"] == 5000
    
    def test_log_confidence_scores(self, logger, temp_log_dir):
        """Test logging confidence scores."""
        logger.log_confidence_scores(
            agent_name="research_agent",
            self_score=85,
            boss_score=90,
            decision="proceed",
            reasoning="High quality output"
        )
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 1
        
        log = logs[0]
        assert log["event_type"] == "confidence_evaluation"
        assert log["data"]["agent_name"] == "research_agent"
        assert log["data"]["self_score"] == 85
        assert log["data"]["boss_score"] == 90
        assert log["data"]["decision"] == "proceed"
    
    def test_log_error(self, logger, temp_log_dir):
        """Test logging errors."""
        logger.log_error(
            error_type="ToolExecutionError",
            error_message="Connection timeout",
            stack_trace="Traceback...",
            context={"tool": "web_search", "url": "https://example.com"},
            agent="research_agent"
        )
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 1
        
        log = logs[0]
        assert log["event_type"] == "error"
        assert log["level"] == "ERROR"
        assert log["data"]["error_type"] == "ToolExecutionError"
        assert log["data"]["error_message"] == "Connection timeout"
    
    def test_log_decision(self, logger, temp_log_dir):
        """Test logging agent decisions."""
        logger.log_decision(
            agent_name="boss_agent",
            decision="delegate_to_research",
            reasoning="Need to gather competitor data",
            context={"task_id": "task-001"}
        )
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 1
        
        log = logs[0]
        assert log["event_type"] == "agent_decision"
        assert log["data"]["agent_name"] == "boss_agent"
        assert log["data"]["decision"] == "delegate_to_research"
    
    def test_log_performance_metric(self, logger, temp_log_dir):
        """Test logging performance metrics."""
        logger.log_performance_metric(
            metric_name="tool_execution_time",
            value=2.5,
            unit="seconds",
            context={"tool": "web_search"}
        )
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 1
        
        log = logs[0]
        assert log["event_type"] == "performance_metric"
        assert log["level"] == "DEBUG"
        assert log["data"]["metric_name"] == "tool_execution_time"
        assert log["data"]["value"] == 2.5
        assert log["data"]["unit"] == "seconds"
    
    def test_log_retry(self, logger, temp_log_dir):
        """Test logging retry attempts."""
        logger.log_retry(
            operation="web_search",
            retry_count=1,
            max_retries=2,
            reason="Rate limit exceeded",
            agent="research_agent"
        )
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 1
        
        log = logs[0]
        assert log["event_type"] == "retry"
        assert log["level"] == "WARNING"
        assert log["data"]["retry_count"] == 1
        assert log["data"]["max_retries"] == 2
    
    def test_log_level_filtering(self, temp_log_dir):
        """Test log level filtering."""
        session_id = str(uuid4())
        
        # Create logger with INFO level
        logger = StructuredLogger(
            session_id=session_id,
            log_dir=temp_log_dir,
            console_output=False,
            log_level="INFO"
        )
        
        # Log at different levels
        logger.log_debug("Debug message")
        logger.log_info("Info message")
        logger.log_warning("Warning message")
        logger.log_error_simple("Error message")
        
        logger.close()
        
        # Read logs
        logs = StructuredLogger.get_session_logs(temp_log_dir, session_id)
        
        # DEBUG should be filtered out
        assert len(logs) == 3
        levels = [log["level"] for log in logs]
        assert "DEBUG" not in levels
        assert "INFO" in levels
        assert "WARNING" in levels
        assert "ERROR" in levels
    
    def test_json_format_validity(self, logger, temp_log_dir):
        """Test that all log entries are valid JSON."""
        # Log various types of entries
        logger.log_info("Test message")
        logger.log_state_transition("STATE1", "STATE2", "reason")
        logger.log_tool_call("tool", {}, {}, 1.0)
        
        # Read log file directly
        log_file = Path(temp_log_dir) / f"session_{logger.session_id}.json"
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Should not raise JSONDecodeError
                    log_entry = json.loads(line)
                    assert isinstance(log_entry, dict)
                    assert "timestamp" in log_entry
                    assert "session_id" in log_entry
                    assert "level" in log_entry
                    assert "event_type" in log_entry
    
    def test_session_log_file_isolation(self, temp_log_dir):
        """Test that each session has its own log file."""
        session_id_1 = str(uuid4())
        session_id_2 = str(uuid4())
        
        logger1 = StructuredLogger(session_id_1, temp_log_dir, False)
        logger2 = StructuredLogger(session_id_2, temp_log_dir, False)
        
        logger1.log_info("Message from session 1")
        logger2.log_info("Message from session 2")
        
        logger1.close()
        logger2.close()
        
        # Check separate log files exist
        log_file_1 = Path(temp_log_dir) / f"session_{session_id_1}.json"
        log_file_2 = Path(temp_log_dir) / f"session_{session_id_2}.json"
        
        assert log_file_1.exists()
        assert log_file_2.exists()
        
        # Check logs are isolated
        logs1 = StructuredLogger.get_session_logs(temp_log_dir, session_id_1)
        logs2 = StructuredLogger.get_session_logs(temp_log_dir, session_id_2)
        
        assert len(logs1) == 1
        assert len(logs2) == 1
        assert logs1[0]["message"] == "Message from session 1"
        assert logs2[0]["message"] == "Message from session 2"
    
    def test_filter_logs_by_level(self, logger, temp_log_dir):
        """Test filtering logs by level."""
        logger.log_info("Info message")
        logger.log_warning("Warning message")
        logger.log_error_simple("Error message")
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        
        # Filter by level
        info_logs = StructuredLogger.filter_logs_by_level(logs, "INFO")
        warning_logs = StructuredLogger.filter_logs_by_level(logs, "WARNING")
        error_logs = StructuredLogger.filter_logs_by_level(logs, "ERROR")
        
        assert len(info_logs) == 1
        assert len(warning_logs) == 1
        assert len(error_logs) == 1
    
    def test_filter_logs_by_event_type(self, logger, temp_log_dir):
        """Test filtering logs by event type."""
        logger.log_state_transition("STATE1", "STATE2", "reason")
        logger.log_tool_call("tool", {}, {}, 1.0)
        logger.log_decision("agent", "decision", "reasoning")
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        
        # Filter by event type
        state_logs = StructuredLogger.filter_logs_by_event_type(logs, "state_transition")
        tool_logs = StructuredLogger.filter_logs_by_event_type(logs, "tool_call")
        decision_logs = StructuredLogger.filter_logs_by_event_type(logs, "agent_decision")
        
        assert len(state_logs) == 1
        assert len(tool_logs) == 1
        assert len(decision_logs) == 1
    
    def test_timestamp_format(self, logger, temp_log_dir):
        """Test that timestamps are in ISO 8601 format."""
        logger.log_info("Test message")
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 1
        
        timestamp = logs[0]["timestamp"]
        # Should be ISO 8601 format ending with Z
        assert timestamp.endswith("Z")
        
        # Should be parseable
        from datetime import datetime
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    def test_multiple_log_entries(self, logger, temp_log_dir):
        """Test logging multiple entries in sequence."""
        for i in range(10):
            logger.log_info(f"Message {i}")
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 10
        
        # Check messages are in order
        for i, log in enumerate(logs):
            assert log["message"] == f"Message {i}"
    
    def test_log_with_complex_data(self, logger, temp_log_dir):
        """Test logging with complex nested data structures."""
        complex_data = {
            "nested": {
                "level1": {
                    "level2": ["item1", "item2"]
                }
            },
            "list": [1, 2, 3],
            "string": "test"
        }
        
        logger.log_info("Complex data", data=complex_data)
        
        logs = StructuredLogger.get_session_logs(temp_log_dir, logger.session_id)
        assert len(logs) == 1
        
        # Verify complex data is preserved
        assert logs[0]["data"] == complex_data
    
    def test_get_session_logs_nonexistent(self, temp_log_dir):
        """Test getting logs for non-existent session returns empty list."""
        logs = StructuredLogger.get_session_logs(temp_log_dir, "nonexistent-session")
        assert logs == []
    
    def test_logger_close(self, temp_log_dir):
        """Test logger cleanup on close."""
        session_id = str(uuid4())
        logger = StructuredLogger(session_id, temp_log_dir, False)
        
        # Log something
        logger.log_info("Test")
        
        # Close logger
        logger.close()
        
        # Handlers should be removed
        assert len(logger.logger.handlers) == 0
