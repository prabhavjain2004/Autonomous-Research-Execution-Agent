"""
WebSocket Server for Real-Time Research Agent UI

This module implements a FastAPI-based WebSocket server that provides real-time
communication between the Boss Agent and the web UI. It broadcasts agent state
updates, log entries, confidence scores, and results to connected clients.

Requirements: 10.1-10.12
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Set, Optional, Any
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from boss_agent import BossAgent
from structured_logging.structured_logger import StructuredLogger
from memory.memory_system import MemorySystem
from config import Config


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts messages to all connected clients.
    
    Attributes:
        active_connections: Set of active WebSocket connections
    """
    
    def __init__(self):
        """Initialize the connection manager with an empty set of connections."""
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection and add it to active connections.
        
        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from active connections.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        self.active_connections.discard(websocket)
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """
        Send a message to a specific WebSocket connection.
        
        Args:
            message: The message to send as a dictionary
            websocket: The target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all active WebSocket connections.
        
        Args:
            message: The message to broadcast as a dictionary
        """
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


# Initialize FastAPI app and connection manager
app = FastAPI(title="Autonomous Research Agent", version="1.0.0")
manager = ConnectionManager()

# Get the directory containing this file
UI_DIR = Path(__file__).parent

# Global state for tracking current execution
current_execution: Optional[Dict[str, Any]] = None


