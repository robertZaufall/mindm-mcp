#!/usr/bin/env python3
"""
server.py - FastMCP implementation for the mindm library

This module implements a Model Context Protocol (MCP) server
for interacting with MindManager through the mindm library using FastMCP.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

try:
    from mcp.server.fastmcp import FastMCP, Context
except ImportError:
    print("Error: Model Context Protocol SDK is required")
    print("Install with: pip install mcp")
    sys.exit(1)

import mindm.mindmanager as mm
import mindmap.mindmap as mindmap
import mindmap.serialization as serialization
from mindmap.mindmap import MindmapTopic, MindmapLink, MindmapNotes, MindmapTag, MindmapReference, MindmapImage, MindmapIcon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mindm-mcp")

@dataclass
class AppContext:
    """Application context for the MindManager MCP server"""
    mindmanager: Optional[mm.Mindmanager] = None
    platform: Optional[str] = None
    document: Optional[Any] = None
    charttype: str = "auto"
    macos_access: str = "appplescript"

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Manage application lifecycle with context
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        AppContext: Application context for the server
    """
    # Initialize on startup
    context = AppContext()
    logger.info("MindManager MCP server starting")
    
    try:
        yield context
    finally:
        # Cleanup on shutdown
        if context.mindmanager is not None:
            # Note: This is a simplified cleanup since Mindmanager in mindm
            # doesn't have a specific shutdown method
            context.mindmanager = None
            logger.info("MindManager MCP server shutting down")

# Create the MCP server
mcp = FastMCP(
    "MindManager",
    description="MindManager Model Context Protocol server for Windows and macOS",
    lifespan=app_lifespan
)

