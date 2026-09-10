# M6 — supervised Grasshopper workflow harness

Ownership, calibration and three fresh discovery runs are complete; one
improvement cycle remains. Released RhinoMCP 0.4.1 is unchanged. M5 stays deferred.

The existing `pilot.run_task`, native gateway, runner task loader, audit and
`binary_compare` serve `gh_definition` tasks. No new modeler orchestration loop.
Each agent starts with `gh_create_document`; the supervisor first claims a fresh
empty document and guards its actual `DocumentID` plus the owned, empty Rhino
around every call. Cleanup calls `gh_clear_canvas`, removes only that owned empty
document and verifies an empty GH server plus preserved Rhino fingerprint.
Startup refuses existing GH documents instead of reusing or clearing them.

The catalog preserves the 27 production `gh_*` schemas/descriptions. Reviewed
stock math/geometry type IDs constrain both construction and type-info
instantiation; scripts/file/external components are refused. Inputs, collections,
call count, session time and canvas size are bounded. This is supervised host
operation, not M5 isolation. Failed calls remain evidence.

The controller runs the solution, reads document information, the tagged graph,
the whole canvas (so untagged nodes cannot disappear), and named output data.
Those values are saved as a hashed `candidate.gh.json`, alongside task/source/tool/
runtime pins. Deferred comparison judging reads that frozen artifact after modeler
execution stops, under the identical trusted release. It does not trust modeler
completion or an agent-supplied verdict. No `.gh` file or replay capability is
claimed: this is a graph/output snapshot. Brep data currently lacks geometry
bounds; loft checks combine required wires, exact section circles, Brep topology
and analytical area. Point bounds come from serialized output coordinates.

Checks require a clean solution, expected component types and unique nicknames,
required wires, graph membership, every node contributing to a checked output,
matching output parameter names/counts/values, no truncation, and point bounds.
Previews from `gh_capture_preview` are supplementary only.

Three families: translated point array, circle profiles/areas, and loft sections.
Thirty controls match expected verdicts: three correct live definitions, 24 bad
saved snapshots, and three independently re-solved wrong-input definitions.
Correct snapshots are committed as regression fixtures. See
[calibration](gh-calibration-results.json) and
[live ownership denial](gh-ownership-denial.json).
The vector-frame family was sealed before discovery, with two fixed unseen cases.

Taxonomy adds GH component search churn, parameter-selector failures, wiring
failures, repeated solution loops and layout thrash. Heuristic churn/loop findings
are candidates for review, not proven defects.

Run discovery through the shared pilot:

```sh
PYTHONPATH=. server/.venv/bin/python -m experiments.workflow.pilot experiments/workflow/gh-discovery-suite.json --model gpt-5.6-terra --reasoning-effort medium
```

Do not edit pinned sources during modeler/comparison runs. Preserve timeouts and
failures; do not repeat failed attempts. Before a comparison, open a fresh empty
Rhino document to meet its unchanged startup gate.

Foundation verification: 285 server, 518 experiment and 13 contract tests pass;
server Ruff passes. Live ownership switch is denied and all cleanup checks pass.

## Fresh discovery

Released0.4.1, gpt-5.6-terra/medium, 40 calls/240 seconds, 27 GH tools.
All three saved graph/output snapshots pass: point array8 calls, profiles12,
loft15, zero failed calls. Every attempt starts gh_create_document; all GH cleanup
and Rhino preservation checks pass. Actual previews and hashes are in the gallery.
[Audit](gh-discovery-audit.json), [registry](gh-discovery-runs.json),
[review](gh-discovery-review.json).

Three/four/five focused value reads return the same values also present in each
whole-graph snapshot. This is observed overlap, not a proven counterfactual saving.
The loft additionally sets four values after graph creation. A fresh planner is
investigating a single gh_get_graph description clarification, preserving the
existing read behavior and verification requirements.

A separate misleading selector is retained: output_name=Centroid without an
explicit index returns Area, because the wrapper sends default output_index0 and
the plugin prioritizes indices. It does not invalidate the independently indexed
evaluator or geometry result. [Exact observation](gh-selector-observation.json).
No second fix is bundled into this cycle; it is a concrete future defect candidate.

Cycle1 candidate is independently reviewed (unchanged AST/full catalog except
gh_get_graph description) with285 server tests passing. Both allocated vector
cases match20 correct/flawed controls, including reversed live vectors. The
comparison is frozen by [review](GH_CYCLE1_REVIEW.md) and
[contract](gh-cycle1-trial.json). A pattern-filter replacement is sealed.
