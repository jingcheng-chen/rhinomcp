# Continue autonomous RhinoMCP improvement

This is the entry point for a development agent with no prior chat context.
Last updated: 2026-09-08. Verify repository and application state before acting;
the previous session's running processes and document selection are not assumptions.

## Governing direction — user clarification, 2026-09-07

Optimize the MCP toolset by inspecting agent workflows across tasks. Modeling is
benchmark execution, not the product being optimized. Do not continue the historical
chair/cushion progression as the main objective. Read `workflow/README.md` first for
the revised cycle and implementation boundary. New capabilities, tool ergonomics and
reusable workflows are legitimate proposals even when no command is defective.
A task success or additional tests alone do not establish an improved MCP tool.

## Current handoff — surface trial accepted; baseline restored

Read [workflow/SURFACE_FEEDBACK.md](workflow/SURFACE_FEEDBACK.md). The fresh builder's
bounds patch passed all 80 live checks, fixing eight known failures while preserving
the prior 61 requirements. Full baseline/candidate/restored suites completed, including
21 fresh modeling sessions. Controller `accepted_trial`, `runtime_dirty=false`,
`promoted=false`. Production source is unchanged; the repaired binary is NOT active.

Trial: `runs/repair-20260907-171657-ec239178/trial-9983c15f`. Candidate MVID:
`606ab732-416a-4b80-b041-19a264b21b2f`. Restored baseline MVID:
`326aaa12-b851-4c6a-afcb-45291e734a5c`, PID 66421, empty unsaved unclaimed document
268435457 at completion. Recheck state before proceeding. All 492 development tests
pass; candidate build has zero warnings/errors, 251 candidate tests and lint pass.
The roadmap saves images for every model/fixture in all three phases.

The warmed operation probe (`runs/bounds-cost-20260908-090849`) measures roughly
0.003–0.019 ms added per deep-copy bounds call on three small Breps. This is neither
a large-model stress test nor an agent-efficiency claim. Full details/hashes are in
`workflow/surface-feedback-trial.json`.

Next bounded milestone: add generic curved-panel and trimmed-patch task/evaluator
registrations to the shared native runner, calibrate correct and flawed fixtures,
then run repeated baseline/candidate sessions with pinned agent settings. Keep the
existing repair unchanged during comparison. Reuse the accepted binary only through
a reviewed supervised runtime transition; preserve baseline recovery. Decide source
adoption after workflow evidence. General new-tool builder and automatic promotion
remain pending; do not resume chair-specific scripts as the optimization target.

## Current handoff — surface feedback candidate prepared

Read [workflow/SURFACE_FEEDBACK.md](workflow/SURFACE_FEEDBACK.md). Independent generic
probes reproduce eight failing predicates out of 19: curved surface feedback is flat,
and creation-time rotation/scaling use incorrect pivots. Four models/screenshots and
analytic expectations are retained. The trimmed-solid control passes. A fresh planner
classified a plugin defect; a fresh bounded builder produced a reviewed two-file patch.
The portable patch and baseline evidence live in `workflow/surface-feedback-*`.

Candidate is NOT built, installed or adopted. All 491 development tests pass; they do
not validate this C# repair. Next: use the existing supervised candidate lifecycle,
run frozen surface probes and the 61-case preservation contract, then compare fresh
workflows. Measure duplication overhead before claiming efficiency. Production
placement guidance remains adopted. Recheck runtime ownership and binary identity.
Builder run: `runs/repair-20260907-171657-ec239178`; scope:
`harness/repairs/surface-feedback.json`. Serializer eligibility was added to the
controller, while exact-path and whole-checkout restrictions remain enforced.

Older handoffs below are historical where they conflict with this section.

## Current handoff — reserved validation passed; guidance adopted

Read [workflow/PLACEMENT_VALIDATION.md](workflow/PLACEMENT_VALIDATION.md). The eight
reserved-case runs all pass with zero failed calls. Median calls are 4.5→4 for the
offset box and 10.5→7 for the elevated through-hole task. Box timing worsens, so do
not claim general speed/cost improvement. These are new cases in existing families,
not a new held-out family; requested model alias/effort are pinned, backend snapshot
is unavailable. The earlier discovery result remains separately preserved.

