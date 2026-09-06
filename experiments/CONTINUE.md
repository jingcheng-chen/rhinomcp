# Continue autonomous RhinoMCP improvement

This is the entry point for a development agent with no prior chat context.
Last updated: 2026-09-06. Verify repository and application state before acting;
the previous session's running processes and document selection are not assumptions.

## Objective and agreed design

Build a repeatable task → modeling → independent evaluation → planning → bounded
repair → retest workflow for RhinoMCP. Improve plugin code or modeling guidance
using evidence, while keeping the agent model and evaluator fixed during a
comparison. The long-term input includes reference pictures; start with objective
geometry tasks and generated references. No additional user data is needed for
infrastructure work now.

The user clarified on 2026-09-06 that the goal is a general RhinoMCP improvement
process across many tasks. The chair is one complex diagnostic benchmark, not the
only ultimate test or a reason to hard-code chair-specific plugin behavior.
Changes should improve reusable operations or guidance and preserve existing tasks;
transfer to other objects and held-out cases is needed to establish generalization.

The current complex benchmark, introduced on 2026-09-05, is to reconstruct
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

## Previous milestone: live trial controller and interrupted recovery

`trial.py` registers reviewed candidates, pins source/patch/binary and declared
adapter/evaluator inputs, and records build/install/test/restore transitions.
`rhino_trial.py` now connects it to a dedicated live Rhino process and document.
The controller builds a separate candidate copy, checks actual loaded MVID and
installed bytes, and runs the frozen 43-case suite. Desktop quit/install/restart
remains supervised through a recorded lifecycle ticket; no automatic promotion.
Read `LIVE_TRIAL.md` for the runbook and evidence, and `TRIAL_CONTROLLER.md` for
checkpoint and recovery semantics.

A fresh supervisor-authored negative candidate disables capture fitting; it is
fault injection for recovery validation, not an agent-produced improvement.
Baseline: 43/43 pass. Candidate: 34/43 pass, with exactly nine fitted capture
regressions. The controller rejects it. At the idle restoration handoff, the
supervisor deliberately stops the controller and adapter. Resume without a stop
attestation blocks; after verified stop and acknowledgement, it proceeds directly
to restoration without replaying candidate installation.

The restored baseline passes **43/43**. Final state is `rejected`,
`runtime_dirty=false`, `promoted=false`. Rhino is left running the working baseline
in an empty unsaved test document. Verify current state before reuse; complete
evidence and lifecycle instructions are recorded in `LIVE_TRIAL.md`.
Local trial: `runs/live-recovery-20260905-224344/trial-dc347a7d/`.
Verified baseline MVID: `90d87782-2887-435e-a8b2-02467f0c5094`.

All **338 tests pass** (115 experiment, 223 server). The candidate build also passes
235 Python/contract tests and lint, with zero C# warnings/errors. Integration fixed
virtual-environment invocation, active-object counting after undoable deletion,
slow pixel measurement and stale connections across restart. The pixel predicate
was preserved and all ten historical image measurements match exactly. Earlier
failed attempts remain recorded and were not rewritten as successes.

Run developer suites sequentially: the existing mock-server fixtures share a port.
Full server lint passes after formatting-only commit `e41c257`; the full server
format check still reports 17 pre-existing files. Do not conflate that limitation
with the focused experiment format check, which passes.

## Previous milestone: first complex screenshot diagnostic

The general-purpose screenshot runner is implemented: `visual_runner.py`,
`visual_mcp.py`, `visual_audit.cs`, and configurable `visual_tasks/`.
Read `VISUAL_BENCHMARKS.md` and `CHAIR_BASELINE.md` before continuing.
Four public chair screenshots were captured from Sketchfab; one rear-oblique
view was reserved outside both fresh agents. No target mesh was extracted.

Run `runs/visual-20260906-084828-2fc89506/` completed with 65 valid named objects
(61 solid extrusions, four open swept frame Breps). The nine structure checks pass,
but visual acceptance is explicitly `unscored`. The fresh planner recommends
`revise_modeling`: angular cushion blocks, inaccurate frame profile and transitions,
open frame ends, and crude strap wrapping. No command failures were reported.
No production behavior changed. No builder was dispatched and nothing was promoted.
This is a diagnostic starting point, not demonstrated self-improvement.

