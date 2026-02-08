"""
Unit tests for Boss Agent
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import uuid

from boss_agent import BossAgent, WorkflowPhase
from models.data_models import AgentOutput, ResearchResult
from evaluation.reflection import ConfidenceScore, AgentType


class TestBossAgent:
    """Tests for BossAgent"""
    
    def test_initialization(self):
        """Test initializing boss agent"""
        mock_memory = Mock()
        mock_logger = Mock()
        
        boss = BossAgent(
            memory_system=mock_memory,
            logger=mock_logger,
            max_retries=5,
            confidence_threshold=0.60
        )
        
        assert boss.memory_system == mock_memory
        assert boss.logger == mock_logger
        assert boss.max_retries == 5
        assert boss.confidence_threshold == 0.60
        assert boss.current_phase is None
        assert boss.active_agent is None
    
    def test_initialization_invalid_retries(self):
        """Test that invalid max_retries raises error"""
        mock_memory = Mock()
        mock_logger = Mock()
        
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            BossAgent(mock_memory, mock_logger, max_retries=-1)
    
    def test_initialization_invalid_threshold(self):
        """Test that invalid confidence_threshold raises error"""
        mock_memory = Mock()
        mock_logger = Mock()
        
        with pytest.raises(ValueError, match="confidence_threshold must be between"):
            BossAgent(mock_memory, mock_logger, confidence_threshold=1.5)
    
    @patch('boss_agent.ResearchAgent')
    @patch('boss_agent.AnalystAgent')
    @patch('boss_agent.StrategyAgent')
    def test_execute_research_success(self, mock_strategy_class, mock_analyst_class, mock_research_class):
        """Test successful research execution"""
        # Setup mocks
        mock_memory = Mock()
        mock_memory.create_session.return_value = "session_123"
        mock_logger = Mock()
        
        # Mock agent outputs
        research_output = AgentOutput(
            agent_name="research_agent",
            task_id="task_001",
            results={"summary": "Research findings", "total_sources": 3},
            self_confidence=75,
            reasoning="Research completed",
            sources=["https://example.com"],
            execution_time=2.0
        )
        
        analyst_output = AgentOutput(
            agent_name="analyst_agent",
            task_id="task_002",
            results={"insights": [{"type": "test", "insight": "Test"}], "patterns": []},
            self_confidence=80,
            reasoning="Analysis completed",
            sources=[],
            execution_time=1.5
        )
        
        strategy_output = AgentOutput(
            agent_name="strategy_agent",
            task_id="task_003",
            results={"recommendations": [{"title": "Test"}], "action_plan": []},
            self_confidence=85,
            reasoning="Strategy completed",
            sources=[],
            execution_time=1.0
        )
        
        # Mock agents
        mock_research = Mock()
        mock_research.agent_name = "research_agent"
        mock_research.execute.return_value = research_output
        mock_research.calculate_confidence.return_value = ConfidenceScore(
            overall=0.75,
            factors={"test": 0.75},
            agent_type=AgentType.RESEARCH,
            reasoning="Test"
        )
        mock_research.reset_retry_count = Mock()
        mock_research_class.return_value = mock_research
        
        mock_analyst = Mock()
        mock_analyst.agent_name = "analyst_agent"
        mock_analyst.execute.return_value = analyst_output
        mock_analyst.calculate_confidence.return_value = ConfidenceScore(
            overall=0.80,
            factors={"test": 0.80},
            agent_type=AgentType.ANALYST,
            reasoning="Test"
        )
        mock_analyst.reset_retry_count = Mock()
        mock_analyst_class.return_value = mock_analyst
        
        mock_strategy = Mock()
        mock_strategy.agent_name = "strategy_agent"
        mock_strategy.execute.return_value = strategy_output
        mock_strategy.calculate_confidence.return_value = ConfidenceScore(
            overall=0.85,
            factors={"test": 0.85},
            agent_type=AgentType.STRATEGY,
            reasoning="Test"
        )
        mock_strategy.reset_retry_count = Mock()
        mock_strategy_class.return_value = mock_strategy
        
        # Create boss agent
        boss = BossAgent(mock_memory, mock_logger)
        
        # Execute research
        result = boss.execute_research("test research goal")
        
        # Verify result
        assert isinstance(result, ResearchResult)
        assert result.session_id == "session_123"
        assert result.goal == "test research goal"
        assert len(result.agents_involved) == 3
        assert "research_agent" in result.agents_involved
        assert "analyst_agent" in result.agents_involved
        assert "strategy_agent" in result.agents_involved
        
        # Verify memory calls
        assert mock_memory.create_session.called
        assert mock_memory.store_decision.called
        assert mock_memory.store_confidence_scores.called
        assert mock_memory.store_final_result.called
        assert mock_memory.update_session_status.called
    
    def test_get_workflow_state(self):
        """Test getting workflow state"""
        mock_memory = Mock()
        mock_logger = Mock()
        
        boss = BossAgent(mock_memory, mock_logger)
        boss.session_id = "session_123"
        boss.current_phase = WorkflowPhase.RESEARCH
        boss.active_agent = "research_agent"
        
        state = boss.get_workflow_state()
        
        assert state["session_id"] == "session_123"
        assert state["current_phase"] == "research"
        assert state["active_agent"] == "research_agent"
        assert "completed_agents" in state
        assert "confidence_scores" in state
    
    def test_reset(self):
        """Test resetting workflow state"""
        mock_memory = Mock()
        mock_logger = Mock()
        
        boss = BossAgent(mock_memory, mock_logger)
        boss.session_id = "session_123"
        boss.current_phase = WorkflowPhase.RESEARCH
        boss.active_agent = "research_agent"
        boss.agent_outputs = {"test": Mock()}
        
        boss.reset()
        
        assert boss.session_id is None
        assert boss.current_phase is None
        assert boss.active_agent is None
        assert len(boss.agent_outputs) == 0
        assert len(boss.confidence_scores) == 0
    
    @patch('boss_agent.ResearchAgent')
    def test_execute_phase_success(self, mock_research_class):
        """Test successful phase execution"""
        mock_memory = Mock()
        mock_memory.create_session.return_value = "session_123"
        mock_logger = Mock()
        
        # Mock agent
        research_output = AgentOutput(
            agent_name="research_agent",
            task_id="task_001",
            results={"summary": "Test"},
            self_confidence=75,
            reasoning="Test",
            sources=[],
            execution_time=1.0
        )
        
        mock_research = Mock()
        mock_research.agent_name = "research_agent"
        mock_research.execute.return_value = research_output
        mock_research.calculate_confidence.return_value = ConfidenceScore(
            overall=0.75,
            factors={},
            agent_type=AgentType.RESEARCH,
            reasoning="Test"
        )
        mock_research.increment_retry_count = Mock()
        mock_research_class.return_value = mock_research
        
        boss = BossAgent(mock_memory, mock_logger)
        boss.session_id = "session_123"
        
        output = boss._execute_phase(
            agent=mock_research,
            task_description="Test task",
            previous_outputs={}
        )
        
        assert output is not None
        assert output.agent_name == "research_agent"
        assert "research_agent" in boss.agent_outputs
        assert "research_agent" in boss.confidence_scores
    
    @patch('boss_agent.ResearchAgent')
    def test_execute_phase_low_confidence_retry(self, mock_research_class):
        """Test phase execution with low confidence triggering retry"""
        mock_memory = Mock()
        mock_memory.create_session.return_value = "session_123"
        mock_logger = Mock()
        
        # Mock agent with low confidence first, then high
        outputs = [
            AgentOutput(
                agent_name="research_agent",
                task_id="task_001",
                results={"summary": "Low quality"},
                self_confidence=40,
                reasoning="Low confidence",
                sources=[],
                execution_time=1.0
            ),
            AgentOutput(
                agent_name="research_agent",
                task_id="task_001",
                results={"summary": "High quality"},
                self_confidence=80,
                reasoning="High confidence",
                sources=[],
                execution_time=1.0
            )
        ]
        
        confidence_scores = [
            ConfidenceScore(overall=0.40, factors={}, agent_type=AgentType.RESEARCH, reasoning="Low"),
            ConfidenceScore(overall=0.80, factors={}, agent_type=AgentType.RESEARCH, reasoning="High")
        ]
        
        mock_research = Mock()
        mock_research.agent_name = "research_agent"
        mock_research.execute.side_effect = outputs
        mock_research.calculate_confidence.side_effect = confidence_scores
        mock_research.increment_retry_count = Mock()
        mock_research_class.return_value = mock_research
        
        boss = BossAgent(mock_memory, mock_logger, confidence_threshold=0.50)
        boss.session_id = "session_123"
        
        output = boss._execute_phase(
            agent=mock_research,
            task_description="Test task",
            previous_outputs={}
        )
        
        # Should succeed on second attempt
        assert output is not None
        assert output.self_confidence == 80
        assert mock_research.increment_retry_count.called
    
    @patch('boss_agent.ResearchAgent')
    def test_execute_phase_max_retries_exceeded(self, mock_research_class):
        """Test phase execution failing after max retries"""
        mock_memory = Mock()
        mock_memory.create_session.return_value = "session_123"
        mock_logger = Mock()
        
        # Mock agent always returning unacceptably low confidence (below min_acceptable)
        low_output = AgentOutput(
            agent_name="research_agent",
            task_id="task_001",
            results={"summary": "Very low quality"},
            self_confidence=20,
            reasoning="Very low confidence",
            sources=[],
            execution_time=1.0
        )
        
        very_low_confidence = ConfidenceScore(
            overall=0.20,  # Below min_acceptable (0.40)
            factors={},
            agent_type=AgentType.RESEARCH,
            reasoning="Very low"
        )
        
        mock_research = Mock()
        mock_research.agent_name = "research_agent"
        mock_research.execute.return_value = low_output
        mock_research.calculate_confidence.return_value = very_low_confidence
        mock_research.increment_retry_count = Mock()
        mock_research_class.return_value = mock_research
        
        boss = BossAgent(mock_memory, mock_logger, max_retries=2, confidence_threshold=0.50)
        boss.session_id = "session_123"
        
        output = boss._execute_phase(
            agent=mock_research,
            task_description="Test task",
            previous_outputs={}
        )
        
        # Should return None immediately due to error_recovery (below min_acceptable)
        assert output is None
        # Should only execute once since it triggers error_recovery
        assert mock_research.execute.call_count == 1
    
    def test_aggregate_results(self):
        """Test result aggregation"""
        mock_memory = Mock()
        mock_logger = Mock()
        
        boss = BossAgent(mock_memory, mock_logger)
        boss.session_id = "session_123"
        
        # Add mock outputs
        boss.agent_outputs = {
            "research_agent": AgentOutput(
                agent_name="research_agent",
                task_id="task_001",
                results={"summary": "Research findings"},
                self_confidence=75,
                reasoning="Test",
                sources=["https://example.edu/test"],
                execution_time=1.0
            ),
            "analyst_agent": AgentOutput(
                agent_name="analyst_agent",
                task_id="task_002",
                results={"insights": [{"type": "test"}], "patterns": []},
                self_confidence=80,
                reasoning="Test",
                sources=[],
                execution_time=1.0
            ),
            "strategy_agent": AgentOutput(
                agent_name="strategy_agent",
                task_id="task_003",
                results={"recommendations": [{"title": "Test"}], "action_plan": []},
                self_confidence=85,
                reasoning="Test",
                sources=[],
                execution_time=1.0
            )
        }
        
        boss.confidence_scores = {
            "research_agent": ConfidenceScore(0.75, {}, AgentType.RESEARCH, "Test"),
            "analyst_agent": ConfidenceScore(0.80, {}, AgentType.ANALYST, "Test"),
            "strategy_agent": ConfidenceScore(0.85, {}, AgentType.STRATEGY, "Test")
        }
        
        result = boss._aggregate_results("test goal", start_time=0.0)
        
        assert isinstance(result, ResearchResult)
        assert result.goal == "test goal"
        assert len(result.agents_involved) == 3
        assert len(result.insights) > 0
        assert len(result.sources) == 1
        assert result.sources[0]["reliability"] == "high"  # .edu domain
    
    def test_create_error_result(self):
        """Test error result creation"""
        mock_memory = Mock()
        mock_logger = Mock()
        
        boss = BossAgent(mock_memory, mock_logger)
        boss.session_id = "session_123"
        
        result = boss._create_error_result("test goal", "Test error message")
        
        assert isinstance(result, ResearchResult)
        assert result.goal == "test goal"
        assert result.session_id == "session_123"
        assert "Error" in result.insights[0]
    
    @patch('boss_agent.ResearchAgent')
    def test_execute_research_with_exception(self, mock_research_class):
        """Test research execution with exception in agent"""
        mock_memory = Mock()
        mock_memory.create_session.return_value = "session_123"
        mock_logger = Mock()
        
        # Mock agent that raises exception
        mock_research = Mock()
        mock_research.agent_name = "research_agent"
        mock_research.execute.side_effect = Exception("Test error")
        mock_research.increment_retry_count = Mock()
        mock_research.reset_retry_count = Mock()
        mock_research_class.return_value = mock_research
        
        boss = BossAgent(mock_memory, mock_logger, max_retries=1)
        
        result = boss.execute_research("test goal")
        
        # Should return error result
        assert isinstance(result, ResearchResult)
        assert "Error" in result.insights[0] or "failed" in result.insights[0].lower()
        assert mock_logger.log_error.called
