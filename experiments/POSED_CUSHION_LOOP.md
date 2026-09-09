# Image review and reclined-cushion diagnosis

This milestone addresses two failures observed during the partial chair integration:
the planner did not receive images, and the back cushion remained open. No production
plugin defect or repair is established.

## Verified image delivery

A fresh probe using the original read-only integration configuration successfully
called `get_reference_image("front-oblique")` and described the reference. The
server exposes both image tools. The previous failure is therefore not reproduced
as a persistent unavailable-tool problem; its exact cause is not established.
Probe: `runs/review-tool-probe-20260906-173714/`. The owned empty document was restored after this probe.

`saved_review.py` and `saved_review_mcp.py` provide an additional deterministic
review route: a frozen pack containing only explicitly selected PNGs, pinned by
manifest and per-image hashes. The gateway has one read-only tool and no Rhino
connection. It rejects unknown IDs, changed bytes, path traversal and symlinks.
Server delivery logs and successful client image responses must both cover every
image. The client image bytes are checked against the manifest hashes. Missing
images yield `incomplete_review`, even if the planner returns a confident answer.
This is tool-level restriction, not OS-level isolation of all local files.

Fresh review `runs/saved-review-20260906-173832-d9435b4f/` received all seven images:
four original public references plus saved Perspective, Front and Right candidate
views. Source/pack hashes stayed unchanged. `client-image-hash-verification.json`
adds full client-byte verification after the initial review. The planner recommends
modeling revision and identifies boxy padding and unresolved frame/strap details.
These remain qualitative observations; cameras are uncalibrated and visual acceptance
is unscored. No hidden image or target mesh entered the pack.