The supervisor adopted the tested anchor-point wording in production
`server/src/rhinomcp/tools/create_object.py`. Only its docstring changed; AST and
published-catalog checks preserve execution, schemas and defaults. No Rhino build
or install was needed. All 490 tests pass. This is supervised description adoption,
not automatic promotion. Fresh MCP sessions expose it; already-running servers may
need restart to refresh schemas. The gateway now rejects duplicate application of
the adopted suffix. Historical A/B replay requires pre-adoption baseline `6265121`.

All eight new screenshots/models are saved and on the roadmap. Final runtime document
268435459 is empty, unsaved and unclaimed, with the same assembly MVID as discovery.
The previous user-work blocker is resolved; this session created a new test document
from Rhino's startup screen. Recheck application state before any future trial.

Next bounded step: diagnose the recorded misleading initial surface-bounds response,
using independent probes and the existing bounded repair route. Keep workflow/task
performance distinct from geometry acceptance. Extend shared evaluator adapters when
needed instead of adding object-specific runners. General new-capability builder
support and automatic promotion remain pending. Older next steps below are historical.

## Latest milestone — placement guidance comparison (2026-09-07)

Read [workflow/PLACEMENT_TRIAL.md](workflow/PLACEMENT_TRIAL.md). The shared runner
now accepts explicit model/reasoning settings. A description-only comparator reuses
that runner with frozen inputs and counterbalanced order. Eight fresh sessions used
`gpt-5.6-terra`, medium reasoning, the same 12 native tools and unchanged evaluators.
All eight models pass; zero calls fail. Median calls decrease from 4.5 to 4 for the
box and 8.5 to 7 for the through-hole task. The preset call-count criterion passes,
but timing is mixed: the candidate box runs are slower. Do not claim overall speed,
cost savings or generalization. Requested alias is pinned; backend snapshot is unknown.

The candidate is a supervisor-authored description suffix explaining centered boxes
and base-anchored cylinders. It was served as an experimental metadata intervention,
not adopted into production. No builder, install or geometry change occurred. All
487 tests pass. All eight artifacts/screenshots and preservation evidence remain
recorded; the roadmap shows every output. Runtime was empty/unclaimed at completion.

Next bounded step: freeze new placement cases with different dimensions and world
offsets (including cutter placement) before running paired validation using the same
agent settings. These are withheld cases within existing families, not a new held-out
family. Review production adoption only after validation; do not silently change the
candidate or acceptance rules. Preserve the current positive-but-limited trial.
General capability-builder/promotion support and the surface-feedback investigation
remain pending. Do not return to chair-specific construction as the primary work.
Older next-step prose below is historical where it conflicts with this milestone.

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

## Previous milestone: fresh-agent benefit and active improved baseline

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

## Previous milestone: calibrated layer-tree diagnosis

Read `LAYER_DIAGNOSIS.md` and `layer_probe.py`. The fixed two-cube assembly requires
`Assembly::Left::Part` and `Assembly::Right::Part`, with duplicate leaf names.
Nine independent saved fixtures validate parent-ID reconstruction, object layer
indices, visible/unlocked ancestors and geometry; correct passes and eight flaws
fail, each identically twice. File reads preserve artifact hashes.

Live run `runs/layers-20260906-144144-a4abc4d4/` confirms `create_layer` cannot resolve
full-path parents: it creates a root-level Part, the second Part errors, and object
assignment fails because the requested children do not exist. A missing parent
also silently creates a root. Existing empty layers remain in the diagnostic file;
its strict exact-tree verdict includes these extras, while parent IDs and failed
assignments independently demonstrate the specific limitation. The fresh planner
returns `plugin_issue`. No builder has been dispatched for layers yet.

Cleanup preserved the original document fingerprint. The accepted capped runtime
is unchanged, PID 94887 / MVID `79b1500e-e20d-47af-9c83-6f915729a712` at this run;
recheck live ownership, empty contents, marker and unsaved state before reuse.
The saved chair is untouched. **404 developer tests pass** (163 experiment,
228 server, 13 contract), plus experiment lint/format. The 52-case baseline contract
is unchanged and its earlier pass remains historical; no new preservation run was
needed for this harness-only diagnostic. Source snapshots preserve failed setup
attempts and the completed evidence separately.

## Previous milestone: accepted layer-parent repair and fresh-agent assembly

