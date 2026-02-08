# Contributing to Autonomous Research Agent

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 🌟 Ways to Contribute

- **Bug Reports**: Report issues you encounter
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit pull requests with fixes or features
- **Documentation**: Improve or expand documentation
- **Testing**: Add or improve tests
- **Examples**: Create usage examples or tutorials

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/autonomous-research-agent.git
cd autonomous-research-agent
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
playwright install

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov hypothesis black flake8 mypy
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## 📝 Development Guidelines

### Code Style

We follow PEP 8 style guidelines:

```bash
# Format code with black
black .

# Check style with flake8
flake8 .

# Type checking with mypy
mypy .
```

### Code Standards

1. **Type Hints**: Use type hints for all function signatures
2. **Docstrings**: Document all public functions and classes
3. **Error Handling**: Handle errors gracefully with specific exceptions
4. **Logging**: Use structured logging for important events
5. **Testing**: Write tests for new functionality

### Example Code

```python
from typing import List, Dict, Any
from structured_logging.structured_logger import StructuredLogger

def process_data(
    data: List[Dict[str, Any]],
    logger: StructuredLogger
) -> Dict[str, Any]:
    """
    Process input data and return results.
    
    Args:
        data: List of data dictionaries to process
        logger: Logger instance for structured logging
    
    Returns:
        Dictionary containing processed results
    
    Raises:
        ValueError: If data is empty or invalid
    """
    if not data:
        raise ValueError("Data cannot be empty")
    
    logger.log_info(
        f"Processing {len(data)} items",
        {"item_count": len(data)}
    )
    
    try:
        # Process data
        results = {"processed": len(data)}
        return results
    except Exception as e:
        logger.log_error(
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace="",
            context={"data_count": len(data)}
        )
        raise
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_research_agent.py -v

# Run specific test
pytest tests/unit/test_research_agent.py::test_execute -v
```

### Writing Tests

Create tests in the `tests/` directory:

```python
import pytest
from agents.research_agent import ResearchAgent

def test_research_agent_initialization():
    """Test that research agent initializes correctly"""
    agent = ResearchAgent(
        logger=mock_logger,
        max_retries=2,
        model_router=mock_router
    )
    assert agent.agent_name == "research_agent"
    assert agent.max_retries == 2

def test_research_agent_execution():
    """Test research agent execution"""
    agent = ResearchAgent(...)
    context = AgentContext(...)
    output = agent.execute(context)
    
    assert output.agent_name == "research_agent"
    assert len(output.sources) > 0
    assert output.self_confidence > 0
```

### Test Coverage

Aim for:
- **Unit Tests**: 80%+ coverage
- **Integration Tests**: Key workflows
- **Property Tests**: Correctness properties

## 📚 Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Longer description if needed. Explain what the function does,
    any important details, and usage notes.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param2 is negative
        RuntimeError: When operation fails
    
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

### README Updates

When adding features:
1. Update main README.md
2. Update relevant module README.md
3. Add usage examples
4. Update configuration documentation

## 🔄 Pull Request Process

### 1. Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear

### 2. Commit Messages

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add web scraping timeout configuration"
git commit -m "Fix confidence calculation for analyst agent"
git commit -m "Update README with installation instructions"

# Bad
git commit -m "fix bug"
git commit -m "update"
git commit -m "changes"
```

### 3. Submit Pull Request

1. Push your branch to your fork
2. Open a pull request on GitHub
3. Fill out the PR template
4. Link related issues
5. Wait for review

### 4. PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] All existing tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Commit messages are clear
```

## 🐛 Bug Reports

### Before Reporting

1. Check existing issues
2. Verify it's reproducible
3. Test on latest version

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Windows 10]
- Python Version: [e.g., 3.10.5]
- Project Version: [e.g., 1.0.0]

**Logs**
Relevant log output or error messages

**Additional Context**
Any other relevant information
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Problem**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives**
Other solutions considered

**Additional Context**
Examples, mockups, or references
```

## 🏗️ Architecture Guidelines

### Adding New Agents

1. Create agent class in `agents/` directory
2. Inherit from `BaseAgent`
3. Implement required methods
4. Add confidence calculation
5. Create tests
6. Update documentation

See `agents/README.md` for detailed guide.

### Adding New Tools

1. Create tool class in `tools/` directory
2. Implement tool interface
3. Add error handling
4. Add rate limiting
5. Create tests
6. Update documentation

### Modifying State Machine

1. Update `agent_loop/state_machine.py`
2. Add new states if needed
3. Update transition logic
4. Add timeout handling
5. Update tests
6. Update documentation

## 📋 Code Review Checklist

Reviewers will check:

- [ ] Code quality and style
- [ ] Test coverage
- [ ] Documentation completeness
- [ ] Error handling
- [ ] Performance considerations
- [ ] Security implications
- [ ] Breaking changes
- [ ] Backward compatibility

## 🤝 Community Guidelines

### Be Respectful

- Be welcoming to newcomers
- Respect different viewpoints
- Accept constructive criticism
- Focus on what's best for the project

### Communication

- Use clear, concise language
- Provide context and examples
- Be patient and helpful
- Ask questions when unclear

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/autonomous-research-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/autonomous-research-agent/discussions)
- **Email**: your.email@example.com

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## 🙏 Thank You

Thank you for contributing to Autonomous Research Agent! Your contributions help make this project better for everyone.
