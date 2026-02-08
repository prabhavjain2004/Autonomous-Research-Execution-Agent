"""
System Integration Test

Quick test to verify all components can be initialized and work together.
"""

import sys
from boss_agent import BossAgent
from structured_logging.structured_logger import StructuredLogger
from memory.memory_system import MemorySystem
from config import Config
from output_formatter import OutputFormatter
from models.data_models import AgentOutput


def test_component_initialization():
    """Test that all components can be initialized."""
    print("Testing component initialization...")
    
    try:
        # Test Config
        print("  ✓ Config initialization")
        config = Config()
        assert config.OPENROUTER_API_KEY is not None, "API key not configured"
        
        # Test Logger
        print("  ✓ StructuredLogger initialization")
        logger = StructuredLogger(session_id="test-session")
        
        # Test Memory
        print("  ✓ MemorySystem initialization")
        memory = MemorySystem()
        
        # Test Boss Agent
        print("  ✓ BossAgent initialization")
        boss = BossAgent(
            logger=logger,
            memory_system=memory,
            max_retries=config.MAX_RETRY_ATTEMPTS
            # Use default confidence_threshold
        )
        
        # Test Output Formatter
        print("  ✓ OutputFormatter initialization")
        formatter = OutputFormatter()
        
        print("\n✅ All components initialized successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_models():
    """Test that data models work correctly."""
    print("\nTesting data models...")
    
    try:
        from models.data_models import AgentOutput, ResearchResult
        
        # Test AgentOutput
        print("  ✓ AgentOutput creation")
        output = AgentOutput(
            agent_name="Test Agent",
            task_id="test-123",
            results={"test": "data"},
            self_confidence=85,
            reasoning="Test reasoning",
            sources=["https://example.com"],
            execution_time=1.5
        )
        assert output.validate(), "AgentOutput validation failed"
        
        # Test ResearchResult
        print("  ✓ ResearchResult creation")
        result = ResearchResult.create_new(
            goal="Test goal",
            agents_involved=["Test Agent"],
            confidence_scores={"Test Agent": {"self": 85, "boss": 80}},
            competitors=[],
            insights=["Test insight"],
            recommendations=[{"text": "Test recommendation", "priority": "medium"}],
            sources=[{"url": "https://example.com", "title": "Test"}],
            overall_confidence=82
        )
        assert result.validate(), "ResearchResult validation failed"
        assert result.validate_schema(), "ResearchResult schema validation failed"
        
        print("\n✅ All data models working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Data model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_output_formatting():
    """Test output formatting."""
    print("\nTesting output formatting...")
    
    try:
        from output_formatter import OutputFormatter
        from models.data_models import AgentOutput
        
        formatter = OutputFormatter()
        
        # Create test outputs
        outputs = [
            AgentOutput(
                agent_name="Research Agent",
                task_id="task-1",
                results={
                    "insights": ["Test insight 1", "Test insight 2"],
                    "recommendations": ["Test recommendation"]
                },
                self_confidence=85,
                reasoning="Test reasoning",
                sources=["https://example.com"],
                execution_time=2.0
            )
        ]
        
        # Format result
        print("  ✓ Formatting research result")
        result = formatter.format_research_result("Test research goal", outputs)
        
        assert result.goal == "Test research goal"
        assert len(result.agents_involved) == 1
        assert len(result.insights) >= 1
        assert result.validate()
        assert result.validate_schema()
        
        print("\n✅ Output formatting working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Output formatting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_system():
    """Test memory system operations."""
    print("\nTesting memory system...")
    
    try:
        from memory.memory_system import MemorySystem
        import uuid
        
        memory = MemorySystem()
        
        # Create session
        print("  ✓ Creating session")
        session_id = memory.create_session("Test goal")
        session_id = str(session_id)  # Convert UUID to string
        
        # Store decision
        print("  ✓ Storing decision")
        memory.store_decision(
            session_id=uuid.UUID(session_id),
            agent_name="Test Agent",
            decision="Test decision",
            context={"reasoning": "Test reasoning", "confidence_score": 85}
        )
        
        # Retrieve history
        print("  ✓ Retrieving session history")
        history = memory.get_session_history(session_id)
        assert history is not None
        assert history.session_id == session_id
        
        print("\n✅ Memory system working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Memory system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*80)
    print("AUTONOMOUS RESEARCH AGENT - SYSTEM INTEGRATION TEST")
    print("="*80)
    print()
    
    results = []
    
    # Run tests
    results.append(("Component Initialization", test_component_initialization()))
    results.append(("Data Models", test_data_models()))
    results.append(("Output Formatting", test_output_formatting()))
    results.append(("Memory System", test_memory_system()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready for use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
