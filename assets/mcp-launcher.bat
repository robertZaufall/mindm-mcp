@echo off
REM MCP Launcher for Claude Desktop
REM This script launches the MCP server and ensures it stays running

conda activate mindm-mcp

echo Starting MindManager MCP Server...

REM Activate your Python environment if needed
REM call C:\path\to\your\env\Scripts\activate.bat

REM Launch the server in a way that prevents it from closing
python -m mindm_mcp.server

REM If the script somehow exits, wait a moment before closing the window
echo Server has exited.
timeout /t 10
