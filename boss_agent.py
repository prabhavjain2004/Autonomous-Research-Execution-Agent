"""
Boss Agent Implementation

The Boss Agent orchestrates the complete research workflow by delegating tasks
to specialized agents (Research, Analyst, Strategy), evaluating their outputs,
and managing the overall execution flow.
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from enum import Enum

from agents.base_agent import AgentContext
from agents.research_agent import ResearchAgent
from agents.analyst_agent import AnalystAgent
from agents.strategy_agent import StrategyAgent
from evaluation.reflection import ReflectionModule, ConfidenceScore
from models.data_models import ResearchResult, AgentOutput
from memory.memory_system import MemorySystem
from structured_logging.structured_logger import StructuredLogger
from agent_loop.state_machine import StateMachine, AgentState


class WorkflowPhase(Enum):
    """Phases of the research workflow"""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    STRATEGY = "strategy"
    COMPLETE = "complete"


class BossAgent:
    """
    Boss Agent for orchestrating multi-agent research workflow
    
    The Boss Agent:
    - Delegates tasks to specialized agents (Research, Analyst, Strategy)
    - Evaluates agent outputs using confidence scores
    - Manages workflow state and transitions
    - Handles replanning when confidence is low
    - Aggregates results into final research output
    - Persists all data to memory system
    """
    
    def __init__(
        self,
        memory_system: MemorySystem,
        logger: StructuredLogger,
        model_router: 'ModelRouter',
        max_retries: int = 3,
        confidence_threshold: float = 0.70
    ):
        """
        Initialize Boss Agent
        
        Args:
            memory_system: Memory system for persistence
            logger: Structured logger
            model_router: Model router for LLM calls
            max_retries: Maximum retries per agent
            confidence_threshold: Minimum confidence to proceed (0.0-1.0)
        """
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        
        self.memory_system = memory_system
        self.logger = logger
        self.model_router = model_router
        self.max_retries = max_retries
        self.confidence_threshold = confidence_threshold
        
        # Initialize specialized agents with model router
        self.research_agent = ResearchAgent(
            logger=logger,
            max_retries=max_retries,
            model_router=model_router
        )
        self.analyst_agent = AnalystAgent(
            logger=logger,
            max_retries=max_retries,
            model_router=model_router
        )
        self.strategy_agent = StrategyAgent(
            logger=logger,
            max_retries=max_retries,
            model_router=model_router
        )
        
        # Initialize reflection module for evaluation
        # Use confidence_threshold as high threshold, and set low threshold appropriately
        low_threshold = max(0.4, confidence_threshold - 0.2)  # At least 0.2 below high threshold
        self.reflection_module = ReflectionModule(
            high_confidence_threshold=confidence_threshold,
            low_confidence_threshold=low_threshold
        )
        
        # Workflow state
        self.current_phase: Optional[WorkflowPhase] = None
        self.active_agent: Optional[str] = None
        self.agent_outputs: Dict[str, AgentOutput] = {}
        self.confidence_scores: Dict[str, ConfidenceScore] = {}
        self.session_id: Optional[str] = None
    
    def execute_research(self, goal: str) -> ResearchResult:
        """
        Execute complete research workflow
        
        Process:
        1. Create session and initialize state machine
        2. Execute Research Agent
        3. Execute Analyst Agent
        4. Execute Strategy Agent
        5. Aggregate results
        6. Persist to memory
        
        Args:
            goal: Research goal/question
        
        Returns:
            ResearchResult with complete findings
        """
        start_time = time.time()
        
        # Create session
        self.session_id = str(self.memory_system.create_session(goal))
        
        self.logger.log_decision(
            agent_name="boss_agent",
            decision=f"Starting research workflow for: {goal}",
            reasoning="Initiating multi-agent research process"
        )
        
        try:
            # Phase 1: Research
            self.current_phase = WorkflowPhase.RESEARCH
            research_output = self._execute_phase(
                agent=self.research_agent,
                task_description=f"Research: {goal}",
                previous_outputs={}
            )
            
            if not research_output:
                return self._create_error_result(goal, "Research phase failed")
            
            # Phase 2: Analysis
            self.current_phase = WorkflowPhase.ANALYSIS
            analyst_output = self._execute_phase(
                agent=self.analyst_agent,
                task_description=f"Analyze findings for: {goal}",
                previous_outputs={"research_agent": research_output}
            )
            
            if not analyst_output:
                return self._create_error_result(goal, "Analysis phase failed")
            
            # Phase 3: Strategy
            self.current_phase = WorkflowPhase.STRATEGY
            strategy_output = self._execute_phase(
                agent=self.strategy_agent,
                task_description=f"Generate strategy for: {goal}",
                previous_outputs={
                    "research_agent": research_output,
                    "analyst_agent": analyst_output
                }
            )
            
            if not strategy_output:
                return self._create_error_result(goal, "Strategy phase failed")
            
            # Phase 4: Aggregate results
            self.current_phase = WorkflowPhase.COMPLETE
            result = self._aggregate_results(goal, start_time)
            
            # Persist final result
            self.memory_system.store_final_result(
                session_id=self.session_id,
                result=result
            )
            
            self.memory_system.update_session_status(
                session_id=self.session_id,
                status="completed"
            )
            
            self.logger.log_decision(
                agent_name="boss_agent",
                decision="Research workflow completed successfully",
                reasoning=f"All phases completed with {len(self.agent_outputs)} agent outputs"
            )
            
            return result
        
        except Exception as e:
            import traceback
            self.logger.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                context={"session_id": str(self.session_id), "phase": self.current_phase.value if self.current_phase else "unknown"}
            )
            
            self.memory_system.update_session_status(
                session_id=self.session_id,
                status="failed"
            )
            
            return self._create_error_result(goal, f"Workflow failed: {str(e)}")
    
    def _execute_phase(
        self,
        agent,
        task_description: str,
        previous_outputs: Dict[str, AgentOutput]
    ) -> Optional[AgentOutput]:
        """
        Execute a single workflow phase with an agent
        
        Args:
            agent: Agent to execute
            task_description: Description of the task
            previous_outputs: Outputs from previous agents
        
        Returns:
            AgentOutput if successful, None if failed after retries
        """
        self.active_agent = agent.agent_name
        task_id = f"{self.session_id}_{agent.agent_name}"
        
        self.logger.log_state_transition(
            from_state="planning",
            to_state="execution",
            reason=f"Executing {agent.agent_name}"
        )
        
        for attempt in range(self.max_retries + 1):
            try:
                # Create context
                context = AgentContext(
                    task_id=task_id,
                    task_description=task_description,
                    previous_outputs=previous_outputs,
                    retry_count=attempt,
                    session_id=self.session_id
                )
                
                # Execute agent
                output = agent.execute(context)
                
                # Store decision
                self.memory_system.store_decision(
                    session_id=self.session_id,
                    agent_name=agent.agent_name,
                    decision=output.reasoning,
                    context={"confidence": output.self_confidence}
                )
                
                # Note: Tool outputs are already logged by individual agents
                # No need to store them again here
                
                # Calculate self-confidence
                confidence_score = agent.calculate_confidence(output)
                
                # Boss Agent evaluates output using LLM
                boss_confidence = self._evaluate_with_llm(
                    agent_name=agent.agent_name,
                    agent_output=output,
                    task_description=task_description
                )
                
                # Store confidence scores (both self and boss)
                self.memory_system.store_confidence_scores(
                    session_id=self.session_id,
                    agent_name=agent.agent_name,
                    self_score=int(confidence_score.overall * 100),  # Convert to 0-100
                    boss_score=int(boss_confidence * 100),  # Convert to 0-100
                    retry_count=attempt
                )
                
                # Use the LOWER of the two scores for decision making (more conservative)
                final_confidence = min(confidence_score.overall, boss_confidence)
                
                # Create a combined confidence score for evaluation
                combined_score = ConfidenceScore(
                    overall=final_confidence,
                    factors={
                        "self_assessment": confidence_score.overall,
                        "boss_assessment": boss_confidence,
                        **confidence_score.factors
                    },
                    agent_type=confidence_score.agent_type,
                    reasoning=f"Self: {confidence_score.overall:.2f}, Boss: {boss_confidence:.2f}. {confidence_score.reasoning}"
                )
                
                # Evaluate output using combined score
                evaluation = self.reflection_module.evaluate_output(output, combined_score)
                
                # Determine decision string for logging
                if evaluation["should_proceed"]:
                    decision_str = "proceed"
                elif evaluation["should_replan"]:
                    decision_str = "replan"
                elif evaluation["should_error_recover"]:
                    decision_str = "error_recover"
                else:
                    decision_str = "unknown"
                
                self.logger.log_confidence_scores(
                    agent_name=agent.agent_name,
                    self_score=int(confidence_score.overall * 100),  # Convert 0.0-1.0 to 0-100
                    boss_score=int(boss_confidence * 100),  # Convert 0.0-1.0 to 0-100
                    decision=decision_str,
                    reasoning=evaluation["reasoning"]
                )
                
                # Check if we should proceed
                if evaluation["should_proceed"]:
                    # Success - store and return
                    self.agent_outputs[agent.agent_name] = output
                    self.confidence_scores[agent.agent_name] = confidence_score
                    return output
                
                elif evaluation["should_replan"] and attempt < self.max_retries:
                    # Low confidence - retry
                    self.logger.log_decision(
                        agent_name="boss_agent",
                        decision=f"Replanning {agent.agent_name} (attempt {attempt + 1}/{self.max_retries})",
                        reasoning=evaluation["reasoning"]
                    )
                    agent.increment_retry_count()
                    continue
                
                else:
                    # Error recovery or max retries reached
                    self.logger.log_error(
                        error_type="LowConfidence",
                        error_message=f"{agent.agent_name} failed after {attempt + 1} attempts",
                        stack_trace="",
                        context={"confidence": confidence_score.overall}
                    )
                    
                    # Store partial result
                    self.agent_outputs[agent.agent_name] = output
                    self.confidence_scores[agent.agent_name] = confidence_score
                    
                    # Return None to indicate failure
                    return None
            
            except Exception as e:
                import traceback
                self.logger.log_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    context={"agent": agent.agent_name, "attempt": attempt}
                )
                
                if attempt >= self.max_retries:
                    return None
                
                agent.increment_retry_count()
                continue
        
        return None
    
    def _evaluate_with_llm(
        self,
        agent_name: str,
        agent_output: AgentOutput,
        task_description: str
    ) -> float:
        """
        Boss Agent evaluates agent output using LLM
        
        Uses the best available model (Gemma 12B) to independently assess
        the quality of the agent's output.
        
        Args:
            agent_name: Name of the agent being evaluated
            agent_output: The output to evaluate
            task_description: Original task description
        
        Returns:
            Confidence score from 0.0 to 1.0
        """
        from model_router import TaskComplexity
        
        # If no model router, fall back to self-assessment only
        if not self.model_router:
            return agent_output.self_confidence / 100.0
        
        # Prepare output summary for LLM
        results_str = str(agent_output.results)[:2000]  # Limit length
        reasoning_str = agent_output.reasoning[:500]
        sources_str = ", ".join(agent_output.sources[:5]) if agent_output.sources else "No sources"
        
        # Create evaluation prompt
        prompt = f"""You are a quality evaluator for an AI research system. Evaluate the following output from the {agent_name}.

