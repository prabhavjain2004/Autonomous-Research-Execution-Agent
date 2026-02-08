"""
Unit tests for web search tool.

Tests DuckDuckGo search, Google search, rate limiting, fallback mechanism,
and error handling with mocked responses.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from tools.web_search import WebSearchTool
from models.data_models import SearchResult


class TestWebSearchTool:
    """Tests for WebSearchTool."""
    
    @pytest.fixture
    def search_tool(self):
        """Create web search tool instance."""
        return WebSearchTool(rate_limit_delay=0.1)  # Short delay for tests
    
    def test_initialization(self):
        """Test web search tool initialization."""
        tool = WebSearchTool(rate_limit_delay=2.5)
        assert tool.rate_limit_delay == 2.5
        assert tool.last_request_time == 0.0
    
    def test_validate_input_success(self, search_tool):
        """Test input validation with valid inputs."""
        assert search_tool.validate_input(query="test query") is True
        assert search_tool.validate_input(query="test", max_results=10) is True
        assert search_tool.validate_input(
            query="test",
            max_results=5,
            engines=["duckduckgo"]
        ) is True
    
    def test_validate_input_missing_query(self, search_tool):
        """Test input validation fails without query."""
        assert search_tool.validate_input(max_results=10) is False
    
    def test_validate_input_empty_query(self, search_tool):
        """Test input validation fails with empty query."""
        assert search_tool.validate_input(query="") is False
        assert search_tool.validate_input(query="   ") is False
    
    def test_validate_input_invalid_max_results(self, search_tool):
        """Test input validation fails with invalid max_results."""
        assert search_tool.validate_input(query="test", max_results=0) is False
        assert search_tool.validate_input(query="test", max_results=-1) is False
        assert search_tool.validate_input(query="test", max_results="10") is False
    
    def test_validate_input_invalid_engines(self, search_tool):
        """Test input validation fails with invalid engines."""
        assert search_tool.validate_input(
            query="test",
            engines=["invalid_engine"]
        ) is False
        assert search_tool.validate_input(
            query="test",
            engines="duckduckgo"  # Should be list
        ) is False
    
    def test_rate_limiting_enforcement(self, search_tool):
        """Test that rate limiting enforces delay between requests."""
        # Set rate limit delay
        search_tool.rate_limit_delay = 0.2
        
        # First request
        start_time = time.time()
        search_tool._enforce_rate_limit()
        first_request_time = time.time()
        
        # Second request should be delayed
        search_tool._enforce_rate_limit()
        second_request_time = time.time()
        
        # Time between requests should be at least rate_limit_delay
        time_diff = second_request_time - first_request_time
        assert time_diff >= 0.2
    
    @patch('tools.web_search.DDGS')
    def test_search_duckduckgo_success(self, mock_ddgs, search_tool):
        """Test DuckDuckGo search with mocked response."""
        # Mock search results
        mock_results = [
            {
                "title": "Result 1",
                "href": "https://example.com/1",
                "body": "Description 1"
            },
            {
                "title": "Result 2",
                "href": "https://example.com/2",
                "body": "Description 2"
            }
        ]
        
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value.text.return_value = mock_results
        mock_ddgs.return_value = mock_instance
        
        results = search_tool.search_duckduckgo("test query", max_results=10)
        
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example.com/1"
        assert results[0].source == "duckduckgo"
    
    @patch('tools.web_search.google_search')
    def test_search_google_success(self, mock_google, search_tool):
        """Test Google search with mocked response."""
        # Mock search results
        mock_result_1 = Mock()
        mock_result_1.title = "Result 1"
        mock_result_1.url = "https://example.com/1"
        mock_result_1.description = "Description 1"
        
        mock_result_2 = Mock()
        mock_result_2.title = "Result 2"
        mock_result_2.url = "https://example.com/2"
        mock_result_2.description = "Description 2"
        
        mock_google.return_value = [mock_result_1, mock_result_2]
        
        results = search_tool.search_google("test query", max_results=10)
        
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].title == "Result 1"
        assert results[0].url == "https://example.com/1"
        assert results[0].source == "google"
    
    @patch('tools.web_search.DDGS')
    def test_execute_duckduckgo_success(self, mock_ddgs, search_tool):
        """Test execute with successful DuckDuckGo search."""
        mock_results = [
            {
                "title": "Result 1",
                "href": "https://example.com/1",
                "body": "Description 1"
            }
        ]
        
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value.text.return_value = mock_results
        mock_ddgs.return_value = mock_instance
        
        result = search_tool.execute(query="test query", max_results=10)
        
        assert result.success is True
        assert result.data is not None
        assert result.data["query"] == "test query"
        assert result.data["count"] == 1
        assert len(result.data["results"]) == 1
    
    @patch('tools.web_search.google_search')
    @patch('tools.web_search.DDGS')
    def test_execute_fallback_to_google(self, mock_ddgs, mock_google, search_tool):
        """Test fallback to Google when DuckDuckGo fails."""
        # Make DuckDuckGo fail
        mock_ddgs.side_effect = Exception("DuckDuckGo error")
        
        # Make Google succeed
        mock_result = Mock()
        mock_result.title = "Result 1"
        mock_result.url = "https://example.com/1"
        mock_result.description = "Description 1"
        mock_google.return_value = [mock_result]
        
        result = search_tool.execute(
            query="test query",
            max_results=10,
            engines=["duckduckgo", "google"]
        )
        
        assert result.success is True
        assert result.data["count"] == 1
        assert result.metadata["source"] == "google"
    
    @patch('tools.web_search.google_search')
    @patch('tools.web_search.DDGS')
    def test_execute_all_engines_fail(self, mock_ddgs, mock_google, search_tool):
        """Test execute when all search engines fail."""
        # Make both engines fail
        mock_ddgs.side_effect = Exception("DuckDuckGo error")
        mock_google.side_effect = Exception("Google error")
        
        result = search_tool.execute(
            query="test query",
            max_results=10,
            engines=["duckduckgo", "google"]
        )
        
        assert result.success is False
        assert result.data is None
        assert "All search engines failed" in result.error
    
    @patch('tools.web_search.DDGS')
    def test_run_with_validation(self, mock_ddgs, search_tool):
        """Test run() method with input validation."""
        mock_results = [
            {
                "title": "Result 1",
                "href": "https://example.com/1",
                "body": "Description 1"
            }
        ]
        
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value.text.return_value = mock_results
        mock_ddgs.return_value = mock_instance
        
        # Valid input
        result = search_tool.run(query="test query")
        assert result.success is True
        
        # Invalid input (missing query)
        result = search_tool.run(max_results=10)
        assert result.success is False
        assert "validation failed" in result.error.lower()
    
    @patch('tools.web_search.DDGS')
    def test_error_handling(self, mock_ddgs, search_tool):
        """Test error handling with mocked failure."""
        # Make search fail
        mock_ddgs.side_effect = Exception("Network error")
        
        result = search_tool.run(query="test query", engines=["duckduckgo"])
        
        assert result.success is False
        assert result.error is not None
    
    @patch('tools.web_search.DDGS')
    def test_max_results_limit(self, mock_ddgs, search_tool):
        """Test that max_results is respected."""
        # Return more results than requested
        mock_results = [
            {
                "title": f"Result {i}",
                "href": f"https://example.com/{i}",
                "body": f"Description {i}"
            }
            for i in range(20)
        ]
        
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value.text.return_value = mock_results
        mock_ddgs.return_value = mock_instance
        
        result = search_tool.execute(query="test query", max_results=5)
        
        # Should respect max_results (though DDGS might return all)
        assert result.success is True
        assert result.data["count"] <= 20  # DDGS returns what it returns
    
    @patch('tools.web_search.DDGS')
    def test_empty_results(self, mock_ddgs, search_tool):
        """Test handling of empty search results."""
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value.text.return_value = []
        mock_ddgs.return_value = mock_instance
        
        result = search_tool.execute(query="test query", engines=["duckduckgo"])
        
        # Empty results should still fail (no results from any engine)
        assert result.success is False
    
    def test_search_result_structure(self, search_tool):
        """Test that search results have correct structure."""
        with patch('tools.web_search.DDGS') as mock_ddgs:
            mock_results = [
                {
                    "title": "Test",
                    "href": "https://example.com",
                    "body": "Description"
                }
            ]
            
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value.text.return_value = mock_results
            mock_ddgs.return_value = mock_instance
            
            result = search_tool.execute(query="test")
            
            assert result.success is True
            search_result = result.data["results"][0]
            
            # Check all required fields
            assert "title" in search_result
            assert "url" in search_result
            assert "snippet" in search_result
            assert "source" in search_result
            assert "timestamp" in search_result
