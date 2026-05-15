# RhinoMCP Implementation TODO

This file translates the May 2026 implementation review into delegable work packages. Each package should be implemented with Python wrappers, C# handlers, contracts, and tests kept in sync.

## Current Baseline

Verified locally:

- `uv run pytest` from `rhino_mcp_server/`: 96 passed.
- `uv run python ../contracts/test_schemas.py` from `rhino_mcp_server/`: passed.
- `dotnet build rhino_mcp_plugin/rhinomcp.sln --configuration Release`: plugin compiled, then failed on macOS post-build copy to `/Applications/Rhino 8.app/Contents/PlugIns/` due permissions.

Known build warnings:

- `LoftType.Developable` is obsolete.
- `System.Drawing.Common` APIs in `CaptureViewport.cs` are Windows-only warnings under .NET 8.
- NuGet vulnerability metadata lookup can fail when network is restricted.

## Delegation Rules

- Keep protocol changes atomic across:
  - `rhino_mcp_server/src/rhinomcp/tools/`
  - `rhino_mcp_plugin/Functions/`
  - `contracts/commands/`
  - `contracts/protocol.json`
  - tests in `rhino_mcp_server/tests/` and `contracts/test_schemas.py`
- Do not silently change tool names unless a compatibility shim is included.
- Prefer returning structured data from tools rather than formatted strings when downstream agents need object IDs.
- Tool errors should be real MCP tool errors, not successful string responses that start with `"Error ..."`.
- For destructive or arbitrary-code tools, document and test the safety behavior explicitly.

## P0: Correctness Bugs

### 1. Fix `select_objects` Filter Semantics

Problem:

- Python and schema document `filters.name` as an array of strings.
- C# currently converts the whole JSON array to one string and compares it to `obj.Name`.
- `and` semantics for custom attributes require a user string to equal every listed value, which makes multi-value lists impossible to match.

Files:

- `rhino_mcp_server/src/rhinomcp/tools/select_objects.py`
- `rhino_mcp_plugin/Functions/SelectObjects.cs`
- `contracts/commands/select_objects.json`
- `rhino_mcp_server/tests/test_tools.py`
- `rhino_mcp_server/tests/test_integration.py`
- `contracts/test_schemas.py`

Implementation notes:

- Treat `filters.name` as `List<string>`.
- For `and`: an object matches when each filter key matches at least one of that key's listed values.
- For `or`: an object matches when any filter key matches any listed value.
- Keep `color` as a single RGB triplet, or explicitly redesign it as a list of RGB triplets. If kept as a single triplet, update docs to stop saying every filter value is always a list.
- Reject invalid `filters_type` in C# instead of silently selecting zero objects.
- Add case-sensitivity policy for names and custom attributes. Default recommendation: exact match for now, documented.

Acceptance criteria:

- Selecting by `{"name": ["Box1"]}` selects `Box1`.
- Selecting by `{"name": ["Box1", "Box2"]}` with `filters_type="or"` selects both.
- Selecting by `{"category": ["wall", "floor"]}` with `filters_type="or"` selects objects with either value.
- Selecting by `{"name": ["Box1"], "category": ["wall"]}` with `filters_type="and"` requires both filters.
- Invalid `filters_type` produces an error.

Verification:

- `uv run pytest tests/test_tools.py::TestSelectObjectsTool`
- `uv run pytest tests/test_integration.py`
- `uv run python ../contracts/test_schemas.py`

### 2. Fix `delete_object(all=True)` Response Handling

Problem:

- C# returns only `{"deleted": true}` for delete-all.
- Python always reads `result["name"]`, so the tool reports an error after a successful delete-all.
- C# treats the presence of `"all"` as delete-all even when the value is `false`.

Files:

- `rhino_mcp_server/src/rhinomcp/tools/delete_object.py`
- `rhino_mcp_plugin/Functions/DeleteObject.cs`
- `contracts/commands/delete_object.json`
- `contracts/responses/delete_result.json`
- `rhino_mcp_server/tests/test_tools.py`
- `rhino_mcp_server/tests/test_integration.py`

Implementation notes:

- In C#, use `parameters["all"]?.ToObject<bool>() == true`.
- Return a consistent payload for delete-all, for example:
  - `deleted: true`
  - `count: <number deleted>`
  - `scope: "all"`
- In Python, branch the message for delete-all instead of assuming `name`.
- Consider rejecting calls with no `id`, no `name`, and no `all=true`.
- Add `additionalProperties: false` to `delete_object.json`.