Task: {task_description}

Agent Output:
- Results: {results_str}
- Reasoning: {reasoning_str}
- Sources: {sources_str}
- Self-Confidence: {agent_output.self_confidence}%

Evaluate the output quality on a scale of 0-100 based on:
1. Completeness: Does it fully address the task?
2. Accuracy: Is the information reliable and well-sourced?
3. Clarity: Is it well-structured and understandable?
4. Relevance: Does it directly answer the research question?

Respond with ONLY a number from 0-100 representing the quality score. No explanation needed."""

        try:
            # Use best model (Gemma 12B) for evaluation
            response = self.model_router.call_with_fallback(
                task_complexity=TaskComplexity.COMPLEX,
                prompt=prompt,
                max_tokens=10,  # Just need a number
                temperature=0.3  # Low temperature for consistent evaluation
            )
            
            if response.success:
                # Extract number from response
                import re
                numbers = re.findall(r'\d+', response.text)
                if numbers:
                    score = int(numbers[0])
                    # Clamp to 0-100 range
                    score = max(0, min(100, score))
                    
                    if self.logger:
                        self.logger.log_info(
                            f"Boss LLM evaluation for {agent_name}: {score}%",
                            {"agent": agent_name, "boss_score": score, "self_score": agent_output.self_confidence}
                        )
                    
                    return score / 100.0  # Convert to 0.0-1.0
                else:
                    # Couldn't parse number, use self-assessment
                    return agent_output.self_confidence / 100.0
            else:
                # LLM call failed, use self-assessment
                if self.logger:
                    self.logger.log_info(
                        f"Boss LLM evaluation failed for {agent_name}, using self-assessment",
                        {"error": response.error}
                    )
                return agent_output.self_confidence / 100.0
        
        except Exception as e:
            # Error during evaluation, use self-assessment
            if self.logger:
                import traceback
                self.logger.log_error(
                    error_type="BossEvaluationError",
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    context={"agent": agent_name}
                )
            return agent_output.self_confidence / 100.0
    
    def _aggregate_results(self, goal: str, start_time: float) -> ResearchResult:
        """
        Aggregate results from all agents into final output
        
        Args:
            goal: Original research goal
            start_time: Workflow start time
        
        Returns:
            ResearchResult with aggregated findings
        """
        execution_time = time.time() - start_time
        
        # Extract data from agent outputs
        research_output = self.agent_outputs.get("research_agent")
        analyst_output = self.agent_outputs.get("analyst_agent")
        strategy_output = self.agent_outputs.get("strategy_agent")
        
        # Build insights
        insights = []
        if research_output:
            summary = research_output.results.get("summary", "")
            if summary:
                insights.append(f"Research: {summary}")
        
        if analyst_output:
            analyst_insights = analyst_output.results.get("insights", [])
            for insight in analyst_insights:
                if isinstance(insight, dict):
                    insights.append(insight.get("insight", ""))
        
        # Build sources
        sources = []
        if research_output and research_output.sources:
            for url in research_output.sources:
                sources.append({
                    "url": url,
                    "type": "web",
                    "reliability": "high" if any(d in url for d in [".edu", ".gov", ".org"]) else "medium"
                })
        
        # Calculate overall confidence
        confidence_scores_dict = {}
        for agent_name, score in self.confidence_scores.items():
            confidence_scores_dict[agent_name] = {
                "overall": int(score.overall * 100),
                **{k: int(v * 100) for k, v in score.factors.items()}
            }
        
        overall_confidence = int(
            (sum(score.overall for score in self.confidence_scores.values()) / len(self.confidence_scores))
            * 100
            if self.confidence_scores else 0
        )
        
        # Create result
        result = ResearchResult(
            session_id=self.session_id,
            goal=goal,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            agents_involved=list(self.agent_outputs.keys()),
            confidence_scores=confidence_scores_dict,
            competitors=[],  # Not implemented in this version
            insights=insights,
            sources=sources,
            recommendations=strategy_output.results.get("recommendations", []) if strategy_output else [],
            overall_confidence=overall_confidence
        )
        
        return result
    
    def _create_error_result(self, goal: str, error_message: str) -> ResearchResult:
        """
        Create error result when workflow fails
        
        Args:
            goal: Original research goal
            error_message: Error description
        
        Returns:
            ResearchResult with error information
        """
        # Build confidence scores dict
        confidence_scores_dict = {}
        for agent_name, score in self.confidence_scores.items():
            confidence_scores_dict[agent_name] = {
                "overall": int(score.overall * 100),
                **{k: int(v * 100) for k, v in score.factors.items()}
            }
        
        return ResearchResult(
            session_id=self.session_id or str(uuid.uuid4()),
            goal=goal,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            agents_involved=list(self.agent_outputs.keys()),
            confidence_scores=confidence_scores_dict,
            competitors=[],
            insights=[f"Error: {error_message}"],
            sources=[],
            recommendations=[],
            overall_confidence=0
        )
    
    def get_workflow_state(self) -> Dict[str, Any]:
        """
        Get current workflow state
        
        Returns:
            Dictionary with workflow state information
        """
        return {
            "session_id": self.session_id,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "active_agent": self.active_agent,
            "completed_agents": list(self.agent_outputs.keys()),
            "confidence_scores": {
                agent_name: score.overall
                for agent_name, score in self.confidence_scores.items()
            }
        }
    
    def reset(self):
        """Reset workflow state for new execution"""
        self.current_phase = None
        self.active_agent = None
        self.agent_outputs = {}
        self.confidence_scores = {}
        self.session_id = None
        
        # Reset agent retry counts
        self.research_agent.reset_retry_count()
        self.analyst_agent.reset_retry_count()
        self.strategy_agent.reset_retry_count()
