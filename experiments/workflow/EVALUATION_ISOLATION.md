# Evaluation boundary design

Current saved-file measurements are independent of agent completion claims but run
inside whichever reviewed plugin process is active. This is a known remaining
boundary, not an isolated judge.

The next concrete step is deferred evaluation: save/hash each agent artifact and
capture, end the agent session, shut down the candidate Rhino process, restore the
trusted baseline binary in a fresh process, and only then evaluate every frozen
artifact with the same evaluator/source pins. Record the measurement process and
binary identity separately from the modeling process. Missing artifacts, changed
hashes, incomplete sessions and mismatched evaluator identities must fail closed.
Compare only after all required verdicts and baseline restoration are complete.
The original immediate-evaluation runner must retain its behavior for historical
replay; deferred measurements are a declared new comparison version.

This provides process separation for reviewed candidates. It does not by itself
protect controller files from deliberately malicious native code with the same OS
user privileges. An adversarial threat model additionally needs a separate account,
VM or enforced filesystem/process sandbox and explicit access-denial tests. Neither
ordinary path restrictions nor a fresh conversational context should be described
as that security boundary.

Status: design only; do not count as implemented isolation.

## Implemented boundary and live recheck — 2026-09-08

`pilot.run_task(..., defer_evaluation=True)` now saves a hash-bound pending artifact;
`pilot.evaluate_saved` requires a specified trusted binary, unchanged sources/task/model,
an empty owned document and preserved state before writing any verdict. Agent
completion claims do not affect its result. The binary comparator accepts the explicit
`evaluation_mode: trusted_baseline`, restores baseline before invoking this judge,
and writes its final comparison only after all deferred verdicts are available.
Historical immediate evaluation remains the default.

Seven focused tests cover wrong runtime, source/task/model drift, model mutation
during measurement, duplicate evaluation and failed geometry despite agent claims.
A separate live recheck of all eight panel files in the restored baseline agrees
with every original verdict and predicate. All four candidate artifacts were judged
in a different process from their modeling process. Original trial records are
unchanged. See `trusted-panel-recheck.json`; local run
`runs/trusted-panel-recheck-20260908-184332` contains each new measurement.

The full deferred comparator path passed the prospective 12-session planar-region
comparison. Every artifact was judged in the final restored baseline process;
candidate modeling and judging PIDs differ. See planar-region-workflow-results.json.
The same-account adversarial isolation limitation above remains. The earlier design-only
status is historical and superseded by this implementation section.