Acceptance criteria:

- `delete_object(all=True)` returns a success message and includes deleted count where available.
- `delete_object(all=False)` does not delete everything.
- Calling with no selector returns a clear error.
- Schema rejects unknown properties.

Verification:

- `uv run pytest tests/test_tools.py::TestDeleteObjectTool`
- `uv run pytest tests/test_integration.py::TestDeleteObject`
- `uv run python ../contracts/test_schemas.py`

### 3. Align `create_object` Contract and C# Behavior

Problem:

- `PIPE` appears in `create_object.json` but is not implemented in `CreateObject.cs`.
- Cone/cylinder `cap` defaults differ: schema/docs imply `true`, C# defaults missing values to `false`.
- Curve `degree` is documented as defaultable but C# defaults missing value to `0`.
- Surface `degree`/`closed` are documented optional but C# defaults to invalid degree `[0,0]`.
- `params` is not schema-discriminated by `type`, so many invalid payloads pass.

Files:

- `contracts/commands/create_object.json`
- `rhino_mcp_server/src/rhinomcp/tools/create_object.py`
- `rhino_mcp_server/src/rhinomcp/tools/create_objects.py`
- `rhino_mcp_plugin/Functions/CreateObject.cs`
- `rhino_mcp_plugin/Functions/_utils.cs`
- `rhino_mcp_server/tests/test_tools.py`
- `rhino_mcp_server/tests/test_integration.py`
- `contracts/test_schemas.py`

Implementation options:

- Preferred: remove `PIPE` from `create_object` and keep pipe creation as the separate `pipe` tool.
- Alternative: implement `PIPE` in `CreateObject.cs` with a clear params shape and keep both APIs.

Required fixes:

- Default cone/cylinder `cap` to `true`.
- Default curve `degree` to `3`, but validate degree is valid for point count.
- Default surface `degree` to `[3, 3]` or a valid value constrained by `count`.
- Default surface `closed` to `[false, false]`.
- Replace broad helper defaults with explicit validation at command boundaries. Missing required geometry values should error, not become origin/zero.
- Use JSON Schema `oneOf`/`if`/`then` to tie `type` to the correct params schema.
- Add top-level `additionalProperties: false`.

Acceptance criteria:

- Valid primitive examples create objects successfully.
- Missing required params are rejected before Rhino tries to create invalid geometry.
- Cone/cylinder without `cap` create capped geometry.
- `PIPE` contract and C# implementation agree.
- Schema rejects `{"type": "BOX", "params": {"radius": 1}}`.

Verification:

- `uv run pytest tests/test_tools.py::TestCreateObjectTool`
- `uv run pytest tests/test_integration.py::TestCreateObject`
- `uv run python ../contracts/test_schemas.py`

### 4. Fix Object Lookup by Name Edge Cases

Problem:

- `getObjectByIdOrName` checks `objs == null`, but `ToList()` is never null.
- If no object matches a name, `objs[0]` throws an index error instead of a clear not-found error.
- Error messages mention ID even when lookup was by name.

Files:

- `rhino_mcp_plugin/Functions/_utils.cs`
- Any tests covering `get_object_info`, `modify_object`, `delete_object`.

Implementation notes:

- Check `objs.Count == 0` and throw `Object with name <name> not found`.
- Keep the multiple-name error.
- Use `Guid.TryParse` for IDs to return a clearer invalid GUID message.

Acceptance criteria:

- Missing name returns a clear not-found error.
- Duplicate names return the existing multiple-match error.
- Invalid GUID returns a clear invalid-guid error.

## P1: Contract Coverage and Runtime Validation

### 5. Add Missing Command Schemas

Problem:

`contracts/protocol.json` and C# expose 31 commands, but only 18 command schemas exist. Missing schemas:

- `boolean_union`
- `boolean_difference`
- `boolean_intersection`
- `create_objects`
- `execute_rhinocommon_csharp_code`
- `extrude_curve`
- `loft`
- `modify_objects`
- `offset_curve`
- `pipe`
- `redo`
- `sweep1`
- `undo`

Files:

- `contracts/commands/*.json`
- `contracts/test_schemas.py`
- `contracts/README.md`
- Matching Python tool files.
- Matching C# handler files.

Implementation notes:

- Add `additionalProperties: false` everywhere unless extensibility is intentional.
- Prefer shared definitions for GUID arrays and nonzero vectors.
- Add positive and negative schema examples.
- Ensure `protocol.json` enum, schema filenames, C# `[McpCommand]`, and Python `send_command` names all match.

