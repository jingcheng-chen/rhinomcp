# RhinoMCP - Rhino Model Context Protocol Integration

<img src="assets/rhinomcp_logo.svg" alt="RhinoMCP Logo" width="130">

RhinoMCP connects Rhino to AI agents through the Model Context Protocol (MCP), allowing AI agents to directly interact with and control Rhino. This integration enables prompt assisted 3D modeling in Rhino 3D.

## Features

### Rhino MCP

- **Two-way communication**: Connect AI agents to Rhino through a socket-based server
- **Object manipulation**: Create, modify, and delete 3D objects in Rhino
- **Document inspection**: Get detailed information about the current Rhino document
- **Script execution**: Execute RhinoScript Python code in Rhino
- **Advanced geometry**: Loft, extrude, sweep, offset, and pipe operations
- **Boolean operations**: Union, difference, and intersection
- **Object selection**: Select objects based on filters (name, color, layer, type) with "and" or "or" logic
- **Layer management**: Get/set current layer, create and delete layers

### Grasshopper MCP (New!)

- **Component management**: Add, delete, and inspect Grasshopper components
- **Connection control**: Connect and disconnect component inputs/outputs
- **Parameter control**: Set and get parameter values on components
- **Solution management**: Run and expire solutions
- **Baking**: Bake component outputs to Rhino
- **Canvas state**: Get full canvas state with all components and connections

> [!NOTE]  
> So far the tool only supports creating primitive objects for proof of concept. More geometries will be added in the future.
> Supported objects: Point, Line, Polyline, Circle, Arc, Ellipse, Curve, Box, Sphere, Cone, Cylinder, Surface (from points)

## Demo

### Demo 1

This demo shows how AI can interact with Rhino in two directions. Click the image below to watch the video.

