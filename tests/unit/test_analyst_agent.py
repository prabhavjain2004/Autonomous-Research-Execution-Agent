"""
Unit tests for Analyst Agent
"""

import pytest
from unittest.mock import Mock

from agents.analyst_agent import AnalystAgent
from agents.base_agent import AgentContext
from models.data_models import AgentOutput
from evaluation.reflection import ConfidenceScore, AgentType


class TestAnalystAgent:
    """Tests for AnalystAgent"""
    
    def test_initialization(self):
        """Test initializing analyst agent"""
        agent = AnalystAgent(
            agent_name="test_analyst",
            max_retries=5,
            enable_code_execution=True
        )
        
        assert agent.agent_name == "test_analyst"
        assert agent.agent_type == AgentType.ANALYST
        assert agent.max_retries == 5
        assert agent.enable_code_execution is True
    
    def test_initialization_with_defaults(self):
        """Test initialization with default values"""
        agent = AnalystAgent()
        
        assert agent.agent_name == "analyst_agent"
        assert agent.enable_code_execution is True
    
    def test_execute_with_previous_outputs(self):
        """Test execution with previous agent outputs"""
        agent = AnalystAgent()
        
        # Create mock previous output
        research_output = AgentOutput(
            agent_name="research_agent",
            task_id="task_001",
            results={
                "query": "test query",
                "sources": [
                    {"url": "https://example.edu/1", "title": "Test 1"},
                    {"url": "https://example.com/2", "title": "Test 2"}
                ],
                "total_sources": 2
            },
            self_confidence=75,
            reasoning="Research completed",
            sources=["https://example.edu/1", "https://example.com/2"],
            execution_time=2.0
        )
        
        context = AgentContext(
            task_id="task_002",
            task_description="analyze research findings",
            previous_outputs={"research_agent": research_output}
        )
        
        output = agent.execute(context)
        
        # Verify output
        assert isinstance(output, AgentOutput)
        assert output.agent_name == "analyst_agent"
        assert output.task_id == "task_002"
        assert output.self_confidence > 0
        
        # Verify results structure
        assert "analysis" in output.results
        assert "patterns" in output.results
        assert "insights" in output.results
        assert "data_sources" in output.results
        assert "research_agent" in output.results["data_sources"]
    
    def test_execute_no_previous_outputs(self):
        """Test execution with no previous outputs"""
        agent = AnalystAgent()
        context = AgentContext(
            task_id="task_003",
            task_description="analyze data",
            previous_outputs={}
        )
        
        output = agent.execute(context)
        
        assert output.self_confidence == 20
        assert "No data available" in output.results["analysis"]
        assert len(output.results["insights"]) == 0
        assert len(output.results["patterns"]) == 0
    
    def test_execute_with_logger(self):
        """Test execution with logger"""
        mock_logger = Mock()
        agent = AnalystAgent(logger=mock_logger)
        
        research_output = AgentOutput(
            agent_name="research_agent",
            task_id="task_004",
            results={"data": "test"},
            self_confidence=70,
            reasoning="Test",
            sources=[],
            execution_time=1.0
        )
        
        context = AgentContext(
            task_id="task_005",
            task_description="test analysis",
            previous_outputs={"research_agent": research_output}
        )
        
        output = agent.execute(context)
        
        # Verify logger was called
        assert mock_logger.log_decision.called
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        agent = AnalystAgent()
        output = AgentOutput(
            agent_name="analyst_agent",
            task_id="task_006",
            results={
                "analysis": "Test analysis shows clear patterns",
                "insights": [
                    {"type": "test", "insight": "Test insight"}
                ],
                "patterns": [
                    {"type": "test", "description": "Test pattern"}
                ]
            },
            self_confidence=75,
            reasoning="Analysis completed with insights",
            sources=[],
            execution_time=2.0
        )
        
        score = agent.calculate_confidence(output)
        
        assert isinstance(score, ConfidenceScore)
        assert score.agent_type == AgentType.ANALYST
        assert 0.0 <= score.overall <= 1.0
        assert "insight_depth" in score.factors
        assert "consistency" in score.factors
    
    def test_calculate_confidence_with_logger(self):
        """Test confidence calculation with logger"""
        mock_logger = Mock()
        agent = AnalystAgent(logger=mock_logger)
        output = AgentOutput(
            agent_name="analyst_agent",
            task_id="task_007",
            results={},
            self_confidence=75,
            reasoning="Test",
            sources=[],
            execution_time=2.0
        )
        
        score = agent.calculate_confidence(output)
        
        # Agents no longer log confidence scores directly
        # Only BossAgent logs confidence scores after evaluation
        assert not mock_logger.log_confidence_scores.called
    
    def test_extract_data_from_context(self):
        """Test data extraction from context"""
        agent = AnalystAgent()
        
        output1 = AgentOutput(
            agent_name="agent1",
            task_id="task_008",
            results={"data": "test1"},
            self_confidence=80,
            reasoning="Test1",
            sources=["source1"],
            execution_time=1.0
        )
        
        output2 = AgentOutput(
            agent_name="agent2",
            task_id="task_009",
            results={"data": "test2"},
            self_confidence=70,
            reasoning="Test2",
            sources=["source2"],
            execution_time=1.5
        )
        
        context = AgentContext(
            task_id="task_010",
            task_description="test",
            previous_outputs={
                "agent1": output1,
                "agent2": output2
            }
        )
        
        data = agent._extract_data_from_context(context)
        
        assert len(data) == 2
        assert "agent1" in data
        assert "agent2" in data
        assert data["agent1"]["confidence"] == 80
        assert data["agent2"]["confidence"] == 70
    
    def test_perform_analysis(self):
        """Test analysis performance"""
        agent = AnalystAgent()
        data = {
            "research_agent": {
                "results": {"query": "test", "total_sources": 5},
                "confidence": 75,
                "sources": ["source1"],
                "reasoning": "Test"
            }
        }
        
        analysis = agent._perform_analysis("test task", data)
        
        assert isinstance(analysis, str)
        assert "test task" in analysis
        assert "RESEARCH_AGENT" in analysis  # Agent name is uppercased in output
        assert "75%" in analysis
    
    def test_identify_patterns(self):
        """Test pattern identification"""
        agent = AnalystAgent()
        data = {
            "research_agent": {
                "results": {"data": "test"},
                "confidence": 80,
                "sources": ["https://example.edu/1", "https://example.com/2"],
                "reasoning": "Test"
            },
            "other_agent": {
                "results": {"data": "test2"},
                "confidence": 60,
                "sources": [],
                "reasoning": "Test2"
            }
        }
        
        patterns = agent._identify_patterns(data, "test analysis")
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        
        # Should have confidence pattern
        confidence_patterns = [p for p in patterns if p["type"] == "confidence_pattern"]
        assert len(confidence_patterns) > 0
        
        # Should have data volume pattern
        volume_patterns = [p for p in patterns if p["type"] == "data_volume_pattern"]
        assert len(volume_patterns) > 0
    
    def test_identify_patterns_with_sources(self):
        """Test pattern identification with source reliability"""
        agent = AnalystAgent()
        data = {
            "research_agent": {
                "results": {},
                "confidence": 75,
                "sources": [
                    "https://example.edu/1",
                    "https://example.gov/2",
                    "https://example.com/3"
                ],
                "reasoning": "Test"
            }
        }
        
        patterns = agent._identify_patterns(data, "test")
        
        # Should have source reliability pattern
        reliability_patterns = [p for p in patterns if p["type"] == "source_reliability_pattern"]
        assert len(reliability_patterns) > 0
        
        pattern = reliability_patterns[0]
        assert "details" in pattern
        assert pattern["details"]["total_sources"] == 3
        assert pattern["details"]["reliable_sources"] == 2  # .edu and .gov
    
    def test_generate_insights(self):
        """Test insight generation"""
        agent = AnalystAgent()
        data = {
            "research_agent": {
                "results": {},
                "confidence": 75,
                "sources": [],
                "reasoning": "Test"
            }
        }
        patterns = [
            {
                "type": "confidence_pattern",
                "description": "Test pattern",
                "details": [{"agent": "research_agent", "confidence": 75}]
            }
        ]
        
        insights = agent._generate_insights("test task", data, patterns)
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        # Should have data quality insight
        quality_insights = [i for i in insights if i["type"] == "data_quality"]
        assert len(quality_insights) > 0
        
        # Each insight should have required fields
        for insight in insights:
            assert "type" in insight
            assert "insight" in insight
            assert "recommendation" in insight
    
    def test_generate_insights_high_confidence(self):
        """Test insight generation with high confidence data"""
        agent = AnalystAgent()
        data = {
            "agent1": {"confidence": 85, "results": {}, "sources": [], "reasoning": "Test"},
            "agent2": {"confidence": 90, "results": {}, "sources": [], "reasoning": "Test"}
        }
        patterns = [
            {
                "type": "confidence_pattern",
                "details": [
                    {"agent": "agent1", "confidence": 85},
                    {"agent": "agent2", "confidence": 90}
                ]
            }
        ]
        
        insights = agent._generate_insights("test", data, patterns)
        
        # Should have confidence insight
        conf_insights = [i for i in insights if i["type"] == "confidence_insight"]
        assert len(conf_insights) > 0
    
    def test_generate_insights_reliable_sources(self):
        """Test insight generation with reliable sources"""
        agent = AnalystAgent()
        data = {
            "research_agent": {
                "confidence": 75,
                "results": {},
                "sources": ["https://example.edu/1"],
                "reasoning": "Test"
            }
        }
        patterns = [
            {
                "type": "source_reliability_pattern",
                "details": {
                    "total_sources": 2,
                    "reliable_sources": 2,
                    "reliability_ratio": 1.0
                }
            }
        ]
        
        insights = agent._generate_insights("test", data, patterns)
        
        # Should have reliability insight
        rel_insights = [i for i in insights if i["type"] == "reliability_insight"]
        assert len(rel_insights) > 0
    
    def test_get_quality_recommendation_high(self):
        """Test quality recommendation for high confidence"""
        agent = AnalystAgent()
        recommendation = agent._get_quality_recommendation(80.0)
        
        assert "sufficient" in recommendation.lower()
    
    def test_get_quality_recommendation_moderate(self):
        """Test quality recommendation for moderate confidence"""
        agent = AnalystAgent()
        recommendation = agent._get_quality_recommendation(60.0)
        
        assert "additional data" in recommendation.lower()
    
    def test_get_quality_recommendation_low(self):
        """Test quality recommendation for low confidence"""
        agent = AnalystAgent()
        recommendation = agent._get_quality_recommendation(40.0)
        
        assert "replanning" in recommendation.lower()
    
    def test_estimate_initial_confidence_no_data(self):
        """Test confidence estimation with no insights or patterns"""
        agent = AnalystAgent()
        confidence = agent._estimate_initial_confidence([], [])
        
        assert confidence == 20
    
    def test_estimate_initial_confidence_with_data(self):
        """Test confidence estimation with insights and patterns"""
        agent = AnalystAgent()
        insights = [
            {"type": "test", "insight": "Test 1", "recommendation": "Test"},
            {"type": "test", "insight": "Test 2", "recommendation": "Test"},
            {"type": "test", "insight": "Test 3", "recommendation": "Test"}
        ]
        patterns = [
            {"type": "test", "description": "Pattern 1"},
            {"type": "test", "description": "Pattern 2"}
        ]
        
        confidence = agent._estimate_initial_confidence(insights, patterns)
        
        assert 20 < confidence <= 100
    
    def test_generate_reasoning_no_data(self):
        """Test reasoning generation with no data"""
        agent = AnalystAgent()
        reasoning = agent._generate_reasoning([], [])
        
        assert "Insufficient data" in reasoning
    
    def test_generate_reasoning_with_data(self):
        """Test reasoning generation with data"""
        agent = AnalystAgent()
        insights = [{"type": "test", "insight": "Test", "recommendation": "Test"}]
        patterns = [{"type": "test", "description": "Test"}]
        
        reasoning = agent._generate_reasoning(insights, patterns)
        
        assert "1 patterns" in reasoning
        assert "1 insights" in reasoning
    
    def test_execution_time_tracking(self):
        """Test that execution time is tracked"""
        agent = AnalystAgent()
        context = AgentContext(
            task_id="task_011",
            task_description="test",
            previous_outputs={}
        )
        
        output = agent.execute(context)
        
        assert output.execution_time > 0
    
    def test_multiple_previous_outputs(self):
        """Test analysis with multiple previous agent outputs"""
        agent = AnalystAgent()
        
        outputs = {}
        for i in range(3):
            outputs[f"agent_{i}"] = AgentOutput(
                agent_name=f"agent_{i}",
                task_id=f"task_{i}",
                results={"data": f"test_{i}"},
                self_confidence=70 + i * 5,
                reasoning=f"Test {i}",
                sources=[],
                execution_time=1.0
            )
        
        context = AgentContext(
            task_id="task_012",
            task_description="analyze multiple sources",
            previous_outputs=outputs
        )
        
        output = agent.execute(context)
        
        assert len(output.results["data_sources"]) == 3
        assert output.results["total_insights"] > 0
