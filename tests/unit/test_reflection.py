"""
Unit tests for reflection and evaluation module
"""

import pytest
from evaluation.reflection import (
    ReflectionModule,
    ConfidenceScore,
    AgentType
)
from models.data_models import AgentOutput


class TestConfidenceScore:
    """Tests for ConfidenceScore dataclass"""
    
    def test_valid_confidence_score(self):
        """Test creating a valid confidence score"""
        score = ConfidenceScore(
            overall=0.75,
            factors={"factor1": 0.8, "factor2": 0.7},
            agent_type=AgentType.RESEARCH,
            reasoning="Test reasoning"
        )
        assert score.overall == 0.75
        assert score.factors["factor1"] == 0.8
        assert score.agent_type == AgentType.RESEARCH
    
    def test_overall_score_bounds_validation(self):
        """Test that overall score must be between 0.0 and 1.0"""
        with pytest.raises(ValueError, match="Overall confidence must be between"):
            ConfidenceScore(
                overall=1.5,
                factors={},
                agent_type=AgentType.RESEARCH,
                reasoning="Test"
            )
        
        with pytest.raises(ValueError, match="Overall confidence must be between"):
            ConfidenceScore(
                overall=-0.1,
                factors={},
                agent_type=AgentType.RESEARCH,
                reasoning="Test"
            )
    
    def test_factor_score_bounds_validation(self):
        """Test that factor scores must be between 0.0 and 1.0"""
        with pytest.raises(ValueError, match="Factor .* must be between"):
            ConfidenceScore(
                overall=0.5,
                factors={"bad_factor": 1.5},
                agent_type=AgentType.RESEARCH,
                reasoning="Test"
            )
    
    def test_to_dict(self):
        """Test serialization to dictionary"""
        score = ConfidenceScore(
            overall=0.75,
            factors={"factor1": 0.8},
            agent_type=AgentType.ANALYST,
            reasoning="Test reasoning"
        )
        data = score.to_dict()
        
        assert data["overall"] == 0.75
        assert data["factors"]["factor1"] == 0.8
        assert data["agent_type"] == "analyst"
        assert data["reasoning"] == "Test reasoning"
    
    def test_from_dict(self):
        """Test deserialization from dictionary"""
        data = {
            "overall": 0.75,
            "factors": {"factor1": 0.8},
            "agent_type": "strategy",
            "reasoning": "Test reasoning"
        }
        score = ConfidenceScore.from_dict(data)
        
        assert score.overall == 0.75
        assert score.factors["factor1"] == 0.8
        assert score.agent_type == AgentType.STRATEGY
        assert score.reasoning == "Test reasoning"


