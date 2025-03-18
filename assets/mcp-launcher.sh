#!/bin/bash
# MCP Launcher for Claude Desktop
# This script launches the MCP server and ensures it stays running

conda activate mindm-mcp

echo "Starting MindManager MCP Server..."

# Activate your Python environment if needed
# source /path/to/your/env/bin/activate

# Launch the server in a way that prevents it from closing
python -m mindm_mcp.server

# If the script somehow exits, wait a moment before closing the window
echo "Server has exited."
sleep 10
