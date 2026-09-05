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

This demonstrates modeling/evaluation/planning, not autonomous plugin-code repair.
The successful modeler corrected the box's centered placement using returned bounds.
No production plugin behavior was changed for the first loop.

## Next concrete milestone

Prepare reliable capture for the planned reference-image task:

1. Preserve the three passing geometry tasks as regression cases.
2. Reproduce the prism's clipped screenshot with a saved candidate and fixed
   camera/capture settings. Determine whether framing or capture scaling is wrong.
3. Make one bounded, evidence-backed capture fix if a defect is confirmed, and
   verify full-object framing plus preservation of the original viewport state.
4. If the fix changes production behavior, keep Python/C#/contracts synchronized
   as required; rebuild/install/restart in the dedicated Rhino session and verify
   the loaded candidate before testing it.
5. Once capture is reliable, define a generated-reference reconstruction task
   with known cameras and explicit geometric acceptance. Do not use unreliable
   screenshots to accept or reject geometry.

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
- The prism's screenshot is clipped despite a passing saved-file geometry result.
  Capture framing is an open investigation, not a confirmed geometry failure.
- The prism modeler created already-transformed profile coordinates. Its successful
  pose is verified, but this run does not validate the optional rotation tool.

## Evidence and portability

`FIRST_LOOP.md`, `POSED_PRISM_LOOP.md`, and `THROUGH_HOLE_LOOP.md` are portable summaries. Full local records are under ignored
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
