# mindm_mcp/server.py
"""
MindManager MCP Server

This module implements a Model Context Protocol (MCP) server for the mindm library,
enabling AI assistants like Claude to interact with MindManager.
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Dict, List, Optional, Any, Union

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import mindm.mindmanager as mm
from mindmap.mindmap import MindmapDocument, MindmapTopic, MindmapNotes, MindmapLink, MindmapReference, MindmapTag
import mindmap.serialization as mms

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mindm-mcp")

# Create FastAPI app
app = FastAPI(
    title="MindManager MCP Server",
    description="Model Context Protocol server for integrating MindManager with AI assistants",
    version="0.1.0",
)

# Add CORS middleware to allow connections from Claude Desktop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active sessions
active_sessions: Dict[str, Dict[str, Any]] = {}

# ----- Pydantic Models -----

class SessionConfig(BaseModel):
    """Configuration for creating a new MindManager session."""
    charttype: str = Field(default="auto", description="Chart type (auto, radial, orgchart)")
    turbo_mode: bool = Field(default=False, description="Enable turbo mode for faster processing")
    
class SessionInfo(BaseModel):
    """Information about an active MindManager session."""
    session_id: str
    charttype: str
    turbo_mode: bool
    document_exists: bool

class TopicData(BaseModel):
    """Data structure for a mind map topic."""
    text: str
    guid: Optional[str] = None
    notes: Optional[str] = None
    parent_guid: Optional[str] = None
    
class MindmapData(BaseModel):
    """Data structure for a complete mindmap."""
    central_topic: str
    topics: List[TopicData] = []
    relationships: List[Dict[str, Any]] = []

class MCPRequest(BaseModel):
    """Generic MCP request structure."""
    action: str
    params: Dict[str, Any] = {}
    
class MCPResponse(BaseModel):
    """Generic MCP response structure."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

# ----- Helper Functions -----

def create_session(charttype: str = "auto", turbo_mode: bool = False) -> str:
    """
    Create a new MindManager session.
    
    Args:
        charttype: Chart type (auto, radial, orgchart)
        turbo_mode: Enable turbo mode for faster processing
        
    Returns:
        str: Session ID
    """
    session_id = str(uuid.uuid4())
    
    try:
        # Create MindmapDocument instance
        document = MindmapDocument(charttype=charttype, turbo_mode=turbo_mode)
        
        # Store session information
        active_sessions[session_id] = {
            "document": document,
            "charttype": charttype,
            "turbo_mode": turbo_mode,
            "last_accessed": asyncio.get_event_loop().time(),
        }
        
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

def get_session(session_id: str) -> Dict[str, Any]:
    """
    Get an active session by ID.
    
    Args:
        session_id: Session ID
        
    Returns:
        Dict: Session information
    """
    if session_id not in active_sessions:
        logger.error(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    
    # Update last accessed time
    active_sessions[session_id]["last_accessed"] = asyncio.get_event_loop().time()
    return active_sessions[session_id]

def mindmap_topic_to_dict(topic: MindmapTopic, recursive: bool = True, visited=None) -> Dict[str, Any]:
    """
    Convert a MindmapTopic to a dictionary representation.
    
    Args:
        topic: MindmapTopic instance
        recursive: Whether to include subtopics recursively
        visited: Set of visited topic GUIDs to prevent recursion loops
        
    Returns:
        Dict: Dictionary representation of the topic
    """
    if visited is None:
        visited = set()
        
    if topic.guid in visited:
        # Return minimal information for already visited topics to avoid cycles
        return {
            "guid": topic.guid,
            "text": topic.text,
            "level": topic.level,
            "visited_reference": True,
        }
    
    visited.add(topic.guid)
    
    result = {
        "guid": topic.guid,
        "text": topic.text,
        "level": topic.level,
    }
    
    if topic.notes:
        if topic.notes.text:
            result["notes"] = topic.notes.text
        elif topic.notes.xhtml:
            result["notes"] = topic.notes.xhtml
    
    if topic.links and len(topic.links) > 0:
        result["links"] = [
            {"text": link.text, "url": link.url, "guid": link.guid} 
            for link in topic.links
        ]
    
    if topic.tags and len(topic.tags) > 0:
        result["tags"] = [tag.text for tag in topic.tags]
    
    if topic.references and len(topic.references) > 0:
        result["references"] = [
            {
                "guid_1": ref.guid_1,
                "guid_2": ref.guid_2,
                "direction": ref.direction,
                "label": ref.label,
            }
            for ref in topic.references
        ]
    
    if recursive and topic.subtopics and len(topic.subtopics) > 0:
        result["subtopics"] = [
            mindmap_topic_to_dict(subtopic, recursive, visited.copy())
            for subtopic in topic.subtopics
        ]
    
    return result

# ----- API Routes -----

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "MindManager MCP Server"}

