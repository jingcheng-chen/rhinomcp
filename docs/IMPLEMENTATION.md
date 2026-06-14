# RhinoMCP - Implementation Details

This document is a source-oriented reference for the RhinoMCP codebase. It is
intended for agents and contributors who need to understand how the Python MCP
server, JSON contracts, and Rhino/Grasshopper plugin fit together without
reading every source file first.

## Project Overview

RhinoMCP connects AI clients to Rhino 3D and Grasshopper through the Model
Context Protocol (MCP).

- **Author:** Jingcheng Chen
- **License:** MIT
- **Repository:** https://github.com/jingcheng-chen/rhinomcp

The runtime bridge is:

```text
AI client -> Python FastMCP server -> TCP JSON on 127.0.0.1:1999 -> Rhino C# plugin -> Rhino + Grasshopper
```

The Python server exposes MCP tools. Each tool sends a JSON command to the Rhino
plugin. The plugin executes the command on Rhino's UI thread, then returns a JSON
result to the Python server.

## Architecture

```text
+-------------------------------------------------------------+
| AI Clients                                                  |
| Claude, Cursor, Claude Desktop, custom MCP clients          |
+--------------------+----------------------------------------+
                     |
                     | MCP, normally stdio for local clients
                     v
+--------------------+----------------------------------------+
| Python MCP Server (server/)                                |
| - FastMCP tool and resource registration                    |
| - Thin tool wrappers                                        |
| - Optional JSON Schema pre-flight validation                |
| - Persistent TCP connection to Rhino                        |
+--------------------+----------------------------------------+
                     |
                     | TCP JSON protocol
                     | 127.0.0.1:1999
                     v
+--------------------+----------------------------------------+
| Rhino Plugin (plugin/)                                     |
| - Rhino command lifecycle: mcpstart, mcpstop, mcptest       |
| - TCP listener inside Rhino                                |
| - Reflection dispatch via [McpCommand] handlers             |
| - Rhino and Grasshopper execution on the UI thread          |
+--------------------+----------------------------------------+
                     |
                     v
              Rhino document and Grasshopper document
```

### Data Flow

```text
MCP tool call
  -> @mcp.tool Python wrapper
  -> RhinoConnection.send_command(command_type, params)
  -> {"type": command_type, "params": {...}}
  -> RhinoMCPServer.ExecuteCommandInternal(...)
  -> RhinoMCPFunctions handler tagged with [McpCommand]
  -> {"status": "success", "result": {...}} or {"status": "error", "message": "..."}
```

## Directory Structure

