"""
Memory system with SQLite for session persistence and knowledge management.

This module provides persistent storage of agent decisions, tool outputs,
confidence scores, and research results organized by session.
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

from models.data_models import ToolResult, ResearchResult
from structured_logging import StructuredLogger


class SessionSummary:
    """Summary of a research session."""
    
    def __init__(
        self,
        session_id: str,
        goal: str,
        created_at: str,
        completed_at: Optional[str],
        status: str,
        overall_confidence: Optional[int]
    ):
        self.session_id = session_id
        self.goal = goal
        self.created_at = created_at
        self.completed_at = completed_at
        self.status = status
        self.overall_confidence = overall_confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "overall_confidence": self.overall_confidence
        }


class SessionHistory:
    """Complete history of a research session."""
    
    def __init__(
        self,
        session_id: str,
        goal: str,
        created_at: str,
        completed_at: Optional[str],
        status: str,
        decisions: List[Dict[str, Any]],
        tool_executions: List[Dict[str, Any]],
        confidence_scores: List[Dict[str, Any]],
        final_result: Optional[Dict[str, Any]]
    ):
        self.session_id = session_id
        self.goal = goal
        self.created_at = created_at
        self.completed_at = completed_at
        self.status = status
        self.decisions = decisions
        self.tool_executions = tool_executions
        self.confidence_scores = confidence_scores
        self.final_result = final_result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "decisions": self.decisions,
            "tool_executions": self.tool_executions,
            "confidence_scores": self.confidence_scores,
            "final_result": self.final_result
        }


class MemorySystem:
    """
    SQLite-based memory system for persistent storage.
    
    Features:
    - Session-based organization
    - Stores agent decisions, tool outputs, confidence scores
    - Summarizes verbose data to prevent unbounded growth
    - Connection pooling and proper resource cleanup
    - Schema designed for future PostgreSQL migration
    """
    
    def __init__(
        self,
        db_path: str = "./data/agent_memory.db",
        logger: Optional[StructuredLogger] = None
    ):
        """
        Initialize memory system.
        
        Args:
            db_path: Path to SQLite database file
            logger: Optional structured logger
        """
        self.db_path = Path(db_path)
        self.logger = logger
        
        # Create database directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._initialize_schema()
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        Ensures proper connection cleanup and error handling.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            if self.logger:
                self.logger.log_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    stack_trace="",
                    context={"operation": "database"}
                )
            raise
        finally:
            conn.close()
    
    def _initialize_schema(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    status TEXT,
                    overall_confidence INTEGER
                )
            """)
            
            # Agent decisions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    context TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Tool executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    output TEXT,
                    execution_time REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Confidence scores table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS confidence_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    self_score INTEGER NOT NULL,
                    boss_score INTEGER NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Research results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_results (
                    session_id TEXT PRIMARY KEY,
                    result TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_created_at 
                ON sessions(created_at DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_decisions_session 
                ON agent_decisions(session_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_executions_session 
                ON tool_executions(session_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_confidence_scores_session 
                ON confidence_scores(session_id)
            """)
    
    def create_session(self, goal: str) -> UUID:
        """
        Create new research session.
        
        Args:
            goal: Research goal
            
        Returns:
            Session UUID
        """
        session_id = uuid4()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (session_id, goal, status)
                VALUES (?, ?, ?)
                """,
                (str(session_id), goal, "in_progress")
            )
        
        if self.logger:
            self.logger.log_info(
                f"Created new session: {session_id}",
                {"session_id": str(session_id), "goal": goal}
            )
        
        return session_id
    
    def store_decision(
        self,
        session_id: UUID,
        agent_name: str,
        decision: str,
        context: Dict[str, Any]
    ):
        """
        Store agent decision with context.
        
        Args:
            session_id: Session UUID
            agent_name: Name of the agent
            decision: Decision made
            context: Additional context
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_decisions (session_id, agent_name, decision, context)
                VALUES (?, ?, ?, ?)
                """,
                (str(session_id), agent_name, decision, json.dumps(context))
            )
        
        if self.logger:
            self.logger.log_decision(agent_name, decision, "Stored to memory", context)
    
    def store_tool_output(
        self,
        session_id: UUID,
        tool_name: str,
        output: ToolResult,
        execution_time: float
    ):
        """
        Store tool execution output (summarized).
        
        Args:
            session_id: Session UUID
            tool_name: Name of the tool
            output: Tool result
            execution_time: Execution time in seconds
        """
        # Summarize output to prevent unbounded growth
        output_summary = {
            "success": output.success,
            "has_data": output.data is not None,
            "error": output.error,
            "metadata": output.metadata
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tool_executions 
                (session_id, tool_name, success, output, execution_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(session_id),
                    tool_name,
                    output.success,
                    json.dumps(output_summary),
                    execution_time
                )
            )
    
    def store_confidence_scores(
        self,
        session_id: UUID,
        agent_name: str,
        self_score: int,
        boss_score: int,
        retry_count: int = 0
    ):
        """
        Store confidence scores for agent output.
        
        Args:
            session_id: Session UUID
            agent_name: Name of the agent
            self_score: Agent's self-confidence score
            boss_score: Boss Agent's evaluation score
            retry_count: Current retry count
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO confidence_scores 
                (session_id, agent_name, self_score, boss_score, retry_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(session_id), agent_name, self_score, boss_score, retry_count)
            )
        
        if self.logger:
            self.logger.log_confidence_scores(
                agent_name, self_score, boss_score, "stored"
            )
    
    def store_final_result(
        self,
        session_id: UUID,
        result: ResearchResult
    ):
        """
        Store final research result.
        
        Args:
            session_id: Session UUID
            result: Research result
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Store result
            cursor.execute(
                """
                INSERT INTO research_results (session_id, result)
                VALUES (?, ?)
                """,
                (str(session_id), result.to_json())
            )
            
            # Update session status
            cursor.execute(
                """
                UPDATE sessions
                SET completed_at = CURRENT_TIMESTAMP,
                    status = ?,
                    overall_confidence = ?
                WHERE session_id = ?
                """,
                ("completed", result.overall_confidence, str(session_id))
            )
        
        if self.logger:
            self.logger.log_info(
                f"Stored final result for session {session_id}",
                {"overall_confidence": result.overall_confidence}
            )
    
    def get_session_history(self, session_id: UUID) -> Optional[SessionHistory]:
        """
        Retrieve complete session history.
        
        Args:
            session_id: Session UUID
            
        Returns:
            SessionHistory object or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (str(session_id),)
            )
            session_row = cursor.fetchone()
            
            if not session_row:
                return None
            
            # Get decisions
            cursor.execute(
                """
                SELECT agent_name, decision, context, timestamp
                FROM agent_decisions
                WHERE session_id = ?
                ORDER BY timestamp
                """,
                (str(session_id),)
            )
            decisions = [
                {
                    "agent_name": row["agent_name"],
                    "decision": row["decision"],
                    "context": json.loads(row["context"]) if row["context"] else {},
                    "timestamp": row["timestamp"]
                }
                for row in cursor.fetchall()
            ]
            
            # Get tool executions
            cursor.execute(
                """
                SELECT tool_name, success, output, execution_time, timestamp
                FROM tool_executions
                WHERE session_id = ?
                ORDER BY timestamp
                """,
                (str(session_id),)
            )
            tool_executions = [
                {
                    "tool_name": row["tool_name"],
                    "success": bool(row["success"]),
                    "output": json.loads(row["output"]) if row["output"] else {},
                    "execution_time": row["execution_time"],
                    "timestamp": row["timestamp"]
                }
                for row in cursor.fetchall()
            ]
            
            # Get confidence scores
            cursor.execute(
                """
                SELECT agent_name, self_score, boss_score, retry_count, timestamp
                FROM confidence_scores
                WHERE session_id = ?
                ORDER BY timestamp
                """,
                (str(session_id),)
            )
            confidence_scores = [
                {
                    "agent_name": row["agent_name"],
                    "self_score": row["self_score"],
                    "boss_score": row["boss_score"],
                    "retry_count": row["retry_count"],
                    "timestamp": row["timestamp"]
                }
                for row in cursor.fetchall()
            ]
            
            # Get final result
            cursor.execute(
                "SELECT result FROM research_results WHERE session_id = ?",
                (str(session_id),)
            )
            result_row = cursor.fetchone()
            final_result = json.loads(result_row["result"]) if result_row else None
            
            return SessionHistory(
                session_id=session_row["session_id"],
                goal=session_row["goal"],
                created_at=session_row["created_at"],
                completed_at=session_row["completed_at"],
                status=session_row["status"],
                decisions=decisions,
                tool_executions=tool_executions,
                confidence_scores=confidence_scores,
                final_result=final_result
            )
    
    def list_sessions(self, limit: int = 50) -> List[SessionSummary]:
        """
        List recent sessions with summaries.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of SessionSummary objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT session_id, goal, created_at, completed_at, status, overall_confidence
                FROM sessions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            
            return [
                SessionSummary(
                    session_id=row["session_id"],
                    goal=row["goal"],
                    created_at=row["created_at"],
                    completed_at=row["completed_at"],
                    status=row["status"],
                    overall_confidence=row["overall_confidence"]
                )
                for row in cursor.fetchall()
            ]
    
    def update_session_status(self, session_id: UUID, status: str):
        """
        Update session status.
        
        Args:
            session_id: Session UUID
            status: New status
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET status = ? WHERE session_id = ?",
                (status, str(session_id))
            )
    
    def get_session_info(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get basic session information.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Dictionary with session info or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (str(session_id),)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return dict(row)
    
    def close(self):
        """Close memory system and cleanup resources."""
        # SQLite connections are closed in context manager
        # This method is here for API consistency
        pass
