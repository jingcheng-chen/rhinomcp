# RhinoMCP - Implementation Details

> This document provides a comprehensive reference for understanding the RhinoMCP codebase without having to read through all source files.

## Project Overview

**RhinoMCP** is a Model Context Protocol (MCP) integration that connects Rhino 3D (the CAD software) to AI agents (Claude, Claude Desktop, and Cursor). It enables prompt-assisted 3D modeling by allowing AI to directly interact with and control Rhino through a standardized protocol.

- **Version:** 0.1.3.6
- **Author:** Jingcheng Chen
- **License:** MIT
- **Repository:** https://github.com/jingcheng-chen/rhinomcp

---

## Architecture

The project uses a **two-tier client-server architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Clients                                │
│  (Claude Desktop, Cursor, Custom MCP Clients)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ MCP Protocol (stdio/HTTP)
                     │
┌────────────────────▼────────────────────────────────────────┐
│         Python MCP Server (rhino_mcp_server)                 │
│  - FastMCP framework (MCP implementation)                    │
│  - Connects to Rhino on 127.0.0.1:1999                      │
│  - Routes tool calls to Rhino plugin via TCP sockets        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ TCP Socket (JSON protocol)
                     │ 127.0.0.1:1999
                     │
┌────────────────────▼────────────────────────────────────────┐
│     Rhino Plugin (rhino_mcp_plugin) - C# .NET 7.0           │
│  - Socket server listening for commands                      │
│  - Executes commands in Rhino's main thread                 │
│  - Returns results back to Python server                    │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User (Claude/AI) → MCP Tool Call → server.py
  → RhinoConnection.send_command()
  → TCP Socket → Rhino Plugin
  → Execute in Rhino (UI thread)
  → Return JSON result
