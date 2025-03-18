# mindm_mcp/mcp_plugin.py
"""
Model Context Protocol (MCP) Plugin for MindManager.

This module implements an MCP plugin that allows Claude Desktop and other
AI assistants to interact with MindManager through the mindm library.
"""

import os
import json
import logging
import asyncio
import socket
import struct
import sys
from typing import Dict, List, Any, Optional, Callable, Awaitable, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mindm-mcp-plugin")

# Use absolute import
try:
    from mindm_mcp.client import MindManagerClient
except ImportError:
    # For development/testing in the current directory
    from client import MindManagerClient

class MindManagerMCPPlugin:
    """Model Context Protocol plugin for MindManager."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """
        Initialize the MindManager MCP Plugin.
        
        Args:
            base_url: URL of the MindManager MCP Server
        """
        self.base_url = base_url
        self.client = MindManagerClient(base_url)
        self.session_id = None
        self._capabilities = self._build_capabilities()
    
    async def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        print("Initializing MindManager MCP plugin", file=sys.stderr)
        try:
            # Create a session
            self.session_id = await self.client.create_session()
            print(f"Created MindManager session: {self.session_id}", file=sys.stderr)
            return True
        except Exception as e:
            print(f"Failed to initialize MindManager MCP plugin: {str(e)}", file=sys.stderr)
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources before shutdown."""
        logger.info("Cleaning up MindManager MCP plugin")
        if self.session_id:
            try:
                await self.client.delete_session(self.session_id)
                logger.info(f"Deleted MindManager session: {self.session_id}")
            except Exception as e:
                logger.error(f"Error deleting session: {str(e)}")
        
        try:
            await self.client.close()
        except Exception as e:
            logger.error(f"Error closing client: {str(e)}")
    
    def _build_capabilities(self) -> Dict[str, Any]:
        """
        Build the capabilities description for the MCP plugin.
        
        Returns:
            Dict: Capabilities description
        """
        return {
            "name": "mindmanager",
            "display_name": "MindManager",
            "description": "Interact with MindManager to create and modify mind maps",
            "version": "0.1.0",
            "actions": [
                {
                    "name": "get_mindmap",
                    "description": "Get the current mindmap from MindManager",
                    "parameters": {},
                    "returns": {
                        "mindmap": {
                            "description": "The current mindmap structure",
                            "type": "object"
                        },
                        "max_topic_level": {
                            "description": "The maximum topic level in the mindmap",
                            "type": "integer"
                        },
                        "selected_topics": {
                            "description": "List of currently selected topics",
                            "type": "array"
                        },
                        "central_topic_selected": {
                            "description": "Whether the central topic is selected",
                            "type": "boolean"
                        }
                    }
                },
                {
                    "name": "create_mindmap",
                    "description": "Create a new mindmap",
                    "parameters": {
                        "central_topic": {
                            "description": "The central topic text",
                            "type": "string",
                            "required": True
                        },
                        "topics": {
                            "description": "List of topics to add",
                            "type": "array",
                            "required": False
                        },
                        "relationships": {
                            "description": "List of relationships between topics",
                            "type": "array",
                            "required": False
                        }
                    },
                    "returns": {
                        "message": {
                            "description": "Status message",
                            "type": "string"
                        }
                    }
                },
                {
                    "name": "add_topic",
                    "description": "Add a topic to the mindmap",
                    "parameters": {
                        "text": {
                            "description": "The topic text",
                            "type": "string",
                            "required": True
                        },
                        "parent_guid": {
                            "description": "GUID of the parent topic",
                            "type": "string",
                            "required": False
                        },
                        "notes": {
                            "description": "Notes for the topic",
                            "type": "string",
                            "required": False
                        }
                    },
                    "returns": {
                        "guid": {
                            "description": "GUID of the created topic",
                            "type": "string"
                        },
                        "text": {
                            "description": "Text of the created topic",
                            "type": "string"
                        }
                    }
                },
                {
                    "name": "update_topic",
                    "description": "Update an existing topic",
                    "parameters": {
                        "guid": {
                            "description": "GUID of the topic to update",
                            "type": "string",
                            "required": True
                        },
                        "text": {
                            "description": "New topic text",
                            "type": "string",
                            "required": False
                        },
                        "notes": {
                            "description": "New notes for the topic",
                            "type": "string",
                            "required": False
                        }
                    },
                    "returns": {
                        "message": {
                            "description": "Status message",
                            "type": "string"
                        }
                    }
                },
                {
                    "name": "add_relationship",
                    "description": "Add a relationship between topics",
                    "parameters": {
                        "guid_1": {
                            "description": "GUID of the first topic",
                            "type": "string",
                            "required": True
                        },
                        "guid_2": {
                            "description": "GUID of the second topic",
                            "type": "string",
                            "required": True
                        },
                        "label": {
                            "description": "Label for the relationship",
                            "type": "string",
                            "required": False
                        }
                    },
                    "returns": {
                        "message": {
                            "description": "Status message",
                            "type": "string"
                        }
                    }
                },
                {
                    "name": "add_tag",
                    "description": "Add a tag to a topic",
                    "parameters": {
                        "topic_guid": {
                            "description": "GUID of the topic",
                            "type": "string",
                            "required": True
                        },
                        "tag_text": {
                            "description": "Tag text",
                            "type": "string",
                            "required": True
                        }
                    },
                    "returns": {
                        "message": {
                            "description": "Status message",
                            "type": "string"
                        }
                    }
                },
                {
                    "name": "serialize_mindmap",
                    "description": "Serialize the mindmap to a specified format",
                    "parameters": {
                        "format_type": {
                            "description": "Format to serialize to (mermaid, markdown, json)",
                            "type": "string",
                            "required": False
                        }
                    },
                    "returns": {
                        "format": {
                            "description": "The format of the serialized mindmap",
                            "type": "string"
                        },
                        "content": {
                            "description": "The serialized mindmap content",
                            "type": "string"
                        }
                    }
                }
            ]
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of the MCP plugin.
        
        Returns:
            Dict: Capabilities description
        """
        return self._capabilities
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP request from Claude Desktop.
        
        Args:
            request: MCP request
            
        Returns:
            Dict: MCP response
        """
        try:
            # Extract action and parameters
            action = request.get("action", "")
            params = request.get("params", {})
            
            # Special handling for capabilities request
            if action == "get_capabilities":
                return {
                    "success": True,
                    "data": await self.get_capabilities(),
                }
            
            # For multiple parameters ensure the session_id is set
            if isinstance(params, dict):
                params["session_id"] = self.session_id
            
            # Dispatch the request to the appropriate handler
            if action == "get_mindmap":
                return await self._handle_get_mindmap(params)
            elif action == "create_mindmap":
                return await self._handle_create_mindmap(params)
            elif action == "add_topic":
                return await self._handle_add_topic(params)
            elif action == "update_topic":
                return await self._handle_update_topic(params)
            elif action == "add_relationship":
                return await self._handle_add_relationship(params)
            elif action == "add_tag":
                return await self._handle_add_tag(params)
            elif action == "serialize_mindmap":
                return await self._handle_serialize_mindmap(params)
            else:
                logger.warning(f"Unknown action: {action}")
                return self._create_error_response(f"Unknown action: {action}")
        
        except Exception as e:
            logger.error(f"Error handling MCP request: {str(e)}")
            return self._create_error_response(f"Error: {str(e)}")
    
    async def _handle_get_mindmap(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_mindmap action.
        
        Args:
            params: Action parameters
            
        Returns:
            Dict: Action response
        """
        try:
            result = await self.client.get_mindmap()
            
            if result["success"]:
                return {
                    "success": True,
                    "data": result["data"],
                }
            else:
                return self._create_error_response(result.get("error", "Unknown error"))
        
        except Exception as e:
            logger.error(f"Error in get_mindmap: {str(e)}")
            return self._create_error_response(f"Error: {str(e)}")
    
    async def _handle_create_mindmap(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create_mindmap action.
        
        Args:
            params: Action parameters
            
        Returns:
            Dict: Action response
        """
        try:
            central_topic = params.get("central_topic", "Central Topic")
            topics = params.get("topics", [])
            relationships = params.get("relationships", [])
            
            result = await self.client.create_mindmap(
                central_topic=central_topic,
                topics=topics,
                relationships=relationships,
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "Mindmap created successfully",
                }
            else:
                return self._create_error_response(result.get("error", "Unknown error"))
        
        except Exception as e:
            logger.error(f"Error in create_mindmap: {str(e)}")
            return self._create_error_response(f"Error: {str(e)}")
    
    async def _handle_add_topic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle add_topic action.
        
        Args:
            params: Action parameters
            
        Returns:
            Dict: Action response
        """
        try:
            text = params.get("text", "")
            parent_guid = params.get("parent_guid", None)
            notes = params.get("notes", None)
            
            result = await self.client.add_topic(
                text=text,
                parent_guid=parent_guid,
                notes=notes,
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "data": result.get("data", {}),
                }
            else:
                return self._create_error_response(result.get("error", "Unknown error"))
        
        except Exception as e:
            logger.error(f"Error in add_topic: {str(e)}")
            return self._create_error_response(f"Error: {str(e)}")
    
    async def _handle_update_topic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle update_topic action.
        
        Args:
            params: Action parameters
            
        Returns:
            Dict: Action response
        """
        try:
            guid = params.get("guid", "")
            text = params.get("text", None)
            notes = params.get("notes", None)
            
            if not guid:
                return self._create_error_response("Topic GUID is required")
            
            result = await self.client.update_topic(
                guid=guid,
                text=text,
                notes=notes,
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "Topic updated successfully",
                }
            else:
                return self._create_error_response(result.get("error", "Unknown error"))
        
        except Exception as e:
            logger.error(f"Error in update_topic: {str(e)}")
            return self._create_error_response(f"Error: {str(e)}")
    
    async def _handle_add_relationship(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle add_relationship action.
        
        Args:
            params: Action parameters
            
        Returns:
            Dict: Action response
        """
        try:
            guid_1 = params.get("guid_1", "")
            guid_2 = params.get("guid_2", "")
            label = params.get("label", "")
            
            if not guid_1 or not guid_2:
                return self._create_error_response("Both guid_1 and guid_2 are required")
            
            result = await self.client.add_relationship(
                guid_1=guid_1,
                guid_2=guid_2,
                label=label,
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "Relationship added successfully",
                }
            else:
                return self._create_error_response(result.get("error", "Unknown error"))
        
        except Exception as e:
            logger.error(f"Error in add_relationship: {str(e)}")
            return self._create_error_response(f"Error: {str(e)}")
    
    async def _handle_add_tag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle add_tag action.
        
        Args:
            params: Action parameters
            
        Returns:
            Dict: Action response
        """
        try:
            topic_guid = params.get("topic_guid", "")
            tag_text = params.get("tag_text", "")
            
            if not topic_guid or not tag_text:
                return self._create_error_response("Both topic_guid and tag_text are required")
            
            result = await self.client.add_tag(
                topic_guid=topic_guid,
                tag_text=tag_text,
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "Tag added successfully",
                }
            else:
                return self._create_error_response(result.get("error", "Unknown error"))
        
        except Exception as e:
            logger.error(f"Error in add_tag: {str(e)}")
            return self._create_error_response(f"Error: {str(e)}")
    
    async def _handle_serialize_mindmap(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle serialize_mindmap action.
        
        Args:
            params: Action parameters
            
        Returns:
            Dict: Action response
        """
        try:
            format_type = params.get("format_type", "mermaid")
            
            result = await self.client.serialize_mindmap(
                format_type=format_type,
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "data": result.get("data", {}),
                }
            else:
                return self._create_error_response(result.get("error", "Unknown error"))
        
        except Exception as e:
            logger.error(f"Error in serialize_mindmap: {str(e)}")
            return self._create_error_response(f"Error: {str(e)}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Create an error response.
        
        Args:
            error_message: Error message
            
        Returns:
            Dict: Error response
        """
        return {
            "success": False,
            "error": error_message,
        }

class MCPServer:
    """MCP Server implementation for Claude Desktop integration."""
    
    def __init__(self, plugin: MindManagerMCPPlugin, host: str = "localhost", port: int = 8090):
        """
        Initialize the MCP Server.
        
        Args:
            plugin: MindManager MCP Plugin instance
            host: Host to listen on
            port: Port to listen on
        """
        self.plugin = plugin
        self.host = host
        self.port = port
        self.server = None
        self.shutdown_event = asyncio.Event()
        self.clients = set()
    
    async def start(self):
        """Start the MCP Server."""
        logger.info(f"Starting MCP Server on {self.host}:{self.port}")
        
        # Initialize the plugin
        success = await self.plugin.initialize()
        if not success:
            logger.error("Failed to initialize MindManager MCP plugin")
            return False
        
        # Create the server
        try:
            server = await asyncio.start_server(
                self._handle_connection,
                self.host,
                self.port,
            )
            
            self.server = server
            logger.info(f"MCP Server running on {self.host}:{self.port}")
            
            # Serve until shut down
            try:
                await self.shutdown_event.wait()
            finally:
                logger.info("Shutting down MCP Server")
                server.close()
                await server.wait_closed()
                await self.plugin.cleanup()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MCP Server: {str(e)}")
            return False
    
    async def stop(self):
        """Stop the MCP Server."""
        logger.info("Stopping MCP Server")
        
        # Close all client connections
        for writer in self.clients:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing client connection: {str(e)}")
        
        self.shutdown_event.set()
    
    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handle a client connection.
        
        Args:
            reader: StreamReader for receiving data
            writer: StreamWriter for sending data
        """
        peer = writer.get_extra_info("peername")
        logger.info(f"Connection from {peer}")
        self.clients.add(writer)
        
        try:
            while not reader.at_eof():
                # Read request length (4 bytes, little-endian unsigned int)
                length_bytes = await reader.readexactly(4)
                length = int.from_bytes(length_bytes, byteorder="little", signed=False)
                
                # Read request JSON
                request_bytes = await reader.readexactly(length)
                request_str = request_bytes.decode("utf-8")
                
                try:
                    request = json.loads(request_str)
                    logger.debug(f"Received request: {request}")
                    
                    # Process the request
                    response = await self.plugin.handle_request(request)
                    
                    # Send response
                    response_str = json.dumps(response)
                    response_bytes = response_str.encode("utf-8")
                    
                    # Write response length and data
                    writer.write(len(response_bytes).to_bytes(4, byteorder="little", signed=False))
                    writer.write(response_bytes)
                    await writer.drain()
                
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    await self._send_error_response(writer, f"Invalid JSON: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    await self._send_error_response(writer, f"Error: {str(e)}")
        
        except asyncio.IncompleteReadError:
            logger.info(f"Client {peer} disconnected")
        
        except ConnectionResetError:
            logger.info(f"Connection reset by {peer}")
        
        except Exception as e:
            logger.error(f"Error handling connection: {e}")
        
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            
            self.clients.discard(writer)
            logger.info(f"Connection from {peer} closed")
    
    async def _send_error_response(self, writer: asyncio.StreamWriter, error_message: str):
        """
        Send an error response to the client.
        
        Args:
            writer: StreamWriter for sending data
            error_message: Error message
        """
        try:
            error_response = json.dumps({"success": False, "error": error_message})
            error_bytes = error_response.encode("utf-8")
            writer.write(len(error_bytes).to_bytes(4, byteorder="little", signed=False))
            writer.write(error_bytes)
            await writer.drain()
        except Exception as e:
            logger.error(f"Error sending error response: {str(e)}")
