# Changelog

Server and plugin share one version. Update them together: the server sends
commands the matching plugin understands, and an older plugin silently ignores
parameters it does not know.

## 0.5.1 — unreleased (prepared 2026-11-07)

A patch found by harness milestone M7 (25 runs on 0.5.0, see
`experiments/workflow/M7.md`): four of the seven flagged runs were agents
listing a layer they were about to create.

### Plugin

- `get_objects` with a `layer_filter` naming a layer that does not exist
  returns an empty listing again, as it did before 0.5.0, instead of refusing
  with `not_found`. `select_objects` keeps refusing an unknown `layer`, since
  selecting on a missing layer is a mistake rather than a look-ahead.

## 0.5.0 — unreleased (prepared 2026-11-07)

A perception release: agents can ground themselves before the first edit, see
what a viewport capture shows, point the camera, filter selections and listings
more precisely, and get errors that say what to try next. Everything is
additive; against a plugin older than 0.5.0 the server refuses the new commands
and parameters with update advice instead of letting them be ignored.

### Server (`rhinomcp` on PyPI)

- Coded errors with guidance. A failure now reads `code: message`, with one
  sentence of guidance on the next line. Codes come from a closed set:
  `invalid_argument`, `not_found`, `unsupported`, `rhino_error`, `timeout`,
  `internal`. Socket timeouts raise `timeout`; plugin-too-old refusals from the
  version tables raise `unsupported` with the update advice as guidance. Errors
  without a code stay valid and read as the bare message.
- Tool wrappers that used to return error text as a successful result
  (`create_layer`, `create_objects`, `delete_layer`, `get_commands`,
  `get_document_summary`, `get_objects`, `get_or_set_current_layer`,
  `get_selected_objects_info`, `modify_objects`, `run_command`,
  `select_objects`, `undo`, `redo`) now raise a real tool error.
- Complete tool annotations: every tool, the Grasshopper family included, has a
  title, a read-only hint and a destructive hint. A registry test fails when a
  new tool ships without them.
- New `get_context` tool: one bounded, read-only snapshot of the document
  (name, path, units, absolute and angle tolerance), the current layer and layer
  count, object count with the top eight types, selection count with the first
  twenty ids, the active viewport's name, projection, display mode and camera,
  the scene bounding box, and the number of open Grasshopper definitions.
  `get_document_summary` is unchanged. Requires plugin 0.5.0.
- `capture_viewport` returns the image followed by a text block of metadata:
  viewport name, display mode, projection, image size, camera location, target
  and up, lens length, scene bounding box, visible and total object counts.
  **The result is now an image plus text instead of a bare image.** New
  parameters: `display_mode`, `camera_location`, `camera_target`,
  `lens_length`, `frame_object_ids`, `frame_bbox` and `format` (`png`, the
  default, or `jpeg`). Size defaults are unchanged. Requires plugin 0.5.0.
- New `set_camera` tool (location, target, up, lens length, perspective or
  parallel projection) and `zoom_to` tool (all objects, the selection, object
  ids or a layer). Both change the view, create no undo record and are
  annotated not read-only. Require plugin 0.5.0.
- `select_objects` filters gain `ids`, `layer`, `type`, `hidden` and `locked`,
  combined with the existing name, color and custom-attribute filters under the
  same and/or rule. The result says how many matched objects Rhino could not
  select because they are hidden or locked. Requires plugin 0.5.0.
- `get_objects` gains `ids`, `selected_only`, `include_hidden` and
  `include_locked`. `include_locked` defaults to true and `include_hidden` to
  false, so a call without them lists what it listed before. Requires plugin
  0.5.0.
- Server instructions and the `overview` and `verification` guides tell agents
  to call `get_context` before the first edit, read capture metadata before
  trusting a picture, and act on error guidance instead of retrying.
  `guidance_version` is now 3.
- Version tables: `get_context`, `set_camera` and `zoom_to` in
  `COMMANDS_SINCE`; the seven `capture_viewport`, five `select_objects` filter
  and four `get_objects` parameters in `PARAMS_SINCE`.

### Plugin (`rhinomcp` on Yak)

- Error replies carry `code` and `guidance`. Unknown objects and layers return
  `not_found`; malformed GUIDs and out-of-range material index, pipe radius and
  curve degree return `invalid_argument`.
