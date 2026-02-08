# System Architecture

## Overview

The Autonomous Research Agent is built using a multi-agent architecture with a boss-worker pattern. This document describes the system's design, components, and data flow.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web UI Layer                             │
│  (HTML/CSS/JS - Real-time status, logs, confidence viz)         │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      Boss Agent                                  │
│  • Orchestrates workflow                                         │
│  • Evaluates outputs (Boss confidence score)                     │
│  • Manages state transitions                                     │
│  • Delegates to specialized agents                               │
└─────┬──────────────┬──────────────┬────────────────────────────┘
      │              │              │
┌─────▼─────┐  ┌────▼─────┐  ┌────▼──────┐
│ Research  │  │ Analyst  │  │ Strategy  │
│  Agent    │  │  Agent   │  │  Agent    │
└─────┬─────┘  └────┬─────┘  └────┬──────┘
      │              │              │
┌─────▼──────────────────▼──────────────────▼──────────────────┐
│                      Tool System                               │
│  • Web Search (Tavily API, DuckDuckGo, Google)               │
│  • Web Scraping (BeautifulSoup, Playwright, Trafilatura)     │
│  • Python Execution                                            │
│  • File Writer                                                 │
│  • JSON Formatter                                              │
└────────────────────────┬───────────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────────┐
│                  Supporting Systems                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Model Router │  │ Memory       │  │ Logging      │        │
│  │ (OpenRouter) │  │ (SQLite)     │  │ (Structured) │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Boss Agent (`src/boss_agent.py`)
- Orchestrates the entire research workflow
- Delegates tasks to specialized agents
- Evaluates agent outputs with confidence scoring
- Manages state transitions and error recovery
- Makes final decisions on proceeding or replanning

### 2. Specialized Agents (`src/agents/`)
- **Research Agent**: Gathers information from web sources
- **Analyst Agent**: Analyzes and synthesizes research data
- **Strategy Agent**: Generates strategic recommendations
- All inherit from `BaseAgent` with common interface

### 3. State Machine (`src/agent_loop/state_machine.py`)
- Manages explicit state transitions
- Prevents infinite loops with timeout protection
- States: IDLE → PLANNING → TOOL_EXECUTION → OBSERVATION → REFLECTION → CONFIDENCE_EVALUATION

### 4. Model Router (`src/model_router.py`)
- Selects optimal OpenRouter model based on task complexity
- Handles API communication with retry logic
- Manages rate limiting and error handling

### 5. Memory System (`src/memory/memory_system.py`)
- SQLite database for session persistence
- Stores decisions, outputs, confidence scores
- Enables audit trails and knowledge reuse

### 6. Tool System (`src/tools/`)
- Modular tool architecture
- Each tool has execute() method
- Tools: Search, Scraper, Python Executor, File Writer, JSON Formatter

### 7. Web UI (`src/ui/`)
- FastAPI backend with WebSocket support
- Real-time monitoring of agent execution
- Session history and result visualization

## Data Flow

### Research Workflow

1. **User Input** → Goal submitted via Web UI or CLI
2. **Boss Agent** → Creates session, initializes state machine
3. **Planning Phase** → Boss delegates to Research Agent
4. **Research Phase** → Research Agent uses search tools
5. **Analysis Phase** → Analyst Agent processes findings
6. **Strategy Phase** → Strategy Agent generates recommendations
7. **Evaluation** → Each output gets dual confidence scoring
8. **Decision** → Proceed, Replan, or Error Recovery
9. **Results** → Stored in memory, displayed to user

### Confidence Scoring Flow

```
Agent Output
    ↓
Self-Assessment (Agent evaluates own work)
    ↓
Boss Evaluation (Boss independently reviews)
    ↓
Final Score = min(self_score, boss_score)
    ↓
Decision Logic:
  - Score ≥ 80%: Proceed
  - Score 60-79%: Replan
  - Score < 60%: Error Recovery
```

## Design Principles

1. **Separation of Concerns**: Each component has a single responsibility
2. **Explicit State Management**: No implicit state transitions
3. **Conservative Quality Control**: Use minimum of two confidence scores
4. **Fail-Safe Defaults**: Timeout protection, retry logic, error recovery
5. **Observability**: Comprehensive logging and monitoring
6. **Modularity**: Easy to add new agents and tools

## Technology Stack

- **Language**: Python 3.10+
- **Web Framework**: FastAPI
- **Database**: SQLite
- **LLM Provider**: OpenRouter
- **Web Scraping**: Playwright, BeautifulSoup, Trafilatura
- **Testing**: Pytest, Hypothesis
- **Type Checking**: Python type hints

## Security Considerations

- API keys stored in environment variables
- No secrets in code or version control
- Rate limiting to prevent abuse
- Timeout protection against hanging operations
- Input validation on all user inputs

## Performance Characteristics

- **Latency**: 30-120 seconds per research task (depends on complexity)
- **Throughput**: Single-threaded, one research at a time
- **Memory**: ~100MB base + model inference overhead
- **Storage**: SQLite database grows with session history

## Future Enhancements

- Parallel agent execution
- Caching for repeated queries
- Multi-language support
- Cloud deployment options
- Advanced visualization
