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

try:
    from importlib.metadata import version as _version
    __version__ = _version("mindm_mcp")
except ImportError:
    __version__ = "unknown"

# --- Globals ---
# Initialize the MCP server
mcp = FastMCP("mindm (MindManager)", version=__version__)

MACOS_ACCESS_METHOD = 'applescript' # appscript is not working with MCPs

# Global instance of MindmapDocument to interact with MindManager
# We initialize it lazily to allow configuration if needed later
mindmap_doc_instance: Optional[MindmapDocument] = None
doc_lock = asyncio.Lock()

# --- Helper Functions ---

async def _get_doc_instance(
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> MindmapDocument:
    """Lazily initializes and returns the MindmapDocument instance."""
    global mindmap_doc_instance
    async with doc_lock:
        if mindmap_doc_instance is None:
            print(f"Initializing MindmapDocument (charttype={charttype}, turbo={turbo_mode}, macos={macos_access})", file=sys.stderr)
            # Add error handling for MindManager initialization if necessary
            try:
                mindmap_doc_instance = MindmapDocument(
                    charttype=charttype,
                    turbo_mode=turbo_mode,
                    macos_access=macos_access
                )
                # Optional: Check if a document is open upon initialization?
                # if not mindmap_doc_instance.mindm.document_exists():
                #     print("Warning: MindManager document not detected during initialization.", file=sys.stderr)
            except Exception as e:
                print(f"ERROR: Failed to initialize MindmapDocument: {e}", file=sys.stderr)
                raise  # Re-raise to signal failure
        # Update modes if needed? For now, we re-initialize if settings change,
        # but a better approach might be methods on MindmapDocument to change settings.
        elif (mindmap_doc_instance.charttype != charttype or
              mindmap_doc_instance.turbo_mode != turbo_mode or
              mindmap_doc_instance.macos_access != macos_access):
              print(f"Re-initializing MindmapDocument due to changed settings (charttype={charttype}, turbo={turbo_mode}, macos={macos_access})", file=sys.stderr)
              try:
                  mindmap_doc_instance = MindmapDocument(
                        charttype=charttype,
                        turbo_mode=turbo_mode,
                        macos_access=macos_access
                    )
              except Exception as e:
                print(f"ERROR: Failed to re-initialize MindmapDocument: {e}", file=sys.stderr)
                raise # Re-raise to signal failure

    return mindmap_doc_instance

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

# --- MCP Tools ---

# == MindmapDocument Methods ==

@mcp.tool()
async def get_mindmap(
    mode: str = 'full',
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> Dict[str, Any]:
    """
    Retrieves the current mind map structure from MindManager.

    Args:
        mode (str): Detail level ('full', 'content', 'text'). Defaults to 'full'.
        charttype (str): Chart type ('orgchart', 'radial', 'auto'). Defaults to 'auto'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.
        macos_access (str): Access method on macOS ('appscript', 'applescript'). Defaults to 'appscript'.

    Returns:
        Dict[str, Any]: Serialized mind map structure or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        print(f"Calling doc.get_mindmap(mode={mode})", file=sys.stderr)
        success = await asyncio.to_thread(doc.get_mindmap, mode=mode) # Run sync MindManager code in thread
        if success and doc.mindmap:
            print("get_mindmap successful, returning serialized mindmap.", file=sys.stderr)
            return _serialize_result(doc.mindmap)
        elif not success:
             print("ERROR: doc.get_mindmap returned False.", file=sys.stderr)
             return {"error": "MindManager Error", "message": "Failed to retrieve mindmap. Is a document open?"}
        else:
             print("ERROR: doc.get_mindmap succeeded but doc.mindmap is empty.", file=sys.stderr)
             return {"error": "MindManager Error", "message": "Mindmap data is empty after retrieval."}
    except Exception as e:
        return _handle_mindmanager_error("get_mindmap", e)

@mcp.tool()
async def get_selection(
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Retrieves the currently selected topics in MindManager.

    Args:
        charttype (str): Chart type ('orgchart', 'radial', 'auto'). Defaults to 'auto'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.
        macos_access (str): Access method on macOS ('appscript', 'applescript'). Defaults to 'appscript'.

    Returns:
        Union[List[Dict[str, Any]], Dict[str, str]]: List of serialized selected topics or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        print("Calling doc.get_selection()", file=sys.stderr)
        selection = await asyncio.to_thread(doc.get_selection) # Run sync MindManager code in thread
        print("get_selection successful, returning serialized selection.", file=sys.stderr)
        return _serialize_result(selection)
    except Exception as e:
        return _handle_mindmanager_error("get_selection", e)

@mcp.tool()
async def create_mindmap_from_mermaid_full(
    mermaid_text: str,
    guid_mapping_json: str, # Pass mapping as JSON string
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD,
    finalize: bool = True
) -> Dict[str, Any]:
    """
    Creates a new MindManager mindmap from full Mermaid text with metadata.

    Args:
        mermaid_text (str): Mermaid string with JSON metadata comments.
        guid_mapping_json (str): JSON string representing the ID to GUID mapping.
        charttype (str): Chart type ('orgchart', 'radial', 'auto'). Defaults to 'auto'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.
        macos_access (str): Access method on macOS ('appscript', 'applescript'). Defaults to 'appscript'.
        finalize (bool): Whether to finalize the map layout after creation. Defaults to True.


    Returns:
        Dict[str, Any]: Success message or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        guid_mapping_dict = {}
        try:
            guid_mapping_dict = json.loads(guid_mapping_json)
            print(f"Parsed guid_mapping_json (length: {len(guid_mapping_dict)})", file=sys.stderr)
            # Ensure keys are strings and values are ints if needed by deserializer,
            # but build_mapping uses guid->int, deserialize needs int->guid
            # guid_mapping_dict = {k: int(v) for k, v in guid_mapping_dict.items()} # Keep mapping as is for deserializer
        except json.JSONDecodeError as json_e:
            print(f"ERROR: Invalid JSON provided for guid_mapping_json: {json_e}", file=sys.stderr)
            return {"error": "Input Error", "message": f"Invalid JSON provided for guid_mapping_json: {json_e}"}
        except ValueError as val_e:
            print(f"ERROR: Invalid value in guid_mapping_json (expected int for ID): {val_e}", file=sys.stderr)
            return {"error": "Input Error", "message": f"Invalid value in guid_mapping_json (expected int for ID): {val_e}"}


        # Deserialize mermaid text to internal MindmapTopic structure
        print("Deserializing Mermaid full text...", file=sys.stderr)
        root_topic = serialization.deserialize_mermaid_full(mermaid_text, guid_mapping_dict) # uses guid->id mapping internally now

        if not root_topic:
            print("ERROR: Failed to deserialize Mermaid text.", file=sys.stderr)
            return {"error": "Deserialization Error", "message": "Failed to deserialize Mermaid text."}

        # Set the deserialized structure as the one to be created
        doc.mindmap = root_topic
        print("Deserialization successful, mindmap structure set.", file=sys.stderr)

        # Create the mindmap in MindManager
        print("Calling doc.create_mindmap()", file=sys.stderr)
        await asyncio.to_thread(doc.create_mindmap) # Run sync MindManager code in thread
        print("doc.create_mindmap() completed.", file=sys.stderr)

        if finalize:
             print("Calling doc.finalize()", file=sys.stderr)
             await asyncio.to_thread(doc.finalize) # Run sync MindManager code in thread
             print("doc.finalize() completed.", file=sys.stderr)

        print("create_mindmap_from_mermaid_full successful.", file=sys.stderr)
        return {"status": "success", "message": "Mindmap created successfully."}
    except Exception as e:
        return _handle_mindmanager_error("create_mindmap_from_mermaid_full", e)

@mcp.tool()
async def create_mindmap_from_mermaid_id(
    mermaid_text: str,
    guid_mapping_json: str, # Pass mapping as JSON string
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD,
    finalize: bool = True
) -> Dict[str, Any]:
    """
    Creates a new MindManager mindmap from Mermaid text with only IDs.

    Args:
        mermaid_text (str): Mermaid string with 'id<number>[Text]' format nodes.
        guid_mapping_json (str): JSON string representing the ID to GUID mapping.
        charttype (str): Chart type ('orgchart', 'radial', 'auto'). Defaults to 'auto'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.
        macos_access (str): Access method on macOS ('appscript', 'applescript'). Defaults to 'appscript'.
        finalize (bool): Whether to finalize the map layout after creation. Defaults to True.

    Returns:
        Dict[str, Any]: Success message or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        guid_mapping_dict = {}
        try:
            guid_mapping_dict = json.loads(guid_mapping_json)
            print(f"Parsed guid_mapping_json (length: {len(guid_mapping_dict)})", file=sys.stderr)
            # guid_mapping_dict = {k: int(v) for k, v in guid_mapping_dict.items()} # Keep mapping as is
        except json.JSONDecodeError as json_e:
            print(f"ERROR: Invalid JSON provided for guid_mapping_json: {json_e}", file=sys.stderr)
            return {"error": "Input Error", "message": f"Invalid JSON provided for guid_mapping_json: {json_e}"}
        except ValueError as val_e:
            print(f"ERROR: Invalid value in guid_mapping_json (expected int for ID): {val_e}", file=sys.stderr)
            return {"error": "Input Error", "message": f"Invalid value in guid_mapping_json (expected int for ID): {val_e}"}

        # Deserialize mermaid text to internal MindmapTopic structure
        print("Deserializing Mermaid ID text...", file=sys.stderr)
        root_topic = serialization.deserialize_mermaid_with_id(mermaid_text, guid_mapping_dict)

        if not root_topic:
            print("ERROR: Failed to deserialize Mermaid ID text.", file=sys.stderr)
            return {"error": "Deserialization Error", "message": "Failed to deserialize Mermaid text."}

        # Set the deserialized structure as the one to be created
        doc.mindmap = root_topic
        print("Deserialization successful, mindmap structure set.", file=sys.stderr)

        # Create the mindmap in MindManager
        print("Calling doc.create_mindmap()", file=sys.stderr)
        await asyncio.to_thread(doc.create_mindmap) # Run sync MindManager code in thread
        print("doc.create_mindmap() completed.", file=sys.stderr)

        if finalize:
            print("Calling doc.finalize()", file=sys.stderr)
            await asyncio.to_thread(doc.finalize) # Run sync MindManager code in thread
            print("doc.finalize() completed.", file=sys.stderr)

        print("create_mindmap_from_mermaid_id successful.", file=sys.stderr)
        return {"status": "success", "message": "Mindmap created successfully from ID-only Mermaid."}
    except Exception as e:
        return _handle_mindmanager_error("create_mindmap_from_mermaid_id", e)

@mcp.tool()
async def finalize_document(
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> Dict[str, Any]:
    """
    Finalizes the layout of the current MindManager document.

    Args:
        charttype (str): Chart type ('orgchart', 'radial', 'auto'). Defaults to 'auto'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.
        macos_access (str): Access method on macOS ('appscript', 'applescript'). Defaults to 'appscript'.

    Returns:
        Dict[str, Any]: Success message or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        if not doc.mindmap:
             print("finalize_document: mindmap not loaded, calling get_mindmap first.", file=sys.stderr)
             await get_mindmap(charttype=charttype, turbo_mode=turbo_mode, macos_access=macos_access) # Ensure mindmap data is loaded
        if not doc.mindmap:
            print("ERROR: finalize_document: Mindmap data not loaded even after get_mindmap.", file=sys.stderr)
            return {"error": "State Error", "message": "Mindmap data not loaded. Cannot finalize."}

        print("Calling doc.finalize()", file=sys.stderr)
        await asyncio.to_thread(doc.finalize) # Run sync MindManager code in thread
        print("doc.finalize() completed.", file=sys.stderr)
        return {"status": "success", "message": "Document finalized."}
    except Exception as e:
        return _handle_mindmanager_error("finalize_document", e)

@mcp.tool()
async def set_background_image(
    image_path: str,
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> Dict[str, Any]:
    """
    Sets the background image for the current MindManager document.

    Args:
        image_path (str): The absolute file path to the background image.
        charttype (str): Chart type ('orgchart', 'radial', 'auto'). Defaults to 'auto'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.
        macos_access (str): Access method on macOS ('appscript', 'applescript'). Defaults to 'appscript'.

    Returns:
        Dict[str, Any]: Success message or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        print(f"Calling doc.set_background_image({image_path})", file=sys.stderr)
        await asyncio.to_thread(doc.set_background_image, image_path) # Run sync MindManager code in thread
        print("doc.set_background_image() completed.", file=sys.stderr)
        return {"status": "success", "message": "Background image set."}
    except FileNotFoundError as fnf_e:
        print(f"ERROR: Background image file not found: {image_path} - {fnf_e}", file=sys.stderr)
        return {"error": "File Not Found", "message": f"Background image file not found: {image_path}"}
    except Exception as e:
        return _handle_mindmanager_error("set_background_image", e)

@mcp.tool()
async def get_library_folder(
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> Union[str, Dict[str, str]]:
    """
    Gets the path to the MindManager library folder.

    Args:
        charttype (str): Chart type ('orgchart', 'radial', 'auto'). Defaults to 'auto'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.
        macos_access (str): Access method on macOS ('appscript', 'applescript'). Defaults to 'appscript'.

    Returns:
        Union[str, Dict[str, str]]: The library folder path or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        print("Calling doc.get_library_folder()", file=sys.stderr)
        folder_path = await asyncio.to_thread(doc.get_library_folder) # Run sync MindManager code in thread
        print(f"doc.get_library_folder() returned: {folder_path}", file=sys.stderr)
        return folder_path
    except Exception as e:
        return _handle_mindmanager_error("get_library_folder", e)

@mcp.tool()
async def get_grounding_information(
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> Union[List[str], Dict[str, str]]:
    """
    Extracts grounding information (central topic, selected subtopics) from the mindmap.
    Requires the mindmap and selection to be loaded first via get_mindmap and get_selection.

    Args:
        charttype (str): Chart type ('orgchart', 'radial', 'auto'). Defaults to 'auto'.
        turbo_mode (bool): Enable turbo mode (text only). Defaults to False.
        macos_access (str): Access method on macOS ('appscript', 'applescript'). Defaults to 'appscript'.

    Returns:
        Union[List[str], Dict[str, str]]: A list containing [top_most_topic, subtopics_string] or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        # Ensure mindmap and selection data are potentially loaded
        if not doc.mindmap:
             print("get_grounding_information: mindmap not loaded, calling get_mindmap first.", file=sys.stderr)
             await get_mindmap(charttype=charttype, turbo_mode=turbo_mode, macos_access=macos_access)
        # Check if selection was potentially populated by get_selection
        # doc.selected_topic_texts might be None or empty list even after calling get_selection if nothing is selected
        if not hasattr(doc, 'selected_topic_texts') or doc.selected_topic_texts is None:
            print("get_grounding_information: selection not loaded, calling get_selection first.", file=sys.stderr)
            await get_selection(charttype=charttype, turbo_mode=turbo_mode, macos_access=macos_access)

        if not doc.mindmap:
             print("ERROR: get_grounding_information: Mindmap data not loaded.", file=sys.stderr)
             return {"error": "State Error", "message": "Mindmap data not loaded."}

        # doc.get_grounding_information uses internal state, no need for await asyncio.to_thread
        print("Calling doc.get_grounding_information()", file=sys.stderr)
        top_most, subtopics_str = doc.get_grounding_information()
        print(f"doc.get_grounding_information() returned: top='{top_most}', subtopics='{subtopics_str}'", file=sys.stderr)
        return [top_most, subtopics_str] # Return as list for JSON
    except Exception as e:
        # This function doesn't directly call MindManager, so errors are less likely external
        print(f"ERROR in get_grounding_information: {e}", file=sys.stderr)
        return {"error": "Internal Error", "message": f"Failed to get grounding information: {e}"}

# == Serialization Methods (Operating on current in-memory mindmap) ==

@mcp.tool()
async def serialize_current_mindmap_to_mermaid(
    id_only: bool = False,
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> Union[str, Dict[str, str]]:
    """
    Serializes the currently loaded mindmap to Mermaid format.
    Requires the mindmap to be loaded first via get_mindmap.

    Args:
        id_only (bool): If True, only include IDs without detailed attributes. Defaults to False.
        charttype (str): Chart type used for loading map if not already loaded.
        turbo_mode (bool): Turbo mode used for loading map if not already loaded.
        macos_access (str): Access method used for loading map if not already loaded.

    Returns:
        Union[str, Dict[str, str]]: Mermaid formatted string or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        if not doc.mindmap:
            print("serialize_current_mindmap_to_mermaid: mindmap not loaded, calling get_mindmap first.", file=sys.stderr)
            await get_mindmap(charttype=charttype, turbo_mode=turbo_mode, macos_access=macos_access) # Ensure mindmap data is loaded
        if not doc.mindmap:
            print("ERROR: serialize_current_mindmap_to_mermaid: Mindmap data not loaded. Cannot serialize.", file=sys.stderr)
            return {"error": "State Error", "message": "Mindmap data not loaded. Cannot serialize."}

        print(f"Serializing current mindmap to Mermaid (id_only={id_only}).", file=sys.stderr)
        guid_mapping = {}
        serialization.build_mapping(doc.mindmap, guid_mapping)
        mermaid_string = serialization.serialize_mindmap(doc.mindmap, guid_mapping, id_only=id_only)
        print("Serialization to Mermaid successful.", file=sys.stderr)
        return mermaid_string
    except Exception as e:
        print(f"ERROR during serialization to Mermaid: {e}", file=sys.stderr)
        return {"error": "Serialization Error", "message": f"Failed to serialize to Mermaid: {e}"}

@mcp.tool()
async def serialize_current_mindmap_to_markdown(
    include_notes: bool = True,
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> Union[str, Dict[str, str]]:
    """
    Serializes the currently loaded mindmap to Markdown format.
    Requires the mindmap to be loaded first via get_mindmap.

    Args:
        include_notes (bool): If True, include notes in the output. Defaults to True.
        charttype (str): Chart type used for loading map if not already loaded.
        turbo_mode (bool): Turbo mode used for loading map if not already loaded.
        macos_access (str): Access method used for loading map if not already loaded.

    Returns:
        Union[str, Dict[str, str]]: Markdown formatted string or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        if not doc.mindmap:
             print("serialize_current_mindmap_to_markdown: mindmap not loaded, calling get_mindmap first.", file=sys.stderr)
             await get_mindmap(charttype=charttype, turbo_mode=turbo_mode, macos_access=macos_access) # Ensure mindmap data is loaded
        if not doc.mindmap:
            print("ERROR: serialize_current_mindmap_to_markdown: Mindmap data not loaded. Cannot serialize.", file=sys.stderr)
            return {"error": "State Error", "message": "Mindmap data not loaded. Cannot serialize."}

        print(f"Serializing current mindmap to Markdown (include_notes={include_notes}).", file=sys.stderr)
        markdown_string = serialization.serialize_mindmap_markdown(doc.mindmap, include_notes=include_notes)
        print("Serialization to Markdown successful.", file=sys.stderr)
        return markdown_string
    except Exception as e:
        print(f"ERROR during serialization to Markdown: {e}", file=sys.stderr)
        return {"error": "Serialization Error", "message": f"Failed to serialize to Markdown: {e}"}


@mcp.tool()
async def serialize_current_mindmap_to_json(
    ignore_rtf: bool = True,
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Serializes the currently loaded mindmap to a detailed JSON object with ID mapping.
    Requires the mindmap to be loaded first via get_mindmap.

    Args:
        ignore_rtf (bool): Whether to ignore RTF content. Defaults to True.
        charttype (str): Chart type used for loading map if not already loaded.
        turbo_mode (bool): Turbo mode used for loading map if not already loaded.
        macos_access (str): Access method used for loading map if not already loaded.

    Returns:
        Union[Dict[str, Any], Dict[str, str]]: JSON serializable dictionary or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        if not doc.mindmap:
             print("serialize_current_mindmap_to_json: mindmap not loaded, calling get_mindmap first.", file=sys.stderr)
             await get_mindmap(charttype=charttype, turbo_mode=turbo_mode, macos_access=macos_access) # Ensure mindmap data is loaded
        if not doc.mindmap:
            print("ERROR: serialize_current_mindmap_to_json: Mindmap data not loaded. Cannot serialize.", file=sys.stderr)
            return {"error": "State Error", "message": "Mindmap data not loaded. Cannot serialize."}

        print(f"Serializing current mindmap to detailed JSON (ignore_rtf={ignore_rtf}).", file=sys.stderr)
        guid_mapping = {}
        serialization.build_mapping(doc.mindmap, guid_mapping)
        serialized_data = serialization.serialize_object(doc.mindmap, guid_mapping, ignore_rtf=ignore_rtf)
        print("Serialization to detailed JSON successful.", file=sys.stderr)
        return serialized_data
    except Exception as e:
        print(f"ERROR during serialization to JSON: {e}", file=sys.stderr)
        return {"error": "Serialization Error", "message": f"Failed to serialize to JSON: {e}"}

@mcp.tool()
async def serialize_current_mindmap_to_json_simple(
    ignore_rtf: bool = True,
    charttype: str = 'auto',
    turbo_mode: bool = False,
    macos_access: str = MACOS_ACCESS_METHOD
) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Serializes the currently loaded mindmap to a simple JSON object without ID mapping.
    Requires the mindmap to be loaded first via get_mindmap.

    Args:
        ignore_rtf (bool): Whether to ignore RTF content. Defaults to True.
        charttype (str): Chart type used for loading map if not already loaded.
        turbo_mode (bool): Turbo mode used for loading map if not already loaded.
        macos_access (str): Access method used for loading map if not already loaded.

    Returns:
        Union[Dict[str, Any], Dict[str, str]]: JSON serializable dictionary or error dictionary.
    """
    try:
        doc = await _get_doc_instance(charttype, turbo_mode, macos_access)
        if not doc.mindmap:
             print("serialize_current_mindmap_to_json_simple: mindmap not loaded, calling get_mindmap first.", file=sys.stderr)
             await get_mindmap(charttype=charttype, turbo_mode=turbo_mode, macos_access=macos_access) # Ensure mindmap data is loaded
        if not doc.mindmap:
            print("ERROR: serialize_current_mindmap_to_json_simple: Mindmap data not loaded. Cannot serialize.", file=sys.stderr)
            return {"error": "State Error", "message": "Mindmap data not loaded. Cannot serialize."}

        print(f"Serializing current mindmap to simple JSON (ignore_rtf={ignore_rtf}).", file=sys.stderr)
        serialized_data = serialization.serialize_object_simple(doc.mindmap, ignore_rtf=ignore_rtf)
        print("Serialization to simple JSON successful.", file=sys.stderr)
        return serialized_data
    except Exception as e:
        print(f"ERROR during serialization to simple JSON: {e}", file=sys.stderr)
        return {"error": "Serialization Error", "message": f"Failed to serialize to simple JSON: {e}"}

# == Deserialization Methods (Standalone - Do not interact with MindManager) ==

@mcp.tool()
async def deserialize_mermaid_id_to_mindmap_topic(
    mermaid_text: str,
    guid_mapping_json: str
) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Deserializes Mermaid text (ID format) into a MindmapTopic structure (JSON).
    Does NOT interact with MindManager.

    Args:
        mermaid_text (str): Mermaid string with 'id<number>[Text]' format nodes.
        guid_mapping_json (str): JSON string representing the ID to GUID mapping.

    Returns:
        Union[Dict[str, Any], Dict[str, str]]: Serialized MindmapTopic structure or error dictionary.
    """
    guid_mapping_dict = {}
    try:
        guid_mapping_dict = json.loads(guid_mapping_json)
        print(f"Parsed guid_mapping_json (length: {len(guid_mapping_dict)})", file=sys.stderr)
        # guid_mapping_dict = {k: int(v) for k, v in guid_mapping_dict.items()} # Keep mapping as is
    except json.JSONDecodeError as json_e:
        print(f"ERROR: Invalid JSON provided for guid_mapping_json: {json_e}", file=sys.stderr)
        return {"error": "Input Error", "message": f"Invalid JSON provided for guid_mapping_json: {json_e}"}
    except ValueError as val_e:
            print(f"ERROR: Invalid value in guid_mapping_json (expected int for ID): {val_e}", file=sys.stderr)
            return {"error": "Input Error", "message": f"Invalid value in guid_mapping_json (expected int for ID): {val_e}"}


    try:
        print("Deserializing Mermaid ID text (standalone)...", file=sys.stderr)
        root_topic = serialization.deserialize_mermaid_with_id(mermaid_text, guid_mapping_dict)
        if root_topic:
            print("Deserialization from Mermaid ID successful.", file=sys.stderr)
            return serialization.serialize_object_simple(root_topic) # Return as simple JSON
        else:
            print("ERROR: Failed to deserialize Mermaid ID text.", file=sys.stderr)
            return {"error": "Deserialization Error", "message": "Failed to deserialize Mermaid ID text."}
    except Exception as e:
        print(f"ERROR during deserialization from Mermaid ID: {e}", file=sys.stderr)
        return {"error": "Deserialization Error", "message": f"Failed to deserialize Mermaid ID text: {e}"}

@mcp.tool()
async def deserialize_mermaid_full_to_mindmap_topic(
    mermaid_text: str,
    guid_mapping_json: str
) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Deserializes Mermaid text (full format with metadata) into a MindmapTopic structure (JSON).
    Does NOT interact with MindManager.

    Args:
        mermaid_text (str): Mermaid string with JSON metadata comments.
        guid_mapping_json (str): JSON string representing the ID to GUID mapping.

    Returns:
        Union[Dict[str, Any], Dict[str, str]]: Serialized MindmapTopic structure or error dictionary.
    """
    guid_mapping_dict = {}
    try:
        guid_mapping_dict = json.loads(guid_mapping_json)
        print(f"Parsed guid_mapping_json (length: {len(guid_mapping_dict)})", file=sys.stderr)
        # guid_mapping_dict = {k: int(v) for k, v in guid_mapping_dict.items()} # Keep mapping as is
    except json.JSONDecodeError as json_e:
        print(f"ERROR: Invalid JSON provided for guid_mapping_json: {json_e}", file=sys.stderr)
        return {"error": "Input Error", "message": f"Invalid JSON provided for guid_mapping_json: {json_e}"}
    except ValueError as val_e:
            print(f"ERROR: Invalid value in guid_mapping_json (expected int for ID): {val_e}", file=sys.stderr)
            return {"error": "Input Error", "message": f"Invalid value in guid_mapping_json (expected int for ID): {val_e}"}

    try:
        print("Deserializing full Mermaid text (standalone)...", file=sys.stderr)
        root_topic = serialization.deserialize_mermaid_full(mermaid_text, guid_mapping_dict)
        if root_topic:
            print("Deserialization from full Mermaid successful.", file=sys.stderr)
            return serialization.serialize_object_simple(root_topic) # Return as simple JSON
        else:
             print("ERROR: Failed to deserialize full Mermaid text.", file=sys.stderr)
             return {"error": "Deserialization Error", "message": "Failed to deserialize full Mermaid text."}
    except Exception as e:
        print(f"ERROR during deserialization from full Mermaid: {e}", file=sys.stderr)
        return {"error": "Deserialization Error", "message": f"Failed to deserialize full Mermaid text: {e}"}


# --- Main Execution ---
if __name__ == "__main__":
    print("Starting MindManager Automation MCP Server...", file=sys.stderr)
    # Run the server using stdio transport by default
    # You can add command-line arguments here to configure transport, etc.
    # For example: mcp.run(transport='stdio', host='localhost', port=8080) for SSE
    try:
        mcp.run(transport='stdio')
    except Exception as main_e:
        print(f"FATAL: Server crashed: {main_e}", file=sys.stderr)
        sys.exit(1)
    finally:
        print("MindManager Automation MCP Server stopped.", file=sys.stderr)