Read `LAYER_PARENT_TRIAL.md`. A fresh bounded builder produced the three-file
repair scoped by `harness/repairs/layer-parent.json`. Full parent paths resolve
case-insensitively, unique short names remain supported, and missing/ambiguous
parents and duplicate siblings fail clearly without inserting layers. The exact
reviewed patch is retained as `harness/repairs/layer-parent.patch` and adopted in
production source. Python documentation and schema match the C# behavior.

Trial `runs/repair-20260906-153718-295e7376/trial-f5110bdd/`: baseline 55 true / six
known layer failures; candidate **61/61 true**, six gains and no regressions;
restoration exactly reproduced the original vector. Final trial state is
`accepted_trial`, `runtime_dirty=false`, `promoted=false`. All 21 fresh modeling
sessions across the three suite passes succeeded. The controller's restoration
policy is unchanged. `harness/trial-preservation-v3.json` now requires all 61 true
for future repairs; retain historical known-failure contracts for replay only.

After restoration, the supervisor separately adopted the tested source and exact
binary. Fresh assembly run `runs/layer-model-20260906-160939-63c22fdf/` passes:
Assembly::Left::Part and Assembly::Right::Part with correct object assignments,
visibility, solid validity and bounds. Both saved-file measurements agree and the
fresh planner accepts. Document cleanup preserved the original fingerprint.
`layer_modeler.py` owns this fixed task and orchestration; `layer_modeler_mcp.py`
limits tool access. This separate task is not counted in the 61-case trial contract.

**Current runtime at handoff:** PID 84726, MVID
`326aaa12-b851-4c6a-afcb-45291e734a5c`, SHA-256
`a8791fdfd00500113f138375a6b196d32b191873a1c5ef228e4fe1fd1df193e1`.
One empty unsaved document, serial 268435457, marker none, modified=true after
cleanup. Verify again before reuse. Trial `adoption.json` records the separate
`accepted_active_baseline` / runtime promotion decision. The capped-only baseline
binary is retained for recovery. The saved original chair is untouched.

**417 developer tests pass** (166 experiment, 238 server, 13 contract); experiment
lint/format and server source lint pass. Candidate build: zero warnings/errors.
The fresh assembly demonstrates one successful task, not broad transfer or a paired
agent-efficiency improvement. The geometry judge checks solids and bounds rather
than complete shape equivalence; keep this scope explicit. Model version pinning
and stronger process isolation remain outstanding.

## Previous milestone: deeper assembly transfer

Read `DEEP_LAYER_TRANSFER.md`. Public assembly data now lives in
`assembly_tasks/deep_stand.json`, validated by `assembly_tasks/schema.json` and
`assembly_task.py`. Run `layer_modeler.py` with `--task` to use that specification;
without it, the original two-cube prompt remains supported. Source and task inputs
are snapshotted for each run.

A fresh agent builds a three-part stand under nine layers, with four-level paths
and repeated intermediate Support and leaf Part names. All 14 saved-file predicates
pass and the fresh planner accepts. A fresh legacy two-cube loop also passes.
Independent calibration gives all 19 expected verdicts twice (nine legacy, ten
stand); nine live layer-command regression checks pass. Document fingerprints
are preserved. **425 developer tests pass** (174 experiment, 238 server, 13 contract).

Campaign: `runs/deep-layer-calibration-20260906-162009-232d6665/`.
Legacy modeling: `runs/layer-model-20260906-162152-1456b3ab/`.
Stand modeling: `runs/layer-model-20260906-162305-f09de086/`.
Production source and installed binary are unchanged. Runtime remains PID 84726,
MVID `326aaa12-b851-4c6a-afcb-45291e734a5c`, same SHA recorded above, empty unsaved
document serial 268435457, marker none. Verify before reuse. The original chair
file hash is unchanged. No new defect was found and no builder was dispatched.

The 61-case contract is unchanged; its full pass is historical, not rerun for this
harness-only extension. Do not resume a completed historical trial against changed
source hashes. This is limited organization transfer, not broad generalization;
geometry checks still establish valid solids and bounds, not complete shape equivalence.

## Previous milestone: continuous cushion top and phase screenshots

