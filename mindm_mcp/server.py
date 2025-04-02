#!/usr/bin/env python3
"""
server.py - FastMCP implementation for the mindm library

This module implements a Model Context Protocol (MCP) server
for interacting with MindManager through the mindm library using FastMCP.
"""

import sys
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
import asyncio
import json
from mcp.server.fastmcp import FastMCP, Context

from mindmap.mindmap import MindmapDocument, MindmapTopic
from mindmap import serialization, helpers
import mindm
from mindm import mindmanager as mm

try:
    from importlib.metadata import version as _version
    __version__ = _version("mindm_mcp")
except ImportError:
    __version__ = "unknown"

# --- Globals ---
# Initialize the MCP server
mcp = FastMCP("mindm (MindManager)", version=__version__)

doc_lock = asyncio.Lock()

# --- Helper Functions ---

def _serialize_result(data: Any) -> Union[Dict, List, str, int, float, bool, None]:
    """Helper to serialize results, especially MindmapTopic structures."""
    if isinstance(data, (MindmapTopic, list)):
         # Use simple serialization for MCP results unless full detail is needed
        return serialization.serialize_object_simple(data)
    elif isinstance(data, tuple):
        # Tuples are often JSON serializable directly if elements are
        return list(data) # Convert to list for guaranteed JSON compatibility
    elif isinstance(data, (dict, str, int, float, bool, type(None))):
        return data
    else:
        # Attempt string conversion for unknown types
        print(f"Warning: Serializing unknown type {type(data)} as string.", file=sys.stderr)
        return str(data)

def _handle_mindmanager_error(func_name: str, e: Exception) -> Dict[str, str]:
    """Formats MindManager errors for MCP response."""
    error_message = f"Error during MindManager operation '{func_name}': {e}"
    print(f"ERROR: {error_message}", file=sys.stderr)
    # Check for specific known errors from mindm.mindmanager if possible
    if "No document found" in str(e):
        return {"error": "MindManager Error", "message": "No document found or MindManager not running."}
    # Add more specific error checks here based on mindm library
    return {"error": "MindManager Error", "message": f"An error occurred: {e}"}


# --- Internal functions ---

MACOS_ACCESS_METHOD = 'applescript' # appscript is not working with MCPs

def _get_document_instance(
        charttype: str = 'auto', 
        turbo_mode: bool = False, 
        inline_editing_mode: bool = False, 
        mermaid_mode: bool = True, 
        macos_access: str = MACOS_ACCESS_METHOD
    ) -> MindmapDocument:
    document = MindmapDocument(
        charttype=charttype, 
        turbo_mode=turbo_mode, 
        inline_editing_mode=inline_editing_mode, 
        mermaid_mode=mermaid_mode, 
        macos_access=macos_access
    )
    return document

def _get_selection(mode='content', turbo_mode=False):
    document = _get_document_instance(turbo_mode=turbo_mode)
    if document.get_mindmap(mode=mode):
        selection = document.get_selection()
        return selection
    return None

def _get_grounding_information(mode='text', turbo_mode=False):
    document = _get_document_instance(turbo_mode=True)
    if document.get_mindmap(mode=mode):
        document.get_selection()
        return document.get_grounding_information()
    return None

def _get_mindmap_content(mode='content', turbo_mode=False):
    document = _get_document_instance(turbo_mode=turbo_mode)
    if document.get_mindmap(mode=mode):
        return document.mindmap
    return None

def _serialize_mermaid(id_only=True, mode='content', turbo_mode=False):
    document = _get_document_instance(turbo_mode=turbo_mode)
    if document.get_mindmap(mode=mode):
        guid_mapping = {}
        serialization.build_mapping(document.mindmap, guid_mapping)
        mermaid = serialization.serialize_mindmap(document.mindmap, guid_mapping, id_only=id_only)
        return mermaid
    return None

def _serialize_markdown(include_notes=True, mode='content', turbo_mode=False):
    document = _get_document_instance(turbo_mode=True)
    if document.get_mindmap(mode=mode):
        markdown = serialization.serialize_mindmap_markdown(document.mindmap, include_notes=include_notes)
        return markdown
    return None

