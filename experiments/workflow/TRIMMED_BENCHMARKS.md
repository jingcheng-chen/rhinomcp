# Planar trimmed-patch benchmark

`trimmed_planar_patch` is registered in the shared native runner. The public task
specifies a rectangular planar patch with one circular opening and an origin-based
X rotation/translation. Dimensions are [width, depth, 0]; other task types retain
strictly positive three-dimensional sizes. A hole touching the boundary is rejected
before launch. Agents choose their construction using the unchanged 12-tool catalog.

The saved-file evaluator uses a deep copy in the task's local frame. It checks all
objects including hidden extras, millimeters, validity, a single open planar face,
one outer/one inner loop, tight trimmed bounds, boundary samples, analytic area and
trim-aware point occupancy. It uses 129 samples per loop and a 41x41 occupancy grid;
it is not a continuous Hausdorff-distance guarantee. Single-face representation is
an explicit restriction of this benchmark.

Twenty-four independent boundary-curve fixtures produced their expected verdicts
twice. Correct and reversed-loop constructions pass for each of two poses/dimensions;
wrong radius, opening location, absent opening, pose, scale, extra/hidden geometry,
units, solidity and clipping fail. Calibration preserves the active document.
`trimmed-calibration.json` contains portable results; full fixture models/source are
in `runs/trimmed-calibration-20260908-183943`.

Only the offset task is used for initial discovery. The reserved task has been used
for judge calibration, but has not been supplied to a modeler or planner. It is a
reserved case within the same family, not another independent family.

The evaluator uses RhinoCommon's documented
[loop conversion](https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.breploop/to3dcurve)
and [trim-aware occupancy](https://mcneel.github.io/rhinocommon-api-docs/api/RhinoCommon/html/M_Rhino_Geometry_BrepFace_IsPointOnFace_1.htm).
Independent fixtures use [planar boundary construction](https://developer.rhino3d.com/api/rhinocommon/rhino.geometry.brep/createplanarbreps?overload=3).
No production tool or plugin source changed to register this task.

## Discovery result

Run `workflow-baseline-20260908-184425-6035a018`: 25 attempts (24-call allowance
plus the rejected over-budget attempt), four failed calls, 237.55 seconds. The
modeler claims completion; the saved Brep has two faces and an unwanted cutter wall,
so mandatory topology/planarity/occupancy checks fail. Sources and document state
are preserved, and the model/screenshot/trace remain available. See
`trimmed-discovery.json` and the roadmap.

A fresh planner proposes a typed planar-region operation, explicitly distinguishing
this restricted interface from production scripting. The reviewed candidate and
pending live trial are described in `PLANAR_REGION_REVIEW.md`.
