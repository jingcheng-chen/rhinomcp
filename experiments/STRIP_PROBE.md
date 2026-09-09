# Curved rectangular strip: live capability diagnosis

Completed 2026-09-06. This is a focused, transferable experiment derived from the
chair's open frame strips. It uses actual MCP create/sweep commands and independent
saved-file measurements. It does not change or install a plugin candidate.

## Fixed task and results

The target is one closed quarter-annular solid: centerline radius 100 mm, radial
width 20 mm, height 10 mm, 90-degree arc in the positive XY quadrant, origin fixed.
Its expected volume is 10000π mm³ and surface area is 3000π + 400 mm². Bounds are
(0,0,0)–(110,110,10). The judge checks validity, closure, naked edges, units, area,
volume, bounds and membership at 192 fixed interior/exterior grid points. Finite
sampling is a diagnostic predicate, not an exhaustive equivalence proof.

| Fixture | Expected and observed result |
| --- | --- |
| Actual MCP sweep, `closed=false` | Fail: valid open shell, 8 naked edges, 2 end loops |
| Actual MCP sweep, `closed=true` | Fail: identical measurements to false |
| Supervisor-capped copy of the first sweep | Pass: one solid, zero naked edges |
| Independent annular-sector extrusion, inward orientation | Pass |
| Independent annular-sector extrusion, outward orientation | Pass |
| Wrong radial width | Fail |
| Wrong radius with deliberately equal volume | Fail despite passing volume |
| Correct shape in the wrong position | Fail |
| Extra object | Fail |

All **nine fixtures produced the expected verdict twice**, with identical repeated
measurements. Capping the actual sweep yields volume 31415.9231 mm³ and area
9824.7771 mm²; the independently extruded sector yields 31415.9266 mm³ and
9824.7780 mm². Capping adds the expected two 20×10 mm end faces. Geometry and
placement were already correct; missing closure is the relevant capability gap.

## Interpretation and bounded proposal

The fresh planner classifies the result as `plugin_issue` for a missing generic
capability, not evidence that end-capping previously worked and regressed.
The existing handler reads `closed` but never uses it. That is a separate contract
issue: closing a sweep around a rail is not the same operation as capping its ends.
Do not silently redefine `closed` to mean end-capping.

The planner proposes an explicit opt-in `cap_planar_ends` parameter on `sweep1`:

- Default false, preserving existing surface output.
- When enabled, attempt planar-hole capping at document tolerance, then require
  valid closed results before adding anything to the document.
- Fail clearly without partial output if capping cannot produce the required solid.
- Test this quarter-arc case, omitted/false compatibility, invalid parameter types,
  uncapable boundaries and multiple-result failure atomicity. Preserve existing
  closed-rail behavior; investigate its unused flag separately.
- Run the existing 43 cases unchanged plus the new capping cases. Keep independent
  controls/evaluator outside the builder's scope.

**This proposal is not implemented.** The current bounded builder is still scoped
to the earlier capture-repair pilot. Next, give it a reviewed, pinned per-repair
scope for the sweep C#/Python/schema/tests while retaining whole-checkout integrity
checks. Then dispatch a fresh builder and use the live trial controller for review,
build, baseline comparison and restoration. Do not bypass those gates with a direct
production edit or reset an executed historical candidate.

Layer hierarchy is a separate requested milestone. The proposed capping change
should preserve source attributes/layer choices and must not introduce chair-specific
layers or geometry. A continuous cushion patch remains another focused modeling task.

## Preservation and evaluator correction

The probe uses the existing dedicated document without resetting it. It records all
pre-existing object IDs, geometry CRCs, serialized object attributes, layer parent
IDs/names/visibility/locking, units and tolerance. It deletes only IDs returned by
its own temporary create/sweep calls, then requires an exact before/after match.
All 65 chair objects and all six existing layers matched. The chair's original
marker remains and its saved model is untouched. These checks do not lock out a
human/external client; concurrent changes cause failure and require inspection.

An initial preflight found that ObjectAttributes has no DataCRC method. The guard
now uses its supported serialized representation; no geometry had changed then.
The first complete probe stopped on an unexpected positive-control verdict before
planning: the independently extruded solid faced inward. Rhino's IsPointInside
expects outward orientation and returned complementary containment results. The
judge now duplicates and normalizes inward Breps in memory before containment,
records original orientation, and checks both orientations as positive controls.
Saved files and geometric requirements are unchanged. The failed record is retained
rather than rewritten. This is a measurement correction, not a plugin repair.

## Evidence and continuation

- Successful run: `runs/strip-20260906-090832-bc7dde0c/`.
- Earlier unexpected-positive run: `runs/strip-20260906-090640-0ebc0f16/`.
- Records: `commands.jsonl`, fixture `.3dm` files, `validation.json`, `before.json`,
  `after.json`, input/source snapshots, planner prompt/events and `summary.json`.
- Loaded baseline MVID: `90d87782-2887-435e-a8b2-02467f0c5094`.
- Source: `strip_probe.py`, `strip_measure.cs`, `strip_controls.cs`.
- Run from the root with `server/.venv/bin/python -m experiments.strip_probe` only
  after verifying the dedicated unsaved document and absence of competing work.

**356 developer tests passed** (133 experiment + 223 server), with experiment
lint/format checks. Eight new tests check positive geometry, nonfinite values,
closure, bounds, area, membership, units and extra-object rejection. No production
C#/Python/schema behavior changed, and the old 43-case live suite was not rerun in
this diagnostic step. Local detailed evidence remains ignored by Git.
