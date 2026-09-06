# Live RhinoMCP improvement experiment

**Continuing development in a fresh session? Start with [CONTINUE.md](CONTINUE.md).**
Visual overview: [roadmap.html](roadmap.html), including the Barcelona-chair destination.
The chair is one complex benchmark for general improvement across many objects.
For screenshot diagnostics, see [VISUAL_BENCHMARKS.md](VISUAL_BENCHMARKS.md).
Agent behavior and runtime responsibilities are mapped in
[harness/README.md](harness/README.md).

The modeling runner uses fresh Codex CLI sessions. A bounded builder can generate
and revise reviewed patches. The trial controller now connects to live Rhino through
`rhino_trial.py`: build, identity checks, the fixed 43-case suite and recovery are
recorded by the controller; desktop quit/install/restart steps remain supervised.
No automatic promotion is enabled. See [TRIAL_CONTROLLER.md](TRIAL_CONTROLLER.md)
for the protocol and [LIVE_TRIAL.md](LIVE_TRIAL.md) for the live adapter runbook.
No user reference data is required for the box, posed-prism, and through-hole tasks.

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
configurable experiment matrix. The box modeler has only create, translate and
analyze tools. The prism task additionally enables extrusion, rotation, and deletion
of individual construction objects. Each gateway operation checks the active
document's serial and run marker.
The through-hole task enables boolean subtraction and individual-object deletion;
extrusion and rotation are disabled for that task.
The planner receives evidence in its prompt and has no Rhino MCP connection.
The task's gateway tools are explicitly preapproved for this authorized test session;
other MCP servers and tools are not enabled. Without that scoped configuration,
non-interactive sessions can cancel modeling calls that require confirmation.

To carry the planner's findings into another attempt, create a fresh empty document
and run `server/.venv/bin/python -m experiments.runner --feedback <previous-summary.json>`.
The previous result is retained and copied into the new run. This is an explicit
new attempt, not automatic replay of potentially completed operations. A failed
geometry verdict exits with code 2; execution errors exit unsuccessfully as well.

## Task definitions

`tasks/schema.json` defines the supported task types. The runner rejects unknown
types, incompatible fields, nonfinite numbers, and invalid dimensions before
contacting Rhino. To run the posed prism, create a new empty Rhino document and use:

```
server/.venv/bin/python -m experiments.runner --task experiments/tasks/posed_prism.json
server/.venv/bin/python -m experiments.runner --task experiments/tasks/through_hole.json
```

`axis_aligned_box` checks world bounds, validity, solidity and volume.
`triangular_prism_pose` specifies a right-triangle profile with unequal legs, its
extrusion height, Z rotation about world origin followed by world translation,
and area/volume tolerances. Evaluation maps measured vertices into the prescribed
local frame, checks the six required corners and containment, and checks planar
faces, straight edges, area and volume. Equivalent subdivisions of planar faces
are accepted. Correct volume alone cannot hide an incorrect pose or handedness.

The modeler may choose any available construction sequence that achieves the
specified result. The live prism run directly constructed the transformed profile;
it did not exercise the optional rotation tool.

`box_through_hole` requires a single Z-aligned circular through-hole inside an
axis-aligned block. It checks block bounds, cylinder axis/radius, full trimmed-face
height, an unobstructed centerline, six outer boundary planes, area and volume.
The schema rejects a hole touching or crossing the block's side walls. A blind
hole with equal removed volume must still fail. Unsupported surface types cannot
pass this task; this is not a general freeform-hole evaluator.

Run each command in its own fresh empty document. Each run snapshots the evaluator
sources and hashes in `evaluator_source/` and `evaluator_versions.json`. A detected
source change before evaluation stops the run instead of silently changing its
acceptance rules.

## Evaluator validation

With Rhino's listener active, run:

```
server/.venv/bin/python -m experiments.validate_live
server/.venv/bin/python -m pytest experiments/tests
```

