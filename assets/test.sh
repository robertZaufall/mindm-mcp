# Direct command-line usage of the MCP handler

# First, make sure MindManager is open with a document

# List available functions
python server.py '{"function": "list_functions"}'

# Get mindmap (full mode)
python server.py '{"function": "get_mindmap", "args": {"mode": "full"}}'

# Get mindmap (text-only mode)
python server.py '{"function": "get_mindmap", "args": {"mode": "text"}}'

# Create a new mindmap from the structure
# python server.py '{"function": "create_mindmap"}'

# Create a new mindmap with verbose output
# python server.py '{"function": "create_mindmap", "args": {"verbose": true}}'

# Run in interactive mode (enter JSON requests manually)
python server.py
