"""
Unit tests for base agent interface
"""

import pytest
from agents.base_agent import BaseAgent, AgentContext
from models.data_models import AgentOutput
from evaluation.reflection import ConfidenceScore, AgentType


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing"""
    
    def __init__(self, agent_name: str = "test_agent", max_retries: int = 3):
        super().__init__(
            agent_name=agent_name,
            agent_type=AgentType.RESEARCH,
            max_retries=max_retries
        )
        self.execute_called = False
        self.calculate_confidence_called = False
    
    def execute(self, context: AgentContext) -> AgentOutput:
        """Test implementation of execute"""
        self.execute_called = True
        return AgentOutput(
            agent_name=self.agent_name,
            task_id=context.task_id,
            results={"test": "data"},
            self_confidence=75,
            reasoning="Test execution",
            sources=[],
            execution_time=1.0
        )
    
    def calculate_confidence(self, output: AgentOutput) -> ConfidenceScore:
        """Test implementation of calculate_confidence"""
        self.calculate_confidence_called = True
        return ConfidenceScore(
            overall=0.75,
            factors={"test_factor": 0.75},
            agent_type=self.agent_type,
            reasoning="Test confidence"
        )


class TestAgentContext:
    """Tests for AgentContext dataclass"""
    
    def test_agent_context_creation(self):
        """Test creating an agent context"""
        context = AgentContext(
            task_id="task_001",
            task_description="Test task"
        )
        
        assert context.task_id == "task_001"
        assert context.task_description == "Test task"
        assert context.previous_outputs == {}
        assert context.retry_count == 0
        assert context.session_id is None
        assert context.additional_context == {}
    
    def test_agent_context_with_all_fields(self):
        """Test creating context with all fields"""
        output = AgentOutput(
            agent_name="prev_agent",
            task_id="task_000",
            results={},
            self_confidence=80,
            reasoning="test",
            sources=[],
            execution_time=1.0
        )
        
        context = AgentContext(
            task_id="task_001",
            task_description="Test task",
            previous_outputs={"prev": output},
            retry_count=2,
            session_id="session_123",
            additional_context={"key": "value"}
        )
        
        assert context.task_id == "task_001"
        assert context.retry_count == 2
        assert context.session_id == "session_123"
        assert "prev" in context.previous_outputs
        assert context.additional_context["key"] == "value"
    
    def test_agent_context_to_dict(self):
        """Test serialization to dictionary"""
        output = AgentOutput(
            agent_name="prev_agent",
            task_id="task_000",
            results={},
            self_confidence=80,
            reasoning="test",
            sources=[],
            execution_time=1.0
        )
        
        context = AgentContext(
            task_id="task_001",
            task_description="Test task",
            previous_outputs={"prev": output},
            retry_count=1,
            session_id="session_123"
        )
        
        data = context.to_dict()
        
        assert data["task_id"] == "task_001"
        assert data["task_description"] == "Test task"
        assert data["retry_count"] == 1
        assert data["session_id"] == "session_123"
        assert "prev" in data["previous_outputs"]
        assert data["previous_outputs"]["prev"]["agent_name"] == "prev_agent"


class TestBaseAgent:
    """Tests for BaseAgent abstract class"""
    
    def test_agent_initialization(self):
        """Test initializing a concrete agent"""
        agent = ConcreteAgent(agent_name="test_agent", max_retries=5)
        
        assert agent.agent_name == "test_agent"
        assert agent.agent_type == AgentType.RESEARCH
        assert agent.max_retries == 5
        assert agent.get_retry_count() == 0
    
    def test_agent_initialization_empty_name(self):
        """Test that empty agent name raises error"""
        with pytest.raises(ValueError, match="agent_name cannot be empty"):
            ConcreteAgent(agent_name="")
    
    def test_agent_initialization_negative_retries(self):
        """Test that negative max_retries raises error"""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            ConcreteAgent(max_retries=-1)
    
    def test_execute_method_called(self):
        """Test that execute method is called"""
        agent = ConcreteAgent()
        context = AgentContext(
            task_id="task_001",
            task_description="Test task"
        )
        
        output = agent.execute(context)
        
        assert agent.execute_called is True
        assert isinstance(output, AgentOutput)
        assert output.agent_name == "test_agent"
        assert output.task_id == "task_001"
    
    def test_calculate_confidence_method_called(self):
        """Test that calculate_confidence method is called"""
        agent = ConcreteAgent()
        output = AgentOutput(
            agent_name="test_agent",
            task_id="task_001",
            results={},
            self_confidence=75,
            reasoning="test",
            sources=[],
            execution_time=1.0
        )
        
        score = agent.calculate_confidence(output)
        
        assert agent.calculate_confidence_called is True
        assert isinstance(score, ConfidenceScore)
        assert score.overall == 0.75
    
    def test_increment_retry_count(self):
        """Test incrementing retry count"""
        agent = ConcreteAgent()
        
        assert agent.get_retry_count() == 0
        
        count = agent.increment_retry_count()
        assert count == 1
        assert agent.get_retry_count() == 1
        
        count = agent.increment_retry_count()
        assert count == 2
        assert agent.get_retry_count() == 2
    
    def test_reset_retry_count(self):
        """Test resetting retry count"""
        agent = ConcreteAgent()
        
        agent.increment_retry_count()
        agent.increment_retry_count()
        assert agent.get_retry_count() == 2
        
        agent.reset_retry_count()
        assert agent.get_retry_count() == 0
    
    def test_has_retries_remaining(self):
        """Test checking if retries are remaining"""
        agent = ConcreteAgent(max_retries=3)
        
        assert agent.has_retries_remaining() is True
        
        agent.increment_retry_count()
        assert agent.has_retries_remaining() is True
        
        agent.increment_retry_count()
        assert agent.has_retries_remaining() is True
        
        agent.increment_retry_count()
        assert agent.has_retries_remaining() is False
    
    def test_can_retry(self):
        """Test can_retry method"""
        agent = ConcreteAgent(max_retries=2)
        
        assert agent.can_retry() is True
        
        agent.increment_retry_count()
        assert agent.can_retry() is True
        
        agent.increment_retry_count()
        assert agent.can_retry() is False
    
    def test_get_agent_info(self):
        """Test getting agent information"""
        agent = ConcreteAgent(agent_name="my_agent", max_retries=5)
        agent.increment_retry_count()
        agent.increment_retry_count()
        
        info = agent.get_agent_info()
        
        assert info["agent_name"] == "my_agent"
        assert info["agent_type"] == "research"
        assert info["max_retries"] == 5
        assert info["current_retry_count"] == 2
        assert info["retries_remaining"] == 3
    
    def test_agent_repr(self):
        """Test string representation of agent"""
        agent = ConcreteAgent(agent_name="test_agent", max_retries=3)
        agent.increment_retry_count()
        
        repr_str = repr(agent)
        
        assert "ConcreteAgent" in repr_str
        assert "test_agent" in repr_str
        assert "research" in repr_str
        assert "1/3" in repr_str
    
    def test_retry_count_tracking_across_executions(self):
        """Test that retry count persists across multiple executions"""
        agent = ConcreteAgent()
        context = AgentContext(
            task_id="task_001",
            task_description="Test task"
        )
        
        # First execution
        agent.execute(context)
        assert agent.get_retry_count() == 0
        
        # Simulate retry
        agent.increment_retry_count()
        agent.execute(context)
        assert agent.get_retry_count() == 1
        
        # Another retry
        agent.increment_retry_count()
        agent.execute(context)
        assert agent.get_retry_count() == 2
    
    def test_abstract_methods_must_be_implemented(self):
        """Test that abstract methods must be implemented"""
        # This test verifies that BaseAgent cannot be instantiated directly
        with pytest.raises(TypeError):
            BaseAgent(
                agent_name="test",
                agent_type=AgentType.RESEARCH,
                max_retries=3
            )
    
    def test_multiple_agents_independent_retry_counts(self):
        """Test that multiple agents have independent retry counts"""
        agent1 = ConcreteAgent(agent_name="agent1")
        agent2 = ConcreteAgent(agent_name="agent2")
        
        agent1.increment_retry_count()
        agent1.increment_retry_count()
        
        assert agent1.get_retry_count() == 2
        assert agent2.get_retry_count() == 0
    
    def test_agent_with_zero_max_retries(self):
        """Test agent with zero max retries"""
        agent = ConcreteAgent(max_retries=0)
        
        assert agent.max_retries == 0
        assert agent.can_retry() is False
        assert agent.has_retries_remaining() is False
    
    def test_context_with_multiple_previous_outputs(self):
        """Test context with multiple previous agent outputs"""
        output1 = AgentOutput(
            agent_name="agent1",
            task_id="task_001",
            results={"data": "1"},
            self_confidence=80,
            reasoning="test1",
            sources=[],
            execution_time=1.0
        )
        
        output2 = AgentOutput(
            agent_name="agent2",
            task_id="task_002",
            results={"data": "2"},
            self_confidence=85,
            reasoning="test2",
            sources=[],
            execution_time=2.0
        )
        
        context = AgentContext(
            task_id="task_003",
            task_description="Test task",
            previous_outputs={
                "agent1": output1,
                "agent2": output2
            }
        )
        
        assert len(context.previous_outputs) == 2
        assert "agent1" in context.previous_outputs
        assert "agent2" in context.previous_outputs
        assert context.previous_outputs["agent1"].self_confidence == 80
        assert context.previous_outputs["agent2"].self_confidence == 85
