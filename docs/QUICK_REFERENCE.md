# Quick Reference Card

Essential commands and information for working with the Autonomous Research Agent.

## Installation

```bash
# Clone repository
git clone https://github.com/prabhavjain2004/Autonomous-Research-Execution-Agent.git
cd Autonomous-Research-Execution-Agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
playwright install

# Configure environment
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux
# Edit .env and add OPENROUTER_API_KEY
```

## Running the Application

```bash
# Web server mode (recommended)
python run.py server

# Custom host/port
python run.py server --host 0.0.0.0 --port 3000

# CLI mode
python run.py cli "Your research goal here"

# CLI with session ID
python run.py cli "Research topic" --session-id my-session
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m property      # Property-based tests only

# Run specific test file
pytest tests/unit/test_agents.py

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Project Structure

```
├── src/                # All application code
│   ├── agents/        # AI agents
│   ├── tools/         # Tool implementations
│   ├── ui/            # Web interface
│   └── main.py        # Entry point
├── tests/             # All tests
├── docs/              # Documentation
├── run.py             # Launcher
└── requirements.txt   # Dependencies
```

## Key Files

| File | Purpose |
|------|---------|
| `run.py` | Application launcher |
| `src/main.py` | Main entry point |
| `src/boss_agent.py` | Boss agent orchestrator |
| `src/config.py` | Configuration management |
| `.env` | Environment variables (DO NOT COMMIT) |
| `.env.example` | Environment template |
| `requirements.txt` | Python dependencies |
| `pytest.ini` | Test configuration |

## Environment Variables

```env
# Required
OPENROUTER_API_KEY=your_key_here

# Optional (with defaults)
DATABASE_PATH=./data/agent_memory.db
LOG_DIR=./logs
LOG_LEVEL=INFO
CONFIDENCE_THRESHOLD_PROCEED=80
CONFIDENCE_THRESHOLD_CRITICAL=60
MAX_RETRY_ATTEMPTS=2
UI_HOST=0.0.0.0
UI_PORT=8000
```

## Common Tasks

### Add New Agent
1. Create file in `src/agents/`
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Register with Boss Agent
5. Add tests in `tests/unit/`

### Add New Tool
1. Create file in `src/tools/`
2. Implement tool interface
3. Add to tool registry
4. Add tests in `tests/unit/`

### Add Documentation
1. Create `.md` file in `docs/`
2. Update `docs/README.md` index
3. Link from main `README.md` if needed

## Debugging

```bash
# Check setup
python tests/validate_setup.py

# View logs
# Check logs/ directory for session logs

# Database inspection
sqlite3 data/agent_memory.db
# .tables
# .schema sessions
# SELECT * FROM sessions;
```

## Git Workflow

```bash
# Check status
git status

# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push
git push origin main

# Pull latest
git pull origin main
```

## Troubleshooting

### Import Errors
- Always use `python run.py`, not `python src/main.py`
- Check that `src/` is in Python path

### API Errors
- Verify `OPENROUTER_API_KEY` in `.env`
- Check API key is valid at openrouter.ai
- Ensure no rate limiting

### Test Failures
- Run `pytest -v` for detailed output
- Check if dependencies are installed
- Verify Python version is 3.10+

### Web UI Not Loading
- Check if port 8000 is available
- Try different port: `python run.py server --port 3000`
- Check firewall settings

## Useful Links

- [Main README](../README.md)
- [Architecture](ARCHITECTURE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Migration Guide](MIGRATION_GUIDE.md)
- [OpenRouter](https://openrouter.ai/)
- [GitHub Repository](https://github.com/prabhavjain2004/Autonomous-Research-Execution-Agent)

## Support

- **Issues**: [GitHub Issues](https://github.com/prabhavjain2004/Autonomous-Research-Execution-Agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/prabhavjain2004/Autonomous-Research-Execution-Agent/discussions)

---

**Last Updated**: February 8, 2026
