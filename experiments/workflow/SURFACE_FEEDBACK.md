# Surface feedback repair candidate

Status: diagnosed and reviewed candidate; not built, installed or adopted. Production placement guidance remains adopted. No workflow performance benefit is established.

A newly inserted curved Brep reports flat bounds even though its interior rises or falls. Rotation and scaling use those bounds for their pivots, so the defect can also change the resulting geometry. This is reusable plugin behavior, independent of chair construction.

## Frozen baseline

`runs/surface-feedback-20260907-171728` preserves requests, analytic expectations, repeated independent measurements, source snapshot, four models/screenshots and document-preservation evidence. Eight of 19 predicates fail:

| Control | Response bounds | Geometry bounds / center | Repeat |
| --- | --- | --- | --- |
| Raised center | Fail | Pass / Pass | Pass |
| Depressed center | Fail | Pass / Pass | Pass |
| Raised, rotated 90° X | Fail | Fail / Fail | Pass |
| Depressed, scaled 2× Z | Fail | Fail / Fail | Pass |

The trimmed through-hole control passes tight bounds, unchanged source geometry and solid checks. These are diagnostic fixtures, not agent modeling runs. Screenshots show appearance; analytic checks establish failures.

Insertion isolation (`runs/bounds-insert-20260907-171221`) found that redraw, identity-transform bounds and pre-reading bounds did not repair the initial result. A deep DuplicateBrep returned the correct bounds immediately. In-memory construction (`runs/bounds-stage-20260907-171140`) was already correct. Underlying-surface bounds are unsuitable for trimmed geometry; the candidate retains the complete Brep and trims.

## Planner → bounded builder

Fresh planner: `runs/surface-feedback-plan-20260907-171559`, classification `plugin_issue`.
Fresh builder: `runs/repair-20260907-171657-ec239178`, baseline `69aa2298c450ee48f864c7ef78e84d83d5b59f47`.
Scope: `harness/repairs/surface-feedback.json`. Portable patch: [surface-feedback-candidate.patch](surface-feedback-candidate.patch).

Supervisor review: exactly two declared files change. The shared Serializer helper computes accurate bounds on a disposed deep Brep copy and preserves the existing path for other geometry. Serialization and rotation/scaling pivots use it. No schema, evaluator, transform order or placement-description changes. Whole-checkout scope validation completed. The controller now permits explicitly declared existing serializer files; undeclared files remain blocked.

Development verification: 491 Python/schema/harness tests pass. This does not compile or validate the proposed C# repair. Duplication adds work for every serialized/transformed Brep; cost on complex geometry remains unknown.

## Next acceptance gate

Use the existing supervised build/install/restart/recovery lifecycle, preserving the working binary and owned empty document. Check candidate integrity before execution. Run the frozen 19 predicates with the candidate and preserve the existing 61-case live contract. Record candidate MVID, screenshots and artifact hashes. Compare fresh surface workflows and check non-surface/trimmed cases before deciding adoption; do not infer efficiency from geometry correctness. Keep automatic promotion and new-tool builder support marked pending.

The last observed document was empty, unsaved and unclaimed (268435459); installed MVID remained 326aaa12-b851-4c6a-afcb-45291e734a5c. Recheck both before continuing.
