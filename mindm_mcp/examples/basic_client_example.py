# mindm_mcp/examples/basic_client_example.py
"""
Basic example of using the MindManager MCP client library.

This example demonstrates how to:
1. Create a session
2. Get the current mindmap
3. Create a new mindmap
4. Add topics
5. Add relationships
6. Serialize the mindmap

Prerequisites:
- MindManager must be installed
- The MindManager MCP server must be running
"""

import asyncio
import logging
from mindm_mcp.client import MindManagerClientContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mindm-basic-example")

async def main():
    """Main entry point."""
    async with MindManagerClientContext() as client:
        # Create a session
        logger.info("Creating session...")
        session_id = await client.create_session()
        logger.info(f"Created session: {session_id}")
        
        # Check if a document is open
        session_info = await client.get_session_info()
        if not session_info["document_exists"]:
            logger.info("No document is open in MindManager. Creating a new mindmap...")
            
            # Create a new mindmap
            await client.create_mindmap(
                central_topic="MindManager MCP Example",
                topics=[
                    {
                        "text": "REST API",
                        "notes": "RESTful API for interacting with MindManager.",
                        "guid": "topic1",
                    },
                    {
                        "text": "Client Library",
                        "notes": "Python client library for the MCP server.",
                        "guid": "topic2",
                    },
                    {
                        "text": "MCP Integration",
                        "notes": "Model Context Protocol integration for Claude Desktop.",
                        "guid": "topic3",
                    },
                    {
                        "text": "Async Support",
                        "notes": "Asynchronous API for non-blocking operations.",
                        "guid": "topic4",
                        "parent_guid": "topic2",
                    },
                    {
                        "text": "Sync Support",
                        "notes": "Synchronous API for simpler usage.",
                        "guid": "topic5",
                        "parent_guid": "topic2",
                    },
                ],
                relationships=[
                    {
                        "guid_1": "topic1",
                        "guid_2": "topic2",
                        "label": "Used by",
                    },
                    {
                        "guid_1": "topic2",
                        "guid_2": "topic3",
                        "label": "Enables",
                    },
                ],
            )
            logger.info("Created new mindmap")
        
        # Get the mindmap
        logger.info("Getting mindmap...")
        result = await client.get_mindmap()
        
        if result["success"]:
            mindmap = result["data"]["mindmap"]
            logger.info(f"Central topic: {mindmap['text']}")
            logger.info(f"Maximum topic level: {result['data']['max_topic_level']}")
            
            # Add a topic
            logger.info("Adding a new topic...")
            topic_result = await client.add_topic(
                text="Added Programmatically",
                parent_guid=mindmap["guid"],
                notes="This topic was added through the MCP client library.",
            )
            
            if topic_result["success"]:
                new_topic_guid = topic_result["data"]["guid"]
                logger.info(f"Added topic with GUID: {new_topic_guid}")
                
                # Add a tag
                logger.info("Adding a tag to the new topic...")
                await client.add_tag(
                    topic_guid=new_topic_guid,
                    tag_text="Automated",
                )
                
                # Add a subtopic
                logger.info("Adding a subtopic...")
                subtopic_result = await client.add_topic(
                    text="Subtopic",
                    parent_guid=new_topic_guid,
                    notes="This is a subtopic of the programmatically added topic.",
                )
                
                if subtopic_result["success"]:
                    subtopic_guid = subtopic_result["data"]["guid"]
                    logger.info(f"Added subtopic with GUID: {subtopic_guid}")
                    
                    # Add a relationship
                    logger.info("Adding a relationship...")
                    await client.add_relationship(
                        guid_1=new_topic_guid,
                        guid_2=subtopic_guid,
                        label="Parent-Child",
                    )
            
            # Serialize the mindmap
            logger.info("Serializing mindmap to Mermaid format...")
            serialized_result = await client.serialize_mindmap(format_type="mermaid")
            
            if serialized_result["success"]:
                mermaid = serialized_result["data"]["content"]
                logger.info("Mermaid diagram:")
                logger.info(mermaid[:200] + "..." if len(mermaid) > 200 else mermaid)
            
            # Serialize to Markdown
            logger.info("Serializing mindmap to Markdown format...")
            md_result = await client.serialize_mindmap(format_type="markdown")
            
            if md_result["success"]:
                markdown = md_result["data"]["content"]
                logger.info("Markdown content:")
                logger.info(markdown[:200] + "..." if len(markdown) > 200 else markdown)
        
        logger.info("Example completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
