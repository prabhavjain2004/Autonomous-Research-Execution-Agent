"""
Research Agent Implementation

This agent specializes in gathering information from web sources using
search and scraping tools, then uses LLM to analyze and summarize findings.
"""

import time
from typing import Dict, Any, List

from agents.base_agent import BaseAgent, AgentContext
from models.data_models import AgentOutput
from evaluation.reflection import ConfidenceScore, AgentType, ReflectionModule
from tools.web_search import WebSearchTool
from tools.web_scraper import WebScraperTool
from structured_logging.structured_logger import StructuredLogger
from model_router import ModelRouter, TaskComplexity


class ResearchAgent(BaseAgent):
    """
    Research Agent for gathering information from web sources
    
    This agent:
    - Performs web searches to find relevant sources
    - Scrapes content from discovered URLs
    - Uses LLM to analyze and summarize findings
    - Calculates confidence based on source quality and relevance
    
    Confidence factors:
    - source_count: Number of sources found
    - source_reliability: Quality of source domains
    - completeness: Amount of information gathered
    - relevance: Alignment with task description
    """
    
    def __init__(
        self,
        agent_name: str = "research_agent",
        max_retries: int = 3,
        max_search_results: int = 5,
        max_scrape_attempts: int = 3,
        logger: StructuredLogger = None,
        model_router: ModelRouter = None
    ):
        """
        Initialize Research Agent
        
        Args:
            agent_name: Name of the agent
            max_retries: Maximum number of retries allowed
            max_search_results: Maximum number of search results to retrieve
            max_scrape_attempts: Maximum number of URLs to attempt scraping
            logger: Optional structured logger
            model_router: Model router for LLM calls
        """
        super().__init__(
            agent_name=agent_name,
            agent_type=AgentType.RESEARCH,
            max_retries=max_retries
        )
        
        if max_search_results < 1:
            raise ValueError("max_search_results must be at least 1")
        if max_scrape_attempts < 1:
            raise ValueError("max_scrape_attempts must be at least 1")
        
        self.max_search_results = max_search_results
        self.max_scrape_attempts = max_scrape_attempts
        self.logger = logger
        self.model_router = model_router
        
        # Initialize tools
        self.search_tool = WebSearchTool()
        self.scraper_tool = WebScraperTool()
        
        # Initialize reflection module for confidence calculation
        self.reflection_module = ReflectionModule()
    
    def execute(self, context: AgentContext) -> AgentOutput:
        """
        Execute research task
        
        Process:
        1. Perform web search for the task description
        2. Scrape content from top results
        3. Aggregate findings
        4. Return structured output
        
        Args:
            context: Execution context with task information
        
        Returns:
            AgentOutput with research findings
        """
        start_time = time.time()
        
        if self.logger:
            self.logger.log_decision(
                agent_name=self.agent_name,
                decision=f"Starting research for: {context.task_description}",
                reasoning="Beginning web search and content gathering"
            )
        
        # Step 1: Perform web search
        search_results = self._perform_search(context.task_description)
        
        if not search_results:
            # No results found
            execution_time = time.time() - start_time
            return AgentOutput(
                agent_name=self.agent_name,
                task_id=context.task_id,
                results={
                    "findings": "No relevant sources found for the research query.",
                    "search_query": context.task_description,
                    "sources_found": 0
                },
                self_confidence=20,
                reasoning="Search returned no results",
                sources=[],
                execution_time=execution_time
            )
        
        # Step 2: Scrape content from top results
        scraped_content = self._scrape_sources(search_results)
        
        # Step 3: Use LLM to analyze and summarize findings
        llm_summary = self._generate_llm_summary(
            context.task_description,
            search_results,
            scraped_content
        )
        
        # Step 4: Aggregate findings
        findings = self._aggregate_findings(
            context.task_description,
            search_results,
            scraped_content,
            llm_summary
        )
        
        execution_time = time.time() - start_time
        
        # Create output
        output = AgentOutput(
            agent_name=self.agent_name,
            task_id=context.task_id,
            results=findings,
            self_confidence=self._estimate_initial_confidence(findings),
            reasoning=self._generate_reasoning(findings),
            sources=[result["url"] for result in search_results],
            execution_time=execution_time
        )
        
        if self.logger:
            self.logger.log_decision(
                agent_name=self.agent_name,
                decision=f"Research completed with {len(output.sources)} sources",
                reasoning=output.reasoning
            )
        
        return output
    
    def calculate_confidence(self, output: AgentOutput) -> ConfidenceScore:
        """
        Calculate confidence score for research output
        
        Uses the reflection module to assess:
        - Source count and reliability
        - Content completeness
        - Relevance to task
        
        Args:
            output: The research output to assess
        
        Returns:
            ConfidenceScore with detailed factor breakdown
        """
        # Use reflection module for consistent confidence calculation
        score = self.reflection_module.calculate_self_confidence(
            output,
            self.agent_type,
            task_description=output.task_id  # Use task_id as proxy for description
        )
        
        return score
    
    def _perform_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform web search
        
        Args:
            query: Search query
        
        Returns:
            List of search results
        """
        try:
            if self.logger:
                self.logger.log_tool_call(
                    tool_name="web_search",
                    inputs={"query": query, "max_results": self.max_search_results},
                    outputs={},
                    execution_time=0.0,
                    success=False  # Will be updated after execution
                )
            
            result = self.search_tool.run(
                query=query,
                max_results=self.max_search_results,
                engines=["tavily", "duckduckgo", "google"]  # Try Tavily first
            )
            
            if result.success and result.data:
                return result.data.get("results", [])
            else:
                if self.logger:
                    import traceback
                    self.logger.log_error(
                        error_type="SearchError",
                        error_message=result.error or "Search failed",
                        stack_trace="",
                        context={"query": query}
                    )
                return []
        
        except Exception as e:
            if self.logger:
                import traceback
                self.logger.log_error(
                    error_type="SearchException",
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    context={"query": query}
                )
            return []
    
    def _scrape_sources(self, search_results: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Scrape content from search result URLs
        
        Args:
            search_results: List of search results with URLs
        
        Returns:
            Dictionary mapping URLs to scraped content
        """
        scraped_content = {}
        attempts = 0
        
        for result in search_results:
            if attempts >= self.max_scrape_attempts:
                break
            
            url = result.get("url")
            if not url:
                continue
            
            attempts += 1
            
            try:
                if self.logger:
                    self.logger.log_tool_call(
                        tool_name="web_scraper",
                        inputs={"url": url},
                        outputs={},
                        execution_time=0.0,
                        success=False
                    )
                
                scrape_result = self.scraper_tool.run(
                    url=url,
                    method="auto"
                )
                
                if scrape_result.success and scrape_result.data:
                    content = scrape_result.data.get("content", "")
                    if content:
                        scraped_content[url] = content
            
            except Exception as e:
                if self.logger:
                    import traceback
                    self.logger.log_error(
                        error_type="ScrapeException",
                        error_message=str(e),
                        stack_trace=traceback.format_exc(),
                        context={"url": url}
                    )
                continue
        
        return scraped_content
    
    def _generate_llm_summary(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        scraped_content: Dict[str, str]
    ) -> str:
        """
        Use LLM to analyze scraped content and generate insights
        
        Args:
            query: Original research query
            search_results: List of search results
            scraped_content: Scraped content from URLs
        
        Returns:
            LLM-generated summary and insights
        """
        if not scraped_content:
            return "No content available for analysis."
        
        # If no model router, use template summary
        if not self.model_router:
            return self._generate_template_summary(query, search_results, scraped_content)
        
        # Prepare content for LLM
        content_parts = []
        for url, content in list(scraped_content.items())[:3]:  # Limit to top 3 sources
            # Truncate content to avoid token limits
            truncated = content[:3000] if len(content) > 3000 else content
            content_parts.append(f"Source: {url}\nContent: {truncated}\n")
        
        combined_content = "\n---\n".join(content_parts)
        
        # Create prompt for LLM
        prompt = f"""You are a research analyst. Analyze the following web content and provide a comprehensive summary that answers this research question:

Research Question: {query}

Web Content:
{combined_content}

Please provide:
1. A clear, direct answer to the research question
2. Key findings from the sources
3. Important details and specifics mentioned
4. Any relevant data, numbers, or comparisons

Be specific and cite information from the sources. Focus on answering the user's question directly."""

        try:
            # Call LLM with moderate complexity
            response = self.model_router.call_with_fallback(
                task_complexity=TaskComplexity.MODERATE,
                prompt=prompt,
                max_tokens=1500,
                temperature=0.7
            )
            
            if response.success:
                return response.text
            else:
                # Fallback to template if LLM fails
                if self.logger:
                    self.logger.log_info(
                        "LLM summary failed, using template fallback",
                        {"error": response.error}
                    )
                return self._generate_template_summary(query, search_results, scraped_content)
        
        except Exception as e:
            if self.logger:
                import traceback
                self.logger.log_error(
                    error_type="LLMSummaryError",
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    context={"query": query}
                )
            return self._generate_template_summary(query, search_results, scraped_content)
    
    def _generate_template_summary(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        scraped_content: Dict[str, str]
    ) -> str:
        """
        Generate template-based summary (fallback when LLM unavailable)
        
        Args:
            query: Original research query
            search_results: List of search results
            scraped_content: Scraped content from URLs
        
        Returns:
            Template-based summary
        """
        summary_parts = [f"Research query: {query}"]
        summary_parts.append(f"\nFound {len(search_results)} relevant sources")
        summary_parts.append(f"Successfully retrieved full content from {len(scraped_content)} sources")
        
        # Add key sources
        if search_results:
            summary_parts.append("\nKey sources:")
            for i, result in enumerate(search_results[:3], 1):
                title = result.get("title", "Unknown")
                summary_parts.append(f"{i}. {title}")
        
        # Add content preview
        if scraped_content:
            summary_parts.append("\nContent preview:")
            for url, content in list(scraped_content.items())[:2]:
                preview = content[:200] + "..." if len(content) > 200 else content
                summary_parts.append(f"- {preview}")
        
        summary_parts.append(f"\nOverall data quality is {'high' if len(scraped_content) >= 2 else 'moderate'} with average confidence of {min(len(scraped_content) * 35, 70)}.0%")
        summary_parts.append(f"{len([r for r in search_results if any(d in r.get('url', '') for d in ['.edu', '.gov', '.org'])])} out of {len(search_results)} sources from authoritative domains")
        
        return "\n".join(summary_parts)
    
    def _aggregate_findings(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        scraped_content: Dict[str, str],
        llm_summary: str
    ) -> Dict[str, Any]:
        """
        Aggregate research findings with LLM analysis
        
        Args:
            query: Original search query
            search_results: List of search results
            scraped_content: Scraped content from URLs
            llm_summary: LLM-generated summary
        
        Returns:
            Dictionary with aggregated findings
        """
        # Compile source information
        sources = []
        for result in search_results:
            url = result.get("url", "")
            source_info = {
                "url": url,
                "title": result.get("title", "Unknown"),
                "snippet": result.get("snippet", ""),
                "has_full_content": url in scraped_content
            }
            sources.append(source_info)
        
        # Aggregate scraped content
        full_content = []
        for url, content in scraped_content.items():
            # Truncate very long content
            truncated = content[:2000] if len(content) > 2000 else content
            full_content.append({
                "url": url,
                "content_preview": truncated,
                "content_length": len(content)
            })
        
        return {
            "query": query,
            "summary": llm_summary,  # LLM-generated summary
            "sources": sources,
            "scraped_content": full_content,
            "total_sources": len(sources),
            "successfully_scraped": len(scraped_content)
        }
    
    def _estimate_initial_confidence(self, findings: Dict[str, Any]) -> int:
        """
        Estimate initial confidence score (0-100)
        
        Args:
            findings: Research findings
        
        Returns:
            Confidence score as integer
        """
        total_sources = findings.get("total_sources", 0)
        scraped_count = findings.get("successfully_scraped", 0)
        
        # Base confidence on source count and scraping success
        if total_sources == 0:
            return 20
        
        source_score = min(total_sources / 5.0, 1.0) * 50  # Up to 50 points
        scrape_score = (scraped_count / max(total_sources, 1)) * 50  # Up to 50 points
        
        return int(source_score + scrape_score)
    
    def _generate_reasoning(self, findings: Dict[str, Any]) -> str:
        """
        Generate reasoning for the research output
        
        Args:
            findings: Research findings
        
        Returns:
            Reasoning string
        """
        total = findings.get("total_sources", 0)
        scraped = findings.get("successfully_scraped", 0)
        
        if total == 0:
            return "No sources found for the research query"
        
        if scraped == 0:
            return f"Found {total} sources but could not retrieve full content"
        
        return (
            f"Successfully researched topic with {total} sources, "
            f"retrieved full content from {scraped} sources"
        )
