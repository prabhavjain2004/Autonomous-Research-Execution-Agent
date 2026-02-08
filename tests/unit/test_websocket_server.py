"""
Unit Tests for WebSocket Server

Tests the WebSocket server functionality including connection management,
message broadcasting, and research execution integration.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from ui.websocket_server import (
    ConnectionManager,
    create_state_update_message,
    create_log_message,
    create_confidence_message,
    create_result_message,
    create_error_message,
    execute_research,
    app
)


class TestConnectionManager:
    """Test suite for ConnectionManager class."""
    
    def test_initialization(self):
        """Test ConnectionManager initializes with empty connections."""
        manager = ConnectionManager()
        assert len(manager.active_connections) == 0
        assert isinstance(manager.active_connections, set)
    
    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connecting a WebSocket."""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)
        
        await manager.connect(websocket)
        
        websocket.accept.assert_called_once()
        assert websocket in manager.active_connections
        assert len(manager.active_connections) == 1
    
    def test_disconnect(self):
        """Test disconnecting a WebSocket."""
        manager = ConnectionManager()
        websocket = Mock(spec=WebSocket)
        manager.active_connections.add(websocket)
        
        manager.disconnect(websocket)
        
        assert websocket not in manager.active_connections
        assert len(manager.active_connections) == 0
    
    def test_disconnect_nonexistent(self):
        """Test disconnecting a WebSocket that isn't connected."""
        manager = ConnectionManager()
        websocket = Mock(spec=WebSocket)
        
        # Should not raise an error
        manager.disconnect(websocket)
        assert len(manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_send_personal_message_success(self):
        """Test sending a personal message successfully."""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)
        message = {"type": "test", "data": "hello"}
        
        await manager.send_personal_message(message, websocket)
        
        websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_personal_message_failure(self):
        """Test handling failure when sending personal message."""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)
        websocket.send_json.side_effect = Exception("Connection error")
        manager.active_connections.add(websocket)
        message = {"type": "test", "data": "hello"}
        
        await manager.send_personal_message(message, websocket)
        
        # Should disconnect on error
        assert websocket not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_connections(self):
        """Test broadcasting to multiple connections."""
        manager = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        ws3 = AsyncMock(spec=WebSocket)
        
        manager.active_connections.add(ws1)
        manager.active_connections.add(ws2)
        manager.active_connections.add(ws3)
        
        message = {"type": "broadcast", "data": "test"}
        await manager.broadcast(message)
        
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_removes_failed_connections(self):
        """Test that broadcast removes connections that fail."""
        manager = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        ws2.send_json.side_effect = Exception("Connection error")
        ws3 = AsyncMock(spec=WebSocket)
        
        manager.active_connections.add(ws1)
        manager.active_connections.add(ws2)
        manager.active_connections.add(ws3)
        
        message = {"type": "broadcast", "data": "test"}
        await manager.broadcast(message)
        
        # ws2 should be removed due to error
        assert ws1 in manager.active_connections
        assert ws2 not in manager.active_connections
        assert ws3 in manager.active_connections
        assert len(manager.active_connections) == 2
    
    @pytest.mark.asyncio
    async def test_broadcast_to_empty_connections(self):
        """Test broadcasting with no active connections."""
        manager = ConnectionManager()
        message = {"type": "broadcast", "data": "test"}
        
        # Should not raise an error
        await manager.broadcast(message)


class TestMessageCreators:
    """Test suite for message creation functions."""
    
    def test_create_state_update_message(self):
        """Test creating a state update message."""
        message = create_state_update_message("PLANNING", "Research Agent", "Searching web")
        
        assert message["type"] == "state_update"
        assert "timestamp" in message
        assert message["data"]["state"] == "PLANNING"
        assert message["data"]["agent"] == "Research Agent"
        assert message["data"]["action"] == "Searching web"
    
    def test_create_state_update_message_minimal(self):
        """Test creating a state update message with minimal data."""
        message = create_state_update_message("IDLE")
        
        assert message["type"] == "state_update"
        assert message["data"]["state"] == "IDLE"
        assert message["data"]["agent"] is None
        assert message["data"]["action"] is None
    
    def test_create_log_message(self):
        """Test creating a log message."""
        log_entry = {
            "level": "INFO",
            "event_type": "state_transition",
            "message": "Transitioned to PLANNING"
        }
        message = create_log_message(log_entry)
        
        assert message["type"] == "log"
        assert "timestamp" in message
        assert message["data"] == log_entry
    
    def test_create_confidence_message(self):
        """Test creating a confidence message."""
        factors = {"source_count": 0.8, "reliability": 0.9}
        message = create_confidence_message("Research Agent", 0.85, factors)
        
        assert message["type"] == "confidence"
        assert "timestamp" in message
        assert message["data"]["agent"] == "Research Agent"
        assert message["data"]["score"] == 0.85
        assert message["data"]["factors"] == factors
    
    def test_create_confidence_message_no_factors(self):
        """Test creating a confidence message without factors."""
        message = create_confidence_message("Analyst Agent", 0.75)
        
        assert message["type"] == "confidence"
        assert message["data"]["agent"] == "Analyst Agent"
        assert message["data"]["score"] == 0.75
        assert message["data"]["factors"] == {}
    
    def test_create_result_message(self):
        """Test creating a result message."""
        result = {
            "session_id": "test-123",
            "goal": "Research AI trends",
            "insights": ["AI is growing"]
        }
        message = create_result_message(result)
        
        assert message["type"] == "result"
        assert "timestamp" in message
        assert message["data"] == result
    
    def test_create_error_message(self):
        """Test creating an error message."""
        context = {"goal": "Test goal", "phase": "research"}
        message = create_error_message("Tool execution failed", context)
        
        assert message["type"] == "error"
        assert "timestamp" in message
        assert message["data"]["error"] == "Tool execution failed"
        assert message["data"]["context"] == context
    
    def test_create_error_message_no_context(self):
        """Test creating an error message without context."""
        message = create_error_message("Generic error")
        
        assert message["type"] == "error"
        assert message["data"]["error"] == "Generic error"
        assert message["data"]["context"] == {}