def _serialize_json(ignore_rtf=True, mode='content', turbo_mode=False):
    document = _get_document_instance(turbo_mode=turbo_mode)
    if document.get_mindmap(mode=mode):
        json_obj = serialization.serialize_object_simple(document.mindmap, ignore_rtf=ignore_rtf)
        return json_obj
    return None

def _get_library_folder():
    mindmanager_obj = mm.Mindmanager()
    library_folder = mindmanager_obj.get_library_folder()
    return library_folder


# --- MCP Tools ---

# == MindmapDocument Methods ==

@mcp.tool()
async def get_mindmap(
    mode: str = 'full',
    turbo_mode: bool = False
) -> Dict[str, Any]:
    """
    Retrieves the current mind map structure from MindManager.

    Args:
        mode (str): Detail level ('full', 'content', 'text'). Defaults to 'full'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.

    Returns:
        Dict[str, Any]: Serialized mind map structure or error dictionary.
    """
    try:
        print(f"Calling get_mindmap(mode={mode}, turbo_mode={turbo_mode})", file=sys.stderr)
        mindmap = _get_mindmap_content(mode=mode, turbo_mode=turbo_mode)
        print("get_mindmap successful, returning serialized mindmap.", file=sys.stderr)
        return _serialize_result(mindmap)
    except Exception as e:
        return _handle_mindmanager_error("get_mindmap", e)