[![demo2](assets/demo2.jpg)](https://youtu.be/pi6dbqUuhI4)

### Demo 2

This demo shows how to ask AI to create custom scripts and execute them in Rhino. Click the image below to watch the video.

[![demo1](assets/demo1.jpg)](https://youtu.be/NFOF_Pjp3qY)

## Tutorial

Thanks to Nate. He has created a showcase and installation [tutorial](https://www.youtube.com/watch?v=z2IBP81ABRM) for this tool.

## Components

The system consists of two main components:

1. **MCP Server (`src/rhino_mcp_server/server.py`)**: A Python server that implements the Model Context Protocol and connects to the Rhino plugin
2. **Rhino Plugin (`src/rhino_mcp_plugin`)**: A Rhino plugin that creates a socket server within Rhino to receive and execute commands

## Installation

### Prerequisites

- Rhino 7 or newer (Works onWindows and Mac); make sure you Rhino is up to date.
- Python 3.10 or newer
- uv package manager

**⚠️ Only run one instance of the MCP server (either on Cursor or Claude Desktop), not both**

### Installing the Rhino Plugin

1. Go to Tools > Package Manager
2. Search for `rhinomcp`
3. Click `Install`

#### Install uv

**If you're on Mac, please install uv as**

```bash
brew install uv
```

**On Windows**

```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**⚠️ Do not proceed before installing UV**

### Config file

**Rhino MCP only:**
```json
{
  "mcpServers": {
    "rhino": {
      "command": "uvx",
      "args": ["rhinomcp"]
    }
  }
}
```

**Rhino + Grasshopper MCP:**
```json
{
  "mcpServers": {
    "rhino": {
      "command": "uvx",
      "args": ["rhinomcp"]
    },
    "grasshopper": {
      "command": "uvx",
      "args": ["grasshoppermcp"]
    }
  }
}
```

### Claude for Desktop Integration

Go to Claude > Settings > Developer > Edit Config > claude_desktop_config.json to include the above config file.

### Cursor integration

Make sure your cursor is up to date.

Create a folder `.cursor` in your project root.

Create a file `mcp.json` in the `.cursor` folder and include the above config file:

Go to Cursor Settings > MCP and check if it's enabled.

## Usage

### Starting Rhino MCP

![RhinoMCP in the command line](assets/rhino_plugin_instruction.jpg)

1. In Rhino, type `MCPStart` in the command line to start the socket server (port 1999)
2. The MCP server will connect automatically when you use Claude or Cursor

### Starting Grasshopper MCP

1. Open Grasshopper in Rhino
2. In Rhino, type `GHMCPStart` in the command line to start the socket server (port 2000)
3. The MCP server will connect automatically when you use Claude or Cursor

### Using with Claude

Once the config file has been set on Claude, and the plugin is running on Rhino, you will see a hammer icon with tools for the RhinoMCP.

![RhinoMCP in Claude](assets/claude_enable_instruction.jpg)

### Using with Cursor

Once the config file has been set on Cursor, and the plugin is running on Rhino, you will see the green indicator in front of the MCP server.

![RhinoMCP in Cursor](assets/cursor_enable_instruction.jpg)

If not, try refresh the server in Cursor. If any console pops up, please do not close it.

Once it's ready, use `Ctrl+I` to open the chat box and start chatting with Rhino. Make sure you've selected **Agent** mode.

![RhinoMCP in Cursor](assets/cursor_usage_instruction.jpg)

## Technical Details

### Communication Protocol

The system uses a simple JSON-based protocol over TCP sockets:

- **Commands** are sent as JSON objects with a `type` and optional `params`
- **Responses** are JSON objects with a `status` and `result` or `message`

## Local Development

### Project Structure

```
rhinomcp/
├── RhinoMCP.sln                 # Solution file (includes both plugins)
├── rhino_mcp_plugin/            # Rhino C# plugin
├── rhino_mcp_server/            # Rhino Python MCP server
├── grasshopper_mcp_plugin/      # Grasshopper C# plugin
├── grasshopper_mcp_server/      # Grasshopper Python MCP server
└── shared/csharp/               # Shared C# code (linked into both plugins)
```

### Prerequisites

- .NET 8.0 SDK
- Python 3.10+
- uv package manager
- Rhino 8

### Building the C# Plugins

Build both Rhino and Grasshopper plugins:

```bash
# From the root directory
dotnet build RhinoMCP.sln

# Or build in Release mode
dotnet build RhinoMCP.sln -c Release
```

The build automatically copies:
- `rhinomcp.rhp` → `/Applications/Rhino 8.app/Contents/PlugIns/` (macOS)
- `grasshopper_mcp.gha` → `~/Library/Application Support/McNeel/Rhinoceros/8.0/Plug-ins/Grasshopper .../Libraries/` (macOS)

After building, restart Rhino to load the updated plugins.

### Running the MCP Servers Locally

#### Rhino MCP Server

```bash
cd rhino_mcp_server

# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Run the MCP server in dev mode (with MCP Inspector)
uv run mcp dev main.py:mcp
```

In Rhino, run `MCPStart` to start the plugin socket server (port 1999).

#### Grasshopper MCP Server

```bash
cd grasshopper_mcp_server

# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Run the MCP server in dev mode (with MCP Inspector)
uv run mcp dev main.py:mcp
```

In Rhino, run `GHMCPStart` to start the Grasshopper plugin socket server (port 2000).

### Testing

```bash
# Run all Rhino MCP tests
cd rhino_mcp_server && uv run pytest tests/ -v

# Run all Grasshopper MCP tests
cd grasshopper_mcp_server && uv run pytest tests/ -v
```

### Local MCP Configuration

For local development, update your MCP config to use the local servers:

```json
{
  "mcpServers": {
    "rhino": {
      "command": "uv",
      "args": ["--directory", "/path/to/rhinomcp/rhino_mcp_server", "run", "main.py"]
    },
    "grasshopper": {
      "command": "uv",
      "args": ["--directory", "/path/to/rhinomcp/grasshopper_mcp_server", "run", "main.py"]
    }
  }
}
```

## Building and Publishing

### Publishing the MCP Servers

```bash
# Rhino MCP Server
cd rhino_mcp_server
uv build
uv publish

# Grasshopper MCP Server
cd grasshopper_mcp_server
uv build
uv publish
```

### Publishing the Rhino Plugin

1. Build in Release mode: `dotnet build RhinoMCP.sln -c Release`
2. Copy `manifest.yml` to the `rhino_mcp_plugin/bin/Release/net8.0` folder
3. Run `yak build` in the Release folder
4. Run `yak push rhinomcp-x.x.x-rh8-any.yak` to publish

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This is a third-party integration and not made by Mcneel. Made by [Jingcheng Chen](https://github.com/jingcheng-chen)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=jingcheng-chen/rhinomcp&type=Date)](https://www.star-history.com/#jingcheng-chen/rhinomcp&Date)
