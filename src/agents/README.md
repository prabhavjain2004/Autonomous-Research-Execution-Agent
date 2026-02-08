# Agents Module

This module contains the specialized AI agents that perform different aspects of the research workflow.

## Overview

The agents module implements a multi-agent architecture where each agent specializes in a specific task:

- **Research Agent**: Gathers information from web sources
- **Analyst Agent**: Analyzes and synthesizes research findings
- **Strategy Agent**: Generates actionable recommendations
- **Base Agent**: Abstract base class providing common functionality

## Architecture

```
BaseAgent (Abstract)
    ├── ResearchAgent
    ├── AnalystAgent
    └── StrategyAgent
```

## Agent Classes

### BaseAgent

Abstract base class that all agents inherit from.

**Key Features:**
- Standardized execution interface
- Retry count management
- Confidence calculation framework
- Tool execution capabilities
- Error handling

**Methods:**
- `execute(context: AgentContext) -> AgentOutput`: Main execution method (abstract)
- `calculate_confidence(output: AgentOutput) -> ConfidenceScore`: Evaluate output quality
- `increment_retry_count()`: Track retry attempts
- `reset_retry_count()`: Reset for new execution

### ResearchAgent

Specializes in gathering information from web sources.

**Capabilities:**
- Web search (DuckDuckGo, Google)
- Content scraping (BeautifulSoup, Playwright)
- Source validation
- Information extraction

**Confidence Factors:**
- Number of sources found
- Source diversity
- Content quality
- Search success rate

### AnalystAgent

Analyzes research findings and extracts insights.

**Capabilities:**
- Data synthesis
- Pattern recognition
- Insight extraction
- Trend analysis

**Confidence Factors:**
- Analysis depth
- Insight quality
- Data coverage
- Reasoning clarity

### StrategyAgent

Generates actionable recommendations based on analysis.

**Capabilities:**
- Strategy formulation
- Recommendation generation
- Action plan creation
- Priority assessment

**Confidence Factors:**
- Recommendation specificity
- Actionability
- Strategic alignment
- Feasibility

## Usage Example

```python
from agents.research_agent import ResearchAgent
from agents.base_agent import AgentContext
from structured_logging.structured_logger import StructuredLogger
from model_router import ModelRouter

# Initialize components
logger = StructuredLogger(session_id="example")
model_router = ModelRouter(api_key="your_key", logger=logger)

# Create agent
agent = ResearchAgent(
    logger=logger,
    max_retries=2,
    model_router=model_router
)

# Create context
context = AgentContext(
    task_id="task_001",
    task_description="Research AI trends in 2024",
    previous_outputs={},
    retry_count=0,
    session_id="example"
)

# Execute
output = agent.execute(context)

# Evaluate confidence
confidence = agent.calculate_confidence(output)
print(f"Confidence: {confidence.overall * 100}%")
```

## Agent Output Format

All agents return an `AgentOutput` object:

```python
@dataclass
class AgentOutput:
    agent_name: str              # Name of the agent
    task_id: str                 # Task identifier
    results: Dict[str, Any]      # Agent-specific results
    reasoning: str               # Explanation of approach
    sources: List[str]           # Data sources used
    self_confidence: int         # Self-assessed confidence (0-100)
    timestamp: str               # ISO 8601 timestamp
```

## Confidence Scoring

Each agent calculates confidence based on multiple factors:

```python
@dataclass
class ConfidenceScore:
    overall: float                    # Overall confidence (0.0-1.0)
    factors: Dict[str, float]         # Individual factor scores
    agent_type: str                   # Agent identifier
    reasoning: str                    # Explanation
```

**Common Factors:**
- Data quality
- Source reliability
- Completeness
- Consistency
- Reasoning clarity

## Adding New Agents

To create a new specialized agent:

1. **Create Agent Class**