```text
rhinomcp/
+-- server/                         # Python package published as rhinomcp
|   +-- main.py                      # Local entry point
|   +-- pyproject.toml               # Python package metadata
|   +-- dev.sh                       # Development runner
|   +-- tests/                       # Pytest tests and mock Rhino server
|   +-- src/rhinomcp/
|       +-- __init__.py              # Auto-discovers tool modules
|       +-- server.py                # FastMCP app and TCP connection manager
|       +-- validation.py            # Contract validation helper
|       +-- prompts/                 # MCP prompts
|       +-- static/                  # RhinoScript reference data
|       +-- tools/                   # MCP tool wrappers
|           +-- create_object.py
|           +-- create_objects.py
|           +-- modify_object.py
|           +-- modify_objects.py
|           +-- delete_object.py
|           +-- get_document_summary.py
|           +-- get_objects.py
|           +-- get_object_info.py
|           +-- object_attributes.py
|           +-- analyze_objects.py
|           +-- capture_viewport.py
|           +-- boolean_operations.py
|           +-- curve_operations.py
|           +-- advanced_geometry.py
|           +-- execute_rhinoscript_python_code.py
|           +-- execute_rhinocommon_csharp_code.py
|           +-- run_command.py
|           +-- undo.py
|           +-- grasshopper_document.py
|           +-- grasshopper_catalog.py
|           +-- grasshopper_components.py
|           +-- grasshopper_connections.py
|           +-- grasshopper_parameters.py
|           +-- grasshopper_solution.py
|           +-- grasshopper_build.py
|           +-- grasshopper_mutation.py
|           +-- grasshopper_graph.py
|
+-- plugin/                         # RhinoCommon plugin
|   +-- rhinomcp.csproj              # .NET 8 plugin project
|   +-- rhinomcp.sln                 # Plugin solution
|   +-- manifest.yml                 # Yak package manifest
|   +-- Commands/
|   |   +-- MCPStartCommand.cs
|   |   +-- MCPStopCommand.cs
|   |   +-- MCPTestCommand.cs
|   |   +-- MCPVersionCommand.cs
|   +-- Functions/
|   |   +-- _Registry.cs             # Reflection dispatch table
|   |   +-- _utils.cs                # Shared Rhino helpers
|   |   +-- CreateObject.cs
|   |   +-- CreateObjects.cs
|   |   +-- ModifyObject.cs
|   |   +-- ModifyObjects.cs
|   |   +-- GetDocumentSummary.cs
|   |   +-- GetObjects.cs
|   |   +-- ObjectAttributes.cs
|   |   +-- BooleanOperations.cs
|   |   +-- CurveOperations.cs
|   |   +-- AdvancedGeometry.cs
|   |   +-- ExecuteRhinoscript.cs
|   |   +-- ExecuteRhinoCommonCSharp.cs
|   |   +-- GrasshopperDocument.cs
|   |   +-- GrasshopperCatalog.cs
|   |   +-- GrasshopperComponents.cs
|   |   +-- GrasshopperConnections.cs
|   |   +-- GrasshopperParameters.cs
|   |   +-- GrasshopperSolution.cs
|   |   +-- GrasshopperBuild.cs
|   |   +-- GrasshopperMutation.cs
|   |   +-- GrasshopperGraph.cs
|   |   +-- GrasshopperHelpers.cs
|   |   +-- GrasshopperGraphHelpers.cs
|   |   +-- TestAllFunctions.cs
|   |   +-- TestGrasshopperFunctions.cs
|   +-- Serializers/
|   |   +-- Serializer.cs
|   +-- McpCommandAttribute.cs
|   +-- RhinoMCPPlugin.cs
|   +-- RhinoMCPServer.cs
|   +-- RhinoMCPServerController.cs
|
+-- contracts/                      # JSON protocol contracts
|   +-- protocol.json                # Command envelope and command enum
|   +-- commands/                    # Per-command parameter schemas
|   +-- responses/                   # Shared response schemas
|   +-- common/definitions.json      # Shared schema definitions
|   +-- test_schemas.py              # Schema coverage and validation tests
|
+-- docs/
|   +-- assets/                      # README images, logo, screenshots
|   +-- demo_chats/                  # Example AI conversations
+-- README.md
+-- IMPLEMENTATION.md
```

## Contracts and Protocol

The protocol is contracts-first. `contracts/protocol.json` defines the command
envelope and the complete command enum. Every command should also have a schema
under `contracts/commands/<command>.json`.

### Command Envelope

```json
{
  "type": "command_name",
  "params": {
    "command_specific": "payload"
  }
}
```

### Response Envelope

```json
{
  "status": "success",
  "result": {}
}
```

or:

```json
{
  "status": "error",
  "message": "error description"
}
```

The plugin always returns the envelope. The Python `RhinoConnection` unwraps
successful responses and raises an exception for `status: error`.

### Change Delta (Perception)

When `RHINO_MCP_PERCEPTION` is enabled, the Python server adds an envelope-level
`include_delta` flag to every command, and the plugin attaches a `_delta` block
to the `result` of each mutating (non-ReadOnly) command:

```json
{
  "status": "success",
  "result": {
    "...": "normal command result",
    "_delta": {
      "created_count": 1,
      "deleted_count": 0,
      "count_before": 3,
      "count_after": 4,
      "created_ids": ["..."],
      "deleted_ids": ["..."],
      "truncated": false
    }
  }
}
```

The delta is computed once at the dispatch choke point (`ExecuteCommandInternal`)
by diffing the document's object id set before and after the handler, so it
covers every mutating command, including multi-effect ones like `run_command`
and booleans with `delete_sources`. The counts are exact set differences; there
is no modified count because an in-place transform reuses the same id. To keep a
single operation over a large model from flooding the client's context, the
`created_ids` / `deleted_ids` arrays are included only when their count is within
`DeltaIdListCap` (50); past that they are omitted and `truncated` is set, while
the counts stay exact. This follows the summarize-don't-enumerate approach
`get_document_summary` takes. The flag rides on the envelope rather than in
`params` so it never collides with a command's parameters or trips params
validation. It is off by default, so responses are byte-identical unless
enabled. See `contracts/responses/change_delta.json`.