class TestReflectionModule:
    """Tests for ReflectionModule"""
    
    def test_initialization_with_defaults(self):
        """Test initialization with default thresholds"""
        module = ReflectionModule()
        assert module.high_confidence_threshold == 0.75
        assert module.low_confidence_threshold == 0.50
        assert module.min_acceptable_confidence == 0.40
    
    def test_initialization_with_custom_thresholds(self):
        """Test initialization with custom thresholds"""
        module = ReflectionModule(
            high_confidence_threshold=0.80,
            low_confidence_threshold=0.60,
            min_acceptable_confidence=0.45
        )
        assert module.high_confidence_threshold == 0.80
        assert module.low_confidence_threshold == 0.60
        assert module.min_acceptable_confidence == 0.45
    
    def test_invalid_threshold_bounds(self):
        """Test that thresholds must be between 0.0 and 1.0"""
        with pytest.raises(ValueError):
            ReflectionModule(high_confidence_threshold=1.5)
        
        with pytest.raises(ValueError):
            ReflectionModule(low_confidence_threshold=-0.1)
    
    def test_invalid_threshold_ordering(self):
        """Test that low threshold must be less than high threshold"""
        with pytest.raises(ValueError, match="low_confidence_threshold must be less than"):
            ReflectionModule(
                high_confidence_threshold=0.50,
                low_confidence_threshold=0.75
            )
    
    def test_calculate_research_confidence_high_quality(self):
        """Test research confidence calculation with high-quality output"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="research_agent",
            task_id="task_001",
            results={"findings": "Machine learning trends show significant growth. " * 20},
            self_confidence=85,
            reasoning="Comprehensive research completed",
            sources=[
                "https://example.edu/ml",
                "https://example.gov/ai",
                "https://example.org/research",
                "https://example.com/tech",
                "https://example.io/data"
            ],
            execution_time=5.0
        )
        
        score = module.calculate_self_confidence(
            output, 
            AgentType.RESEARCH,
            task_description="research machine learning trends"
        )
        
        assert isinstance(score, ConfidenceScore)
        assert 0.0 <= score.overall <= 1.0
        assert score.agent_type == AgentType.RESEARCH
        assert "source_count" in score.factors
        assert "source_reliability" in score.factors
        assert "completeness" in score.factors
        assert "relevance" in score.factors
        assert score.overall > 0.6  # Should be high quality
    
    def test_calculate_research_confidence_low_quality(self):
        """Test research confidence calculation with low-quality output"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="research_agent",
            task_id="task_002",
            results={"findings": "Short content"},
            self_confidence=30,
            reasoning="Limited research",
            sources=[],
            execution_time=1.0
        )
        
        score = module.calculate_self_confidence(
            output,
            AgentType.RESEARCH,
            task_description="research quantum computing"
        )
        
        assert score.overall < 0.5  # Should be low quality
        assert score.factors["source_count"] == 0.0
        assert score.factors["source_reliability"] == 0.0
    
    def test_calculate_analyst_confidence_high_quality(self):
        """Test analyst confidence calculation with high-quality output"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="analyst_agent",
            task_id="task_003",
            results={
                "analysis": "1. First insight\n2. Second insight\n3. Third insight",
                "patterns": "Clear growth pattern identified"
            },
            self_confidence=80,
            reasoning=(
                "The data shows a clear pattern of growth. "
                "This indicates strong market demand. "
                "Therefore, we can conclude positive trends. "
                "Evidence demonstrates correlation between marketing and sales."
            ),
            sources=["internal_data.csv"],
            execution_time=3.0
        )
        
        score = module.calculate_self_confidence(
            output,
            AgentType.ANALYST,
            task_description="analyze sales data"
        )
        
        assert isinstance(score, ConfidenceScore)
        assert score.agent_type == AgentType.ANALYST
        assert "insight_depth" in score.factors
        assert "consistency" in score.factors
        assert "pattern_clarity" in score.factors
        assert "evidence_strength" in score.factors
        assert score.overall > 0.6  # Should be high quality
    
    def test_calculate_analyst_confidence_with_contradictions(self):
        """Test analyst confidence with contradictory content"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="analyst_agent",
            task_id="task_004",
            results={"analysis": "Growth is strong"},
            self_confidence=50,
            reasoning="Growth is strong. However, there are concerns. But also contradicts previous data.",
            sources=[],
            execution_time=2.0
        )
        
        score = module.calculate_self_confidence(output, AgentType.ANALYST)
        
        # Consistency should be lower due to contradiction indicators
        assert score.factors["consistency"] < 1.0
    
    def test_calculate_strategy_confidence_high_quality(self):
        """Test strategy confidence calculation with high-quality output"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="strategy_agent",
            task_id="task_005",
            results={
                "strategy": "Comprehensive marketing plan",
                "steps": ["Step 1: Create campaign", "Step 2: Execute deployment"]
            },
            self_confidence=85,
            reasoning=(
                "Step 1: Create comprehensive marketing campaign. "
                "Action: Develop social media strategy. "
                "Implement A/B testing timeline. "
                "Execute deployment by Q2. "
                "Build analytics dashboard. "
                "Design user feedback system. "
                "This approach is realistic and achievable for marketing goals."
            ),
            sources=[],
            execution_time=4.0
        )
        
        score = module.calculate_self_confidence(
            output,
            AgentType.STRATEGY,
            task_description="create marketing strategy plan"
        )
        
        assert isinstance(score, ConfidenceScore)
        assert score.agent_type == AgentType.STRATEGY
        assert "specificity" in score.factors
        assert "actionability" in score.factors
        assert "alignment" in score.factors
        assert "feasibility" in score.factors
        assert score.overall > 0.6  # Should be high quality
    
    def test_calculate_strategy_confidence_low_quality(self):
        """Test strategy confidence with vague content"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="strategy_agent",
            task_id="task_006",
            results={"strategy": "We should do better"},
            self_confidence=30,
            reasoning="We should do better and try harder.",
            sources=[],
            execution_time=1.0
        )
        
        score = module.calculate_self_confidence(
            output,
            AgentType.STRATEGY,
            task_description="improve sales"
        )
        
        assert score.overall < 0.5  # Should be low quality
        assert score.factors["specificity"] < 0.5
        assert score.factors["actionability"] < 0.5
    
    def test_calculate_confidence_unknown_agent_type(self):
        """Test that unknown agent type raises error"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="test_agent",
            task_id="task_007",
            results={},
            self_confidence=50,
            reasoning="test",
            sources=[],
            execution_time=1.0
        )
        
        # Create a mock agent type that doesn't exist
        with pytest.raises(ValueError, match="Unknown agent type"):
            # We need to bypass the enum validation
            class FakeAgentType:
                pass
            module.calculate_self_confidence(output, FakeAgentType())
    
    def test_evaluate_output_high_confidence(self):
        """Test evaluation with high confidence score"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="test_agent",
            task_id="task_008",
            results={},
            self_confidence=85,
            reasoning="test",
            sources=[],
            execution_time=1.0
        )
        score = ConfidenceScore(
            overall=0.85,
            factors={},
            agent_type=AgentType.RESEARCH,
            reasoning="High quality"
        )
        
        decision = module.evaluate_output(output, score)
        
        assert decision["should_proceed"] is True
        assert decision["should_replan"] is False
        assert decision["should_error_recover"] is False
        assert decision["confidence"] == 0.85
        assert "High confidence" in decision["reasoning"]
    
    def test_evaluate_output_moderate_confidence(self):
        """Test evaluation with moderate confidence score"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="test_agent",
            task_id="task_009",
            results={},
            self_confidence=65,
            reasoning="test",
            sources=[],
            execution_time=1.0
        )
        score = ConfidenceScore(
            overall=0.65,
            factors={},
            agent_type=AgentType.ANALYST,
            reasoning="Moderate quality"
        )
        
        decision = module.evaluate_output(output, score)
        
        assert decision["should_proceed"] is True
        assert decision["should_replan"] is False
        assert decision["should_error_recover"] is False
        assert "Moderate confidence" in decision["reasoning"]
    
    def test_evaluate_output_low_confidence(self):
        """Test evaluation with low confidence score"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="test_agent",
            task_id="task_010",
            results={},
            self_confidence=45,
            reasoning="test",
            sources=[],
            execution_time=1.0
        )
        score = ConfidenceScore(
            overall=0.45,
            factors={},
            agent_type=AgentType.STRATEGY,
            reasoning="Low quality"
        )
        
        decision = module.evaluate_output(output, score)
        
        assert decision["should_proceed"] is False
        assert decision["should_replan"] is True
        assert decision["should_error_recover"] is False
        assert "Low confidence" in decision["reasoning"]
    
    def test_evaluate_output_unacceptable_confidence(self):
        """Test evaluation with unacceptable confidence score"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="test_agent",
            task_id="task_011",
            results={},
            self_confidence=25,
            reasoning="test",
            sources=[],
            execution_time=1.0
        )
        score = ConfidenceScore(
            overall=0.25,
            factors={},
            agent_type=AgentType.RESEARCH,
            reasoning="Very poor quality"
        )
        
        decision = module.evaluate_output(output, score)
        
        assert decision["should_proceed"] is False
        assert decision["should_replan"] is False
        assert decision["should_error_recover"] is True
        assert "Unacceptable confidence" in decision["reasoning"]
    
    def test_should_replan_low_confidence(self):
        """Test replanning decision with low confidence"""
        module = ReflectionModule()
        score = ConfidenceScore(
            overall=0.45,
            factors={},
            agent_type=AgentType.RESEARCH,
            reasoning="Low"
        )
        
        assert module.should_replan(score, retry_count=0, max_retries=3) is True
    
    def test_should_replan_high_confidence(self):
        """Test replanning decision with high confidence"""
        module = ReflectionModule()
        score = ConfidenceScore(
            overall=0.85,
            factors={},
            agent_type=AgentType.RESEARCH,
            reasoning="High"
        )
        
        assert module.should_replan(score, retry_count=0, max_retries=3) is False
    
    def test_should_replan_max_retries_reached(self):
        """Test that replanning is not triggered when max retries reached"""
        module = ReflectionModule()
        score = ConfidenceScore(
            overall=0.45,
            factors={},
            agent_type=AgentType.RESEARCH,
            reasoning="Low"
        )
        
        # Even with low confidence, should not replan if retries exhausted
        assert module.should_replan(score, retry_count=3, max_retries=3) is False
    
    def test_confidence_score_reasoning_generation(self):
        """Test that reasoning is generated correctly"""
        module = ReflectionModule()
        output = AgentOutput(
            agent_name="research_agent",
            task_id="task_012",
            results={"findings": "test content with relevant keywords"},
            self_confidence=70,
            reasoning="test",
            sources=["https://example.edu/test"],
            execution_time=2.0
        )
        
        score = module.calculate_self_confidence(
            output,
            AgentType.RESEARCH,
            task_description="test task"
        )
        
        assert len(score.reasoning) > 0
        assert "research" in score.reasoning.lower()
    
    def test_all_confidence_factors_in_range(self):
        """Test that all confidence factors are within valid range"""
        module = ReflectionModule()
        
        # Test with various outputs
        outputs = [
            (AgentOutput(
                agent_name="research_agent",
                task_id="task_013",
                results={"findings": "x" * 500},
                self_confidence=70,
                reasoning="test",
                sources=["test.edu"],
                execution_time=2.0
            ), AgentType.RESEARCH, "research"),
            (AgentOutput(
                agent_name="analyst_agent",
                task_id="task_014",
                results={"analysis": "shows evidence indicates"},
                self_confidence=70,
                reasoning="test",
                sources=[],
                execution_time=2.0
            ), AgentType.ANALYST, "analyze"),
            (AgentOutput(
                agent_name="strategy_agent",
                task_id="task_015",
                results={"strategy": "step action implement"},
                self_confidence=70,
                reasoning="test",
                sources=[],
                execution_time=2.0
            ), AgentType.STRATEGY, "strategy")
        ]
        
        for output, agent_type, task_desc in outputs:
            score = module.calculate_self_confidence(output, agent_type, task_desc)
            
            # Check all factors are in valid range
            for factor_name, factor_value in score.factors.items():
                assert 0.0 <= factor_value <= 1.0, f"Factor {factor_name} out of range: {factor_value}"
            
            # Check overall is in valid range
            assert 0.0 <= score.overall <= 1.0
