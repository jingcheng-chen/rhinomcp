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

- One shared task/session runner with a common agent-facing gateway; task definitions
  should supply inputs, budgets and evaluator adapters, not fork orchestration.
  Migrate a small cross-task pilot first; keep old runners as historical replay paths.
- Explicit model/version, prompt, evaluator and environment pinning for prospective
  comparisons. The current audit deliberately cannot authorize a promotion.
- A reviewed capability-builder route permitting exact declared new files and their
  parent directories, with whole-checkout integrity and protocol completeness checks.
  Existing `repair.py` and `bounded_builder.md` remain edit-only and defect-only.
  Do not bypass those restrictions by relabeling a capability request as a defect.
- A common baseline/candidate comparison and promotion decision across registered
  task families. Do not create a runner for every object or substitute a test count
  for agent-effectiveness measurements.

The next bounded work is the common task/session contract and a non-chair pilot for
reliable geometry feedback, then builder extension and paired trials. Curved panels
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
