# Reviewed binary workflow comparison

The binary route reuses `pilot.run_task` and `rhino_trial.lifecycle`; the existing
`compare.py` remains description-only. No candidate build, source adoption or
installation path is embedded in this route.

## Frozen panel trial

`panel-binary-trial.json` selects the unchanged baseline and candidate from the
accepted surface-feedback trial. The prior trial is immutable. This new comparison
has its own directory, copied binaries, source/task/catalog hashes and lifecycle
requests. Raised and depressed task/evaluator definitions are unchanged after
discovery. Both tasks use 24 calls, 240 seconds, gpt-5.6-terra/medium, and two
baseline/candidate pairs ordered AB then BA per task. Backend snapshot is unknown.

The prespecified rule reports correctness per task first. Any lower candidate pass
count blocks a positive overall signal. Increased pass count is a correctness signal;
fewer median calls counts as an efficiency signal only when both arms pass both
repeats and failed calls do not increase. Time and token measurements are secondary.
An observed signal with two repeats is descriptive, not statistical proof or a
promotion decision. Both panels belong to one discovery family.

## Supervisor review

The existing bounds patch changes only the shared Brep-bound helper and its callers.
The prior independent 80-case trial established eight repairs and no regressions;
it did not establish agent-efficiency benefit. Reuse precisely the recorded binaries,
without rebuilding or changing construction instructions. Inspect loaded identity
and ownership at each lifecycle handoff; service tickets under LIVE_TRIAL.md.
The user authorized continued roadmap development and validation on 2026-09-08.

The route records dirty state before restart, verifies both arms, retains failures,
rejects input drift, prevents task replay, and restores baseline on normal exit or
handled failure. Hard termination requires the explicit recovery command after the
old controller is stopped. The shared lock prevents a second controller running
concurrently. Recovery does not clear an unfinished model or silently rerun it.
Evaluation still executes within reviewed Rhino code; this is not malicious-code
isolation. Desktop lifecycle remains supervised.

## Commands

From the repository root with a fresh empty dedicated Rhino document:

```sh
PYTHONPATH=. server/.venv/bin/python -m experiments.workflow.binary_compare prepare experiments/workflow/panel-binary-trial.json --review-file experiments/workflow/BINARY_COMPARISON.md
PYTHONPATH=. server/.venv/bin/python -m experiments.workflow.binary_compare run /absolute/path/to/new-comparison
PYTHONPATH=. server/.venv/bin/python -m experiments.workflow.binary_compare recover /absolute/path/to/interrupted-comparison
```

The command prints lifecycle ticket paths. The supervisor verifies the owned empty
runtime, quits Rhino, installs the ticket's exact binary using local instructions,
starts a fresh document/listener, and acknowledges the request hash. Acceptance
requires both comparison evidence and terminal state `complete` with verified
baseline restoration. A comparison result written before recovery is provisional.

## Completed live result — 2026-09-08

Run `workflow-binary-20260908-181813-4eec688b` completed all eight sessions and four
supervised transitions. Final stage `complete`, `runtime_dirty=false`, `promoted=false`.
The restored baseline MVID is `326aaa12-b851-4c6a-afcb-45291e734a5c` in PID 46932,
empty unsaved unclaimed document 268435457 at completion. Recheck before reuse.

| Task | Baseline pass | Candidate pass | Median calls B → C | Median seconds B → C |
| --- | --- | --- | --- | --- |
| Raised panel | 2/2 | 1/2 | 17 → 6.5 | 152.10 → 79.33 |
| Depressed panel | 2/2 | 1/2 | 10.5 → 3.5 | 94.35 → 37.07 |

All calls returned without errors. Each arm contains four fresh sessions. Both
candidate failures claim completion but have the wrong shape: local peak 80 instead
of 20 mm and trough -60 instead of -15 mm. The inputs treat interpolation points as
Bezier control points. No construction strategy or task wording was changed.

The prespecified result is **no benefit established**. Lower task success blocks an
efficiency claim; a small stochastic sample does not prove the repair caused the
failures. The earlier 80-case defect repair remains separately valid and immutable.
The candidate remains unadopted. All eight outputs, verdicts, metric/source pins and
image hashes are in `panel-binary-results.json` and the roadmap gallery.

A distinct surface-input wording hypothesis is recorded in
`surface-semantics-observation.md`. It requires a new frozen comparison.
