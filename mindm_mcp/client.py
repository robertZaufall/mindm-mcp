# mindm_mcp/client.py
"""
Client library for interacting with the MindManager MCP Server.

This module provides a convenient Python API for applications to communicate
with the MindManager MCP Server, enabling remote control of MindManager.
"""

import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mindm-mcp-client")

class MindManagerClient:
    """Client for interacting with MindManager through the MCP Server."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """
        Initialize the MindManager client.
        
        Args:
            base_url: URL of the MindManager MCP Server
        """
        self.base_url = base_url
        self.session_id = None
        self._http_session = None
    
    async def _ensure_session(self):
        """Ensure HTTP session is initialized."""
        if self._http_session is None:
            self._http_session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the HTTP session."""
        if self._http_session:
            await self._http_session.close()
            self._http_session = None
    
    async def create_session(self, charttype: str = "auto", turbo_mode: bool = False) -> str:
        """
        Create a new MindManager session.
        
        Args:
            charttype: Chart type (auto, radial, orgchart)
            turbo_mode: Enable turbo mode for faster processing
            
        Returns:
            str: Session ID
        """
        await self._ensure_session()
        
        async with self._http_session.post(
            f"{self.base_url}/sessions",
            json={"charttype": charttype, "turbo_mode": turbo_mode},
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.session_id = data["session_id"]
                return self.session_id
            else:
                error_text = await response.text()
                logger.error(f"Failed to create session: {error_text}")
                raise Exception(f"Failed to create session: {error_text}")
    
    async def get_session_info(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a session.
        
        Args:
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Session information
        """
        await self._ensure_session()
        session_id = session_id or self.session_id
        
        if not session_id:
            raise ValueError("No session ID provided and no current session")
        
        async with self._http_session.get(
            f"{self.base_url}/sessions/{session_id}",
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Failed to get session info: {error_text}")
                raise Exception(f"Failed to get session info: {error_text}")
    
    async def delete_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a session.
        
        Args:
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Status information
        """
        await self._ensure_session()
        session_id = session_id or self.session_id
        
        if not session_id:
            raise ValueError("No session ID provided and no current session")
        
        async with self._http_session.delete(
            f"{self.base_url}/sessions/{session_id}",
        ) as response:
            if response.status == 200:
                if session_id == self.session_id:
                    self.session_id = None
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Failed to delete session: {error_text}")
                raise Exception(f"Failed to delete session: {error_text}")
    
    async def get_mindmap(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the current mindmap.
        
        Args:
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Mindmap data
        """
        await self._ensure_session()
        session_id = session_id or self.session_id
        
        if not session_id:
            raise ValueError("No session ID provided and no current session")
        
        async with self._http_session.post(
            f"{self.base_url}/sessions/{session_id}/get_mindmap",
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Failed to get mindmap: {error_text}")
                raise Exception(f"Failed to get mindmap: {error_text}")
    
    async def create_mindmap(
        self,
        central_topic: str,
        topics: List[Dict[str, Any]] = None,
        relationships: List[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new mindmap.
        
        Args:
            central_topic: Text for the central topic
            topics: List of topic data dictionaries
            relationships: List of relationship dictionaries
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Status information
        """
        await self._ensure_session()
        session_id = session_id or self.session_id
        
        if not session_id:
            raise ValueError("No session ID provided and no current session")
        
        topics = topics or []
        relationships = relationships or []
        
        async with self._http_session.post(
            f"{self.base_url}/sessions/{session_id}/create_mindmap",
            json={
                "central_topic": central_topic,
                "topics": topics,
                "relationships": relationships,
            },
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Failed to create mindmap: {error_text}")
                raise Exception(f"Failed to create mindmap: {error_text}")
    
    async def add_topic(
        self,
        text: str,
        parent_guid: Optional[str] = None,
        notes: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a topic to the mindmap.
        
        Args:
            text: Topic text
            parent_guid: GUID of the parent topic (uses central topic if not provided)
            notes: Topic notes
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Status information with the created topic's GUID
        """
        await self._ensure_session()
        session_id = session_id or self.session_id
        
        if not session_id:
            raise ValueError("No session ID provided and no current session")
        
        data = {
            "text": text,
            "parent_guid": parent_guid,
        }
        
        if notes is not None:
            data["notes"] = notes
        
        async with self._http_session.post(
            f"{self.base_url}/sessions/{session_id}/add_topic",
            json=data,
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Failed to add topic: {error_text}")
                raise Exception(f"Failed to add topic: {error_text}")
    
    async def update_topic(
        self,
        guid: str,
        text: Optional[str] = None,
        notes: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing topic.
        
        Args:
            guid: Topic GUID
            text: New topic text (if None, keeps existing text)
            notes: New topic notes (if None, keeps existing notes)
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Status information
        """
        await self._ensure_session()
        session_id = session_id or self.session_id
        
        if not session_id:
            raise ValueError("No session ID provided and no current session")
        
        data = {
            "guid": guid,
        }
        
        if text is not None:
            data["text"] = text
        
        if notes is not None:
            data["notes"] = notes
        
        async with self._http_session.post(
            f"{self.base_url}/sessions/{session_id}/update_topic",
            json=data,
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Failed to update topic: {error_text}")
                raise Exception(f"Failed to update topic: {error_text}")
    
    async def add_relationship(
        self,
        guid_1: str,
        guid_2: str,
        label: str = "",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a relationship between topics.
        
        Args:
            guid_1: GUID of the first topic
            guid_2: GUID of the second topic
            label: Relationship label
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Status information
        """
        await self._ensure_session()
        session_id = session_id or self.session_id
        
        if not session_id:
            raise ValueError("No session ID provided and no current session")
        
        async with self._http_session.post(
            f"{self.base_url}/sessions/{session_id}/add_relationship",
            json={
                "guid_1": guid_1,
                "guid_2": guid_2,
                "label": label,
            },
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Failed to add relationship: {error_text}")
                raise Exception(f"Failed to add relationship: {error_text}")
    
    async def add_tag(
        self,
        topic_guid: str,
        tag_text: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a tag to a topic.
        
        Args:
            topic_guid: Topic GUID
            tag_text: Tag text
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Status information
        """
        await self._ensure_session()
        session_id = session_id or self.session_id
        
        if not session_id:
            raise ValueError("No session ID provided and no current session")
        
        async with self._http_session.post(
            f"{self.base_url}/sessions/{session_id}/add_tag",
            json={
                "topic_guid": topic_guid,
                "tag_text": tag_text,
            },
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Failed to add tag: {error_text}")
                raise Exception(f"Failed to add tag: {error_text}")
    
    async def serialize_mindmap(
        self,
        format_type: str = "mermaid",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Serialize the current mindmap to a specified format.
        
        Args:
            format_type: Format to serialize to (mermaid, markdown, json)
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Serialized mindmap data
        """
        await self._ensure_session()
        session_id = session_id or self.session_id
        
        if not session_id:
            raise ValueError("No session ID provided and no current session")
        
        params = {"format_type": format_type}
        
        async with self._http_session.post(
            f"{self.base_url}/sessions/{session_id}/serialize_mindmap",
            params=params,
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Failed to serialize mindmap: {error_text}")
                raise Exception(f"Failed to serialize mindmap: {error_text}")

# Async context manager for MindManagerClient
class MindManagerClientContext:
    """Context manager for MindManagerClient to ensure proper resource cleanup."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.client = MindManagerClient(base_url)
    
    async def __aenter__(self):
        return self.client
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.close()

# Synchronous wrapper for MindManagerClient
class SyncMindManagerClient:
    """
    Synchronous wrapper for MindManagerClient.
    
    This class provides a synchronous API for applications that do not use asyncio.
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """
        Initialize the synchronous MindManager client.
        
        Args:
            base_url: URL of the MindManager MCP Server
        """
        self.base_url = base_url
        self.client = MindManagerClient(base_url)
        self.session_id = None
        self._loop = None
    
    def _get_loop(self):
        """Get or create event loop for synchronous operations."""
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    def _run_async(self, coro):
        """Run coroutine synchronously."""
        loop = self._get_loop()
        return loop.run_until_complete(coro)
    
    def close(self):
        """Close the HTTP session."""
        self._run_async(self.client.close())
    
    def create_session(self, charttype: str = "auto", turbo_mode: bool = False) -> str:
        """
        Create a new MindManager session.
        
        Args:
            charttype: Chart type (auto, radial, orgchart)
            turbo_mode: Enable turbo mode for faster processing
            
        Returns:
            str: Session ID
        """
        result = self._run_async(self.client.create_session(charttype, turbo_mode))
        self.session_id = self.client.session_id
        return result
    
    def get_session_info(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a session.
        
        Args:
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Session information
        """
        return self._run_async(self.client.get_session_info(session_id or self.session_id))
    
    def delete_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a session.
        
        Args:
            session_id: Session ID (uses the current session if not provided)
            
        Returns:
            Dict: Status information
        """
        result = self._run_async(self.client.delete_session(session_id or self.session_id))
        if self.session_id == (session_id or self.session_id):
            self.session_id = None
        return result
    
    # Add synchronous versions of all other methods
    def get_mindmap(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self._run_async(self.client.get_mindmap(session_id or self.session_id))
    
    def create_mindmap(
        self,
        central_topic: str,
        topics: List[Dict[str, Any]] = None,
        relationships: List[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._run_async(
            self.client.create_mindmap(
                central_topic, topics, relationships, session_id or self.session_id
            )
        )
    
    def add_topic(
        self,
        text: str,
        parent_guid: Optional[str] = None,
        notes: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._run_async(
            self.client.add_topic(text, parent_guid, notes, session_id or self.session_id)
        )
    
    def update_topic(
        self,
        guid: str,
        text: Optional[str] = None,
        notes: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._run_async(
            self.client.update_topic(guid, text, notes, session_id or self.session_id)
        )
    
    def add_relationship(
        self,
        guid_1: str,
        guid_2: str,
        label: str = "",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._run_async(
            self.client.add_relationship(guid_1, guid_2, label, session_id or self.session_id)
        )
    
    def add_tag(
        self,
        topic_guid: str,
        tag_text: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._run_async(
            self.client.add_tag(topic_guid, tag_text, session_id or self.session_id)
        )
    
    def serialize_mindmap(
        self,
        format_type: str = "mermaid",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._run_async(
            self.client.serialize_mindmap(format_type, session_id or self.session_id)
        )

# Context manager for SyncMindManagerClient
class SyncMindManagerClientContext:
    """Context manager for SyncMindManagerClient to ensure proper resource cleanup."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.client = SyncMindManagerClient(base_url)
    
    def __enter__(self):
        return self.client
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