Acceptance criteria:

- Every protocol command has a schema file.
- `contracts/test_schemas.py` verifies all protocol commands have schemas.
- Invalid examples are rejected for every new schema.

### 6. Wire Schema Validation into the Runtime Path

Problem:

- `rhinomcp.validation` exists but is not used in `RhinoConnection.send_command`.
- Missing/invalid tool arguments can pass through until C# throws late or silently defaults.

Files:

- `rhino_mcp_server/src/rhinomcp/server.py`
- `rhino_mcp_server/src/rhinomcp/validation.py`
- `rhino_mcp_server/pyproject.toml`
- tests in `rhino_mcp_server/tests/test_connection.py`

Implementation notes:

- Add env flag, for example `RHINO_MCP_VALIDATE=1`, defaulting to enabled if `jsonschema` is installed.
- Validate command params before sending.
- Optionally validate response envelopes after receiving.
- For commands without schemas during the transition, fail in CI but allow runtime fallback only if explicitly configured.
- `jsonschema.RefResolver` is deprecated in newer jsonschema. Move toward `referencing.Registry` if touching this module.

Acceptance criteria:

- Invalid `create_object` payload fails in Python before socket send.
- Unknown command fails before socket send.
- Tests cover validation enabled and disabled.

## P1: MCP Modernization

### 7. Return Structured Tool Results and Real Tool Errors

Problem:

- Many tools catch exceptions and return strings beginning with `"Error ..."`, which MCP clients treat as successful tool calls.
- Many tools discard IDs and structured result data needed by later tool calls.

Files:

- All files under `rhino_mcp_server/src/rhinomcp/tools/`
- `rhino_mcp_server/tests/test_tools.py`

Implementation notes:

- For failure, raise exceptions so FastMCP returns a tool error.
- Return dictionaries/lists for tools whose output is machine-readable.
- Keep short human messages inside a `message` field if useful.
- Candidate return shape:
  - `success: true`
  - `message: "..."`
  - command-specific IDs/results
- High-value tools to convert first:
  - `create_object`
  - `create_objects`
  - `modify_object`
  - `delete_object`
  - `select_objects`
  - `run_command`
  - script execution tools

Acceptance criteria:

- Failed socket communication surfaces as an MCP tool error.
- `create_object` returns the created object ID.
- Existing tests assert structured results, not only substrings.

### 8. Add Tool Annotations and Descriptions for Client UX

Problem:

- MCP clients increasingly use tool metadata to decide whether a tool is read-only, destructive, or open-world.
- The C# plugin has `[McpCommand(ReadOnly = true)]`, but Python MCP tool registration does not expose equivalent annotations.

Files:

- Tool modules under `rhino_mcp_server/src/rhinomcp/tools/`

Implementation notes:

- Use the current Python MCP SDK support for tool annotations where available.
- Mark read-only tools:
  - `get_document_summary`
  - `get_objects`
  - `get_object_info`
  - `get_selected_objects_info`
  - RhinoScript documentation tools
  - `capture_viewport`
  - `get_commands`
- Mark destructive/open-world tools:
  - `delete_object`
  - `delete_layer`
  - `run_command`
  - `execute_rhinoscript_python_code`
  - `execute_rhinocommon_csharp_code`

Acceptance criteria:

- Tool metadata reflects read-only/destructive behavior.
- Tests or a small introspection script verify annotations appear in the tool list.

### 9. Review FastMCP Dependency Choice

Problem:

- `pyproject.toml` depends on both `fastmcp>=2.14.5` and `mcp[cli]>=1.16.0`.
- Code imports from `mcp.server.fastmcp`, so the standalone `fastmcp` package appears unused.

Files:

- `rhino_mcp_server/pyproject.toml`
- `rhino_mcp_server/uv.lock`
- imports in `rhino_mcp_server/src/rhinomcp/`

Implementation notes:

- Decide whether to use official SDK FastMCP (`mcp.server.fastmcp`) or standalone FastMCP 2.x (`fastmcp`).
- If staying on official SDK, remove unused `fastmcp` dependency.
- If migrating to standalone FastMCP, update imports and verify behavior.
- Update docs to avoid ambiguity.

Acceptance criteria:

- Only one MCP server framework dependency remains unless there is a documented reason.
- `uv run pytest` passes after lock update.

## P1: TCP Bridge Reliability

### 10. Serialize Access to the Persistent Socket

Problem:

- The global connection object is shared.
- Connection creation is locked, but `send_command` is not.
- Concurrent tool calls can interleave writes/reads and attach the wrong response to the wrong request.

