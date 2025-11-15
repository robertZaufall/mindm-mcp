import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Union

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import mindm_mcp.server as server


MERMAID_FULL_EXAMPLE = """
mindmap
  [Creating an AI startup] %% {"id": 1}
    [Vision & Strategy] %% {"id": 2}
      [Mission and Value] %% {"id": 3}
        [Problem statement] %% {"id": 4}
        [Value proposition] %% {"id": 5}
        [Long term goals] %% {"id": 6}
      [Competitive Positioning] %% {"id": 7}
        [Differentiation pillars] %% {"id": 8}
        [Key competitors map] %% {"id": 9}
        [Barrier strategies] %% {"id": 10}
    [Product & Tech] %% {"id": 19}
      [MVP Design] %% {"id": 20}
        [Core feature set] %% {"id": 21}
        [User flows map] %% {"id": 22}
        [Rapid prototyping] %% {"id": 23}
"""

MERMAID_SIMPLE_EXAMPLE = """
mindmap
  Creating an AI startup
    Vision & Strategy
      Mission and Value
        Problem statement
        Value proposition
        Long term goals
      Competitive Positioning
        Differentiation pillars
        Key competitors map
        Barrier strategies
    Product & Tech
      MVP Design
        Core feature set
        User flows map
        Rapid prototyping
"""

async def call_get_mindmap():
    """Calls server.get_mindmap with different parameters."""
    print("\n--- Testing get_mindmap ---")
    modes = ['full', 'content', 'text']
    turbo_modes = [True, False]
    for mode in modes:
        for turbo_mode in turbo_modes:
            print(f"Calling get_mindmap(mode='{mode}', turbo_mode={turbo_mode})")
            result = await server.get_mindmap(mode=mode, turbo_mode=turbo_mode)
            print(f"Result: {json.dumps(result, indent=2)}")

async def call_get_selection():
    """Calls server.get_selection with different parameters."""
    print("\n--- Testing get_selection ---")
    modes = ['full', 'content', 'text']
    turbo_modes = [True, False]
    for mode in modes:
        for turbo_mode in turbo_modes:
            print(f"Calling get_selection(mode='{mode}', turbo_mode={turbo_mode})")
            result = await server.get_selection(mode=mode, turbo_mode=turbo_mode)
            print(f"Result: {json.dumps(result, indent=2)}")

async def call_get_library_folder():
    """Calls server.get_library_folder."""
    print("\n--- Testing get_library_folder ---")
    print("Calling get_library_folder()")
    result = await server.get_library_folder()
    print(f"Result: {json.dumps(result, indent=2)}")

async def call_get_grounding_information():
    """Calls server.get_grounding_information with different parameters."""
    print("\n--- Testing get_grounding_information ---")
    modes = ['full', 'content', 'text']
    turbo_modes = [True, False]
    for mode in modes:
        for turbo_mode in turbo_modes:
            print(f"Calling get_grounding_information(mode='{mode}', turbo_mode={turbo_mode})")
            result = await server.get_grounding_information(mode=mode, turbo_mode=turbo_mode)
            print(f"Result: {json.dumps(result, indent=2)}")

async def call_serialize_current_mindmap_to_mermaid():
    """Calls server.serialize_current_mindmap_to_mermaid with different parameters."""
    print("\n--- Testing serialize_current_mindmap_to_mermaid ---")
    id_only_options = [True, False]
    modes = ['full', 'content', 'text']
    turbo_modes = [True, False]
    for id_only in id_only_options:
        for mode in modes:
            for turbo_mode in turbo_modes:
                print(f"Calling serialize_current_mindmap_to_mermaid(id_only={id_only}, mode='{mode}', turbo_mode={turbo_mode})")
                result = await server.serialize_current_mindmap_to_mermaid(id_only=id_only, mode=mode, turbo_mode=turbo_mode)
                print(f"Result: {json.dumps(result, indent=2)}")

async def call_serialize_current_mindmap_to_markdown():
    """Calls server.serialize_current_mindmap_to_markdown with different parameters."""
    print("\n--- Testing serialize_current_mindmap_to_markdown ---")
    include_notes_options = [True, False]
    modes = ['full', 'content', 'text']
    turbo_modes = [True, False]
    for include_notes in include_notes_options:
        for mode in modes:
            for turbo_mode in turbo_modes:
                print(f"Calling serialize_current_mindmap_to_markdown(include_notes={include_notes}, mode='{mode}', turbo_mode={turbo_mode})")
                result = await server.serialize_current_mindmap_to_markdown(include_notes=include_notes, mode=mode, turbo_mode=turbo_mode)
                print(f"Result: {json.dumps(result, indent=2)}")

async def call_serialize_current_mindmap_to_json():
    """Calls server.serialize_current_mindmap_to_json with different parameters."""
    print("\n--- Testing serialize_current_mindmap_to_json ---")
    ignore_rtf_options = [True, False]
    modes = ['full', 'content', 'text']
    turbo_modes = [True, False]
    for ignore_rtf in ignore_rtf_options:
        for mode in modes:
            for turbo_mode in turbo_modes:
                print(f"Calling serialize_current_mindmap_to_json(ignore_rtf={ignore_rtf}, mode='{mode}', turbo_mode={turbo_mode})")
                result = await server.serialize_current_mindmap_to_json(ignore_rtf=ignore_rtf, mode=mode, turbo_mode=turbo_mode)
                print(f"Result: {json.dumps(result, indent=2)}")

async def call_create_mindmap_from_mermaid():
    """Calls server.create_mindmap_from_mermaid with an example diagram."""
    print("\n--- Testing create_mindmap_from_mermaid ---")
    print("Calling create_mindmap_from_mermaid(turbo_mode=True)")
    result = await server.create_mindmap_from_mermaid(
        mermaid=MERMAID_FULL_EXAMPLE,
        turbo_mode=True,
    )
    print(f"Result: {json.dumps(result, indent=2)}")

async def call_create_mindmap_from_mermaid_simple():
    """Calls server.create_mindmap_from_mermaid_simple with an example diagram."""
    print("\n--- Testing create_mindmap_from_mermaid_simple ---")
    print("Calling create_mindmap_from_mermaid_simple(turbo_mode=True)")
    result = await server.create_mindmap_from_mermaid_simple(
        mermaid=MERMAID_SIMPLE_EXAMPLE,
        turbo_mode=True,
    )
    print(f"Result: {json.dumps(result, indent=2)}")


async def main():
    """Calls all the test functions."""
    await call_get_mindmap()
    await call_get_selection()
    await call_get_library_folder()
    await call_get_grounding_information()
    await call_serialize_current_mindmap_to_mermaid()
    await call_serialize_current_mindmap_to_markdown()
    await call_serialize_current_mindmap_to_json()
    await call_create_mindmap_from_mermaid()
    await call_create_mindmap_from_mermaid_simple()

if __name__ == "__main__":
    # Check if MindManager is running before running the tests
    try:
        import mindm.mindmanager as mm
        server._get_library_folder()
        print("MindManager is running. Proceeding with tests.")
        asyncio.run(main())
    except Exception as e:
        print(f"Error: MindManager is not running or an error occurred: {e}")
        print("Please ensure MindManager is running and try again.")
        sys.exit(1)
