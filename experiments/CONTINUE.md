# Continue autonomous RhinoMCP improvement

This is the entry point for a development agent with no prior chat context.
Last updated: 2026-09-05. Verify repository and application state before acting;
the previous session's running processes and document selection are not assumptions.

## Objective and agreed design

Build a repeatable task → modeling → independent evaluation → planning → bounded
repair → retest workflow for RhinoMCP. Improve plugin code or modeling guidance
using evidence, while keeping the agent model and evaluator fixed during a
comparison. The long-term input includes reference pictures; start with objective
geometry tasks and generated references. No additional user data is needed now.

The approach is inspired by Harness-of-Harness:
https://arxiv.org/html/2609.01481v1

Use fresh agent sessions at role boundaries and saved artifacts for continuity.
Keep evaluator rules and hidden references outside agents' writable/access scope.
Use small, verifiable changes, developer checks before independent QA, preservation
tests, and a balance of repairs with new capabilities. Do not manufacture a plugin
defect when a task passes. The controller enforces boundaries; role prompts alone
are not isolation.

## Read in this order

1. Repository `AGENTS.md`: architecture, protocol change requirements, build rules,
   and the machine-local installation instruction.
2. This file: current state and next milestone.
3. `README.md` in this directory: startup and run commands.
4. `harness/README.md`: map of behavior, permissions, tasks and evaluator code.
5. `FIRST_LOOP.md`: completed live experiment and evidence locations.
6. `../docs/AUTONOMOUS_IMPROVEMENT_PLAN.md`: full phased roadmap.

## Implemented and verified

- One box task: exactly one valid closed solid, minimum (0,0,0), XYZ dimensions
  100 × 50 × 30 mm, volume 150,000 mm³.
- A posed scalene triangular prism task: 80 × 40 mm local right-triangle profile,
  25 mm extrusion, +30° world-Z rotation then translation (120,-40,15) mm.
  A fresh live modeling/evaluation/planning cycle passed; the box regression passed.
- Explicit task-type schemas and pose-sensitive evaluation: six corners,
  containment, planar faces, straight edges, area and volume. Split planar faces
  are accepted. Prism fixtures independently use joined faces, not extrusion.
- Independent RhinoCommon measurements of saved `.3dm` files and analytic checks.
- Live fixtures: a correct box passes; wrong scale, wrong position, extra geometry,
  open surface, and wrong units fail. Repeated measurements agreed.
- Fresh Codex modeler and planner sessions, narrow MCP gateway, scoped approval
  for task-specific tools, timeouts, logs, artifact hashes, and explicit feedback input.
- A completed passing live loop, preceded by a failed attempt whose MCP creation
  calls were canceled by client configuration. The supervising development session
  fixed the configuration; the next attempt consumed the prior planner's findings.
- 193 existing Python tests and 23 experiment tests passed at the first milestone.
  The C# Release build passed and was installed before Rhino was launched.
- At the posed-prism milestone, 38 experiment tests passed and 15 live fixtures
  each produced their expected verdict twice (three valid forms, twelve flaws).
  The current server suite also passed all 223 tests.
  See `POSED_PRISM_LOOP.md` for the run records and verification details.
- The through-hole task now validates a 100 × 60 × 20 mm block with a radius-6
  Z-axis hole at XY (30,20). It checks trimmed hole depth, axis, radius, clear
  centerline, outer boundary planes, area and volume. See `THROUGH_HOLE_LOOP.md`.
- A live task exposed an evaluator bug: `BrepFace.GetBoundingBox(true)` measured
  the oversized cutter's untrimmed surface. A new correct fixture reproduced it;
  the supervisor changed measurement to `DuplicateFace(false).GetBoundingBox(true)`.
  The unchanged original candidate then passed. Requirements were not relaxed.
- Runs now snapshot evaluator sources/hashes. The new fixture suite has 26 cases:
  six valid representations and twenty flaws, each measured twice. A blind hole
  with the correct volume is rejected on other geometric predicates.
- The fresh through-hole run and box/prism regressions all passed. At this milestone,
  all 56 experiment tests and 223 current server tests passed, plus experiment lint
  and formatting checks. Production plugin code remains unchanged.

- Capture repair is in progress; see `CAPTURE_REPAIR.md`. Fitting the requested
  aspect fixes clipping. An intermediate candidate passed eleven imported-model
  checks, but a fresh modeling loop exposed an empty image without a document
  refresh. Restoring every viewport around that refresh still allowed queued
  redraws to move cameras after return. A direct `RhinoApp.Wait()` experiment
  preserved state; that final ordering is in source but awaits build/live validation.