Files:

- `rhino_mcp_server/src/rhinomcp/server.py`
- `rhino_mcp_server/tests/test_connection.py`

Implementation options:

- Simple fix: add an instance lock around the whole `send_command` method.
- Better fix: open a short-lived TCP connection per command and remove persistent socket state.
- Best long-term fix: add request IDs and framed messages.

Acceptance criteria:

- Concurrent Python tool calls cannot write/read the same socket simultaneously.
- Tests simulate parallel `send_command` calls and verify no interleaving.

### 11. Replace Ad Hoc JSON Stream Parsing with Message Framing

Problem:

- C# reads bytes into `incompleteData` and calls `JObject.Parse`.
- This works for one JSON object at a time but is fragile for concatenated messages, large messages, or partial multi-byte boundaries.
- Python response parsing uses `raw_decode` but does not check for trailing garbage.

Files:

- `rhino_mcp_server/src/rhinomcp/server.py`
- `rhino_mcp_plugin/RhinoMCPServer.cs`
- `rhino_mcp_server/tests/mock_rhino_server.py`
- `rhino_mcp_server/tests/test_connection.py`

Implementation options:

- Newline-delimited JSON: append `\n`, read lines.
- Length-prefixed JSON: send byte length, then payload.
- Add protocol versioning if changing framing.

Acceptance criteria:

- Two commands sent back-to-back are parsed as two commands.
- Large responses and chunked responses pass.
- Invalid/trailing data is rejected cleanly.

### 12. Improve C# Server Loop and Shutdown

Problem:

- Server loop polls `listener.Pending()` and sleeps.
- Client threads can remain blocked or sleeping until shutdown.
- `IsServerRunning()` only checks `server != null`, not actual `running`.

Files:

- `rhino_mcp_plugin/RhinoMCPServer.cs`
- `rhino_mcp_plugin/RhinoMCPServerController.cs`
- command files under `rhino_mcp_plugin/Commands/`

Implementation notes:

- Prefer async accept/read with cancellation token, or blocking accept interrupted by `listener.Stop()`.
- Track actual running state.
- Add clearer status command output.

Acceptance criteria:

- `mcpstart` twice does not produce misleading duplicate output.
- `mcpstop` reliably stops accepting and closes active clients.
- `mcpversion` and any status/test command report useful server state.

## P1: Rhino/.NET Compatibility

### 13. Decide Rhino 7 vs Rhino 8 Support

Problem:

- README says Rhino 7 or newer.
- Plugin targets `net8.0` and RhinoCommon 8, which is Rhino 8 oriented.
- Rhino 7 plugin compatibility generally requires .NET Framework 4.8 targeting.

Files:

- `README.md`
- `rhino_mcp_plugin/rhinomcp.csproj`
- `rhino_mcp_plugin/manifest.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/rhino-plugin-publish.yml`

Implementation options:

- If supporting Rhino 8 only: update README, manifest, and package docs.
- If supporting Rhino 7 and 8: multi-target `net48;net8.0` and condition package references/APIs accordingly.

Acceptance criteria:

- Docs and build target agree.
- CI matrix reflects the supported Rhino versions.

### 14. Fix Cross-Platform Viewport Capture

Problem:

- `CaptureViewport.cs` uses `System.Drawing.Common` save/dispose APIs that are Windows-only under modern .NET.
- Build emits platform warnings.

Files:

- `rhino_mcp_plugin/Functions/CaptureViewport.cs`
- `rhino_mcp_plugin/rhinomcp.csproj`

Implementation notes:

- Investigate Rhino/Eto cross-platform bitmap encoding APIs first.
- If `System.Drawing` remains required, isolate it behind platform-specific build guards and document Mac limitation.
- Add graceful runtime error if capture is unsupported on a platform.

Acceptance criteria:

- Build has no CA1416 warnings, or warnings are intentionally suppressed with documented platform guards.
- `capture_viewport` works on supported platforms or fails with a precise unsupported-platform message.

### 15. Make Post-Build Copy Optional

Problem:

- Local macOS build compiles the plugin, then fails copying to `/Applications/Rhino 8.app/Contents/PlugIns/`.

Files:

- `rhino_mcp_plugin/rhinomcp.csproj`
- README build instructions.

Implementation notes:

- Add an MSBuild property such as `CopyToRhinoPluginDir=false` by default.
- Only run the copy target when explicitly enabled.
- Keep release packaging independent of local app installation.

