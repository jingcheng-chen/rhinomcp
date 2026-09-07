# MCP workflow improvement — governing workflow

The optimization target is RhinoMCP and the reusable tool workflows available to
ordinary agents. Modeling outputs are benchmark evidence. The chair is one task,
not the architecture or the primary progress metric. This direction supersedes
chair-first next steps in historical reports (user clarification, 2026-09-07).

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

## Remaining implementation — do not confuse with the existing defect pilot

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
