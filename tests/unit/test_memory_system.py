"""
Unit tests for memory system.

Tests database initialization, CRUD operations, connection handling,
and data size constraints.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from uuid import UUID

from memory import MemorySystem, SessionSummary, SessionHistory
from models.data_models import ToolResult, ResearchResult


class TestMemorySystem:
    """Tests for MemorySystem."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for tests."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_memory.db"
        yield str(db_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory(self, temp_db_path):
        """Create memory system instance for tests."""
        memory = MemorySystem(db_path=temp_db_path)
        yield memory
        memory.close()
    
    def test_memory_initialization(self, temp_db_path):
        """Test memory system initialization creates database."""
        memory = MemorySystem(db_path=temp_db_path)
        
        # Check database file was created
        assert Path(temp_db_path).exists()
        
        memory.close()
    
    def test_create_session(self, memory):
        """Test creating a new session."""
        session_id = memory.create_session("Research TapNex competitors")
        
        # Should return UUID
        assert isinstance(session_id, UUID)
        
        # Session should exist in database
        session_info = memory.get_session_info(session_id)
        assert session_info is not None
        assert session_info["goal"] == "Research TapNex competitors"
        assert session_info["status"] == "in_progress"
    
    def test_session_uniqueness(self, memory):
        """Test that each session gets a unique ID."""
        session_id_1 = memory.create_session("Goal 1")
        session_id_2 = memory.create_session("Goal 2")
        
        assert session_id_1 != session_id_2
    
    def test_store_decision(self, memory):
        """Test storing agent decision."""
        session_id = memory.create_session("Test goal")
        
        memory.store_decision(
            session_id=session_id,
            agent_name="research_agent",
            decision="search_web",
            context={"query": "test query"}
        )
        
        # Retrieve session history
        history = memory.get_session_history(session_id)
        assert history is not None
        assert len(history.decisions) == 1
        
        decision = history.decisions[0]
        assert decision["agent_name"] == "research_agent"
        assert decision["decision"] == "search_web"
        assert decision["context"]["query"] == "test query"
    
    def test_store_tool_output(self, memory):
        """Test storing tool execution output."""
        session_id = memory.create_session("Test goal")
        
        tool_result = ToolResult(
            success=True,
            data={"results": ["item1", "item2"]},
            metadata={"count": 2}
        )
        
        memory.store_tool_output(
            session_id=session_id,
            tool_name="web_search",
            output=tool_result,
            execution_time=1.5
        )
        
        # Retrieve session history
        history = memory.get_session_history(session_id)
        assert history is not None
        assert len(history.tool_executions) == 1
        
        execution = history.tool_executions[0]
        assert execution["tool_name"] == "web_search"
        assert execution["success"] is True
        assert execution["execution_time"] == 1.5
    
    def test_store_confidence_scores(self, memory):
        """Test storing confidence scores."""
        session_id = memory.create_session("Test goal")
        
        memory.store_confidence_scores(
            session_id=session_id,
            agent_name="research_agent",
            self_score=85,
            boss_score=90,
            retry_count=0
        )
        
        # Retrieve session history
        history = memory.get_session_history(session_id)
        assert history is not None
        assert len(history.confidence_scores) == 1
        
        scores = history.confidence_scores[0]
        assert scores["agent_name"] == "research_agent"
        assert scores["self_score"] == 85
        assert scores["boss_score"] == 90
        assert scores["retry_count"] == 0
    
    def test_store_final_result(self, memory):
        """Test storing final research result."""
        session_id = memory.create_session("Test goal")
        
        result = ResearchResult.create_new(
            goal="Test goal",
            agents_involved=["research_agent"],
            confidence_scores={"research_agent": {"self": 85, "boss": 90}},
            competitors=[{"name": "Company A"}],
            insights=["Insight 1"],
            recommendations=[{"action": "Action 1"}],
            sources=[{"url": "https://example.com"}],
            overall_confidence=87
        )
        
        memory.store_final_result(session_id, result)
        
        # Retrieve session history
        history = memory.get_session_history(session_id)
        assert history is not None
        assert history.final_result is not None
        assert history.final_result["goal"] == "Test goal"
        assert history.final_result["overall_confidence"] == 87
        
        # Check session status updated
        session_info = memory.get_session_info(session_id)
        assert session_info["status"] == "completed"
        assert session_info["overall_confidence"] == 87
    
    def test_get_session_history_complete(self, memory):
        """Test retrieving complete session history."""
        session_id = memory.create_session("Test goal")
        
        # Store various data
        memory.store_decision(
            session_id, "agent1", "decision1", {"key": "value"}
        )
        memory.store_tool_output(
            session_id,
            "tool1",
            ToolResult(success=True, data={"test": "data"}),
            1.0
        )
        memory.store_confidence_scores(
            session_id, "agent1", 85, 90
        )
        
        # Retrieve history
        history = memory.get_session_history(session_id)
        
        assert history is not None
        assert history.session_id == str(session_id)
        assert history.goal == "Test goal"
        assert len(history.decisions) == 1
        assert len(history.tool_executions) == 1
        assert len(history.confidence_scores) == 1
    
    def test_get_session_history_nonexistent(self, memory):
        """Test retrieving history for non-existent session."""
        from uuid import uuid4
        
        history = memory.get_session_history(uuid4())
        assert history is None
    
    def test_list_sessions(self, memory):
        """Test listing sessions."""
        # Create multiple sessions
        session_id_1 = memory.create_session("Goal 1")
        session_id_2 = memory.create_session("Goal 2")
        session_id_3 = memory.create_session("Goal 3")
        
        # List sessions
        sessions = memory.list_sessions(limit=10)
        
        assert len(sessions) == 3
        assert all(isinstance(s, SessionSummary) for s in sessions)
        
        # Should be ordered by created_at DESC (most recent first)
        session_ids = [s.session_id for s in sessions]
        assert str(session_id_3) in session_ids
        assert str(session_id_2) in session_ids
        assert str(session_id_1) in session_ids
    
    def test_list_sessions_limit(self, memory):
        """Test listing sessions with limit."""
        # Create 5 sessions
        for i in range(5):
            memory.create_session(f"Goal {i}")
        
        # List with limit
        sessions = memory.list_sessions(limit=3)
        
        assert len(sessions) == 3
    
    def test_update_session_status(self, memory):
        """Test updating session status."""
        session_id = memory.create_session("Test goal")
        
        # Update status
        memory.update_session_status(session_id, "error")
        
        # Check status updated
        session_info = memory.get_session_info(session_id)
        assert session_info["status"] == "error"
    
    def test_multiple_decisions_per_session(self, memory):
        """Test storing multiple decisions for same session."""
        session_id = memory.create_session("Test goal")
        
        # Store multiple decisions
        for i in range(5):
            memory.store_decision(
                session_id,
                f"agent_{i}",
                f"decision_{i}",
                {"index": i}
            )
        
        # Retrieve history
        history = memory.get_session_history(session_id)
        assert len(history.decisions) == 5
        
        # Check order preserved
        for i, decision in enumerate(history.decisions):
            assert decision["agent_name"] == f"agent_{i}"
    
    def test_multiple_tool_executions_per_session(self, memory):
        """Test storing multiple tool executions for same session."""
        session_id = memory.create_session("Test goal")
        
        # Store multiple tool executions
        for i in range(5):
            memory.store_tool_output(
                session_id,
                f"tool_{i}",
                ToolResult(success=True, data={"index": i}),
                float(i)
            )
        
        # Retrieve history
        history = memory.get_session_history(session_id)
        assert len(history.tool_executions) == 5
    
    def test_multiple_confidence_scores_per_session(self, memory):
        """Test storing multiple confidence scores for same session."""
        session_id = memory.create_session("Test goal")
        
        # Store multiple confidence scores (e.g., from retries)
        for i in range(3):
            memory.store_confidence_scores(
                session_id,
                "research_agent",
                70 + i * 5,
                75 + i * 5,
                retry_count=i
            )
        
        # Retrieve history
        history = memory.get_session_history(session_id)
        assert len(history.confidence_scores) == 3
        
        # Check retry counts
        for i, scores in enumerate(history.confidence_scores):
            assert scores["retry_count"] == i
    
    def test_session_summary_to_dict(self):
        """Test SessionSummary to_dict method."""
        summary = SessionSummary(
            session_id="test-id",
            goal="Test goal",
            created_at="2024-01-15T10:00:00",
            completed_at="2024-01-15T10:30:00",
            status="completed",
            overall_confidence=85
        )
        
        summary_dict = summary.to_dict()
        assert isinstance(summary_dict, dict)
        assert summary_dict["session_id"] == "test-id"
        assert summary_dict["goal"] == "Test goal"
        assert summary_dict["overall_confidence"] == 85
    
    def test_session_history_to_dict(self):
        """Test SessionHistory to_dict method."""
        history = SessionHistory(
            session_id="test-id",
            goal="Test goal",
            created_at="2024-01-15T10:00:00",
            completed_at="2024-01-15T10:30:00",
            status="completed",
            decisions=[],
            tool_executions=[],
            confidence_scores=[],
            final_result=None
        )
        
        history_dict = history.to_dict()
        assert isinstance(history_dict, dict)
        assert history_dict["session_id"] == "test-id"
        assert history_dict["goal"] == "Test goal"
    
    def test_tool_output_summarization(self, memory):
        """Test that tool outputs are summarized to prevent unbounded growth."""
        session_id = memory.create_session("Test goal")
        
        # Store tool output with large data
        large_data = {"results": ["item"] * 1000}  # Large list
        tool_result = ToolResult(
            success=True,
            data=large_data,
            metadata={"count": 1000}
        )
        
        memory.store_tool_output(
            session_id,
            "web_search",
            tool_result,
            1.0
        )
        
        # Retrieve history
        history = memory.get_session_history(session_id)
        execution = history.tool_executions[0]
        
        # Output should be summarized (not full data)
        assert "has_data" in execution["output"]
        assert execution["output"]["has_data"] is True
        # Full data should not be stored
        assert "results" not in execution["output"]
    
    def test_decision_persistence_round_trip(self, memory):
        """Test decision can be stored and retrieved correctly."""
        session_id = memory.create_session("Test goal")
        
        original_context = {
            "query": "test query",
            "max_results": 10,
            "nested": {"key": "value"}
        }
        
        memory.store_decision(
            session_id,
            "research_agent",
            "search_web",
            original_context
        )
        
        # Retrieve and verify
        history = memory.get_session_history(session_id)
        retrieved_context = history.decisions[0]["context"]
        
        assert retrieved_context == original_context
    
    def test_final_result_persistence_round_trip(self, memory):
        """Test final result can be stored and retrieved correctly."""
        session_id = memory.create_session("Test goal")
        
        original_result = ResearchResult.create_new(
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
        
        memory.store_final_result(session_id, original_result)
        
        # Retrieve and verify
        history = memory.get_session_history(session_id)
        retrieved_result = history.final_result
        
        assert retrieved_result["goal"] == original_result.goal
        assert retrieved_result["overall_confidence"] == original_result.overall_confidence
        assert len(retrieved_result["agents_involved"]) == 2
        assert len(retrieved_result["insights"]) == 2
    
    def test_connection_cleanup(self, temp_db_path):
        """Test that database connections are properly cleaned up."""
        memory = MemorySystem(db_path=temp_db_path)
        
        # Perform operations
        session_id = memory.create_session("Test")
        memory.store_decision(session_id, "agent", "decision", {})
        
        # Close memory system
        memory.close()
        
        # Should be able to create new instance and access data
        memory2 = MemorySystem(db_path=temp_db_path)
        history = memory2.get_session_history(session_id)
        
        assert history is not None
        assert len(history.decisions) == 1
        
        memory2.close()
