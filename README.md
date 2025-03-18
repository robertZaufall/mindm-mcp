# MindManager MCP

MindManager MCP (Model Context Protocol) is a server and client library that enables AI assistants like Claude to interact with MindManager through the [mindm](https://github.com/robertZaufall/mindm) Python library.

[![PyPI version](https://img.shields.io/pypi/v/mindm_mcp.svg)](https://pypi.org/project/mindm_mcp/)

## Features

- RESTful API for interacting with MindManager
- WebSocket support for real-time communication
- Model Context Protocol (MCP) integration for Claude Desktop
- Client library for Python applications
- Async and sync client interfaces

## Installation

Install using `pip`:

```bash
pip install mindm_mcp
```

This package requires MindManager to be installed on your system, as it interacts with the MindManager application through the [mindm](https://github.com/robertZaufall/mindm) library.

## Quick Start

### Starting the MCP Server

To start the MindManager MCP server:

```bash
mindm-mcp-server --host 127.0.0.1 --port 8000
```

### Using the Client Library

```python
from mindm_mcp.client import SyncMindManagerClientContext

# Use the client with a context manager for automatic cleanup
with SyncMindManagerClientContext() as client:
    # Create a session
    client.create_session()
    
    # Get the current mindmap
    result = client.get_mindmap()
    if result["success"]:
        mindmap = result["data"]["mindmap"]
        print(f"Central topic: {mindmap['text']}")
    
    # Add a topic
    client.add_topic("New Topic", notes="This is a note for the new topic")
```

### Claude Desktop Integration

To enable Claude Desktop to interact with MindManager:

1. Start the MindManager MCP server:
   ```bash
   mindm-mcp-server
   ```

2. Start the Claude Desktop integration:
   ```bash
   mindm-claude-integration --port 8090
   ```

3. Configure Claude Desktop to use the MCP plugin at `localhost:8090`

## API Reference

### REST API Endpoints

- `POST /sessions` - Create a new MindManager session
- `GET /sessions/{session_id}` - Get session information
- `DELETE /sessions/{session_id}` - Delete a session
- `POST /sessions/{session_id}/get_mindmap` - Get the current mindmap
- `POST /sessions/{session_id}/create_mindmap` - Create a new mindmap
- `POST /sessions/{session_id}/add_topic` - Add a topic to the mindmap
- `POST /sessions/{session_id}/update_topic` - Update an existing topic
- `POST /sessions/{session_id}/add_relationship` - Add a relationship between topics
- `POST /sessions/{session_id}/add_tag` - Add a tag to a topic
- `POST /sessions/{session_id}/serialize_mindmap` - Serialize the mindmap to a specific format

### MCP Actions

The following actions are supported through the Model Context Protocol:

- `get_mindmap` - Get the current mindmap
- `create_mindmap` - Create a new mindmap
- `add_topic` - Add a topic to the mindmap
- `update_topic` - Update an existing topic
- `add_relationship` - Add a relationship between topics
- `add_tag` - Add a tag to a topic
- `serialize_mindmap` - Serialize the mindmap to a specific format

## Examples

### Basic Client Example

```python
import asyncio
from mindm_mcp.client import MindManagerClientContext

async def main():
    async with MindManagerClientContext() as client:
        # Create a session
        await client.create_session()
        
        # Get the current mindmap
        result = await client.get_mindmap()
        if result["success"]:
            mindmap = result["data"]["mindmap"]
            print(f"Central topic: {mindmap['text']}")
            
            # Add a subtopic
            topic_result = await client.add_topic(
                text="New Subtopic",
                parent_guid=mindmap["guid"],
                notes="This is a sample subtopic",
            )
            
            if topic_result["success"]:
                print(f"Added topic with GUID: {topic_result['data']['guid']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Claude MCP Example

```python
import json
import asyncio
import socket
import struct

async def send_mcp_request(host, port, action, params):
    # Connect to the MCP server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    
    # Create request
    request = {
        "action": action,
        "params": params,
    }
    request_json = json.dumps(request)
    request_bytes = request_json.encode("utf-8")
    
    # Send request length and data
    sock.sendall(len(request_bytes).to_bytes(4, byteorder="little", signed=False))
    sock.sendall(request_bytes)
    
    # Receive response length
    length_bytes = sock.recv(4)
    length = int.from_bytes(length_bytes, byteorder="little", signed=False)
    
    # Receive response data
    response_bytes = sock.recv(length)
    response_json = response_bytes.decode("utf-8")
    response = json.loads(response_json)
    
    # Close connection
    sock.close()
    
    return response

async def main():
    # Get the current mindmap
    result = await send_mcp_request("localhost", 8090, "get_mindmap", {})
    
    if result["success"]:
        mindmap = result["data"]["mindmap"]
        print(f"Central topic: {mindmap['text']}")
        
        # Add a new topic
        topic_result = await send_mcp_request(
            "localhost",
            8090,
            "add_topic",
            {
                "text": "Added by MCP",
                "notes": "This topic was added through the Model Context Protocol",
            },
        )
        
        if topic_result["success"]:
            print(f"Added topic with GUID: {topic_result['data']['guid']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
