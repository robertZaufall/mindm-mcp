# MindManager MCP Server

A Model Context Protocol (MCP) server implementation for the `mindm` library, providing a standardized interface to interact with MindManager on Windows and macOS.  

[![PyPI version](https://img.shields.io/pypi/v/mindm-mcp.svg)](https://pypi.org/project/mindm-mcp/)
[![PyPI version](https://img.shields.io/pypi/v/mindm.svg)](https://pypi.org/project/mindm/)

## Overview

This server allows you to programmatically interact with MindManager through the Model Context Protocol (MCP), a standardized way to provide context and tools to LLMs. It leverages the `mindm` library to manipulate MindManager documents, topics, relationships, and other mindmap elements.

Example:

![MindManager MCP in Claude](https://github.com/robertZaufall/mindm-mcp/blob/master/assets/claude.png?raw=true)

## Features

- Retrieve mindmap structure and central topics
- Export mindmaps to Mermaid, Markdown, JSON formats to be used in LLM chats
- Get information about MindManager installation and library folders
- Get current selection from MindManager

## Planned Features

- Create new mindmaps from serialized data
- Add, modify, and manipulate topics and subtopics
- Add relationships between topics
- Add tags to topics
- Set document background images

## Requirements

- Python 3.12 or higher
- `mcp` package (Model Context Protocol SDK)
- `mindm` library (included in this project)
- MindManager (supported versions: 23-) installed on Windows or macOS

## Installation macOS

```bash
# Clone the repository (if you're using it from a repository)
git clone https://github.com/robertZaufall/mindm-mcp.git
cd mindm-mcp

# create a virtual environment for Python
brew install uv # if needed
uv pip install -r pyproject.toml

# alternative: manual installation of modules
uv add "mcp[cli]"
uv add fastmcp
uv add markdown-it-py
uv add -U --index-url=https://test.pypi.org/simple/ --extra-index-url=https://pypi.org/simple/ mindm mindm-mcp
```

## Installation Windows

```bash
# Change to DOS command prompt
cmd

# Clone the repository (if you're using it from a repository)
git clone https://github.com/robertZaufall/mindm-mcp.git
cd mindm-mcp

# create a virtual environment for Python
pip install uv # if needed
uv pip install -r pyproject.toml

# install nodejs
choco install nodejs # if you have chocolatey installed. If not install nodejs otherwise
refreshenv
node -v
npm install -g npx
```

## Usage

### MCP inspector

```bash
# run mcp with inspector
uv run --with mind --with fastmcp --with markdown-it-py mcp dev mindm_mcp/server.py
```

### Claude Desktop

#### Local python file

Adjust the path for the local file as needed.
```json
{
  "mcpServers": {
    "mindm (MindManager)": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mindm>=0.0.4.6",
        "--with",
        "fastmcp",
        "--with",
        "markdown-it-py",
        "/Users/master/git/mindm-mcp/mindm_mcp/server.py"
      ]
    }
  }
}
```

#### Module from package repository

Adjust `VIRTUAL_ENV` as needed.
```json
{
    "mcpServers": {
      "mindm (MindManager)": {
        "command": "uv",
        "args": [
          "run",
          "--with",
          "mindm>=0.0.4.6",
          "--with",
          "mindm-mcp>=0.0.1.50",
          "--with",
          "fastmcp",
          "--with",
          "markdown-it-py",
          "-m",
          "mindm_mcp.server"
        ],
        "env": {
            "VIRTUAL_ENV": "/Users/master/git/mindm-mcp/.venv"
        }
      }
    }
}
```

Hint: If the MCP server does not show up with the hammer icon on Windows, close Claude Desktop and kill all background processes.  


## MCP Tools

The server exposes the following tools through the Model Context Protocol:

### Document Interaction
- `get_mindmap`: Retrieves the current mindmap structure from MindManager
- `get_selection`: Retrieves the currently selected topics in MindManager
- `get_library_folder`: Gets the path to the MindManager library folder
- `get_grounding_information`: Extracts grounding information (central topic, selected subtopics) from the mindmap

### Serialization
- `serialize_current_mindmap_to_mermaid`: Serializes the currently loaded mindmap to Mermaid format
- `serialize_current_mindmap_to_markdown`: Serializes the currently loaded mindmap to Markdown format
- `serialize_current_mindmap_to_json`: Serializes the currently loaded mindmap to a detailed JSON object with ID mapping


## Platform Support

- **Windows**: Full support for topics, notes, icons, images, tags, links, relationships, and RTF formatting
- **macOS**: Support for topics, notes, and relationships (limited support compared to Windows)

## Integration with Claude and other LLMs

This MCP server can be installed in Claude Desktop or other MCP-compatible applications, allowing LLMs to:

1. Access mindmap content
2. Manipulate mindmaps (coming)
3. Create new mindmaps based on LLM-generated content (coming)

## Troubleshooting

- Ensure MindManager is running before starting the server
- For macOS, make sure you allow Claude Desktop to automate MindManager

## Acknowledgements

This project is built upon the `mindm` library, providing Python interfaces to MindManager on Windows and macOS platforms. It uses the Model Context Protocol (MCP) SDK developed by Anthropic.

## License

MIT License - See LICENSE file for details