Read `CUSHION_TOP_LOOP.md`. The fixed public `cushion_task.json` describes one
100×100 mm, four-lobed open top surface with recessed crossing seams. A fresh
modeler uses the existing assembly gateway and SURFACE creation. No production
plugin/server/schema change is needed. `cushion_probe.py` measures the saved file
through `cushion_measure.cs`: one valid untrimmed open face, C1 continuity, exact
layer tree/assignment, XY bounds, 1,681 surface samples and 441 target distances.
Error limits remain 1 mm. This is a finite-sample geometry test, not a visual score.

Twelve independent Bezier fixtures return their expected verdicts twice; the two
positives include a changed parameter domain. Final calibration:
`runs/cushion-calibration-20260906-163932-cefbb616/`.
First fresh run `runs/cushion-model-20260906-163948-e09d1b86/` passes geometry
(maximum sampled height error 0.24092 mm), but its new screenshot helper failed to
restore display modes before the planner. See its `capture-incident.json`; original
modes were not persisted and exact display restoration is not claimed for that run.
Geometry/layers were cleaned up; the supervisor reset dedicated views to Wireframe.
The corrected helper persists and verifies modes around capture.

Second fresh run: `runs/cushion-model-20260906-164426-a4a9967e/`, geometry passes
with maximum sampled height error 0.12890 mm and shaded Perspective/Top/Front
screenshots. The fresh planner accepts; cleanup preserves the original document fingerprint.
Display-mode restoration passes. Task and evaluator bytes are unchanged
between runs. **438 developer tests pass** (187 experiment, 238 server, 13 contract),
plus the focused 13 tests after the screenshot-helper correction. Verify final
`summary.json` and `preservation.json` before any reuse.

Final runtime: PID 84726, MVID `326aaa12-b851-4c6a-afcb-45291e734a5c`,
same installed SHA as above, empty unsaved document 268435457, marker none.
Original chair hash and pinned inputs remain unchanged; see run `completion.json`.

The roadmap now includes nine actual modeling-phase screenshots with evidence
links. Selected images and `assets/model-progress.json` are tracked. Historical
models, including the original chair, are not relabeled as new results. The accepted
61-case contract remains unchanged; its full pass is historical and not rerun for
this harness-only task. A passing surface is not evidence of a plugin-code repair.

## Latest milestone: closed cushion body through existing tools

Read `CUSHION_BODY_LOOP.md`. The public `cushion_body_task.json` adds a flat bottom
at Z=0 and four vertical walls to the analytic smooth top. Scale 1 has a 100×100 mm
footprint and minimum vertical thickness 10 mm; scale 0.75 scales all dimensions.
Sharp C0 perimeter joins are explicitly accepted; rounded/rolled cushion edges
are not demonstrated. Required output is one valid solid `cushion_body` on
`Cushion::Upholstery::Body`.

The existing production `run_command` can invoke native Join. The harness-only
`cushion_body_mcp.py` exposes a fixed UUID-only selection/Join recipe alongside the
existing restricted creation tools. No arbitrary agent-authored macro is allowed.
This expands the task gateway, not production plugin code. Do not classify a missing
operation in a narrow gateway as a missing RhinoMCP operation without checking.

`cushion_body_probe.py`/`cushion_body_measure.cs` reuse unchanged top checks in
normalized coordinates and add closure, naked-edge, boundary-plane, underside,
volume and membership requirements. Twelve calibration verdicts pass twice,
including independent correct full-size/scaled bodies and wrong-scale evaluation.
Campaign: `runs/cushion-body-calibration-20260906-165916-e73f1c0b/`.
Full-size model: `runs/cushion-body-model-20260906-170006-73abe04e/` passes all 17
predicates; fresh planner accepts. Maximum sampled height error is 0.65252 mm.
Scaled model: `runs/cushion-body-model-20260906-170246-4abd21d9/`, also 17/17
with fresh planner acceptance; maximum sampled height error 0.18069 mm. Both runs
preserve the original document fingerprint and restore all four display modes.
The scaled agent recovered a layer-assignment-before-creation error. The campaign's
`modeling-results.json` records both. The roadmap has 11 pictured modeling phases.
Final `completion.json` verifies both artifact hashes, pinned inputs and original
chair bytes. Runtime remains PID 84726 / MVID `326aaa12-b851-4c6a-afcb-45291e734a5c`,
empty unsaved document 268435457, marker none, modified=true after cleanup; verify
again before reuse. Installed SHA remains `a8791fdfd00500113f138375a6b196d32b191873a1c5ef228e4fe1fd1df193e1`.

