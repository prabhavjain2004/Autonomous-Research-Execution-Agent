"""
Unit tests for agent loop state machine.

Tests state transitions, timeout enforcement, error recovery,
and termination conditions.
"""

import pytest
import time
import tempfile
import shutil
from uuid import uuid4

from agent_loop import StateMachine, AgentState, StateTransition
from structured_logging import StructuredLogger


class TestStateMachine:
    """Tests for StateMachine."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def logger(self, temp_log_dir):
        """Create logger instance."""
        session_id = str(uuid4())
        logger = StructuredLogger(
            session_id=session_id,
            log_dir=temp_log_dir,
            console_output=False
        )
        yield logger
        logger.close()
    
    @pytest.fixture
    def state_machine(self, logger):
        """Create state machine instance."""
        return StateMachine(logger=logger)
    
    def test_initialization(self, logger):
        """Test state machine initialization."""
        sm = StateMachine(logger=logger)
        
        assert sm.current_state == AgentState.IDLE
        assert sm.transition_count == 0
        assert len(sm.context) == 0
        assert len(sm.transition_history) == 0
    
    def test_transition_to(self, state_machine):
        """Test state transition."""
        state_machine.transition_to(
            AgentState.PLANNING,
            reason="Starting new task"
        )
        
        assert state_machine.current_state == AgentState.PLANNING
        assert state_machine.transition_count == 1
        assert len(state_machine.transition_history) == 1
    
    def test_transition_history_tracking(self, state_machine):
        """Test that transition history is tracked."""
        state_machine.transition_to(AgentState.PLANNING, "Start")
        state_machine.transition_to(AgentState.TOOL_EXECUTION, "Execute")
        
        history = state_machine.get_transition_history()
        
        assert len(history) == 2
        assert history[0]["from"] == "idle"
        assert history[0]["to"] == "planning"
        assert history[1]["from"] == "planning"
        assert history[1]["to"] == "tool_execution"
    
    def test_state_entry_time_tracking(self, state_machine):
        """Test that state entry time is tracked."""
        state_machine.transition_to(AgentState.PLANNING, "Start")
        
        assert state_machine.state_entry_time is not None
        assert state_machine.state_entry_time > 0
    
    def test_timeout_detection(self, logger):
        """Test timeout detection."""
        # Create state machine with very short timeout
        sm = StateMachine(
            logger=logger,
            state_timeouts={AgentState.PLANNING: 0.1}
        )
        
        sm.transition_to(AgentState.PLANNING, "Start")
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Check timeout
        assert sm.check_timeout() is True
    
    def test_no_timeout_within_limit(self, state_machine):
        """Test no timeout when within limit."""
        state_machine.transition_to(AgentState.PLANNING, "Start")
        
        # Check immediately (should not timeout)
        assert state_machine.check_timeout() is False
    
    def test_execute_state_success(self, state_machine):
        """Test successful state execution."""
        def handler():
            return "success"
        
        state_machine.transition_to(AgentState.PLANNING, "Start")
        result = state_machine.execute_state(handler)
        
        assert result == "success"
    
    def test_execute_state_with_error(self, state_machine):
        """Test state execution with error transitions to ERROR_RECOVERY."""
        def handler():
            raise ValueError("Test error")
        
        state_machine.transition_to(AgentState.PLANNING, "Start")
        result = state_machine.execute_state(handler)
        
        assert result is None
        assert state_machine.current_state == AgentState.ERROR_RECOVERY
    
    def test_execute_state_with_timeout(self, logger):
        """Test state execution with timeout."""
        sm = StateMachine(
            logger=logger,
            state_timeouts={AgentState.PLANNING: 0.1}
        )
        
        def slow_handler():
            time.sleep(0.2)
            return "done"
        
        sm.transition_to(AgentState.PLANNING, "Start")
        result = sm.execute_state(slow_handler)
        
        # Should timeout and transition to ERROR_RECOVERY
        assert sm.current_state == AgentState.ERROR_RECOVERY
    
    def test_is_terminal_state(self, state_machine):
        """Test terminal state detection."""
        assert state_machine.is_terminal_state() is False
        
        state_machine.transition_to(AgentState.COMPLETE, "Done")
        assert state_machine.is_terminal_state() is True
        
        state_machine.transition_to(AgentState.ERROR_RECOVERY, "Error")
        assert state_machine.is_terminal_state() is True
    
    def test_reset(self, state_machine):
        """Test state machine reset."""
        # Make some transitions
        state_machine.transition_to(AgentState.PLANNING, "Start")
        state_machine.set_context("key", "value")
        
        # Reset
        state_machine.reset()
        
        assert state_machine.current_state == AgentState.IDLE
        assert state_machine.transition_count == 0
        assert len(state_machine.context) == 0
        assert len(state_machine.transition_history) == 0
    
    def test_context_management(self, state_machine):
        """Test context get/set operations."""
        state_machine.set_context("key1", "value1")
        state_machine.set_context("key2", 42)
        
        assert state_machine.get_context("key1") == "value1"
        assert state_machine.get_context("key2") == 42
        assert state_machine.get_context("nonexistent", "default") == "default"
    
    def test_get_state_duration(self, state_machine):
        """Test getting state duration."""
        state_machine.transition_to(AgentState.PLANNING, "Start")
        
        time.sleep(0.1)
        
        duration = state_machine.get_state_duration()
        assert duration >= 0.1
    
    def test_validate_transition_valid(self, state_machine):
        """Test validation of valid transitions."""
        assert state_machine.validate_transition(
            AgentState.IDLE,
            AgentState.PLANNING
        ) is True
        
        assert state_machine.validate_transition(
            AgentState.PLANNING,
            AgentState.TOOL_EXECUTION
        ) is True
    
    def test_validate_transition_invalid(self, state_machine):
        """Test validation of invalid transitions."""
        assert state_machine.validate_transition(
            AgentState.IDLE,
            AgentState.COMPLETE
        ) is False
        
        assert state_machine.validate_transition(
            AgentState.PLANNING,
            AgentState.OBSERVATION
        ) is False
    
    def test_get_valid_next_states(self, state_machine):
        """Test getting valid next states."""
        # From IDLE
        valid_states = state_machine.get_valid_next_states()
        assert AgentState.PLANNING in valid_states
        
        # From PLANNING
        state_machine.transition_to(AgentState.PLANNING, "Start")
        valid_states = state_machine.get_valid_next_states()
        assert AgentState.TOOL_EXECUTION in valid_states
        assert AgentState.ERROR_RECOVERY in valid_states
    
    def test_max_transitions_limit(self, logger):
        """Test that max transitions limit prevents infinite loops."""
        sm = StateMachine(logger=logger, max_transitions=5)
        
        # Make many transitions
        for i in range(10):
            if sm.current_state == AgentState.ERROR_RECOVERY:
                break
            sm.transition_to(AgentState.PLANNING, f"Transition {i}")
            sm.transition_to(AgentState.TOOL_EXECUTION, f"Transition {i}")
        
        # Should have transitioned to ERROR_RECOVERY
        assert sm.current_state == AgentState.ERROR_RECOVERY
    
    def test_state_transition_correctness(self, state_machine):
        """Test correct state transition sequence."""
        # Valid sequence: IDLE -> PLANNING -> TOOL_EXECUTION -> OBSERVATION
        state_machine.transition_to(AgentState.PLANNING, "Start")
        assert state_machine.current_state == AgentState.PLANNING
        
        state_machine.transition_to(AgentState.TOOL_EXECUTION, "Execute")
        assert state_machine.current_state == AgentState.TOOL_EXECUTION
        
        state_machine.transition_to(AgentState.OBSERVATION, "Observe")
        assert state_machine.current_state == AgentState.OBSERVATION
        
        state_machine.transition_to(AgentState.REFLECTION, "Reflect")
        assert state_machine.current_state == AgentState.REFLECTION
    
    def test_error_recovery_transition(self, state_machine):
        """Test transition to ERROR_RECOVERY from any state."""
        state_machine.transition_to(AgentState.PLANNING, "Start")
        state_machine.transition_to(AgentState.ERROR_RECOVERY, "Error occurred")
        
        assert state_machine.current_state == AgentState.ERROR_RECOVERY
    
    def test_complete_to_idle_transition(self, state_machine):
        """Test transition from COMPLETE to IDLE."""
        # Simulate completion
        state_machine.transition_to(AgentState.PLANNING, "Start")
        state_machine.transition_to(AgentState.TOOL_EXECUTION, "Execute")
        state_machine.transition_to(AgentState.OBSERVATION, "Observe")
        state_machine.transition_to(AgentState.REFLECTION, "Reflect")
        state_machine.transition_to(AgentState.CONFIDENCE_EVALUATION, "Evaluate")
        state_machine.transition_to(AgentState.COMPLETE, "Done")
        
        assert state_machine.current_state == AgentState.COMPLETE
        
        # Transition back to IDLE
        state_machine.transition_to(AgentState.IDLE, "Ready for next task")
        assert state_machine.current_state == AgentState.IDLE
    
    def test_replanning_transition(self, state_machine):
        """Test transition to REPLANNING when confidence is low."""
        state_machine.transition_to(AgentState.PLANNING, "Start")
        state_machine.transition_to(AgentState.TOOL_EXECUTION, "Execute")
        state_machine.transition_to(AgentState.OBSERVATION, "Observe")
        state_machine.transition_to(AgentState.REFLECTION, "Reflect")
        state_machine.transition_to(AgentState.CONFIDENCE_EVALUATION, "Evaluate")
        state_machine.transition_to(AgentState.REPLANNING, "Low confidence")
        
        assert state_machine.current_state == AgentState.REPLANNING
        
        # Can transition back to TOOL_EXECUTION
        state_machine.transition_to(AgentState.TOOL_EXECUTION, "Retry")
        assert state_machine.current_state == AgentState.TOOL_EXECUTION
    
    def test_state_enum_values(self):
        """Test AgentState enum has expected values."""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.PLANNING.value == "planning"
        assert AgentState.TOOL_EXECUTION.value == "tool_execution"
        assert AgentState.OBSERVATION.value == "observation"
        assert AgentState.REFLECTION.value == "reflection"
        assert AgentState.CONFIDENCE_EVALUATION.value == "confidence_evaluation"
        assert AgentState.REPLANNING.value == "replanning"
        assert AgentState.ERROR_RECOVERY.value == "error_recovery"
        assert AgentState.COMPLETE.value == "complete"
    
    def test_state_transition_logging(self, state_machine, temp_log_dir):
        """Test that state transitions are logged."""
        state_machine.transition_to(AgentState.PLANNING, "Start")
        
        # Check logs
        logs = StructuredLogger.get_session_logs(
            temp_log_dir,
            state_machine.logger.session_id
        )
        
        # Should have state transition log
        transition_logs = [
            log for log in logs
            if log.get("event_type") == "state_transition"
        ]
        
        assert len(transition_logs) > 0
    
    def test_custom_timeouts(self, logger):
        """Test custom timeout configuration."""
        custom_timeouts = {
            AgentState.PLANNING: 60,
            AgentState.TOOL_EXECUTION: 180,
        }
        
        sm = StateMachine(logger=logger, state_timeouts=custom_timeouts)
        
        assert sm.state_timeouts[AgentState.PLANNING] == 60
        assert sm.state_timeouts[AgentState.TOOL_EXECUTION] == 180
