# Workflow flaw taxonomy v1

M1 is complete: one read-only command classifies the registered traces, validates
reviewed labels and produces a portable ranked report. No Rhino session is needed.

```sh
server/.venv/bin/python -m experiments.workflow.audit experiments/workflow/flaw-runs.json --labels experiments/workflow/flaw-labels.json --output experiments/workflow/flaw-report.json
```

The CLI also accepts multiple registry paths, rejecting duplicate IDs or run paths.
[The registry](flaw-runs.json) includes all seven entries in `historical.json` and
all 16 native pilot attempts found on 2026-09-09, including the timed-out attempt
that never reached registry finalization. Deterministic precision fixtures are not
agent runs and are excluded. The latest five runs are marked `released-0.4.0`;
the other eleven same-day runs used pre-release 0.3.2 binaries. No new modeling,
plugin installation, tool intervention or task retry was performed for M1.

## What is classified

`audit.py` retains its existing metrics and adds the classification from `flaws.py`.
The adapter pairs started/completed events by ID, in first-seen order, so concurrent
completions count once. It reads the common Codex/normalized-Claude event format,
including failures rejected before reaching the gateway. It unwraps MCP text,
structured results and JSON envelopes; negative geometry measurements alone do
not make an inspection call a failed call. Unknown wrappers are conservative
mutation barriers. Capability handshakes in controller logs are not inserted into
the agent trace; an explicit agent capability query is counted as discovery.

| Category | Detection and limits |
| --- | --- |
| `failed_call` | Explicit failed status, MCP error flag, or unsuccessful result envelope. Causes: gateway scope/budget, schema/input, runtime exception, transport, missing object, missing layer, unknown. Text patterns classify symptoms, not proven root causes. |
| `retry_after_error` | Next matching command/target/type after a failure, allowing changed arguments. Candidate only: this may be an independent intent. Charge the retry, not its prior error again. |
| `discovery` | Schema/catalog queries or guidance calls. Routine observation, not automatically friction. Different topics remain distinct. |
| `redundant_read` | Same query and same decoded response, without an intervening possible mutation; schema/guidance are static. Failed and unfinished writes invalidate document reads. Missing responses cannot establish duplication. This is repeated information, not proof that removing verification is safe. |
| `orchestration` | Reviewed costly workaround with cited trace/agent evidence. Calls per operation are explicit maps rather than inferred from object count. Cost is observed calls, not counterfactual savings. |
| `typed_fallback` | Macro/script use is a candidate. A reviewed typed-alternative claim requires a hash-pinned exposed catalog containing that alternative. Controller scripts and hidden gateway internals are not agent fallbacks. |
| `misleading_response` | Reviewed tool/agent claim linked to contradictory evidence. A final failing model alone never proves a tool lied. The current reviewed case is a misread transform response. |
| `wrong_default` | Reviewed anchor/pivot/parameter mismatch linked to the request, returned geometry and correction or independent verdict. No automatic inference from any move following creation. |
| `recovery_loop` | Undo, or a named object created, deleted and recreated within the recent mutation window (eight preceding mutations). Candidate only. Deleting a construction profile alone is normal cleanup. This heuristic does not claim exhaustive recovery detection. |
| `unmet_capability` | Explicit agent statements matching missing/unavailable-tool phrases are candidates; reviewed evidence can register other wording. This is not proof a tool is missing. |
| `completion_contradiction` | Agent claims complete, independent saved-file verdict fails. Separate from tool-response truth; no fabricated tool duration is assigned to the claim. |

No signal means “not detected,” not “proven absent.” Semantic classes require
supervisor review because event logs alone do not establish intent or correctness.
`confidence` distinguishes `observation`, `candidate`, `observed`, and `reviewed`.
Even an observed/reviewed problem may belong to the gateway or the agent; it does
not automatically justify a production repair.

## Evidence and review

Each finding has stable run-local IDs, event IDs/line numbers, charged call IDs,
and a reason. Reports hash the source trace, timings, evaluation, result, status,
environment, classifier and input registries where present. Raw events and models
remain local; the tracked report includes call indexes and compact evidence.

The registry's optional `review` block binds semantic findings to the event-file
hash plus exact quotes and hashes of supporting files within that run. Changed
traces, stale quotes, absent call IDs, path escapes or unavailable typed alternatives
cause refusal. Reviewed evidence is an accountable supervisor interpretation,
not an independent learned classifier or a security boundary against the reviewer.

The current panel fidelity note is pinned to its original evaluation. Its
geometry verdict stays **fail**. The valid, correctly bounded outer rectangle had
a sampled interior shape/height miss under the old 0.05 mm test; this is excluded
from workflow completion contradictions. The separate agent-reported difficulty
with the SURFACE schema remains eligible as a workflow observation. No tolerance
or historical verdict is changed.

Operation maps are supplied for all five released runs. They separate constructing
the required result, applying pose/openings and removing construction objects from
support activities (guidance and verification). Each released call is assigned
once. Missing operation maps remain null for older runs; there is no invented
“optimal” call count or denominator.

## Ranking and timing

For each category/subtype/confidence (and separately tool, family and cohort):