class TestExecuteResearch:
    """Test suite for execute_research function."""
    
    @pytest.mark.asyncio
    @patch('ui.websocket_server.BossAgent')
    @patch('ui.websocket_server.StructuredLogger')
    @patch('ui.websocket_server.MemorySystem')
    @patch('ui.websocket_server.Config')
    @patch('ui.websocket_server.manager')
    async def test_execute_research_success(self, mock_manager, mock_config, 
                                           mock_memory, mock_logger, mock_boss):
        """Test successful research execution."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.MAX_RETRIES = 3
        mock_config_instance.CONFIDENCE_THRESHOLD_PROCEED = 0.7
        mock_config.return_value = mock_config_instance
        
        mock_result = Mock()
        mock_result.to_dict.return_value = {
            "session_id": "test-123",
            "goal": "Test goal",
            "insights": ["Test insight"]
        }
        mock_boss_instance = Mock()
        mock_boss_instance.execute_research.return_value = mock_result
        mock_boss.return_value = mock_boss_instance
        
        mock_manager.broadcast = AsyncMock()
        
        # Execute
        result = await execute_research("Test goal", "test-123")
        
        # Verify
        assert result["session_id"] == "test-123"
        assert result["goal"] == "Test goal"
        assert mock_boss_instance.execute_research.called
        assert mock_manager.broadcast.call_count >= 2  # At least start and end messages
    
    @pytest.mark.asyncio
    @patch('ui.websocket_server.BossAgent')
    @patch('ui.websocket_server.StructuredLogger')
    @patch('ui.websocket_server.MemorySystem')
    @patch('ui.websocket_server.Config')
    @patch('ui.websocket_server.manager')
    async def test_execute_research_failure(self, mock_manager, mock_config,
                                           mock_memory, mock_logger, mock_boss):
        """Test research execution with failure."""
        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.MAX_RETRIES = 3
        mock_config_instance.CONFIDENCE_THRESHOLD_PROCEED = 0.7
        mock_config.return_value = mock_config_instance
        
        mock_boss_instance = Mock()
        mock_boss_instance.execute_research.side_effect = Exception("Execution failed")
        mock_boss.return_value = mock_boss_instance
        
        mock_manager.broadcast = AsyncMock()
        
        # Execute and verify exception
        with pytest.raises(Exception, match="Execution failed"):
            await execute_research("Test goal", "test-123")
        
        # Verify error was broadcast
        assert mock_manager.broadcast.called


class TestWebSocketEndpoints:
    """Test suite for WebSocket endpoints."""
    
    def test_health_check_endpoint(self):
        """Test the health check endpoint."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "active_connections" in data
    
    def test_index_endpoint(self):
        """Test the index endpoint."""
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        assert "Autonomous Research Agent" in response.text
        assert "WebSocket" in response.text


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self):
        """Test WebSocket connection and disconnection."""
        manager = ConnectionManager()
        websocket = AsyncMock(spec=WebSocket)
        
        # Connect
        await manager.connect(websocket)
        assert len(manager.active_connections) == 1
        
        # Disconnect
        manager.disconnect(websocket)
        assert len(manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_websocket_connections(self):
        """Test multiple simultaneous WebSocket connections."""
        manager = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        ws3 = AsyncMock(spec=WebSocket)
        
        await manager.connect(ws1)
        await manager.connect(ws2)
        await manager.connect(ws3)
        
        assert len(manager.active_connections) == 3
        
        # Broadcast to all
        message = {"type": "test"}
        await manager.broadcast(message)
        
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()
        ws3.send_json.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
