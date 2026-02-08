"""
Unit tests for Strategy Agent
"""

import pytest
from unittest.mock import Mock

from agents.strategy_agent import StrategyAgent
from agents.base_agent import AgentContext
from models.data_models import AgentOutput
from evaluation.reflection import ConfidenceScore, AgentType


class TestStrategyAgent:
    """Tests for StrategyAgent"""
    
    def test_initialization(self):
        """Test initializing strategy agent"""
        agent = StrategyAgent(
            agent_name="test_strategy",
            max_retries=5,
            max_recommendations=10
        )
        
        assert agent.agent_name == "test_strategy"
        assert agent.agent_type == AgentType.STRATEGY
        assert agent.max_retries == 5
        assert agent.max_recommendations == 10
    
    def test_initialization_with_defaults(self):
        """Test initialization with default values"""
        agent = StrategyAgent()
        
        assert agent.agent_name == "strategy_agent"
        assert agent.max_recommendations == 5
    
    def test_initialization_invalid_max_recommendations(self):
        """Test that invalid max_recommendations raises error"""
        with pytest.raises(ValueError, match="max_recommendations must be at least 1"):
            StrategyAgent(max_recommendations=0)
    
    def test_execute_with_previous_outputs(self):
        """Test execution with previous agent outputs"""
        agent = StrategyAgent()
        
        # Create mock previous outputs
        research_output = AgentOutput(
            agent_name="research_agent",
            task_id="task_001",
            results={
                "summary": "Research findings summary",
                "total_sources": 5
            },
            self_confidence=75,
            reasoning="Research completed",
            sources=["source1"],
            execution_time=2.0
        )
        
        analyst_output = AgentOutput(
            agent_name="analyst_agent",
            task_id="task_002",
            results={
                "insights": [
                    {
                        "type": "data_quality",
                        "insight": "High quality data",
                        "recommendation": "Proceed with implementation"
                    }
                ],
                "patterns": [{"type": "test", "description": "Test pattern"}]
            },
            self_confidence=80,
            reasoning="Analysis completed",
            sources=[],
            execution_time=1.5
        )
        
        context = AgentContext(
            task_id="task_003",
            task_description="create strategic plan",
            previous_outputs={
                "research_agent": research_output,
                "analyst_agent": analyst_output
            }
        )
        
        output = agent.execute(context)
        
        # Verify output
        assert isinstance(output, AgentOutput)
        assert output.agent_name == "strategy_agent"
        assert output.task_id == "task_003"
        assert output.self_confidence > 0
        
        # Verify results structure
        assert "strategy" in output.results
        assert "recommendations" in output.results
        assert "action_plan" in output.results
        assert "feasibility_assessment" in output.results
        assert len(output.results["recommendations"]) > 0
        assert len(output.results["action_plan"]) > 0
    
    def test_execute_no_previous_outputs(self):
        """Test execution with no previous outputs"""
        agent = StrategyAgent()
        context = AgentContext(
            task_id="task_004",
            task_description="create strategy",
            previous_outputs={}
        )
        
        output = agent.execute(context)
        
        assert output.self_confidence == 20
        assert "No previous outputs available" in output.results["strategy"]
        assert len(output.results["recommendations"]) == 0
        assert len(output.results["action_plan"]) == 0
    
    def test_execute_with_logger(self):
        """Test execution with logger"""
        mock_logger = Mock()
        agent = StrategyAgent(logger=mock_logger)
        
        research_output = AgentOutput(
            agent_name="research_agent",
            task_id="task_005",
            results={"data": "test"},
            self_confidence=70,
            reasoning="Test",
            sources=[],
            execution_time=1.0
        )
        
        context = AgentContext(
            task_id="task_006",
            task_description="test strategy",
            previous_outputs={"research_agent": research_output}
        )
        
        output = agent.execute(context)
        
        # Verify logger was called
        assert mock_logger.log_decision.called
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        agent = StrategyAgent()
        output = AgentOutput(
            agent_name="strategy_agent",
            task_id="task_007",
            results={
                "strategy": "Strategic plan with actionable steps",
                "recommendations": [
                    {"title": "Implement solution", "description": "Execute plan"}
                ],
                "action_plan": [
                    {"step": 1, "action": "Review", "timeline": "1 week"}
                ]
            },
            self_confidence=75,
            reasoning="Strategy completed",
            sources=[],
            execution_time=2.0
        )
        
        score = agent.calculate_confidence(output)
        
        assert isinstance(score, ConfidenceScore)
        assert score.agent_type == AgentType.STRATEGY
        assert 0.0 <= score.overall <= 1.0
        assert "specificity" in score.factors
        assert "actionability" in score.factors
    
    def test_review_previous_outputs(self):
        """Test reviewing previous outputs"""
        agent = StrategyAgent()
        
        output1 = AgentOutput(
            agent_name="research_agent",
            task_id="task_008",
            results={"summary": "Research summary"},
            self_confidence=75,
            reasoning="Test",
            sources=[],
            execution_time=1.0
        )
        
        output2 = AgentOutput(
            agent_name="analyst_agent",
            task_id="task_009",
            results={
                "insights": [
                    {"type": "test", "insight": "Test insight", "recommendation": "Test rec"}
                ]
            },
            self_confidence=80,
            reasoning="Test",
            sources=[],
            execution_time=1.0
        )
        
        context = AgentContext(
            task_id="task_010",
            task_description="test",
            previous_outputs={"research_agent": output1, "analyst_agent": output2}
        )
        
        review = agent._review_previous_outputs(context)
        
        assert "agents_reviewed" in review
        assert "key_findings" in review
        assert "insights" in review
        assert "confidence_levels" in review
        assert len(review["agents_reviewed"]) == 2
        assert review["confidence_levels"]["research_agent"] == 75
        assert review["confidence_levels"]["analyst_agent"] == 80
    
    def test_generate_recommendations_high_confidence(self):
        """Test recommendation generation with high confidence"""
        agent = StrategyAgent()
        review = {
            "confidence_levels": {"agent1": 80, "agent2": 85},
            "insights": []
        }
        
        recommendations = agent._generate_template_recommendations("test task", review)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should recommend proceeding with implementation (check string content)
        assert any("proceed" in r.lower() or "implementation" in r.lower() for r in recommendations)
    
    def test_generate_recommendations_low_confidence(self):
        """Test recommendation generation with low confidence"""
        agent = StrategyAgent()
        review = {
            "confidence_levels": {"agent1": 40, "agent2": 35},
            "insights": []
        }
        
        recommendations = agent._generate_template_recommendations("test task", review)
        
        # Should recommend additional research (check string content)
        assert any("research" in r.lower() or "data" in r.lower() for r in recommendations)
    
    def test_generate_recommendations_with_insights(self):
        """Test recommendation generation with insights"""
        agent = StrategyAgent()
        review = {
            "confidence_levels": {"agent1": 70},
            "insights": [
                {
                    "type": "data_quality",
                    "insight": "Good quality",
                    "recommendation": "Proceed with plan"
                }
            ]
        }
        
        recommendations = agent._generate_template_recommendations("test task", review)
        
        # Should include insight-driven recommendations (check string content)
        assert any("proceed with plan" in r.lower() for r in recommendations)
    
    def test_generate_recommendations_respects_max(self):
        """Test that max_recommendations is respected"""
        agent = StrategyAgent(max_recommendations=2)
        review = {
            "confidence_levels": {"agent1": 70},
            "insights": [
                {"type": "test1", "insight": "Test 1", "recommendation": "Rec 1"},
                {"type": "test2", "insight": "Test 2", "recommendation": "Rec 2"},
                {"type": "test3", "insight": "Test 3", "recommendation": "Rec 3"}
            ]
        }
        
        recommendations = agent._generate_template_recommendations("test task", review)
        
        assert len(recommendations) <= 2
    
    def test_create_action_plan(self):
        """Test action plan creation"""
        agent = StrategyAgent()
        recommendations = [
            "Implement high priority recommendation for system improvement",
            "Execute medium priority optimization strategy"
        ]
        review = {"confidence_levels": {"agent1": 75}}
        
        action_plan = agent._create_action_plan("test task", recommendations, review)
        
        assert isinstance(action_plan, list)
        assert len(action_plan) > 0
        
        # Verify action plan structure
        for step in action_plan:
            assert "step" in step
            assert "phase" in step
            assert "action" in step
            assert "description" in step
            assert "timeline" in step
            assert "dependencies" in step
            assert "success_criteria" in step
    
    def test_assess_feasibility_high(self):
        """Test feasibility assessment with high confidence"""
        agent = StrategyAgent()
        recommendations = [{"title": "Test"}]
        review = {"confidence_levels": {"agent1": 85, "agent2": 90}}
        
        feasibility = agent._assess_feasibility(recommendations, review)
        
        assert "overall_score" in feasibility
        assert "level" in feasibility
        assert "factors" in feasibility
        assert "risks" in feasibility
        assert "mitigation_strategies" in feasibility
        assert feasibility["level"] in ["high", "moderate", "low"]
    
    def test_assess_feasibility_low(self):
        """Test feasibility assessment with low confidence"""
        agent = StrategyAgent()
        recommendations = [{"title": f"Test {i}"} for i in range(5)]
        review = {"confidence_levels": {"agent1": 40}}
        
        feasibility = agent._assess_feasibility(recommendations, review)
        
        assert feasibility["overall_score"] < 0.7
    
    def test_identify_risks(self):
        """Test risk identification"""
        agent = StrategyAgent()
        recommendations = [{"title": f"Test {i}"} for i in range(5)]
        review = {"confidence_levels": {"agent1": 50}}
        
        risks = agent._identify_risks(recommendations, review)
        
        assert isinstance(risks, list)
        assert len(risks) > 0
    
    def test_suggest_mitigations_high_feasibility(self):
        """Test mitigation suggestions for high feasibility"""
        agent = StrategyAgent()
        mitigations = agent._suggest_mitigations("high")
        
        assert isinstance(mitigations, list)
        assert len(mitigations) > 0
    
    def test_suggest_mitigations_low_feasibility(self):
        """Test mitigation suggestions for low feasibility"""
        agent = StrategyAgent()
        mitigations = agent._suggest_mitigations("low")
        
        assert isinstance(mitigations, list)
        assert len(mitigations) > 0
        # Low feasibility should have more mitigations
        assert len(mitigations) >= 3
    
    def test_create_strategy_summary(self):
        """Test strategy summary creation"""
        agent = StrategyAgent()
        recommendations = [
            {"priority": "high", "title": "High priority item"},
            {"priority": "medium", "title": "Medium priority item"}
        ]
        
        summary = agent._create_strategy_summary("test task", recommendations)
        
        assert isinstance(summary, str)
        assert "test task" in summary
        assert "High priority item" in summary
    
    def test_estimate_initial_confidence_no_data(self):
        """Test confidence estimation with no data"""
        agent = StrategyAgent()
        confidence = agent._estimate_initial_confidence([], [], {"overall_score": 0.5})
        
        assert confidence == 20
    
    def test_estimate_initial_confidence_with_data(self):
        """Test confidence estimation with data"""
        agent = StrategyAgent()
        recommendations = [{"title": f"Test {i}"} for i in range(3)]
        action_plan = [{"step": i} for i in range(4)]
        feasibility = {"overall_score": 0.8}
        
        confidence = agent._estimate_initial_confidence(
            recommendations,
            action_plan,
            feasibility
        )
        
        assert 20 < confidence <= 100
    
    def test_generate_reasoning_no_data(self):
        """Test reasoning generation with no data"""
        agent = StrategyAgent()
        reasoning = agent._generate_reasoning([], [])
        
        assert "Insufficient data" in reasoning
    
    def test_generate_reasoning_with_data(self):
        """Test reasoning generation with data"""
        agent = StrategyAgent()
        recommendations = [{"title": "Test"}]
        action_plan = [{"step": 1}, {"step": 2}]
        
        reasoning = agent._generate_reasoning(recommendations, action_plan)
        
        assert "1 recommendations" in reasoning
        assert "2-step" in reasoning
    
    def test_execution_time_tracking(self):
        """Test that execution time is tracked"""
        agent = StrategyAgent()
        context = AgentContext(
            task_id="task_011",
            task_description="test",
            previous_outputs={}
        )
        
        output = agent.execute(context)
        
        assert output.execution_time > 0
    
    def test_recommendation_structure(self):
        """Test that recommendations have required structure"""
        agent = StrategyAgent()
        review = {
            "confidence_levels": {"agent1": 75},
            "insights": []
        }
        
        recommendations = agent._generate_template_recommendations("test", review)
        
        # Recommendations are now strings, not dicts
        for rec in recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0