- `score_calls = frequency × mean_cost_calls`, the sum of charged calls.
- `score_seconds = frequency × mean_cost_seconds` only when every charged call
  has a usable duration. Otherwise the score is null and the measured subtotal
  and coverage are shown. The complete-only seconds ranking excludes unknowns.
- Exact unique `(tool, arguments)` matches to `calls.jsonl` provide gateway times,
  including guard overhead. Repeated signatures are ambiguous without event IDs;
  their times remain unknown. Session elapsed time is reported separately and
  is never distributed across calls or described as removable waste.

The primary ordering is call cost, then frequency and stable category names;
seconds provide a separate ranking, not a dimensionally mixed score. Observations
and candidate hypotheses are retained in the overall ranking but excluded from
`observed_or_reviewed_flaws` and `observed_flaws_by_cohort`.

Categories overlap. A retry can also fail; a repeated guidance call is both
discovery and a redundant read. Do not sum category costs as total wasted calls.
The underlying 378 attempts, not the sum of findings, is the corpus call count.
These are discovery priorities, not effect sizes or promotion criteria.

## Results and top three current-trace priorities

[The report](flaw-report.json) covers **23 runs, 378 agent calls and 18 failed
calls**. Exactly 129 calls have uniquely attributable gateway durations. All 23
reviewed run-level calibration labels match. Missing runs on another checkout are
reported unavailable; label validation then reports incomplete, not success.

The highest call-cost problems in the same-day traces are below. **All three were
observed on pre-release 0.3.2, not demonstrated on released 0.4.0.** They are leads
to validate, not evidence that 0.4.0 regressed.

| Priority | Evidence | Observed cost |
| --- | --- | --- |
| 1. Unclear surface parameters leading to a multi-call workaround | `20260909-182654-2ada6f48-task-4`: agent explicitly reports truncated/unclear SURFACE parameter docs; seven curve creations, one loft and seven deletes construct one panel. | One reviewed episode, 15 calls, 7.434 gateway seconds. The 150.7-second session is not all attributable to this flaw. |
| 2. Silently ignored placement parameters requiring corrective moves | `084123` and `125308`, tasks 1–2: six BOX/CYLINDER calls pass nested `base`/`base_point`; returned bounds show default placement; six later translations correct it. | Six corrections across four runs/two families, 6 calls, 1.727 gateway seconds. |
| 3. Surface input errors and repeated repair attempts | `20260909-184415-0e2b7f48-task-1`: missing parameters give a null-reference error; nested points give a double-parsing error; three subsequent calls fail the count/degree constraint. | Four schema/input failures, 4 calls, 0.506 gateway seconds; additionally one runtime failure (0.130 s) and four linked retry candidates. Session timed out at 180.3 s. |

A separate same-day posed-patch case (`084123`, task 3) applied a center rotation
when the task required world-origin rotation. The returned bounds expose the
pivot, the agent incorrectly claims correct pose, and independent boundary/pose
checks fail. It is retained as a reviewed pivot issue, misread success response,
and observed completion contradiction, without triple-counting call savings.

In the **released 0.4.0 subset**, all five saved models still pass and all 40 calls
succeed. The only detected nonroutine issue is **two duplicate guidance reads** in
the panel: `item_1 → item_3` repeats `transforms`, and `item_2 → item_4` repeats
`verification`, with identical replies. Their individual durations are unknown.
There are seven guidance calls total, not seven errors. Different inspection
responses are not declared redundant merely because they inspect the same object.
The earlier M0 prose saying “four guidance topics” was inaccurate: four calls
covered two topics. M1 corrects that description without changing the M0 evidence.

Historical gateway-only failures (seven out-of-scope schema requests and four
budget rejections) are classified separately from the two missing-layer failures.
They must not be promoted as native production-tool defects.

## Validation and next step

Portable synthetic controls cover provider envelopes, concurrency, unfinished
calls, read invalidation, changed responses, retry targets, normal cleanup versus
recreation, unknown timings, semantic evidence integrity, typed alternatives,
fidelity handling, operation maps, duplicate registries and calibration disagreement.
`flaw-labels.json` freezes reviewed labels for the 23 local traces; a local-evidence
test checks them when the files exist, and skips explicitly on other checkouts.
This is calibration on discovery data, not held-out precision/recall measurement.

Proceed to M2's new realistic workflow families, using these findings to motivate
later proposals. Before a product intervention, reproduce a relevant priority on
the released catalog across tasks and follow the planned independent comparison.
Do not infer that normal guidance/inspection is waste or tune a recipe for one panel.

Verification: **285 server, 407 experiment and 13 contract tests passed** (705 total);
server lint and the changed audit/test modules pass Ruff. No production source
changed, so no plugin build or installation was required for M1.

## Grasshopper extension (M6)

`gh_friction` distinguishes repeated identical component queries, failed port
selectors, wiring errors, repeated solution/expire loops, and layout thrash.
Search/loop/layout heuristics are candidate findings requiring intent review.
GH catalog queries join discovery; graph, canvas and value reads use the same
mutation barriers as Rhino reads. No geometry verdict is inferred from traces.
