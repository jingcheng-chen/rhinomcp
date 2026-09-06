# Harness definition

This directory contains the active agents' role instructions. `../runner.py`
loads these files when assembling each session prompt; they are executable
configuration, not a second copy of instructions kept elsewhere.

| Concern | Source of truth |
| --- | --- |
| Modeler behavior | `roles/modeler.md` |
| Planner behavior and evaluator-issue routing | `roles/planner.md`, `../runner.py` |
| Builder behavior | `roles/bounded_builder.md` for per-repair work; `roles/builder.md` for historical capture replay |
| Reviewed per-repair source scope and requirements | `repairs/sweep-cap.json`, copied and hash-pinned in each run |
| Builder checkout, dispatch, review and integrity gates | `../repair.py`, `../builder_mcp.py` |
| Screenshot diagnostic tasks and runner | `../visual_tasks/`, `../visual_runner.py`, `../VISUAL_BENCHMARKS.md` |
| Focused curved-strip diagnosis and independent controls | `../strip_probe.py`, `../strip_measure.cs`, `../strip_controls.cs`, `../STRIP_PROBE.md` |
| Requested hierarchical layer policy (upcoming) | `../CONTINUE.md` |
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
| Frozen live trial cases and evaluator inputs | `trial-suite.json` (43 preservation checks); `trial-sweep-cap.json` (50 checks with three explicit baseline capability failures) |
| Live build/probe/test and supervised lifecycle tickets | `../rhino_trial.py`, `../LIVE_TRIAL.md` |
| Assembly metadata without executing candidate code | `../assembly_identity/` |
| Machine installation and Rhino startup | `../README.md`, local `AGENTS.md` |
| Development handoff and next milestone | `../CONTINUE.md` |
| Actual prompts, tool calls, evidence and decisions | `../runs/<run>/` (local, ignored by Git) |

Changing Markdown does not grant permissions. The controller and gateway enforce
tool access and output contracts. The deterministic evaluator is ordinary code,
not an AI role. Fresh builder sessions and review corrections are implemented for a known-defect
pilot. The live adapter connects the controller to the frozen 43-case Rhino suite.
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
