#!/usr/bin/env python3
import subprocess
import time
import sys
import signal
import asyncio
import os
import json

def start_services():
    """Start both the MCP server and Claude integration services."""
    # Don't print directly to stdout - Claude Desktop expects JSON
    print("Starting MindManager MCP combined services...", file=sys.stderr)
    
    # Start the MCP server as a subprocess using the Python module path
    # Use port 8001 instead of the default 8000
    server_process = subprocess.Popen(
        [sys.executable, "-m", "mindm_mcp.main", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give the server time to start up
    time.sleep(2)
    
    if server_process.poll() is not None:
        print("Error: MCP Server failed to start", file=sys.stderr)
        stderr_output = server_process.stderr.read().decode('utf-8')
        print(f"Server error: {stderr_output}", file=sys.stderr)
        return 1
    
    print("MCP Server started successfully on port 8001", file=sys.stderr)
    print("Starting Claude integration...", file=sys.stderr)
    
    try:
        # Run the Claude integration in the foreground using the Python module path
        # Connect to the MCP server on port 8001
        integration_process = subprocess.Popen(
            [sys.executable, "-m", "mindm_mcp.claude_integration", "--port", "8090", "--server-url", "http://127.0.0.1:8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for the integration process to finish
        integration_process.wait()
    
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
    
    finally:
        # Clean up the server process when done
        print("Shutting down MCP Server...", file=sys.stderr)
        if server_process.poll() is None:  # If still running
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
    
    return 0

if __name__ == "__main__":
    sys.exit(start_services())