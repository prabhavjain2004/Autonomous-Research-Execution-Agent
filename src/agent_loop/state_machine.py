"""
Agent loop state machine for explicit control flow.

This module provides a state machine that manages agent execution with
well-defined states, transitions, timeout handling, and error recovery.
"""

import time
from enum import Enum
from typing import Callable, Dict, Optional, Any, List
from dataclasses import dataclass

from structured_logging import StructuredLogger


class AgentState(Enum):
    """States in the agent execution loop."""
    IDLE = "idle"
    PLANNING = "planning"
    TOOL_EXECUTION = "tool_execution"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    CONFIDENCE_EVALUATION = "confidence_evaluation"
    REPLANNING = "replanning"
    ERROR_RECOVERY = "error_recovery"
    COMPLETE = "complete"


@dataclass
class StateTransition:
    """
    Defines a state transition with condition and optional action.
    
    Attributes:
        from_state: Source state
        to_state: Target state
        condition: Function that returns True if transition should occur
        action: Optional function to execute during transition
    """
    from_state: AgentState
    to_state: AgentState
    condition: Callable[[], bool]
    action: Optional[Callable] = None


class StateMachine:
    """
    State machine for agent loop control.
    
    Features:
    - Explicit state transitions with validation
    - Timeout handling per state
    - Error recovery mechanisms
    - Transition logging
    - Prevents infinite loops
    """
    
    def __init__(
        self,
        logger: StructuredLogger,
        state_timeouts: Optional[Dict[AgentState, int]] = None,
        max_transitions: int = 50
    ):
        """
        Initialize state machine for agent loop.
        
        Args:
            logger: Structured logger for observability
            state_timeouts: Timeout in seconds for each state
            max_transitions: Maximum state transitions to prevent infinite loops
        """
        self.current_state = AgentState.IDLE
        self.logger = logger
        self.max_transitions = max_transitions
        self.transition_count = 0
        
        # Default timeouts (can be overridden)
        self.state_timeouts = state_timeouts or {
            AgentState.PLANNING: 30,
            AgentState.TOOL_EXECUTION: 120,
            AgentState.OBSERVATION: 20,
            AgentState.REFLECTION: 30,
            AgentState.CONFIDENCE_EVALUATION: 20,
            AgentState.REPLANNING: 30,
            AgentState.ERROR_RECOVERY: 10,
        }
        
        # State execution context
        self.context: Dict[str, Any] = {}
        
        # Transition history
        self.transition_history: List[Dict[str, Any]] = []
        
        # State entry times for timeout tracking
        self.state_entry_time: Optional[float] = None
    
    def transition_to(
        self,
        new_state: AgentState,
        reason: str = "",
        agent: Optional[str] = None
    ):
        """
        Transition to new state with logging.
        
        Args:
            new_state: Target state
            reason: Reason for transition
            agent: Agent name if applicable
        """
        old_state = self.current_state
        
        # Log transition
        self.logger.log_state_transition(
            from_state=old_state.value,
            to_state=new_state.value,
            reason=reason,
            agent=agent
        )
        
        # Record transition
        self.transition_history.append({
            "from": old_state.value,
            "to": new_state.value,
            "reason": reason,
            "timestamp": time.time()
        })
        
        # Update state
        self.current_state = new_state
        self.state_entry_time = time.time()
        self.transition_count += 1
        
        # Check for infinite loop (but don't recurse)
        if self.transition_count >= self.max_transitions and new_state != AgentState.ERROR_RECOVERY:
            self.logger.log_error(
                error_type="InfiniteLoopError",
                error_message=f"Exceeded maximum transitions: {self.max_transitions}",
                stack_trace="",
                context={"transition_count": self.transition_count}
            )
            # Force transition to ERROR_RECOVERY without recursion
            self.current_state = AgentState.ERROR_RECOVERY
            self.logger.log_state_transition(
                from_state=new_state.value,
                to_state=AgentState.ERROR_RECOVERY.value,
                reason="Max transitions exceeded",
                agent=agent
            )
    
    def check_timeout(self) -> bool:
        """
        Check if current state has exceeded its timeout.
        
        Returns:
            True if timeout exceeded, False otherwise
        """
        if self.current_state not in self.state_timeouts:
            return False
        
        if self.state_entry_time is None:
            return False
        
        timeout = self.state_timeouts[self.current_state]
        elapsed = time.time() - self.state_entry_time
        
        if elapsed > timeout:
            self.logger.log_error(
                error_type="TimeoutError",
                error_message=f"State {self.current_state.value} exceeded timeout of {timeout}s",
                stack_trace="",
                context={
                    "state": self.current_state.value,
                    "timeout": timeout,
                    "elapsed": elapsed
                }
            )
            return True
        
        return False
    
    def execute_state(
        self,
        state_handler: Callable[[], Any]
    ) -> Any:
        """
        Execute current state logic with timeout handling.
        
        Args:
            state_handler: Function to execute for current state
            
        Returns:
            State execution result
        """
        try:
            # Check timeout before execution
            if self.check_timeout():
                self.transition_to(
                    AgentState.ERROR_RECOVERY,
                    f"Timeout in {self.current_state.value}"
                )
                return None
            
            # Execute state handler
            result = state_handler()
            
            # Check timeout after execution
            if self.check_timeout():
                self.transition_to(
                    AgentState.ERROR_RECOVERY,
                    f"Timeout in {self.current_state.value}"
                )
                return None
            
            return result
        
        except Exception as e:
            # Any error transitions to ERROR_RECOVERY
            self.logger.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace="",
                context={"state": self.current_state.value}
            )
            self.transition_to(
                AgentState.ERROR_RECOVERY,
                f"Error in {self.current_state.value}: {str(e)}"
            )
            return None
    
    def is_terminal_state(self) -> bool:
        """
        Check if current state is terminal (COMPLETE or ERROR_RECOVERY).
        
        Returns:
            True if in terminal state
        """
        return self.current_state in [AgentState.COMPLETE, AgentState.ERROR_RECOVERY]
    
    def reset(self):
        """Reset state machine to IDLE."""
        self.current_state = AgentState.IDLE
        self.transition_count = 0
        self.context = {}
        self.transition_history = []
        self.state_entry_time = None
        
        self.logger.log_info(
            "State machine reset to IDLE",
            {"transition_count": self.transition_count}
        )
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get value from execution context.
        
        Args:
            key: Context key
            default: Default value if key not found
            
        Returns:
            Context value or default
        """
        return self.context.get(key, default)
    
    def set_context(self, key: str, value: Any):
        """
        Set value in execution context.
        
        Args:
            key: Context key
            value: Value to store
        """
        self.context[key] = value
    
    def get_transition_history(self) -> List[Dict[str, Any]]:
        """
        Get complete transition history.
        
        Returns:
            List of transition records
        """
        return self.transition_history.copy()
    
    def get_state_duration(self) -> float:
        """
        Get duration in current state.
        
        Returns:
            Duration in seconds
        """
        if self.state_entry_time is None:
            return 0.0
        return time.time() - self.state_entry_time
    
    def validate_transition(
        self,
        from_state: AgentState,
        to_state: AgentState
    ) -> bool:
        """
        Validate if a state transition is allowed.
        
        Args:
            from_state: Source state
            to_state: Target state
            
        Returns:
            True if transition is valid
        """
        # Define valid transitions
        valid_transitions = {
            AgentState.IDLE: [AgentState.PLANNING],
            AgentState.PLANNING: [AgentState.TOOL_EXECUTION, AgentState.ERROR_RECOVERY],
            AgentState.TOOL_EXECUTION: [AgentState.OBSERVATION, AgentState.ERROR_RECOVERY],
            AgentState.OBSERVATION: [AgentState.REFLECTION, AgentState.ERROR_RECOVERY],
            AgentState.REFLECTION: [AgentState.CONFIDENCE_EVALUATION, AgentState.ERROR_RECOVERY],
            AgentState.CONFIDENCE_EVALUATION: [
                AgentState.COMPLETE,
                AgentState.REPLANNING,
                AgentState.ERROR_RECOVERY
            ],
            AgentState.REPLANNING: [AgentState.TOOL_EXECUTION, AgentState.ERROR_RECOVERY],
            AgentState.ERROR_RECOVERY: [AgentState.COMPLETE, AgentState.IDLE],
            AgentState.COMPLETE: [AgentState.IDLE],
        }
        
        allowed_states = valid_transitions.get(from_state, [])
        return to_state in allowed_states
    
    def get_valid_next_states(self) -> List[AgentState]:
        """
        Get list of valid next states from current state.
        
        Returns:
            List of valid next states
        """
        valid_transitions = {
            AgentState.IDLE: [AgentState.PLANNING],
            AgentState.PLANNING: [AgentState.TOOL_EXECUTION, AgentState.ERROR_RECOVERY],
            AgentState.TOOL_EXECUTION: [AgentState.OBSERVATION, AgentState.ERROR_RECOVERY],
            AgentState.OBSERVATION: [AgentState.REFLECTION, AgentState.ERROR_RECOVERY],
            AgentState.REFLECTION: [AgentState.CONFIDENCE_EVALUATION, AgentState.ERROR_RECOVERY],
            AgentState.CONFIDENCE_EVALUATION: [
                AgentState.COMPLETE,
                AgentState.REPLANNING,
                AgentState.ERROR_RECOVERY
            ],
            AgentState.REPLANNING: [AgentState.TOOL_EXECUTION, AgentState.ERROR_RECOVERY],
            AgentState.ERROR_RECOVERY: [AgentState.COMPLETE, AgentState.IDLE],
            AgentState.COMPLETE: [AgentState.IDLE],
        }
        
        return valid_transitions.get(self.current_state, [])