- Last loaded MVID is `6efd7016-3b1e-4ede-b5a9-5c9f28a73634`, NOT the final source.
  A quit/save dialog is pending for a disposable capture fixture. Desktop control
  reported the Mac locked; the user was asked to unlock it. Do not overwrite the
  loaded plugin file before Rhino exits. No isolated builder is implemented.

This demonstrates modeling/evaluation/planning and a supervised plugin-code repair.
The successful modeler corrected the box's centered placement using returned bounds.
No production plugin behavior was changed for the first loop.

## Next concrete milestone

Finish and verify the capture repair first:

1. After the user unlocks the Mac, inspect the Rhino quit dialog. The only remaining
   document is the disposable imported capture fixture, backed by the existing saved
   prism. Finish quitting, build/install per local `AGENTS.md`, then restart and
   run `mcpstart`. Verify the loaded MVID changed from the value above.
2. Run `validate_capture` with the saved prism as documented in `README.md`.
   The current checker starts with unrefreshed geometry. All eleven cases must pass.
3. Run the 26 geometry fixtures and a fresh posed-prism model/evaluate/plan loop.
   Inspect the fresh PNG as well as its geometry verdict; a previous intermediate
   candidate passed geometry but produced an empty screenshot.
4. Update this handoff/report with actual final outcomes. The current source adds
   `RhinoApp.Wait()` after the document redraw; it has only been checked through
   a direct live scripting experiment, not the rebuilt command yet.

Then define the first generated-reference reconstruction task:

1. Preserve the box, posed prism and through-hole geometry tasks and the new
   capture regression. Read `CAPTURE_REPAIR.md` for the verified production fix.
2. Generate reference views from a known, saved object with fixed cameras. Record
   camera calibration, model units and an explicit scale cue; pictures alone do
   not determine absolute dimensions. Keep hidden geometry outside the modeler.
3. Extend the narrow modeler gateway to deliver only the intended reference images
   and task brief, while retaining trusted independent saved-file evaluation.
4. Run a fresh modeler/evaluator/planner loop against objective geometric criteria.
   Treat visual similarity as supporting evidence, not a replacement for geometry.
5. Record the result and any task ambiguities before attempting real-photo tasks.

Then implement an isolated builder adapter and verified restart/reload plus
baseline/candidate comparison. Basic profile extrusion is already exercised by
the prism task. Before automatic repairs, add a distinct evaluator-issue route:
the current planner enum only has `plugin_issue`, so its through-hole measurement
diagnosis was assigned that action despite being an evaluator bug. Such findings
must go to supervisory review, never authorize the plugin builder to edit the
evaluator. See the roadmap for acceptance criteria.

## Known limits and operational lessons

- Rhino startup and `mcpstart` were performed by the supervising desktop agent.
  The Python runner requires an already-running listener and an empty unsaved doc.
- Do not reset or close unrelated user work. Inspect current state; create a new
  dedicated document. Never infer that the previous run's document is still active.
- No automatic plugin repair, automatic session resume, candidate promotion,
  rollback, full five-task suite, or real-photo evaluation is implemented yet.
- The gateway checks document identity but cannot lock out a human or external
  client. Current evaluation runs inside Rhino through the trusted C# bridge;
  stronger isolation is required before accepting untrusted plugin changes.
- The CLI uses its default model with personal configuration ignored. Explicit
  model/version recording and configurable adapters remain work for comparisons.
- Session `complete` is a claim, not acceptance. Read `evaluation.json` and actual
  logs. Do not blindly repeat a mutation after an interruption.
- The machine-local app-bundle copy belongs in local instructions, not tracked
  automation. A file replacement does not reload the active assembly.
- Capture repair still needs final live verification. Its pixel thresholds are
  specific to black wireframe fixture geometry, not general image acceptance rules.
- Stop the dedicated Rhino process before replacing its loaded plugin file. An
  in-place replacement caused metadata errors; a fresh restart was required.
- The prism modeler created already-transformed profile coordinates. Its successful
  pose is verified, but this run does not validate the optional rotation tool.

## Evidence and portability

`FIRST_LOOP.md`, `POSED_PRISM_LOOP.md`, `THROUGH_HOLE_LOOP.md`, and
`CAPTURE_REPAIR.md` are portable summaries. Full local records are under ignored
`runs/` directories and may not exist on another machine. If absent, rerun the
fixtures and task; do not claim fresh verification from the historical report.
Do not rely on a chat session, sidebar task, or its internal memory for state.

Development is on the `harness` branch. Check `git status` and recent commits before
continuing; a working tree may contain work newer than this handoff. Full local run
artifacts remain ignored and are not transferred by checking out the branch.

After each development milestone, update this file with what is implemented,
verification results, unresolved issues and the next bounded step. Add a concise
report for important live runs; leave detailed logs in the run directory. Preserve
the distinction between implemented behavior and future roadmap items.
