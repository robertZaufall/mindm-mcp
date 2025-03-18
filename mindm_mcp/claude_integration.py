# mindm_mcp/claude_integration.py
"""
MindManager MCP Integration for Claude Desktop.

This script launches an MCP server that Claude Desktop can connect to for
interacting with MindManager through the mindm library.
"""

import os
import sys
import asyncio
import argparse
import logging
import signal
from typing import Dict, Any, Optional

from mindm_mcp.mcp_plugin import MindManagerMCPPlugin, MCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mindm-claude-integration")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MindManager MCP Integration for Claude Desktop")
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind the MCP server to (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8090,
        help="Port to bind the MCP server to (default: 8090)",
    )
    parser.add_argument(
        "--server-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="URL of the MindManager MCP server (default: http://127.0.0.1:8000)",
    )
    return parser.parse_args()

async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Create the plugin
    plugin = MindManagerMCPPlugin(base_url=args.server_url)
    
    # Create and start the server
    server = MCPServer(plugin, host=args.host, port=args.port)
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(server.stop()))
    
    # Run the server
    try:
        # Log to stderr to avoid interfering with MCP protocol
        print(f"Starting MindManager MCP Integration on {args.host}:{args.port}", file=sys.stderr)
        print(f"Using MindManager MCP server at {args.server_url}", file=sys.stderr)
        print("Press Ctrl+C to stop the server", file=sys.stderr)
        
        await server.start()
    
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        return 1
    
    return 0

def run_integration():
    """
    Entry point for the console script.
    This function is called when running mindm-claude-integration from the command line.
    """
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Integration stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error running integration: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_integration())