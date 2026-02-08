"""
Unit tests for Research Agent
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from agents.research_agent import ResearchAgent
from agents.base_agent import AgentContext
from models.data_models import AgentOutput, ToolResult
from evaluation.reflection import ConfidenceScore, AgentType


class TestResearchAgent:
    """Tests for ResearchAgent"""
    
    def test_initialization(self):
        """Test initializing research agent"""
        agent = ResearchAgent(
            agent_name="test_research",
            max_retries=5,
            max_search_results=10,
            max_scrape_attempts=5
        )
        
        assert agent.agent_name == "test_research"
        assert agent.agent_type == AgentType.RESEARCH
        assert agent.max_retries == 5
        assert agent.max_search_results == 10
        assert agent.max_scrape_attempts == 5
    
    def test_initialization_with_defaults(self):
        """Test initialization with default values"""
        agent = ResearchAgent()
        
        assert agent.agent_name == "research_agent"
        assert agent.max_search_results == 5
        assert agent.max_scrape_attempts == 3
    
    def test_initialization_invalid_max_search_results(self):
        """Test that invalid max_search_results raises error"""
        with pytest.raises(ValueError, match="max_search_results must be at least 1"):
            ResearchAgent(max_search_results=0)
    
    def test_initialization_invalid_max_scrape_attempts(self):
        """Test that invalid max_scrape_attempts raises error"""
        with pytest.raises(ValueError, match="max_scrape_attempts must be at least 1"):
            ResearchAgent(max_scrape_attempts=0)
    
    @patch('agents.research_agent.WebSearchTool')
    @patch('agents.research_agent.WebScraperTool')
    def test_execute_successful_research(self, mock_scraper_class, mock_search_class):
        """Test successful research execution"""
        # Setup mocks
        mock_search = Mock()
        mock_search_class.return_value = mock_search
        mock_search.run.return_value = ToolResult(
            success=True,
            data={
                "results": [
                    {
                        "url": "https://example.com/1",
                        "title": "Test Article 1",
                        "snippet": "Test snippet 1"
                    },
                    {
                        "url": "https://example.com/2",
                        "title": "Test Article 2",
                        "snippet": "Test snippet 2"
                    }
                ]
            },
            error=None
        )
        
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.run.return_value = ToolResult(
            success=True,
            data={"content": "Scraped content from the article"},
            error=None
        )
        
        # Create agent and execute
        agent = ResearchAgent()
        context = AgentContext(
            task_id="task_001",
            task_description="research machine learning trends"
        )
        
        output = agent.execute(context)
        
        # Verify output
        assert isinstance(output, AgentOutput)
        assert output.agent_name == "research_agent"
        assert output.task_id == "task_001"
        assert output.self_confidence > 0
        assert len(output.sources) == 2
        assert "https://example.com/1" in output.sources
        assert "https://example.com/2" in output.sources
        
        # Verify results structure
        assert "query" in output.results
        assert "summary" in output.results
        assert "sources" in output.results
        assert output.results["total_sources"] == 2
    
    @patch('agents.research_agent.WebSearchTool')
    @patch('agents.research_agent.WebScraperTool')
    def test_execute_no_search_results(self, mock_scraper_class, mock_search_class):
        """Test execution when search returns no results"""
        mock_search = Mock()
        mock_search_class.return_value = mock_search
        mock_search.run.return_value = ToolResult(
            success=True,
            data={"results": []},
            error=None
        )
        
        agent = ResearchAgent()
        context = AgentContext(
            task_id="task_002",
            task_description="obscure topic with no results"
        )
        
        output = agent.execute(context)
        
        assert output.self_confidence == 20
        assert len(output.sources) == 0
        assert "No relevant sources found" in output.results["findings"]
    
    @patch('agents.research_agent.WebSearchTool')
    @patch('agents.research_agent.WebScraperTool')
    def test_execute_search_failure(self, mock_scraper_class, mock_search_class):
        """Test execution when search fails"""
        mock_search = Mock()
        mock_search_class.return_value = mock_search
        mock_search.run.return_value = ToolResult(
            success=False,
            data=None,
            error="Search API error"
        )
        
        agent = ResearchAgent()
        context = AgentContext(
            task_id="task_003",
            task_description="test query"
        )
        
        output = agent.execute(context)
        
        assert output.self_confidence == 20
        assert len(output.sources) == 0
    
    @patch('agents.research_agent.WebSearchTool')
    @patch('agents.research_agent.WebScraperTool')
    def test_execute_scraping_failures(self, mock_scraper_class, mock_search_class):
        """Test execution when scraping fails"""
        mock_search = Mock()
        mock_search_class.return_value = mock_search
        mock_search.run.return_value = ToolResult(
            success=True,
            data={
                "results": [
                    {"url": "https://example.com/1", "title": "Test", "snippet": "Test"}
                ]
            },
            error=None
        )
        
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.run.return_value = ToolResult(
            success=False,
            data=None,
            error="Scraping failed"
        )
        
        agent = ResearchAgent()
        context = AgentContext(
            task_id="task_004",
            task_description="test query"
        )
        
        output = agent.execute(context)
        
        # Should still have sources from search
        assert len(output.sources) == 1
        # But no scraped content
        assert output.results["successfully_scraped"] == 0
    
    @patch('agents.research_agent.WebSearchTool')
    @patch('agents.research_agent.WebScraperTool')
    def test_execute_with_logger(self, mock_scraper_class, mock_search_class):
        """Test execution with logger"""
        mock_search = Mock()
        mock_search_class.return_value = mock_search
        mock_search.run.return_value = ToolResult(
            success=True,
            data={"results": [{"url": "https://example.com", "title": "Test", "snippet": "Test"}]},
            error=None
        )
        
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.run.return_value = ToolResult(
            success=True,
            data={"content": "Test content"},
            error=None
        )
        
        mock_logger = Mock()
        agent = ResearchAgent(logger=mock_logger)
        context = AgentContext(
            task_id="task_005",
            task_description="test query"
        )
        
        output = agent.execute(context)
        
        # Verify logger was called
        assert mock_logger.log_decision.called
        assert mock_logger.log_tool_call.called
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        agent = ResearchAgent()
        output = AgentOutput(
            agent_name="research_agent",
            task_id="task_006",
            results={
                "query": "test",
                "sources": [
                    {"url": "https://example.edu/1"},
                    {"url": "https://example.gov/2"}
                ]
            },
            self_confidence=75,
            reasoning="Test",
            sources=["https://example.edu/1", "https://example.gov/2"],
            execution_time=2.0
        )
        
        score = agent.calculate_confidence(output)
        
        assert isinstance(score, ConfidenceScore)
        assert score.agent_type == AgentType.RESEARCH
        assert 0.0 <= score.overall <= 1.0
        assert "source_count" in score.factors
        assert "source_reliability" in score.factors
    
    def test_calculate_confidence_with_logger(self):
        """Test confidence calculation with logger"""
        mock_logger = Mock()
        agent = ResearchAgent(logger=mock_logger)
        output = AgentOutput(
            agent_name="research_agent",
            task_id="task_007",
            results={},
            self_confidence=75,
            reasoning="Test",
            sources=["https://example.com"],
            execution_time=2.0
        )
        
        score = agent.calculate_confidence(output)
        
        # Agents no longer log confidence scores directly
        # Only BossAgent logs confidence scores after evaluation
        assert not mock_logger.log_confidence_scores.called
    
    @patch('agents.research_agent.WebSearchTool')
    @patch('agents.research_agent.WebScraperTool')
    def test_max_scrape_attempts_respected(self, mock_scraper_class, mock_search_class):
        """Test that max_scrape_attempts is respected"""
        mock_search = Mock()
        mock_search_class.return_value = mock_search
        mock_search.run.return_value = ToolResult(
            success=True,
            data={
                "results": [
                    {"url": f"https://example.com/{i}", "title": f"Test {i}", "snippet": "Test"}
                    for i in range(10)  # 10 results
                ]
            },
            error=None
        )
        
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.run.return_value = ToolResult(
            success=True,
            data={"content": "Test content"},
            error=None
        )
        
        agent = ResearchAgent(max_scrape_attempts=3)
        context = AgentContext(
            task_id="task_008",
            task_description="test query"
        )
        
        output = agent.execute(context)
        
        # Should only scrape 3 URLs despite having 10 results
        assert mock_scraper.run.call_count == 3
    
    @patch('agents.research_agent.WebSearchTool')
    @patch('agents.research_agent.WebScraperTool')
    def test_aggregate_findings_structure(self, mock_scraper_class, mock_search_class):
        """Test that aggregated findings have correct structure"""
        mock_search = Mock()
        mock_search_class.return_value = mock_search
        mock_search.run.return_value = ToolResult(
            success=True,
            data={
                "results": [
                    {"url": "https://example.com/1", "title": "Test 1", "snippet": "Snippet 1"}
                ]
            },
            error=None
        )
        
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.run.return_value = ToolResult(
            success=True,
            data={"content": "Full article content here"},
            error=None
        )
        
        agent = ResearchAgent()
        context = AgentContext(
            task_id="task_009",
            task_description="test query"
        )
        
        output = agent.execute(context)
        
        # Verify structure
        assert "query" in output.results
        assert "summary" in output.results
        assert "sources" in output.results
        assert "scraped_content" in output.results
        assert "total_sources" in output.results
        assert "successfully_scraped" in output.results
        
        # Verify source structure
        source = output.results["sources"][0]
        assert "url" in source
        assert "title" in source
        assert "snippet" in source
        assert "has_full_content" in source
    
    def test_estimate_initial_confidence_no_sources(self):
        """Test confidence estimation with no sources"""
        agent = ResearchAgent()
        findings = {
            "total_sources": 0,
            "successfully_scraped": 0
        }
        
        confidence = agent._estimate_initial_confidence(findings)
        
        assert confidence == 20
    
    def test_estimate_initial_confidence_with_sources(self):
        """Test confidence estimation with sources"""
        agent = ResearchAgent()
        findings = {
            "total_sources": 5,
            "successfully_scraped": 3
        }
        
        confidence = agent._estimate_initial_confidence(findings)
        
        assert 20 < confidence <= 100
    
    def test_generate_reasoning_no_sources(self):
        """Test reasoning generation with no sources"""
        agent = ResearchAgent()
        findings = {
            "total_sources": 0,
            "successfully_scraped": 0
        }
        
        reasoning = agent._generate_reasoning(findings)
        
        assert "No sources found" in reasoning
    
    def test_generate_reasoning_with_sources(self):
        """Test reasoning generation with sources"""
        agent = ResearchAgent()
        findings = {
            "total_sources": 5,
            "successfully_scraped": 3
        }
        
        reasoning = agent._generate_reasoning(findings)
        
        assert "5 sources" in reasoning
        assert "3 sources" in reasoning
    
    @patch('agents.research_agent.WebSearchTool')
    @patch('agents.research_agent.WebScraperTool')
    def test_execution_time_tracking(self, mock_scraper_class, mock_search_class):
        """Test that execution time is tracked"""
        mock_search = Mock()
        mock_search_class.return_value = mock_search
        mock_search.run.return_value = ToolResult(
            success=True,
            data={"results": []},
            error=None
        )
        
        agent = ResearchAgent()
        context = AgentContext(
            task_id="task_010",
            task_description="test query"
        )
        
        output = agent.execute(context)
        
        assert output.execution_time > 0
    
    @patch('agents.research_agent.WebSearchTool')
    @patch('agents.research_agent.WebScraperTool')
    def test_content_truncation_in_findings(self, mock_scraper_class, mock_search_class):
        """Test that very long content is truncated in findings"""
        mock_search = Mock()
        mock_search_class.return_value = mock_search
        mock_search.run.return_value = ToolResult(
            success=True,
            data={
                "results": [
                    {"url": "https://example.com/1", "title": "Test", "snippet": "Test"}
                ]
            },
            error=None
        )
        
        # Create very long content
        long_content = "x" * 5000
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.run.return_value = ToolResult(
            success=True,
            data={"content": long_content},
            error=None
        )
        
        agent = ResearchAgent()
        context = AgentContext(
            task_id="task_011",
            task_description="test query"
        )
        
        output = agent.execute(context)
        
        # Content preview should be truncated
        scraped = output.results["scraped_content"][0]
        assert len(scraped["content_preview"]) <= 2000
        assert scraped["content_length"] == 5000
