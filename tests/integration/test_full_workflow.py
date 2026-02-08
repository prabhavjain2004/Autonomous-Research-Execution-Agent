"""
Full End-to-End Integration Test

This test runs the complete research workflow from start to finish,
catching all integration issues including:
- UUID serialization
- Method signature mismatches
- Data type conversions
- JSON serialization
- Database operations
- WebSocket communication
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from boss_agent import BossAgent
from memory.memory_system import MemorySystem
from structured_logging.structured_logger import StructuredLogger
from config import Config


class TestFullWorkflow:
    """Test complete research workflow end-to-end"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def boss_agent(self, temp_db, temp_log_dir):
        """Create BossAgent with real dependencies"""
        from model_router import ModelRouter
        import os
        
        logger = StructuredLogger(
            session_id="test-integration",
            log_dir=temp_log_dir
        )
        memory = MemorySystem(db_path=temp_db, logger=logger)
        
        # Create ModelRouter with test API key
        api_key = os.getenv("OPENROUTER_API_KEY", "test-key")
        model_router = ModelRouter(api_key=api_key, logger=logger)
        
        # Use realistic thresholds from config
        boss = BossAgent(
            memory_system=memory,
            logger=logger,
            model_router=model_router,
            max_retries=2,
            confidence_threshold=0.50  # Realistic threshold
        )
        
        return boss
    
    def test_complete_workflow_with_mocked_tools(self, boss_agent, monkeypatch):
        """
        Test complete workflow with mocked tool responses
        
        This catches:
        - UUID serialization issues
        - Method signature mismatches
        - Data type conversions
        - JSON serialization
        - Database operations
        """
        from tools.web_search import WebSearchTool
        from tools.web_scraper import WebScraperTool
        from models.data_models import ToolResult
        
        # Mock web search to return realistic data
        def mock_search_run(**kwargs):
            return ToolResult(
                success=True,
                data={
                    "results": [
                        {
                            "title": "Test Source 1",
                            "url": "https://example.com/1",
                            "snippet": "Test content about pricing"
                        },
                        {
                            "title": "Test Source 2",
                            "url": "https://example.com/2",
                            "snippet": "More pricing information"
                        }
                    ]
                },
                metadata={"engine": "test"}
            )
        
        # Mock web scraper to return content
        def mock_scraper_run(**kwargs):
            return ToolResult(
                success=True,
                data={
                    "content": "This is test content about pricing differences. " * 50,
                    "url": kwargs.get("url", ""),
                    "method": "test"
                },
                metadata={"length": 1000}
            )
        
        # Apply mocks
        monkeypatch.setattr(WebSearchTool, "run", mock_search_run)
        monkeypatch.setattr(WebScraperTool, "run", mock_scraper_run)
        
        # Execute research
        goal = "Find three specific pricing differences between Product A and Product B"
        result = boss_agent.execute_research(goal)
        
        # Verify result structure
        assert result is not None
        assert result.goal == goal
        assert isinstance(result.session_id, str)  # Must be string, not UUID
        assert len(result.agents_involved) > 0
        assert result.overall_confidence >= 0
        assert result.overall_confidence <= 100
        
        # Verify JSON serialization works
        json_str = result.to_json()
        assert isinstance(json_str, str)
        
        # Verify JSON can be parsed
        parsed = json.loads(json_str)
        assert parsed["goal"] == goal
        assert "session_id" in parsed
        assert isinstance(parsed["session_id"], str)
        
        # Verify to_dict works
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert isinstance(result_dict["session_id"], str)
        
        # Verify database operations worked
        session_history = boss_agent.memory_system.get_session_history(result.session_id)
        assert session_history is not None
        assert session_history.goal == goal
        assert len(session_history.decisions) > 0
        assert len(session_history.confidence_scores) > 0
        
        # Verify session can be serialized
        session_dict = session_history.to_dict()
        session_json = json.dumps(session_dict)
        assert isinstance(session_json, str)
    
    def test_workflow_state_serialization(self, boss_agent):
        """Test that workflow state can be serialized at any point"""
        # Get initial state
        state = boss_agent.get_workflow_state()
        
        # Verify state is JSON serializable
        state_json = json.dumps(state)
        assert isinstance(state_json, str)
        
        # Parse and verify
        parsed_state = json.loads(state_json)
        assert "session_id" in parsed_state
        assert "current_phase" in parsed_state
    
    def test_error_result_serialization(self, boss_agent):
        """Test that error results can be serialized"""
        # Create error result
        error_result = boss_agent._create_error_result(
            goal="Test goal",
            error_message="Test error"
        )
        
        # Verify JSON serialization
        json_str = error_result.to_json()
        assert isinstance(json_str, str)
        
        # Verify parsing
        parsed = json.loads(json_str)
        assert "session_id" in parsed
        assert isinstance(parsed["session_id"], str)
        assert "Test error" in str(parsed["insights"])
    
    def test_memory_system_uuid_handling(self, temp_db, temp_log_dir):
        """Test that memory system handles UUIDs correctly"""
        logger = StructuredLogger(session_id="test-uuid", log_dir=temp_log_dir)
        memory = MemorySystem(db_path=temp_db, logger=logger)
        
        # Create session
        session_id = memory.create_session("Test goal")
        
        # Verify session_id is UUID
        from uuid import UUID
        assert isinstance(session_id, UUID)
        
        # Verify string conversion works
        session_id_str = str(session_id)
        assert isinstance(session_id_str, str)
        
        # Verify we can retrieve with string
        session_info = memory.get_session_info(session_id_str)
        assert session_info is not None
        
        # Verify we can retrieve with UUID
        session_info2 = memory.get_session_info(session_id)
        assert session_info2 is not None
    
    def test_confidence_scores_serialization(self, boss_agent, temp_db, temp_log_dir):
        """Test that confidence scores are properly stored and serialized"""
        from evaluation.reflection import ConfidenceScore, AgentType
        
        # Create confidence score
        score = ConfidenceScore(
            overall=0.75,
            factors={"test_factor": 0.8},
            agent_type=AgentType.RESEARCH,
            reasoning="Test reasoning"
        )
        
        # Verify to_dict works
        score_dict = score.to_dict()
        assert isinstance(score_dict, dict)
        
        # Verify JSON serialization
        score_json = json.dumps(score_dict)
        assert isinstance(score_json, str)
        
        # Verify parsing
        parsed = json.loads(score_json)
        assert parsed["overall"] == 0.75


class TestWebSocketIntegration:
    """Test WebSocket server integration"""
    
    def test_result_broadcast_serialization(self):
        """Test that results can be broadcast via WebSocket"""
        from models.data_models import ResearchResult
        
        # Create result
        result = ResearchResult.create_new(
            goal="Test goal",
            agents_involved=["research_agent"],
            confidence_scores={"research_agent": {"overall": 75, "self": 75, "boss": 75}},
            competitors=[],
            insights=["Test insight"],
            recommendations=[],
            sources=[{"url": "https://example.com", "type": "web"}],
            overall_confidence=75
        )
        
        # Verify to_dict for WebSocket
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert isinstance(result_dict["session_id"], str)
        
        # Verify JSON serialization for WebSocket
        message = {
            "type": "result",
            "data": result_dict
        }
        message_json = json.dumps(message)
        assert isinstance(message_json, str)
        
        # Verify parsing
        parsed = json.loads(message_json)
        assert parsed["type"] == "result"
        assert isinstance(parsed["data"]["session_id"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
