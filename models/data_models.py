"""
Core data models and type definitions for the autonomous research agent system.

This module defines all data structures used throughout the system with proper
type hints, validation methods, and serialization support.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4
import json
from enum import Enum


class AgentType(Enum):
    """Types of specialized agents in the system."""
    RESEARCH = "research"
    ANALYST = "analyst"
    STRATEGY = "strategy"
    BOSS = "boss"


class DecisionType(Enum):
    """Types of decisions the Boss Agent can make."""
    PROCEED = "proceed"
    REPLAN = "replan"
    ESCALATE = "escalate"


@dataclass
class Task:
    """
    Represents a task to be executed by an agent.
    
    Attributes:
        task_id: Unique identifier for the task
        description: Human-readable description of what needs to be done
        agent_type: Type of agent that should execute this task
        context: Additional context and parameters for task execution
        priority: Priority level (higher = more important)
    """
    task_id: str
    description: str
    agent_type: str
    context: Dict[str, Any]
    priority: int = 1
    
    def validate(self) -> bool:
        """
        Validate task data.
        
        Returns:
            True if task is valid, False otherwise
        """
        if not self.task_id or not self.description:
            return False
        if self.agent_type not in [e.value for e in AgentType]:
            return False
        if self.priority < 1:
            return False
        return True


@dataclass
class AgentOutput:
    """
    Output from a specialized agent after task execution.
    
    Attributes:
        agent_name: Name of the agent that produced this output
        task_id: ID of the task that was executed
        results: Dictionary containing the execution results
        self_confidence: Agent's self-assessed confidence score (0-100)
        reasoning: Explanation of how the agent arrived at these results
        sources: List of sources used (URLs, documents, etc.)
        execution_time: Time taken to execute the task in seconds
    """
    agent_name: str
    task_id: str
    results: Dict[str, Any]
    self_confidence: int
    reasoning: str
    sources: List[str]
    execution_time: float
    
    def validate(self) -> bool:
        """
        Validate agent output data.
        
        Returns:
            True if output is valid, False otherwise
        """
        if not self.agent_name or not self.task_id:
            return False
        if not 0 <= self.self_confidence <= 100:
            return False
        if self.execution_time < 0:
            return False
        return True


@dataclass
class EvaluationResult:
    """
    Boss Agent's evaluation of a specialized agent's output.
    
    Attributes:
        boss_confidence: Boss Agent's confidence score (0-100)
        decision: Decision on what to do next (proceed, replan, escalate)
        reasoning: Explanation of the evaluation and decision
        suggestions: List of suggestions for improvement if replanning
    """
    boss_confidence: int
    decision: str
    reasoning: str
    suggestions: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """
        Validate evaluation result data.
        
        Returns:
            True if evaluation is valid, False otherwise
        """
        if not 0 <= self.boss_confidence <= 100:
            return False
        if self.decision not in [e.value for e in DecisionType]:
            return False
        if not self.reasoning:
            return False
        return True


@dataclass
class SearchResult:
    """
    Result from a web search operation.
    
    Attributes:
        title: Title of the search result
        url: URL of the result
        snippet: Brief excerpt or description
        source: Search engine that provided this result
        timestamp: When this result was obtained
    """
    title: str
    url: str
    snippet: str
    source: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ModelResponse:
    """
    Response from an LLM model call.
    
    Attributes:
        model: Model identifier that was used
        text: Generated text response
        tokens_used: Number of tokens consumed
        latency: Response time in seconds
        success: Whether the call was successful
        error: Error message if call failed
    """
    model: str
    text: str
    tokens_used: int
    latency: float
    success: bool
    error: Optional[str] = None
    
    def validate(self) -> bool:
        """
        Validate model response data.
        
        Returns:
            True if response is valid, False otherwise
        """
        if not self.model:
            return False
        if self.success and not self.text:
            return False
        if not self.success and not self.error:
            return False
        if self.tokens_used < 0 or self.latency < 0:
            return False
        return True


@dataclass
class ToolResult:
    """
    Result from a tool execution.
    
    Attributes:
        success: Whether the tool execution succeeded
        data: Data returned by the tool (None if failed)
        error: Error message if execution failed
        metadata: Additional metadata about the execution
    """
    success: bool
    data: Optional[Any]
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """
        Validate tool result data.
        
        Returns:
            True if result is valid, False otherwise
        """
        if self.success and self.data is None:
            return False
        if not self.success and not self.error:
            return False
        return True


@dataclass
class ResearchResult:
    """
    Final output from a complete research session.
    
    This is the structured output that gets returned to users and persisted
    to the database. It follows a strict JSON schema for validation.
    
    Attributes:
        session_id: Unique session identifier (UUID)
        goal: Original research goal provided by user
        timestamp: ISO 8601 timestamp of completion
        agents_involved: List of agent names that participated
        confidence_scores: Dict mapping agent names to their confidence scores
        competitors: List of identified competitors with details
        insights: List of key insights discovered
        recommendations: List of strategic recommendations
        sources: List of sources used with URLs and metadata
        overall_confidence: Overall confidence score for the research
    """
    session_id: str
    goal: str
    timestamp: str
    agents_involved: List[str]
    confidence_scores: Dict[str, Dict[str, int]]
    competitors: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[Dict[str, Any]]
    sources: List[Dict[str, str]]
    overall_confidence: int
    
    @classmethod
    def create_new(
        cls,
        goal: str,
        agents_involved: List[str],
        confidence_scores: Dict[str, Dict[str, int]],
        competitors: List[Dict[str, Any]],
        insights: List[str],
        recommendations: List[Dict[str, Any]],
        sources: List[Dict[str, str]],
        overall_confidence: int
    ) -> "ResearchResult":
        """
        Create a new ResearchResult with auto-generated session_id and timestamp.
        
        Args:
            goal: Research goal
            agents_involved: List of agent names
            confidence_scores: Confidence scores per agent
            competitors: List of competitors
            insights: List of insights
            recommendations: List of recommendations
            sources: List of sources
            overall_confidence: Overall confidence score
            
        Returns:
            New ResearchResult instance
        """
        return cls(
            session_id=str(uuid4()),
            goal=goal,
            timestamp=datetime.utcnow().isoformat() + "Z",
            agents_involved=agents_involved,
            confidence_scores=confidence_scores,
            competitors=competitors,
            insights=insights,
            recommendations=recommendations,
            sources=sources,
            overall_confidence=overall_confidence
        )
    
    def to_json(self) -> str:
        """
        Serialize to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation with UUID converted to string
        """
        data = asdict(self)
        # Convert UUID to string for JSON serialization
        data['session_id'] = str(data['session_id'])
        return data
    
    def validate(self) -> bool:
        """
        Validate research result data against requirements.
        
        Returns:
            True if result is valid, False otherwise
        """
        # Validate session_id is UUID format
        try:
            UUID(self.session_id)
        except (ValueError, AttributeError):
            return False
        
        # Validate required fields are present and non-empty
        if not self.goal or not self.timestamp:
            return False
        
        if not self.agents_involved or len(self.agents_involved) == 0:
            return False
        
        # Validate timestamp is ISO 8601 format
        try:
            datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return False
        
        # Validate confidence scores
        for agent, scores in self.confidence_scores.items():
            if 'self' not in scores or 'boss' not in scores:
                return False
            if not 0 <= scores['self'] <= 100:
                return False
            if not 0 <= scores['boss'] <= 100:
                return False
        
        # Validate overall confidence
        if not 0 <= self.overall_confidence <= 100:
            return False
        
        # Validate sources have URLs
        for source in self.sources:
            if 'url' not in source:
                return False
        
        return True
    
    def validate_schema(self) -> bool:
        """
        Validate against JSON schema.
        
        This is a simplified validation. For production, use jsonschema library.
        
        Returns:
            True if schema is valid, False otherwise
        """
        required_fields = [
            'session_id', 'goal', 'timestamp', 'agents_involved',
            'confidence_scores', 'competitors', 'insights',
            'recommendations', 'sources', 'overall_confidence'
        ]
        
        result_dict = self.to_dict()
        
        # Check all required fields exist
        for field in required_fields:
            if field not in result_dict:
                return False
        
        # Validate types
        if not isinstance(result_dict['agents_involved'], list):
            return False
        if not isinstance(result_dict['confidence_scores'], dict):
            return False
        if not isinstance(result_dict['competitors'], list):
            return False
        if not isinstance(result_dict['insights'], list):
            return False
        if not isinstance(result_dict['recommendations'], list):
            return False
        if not isinstance(result_dict['sources'], list):
            return False
        
        return self.validate()
