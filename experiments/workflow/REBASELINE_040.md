# Released 0.4.0 baseline preparation

Status: M0 task declaration complete; runtime installation, identity selection and
fresh agent observations remain pending. No effectiveness claim is made.

## Verified state (2026-09-09)

The clean `harness` checkout started at `8ae969b`; the installed Python server
reports 0.4.0. `describe_capabilities` reports plugin 0.3.2 and advises updating
Rhino's plugin. The loaded assembly MVID is
`addb4d4c-9ce9-4021-b777-53b34874e663`, matching the previously recorded local
overlay. Rhino PID 58823 has one unsaved document (serial 268435457), zero objects,
no experiment marker, and **Modified=true**. This is an observation, not ongoing
permission or a reusable ownership claim.

The supervisor requested permission to close that session without saving, install
0.4.0 and restart as a dedicated test session. Until permission arrives, do not
build/install, reset the document, claim it, or launch live modeling. The current
baseline registry stays unchanged until the released runtime is actually verified.

## Frozen task declarations

The pilot's default is now `release-pilot.json`, with one discovery task in each
of five families: primitives, subtractive solids, posed solids, trimmed patches,
and curved panels. All entries reference new `_v2.json` files. Nine task variants
were redeclared; all prior task files and historical suite manifests are retained.
`unseen_precision_panel.json` is historical only and absent from the active suite.
Other names containing `unseen` or `reserved` do not confer held-out status: these
families have already been spent according to CONTINUE.md.

Tolerances were set before any new modeler run:

- Analytic solids use 0.001 mm for position/dimensions and absolute volume/area
  budgets computed as 1% of the target measurements.
- Curved panels use 0.001 mm for local bounds and rectangular boundaries, and a
  separate `shape_tolerance` equal to 0.5% of the largest task dimension for the
  two sampled surface-deviation checks (0.5 mm on the 100 mm panels).
- Trimmed patches are analytic planes with exact rectangular/circular boundaries:
  their plane, local bounds and boundaries use 0.001 mm, their area budget is 1%
  of the target trimmed area, and their topology and occupancy requirements remain.
  The freeform deviation allowance does not relax these analytic boundary checks.

The optional shape tolerance is restricted to panel tasks and must be positive
and finite. Its absence preserves the original evaluator behavior. The document
absolute tolerance continues to use `linear_tolerance`; allowing a 0.5 mm shape
deviation therefore does not alter Rhino's construction tolerance. Open surfaces
retain the required legacy volume field, which their evaluators do not use.

A surface-only failure remains a failed geometry verdict. During the M1 trace
audit it should be recorded as fidelity, not workflow friction, unless there is
independent evidence that a tool misled the agent. No verdict is silently converted
to a pass. Bounds/topology/boundary checks remain separately visible.

## Verification and next action

Regression tests accept a 0.4 mm panel deviation under v2 and reject that same
measurement under v1, while independently rejecting wrong bounds, a misplaced
boundary, holes and a 0.51 mm deviation under v2. Task validation rejects
nonpositive/nonfinite shape tolerances and use on analytic solids. Suite tests
check all five families and the declared percentage budgets.

Full verification: 285 server tests, 363 experiment tests and 13 contract tests
passed; server Ruff checks passed. Contract tests retain their pre-existing pytest
return-value warnings. No plugin source changed and no plugin build was performed.

Before running the following command, verify a dedicated fresh unmodified Rhino
document, install the release from `releases/0.4.0`, restart, and record the actual
loaded 0.4.0 identity through the selection flow. The pilot itself does not enforce
a release version; its existing runtime and source pins detect changes during a run.

```sh
PYTHONPATH="$PWD" server/.venv/bin/python -m experiments.workflow.pilot experiments/workflow/release-pilot.json --model gpt-5.6-terra --reasoning-effort medium
```

Keep every attempt, save portable verdicts and trace summaries, and add actual
model screenshots to the roadmap when the modeling milestone completes. Do not
rerun a failed task to obtain a pass. M0 is not complete until those observations
and the released baseline identity are recorded.
