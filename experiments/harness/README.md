# Harness definition

**Governing workflow (2026-09-07):** read [workflow/README.md](../workflow/README.md).
Optimize agent effectiveness through MCP changes across tasks. The geometry planner
below judges individual tasks; `roles/workflow_planner.md`, invoked by
`workflow/plan.py`, proposes improvements from cross-task traces. These are distinct
roles. The new proposal route does not yet dispatch a capability builder.


This directory contains the active agents' role instructions. `../runner.py`
loads these files when assembling each session prompt; they are executable
configuration, not a second copy of instructions kept elsewhere.

| Concern | Source of truth |
| --- | --- |
| Description-only paired comparison | `../workflow/compare.py`, `../workflow/placement-trial.json`; reuses the native pilot |
| Shared native-interface pilot | `../workflow/pilot.json`, `../workflow/pilot.py`, `../workflow/native_mcp.py` |
| Modeler behavior | `roles/modeler.md` |
| Planner behavior and evaluator-issue routing | `roles/planner.md`, `../runner.py` |
| Builder behavior | `roles/bounded_builder.md` for per-repair work; `roles/builder.md` for historical capture replay |
| Reviewed per-repair source scope and requirements | `repairs/sweep-cap.json`, copied and hash-pinned in each run |
| Builder checkout, dispatch, review and integrity gates | `../repair.py`, `../builder_mcp.py` |
| Screenshot diagnostic tasks and runner | `../visual_tasks/`, `../visual_runner.py`, `../VISUAL_BENCHMARKS.md` |
| Focused curved-strip diagnosis and independent controls | `../strip_probe.py`, `../strip_measure.cs`, `../strip_controls.cs`, `../STRIP_PROBE.md` |
| Fresh curved-strip tasks and calibrated posed judge | `../tasks/quarter_strip_*.json`, `../strip_task.py`, `../validate_strip_task.py`, `../STRIP_MODELER_LOOP.md` |
| Calibrated layer-tree diagnosis | `../layer_probe.py`, `../layer_measure.cs`, `../layer_controls.cs`, `../LAYER_DIAGNOSIS.md`, `../CONTINUE.md` |
| Bounded layer repair, comparison and accepted baseline | `repairs/layer-parent.json`, `trial-layer-parent.json`, `trial-preservation-v3.json`, `../LAYER_PARENT_TRIAL.md` |
| Fresh assembly task and restricted gateway | `../layer_modeler.py` (fixed task and orchestration), `../layer_modeler_mcp.py` (allowed commands), `../layer_probe.py` (judge) |
| Screenshot gateway and structural audit | `../visual_mcp.py`, `../visual_audit.cs` |
| Modeling tasks and expected measurements | `../tasks/box.json`, `../tasks/posed_prism.json`, `../tasks/through_hole.json`, `../tasks/reference_box.json` |
| Supported task types and input contract | `../tasks/schema.json` |
| Role order, context assembly, session launch, timeouts, output schemas | `../runner.py` |
| Permitted modeling operations and call budget | `../modeler_mcp.py` |
| Document identity guard and controller-only execution | `../bridge.py` |
| Reference drawing generation and fixed-view image delivery | `../references.py`, `../modeler_mcp.py` |
| Trusted saved-file measurements and acceptance | `../evaluate.cs`, `../evaluator.py` |
| Live capture framing and viewport-preservation regression | `../validate_capture.py` |
| Candidate trial transitions, input identity and recovery | `../trial.py`, `../TRIAL_CONTROLLER.md` |
| Frozen live trial cases and evaluator inputs | `trial-suite.json` (43 preservation checks); `trial-sweep-cap.json` (historical 50 checks with three explicit baseline capability failures); `trial-preservation-v2.json` (historical 52); `trial-layer-parent.json` (61, six baseline failures); `trial-preservation-v3.json` (current 61, all true) |
| Live build/probe/test and supervised lifecycle tickets | `../rhino_trial.py`, `../LIVE_TRIAL.md` |
| Assembly metadata without executing candidate code | `../assembly_identity/` |
| Machine installation and Rhino startup | `../README.md`, local `AGENTS.md` |
| Development handoff and next milestone | `../CONTINUE.md` |
| Actual prompts, tool calls, evidence and decisions | `../runs/<run>/` (local, ignored by Git) |

Changing Markdown does not grant permissions. The controller and gateway enforce
tool access and output contracts. The deterministic evaluator is ordinary code,
not an AI role. Fresh builder sessions and review corrections are implemented for a known-defect
pilot. The live adapter connects the controller to a frozen suite; the active improved
baseline uses 61 requirements, including seven fresh modeling sessions. The fresh
layer-assembly task runs separately and is not yet included in that contract.
Desktop quit/install/restart remains supervised through hash-bound lifecycle tickets.
QA-reviewer sessions and automatic promotion are still planned. See
`../BUILDER_LOOP.md`, `../TRIAL_CONTROLLER.md` and `../LIVE_TRIAL.md`.

For every invocation the runner saves the assembled prompt and output schema,
so past runs retain the instructions they actually used even after role edits.
Runs also snapshot evaluator sources and record their hashes. Evaluator corrections
belong to the supervising development workflow, never to a plugin builder seeking
to pass its own candidate. Preserve old verdicts and validate corrections with
independent fixtures before starting another experiment.
Maintain one source for each rule. Extract additional schemas or adapter modules
when their complexity warrants it; a top-level `harness/` rename is unnecessary.

## Dispatch a new bounded repair

The supervisor reviews a scope file and a completed planner diagnosis with action
`plugin_issue`. `repair.py --scope harness/repairs/sweep-cap.json --diagnosis
runs/<strip-run>/summary.json` exports the pinned production revision and launches
a fresh builder. Run from the repository root with the `experiments/` prefix on
both relative paths and use `server/.venv/bin/python -m experiments.repair`.
The scope lists exact existing production source files, instructions and acceptance
requirements. It cannot grant writes to the harness, tests, evaluator or Git metadata.

