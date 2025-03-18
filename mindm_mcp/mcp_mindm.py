#!/usr/bin/env python3
"""
Minimal MCP implementation for mindm library.
This script provides direct access to mindm functions from Claude Desktop.
"""

import sys
import json
import traceback
from typing import Dict, Any, Callable, Optional, List, Union

# Import the mindm library
import mindmap.mindmap as mm

class MCPHandler:
    """
    Model Context Protocol handler for mindm library.
    Provides a simple interface to call mindm functions from Claude Desktop.
    """
    
    def __init__(self):
        """Initialize the MCP handler."""
        self.document = None
        self.functions = {
            "get_mindmap": self.get_mindmap,
            "create_mindmap": self.create_mindmap,
            "list_functions": self.list_functions,
        }
    
    def list_functions(self, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """List all available functions."""
        return {
            "status": "success",
            "functions": list(self.functions.keys())
        }
    
    def get_mindmap(self, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load a mindmap from the currently open MindManager document.
        
        Args:
            args (Dict[str, Any], optional): Optional arguments.
                mode: 'full', 'content', or 'text' (default: 'full')
        
        Returns:
            Dict[str, Any]: Status and mindmap information.
        """
        try:
            # Create a document if we don't have one
            if self.document is None:
                self.document = mm.MindmapDocument()
            
            # Extract mode parameter if provided
            mode = 'full'
            if args and 'mode' in args:
                mode = args['mode']
            
            # Get the mindmap
            result = self.document.get_mindmap(mode=mode)
            
            if result:
                # Extract basic information (not the full object which could be huge)
                central_topic_text = self.document.mindmap.text
                topic_count = self._count_topics(self.document.mindmap)
                selected_count = len(self.document.selected_topic_texts)
                
                # Get grounding information
                top_most_topic, subtopics = self.document.get_grounding_information()
                
                return {
                    "status": "success",
                    "mindmap": {
                        "central_topic": central_topic_text,
                        "topic_count": topic_count,
                        "max_level": self.document.max_topic_level,
                        "selected_topics": self.document.selected_topic_texts,
                        "top_most_topic": top_most_topic,
                        "subtopics": subtopics
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to get mindmap. No document is open in MindManager."
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
    
    def create_mindmap(self, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new mindmap document based on the loaded mindmap structure.
        
        Args:
            args (Dict[str, Any], optional): Optional arguments.
                verbose: Whether to enable verbose output (default: False)
        
        Returns:
            Dict[str, Any]: Status and creation result.
        """
        try:
            # Check if we have a document and mindmap loaded
            if self.document is None or self.document.mindmap is None:
                return {
                    "status": "error",
                    "message": "No mindmap loaded. Call get_mindmap first."
                }
            
            # Extract verbose parameter if provided
            verbose = False
            if args and 'verbose' in args:
                verbose = args['verbose']
            
            # Create the mindmap
            self.document.create_mindmap(verbose=verbose)
            
            return {
                "status": "success",
                "message": "Mindmap created successfully",
                "topics_created": self._count_topics(self.document.mindmap)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
    
    def _count_topics(self, topic, count=0, visited=None):
        """
        Recursively count topics in a mindmap.
        
        Args:
            topic: The topic to start counting from
            count: Current count
            visited: Set of visited topics to prevent infinite recursion
            
        Returns:
            int: Total count of topics
        """
        if visited is None:
            visited = set()
            
        if topic.guid in visited:
            return count
            
        visited.add(topic.guid)
        count += 1
        
        for subtopic in topic.subtopics:
            count = self._count_topics(subtopic, count, visited)
            
        return count
    
    def handle_request(self, request_str: str) -> str:
        """
        Parse and handle MCP requests.
        
        Args:
            request_str (str): JSON string with function name and arguments
            
        Returns:
            str: JSON response string
        """
        try:
            request = json.loads(request_str)
            function_name = request.get("function", "")
            args = request.get("args", {})
            
            if function_name in self.functions:
                result = self.functions[function_name](args)
                return json.dumps(result)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown function: {function_name}",
                    "available_functions": list(self.functions.keys())
                })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error handling request: {str(e)}",
                "traceback": traceback.format_exc()
            })

def main():
    """Main entry point for the MCP handler."""
    handler = MCPHandler()
    
    # If arguments are provided, process as a single request
    if len(sys.argv) > 1:
        request = sys.argv[1]
        response = handler.handle_request(request)
        print(response)
        return
    
    # Otherwise, enter interactive mode
    print("MCP for mindm started. Enter requests as JSON or 'exit' to quit.")
    while True:
        try:
            line = input("> ")
            if line.lower() in ["exit", "quit"]:
                break
                
            response = handler.handle_request(line)
            print(response)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