### Schema Validation

`server/src/rhinomcp/validation.py` validates tool parameters against
`contracts/commands/` before a TCP send when validation is enabled.

Environment variable:

| Variable             | Default | Behavior                                                                      |
| -------------------- | ------- | ----------------------------------------------------------------------------- |
| `RHINO_MCP_VALIDATE` | `warn`  | `off`, `warn`, or `strict`. In strict mode, invalid params never reach Rhino. |

The contract test script is:

```bash
python contracts/test_schemas.py
```

## Python Server

Main file: `server/src/rhinomcp/server.py`

### Responsibilities

- Creates the FastMCP server: `mcp = FastMCP("RhinoMCP", lifespan=server_lifespan)`.
- Manages a persistent `RhinoConnection` to the plugin.
- Serializes concurrent tool calls with a socket send lock.
- Validates command params when `RHINO_MCP_VALIDATE` is not `off`.
- Provides actionable startup errors when Rhino or `mcpstart` is not running.
- Exposes RhinoScript documentation resources:
  - `rhinoscript://modules`
  - `rhinoscript://module/{module_name}`
  - `rhinoscript://function/{function_name}`

### Connection Settings

| Variable                 | Default           | Effect                                                                      |
| ------------------------ | ----------------- | --------------------------------------------------------------------------- |
| `RHINO_MCP_HOST`         | `127.0.0.1`       | TCP host. Non-loopback hosts are refused unless explicitly allowed.         |
| `RHINO_MCP_PORT`         | `1999`            | TCP port.                                                                   |
| `RHINO_MCP_ALLOW_REMOTE` | unset             | Set to `1` only if accepting unauthenticated remote command execution risk. |
| `RHINO_MCP_TIMEOUT`      | `15.0`            | Socket timeout in seconds.                                                  |
| `RHINO_MCP_PERCEPTION`   | unset             | Set truthy to attach a `_delta` change block to mutating-command results.   |
| `RHINO_MCP_DEBUG`        | unset             | Enables verbose logging when truthy.                                        |
| `RHINO_MCP_LOG_LEVEL`    | `INFO` or `DEBUG` | Explicit Python logging level.                                              |

### Tool Registration

`server/src/rhinomcp/__init__.py` auto-imports all modules in
`server/src/rhinomcp/tools/` except files whose names start with `_`.

Each tool module registers functions with `@mcp.tool()` when imported. Most
wrappers are intentionally thin:

```python
@mcp.tool()
def gh_run_solution(ctx: Context, recompute: bool = True) -> Dict[str, Any]:
    return send_grasshopper_command("gh_run_solution", {"recompute": recompute})
```

This keeps Rhino and Grasshopper document logic in the C# plugin, where the
native APIs are available.

## Rhino Plugin

Main files:

- `plugin/RhinoMCPPlugin.cs`
- `plugin/RhinoMCPServer.cs`
- `plugin/RhinoMCPServerController.cs`
- `plugin/McpCommandAttribute.cs`
- `plugin/Functions/_Registry.cs`

### Lifecycle Commands

| Rhino command                | Purpose                                                               |
| ---------------------------- | --------------------------------------------------------------------- |
| `mcpstart`                   | Start the TCP listener on `127.0.0.1:1999`.                           |
| `mcpstop`                    | Stop the TCP listener.                                                |
| `mcpstatus`                  | Report listener status.                                               |
| `mcptest` / `MCPTestCommand` | Run in-Rhino handler tests, including Grasshopper tests when enabled. |
| `mcpversion`                 | Report plugin version.                                                |

### TCP Server

`RhinoMCPServer` listens on loopback, accepts TCP clients, parses JSON command
objects, and executes every command through `RhinoApp.InvokeOnUiThread(...)`.
This is required because RhinoCommon and Grasshopper document APIs must run on
Rhino's main thread.

### Wire Framing

Messages in both directions are length-prefixed: a 4-byte big-endian size
header followed by that many bytes of UTF-8 JSON. This makes message
boundaries exact, so pipelined commands and back-to-back responses cannot be
misread, and frames split across TCP segments are read until complete.

