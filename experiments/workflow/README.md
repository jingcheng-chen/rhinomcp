# MCP workflow improvement — governing workflow

The optimization target is RhinoMCP and the reusable tool workflows available to
ordinary agents. Modeling outputs are benchmark evidence. The chair is one task,
not the architecture or the primary progress metric. This direction supersedes
chair-first next steps in historical reports (user clarification, 2026-09-07).

## Direction — user clarification, 2026-09-09

Enhance the overall Rhino modeling workflow by detecting flaws in agent runs and
improving the MCP tools; do not chase precision. The 0.05 mm panel tolerance and the
biquadratic surface recipe are historical; a valid, correctly posed result that
misses a tight shape tolerance is a fidelity note, not a workflow flaw. The
milestone queue (re-baseline on the released 0.4.0, flaw detection from traces,
realistic workflow families, one improvement cycle per flaw, held-out bank,
isolation, then a Grasshopper harness) is in [CONTINUE.md](../CONTINUE.md).

## Tolerance policy — 2026-09-09

Tolerances describe what a realistic modeling task needs and are fixed before a run:

- analytic solids and posed geometry: the document absolute tolerance (0.001 mm at
  task scale) for positions and dimensions; 1% for volume and area unless the task
  says otherwise;
- freeform surfaces and trimmed patches: linear deviation up to 0.5% of the object's
  largest dimension (0.5 mm on a 100 mm panel); topology, pose and boundary checks
  stay exact;
- a run that passes topology, pose and bounds but misses a shape tolerance is
  recorded as fidelity, not counted as friction, unless a tool response misled the
  agent.

Never change a tolerance to pass or fail a specific run. Re-declare the task as a
new version and keep the old file for historical pins.

The default pilot now uses `release-pilot.json` and versioned tasks for five
families. Panel tasks may declare `shape_tolerance` for sampled surface deviation;
`linear_tolerance` still controls document tolerance, bounds and boundaries.
Analytic trimmed patches retain strict plane/boundary checks and a 1% area budget.
See [M0 preparation](REBASELINE_040.md) for declarations, verification and the
completed released-runtime observations. Historical suite files remain replay inputs.

## Distribution requirement — user-approved 2026-09-09

Reusable modeling knowledge ships with RhinoMCP. Keep essential semantics in tool
descriptions and longer guidance in the packaged canonical guide, exposed by a
read-only MCP tool/resource and shared prompts. Optional skills derive from that
same source. Validate wheel installation without experiment files or local memory.
See [implemented distribution and live checks](DISTRIBUTABLE_GUIDANCE.md).

## Cycle

1. Observe fresh agents across a diverse registered suite. Keep task verdicts separate
   from tool calls, failed calls, duration, tokens and recovery behavior.
2. Diagnose workflow friction across traces: misleading responses, unavailable
   capabilities, excessive orchestration, schema confusion and fragile recovery.
   Distinguish tool/gateway/harness/modeling causes. Passing tasks can expose friction.
3. Propose a defect repair, new capability, tool-interface improvement or reusable
   tool workflow. State a falsifiable expected benefit and a preservation contract.
4. Review a bounded production scope; use a fresh builder and independent validation.
   A proposal alone never grants write/install permission. New commands require the
   Python wrapper, C# handler, schema, protocol enum and protocol-envelope coverage.
5. Compare fresh agents on baseline and candidate with identical model/version,
   task inputs, evaluator, budget and environment. Change one intervention at a time.
   Report task success alongside efficiency; failed fast is not improved performance.
6. Retest multiple families, including tasks withheld from discovery. Retain only
   changes with demonstrated benefit and no unacceptable regressions. Keep inconclusive
   changes unpromoted; record task-specific benefit without generalizing it.

## M1 trace classification — complete, 2026-09-09

The audit now produces evidence-linked flaw counts and rankings by tool, family
and cohort. It normalizes native and wrapped calls, separates discovery from
redundancy, preserves unknown timing, and uses hash-bound reviewed annotations for
semantic claims. The seven historical and sixteen same-day runs are registered,
including the timed-out surface attempt. All 23 calibration labels match; portable
synthetic tests cover the taxonomy's additional cases. These are discovery
observations, not held-out classifier accuracy or candidate-effectiveness claims.

```sh
server/.venv/bin/python -m experiments.workflow.audit experiments/workflow/flaw-runs.json --labels experiments/workflow/flaw-labels.json --output experiments/workflow/flaw-report.json
```

