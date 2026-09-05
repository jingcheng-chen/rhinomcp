# Continue autonomous RhinoMCP improvement

This is the entry point for a development agent with no prior chat context.
Last updated: 2026-09-05. Verify repository and application state before acting;
the previous session's running processes and document selection are not assumptions.

## Objective and agreed design

Build a repeatable task → modeling → independent evaluation → planning → bounded
repair → retest workflow for RhinoMCP. Improve plugin code or modeling guidance
using evidence, while keeping the agent model and evaluator fixed during a
comparison. The long-term input includes reference pictures; start with objective
geometry tasks and generated references. No additional user data is needed for
infrastructure work now.

The user specified the concrete modeling destination on 2026-09-05: reconstruct
this Barcelona chair in Rhino using only screenshots from different angles:
https://sketchfab.com/3d-models/barcelona-chair-7f871ae1a07f4f68b2146d71b4c52bfa
The scene includes a matching ottoman; chair-first is a working scope assumption,
not a confirmed exclusion of the ottoman. A screenshot pack, scale/camera policy,
visual thresholds and required editability remain to be defined. Do not give the
modeler the source mesh. Start with a baseline chair attempt, then turn observed
failures into focused frame/cushion tasks. This modeling track can advance alongside
the validation/recovery milestone below; chair reconstruction is not yet demonstrated.
See [roadmap.html](roadmap.html) for the visual status snapshot and proposed path.

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

- Capture repair is verified; see `CAPTURE_REPAIR.md`. The final implementation
  fits the requested image aspect, refreshes display caches, waits for queued
  redraws, and restores every viewport's projection and camera target.
  All eleven capture checks pass, starting with unrefreshed geometry. The 26
  geometry fixtures still produce their expected verdicts twice.
- Fresh prism loop `20260905-205440-a9e6b334` passes geometry evaluation and
  planning, and its PNG passes the controlled-fixture pixel/margin check.
  An earlier empty-image diagnosis was a preview interpretation error: the
  saved intermediate and final PNGs have identical hashes and valid pixel bounds.
  See the explicit correction in `CAPTURE_REPAIR.md`; do not pursue that false lead.
- Final plugin MVID is `90d87782-2887-435e-a8b2-02467f0c5094`, verified after a
  clean build/install/restart. The Release build has zero warnings/errors;
  all 279 Python tests, schema checks and relevant lint/format checks pass.
  At that milestone, an isolated builder and automatic code-repair/promotion
  were still unimplemented; see the later builder pilot below.

- Generated-reference input now works for grid-aligned cuboids. A hidden saved box
  produces calibrated Top/Front/Right drawings; only those PNGs reach the modeler.
  Two fresh loops reconstruct 70×40×30 and 40×70×30 mm correctly. Checking the
  second against the first task rejects dimensions while accepting equal volume.
  See `REFERENCE_LOOP.md` for evidence and the deliberately constrained scope.
- All 286 Python tests pass (63 experiment, 223 server), and the 26 live geometry
  fixtures retain their expected verdicts twice. Reference images/model are hashed,
  generator source is retained, and reference-task feedback is blocked to prevent
  the planner's private answer from leaking into a new modeler attempt.

- The isolated builder pilot is complete; see `BUILDER_LOOP.md`. Fresh planner and
  builder sessions generated a capture repair in an independent production checkout.
  A second builder session addressed supervisor review. The scope gate passed, the
  candidate built cleanly, 223 candidate tests and all 11 live captures passed, and
  26 geometry fixtures preserved expected verdicts twice. A fresh prism loop passed.
- `evaluator_issue` now routes to supervision and cannot dispatch the builder; both
  unit tests and a fresh live planner session verify that route. Root tests total 304.
  Exact-path edits, hashes, whole-checkout integrity checks and fresh review sessions
  are implemented; candidate execution and acceptance remain supervised.
- The trial candidate MVID was `e7e17267-3a6a-45e4-b37f-869810ee216d`. The supervisor
  restored and verified the prior working binary `90d87782-2887-435e-a8b2-02467f0c5094`.
  Rhino was left running with an empty document. Verify current state before reuse.
  Root production source remains unchanged; the replay patch lives in the ignored
  pilot directory `runs/repair-20260905-211537-bc56415e/` and was not promoted.

