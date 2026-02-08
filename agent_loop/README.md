# Agent Loop Module

This module implements the state machine that controls agent execution flow, manages state transitions, and handles timeouts.

## Overview

The agent loop provides explicit state management for the research workflow, ensuring predictable execution with proper error handling and timeout protection.

## State Machine

### States

```
IDLE                    → Initial state, waiting for work
PLANNING                → Agent planning next action
TOOL_EXECUTION          → Executing tools (search, scrape, etc.)
OBSERVATION             → Processing tool results
REFLECTION              → Analyzing execution quality
CONFIDENCE_EVALUATION   → Evaluating output confidence
REPLANNING              → Low confidence, creating new plan
ERROR_RECOVERY          → Handling errors
COMPLETE                → Workflow finished
```

### State Transitions

```
IDLE → PLANNING
    ↓
TOOL_EXECUTION
    ↓
OBSERVATION
    ↓
REFLECTION
    ↓
CONFIDENCE_EVALUATION
    ↓
    ├─→ COMPLETE (high confidence)
    ├─→ REPLANNING (low confidence)
    └─→ ERROR_RECOVERY (errors)
```

## Usage

```python
from agent_loop.state_machine import StateMachine, AgentState

# Create state machine
state_machine = StateMachine(
    initial_state=AgentState.IDLE,
    timeouts={
        "PLANNING": 30,
        "TOOL_EXECUTION": 120,
        "OBSERVATION": 20,
        "REFLECTION": 30,
        "CONFIDENCE_EVALUATION": 20,
        "REPLANNING": 30,
        "ERROR_RECOVERY": 10
    }
)

# Transition states
state_machine.transition_to(AgentState.PLANNING)
state_machine.transition_to(AgentState.TOOL_EXECUTION)

# Check current state
if state_machine.current_state == AgentState.COMPLETE:
    print("Workflow complete!")

# Check for timeout
if state_machine.is_timeout():
    print("State timeout exceeded!")
```

## State Descriptions

### IDLE
- **Purpose**: Waiting for work
- **Timeout**: None
- **Next States**: PLANNING

### PLANNING
- **Purpose**: Agent decides what to do next
- **Timeout**: 30 seconds
- **Next States**: TOOL_EXECUTION, COMPLETE
- **Activities**: Task analysis, tool selection, strategy formation

### TOOL_EXECUTION
- **Purpose**: Execute selected tools
- **Timeout**: 120 seconds
- **Next States**: OBSERVATION, ERROR_RECOVERY
- **Activities**: Web search, scraping, code execution, file operations

### OBSERVATION
- **Purpose**: Process and parse tool results
- **Timeout**: 20 seconds
- **Next States**: REFLECTION
- **Activities**: Data extraction, result validation, error detection

### REFLECTION
- **Purpose**: Analyze execution quality
- **Timeout**: 30 seconds
- **Next States**: CONFIDENCE_EVALUATION
- **Activities**: Quality assessment, completeness check, reasoning

### CONFIDENCE_EVALUATION
- **Purpose**: Calculate confidence scores
- **Timeout**: 20 seconds
- **Next States**: COMPLETE, REPLANNING, ERROR_RECOVERY
- **Activities**: Self-assessment, boss evaluation, decision making

### REPLANNING
- **Purpose**: Create improved plan after low confidence
- **Timeout**: 30 seconds
- **Next States**: TOOL_EXECUTION
- **Activities**: Strategy adjustment, alternative approaches, retry logic

### ERROR_RECOVERY
- **Purpose**: Handle and recover from errors
- **Timeout**: 10 seconds
- **Next States**: REPLANNING, COMPLETE
- **Activities**: Error analysis, recovery strategy, fallback options

### COMPLETE
- **Purpose**: Workflow finished
- **Timeout**: None
- **Next States**: None (terminal state)

## Timeout Management

Each state has a timeout to prevent hanging:

```python
# Configure timeouts
timeouts = {
    "PLANNING": 30,              # 30 seconds
    "TOOL_EXECUTION": 120,       # 2 minutes
    "OBSERVATION": 20,           # 20 seconds
    "REFLECTION": 30,            # 30 seconds
    "CONFIDENCE_EVALUATION": 20, # 20 seconds
    "REPLANNING": 30,            # 30 seconds
    "ERROR_RECOVERY": 10         # 10 seconds
}

# Check for timeout
if state_machine.is_timeout():
    # Handle timeout
    state_machine.transition_to(AgentState.ERROR_RECOVERY)
```

## Configuration

Set timeouts via environment variables:

```env
TIMEOUT_PLANNING=30
TIMEOUT_TOOL_EXECUTION=120
TIMEOUT_OBSERVATION=20
TIMEOUT_REFLECTION=30
TIMEOUT_CONFIDENCE_EVALUATION=20
TIMEOUT_REPLANNING=30
TIMEOUT_ERROR_RECOVERY=10
```

## Best Practices

1. **Always check timeouts** before long operations
2. **Log all state transitions** for debugging
3. **Handle invalid transitions** gracefully
4. **Use appropriate timeouts** for each state
5. **Implement proper error recovery** logic

## Testing

```bash
# Run state machine tests
pytest tests/unit/test_state_machine.py -v

# Test with coverage
pytest tests/unit/test_state_machine.py --cov=agent_loop
```

## Related Documentation

- [Boss Agent](../boss_agent.py) - Uses state machine for orchestration
- [Agents](../agents/README.md) - Execute within state machine
- [Error Handling](../error_handling.py) - Error recovery strategies
