# Placement guidance comparison — 2026-09-07

The description candidate met the **preset call-count criterion** in this small
trial. All eight saved models passed the unchanged evaluators; no MCP calls failed.
This is evidence of fewer calls on two discovery tasks, not generalization or a
consistent reduction in latency or token cost. The candidate is not adopted into
production yet. No plugin build, installation or geometry-code change occurred.

| Family | Baseline median calls | Candidate median calls | Baseline median seconds | Candidate median seconds |
| --- | ---: | ---: | ---: | ---: |
| primitives | 4.5 | 4 | 31.80 | 43.55 |
| subtractive-solids | 8.5 | 7 | 49.70 | 47.37 |

Both box baseline agents created at the origin and corrected placement with a
separate translation. Both candidate agents placed the box correctly during creation.
The candidate changes only `create_object.description`, explaining centered boxes
and base-anchored cylinders with generic coordinate formulas. The geometry operations,
parameter schemas, defaults, task instructions and evaluator rules are identical.
The candidate text was written and reviewed by the supervisor; no autonomous builder
session was dispatched in this milestone.

The box's call-count improvement was small: one pair improved from 5 to 4, while
the other tied at 4. Candidate box latency was higher. The Boolean preview and other
verification calls are not automatically classified as waste. Additional cases and
more repetitions are required before treating this as a reliable overall benefit.

## Trial controls and limits

The contract was frozen before launch: two repeats per arm per task, ordered
baseline/candidate then candidate/baseline. Every role session explicitly requested
`gpt-5.6-terra` with medium reasoning and used the same CLI version, 30-call budget,
180-second limit and 12-tool catalog. The CLI's backend model snapshot is unavailable;
the recorded model is a requested alias, not a verified immutable model release.

Source, task, description and evaluator hashes were checked around every session.
The same Rhino process and assembly MVID were retained. Catalog parity checks allow
only the creation-tool description to differ. Each model and screenshot was saved;
every cleanup fingerprint matched. Final document 268435457 was empty, unsaved and
unclaimed; MVID `326aaa12-b851-4c6a-afcb-45291e734a5c`. Recheck runtime on resumption.

The earlier default-model native baseline is discovery evidence only and is excluded
from this comparison. Each task uses box creation, so two families do not by themselves
establish broad transfer. No held-out task was run in this milestone. The trial's
preset criterion requires all passes, lower median calls in each family, and no
increase in failures; it does not require lower time or token totals.

## Every run

| Family | Pair | Arm | Verdict | Calls | Seconds | Input / cached input / output tokens |
| --- | ---: | --- | --- | ---: | ---: | --- |
| primitives | 1 | baseline | pass | 5 | 38.05 | 104,259 / 83,456 / 535 |
| primitives | 1 | candidate | pass | 4 | 30.19 | 88,743 / 68,352 / 460 |
| primitives | 2 | candidate | pass | 4 | 56.91 | 73,393 / 54,272 / 382 |
| primitives | 2 | baseline | pass | 4 | 25.56 | 71,607 / 43,264 / 491 |
| subtractive-solids | 1 | baseline | pass | 9 | 53.56 | 145,713 / 110,592 / 1,136 |
| subtractive-solids | 1 | candidate | pass | 7 | 47.52 | 145,962 / 125,696 / 882 |
| subtractive-solids | 2 | candidate | pass | 7 | 47.23 | 144,805 / 121,856 / 955 |
| subtractive-solids | 2 | baseline | pass | 8 | 45.84 | 123,174 / 100,608 / 968 |

Cached tokens are a subset of input tokens. These are CLI usage counters, not money
spent; guard overhead, caching and service latency affect time and usage. Full traces,
invocations and source snapshots are local under
`experiments/runs/workflow-comparison-20260907-101633-464f2821/`.

[Comparison](placement-results.json), [input hashes](placement-input-pins.json),
[candidate text](placement-guidance.txt), [frozen contract](placement-trial.json),
and [all eight screenshot/model hashes](placement-images.json) are tracked.

Next: reserve new placement cases with different dimensions and world offsets,
including cutter placement, freeze their acceptance criteria, and run paired validation
with the same agent configuration. Then review production adoption. These will be new
cases within the existing task families, not evidence of an unseen family. Keep the
separate surface-feedback investigation and general capability-builder route visible.

Verification: **487 tests pass**, with 12 existing warnings; focused lint/format checks
pass. The 61-case live production suite was not rerun because production code and the
loaded binary were unchanged. No automatic promotion is authorized.
