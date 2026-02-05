# Grasshopper MCP Server

MCP (Model Context Protocol) server for Grasshopper integration.

## Installation

```bash
uv pip install -e .
```

## Usage

Start the MCP server:

```bash
grasshoppermcp
```

Or run in development mode:

```bash
uv run mcp dev src/grasshoppermcp:mcp
```

## Requirements

- Python 3.10+
- Grasshopper MCP Plugin running in Rhino/Grasshopper (port 2000)

## Available Tools

- `get_gh_document_info` - Get information about the active Grasshopper document
- `list_components` - List components on the canvas
- `add_component` - Add a component to the canvas
- `delete_component` - Delete a component
- `get_component_info` - Get detailed component information
- `connect_components` - Connect two components
- `disconnect_components` - Disconnect two components
- `set_parameter_value` - Set a parameter value
- `get_parameter_value` - Get a parameter value
- `run_solution` - Recompute the solution
- `expire_solution` - Expire a component or solution
- `bake_component` - Bake geometry to Rhino
- `get_canvas_state` - Get full canvas state