See [the taxonomy, ranking limits and top findings](FLAW_TAXONOMY.md). The largest
same-day problems were observed on pre-release 0.3.2. The five released runs still
pass, with two repeated guidance reads in the panel. Next is M2's broader families.
The older audit artifacts below remain historical snapshots.

## Implemented in this milestone

- `historical.json`: explicit run registry spanning five task families. Files missing
  on another checkout are reported unavailable, never treated as failed or zero-cost.
- `audit.py`: one task-independent CLI-event adapter, including schema queries and
  calls rejected before they reached the gateway log. Started/completed pairs count
  once. Full traces stay local; tracked summaries retain evidence hashes.
- `proposal.schema.json` and `proposals.py`: proposals cover capabilities as well as
  defects, require task success alongside efficiency, multiple validation families
  and held-out families absent from discovery. These are declared plans, not proof
  that the future tasks are unseen or that an improvement has been validated.
- `plan.py` loads `harness/roles/workflow_planner.md` into a fresh planner with audited
  evidence, validates its proposal and preserves sources. No builder is dispatched.
- `historical-audit.json`: actual historical observations; explicitly ineligible
  for causal baseline/candidate claims because comparable pins were not recorded.

From the repository root:

```sh
server/.venv/bin/python -m experiments.workflow.audit experiments/workflow/historical.json --output experiments/workflow/historical-audit.json
PYTHONPATH=/absolute/path/to/rhinomcp server/.venv/bin/python -m experiments.workflow.plan experiments/workflow/historical-audit.json
```

## Baseline — released 0.4.1 (2026-09-10); recorded baseline still 0.4.0

rhinomcp 0.4.1 (tag `releases/0.4.1`) is the baseline for every new comparison
once M0b records its identity. Until then `current-baseline.json` names the
released 0.4.0 recorded by M0 ([report](REBASELINE_040.md),
[trace registry](release-040-runs.json)). 0.4.1 fixes `update_object_attributes`,
which failed on every call in 0.4.0 and dominated the M2 flaw ranking, so rankings
built from 0.4.0 runs are stale. Connections read `describe_capabilities` once
before the first command; treat that entry in traces as infrastructure, not agent
behavior.

## Isolation — Parallels VM (decided 2026-09-10)

Unattended operation runs candidates in a fresh Parallels guest restored from a
clean snapshot; the host keeps the controller, evaluators and the trusted judge.
The boundary, network policy and transport rules are in
[ISOLATED_ENVIRONMENT.md](ISOLATED_ENVIRONMENT.md); the implementation steps M5a to
M5d are in [CONTINUE.md](../CONTINUE.md). Until M5d is done, full-catalog runs on the
host must refuse and record the three execution tools instead of running them.

## Later: Grasshopper harness

