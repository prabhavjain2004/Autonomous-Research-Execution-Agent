# Evaluation Module

This module implements confidence scoring and reflection capabilities for evaluating agent output quality.

## Overview

The evaluation system provides dual confidence assessment:
1. **Self-Assessment**: Agents evaluate their own outputs
2. **Boss Evaluation**: Boss agent independently reviews outputs using LLM

The system uses the **lower** of the two scores for conservative decision-making.

## Components

### ReflectionModule

Main class for evaluating agent outputs and making proceed/replan/error decisions.

```python
from evaluation.reflection import ReflectionModule, ConfidenceScore

# Initialize
reflection = ReflectionModule(
    high_confidence_threshold=0.80,  # 80% to proceed
    low_confidence_threshold=0.60    # Below 60% triggers error recovery
)

# Evaluate output
evaluation = reflection.evaluate_output(
    agent_output=output,
    confidence_score=score
)

# Check decision
if evaluation["should_proceed"]:
    # High confidence, continue
    pass
elif evaluation["should_replan"]:
    # Low confidence, retry
    pass
elif evaluation["should_error_recover"]:
    # Very low confidence, error recovery
    pass
```

### ConfidenceScore

Data class representing confidence evaluation:

```python
@dataclass
class ConfidenceScore:
    overall: float                    # Overall confidence (0.0-1.0)
    factors: Dict[str, float]         # Individual factor scores
    agent_type: str                   # Agent identifier
    reasoning: str                    # Explanation
```

## Confidence Factors

Different agents use different confidence factors:

### Research Agent
- **source_count**: Number of sources found
- **source_diversity**: Variety of source types
- **content_quality**: Quality of extracted content
- **search_success**: Success rate of searches

### Analyst Agent
- **analysis_depth**: Thoroughness of analysis
- **insight_quality**: Quality of insights
- **data_coverage**: Completeness of data
- **reasoning_clarity**: Clarity of reasoning

### Strategy Agent
- **recommendation_count**: Number of recommendations
- **specificity**: Level of detail
- **actionability**: How actionable recommendations are
- **strategic_alignment**: Alignment with goals

## Decision Logic

```
Confidence Score → Decision
─────────────────────────────
≥ 80%            → PROCEED
60% - 79%        → REPLAN
< 60%            → ERROR_RECOVERY
```

## Usage Examples

### Basic Evaluation

```python
from evaluation.reflection import ReflectionModule, ConfidenceScore
from models.data_models import AgentOutput

# Create reflection module
reflection = ReflectionModule(
    high_confidence_threshold=0.80,
    low_confidence_threshold=0.60
)

# Agent output
output = AgentOutput(
    agent_name="research_agent",
    task_id="task_001",
    results={"findings": [...]},
    reasoning="Found 10 sources...",
    sources=["url1", "url2"],
    self_confidence=85,
    timestamp="2024-01-01T00:00:00Z"
)

# Confidence score
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

# Evaluate
evaluation = reflection.evaluate_output(output, score)

print(f"Should proceed: {evaluation['should_proceed']}")
print(f"Reasoning: {evaluation['reasoning']}")
```

### Custom Thresholds

```python
# Stricter thresholds
strict_reflection = ReflectionModule(
    high_confidence_threshold=0.90,  # Need 90% to proceed
    low_confidence_threshold=0.70    # Below 70% is error
)

# More lenient thresholds
lenient_reflection = ReflectionModule(
    high_confidence_threshold=0.70,  # 70% to proceed
    low_confidence_threshold=0.50    # Below 50% is error
)
```

### Dual Confidence Assessment

```python
# Self-assessment
self_score = agent.calculate_confidence(output)

# Boss evaluation (using LLM)
boss_score = boss_agent.evaluate_with_llm(
    agent_name=agent.agent_name,
    agent_output=output,
    task_description=task
)

# Use lower score (conservative)
final_score = min(self_score.overall, boss_score)

# Create combined confidence score
combined = ConfidenceScore(
    overall=final_score,
    factors={
        "self_assessment": self_score.overall,
        "boss_assessment": boss_score,
        **self_score.factors
    },
    agent_type=agent.agent_name,
    reasoning=f"Self: {self_score.overall:.2f}, Boss: {boss_score:.2f}"
)

# Evaluate
evaluation = reflection.evaluate_output(output, combined)
```

## Confidence Calculation

Each agent implements its own confidence calculation:

```python
def calculate_confidence(self, output: AgentOutput) -> ConfidenceScore:
    """Calculate confidence based on agent-specific factors"""
    
    # Extract metrics
    source_count = len(output.sources)
    has_results = bool(output.results)
    
    # Calculate factors
    factors = {
        "source_count": min(source_count / 10.0, 1.0),
        "has_results": 1.0 if has_results else 0.0,
        "self_confidence": output.self_confidence / 100.0
    }
    
    # Overall score (weighted average)
    overall = sum(factors.values()) / len(factors)
    
    return ConfidenceScore(
        overall=overall,
        factors=factors,
        agent_type=self.agent_name,
        reasoning=f"Based on {source_count} sources"
    )
```

## Configuration

Set confidence thresholds via environment variables:

```env
CONFIDENCE_THRESHOLD_PROCEED=80
CONFIDENCE_THRESHOLD_CRITICAL=60
MAX_RETRY_ATTEMPTS=2
```

## Best Practices

1. **Be Conservative**: Use lower of self and boss scores
2. **Multiple Factors**: Consider multiple aspects of quality
3. **Clear Reasoning**: Provide explanations for scores
4. **Appropriate Thresholds**: Set based on task criticality
5. **Track History**: Store all confidence scores for analysis
6. **Iterate on Failures**: Use replanning for low confidence

## Testing

```bash
# Run evaluation tests
pytest tests/unit/test_reflection.py -v

# Test with coverage
pytest tests/unit/test_reflection.py --cov=evaluation
```

## Evaluation Metrics

Track these metrics over time:

- **Average Confidence**: Mean confidence across all outputs
- **Proceed Rate**: Percentage of outputs that proceed
- **Replan Rate**: Percentage requiring replanning
- **Error Rate**: Percentage triggering error recovery
- **Confidence Distribution**: Histogram of confidence scores

## Troubleshooting

**Always low confidence:**
- Review agent implementation
- Check data quality
- Verify tool functionality
- Adjust thresholds if too strict

**Always high confidence:**
- Verify scoring logic
- Check for overfitting
- Review evaluation criteria
- Consider stricter thresholds

**Inconsistent scores:**
- Add more evaluation factors
- Improve scoring logic
- Normalize factor weights
- Review edge cases

## Related Documentation

- [Boss Agent](../boss_agent.py) - Uses evaluation for decision-making
- [Agents](../agents/README.md) - Implement confidence calculation
- [Memory System](../memory/README.md) - Stores confidence scores
