"""
Unit tests for base tool interface.

Tests input validation, error handling, and tool output format consistency.
"""

import pytest
from tools.base_tool import BaseTool
from models.data_models import ToolResult


class MockSuccessTool(BaseTool):
    """Mock tool that succeeds."""
    
    def validate_input(self, **kwargs) -> bool:
        return "required_param" in kwargs
    
    def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            data={"result": "success", "input": kwargs.get("required_param")},
            metadata={"tool": "mock_success"}
        )


class MockFailureTool(BaseTool):
    """Mock tool that raises an exception."""
    
    def validate_input(self, **kwargs) -> bool:
        return True
    
    def execute(self, **kwargs) -> ToolResult:
        raise ValueError("Simulated tool failure")


class MockInvalidResultTool(BaseTool):
    """Mock tool that returns invalid result."""
    
    def validate_input(self, **kwargs) -> bool:
        return True
    
    def execute(self, **kwargs) -> ToolResult:
        # Return invalid result (success=True but no data)
        return ToolResult(success=True, data=None)


class TestBaseTool:
    """Tests for BaseTool."""
    
    def test_successful_execution(self):
        """Test successful tool execution."""
        tool = MockSuccessTool()
        result = tool.run(required_param="test_value")
        
        assert result.success is True
        assert result.data is not None
        assert result.data["result"] == "success"
        assert result.data["input"] == "test_value"
        assert result.error is None
    
    def test_input_validation_success(self):
        """Test that input validation passes with valid inputs."""
        tool = MockSuccessTool()
        assert tool.validate_input(required_param="test") is True
    
    def test_input_validation_failure(self):
        """Test that input validation fails with invalid inputs."""
        tool = MockSuccessTool()
        assert tool.validate_input(wrong_param="test") is False
    
    def test_run_with_invalid_input(self):
        """Test that run() returns error when validation fails."""
        tool = MockSuccessTool()
        result = tool.run(wrong_param="test")
        
        assert result.success is False
        assert result.data is None
        assert "validation failed" in result.error.lower()
    
    def test_error_handling(self):
        """Test that errors are handled gracefully."""
        tool = MockFailureTool()
        result = tool.run()
        
        assert result.success is False
        assert result.data is None
        assert result.error is not None
        assert "ValueError" in result.error
        assert "Simulated tool failure" in result.error
    
    def test_error_no_exception_propagation(self):
        """Test that exceptions don't propagate from run()."""
        tool = MockFailureTool()
        
        # Should not raise exception
        try:
            result = tool.run()
            assert result.success is False
        except Exception:
            pytest.fail("Exception should not propagate from run()")
    
    def test_handle_error_returns_tool_result(self):
        """Test that handle_error returns proper ToolResult."""
        tool = MockSuccessTool()
        error = ValueError("Test error")
        
        result = tool.handle_error(error, context={"key": "value"})
        
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.data is None
        assert "ValueError" in result.error
        assert "Test error" in result.error
        assert result.metadata["key"] == "value"
    
    def test_invalid_result_handling(self):
        """Test that invalid results are caught."""
        tool = MockInvalidResultTool()
        result = tool.run()
        
        assert result.success is False
        assert "invalid result" in result.error.lower()
    
    def test_tool_result_format_consistency(self):
        """Test that all tool results have consistent format."""
        success_tool = MockSuccessTool()
        failure_tool = MockFailureTool()
        
        success_result = success_tool.run(required_param="test")
        failure_result = failure_tool.run()
        
        # Both should be ToolResult instances
        assert isinstance(success_result, ToolResult)
        assert isinstance(failure_result, ToolResult)
        
        # Both should have all required fields
        assert hasattr(success_result, 'success')
        assert hasattr(success_result, 'data')
        assert hasattr(success_result, 'error')
        assert hasattr(success_result, 'metadata')
        
        assert hasattr(failure_result, 'success')
        assert hasattr(failure_result, 'data')
        assert hasattr(failure_result, 'error')
        assert hasattr(failure_result, 'metadata')
    
    def test_tool_with_logger(self):
        """Test tool with logger attached."""
        import tempfile
        import shutil
        from uuid import uuid4
        from structured_logging import StructuredLogger
        
        temp_dir = tempfile.mkdtemp()
        session_id = str(uuid4())
        
        try:
            logger = StructuredLogger(
                session_id=session_id,
                log_dir=temp_dir,
                console_output=False
            )
            
            tool = MockFailureTool(logger=logger)
            result = tool.run()
            
            # Error should be logged
            logs = StructuredLogger.get_session_logs(temp_dir, session_id)
            error_logs = [log for log in logs if log["event_type"] == "error"]
            
            assert len(error_logs) > 0
            assert "ValueError" in error_logs[0]["data"]["error_type"]
            
            logger.close()
        finally:
            shutil.rmtree(temp_dir)
    
    def test_tool_without_logger(self):
        """Test tool works without logger."""
        tool = MockSuccessTool(logger=None)
        result = tool.run(required_param="test")
        
        assert result.success is True
    
    def test_multiple_executions(self):
        """Test tool can be executed multiple times."""
        tool = MockSuccessTool()
        
        result1 = tool.run(required_param="value1")
        result2 = tool.run(required_param="value2")
        result3 = tool.run(required_param="value3")
        
        assert result1.success is True
        assert result2.success is True
        assert result3.success is True
        
        assert result1.data["input"] == "value1"
        assert result2.data["input"] == "value2"
        assert result3.data["input"] == "value3"
    
    def test_error_context_preserved(self):
        """Test that error context is preserved in result."""
        tool = MockFailureTool()
        result = tool.run(param1="value1", param2="value2")
        
        assert result.success is False
        assert "param1" in result.metadata["inputs"]
        assert "param2" in result.metadata["inputs"]