Acceptance criteria:

- `dotnet build rhino_mcp_plugin/rhinomcp.sln --configuration Release` succeeds without requiring write access to `/Applications`.
- Optional copy still works when explicitly requested by a developer.

## P2: API Quality and UX

### 16. Fix Prompt Documentation Drift

Problem:

- Prompt says `get_objects(filters=...)`, but the actual tool uses `layer_filter`, `type_filter`, and `bbox_filter`.
- Prompt says `execute_rhinoscript_python_code` accepts `verified_functions`, but the function only accepts `code`.

Files:

- `rhino_mcp_server/src/rhinomcp/prompts/assert_general_strategy.py`
- `rhino_mcp_server/src/rhinomcp/tools/execute_rhinoscript_python_code.py`
- `rhino_mcp_server/src/rhinomcp/tools/get_objects.py`

Acceptance criteria:

- Prompt examples match real function signatures.
- Any verification-field idea is either implemented or removed from prompt docs.

### 17. Normalize Version Metadata

Problem:

- Python package version is `0.2.1`.
- Plugin manifest version is `0.2.1`.
- `rhinomcp.__version__` is `0.1.0`.

Files:

- `rhino_mcp_server/src/rhinomcp/__init__.py`
- `rhino_mcp_server/pyproject.toml`
- `rhino_mcp_plugin/manifest.yml`
- `rhino_mcp_plugin/rhinomcp.csproj`

Implementation notes:

- Use `importlib.metadata.version("rhinomcp")` or a single generated version source for Python.
- Keep package, manifest, and plugin versions intentionally synchronized or document why not.

Acceptance criteria:

- `python -c "import rhinomcp; print(rhinomcp.__version__)"` prints the package version.

### 18. Add Ruff to Dev Dependencies or Fix Docs

Problem:

- README/AGENTS mention `ruff check`, CI installs ruff separately, but local `uv run ruff` fails because ruff is not in dev dependencies.

Files:

- `rhino_mcp_server/pyproject.toml`
- `rhino_mcp_server/uv.lock`
- `.github/workflows/ci.yml`

Acceptance criteria:

- `uv run ruff check src/rhinomcp` works after `uv pip install -e ".[dev]"`.
- CI can use the project dependency instead of ad hoc `pip install ruff`.

### 19. Clean Up Unused Imports and Dead Code

Problem:

- Many files import unused namespaces/modules.
- `validation.with_validation` is a no-op wrapper.
- `Serializer` layer cache uses a confusing `Guid` conversion from runtime serial number and is never invalidated on layer changes.

Files:

- `rhino_mcp_server/src/rhinomcp/**/*.py`
- `rhino_mcp_plugin/**/*.cs`
- `rhino_mcp_server/src/rhinomcp/validation.py`
- `rhino_mcp_plugin/Serializers/Serializer.cs`

Implementation notes:

- Run ruff after adding it.
- Remove unused imports rather than suppressing.
- Either remove the layer cache or implement correct invalidation from layer-create/delete/current-layer changes.

Acceptance criteria:

- `ruff check` passes, or remaining ignores are documented.
- No obvious dead wrappers remain.

## P2: Security and Safety

### 20. Add Explicit Safety Gates for Arbitrary Execution Tools

Problem:

- `execute_rhinoscript_python_code`, `execute_rhinocommon_csharp_code`, and `run_command` can execute arbitrary Rhino-side code/commands.
- That may be acceptable for a local trusted MCP server, but the risk must be explicit and configurable.

Files:

- `rhino_mcp_server/src/rhinomcp/tools/execute_rhinoscript_python_code.py`
- `rhino_mcp_server/src/rhinomcp/tools/execute_rhinocommon_csharp_code.py`
- `rhino_mcp_server/src/rhinomcp/tools/run_command.py`
- `rhino_mcp_plugin/Functions/ExecuteRhinoscript.cs`
- `rhino_mcp_plugin/Functions/ExecuteRhinoCommonCSharp.cs`
- `rhino_mcp_plugin/Functions/RunCommand.cs`
- `README.md`

Implementation options:

- Add env flags:
  - `RHINO_MCP_ENABLE_RHINOSCRIPT=1`
  - `RHINO_MCP_ENABLE_CSHARP=1`
  - `RHINO_MCP_ENABLE_RUN_COMMAND=1`
- Default depends on product posture. Conservative recommendation: enabled for local dev, documented as unsafe for untrusted clients.
- Add denylist or allowlist support for Rhino commands if practical.
- Mark these tools as destructive/open-world in MCP annotations.