**Historical Rhino state at that milestone:** the saved baseline chair remained in the owned
unsaved document, marker `visual-20260906-084828-2fc89506`, original plugin MVID
`90d87782-2887-435e-a8b2-02467f0c5094`. Verify live identity and contents before any
cleanup; do not reuse the older assumption of an empty document. Full local model,
images and reports are saved in the run. Source/image hashes preserve the baseline.

All **348 developer tests pass** (125 experiment, 223 server), including ten new
screenshot-boundary and diagnostic-verdict tests. Experiment lint/format checks
pass. The 43-case live contract is unchanged; its live suite was not rerun because
this milestone changed no production plugin/server/protocol behavior.

## Previous milestone: curved-strip closure probe

Read `STRIP_PROBE.md`. Actual MCP sweeps of a quarter-circle rectangular strip are
open with both `closed=false` and `closed=true`; measurements are identical. A
supervisor-capped copy and independently extruded sector pass the fixed geometry
checks. Wrong width/radius/position, extra objects and open shells fail. All nine
fixtures produce expected verdicts twice. Containment measurement now normalizes
inward normals on an in-memory copy, with both orientations verified as positives;
the initial unexpected-positive run remains preserved.

Fresh planner result: `plugin_issue` for unsupported end-capping, not a regression
of an existing cap feature. Proposed change: explicit opt-in `cap_planar_ends` on
`sweep1`, default false, valid closed output or clear failure without partial objects.
The unused `closed` flag is a distinct rail-closure contract issue; do not repurpose it.
No plugin change or builder dispatch has happened yet.

Run: `runs/strip-20260906-090832-bc7dde0c/`. All 65 chair objects, their attributes,
and six existing layers match their before-probe state. The existing chair marker
and original plugin remain in place; verify current ownership before further work.
**356 developer tests pass** (133 experiment, 223 server), plus experiment lint/format.

## Previous milestone: validated generic sweep end caps

Read `SWEEP_CAP_TRIAL.md`. A fresh bounded builder added opt-in
`cap_planar_ends` to `sweep1` across C#, Python and schema. Default false preserves
existing open sweeps. Enabled capping validates all outputs before adding any,
accepts existing solids, fails clearly for uncapable results, rolls back partial
insertions and disposes temporary geometry. The old unused `closed` flag is
unchanged and remains a separate contract issue.

New repairs use `harness/roles/bounded_builder.md` and a reviewed per-repair scope
(`harness/repairs/sweep-cap.json`). Manifest hashes and checkout inventory protect
scope across initial dispatch, review/revision and trial preparation. The old
capture replay remains supported. The exact tested patch is preserved in
`harness/repairs/sweep-cap.patch` for replay from its pinned baseline revision.

The expanded frozen contract `harness/trial-sweep-cap.json` retains all 43 previous
verdicts and adds seven sweep cases. Baseline: 47 true, three explicitly measured
capability failures. Candidate: **50/50 true**. Restored baseline: exactly the same
47 true / three false vector. No regressions; three measured improvements. Final
controller state: `accepted_trial`, `runtime_dirty=false`, `promoted=false`.
The supervisor then integrated the exact tested three-file patch into this branch
and added independent permanent transport/schema tests. This is source adoption;
at that milestone the running Rhino plugin was still the restored original binary.

Local builder: `runs/repair-20260906-092614-ae7792cc/`.
Successful trial: `trial-667b3692/` inside that run. Earlier `trial-194a32ba` failed
before build/install due to adapter launch setup and was safely rejected; do not
resume it. Use an absolute repository PYTHONPATH for live controller invocation and
call `rhino_trial.claim_empty(trial_directory)` on a verified fresh empty document
before running. Never reset a registered candidate or replay an interrupted step
without checking its durable state and whether a child process remains alive.

**Historical Rhino state at that handoff:** PID 59985, one dedicated empty unsaved
document, serial 268435457, marker none, modified=true from the cleared test work;
original MVID
`90d87782-2887-435e-a8b2-02467f0c5094`. Recheck actual identity before reuse.
The original chair is safely stored in
`runs/visual-20260906-084828-2fc89506/candidate.3dm`, SHA-256
`188777bf59d32b40dc122959b6753b6407f9e58f874a562ef76f9f98983a6923`.
Its full geometry/attribute/layer fingerprint was verified before closing.
Rhino takes time to exit; wait for the main process to disappear before copying
any plugin. No forced termination or in-place loaded-binary replacement occurred.

