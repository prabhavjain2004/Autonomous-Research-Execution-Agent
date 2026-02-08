"""
Web search tool using Tavily, DuckDuckGo and Google Search APIs.

This tool provides web search capabilities with rate limiting, fallback mechanisms,
and support for multiple search engines.
"""

import time
import os
from typing import List, Optional
from datetime import datetime

from duckduckgo_search import DDGS
from googlesearch import search as google_search

from .base_tool import BaseTool
from models.data_models import ToolResult, SearchResult
from structured_logging import StructuredLogger


class WebSearchTool(BaseTool):
    """
    Web search tool with multiple search engine support.
    
    Features:
    - Tavily API search (primary - most reliable)
    - DuckDuckGo search (fallback)
    - Google search (fallback)
    - Rate limiting to prevent API abuse
    - Automatic fallback between engines
    - Structured search results
    """
    
    def __init__(
        self,
        logger: Optional[StructuredLogger] = None,
        rate_limit_delay: float = 2.5
    ):
        """
        Initialize web search tool with rate limiting.
        
        Args:
            logger: Structured logger for observability
            rate_limit_delay: Delay between requests in seconds (default: 2.5)
        """
        super().__init__(logger)
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0.0
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    def _enforce_rate_limit(self):
        """
        Enforce rate limiting between requests.
        
        Ensures at least rate_limit_delay seconds between consecutive requests.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            if self.logger:
                self.logger.log_debug(
                    f"Rate limiting: sleeping for {sleep_time:.2f}s",
                    {"sleep_time": sleep_time}
                )
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate search input parameters.
        
        Args:
            query: Search query string (required)
            max_results: Maximum number of results (optional)
            engines: List of search engines to try (optional)
            
        Returns:
            True if inputs are valid
        """
        if "query" not in kwargs:
            return False
        
        query = kwargs["query"]
        if not isinstance(query, str) or len(query.strip()) == 0:
            return False
        
        if "max_results" in kwargs:
            max_results = kwargs["max_results"]
            if not isinstance(max_results, int) or max_results < 1:
                return False
        
        if "engines" in kwargs:
            engines = kwargs["engines"]
            if not isinstance(engines, list):
                return False
            valid_engines = {"tavily", "duckduckgo", "google"}
            if not all(e in valid_engines for e in engines):
                return False
        
        return True
    
    def search_tavily(
        self,
        query: str,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search using Tavily API (most reliable, designed for AI agents).
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        if not self.tavily_api_key or self.tavily_api_key == "your_tavily_api_key_here":
            raise ValueError("Tavily API key not configured")
        
        self._enforce_rate_limit()
        
        results = []
        
        try:
            import requests
            
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                    "include_answer": False,
                    "include_raw_content": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for result in data.get("results", []):
                    results.append(SearchResult(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        snippet=result.get("content", ""),
                        source="tavily",
                        timestamp=datetime.utcnow().isoformat() + "Z"
                    ))
                
                if self.logger:
                    self.logger.log_info(
                        f"Tavily search completed: {len(results)} results",
                        {"query": query, "results_count": len(results)}
                    )
            else:
                error_msg = f"Tavily API returned status {response.status_code}"
                if self.logger:
                    self.logger.log_warning(
                        f"Tavily search failed: {error_msg}",
                        {"query": query, "status_code": response.status_code}
                    )
                raise Exception(error_msg)
        
        except Exception as e:
            if self.logger:
                self.logger.log_warning(
                    f"Tavily search failed: {str(e)}",
                    {"query": query, "error": str(e)}
                )
            raise
        
        return results
    
    def search_duckduckgo(
        self,
        query: str,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search using DuckDuckGo API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        self._enforce_rate_limit()
        
        results = []
        
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=max_results)
                
                for result in search_results:
                    results.append(SearchResult(
                        title=result.get("title", ""),
                        url=result.get("href", ""),
                        snippet=result.get("body", ""),
                        source="duckduckgo",
                        timestamp=datetime.utcnow().isoformat() + "Z"
                    ))
            
            if self.logger:
                self.logger.log_info(
                    f"DuckDuckGo search completed: {len(results)} results",
                    {"query": query, "results_count": len(results)}
                )
        
        except Exception as e:
            if self.logger:
                self.logger.log_warning(
                    f"DuckDuckGo search failed: {str(e)}",
                    {"query": query, "error": str(e)}
                )
            raise
        
        return results
    
    def search_google(
        self,
        query: str,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search using Google Search API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        self._enforce_rate_limit()
        
        results = []
        
        try:
            # googlesearch library returns URLs only
            urls = list(google_search(query, num_results=max_results, advanced=True))
            
            for item in urls[:max_results]:
                # googlesearch returns SearchResult objects with url, title, description
                results.append(SearchResult(
                    title=getattr(item, 'title', '') or '',
                    url=getattr(item, 'url', '') or str(item),
                    snippet=getattr(item, 'description', '') or '',
                    source="google",
                    timestamp=datetime.utcnow().isoformat() + "Z"
                ))
            
            if self.logger:
                self.logger.log_info(
                    f"Google search completed: {len(results)} results",
                    {"query": query, "results_count": len(results)}
                )
        
        except Exception as e:
            if self.logger:
                self.logger.log_warning(
                    f"Google search failed: {str(e)}",
                    {"query": query, "error": str(e)}
                )
            raise
        
        return results
    
    def execute(
        self,
        query: str,
        max_results: int = 10,
        engines: Optional[List[str]] = None
    ) -> ToolResult:
        """
        Execute web search with fallback between engines.
        
        Args:
            query: Search query
            max_results: Maximum results to return (default: 10)
            engines: List of engines to try (default: ["tavily", "duckduckgo", "google"])
            
        Returns:
            ToolResult with search results
        """
        if engines is None:
            # Try Tavily first if API key is configured, then fallback to others
            if self.tavily_api_key and self.tavily_api_key != "your_tavily_api_key_here":
                engines = ["tavily", "duckduckgo", "google"]
            else:
                engines = ["duckduckgo", "google"]
        
        results = []
        errors = []
        
        start_time = time.time()
        
        # Try each search engine in order
        for engine in engines:
            try:
                if engine == "tavily":
                    results = self.search_tavily(query, max_results)
                elif engine == "duckduckgo":
                    results = self.search_duckduckgo(query, max_results)
                elif engine == "google":
                    results = self.search_google(query, max_results)
                
                # If we got results, stop trying other engines
                if results:
                    break
            
            except Exception as e:
                error_msg = f"{engine} failed: {str(e)}"
                errors.append(error_msg)
                
                if self.logger:
                    self.logger.log_warning(
                        f"Search engine {engine} failed, trying next",
                        {"engine": engine, "error": str(e)}
                    )
                
                # Continue to next engine
                continue
        
        execution_time = time.time() - start_time
        
        # If no results from any engine, return failure
        if not results:
            error_message = "All search engines failed. " + "; ".join(errors)
            return ToolResult(
                success=False,
                data=None,
                error=error_message,
                metadata={
                    "query": query,
                    "engines_tried": engines,
                    "execution_time": execution_time
                }
            )
        
        # Convert SearchResult objects to dicts for storage
        results_data = [result.to_dict() for result in results]
        
        return ToolResult(
            success=True,
            data={
                "query": query,
                "results": results_data,
                "count": len(results_data)
            },
            metadata={
                "engines_tried": engines,
                "execution_time": execution_time,
                "source": results[0].source if results else None
            }
        )