The plugin stays compatible with older unframed clients by sniffing the first
byte of each connection: bare JSON (`{` or whitespace) selects the legacy
unframed protocol for that connection, while a frame header's first byte is
always below those values (frame sizes are capped at 64 MB). The bundled
Python server always speaks the framed protocol and reports an actionable
error if it detects an unframed (pre-framing) plugin.

### Handler Dispatch

Dispatch is reflection based. `RhinoMCPFunctions.GetDispatchTable()` scans
public instance methods decorated with `[McpCommand("command_name")]`.

```csharp
[McpCommand("get_document_summary", ReadOnly = true)]
public JObject GetDocumentSummary(JObject parameters)
{
    ...
}
```

`ReadOnly = true` tells the dispatcher not to create a Rhino undo record.
Mutating commands are wrapped in `doc.BeginUndoRecord($"MCP: {cmdType}")`.

To add a command, the implementation must stay in sync across:

1. `contracts/protocol.json`
2. `contracts/commands/<command>.json`
3. `server/src/rhinomcp/tools/<module>.py`
4. `plugin/Functions/<Feature>.cs` with `[McpCommand]`
5. Python tests, schema tests, and, where relevant, `MCPTestCommand`

## Command Surface

`contracts/protocol.json` defines 59 command types: 34 Rhino
commands and 25 Grasshopper commands.

### Rhino Commands

| Area                          | Commands                                                                                                                                              |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Object creation and edits     | `create_object`, `create_objects`, `modify_object`, `modify_objects`, `delete_object`                                                                 |
| Object and document query     | `get_document_summary`, `get_objects`, `get_object_info`, `get_selected_objects_info`, `get_object_attributes`, `analyze_objects`, `capture_viewport` |
| Object attributes             | `update_object_attributes`                                                                                                                            |
| Selection                     | `select_objects`                                                                                                                                      |
| Layers                        | `create_layer`, `delete_layer`, `get_or_set_current_layer`                                                                                            |
| Scripting and commands        | `run_command`, `get_commands`, `execute_rhinoscript_python_code`, `execute_rhinocommon_csharp_code`                                                   |
| Undo                          | `undo`, `redo`                                                                                                                                        |
| Booleans                      | `boolean_union`, `boolean_difference`, `boolean_intersection`                                                                                         |
| Curves and generated geometry | `loft`, `extrude_curve`, `sweep1`, `offset_curve`, `pipe`, `project_curve`, `intersect_curves`, `split_curve`                                         |

### Grasshopper Commands

| Area                  | Commands                                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Document and canvas   | `gh_create_document`, `gh_get_document_info`, `gh_get_canvas_state`, `gh_clear_canvas`                                                            |
| Component catalog     | `gh_search_components`, `gh_batch_search_components`, `gh_list_component_categories`, `gh_get_available_components`, `gh_get_component_type_info` |
| Canvas components     | `gh_list_components`, `gh_get_component_info`, `gh_add_component`, `gh_update_component`, `gh_delete_component`, `gh_layout_components`           |
| Connections           | `gh_connect_components`, `gh_disconnect_components`                                                                                               |
| Parameters and data   | `gh_set_parameter_value`, `gh_get_parameter_value`                                                                                                |
| Solutions             | `gh_run_solution`, `gh_expire_solution`                                                                                                           |
| Batch graph workflows | `gh_build_graph`, `gh_mutate_graph`, `gh_get_graph`, `gh_clear_graph`                                                                             |

## Grasshopper Implementation

Grasshopper support is split across Python wrapper modules and C# partial
handler files. The C# side uses Grasshopper's native `GH_Document`,
`IGH_DocumentObject`, `IGH_Component`, `IGH_Param`, and special component types.

### Document Handling

`GetActiveGrasshopperDocument(...)` in `GrasshopperHelpers.cs` resolves the
active canvas document, falls back to the document server, and can create a new
document when the command allows it. Batch commands such as `gh_build_graph` and
`gh_mutate_graph` call it with `createIfMissing: true`.

If Rhino itself is not running or the TCP listener is not active, the Python
server returns guidance telling the user to start Rhino and run `mcpstart`.