The existing required-server and per-tool approval configuration agrees with the
[official MCP configuration documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
Explicit tool names worked in the new probe, but one successful probe does not prove
that prompt wording was the sole cause of the earlier session failure.

## Measured open boundaries

`chair_boundary_probe.py`/`.cs` read the unchanged saved integration model twice.
Run: `runs/chair-boundary-20260906-173916/`.
The four naked edges form two nearby pairs. Their endpoints coincide, but sampled
closest distances reach about **0.087 mm**, versus **0.01 mm** document tolerance.
These are sampled distances, not an exact Hausdorff bound or a complete proof of
Rhino's join decision. They establish that equal endpoints do not mean equal curves.
The failure does not demonstrate a plugin bug, and increasing tolerance is not the
proposed repair. The original chair and integration artifacts are preserved.

## Transferable posed-body task

`posed_cushion_modeler.py` uses the same analytic four-lobed 100 mm cushion and
17 local geometry/layer predicates as the closed-body task. It adds a world-X rigid
rotation followed by translation. The gateway exposes the existing `modify_object`
operation. The modeling instruction is to create and join the local solid first,
then pose the entire object. It explicitly explains that this tool rotates about
the bounding-box center, requiring compensation to implement rotation about origin.

Two prescribed poses: +65° then (200,-40,80) mm, and −35° then (−120,70,20) mm.
The saved-file reader duplicates each geometry, inverse-transforms it and applies
the unchanged body predicates in local coordinates. It never writes the artifact.
This verifies sampled shape, pose, solid closure, boundary planes, volume, membership
and layers. It does not score chair likeness or demonstrate rounded perimeter joins.

Calibration `runs/posed-cushion-calibration-20260906-174320/` passes all **13 expected
verdicts twice**: two correct poses and eleven rejection cases, including wrong pose,
wrong scale, open/unjoined bodies, extra geometry and layer faults. Document
fingerprint is preserved. The first campaign, `...-174133`, failed because mutation
of geometry obtained from the File3dm collection was not persisted by that fixture
writer. The corrected writer inserts transformed duplicates into a new File3dm.
No evaluator predicate or threshold was relaxed. Both campaigns remain recorded.

## Hidden-copy incident and repair

The first fresh posed run, `runs/posed-cushion-model-20260906-174420-3b37dd79/`,
produced a closed cushion but its saved artifact also contained **65 hidden baseline
chair display copies**. The fixed one-object evaluator correctly rejected it.
The fresh planner suggested excluding the hidden objects; the supervisor rejected
that suggestion because the task requires a clean artifact, not merely one visible
object. The failed model, measurements and screenshots remain unchanged.

The earlier comparison helper attempted to delete hidden copies without showing
them first and ignored deletion failures. Default live enumeration omitted hidden
objects, so ownership counts and the document fingerprint incorrectly reported
an empty/restored document. This **corrects the previous integration cleanup claim**.
The original chair and integration model files themselves remain unchanged; the
contamination affected the subsequently saved posed-cushion artifact.

`bridge.identity`, `rhino_trial.runtime` and `strip_probe.fingerprint` now explicitly
include normal, hidden, locked, reference and light objects. The comparison helper
also enumerates hidden originals, shows each temporary copy before deletion, checks
every deletion result, and restores view settings before reporting cleanup failure.
Rhino's [object enumerator settings](https://developer.rhino3d.com/api/rhinocommon/rhino.docobjects.tables.objecttable/getobjectlist)
allow explicit hidden/locked inclusion. This repair is in harness code only.

Recovery `runs/comparison-cleanup-recovery-20260906-174936/` archived all hidden
objects before cleanup and verified their names, transformed geometry CRCs, hidden
state and neutral comparison color against the 65-object baseline. Only those
verified copies were removed. The live count then became zero with the new checks.

Regression `runs/comparison-cleanup-validation-20260906-175039/` proves normal,
hidden and locked objects are all counted, preserves a pre-existing hidden sentinel
through actual paired model rendering, removes every display copy, and restores
the original empty document. Saved comparison source files are unchanged. Previous
historical preservation claims based solely on default enumeration do not prove
absence of hidden objects; do not silently reinterpret their old logs.

## Fresh clean repeat

`runs/posed-cushion-model-20260906-175112-f2f8dd8d/` passes **17/17** predicates
with exactly one object in the saved file, zero naked edges and maximum sampled
height error **0.24092 mm**. Repeated measurements agree. A fresh geometry planner
accepts the fixed verdict. This planner reviews measurements, not a new visual
similarity score. The modeler recovered a layer assignment attempted before the
layer existed. This is a workflow error, not a plugin defect.

Actual Perspective, Front and Top screenshots are tracked for both the failed
contaminated run and the clean repeat. The failed run is not relabeled as passing
just because its visible cushion looked correct.

## Alternate-pose failure and returned-bounds reproduction

`runs/posed-cushion-model-20260906-175410-5bf01af5/` fails: 42 separate objects,
no completed closed body and no demonstrated alternate pose. The agent interpreted
flat reported bounds as a flattened top, deleted it, and attempted many small
patches until the 60-call budget was exhausted. The actual phase-15 screenshots and
failed artifact remain recorded. This is not a second successful transfer case.

The raw audit expanded to 7,621,046 prompt characters; the CLI rejected the planner
input above its 1,048,576-character limit. `planner_context` now passes fixed verdicts,
counts, hash and a bounded first-ten-object summary, retaining the full audit on disk.
A regression test verifies that even large failure data stays below 10,000 characters
for a normal task prompt. The recovered planner result is in
`summary-recovered.json`; its original too-large attempt remains intact. An initial
compact review used a mistaken supervisor sentence about the subsequent direct
bounds; it was discarded and a fresh corrected review was selected. Both are retained
in `planner-recovery.json`. No model or evaluator rule changed during review recovery.

Two clean reproductions, `runs/surface-bounds-20260906-180014/` and `...-180231/`,
use a 3×3 interpolation grid with perimeter Z=10 and center Z=30. In both cases the
creation response reports **Z=10..10**, while subsequent direct Brep/surface bounds
report **Z=10..30** and the actual surface center is **Z=30**. Repeated direct reads
agree; the surface is not flattened. `surface_bounds_probe.py` preserves the live
document and records exact inputs, tool output and measurements. This establishes
an inaccurate initial response in this fixture; the underlying timing/cache cause
and broader affected command set are not yet established. No production repair has
been made. Do not replace trimmed geometry bounds with untrimmed surface bounds
without calibrated regression coverage.

The selected planner recommends correcting the modeling interpretation and retaining
the failed verdict. The supervisor's next priority is to investigate the misleading
initial bounds, add regression cases and only then dispatch a bounded production
repair if warranted. After that, retry the alternate pose. Curved-perimeter/shared-edge
closure remains a separate task before another chair-back attempt.

## Final verification and handoff

Completion: `runs/posed-cushion-completion-20260906-180450/summary.json`.
All three new modeling artifacts and all 15 phase-image entries retain their hashes.
The original and integration chair files are unchanged. The current document is
verified empty with explicit hidden/locked enumeration, marker none, six original
layers and 0.001 mm tolerance. All three modeling captures restored display modes.
Runtime remains PID 84726 / document 268435457 / MVID
`326aaa12-b851-4c6a-afcb-45291e734a5c`; installed SHA-256
`a8791fdfd00500113f138375a6b196d32b191873a1c5ef228e4fe1fd1df193e1`.
The document is unsaved and modified=true after test cleanup; verify before reuse.

**465 developer tests pass** (214 experiment, 238 server, 13 contract), plus experiment
lint/format checks. The 61-case production contract and plugin source/binary are
unchanged; its earlier full live pass remains historical, not rerun here. The live
harness cleanup regression and focused posed calibration/modeling are separate
validation records. Frozen historical source pins must not be resumed against
changed harness files.
