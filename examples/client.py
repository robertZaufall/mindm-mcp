#!/usr/bin/env python3
"""
client.py - Example client for interacting with the mindm MCP server

This module demonstrates how to use the MCP client to interact with
the mindm server to manipulate MindManager maps programmatically.
"""

import json
import sys
import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from contextlib import AsyncExitStack

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Updated imports for current MCP SDK version
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("Error: Model Context Protocol SDK is required")
    print("Install with: pip install mcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mindm-mcp-client")

class MindManagerClient:
    """
    Client for interacting with the MindManager MCP server
    """
    
    def __init__(self, server_path: str = None):
        """
        Initialize the MindManager client
        
        Args:
            server_path (str): Path to the server script
        """
        self.server_path = server_path if server_path else "-m mindm_mcp.server"
        self.session = None
        self.exit_stack = AsyncExitStack()
        
    async def connect(self):
        """
        Connect to the MCP server
        """
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_path],
            env=None
        )
        
        # Use AsyncExitStack to manage the async context managers
        read_write = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.read_stream, self.write_stream = read_write
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.read_stream, self.write_stream))
        
        # Initialize the connection
        await self.session.initialize()
        logger.info(f"Connected to MindManager MCP server")
    
    async def disconnect(self):
        """
        Disconnect from the MCP server
        """
        # Close all context managers
        await self.exit_stack.aclose()
        self.session = None
        logger.info("Disconnected from MindManager MCP server")
    
    async def initialize(self, charttype: str = "auto", macos_access: str = "appscript") -> Dict[str, Any]:
        """
        Initialize the MindManager interface
        
        Args:
            charttype (str): Chart type (auto, orgchart, radial)
            macos_access (str): macOS access method (appscript, applescript)
            
        Returns:
            Dict[str, Any]: Initialization status
        """
        return await self.session.call_tool("initialize", {
            "charttype": charttype,
            "macos_access": macos_access
        })
    
    async def get_version(self) -> Dict[str, Any]:
        """
        Get the MindManager version
        
        Returns:
            Dict[str, Any]: Version information
        """
        return await self.session.call_tool("get_version")
    
    async def get_mindmap(self, mode: str = "full") -> Dict[str, Any]:
        """
        Get the current mindmap structure
        
        Args:
            mode (str): Attribute gathering mode (full, content, text)
            
        Returns:
            Dict[str, Any]: Mindmap data
        """
        return await self.session.call_tool("get_mindmap", {
            "mode": mode
        })
    
    async def get_central_topic(self) -> Dict[str, Any]:
        """
        Get the central topic of the mindmap
        
        Returns:
            Dict[str, Any]: Central topic data
        """
        return await self.session.call_tool("get_central_topic")
    
    async def get_selection(self) -> Dict[str, Any]:
        """
        Get the currently selected topics
        
        Returns:
            Dict[str, Any]: Selected topics data
        """
        return await self.session.call_tool("get_selection")
    
    async def create_mindmap(self, mindmap_data: Dict[str, Any], charttype: str = "auto") -> Dict[str, Any]:
        """
        Create a new mindmap from the provided structure
        
        Args:
            mindmap_data (Dict[str, Any]): Serialized mindmap structure
            charttype (str): Chart type to use
            
        Returns:
            Dict[str, Any]: Creation status
        """
        return await self.session.call_tool("create_mindmap", {
            "mindmap_data": mindmap_data,
            "charttype": charttype
        })
    
    async def add_subtopic(self, parent_guid: str, text: str = "New Topic") -> Dict[str, Any]:
        """
        Add a subtopic to an existing topic
        
        Args:
            parent_guid (str): GUID of the parent topic
            text (str): Text content for the new subtopic
            
        Returns:
            Dict[str, Any]: Operation status with new subtopic GUID
        """
        return await self.session.call_tool("add_subtopic", {
            "parent_guid": parent_guid,
            "text": text
        })
    
    async def set_topic_text(self, guid: str, text: str) -> Dict[str, Any]:
        """
        Set the text content of a topic
        
        Args:
            guid (str): GUID of the topic to update
            text (str): New text content
            
        Returns:
            Dict[str, Any]: Operation status
        """
        return await self.session.call_tool("set_topic_text", {
            "guid": guid,
            "text": text
        })
    
    async def add_relationship(self, from_guid: str, to_guid: str, label: str = "") -> Dict[str, Any]:
        """
        Add a relationship between two topics
        
        Args:
            from_guid (str): GUID of the source topic
            to_guid (str): GUID of the target topic
            label (str): Label for the relationship
            
        Returns:
            Dict[str, Any]: Operation status
        """
        return await self.session.call_tool("add_relationship", {
            "from_guid": from_guid,
            "to_guid": to_guid,
            "label": label
        })
    
    async def add_tag(self, topic_guid: str, tag_text: str) -> Dict[str, Any]:
        """
        Add a tag to a topic
        
        Args:
            topic_guid (str): GUID of the topic
            tag_text (str): Text of the tag
            
        Returns:
            Dict[str, Any]: Operation status
        """
        return await self.session.call_tool("add_tag", {
            "topic_guid": topic_guid,
            "tag_text": tag_text
        })
    
    async def get_library_folder(self) -> Dict[str, Any]:
        """
        Get the MindManager library folder
        
        Returns:
            Dict[str, Any]: Library folder path
        """
        return await self.session.call_tool("get_library_folder")
    
    async def set_background_image(self, image_path: str) -> Dict[str, Any]:
        """
        Set the background image for the current document
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            Dict[str, Any]: Operation status
        """
        return await self.session.call_tool("set_background_image", {
            "image_path": image_path
        })
    
    async def export_to_mermaid(self, id_only: bool = False) -> Dict[str, Any]:
        """
        Export the current mindmap to Mermaid format
        
        Args:
            id_only (bool): If True, export with ID references only
            
        Returns:
            Dict[str, Any]: Mermaid diagram representation
        """
        return await self.session.call_tool("export_to_mermaid", {
            "id_only": id_only
        })
    
    async def export_to_markdown(self, include_notes: bool = True) -> Dict[str, Any]:
        """
        Export the current mindmap to Markdown format
        
        Args:
            include_notes (bool): If True, include notes
            
        Returns:
            Dict[str, Any]: Markdown representation
        """
        return await self.session.call_tool("export_to_markdown", {
            "include_notes": include_notes
        })
    
    async def get_mindmanager_info(self) -> str:
        """
        Get information about the MindManager application
        
        Returns:
            str: Information about MindManager
        """
        content, _ = await self.session.read_resource("mindmanager://info")
        return content.decode("utf-8") if isinstance(content, bytes) else content
    
    async def get_topic_data(self, topic_guid: str) -> Dict[str, Any]:
        """
        Get data for a specific topic by GUID
        
        Args:
            topic_guid (str): GUID of the topic
            
        Returns:
            Dict[str, Any]: Topic data
        """
        # Get the entire mindmap and find the topic
        mindmap_result = await self.get_mindmap(mode="full")
        if mindmap_result["status"] != "success":
            return {"status": "error", "message": "Failed to get mindmap"}
        
        # Find the topic with the matching GUID
        mindmap = mindmap_result.get("mindmap", {})
        return self._find_topic_by_guid(mindmap, topic_guid)
    
    def _find_topic_by_guid(self, topic_data: Dict[str, Any], guid: str) -> Dict[str, Any]:
        """
        Recursively find a topic by GUID in the mindmap structure
        
        Args:
            topic_data (Dict[str, Any]): Current topic data
            guid (str): GUID to find
            
        Returns:
            Dict[str, Any]: Found topic data or error
        """
        if topic_data.get("guid", "") == guid:
            return {"status": "success", "topic": topic_data}
        
        for subtopic in topic_data.get("subtopics", []):
            result = self._find_topic_by_guid(subtopic, guid)
            if result["status"] == "success":
                return result
        
        return {"status": "error", "message": f"Topic with GUID {guid} not found"}
    
    async def iterate_topics(self, topic_guid: str, action: str, value: str = None) -> Dict[str, Any]:
        """
        Perform an action on all subtopics recursively
        
        Args:
            topic_guid (str): GUID of the starting topic
            action (str): Action to perform (e.g., 'uppercase', 'lowercase', 'prefix', 'suffix')
            value (str): Value to use for prefix/suffix actions
            
        Returns:
            Dict[str, Any]: Operation status
        """
        if not topic_guid:
            return {"status": "error", "message": "Topic GUID is required"}
        
        # Get current topic text
        topic_result = await self.get_topic_data(topic_guid)
        if topic_result["status"] != "success":
            return topic_result
        
        # Apply the action to the current topic
        text = topic_result.get("topic", {}).get("text", "")
        new_text = self._apply_text_action(text, action, value)
        
        # Update the topic
        update_result = await self.set_topic_text(topic_guid, new_text)
        if update_result["status"] != "success":
            return update_result
        
        # Process each subtopic recursively
        results = []
        for subtopic in topic_result.get("topic", {}).get("subtopics", []):
            subtopic_guid = subtopic.get("guid", "")
            if subtopic_guid:
                subtopic_result = await self.iterate_topics(subtopic_guid, action, value)
                results.append(subtopic_result)
        
        return {
            "status": "success", 
            "topic_guid": topic_guid,
            "text": new_text,
            "subtopics_processed": len(results)
        }
    
    def _apply_text_action(self, text: str, action: str, value: str = None) -> str:
        """
        Apply a text transformation action
        
        Args:
            text (str): Original text
            action (str): Action to apply
            value (str): Optional value for some actions
            
        Returns:
            str: Transformed text
        """
        if action == "uppercase":
            return text.upper()
        elif action == "lowercase":
            return text.lower()
        elif action == "capitalize":
            return text.capitalize()
        elif action == "title":
            return text.title()
        elif action == "prefix" and value:
            return f"{value}{text}"
        elif action == "suffix" and value:
            return f"{text}{value}"
        elif action == "replace" and value and "," in value:
            old, new = value.split(",", 1)
            return text.replace(old, new)
        else:
            return text  # No change if action not recognized