**451 developer tests pass** (200 experiment, 238 server, 13 contract), plus
experiment lint/format. The accepted 61-case production-repair contract is unchanged;
its earlier full pass is historical and not rerun for this harness-only task.
Open-top evaluator source remains unchanged. No build, installation or bounded
plugin builder was needed. Selected actual shaded captures are tracked in the
roadmap gallery with source hashes; original saved chair remains historical.

## Latest chair integration diagnostic

Run `runs/integration-20260906-171254-6eb9935e/`; see `CHAIR_INTEGRATION.md`.
A fresh screenshot-only modeler used the four original public views with continuous
cushion/closed-strip guidance and the eight-layer tree. 28 valid objects; all nine
structural observations and five of six integration observations pass. Seat and
frame are solid; the six-face back cushion has four naked edges. **Partial, visual
acceptance unscored.** No plugin defect or promotion is established.
The new File3dm audit initially failed; an explicit-iteration correction recovered
repeat-identical measurements of the unchanged artifact. Recovery sources/logs persist.

Fresh planner returned modeling feedback but failed to use image tools. Its visual
claims are unsupported. See `review-evidence-supervisor.json`; original summary is
retained. Future summaries record required image delivery, with a regression test;
updated tool-specific prompts have not yet been validated in a fresh session.
Matched model-to-model Perspective/Front/Right captures preserve identical camera
records and both source files. Selected images/provenance are tracked in assets;
roadmap shows all 12 phases and paired chair comparisons.

**Correction from the next milestone:** that cleanup check omitted hidden objects.
The comparison left 65 hidden copies; the next saved-file check caught them.
They have since been archived, verified and removed, and live enumeration/cleanup
now pass a hidden-object regression. See `POSED_CUSHION_LOOP.md`.
Historical runtime PID 84726 / document 268435457 / MVID
`326aaa12-b851-4c6a-afcb-45291e734a5c`, marker none, unsaved modified=true.
Reverify before reuse. New chair SHA `8d283f733e44ef95764d5c57c68d56b39b4e7bab38030b78a142a4821a06b2b6`.
458 developer tests (207 experiment, 238 server, 13 contract); production plugin and
accepted 61-case contract unchanged, historical full live pass not rerun here.

## Latest: verified image review, boundary diagnosis and posed cushions

Read `POSED_CUSHION_LOOP.md`. The original image gateway succeeds in a fresh explicit
probe. A fresh saved-image review receives all seven selected PNGs; source hashes
and client-returned image bytes match. `saved_review.py`/`saved_review_mcp.py` provide
a read-only frozen-pack route independent of live Rhino. Missing image delivery
marks the review incomplete. Exact cause of the previous planner's tool-use failure
is not established; visual similarity remains qualitative/unscored.

Boundary read `runs/chair-boundary-20260906-173916/` finds two naked-edge pairs on
the unchanged back cushion. Matching endpoints hide sampled curve gaps up to about
0.087 mm versus 0.01 mm tolerance. No plugin defect follows; do not raise tolerance
just to make a closed-solid verdict pass.

The first posed-cushion run `...-174420-3b37dd79` saves 65 hidden comparison copies
plus the new cushion, correctly failing uniqueness. The planner proposed excluding
hidden extras; the supervisor rejected that because a clean saved file is required.
The old comparison's unchecked deletion of hidden objects and default enumeration
caused the contamination. **The earlier empty-document claim was incorrect.**
Recovery archives and verifies those exact copies against baseline geometry before
removal. `bridge.identity`, `rhino_trial.runtime`, `strip_probe.fingerprint` and
`compare_models.cs` now include hidden/locked objects; comparison shows copies before
checked deletion. Live regression `.../comparison-cleanup-validation-20260906-175039/`
counts normal/hidden/locked objects, preserves a hidden sentinel and removes every
comparison copy. Original chair and integration artifacts remain byte-identical.

`posed_cushion_modeler.py` builds and joins the analytic closed cushion locally,
then uses existing modify_object with bbox-center compensation to implement world
rotation/translation. `posed_cushion_probe.py` inverse-transforms a duplicate for
the unchanged 17 body predicates. Calibration `...-174320` has 13 expected verdicts
twice, including wrong pose/scale and open bodies. An earlier fixture writer failed
to persist transforms; retained failed campaign `...-174133` was corrected by adding
transformed duplicates to new files, without relaxing the judge.

