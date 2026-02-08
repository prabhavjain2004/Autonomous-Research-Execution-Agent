"""
Unit tests for data models.

Tests serialization, deserialization, validation, and edge cases for all data models.
"""

import pytest
import json
from datetime import datetime
from uuid import UUID

from models.data_models import (
    Task,
    AgentOutput,
    EvaluationResult,
    ResearchResult,
    SearchResult,
    ModelResponse,
    ToolResult,
    AgentType,
    DecisionType,
)


class TestTask:
    """Tests for Task data model."""
    
    def test_task_creation(self):
        """Test creating a valid task."""
        task = Task(
            task_id="task-001",
            description="Research competitors",
            agent_type="research",
            context={"query": "TapNex competitors"},
            priority=1
        )
        assert task.task_id == "task-001"
        assert task.description == "Research competitors"
        assert task.agent_type == "research"
        assert task.priority == 1
    
    def test_task_validation_success(self):
        """Test task validation with valid data."""
        task = Task(
            task_id="task-001",
            description="Research competitors",
            agent_type="research",
            context={}
        )
        assert task.validate() is True
    
    def test_task_validation_empty_id(self):
        """Test task validation fails with empty ID."""
        task = Task(
            task_id="",
            description="Research competitors",
            agent_type="research",
            context={}
        )
        assert task.validate() is False
    
    def test_task_validation_invalid_agent_type(self):
        """Test task validation fails with invalid agent type."""
        task = Task(
            task_id="task-001",
            description="Research competitors",
            agent_type="invalid_agent",
            context={}
        )
        assert task.validate() is False
    
    def test_task_validation_invalid_priority(self):
        """Test task validation fails with invalid priority."""
        task = Task(
            task_id="task-001",
            description="Research competitors",
            agent_type="research",
            context={},
            priority=0
        )
        assert task.validate() is False


class TestAgentOutput:
    """Tests for AgentOutput data model."""
    
    def test_agent_output_creation(self):
        """Test creating valid agent output."""
        output = AgentOutput(
            agent_name="research_agent",
            task_id="task-001",
            results={"competitors": ["Company A", "Company B"]},
            self_confidence=85,
            reasoning="Found multiple reliable sources",
            sources=["https://example.com"],
            execution_time=12.5
        )
        assert output.agent_name == "research_agent"
        assert output.self_confidence == 85
        assert output.execution_time == 12.5
    
    def test_agent_output_validation_success(self):
        """Test agent output validation with valid data."""
        output = AgentOutput(
            agent_name="research_agent",
            task_id="task-001",
            results={},
            self_confidence=85,
            reasoning="Test",
            sources=[],
            execution_time=1.0
        )
        assert output.validate() is True
    
    def test_agent_output_validation_confidence_bounds(self):
        """Test agent output validation enforces confidence bounds."""
        # Test lower bound
        output = AgentOutput(
            agent_name="research_agent",
            task_id="task-001",
            results={},
            self_confidence=-1,
            reasoning="Test",
            sources=[],
            execution_time=1.0
        )
        assert output.validate() is False
        
        # Test upper bound
        output.self_confidence = 101
        assert output.validate() is False
        
        # Test valid bounds
        output.self_confidence = 0
        assert output.validate() is True
        output.self_confidence = 100
        assert output.validate() is True
    
    def test_agent_output_validation_negative_time(self):
        """Test agent output validation fails with negative execution time."""
        output = AgentOutput(
            agent_name="research_agent",
            task_id="task-001",
            results={},
            self_confidence=85,
            reasoning="Test",
            sources=[],
            execution_time=-1.0
        )
        assert output.validate() is False


class TestEvaluationResult:
    """Tests for EvaluationResult data model."""
    
    def test_evaluation_result_creation(self):
        """Test creating valid evaluation result."""
        result = EvaluationResult(
            boss_confidence=90,
            decision="proceed",
            reasoning="High quality output",
            suggestions=[]
        )
        assert result.boss_confidence == 90
        assert result.decision == "proceed"
    
    def test_evaluation_result_validation_success(self):
        """Test evaluation result validation with valid data."""
        result = EvaluationResult(
            boss_confidence=90,
            decision="proceed",
            reasoning="Good"
        )
        assert result.validate() is True
    
    def test_evaluation_result_validation_confidence_bounds(self):
        """Test evaluation result validation enforces confidence bounds."""
        result = EvaluationResult(
            boss_confidence=101,
            decision="proceed",
            reasoning="Test"
        )
        assert result.validate() is False
    
    def test_evaluation_result_validation_invalid_decision(self):
        """Test evaluation result validation fails with invalid decision."""
        result = EvaluationResult(
            boss_confidence=90,
            decision="invalid_decision",
            reasoning="Test"
        )
        assert result.validate() is False
    
    def test_evaluation_result_validation_empty_reasoning(self):
        """Test evaluation result validation fails with empty reasoning."""
        result = EvaluationResult(
            boss_confidence=90,
            decision="proceed",
            reasoning=""
        )
        assert result.validate() is False


