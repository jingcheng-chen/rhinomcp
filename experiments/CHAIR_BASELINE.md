# First complex screenshot diagnostic: Barcelona chair

Completed 2026-09-06. The chair is one benchmark for a general RhinoMCP improvement
process across many objects. This run establishes a starting point and identifies
reusable experiments; it does not demonstrate self-improvement or generalization.

## Result

A fresh modeler built a recognizable, schematic chair from four browser screenshots.
The independent planner recommends `revise_modeling`. All nine basic structural
checks pass, but visual fidelity remains **unscored** and materially incomplete.
No production plugin, server or protocol behavior changed; no repair was dispatched
and no candidate was promoted. The existing 43-case contract is unchanged.

| Observation | Result |
| --- | --- |
| Saved geometry | 65 valid named objects; no construction curves |
| Representation | 61 solid extrusions, four open swept Breps |
| Bounds in normalized coordinates | 1000 × 1051.45 × 1244.30 mm |
| Required naming groups | frame, seat, back and straps present |
| Modeler | 172.4 seconds, 38 gateway calls, including 21 modeling commands |
| Planner | 60.2 seconds; four public images and three candidate views inspected |
| Tool errors | No reported command failures |
| Acceptance | `unscored`; structural validity does not establish appearance |

The modeler used rectangular sweep profiles for the metal strips, rather than
round pipes. It removed its source curves and excluded the ottoman. It also
reported its own limitations: hard-edged panels, absent soft upholstery details,
unrounded metal edges/junctions and open frame strips.

## What the failures suggest

1. **Continuous cushion surfaces:** the modeler stacked separate box-like tuft
   panels on slabs. The references show continuous, rounded padding with convex
   cells and recessed seams. This is initially a modeling strategy/affordance
   question; it does not prove that the existing surface tools are defective.
2. **Curved strip construction:** the overall X frame is recognizable, but the
   profile, transitions and frame-to-cushion spacing differ. Four frame objects
   remain open. The existing `sweep1` contract has a `closed` sweep option but no
   explicit end-cap option; its implementation does not cap planar ends. This
   merits a focused workflow/capability test, not a claim of a regression.
3. **Visual evaluation and capture:** cameras and materials are not matched. Some
   candidate orthographic captures are tight or crop the top; inspect framing in
   a focused tall-object fixture before relying on silhouette scores. The
   previous wireframe capture suite is not general image acceptance evidence.

The supervisor also compared the separately reserved rear-oblique screenshot
against the final model views. It supports the qualitative concerns about the
flat back slab, squared frame and strap wrapping. This comparison uses approximate
views and is not an objective held-out score. The reserved image was not delivered
to either fresh agent. One unseen view of the same chair is not transfer to a new
object; other complex cases and repeated trials remain necessary.

## Next bounded experiments

Split the next work into two reusable tasks, so causes can be isolated:

- A curved rectangular strip with a fixed rail/profile, controlled orientation and
  explicit solid-closure requirement. First reproduce the open-end result, inspect
  available workflows, and define independent geometry predicates. Only then decide
  whether to add a generic capping capability or revise guidance.
- A continuous rounded 2×2 cushion patch with convex regions and recessed seams.
  First attempt it using existing surface tools. Distinguish missing instructions
  from an actual missing operation; calibrate visual/geometry checks with positives
  and deliberate negatives.

Apply any learned construction to the chair afterward. Keep plugin/evaluator/model
settings fixed for comparisons, rerun the 43-case suite for production changes,
and eventually test another unseen object. Avoid chair-specific plugin commands.

## Evidence and reproduction

Source: [Barcelona Chair by alesandrofrom on Sketchfab](https://sketchfab.com/3d-models/barcelona-chair-7f871ae1a07f4f68b2146d71b4c52bfa).
Only browser screenshots were used; the target mesh was not extracted. Public
views are `front`, `front-oblique`, `side`, `back-detail`; the reserved view is
`rear-oblique`. These are approximate perspective labels. The scene includes the
excluded ottoman; rear screenshots crop some feet. Width 1000 mm is a normalization
convention, not a recovered real-world dimension.

- Reference pack: `runs/chair-reference-20260906/` with `manifest.json` and hashes.
- Run: `runs/visual-20260906-084828-2fc89506/`.
- Model: `candidate.3dm`, SHA-256
  `188777bf59d32b40dc122959b6753b6407f9e58f874a562ef76f9f98983a6923`.
- Loaded plugin MVID: `90d87782-2887-435e-a8b2-02467f0c5094`.
- Reports: `evaluation.json`, `summary.json`, per-role events/prompts/status,
  gateway logs and `perspective/front/right/back/top.png`.
- Run source: `9ef4a0f` plus the saved, hashed new-runner snapshots in `source/`.
  Agent version and executable invocation are recorded; explicit model pinning
  remains a limitation of the current session launcher.

The Rhino document remains open with the baseline chair and run marker. Do not
assume it is empty or clear it without verifying ownership and saved evidence.
See `VISUAL_BENCHMARKS.md` for the generic runbook. Local images/models/logs are
ignored by Git and are not transferred by checking out this branch.

Verification: **348 developer tests passed** (125 experiment + 223 server), with
experiment lint/format checks. Ten new tests cover reference isolation/integrity,
read-only review, forbidden execution and the separation of structure from visual
acceptance. The saved-file audit also ran successfully in Rhino. The old 43-case
live suite was not rerun in this step because production behavior was unchanged;
its previous restoration result remains historical evidence.
