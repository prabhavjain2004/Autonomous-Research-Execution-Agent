"""
Main Entry Point for Autonomous Research Agent

This module provides both CLI and server modes for running the research agent system.

Usage:
    # Start web server
    python main.py server
    
    # Run CLI research
    python main.py cli "Research AI trends in 2024"
    
    # Show help
    python main.py --help
"""

import sys
import argparse
import asyncio
from typing import Optional

from boss_agent import BossAgent
from structured_logging.structured_logger import StructuredLogger
from memory.memory_system import MemorySystem
from config import Config
from output_formatter import OutputFormatter


def run_cli_research(goal: str, session_id: Optional[str] = None) -> None:
    """
    Run research in CLI mode.
    
    Args:
        goal: Research goal
        session_id: Optional session ID
    """
    print(f"\n{'='*80}")
    print(f"Autonomous Research Agent - CLI Mode")
    print(f"{'='*80}\n")
    print(f"Goal: {goal}\n")
    
    # Initialize components
    config = Config()
    
    logger = StructuredLogger(session_id="cli-session")
    memory = MemorySystem()
    
    # Create Model Router for LLM calls
    from model_router import ModelRouter
    model_router = ModelRouter(
        api_key=config.OPENROUTER_API_KEY,
        logger=logger
    )
    
    print(f"Initializing agents...\n")
    
    # Create Boss Agent with model router
    boss = BossAgent(
        logger=logger,
        memory_system=memory,
        model_router=model_router,
        max_retries=config.MAX_RETRY_ATTEMPTS,
        confidence_threshold=config.CONFIDENCE_THRESHOLD_PROCEED / 100.0
    )
    
    try:
        print("Starting research...\n")
        
        # Execute research (session_id is created internally)
        result = boss.execute_research(goal)
        
        # Get the actual session_id that was created
        actual_session_id = str(boss.session_id)
        
        # Format output
        formatter = OutputFormatter()
        
        print(f"\n{'='*80}")
        print(f"Research Complete!")
        print(f"{'='*80}\n")
        
        print(f"Overall Confidence: {result.overall_confidence}%\n")
        
        print(f"Agents Involved:")
        for agent in result.agents_involved:
            scores = result.confidence_scores.get(agent, {})
            print(f"  - {agent}: Self={scores.get('self', 0)}%, Boss={scores.get('boss', 0)}%")
        
        print(f"\nKey Insights ({len(result.insights)}):")
        for i, insight in enumerate(result.insights[:5], 1):
            print(f"  {i}. {insight}")
        if len(result.insights) > 5:
            print(f"  ... and {len(result.insights) - 5} more")
        
        print(f"\nRecommendations ({len(result.recommendations)}):")
        for i, rec in enumerate(result.recommendations[:5], 1):
            if isinstance(rec, dict):
                print(f"  {i}. {rec.get('text', str(rec))}")
            else:
                print(f"  {i}. {rec}")
        if len(result.recommendations) > 5:
            print(f"  ... and {len(result.recommendations) - 5} more")
        
        print(f"\nSources ({len(result.sources)}):")
        for i, source in enumerate(result.sources[:5], 1):
            print(f"  {i}. {source.get('url', 'N/A')}")
        if len(result.sources) > 5:
            print(f"  ... and {len(result.sources) - 5} more")
        
        print(f"\nResults saved to memory system.")
        print(f"Session ID: {actual_session_id}")
        print(f"\n{'='*80}\n")
        
    except KeyboardInterrupt:
        print("\n\nResearch interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during research: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """
    Run the web server.
    
    Args:
        host: Host address to bind to
        port: Port number
        reload: Enable auto-reload for development
    """
    print(f"\n{'='*80}")
    print(f"Autonomous Research Agent - Server Mode")
    print(f"{'='*80}\n")
    print(f"Starting server on http://{host}:{port}")
    print(f"Web UI available at: http://localhost:{port}")
    print(f"WebSocket endpoint: ws://localhost:{port}/ws")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    from ui.websocket_server import start_server
    
    try:
        start_server(host=host, port=port, reload=reload)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Autonomous Research Agent - Multi-Agent Research System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start web server
  python main.py server
  
  # Start server on custom port
  python main.py server --port 3000
  
  # Run CLI research
  python main.py cli "Research the latest trends in artificial intelligence"
  
  # Run CLI research with custom session ID
  python main.py cli "Research quantum computing" --session-id my-session-123
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Server mode
    server_parser = subparsers.add_parser('server', help='Start web server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    server_parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    server_parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    
    # CLI mode
    cli_parser = subparsers.add_parser('cli', help='Run research in CLI mode')
    cli_parser.add_argument('goal', help='Research goal')
    cli_parser.add_argument('--session-id', help='Optional session ID')
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    if args.mode == 'server':
        run_server(host=args.host, port=args.port, reload=args.reload)
    elif args.mode == 'cli':
        run_cli_research(args.goal, args.session_id)


if __name__ == "__main__":
    main()
