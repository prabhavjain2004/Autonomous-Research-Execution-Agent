"""
Unit Tests for Output Formatter

Tests the output formatting functionality for research results.
"""

import pytest
import uuid
from datetime import datetime
from dataclasses import dataclass

from output_formatter import OutputFormatter
from models.data_models import AgentOutput, ResearchResult


# Create test agent outputs
def create_test_output(agent_name="Test Agent", confidence=80):
    """Helper to create test AgentOutput."""
    return AgentOutput(
        agent_name=agent_name,
        task_id="test-task-123",
        results={
            "insights": ["Test insight"],
            "recommendations": ["Test recommendation"]
        },
        self_confidence=confidence,
        reasoning="Test reasoning",
        sources=["https://example.com"],
        execution_time=1.0
    )


class TestOutputFormatter:
    """Test suite for OutputFormatter class."""
    
    def test_initialization(self):
        """Test OutputFormatter initializes correctly."""
        formatter = OutputFormatter()
        assert formatter is not None
    
    def test_format_research_result_success(self):
        """Test formatting a successful research result."""
        formatter = OutputFormatter()
        
        outputs = [
            create_test_output("Research Agent", 85),
            create_test_output("Analyst Agent", 90),
            create_test_output("Strategy Agent", 88)
        ]
        
        result = formatter.format_research_result("Research AI trends", outputs)
        
        assert result is not None
        assert result.goal == "Research AI trends"
        assert len(result.agents_involved) == 3
        assert "Research Agent" in result.agents_involved
        assert len(result.insights) >= 1
        assert len(result.recommendations) >= 1
        assert 0 <= result.overall_confidence <= 100
    
    def test_format_research_result_with_session_id(self):
        """Test formatting with provided session ID."""
        formatter = OutputFormatter()
        session_id = str(uuid.uuid4())
        
        outputs = [create_test_output()]
        
        result = formatter.format_research_result("Test goal", outputs, session_id=session_id)
        
        assert result.session_id == session_id
    
    def test_format_research_result_generates_uuid(self):
        """Test that UUID is generated if not provided."""
        formatter = OutputFormatter()
        
        outputs = [create_test_output()]
        
        result = formatter.format_research_result("Test goal", outputs)
        
        # Should be valid UUID
        uuid.UUID(result.session_id)
    
    def test_format_research_result_empty_goal(self):
        """Test that empty goal raises ValueError."""
        formatter = OutputFormatter()
        
        outputs = [create_test_output()]
        
        with pytest.raises(ValueError, match="goal cannot be empty"):
            formatter.format_research_result("", outputs)
    
    def test_format_research_result_no_outputs(self):
        """Test that no outputs raises ValueError."""
        formatter = OutputFormatter()
        
        with pytest.raises(ValueError, match="At least one agent output is required"):
            formatter.format_research_result("Test goal", [])
    
    def test_format_research_result_invalid_session_id(self):
        """Test that invalid session ID raises ValueError."""
        formatter = OutputFormatter()
        
        outputs = [create_test_output()]
        
        with pytest.raises(ValueError, match="Invalid session_id format"):
            formatter.format_research_result("Test goal", outputs, session_id="invalid-uuid")
    
    def test_calculate_overall_confidence(self):
        """Test overall confidence calculation."""
        formatter = OutputFormatter()
        
        confidence_scores = {
            "Research Agent": {"self": 80, "boss": 75},
            "Analyst Agent": {"self": 90, "boss": 85},
            "Strategy Agent": {"self": 85, "boss": 80}
        }
        
        overall = formatter._calculate_overall_confidence(confidence_scores)
        
        assert 0 <= overall <= 100
        # Should be weighted average: 40% self, 60% boss
        expected_self = (80 + 90 + 85) / 3
        expected_boss = (75 + 85 + 80) / 3
        expected = int((expected_self * 0.4) + (expected_boss * 0.6))
        assert abs(overall - expected) <= 1  # Allow 1 point rounding difference
    
    def test_calculate_overall_confidence_empty(self):
        """Test overall confidence with no scores."""
        formatter = OutputFormatter()
        
        overall = formatter._calculate_overall_confidence({})
        
        assert overall == 0
    
    def test_format_error_result(self):
        """Test formatting an error result."""
        formatter = OutputFormatter()
        
        result = formatter.format_error_result(
            "Test goal",
            "Tool execution failed",
            partial_outputs=None
        )
        
        assert result is not None
        assert result.goal == "Test goal"
        assert result.overall_confidence == 0
        assert "failed" in result.insights[0].lower()
        assert len(result.recommendations) > 0
    
    def test_format_error_result_with_partial_outputs(self):
        """Test formatting error result with partial outputs."""
        formatter = OutputFormatter()
        
        partial_outputs = [create_test_output("Research Agent", 60)]
        
        result = formatter.format_error_result(
            "Test goal",
            "Network error",
            partial_outputs=partial_outputs
        )
        
        assert "Research Agent" in result.agents_involved
        assert "Research Agent" in result.confidence_scores
    
    def test_validate_result_success(self):
        """Test validating a valid result."""
        formatter = OutputFormatter()
        
        result = ResearchResult.create_new(
            goal="Test goal",
            agents_involved=["Research Agent"],
            confidence_scores={"Research Agent": {"self": 80, "boss": 75}},
            competitors=[],
            insights=["Test insight"],
            recommendations=[{"text": "Test recommendation", "priority": "medium"}],
            sources=[{"url": "https://example.com", "title": "Test"}],
            overall_confidence=77
        )
        
        assert formatter.validate_result(result) is True
    
    def test_validate_result_invalid_uuid(self):
        """Test validation fails with invalid UUID."""
        formatter = OutputFormatter()
        
        result = ResearchResult.create_new(
            goal="Test goal",
            agents_involved=["Research Agent"],
            confidence_scores={"Research Agent": {"self": 80, "boss": 75}},
            competitors=[],
            insights=["Test insight"],
            recommendations=[{"text": "Test", "priority": "medium"}],
            sources=[],
            overall_confidence=77
        )
        
        # Corrupt the UUID
        result.session_id = "invalid-uuid"
        
        assert formatter.validate_result(result) is False
    
    def test_format_preserves_goal(self):
        """Test that goal is preserved exactly."""
        formatter = OutputFormatter()
        goal = "Research the impact of AI on healthcare in 2024"
        
        outputs = [create_test_output()]
        
        result = formatter.format_research_result(goal, outputs)
        
        assert result.goal == goal
    
    def test_format_includes_timestamp(self):
        """Test that result includes valid timestamp."""
        formatter = OutputFormatter()
        
        outputs = [create_test_output()]
        
        result = formatter.format_research_result("Test goal", outputs)
        
        # Should be valid ISO 8601 timestamp
        datetime.fromisoformat(result.timestamp.replace('Z', '+00:00'))
    
    def test_format_with_multiple_agents(self):
        """Test formatting with multiple different agents."""
        formatter = OutputFormatter()
        
        outputs = [
            create_test_output("Research Agent", 85),
            create_test_output("Analyst Agent", 90),
            create_test_output("Strategy Agent", 88)
        ]
        
        result = formatter.format_research_result("Test goal", outputs)
        
        assert len(result.agents_involved) == 3
        assert len(result.confidence_scores) == 3
        assert all(agent in result.confidence_scores for agent in result.agents_involved)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