Live validation creates independent `.3dm` fixtures in memory, leaving the active
document unchanged. Box fixtures check correct geometry and five error cases.
Prism fixtures check correct geometry, equivalent split faces, and seven errors:
wrong rotation, translation, handedness, scale, open geometry, extra objects and
wrong units. Every fixture is measured twice. The prism references are built from
joined planar faces, independently of the production extrusion operation.
Through-hole fixtures add three correct representations and eight flawed models,
including blind and equal-volume blind holes. Correct extrusion/Brep references
use an inner profile rather than the production subtraction command. A separate
oversized-cutter fixture protects against confusing untrimmed surface bounds with
actual trimmed-face bounds.
The evaluator uses RhinoCommon directly on saved files, not the modeler's analysis
claims. Its scope is the three explicit task types, not general shape reconstruction.
Screenshots are illustrative and do not affect the verdict. The prism run exposed
a clipped screenshot; capture framing needs separate investigation.

## Boundaries and recovery

- The runner coordinates its own processes with a local advisory lock. It cannot
  prevent a person or unrelated MCP client from changing Rhino. Keep the dedicated
  session idle while it runs; document identity checks reduce accidental crossover.
- A 180-second default timeout bounds each agent session; `--timeout` overrides it.
  The modeler gateway allows at most 20 calls. Process groups are terminated on
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

## Capture regression

With a new empty, unsaved Rhino document and the listener running, use a saved
passing posed-prism candidate:

```
server/.venv/bin/python -m experiments.validate_capture --model experiments/runs/<prism-run>/candidate.3dm
```

This imports that file into the dedicated document, uses black wireframe geometry,
and captures Perspective, Top and Back at 1000×750, 400×1000 and 1000×400.
The first capture starts without an explicit display refresh after geometry creation.
It checks nonempty geometry pixels and a five-pixel border, output dimensions,
and before/after camera, target, projection, frustum, view identity/name/size,
display mode, active view, document modified flag and geometry checksums.
It also exercises capture without fitting and a missing-view error.
The pixel rule applies only to this controlled fixture; it is not a general image
similarity score and does not replace independent saved-file geometry evaluation.
The report and PNGs are saved under `runs/capture-validation-<timestamp>/`.
Run the same checker and saved file against baseline and candidate assemblies,
restarting the dedicated Rhino application between installations.

## Generated-reference task

In a fresh empty, unsaved Rhino document with the listener running:

```
server/.venv/bin/python -m experiments.runner --task experiments/tasks/reference_box.json
```

The controller saves and validates a hidden reference box, then generates three
orthographic grid drawings. Only PNGs are available to the modeler through
`get_reference_image`; target dimensions are absent from its prompt. The grid,
axis labels, supplied cuboid assumption and exact 10 mm increments make this
first image task unambiguous. These are analytic drawings, not viewport captures
or photographs. Other task types remain text-driven and cannot use the image tool.

`references.py` defines generation and calibration; `tasks/schema.json` constrains
this input mode to supported boxes. Runs retain reference hashes, generator source,
public calibration and the separate reference evaluation. Reference-task feedback
replay is disabled until hidden-answer redaction exists. See `REFERENCE_LOOP.md`
for two passing live reconstructions and the swapped-axis negative control.

## Bounded builder pilot

Replay the known capture defect with the recorded baseline evidence:

```
server/.venv/bin/python -m experiments.repair --evidence experiments/runs/capture-validation-20260905-202746/validation.json
```

This needs no Rhino connection: it prepares an independent production checkout,
starts fresh planner/builder sessions, and stops at a scoped patch for review.
It does not build, install, execute or promote the candidate. `--timeout` bounds
each session. The baseline source is pinned to `a7bd5d1`. On another host, first
rebuild and measure that baseline in a dedicated Rhino session and supply its
operator-verified loaded MVID with `--baseline-mvid`; never label evidence from a
different source as this baseline. Follow the local installation instructions.

To return review findings to an unexecuted candidate, put the findings in a text
file and use:

```
server/.venv/bin/python -m experiments.repair --revise experiments/runs/<repair-run> --feedback <review.txt>
```

Each review uses a fresh session and retains its input patch and feedback. Inspect
checkpoints/failure records after interruption; do not blindly replay writes or
revise a checkout after builds have added files. See `BUILDER_LOOP.md` for the
completed supervised build/live-test/restoration pilot and its isolation limits.