def create_state_update_message(state: str, agent: Optional[str] = None, 
                                action: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a state update message for broadcasting.
    
    Args:
        state: The current state of the agent loop
        agent: The currently active agent (optional)
        action: The current action being performed (optional)
    
    Returns:
        Dictionary containing the state update message
    """
    return {
        "type": "state_update",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "state": state,
            "agent": agent,
            "action": action
        }
    }


def create_log_message(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a log message for broadcasting.
    
    Args:
        log_entry: The log entry to broadcast
    
    Returns:
        Dictionary containing the log message
    """
    return {
        "type": "log",
        "timestamp": datetime.utcnow().isoformat(),
        "data": log_entry
    }


def create_confidence_message(agent_name: str, confidence_score: float, 
                              factors: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Create a confidence score message for broadcasting.
    
    Args:
        agent_name: Name of the agent
        confidence_score: The confidence score (0.0-1.0)
        factors: Optional dictionary of confidence factors
    
    Returns:
        Dictionary containing the confidence message
    """
    return {
        "type": "confidence",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "agent": agent_name,
            "score": confidence_score,
            "factors": factors or {}
        }
    }


def create_result_message(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a result message for broadcasting.
    
    Args:
        result: The research result to broadcast
    
    Returns:
        Dictionary containing the result message
    """
    return {
        "type": "result",
        "timestamp": datetime.utcnow().isoformat(),
        "data": result
    }


def create_error_message(error: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create an error message for broadcasting.
    
    Args:
        error: The error message
        context: Optional error context
    
    Returns:
        Dictionary containing the error message
    """
    return {
        "type": "error",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "error": error,
            "context": context or {}
        }
    }


async def execute_research(goal: str, session_id: str) -> Dict[str, Any]:
    """
    Execute a research task and broadcast updates in real-time.
    
    This function creates a Boss Agent, executes the research workflow,
    and broadcasts state updates, logs, confidence scores, and results
    to all connected WebSocket clients.
    
    Args:
        goal: The research goal to execute
        session_id: Unique session identifier
    
    Returns:
        Dictionary containing the research result
    
    Requirements: 10.2, 10.3, 10.4, 10.6, 10.11
    """
    global current_execution
    
    try:
        # Initialize components
        config = Config()
        logger = StructuredLogger(session_id=session_id)
        memory = MemorySystem()
        
        # Create Model Router for LLM calls
        from model_router import ModelRouter
        model_router = ModelRouter(
            api_key=config.OPENROUTER_API_KEY,
            logger=logger
        )
        
        # Create Boss Agent with model router
        boss = BossAgent(
            logger=logger,
            memory_system=memory,
            model_router=model_router,
            max_retries=config.MAX_RETRY_ATTEMPTS,
            confidence_threshold=config.CONFIDENCE_THRESHOLD_PROCEED / 100.0  # Convert to 0-1 scale
        )
        
        # Broadcast initial state
        await manager.broadcast(create_state_update_message(
            state="PLANNING",
            agent="Boss Agent",
            action=f"Starting research: {goal}"
        ))
        
        # Track execution state
        current_execution = {
            "session_id": session_id,
            "goal": goal,
            "status": "running",
            "start_time": datetime.utcnow().isoformat()
        }
        
        # Execute research with real-time updates
        # Note: In a full implementation, we would hook into the Boss Agent's
        # execution to broadcast updates at each step. For now, we'll execute
        # and broadcast the result.
        
        result = boss.execute_research(goal)
        
        # Get the session_id that was created by the boss agent
        session_id = str(boss.session_id)
        
        # Broadcast final result
        await manager.broadcast(create_result_message(result.to_dict()))
        
        # Broadcast completion state
        await manager.broadcast(create_state_update_message(
            state="COMPLETE",
            agent="Boss Agent",
            action="Research completed successfully"
        ))
        
        # Update execution state
        current_execution["status"] = "completed"
        current_execution["end_time"] = datetime.utcnow().isoformat()
        
        return result.to_dict()
        
    except Exception as e:
        # Broadcast error
        error_msg = f"Research execution failed: {str(e)}"
        await manager.broadcast(create_error_message(error_msg, {"goal": goal}))
        
        # Update execution state
        if current_execution:
            current_execution["status"] = "error"
            current_execution["error"] = str(e)
            current_execution["end_time"] = datetime.utcnow().isoformat()
        
        raise


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for client connections.
    
    Handles incoming WebSocket connections, processes client messages,
    and manages the connection lifecycle.
    
    Requirements: 10.1, 10.11
    """
    await manager.connect(websocket)
    
    try:
        # Send connection confirmation
        await manager.send_personal_message({
            "type": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": "Connected to research agent server"}
        }, websocket)
        
        # Send current execution state if any
        if current_execution:
            await manager.send_personal_message({
                "type": "execution_state",
                "timestamp": datetime.utcnow().isoformat(),
                "data": current_execution
            }, websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "start_research":
                # Start a new research task
                goal = data.get("goal")
                if not goal:
                    await manager.send_personal_message(
                        create_error_message("No research goal provided"),
                        websocket
                    )
                    continue
                
                # Generate session ID
                session_id = str(uuid.uuid4())
                
                # Execute research in background
                asyncio.create_task(execute_research(goal, session_id))
                
                # Send acknowledgment
                await manager.send_personal_message({
                    "type": "research_started",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "session_id": session_id,
                        "goal": goal
                    }
                }, websocket)
            
            elif message_type == "get_sessions":
                # Retrieve session history
                try:
                    memory = MemorySystem()
                    sessions = memory.list_sessions(limit=data.get("limit", 50))
                    await manager.send_personal_message({
                        "type": "sessions",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {"sessions": [s.to_dict() for s in sessions]}
                    }, websocket)
                except Exception as e:
                    await manager.send_personal_message(
                        create_error_message(f"Failed to retrieve sessions: {str(e)}"),
                        websocket
                    )
            
            elif message_type == "get_session_history":
                # Retrieve specific session history
                session_id = data.get("session_id")
                if not session_id:
                    await manager.send_personal_message(
                        create_error_message("No session_id provided"),
                        websocket
                    )
                    continue
                
                try:
                    memory = MemorySystem()
                    history = memory.get_session_history(session_id)
                    await manager.send_personal_message({
                        "type": "session_history",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": history.to_dict() if history else None
                    }, websocket)
                except Exception as e:
                    await manager.send_personal_message(
                        create_error_message(f"Failed to retrieve session history: {str(e)}"),
                        websocket
                    )
            
            elif message_type == "ping":
                # Respond to ping
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
            
            else:
                # Unknown message type
                await manager.send_personal_message(
                    create_error_message(f"Unknown message type: {message_type}"),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.get("/")
async def get_index():
    """
    Serve the main HTML page.
    
    Returns:
        HTML response with the web UI
    """
    index_path = UI_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Autonomous Research Agent</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>Autonomous Research Agent</h1>
        <p>WebSocket server is running. Frontend UI files not found.</p>
        <p>Connect to WebSocket at: <code>ws://localhost:8000/ws</code></p>
    </body>
    </html>
    """)


@app.get("/styles.css")
async def get_styles():
    """Serve the CSS file."""
    css_path = UI_DIR / "styles.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return HTMLResponse(content="/* CSS not found */", media_type="text/css")


@app.get("/app.js")
async def get_app_js():
    """Serve the JavaScript file."""
    js_path = UI_DIR / "app.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    return HTMLResponse(content="// JavaScript not found", media_type="application/javascript")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with server status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_connections": len(manager.active_connections),
        "current_execution": current_execution
    }


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Start the WebSocket server.
    
    Args:
        host: Host address to bind to
        port: Port number to listen on
        reload: Enable auto-reload for development
    """
    uvicorn.run(
        "ui.websocket_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    start_server(reload=True)