```

---

## Directory Structure

```
rhinomcp/
├── rhino_mcp_server/                 # Python MCP server package
│   ├── src/rhinomcp/
│   │   ├── server.py                 # Main MCP server & connection manager
│   │   ├── tools/                    # MCP tools (16+ functions)
│   │   │   ├── create_object.py      # Create geometric objects
│   │   │   ├── create_objects.py     # Batch object creation
│   │   │   ├── modify_object.py      # Modify existing objects
│   │   │   ├── modify_objects.py     # Batch modifications
│   │   │   ├── delete_object.py      # Delete objects
│   │   │   ├── get_document_info.py  # Document metadata & objects
│   │   │   ├── get_object_info.py    # Individual object details
│   │   │   ├── get_selected_objects_info.py
│   │   │   ├── select_objects.py     # Select objects with filters
│   │   │   ├── create_layer.py       # Layer management
│   │   │   ├── delete_layer.py
│   │   │   ├── get_or_set_current_layer.py
│   │   │   ├── execute_rhinoscript_python_code.py  # Run Python in Rhino
│   │   │   ├── get_rhinoscript_python_function_names.py
│   │   │   └── get_rhinoscript_python_code_guide.py
│   │   ├── prompts/                  # MCP prompts (strategy guidance)
│   │   │   └── assert_general_strategy.py
│   │   └── static/
│   │       └── rhinoscriptsyntax.py  # RhinoScript Python reference (~1.5MB)
│   ├── main.py                       # Entry point
│   ├── pyproject.toml                # Python project config
│   ├── uv.lock                       # Dependency lock file
│   └── dev.sh                        # Development runner
│
├── rhino_mcp_plugin/                 # C# Rhino plugin (.NET 7.0)
│   ├── RhinoMCPPlugin.cs             # Plugin base class
│   ├── RhinoMCPServer.cs             # TCP socket server (main logic)
│   ├── RhinoMCPServerController.cs   # Server lifecycle control
│   ├── Functions/
│   │   ├── CreateObject.cs           # Object creation (13 geometric types)
│   │   ├── CreateObjects.cs
│   │   ├── ModifyObject.cs
│   │   ├── ModifyObjects.cs
│   │   ├── DeleteObject.cs
│   │   ├── GetDocumentInfo.cs        # Fetches up to 30 items
│   │   ├── GetObjectInfo.cs
│   │   ├── GetSelectedObjectsInfo.cs
│   │   ├── SelectObjects.cs          # Advanced filtering
│   │   ├── CreateLayer.cs
│   │   ├── DeleteLayer.cs
│   │   ├── GetOrSetCurrentLayer.cs
│   │   ├── ExecuteRhinoscript.cs     # Execute Python scripts in Rhino
│   │   └── _utils.cs                 # Helper methods
│   ├── Serializers/
│   │   └── Serializer.cs             # Converts Rhino geometry to JSON
│   ├── rhinomcp.csproj               # C# project (targets net7.0)
│   ├── manifest.yml                  # Yak package metadata
│   └── bin/Release/                  # Build output (.rhp plugin file)
│
├── grasshopper_mcp_server/           # Grasshopper integration (experimental)
├── grasshopper_mcp_plugin/           # Grasshopper plugin (experimental)
│
├── .github/workflows/
│   ├── mcp-server-publish.yml        # PyPI publish workflow
│   └── rhino-plugin-publish.yml      # Yak package publish workflow
│
├── .cursor/
│   └── mcp.json                      # Cursor IDE MCP configuration
│
├── assets/                           # Demo images & logo
├── demo_chats/                       # Sample AI interactions
├── website/                          # Documentation website
├── README.md                         # Main documentation
└── IMPLEMENTATION.md                 # This file
```

---

## Key Components

### 1. Python MCP Server (`rhino_mcp_server/src/rhinomcp/server.py`)

**Purpose:** Implements Model Context Protocol and manages socket communication with Rhino

**Key Classes:**

#### `RhinoConnection`
Manages TCP socket connection to Rhino plugin:
- Connects to `127.0.0.1:1999`
- Sends JSON commands: `{"type": "command_name", "params": {...}}`
- Receives JSON responses with status and results
- Implements chunked receiving with 15-second timeout
- Reconnects automatically if connection drops

```python
# Connection pattern
conn = RhinoConnection()
conn.connect()
result = conn.send_command("create_object", params)
```

#### FastMCP Server
- Registers 16+ tools for AI agents
- Implements lifespan management (startup/shutdown)
- Global persistent connection reuse via `rhino_connection` global variable

### 2. Rhino Plugin (`rhino_mcp_plugin/`)

**Purpose:** Socket server running inside Rhino, executing commands in the main thread

#### `RhinoMCPServer.cs`
- Listens on `127.0.0.1:1999`
- Handles multi-threaded client connections
- Routes commands to `RhinoMCPFunctions` handlers
- Executes all Rhino operations on UI thread using `RhinoApp.InvokeOnUiThread()`
- Wraps operations in Undo records

**Command Dispatch (simplified):**
```csharp
Dictionary<string, Func<JObject, JObject>> handlers = {
    ["get_document_info"] = handler.GetDocumentInfo,
    ["create_object"] = handler.CreateObject,
    ["modify_object"] = handler.ModifyObject,
    ["delete_object"] = handler.DeleteObject,
    ["select_objects"] = handler.SelectObjects,
    // ... more handlers
}
```

#### `RhinoMCPPlugin.cs`
- Plugin base class extending `Rhino.PlugIns.PlugIn`
- Registers Rhino commands: `mcpstart`, `mcpstop`, `mcpstatus`

#### `RhinoMCPServerController.cs`
- Singleton controller for server lifecycle
- Start/Stop/Status management

### 3. Functions (`rhino_mcp_plugin/Functions/`)

Each file implements a specific Rhino operation:

| File | Purpose |
|------|---------|
| `CreateObject.cs` | Create single geometry (13 types supported) |
| `CreateObjects.cs` | Batch create multiple objects |
| `ModifyObject.cs` | Modify existing object properties |
| `ModifyObjects.cs` | Batch modify |
| `DeleteObject.cs` | Delete by ID or name |
| `GetDocumentInfo.cs` | Fetch document state (limited to 30 items) |
| `GetObjectInfo.cs` | Get single object details |
| `GetSelectedObjectsInfo.cs` | Get currently selected objects |
| `SelectObjects.cs` | Select by filters (name, color, attributes) |
| `CreateLayer.cs` | Create new layer |
| `DeleteLayer.cs` | Delete layer |
| `GetOrSetCurrentLayer.cs` | Get/set active layer |
| `ExecuteRhinoscript.cs` | Execute Python code in Rhino |
| `_utils.cs` | Helper methods for transforms |

### 4. Serializer (`rhino_mcp_plugin/Serializers/Serializer.cs`)

Converts Rhino geometry objects to JSON for client consumption:

```csharp
RhinoObject → JObject {
  "id": "guid-string",
  "name": "ObjectName",
  "type": "POINT|LINE|CURVE|BREP|...",
  "layer": "LayerName",
  "color": {"r": 255, "g": 0, "b": 0},
  "bounding_box": [[min_x, min_y, min_z], [max_x, max_y, max_z]],
  "geometry": { /* type-specific data */ }
}
```

---

## MCP Tools Reference

16 primary tools exposed to AI agents:

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `create_object` | Create single geometry | type, name, color, params, translation, rotation, scale |
| `create_objects` | Batch create | List of object specs |
| `modify_object` | Edit object | id/name, new_name, color, transforms |
| `modify_objects` | Batch edit | List of modifications |
| `delete_object` | Remove object | id or name |
| `get_document_info` | Fetch document state | None (returns up to 30 objects/layers) |
| `get_object_info` | Get object details | id or name |
| `get_selected_objects_info` | Get selection | None |
| `select_objects` | Select by filters | filters (name, color, attributes), filter_type (and/or) |
| `create_layer` | New layer | name, color, locked |
| `delete_layer` | Remove layer | name |
| `get_or_set_current_layer` | Active layer | get_only flag, name (for set) |
| `execute_rhinoscript_python_code` | Run Python in Rhino | code string |
| `get_rhinoscript_python_function_names` | List RhinoScript functions | None |
| `get_rhinoscript_python_code_guide` | Get function documentation | function_name |

---

## Supported Geometry Types

13 geometric primitives (defined in `CreateObject.cs`):

| Type | Parameters | Description |
|------|------------|-------------|
| `POINT` | x, y, z | Single point |
| `LINE` | start [x,y,z], end [x,y,z] | Two endpoints |
| `POLYLINE` | points [[x,y,z], ...] | Connected points |
| `CIRCLE` | center [x,y,z], radius | Circle on XY plane |
| `ARC` | center, radius, start_angle, end_angle (degrees) | Arc segment |
| `ELLIPSE` | center, radius_x, radius_y | Ellipse on XY plane |
| `CURVE` | control_points, degree | B-spline curve |
| `BOX` | width, length, height | Rectangular box |
| `SPHERE` | radius | Sphere at origin |
| `CONE` | radius, height, cap (bool) | Cone |
| `CYLINDER` | radius, height, cap (bool) | Cylinder |
| `PIPE` | (documented, implementation varies) | Pipe along curve |
| `SURFACE` | points (grid), u_degree, v_degree, u_closed, v_closed | NURBS surface |

---

## Object Transformations

`_utils.cs` provides transformation utilities applied after object creation:

```csharp
applyTranslation(geometry, translation)  // Move along vector [x, y, z]
applyRotation(geometry, rotation)        // Rotate around center (X, Y, Z angles in radians)
applyScale(geometry, scale)              // Scale from bounding box min (non-uniform [x, y, z])
```

**Application Order:** Translation → Rotation → Scale

---

## Communication Protocol

### TCP Socket (JSON-based)

**Command (Client → Server):**
```json
{
  "type": "command_type",
  "params": { /* command-specific parameters */ }
}
```

**Response (Server → Client):**
```json
{
  "status": "success",
  "result": { /* data */ }
}
// or
{
  "status": "error",
  "message": "error description"
}
```

### Socket Parameters
- **Host:** `127.0.0.1`
- **Port:** `1999`
- **Timeout:** 15 seconds
- **Buffer:** 8192 bytes (chunked reading)

---

## Configuration

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:
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

### Cursor IDE

`.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "rhino": {
      "command": "uv",
      "args": ["--directory", "/path/to/rhino_mcp_server", "run", "main.py"]
    }
  }
}
```

---

## Startup Sequence

1. Start Rhino desktop application
2. In Rhino command line, run: `mcpstart`
3. Rhino plugin launches TCP server on port 1999
4. Start Claude Desktop or Cursor
5. MCP connects via configured command
6. Python server connects to Rhino plugin
7. Ready to receive AI tool calls

---

## Build & Publishing

### Python MCP Server

**Workflow:** `.github/workflows/mcp-server-publish.yml`
- Triggered on GitHub release
- Builds Python package with `python -m build`
- Publishes to PyPI using trusted publishing
- Install: `uvx rhinomcp`

### Rhino Plugin

**Workflow:** `.github/workflows/rhino-plugin-publish.yml`
- Triggered on GitHub release
- Builds .NET 7.0 solution with MSBuild
- Outputs `.rhp` (Rhino plugin) file
- Packages as `.yak` file using Yak CLI
- Publishes to Rhino Package Manager

### Development Commands

**Python:**
```bash
cd rhino_mcp_server
./dev.sh  # Runs: uv venv && uv run mcp dev main.py:mcp
```

**C# Plugin:**
- Built with Visual Studio/Rider targeting net7.0
- Post-build copies to Rhino applications folder

---

## Dependencies

### Python (`pyproject.toml`)
- **fastmcp** >= 2.11.2 (MCP server framework)
- **mcp** >= 1.12.4 (MCP CLI support)
- Python >= 3.10

### C# (`.csproj`)
- **RhinoCommon** 8.17.25066.7001 (Rhino SDK)
- **Newtonsoft.Json** 13.0.3 (JSON serialization)
- **.NET SDK** 7.0

---

## Important Implementation Notes

### Performance Optimizations
1. **Document Info Limiting:** Only fetches first 30 objects/layers to prevent overwhelming AI context
2. **Global Connection Reuse:** Single persistent TCP connection across tool calls
3. **Thread Management:** Rhino operations run on main UI thread via `InvokeOnUiThread`
4. **Chunked JSON Reading:** Handles large responses in multiple TCP packets

### Threading Model
- Python server: Async/sync hybrid, single connection
- Rhino plugin: Multi-threaded client handling, UI thread execution
- All Rhino API calls must be on UI thread (enforced by `InvokeOnUiThread`)

### Error Handling
- Socket disconnection triggers automatic reconnection
- Commands wrapped in try-catch with JSON error responses
- Undo records created for all modifications

### Limitations
- Single MCP server instance only (one AI client at a time)
- Document info limited to 30 items (by design)
- Script execution is experimental
- Only primitive geometries supported (no complex assemblies)

---

## Key Files Quick Reference

| Purpose | Python File | C# File |
|---------|-------------|---------|
| Main entry | `main.py` | `RhinoMCPPlugin.cs` |
| Server/Connection | `server.py` | `RhinoMCPServer.cs` |
| Create objects | `tools/create_object.py` | `Functions/CreateObject.cs` |
| Modify objects | `tools/modify_object.py` | `Functions/ModifyObject.cs` |
| Delete objects | `tools/delete_object.py` | `Functions/DeleteObject.cs` |
| Document info | `tools/get_document_info.py` | `Functions/GetDocumentInfo.cs` |
| Object info | `tools/get_object_info.py` | `Functions/GetObjectInfo.cs` |
| Selection | `tools/select_objects.py` | `Functions/SelectObjects.cs` |
| Layers | `tools/create_layer.py` | `Functions/CreateLayer.cs` |
| Scripting | `tools/execute_rhinoscript_python_code.py` | `Functions/ExecuteRhinoscript.cs` |
| Utilities | - | `Functions/_utils.cs` |
| Serialization | - | `Serializers/Serializer.cs` |

---

## Version History (Recent)

- **0.1.3.6** - Latest release
- **0.1.3.5** - Bug fixes
- **0.1.3.4** - Added Arc, Ellipse, Cone, Cylinder, Surface geometry types
- **0.1.3.3** - User attributes support
- **0.1.3.2** - Build fixes
- **0.1.2.2** - Attributes filtering for selection

---

*Last updated: February 2026*
