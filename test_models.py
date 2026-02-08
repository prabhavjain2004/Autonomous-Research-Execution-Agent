#!/usr/bin/env python3
"""
Quick test script to verify OpenRouter models are working
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from model_router import ModelRouter, TaskComplexity

def test_models():
    """Test all configured models"""
    
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set in environment")
        print("   Set it in .env file or export it")
        return False
    
    print(f"✅ API Key found: {api_key[:15]}...")
    
    # Create router
    router = ModelRouter(api_key)
    print(f"✅ ModelRouter created with {len(router.MODELS)} models")
    
    # List models
    print("\n📋 Configured Models:")
    for key, info in router.MODELS.items():
        print(f"   - {key}: {info['id']}")
        print(f"     Context: {info['context']:,} tokens")
        print(f"     Complexity: {', '.join(info['complexity'])}")
    
    # Test a simple call
    print("\n🧪 Testing model call...")
    test_prompt = "Say 'Hello, I am working!' in exactly those words."
    
    response = router.call_with_fallback(
        task_complexity=TaskComplexity.SIMPLE,
        prompt=test_prompt,
        max_tokens=50,
        temperature=0.7
    )
    
    if response.success:
        print(f"✅ Model call successful!")
        print(f"   Model: {response.model}")
        print(f"   Response: {response.text[:100]}")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Latency: {response.latency:.2f}s")
        return True
    else:
        print(f"❌ Model call failed")
        print(f"   Error: {response.error}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("OpenRouter Model Test")
    print("=" * 70)
    
    success = test_models()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ All tests passed! Models are working.")
        print("\nYour system is ready to use with LLM integration.")
    else:
        print("❌ Tests failed. Check the error messages above.")
        print("\nSee OPENROUTER_TROUBLESHOOTING.md for help.")
    print("=" * 70)