@app.post("/sessions", response_model=SessionInfo)
async def create_new_session(config: SessionConfig):
    """
    Create a new MindManager session.
    
    Args:
        config: Session configuration
        
    Returns:
        SessionInfo: Information about the created session
    """
    session_id = create_session(config.charttype, config.turbo_mode)
    session = get_session(session_id)
    
    return SessionInfo(
        session_id=session_id,
        charttype=session["charttype"],
        turbo_mode=session["turbo_mode"],
        document_exists=session["document"].mindm.document_exists(),
    )

@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """
    Get information about an active session.
    
    Args:
        session_id: Session ID
        
    Returns:
        SessionInfo: Session information
    """
    session = get_session(session_id)
    
    return SessionInfo(
        session_id=session_id,
        charttype=session["charttype"],
        turbo_mode=session["turbo_mode"],
        document_exists=session["document"].mindm.document_exists(),
    )

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete an active session.
    
    Args:
        session_id: Session ID
        
    Returns:
        Dict: Status information
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    
    try:
        # Clean up resources
        session = active_sessions[session_id]
        del active_sessions[session_id]
        logger.info(f"Deleted session: {session_id}")
        return {"success": True, "message": f"Session {session_id} deleted"}
    
    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.post("/sessions/{session_id}/get_mindmap")
async def get_mindmap(session_id: str):
    """
    Get the current mindmap from MindManager.
    
    Args:
        session_id: Session ID
        
    Returns:
        Dict: Mindmap data
    """
    session = get_session(session_id)
    document = session["document"]
    
    try:
        # Get the mindmap from the active document
        if not document.get_mindmap():
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No mindmap document is open in MindManager"},
            )
        
        # Convert mindmap to dictionary
        mindmap_data = mindmap_topic_to_dict(document.mindmap)
        
        return {
            "success": True,
            "data": {
                "mindmap": mindmap_data,
                "max_topic_level": document.max_topic_level,
                "selected_topics": [
                    {"text": text, "level": level, "guid": guid}
                    for text, level, guid in zip(
                        document.selected_topic_texts,
                        document.selected_topic_levels,
                        document.selected_topic_ids,
                    )
                ],
                "central_topic_selected": document.central_topic_selected,
            },
        }
    
    except Exception as e:
        logger.error(f"Failed to get mindmap: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to get mindmap: {str(e)}"},
        )

