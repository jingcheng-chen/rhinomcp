# Placement validation and supervised adoption — 2026-09-07

The reserved cases meet the unchanged acceptance rule: **all eight models pass,
zero MCP calls fail, and median calls decrease in both families**. The tested wording
is now adopted in the production Python MCP `create_object` description. No geometry
code, command schema, defaults or Rhino binary changed. This is a supervised interface
improvement, not automatic promotion.

| Reserved case | Baseline median calls | Candidate median calls | Baseline seconds | Candidate seconds |
| --- | ---: | ---: | ---: | ---: |
| primitives | 4.5 | 4 | 39.87 | 65.56 |
| subtractive-solids | 10.5 | 7 | 87.84 | 52.91 |

The offset box is 64 × 36 × 22 mm with minimum (−110,45,−28). The through-hole
block is 72 × 44 × 18 mm with minimum (140,−80,35), radius 4.5 and axis XY (161,−63).
These dimensions/offsets were reserved after discovery; they are new cases within
the same families, not evidence from a new task family. The candidate, requested
model (`gpt-5.6-terra`, medium reasoning), budgets and evaluators stayed fixed.
Each case ran baseline/candidate, then candidate/baseline, in fresh sessions.

Box timing worsened despite fewer calls. No general speed or cost saving is claimed.
The sample remains small and shares primitive creation across cases. The model alias
is explicit, but the backend snapshot is unavailable. Preserve those limitations when
reporting the result. The earlier eight discovery runs remain separate evidence.

## Every reserved-case run

All rows passed independent saved-file evaluation.

| Family | Pair | Arm | Calls | Seconds | Input / cached input / output tokens |
| --- | ---: | --- | ---: | ---: | --- |
| primitives | 1 | baseline | 5 | 37.22 | 105,431 / 84,480 / 652 |
| primitives | 1 | candidate | 4 | 101.93 | 90,265 / 79,360 / 523 |
| primitives | 2 | candidate | 4 | 29.19 | 88,205 / 53,248 / 483 |
| primitives | 2 | baseline | 4 | 42.51 | 118,908 / 81,408 / 864 |
| subtractive-solids | 1 | baseline | 10 | 65.62 | 176,176 / 151,040 / 1,381 |
| subtractive-solids | 1 | candidate | 7 | 56.54 | 174,207 / 156,928 / 1,098 |
| subtractive-solids | 2 | candidate | 7 | 49.28 | 147,785 / 130,816 / 1,005 |
| subtractive-solids | 2 | baseline | 11 | 110.05 | 141,055 / 124,672 / 1,295 |

Cached input is part of input, not additional usage. Timing includes model/client
latency and gateway guards. These counters are not monetary costs.

## Adoption and preservation

The supervisor added the tested generic anchor-point guidance to the production
function docstring. An AST comparison confirmed that executable code was identical.
A freshly loaded MCP catalog matched the tested candidate after normalizing terminal
whitespace removed by docstring extraction; all schemas/defaults/other metadata matched.
Fresh MCP server sessions load the new description. Existing servers may need restarting
to refresh their advertised tools; the Rhino plugin itself needs no rebuild or restart.

All eight cleanup fingerprints matched. Final runtime: document 268435459, zero
objects, no file path or marker; assembly MVID `326aaa12-b851-4c6a-afcb-45291e734a5c`.
Rhino was initially at its startup screen with no document; a fresh test document was
created. No user model was closed or cleared by this session. Recheck before resuming.

The historical A/B contracts require the old production description. The gateway
now rejects reapplying guidance already in production, so an accidental replay cannot
masquerade as a fresh intervention. To reproduce the old baseline, use pre-adoption
commit `6265121` in an isolated checkout with the unchanged Rhino binary. Detailed
pre-adoption source snapshots remain in the run artifacts.

[Comparison](placement-validation-results.json), [all eight screenshots and hashes](placement-validation-images.json),
and [adoption record](placement-adoption.json) are tracked. Full evidence is local under
`experiments/runs/workflow-comparison-20260907-162356-15ca48a3/`.
The earlier [independent calibration](placement-validation-controls.json) proved correct
fixtures pass and misplaced fixtures fail twice each. Its first elevated inner-profile
generator failed; constructing locally then translating fixed that generator without
changing the evaluator or acceptance rule.

Next: investigate the already-evidenced misleading initial surface bounds through
the shared workflow and existing bounded repair route. Add reusable evaluator adapters
where needed; do not create another object-specific modeling runner. General capability
builder support and automatic promotion remain pending.

Verification: **490 tests pass**, with 12 existing warnings; relevant lint and format
checks pass. The unchanged 61-case live production suite was not rerun for this
docstring-only change.
