# 🤖 Autonomous Research & Execution Agent

> A free, open-source multi-agent AI system for autonomous research and strategic analysis powered by OpenRouter

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenRouter](https://img.shields.io/badge/Powered%20by-OpenRouter-green.svg)](https://openrouter.ai/)

## 🌟 Overview

This is a production-grade multi-agent system that autonomously researches topics, analyzes findings, and generates strategic recommendations. Built with a boss-worker architecture, it orchestrates specialized AI agents to deliver comprehensive research results with confidence scoring and quality control.

**Key Highlights:**
- 🆓 **Completely Free** - Uses OpenRouter's free tier models
- 🤖 **Multi-Agent System** - Boss agent orchestrates Research, Analyst, and Strategy agents
- 🎯 **Confidence-Based Quality Control** - Dual scoring (self + boss evaluation) with automatic replanning
- 🧠 **Intelligent Model Routing** - Automatic selection of optimal models based on task complexity
- 🌐 **Real-Time Web UI** - Live monitoring with WebSocket communication
- 💾 **Session Memory** - SQLite persistence for audit trails and knowledge reuse
- 🛠️ **Comprehensive Tools** - Web search, scraping, Python execution, and more

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

> **New to the project?** Check out our [Quick Start Guide](QUICK_START.md) for a 5-minute setup!

## ✨ Features

### Core Capabilities
- **Multi-Agent Orchestration**: Boss agent delegates tasks to specialized agents (Research, Analyst, Strategy)
- **Confidence Scoring**: Dual evaluation system with self-assessment and boss review
- **Automatic Replanning**: Low-confidence outputs trigger automatic retries with improved strategies
- **Intelligent Model Selection**: Routes tasks to appropriate OpenRouter models based on complexity
- **State Machine Control**: Explicit state transitions with timeout handling and error recovery
- **Session Persistence**: All decisions, outputs, and confidence scores stored in SQLite
- **Real-Time Monitoring**: Web UI with live updates via WebSockets
- **Comprehensive Logging**: Structured JSON logs with session isolation

### Tool System
- **Web Search**: Tavily API (primary), DuckDuckGo, and Google search integration
- **Web Scraping**: BeautifulSoup, Playwright, and Trafilatura for content extraction
- **Python Execution**: Safe code execution in isolated environment
- **File Operations**: Read/write capabilities for data persistence
- **JSON Formatting**: Structured output with schema validation

### Quality Assurance
- **423 Passing Tests**: Comprehensive unit, property, and integration tests
- **Type Safety**: Full type hints throughout codebase
- **Error Handling**: Exponential backoff and retry logic
- **Rate Limiting**: Prevents API throttling
- **Timeout Management**: Prevents hanging operations

## 🏗️ Architecture

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

## 🚀 Quick Start

Get up and running in 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/autonomous-research-agent.git
cd autonomous-research-agent

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
playwright install

# 4. Configure environment
copy .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# 5. Run the web server
python main.py server

# 6. Open browser to http://localhost:8000
```

## 📦 Installation

### Prerequisites

- **Python 3.10 or higher** - [Download Python](https://www.python.org/downloads/)
- **OpenRouter API Key** - [Get free API key](https://openrouter.ai/)

### Step-by-Step Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/autonomous-research-agent.git
cd autonomous-research-agent
```

#### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Install Playwright Browsers

Playwright is used for advanced web scraping:

```bash
playwright install
```

This downloads Chromium, Firefox, and WebKit browsers (~300MB).

#### 5. Configure Environment Variables

Copy the example environment file:

```bash
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux
```

Edit `.env` and add your OpenRouter API key:

```env
OPENROUTER_API_KEY=your_api_key_here
```

**Get your free OpenRouter API key:**
1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste into `.env` file

#### 6. Create Required Directories

The system will create these automatically, but you can create them manually:

```bash
mkdir data logs outputs
```

## ⚙️ Configuration

All configuration is managed through environment variables in the `.env` file:

### Required Settings

```env
# OpenRouter API Key (REQUIRED)
OPENROUTER_API_KEY=your_api_key_here
```

### Optional Settings

```env
# Database
DATABASE_PATH=./data/agent_memory.db

# Logging
LOG_DIR=./logs
LOG_LEVEL=INFO

# Confidence Thresholds
CONFIDENCE_THRESHOLD_PROCEED=80
CONFIDENCE_THRESHOLD_CRITICAL=60
MAX_RETRY_ATTEMPTS=2

# Rate Limiting
RATE_LIMIT_DELAY=2.5

# Web UI
UI_HOST=0.0.0.0
UI_PORT=8000

# Timeouts (seconds)
TIMEOUT_PLANNING=30
TIMEOUT_TOOL_EXECUTION=120
TIMEOUT_OBSERVATION=20
```

See `.env.example` for complete list of configuration options.

## 🎯 Usage

### Web Server Mode (Recommended)

Start the web server for interactive research with real-time monitoring:

```bash
python main.py server
```

Then open your browser to `http://localhost:8000`

**Web UI Features:**
- Submit research goals
- Monitor agent execution in real-time
- View confidence scores and evaluations
- Browse session history
- Export results

**Custom host/port:**
```bash
python main.py server --host 0.0.0.0 --port 3000
```

### CLI Mode

Run research directly from command line:

```bash
python main.py cli "Research the latest trends in artificial intelligence"
```

**With custom session ID:**
```bash
python main.py cli "Research quantum computing" --session-id my-session-123
```

**Example output:**
```
================================================================================
Autonomous Research Agent - CLI Mode
================================================================================

Goal: Research the latest trends in artificial intelligence

Initializing agents...
Starting research...

================================================================================
Research Complete!
================================================================================

Overall Confidence: 87%

Agents Involved:
  - research_agent: Self=85%, Boss=88%
  - analyst_agent: Self=89%, Boss=86%
  - strategy_agent: Self=88%, Boss=87%

Key Insights (5):
  1. Research: AI adoption accelerating across industries...
  2. Large language models showing breakthrough capabilities...
  ...

Results saved to memory system.
Session ID: abc123-def456-ghi789
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

## 📁 Project Structure

```
autonomous-research-agent/
├── agents/                 # Specialized AI agents
│   ├── base_agent.py      # Base agent class
│   ├── research_agent.py  # Web research specialist
│   ├── analyst_agent.py   # Data analysis specialist
│   ├── strategy_agent.py  # Strategy generation specialist
│   └── README.md          # Agent documentation
├── agent_loop/            # State machine and execution control
│   ├── state_machine.py   # State transitions and timeouts
│   └── README.md          # State machine documentation
├── evaluation/            # Confidence scoring and reflection
│   ├── reflection.py      # Confidence evaluation logic
│   └── README.md          # Evaluation documentation
├── memory/                # Session persistence
│   ├── memory_system.py   # SQLite database interface
│   └── README.md          # Memory system documentation
├── models/                # Data models and schemas
│   ├── data_models.py     # Pydantic models
│   └── README.md          # Data models documentation
├── boss_agent.py          # Boss agent orchestrator
├── model_router.py        # OpenRouter model selection
├── config.py              # Configuration management
├── error_handling.py      # Error handling utilities
├── main.py                # Application entry point
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🔍 How It Works

### 1. Research Workflow

```
User Goal → Boss Agent → Research Agent → Analyst Agent → Strategy Agent → Results
```

### 2. Confidence-Based Quality Control

Each agent output is evaluated twice:
1. **Self-Assessment**: Agent evaluates its own output
2. **Boss Evaluation**: Boss agent independently reviews using LLM

The **lower** of the two scores is used (conservative approach).

**Decision Logic:**
- Score ≥ 80%: Proceed to next phase
- Score 60-79%: Replan and retry (up to 2 times)
- Score < 60%: Error recovery or fail

### 3. Model Selection

The system automatically selects the best OpenRouter model based on task complexity:

- **Simple tasks**: Fast, efficient models
- **Medium tasks**: Balanced models
- **Complex tasks**: Most capable models (Gemma 12B)

All models are from OpenRouter's **free tier**.

### 4. State Machine

The system uses explicit state transitions:

```
IDLE → PLANNING → TOOL_EXECUTION → OBSERVATION → REFLECTION 
     → CONFIDENCE_EVALUATION → [PROCEED | REPLAN | ERROR_RECOVERY]
```

Each state has timeout protection to prevent hanging.

### 5. Memory System

All data is persisted to SQLite:
- Sessions (research goals, timestamps, status)
- Agent decisions and reasoning
- Tool executions and results
- Confidence scores (self + boss)
- Final research results

## 🛠️ Development

### Code Quality Standards

- **Python 3.10+** with type hints
- **PEP8** style guidelines
- **Docstrings** for all public APIs
- **No global mutable state**
- **Comprehensive error handling**
- **Rate limiting** for external APIs
- **Unit tests** for all modules

### Testing Strategy

- **Unit Tests**: Test components in isolation
- **Property Tests**: Test correctness properties (Hypothesis)
- **Integration Tests**: Test end-to-end workflows

### Adding New Agents

1. Create new agent class in `agents/` directory
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Add confidence calculation logic
5. Register with Boss Agent
6. Add tests

See `agents/README.md` for detailed guide.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code of conduct
- Development setup
- Coding standards
- Testing requirements
- Pull request process

Quick contribution checklist:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

You are free to:
- Use commercially
- Modify
- Distribute
- Use privately

Under the condition of including the license and copyright notice.

## 🙏 Acknowledgments

- **OpenRouter** - For providing free access to powerful AI models
- **FastAPI** - For the excellent web framework
- **Playwright** - For robust web scraping capabilities
- All open-source contributors

## 📞 Support

Need help? Here's how to get support:

### Documentation
- [Quick Start Guide](QUICK_START.md) - Get started in 5 minutes
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Module READMEs](agents/README.md) - Detailed component documentation

### Community
- **Issues**: [Report bugs or request features](https://github.com/yourusername/autonomous-research-agent/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/yourusername/autonomous-research-agent/discussions)
- **Pull Requests**: [Contribute code](https://github.com/yourusername/autonomous-research-agent/pulls)

### Common Questions

**Q: Is this really free?**  
A: Yes! The project is open-source (MIT License) and uses OpenRouter's free tier models.

**Q: Do I need a credit card?**  
A: No credit card required for OpenRouter's free tier.

**Q: What models does it use?**  
A: It uses various models from OpenRouter's free tier, automatically selected based on task complexity.

**Q: Can I use my own API keys?**  
A: Yes, you can configure any OpenRouter-compatible API key.

**Q: How do I report a bug?**  
A: Open an issue on GitHub with details about the problem and steps to reproduce.

## 🗺️ Roadmap

- [ ] Add more specialized agents (Financial, Technical, etc.)
- [ ] Implement caching for repeated queries
- [ ] Add export formats (PDF, Markdown, JSON)
- [ ] Multi-language support
- [ ] Docker containerization
- [ ] Cloud deployment guides

---

**Made with ❤️ by the community | Powered by OpenRouter's free tier**