@app.post("/sessions/{session_id}/create_mindmap")
async def create_mindmap(session_id: str, data: MindmapData):
    """
    Create a new mindmap in MindManager.
    
    Args:
        session_id: Session ID
        data: Mindmap data
        
    Returns:
        Dict: Status information
    """
    session = get_session(session_id)
    document = session["document"]
    
    try:
        # Create a new mindmap structure
        central_topic = MindmapTopic(
            guid=str(uuid.uuid4()),
            text=data.central_topic,
            level=0,
        )
        
        # Add topics from the data
        topic_map = {central_topic.guid: central_topic}
        
        # First pass: create all topics
        for topic_data in data.topics:
            topic = MindmapTopic(
                guid=topic_data.guid or str(uuid.uuid4()),
                text=topic_data.text,
                level=1 if topic_data.parent_guid is None else 2,
            )
            
            if topic_data.notes:
                topic.notes = MindmapNotes(text=topic_data.notes)
            
            topic_map[topic.guid] = topic
        
        # Second pass: build topic hierarchy
        for topic_data in data.topics:
            topic = topic_map[topic_data.guid or ""]
            parent_guid = topic_data.parent_guid
            
            if parent_guid is None or parent_guid == "":
                # Connect to central topic
                topic.parent = central_topic
                central_topic.subtopics.append(topic)
            elif parent_guid in topic_map:
                # Connect to parent topic
                parent = topic_map[parent_guid]
                topic.parent = parent
                parent.subtopics.append(topic)
        
        # Add relationships
        for rel_data in data.relationships:
            if "guid_1" in rel_data and "guid_2" in rel_data:
                guid_1 = rel_data["guid_1"]
                guid_2 = rel_data["guid_2"]
                label = rel_data.get("label", "")
                direction = rel_data.get("direction", 1)
                
                if guid_1 in topic_map and guid_2 in topic_map:
                    topic = topic_map[guid_1]
                    ref = MindmapReference(
                        guid_1=guid_1,
                        guid_2=guid_2,
                        direction=direction,
                        label=label,
                    )
                    topic.references.append(ref)
        
        # Set the mindmap in the document
        document.mindmap = central_topic
        
        # Create the mindmap in MindManager
        document.create_mindmap()
        
        return {"success": True, "message": "Mindmap created successfully"}
    
    except Exception as e:
        logger.error(f"Failed to create mindmap: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to create mindmap: {str(e)}"},
        )

@app.post("/sessions/{session_id}/add_topic")
async def add_topic(session_id: str, topic_data: TopicData):
    """
    Add a topic to the mindmap.
    
    Args:
        session_id: Session ID
        topic_data: Topic data
        
    Returns:
        Dict: Status information with the created topic's GUID
    """
    session = get_session(session_id)
    document = session["document"]
    
    try:
        # Ensure we have the current mindmap
        if not document.mindmap:
            if not document.get_mindmap():
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "No mindmap document is open in MindManager"},
                )
        
        # Find the parent topic
        parent_guid = topic_data.parent_guid
        parent_topic = None
        
        if parent_guid is None or parent_guid == "":
            # Use central topic as parent
            parent_topic = document.mindm.get_central_topic()
        else:
            # Find the parent topic by GUID
            parent_topic = document.mindm.get_topic_by_id(parent_guid)
        
        if not parent_topic:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Parent topic not found"},
            )
        
        # Add the new topic
        new_topic = document.mindm.add_subtopic_to_topic(parent_topic, topic_data.text)
        new_topic_guid = document.mindm.get_guid_from_topic(new_topic)
        
        # Add notes if provided
        if topic_data.notes:
            notes = MindmapNotes(text=topic_data.notes)
            if notes.text:
                new_topic.Notes.Text = notes.text
        
        return {
            "success": True,
            "data": {
                "guid": new_topic_guid,
                "text": topic_data.text,
            },
        }
    
    except Exception as e:
        logger.error(f"Failed to add topic: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to add topic: {str(e)}"},
        )

@app.post("/sessions/{session_id}/update_topic")
async def update_topic(session_id: str, topic_data: TopicData):
    """
    Update an existing topic in the mindmap.
    
    Args:
        session_id: Session ID
        topic_data: Topic data with updated information
        
    Returns:
        Dict: Status information
    """
    session = get_session(session_id)
    document = session["document"]
    
    try:
        # Ensure we have a GUID
        if not topic_data.guid:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Topic GUID is required for updates"},
            )
        
        # Find the topic
        topic = document.mindm.get_topic_by_id(topic_data.guid)
        if not topic:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Topic not found with GUID: {topic_data.guid}"},
            )
        
        # Update the text
        if topic_data.text:
            document.mindm.set_text_to_topic(topic, topic_data.text)
        
        # Update notes if provided
        if topic_data.notes is not None:
            if document.mindm.platform == "win":
                # Windows implementation
                if topic_data.notes:
                    topic.Notes.Text = topic_data.notes
                else:
                    # Clear notes
                    topic.Notes.Text = ""
            elif document.mindm.platform == "darwin":
                # macOS implementation
                if topic_data.notes:
                    topic.notes.set(topic_data.notes)
                else:
                    # Clear notes
                    topic.notes.set("")
        
        return {"success": True, "message": "Topic updated successfully"}
    
    except Exception as e:
        logger.error(f"Failed to update topic: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to update topic: {str(e)}"},
        )

