#!/usr/bin/env python3
"""
Direct MindManager MCP Integration for Claude Desktop.

This script implements a direct MCP server that Claude Desktop can connect to
without requiring a separate MindManager MCP server process.
"""

import os
import sys
import asyncio
import json
import logging
import socket
import struct
import argparse
import signal
from typing import Dict, List, Any, Optional, Tuple

import mindm.mindmanager as mm
from mindmap.mindmap import MindmapDocument, MindmapTopic, MindmapNotes, MindmapTag

# Configure logging to go to stderr only
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("mindm-direct-integration")

class MindManagerDirectPlugin:
    """Direct MCP plugin for MindManager."""
    
    def __init__(self):
        """Initialize the MindManager Direct Plugin."""
        self.document = None
        self._capabilities = self._build_capabilities()
    
    async def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        print("Initializing MindManager Direct Plugin", file=sys.stderr)
        try:
            # Create MindmapDocument instance
            self.document = MindmapDocument(charttype="auto", turbo_mode=False)
            print("Created MindManager document", file=sys.stderr)
            return True
        except Exception as e:
            error_str = str(e)
            print(f"Failed to initialize MindManager Direct Plugin: {error_str}", file=sys.stderr)
            
            # Handle common errors with helpful messages
            if "declined permission" in error_str:
                print("\n===== PERMISSION ERROR =====", file=sys.stderr)
                print("MindManager requires automation permissions on macOS.", file=sys.stderr)
                print("Please follow these steps:", file=sys.stderr)
                print("1. Open System Preferences/Settings", file=sys.stderr)
                print("2. Go to Security & Privacy / Privacy", file=sys.stderr)
                print("3. Select 'Automation' from the list", file=sys.stderr)
                print("4. Ensure the checkbox next to 'MindManager' is checked for Terminal and/or Claude", file=sys.stderr)
                print("5. Restart Claude Desktop and try again", file=sys.stderr)
                print("============================\n", file=sys.stderr)
            elif "not found" in error_str and "Applications/MindManager.app" in error_str:
                print("\n===== APPLICATION ERROR =====", file=sys.stderr)
                print("MindManager application was not found.", file=sys.stderr)
                print("Please make sure MindManager is installed and located in the Applications folder.", file=sys.stderr)
                print("============================\n", file=sys.stderr)
                
            return False
    
    async def cleanup(self) -> None:
        """Clean up resources before shutdown."""
        print("Cleaning up MindManager Direct Plugin", file=sys.stderr)
    
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
            else:
                print(f"Unknown action: {action}", file=sys.stderr)
                return self._create_error_response(f"Unknown action: {action}")
        
        except Exception as e:
            print(f"Error handling MCP request: {str(e)}", file=sys.stderr)
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
            # Get the mindmap from the active document
            if not self.document.get_mindmap():
                return self._create_error_response("No mindmap document is open in MindManager")
            
            # Convert mindmap to dictionary
            mindmap_data = self._mindmap_topic_to_dict(self.document.mindmap)
            
            return {
                "success": True,
                "data": {
                    "mindmap": mindmap_data,
                    "max_topic_level": self.document.max_topic_level,
                    "selected_topics": [
                        {"text": text, "level": level, "guid": guid}
                        for text, level, guid in zip(
                            self.document.selected_topic_texts,
                            self.document.selected_topic_levels,
                            self.document.selected_topic_ids,
                        )
                    ],
                    "central_topic_selected": self.document.central_topic_selected,
                },
            }
        
        except Exception as e:
            print(f"Error in get_mindmap: {str(e)}", file=sys.stderr)
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
            central_topic_text = params.get("central_topic", "Central Topic")
            topics = params.get("topics", [])
            relationships = params.get("relationships", [])
            
            # Create a new mindmap with the central topic
            self.document.create_mindmap(central_topic_text)
            
            # Add topics
            for topic_data in topics:
                text = topic_data.get("text", "")
                parent_guid = topic_data.get("parent_guid", None)
                notes = topic_data.get("notes", None)
                
                if not parent_guid:
                    # Add to central topic
                    central_topic = self.document.mindm.get_central_topic()
                    new_topic = self.document.mindm.add_subtopic_to_topic(central_topic, text)
                else:
                    # Add to specified parent
                    parent = self.document.mindm.get_topic_by_id(parent_guid)
                    if not parent:
                        continue
                    new_topic = self.document.mindm.add_subtopic_to_topic(parent, text)
                
                # Add notes if provided
                if notes and new_topic:
                    if self.document.mindm.platform == "win":
                        new_topic.Notes.Text = notes
                    elif self.document.mindm.platform == "darwin":
                        new_topic.notes.set(notes)
            
            # Add relationships
            for rel in relationships:
                guid_1 = rel.get("guid_1", "")
                guid_2 = rel.get("guid_2", "")
                label = rel.get("label", "")
                
                if guid_1 and guid_2:
                    self.document.mindm.add_relationship(guid_1, guid_2, label)
            
            return {
                "success": True,
                "message": "Mindmap created successfully",
            }
        
        except Exception as e:
            print(f"Error in create_mindmap: {str(e)}", file=sys.stderr)
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
            
            # Ensure we have the current mindmap
            if not self.document.mindmap:
                if not self.document.get_mindmap():
                    return self._create_error_response("No mindmap document is open in MindManager")
            
            # Find the parent topic
            parent_topic = None
            
            if not parent_guid:
                # Use central topic as parent
                parent_topic = self.document.mindm.get_central_topic()
            else:
                # Find the parent topic by GUID
                parent_topic = self.document.mindm.get_topic_by_id(parent_guid)
            
            if not parent_topic:
                return self._create_error_response("Parent topic not found")
            
            # Add the new topic
            new_topic = self.document.mindm.add_subtopic_to_topic(parent_topic, text)
            new_topic_guid = self.document.mindm.get_guid_from_topic(new_topic)
            
            # Add notes if provided
            if notes:
                if self.document.mindm.platform == "win":
                    new_topic.Notes.Text = notes
                elif self.document.mindm.platform == "darwin":
                    new_topic.notes.set(notes)
            
            return {
                "success": True,
                "data": {
                    "guid": new_topic_guid,
                    "text": text,
                },
            }
        
        except Exception as e:
            print(f"Error in add_topic: {str(e)}", file=sys.stderr)
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
            
            # Find the topic
            topic = self.document.mindm.get_topic_by_id(guid)
            if not topic:
                return self._create_error_response(f"Topic not found with GUID: {guid}")
            
            # Update the text
            if text is not None:
                self.document.mindm.set_text_to_topic(topic, text)
            
            # Update notes if provided
            if notes is not None:
                if self.document.mindm.platform == "win":
                    topic.Notes.Text = notes if notes else ""
                elif self.document.mindm.platform == "darwin":
                    topic.notes.set(notes if notes else "")
            
            return {
                "success": True,
                "message": "Topic updated successfully",
            }
        
        except Exception as e:
            print(f"Error in update_topic: {str(e)}", file=sys.stderr)
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
            
            # Add the relationship
            self.document.mindm.add_relationship(guid_1, guid_2, label)
            
            return {
                "success": True,
                "message": "Relationship added successfully",
            }
        
        except Exception as e:
            print(f"Error in add_relationship: {str(e)}", file=sys.stderr)
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
            
            # Add the tag
            self.document.mindm.add_tag_to_topic(topic=None, tag_text=tag_text, topic_guid=topic_guid)
            
            return {
                "success": True,
                "message": "Tag added successfully",
            }
        
        except Exception as e:
            print(f"Error in add_tag: {str(e)}", file=sys.stderr)
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
    
    def _mindmap_topic_to_dict(self, topic: MindmapTopic, recursive: bool = True, visited=None) -> Dict[str, Any]:
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
                self._mindmap_topic_to_dict(subtopic, recursive, visited.copy())
                for subtopic in topic.subtopics
            ]
        
        return result

