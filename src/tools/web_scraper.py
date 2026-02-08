"""
Web scraper tool with multiple backends and automatic fallback.

This tool provides web scraping capabilities using multiple methods:
- requests + BeautifulSoup (fast, simple HTML)
- trafilatura (efficient content extraction)
- newspaper3k (article extraction)
- Playwright (JavaScript-heavy sites)
"""

import time
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import trafilatura
from newspaper import Article

from .base_tool import BaseTool
from models.data_models import ToolResult
from structured_logging import StructuredLogger


class WebScraperTool(BaseTool):
    """
    Web scraper with multiple backends and automatic fallback.
    
    Features:
    - Multiple scraping methods with automatic fallback
    - Timeout handling for each method
    - User-agent rotation
    - Error recovery and graceful degradation
    """
    
    def __init__(
        self,
        logger: Optional[StructuredLogger] = None,
        timeout: int = 30,
        use_browser: bool = False
    ):
        """
        Initialize web scraper with multiple backends.
        
        Args:
            logger: Structured logger for observability
            timeout: Request timeout in seconds (default: 30)
            use_browser: Whether to use Playwright for JS-heavy sites (default: False)
        """
        super().__init__(logger)
        self.timeout = timeout
        self.use_browser = use_browser
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate scraper input parameters.
        
        Args:
            url: URL to scrape (required)
            method: Scraping method (optional)
            
        Returns:
            True if inputs are valid
        """
        if "url" not in kwargs:
            return False
        
        url = kwargs["url"]
        if not isinstance(url, str) or len(url.strip()) == 0:
            return False
        
        # Validate URL format
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
        except Exception:
            return False
        
        # Validate method if provided
        if "method" in kwargs:
            method = kwargs["method"]
            valid_methods = {"auto", "requests", "trafilatura", "newspaper", "playwright"}
            if method not in valid_methods:
                return False
        
        return True
    
    def scrape_with_requests(self, url: str) -> str:
        """
        Scrape using requests + BeautifulSoup.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text content
        """
        headers = {"User-Agent": self.user_agent}
        
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if self.logger:
            self.logger.log_info(
                f"Scraped with requests: {len(text)} characters",
                {"url": url, "method": "requests", "length": len(text)}
            )
        
        return text
    
    def scrape_with_trafilatura(self, url: str) -> str:
        """
        Scrape using trafilatura (efficient extraction).
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text content
        """
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            raise ValueError("Failed to download content")
        
        text = trafilatura.extract(downloaded)
        
        if not text:
            raise ValueError("Failed to extract content")
        
        if self.logger:
            self.logger.log_info(
                f"Scraped with trafilatura: {len(text)} characters",
                {"url": url, "method": "trafilatura", "length": len(text)}
            )
        
        return text
    
    def scrape_with_newspaper(self, url: str) -> str:
        """
        Scrape using newspaper3k (article extraction).
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted article text
        """
        article = Article(url)
        article.download()
        article.parse()
        
        if not article.text:
            raise ValueError("Failed to extract article text")
        
        if self.logger:
            self.logger.log_info(
                f"Scraped with newspaper: {len(article.text)} characters",
                {"url": url, "method": "newspaper", "length": len(article.text)}
            )
        
        return article.text
    
    def scrape_with_playwright(self, url: str) -> str:
        """
        Scrape using Playwright (JavaScript rendering).
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text content
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run: pip install playwright && playwright install"
            )
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(url, timeout=self.timeout * 1000)
                page.wait_for_load_state("networkidle", timeout=self.timeout * 1000)
                
                # Get text content
                text = page.inner_text("body")
                
                if self.logger:
                    self.logger.log_info(
                        f"Scraped with Playwright: {len(text)} characters",
                        {"url": url, "method": "playwright", "length": len(text)}
                    )
                
                return text
            
            finally:
                browser.close()
    
    def execute(
        self,
        url: str,
        method: str = "auto"
    ) -> ToolResult:
        """
        Execute web scraping with automatic fallback.
        
        Args:
            url: URL to scrape
            method: Scraping method (auto, requests, trafilatura, newspaper, playwright)
            
        Returns:
            ToolResult with extracted content
        """
        start_time = time.time()
        
        # Define fallback cascade
        if method == "auto":
            methods = ["requests", "trafilatura", "newspaper"]
            if self.use_browser:
                methods.append("playwright")
        else:
            methods = [method]
        
        content = None
        errors = []
        successful_method = None
        
        # Try each method in order
        for scrape_method in methods:
            try:
                if self.logger:
                    self.logger.log_debug(
                        f"Attempting scrape with {scrape_method}",
                        {"url": url, "method": scrape_method}
                    )
                
                if scrape_method == "requests":
                    content = self.scrape_with_requests(url)
                elif scrape_method == "trafilatura":
                    content = self.scrape_with_trafilatura(url)
                elif scrape_method == "newspaper":
                    content = self.scrape_with_newspaper(url)
                elif scrape_method == "playwright":
                    content = self.scrape_with_playwright(url)
                
                # If we got content, stop trying other methods
                if content and len(content.strip()) > 0:
                    successful_method = scrape_method
                    break
            
            except Exception as e:
                error_msg = f"{scrape_method} failed: {str(e)}"
                errors.append(error_msg)
                
                if self.logger:
                    self.logger.log_warning(
                        f"Scraping method {scrape_method} failed, trying next",
                        {"url": url, "method": scrape_method, "error": str(e)}
                    )
                
                # Continue to next method
                continue
        
        execution_time = time.time() - start_time
        
        # If no content from any method, return failure
        if not content or len(content.strip()) == 0:
            error_message = "All scraping methods failed. " + "; ".join(errors)
            return ToolResult(
                success=False,
                data=None,
                error=error_message,
                metadata={
                    "url": url,
                    "methods_tried": methods,
                    "execution_time": execution_time
                }
            )
        
        # Truncate very long content for storage
        max_length = 50000  # 50K characters
        truncated = False
        if len(content) > max_length:
            content = content[:max_length]
            truncated = True
        
        return ToolResult(
            success=True,
            data={
                "url": url,
                "content": content,
                "length": len(content),
                "truncated": truncated
            },
            metadata={
                "method": successful_method,
                "methods_tried": methods,
                "execution_time": execution_time
            }
        )