Clean fresh repeat `runs/posed-cushion-model-20260906-175112-f2f8dd8d/` passes all 17
checks, with one saved solid, zero naked edges and 0.24092 mm maximum sampled height
error. A fresh geometry planner accepts. The alternate run `...-175410-5bf01af5` fails with 42 separate objects after
the agent misread flat returned bounds and exhausted its call budget. Its planner
input exceeded the CLI limit; compact feedback recovered a fresh planner without
changing the artifact. See `summary-recovered.json` and `planner-recovery.json`. Failed/successful phase
screenshots are distinct. This proves a planar-perimeter posed cushion workflow,
not closure of the original chair's curved perimeter or accurate chair padding.

## Next concrete milestone — common workflow, not another model

`workflow/audit.py` now audits recorded agent workflows independently of geometry.
The registry spans seven historical runs across five families. It reports attempts,
failures, schema queries, duration, usage and independent verdicts. Historical runs
are explicitly not eligible for causal plugin-version comparisons. Missing data is
unknown, not zero. A fresh workflow planner uses audited evidence to propose changes
through a new contract supporting defects, capabilities, ergonomics and reusable
workflows. Proposals require success/efficiency metrics, multiple validation families
and held-out families; they grant no builder or installation permission.

Next implement a shared task/session contract and migrate a small non-chair pilot
through common runner/gateway adapters, recording comparison pins. Use reliable
geometry feedback as the first investigation: the existing surface-bounds probes
are evidence, not the whole benchmark. Validate on genuinely different task families
with fixed inputs/agent/evaluator before claiming broad benefit. Do not create more
object-specific runners. Preserve old task evaluators and historical scripts.

Then extend the bounded builder for explicitly declared new source files and protocol
updates. The current repair.py/bounded_builder route remains defect-only/edit-only;
new capability proposals must not be misrouted through it. See workflow/README.md.
A shared comparison/promotion path is still pending. No plugin improvement is claimed
from this workflow audit, and no Rhino modeling/build/install ran in this milestone.

Historical runtime at the last live handoff (reverify before any live work): PID 84726,
document 268435457, MVID `326aaa12-b851-4c6a-afcb-45291e734a5c`, empty including
hidden objects, marker none. Original chair files remain reference benchmarks.
The accepted 61-case production contract is unchanged; its live pass is historical.
Screenshots remain visible for all 15 historical modeling phases.

## Requested visual progress policy

The user requested a screenshot of the model at each modeling phase on 2026-09-06.
Keep actual screenshots visible in the roadmap gallery (`#model-progress`), with
phase labels, evidence links and clear geometry/visual verdicts. Keep failed and
successful attempts distinct. Do not use illustrations as result evidence or imply
that separate benchmark objects are successive chair versions.

Track selected images and their provenance/hashes in `assets/model-progress.json`;
raw run images alone are ignored and do not survive checkout. New surface tasks
should include shaded Perspective, Top and Front views using the supervisor helper
`model_screenshots.py`, in addition to any wireframe diagnostic. Preserve display
modes, cameras, saved model bytes and pre-existing document contents.

## Requested model organization milestone

The user requested proper layers, preferably hierarchical, on 2026-09-06. The
basic capability is now validated; apply it in new modeling tasks. Use a
model/assembly root with functional children, e.g. `Model::Frame::Left`,
`Model::Frame::Right`, `Model::Upholstery::Seat`, `Model::Upholstery::Back`, and
`Model::Straps`. Keep construction geometry separate and remove it from final
outputs. Object names complement layers; they do not replace them.

Existing tools expose `create_layer(parent=...)` and attribute assignment by layer
name/full path. Full-path parent resolution and the basic two-branch assembly now pass. Keep saved-file
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

## Representative-interface check (2026-09-07)

The fresh workflow planner proposed batch schema discovery. Supervisor triage defers
it: repeated schema calls were observed through our custom gateways, not ordinary
production MCP usage. See [results](workflow/RESULTS.md) and
[proposal triage](workflow/proposal-triage.json). A valid proposal is not an approved
change. The next pilot must expose representative native MCP tool schemas and record
comparison pins. Reuse existing tasks/evaluators; do not add another object-specific
runner. Reliable surface feedback remains an independent investigation, suitable
for the existing repair route once cross-task acceptance cases are fixed.
