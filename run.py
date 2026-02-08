#!/usr/bin/env python3
"""
Launcher script for Autonomous Research Agent.
This script allows running the application from the root directory.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run main
if __name__ == "__main__":
    from main import main
    main()
