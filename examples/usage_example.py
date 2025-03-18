#!/usr/bin/env python3
"""
Example usage of the MCP for mindm library.
Make sure MindManager is open with a document before running this script.
"""

import json
import subprocess
import sys
import os

def call_mcp(function_name, args=None):
    """
    Call the MCP handler with the given function name and arguments.
    
    Args:
        function_name (str): Name of the MCP function to call
        args (dict, optional): Arguments to pass to the function
        
    Returns:
        dict: The response from the MCP handler
    """
    if args is None:
        args = {}
        
    request = {
        "function": function_name,
        "args": args
    }
    
    # Convert request to JSON string
    request_json = json.dumps(request)
    
    # Call the MCP handler script
    server_path = os.path.join(os.path.dirname(__file__), "..", "mindm_mcp", "server.py")
    result = subprocess.run(
        [sys.executable, server_path, request_json],
        capture_output=True,
        text=True
    )
    
    # Parse and return the response
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": f"Failed to parse response: {result.stdout}",
            "stderr": result.stderr
        }

def main():
    """Example workflow using the MCP for mindm."""
    print("Getting mindmap from MindManager...")
    result = call_mcp("get_mindmap", {"mode": "full"})
    
    if result["status"] == "error":
        print(f"Error: {result['message']}")
        return
    
    print("\nCurrent mindmap information:")
    print(f"Central topic: {result['mindmap']['central_topic']}")
    print(f"Total topics: {result['mindmap']['topic_count']}")
    print(f"Maximum level: {result['mindmap']['max_level']}")
    
    if result['mindmap']['selected_topics']:
        print("\nSelected topics:")
        for topic in result['mindmap']['selected_topics']:
            print(f"- {topic}")
    
    # Ask user if they want to create a new mindmap
    answer = input("\nDo you want to create a new mindmap from this structure? (y/n): ")
    if answer.lower() == 'y':
        print("\nCreating new mindmap...")
        create_result = call_mcp("create_mindmap", {"verbose": True})
        
        if create_result["status"] == "error":
            print(f"Error: {create_result['message']}")
        else:
            print(f"Success: {create_result['message']}")
            print(f"Created {create_result['topics_created']} topics")
    
    print("\nDone.")

if __name__ == "__main__":
    main()