The cycle above applies unchanged to Grasshopper once the Rhino queue has produced
at least one kept improvement. Tasks describe small definitions with checkable
outputs; agents get the `gh_*` tools only and start from `gh_create_document`; the
evaluator reads the graph, runs the solution and checks output parameters, with
previews as supplementary evidence. The design sketch and its open questions (a
bake command for saved-file judging, Grasshopper-specific friction classes) are in
[CONTINUE.md](../CONTINUE.md#m6--grasshopper-harness-later).

## Current implementation — 2026-09-08 (historical)

The shared runner now registers analytic solids, biquadratic panels and trimmed
planar patches. It records explicit model alias/effort, task, catalog, evaluator,
budget and runtime pins. Backend model snapshots remain unavailable.

The declared-file capability builder, reviewed trial intake and supervised binary
comparator are implemented. The panel comparison rejected the bounds candidate.
The planar-region trial passes all 79 checks; the completed 12-session comparison
improves trimmed-patch success from 0/4 to 4/4 while preserving through-hole success.
All artifacts were evaluated after trusted-baseline restoration. Guarded source
and runtime selection, rollback and reactivation are verified. The selected tool
is now part of the 13-tool default benchmark interface (69 full production tools).
See [selection evidence](PLANAR_REGION_SELECTION.md), [current baseline](current-baseline.json)
and [evaluation boundary](EVALUATION_ISOLATION.md).

Durable resource limits, verified checkpoint continuation and a finite reviewed
comparison queue are implemented and live-validated. See [continuation](CONTINUATION.md)
and [campaign evidence](CAMPAIGN.md). The [Claude adapter](CLAUDE_PROVIDER.md) is
live-validated for native modeling: 20 successful calls across three fresh sessions,
with independent verdicts of two passes and one detected pose failure. Binary
comparison orchestration remains Codex-only.
Remaining work includes broader family coverage, hard adversarial judge isolation
and unattended operation in a [dedicated environment](ISOLATED_ENVIRONMENT.md). Scoped supervised
selection is not general automatic promotion.

## Historical implementation plan — superseded by the status above

- Extend the shared pilot beyond its existing analytic solid evaluator adapter.
  Keep task definitions as inputs and evaluator registrations, rather than forking
  orchestration. Old runners remain historical replay paths.
- Explicit model/version, prompt, evaluator and environment pinning for prospective
  comparisons. The current audit deliberately cannot authorize a promotion.
- A reviewed capability-builder route permitting exact declared new files and their
  parent directories, with whole-checkout integrity and protocol completeness checks.
  Existing `repair.py` and `bounded_builder.md` remain edit-only and defect-only.
  Do not bypass those restrictions by relabeling a capability request as a defect.
- A common baseline/candidate comparison and promotion decision across registered
  task families. Do not create a runner for every object or substitute a test count
  for agent-effectiveness measurements.

The shared native-interface pilot is implemented below. Next, pin agent configuration
and investigate primitive placement guidance through repeated paired trials. Reliable
geometry feedback remains another evidence-backed investigation. Curved panels
and trimmed patches are proposed validation families, not implemented benchmarks.
No more chair-only construction milestones are scheduled by this workflow.

## Representative-interface check (2026-09-07)

The fresh workflow planner proposed batch schema discovery. Supervisor triage defers
it: repeated schema calls were observed through our custom gateways, not ordinary
production MCP usage. See [results](RESULTS.md) and
[proposal triage](proposal-triage.json). A valid proposal is not an approved
change. The next pilot must expose representative native MCP tool schemas and record
comparison pins. Reuse existing tasks/evaluators; do not add another object-specific
runner. Reliable surface feedback remains an independent investigation, suitable
for the existing repair route once cross-task acceptance cases are fixed.

## Native-interface pilot (2026-09-07)

`pilot.json` registers existing box and through-hole tasks with one common tool set,
call budget and timeout. `pilot.py` handles fresh sessions, source snapshots, runtime
identity, saved-file evaluation, screenshots, workflow metrics and guarded cleanup.
`native_mcp.py` exposes 12 production tools with identical names, descriptions, input
and output schemas, defaults and return values. It adds only document checks, call
budget enforcement, serialization and a controller-side call log. It does not supply
special modeling recipes or a schema-discovery tool.

This is a **restricted native interface**, not the complete production server:
script execution, desktop/filesystem access and other capabilities are excluded.
Both tasks get the same tools. Guard time contributes to measured elapsed time;
client traces remain the source for all attempts, including rejected calls.

```sh
PYTHONPATH=/absolute/path/to/rhinomcp server/.venv/bin/python -m experiments.workflow.pilot
```

Use one empty, unsaved, unclaimed dedicated Rhino document. The suite holds the
shared Rhino lock, saves each candidate and screenshot, and removes its construction
objects including hidden objects after each task. Source and loaded plugin identities
are checked before evaluation. Failure records remain local; failures are not retried
silently. The original units, tolerance, objects and layer fingerprint must survive.

The run records CLI version, task, prompt, tool catalog, code and binary hashes,
budgets and runtime identity. The resolved agent model version is still unavailable;
these baseline observations cannot authorize comparison or promotion. Explicit agent
configuration, repeated paired trials and held-out cases are the next comparison work.

## Controlled description trial

`placement-trial.json` freezes the requested model (`gpt-5.6-terra`), medium reasoning,
intervention text, task suite, repeat count and acceptance rule. `compare.py` reuses
`pilot.run_task`; it does not implement another geometry workflow. For each task it
runs baseline/candidate, then candidate/baseline, with fresh sessions and identical
inputs. Only `create_object.description` may differ in the exposed tool catalog.
The proposed suffix is served from a frozen run artifact; production source remains
unchanged while the experiment runs.

```sh
PYTHONPATH=/absolute/path/to/rhinomcp server/.venv/bin/python -m experiments.workflow.compare
```

Every session explicitly selects the same model alias and reasoning effort through
the CLI. These settings are documented in the [official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
The invocation is retained; the backend model snapshot is not exposed. Alias pinning
improves experimental control without proving immutable model weights. The CLI version,
plugin binary/MVID, task inputs, evaluator/harness/production source hashes, descriptions
and budgets must remain fixed throughout the comparison. An input/environment mismatch
aborts the trial. Default historical runners retain their existing model behavior.

Acceptance requires all task verdicts to pass, fewer median calls in each family,
and no increase in failed calls. Time and token usage are reported separately.
Neither faster failures nor incomplete runs pass. Even a positive small discovery
trial does not authorize automatic promotion or establish held-out generalization.


## Reserved-case validation and adoption

[PLACEMENT_VALIDATION.md](PLACEMENT_VALIDATION.md) records eight additional passing
agent runs on new dimensions/offsets. The supervisor adopted the tested placement
wording into the production creation-tool docstring. Median calls decreased in both
families; latency was mixed. See the report for limits, screenshots and adoption checks.

The current production baseline already includes the guidance. Historical description
trials must use pre-adoption revision `6265121`; the gateway rejects duplicating a suffix
already present in the native description. The generic pilot remains usable without
an intervention. Automatic promotion and general capability-builder support are still
pending. Next investigate the independent surface-feedback evidence through the shared
workflow and existing bounded repair path.

## Generic panel registration (2026-09-08)

See [PANEL_BENCHMARKS.md](PANEL_BENCHMARKS.md). The shared pilot now accepts posed biquadratic panels with a saved-file evaluator and explicit CLI agent settings. Twenty-two calibration fixtures pass expected verdicts. Two fresh baseline discoveries produce one pass and one modeling failure; no candidate workflow comparison or adoption is claimed. Binary switching/recovery orchestration and trimmed-patch registration remain pending.

## M2 workflow scenes

Four prepared-scene families now reuse the native pilot and evaluator registry.
The 17-tool subset and full 70-definition production catalog are both observed on
released 0.4.0, with document-scoped Rhino permissions. Thirty saved-file fixtures
calibrate the analytic scene, identity, layer and inspection checks. See
[the M2 report](SCENE_BENCHMARKS.md), [suite](m2-pilot.json) and
[reserved family allocation](HELD_OUT.md). This extends discovery coverage; it does
not establish a candidate improvement or generalization claim.

## M3 cross-family cycles on 0.4.0

[M3.md](M3.md) records the attribute-update and lookup-description investigations.
`plan.py REPORT --context CONTEXT --model MODEL --reasoning-effort EFFORT` accepts
explicit supervisor context instead of injecting the old surface-construction
proposal. Context, evidence and model settings are hashed for the fresh planner.

`binary_compare.py` retains the shared pilot, saved-file evaluator, AB/BA schedule,
resource ledger and restoration checks. `full_catalog: true` exposes the complete
production catalog while keeping Grasshopper calls outside the Rhino-document
permission scope. For a reviewed description-only source trial, declare
`description_tools`, both `interfaces` with `server_source` and empty `extra_tools`,
and identical `binaries` identities. Only the declared descriptions may differ;
all other catalog fields must match. The supervisor separately reviews executable
source equivalence, and both source trees are frozen before sessions. Example
contracts: `m3-cycle1-trial.json` and `m3-cycle2-trial.json`. These consume local
reviewed build/source artifacts; they do not reproduce them implicitly.

The scene evaluator now also measures closed axis-aligned rectangular polylines,
checking corners, closure, planarity, bounds, area and perimeter. Offset and
section cases use the same task runner and saved-file measurement path as boxes.
`validate_scene.run([...])` calibrates selected task names without launching agents;
`validate_attributes.py` runs controller-only attribute checks in an owned empty
document. Preserve all failed attempts and setup failures, and never convert an
agent completion claim into a task verdict.

## M4 supervisor-held family bank

The [sealed bank and allocation runbook](HELD_OUT.md) now govern future held-out
claims. Use `python -m experiments.workflow.held_out status` with the server venv
from the repository root. Metadata is public, fixed payloads remain in the ignored
local vault. Spend before exposure; even an abandoned validation consumes its
family. Seal a new family before closing the old allocation. The CLI neither
launches modeling nor bypasses the existing comparison/calibration gates.
See [M4 evidence and limits](M4.md). A checkout without private payloads must report
unavailable cases; do not reconstruct them with new parameters under the old hash.
