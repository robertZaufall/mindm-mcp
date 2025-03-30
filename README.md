# MindManager MCP Server

A Model Context Protocol (MCP) server implementation for the `mindm` library, providing a standardized interface to interact with MindManager on Windows and macOS.

## Overview

This server allows you to programmatically interact with MindManager through the Model Context Protocol (MCP), a standardized way to provide context and tools to LLMs. It leverages the `mindm` library to manipulate MindManager documents, topics, relationships, and other mindmap elements.

## Features

- Initialize MindManager connection with platform-specific settings
- Retrieve mindmap structure and central topics
- Create new mindmaps from serialized data
- Add, modify, and manipulate topics and subtopics
- Add relationships between topics
- Add tags to topics
- Export mindmaps to Mermaid and Markdown formats
- Get information about MindManager installation and library folders
- Set document background images
- Get current selection from MindManager

## Requirements

- Python 3.9 or higher
- `mcp` package (Model Context Protocol SDK)
- `mindm` library (included in this project)
- MindManager (supported versions: 23-) installed on Windows or macOS

## Installation

```bash
# Install required packages
pip install mcp
pip install -U --index-url=https://test.pypi.org/simple/ --extra-index-url=https://pypi.org/simple/ mindm mindm-mcp

# Clone the repository (if you're using it from a repository)
git clone https://github.com/robertZaufall/mindm-mcp.git
cd mindm-mcp
```

```bash
# Install required packages
uv run mcp dev mindm_mcp/server.py

# Clone the repository (if you're using it from a repository)
git clone https://github.com/robertZaufall/mindm-mcp.git
cd mindm-mcp
```

## Usage

### Starting the server

```bash
# Using the CLI
python server.py

# Alternative: Install with the MCP CLI
pip install 'mcp[cli]'
mcp install mindm_mcp/server.py

# for debugging
mcp dev mindm_mcp/server.py
```

## MCP Tools

The server exposes the following tools through the Model Context Protocol:

- `initialize`: Initialize connection to MindManager
- `get_version`: Get MindManager version
- `get_mindmap`: Get the current mindmap structure
- `get_central_topic`: Get the central topic of the current mindmap
- `get_selection`: Get currently selected topics
- `create_mindmap`: Create a new mindmap from provided structure
- `add_subtopic`: Add a subtopic to an existing topic
- `set_topic_text`: Update a topic's text content
- `add_relationship`: Add a relationship between topics
- `add_tag`: Add a tag to a topic
- `get_library_folder`: Get MindManager library folder path
- `set_background_image`: Set document background image
- `export_to_mermaid`: Export mindmap to Mermaid format
- `export_to_markdown`: Export mindmap to Markdown format

## MCP Resources

The server exposes the following resources:

- `mindmanager://info`: Information about the MindManager application

## Platform Support

- **Windows**: Full support for topics, notes, icons, images, tags, links, relationships, and RTF formatting
- **macOS**: Support for topics, notes, and relationships (limited support compared to Windows)

## Integration with Claude and other LLMs

This MCP server can be installed in Claude Desktop or other MCP-compatible applications, allowing LLMs to:

1. Access mindmap content
2. Manipulate mindmaps programmatically
3. Create new mindmaps based on LLM-generated content

## Troubleshooting

- Ensure MindManager is running before starting the server
- For macOS, verify that the `appscript` package is installed
- Check that the correct MindManager version (23-26) is installed
- Verify server URL and port settings in the client

## Acknowledgements

This project is built upon the `mindm` library developed by Robert Zaufall, providing Python interfaces to MindManager on Windows and macOS platforms. It uses the Model Context Protocol (MCP) SDK developed by Anthropic.

## License

MIT License - See LICENSE file for details
