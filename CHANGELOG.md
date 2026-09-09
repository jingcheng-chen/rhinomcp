# Changelog

Server and plugin share one version. Update them together: the server sends
commands the matching plugin understands, and an older plugin silently ignores
parameters it does not know.

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
- Newtonsoft.Json 13.0.4.

### Experiments harness (contributors)

- Gateways moved to SDK 2.x; the native pilot registers low-level handlers and
  returns gateway rejections as tool errors as before. Recorded catalogs keep the
  camelCase wire format. Comparisons against runs recorded before this change
  must use their archived sources.

## 0.3.2 and earlier

See the GitHub releases for earlier versions.
