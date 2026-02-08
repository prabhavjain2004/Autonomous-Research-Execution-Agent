"""
Strategy Agent Implementation

This agent specializes in generating strategic recommendations using LLM based on
research findings and analysis.
"""

import time
from typing import Dict, Any, List

from agents.base_agent import BaseAgent, AgentContext
from models.data_models import AgentOutput
from evaluation.reflection import ConfidenceScore, AgentType, ReflectionModule
from structured_logging.structured_logger import StructuredLogger
from model_router import ModelRouter, TaskComplexity


class StrategyAgent(BaseAgent):
    """
    Strategy Agent for generating recommendations and action plans
    
    This agent:
    - Reviews research findings and analysis using LLM
    - Generates strategic recommendations
    - Creates actionable plans with steps
    - Calculates confidence based on plan quality
    
    Confidence factors:
    - specificity: Concrete details and clear steps
    - actionability: Presence of action verbs and executable tasks
    - alignment: Alignment with original goals
    - feasibility: Realistic and achievable recommendations
    """
    
    def __init__(
        self,
        agent_name: str = "strategy_agent",
        max_retries: int = 3,
        max_recommendations: int = 5,
        logger: StructuredLogger = None,
        model_router: ModelRouter = None
    ):
        """
        Initialize Strategy Agent
        
        Args:
            agent_name: Name of the agent
            max_retries: Maximum number of retries allowed
            max_recommendations: Maximum number of recommendations to generate
            logger: Optional structured logger
            model_router: Model router for LLM calls
        """
        super().__init__(
            agent_name=agent_name,
            agent_type=AgentType.STRATEGY,
            max_retries=max_retries
        )
        
        if max_recommendations < 1:
            raise ValueError("max_recommendations must be at least 1")
        
        self.max_recommendations = max_recommendations
        self.logger = logger
        self.model_router = model_router
        
        # Initialize reflection module for confidence calculation
        self.reflection_module = ReflectionModule()
    
    def execute(self, context: AgentContext) -> AgentOutput:
        """
        Execute strategy generation task
        
        Process:
        1. Review previous agent outputs (research and analysis)
        2. Generate strategic recommendations
        3. Create action plan with steps
        4. Return structured output
        
        Args:
            context: Execution context with task information and previous outputs
        
        Returns:
            AgentOutput with strategic recommendations
        """
        start_time = time.time()
        
        if self.logger:
            self.logger.log_decision(
                agent_name=self.agent_name,
                decision=f"Starting strategy generation for: {context.task_description}",
                reasoning="Beginning strategic planning and recommendation generation"
            )
        
        # Step 1: Review previous outputs
        review = self._review_previous_outputs(context)
        
        if not context.previous_outputs:
            # No previous outputs to base strategy on
            execution_time = time.time() - start_time
            return AgentOutput(
                agent_name=self.agent_name,
                task_id=context.task_id,
                results={
                    "strategy": "No previous outputs available for strategic planning.",
                    "recommendations": [],
                    "action_plan": []
                },
                self_confidence=20,
                reasoning="No input data for strategy generation",
                sources=[],
                execution_time=execution_time
            )
        
        # Step 2: Generate recommendations
        recommendations = self._generate_recommendations(
            context.task_description,
            review
        )
        
        # Step 3: Create action plan
        action_plan = self._create_action_plan(
            context.task_description,
            recommendations,
            review
        )
        
        # Step 4: Assess feasibility
        feasibility = self._assess_feasibility(recommendations, review)
        
        execution_time = time.time() - start_time
        
        # Create output
        output = AgentOutput(
            agent_name=self.agent_name,
            task_id=context.task_id,
            results={
                "strategy": self._create_strategy_summary(
                    context.task_description,
                    recommendations
                ),
                "recommendations": recommendations,
                "action_plan": action_plan,
                "feasibility_assessment": feasibility,
                "total_recommendations": len(recommendations),
                "data_sources": list(context.previous_outputs.keys())
            },
            self_confidence=self._estimate_initial_confidence(
                recommendations,
                action_plan,
                feasibility
            ),
            reasoning=self._generate_reasoning(recommendations, action_plan),
            sources=[],  # Strategy doesn't use external sources
            execution_time=execution_time
        )
        
        if self.logger:
            self.logger.log_decision(
                agent_name=self.agent_name,
                decision=f"Strategy completed with {len(recommendations)} recommendations",
                reasoning=output.reasoning
            )
        
        return output
    
    def calculate_confidence(self, output: AgentOutput) -> ConfidenceScore:
        """
        Calculate confidence score for strategy output
        
        Uses the reflection module to assess:
        - Specificity of recommendations
        - Actionability of plans
        - Alignment with goals
        - Feasibility of execution
        
        Args:
            output: The strategy output to assess
        
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
    
    def _review_previous_outputs(self, context: AgentContext) -> Dict[str, Any]:
        """
        Review previous agent outputs
        
        Args:
            context: Execution context
        
        Returns:
            Dictionary with review summary
        """
        review = {
            "agents_reviewed": [],
            "key_findings": [],
            "insights": [],
            "confidence_levels": {}
        }
        
        for agent_name, output in context.previous_outputs.items():
            review["agents_reviewed"].append(agent_name)
            review["confidence_levels"][agent_name] = output.self_confidence
            
            # Extract key findings from results
            results = output.results
            if isinstance(results, dict):
                # From research agent
                if "summary" in results:
                    review["key_findings"].append({
                        "source": agent_name,
                        "finding": results["summary"]
                    })
                
                # From analyst agent
                if "insights" in results:
                    insights = results["insights"]
                    if isinstance(insights, list):
                        for insight in insights:
                            if isinstance(insight, dict):
                                review["insights"].append({
                                    "source": agent_name,
                                    "type": insight.get("type", "unknown"),
                                    "insight": insight.get("insight", ""),
                                    "recommendation": insight.get("recommendation", "")
                                })
        
        return review
    
    def _generate_recommendations(
        self,
        task_description: str,
        review: Dict[str, Any]
    ) -> List[str]:
        """
        Generate strategic recommendations using LLM

        Args:
            task_description: Task description
            review: Review of previous outputs

        Returns:
            List of recommendation strings
        """
        if not self.model_router:
            return self._generate_template_recommendations(task_description, review)

        # Prepare context from review
        context_parts = []

        # Add key findings
        key_findings = review.get("key_findings", [])
        if key_findings:
            context_parts.append("Key Research Findings:")
            for finding in key_findings[:3]:
                if isinstance(finding, dict):
                    context_parts.append(f"- {finding.get('finding', '')}")

        # Add insights
        insights = review.get("insights", [])
        if insights:
            context_parts.append("\nAnalysis Insights:")
            for insight in insights[:3]:
                if isinstance(insight, dict):
                    context_parts.append(f"- {insight.get('insight', '')}")

        # Add confidence levels
        confidence_levels = review.get("confidence_levels", {})
        if confidence_levels:
            avg_confidence = sum(confidence_levels.values()) / len(confidence_levels)
            context_parts.append(f"\nOverall Data Confidence: {avg_confidence:.1f}%")

        combined_context = "\n".join(context_parts)

        # Create prompt for LLM
        prompt = f"""You are a strategic advisor. Based on the research and analysis provided, generate 3-5 specific, actionable strategic recommendations.

    Research Question: {task_description}

    {combined_context}

    Please provide clear, actionable recommendations. Each recommendation should be:
    1. Specific and concrete
    2. Directly related to the research question
    3. Actionable with clear next steps
    4. Based on the findings and insights provided

    Format: Provide each recommendation as a separate numbered point."""

        try:
            response = self.model_router.call_with_fallback(
                task_complexity=TaskComplexity.COMPLEX,
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7
            )

            if response.success:
                # Parse recommendations from response
                recommendations_text = response.text
                # Split by newlines and filter
                rec_lines = [line.strip() for line in recommendations_text.split('\n') if line.strip()]

                # Extract recommendations (remove numbering)
                recommendations = []
                for line in rec_lines:
                    # Remove common numbering patterns
                    clean_line = line.lstrip('0123456789.-•*) ')
                    if clean_line and len(clean_line) > 20:  # Filter out very short lines
                        recommendations.append(clean_line)

                # Limit to 5 recommendations
                return recommendations[:5] if recommendations else [recommendations_text]
            else:
                return [f"Unable to generate recommendations: {response.error}"]

        except Exception as e:
            if self.logger:
                import traceback
                self.logger.log_error(
                    error_type="LLMRecommendationError",
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    context={"task": task_description}
                )
            return ["Error generating recommendations."]

    def _generate_template_recommendations(
        self,
        task_description: str,
        review: Dict[str, Any]
    ) -> List[str]:
        """
        Generate template-based recommendations (fallback)

        Args:
            task_description: Task description
            review: Review of previous outputs

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Recommendation based on confidence levels
        confidence_levels = review.get("confidence_levels", {})
        if confidence_levels:
            avg_confidence = sum(confidence_levels.values()) / len(confidence_levels)

            if avg_confidence >= 70:
                recommendations.append(
                    f"Proceed with implementation based on high confidence ({avg_confidence:.1f}%) findings. "
                    "The research data strongly supports moving forward with the identified strategies."
                )
            elif avg_confidence >= 50:
                recommendations.append(
                    f"Validate key findings before full implementation. Moderate confidence ({avg_confidence:.1f}%) "
                    "suggests additional verification would strengthen the strategy."
                )
            else:
                recommendations.append(
                    f"Conduct additional research to improve data quality. Low confidence ({avg_confidence:.1f}%) "
                    "indicates insufficient data for strategic decision-making."
                )

        # Recommendations based on insights
        insights = review.get("insights", [])
        for insight in insights[:2]:
            if isinstance(insight, dict):
                rec = insight.get("recommendation", "")
                if rec:
                    recommendations.append(rec)

        # General monitoring recommendation
        recommendations.append(
            f"Establish monitoring framework for '{task_description}' to track progress "
            "and identify issues early. Continuous monitoring enables rapid response to changes."
        )

        return recommendations[:self.max_recommendations]

    
    def _create_action_plan(
        self,
        task_description: str,
        recommendations: List[str],
        review: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create action plan with steps
        
        Args:
            task_description: Task description
            recommendations: Generated recommendations (list of strings)
            review: Review of previous outputs
        
        Returns:
            List of action steps
        """
        action_plan = []
        
        # Step 1: Review and prioritize
        action_plan.append({
            "step": 1,
            "phase": "preparation",
            "action": "Review and Prioritize Recommendations",
            "description": (
                f"Review all {len(recommendations)} recommendations and "
                "prioritize based on impact and feasibility."
            ),
            "timeline": "1-2 days",
            "dependencies": [],
            "success_criteria": "Prioritized list of recommendations with assigned owners"
        })
        
        # Step 2: Implement recommendations
        if len(recommendations) > 0:
            # Show first 2 recommendations as examples
            rec_preview = "; ".join(rec[:50] + "..." if len(rec) > 50 else rec for rec in recommendations[:2])
            action_plan.append({
                "step": 2,
                "phase": "execution",
                "action": "Implement Recommendations",
                "description": (
                    f"Execute {len(recommendations)} strategic recommendations. "
                    f"Starting with: {rec_preview}"
                ),
                "timeline": "1-2 weeks",
                "dependencies": [1],
                "success_criteria": "Recommendations implemented and validated"
            })
        
        # Step 3: Monitor and measure
        action_plan.append({
            "step": len(action_plan) + 1,
            "phase": "monitoring",
            "action": "Monitor Progress and Measure Results",
            "description": (
                "Establish KPIs and monitoring framework to track implementation "
                "progress and measure outcomes."
            ),
            "timeline": "Ongoing",
            "dependencies": [2] if len(action_plan) >= 2 else [1],
            "success_criteria": "KPIs defined and monitoring dashboard operational"
        })
        
        # Step 4: Iterate and optimize
        action_plan.append({
            "step": len(action_plan) + 1,
            "phase": "optimization",
            "action": "Iterate Based on Results",
            "description": (
                "Review results, gather feedback, and iterate on strategy "
                "to optimize outcomes."
            ),
            "timeline": "Ongoing",
            "dependencies": [len(action_plan)],
            "success_criteria": "Continuous improvement process established"
        })
        
        return action_plan
    
    def _assess_feasibility(
        self,
        recommendations: List[str],
        review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess feasibility of recommendations
        
        Args:
            recommendations: Generated recommendations (list of strings)
            review: Review of previous outputs
        
        Returns:
            Feasibility assessment
        """
        # Calculate feasibility score based on confidence levels
        confidence_levels = review.get("confidence_levels", {})
        avg_confidence = (
            sum(confidence_levels.values()) / len(confidence_levels)
            if confidence_levels else 50
        )
        
        # Feasibility factors
        data_quality_score = avg_confidence / 100.0
        complexity_score = max(0.5, 1.0 - (len(recommendations) * 0.1))  # More recs = more complex
        resource_score = 0.8  # Assume moderate resources available
        
        overall_feasibility = (
            data_quality_score * 0.4 +
            complexity_score * 0.3 +
            resource_score * 0.3
        )
        
        feasibility_level = (
            "high" if overall_feasibility >= 0.7
            else "moderate" if overall_feasibility >= 0.5
            else "low"
        )
        
        return {
            "overall_score": overall_feasibility,
            "level": feasibility_level,
            "factors": {
                "data_quality": data_quality_score,
                "complexity": complexity_score,
                "resources": resource_score
            },
            "risks": self._identify_risks(recommendations, review),
            "mitigation_strategies": self._suggest_mitigations(feasibility_level)
        }
    
    def _identify_risks(
        self,
        recommendations: List[str],
        review: Dict[str, Any]
    ) -> List[str]:
        """
        Identify potential risks
        
        Args:
            recommendations: Generated recommendations (list of strings)
            review: Review of previous outputs
        
        Returns:
            List of identified risks
        """
        risks = []
        
        # Risk 1: Low confidence
        confidence_levels = review.get("confidence_levels", {})
        if confidence_levels:
            avg_confidence = sum(confidence_levels.values()) / len(confidence_levels)
            if avg_confidence < 60:
                risks.append(
                    f"Data confidence is moderate ({avg_confidence:.1f}%), "
                    "which may impact recommendation reliability"
                )
        
        # Risk 2: High complexity
        if len(recommendations) > 3:
            risks.append(
                f"High number of recommendations ({len(recommendations)}) "
                "may increase implementation complexity"
            )
        
        # Risk 3: Resource constraints
        risks.append("Resource availability may impact implementation timeline")
        
        return risks
    
    def _suggest_mitigations(self, feasibility_level: str) -> List[str]:
        """
        Suggest mitigation strategies
        
        Args:
            feasibility_level: Assessed feasibility level
        
        Returns:
            List of mitigation strategies
        """
        if feasibility_level == "high":
            return [
                "Maintain regular progress reviews",
                "Document lessons learned for future iterations"
            ]
        elif feasibility_level == "moderate":
            return [
                "Prioritize high-impact, low-complexity recommendations first",
                "Allocate additional resources for critical tasks",
                "Establish clear success criteria and checkpoints"
            ]
        else:  # low
            return [
                "Consider phased implementation approach",
                "Gather additional data to improve confidence",
                "Reduce scope to focus on highest-priority items",
                "Secure executive sponsorship and resources"
            ]
    
    def _create_strategy_summary(
        self,
        task_description: str,
        recommendations: List[str]
    ) -> str:
        """
        Create strategy summary
        
        Args:
            task_description: Task description
            recommendations: Generated recommendations (list of strings)
        
        Returns:
            Strategy summary string
        """
        summary_parts = [
            f"Strategic Plan for: {task_description}",
            f"\nGenerated {len(recommendations)} strategic recommendations:"
        ]
        
        # Show first 3 recommendations
        for i, rec in enumerate(recommendations[:3], 1):
            # Truncate long recommendations
            rec_preview = rec[:100] + "..." if len(rec) > 100 else rec
            summary_parts.append(f"{i}. {rec_preview}")
        
        if len(recommendations) > 3:
            summary_parts.append(f"\n... and {len(recommendations) - 3} more recommendations")
        
        return "\n".join(summary_parts)
    
    def _estimate_initial_confidence(
        self,
        recommendations: List[str],
        action_plan: List[Dict[str, Any]],
        feasibility: Dict[str, Any]
    ) -> int:
        """
        Estimate initial confidence score (0-100)
        
        Args:
            recommendations: Generated recommendations (list of strings)
            action_plan: Action plan
            feasibility: Feasibility assessment
        
        Returns:
            Confidence score as integer
        """
        if not recommendations:
            return 20
        
        # Base confidence on recommendations, action plan, and feasibility
        rec_score = min(len(recommendations) / 3.0, 1.0) * 40  # Up to 40 points
        plan_score = min(len(action_plan) / 4.0, 1.0) * 30  # Up to 30 points
        feasibility_score = feasibility.get("overall_score", 0.5) * 30  # Up to 30 points
        
        return int(rec_score + plan_score + feasibility_score)
    
    def _generate_reasoning(
        self,
        recommendations: List[str],
        action_plan: List[Dict[str, Any]]
    ) -> str:
        """
        Generate reasoning for the strategy output
        
        Args:
            recommendations: Generated recommendations (list of strings)
            action_plan: Action plan
        
        Returns:
            Reasoning string
        """
        if not recommendations:
            return "Insufficient data for strategy generation"
        
        return (
            f"Generated comprehensive strategy with {len(recommendations)} recommendations "
            f"and {len(action_plan)}-step action plan"
        )