### Component Lookup

`GrasshopperCatalog.cs` searches `Instances.ComponentServer.ObjectProxies`.
Lookup supports:

- Common aliases such as `Slider` -> `Number Slider` and `Add` -> `Addition`.
- Lookup by component GUID.
- Exact name and nickname matching.
- Partial name and nickname fallback.
- Suggestions when type lookup fails.
- A session-local `GhComponentProxyCache` keyed by normalized name or GUID.

### Component State

Grasshopper component responses include standard component metadata plus richer
state for controls where possible:

- Number sliders: value, min, max, decimals.
- Boolean toggles: value.
- Panels: content.
- Value lists: selected item state.
- Graph metadata: `alias`, `graph_id`, `role`.

The metadata is stored on Grasshopper document objects with keys:

- `rhinomcp.alias`
- `rhinomcp.graph_id`
- `rhinomcp.role`

This lets later commands find generated graph objects without relying only on
Rhino-generated GUIDs.

### Single-Operation Commands

Single-operation tools exist for straightforward edits and inspection:

- Add, update, delete, list, and inspect components.
- Connect and disconnect parameters.
- Set and read parameter values.
- Run or expire a solution.
- Lay out canvas objects.

These are useful for small interactions. For larger graph creation or iterative
edits, prefer the batch APIs below to avoid many slow UI-thread round trips.

### `gh_build_graph`

`gh_build_graph` creates a new graph in one command. It accepts:

- `components`: required list of component specs, each with an alias.
- `connections`: optional alias-based wiring.
- `values`: optional value updates for sliders, toggles, panels, value lists, or params.
- `preview_updates` and `preview_policy`: optional preview control.
- `groups`: optional Grasshopper groups/labels.
- `layout`: optional automatic canvas layout.
- `graph_id`: optional ownership tag.
- `recompute`: whether to solve once after construction.
- `rollback_on_error`: remove created objects if construction fails.

The response includes created component and group counts, aliases to instance
IDs, timing metrics, preview/layout results, a graph summary, and the graph id.

### `gh_mutate_graph`

`gh_mutate_graph` applies multiple edits to an existing or new graph in one
command. Supported operation names are:

- `create`
- `connect`
- `set`
- `update`
- `disconnect`
- `delete`
- `recompute`

It also supports:

- Alias and graph-id selectors.
- Preview policy for new and existing components.
- Groups and layout.
- Verification of outputs.
- `fail_on_verification_error`, which turns failed verification into a tool error.
- Timing metrics: mutation, solution, verification, and total duration.
- Pragmatic rollback for created objects, added/removed wires, and captured
  object state snapshots when `rollback_on_error` is true.

Grasshopper does not expose a database-style transaction. Rollback is therefore
best-effort and command-scoped. Deleting existing objects has limited rollback
semantics compared with reverting property and connection changes.

### Graph Discovery

`gh_get_graph` and `gh_clear_graph` operate by `graph_id`. They are intended for
generated graph lifecycle workflows where the assistant should inspect, update,
or remove only the graph it created without clearing unrelated user work.

## Rhino Geometry Implementation

### Create Object

`CreateObject.cs` supports core primitives and curves, including:

| Type       | Description                                               |
| ---------- | --------------------------------------------------------- |
| `POINT`    | Single point.                                             |
| `LINE`     | Two-point line.                                           |
| `POLYLINE` | Connected point sequence.                                 |
| `CIRCLE`   | Circle.                                                   |
| `ARC`      | Arc segment.                                              |
| `ELLIPSE`  | Ellipse.                                                  |
| `CURVE`    | Interpolated or control-point curve, depending on params. |
| `BOX`      | Box Brep.                                                 |
| `SPHERE`   | Sphere.                                                   |
| `CONE`     | Cone.                                                     |
| `CYLINDER` | Cylinder.                                                 |
| `SURFACE`  | Surface from a point grid.                                |

`_utils.cs` provides shared transform helpers used by creation and modification
commands. The typical transform order is translation, rotation, then scale.

### Advanced Geometry

Additional handlers cover booleans, curve projection/intersection/splitting,
loft/extrude/sweep/offset/pipe operations, object analysis, viewport capture,
and object attribute reads/writes.

### Serialization

