"""
Base Agent Interface

This module defines the abstract base class for all specialized agents.
All agents must implement the execute method and provide confidence calculation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from models.data_models import AgentOutput
from evaluation.reflection import ConfidenceScore, AgentType


@dataclass
class AgentContext:
    """
    Context information passed to agents during execution
    
    Attributes:
        task_id: Unique identifier for the task
        task_description: Description of the task to execute
        previous_outputs: Outputs from previous agents in the workflow
        retry_count: Number of times this task has been retried
        session_id: ID of the current session
        additional_context: Any additional context data
    """
    task_id: str
    task_description: str
    previous_outputs: Dict[str, AgentOutput] = field(default_factory=dict)
    retry_count: int = 0
    session_id: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "previous_outputs": {
                k: {
                    "agent_name": v.agent_name,
                    "task_id": v.task_id,
                    "self_confidence": v.self_confidence
                }
                for k, v in self.previous_outputs.items()
            },
            "retry_count": self.retry_count,
            "session_id": self.session_id,
            "additional_context": self.additional_context
        }


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents
    
    All agents must:
    - Implement the execute method to perform their specialized task
    - Implement the calculate_confidence method for self-assessment
    - Track retry counts for error recovery
    
    Attributes:
        agent_name: Name of the agent
        agent_type: Type of agent (research, analyst, strategy)
        max_retries: Maximum number of retries allowed
    """
    
    def __init__(
        self,
        agent_name: str,
        agent_type: AgentType,
        max_retries: int = 3
    ):
        """
        Initialize base agent
        
        Args:
            agent_name: Name of the agent
            agent_type: Type of agent
            max_retries: Maximum number of retries allowed
        """
        if not agent_name:
            raise ValueError("agent_name cannot be empty")
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.max_retries = max_retries
        self._retry_count = 0
    
    @abstractmethod
    def execute(self, context: AgentContext) -> AgentOutput:
        """
        Execute the agent's specialized task
        
        This method must be implemented by all subclasses to perform
        their specific functionality (research, analysis, strategy).
        
        Args:
            context: Context information for task execution
        
        Returns:
            AgentOutput with results and metadata
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    @abstractmethod
    def calculate_confidence(self, output: AgentOutput) -> ConfidenceScore:
        """
        Calculate confidence score for the agent's output
        
        This method must be implemented by all subclasses to provide
        agent-specific confidence assessment.
        
        Args:
            output: The output to assess
        
        Returns:
            ConfidenceScore with overall score and factor breakdown
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    def increment_retry_count(self) -> int:
        """
        Increment the retry count
        
        Returns:
            Current retry count after increment
        """
        self._retry_count += 1
        return self._retry_count
    
    def reset_retry_count(self) -> None:
        """Reset the retry count to zero"""
        self._retry_count = 0
    
    def get_retry_count(self) -> int:
        """
        Get the current retry count
        
        Returns:
            Current retry count
        """
        return self._retry_count
    
    def has_retries_remaining(self) -> bool:
        """
        Check if retries are still available
        
        Returns:
            True if retry count is below max_retries
        """
        return self._retry_count < self.max_retries
    
    def can_retry(self) -> bool:
        """
        Check if the agent can retry the current task
        
        Returns:
            True if retries are available, False otherwise
        """
        return self.has_retries_remaining()
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent
        
        Returns:
            Dictionary with agent metadata
        """
        return {
            "agent_name": self.agent_name,
            "agent_type": self.agent_type.value,
            "max_retries": self.max_retries,
            "current_retry_count": self._retry_count,
            "retries_remaining": self.max_retries - self._retry_count
        }
    
    def __repr__(self) -> str:
        """String representation of the agent"""
        return (
            f"{self.__class__.__name__}("
            f"name={self.agent_name}, "
            f"type={self.agent_type.value}, "
            f"retries={self._retry_count}/{self.max_retries})"
        )