This demonstrates modeling/evaluation/planning and a supervised plugin-code repair.
The successful modeler corrected the box's centered placement using returned bounds.
No production plugin behavior was changed for the first loop.

## Latest milestone: durable trial controller

`trial.py` now registers reviewed builder candidates, pins source/patch/binary,
adapter and evaluator inputs, and records build/install/test/restore transitions.
It compares exact baseline/candidate case sets, rejects regressions and restores
through an operator-owned adapter, then verifies baseline identity and tests.
The checkpoint blocks further builder revision. Interrupted commands are not
replayed: unresolved child processes require an operator stop attestation before
recovery. No automatic promotion is enabled.

All 326 tests pass (103 experiment, 223 server), including 22 controller tests with
real subprocesses and a disposable file-based runtime. This is NOT live Rhino
rollback evidence. The runtime adapter for Rhino remains unimplemented. Read
`TRIAL_CONTROLLER.md` for the protocol, failure behavior, evidence and limitations.
`harness/trial-suite.json` freezes 43 live verdicts covering all canonical tasks,
swapped-reference control, 26 repeated fixtures and 11 captures; this combined suite
has not yet been run through the trial controller.

## Next concrete milestone

Connect the trial controller to a reviewed local Rhino runtime adapter:

1. Read `TRIAL_CONTROLLER.md`, `BUILDER_LOOP.md` and the fixed trial suite. Keep
   machine-specific installation configuration outside tracked project commands.
2. Implement build/probe/install/test/restore for an explicitly owned dedicated
   Rhino process and document. Verify loaded MVID separately from installed bytes;
   do not close unrelated work. Compile a separate copy of the reviewed snapshot.
3. Generate a new bounded, reviewed candidate. The historical completed builder
   pilot is not eligible for preparation; do not reset its executed checkpoint.
4. Run baseline and candidate comparisons, deliberately fail a candidate, verify
   real baseline restoration and all required verdicts, then exercise interruption.
   Current automatic restoration is proven only with the file-based test adapter.
5. Address evaluator-process trust and held-out comparisons before automatic
   promotion. The current C# judge runs in the candidate's Rhino process.

Fresh Codex sessions are implemented for modeling, planning and bounded building.
Claude Code adapters, model/version selection, held-out comparisons, OS-level
isolation and unattended installation remain roadmap items. Reference-task feedback
is still blocked until a public-feedback/redaction boundary is implemented.

## Known limits and operational lessons

- Rhino startup and `mcpstart` were performed by the supervising desktop agent.
  The Python runner requires an already-running listener and an empty unsaved doc.
- Do not reset or close unrelated user work. Inspect current state; create a new
  dedicated document. Never infer that the previous run's document is still active.
- Bounded source repair and review dispatch are implemented. The trial controller has
  adapter-based validation/recovery, but unattended live Rhino installation/rollback,
  promotion, automatic continuation of interrupted agent sessions, a full five-task
  suite and real-photo evaluation are not implemented.
- The gateway checks document identity but cannot lock out a human or external
  client. Current evaluation runs inside Rhino through the trusted C# bridge;
  stronger isolation is required before accepting untrusted plugin changes.
- The CLI uses its default model with personal configuration ignored. Explicit
  model/version recording and configurable adapters remain work for comparisons.
- Session `complete` is a claim, not acceptance. Read `evaluation.json` and actual
  logs. Do not blindly repeat a mutation after an interruption.
- The machine-local app-bundle copy belongs in local instructions, not tracked
  automation. A file replacement does not reload the active assembly.
- Capture repair passes the live regression. Its pixel thresholds are specific
  to black wireframe fixture geometry, not general image acceptance rules.
- Stop the dedicated Rhino process before replacing its loaded plugin file. An
  in-place replacement caused metadata errors; a fresh restart was required.
- The prism modeler created already-transformed profile coordinates. Its successful
  pose is verified, but this run does not validate the optional rotation tool.

## Evidence and portability

`FIRST_LOOP.md`, `POSED_PRISM_LOOP.md`, `THROUGH_HOLE_LOOP.md`, and
`CAPTURE_REPAIR.md`, `REFERENCE_LOOP.md`, `BUILDER_LOOP.md`, and
`TRIAL_CONTROLLER.md` are portable summaries. Full local records are under ignored
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
