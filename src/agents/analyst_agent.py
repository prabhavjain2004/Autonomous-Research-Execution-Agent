"""
Analyst Agent Implementation

This agent specializes in analyzing data using LLM to identify patterns and draw
insights from research findings.
"""

import time
from typing import Dict, Any, List

from agents.base_agent import BaseAgent, AgentContext
from models.data_models import AgentOutput
from evaluation.reflection import ConfidenceScore, AgentType, ReflectionModule
from tools.python_executor import PythonExecutorTool
from structured_logging.structured_logger import StructuredLogger
from model_router import ModelRouter, TaskComplexity


class AnalystAgent(BaseAgent):
    """
    Analyst Agent for data analysis and pattern recognition
    
    This agent:
    - Analyzes research findings from previous agents using LLM
    - Identifies patterns and trends in the data
    - Draws insights and conclusions
    - Calculates confidence based on analysis quality
    
    Confidence factors:
    - insight_depth: Complexity and depth of analysis
    - consistency: Logical consistency of findings
    - pattern_clarity: Clarity of identified patterns
    - evidence_strength: Strength of supporting evidence
    """
    
    def __init__(
        self,
        agent_name: str = "analyst_agent",
        max_retries: int = 3,
        enable_code_execution: bool = True,
        logger: StructuredLogger = None,
        model_router: ModelRouter = None
    ):
        """
        Initialize Analyst Agent
        
        Args:
            agent_name: Name of the agent
            max_retries: Maximum number of retries allowed
            enable_code_execution: Whether to enable Python code execution for analysis
            logger: Optional structured logger
            model_router: Model router for LLM calls
        """
        super().__init__(
            agent_name=agent_name,
            agent_type=AgentType.ANALYST,
            max_retries=max_retries
        )
        
        self.enable_code_execution = enable_code_execution
        self.logger = logger
        self.model_router = model_router
        
        # Initialize tools
        if enable_code_execution:
            self.python_executor = PythonExecutorTool()
        
        # Initialize reflection module for confidence calculation
        self.reflection_module = ReflectionModule()
    
    def execute(self, context: AgentContext) -> AgentOutput:
        """
        Execute analysis task
        
        Process:
        1. Extract data from previous agent outputs
        2. Perform analysis to identify patterns
        3. Generate insights and conclusions
        4. Return structured output
        
        Args:
            context: Execution context with task information and previous outputs
        
        Returns:
            AgentOutput with analysis results
        """
        start_time = time.time()
        
        if self.logger:
            self.logger.log_decision(
                agent_name=self.agent_name,
                decision=f"Starting analysis for: {context.task_description}",
                reasoning="Beginning data analysis and pattern recognition"
            )
        
        # Step 1: Extract data from previous outputs
        data = self._extract_data_from_context(context)
        
        if not data:
            # No data to analyze
            execution_time = time.time() - start_time
            return AgentOutput(
                agent_name=self.agent_name,
                task_id=context.task_id,
                results={
                    "analysis": "No data available for analysis.",
                    "insights": [],
                    "patterns": []
                },
                self_confidence=20,
                reasoning="No input data provided for analysis",
                sources=[],
                execution_time=execution_time
            )
        
        # Step 2: Use LLM to perform deep analysis
        analysis_results = self._perform_llm_analysis(context.task_description, data)
        
        # Step 3: Extract patterns from LLM analysis
        patterns = self._identify_patterns(data, analysis_results)
        
        # Step 4: Use LLM to generate insights
        insights = self._generate_llm_insights(context.task_description, data, analysis_results)
        
        execution_time = time.time() - start_time
        
        # Create output
        output = AgentOutput(
            agent_name=self.agent_name,
            task_id=context.task_id,
            results={
                "analysis": analysis_results,
                "patterns": patterns,
                "insights": insights,
                "data_sources": list(context.previous_outputs.keys()),
                "total_insights": len(insights)
            },
            self_confidence=self._estimate_initial_confidence(insights, patterns),
            reasoning=self._generate_reasoning(insights, patterns),
            sources=[],  # Analyst doesn't use external sources
            execution_time=execution_time
        )
        
        if self.logger:
            self.logger.log_decision(
                agent_name=self.agent_name,
                decision=f"Analysis completed with {len(insights)} insights",
                reasoning=output.reasoning
            )
        
        return output
    
    def calculate_confidence(self, output: AgentOutput) -> ConfidenceScore:
        """
        Calculate confidence score for analysis output
        
        Uses the reflection module to assess:
        - Insight depth and complexity
        - Logical consistency
        - Pattern clarity
        - Evidence strength
        
        Args:
            output: The analysis output to assess
        
        Returns:
            ConfidenceScore with detailed factor breakdown
        """
        # Use reflection module for consistent confidence calculation
        score = self.reflection_module.calculate_self_confidence(
            output,
            self.agent_type,
            task_description=output.task_id
        )
        
        return score
    
    def _extract_data_from_context(self, context: AgentContext) -> Dict[str, Any]:
        """
        Extract data from previous agent outputs
        
        Args:
            context: Execution context
        
        Returns:
            Dictionary with extracted data
        """
        extracted_data = {}
        
        for agent_name, output in context.previous_outputs.items():
            extracted_data[agent_name] = {
                "results": output.results,
                "confidence": output.self_confidence,
                "sources": output.sources,
                "reasoning": output.reasoning
            }
        
        return extracted_data
    
    def _perform_llm_analysis(self, task_description: str, data: Dict[str, Any]) -> str:
        """
        Use LLM to perform deep analysis on the data
        
        Args:
            task_description: Description of the analysis task
            data: Data to analyze
        
        Returns:
            LLM-generated analysis
        """
        if not self.model_router:
            return self._perform_analysis(task_description, data)  # Fallback to template
        
        # Prepare data for LLM
        data_summary = []
        for agent_name, agent_data in data.items():
            results = agent_data.get("results", {})
            summary = results.get("summary", str(results)[:1000])  # Limit length
            data_summary.append(f"{agent_name} findings:\n{summary}")
        
        combined_data = "\n\n".join(data_summary)
        
        # Create prompt for LLM
        prompt = f"""You are a data analyst. Analyze the following research findings and provide a comprehensive analysis.

Task: {task_description}

Research Findings:
{combined_data}

Please provide:
1. A detailed analysis of the findings
2. Key patterns and trends you observe
3. Important connections between different pieces of information
4. Any notable insights or conclusions

Be specific and analytical in your response."""

        try:
            response = self.model_router.call_with_fallback(
                task_complexity=TaskComplexity.COMPLEX,
                prompt=prompt,
                max_tokens=1500,
                temperature=0.7
            )
            
            if response.success:
                return response.text
            else:
                return f"Analysis unavailable: {response.error}"
        
        except Exception as e:
            if self.logger:
                import traceback
                self.logger.log_error(
                    error_type="LLMAnalysisError",
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    context={"task": task_description}
                )
            return "Error generating analysis."
    
    def _generate_llm_insights(
        self,
        task_description: str,
        data: Dict[str, Any],
        analysis: str
    ) -> List[Dict[str, str]]:
        """
        Use LLM to generate insights from the analysis
        
        Args:
            task_description: Description of the task
            data: Original data
            analysis: LLM-generated analysis
        
        Returns:
            List of insights
        """
        if not self.model_router:
            return self._generate_insights(task_description, data, [])  # Fallback
        
        # Create prompt for insights
        prompt = f"""Based on the following analysis, generate 3-5 key insights that directly answer the research question.

Research Question: {task_description}

Analysis:
{analysis}

Please provide specific, actionable insights. Format each insight as a clear statement."""

        try:
            response = self.model_router.call_with_fallback(
                task_complexity=TaskComplexity.MODERATE,
                prompt=prompt,
                max_tokens=800,
                temperature=0.7
            )
            
            if response.success:
                # Parse insights from response
                insights_text = response.text
                # Split by newlines and filter empty lines
                insight_lines = [line.strip() for line in insights_text.split('\n') if line.strip()]
                
                # Create structured insights
                insights = []
                for i, line in enumerate(insight_lines[:5], 1):  # Limit to 5
                    # Remove numbering if present
                    clean_line = line.lstrip('0123456789.-) ')
                    if clean_line:
                        insights.append({
                            "insight": clean_line,
                            "confidence": "high" if i <= 3 else "moderate"
                        })
                
                return insights if insights else [{"insight": insights_text, "confidence": "moderate"}]
            else:
                return [{"insight": f"Insights unavailable: {response.error}", "confidence": "low"}]
        
        except Exception as e:
            if self.logger:
                import traceback
                self.logger.log_error(
                    error_type="LLMInsightsError",
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    context={"task": task_description}
                )
            return [{"insight": "Error generating insights.", "confidence": "low"}]
    
    def _perform_analysis(self, task_description: str, data: Dict[str, Any]) -> str:
        """
        Perform analysis on the data
        
        Args:
            task_description: Description of the analysis task
            data: Data to analyze
        
        Returns:
            Analysis summary
        """
        analysis_parts = [
            f"Analysis of: {task_description}",
            f"\nData sources analyzed: {len(data)}"
        ]
        
        # Analyze each data source
        for agent_name, agent_data in data.items():
            confidence = agent_data.get("confidence", 0)
            results = agent_data.get("results", {})
            
            analysis_parts.append(f"\n{agent_name.upper()} Analysis:")
            analysis_parts.append(f"- Confidence level: {confidence}%")
            
            # Extract key information
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, (str, int, float)):
                        analysis_parts.append(f"- {key}: {value}")
                    elif isinstance(value, list) and len(value) > 0:
                        analysis_parts.append(f"- {key}: {len(value)} items")
        
        return "\n".join(analysis_parts)
    
    def _identify_patterns(self, data: Dict[str, Any], analysis: str) -> List[Dict[str, Any]]:
        """
        Identify patterns in the data
        
        Args:
            data: Data to analyze
            analysis: Analysis summary
        
        Returns:
            List of identified patterns
        """
        patterns = []
        
        # Pattern 1: Confidence levels across agents
        confidences = []
        for agent_name, agent_data in data.items():
            confidence = agent_data.get("confidence", 0)
            confidences.append({
                "agent": agent_name,
                "confidence": confidence
            })
        
        if confidences:
            avg_confidence = sum(c["confidence"] for c in confidences) / len(confidences)
            patterns.append({
                "type": "confidence_pattern",
                "description": f"Average confidence across agents: {avg_confidence:.1f}%",
                "details": confidences
            })
        
        # Pattern 2: Data volume patterns
        data_volumes = []
        for agent_name, agent_data in data.items():
            results = agent_data.get("results", {})
            if isinstance(results, dict):
                volume = len(str(results))
                data_volumes.append({
                    "agent": agent_name,
                    "data_volume": volume
                })
        
        if data_volumes:
            total_volume = sum(d["data_volume"] for d in data_volumes)
            patterns.append({
                "type": "data_volume_pattern",
                "description": f"Total data volume: {total_volume} characters",
                "details": data_volumes
            })
        
        # Pattern 3: Source reliability (if research data available)
        for agent_name, agent_data in data.items():
            sources = agent_data.get("sources", [])
            if sources:
                reliable_sources = sum(
                    1 for s in sources
                    if any(domain in str(s) for domain in [".edu", ".gov", ".org"])
                )
                patterns.append({
                    "type": "source_reliability_pattern",
                    "description": f"{agent_name}: {reliable_sources}/{len(sources)} reliable sources",
                    "details": {
                        "total_sources": len(sources),
                        "reliable_sources": reliable_sources,
                        "reliability_ratio": reliable_sources / len(sources) if sources else 0
                    }
                })
        
        return patterns
    
    def _generate_insights(
        self,
        task_description: str,
        data: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Generate insights from analysis and patterns
        
        Args:
            task_description: Task description
            data: Analyzed data
            patterns: Identified patterns
        
        Returns:
            List of insights
        """
        insights = []
        
        # Insight 1: Overall data quality
        if data:
            avg_confidence = sum(
                d.get("confidence", 0) for d in data.values()
            ) / len(data)
            
            quality_level = "high" if avg_confidence >= 70 else "moderate" if avg_confidence >= 50 else "low"
            insights.append({
                "type": "data_quality",
                "insight": f"Overall data quality is {quality_level} with average confidence of {avg_confidence:.1f}%",
                "recommendation": self._get_quality_recommendation(avg_confidence)
            })
        
        # Insight 2: Pattern-based insights
        for pattern in patterns:
            if pattern["type"] == "confidence_pattern":
                details = pattern.get("details", [])
                if details:
                    high_conf = [d for d in details if d["confidence"] >= 70]
                    if high_conf:
                        insights.append({
                            "type": "confidence_insight",
                            "insight": f"{len(high_conf)} out of {len(details)} agents show high confidence",
                            "recommendation": "Findings from high-confidence agents can be prioritized"
                        })
            
            elif pattern["type"] == "source_reliability_pattern":
                details = pattern.get("details", {})
                reliability = details.get("reliability_ratio", 0)
                if reliability >= 0.5:
                    insights.append({
                        "type": "reliability_insight",
                        "insight": f"High source reliability detected ({reliability*100:.0f}% from trusted domains)",
                        "recommendation": "Research findings are well-supported by authoritative sources"
                    })
        
        # Insight 3: Task-specific insight
        insights.append({
            "type": "task_completion",
            "insight": f"Analysis completed for: {task_description}",
            "recommendation": "Review patterns and insights for strategic planning"
        })
        
        return insights
    
    def _get_quality_recommendation(self, confidence: float) -> str:
        """
        Get recommendation based on confidence level
        
        Args:
            confidence: Average confidence score
        
        Returns:
            Recommendation string
        """
        if confidence >= 70:
            return "Data quality is sufficient for strategic decision-making"
        elif confidence >= 50:
            return "Consider gathering additional data to improve confidence"
        else:
            return "Recommend replanning with refined research approach"
    
    def _estimate_initial_confidence(
        self,
        insights: List[Dict[str, str]],
        patterns: List[Dict[str, Any]]
    ) -> int:
        """
        Estimate initial confidence score (0-100)
        
        Args:
            insights: Generated insights
            patterns: Identified patterns
        
        Returns:
            Confidence score as integer
        """
        if not insights and not patterns:
            return 20
        
        # Base confidence on number of insights and patterns
        insight_score = min(len(insights) / 3.0, 1.0) * 50  # Up to 50 points
        pattern_score = min(len(patterns) / 3.0, 1.0) * 50  # Up to 50 points
        
        return int(insight_score + pattern_score)
    
    def _generate_reasoning(
        self,
        insights: List[Dict[str, str]],
        patterns: List[Dict[str, Any]]
    ) -> str:
        """
        Generate reasoning for the analysis output
        
        Args:
            insights: Generated insights
            patterns: Identified patterns
        
        Returns:
            Reasoning string
        """
        if not insights and not patterns:
            return "Insufficient data for meaningful analysis"
        
        return (
            f"Completed analysis with {len(patterns)} patterns identified "
            f"and {len(insights)} insights generated"
        )