```python
from agents.base_agent import BaseAgent, AgentContext, AgentOutput
from evaluation.reflection import ConfidenceScore

class MyCustomAgent(BaseAgent):
    def __init__(self, logger, max_retries, model_router):
        super().__init__(
            agent_name="my_custom_agent",
            logger=logger,
            max_retries=max_retries,
            model_router=model_router
        )
    
    def execute(self, context: AgentContext) -> AgentOutput:
        # Implement your agent logic
        pass
    
    def calculate_confidence(self, output: AgentOutput) -> ConfidenceScore:
        # Implement confidence calculation
        pass
```

2. **Implement Execute Method**

```python
def execute(self, context: AgentContext) -> AgentOutput:
    # Log start
    self.logger.log_info(
        f"{self.agent_name} starting execution",
        {"task_id": context.task_id}
    )
    
    # Perform work
    results = self._do_work(context)
    
    # Create output
    return AgentOutput(
        agent_name=self.agent_name,
        task_id=context.task_id,
        results=results,
        reasoning="Explanation of approach",
        sources=["source1", "source2"],
        self_confidence=85,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
```

3. **Implement Confidence Calculation**

```python
def calculate_confidence(self, output: AgentOutput) -> ConfidenceScore:
    factors = {
        "quality": 0.9,
        "completeness": 0.8,
        "reliability": 0.85
    }
    
    overall = sum(factors.values()) / len(factors)
    
    return ConfidenceScore(
        overall=overall,
        factors=factors,
        agent_type=self.agent_name,
        reasoning="High quality output with good coverage"
    )
```

4. **Register with Boss Agent**

```python
# In boss_agent.py
self.my_custom_agent = MyCustomAgent(
    logger=logger,
    max_retries=max_retries,
    model_router=model_router
)
```

5. **Add Tests**

```python
# tests/unit/test_my_custom_agent.py
def test_my_custom_agent_execution():
    agent = MyCustomAgent(logger, max_retries=2, model_router)
    context = AgentContext(...)
    output = agent.execute(context)
    assert output.agent_name == "my_custom_agent"
```

## Best Practices

1. **Error Handling**: Always wrap agent logic in try-except blocks
2. **Logging**: Log all major decisions and state changes
3. **Confidence**: Be conservative in confidence scoring
4. **Sources**: Always track and return data sources
5. **Reasoning**: Provide clear explanations of agent decisions
6. **Retries**: Implement retry logic for transient failures
7. **Timeouts**: Set reasonable timeouts for long-running operations

## Testing

Run agent tests:

```bash
# All agent tests
pytest tests/unit/test_*_agent.py

# Specific agent
pytest tests/unit/test_research_agent.py -v

# With coverage
pytest tests/unit/test_*_agent.py --cov=agents
```

## Dependencies

- `model_router`: For LLM API calls
- `structured_logging`: For logging
- `memory`: For persistence
- `evaluation`: For confidence scoring
- `models`: For data structures

## Configuration

Agents respect these environment variables:

```env
MAX_RETRY_ATTEMPTS=2
CONFIDENCE_THRESHOLD_PROCEED=80
RATE_LIMIT_DELAY=2.5
```

## Performance Considerations

- **Rate Limiting**: All agents respect rate limits to avoid API throttling
- **Caching**: Consider caching repeated queries
- **Parallel Execution**: Agents can run in parallel when independent
- **Resource Management**: Clean up resources (connections, files) properly

## Troubleshooting

**Agent returns low confidence:**
- Check input quality
- Verify data sources are accessible
- Review agent logs for errors
- Ensure sufficient context provided

**Agent execution fails:**
- Check API keys and credentials
- Verify network connectivity
- Review error logs
- Check rate limits

**Slow execution:**
- Review timeout settings
- Check network latency
- Consider caching strategies
- Optimize tool usage

## Related Documentation

- [Boss Agent](../boss_agent.py) - Agent orchestration
- [State Machine](../agent_loop/README.md) - Execution control
- [Evaluation](../evaluation/README.md) - Confidence scoring
- [Memory System](../memory/README.md) - Data persistence