class TestSearchResult:
    """Tests for SearchResult data model."""
    
    def test_search_result_creation(self):
        """Test creating valid search result."""
        result = SearchResult(
            title="Test Article",
            url="https://example.com",
            snippet="This is a test snippet",
            source="duckduckgo",
            timestamp="2024-01-15T10:30:00Z"
        )
        assert result.title == "Test Article"
        assert result.url == "https://example.com"
    
    def test_search_result_to_dict(self):
        """Test search result serialization to dict."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="Snippet",
            source="google",
            timestamp="2024-01-15T10:30:00Z"
        )
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["title"] == "Test"
        assert result_dict["url"] == "https://example.com"


class TestModelResponse:
    """Tests for ModelResponse data model."""
    
    def test_model_response_success(self):
        """Test creating successful model response."""
        response = ModelResponse(
            model="qwen-4b",
            text="Generated text",
            tokens_used=100,
            latency=1.5,
            success=True
        )
        assert response.success is True
        assert response.error is None
        assert response.validate() is True
    
    def test_model_response_failure(self):
        """Test creating failed model response."""
        response = ModelResponse(
            model="qwen-4b",
            text="",
            tokens_used=0,
            latency=0.5,
            success=False,
            error="API timeout"
        )
        assert response.success is False
        assert response.error == "API timeout"
        assert response.validate() is True
    
    def test_model_response_validation_success_without_text(self):
        """Test model response validation fails if success but no text."""
        response = ModelResponse(
            model="qwen-4b",
            text="",
            tokens_used=0,
            latency=0.5,
            success=True
        )
        assert response.validate() is False
    
    def test_model_response_validation_failure_without_error(self):
        """Test model response validation fails if failure but no error."""
        response = ModelResponse(
            model="qwen-4b",
            text="",
            tokens_used=0,
            latency=0.5,
            success=False
        )
        assert response.validate() is False
    
    def test_model_response_validation_negative_values(self):
        """Test model response validation fails with negative values."""
        response = ModelResponse(
            model="qwen-4b",
            text="Test",
            tokens_used=-1,
            latency=1.0,
            success=True
        )
        assert response.validate() is False


class TestToolResult:
    """Tests for ToolResult data model."""
    
    def test_tool_result_success(self):
        """Test creating successful tool result."""
        result = ToolResult(
            success=True,
            data={"results": ["item1", "item2"]},
            metadata={"execution_time": 1.5}
        )
        assert result.success is True
        assert result.data is not None
        assert result.validate() is True
    
    def test_tool_result_failure(self):
        """Test creating failed tool result."""
        result = ToolResult(
            success=False,
            data=None,
            error="Connection timeout"
        )
        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.validate() is True
    
    def test_tool_result_validation_success_without_data(self):
        """Test tool result validation fails if success but no data."""
        result = ToolResult(
            success=True,
            data=None
        )
        assert result.validate() is False
    
    def test_tool_result_validation_failure_without_error(self):
        """Test tool result validation fails if failure but no error."""
        result = ToolResult(
            success=False,
            data=None
        )
        assert result.validate() is False


class TestResearchResult:
    """Tests for ResearchResult data model."""
    
    def test_research_result_create_new(self):
        """Test creating new research result with auto-generated fields."""
        result = ResearchResult.create_new(
            goal="Research TapNex competitors",
            agents_involved=["research_agent", "analyst_agent"],
            confidence_scores={
                "research_agent": {"self": 85, "boss": 90},
                "analyst_agent": {"self": 80, "boss": 85}
            },
            competitors=[{"name": "Company A"}],
            insights=["Insight 1"],
            recommendations=[{"action": "Action 1"}],
            sources=[{"url": "https://example.com"}],
            overall_confidence=87
        )
        
        # Check auto-generated fields
        assert result.session_id is not None
        assert result.timestamp is not None
        
        # Validate UUID format
        UUID(result.session_id)
        
        # Validate ISO 8601 timestamp
        datetime.fromisoformat(result.timestamp.replace('Z', '+00:00'))
    
    def test_research_result_to_json(self):
        """Test research result serialization to JSON."""
        result = ResearchResult.create_new(
            goal="Test goal",
            agents_involved=["research_agent"],
            confidence_scores={"research_agent": {"self": 85, "boss": 90}},
            competitors=[],
            insights=[],
            recommendations=[],
            sources=[],
            overall_confidence=85
        )
        
        json_str = result.to_json()
        assert isinstance(json_str, str)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["goal"] == "Test goal"
        assert parsed["overall_confidence"] == 85
    
    def test_research_result_to_dict(self):
        """Test research result conversion to dict."""
        result = ResearchResult.create_new(
            goal="Test goal",
            agents_involved=["research_agent"],
            confidence_scores={"research_agent": {"self": 85, "boss": 90}},
            competitors=[],
            insights=[],
            recommendations=[],
            sources=[],
            overall_confidence=85
        )
        
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert "session_id" in result_dict
        assert "goal" in result_dict
    
    def test_research_result_validation_success(self):
        """Test research result validation with valid data."""
        result = ResearchResult.create_new(
            goal="Test goal",
            agents_involved=["research_agent"],
            confidence_scores={"research_agent": {"self": 85, "boss": 90}},
            competitors=[],
            insights=[],
            recommendations=[],
            sources=[{"url": "https://example.com"}],
            overall_confidence=85
        )
        assert result.validate() is True
    
    def test_research_result_validation_invalid_uuid(self):
        """Test research result validation fails with invalid UUID."""
        result = ResearchResult(
            session_id="not-a-uuid",
            goal="Test",
            timestamp="2024-01-15T10:30:00Z",
            agents_involved=["research_agent"],
            confidence_scores={"research_agent": {"self": 85, "boss": 90}},
            competitors=[],
            insights=[],
            recommendations=[],
            sources=[],
            overall_confidence=85
        )
        assert result.validate() is False
    
    def test_research_result_validation_empty_agents(self):
        """Test research result validation fails with empty agents list."""
        result = ResearchResult.create_new(
            goal="Test",
            agents_involved=[],
            confidence_scores={},
            competitors=[],
            insights=[],
            recommendations=[],
            sources=[],
            overall_confidence=85
        )
        assert result.validate() is False
    
    def test_research_result_validation_confidence_scores(self):
        """Test research result validation checks confidence score structure."""
        result = ResearchResult.create_new(
            goal="Test",
            agents_involved=["research_agent"],
            confidence_scores={"research_agent": {"self": 85}},  # Missing 'boss'
            competitors=[],
            insights=[],
            recommendations=[],
            sources=[],
            overall_confidence=85
        )
        assert result.validate() is False
    
    def test_research_result_validation_confidence_bounds(self):
        """Test research result validation enforces confidence bounds."""
        result = ResearchResult.create_new(
            goal="Test",
            agents_involved=["research_agent"],
            confidence_scores={"research_agent": {"self": 101, "boss": 90}},
            competitors=[],
            insights=[],
            recommendations=[],
            sources=[],
            overall_confidence=85
        )
        assert result.validate() is False
    
    def test_research_result_validation_sources_require_url(self):
        """Test research result validation requires URL in sources."""
        result = ResearchResult.create_new(
            goal="Test",
            agents_involved=["research_agent"],
            confidence_scores={"research_agent": {"self": 85, "boss": 90}},
            competitors=[],
            insights=[],
            recommendations=[],
            sources=[{"title": "No URL"}],
            overall_confidence=85
        )
        assert result.validate() is False
    
    def test_research_result_validate_schema(self):
        """Test research result schema validation."""
        result = ResearchResult.create_new(
            goal="Test",
            agents_involved=["research_agent"],
            confidence_scores={"research_agent": {"self": 85, "boss": 90}},
            competitors=[],
            insights=[],
            recommendations=[],
            sources=[{"url": "https://example.com"}],
            overall_confidence=85
        )
        assert result.validate_schema() is True
    
    def test_research_result_round_trip_serialization(self):
        """Test research result can be serialized and deserialized."""
        original = ResearchResult.create_new(
            goal="Test goal",
            agents_involved=["research_agent", "analyst_agent"],
            confidence_scores={
                "research_agent": {"self": 85, "boss": 90},
                "analyst_agent": {"self": 80, "boss": 85}
            },
            competitors=[{"name": "Company A", "url": "https://example.com"}],
            insights=["Insight 1", "Insight 2"],
            recommendations=[{"action": "Action 1", "priority": "high"}],
            sources=[{"url": "https://example.com", "title": "Source 1"}],
            overall_confidence=87
        )
        
        # Serialize to JSON
        json_str = original.to_json()
        
        # Deserialize back
        data = json.loads(json_str)
        reconstructed = ResearchResult(**data)
        
        # Verify fields match
        assert reconstructed.goal == original.goal
        assert reconstructed.session_id == original.session_id
        assert reconstructed.overall_confidence == original.overall_confidence
        assert len(reconstructed.agents_involved) == len(original.agents_involved)
