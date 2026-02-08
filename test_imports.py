#!/usr/bin/env python3
"""
Test script to verify all imports work correctly after restructuring.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("=" * 70)
print("IMPORT VERIFICATION TEST")
print("=" * 70)

errors = []
success = []

# Test core modules
modules_to_test = [
    ("config", "Configuration"),
    ("error_handling", "Error Handling"),
    ("output_formatter", "Output Formatter"),
    ("model_router", "Model Router"),
    ("boss_agent", "Boss Agent"),
]

print("\n1. Testing Core Modules:")
print("-" * 70)
for module_name, display_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✓ {display_name:30} - OK")
        success.append(module_name)
    except Exception as e:
        print(f"✗ {display_name:30} - FAILED: {str(e)}")
        errors.append((module_name, str(e)))

# Test agent modules
agent_modules = [
    ("agents.base_agent", "Base Agent"),
    ("agents.research_agent", "Research Agent"),
    ("agents.analyst_agent", "Analyst Agent"),
    ("agents.strategy_agent", "Strategy Agent"),
]

print("\n2. Testing Agent Modules:")
print("-" * 70)
for module_name, display_name in agent_modules:
    try:
        __import__(module_name)
        print(f"✓ {display_name:30} - OK")
        success.append(module_name)
    except Exception as e:
        print(f"✗ {display_name:30} - FAILED: {str(e)}")
        errors.append((module_name, str(e)))

# Test tool modules
tool_modules = [
    ("tools.base_tool", "Base Tool"),
    ("tools.web_search", "Web Search Tool"),
    ("tools.web_scraper", "Web Scraper Tool"),
    ("tools.python_executor", "Python Executor Tool"),
    ("tools.file_writer", "File Writer Tool"),
    ("tools.json_formatter", "JSON Formatter Tool"),
]

print("\n3. Testing Tool Modules:")
print("-" * 70)
for module_name, display_name in tool_modules:
    try:
        __import__(module_name)
        print(f"✓ {display_name:30} - OK")
        success.append(module_name)
    except Exception as e:
        print(f"✗ {display_name:30} - FAILED: {str(e)}")
        errors.append((module_name, str(e)))

# Test support modules
support_modules = [
    ("memory.memory_system", "Memory System"),
    ("models.data_models", "Data Models"),
    ("evaluation.reflection", "Reflection Module"),
    ("agent_loop.state_machine", "State Machine"),
    ("structured_logging.structured_logger", "Structured Logger"),
]

print("\n4. Testing Support Modules:")
print("-" * 70)
for module_name, display_name in support_modules:
    try:
        __import__(module_name)
        print(f"✓ {display_name:30} - OK")
        success.append(module_name)
    except Exception as e:
        print(f"✗ {display_name:30} - FAILED: {str(e)}")
        errors.append((module_name, str(e)))

# Test UI module
print("\n5. Testing UI Module:")
print("-" * 70)
try:
    import ui.websocket_server
    print(f"✓ {'WebSocket Server':30} - OK")
    success.append("ui.websocket_server")
except Exception as e:
    print(f"✗ {'WebSocket Server':30} - FAILED: {str(e)}")
    errors.append(("ui.websocket_server", str(e)))

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✓ Successful imports: {len(success)}")
print(f"✗ Failed imports: {len(errors)}")

if errors:
    print("\n" + "=" * 70)
    print("ERRORS DETAILS")
    print("=" * 70)
    for module, error in errors:
        print(f"\nModule: {module}")
        print(f"Error: {error}")
    print("\n" + "=" * 70)
    sys.exit(1)
else:
    print("\n✓ ALL IMPORTS SUCCESSFUL!")
    print("=" * 70)
    sys.exit(0)
