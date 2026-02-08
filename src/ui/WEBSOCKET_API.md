# WebSocket API Documentation

## Overview

The WebSocket server provides real-time communication between the Autonomous Research Agent backend and web clients. It broadcasts agent state updates, logs, confidence scores, and results to all connected clients.

## Connection

**Endpoint:** `ws://localhost:8000/ws`

**Protocol:** WebSocket

## Message Format

All messages are JSON objects with the following structure:

```json
{
  "type": "message_type",
  "timestamp": "ISO 8601 timestamp",
  "data": { /* message-specific data */ }
}
```

## Client → Server Messages

### Start Research

Start a new research task.

```json
{
  "type": "start_research",
  "goal": "Research AI trends in 2024"
}
```

**Response:**
```json
{
  "type": "research_started",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "session_id": "uuid-here",
    "goal": "Research AI trends in 2024"
  }
}
```

### Get Sessions

Retrieve list of past research sessions.

```json
{
  "type": "get_sessions",
  "limit": 50
}
```

**Response:**
```json
{
  "type": "sessions",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "sessions": [
      {
        "session_id": "uuid-1",
        "goal": "Research AI trends",
        "status": "completed",
        "created_at": "2024-01-01T10:00:00Z"
      }
    ]
  }
}
```

### Get Session History

Retrieve detailed history for a specific session.

```json
{
  "type": "get_session_history",
  "session_id": "uuid-here"
}
```

**Response:**
```json
{
  "type": "session_history",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "session_id": "uuid-here",
    "decisions": [...],
    "tool_outputs": [...],
    "confidence_scores": [...],
    "final_result": {...}
  }
}
```

### Ping

Health check message.

```json
{
  "type": "ping"
}
```

**Response:**
```json
{
  "type": "pong",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Server → Client Messages

### Connection Confirmation

Sent immediately after connection is established.

```json
{
  "type": "connected",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "message": "Connected to research agent server"
  }
}
```

### State Update

Broadcast when agent state changes.

```json
{
  "type": "state_update",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "state": "PLANNING",
    "agent": "Research Agent",
    "action": "Searching for sources"
  }
}
```

**States:**
- `IDLE` - No active research
- `PLANNING` - Planning research approach
- `TOOL_EXECUTION` - Executing tools
- `OBSERVATION` - Processing tool outputs
- `REFLECTION` - Evaluating results
- `CONFIDENCE_EVALUATION` - Calculating confidence
- `REPLANNING` - Adjusting approach
- `ERROR_RECOVERY` - Handling errors
- `COMPLETE` - Research finished

### Log Entry

Broadcast for each log entry.

```json
{
  "type": "log",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "level": "INFO",
    "event_type": "state_transition",
    "message": "Transitioned to PLANNING",
    "context": {...}
  }
}
```

**Log Levels:**
- `DEBUG` - Detailed debugging information
- `INFO` - General information
- `WARNING` - Warning messages
- `ERROR` - Error messages

### Confidence Score

Broadcast when confidence scores are calculated.

```json
{
  "type": "confidence",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "agent": "Research Agent",
    "score": 0.85,
    "factors": {
      "source_count": 0.8,
      "reliability": 0.9,
      "completeness": 0.85,
      "relevance": 0.85
    }
  }
}
```

### Research Result

Broadcast when research completes.

```json
{
  "type": "result",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "session_id": "uuid-here",
    "goal": "Research AI trends in 2024",
    "agents_involved": ["Research Agent", "Analyst Agent", "Strategy Agent"],
    "insights": ["Insight 1", "Insight 2"],
    "recommendations": ["Recommendation 1"],
    "sources": [
      {
        "url": "https://example.com",
        "title": "AI Trends",
        "reliability": 0.9
      }
    ],
    "confidence_scores": {
      "research": {"self": 0.85, "boss": 0.8},
      "analyst": {"self": 0.9, "boss": 0.85},
      "strategy": {"self": 0.88, "boss": 0.82}
    },
    "overall_confidence": 0.84,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Error

Broadcast when errors occur.

```json
{
  "type": "error",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "error": "Tool execution failed",
    "context": {
      "tool": "WebSearchTool",
      "phase": "research"
    }
  }
}
```

### Execution State

Sent to new connections to show current execution status.

```json
{
  "type": "execution_state",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "session_id": "uuid-here",
    "goal": "Research AI trends",
    "status": "running",
    "start_time": "2024-01-01T11:00:00Z"
  }
}
```

## HTTP Endpoints

### Health Check

**GET** `/health`

Returns server health status.

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "active_connections": 3,
  "current_execution": {
    "session_id": "uuid-here",
    "status": "running"
  }
}
```

### Index Page

**GET** `/`

Returns the main HTML page for the web UI.

## Running the Server

### Development Mode

```bash
python ui/websocket_server.py
```

Server will start on `http://localhost:8000` with auto-reload enabled.

### Production Mode

```bash
python -c "from ui.websocket_server import start_server; start_server(host='0.0.0.0', port=8000, reload=False)"
```

### Using uvicorn directly

```bash
uvicorn ui.websocket_server:app --host 0.0.0.0 --port 8000
```

## Example Client (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to server');
  
  // Start research
  ws.send(JSON.stringify({
    type: 'start_research',
    goal: 'Research AI trends in 2024'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type, message.data);
  
  switch (message.type) {
    case 'state_update':
      console.log('State:', message.data.state);
      break;
    case 'confidence':
      console.log('Confidence:', message.data.score);
      break;
    case 'result':
      console.log('Result:', message.data);
      break;
    case 'error':
      console.error('Error:', message.data.error);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from server');
};
```

## Requirements Satisfied

This WebSocket server implementation satisfies the following requirements:

- **10.1**: Input field for research goals (via WebSocket message)
- **10.2**: Real-time agent state display
- **10.3**: Active agent display
- **10.4**: Current action display
- **10.5**: Live log viewer (log messages broadcast)
- **10.6**: Confidence score visualization (confidence messages)
- **10.7**: Decision history (via session history)
- **10.8**: Results display (result messages)
- **10.9**: Session history browser (get_sessions, get_session_history)
- **10.11**: Real-time updates without page refresh
- **10.12**: Lightweight implementation (no heavy frameworks)
