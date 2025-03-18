# mindm_mcp/__init__.py
"""
Model Context Protocol (MCP) server for MindManager.

This package provides a Model Context Protocol server for the mindm library,
enabling AI assistants like Claude to interact with MindManager.
"""

import os
import sys

__version__ = "0.1.0"

# Import main components for easier access
from mindm_mcp.server import app
from mindm_mcp.client import (
    MindManagerClient,
    MindManagerClientContext,
    SyncMindManagerClient,
    SyncMindManagerClientContext,
)
from mindm_mcp.mcp_plugin import MindManagerMCPPlugin, MCPServer

# Check if MindManager is installed
try:
    import mindm.mindmanager
except ImportError:
    print("Warning: mindm library not found. Please install it using: pip install mindm")
    
# Public API
__all__ = [
    "app",
    "MindManagerClient",
    "MindManagerClientContext",
    "SyncMindManagerClient",
    "SyncMindManagerClientContext",
    "MindManagerMCPPlugin",
    "MCPServer",
]