@app.post("/sessions/{session_id}/add_relationship")
async def add_relationship(
    session_id: str,
    relationship: Dict[str, str],
):
    """
    Add a relationship between two topics.
    
    Args:
        session_id: Session ID
        relationship: Dictionary with guid_1, guid_2, and optional label
        
    Returns:
        Dict: Status information
    """
    session = get_session(session_id)
    document = session["document"]
    
    try:
        # Validate input
        if "guid_1" not in relationship or "guid_2" not in relationship:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Both guid_1 and guid_2 are required"},
            )
        
        guid_1 = relationship["guid_1"]
        guid_2 = relationship["guid_2"]
        label = relationship.get("label", "")
        
        # Add the relationship
        document.mindm.add_relationship(guid_1, guid_2, label)
        
        return {"success": True, "message": "Relationship added successfully"}
    
    except Exception as e:
        logger.error(f"Failed to add relationship: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to add relationship: {str(e)}"},
        )

@app.post("/sessions/{session_id}/add_tag")
async def add_tag(
    session_id: str,
    data: Dict[str, str],
):
    """
    Add a tag to a topic.
    
    Args:
        session_id: Session ID
        data: Dictionary with topic_guid and tag_text
        
    Returns:
        Dict: Status information
    """
    session = get_session(session_id)
    document = session["document"]
    
    try:
        # Validate input
        if "topic_guid" not in data or "tag_text" not in data:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Both topic_guid and tag_text are required"},
            )
        
        topic_guid = data["topic_guid"]
        tag_text = data["tag_text"]
        
        # Add the tag
        document.mindm.add_tag_to_topic(topic=None, tag_text=tag_text, topic_guid=topic_guid)
        
        return {"success": True, "message": "Tag added successfully"}
    
    except Exception as e:
        logger.error(f"Failed to add tag: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to add tag: {str(e)}"},
        )

@app.post("/sessions/{session_id}/serialize_mindmap")
async def serialize_mindmap(session_id: str, format_type: str = "mermaid"):
    """
    Serialize the current mindmap to a specified format.
    
    Args:
        session_id: Session ID
        format_type: Format to serialize to (mermaid, markdown, json)
        
    Returns:
        Dict: Serialized mindmap data
    """
    session = get_session(session_id)
    document = session["document"]
    
    try:
        # Ensure we have the current mindmap
        if not document.mindmap:
            if not document.get_mindmap():
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "No mindmap document is open in MindManager"},
                )
        
        # Serialize based on format type
        if format_type == "mermaid":
            # Build GUID mapping
            guid_mapping = {}
            mms.build_mapping(document.mindmap, guid_mapping)
            
            # Serialize to Mermaid format
            serialized = mms.serialize_mindmap(document.mindmap, guid_mapping, id_only=False)
            return {"success": True, "data": {"format": "mermaid", "content": serialized}}
        
        elif format_type == "markdown":
            # Serialize to Markdown format
            serialized = mms.serialize_mindmap_markdown(document.mindmap, include_notes=True)
            return {"success": True, "data": {"format": "markdown", "content": serialized}}
        
        elif format_type == "json":
            # Serialize to JSON format
            serialized = mindmap_topic_to_dict(document.mindmap)
            return {"success": True, "data": {"format": "json", "content": serialized}}
        
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": f"Unsupported format type: {format_type}"},
            )
    
    except Exception as e:
        logger.error(f"Failed to serialize mindmap: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to serialize mindmap: {str(e)}"},
        )

# ----- WebSocket for MCP protocol -----

class ConnectionManager:
    """Manager for WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new client."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """Disconnect a client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def send_message(self, client_id: str, message: str):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections.values():
            await connection.send_text(message)

