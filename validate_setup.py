"""
Validation script to verify project setup is complete and correct.

This script checks that all required directories, files, and configurations
are in place before starting development.
"""

import os
import sys
from pathlib import Path


def check_directory(path: str) -> bool:
    """Check if a directory exists."""
    exists = os.path.isdir(path)
    status = "✓" if exists else "✗"
    print(f"  {status} {path}/")
    return exists


def check_file(path: str) -> bool:
    """Check if a file exists."""
    exists = os.path.isfile(path)
    status = "✓" if exists else "✗"
    print(f"  {status} {path}")
    return exists


def main():
    """Run validation checks."""
    print("=== Project Setup Validation ===\n")
    
    all_checks_passed = True
    
    # Check required directories
    print("Checking directories...")
    required_dirs = [
        "planner",
        "tools",
        "memory",
        "agent_loop",
        "evaluation",
        "structured_logging",
        "ui",
        "tests",
        "tests/unit",
        "tests/property",
        "tests/integration",
    ]
    
    for directory in required_dirs:
        if not check_directory(directory):
            all_checks_passed = False
    
    print()
    
    # Check required files
    print("Checking core files...")
    required_files = [
        "config.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
        "pytest.ini",
        "setup.sh",
        "setup.bat",
    ]
    
    for file in required_files:
        if not check_file(file):
            all_checks_passed = False
    
    print()
    
    # Check module __init__.py files
    print("Checking module initialization files...")
    init_files = [
        "planner/__init__.py",
        "tools/__init__.py",
        "memory/__init__.py",
        "agent_loop/__init__.py",
        "evaluation/__init__.py",
        "structured_logging/__init__.py",
        "ui/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/property/__init__.py",
        "tests/integration/__init__.py",
    ]
    
    for file in init_files:
        if not check_file(file):
            all_checks_passed = False
    
    print()
    
    # Check if .env exists (optional but recommended)
    print("Checking optional files...")
    if os.path.isfile(".env"):
        print("  ✓ .env (configured)")
    else:
        print("  ⚠ .env (not configured - copy from .env.example)")
    
    print()
    
    # Check if data directories exist (optional, created at runtime)
    print("Checking runtime directories (optional)...")
    runtime_dirs = ["data", "logs", "outputs"]
    for directory in runtime_dirs:
        if os.path.isdir(directory):
            print(f"  ✓ {directory}/")
        else:
            print(f"  ⚠ {directory}/ (will be created at runtime)")
    
    print()
    
    # Try importing config
    print("Checking Python imports...")
    try:
        import config
        print("  ✓ config module imports successfully")
    except Exception as e:
        print(f"  ✗ config module import failed: {e}")
        all_checks_passed = False
    
    print()
    
    # Final result
    print("=" * 40)
    if all_checks_passed:
        print("✓ All required checks passed!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure your API key")
        print("2. Run setup.sh (Linux/Mac) or setup.bat (Windows)")
        print("3. Start implementing the next tasks")
        return 0
    else:
        print("✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
