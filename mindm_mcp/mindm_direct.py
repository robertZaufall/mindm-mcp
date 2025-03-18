#!/usr/bin/env python3
"""
Direct MindManager MCP Integration for Claude Desktop.

This script directly interacts with MindManager without intermediate servers,
providing a streamlined MCP interface for Claude Desktop.
"""

import os
import sys
import json
import logging
import socket
import struct
import asyncio
import argparse
import signal
from typing import Dict, List, Any, Optional

try:
    import mindm.mindmanager as mm
    from mindmap.mindmap import MindmapDocument, MindmapTopic, MindmapNotes, MindmapTag
except ImportError:
    print("Error: mindm package not found. Installing it now...", file=sys.stderr)
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mindm"])
    import mindm.mindmanager as mm
    from mindmap.mindmap import MindmapDocument, MindmapTopic, MindmapNotes, MindmapTag

# Configure logging to go to stderr only
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("mindm-direct")

class SimpleMMInterface:
    """Simple interface for MindManager operations."""
    
    def __init__(self):
        """Initialize the MindManager interface."""
        self.document = None
        self.initialized = False
    
    def initialize(self):
        """Initialize connection to MindManager."""
        try:
            # Direct connection to MindManager
            self.document = MindmapDocument(charttype="auto", turbo_mode=False)
            self.initialized = True
            print("Successfully connected to MindManager.", file=sys.stderr)
            return True
        except Exception as e:
            print(f"Error connecting to MindManager: {e}", file=sys.stderr)
            return False
    
    def get_mindmap(self):
        """Get the current mindmap from MindManager."""
        if not self.initialized:
            if not self.initialize():
                return {"success": False, "error": "Failed to initialize MindManager connection"}
        
        try:
            success = self.document.get_mindmap()
            if not success:
                return {"success": False, "error": "No mindmap document is open in MindManager"}
            
            mindmap_data = self.mindmap_to_dict(self.document.mindmap)
            
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
                }
            }
        except Exception as e:
            print(f"Error getting mindmap: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
    
    def create_mindmap(self, central_topic, topics=None, relationships=None):
        """Create a new mindmap."""
        if not self.initialized:
            if not self.initialize():
                return {"success": False, "error": "Failed to initialize MindManager connection"}
        
        try:
            topics = topics or []
            relationships = relationships or []
            
            # Create mindmap with central topic
            self.document.create_mindmap(central_topic)
            
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
            
            return {"success": True, "message": "Mindmap created successfully"}
        except Exception as e:
            print(f"Error creating mindmap: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
    
    def add_topic(self, text, parent_guid=None, notes=None):
        """Add a topic to the mindmap."""
        if not self.initialized:
            if not self.initialize():
                return {"success": False, "error": "Failed to initialize MindManager connection"}
        
        try:
            # Ensure we have the current mindmap
            if not self.document.mindmap:
                if not self.document.get_mindmap():
                    return {"success": False, "error": "No mindmap document is open in MindManager"}
            
            # Find the parent topic
            if not parent_guid:
                parent_topic = self.document.mindm.get_central_topic()
            else:
                parent_topic = self.document.mindm.get_topic_by_id(parent_guid)
                
            if not parent_topic:
                return {"success": False, "error": "Parent topic not found"}
            
            # Add the topic
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
                    "text": text
                }
            }
        except Exception as e:
            print(f"Error adding topic: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
    
    def update_topic(self, guid, text=None, notes=None):
        """Update a topic in the mindmap."""
        if not self.initialized:
            if not self.initialize():
                return {"success": False, "error": "Failed to initialize MindManager connection"}
        
        try:
            if not guid:
                return {"success": False, "error": "Topic GUID is required"}
                
            # Find the topic
            topic = self.document.mindm.get_topic_by_id(guid)
            if not topic:
                return {"success": False, "error": f"Topic not found with GUID: {guid}"}
            
            # Update text if provided
            if text is not None:
                self.document.mindm.set_text_to_topic(topic, text)
            
            # Update notes if provided
            if notes is not None:
                if self.document.mindm.platform == "win":
                    topic.Notes.Text = notes if notes else ""
                elif self.document.mindm.platform == "darwin":
                    topic.notes.set(notes if notes else "")
            
            return {"success": True, "message": "Topic updated successfully"}
        except Exception as e:
            print(f"Error updating topic: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
    
    def add_relationship(self, guid_1, guid_2, label=""):
        """Add a relationship between topics."""
        if not self.initialized:
            if not self.initialize():
                return {"success": False, "error": "Failed to initialize MindManager connection"}
        
        try:
            if not guid_1 or not guid_2:
                return {"success": False, "error": "Both guid_1 and guid_2 are required"}
            
            # Add the relationship
            self.document.mindm.add_relationship(guid_1, guid_2, label)
            
            return {"success": True, "message": "Relationship added successfully"}
        except Exception as e:
            print(f"Error adding relationship: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
    
    def add_tag(self, topic_guid, tag_text):
        """Add a tag to a topic."""
        if not self.initialized:
            if not self.initialize():
                return {"success": False, "error": "Failed to initialize MindManager connection"}
        
        try:
            if not topic_guid or not tag_text:
                return {"success": False, "error": "Both topic_guid and tag_text are required"}
            
            # Add the tag
            self.document.mindm.add_tag_to_topic(topic=None, tag_text=tag_text, topic_guid=topic_guid)
            
            return {"success": True, "message": "Tag added successfully"}
        except Exception as e:
            print(f"Error adding tag: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
    
    def get_capabilities(self):
        """Get the capabilities of the MindManager integration."""
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
    
    def handle_request(self, request):
        """Handle an MCP request."""
        try:
            action = request.get("action", "")
            params = request.get("params", {})
            
            # Special handling for capabilities request
            if action == "get_capabilities":
                return {"success": True, "data": self.get_capabilities()}
            
            # Dispatch to appropriate handler
            if action == "get_mindmap":
                return self.get_mindmap()
            elif action == "create_mindmap":
                central_topic = params.get("central_topic", "Central Topic")
                topics = params.get("topics", [])
                relationships = params.get("relationships", [])
                return self.create_mindmap(central_topic, topics, relationships)
            elif action == "add_topic":
                text = params.get("text", "")
                parent_guid = params.get("parent_guid")
                notes = params.get("notes")
                return self.add_topic(text, parent_guid, notes)
            elif action == "update_topic":
                guid = params.get("guid", "")
                text = params.get("text")
                notes = params.get("notes")
                return self.update_topic(guid, text, notes)
            elif action == "add_relationship":
                guid_1 = params.get("guid_1", "")
                guid_2 = params.get("guid_2", "")
                label = params.get("label", "")
                return self.add_relationship(guid_1, guid_2, label)
            elif action == "add_tag":
                topic_guid = params.get("topic_guid", "")
                tag_text = params.get("tag_text", "")
                return self.add_tag(topic_guid, tag_text)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            print(f"Error handling request: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
    
    def mindmap_to_dict(self, topic, recursive=True, visited=None):
        """Convert a MindmapTopic to a dictionary representation."""
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
                self.mindmap_to_dict(subtopic, recursive, visited.copy())
                for subtopic in topic.subtopics
            ]
        
        return result

class DirectMCPServer:
    """Simplified MCP Server for Claude Desktop integration."""
    
    def __init__(self, interface, host="localhost", port=8090):
        """Initialize the server."""
        self.interface = interface
        self.host = host
        self.port = port
        self.server = None
        self.shutdown_event = asyncio.Event()
        self.clients = set()
    
    async def start(self):
        """Start the MCP server."""
        print(f"Starting MindManager MCP server on {self.host}:{self.port}", file=sys.stderr)
        
        # Initialize the direct connection to MindManager
        if not self.interface.initialize():
            print("Failed to initialize MindManager interface.", file=sys.stderr)
            return False
        
        # Create the server
        try:
            server = await asyncio.start_server(
                self._handle_connection,
                self.host,
                self.port,
            )
            
            self.server = server
            print(f"MindManager MCP server running on {self.host}:{self.port}", file=sys.stderr)
            
            # Serve until shut down
            try:
                await self.shutdown_event.wait()
            finally:
                print("Shutting down MindManager MCP server", file=sys.stderr)
                server.close()
                await server.wait_closed()
                
            return True
            
        except Exception as e:
            print(f"Failed to start MindManager MCP server: {str(e)}", file=sys.stderr)
            return False
    
    async def stop(self):
        """Stop the MCP server."""
        print("Stopping MindManager MCP server", file=sys.stderr)
        
        # Close all client connections
        for writer in self.clients:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                print(f"Error closing client connection: {str(e)}", file=sys.stderr)
        
        self.shutdown_event.set()
    
    async def _handle_connection(self, reader, writer):
        """Handle a client connection."""
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
                    
                    # Process the request directly with the interface
                    response = self.interface.handle_request(request)
                    
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
    
    async def _send_error_response(self, writer, error_message):
        """Send an error response to the client."""
        try:
            error_response = json.dumps({"success": False, "error": error_message})
            error_bytes = error_response.encode("utf-8")
            writer.write(len(error_bytes).to_bytes(4, byteorder="little", signed=False))
            writer.write(error_bytes)
            await writer.drain()
        except Exception as e:
            print(f"Error sending error response: {str(e)}", file=sys.stderr)

def find_free_port(host="localhost", start_port=8090):
    """Find a free port to use."""
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
    
    # Create the MindManager interface
    interface = SimpleMMInterface()
    
    # Create and start the server
    server = DirectMCPServer(interface, host=args.host, port=port)
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(server.stop()))
    
    # Run the server
    try:
        print(f"Starting Direct MindManager MCP Integration on {args.host}:{port}", file=sys.stderr)
        print("Press Ctrl+C to stop the server", file=sys.stderr)
        
        success = await server.start()
        
        if not success:
            print("Failed to start MCP server due to initialization errors.", file=sys.stderr)
            # Keep the process alive for a few seconds so Claude Desktop can read the error
            await asyncio.sleep(10)
            return 1
    
    except Exception as e:
        print(f"Error running MCP server: {e}", file=sys.stderr)
        await asyncio.sleep(10)
        return 1
    
    return 0

def run_direct():
    """Entry point for the console script."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        print("Integration stopped by user", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Error running integration: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(run_direct())