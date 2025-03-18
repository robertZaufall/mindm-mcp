# mindm_mcp/examples/claude_mcp_example.py
"""
Example of using the MindManager MCP plugin with Claude Desktop.

This example demonstrates how to use the Model Context Protocol to communicate
with the MindManager MCP plugin, similar to how Claude Desktop would interact with it.

Prerequisites:
- MindManager must be installed
- The MindManager MCP server must be running
- The MindManager MCP plugin must be running
"""

import json
import asyncio
import socket
import logging
import struct
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("claude-mcp-example")

async def send_mcp_request(host: str, port: int, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a request to the MCP server using the MCP protocol.
    
    Args:
        host: MCP server host
        port: MCP server port
        action: Action to perform
        params: Action parameters
        
    Returns:
        Dict: Response from the MCP server
    """
    try:
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
        
        # Send request length (4 bytes, little-endian unsigned int)
        length_bytes = len(request_bytes).to_bytes(4, byteorder="little", signed=False)
        sock.sendall(length_bytes)
        
        # Send request data
        sock.sendall(request_bytes)
        
        # Receive response length
        length_bytes = sock.recv(4)
        if not length_bytes:
            raise RuntimeError("Connection closed unexpectedly")
        
        length = int.from_bytes(length_bytes, byteorder="little", signed=False)
        
        # Receive response data
        response_bytes = b""
        remaining = length
        while remaining > 0:
            chunk = sock.recv(min(4096, remaining))
            if not chunk:
                raise RuntimeError("Connection closed unexpectedly")
            response_bytes += chunk
            remaining -= len(chunk)
        
        response_json = response_bytes.decode("utf-8")
        response = json.loads(response_json)
        
        # Close connection
        sock.close()
        
        return response
    
    except Exception as e:
        logger.error(f"Error sending MCP request: {str(e)}")
        return {"success": False, "error": f"Error: {str(e)}"}

async def main():
    """Main entry point."""
    host = "localhost"
    port = 8090
    
    logger.info(f"Connecting to MindManager MCP plugin at {host}:{port}")
    
    try:
        # Get the current mindmap
        logger.info("Getting the current mindmap...")
        result = await send_mcp_request(host, port, "get_mindmap", {})
        
        if not result["success"]:
            logger.error(f"Failed to get mindmap: {result.get('error', 'Unknown error')}")
            return
        
        mindmap = result["data"]["mindmap"]
        logger.info(f"Central topic: {mindmap['text']}")
        
        # Create or update the mindmap with Claude-related content
        if "Claude" not in mindmap["text"]:
            logger.info("Creating a new Claude-focused mindmap...")
            
            # Create a new mindmap
            create_result = await send_mcp_request(
                host,
                port,
                "create_mindmap",
                {
                    "central_topic": "Claude AI Integration",
                    "topics": [
                        {
                            "text": "Model Context Protocol",
                            "notes": "The Model Context Protocol (MCP) enables AI assistants to interact with external tools.",
                            "guid": "mcp_topic",
                        },
                        {
                            "text": "MindManager Integration",
                            "notes": "Integration between Claude and MindManager for mind mapping capabilities.",
                            "guid": "integration_topic",
                        },
                        {
                            "text": "Use Cases",
                            "notes": "Potential applications for Claude and MindManager integration.",
                            "guid": "usecases_topic",
                        },
                    ],
                },
            )
            
            if not create_result["success"]:
                logger.error(f"Failed to create mindmap: {create_result.get('error', 'Unknown error')}")
                return
            
            logger.info("Created new mindmap with Claude integration theme")
            
            # Get the updated mindmap
            result = await send_mcp_request(host, port, "get_mindmap", {})
            if not result["success"]:
                logger.error(f"Failed to get updated mindmap: {result.get('error', 'Unknown error')}")
                return
            
            mindmap = result["data"]["mindmap"]
        
        # Add use case topics
        logger.info("Adding use case topics...")
        
        # Find the use cases topic
        usecases_guid = None
        if "subtopics" in mindmap:
            for topic in mindmap["subtopics"]:
                if topic["text"] == "Use Cases":
                    usecases_guid = topic["guid"]
                    break
        
        if not usecases_guid:
            # Add the Use Cases topic if it doesn't exist
            usecase_result = await send_mcp_request(
                host,
                port,
                "add_topic",
                {
                    "text": "Use Cases",
                    "notes": "Potential applications for Claude and MindManager integration.",
                },
            )
            
            if not usecase_result["success"]:
                logger.error(f"Failed to add Use Cases topic: {usecase_result.get('error', 'Unknown error')}")
                return
            
            usecases_guid = usecase_result["data"]["guid"]
            logger.info(f"Added Use Cases topic with GUID: {usecases_guid}")
        
        # Add specific use case topics
        use_cases = [
            {
                "text": "Brainstorming Sessions",
                "notes": "Claude can help generate ideas and organize them into mind maps for brainstorming sessions.",
            },
            {
                "text": "Project Planning",
                "notes": "Use Claude to analyze project requirements and create structured project plans in MindManager.",
            },
            {
                "text": "Knowledge Organization",
                "notes": "Leverage Claude's knowledge to organize complex information into intuitive mind maps.",
            },
            {
                "text": "Learning and Education",
                "notes": "Create educational mind maps to help with learning and retention of complex topics.",
            },
        ]
        
        added_topics = []
        for use_case in use_cases:
            topic_result = await send_mcp_request(
                host,
                port,
                "add_topic",
                {
                    "text": use_case["text"],
                    "notes": use_case["notes"],
                    "parent_guid": usecases_guid,
                },
            )
            
            if topic_result["success"]:
                logger.info(f"Added use case topic: {use_case['text']}")
                added_topics.append(topic_result["data"]["guid"])
            else:
                logger.error(f"Failed to add use case topic: {topic_result.get('error', 'Unknown error')}")
        
        # Add tags to the topics
        for topic_guid in added_topics:
            await send_mcp_request(
                host,
                port,
                "add_tag",
                {
                    "topic_guid": topic_guid,
                    "tag_text": "Claude-Enabled",
                },
            )
            logger.info(f"Added 'Claude-Enabled' tag to topic {topic_guid}")
        
        # Serialize the final mindmap to Mermaid format
        logger.info("Serializing the mindmap to Mermaid format...")
        serialize_result = await send_mcp_request(
            host,
            port,
            "serialize_mindmap",
            {
                "format_type": "mermaid",
            },
        )
        
        if serialize_result["success"]:
            mermaid_content = serialize_result["data"]["content"]
            logger.info("Mermaid representation of the mindmap:")
            logger.info(mermaid_content[:200] + "..." if len(mermaid_content) > 200 else mermaid_content)
        else:
            logger.error(f"Failed to serialize mindmap: {serialize_result.get('error', 'Unknown error')}")
        
        logger.info("Claude MCP example completed successfully")
    
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())