Acceptance criteria:

- Disabled tools fail with a clear message before reaching Rhino.
- README explains risk and configuration.
- Tests cover enabled/disabled states.

### 21. Restrict Binding and Document Network Assumptions

Problem:

- Defaults bind to `127.0.0.1`, which is good.
- Python can override host via env.
- The security implications of exposing the bridge beyond localhost are not documented.

Files:

- `README.md`
- `rhino_mcp_server/src/rhinomcp/server.py`
- `rhino_mcp_plugin/RhinoMCPServer.cs`

Implementation notes:

- Keep localhost default.
- Warn strongly against binding Rhino plugin to non-loopback interfaces unless authentication/framing is added.
- Consider refusing non-loopback by default unless `RHINO_MCP_ALLOW_REMOTE=1`.

Acceptance criteria:

- Remote binding requires explicit opt-in.
- README documents the risk.

## P3: Testing and CI Improvements

### 22. Add Contract Synchronization Tests

Problem:

- Existing protocol-envelope test uses a hardcoded list of expected commands.
- It does not automatically compare:
  - protocol enum
  - schema filenames
  - Python `send_command` names
  - C# `[McpCommand]` names

Files:

- `contracts/test_schemas.py`
- Possibly a new `tests/test_contract_sync.py`.

Acceptance criteria:

- Test fails when a command exists in C# but not in protocol.
- Test fails when a command exists in protocol but not Python.
- Test fails when a command exists in protocol but lacks a schema.

### 23. Add More Realistic Mock Server Behavior

Problem:

- The mock server sometimes mirrors Python expectations rather than actual C# behavior.
- Example: Python delete-all bug was not caught by tests.

Files:

- `rhino_mcp_server/tests/mock_rhino_server.py`
- `rhino_mcp_server/tests/test_integration.py`

Implementation notes:

- Align mock responses with C# handlers.
- Add tests for exact response shapes where Python wrappers consume them.
- Prefer dedicated unit tests for wrapper response handling.

Acceptance criteria:

- Delete-all wrapper bug is covered.
- Select-by-name array behavior is covered.
- C# and mock response examples are documented.

### 24. Add C# Unit/Integration Test Strategy

Problem:

- Most behavior is tested through Python mocks.
- C# command handlers have no automated tests.

Implementation options:

- Extract pure validation/filtering helpers and unit test without Rhino runtime.
- Add smoke tests that compile handlers and verify dispatch table.
- For Rhino-dependent tests, document manual Rhino reproduction steps or use Rhino.Inside if feasible.

Acceptance criteria:

- Dispatch table duplicate/missing command tests exist.
- Helper logic such as select filter matching is testable without live Rhino where practical.

## Suggested Parallel Workstreams

Workstream A: Protocol and Schema

- Tasks 5, 6, 22.
- Owns `contracts/`, validation, and sync tests.

Workstream B: Core Bug Fixes

- Tasks 1, 2, 3, 4.
- Owns Python wrappers and C# handler corrections.

Workstream C: MCP Modernization

- Tasks 7, 8, 9, 16.
- Owns tool return shapes, errors, annotations, dependency choice, and prompt accuracy.

Workstream D: Transport Reliability

- Tasks 10, 11, 12.
- Owns socket locking/framing/server loop behavior.

Workstream E: Platform and Release

- Tasks 13, 14, 15, 17, 18, 19.
- Owns Rhino/.NET compatibility, CI, local build ergonomics, and cleanup.

Workstream F: Security

- Tasks 20, 21.
- Owns code-execution guardrails and network safety posture.

## Final Verification Checklist

Run from repo root unless noted:

```bash
cd rhino_mcp_server
uv run pytest
uv run pytest --cov=rhinomcp --cov-report=term-missing
uv run ruff check src/rhinomcp
uv run ruff format src/rhinomcp --check
uv run python ../contracts/test_schemas.py
cd ..
dotnet restore rhino_mcp_plugin/rhinomcp.sln
dotnet build rhino_mcp_plugin/rhinomcp.sln --configuration Release
```

Manual Rhino smoke test after plugin build:

1. Start Rhino.
2. Run `mcpstart`.
3. Start the Python MCP server with `uvx rhinomcp` or local dev command.
4. Call `get_document_summary`.
5. Create a box and verify the returned ID.
6. Select by `{"name": ["<box name>"]}`.
7. Capture viewport if supported on the platform.
8. Delete the object by ID.
9. Run `undo`.
10. Stop with `mcpstop`.
