"""
Output Formatter for Research Results

This module provides functionality to format agent outputs into structured
ResearchResult objects with JSON schema validation.

Requirements: 11.1-11.11
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from models.data_models import ResearchResult, AgentOutput


class OutputFormatter:
    """
    Formats agent outputs into structured ResearchResult objects.
    
    This class aggregates outputs from multiple agents and creates a
    properly formatted ResearchResult with all required fields populated
    and validated against the JSON schema.
    """
    
    def __init__(self):
        """Initialize the output formatter."""
        pass
    
    def format_research_result(
        self,
        goal: str,
        agent_outputs: List[AgentOutput],
        session_id: Optional[str] = None
    ) -> ResearchResult:
        """
        Format agent outputs into a ResearchResult.
        
        Args:
            goal: The original research goal
            agent_outputs: List of outputs from all agents
            session_id: Optional session ID (generates new UUID if not provided)
        
        Returns:
            ResearchResult object with all fields populated
        
        Raises:
            ValueError: If required data is missing or invalid
        
        Requirements: 11.1-11.11
        """
        # Validate inputs
        if not goal or not goal.strip():
            raise ValueError("Research goal cannot be empty")
        
        if not agent_outputs:
            raise ValueError("At least one agent output is required")
        
        # Generate or validate session ID (Requirement 11.1)
        if session_id:
            try:
                uuid.UUID(session_id)
            except ValueError:
                raise ValueError(f"Invalid session_id format: {session_id}")
        else:
            session_id = str(uuid.uuid4())
        
        # Extract data from agent outputs
        agents_involved = []
        confidence_scores = {}
        insights = []
        recommendations = []
        sources = []
        competitors = []
        
        for output in agent_outputs:
            # Validate agent output
            if not output.validate():
                raise ValueError(f"Invalid agent output from {output.agent_name}")
            
            # Collect agent names (Requirement 11.4)
            if output.agent_name not in agents_involved:
                agents_involved.append(output.agent_name)
            
            # Collect confidence scores (Requirement 11.5)
            # Convert 0-100 scale to 0-100 integer
            confidence_scores[output.agent_name] = {
                "self": output.self_confidence,
                "boss": output.self_confidence  # Default to self if boss not available
            }
            
            # Extract data from results
            results = output.results
            
            # Extract insights
            if "insights" in results:
                agent_insights = results["insights"]
                if isinstance(agent_insights, list):
                    for insight in agent_insights:
                        if isinstance(insight, str) and insight not in insights:
                            insights.append(insight)
            
            # Extract recommendations
            if "recommendations" in results:
                agent_recs = results["recommendations"]
                if isinstance(agent_recs, list):
                    for rec in agent_recs:
                        if isinstance(rec, str):
                            rec_dict = {"text": rec, "priority": "medium"}
                            if rec_dict not in recommendations:
                                recommendations.append(rec_dict)
                        elif isinstance(rec, dict) and rec not in recommendations:
                            recommendations.append(rec)
            
            # Extract sources
            if output.sources:
                for source_url in output.sources:
                    source_dict = {"url": source_url, "title": source_url}
                    if source_dict not in sources:
                        sources.append(source_dict)
            
            # Extract competitors
            if "competitors" in results:
                agent_comps = results["competitors"]
                if isinstance(agent_comps, list):
                    for comp in agent_comps:
                        if isinstance(comp, dict) and comp not in competitors:
                            competitors.append(comp)
        
        # Calculate overall confidence (Requirement 11.10)
        overall_confidence = self._calculate_overall_confidence(confidence_scores)
        
        # Ensure we have at least some data (Requirement 11.7, 11.8)
        if not insights:
            insights = ["No specific insights were generated from the research."]
        
        if not recommendations:
            recommendations = [{"text": "Further research may be needed.", "priority": "low"}]
        
        if not competitors:
            competitors = []
        
        # Create ResearchResult (Requirements 11.1-11.10)
        result = ResearchResult.create_new(
            goal=goal,  # Requirement 11.2
            agents_involved=agents_involved,  # Requirement 11.4
            confidence_scores=confidence_scores,  # Requirement 11.5
            competitors=competitors,  # Requirement 11.6
            insights=insights,  # Requirement 11.7
            recommendations=recommendations,  # Requirement 11.8
            sources=sources,  # Requirement 11.9
            overall_confidence=overall_confidence  # Requirement 11.10
        )
        
        # Override session_id if provided
        if session_id:
            result.session_id = session_id
        
        # Validate against schema (Requirement 11.11)
        if not result.validate_schema():
            raise ValueError("Generated result does not conform to JSON schema")
        
        return result
    
    def _calculate_overall_confidence(self, confidence_scores: Dict[str, Dict[str, int]]) -> int:
        """
        Calculate overall confidence score from individual agent scores.
        
        Uses weighted average of self and boss confidence scores.
        
        Args:
            confidence_scores: Dictionary of agent confidence scores (0-100)
        
        Returns:
            Overall confidence score between 0 and 100
        """
        if not confidence_scores:
            return 0
        
        total_self = 0
        total_boss = 0
        count = 0
        
        for agent, scores in confidence_scores.items():
            total_self += scores.get("self", 0)
            total_boss += scores.get("boss", 0)
            count += 1
        
        if count == 0:
            return 0
        
        # Weighted average: 40% self, 60% boss
        avg_self = total_self / count
        avg_boss = total_boss / count
        overall = (avg_self * 0.4) + (avg_boss * 0.6)
        
        # Ensure bounds and return as integer
        return int(max(0, min(100, overall)))
    
    def format_error_result(
        self,
        goal: str,
        error_message: str,
        partial_outputs: Optional[List[AgentOutput]] = None,
        session_id: Optional[str] = None
    ) -> ResearchResult:
        """
        Format an error result when research fails.
        
        Args:
            goal: The original research goal
            error_message: Description of the error
            partial_outputs: Any partial outputs from agents
            session_id: Optional session ID
        
        Returns:
            ResearchResult object indicating failure
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        agents_involved = []
        confidence_scores = {}
        
        if partial_outputs:
            for output in partial_outputs:
                if output.agent_name not in agents_involved:
                    agents_involved.append(output.agent_name)
                confidence_scores[output.agent_name] = {
                    "self": output.self_confidence,
                    "boss": 0
                }
        
        result = ResearchResult(
            session_id=session_id,
            goal=goal,
            timestamp=datetime.utcnow().isoformat() + "Z",
            agents_involved=agents_involved or ["Boss Agent"],
            confidence_scores=confidence_scores or {"Boss Agent": {"self": 0, "boss": 0}},
            competitors=[],
            insights=[f"Research failed: {error_message}"],
            recommendations=[{"text": "Review the error and retry with adjusted parameters.", "priority": "high"}],
            sources=[],
            overall_confidence=0
        )
        
        return result
    
    def validate_result(self, result: ResearchResult) -> bool:
        """
        Validate a ResearchResult object.
        
        Args:
            result: The ResearchResult to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check basic validation
            if not result.validate():
                return False
            
            # Check schema validation
            if not result.validate_schema():
                return False
            
            return True
            
        except Exception:
            return False
