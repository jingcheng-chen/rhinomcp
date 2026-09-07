# Native MCP workflow baseline — 2026-09-07

One shared runner executed two existing tasks using the same 12 production tool
definitions. Fresh sessions received the normal tool descriptions and parameters,
without the previous gateway's placement recipes or describe-command calls.
This is a restricted subset of production capabilities; it is not a full-server trial.

| Task family | Saved-file verdict | MCP calls | Failed calls | Agent seconds | Input / cached input / output tokens |
| --- | --- | ---: | ---: | ---: | --- |
| Primitives: box | Pass | 5 | 0 | 45.35 | 99,001 / 81,664 / 601 |
| Subtractive solids: through-hole | Pass | 9 | 0 | 77.92 | 201,000 / 176,896 / 1,297 |

Cached input is a subset of input, not an additional total. These are CLI-reported
usage counters. Elapsed time includes the gateway's document checks and client/model
latency. Do not compare these costs with historical custom-gateway runs as an A/B test.
No explicit schema-discovery tool is exposed, so zero describe calls is a property
of this interface, not a measured performance improvement.

The box agent created a centered box at zero, then translated by (50,25,15).
The through-hole agent did the same for its block, then created a cylinder as though
translation located its middle; the cylinder's base was instead at Z=10, requiring
another translation of −11 mm for a cutter spanning both faces. Returned bounds let
both agents recover. The second agent also used the production Boolean dry-run
option before committing the subtraction; that verification is not assumed waste.

**Candidate hypothesis:** documenting primitive anchor points and transform conventions
in the production tool description could prevent placement corrections across tasks.
The box is centered at the origin; the cylinder starts at its base. The current
creation docs list dimensions and translation without explaining those anchors.
Both cases share box creation, so evidence for broader transfer is still limited.
Keep geometry semantics unchanged and validate other placements/primitive combinations.
No production change or automated builder dispatch was performed in this milestone.

## Evidence and boundaries

Local run: `experiments/runs/workflow-baseline-20260907-094247-98d5be10/`.
The `task-1` and `task-2` directories preserve task, prompt, tool definitions, source
snapshots/hashes, CLI invocation/events, controller call log, environment, candidate,
evaluation, screenshot and preservation check. Both cleanup fingerprints match.
Loaded assembly MVID: `326aaa12-b851-4c6a-afcb-45291e734a5c`; final document
268435457 has zero objects, no file path and no experiment marker. No build/install
was needed. This is a session observation; recheck Rhino before continuing.

[native-baseline.json](native-baseline.json) retains compact trace metrics/hashes.
The shared auditor's conservative historical-comparison warning applies to these
prospective baseline records too: no paired candidate or controlled model version
exists. The suite records CLI version and production/harness sources, but the resolved
agent model version is unavailable. Explicit agent configuration, repeated paired
trials and additional validation cases are required before claiming improvement.

[Image provenance](native-baseline-images.json) pins both PNGs and saved models.
The roadmap includes these actual wireframe captures. Saved-file geometry checks,
rather than appearance alone, establish the reported correctness.

Verification: **482 tests pass** (12 existing warnings), including native tool-schema
parity, scope/budget enforcement, document-change rejection and suite validation.
The 61-case live production preservation suite was not rerun; no production code changed.
