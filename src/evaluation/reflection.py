"""
Reflection and Evaluation Module

This module implements self-reflection and confidence scoring for agent outputs,
as well as Boss Agent evaluation logic for determining whether to proceed or replan.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

from models.data_models import AgentOutput


class AgentType(Enum):
    """Types of specialized agents"""
    RESEARCH = "research"
    ANALYST = "analyst"
    STRATEGY = "strategy"


@dataclass
class ConfidenceScore:
    """
    Confidence score with breakdown by factor
    
    Attributes:
        overall: Overall confidence score (0.0-1.0)
        factors: Dictionary of individual confidence factors
        agent_type: Type of agent that generated this score
        reasoning: Explanation of the confidence assessment
    """
    overall: float
    factors: Dict[str, float]
    agent_type: AgentType
    reasoning: str
    
    def __post_init__(self):
        """Validate confidence score bounds"""
        if not 0.0 <= self.overall <= 1.0:
            raise ValueError(f"Overall confidence must be between 0.0 and 1.0, got {self.overall}")
        
        for factor_name, score in self.factors.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Factor '{factor_name}' must be between 0.0 and 1.0, got {score}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "overall": self.overall,
            "factors": self.factors,
            "agent_type": self.agent_type.value,
            "reasoning": self.reasoning
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceScore":
        """Create from dictionary"""
        return cls(
            overall=data["overall"],
            factors=data["factors"],
            agent_type=AgentType(data["agent_type"]),
            reasoning=data["reasoning"]
        )


class ReflectionModule:
    """
    Reflection module for calculating confidence scores and evaluating outputs
    
    This module implements:
    - Agent-specific confidence calculation based on output characteristics
    - Boss Agent evaluation logic for quality gates
    - Replanning decision logic based on confidence thresholds
    """
    
    def __init__(
        self,
        high_confidence_threshold: float = 0.75,
        low_confidence_threshold: float = 0.50,
        min_acceptable_confidence: float = 0.40
    ):
        """
        Initialize reflection module
        
        Args:
            high_confidence_threshold: Threshold for high confidence (proceed)
            low_confidence_threshold: Threshold below which replanning is triggered
            min_acceptable_confidence: Minimum acceptable confidence to avoid error recovery
        """
        if not 0.0 <= high_confidence_threshold <= 1.0:
            raise ValueError("high_confidence_threshold must be between 0.0 and 1.0")
        if not 0.0 <= low_confidence_threshold <= 1.0:
            raise ValueError("low_confidence_threshold must be between 0.0 and 1.0")
        if not 0.0 <= min_acceptable_confidence <= 1.0:
            raise ValueError("min_acceptable_confidence must be between 0.0 and 1.0")
        if low_confidence_threshold >= high_confidence_threshold:
            raise ValueError("low_confidence_threshold must be less than high_confidence_threshold")
        
        self.high_confidence_threshold = high_confidence_threshold
        self.low_confidence_threshold = low_confidence_threshold
        self.min_acceptable_confidence = min_acceptable_confidence
    
    def calculate_self_confidence(
        self,
        agent_output: AgentOutput,
        agent_type: AgentType,
        task_description: str = ""
    ) -> ConfidenceScore:
        """
        Calculate self-confidence score for an agent's output
        
        Different agents use different factors for confidence calculation:
        - Research: source_count, source_reliability, completeness, relevance
        - Analyst: insight_depth, consistency, pattern_clarity, evidence_strength
        - Strategy: specificity, actionability, alignment, feasibility
        
        Args:
            agent_output: The output from the agent
            agent_type: Type of agent that generated the output
            task_description: Optional task description for relevance checking
        
        Returns:
            ConfidenceScore with overall score and factor breakdown
        """
        if agent_type == AgentType.RESEARCH:
            return self._calculate_research_confidence(agent_output, task_description)
        elif agent_type == AgentType.ANALYST:
            return self._calculate_analyst_confidence(agent_output, task_description)
        elif agent_type == AgentType.STRATEGY:
            return self._calculate_strategy_confidence(agent_output, task_description)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    def _calculate_research_confidence(self, output: AgentOutput, task_description: str = "") -> ConfidenceScore:
        """Calculate confidence for research agent output"""
        factors = {}
        
        # Source count: more sources = higher confidence
        source_count = len(output.sources)
        factors["source_count"] = min(source_count / 5.0, 1.0)  # Cap at 5 sources
        
        # Source reliability: based on domain quality indicators
        if output.sources:
            reliable_domains = sum(
                1 for s in output.sources
                if any(domain in s for domain in [".edu", ".gov", ".org"])
            )
            factors["source_reliability"] = reliable_domains / len(output.sources)
        else:
            factors["source_reliability"] = 0.0
        
        # Completeness: based on results content
        results_str = str(output.results)
        content_length = len(results_str)
        factors["completeness"] = min(content_length / 1000.0, 1.0)  # Cap at 1000 chars
        
        # Relevance: based on keyword matching (simplified)
        if task_description:
            task_keywords = task_description.lower().split()
            results_lower = results_str.lower()
            keyword_matches = sum(1 for kw in task_keywords if kw in results_lower)
            factors["relevance"] = min(keyword_matches / len(task_keywords), 1.0) if task_keywords else 0.5
        else:
            factors["relevance"] = 0.5  # Default if no task description
        
        # Calculate overall as weighted average
        weights = {
            "source_count": 0.25,
            "source_reliability": 0.30,
            "completeness": 0.20,
            "relevance": 0.25
        }
        overall = sum(factors[k] * weights[k] for k in factors)
        
        reasoning = self._generate_reasoning(factors, "research")
        
        return ConfidenceScore(
            overall=overall,
            factors=factors,
            agent_type=AgentType.RESEARCH,
            reasoning=reasoning
        )
    
    def _calculate_analyst_confidence(self, output: AgentOutput, task_description: str = "") -> ConfidenceScore:
        """Calculate confidence for analyst agent output"""
        factors = {}
        
        # Get content from results
        results_str = str(output.results)
        reasoning_str = output.reasoning
        content_lower = (results_str + " " + reasoning_str).lower()
        
        # Insight depth: based on analysis complexity
        analysis_indicators = ["because", "therefore", "indicates", "suggests", "correlation", "pattern"]
        insight_count = sum(1 for indicator in analysis_indicators if indicator in content_lower)
        factors["insight_depth"] = min(insight_count / 3.0, 1.0)  # Cap at 3 insights
        
        # Consistency: check for contradictions (simplified)
        contradiction_indicators = ["however", "but", "although", "contradicts"]
        contradiction_count = sum(1 for indicator in contradiction_indicators if indicator in content_lower)
        factors["consistency"] = max(0.0, 1.0 - (contradiction_count * 0.2))
        
        # Pattern clarity: based on structured output
        has_structure = any(marker in results_str for marker in ["1.", "2.", "-", "*", "•"])
        factors["pattern_clarity"] = 0.8 if has_structure else 0.4
        
        # Evidence strength: based on data references
        evidence_indicators = ["data", "shows", "demonstrates", "evidence", "results"]
        evidence_count = sum(1 for indicator in evidence_indicators if indicator in content_lower)
        factors["evidence_strength"] = min(evidence_count / 3.0, 1.0)
        
        # Calculate overall as weighted average
        weights = {
            "insight_depth": 0.30,
            "consistency": 0.25,
            "pattern_clarity": 0.20,
            "evidence_strength": 0.25
        }
        overall = sum(factors[k] * weights[k] for k in factors)
        
        reasoning = self._generate_reasoning(factors, "analyst")
        
        return ConfidenceScore(
            overall=overall,
            factors=factors,
            agent_type=AgentType.ANALYST,
            reasoning=reasoning
        )
    
    def _calculate_strategy_confidence(self, output: AgentOutput, task_description: str = "") -> ConfidenceScore:
        """Calculate confidence for strategy agent output"""
        factors = {}
        
        # Get content from results
        results_str = str(output.results)
        reasoning_str = output.reasoning
        content_lower = (results_str + " " + reasoning_str).lower()
        
        # Specificity: based on concrete details
        specific_indicators = ["step", "action", "implement", "execute", "timeline", "deadline"]
        specific_count = sum(1 for indicator in specific_indicators if indicator in content_lower)
        factors["specificity"] = min(specific_count / 4.0, 1.0)
        
        # Actionability: based on action verbs
        action_verbs = ["create", "develop", "build", "design", "test", "deploy", "monitor"]
        action_count = sum(1 for verb in action_verbs if verb in content_lower)
        factors["actionability"] = min(action_count / 3.0, 1.0)
        
        # Alignment: based on goal reference
        if task_description:
            task_keywords = task_description.lower().split()
            keyword_matches = sum(1 for kw in task_keywords if kw in content_lower)
            factors["alignment"] = min(keyword_matches / len(task_keywords), 1.0) if task_keywords else 0.5
        else:
            factors["alignment"] = 0.5  # Default if no task description
        
        # Feasibility: based on realistic constraints
        feasibility_indicators = ["realistic", "achievable", "practical", "feasible"]
        has_feasibility = any(indicator in content_lower for indicator in feasibility_indicators)
        factors["feasibility"] = 0.8 if has_feasibility else 0.5
        
        # Calculate overall as weighted average
        weights = {
            "specificity": 0.30,
            "actionability": 0.30,
            "alignment": 0.20,
            "feasibility": 0.20
        }
        overall = sum(factors[k] * weights[k] for k in factors)
        
        reasoning = self._generate_reasoning(factors, "strategy")
        
        return ConfidenceScore(
            overall=overall,
            factors=factors,
            agent_type=AgentType.STRATEGY,
            reasoning=reasoning
        )
    
    def _generate_reasoning(self, factors: Dict[str, float], agent_type: str) -> str:
        """Generate human-readable reasoning for confidence score"""
        high_factors = [k for k, v in factors.items() if v >= 0.7]
        low_factors = [k for k, v in factors.items() if v < 0.5]
        
        reasoning_parts = []
        
        if high_factors:
            reasoning_parts.append(f"Strong {', '.join(high_factors)}")
        
        if low_factors:
            reasoning_parts.append(f"Weak {', '.join(low_factors)}")
        
        if not reasoning_parts:
            reasoning_parts.append("Moderate performance across all factors")
        
        return f"{agent_type.capitalize()} agent: {'; '.join(reasoning_parts)}"
    
    def evaluate_output(
        self,
        agent_output: AgentOutput,
        confidence_score: ConfidenceScore
    ) -> Dict[str, Any]:
        """
        Boss Agent evaluation of specialized agent output
        
        Determines whether to:
        - Proceed to next stage (high confidence)
        - Request replanning (low confidence)
        - Trigger error recovery (unacceptable confidence)
        
        Args:
            agent_output: The output to evaluate
            confidence_score: The confidence score for the output
        
        Returns:
            Dictionary with evaluation decision and reasoning
        """
        decision = {
            "should_proceed": False,
            "should_replan": False,
            "should_error_recover": False,
            "confidence": confidence_score.overall,
            "reasoning": ""
        }
        
        if confidence_score.overall >= self.high_confidence_threshold:
            decision["should_proceed"] = True
            decision["reasoning"] = (
                f"High confidence ({confidence_score.overall:.2f}) - "
                f"proceeding to next stage. {confidence_score.reasoning}"
            )
        elif confidence_score.overall >= self.low_confidence_threshold:
            decision["should_proceed"] = True
            decision["reasoning"] = (
                f"Moderate confidence ({confidence_score.overall:.2f}) - "
                f"proceeding with caution. {confidence_score.reasoning}"
            )
        elif confidence_score.overall >= self.min_acceptable_confidence:
            decision["should_replan"] = True
            decision["reasoning"] = (
                f"Low confidence ({confidence_score.overall:.2f}) - "
                f"replanning recommended. {confidence_score.reasoning}"
            )
        else:
            decision["should_error_recover"] = True
            decision["reasoning"] = (
                f"Unacceptable confidence ({confidence_score.overall:.2f}) - "
                f"error recovery required. {confidence_score.reasoning}"
            )
        
        return decision
    
    def should_replan(
        self,
        confidence_score: ConfidenceScore,
        retry_count: int,
        max_retries: int = 3
    ) -> bool:
        """
        Determine if replanning should be triggered
        
        Args:
            confidence_score: Current confidence score
            retry_count: Number of retries so far
            max_retries: Maximum allowed retries
        
        Returns:
            True if replanning should be triggered
        """
        # Don't replan if we've exhausted retries
        if retry_count >= max_retries:
            return False
        
        # Replan if confidence is below threshold
        return confidence_score.overall < self.low_confidence_threshold