# Initialize connection manager
manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time communication.
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            try:
                # Parse request
                request = json.loads(data)
                action = request.get("action", "")
                params = request.get("params", {})
                
                # Process based on action
                if action == "create_session":
                    charttype = params.get("charttype", "auto")
                    turbo_mode = params.get("turbo_mode", False)
                    session_id = create_session(charttype, turbo_mode)
                    
                    await websocket.send_json({
                        "success": True,
                        "action": "create_session",
                        "data": {
                            "session_id": session_id,
                            "charttype": charttype,
                            "turbo_mode": turbo_mode,
                        },
                    })
                
                elif action == "get_mindmap":
                    session_id = params.get("session_id")
                    if not session_id:
                        await websocket.send_json({
                            "success": False,
                            "action": "get_mindmap",
                            "error": "session_id is required",
                        })
                        continue
                    
                    session = get_session(session_id)
                    document = session["document"]
                    
                    # Get the mindmap
                    if not document.get_mindmap():
                        await websocket.send_json({
                            "success": False,
                            "action": "get_mindmap",
                            "error": "No mindmap document is open in MindManager",
                        })
                        continue
                    
                    # Convert mindmap to dictionary
                    mindmap_data = mindmap_topic_to_dict(document.mindmap)
                    
                    await websocket.send_json({
                        "success": True,
                        "action": "get_mindmap",
                        "data": {
                            "mindmap": mindmap_data,
                            "max_topic_level": document.max_topic_level,
                            "selected_topics": [
                                {"text": text, "level": level, "guid": guid}
                                for text, level, guid in zip(
                                    document.selected_topic_texts,
                                    document.selected_topic_levels,
                                    document.selected_topic_ids,
                                )
                            ],
                            "central_topic_selected": document.central_topic_selected,
                        },
                    })
                
                elif action == "add_topic":
                    session_id = params.get("session_id")
                    text = params.get("text", "")
                    parent_guid = params.get("parent_guid", "")
                    notes = params.get("notes", "")
                    
                    if not session_id:
                        await websocket.send_json({
                            "success": False,
                            "action": "add_topic",
                            "error": "session_id is required",
                        })
                        continue
                    
                    session = get_session(session_id)
                    document = session["document"]
                    
                    # Find the parent topic
                    parent_topic = None
                    if not parent_guid:
                        parent_topic = document.mindm.get_central_topic()
                    else:
                        parent_topic = document.mindm.get_topic_by_id(parent_guid)
                    
                    if not parent_topic:
                        await websocket.send_json({
                            "success": False,
                            "action": "add_topic",
                            "error": "Parent topic not found",
                        })
                        continue
                    
                    # Add the topic
                    new_topic = document.mindm.add_subtopic_to_topic(parent_topic, text)
                    new_topic_guid = document.mindm.get_guid_from_topic(new_topic)
                    
                    # Add notes if provided
                    if notes:
                        if document.mindm.platform == "win":
                            new_topic.Notes.Text = notes
                        elif document.mindm.platform == "darwin":
                            new_topic.notes.set(notes)
                    
                    await websocket.send_json({
                        "success": True,
                        "action": "add_topic",
                        "data": {
                            "guid": new_topic_guid,
                            "text": text,
                        },
                    })
                
                else:
                    await websocket.send_json({
                        "success": False,
                        "action": action,
                        "error": f"Unknown action: {action}",
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "success": False,
                    "error": "Invalid JSON format",
                })
            
            except Exception as e:
                logger.error(f"Error processing WebSocket request: {str(e)}")
                await websocket.send_json({
                    "success": False,
                    "error": f"Error processing request: {str(e)}",
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(client_id)

# ----- Session Maintenance -----

async def cleanup_inactive_sessions():
    """
    Periodically clean up inactive sessions to free resources.
    
    This task runs every 5 minutes and removes sessions that have been
    inactive for more than 30 minutes.
    """
    while True:
        try:
            current_time = asyncio.get_event_loop().time()
            session_ids_to_remove = []
            
            for session_id, session in active_sessions.items():
                # Check if session has been inactive for more than 30 minutes
                if current_time - session["last_accessed"] > 1800:  # 30 minutes in seconds
                    session_ids_to_remove.append(session_id)
            
            # Remove inactive sessions
            for session_id in session_ids_to_remove:
                logger.info(f"Removing inactive session: {session_id}")
                del active_sessions[session_id]
            
            # Wait for 5 minutes before checking again
            await asyncio.sleep(300)
        
        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}")
            await asyncio.sleep(300)  # Continue the loop even if there's an error