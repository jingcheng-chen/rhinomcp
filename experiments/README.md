# Live RhinoMCP improvement experiment

**Continuing development in a fresh session? Start with [CONTINUE.md](CONTINUE.md).**
Agent behavior and runtime responsibilities are mapped in
[harness/README.md](harness/README.md).

This first implementation runs one model/evaluate/plan loop with fresh Codex CLI
sessions. It does not yet automatically edit, install, or promote plugin fixes.
No user reference data is required for the included box task.

## Agent/operator startup runbook

1. From `server/`, install the development environment with `uv sync --extra dev`.
2. With Rhino closed, run `dotnet build plugin/rhinomcp.sln --configuration Release`
   from the repository root. Follow the local installation instruction in
   `AGENTS.md` before launching Rhino. The local app-bundle copy is intentionally
   not embedded in the experiment runner. On another machine, install/register
   the plugin using that machine's Rhino installation procedure and ensure its
   runtime dependencies are available.
3. Launch Rhino 8, select **New Model**, and run `mcpstart` in its command field.
   Reserve this application session for testing and leave other MCP clients idle.
   Do not use a document containing user work. A build/file replacement does not
   replace an already loaded assembly; close and restart the dedicated Rhino
   process after plugin changes.
4. From the repository root, run
   `server/.venv/bin/python -m experiments.runner`.
   The runner checks the live connection, loaded assembly path/version/MVID,
   and empty unsaved document before making changes. It starts a narrow stdio
   MCP gateway automatically for the modeler; no separate production MCP server
   process is necessary.
5. Inspect `experiments/runs/<run>/summary.json`, `evaluation.json`, the saved
   `candidate.3dm`, screenshot, and each session's prompt, events and result.
   A deterministic failure remains a failure even if either agent claims success.

Codex must already be installed and authenticated. The adapter ignores personal
client configuration, disables unrelated tools, and uses the CLI's default model;
the event stream records the actual run. Client/model selection is not yet a
configurable experiment matrix. The modeler has only create, translate and analyze
tools. Each gateway operation checks the active document's serial and run marker.
The planner receives evidence in its prompt and has no Rhino MCP connection.
The three gateway tools are explicitly preapproved for this authorized test session;
other MCP servers and tools are not enabled. Without that scoped configuration,
non-interactive sessions can cancel modeling calls that require confirmation.

To carry the planner's findings into another attempt, create a fresh empty document
and run `server/.venv/bin/python -m experiments.runner --feedback <previous-summary.json>`.
The previous result is retained and copied into the new run. This is an explicit
new attempt, not automatic replay of potentially completed operations. A failed
geometry verdict exits with code 2; execution errors exit unsuccessfully as well.

## Evaluator validation

With Rhino's listener active, run:

```
server/.venv/bin/python -m experiments.validate_live
server/.venv/bin/python -m pytest experiments/tests
```

Live validation creates independent `.3dm` fixtures in memory, leaving the active
document unchanged. It checks a correct box and rejects wrong scale, wrong position,
extra geometry, an open surface, and wrong units. Every fixture is measured twice.
The evaluator uses RhinoCommon directly on saved files, not the modeler's analysis
claims. Its scope is the included axis-aligned box specification, not general shape
reconstruction. Screenshots are illustrative and do not affect the verdict.

## Boundaries and recovery

- The runner coordinates its own processes with a local advisory lock. It cannot
  prevent a person or unrelated MCP client from changing Rhino. Keep the dedicated
  session idle while it runs; document identity checks reduce accidental crossover.
- A 180-second default timeout bounds each agent session; `--timeout` overrides it.
  The modeler gateway allows at most 12 calls. Process groups are terminated on
  timeout. Mutations are never retried automatically.
- Checkpoints, failures, and partial session logs are retained. Automatic resume,
  malformed-output correction, provider switching, and plugin-repair sessions are
  future work. After interruption inspect the document and logs, then create a
  new empty document for a new attempt. Never blindly repeat a mutating call.
- Tool restrictions reduce accidental access. This local prototype is not a
  hardened isolation boundary against malicious plugin code: trusted evaluation
  currently executes inside Rhino through the existing C# bridge. Automatic
  plugin builders require stronger process/filesystem isolation before enabling
  autonomous candidate acceptance.
- Rhino UI startup is documented rather than implemented in the Python runner.
  A supervising desktop agent can launch Rhino, create a document and enter
  `mcpstart`; fully unattended restart/reload remains a later milestone.

The broader roadmap is in `docs/AUTONOMOUS_IMPROVEMENT_PLAN.md`.
