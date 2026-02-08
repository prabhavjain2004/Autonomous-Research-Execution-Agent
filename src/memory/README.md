# Memory Module

This module provides persistent storage for agent sessions, decisions, tool executions, and research results using SQLite.

## Overview

The memory system stores all workflow data for audit trails, knowledge reuse, and session management. It provides a complete history of agent decisions, confidence scores, and research outcomes.

## Features

- **Session Management**: Track research sessions with goals and status
- **Decision Storage**: Record all agent decisions and reasoning
- **Tool Execution Logs**: Store tool calls and results
- **Confidence Tracking**: Record self and boss confidence scores
- **Result Persistence**: Save final research outputs
- **Query Interface**: Retrieve historical data

## Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Decisions Table
```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    decision TEXT NOT NULL,
    context TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

### Tool Executions Table
```sql
CREATE TABLE tool_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    inputs TEXT,
    outputs TEXT,
    success BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

### Confidence Scores Table
```sql
CREATE TABLE confidence_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    self_score INTEGER NOT NULL,
    boss_score INTEGER NOT NULL,
    retry_count INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

### Results Table
```sql
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    result_data TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

## Usage

### Initialize Memory System

```python
from memory.memory_system import MemorySystem

# Create memory system (uses DATABASE_PATH from config)
memory = MemorySystem()
```

### Create Session

```python
# Create new research session
session_id = memory.create_session(
    goal="Research AI trends in 2024"
)
print(f"Session ID: {session_id}")
```

### Store Decision

```python
# Record agent decision
memory.store_decision(
    session_id=session_id,
    agent_name="research_agent",
    decision="Searching for AI trends using web search",
    context={"search_query": "AI trends 2024"}
)
```

### Store Tool Execution

```python
# Record tool usage
memory.store_tool_execution(
    session_id=session_id,
    agent_name="research_agent",
    tool_name="web_search",
    inputs={"query": "AI trends 2024"},
    outputs={"results": [...]},
    success=True
)
```

### Store Confidence Scores

```python
# Record confidence evaluation
memory.store_confidence_scores(
    session_id=session_id,
    agent_name="research_agent",
    self_score=85,
    boss_score=88,
    retry_count=0
)
```

### Store Final Result

```python
# Save research result
memory.store_final_result(
    session_id=session_id,
    result=research_result  # ResearchResult object
)
```

### Update Session Status

```python
# Update session status
memory.update_session_status(
    session_id=session_id,
    status="completed"  # or "failed", "in_progress"
)
```

### Query Data

```python
# Get session info
session = memory.get_session(session_id)

# Get all decisions for session
decisions = memory.get_decisions(session_id)

# Get tool executions
tools = memory.get_tool_executions(session_id)

# Get confidence scores
scores = memory.get_confidence_scores(session_id)

# Get final result
result = memory.get_result(session_id)

# List all sessions
all_sessions = memory.list_sessions()
```

## Configuration

Set database path via environment variable:

```env
DATABASE_PATH=./data/agent_memory.db
```

The database file and directory are created automatically if they don't exist.

## Data Retention

By default, all data is retained indefinitely. To implement cleanup:

```python
# Delete old sessions (example)
memory.delete_session(session_id)

# Or implement custom cleanup logic
import sqlite3
conn = sqlite3.connect(memory.db_path)
cursor = conn.cursor()
cursor.execute("""
    DELETE FROM sessions 
    WHERE created_at < datetime('now', '-30 days')
""")
conn.commit()
```

## Best Practices

1. **Always create session first** before storing other data
2. **Use consistent session IDs** across related operations
3. **Store context** with decisions for better debugging
4. **Record all tool executions** for audit trail
5. **Update session status** when workflow completes
6. **Handle database errors** gracefully
7. **Close connections** properly (handled automatically)

## Performance Considerations

- **Indexes**: Key columns are indexed for fast queries
- **Batch Operations**: Use transactions for multiple inserts
- **Connection Pooling**: Single connection per MemorySystem instance
- **Query Optimization**: Use specific queries instead of SELECT *

## Troubleshooting

**Database locked error:**
- Ensure only one process accesses database at a time
- Check file permissions
- Close connections properly

**Slow queries:**
- Check database size
- Verify indexes exist
- Use EXPLAIN QUERY PLAN for optimization

**Disk space issues:**
- Monitor database file size
- Implement data retention policy
- Archive old sessions

## Testing

```bash
# Run memory system tests
pytest tests/unit/test_memory_system.py -v

# Test with coverage
pytest tests/unit/test_memory_system.py --cov=memory
```

## Migration

To migrate to a new schema version:

1. Backup existing database
2. Create migration script
3. Test on copy first
4. Apply to production

Example migration:

```python
import sqlite3

def migrate_v1_to_v2(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add new column
    cursor.execute("""
        ALTER TABLE sessions 
        ADD COLUMN priority INTEGER DEFAULT 0
    """)
    
    conn.commit()
    conn.close()
```

## Related Documentation

- [Boss Agent](../boss_agent.py) - Primary memory system user
- [Agents](../agents/README.md) - Store decisions and tool executions
- [Data Models](../models/README.md) - Data structures stored in memory
