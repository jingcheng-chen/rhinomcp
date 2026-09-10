# Released 0.4.1 baseline — M0b

Completed 2026-09-10 on the supervised host. M5 remains deferred. Package Manager
installed 0.4.1, Rhino restarted, and `select_release` verified tag/source equality,
server/plugin versions, the fresh empty document and loaded binary identity.
The previous 0.4.0 selection is retained in `baseline-history.json`.

Loaded package: `packages/8.0/rhinomcp/0.4.1/net8.0/rhinomcp.rhp`.
MVID: `2c401408-5a49-4a4b-831d-fa9f5cb913c5`.
SHA256: `6452bb1b574f2b3566576e297dc9a80dfd4a3b83bfd937a00dcc964e9b01b6da`.
Selection journal: `experiments/runs/selection-release-20260910-140702-e1b9dacd`.
No local plugin build or production source change was needed.

## Frozen observations

The unchanged versioned release tasks ran once each with the 14-tool native
subset. The unchanged M2 scene tasks then ran once each with the full production
catalog. All used fresh Codex gpt-5.6-terra/medium sessions and the existing pilot,
independent saved-file evaluator and cleanup. Release budgets were 30 calls/240
seconds; scene budgets were 50 calls/240 seconds. No attempt was repeated.

| Family | Catalog | Saved-file verdict | Calls | Failed calls |
| --- | --- | --- | ---: | ---: |
| Primitives | Native | Pass | 3 | 0 |
| Subtractive solids | Native | Pass | 7 | 0 |
| Posed solids | Native | Pass | 8 | 0 |
| Trimmed patches | Native | Pass | 15 | 0 |
| Curved panels | Native | Fail | 7 | 0 |
| Editing existing | Full | Pass | 14 | 0 |
| Small assemblies | Full | Pass | 12 | 0 |
| Document inspection | Full | Pass | 4 | 0 |
| Recovery | Full | Pass | 8 | 0 |

Eight of nine saved files pass; all 78 tool calls return without errors. All
preservation checks pass. The panel's local Y extent is about 160 mm instead of
80 mm, with incorrect boundary and sampled surface. The supplied interpolation
points encode the wrong geometry. This is not a tolerance-only fidelity miss or
proof of a surface-tool bug. Its successful creation/inspection responses do not
certify agreement with the task. The agent nevertheless claims completion; the
independent failure remains recorded. Actual screenshots, including this failure,
are in the roadmap gallery with hashes in `assets/model-progress.json`.

## Current ranking and next investigation

`flaw-report.json` is rebuilt solely from `release-041-runs.json`. The historical
M1 registry and M2 reports remain historical evidence. The only observed current
flaw class is the panel's completion contradiction. Seven guidance reads in native
runs and one in editing are discovery costs, not automatically defects. Multi-call
inspection and five individual assembly attribute updates are further cost leads;
no unavailable batch capability or avoidable call is asserted without review.
There are no current failed-call, retry or execution-fallback observations.

M3b must investigate this evidence rather than reuse the fifteen fixed attribute
failures. Any proposal must distinguish agent arithmetic/verification errors from
misleading tools, and demonstrate cross-task benefit before adoption. Two cycles
and the Claude transfer checks remain to be done; M6 has not started.

## Host gateway and evidence

Full-catalog definitions remain unchanged, but `run_command`,
`execute_rhinoscript_python_code`, and `execute_rhinocommon_csharp_code` are
unconditionally refused before reaching production. Rejections consume budget and
retain arguments/error/timing. All three have regression coverage. Grasshopper
calls remain refused by this Rhino-only gateway. Trusted controller evaluation
uses its existing separate bridge. No execution attempts occurred in these runs.
The pilot now derives registry cohort versions from recorded runtime identity,
removing its stale hardcoded 0.4.0 label.

[Portable results](release-041-results.json) retain verdicts, environment, source
and artifact hashes. [Registry](release-041-runs.json) points to full local evidence.
The tracked ranking omits per-call indexes; raw traces remain under `runs/`.
Backend model snapshots are unavailable, and this is one observation per family,
not a paired improvement or generalization result.

Validation: 285 server tests, 474 experiment tests, 13 contract tests and server
Ruff pass. No controller/modeler remains after the pilots. Rhino PID 99475 remains
on 0.4.1; reverify ownership and open a fresh document before comparison preparation,
because normal pilot cleanup leaves the empty document modified.
