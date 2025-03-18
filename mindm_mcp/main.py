# mindm_mcp/main.py
"""
Main entry point for the MindManager MCP Server.
"""

import asyncio
import os
import sys
import logging
import argparse
import uvicorn

from mindm_mcp.server import app, cleanup_inactive_sessions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mindm-mcp")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MindManager MCP Server")
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1", 
        help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    return parser.parse_args()

def start_server():
    """Start the FastAPI server."""
    args = parse_arguments()
    
    # Set up the cleanup task
    @app.on_event("startup")
    async def startup_event():
        asyncio.create_task(cleanup_inactive_sessions())
    
    # Start the server
    logger.info(f"Starting MindManager MCP Server on {args.host}:{args.port}")
    uvicorn.run(
        "mindm_mcp.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )

if __name__ == "__main__":
    start_server()
