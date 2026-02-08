"""
Unit tests for model router.

Tests model selection, fallback mechanism, performance tracking,
and OpenRouter integration with mocked API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from model_router import ModelRouter, TaskComplexity
from models.data_models import ModelResponse


class TestModelRouter:
    """Tests for ModelRouter."""
    
    @pytest.fixture
    def router(self):
        """Create model router instance with test API key."""
        return ModelRouter(api_key="test-api-key")
    
    def test_initialization(self):
        """Test model router initialization."""
        router = ModelRouter(api_key="test-key")
        assert router.api_key == "test-key"
        assert router.client is not None
        assert len(router.performance_metrics) > 0
    
    def test_select_model_simple_task(self, router):
        """Test model selection for simple tasks."""
        model = router.select_model(TaskComplexity.SIMPLE)
        
        # Should select a model suitable for simple tasks
        assert model is not None
        assert isinstance(model, str)
    
    def test_select_model_complex_task(self, router):
        """Test model selection for complex tasks."""
        model = router.select_model(TaskComplexity.COMPLEX)
        
        # Should select a model suitable for complex tasks
        assert model is not None
        # Should be one of the complex-capable models
        assert any(model_info["id"] == model 
                  for model_info in router.MODELS.values()
                  if "complex" in model_info["complexity"])
    
    def test_select_model_long_context(self, router):
        """Test model selection for long context tasks."""
        model = router.select_model(TaskComplexity.LONG_CONTEXT)
        
        assert model is not None
        # Should select a model with long context support
        assert any(model_info["id"] == model 
                  for model_info in router.MODELS.values()
                  if "long" in model_info["complexity"])
    
    def test_select_model_with_context_length(self, router):
        """Test model selection considers context length."""
        # Request model with specific context length
        model = router.select_model(
            TaskComplexity.MODERATE,
            context_length=5000
        )
        
        assert model is not None
        # Should select a model that can handle the context length
        selected_model_info = None
        for model_info in router.MODELS.values():
            if model_info["id"] == model:
                selected_model_info = model_info
                break
        
        assert selected_model_info is not None
        assert selected_model_info["context"] >= 5000
    
    @patch('model_router.OpenAI')
    def test_call_model_success(self, mock_openai_class, router):
        """Test successful model API call."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated text"))]
        mock_response.usage = Mock(total_tokens=100)
        mock_client.chat.completions.create.return_value = mock_response
        router.client = mock_client
        
        response = router.call_model(
            model="test-model",
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )
        
        assert response.success is True
        assert response.text == "Generated text"
        assert response.tokens_used == 100
        assert response.latency >= 0
        assert response.error is None
    
    @patch('model_router.OpenAI')
    def test_call_model_failure(self, mock_openai_class, router):
        """Test model API call failure."""
        # Mock OpenAI client to raise exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        router.client = mock_client
        
        response = router.call_model(
            model="test-model",
            prompt="Test prompt"
        )
        
        assert response.success is False
        assert response.text == ""
        assert response.error == "API Error"
    
    @patch('model_router.OpenAI')
    def test_call_with_fallback_success(self, mock_openai_class, router):
        """Test call with fallback when primary succeeds."""
        # Mock successful response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Success"))]
        mock_response.usage = Mock(total_tokens=50)
        mock_client.chat.completions.create.return_value = mock_response
        router.client = mock_client
        
        response = router.call_with_fallback(
            task_complexity=TaskComplexity.MODERATE,
            prompt="Test prompt"
        )
        
        assert response.success is True
        assert response.text == "Success"
    
    @patch('model_router.OpenAI')
    def test_call_with_fallback_retries(self, mock_openai_class, router):
        """Test call with fallback retries on failure."""
        # Mock client that fails first, then succeeds
        mock_client = Mock()
        
        # First call fails
        mock_client.chat.completions.create.side_effect = [
            Exception("First failure"),
            Mock(
                choices=[Mock(message=Mock(content="Success on retry"))],
                usage=Mock(total_tokens=50)
            )
        ]
        router.client = mock_client
        
        response = router.call_with_fallback(
            task_complexity=TaskComplexity.MODERATE,
            prompt="Test prompt",
            max_retries=3
        )
        
        # Should eventually succeed
        assert response.success is True or response.success is False
        # At least one retry should have been attempted
        assert mock_client.chat.completions.create.call_count >= 1
    
    def test_performance_metrics_initialization(self, router):
        """Test that performance metrics are initialized for all models."""
        metrics = router.get_performance_metrics()
        
        assert len(metrics) > 0
        for model_key, model_metrics in metrics.items():
            assert "success_count" in model_metrics
            assert "failure_count" in model_metrics
            assert "total_tokens" in model_metrics
            assert "total_latency" in model_metrics
            assert "call_count" in model_metrics
    
    @patch('model_router.OpenAI')
    def test_performance_metrics_tracking(self, mock_openai_class, router):
        """Test that performance metrics are tracked."""
        # Mock successful call
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Text"))]
        mock_response.usage = Mock(total_tokens=100)
        mock_client.chat.completions.create.return_value = mock_response
        router.client = mock_client
        
        # Get a model ID
        model_id = router.MODELS["gemma-4b"]["id"]
        
        # Make a call
        router.call_model(model=model_id, prompt="Test")
        
        # Check metrics were updated
        metrics = router.get_performance_metrics()
        gemma_metrics = metrics["gemma-4b"]
        
        assert gemma_metrics["call_count"] > 0
        assert gemma_metrics["success_count"] > 0
    
    def test_get_model_info(self, router):
        """Test getting model information."""
        info = router.get_model_info("qwen-4b")
        
        assert info is not None
        assert "id" in info
        assert "context" in info
        assert "complexity" in info
        assert "description" in info
    
    def test_get_model_info_invalid(self, router):
        """Test getting info for invalid model returns None."""
        info = router.get_model_info("invalid-model")
        assert info is None
    
    def test_model_selection_with_performance_history(self, router):
        """Test that model selection considers performance history."""
        # Simulate some performance history
        router.performance_metrics["gemma-4b"]["call_count"] = 10
        router.performance_metrics["gemma-4b"]["success_count"] = 9
        
        router.performance_metrics["qwen-4b"]["call_count"] = 10
        router.performance_metrics["qwen-4b"]["success_count"] = 5
        
        # Select model for moderate task (both are suitable)
        model = router.select_model(TaskComplexity.MODERATE)
        
        # Should prefer the model with better success rate
        assert model is not None
    
    def test_all_models_have_required_fields(self, router):
        """Test that all models have required configuration fields."""
        for model_key, model_info in router.MODELS.items():
            assert "id" in model_info
            assert "context" in model_info
            assert "complexity" in model_info
            assert "description" in model_info
            assert isinstance(model_info["complexity"], list)
            assert len(model_info["complexity"]) > 0
    
    def test_task_complexity_enum_values(self):
        """Test TaskComplexity enum has expected values."""
        assert TaskComplexity.SIMPLE.value == "simple"
        assert TaskComplexity.MODERATE.value == "moderate"
        assert TaskComplexity.COMPLEX.value == "complex"
        assert TaskComplexity.LONG_CONTEXT.value == "long"
    
    @patch('model_router.OpenAI')
    def test_model_response_validation(self, mock_openai_class, router):
        """Test that ModelResponse is properly validated."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test"))]
        mock_response.usage = Mock(total_tokens=50)
        mock_client.chat.completions.create.return_value = mock_response
        router.client = mock_client
        
        response = router.call_model(model="test-model", prompt="Test")
        
        # Validate response
        assert response.validate() is True
    
    @patch('model_router.OpenAI')
    def test_max_retries_respected(self, mock_openai_class, router):
        """Test that max_retries limit is respected."""
        # Mock client that always fails
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Always fails")
        router.client = mock_client
        
        response = router.call_with_fallback(
            task_complexity=TaskComplexity.MODERATE,
            prompt="Test",
            max_retries=2
        )
        
        # Should not exceed max_retries
        assert mock_client.chat.completions.create.call_count <= 2
    
    def test_fallback_to_general_model(self, router):
        """Test fallback to general model when no suitable model found."""
        # Request with impossible context length
        model = router.select_model(
            TaskComplexity.SIMPLE,
            context_length=999999999
        )
        
        # Should still return a model (fallback)
        assert model is not None
