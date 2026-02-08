# Models Module

This module defines the data models and schemas used throughout the application using Pydantic for validation and type safety.

## Overview

The models module provides strongly-typed data structures for:
- Agent inputs and outputs
- Research results
- Confidence scores
- Session data
- Tool execution records

## Data Models

### AgentContext

Input context provided to agents for execution.

```python
@dataclass
class AgentContext:
    task_id: str                              # Unique task identifier
    task_description: str                     # What the agent should do
    previous_outputs: Dict[str, AgentOutput]  # Outputs from previous agents
    retry_count: int                          # Current retry attempt
    session_id: str                           # Session identifier
```

**Usage:**
```python
context = AgentContext(
    task_id="task_001",
    task_description="Research AI trends",
    previous_outputs={},
    retry_count=0,
    session_id="session_123"
)
```

### AgentOutput

Output produced by agent execution.

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

**Usage:**
```python
output = AgentOutput(
    agent_name="research_agent",
    task_id="task_001",
    results={
        "summary": "AI trends include...",
        "findings": [...]
    },
    reasoning="Searched 5 sources and analyzed content",
    sources=["https://example.com"],
    self_confidence=85,
    timestamp="2024-01-01T00:00:00Z"
)
```

### ResearchResult

Final aggregated research output.

```python
@dataclass
class ResearchResult:
    session_id: str                           # Session identifier
    goal: str                                 # Research goal
    timestamp: str                            # ISO 8601 timestamp
    agents_involved: List[str]                # Agents that participated
    confidence_scores: Dict[str, Dict]        # Confidence scores by agent
    competitors: List[Dict[str, Any]]         # Competitor information
    insights: List[str]                       # Key insights
    sources: List[Dict[str, str]]             # Source information
    recommendations: List[Any]                # Strategic recommendations
    overall_confidence: int                   # Overall confidence (0-100)
```

**Usage:**
```python
result = ResearchResult(
    session_id="session_123",
    goal="Research AI trends",
    timestamp="2024-01-01T00:00:00Z",
    agents_involved=["research_agent", "analyst_agent"],
    confidence_scores={
        "research_agent": {"overall": 85, "self": 85, "boss": 88}
    },
    competitors=[],
    insights=["AI adoption is accelerating"],
    sources=[{"url": "https://example.com", "type": "web"}],
    recommendations=["Invest in AI capabilities"],
    overall_confidence=87
)
```

### ConfidenceScore

Confidence evaluation with factors and reasoning.

```python
@dataclass
class ConfidenceScore:
    overall: float                    # Overall confidence (0.0-1.0)
    factors: Dict[str, float]         # Individual factor scores
    agent_type: str                   # Agent identifier
    reasoning: str                    # Explanation
```

**Usage:**
```python
score = ConfidenceScore(
    overall=0.85,
    factors={
        "source_count": 0.9,
        "source_diversity": 0.8,
        "content_quality": 0.85
    },
    agent_type="research_agent",
    reasoning="High quality sources with good diversity"
)
```

## Validation

All models include validation:

```python
# Type checking
context = AgentContext(
    task_id=123,  # Error: must be string
    task_description="Research",
    previous_outputs={},
    retry_count=0,
    session_id="session_123"
)

# Range validation
output = AgentOutput(
    agent_name="research_agent",
    task_id="task_001",
    results={},
    reasoning="",
    sources=[],
    self_confidence=150,  # Error: must be 0-100
    timestamp="2024-01-01T00:00:00Z"
)
```

## Serialization

Models support JSON serialization:

```python
import json
from dataclasses import asdict

# To JSON
result_dict = asdict(result)
result_json = json.dumps(result_dict, indent=2)

# From JSON
result_data = json.loads(result_json)
result = ResearchResult(**result_data)
```

## Usage Patterns

### Creating Agent Context

```python
def create_context(
    task_id: str,
    description: str,
    session_id: str,
    previous_outputs: Optional[Dict] = None
) -> AgentContext:
    """Helper to create agent context"""
    return AgentContext(
        task_id=task_id,
        task_description=description,
        previous_outputs=previous_outputs or {},
        retry_count=0,
        session_id=session_id
    )
```

### Building Agent Output

```python
def create_output(
    agent_name: str,
    task_id: str,
    results: Dict,
    sources: List[str],
    confidence: int
) -> AgentOutput:
    """Helper to create agent output"""
    return AgentOutput(
        agent_name=agent_name,
        task_id=task_id,
        results=results,
        reasoning=f"Processed {len(sources)} sources",
        sources=sources,
        self_confidence=confidence,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
```

### Aggregating Results

```python
def aggregate_results(
    session_id: str,
    goal: str,
    outputs: Dict[str, AgentOutput],
    scores: Dict[str, ConfidenceScore]
) -> ResearchResult:
    """Aggregate agent outputs into final result"""
    
    # Extract insights
    insights = []
    for output in outputs.values():
        if "summary" in output.results:
            insights.append(output.results["summary"])
    
    # Calculate overall confidence
    overall = int(
        sum(s.overall for s in scores.values()) / len(scores) * 100
    )
    
    return ResearchResult(
        session_id=session_id,
        goal=goal,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        agents_involved=list(outputs.keys()),
        confidence_scores={
            name: {"overall": int(score.overall * 100)}
            for name, score in scores.items()
        },
        competitors=[],
        insights=insights,
        sources=[],
        recommendations=[],
        overall_confidence=overall
    )
```

## Best Practices

1. **Use Type Hints**: Always specify types for clarity
2. **Validate Early**: Check data at boundaries
3. **Immutable Data**: Use dataclasses with frozen=True when appropriate
4. **Clear Names**: Use descriptive field names
5. **Document Fields**: Add docstrings for complex fields
6. **Default Values**: Provide sensible defaults where appropriate
7. **Consistent Formats**: Use ISO 8601 for timestamps

## Testing

```bash
# Run model tests
pytest tests/unit/test_data_models.py -v

# Test with coverage
pytest tests/unit/test_data_models.py --cov=models
```

## Adding New Models

To add a new data model:

1. **Define the Model**

```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class MyNewModel:
    """Description of the model"""
    field1: str
    field2: int
    field3: List[str]
    field4: Dict[str, Any]
```

2. **Add Validation**

```python
@dataclass
class MyNewModel:
    field1: str
    field2: int
    
    def __post_init__(self):
        if self.field2 < 0:
            raise ValueError("field2 must be non-negative")
```

3. **Add Helper Methods**

```python
@dataclass
class MyNewModel:
    field1: str
    field2: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MyNewModel':
        """Create from dictionary"""
        return cls(**data)
```

4. **Add Tests**

```python
def test_my_new_model():
    model = MyNewModel(field1="test", field2=42)
    assert model.field1 == "test"
    assert model.field2 == 42
```

## Related Documentation

- [Agents](../agents/README.md) - Use models for inputs/outputs
- [Boss Agent](../boss_agent.py) - Aggregates results
- [Memory System](../memory/README.md) - Stores model data
- [Evaluation](../evaluation/README.md) - Uses confidence scores