@mcp.tool()
async def initialize(
    charttype: str = "auto", 
    macos_access: str = "applescript",
    ctx: Context[AppContext, Any] = None
) -> Dict[str, Any]:
    """
    Initialize the MindManager interface
    
    Args:
        charttype: Chart type (auto, orgchart, radial)
        macos_access: macOS access method (appscript, applescript)
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Initialization status with platform information
    """
    try:
        # Initialize MindManager
        ctx.app.charttype = charttype
        ctx.app.macos_access = macos_access
        
        ctx.app.mindmanager = mm.Mindmanager(charttype, macos_access)
        ctx.app.platform = ctx.app.mindmanager.platform
        
        if ctx.app.mindmanager.document_exists():
            ctx.app.document = ctx.app.mindmanager.get_active_document_object()
            logger.info(f"Initialized MindManager on {ctx.app.platform} platform")
            return {"status": "success", "platform": ctx.app.platform}
        else:
            logger.warning("No MindManager document is open")
            return {"status": "warning", "message": "No document is open", "platform": ctx.app.platform}
                
    except Exception as e:
        logger.error(f"Error initializing MindManager: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_version(ctx: Context[AppContext, Any] = None) -> Dict[str, Any]:
    """
    Get the MindManager version
    
    Args:
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Version information
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    try:
        version = ctx.app.mindmanager.get_version()
        return {"status": "success", "version": version}
    except Exception as e:
        logger.error(f"Error getting version: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_mindmap(
    mode: str = "full",
    ctx: Context[AppContext, Any] = None
) -> Dict[str, Any]:
    """
    Get the current mindmap structure
    
    Args:
        mode: Attribute gathering mode (full, content, text)
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Mindmap data
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    if not ctx.app.mindmanager.document_exists():
        return {"status": "error", "message": "No document is open"}
    
    try:
        # Create MindmapDocument instance
        doc = mindmap.MindmapDocument(
            charttype=ctx.app.charttype, 
            macos_access=ctx.app.macos_access if ctx.app.platform == "darwin" else None
        )
        
        # Get the mindmap
        result = doc.get_mindmap(mode=mode)
        if not result:
            return {"status": "error", "message": "Failed to get mindmap"}
        
        # Serialize mindmap
        guid_mapping = {}
        serialization.build_mapping(doc.mindmap, guid_mapping)
        serialized = serialization.serialize_object_simple(doc.mindmap)
        
        return {
            "status": "success", 
            "mindmap": serialized,
            "max_topic_level": doc.max_topic_level
        }
        
    except Exception as e:
        logger.error(f"Error getting mindmap: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_central_topic(ctx: Context[AppContext, Any] = None) -> Dict[str, Any]:
    """
    Get the central topic of the mindmap
    
    Args:
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Central topic data
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    try:
        central_topic = ctx.app.mindmanager.get_central_topic()
        if central_topic:
            serialized = serialization.serialize_object_simple(central_topic)
            return {"status": "success", "topic": serialized}
        else:
            return {"status": "error", "message": "Could not get central topic"}
    except Exception as e:
        logger.error(f"Error getting central topic: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_selection(ctx: Context[AppContext, Any] = None) -> Dict[str, Any]:
    """
    Get the currently selected topics
    
    Args:
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Selected topics data
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    try:
        selection = ctx.app.mindmanager.get_selection()
        
        if not selection:
            return {"status": "success", "selection": []}
        
        selected_topics = []
        for topic in selection:
            topic_data = {
                "guid": ctx.app.mindmanager.get_guid_from_topic(topic),
                "text": ctx.app.mindmanager.get_text_from_topic(topic),
                "level": ctx.app.mindmanager.get_level_from_topic(topic)
            }
            selected_topics.append(topic_data)
            
        return {"status": "success", "selection": selected_topics}
    except Exception as e:
        logger.error(f"Error getting selection: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def create_mindmap(
    mindmap_data: Dict[str, Any],
    charttype: str = "auto",
    ctx: Context[AppContext, Any] = None
) -> Dict[str, Any]:
    """
    Create a new mindmap from the provided structure
    
    Args:
        mindmap_data: Serialized mindmap structure
        charttype: Chart type to use
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Creation status
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    try:
        if not mindmap_data:
            return {"status": "error", "message": "No mindmap data provided"}
        
        # Convert serialized data back to a MindmapTopic structure
        central_topic = MindmapTopic(
            text=mindmap_data.get("text", "New Mindmap"),
            guid=mindmap_data.get("guid", "")
        )
        
        # Process subtopics recursively
        def process_subtopics(parent_topic, subtopics_data):
            if not subtopics_data:
                return
            
            for subtopic_data in subtopics_data:
                subtopic = MindmapTopic(
                    text=subtopic_data.get("text", ""),
                    guid=subtopic_data.get("guid", ""),
                    parent=parent_topic
                )
                
                if "notes" in subtopic_data:
                    notes_data = subtopic_data["notes"]
                    subtopic.notes = MindmapNotes(
                        text=notes_data.get("text", ""),
                        xhtml=notes_data.get("xhtml", ""),
                        rtf=notes_data.get("rtf", "")
                    )
                
                # Add tags
                if "tags" in subtopic_data:
                    for tag_text in subtopic_data["tags"]:
                        subtopic.tags.append(MindmapTag(text=tag_text))
                
                # Process links
                if "links" in subtopic_data:
                    for link_data in subtopic_data["links"]:
                        subtopic.links.append(MindmapLink(
                            text=link_data.get("text", ""),
                            url=link_data.get("url", ""),
                            guid=link_data.get("guid", "")
                        ))
                
                # Process references
                if "references" in subtopic_data:
                    for ref_data in subtopic_data["references"]:
                        subtopic.references.append(MindmapReference(
                            guid_1=ref_data.get("guid_1", ""),
                            guid_2=ref_data.get("guid_2", ""),
                            direction=ref_data.get("direction", 1),
                            label=ref_data.get("label", "")
                        ))
                
                parent_topic.subtopics.append(subtopic)
                
                # Process nested subtopics
                if "subtopics" in subtopic_data:
                    process_subtopics(subtopic, subtopic_data["subtopics"])
        
        # Process main subtopics
        if "subtopics" in mindmap_data:
            process_subtopics(central_topic, mindmap_data["subtopics"])
        
        # Create document and mindmap
        doc = mindmap.MindmapDocument(charttype=charttype)
        doc.mindmap = central_topic
        doc.create_mindmap()
        
        return {"status": "success", "message": "Mindmap created successfully"}
    except Exception as e:
        logger.error(f"Error creating mindmap: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def add_subtopic(
    parent_guid: str,
    text: str = "New Topic",
    ctx: Context[AppContext, Any] = None
) -> Dict[str, Any]:
    """
    Add a subtopic to an existing topic
    
    Args:
        parent_guid: GUID of the parent topic
        text: Text content for the new subtopic
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Operation status with new subtopic GUID
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    try:
        if not parent_guid:
            return {"status": "error", "message": "Parent GUID is required"}
        
        # Get the parent topic
        parent = ctx.app.mindmanager.get_topic_by_id(parent_guid)
        if not parent:
            return {"status": "error", "message": "Parent topic not found"}
        
        # Add the subtopic
        subtopic = ctx.app.mindmanager.add_subtopic_to_topic(parent, text)
        if not subtopic:
            return {"status": "error", "message": "Failed to create subtopic"}
        
        subtopic_guid = ctx.app.mindmanager.get_guid_from_topic(subtopic)
        
        return {
            "status": "success",
            "guid": subtopic_guid,
            "text": text
        }
    except Exception as e:
        logger.error(f"Error adding subtopic: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_topic_text(
    guid: str,
    text: str,
    ctx: Context[AppContext, Any] = None
) -> Dict[str, Any]:
    """
    Set the text content of a topic
    
    Args:
        guid: GUID of the topic to update
        text: New text content
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Operation status
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    try:
        if not guid:
            return {"status": "error", "message": "Topic GUID is required"}
        
        # Get the topic
        topic = ctx.app.mindmanager.get_topic_by_id(guid)
        if not topic:
            return {"status": "error", "message": "Topic not found"}
        
        # Update the text
        ctx.app.mindmanager.set_text_to_topic(topic, text)
        
        return {
            "status": "success",
            "guid": guid,
            "text": text
        }
    except Exception as e:
        logger.error(f"Error setting topic text: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def add_relationship(
    from_guid: str,
    to_guid: str,
    label: str = "",
    ctx: Context[AppContext, Any] = None
) -> Dict[str, Any]:
    """
    Add a relationship between two topics
    
    Args:
        from_guid: GUID of the source topic
        to_guid: GUID of the target topic
        label: Label for the relationship
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Operation status
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    try:
        if not from_guid or not to_guid:
            return {"status": "error", "message": "Source and target GUIDs are required"}
        
        # Add the relationship
        ctx.app.mindmanager.add_relationship(from_guid, to_guid, label)
        
        return {
            "status": "success",
            "from_guid": from_guid,
            "to_guid": to_guid,
            "label": label
        }
    except Exception as e:
        logger.error(f"Error adding relationship: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def add_tag(
    topic_guid: str,
    tag_text: str,
    ctx: Context[AppContext, Any] = None
) -> Dict[str, Any]:
    """
    Add a tag to a topic
    
    Args:
        topic_guid: GUID of the topic
        tag_text: Text of the tag
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Operation status
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    try:
        if not topic_guid:
            return {"status": "error", "message": "Topic GUID is required"}
        
        if not tag_text:
            return {"status": "error", "message": "Tag text is required"}
        
        # Add the tag
        ctx.app.mindmanager.add_tag_to_topic(topic=None, tag_text=tag_text, topic_guid=topic_guid)
        
        return {
            "status": "success",
            "topic_guid": topic_guid,
            "tag_text": tag_text
        }
    except Exception as e:
        logger.error(f"Error adding tag: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_library_folder(ctx: Context[AppContext, Any] = None) -> Dict[str, Any]:
    """
    Get the MindManager library folder
    
    Args:
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Library folder path
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    try:
        library_folder = ctx.app.mindmanager.get_library_folder()
        return {
            "status": "success",
            "library_folder": library_folder,
            "platform": ctx.app.platform
        }
    except Exception as e:
        logger.error(f"Error getting library folder: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_background_image(
    image_path: str,
    ctx: Context[AppContext, Any] = None
) -> Dict[str, Any]:
    """
    Set the background image for the current document
    
    Args:
        image_path: Path to the image file
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Operation status
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    try:
        if not image_path:
            return {"status": "error", "message": "Image path is required"}
        
        # Check if the file exists
        if not os.path.exists(image_path):
            return {"status": "error", "message": f"Image file not found: {image_path}"}
        
        # Set the background image
        ctx.app.mindmanager.set_document_background_image(image_path)
        
        return {
            "status": "success",
            "image_path": image_path
        }
    except Exception as e:
        logger.error(f"Error setting background image: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def export_to_mermaid(
    id_only: bool = False,
    ctx: Context[AppContext, Any] = None
) -> Dict[str, Any]:
    """
    Export the current mindmap to Mermaid format
    
    Args:
        id_only: If True, export with ID references only
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Mermaid diagram representation
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    if not ctx.app.mindmanager.document_exists():
        return {"status": "error", "message": "No document is open"}
    
    try:
        # Create MindmapDocument instance
        doc = mindmap.MindmapDocument(
            charttype=ctx.app.charttype, 
            macos_access=ctx.app.macos_access if ctx.app.platform == "darwin" else None
        )
        
        # Get the mindmap
        result = doc.get_mindmap(mode="full")
        if not result:
            return {"status": "error", "message": "Failed to get mindmap"}
        
        # Create GUID mapping and serialize to Mermaid
        guid_mapping = {}
        serialization.build_mapping(doc.mindmap, guid_mapping)
        mermaid = serialization.serialize_mindmap(doc.mindmap, guid_mapping, id_only=id_only)
        
        return {
            "status": "success",
            "mermaid": mermaid
        }
    except Exception as e:
        logger.error(f"Error exporting to Mermaid: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def export_to_markdown(
    include_notes: bool = True,
    ctx: Context[AppContext, Any] = None
) -> Dict[str, Any]:
    """
    Export the current mindmap to Markdown format
    
    Args:
        include_notes: If True, include notes
        ctx: MCP context
        
    Returns:
        Dict[str, Any]: Markdown representation
    """
    if not ctx.app.mindmanager:
        return {"status": "error", "message": "MindManager not initialized"}
    
    if not ctx.app.mindmanager.document_exists():
        return {"status": "error", "message": "No document is open"}
    
    try:
        # Create MindmapDocument instance
        doc = mindmap.MindmapDocument(
            charttype=ctx.app.charttype, 
            macos_access=ctx.app.macos_access if ctx.app.platform == "darwin" else None
        )
        
        # Get the mindmap
        result = doc.get_mindmap(mode="full" if include_notes else "text")
        if not result:
            return {"status": "error", "message": "Failed to get mindmap"}
        
        # Serialize to Markdown
        markdown = serialization.serialize_mindmap_markdown(doc.mindmap, include_notes=include_notes)
        
        return {
            "status": "success",
            "markdown": markdown
        }
    except Exception as e:
        logger.error(f"Error exporting to Markdown: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.resource("mindmanager://info")
async def get_mindmanager_info() -> str:
    """
    Get information about the MindManager application
    
    Returns:
        str: Information about MindManager
    """
    # Now, how do we access the context?
    # Let's try to get it from a global variable or another approach
    
    # Example approach using a global variable to access the context
    from mcp.server.fastmcp import get_current_context
    
    try:
        # Get the current context
        ctx = get_current_context()
        
        # Check if MindManager is initialized
        if not hasattr(ctx.app, 'mindmanager') or ctx.app.mindmanager is None:
            return "MindManager is not initialized"
        
        version = ctx.app.mindmanager.get_version()
        platform = ctx.app.platform
        library = ctx.app.mindmanager.get_library_folder()
        
        info = (
            f"MindManager Information\n"
            f"----------------------\n"
            f"Version: {version}\n"
            f"Platform: {platform}\n"
            f"Library Folder: {library}\n"
        )
        
        if ctx.app.mindmanager.document_exists():
            info += "Status: Document is open\n"
        else:
            info += "Status: No document is open\n"
            
        return info
    except Exception as e:
        logger.error(f"Error getting MindManager info: {str(e)}")
        return f"Error getting MindManager info: {str(e)}"

if __name__ == "__main__":
    import argparse
    import uvicorn
    import anyio
    
    parser = argparse.ArgumentParser(description="MindManager MCP Server")
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    args = parser.parse_args()
    
    logger.info(f"Starting MindManager MCP server on {args.host}:{args.port}")
    
    # Option 1: Try running with transport="sse" explicitly
    try:
        from mcp.server.config import set_server_settings
        # Try to set server settings if the function exists
        set_server_settings(host=args.host, port=args.port)
    except ImportError:
        pass
    
    # Run the server with sse transport (web server)
    mcp.run(transport="sse")