The verified candidate binary is `trial-667b3692/candidate.rhp`, MVID
`79b1500e-e20d-47af-9c83-6f915729a712`, SHA-256
`635e8ccf94a55775ea2b58166d83eb995ad517c3de3d66963caed7772a027d7e`.
Rebuilding changes binary identity; do not assume its old MVID. Baseline binary
and complete lifecycle tickets are retained in the trial directory.

Final source validation: **385 tests pass** (144 harness, 228 server, 13 contract
tests); standalone contract validation passes. Experiment lint/format and server
source lint pass. The fresh post-trial planner recommends `accept`, followed by
a small fresh-modeler curved-strip task. See the saved post-trial plan.

## Latest milestone: fresh-agent benefit and active improved baseline

Read `STRIP_MODELER_LOOP.md`. A fixed quarter-annular strip task now runs through
fresh modeler/planner sessions and a narrow, task-specific `sweep1` gateway.
The old plugin fails the origin task; the exact accepted cap binary passes with
identical prompt bytes and evaluator hashes. A translated task also passes.
Nine independent calibration cases returned their expected verdicts twice,
including wrong-pose cross-evaluations. Judge bounds are normalized local bounds;
world pose is checked by inverse-transforming an in-memory duplicate.

The new `harness/trial-preservation-v2.json` requires **52/52 true**: all previous
50 requirements plus both strip modeling tasks. All pass, including fresh repeats
of both poses. The former three capability failures are no longer allowed for this
baseline. **392 developer tests pass** (151 experiment, 228 server, 13 contract).
These fixed-shape runs do not establish broad transfer or improved chair geometry.

Campaign: `runs/strip-modeling-20260906-140908/`; its source snapshots, comparison,
calibration, preservation result and activation decision preserve the evidence.
The supervisor explicitly adopted the exact previously accepted runtime after
validation. No production source changes or rebuild were needed for this milestone.
Historical trial restoration and promotion records remain unchanged.

**Current runtime at handoff:** PID 94887, MVID
`79b1500e-e20d-47af-9c83-6f915729a712`, SHA-256
`635e8ccf94a55775ea2b58166d83eb995ad517c3de3d66963caed7772a027d7e`.
One empty unsaved document, serial 268435457, marker none, modified=true after
cleanup. Verify identity and contents again before acting. `claim_empty` requires
an unmodified fresh document; do not blindly reuse this handoff state. The original
binary remains in the prior trial for recovery. The saved chair is untouched.

## Next concrete milestone

Define a small assembly task with **hierarchical layers**, then independently
validate nesting, full paths and saved part assignments before a fresh agent run.
Include duplicate child names under distinct parents and save/reopen checks.
Use observed failures to distinguish modeling guidance from a reusable plugin
repair. Preserve the new 52-case baseline and keep the chair one of many cases.
Continuous cushions and broader unseen-shape/image transfer follow separately.

## Requested model organization milestone

The user requested proper layers, preferably hierarchical, on 2026-09-06. Add
this after the focused strip/cushion work unless a test needs it sooner. Use a
model/assembly root with functional children, e.g. `Model::Frame::Left`,
`Model::Frame::Right`, `Model::Upholstery::Seat`, `Model::Upholstery::Back`, and
`Model::Straps`. Keep construction geometry separate and remove it from final
outputs. Object names complement layers; they do not replace them.

Existing tools expose `create_layer(parent=...)` and attribute assignment by layer
name/full path. Verify actual nesting and full-path resolution before relying on
this: the current creation handler looks up a parent by name. Define saved-file
checks for parent IDs/full paths, object-to-layer assignments, visibility, and no
unintended Default-layer geometry. Test duplicate child names under distinct
parents and save/reopen preservation. The historical chair baseline is unchanged;
it must not retroactively pass a new layer criterion.

Engineering work still ahead: unattended desktop lifecycle, evaluator-process
isolation, held-out comparisons, and explicit model/environment pinning. Recovery
at an idle handoff is verified; this is not proof of every partial-install crash.

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
  live validation/recovery with supervised desktop steps. Unattended installation,
  promotion, automatic continuation of interrupted agent sessions and real-photo
  evaluation are not implemented. The new baseline suite includes seven modeling runs.
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
`CAPTURE_REPAIR.md`, `REFERENCE_LOOP.md`, `BUILDER_LOOP.md`, `SWEEP_CAP_TRIAL.md`, and
`TRIAL_CONTROLLER.md`, `STRIP_MODELER_LOOP.md` and `LIVE_TRIAL.md` are portable summaries. Full local records are under ignored
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