- `get_context`, `set_camera` and `zoom_to` commands. `get_context` only
  reads; `set_camera` and `zoom_to` change the view, create no undo record and
  are annotated not read-only.
- `capture_viewport` applies display mode, camera, lens and framing only for
  the capture and restores the viewport afterwards. An explicit camera
  (`camera_location`, `camera_target` or `lens_length`) combined with framing
  (`frame_object_ids`, `frame_bbox` or `zoom_to_fit`), or an unknown display
  mode, is refused with `invalid_argument`; unknown frame ids with
  `not_found`. A degenerate framing box is padded as `zoom_to` pads it. JPEG
  output.
- `select_objects` and `get_objects` honour the new filters; an unknown id or
  layer in a filter is refused with `not_found`.
- Several Rhino instances can run a bridge at the same time. `mcpstart` takes
  the first free port from 1999 to 2008; `-mcpstart Port=<n>` or the
  `RHINO_MCP_PORT` environment variable pin one. A taken port is reported and
  nothing starts, instead of an exception. The port is printed and, on
  Windows, prefixed to the Rhino window title.
- `mcpstatus` command: port, how it was chosen, document, connected clients
  and their latest command.
- Windows tray icon (`RhinoMCPTray.exe`, shipped next to the plug-in and
  started by `mcpstart`): one window listing every Rhino running a server,
  with port, matching MCP entry, Rhino/Grasshopper documents and connected
  clients, named after the client process (e.g. the Claude Code session and
  its working folder). `mcpwindow` opens it; clicking an instance brings that
  Rhino to the front.
- `mcpstop` closes open client connections immediately.

### Behaviour changes

- A plugin error no longer closes the socket; the next command reuses the
  connection.
- `get_or_set_current_layer` returns `not_found` for an unknown layer instead of
  silently falling back to the current layer.
- `delete_layer` returns `not_found` for an unknown layer instead of a
  `success: false` result.
- An unknown `layer_filter` in `get_objects` returns `not_found` instead of an
  empty listing.

### Claude Code plugin

- The repository is a Claude Code plugin marketplace. The `rhinomcp` plugin
  adds `rhino-modeler`, `rhino-inspector` and `grasshopper-builder` agents, a
  `/scene` command that calls `get_context` and a `/snapshot [display mode]`
  command that captures the viewport. Install with
  `claude plugin marketplace add jingcheng-chen/rhinomcp` and
  `claude plugin install rhinomcp@rhinomcp`; the MCP server is configured
  separately as `rhino`.

### Deferred

- Document open/save/close, multi-instance targeting from the server,
  `set_layer_material`, per-turn undo grouping, Rhino 9 / Grasshopper 2,
  coercion notes on success responses, coding the remaining error sites, the
  30-item caps in `get_document_summary`, and the in-Rhino chat panel,
  `ask_user` tool and Claude Desktop connector bundle.

## 0.4.1.1 — unreleased (prepared 2026-09-13)

### Fixed