async def main():
    """
    Main function demonstrating client usage
    """
    client = MindManagerClient()
    
    try:
        # Connect to the MCP server
        await client.connect()
        
        # Initialize the connection to MindManager
        init_result = await client.initialize()
        if init_result["status"] != "success" and init_result["status"] != "warning":
            logger.error(f"Failed to initialize MindManager: {init_result.get('message', 'Unknown error')}")
            return
        
        logger.info(f"Connected to MindManager on {init_result.get('platform', 'unknown')} platform")
        
        # Get MindManager info from resource
        info = await client.get_mindmanager_info()
        logger.info(f"MindManager Info:\n{info}")
        
        # Get the version
        version_result = await client.get_version()
        if version_result["status"] == "success":
            logger.info(f"MindManager version: {version_result.get('version', 'unknown')}")
        
        # Get the central topic
        central_result = await client.get_central_topic()
        if central_result["status"] == "success":
            central_topic = central_result.get("topic", {})
            logger.info(f"Central topic: {central_topic.get('text', 'No text')}")
        
            # Add a subtopic to the central topic
            central_guid = central_topic.get("guid", "")
            if central_guid:
                subtopic_result = await client.add_subtopic(central_guid, "New MCP Subtopic")
                if subtopic_result["status"] == "success":
                    logger.info(f"Added subtopic: {subtopic_result.get('text', 'unknown')}")
                    subtopic_guid = subtopic_result.get("guid", "")
                    
                    # Add another level of subtopics
                    if subtopic_guid:
                        for i in range(3):
                            sub_result = await client.add_subtopic(subtopic_guid, f"Nested Topic {i+1}")
                            if sub_result["status"] == "success":
                                logger.info(f"  Added nested topic: {sub_result.get('text', 'unknown')}")
                        
                        # Get selection after adding subtopics
                        selection_result = await client.get_selection()
                        if selection_result["status"] == "success":
                            nested_topics = selection_result.get("selection", [])
                            
                            if len(nested_topics) >= 2:
                                first_guid = nested_topics[0].get("guid", "")
                                second_guid = nested_topics[1].get("guid", "")
                                if first_guid and second_guid:
                                    rel_result = await client.add_relationship(first_guid, second_guid, "Related to")
                                    if rel_result["status"] == "success":
                                        logger.info(f"Added relationship between topics")
                            
                            # Add tags to topics
                            for i, topic in enumerate(nested_topics):
                                topic_guid = topic.get("guid", "")
                                if topic_guid:
                                    tag_result = await client.add_tag(topic_guid, f"Priority-{i+1}")
                                    if tag_result["status"] == "success":
                                        logger.info(f"Added tag to topic: Priority-{i+1}")
        
        # Export to Mermaid format
        mermaid_result = await client.export_to_mermaid()
        if mermaid_result["status"] == "success":
            mermaid_content = mermaid_result.get("mermaid", "")
            preview_length = min(len(mermaid_content), 200)
            logger.info(f"Mermaid Diagram Preview:\n{mermaid_content[:preview_length]}...")
        
        # Export to Markdown format
        markdown_result = await client.export_to_markdown()
        if markdown_result["status"] == "success":
            markdown_content = markdown_result.get("markdown", "")
            preview_length = min(len(markdown_content), 200)
            logger.info(f"Markdown Content Preview:\n{markdown_content[:preview_length]}...")
        
        # Demonstrate topic text transformation
        if central_guid:
            transform_result = await client.iterate_topics(central_guid, "uppercase")
            if transform_result["status"] == "success":
                logger.info(f"Transformed topics to uppercase: {transform_result.get('subtopics_processed', 0)} subtopics processed")
        
        logger.info("Client example completed successfully")
    
    except Exception as e:
        logger.error(f"Error in client example: {str(e)}")
    
    finally:
        # Disconnect from the server
        await client.disconnect()


if __name__ == "__main__":
    try:
        # Run the main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Client example interrupted by user")