Each run saves the complete manifest, its hash, original checkout inventory,
development evidence, prompt, builder result, patch and review checkpoint. The
gateway checks the manifest hash on every read/write; review and trial preparation
recheck the pin and the whole checkout. Source additions remain prohibited.
Revision uses the same pinned instructions, with explicit supervisor feedback.
This protects against accidental scope drift; these files are not an OS security
boundary against an adversarial process with filesystem access.

The trial contract can explicitly record observed baseline failures using
`baseline_expectations`. Unlisted cases still require true. The baseline and
restored baseline must match exactly; the candidate must pass every case.
Comparison records improvements, regressions and unmet requirements separately.
False baseline results must be measured before the contract is frozen, never added
post hoc to excuse a failed trial. Existing 43 preservation verdicts remain true.

For the live adapter, launch the controller with an **absolute** repository
`PYTHONPATH`, and explicitly call `rhino_trial.claim_empty(trial_directory)` after
verifying a fresh, empty, unmodified dedicated Rhino document. A relative path is
insufficient because adapter subprocesses run from the trial directory. These are
still supervisor setup steps, not unattended orchestration.

The bounded sweep tool is enabled only for `quarter_annular_strip` tasks. Their
shape is fixed in v1; only translation varies. Saved-file bounds are reported in
the normalized local frame. See `../STRIP_MODELER_LOOP.md` for the paired runtime
comparison and the separate supervisor decision to keep the verified binary active.

## Public assembly tasks

`../assembly_tasks/` stores public task JSON and its schema; `../assembly_task.py`
validates complete ancestors, part assignments and numeric bounds. Run
`../layer_modeler.py` with `--task experiments/assembly_tasks/deep_stand.json` from
the repository root (through `python -m experiments.layer_modeler`). Omitting the
option preserves the original two-cube task. The same narrow gateway applies.

`../validate_deep_layers.py` and `../deep_layer_controls.cs` calibrate the saved-file
judge independently. See `../DEEP_LAYER_TRANSFER.md` for 19 fixture verdicts, nine
live command checks and passing fresh legacy/stand runs. These assembly runs remain
separate from the 61-case production trial contract.

## Continuous surface task and visual progress

`../cushion_task.json` is the fixed public cushion-top task.
`../cushion_modeler.py` uses the existing restricted assembly gateway (which already
allows SURFACE creation); `../cushion_probe.py` and `../cushion_measure.cs` judge the
saved file. `../cushion_controls.cs` creates independent Bezier fixtures;
`../validate_cushion.py` verifies both positive and deliberately flawed examples.
See `../CUSHION_TOP_LOOP.md` for scope and evidence. Run modules from the repository
root using the server virtual environment and an absolute repository PYTHONPATH.

`../model_screenshots.py` provides supervisor-only shaded progress captures with
persisted display-mode recovery records. Add a selected actual model screenshot to
`../roadmap.html#model-progress` and its provenance to `../assets/model-progress.json`
at every modeling milestone. Retain failed attempts as such; pictures are not an
independent geometry verdict. This reporting policy is a persistent user request.

## Closed cushion body and native Join

`../cushion_body_task.json`, `../cushion_body_modeler.py` and
`../cushion_body_probe.py` define the closed-body diagnostic at scales 1 and 0.75.
`../cushion_body_measure.cs` extracts the top and measures closure, boundary planes,
volume and membership. The unchanged open-top judge is reused in normalized
coordinates. `../validate_cushion_body.py` calibrates independent saved controls
from `../cushion_body_controls.cs`.

`../cushion_body_mcp.py` extends the assembly gateway with a UUID-only Join recipe
through the existing production `run_command`. It exposes no agent-authored macro
or script input. This is a harness permission/workflow change, not a new plugin
operation. See `../CUSHION_BODY_LOOP.md` before classifying a missing gateway tool
as a plugin defect. Keep the six-surface assembly and closed-solid verdict distinct.

## Screenshot integration and comparisons

`../integration_runner.py` and `../visual_tasks/barcelona_chair_integration.json`
retain the original public screenshot boundary while adding the verified general
surface/closure/layer workflow guidance. `../integration_mcp.py` exposes attributes
and a UUID-only Join recipe; its read-only planner rejects Join explicitly.
`../integration_audit.py`/`.cs` add repeated saved-file integration observations.
They do not assign a visual score or authorize a builder.

After the diagnostic completes, `../compare_models.py`/`.cs` render neutral-gray
copies of the two saved models with shared camera settings. `../finish_integration.py`
checks ownership, runs the comparison, then restores the originally empty document,
tolerance and display modes. Read `../CHAIR_INTEGRATION.md` and the run checkpoint
before any recovery; partial/failed runs must remain distinguishable from successes.
The old diagnostic runner and historical task remain unchanged.

## Saved-image review and posed cushions

`../saved_review.py` freezes explicit reference/model PNGs for a fresh planner.
`../saved_review_mcp.py` exposes only hash-checked image IDs. Completion requires
matching server logs and image bytes in successful client responses for every
required image; a text result does not establish image review.

`../chair_boundary_probe.py` measures the saved chair's open back edges without
changing the model. `../posed_cushion_modeler.py` tests closing a local analytic
body before applying its pose through existing `modify_object`.
`../posed_cushion_probe.py` inverse-transforms duplicates for the unchanged body
judge; `../validate_posed_cushion.py` checks independent positive/negative fixtures.
See `../POSED_CUSHION_LOOP.md` for limits, recovery evidence and live run results.
