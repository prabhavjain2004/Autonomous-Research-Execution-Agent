"""
Model router for intelligent LLM selection using OpenRouter.

This module provides automatic model selection based on task complexity,
with fallback mechanisms and performance tracking.
"""

import time
from typing import Optional, Dict, Any
from enum import Enum
import os

from openai import OpenAI

from models.data_models import ModelResponse
from structured_logging import StructuredLogger


class TaskComplexity(Enum):
    """Task complexity levels for model selection."""
    SIMPLE = "simple"          # Formatting, summarization
    MODERATE = "moderate"      # Data extraction, basic analysis
    COMPLEX = "complex"        # Deep reasoning, strategy generation
    LONG_CONTEXT = "long"      # Large context requirements


class ModelRouter:
    """
    Intelligent model router using OpenRouter free models.
    
    Features:
    - Automatic model selection based on task complexity
    - Fallback mechanism for failed API calls
    - Performance metrics tracking
    - Support for multiple free OpenRouter models
    """
    
    # OpenRouter free models with their characteristics
    # Updated with currently available models as of Feb 2026
    # Using exact IDs from OpenRouter
    MODELS = {
        "qwen-4b": {
            "id": "qwen/qwen3-4b:free",
            "context": 41000,
            "complexity": ["complex", "moderate"],
            "description": "Dual-mode architecture for reasoning and dialogue"
        },
        "gemma-12b": {
            "id": "google/gemma-3-12b-it:free",
            "context": 33000,
            "complexity": ["complex", "long"],
            "description": "Multimodal, best for analysis and reasoning"
        },
        "llama-3b": {
            "id": "meta-llama/llama-3.2-3b-instruct:free",
            "context": 131000,
            "complexity": ["long", "moderate", "simple", "complex"],
            "description": "Multilingual, excellent for long context"
        },
        "gemma-4b": {
            "id": "google/gemma-3-4b-it:free",
            "context": 33000,
            "complexity": ["moderate", "simple"],
            "description": "Multimodal, general purpose"
        }
    }
    
    def __init__(
        self,
        api_key: str,
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize model router with OpenRouter API key.
        
        Args:
            api_key: OpenRouter API key
            logger: Structured logger for observability
        """
        self.api_key = api_key
        self.logger = logger
        
        # Initialize OpenAI client with OpenRouter base URL
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Performance tracking
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        for model_key in self.MODELS.keys():
            self.performance_metrics[model_key] = {
                "success_count": 0,
                "failure_count": 0,
                "total_tokens": 0,
                "total_latency": 0.0,
                "call_count": 0
            }
    
    def select_model(
        self,
        task_complexity: TaskComplexity,
        context_length: Optional[int] = None
    ) -> str:
        """
        Select optimal model based on task requirements.
        
        Args:
            task_complexity: Complexity level of task
            context_length: Estimated context length needed
            
        Returns:
            Model identifier for OpenRouter API
        """
        complexity_str = task_complexity.value
        
        # Filter models by complexity
        suitable_models = []
        for model_key, model_info in self.MODELS.items():
            if complexity_str in model_info["complexity"]:
                # Check context length if specified
                if context_length and context_length > model_info["context"]:
                    continue
                suitable_models.append((model_key, model_info))
        
        if not suitable_models:
            # Fallback to a general model
            suitable_models = [("gemma-4b", self.MODELS["gemma-4b"])]
        
        # Select model with best performance metrics
        best_model = None
        best_score = -1
        
        for model_key, model_info in suitable_models:
            metrics = self.performance_metrics[model_key]
            
            # Calculate success rate
            total_calls = metrics["call_count"]
            if total_calls > 0:
                success_rate = metrics["success_count"] / total_calls
            else:
                success_rate = 0.5  # Neutral for untested models
            
            # Simple scoring: prioritize success rate
            score = success_rate
            
            if score > best_score:
                best_score = score
                best_model = model_key
        
        if not best_model:
            best_model = suitable_models[0][0]
        
        selected_model_id = self.MODELS[best_model]["id"]
        
        if self.logger:
            self.logger.log_model_selection(
                task_complexity=complexity_str,
                selected_model=best_model,
                reasoning=f"Selected based on complexity and performance (score: {best_score:.2f})",
                context_length=context_length
            )
        
        return selected_model_id
    
    def call_model(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> ModelResponse:
        """
        Call OpenRouter API with selected model.
        
        Args:
            model: Model identifier
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            ModelResponse with generated text and metadata
        """
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            latency = time.time() - start_time
            
            # Extract response
            text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Update metrics
            self._update_metrics(model, success=True, tokens=tokens_used, latency=latency)
            
            if self.logger:
                self.logger.log_info(
                    f"Model call successful: {model}",
                    {
                        "model": model,
                        "tokens": tokens_used,
                        "latency": latency
                    }
                )
            
            return ModelResponse(
                model=model,
                text=text,
                tokens_used=tokens_used,
                latency=latency,
                success=True
            )
        
        except Exception as e:
            latency = time.time() - start_time
            error_message = str(e)
            
            # Update metrics
            self._update_metrics(model, success=False, tokens=0, latency=latency)
            
            if self.logger:
                self.logger.log_error(
                    error_type=type(e).__name__,
                    error_message=error_message,
                    stack_trace="",
                    context={"model": model, "prompt_length": len(prompt)}
                )
            
            return ModelResponse(
                model=model,
                text="",
                tokens_used=0,
                latency=latency,
                success=False,
                error=error_message
            )
    
    def call_with_fallback(
        self,
        task_complexity: TaskComplexity,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> ModelResponse:
        """
        Call model with automatic fallback on failure.
        
        Args:
            task_complexity: Task complexity for model selection
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            max_retries: Maximum retry attempts
            
        Returns:
            ModelResponse from successful call
        """
        import time
        
        context_length = len(prompt) // 4  # Rough estimate (4 chars per token)
        
        # Get all suitable models for this complexity
        complexity_str = task_complexity.value
        suitable_models = []
        for model_key, model_info in self.MODELS.items():
            if complexity_str in model_info["complexity"]:
                if context_length and context_length > model_info["context"]:
                    continue
                suitable_models.append(model_key)
        
        if not suitable_models:
            suitable_models = list(self.MODELS.keys())
        
        # Try each suitable model
        last_error = None
        for attempt, model_key in enumerate(suitable_models[:max_retries]):
            model_id = self.MODELS[model_key]["id"]
            
            if self.logger and attempt > 0:
                self.logger.log_retry(
                    operation="model_call",
                    retry_count=attempt,
                    max_retries=max_retries,
                    reason=f"Previous model failed: {last_error}"
                )
            
            # Add exponential backoff for rate limits
            if attempt > 0:
                backoff_time = min(2 ** attempt, 10)  # Max 10 seconds
                time.sleep(backoff_time)
            
            response = self.call_model(model_id, prompt, max_tokens, temperature)
            
            if response.success:
                return response
            
            last_error = response.error
            
            # If rate limited, wait longer before next attempt
            if "429" in str(response.error) or "rate" in str(response.error).lower():
                time.sleep(5)  # Wait 5 seconds for rate limits
        
        # All attempts failed - return last response
        return ModelResponse(
            model="all_models",
            text="",
            tokens_used=0,
            latency=0.0,
            success=False,
            error=f"All models failed. Last error: {last_error}"
        )
    
    def _update_metrics(
        self,
        model: str,
        success: bool,
        tokens: int,
        latency: float
    ):
        """
        Update performance metrics for a model.
        
        Args:
            model: Model identifier
            success: Whether call was successful
            tokens: Tokens used
            latency: Response latency
        """
        # Find model key from ID
        model_key = None
        for key, info in self.MODELS.items():
            if info["id"] == model:
                model_key = key
                break
        
        if not model_key:
            return
        
        metrics = self.performance_metrics[model_key]
        metrics["call_count"] += 1
        
        if success:
            metrics["success_count"] += 1
            metrics["total_tokens"] += tokens
            metrics["total_latency"] += latency
        else:
            metrics["failure_count"] += 1
    
    def get_performance_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics for all models.
        
        Returns:
            Dictionary of performance metrics per model
        """
        return self.performance_metrics.copy()
    
    def get_model_info(self, model_key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model.
        
        Args:
            model_key: Model key (e.g., "qwen-4b")
            
        Returns:
            Model information dictionary or None
        """
        return self.MODELS.get(model_key)