class DirectMCPServer:
    """Direct MCP Server implementation for Claude Desktop integration."""
    
    def __init__(self, plugin: MindManagerDirectPlugin, host: str = "localhost", port: int = 8090):
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
        print(f"Starting Direct MCP Server on {self.host}:{self.port}", file=sys.stderr)
        
        # Initialize the plugin
        success = await self.plugin.initialize()
        if not success:
            print("Failed to initialize MindManager Direct Plugin", file=sys.stderr)
            return False
        
        # Create the server
        try:
            server = await asyncio.start_server(
                self._handle_connection,
                self.host,
                self.port,
            )
            
            self.server = server
            print(f"Direct MCP Server running on {self.host}:{self.port}", file=sys.stderr)
            
            # Serve until shut down
            try:
                await self.shutdown_event.wait()
            finally:
                print("Shutting down Direct MCP Server", file=sys.stderr)
                server.close()
                await server.wait_closed()
                await self.plugin.cleanup()
                
            return True
            
        except Exception as e:
            print(f"Failed to start Direct MCP Server: {str(e)}", file=sys.stderr)
            return False
    
    async def stop(self):
        """Stop the MCP Server."""
        print("Stopping Direct MCP Server", file=sys.stderr)
        
        # Close all client connections
        for writer in self.clients:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                print(f"Error closing client connection: {str(e)}", file=sys.stderr)
        
        self.shutdown_event.set()
    
    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handle a client connection.
        
        Args:
            reader: StreamReader for receiving data
            writer: StreamWriter for sending data
        """
        peer = writer.get_extra_info("peername")
        print(f"Connection from {peer}", file=sys.stderr)
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
                    print(f"Received request: {request}", file=sys.stderr)
                    
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
                    print(f"Invalid JSON: {e}", file=sys.stderr)
                    await self._send_error_response(writer, f"Invalid JSON: {str(e)}")
                
                except Exception as e:
                    print(f"Error processing request: {e}", file=sys.stderr)
                    await self._send_error_response(writer, f"Error: {str(e)}")
        
        except asyncio.IncompleteReadError:
            print(f"Client {peer} disconnected", file=sys.stderr)
        
        except ConnectionResetError:
            print(f"Connection reset by {peer}", file=sys.stderr)
        
        except Exception as e:
            print(f"Error handling connection: {e}", file=sys.stderr)
        
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            
            self.clients.discard(writer)
            print(f"Connection from {peer} closed", file=sys.stderr)
    
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
            print(f"Error sending error response: {str(e)}", file=sys.stderr)

def find_free_port(host="localhost", start_port=8090):
    """
    Find a free port to use.
    
    Args:
        host: Host to check
        start_port: Port to start checking from
        
    Returns:
        int: Free port number
    """
    port = start_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        while port < start_port + 100:
            try:
                s.bind((host, port))
                s.listen(1)
                s.close()
                return port
            except OSError:
                port += 1
    raise RuntimeError("Could not find a free port")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Direct MindManager MCP Integration for Claude Desktop")
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind the MCP server to (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,  # 0 means find a free port
        help="Port to bind the MCP server to (default: auto-detect)",
    )
    return parser.parse_args()

async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # If port is 0, find a free port
    if args.port == 0:
        port = find_free_port(args.host, 8090)
    else:
        port = args.port
    
    # Create the plugin
    plugin = MindManagerDirectPlugin()
    
    # Create and start the server
    server = DirectMCPServer(plugin, host=args.host, port=port)
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(server.stop()))
    
    # Run the server
    try:
        print(f"Starting Direct MindManager MCP Integration on {args.host}:{port}", file=sys.stderr)
        print("Press Ctrl+C to stop the server", file=sys.stderr)
        
        server_started = await server.start()
        
        if not server_started:
            print("\n===== INITIALIZATION FAILED =====", file=sys.stderr)
            print("Could not start the MCP server due to initialization errors.", file=sys.stderr)
            print("Please check the above messages for details on how to fix this issue.", file=sys.stderr)
            print("================================\n", file=sys.stderr)
            
            # Keep the process alive for a few seconds so Claude Desktop can read the error message
            print("Waiting for 10 seconds before exiting...", file=sys.stderr)
            await asyncio.sleep(10)
            return 1
    
    except Exception as e:
        print(f"Error running Direct MCP server: {e}", file=sys.stderr)
        
        # Keep the process alive for a few seconds so Claude Desktop can read the error message
        print("Waiting for 10 seconds before exiting...", file=sys.stderr)
        await asyncio.sleep(10)
        return 1
    
    return 0

def run_direct_integration():
    """
    Entry point for the console script.
    This function is called when running mindm-direct-integration from the command line.
    """
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        print("Integration stopped by user", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Error running integration: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(run_direct_integration())