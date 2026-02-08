"""
Unit tests for web scraper tool.

Tests each scraping method, fallback cascade, timeout handling,
and error handling with mocked responses.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.web_scraper import WebScraperTool


class TestWebScraperTool:
    """Tests for WebScraperTool."""
    
    @pytest.fixture
    def scraper_tool(self):
        """Create web scraper tool instance."""
        return WebScraperTool(timeout=10)
    
    def test_initialization(self):
        """Test web scraper tool initialization."""
        tool = WebScraperTool(timeout=30, use_browser=True)
        assert tool.timeout == 30
        assert tool.use_browser is True
    
    def test_validate_input_success(self, scraper_tool):
        """Test input validation with valid inputs."""
        assert scraper_tool.validate_input(url="https://example.com") is True
        assert scraper_tool.validate_input(
            url="https://example.com",
            method="requests"
        ) is True
    
    def test_validate_input_missing_url(self, scraper_tool):
        """Test input validation fails without URL."""
        assert scraper_tool.validate_input(method="requests") is False
    
    def test_validate_input_empty_url(self, scraper_tool):
        """Test input validation fails with empty URL."""
        assert scraper_tool.validate_input(url="") is False
        assert scraper_tool.validate_input(url="   ") is False
    
    def test_validate_input_invalid_url(self, scraper_tool):
        """Test input validation fails with invalid URL."""
        assert scraper_tool.validate_input(url="not-a-url") is False
        assert scraper_tool.validate_input(url="ftp://example.com") is True  # Valid URL
    
    def test_validate_input_invalid_method(self, scraper_tool):
        """Test input validation fails with invalid method."""
        assert scraper_tool.validate_input(
            url="https://example.com",
            method="invalid_method"
        ) is False
    
    @patch('tools.web_scraper.requests.get')
    def test_scrape_with_requests_success(self, mock_get, scraper_tool):
        """Test scraping with requests + BeautifulSoup."""
        # Mock response
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Heading</h1>
                <p>Test paragraph content.</p>
                <script>console.log('test');</script>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        content = scraper_tool.scrape_with_requests("https://example.com")
        
        assert "Test Heading" in content
        assert "Test paragraph content" in content
        # Script should be removed
        assert "console.log" not in content
    
    @patch('tools.web_scraper.trafilatura.fetch_url')
    @patch('tools.web_scraper.trafilatura.extract')
    def test_scrape_with_trafilatura_success(
        self,
        mock_extract,
        mock_fetch,
        scraper_tool
    ):
        """Test scraping with trafilatura."""
        mock_fetch.return_value = "<html>content</html>"
        mock_extract.return_value = "Extracted content from trafilatura"
        
        content = scraper_tool.scrape_with_trafilatura("https://example.com")
        
        assert content == "Extracted content from trafilatura"
        mock_fetch.assert_called_once()
        mock_extract.assert_called_once()
    
    @patch('tools.web_scraper.Article')
    def test_scrape_with_newspaper_success(self, mock_article_class, scraper_tool):
        """Test scraping with newspaper3k."""
        mock_article = Mock()
        mock_article.text = "Article content from newspaper"
        mock_article_class.return_value = mock_article
        
        content = scraper_tool.scrape_with_newspaper("https://example.com")
        
        assert content == "Article content from newspaper"
        mock_article.download.assert_called_once()
        mock_article.parse.assert_called_once()
    
    @patch('tools.web_scraper.requests.get')
    def test_execute_requests_success(self, mock_get, scraper_tool):
        """Test execute with successful requests scraping."""
        mock_response = Mock()
        mock_response.content = b"<html><body><p>Test content</p></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = scraper_tool.execute(url="https://example.com", method="requests")
        
        assert result.success is True
        assert result.data is not None
        assert "Test content" in result.data["content"]
        assert result.metadata["method"] == "requests"
    
    @patch('tools.web_scraper.trafilatura.extract')
    @patch('tools.web_scraper.trafilatura.fetch_url')
    @patch('tools.web_scraper.requests.get')
    def test_execute_fallback_to_trafilatura(
        self,
        mock_requests,
        mock_fetch,
        mock_extract,
        scraper_tool
    ):
        """Test fallback to trafilatura when requests fails."""
        # Make requests fail
        mock_requests.side_effect = Exception("Connection error")
        
        # Make trafilatura succeed
        mock_fetch.return_value = "<html>content</html>"
        mock_extract.return_value = "Trafilatura content"
        
        result = scraper_tool.execute(url="https://example.com", method="auto")
        
        assert result.success is True
        assert "Trafilatura content" in result.data["content"]
        assert result.metadata["method"] == "trafilatura"
    
    @patch('tools.web_scraper.Article')
    @patch('tools.web_scraper.trafilatura.fetch_url')
    @patch('tools.web_scraper.requests.get')
    def test_execute_fallback_to_newspaper(
        self,
        mock_requests,
        mock_fetch,
        mock_article_class,
        scraper_tool
    ):
        """Test fallback to newspaper when requests and trafilatura fail."""
        # Make requests fail
        mock_requests.side_effect = Exception("Connection error")
        
        # Make trafilatura fail
        mock_fetch.return_value = None
        
        # Make newspaper succeed
        mock_article = Mock()
        mock_article.text = "Newspaper content"
        mock_article_class.return_value = mock_article
        
        result = scraper_tool.execute(url="https://example.com", method="auto")
        
        assert result.success is True
        assert "Newspaper content" in result.data["content"]
        assert result.metadata["method"] == "newspaper"
    
    @patch('tools.web_scraper.Article')
    @patch('tools.web_scraper.trafilatura.fetch_url')
    @patch('tools.web_scraper.requests.get')
    def test_execute_all_methods_fail(
        self,
        mock_requests,
        mock_fetch,
        mock_article_class,
        scraper_tool
    ):
        """Test execute when all scraping methods fail."""
        # Make all methods fail
        mock_requests.side_effect = Exception("Requests error")
        mock_fetch.return_value = None
        
        mock_article = Mock()
        mock_article.text = ""
        mock_article_class.return_value = mock_article
        
        result = scraper_tool.execute(url="https://example.com", method="auto")
        
        assert result.success is False
        assert result.data is None
        assert "All scraping methods failed" in result.error
    
    @patch('tools.web_scraper.requests.get')
    def test_run_with_validation(self, mock_get, scraper_tool):
        """Test run() method with input validation."""
        mock_response = Mock()
        mock_response.content = b"<html><body>Content</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Valid input
        result = scraper_tool.run(url="https://example.com")
        assert result.success is True
        
        # Invalid input (missing URL)
        result = scraper_tool.run(method="requests")
        assert result.success is False
        assert "validation failed" in result.error.lower()
    
    @patch('tools.web_scraper.requests.get')
    def test_error_handling(self, mock_get, scraper_tool):
        """Test error handling with mocked failure."""
        # Make scraping fail
        mock_get.side_effect = Exception("Network error")
        
        result = scraper_tool.run(url="https://example.com", method="requests")
        
        assert result.success is False
        assert result.error is not None
    
    @patch('tools.web_scraper.requests.get')
    def test_content_truncation(self, mock_get, scraper_tool):
        """Test that very long content is truncated."""
        # Create very long content (>50K characters)
        long_content = "x" * 60000
        mock_response = Mock()
        mock_response.content = f"<html><body><p>{long_content}</p></body></html>".encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = scraper_tool.execute(url="https://example.com", method="requests")
        
        assert result.success is True
        assert result.data["truncated"] is True
        assert len(result.data["content"]) <= 50000
    
    @patch('tools.web_scraper.requests.get')
    def test_script_and_style_removal(self, mock_get, scraper_tool):
        """Test that script and style tags are removed."""
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <head>
                <style>body { color: red; }</style>
            </head>
            <body>
                <p>Visible content</p>
                <script>alert('test');</script>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        content = scraper_tool.scrape_with_requests("https://example.com")
        
        assert "Visible content" in content
        assert "color: red" not in content
        assert "alert" not in content
    
    @patch('tools.web_scraper.requests.get')
    def test_whitespace_cleanup(self, mock_get, scraper_tool):
        """Test that excessive whitespace is cleaned up."""
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <body>
                <p>Line 1</p>
                
                
                <p>Line 2</p>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        content = scraper_tool.scrape_with_requests("https://example.com")
        
        # Should not have excessive blank lines
        assert "\n\n\n" not in content
    
    @patch('tools.web_scraper.trafilatura.fetch_url')
    def test_trafilatura_download_failure(self, mock_fetch, scraper_tool):
        """Test trafilatura handles download failure."""
        mock_fetch.return_value = None
        
        with pytest.raises(ValueError, match="Failed to download"):
            scraper_tool.scrape_with_trafilatura("https://example.com")
    
    @patch('tools.web_scraper.trafilatura.extract')
    @patch('tools.web_scraper.trafilatura.fetch_url')
    def test_trafilatura_extraction_failure(
        self,
        mock_fetch,
        mock_extract,
        scraper_tool
    ):
        """Test trafilatura handles extraction failure."""
        mock_fetch.return_value = "<html>content</html>"
        mock_extract.return_value = None
        
        with pytest.raises(ValueError, match="Failed to extract"):
            scraper_tool.scrape_with_trafilatura("https://example.com")
    
    @patch('tools.web_scraper.Article')
    def test_newspaper_empty_text(self, mock_article_class, scraper_tool):
        """Test newspaper handles empty article text."""
        mock_article = Mock()
        mock_article.text = ""
        mock_article_class.return_value = mock_article
        
        with pytest.raises(ValueError, match="Failed to extract article"):
            scraper_tool.scrape_with_newspaper("https://example.com")
    
    @patch('tools.web_scraper.requests.get')
    def test_execution_time_tracking(self, mock_get, scraper_tool):
        """Test that execution time is tracked."""
        mock_response = Mock()
        mock_response.content = b"<html><body>Content</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = scraper_tool.execute(url="https://example.com")
        
        assert result.success is True
        assert "execution_time" in result.metadata
        assert result.metadata["execution_time"] >= 0
    
    @patch('tools.web_scraper.requests.get')
    def test_methods_tried_tracking(self, mock_get, scraper_tool):
        """Test that methods tried are tracked in metadata."""
        mock_response = Mock()
        mock_response.content = b"<html><body>Content</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = scraper_tool.execute(url="https://example.com", method="auto")
        
        assert result.success is True
        assert "methods_tried" in result.metadata
        assert isinstance(result.metadata["methods_tried"], list)