@mcp.tool()
async def get_selection(
    mode: str = 'full',
    turbo_mode: bool = False
) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Retrieves the currently selected topics in MindManager.

    Args:
        mode (str): Detail level ('full', 'content', 'text'). Defaults to 'full'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: List of serialized selected topics or error dictionary.
    """
    try:
        print(f"Calling get_selection(mode={mode}, turbo_mode={turbo_mode})", file=sys.stderr)
        selection = _get_selection(mode=mode, turbo_mode=turbo_mode)
        print("get_selection successful, returning serialized selection.", file=sys.stderr)
        return _serialize_result(selection)
    except Exception as e:
        return _handle_mindmanager_error("get_selection", e)


@mcp.tool()
async def get_library_folder(
) -> Union[str, Dict[str, str]]:
    """
    Gets the path to the MindManager library folder.

    Returns:
        Union[str, Dict[str, str]]: The library folder path or error dictionary.
    """
    try:
        folder_path = _get_library_folder()
        print(f"get_library_folder() returned: {folder_path}", file=sys.stderr)
        return folder_path
    except Exception as e:
        return _handle_mindmanager_error("get_library_folder", e)


@mcp.tool()
async def get_mindmanager_version(
) -> Union[str, Dict[str, str]]:
    """
    Gets the version of the MindManager application.

    Returns:
        Union[str, Dict[str, str]]: The version of the MindManager application or error dictionary.
    """
    try:
        version = mm.Mindmanager().get_version()
        print(f"get_mindmanager_version() returned: {version}", file=sys.stderr)
        return version
    except Exception as e:
        return _handle_mindmanager_error("get_mindmanager_version", e)


@mcp.tool()
async def get_grounding_information(
    mode: str = 'full',
    turbo_mode: bool = False
) -> Union[List[str], Dict[str, str]]:
    """
    Extracts grounding information (central topic, selected subtopics) from the mindmap.

    Args:
        mode (str): Detail level ('full', 'content', 'text'). Defaults to 'full'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.

    Returns:
        Union[List[str], Dict[str, str]]: A list containing [top_most_topic, subtopics_string] or error dictionary.
    """
    try:
        print("Calling get_grounding_information()", file=sys.stderr)
        top_most, subtopics_str = _get_grounding_information(mode=mode, turbo_mode=turbo_mode)
        print(f"get_grounding_information() returned: top='{top_most}', subtopics='{subtopics_str}'", file=sys.stderr)
        return [top_most, subtopics_str] # Return as list for JSON
    except Exception as e:
        # This function doesn't directly call MindManager, so errors are less likely external
        print(f"ERROR in get_grounding_information: {e}", file=sys.stderr)
        return {"error": "Internal Error", "message": f"Failed to get grounding information: {e}"}


# == Serialization Methods (Operating on current in-memory mindmap) ==

@mcp.tool()
async def serialize_current_mindmap_to_mermaid(
    id_only: bool = False,
    mode: str = 'full',
    turbo_mode: bool = False
) -> Union[str, Dict[str, str]]:
    """
    Serializes the currently loaded mindmap to Mermaid format.

    Args:
        id_only (bool): If True, only include IDs without detailed attributes. Defaults to False.
        mode (str): Detail level ('full', 'content', 'text'). Defaults to 'full'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.

    Returns:
        Union[str, Dict[str, str]]: Mermaid formatted string or error dictionary.
    """
    try:
        print(f"Serializing current mindmap to Mermaid (id_only={id_only}).", file=sys.stderr)
        text = _serialize_mermaid(id_only=id_only, mode=mode, turbo_mode=turbo_mode)
        print("Serialization to Mermaid successful.", file=sys.stderr)
        return text
    except Exception as e:
        print(f"ERROR during serialization to Mermaid: {e}", file=sys.stderr)
        return {"error": "Serialization Error", "message": f"Failed to serialize to Mermaid: {e}"}


@mcp.tool()
async def serialize_current_mindmap_to_markdown(
    include_notes: bool = True,
    mode: str = 'content',
    turbo_mode: bool = False
) -> Union[str, Dict[str, str]]:
    """
    Serializes the currently loaded mindmap to Markdown format.

    Args:
        include_notes (bool): If True, include notes in the serialization. Defaults to True.
        mode (str): Detail level ('full', 'content', 'text'). Defaults to 'full'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.

    Returns:
        Union[str, Dict[str, str]]: Markdown formatted string or error dictionary.
    """
    try:
        print(f"Serializing current mindmap to Markdown.", file=sys.stderr)
        text = _serialize_markdown(include_notes=include_notes, mode=mode, turbo_mode=turbo_mode)
        print("Serialization to Markdown successful.", file=sys.stderr)
        return text
    except Exception as e:
        print(f"ERROR during serialization to Markdown: {e}", file=sys.stderr)
        return {"error": "Serialization Error", "message": f"Failed to serialize to Markdown: {e}"}


@mcp.tool()
async def serialize_current_mindmap_to_json(
    ignore_rtf: bool = True,
    mode: str = 'content',
    turbo_mode: bool = True
) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Serializes the currently loaded mindmap to a detailed JSON object with ID mapping.

    Args:
        ignore_rtf (bool): Whether to ignore RTF content. Defaults to True.
        mode (str): Detail level ('full', 'content', 'text'). Defaults to 'full'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.

    Returns:
        Union[Dict[str, Any], Dict[str, str]]: JSON serializable dictionary or error dictionary.
    """
    try:
        print(f"Serializing current mindmap to detailed JSON (ignore_rtf={ignore_rtf}).", file=sys.stderr)
        json_obj = _serialize_json(ignore_rtf=ignore_rtf, mode=mode, turbo_mode=turbo_mode)
        print("Serialization to detailed JSON successful.", file=sys.stderr)
        return json_obj
    except Exception as e:
        print(f"ERROR during serialization to JSON: {e}", file=sys.stderr)
        return {"error": "Serialization Error", "message": f"Failed to serialize to JSON: {e}"}


@mcp.tool()
async def get_versions() -> Dict[str, str]:
    """
    Get the versions of the MindManager Automation MCP Server components.

    Returns:
        Dict[str, str]: A dictionary containing the versions of the components.
    """
    result = {}
    result["mindm-mcp"] = __version__
    result["mindm"] = mindm.__version__
    return result


def main():
    print("Starting MindManager Automation MCP Server...", file=sys.stderr)
    try:
        mcp.run(transport='stdio')
    except Exception as main_e:
        print(f"FATAL: Server crashed: {main_e}", file=sys.stderr)
        sys.exit(1)
    finally:
        print("MindManager Automation MCP Server stopped.", file=sys.stderr)

# --- Main Execution ---
if __name__ == "__main__":
    main()