- Normalize numeric negative zero in plugin results before response validation
  and MCP output. Strict clients can now consume geometry containing `-0.0`
  without rejecting an already-completed operation (#57). Nonzero measurements
  and strings are preserved. The fix works with existing plugins; raw TCP
  responses are unchanged.
- Version compatibility checks retain nonzero fourth components, distinguishing
  patch revision `0.4.1.1` from `0.4.1`.

## 0.4.1 — unreleased (prepared 2026-09-10)

### Fixed

- `get_object_info` guidance now names the accepted `id` and `name` selectors,
  states that at least one is needed, and explains ID precedence and discovery.
  The signature, response and execution behavior are unchanged.
- `update_object_attributes` works again with the Newtonsoft assembly loaded by
  Rhino 8. A missing overload prevented all updates in 0.4.0, including calls that
  only changed an object's layer. This was a 0.4.0 regression; see Changed below.
- Attribute edits use a detached copy before committing, preserving existing and
  newly assigned user strings. Scalar encoding, null deletion and validation stay
  unchanged; no wire-contract change is required.

### Changed

- Newtonsoft.Json is pinned to 13.0.3, the version Rhino 8 bundles and loads
  before any plugin. 0.4.0 compiled against 13.0.4, whose new
  `JToken.ToString(Formatting)` overload the compiler chose for an unchanged call;
  Rhino's 13.0.3 has no such overload, so every attribute update failed at runtime.
  Compiling against the bundled version keeps that class of mismatch impossible.

## 0.4.0 — unreleased (prepared 2026-09-09)

### Fixed: fresh installs of 0.3.2 fail to start

`rhinomcp 0.3.2` on PyPI declares `mcp[cli]>=1.16.0` with no upper bound. Since
MCP Python SDK 2.0 (2026-07-28) removed `mcp.server.fastmcp`, a new `uvx rhinomcp`
install resolves the 2.x SDK and fails at import. 0.4.0 moves the server to the
2.x API (`mcp>=2.0.0,<3`) instead of pinning the retired 1.x line.

### Server (`rhinomcp` on PyPI)

- MCP Python SDK 2.x. The tool catalog, prompts, resources and instructions are
  unchanged for clients; no client configuration changes are needed.
- Tool errors keep their text. SDK 2.x reports an unexpected tool exception to
  the client as only `Error executing tool <name>`; RhinoMCP re-raises failures
  as `ToolError` so messages such as "start Rhino and run `mcpstart`" still reach
  the agent.
- Version compatibility guard. The server reads the plugin's version once per
  connection and warns when the two differ; `describe_capabilities` now also
  reports `server_version`, `plugin_matches_server` and `update_advice`. A
  command the connected plugin does not support fails with update instructions
  instead of a bare "Unknown command type", and a parameter an older plugin would
  silently ignore (`sweep1.cap_planar_ends`) is refused rather than dropped.
- Client configuration in the README now launches `uvx rhinomcp@latest`, so the
  server is re-resolved on every client start instead of staying on the first
  version uv downloaded. See "Staying up to date" in the README.
- New `create_planar_region` tool: builds a planar face from closed boundary
  curves, with inner boundaries as holes. Requires plugin 0.4.0.
- New `get_modeling_guidance` tool, the `rhinomcp://guidance/{topic}` resource and
  six packaged guides (`overview`, `transforms`, `planar_regions`, `organization`,
  `verification`, `recovery`). The `asset_general_strategy` prompt and the server
  instructions use the same packaged content. No experiment checkout or separate
  skill is required.
- `sweep1` gains `cap_planar_ends` (default off). Requires plugin 0.4.0; an older
  plugin ignores the flag and returns uncapped surfaces.
- `create_layer`: `parent` accepts an exact full path such as `Assembly::Left`;
  a simple name must identify exactly one layer. Missing or ambiguous parents
  return errors instead of creating a mislocated layer (plugin 0.4.0).
- `capture_viewport`: `zoom_to_fit` fits visible objects to the requested image
  size, and the original camera and projection are restored afterwards
  (plugin 0.4.0).
- `analyze_objects`: `naked_edge_count` counts all naked topological edges,
  including inner hole boundaries (plugin 0.4.0; 0.3.2 reports outer edges only).
- `create_object` documents anchor points (centered boxes, base-anchored
  cylinders); `modify_object` documents its pivot and transform order.
- Development: dependencies refreshed to current releases; the lint rule set is
  pinned in the root `ruff.toml` because ruff 0.16 widened its defaults.

### Plugin (`rhinomcp` on Yak)

- `create_planar_region` command with coplanarity and planar-face checks.
- `sweep1`: optional planar-end capping at document tolerance. Every result must
  become a valid solid before any is added; otherwise the command fails without
  changing the document.
- `create_layer`: parent lookup by full path or unique name, with explicit
  not-found and ambiguous-name errors.
- `capture_viewport`: snapshots every viewport before refreshing or fitting and
  restores camera, target and projection without another redraw; finishes queued
  redraws on Mac before capturing.
- `analyze_objects`: Brep naked edges are counted from edge valence, so inner
  loops are included and seams are not.
- Newtonsoft.Json 13.0.4 (reverted in 0.4.1: Rhino 8 loads its own 13.0.3).

### Experiments harness (contributors)

- Gateways moved to SDK 2.x; the native pilot registers low-level handlers and
  returns gateway rejections as tool errors as before. Recorded catalogs keep the
  camelCase wire format. Comparisons against runs recorded before this change
  must use their archived sources.

## 0.3.2 and earlier

See the GitHub releases for earlier versions.