`plugin/Serializers/Serializer.cs` converts Rhino objects to JSON, including:

- Object id, name, type, layer, and color.
- Bounding boxes.
- Geometry-specific data where supported.
- Attributes and user strings where requested.

## Security Model

The Rhino plugin listens on an unauthenticated loopback TCP socket. The Python
server refuses non-loopback `RHINO_MCP_HOST` values unless
`RHINO_MCP_ALLOW_REMOTE=1` is set.

High-risk commands include:

- `run_command`
- `execute_rhinoscript_python_code`
- `execute_rhinocommon_csharp_code`

These commands are powerful by design. They should only be exposed to trusted
local MCP clients.

## Testing

### Python Tests

Run from `server/`:

```bash
uv run pytest
uv run pytest tests/test_tools.py
uv run pytest --cov=rhinomcp --cov-report=term-missing
```

The Python tests mock the Rhino connection and assert the exact command names
and params sent by tool wrappers.

### Schema Tests

Run from the repo root:

```bash
python contracts/test_schemas.py
```

The schema tests cover valid and invalid payloads and check that command schemas
stay aligned with the protocol enum.

### Plugin Tests

`MCPTestCommand` exercises C# handlers inside Rhino. Grasshopper tests are
included in `plugin/Functions/TestGrasshopperFunctions.cs` and cover document
creation, component catalog, component CRUD, wiring, solving, graph build,
mutation, graph discovery/clear, layout, parameter values, and cleanup.

For visible Grasshopper inspection, the test command can leave generated test
objects on the canvas instead of clearing them.

## Build and Publishing

### Python Server

Run from `server/`:

```bash
uv venv
uv pip install -e ".[dev]"
uv run pytest
uv run ruff check src/rhinomcp
uv run ruff format src/rhinomcp --check
uv build
```

The package entry point is:

```text
rhinomcp = rhinomcp.server:main
```

Published installs are intended to run with:

```bash
uvx rhinomcp
```

### Rhino Plugin

Run from the repo root:

```bash
dotnet restore plugin/rhinomcp.sln
dotnet build plugin/rhinomcp.sln --configuration Release
```

The Release build outputs the Rhino plugin under:

```text
plugin/bin/Release/net8.0/rhinomcp.rhp
```

On macOS, local install can use:

```bash
plugin/install.sh
```

or opt into the post-build copy target:

```bash
dotnet build plugin/rhinomcp.sln --configuration Release -p:CopyToRhinoPluginDir=true
```

### Release Workflows

| Workflow                                     | Purpose                                                         |
| -------------------------------------------- | --------------------------------------------------------------- |
| `.github/workflows/ci.yml`                   | Python tests, schema validation, lint, and plugin build checks. |
| `.github/workflows/mcp-server-publish.yml`   | Build and publish the Python package to PyPI.                   |
| `.github/workflows/rhino-plugin-publish.yml` | Build and publish the Yak package for Rhino Package Manager.    |

## Dependencies

### Python

Defined in `server/pyproject.toml`:

- Python `>=3.10`
- `mcp[cli]>=1.16.0`
- Optional validation/dev: `jsonschema`, `pytest`, `pytest-cov`, `pytest-asyncio`, `ruff`

### C#

Defined in `plugin/rhinomcp.csproj`:

- Target framework: `net8.0`
- `RhinoCommon` `8.17.25066.7001`
- `Grasshopper` `8.17.25066.7001`
- `Newtonsoft.Json` `13.0.3`
- `Microsoft.CodeAnalysis.CSharp.Scripting` `4.8.0`
- `System.Drawing.Common` `8.0.0`

## Implementation Notes

- The Python server keeps one persistent TCP connection and serializes sends with
  a lock to avoid request/response interleaving.
- Rhino and Grasshopper operations run on Rhino's UI thread.
- Read-only C# commands should use `[McpCommand(..., ReadOnly = true)]`.
- Mutating C# commands get Rhino undo records automatically through the dispatcher.
- Batch Grasshopper APIs suppress intermediate round trips and solve once when
  `recompute` is true.
- `gh_build_graph` and `gh_mutate_graph` return timing metrics to make round-trip
  and solution performance visible.
- Generated Grasshopper graphs should use a `graph_id` so future commands can
  update or clear only the generated objects.
