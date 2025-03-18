# tests/test_client.py
"""
Tests for the MindManager MCP client.

These tests validate the basic functionality of the client library.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from mindm_mcp.client import MindManagerClient

@pytest.fixture
def client():
    """Create a test client instance."""
    return MindManagerClient("http://localhost:8000")

@pytest.mark.asyncio
async def test_create_session(client):
    """Test creating a session."""
    with patch.object(client, "_http_session") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"session_id": "test-session-id"}
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        session_id = await client.create_session()
        
        assert session_id == "test-session-id"
        assert client.session_id == "test-session-id"
        mock_session.post.assert_called_once_with(
            "http://localhost:8000/sessions",
            json={"charttype": "auto", "turbo_mode": False},
        )

@pytest.mark.asyncio
async def test_get_mindmap(client):
    """Test getting a mindmap."""
    client.session_id = "test-session-id"
    
    with patch.object(client, "_http_session") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "mindmap": {
                    "guid": "central-topic-guid",
                    "text": "Central Topic",
                    "level": 0,
                },
                "max_topic_level": 1,
                "selected_topics": [],
                "central_topic_selected": False,
            },
        }
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = await client.get_mindmap()
        
        assert result["success"] is True
        assert result["data"]["mindmap"]["text"] == "Central Topic"
        mock_session.post.assert_called_once_with(
            "http://localhost:8000/sessions/test-session-id/get_mindmap",
        )

@pytest.mark.asyncio
async def test_add_topic(client):
    """Test adding a topic."""
    client.session_id = "test-session-id"
    
    with patch.object(client, "_http_session") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "guid": "new-topic-guid",
                "text": "New Topic",
            },
        }
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = await client.add_topic(
            text="New Topic",
            parent_guid="parent-guid",
            notes="Topic notes",
        )
        
        assert result["success"] is True
        assert result["data"]["guid"] == "new-topic-guid"
        mock_session.post.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(client):
    """Test error handling."""
    client.session_id = "test-session-id"
    
    with patch.object(client, "_http_session") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal server error"
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(Exception):
            await client.get_mindmap()
