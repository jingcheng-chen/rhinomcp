# M6 — Grasshopper harness complete

Three definition families are calibrated and have fresh 0.4.1 discovery runs.
One fresh planner/builder/comparison cycle is complete and **rejected**, including
its fixed Claude check. No production code is adopted or published. M5 remains
deferred; no VM was touched.

## Shared harness and ownership

The existing `pilot.run_task`, native gateway, runner task loader, audit and
`binary_compare` serve `gh_definition` tasks. There is no new modeler orchestration
loop. Every agent starts with `gh_create_document`; the supervisor claims a fresh
empty document and guards its actual `DocumentID` plus the owned, empty Rhino
around each call, including failed calls. Cleanup calls `gh_clear_canvas`, removes
only that owned empty document, and verifies an empty GH server and preserved
Rhino fingerprint. Startup refuses existing GH documents. A live two-document
switch was refused: [ownership evidence](gh-ownership-denial.json).

The catalog preserves the 27 production `gh_*` schemas/descriptions. Reviewed
stock type IDs constrain construction and type-info instantiation. Inputs,
collections, calls, time and canvas size are bounded (32 objects). This supervised
host boundary is narrower than the installed component library and is not M5
isolation. The frozen restriction also refuses some legitimate stock constructors;
those refusals are recorded separately from tool defects.

The controller runs the solution, reads document information, the tagged graph,
the whole canvas (so untagged nodes cannot disappear), and named/indexed output
data. It saves a hashed `candidate.gh.json` with task/source/tool/runtime pins.
Deferred judging reads that frozen artifact after modelers stop, under the same
trusted release. Agent completion and agent-supplied verdicts are not acceptance.
This is a graph/output snapshot, not a replayable `.gh` definition or baked `.3dm`.
Brep output data lacks bounds: loft checks combine required wires, exact section
circles, Brep topology and analytical area. Point bounds use serialized coordinates.

Checks require a clean solution, expected component types and unique nicknames,
required wires, graph membership, every node contributing to a checked output,
matching parameter names/counts/values, no truncation, and point bounds.
`gh_capture_preview` images are supplementary only.

## Calibration and discovery

Thirty controls across point arrays, circle profiles/areas and loft sections match:
three correct live definitions, 24 bad snapshots, and three live wrong-input
solutions. Correct snapshots are committed as regression fixtures. The separately
allocated vector-frame family adds 20 controls, including reversed live vectors.
[Discovery calibration](gh-calibration-results.json),
[held-out calibration](gh-heldout-calibration-results.json).

Fresh Codex gpt-5.6-terra/medium runs, 40 calls/240 seconds, all pass: point array 8
calls, profiles 12, loft 15, zero failed calls. Every cleanup passes.
[Audit](gh-discovery-audit.json), [registry](gh-discovery-runs.json),
[review](gh-discovery-review.json). Actual previews and hashes are in the roadmap.

Three/four/five focused reads return data also present in each whole-graph snapshot.
This is observed overlap, not proof that every read was unnecessary. A fresh planner
proposed clarifying graph-wide value inspection. A bounded builder changed only
`gh_get_graph`'s docstring; independent executable-AST and full-catalog review passes,
as do 285 candidate server tests. [Proposal](gh-cycle1-proposal.json),
[patch](gh-cycle1-candidate.patch), [source review](gh-cycle1-source-validation.json).

## Frozen cycle and rejection

[Predeclared review](GH_CYCLE1_REVIEW.md), [contract](gh-cycle1-trial.json),
[immutable results](gh-cycle1-results.json), [audit](gh-cycle1-audit.json).
Two AB/BA pairs per task, 16 Codex sessions. All 16 saved artifacts pass independent
judging; 313 calls, 48 failures. Correctness is preserved, but the failed-call gate
rejects the candidate in both held-out cases:

| Task | Median calls, baseline → candidate | Failed calls, baseline → candidate |
| --- | ---: | ---: |
| Point array | 16 → 14 | 0 → 0 |
| Circle profiles | 11.5 → 12.5 | 0 → 0 |
| Held-out orthogonal frame | 28.5 → 23.5 | 12 → 14 |
| Held-out tilted frame | 25 → 25.5 | 8 → 14 |

The generic comparator benefit flag is not the reviewed keep decision. Forty
failures are explicit host component refusals. The eight others comprise three
input-name/index precedence errors, three invalid vector encodings, one missing
value target and one wrong nested input-index key. The post-run auditor recognizes
`host_component_refusal`; this changes labels, not counts or saved verdicts.

The fixed Claude sonnet/medium check also rejects on point-array failed calls.
All four artifacts pass: point baseline 5 calls / 0 failures, candidate 8/3; profiles
baseline 7/1, candidate 11/0. These four failures are missing `gh_build_graph` value
target selectors. No attempt was retried. Every GH cleanup and Rhino preservation
check passes. Vector frame is spent/closed as rejected, with pattern filtering
sealed as replacement. Instance/block reuse and mesh repair remain unopened.

These are two repeats per arm/task and requested model aliases, not immutable
backend snapshots or statistical/causal proof. Host restrictions materially shape
held-out behavior, so no full-library/generalization benefit is claimed.

## Concrete follow-up findings

The graph remains useful even when task outputs pass. A request for
`output_name=Centroid` returned Area because the wrapper also sends default index0,
which takes precedence in C#. The same default causes named Unitize input writes
to target vector input0. The evaluator uses explicit indices and is unaffected.
[Recorded selector observation](gh-selector-observation.json). A future bounded
repair should investigate this selector class, separately from batch-value shape
clarity. Before another GH campaign, review broader safe stock-component coverage
or expose the allowed type list clearly; do not count guard refusals as plugin bugs.
A bake capability remains prospective, not implemented or claimed here.

Final verification: 285 server, 519 experiment and 13 contract tests pass; server Ruff
passes. [Runtime](m6-final-runtime.json) remains Package Manager 0.4.1 with matching
server, no update advice, empty Rhino, no GH documents, and no running modeler.

## Commands

```sh
PYTHONPATH=. server/.venv/bin/python -m experiments.workflow.pilot experiments/workflow/gh-discovery-suite.json --model gpt-5.6-terra --reasoning-effort medium
PYTHONPATH=. server/.venv/bin/python -m experiments.workflow.validate_gh
```

Do not edit pinned sources during sessions. Preserve failures/timeouts; do not rerun
until passing. Start a comparison from a fresh empty Rhino document. Held-out
specifications already spent by this cycle are discovery material from now on.

The portable audit samples three references per aggregate ranking and retains all
per-run findings/counts plus the full-audit hash; raw calls remain in ignored runs.
