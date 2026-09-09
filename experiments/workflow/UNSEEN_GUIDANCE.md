# Fresh-task guidance feedback — 2026-09-09

Four fresh Claude sonnet/medium sessions used the unchanged packaged guidance and
14-tool native interface. These are new parameterized cases within existing families,
not four previously unseen families. Each had 32 calls and 240 seconds available.
The prompt requested qualitative feedback, without adding construction recipes.

| Case | Independent saved-model result | Calls |
| --- | --- | --- |
| Offset through-hole block | Pass: bounds, solid, volume, hole radius/axis/full clearance | 8 |
| Negative-angle triangular prism | Pass: posed vertices, handedness, closure and volume | 8 |
| Steep tilted perforated patch | Pass: pose, boundaries, actual opening and area | 9 |
| Shallow curved panel | Fail: surface shape and height; boundary and topology pass | 21 |

Total: 3/4 passes, 46 calls, zero failed calls, 281.40 modeling seconds.
All source pins, plugin identity and document fingerprints remained unchanged.
Screenshots are evidence of appearance; saved-file measurements determine verdicts.
Run: `experiments/runs/workflow-baseline-20260909-182654-2ada6f48`.
Full feedback, measurements and provenance: `unseen-guidance-results.json`.

## Findings and disposition

1. **Confirmed incomplete edge reporting.** The patch agent noticed five edges but
   only four reported naked edges. `plugin/Functions/AnalyzeObjects.cs:183` uses
   `DuplicateNakedEdgeCurves(true, false)`, excluding inner loops. A read-only check
   of the saved patch returned outer=4, inner=1, total=5, topological naked=5.
   This is a diagnostic reporting issue, not a missing hole. Prioritize a bounded
   repair with inner-hole, outer-boundary, closed-solid and seam preservation cases.
   No plugin change or installation was made during this discovery run.
2. **Curved construction lacks measured accuracy.** The panel's maximum sampled
   surface-to-reference deviation was 0.43982 mm (tolerance 0.05 mm); its height
   was 8.66669 instead of 9 mm. All 49 supplied curve points were accurate to
   0.000028 mm in vertical formula residual, pointing to interpolation/loft behavior
   between samples rather than incorrect world-point arithmetic. The agent admitted
   it did not numerically bound non-sampled deviation but still claimed completion.
   Develop a tested curved-surface recipe and an accuracy-check workflow before
   adding advice to the distributed guide. Do not merely loosen the tolerance.
3. **Surface schema clarity.** The panel agent requested clearer control-grid
   documentation. Inspection shows SURFACE already accepts count/points/degree/closed,
   and calls `NurbsSurface.CreateThroughPoints`: these are interpolation points,
   not direct control vertices. Clarify that distinction and point ordering after
   validating an accurate construction. The reported truncation itself is unverified.
4. **World-origin rotation ergonomics.** The patch agent used the documented pivot
   compensation successfully, but requested a direct origin/pivot option to avoid
   manual arithmetic. This is a capability proposal requiring comparison, not a
   demonstrated bug in the current documented behavior.
5. **Optional Boolean metrics.** The block agent proposed returning bounds, volume
   and edge checks with Boolean results to save a follow-up analysis call. Measure
   round-trip savings against response size/cost before adopting it.
6. **Feedback collection gap.** The prism passed independently but its structured
   summary was just `Test`; its trace omitted the requested improvement feedback.
   The block supplied feedback in narrative events rather than its structured result.
   Future feedback collection should require explicit fields and preserve narrative
   events. Missing feedback must not be invented or conflated with geometry failure.

This is discovery, one run per case, without a paired baseline. It does not establish
causal benefit, repeatability, generalization to untouched families or adversarial
judge isolation. The guide and production code remain unchanged during this turn.
The read-only edge probe initially failed due to its object enumeration approach;
those errors are retained in local logs, separately from the 46 agent tool calls.
