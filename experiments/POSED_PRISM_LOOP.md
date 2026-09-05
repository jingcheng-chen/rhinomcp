# Posed prism milestone — 2026-09-05

## Result

The next task and the existing box regression both passed fresh live Codex
modeler → saved-file evaluator → fresh Codex planner cycles on the `harness`
branch. No production plugin changes were required.

The new task defines a triangular prism from local profile (0,0), (80,0), (0,40),
extruded by 25 mm, rotated +30° about world Z through origin, then translated by
(120,-40,15) mm. It requires exactly one valid closed solid and no construction
profile. The modeler constructed the transformed profile directly, extruded it,
deleted the profile, and inspected the result in four MCP calls.

| Predicate | Result |
| --- | --- |
| Units / complete object count | Millimeters / 1 |
| Geometry validity / closed solid | Pass / pass |
| Six prescribed corners | Pass within 0.001 mm |
| Vertices inside reference prism | Pass |
| Planar faces / straight edges | Pass / pass |
| Volume | 40,000 mm³ |
| Surface area | 8,436.0679775 mm² |

Final base corners were (120,-40,15), (189.282032303,0,15), and
(100,-5.358983849,15); top corners have the same XY coordinates at Z=40 mm.
The modeler's chosen sequence did not use the optional rotation tool. The result
demonstrates correct final pose, not coverage of every available operation.

## Independent evaluator validation

Fifteen saved-file fixtures were evaluated twice each. Three valid forms passed:
the original box, the posed prism, and the same prism with a subdivided planar
face. All twelve deliberately flawed forms failed. Prism errors covered wrong
rotation, translation, mirrored triangle, scale, open geometry, extra geometry,
and units. The reference prism was built from joined planar faces rather than
the production curve-extrusion tool.

The new evaluator checks positions and shape, not just volume or bounding-box
dimensions. Unit tests also reject an outlying vertex even when required corners
and reported volume are present, and accept equivalent face subdivisions.

## Local evidence

- Prism: `runs/20260905-190302-8a0becaf/`
- Box regression: `runs/20260905-190407-f8cdae08/`
- Box fixtures: `runs/evaluator-box-20260905-190230/`
- Prism fixtures: `runs/evaluator-prism-20260905-190231/`

Prism artifact SHA-256:
`ab2b128361fa95a4b4a4bdcc292a52283ff6ac068257a17379db16fab1545586`.
Box regression artifact SHA-256:
`fcdf14fb8059f4cd10644be2b3989d94c25f9d7868b05c4dd5574ac9eac512a8`.

These generated directories are ignored by Git; this report is the portable
summary. The original harness milestone was committed as `3e5ee41` before this
work began. All 38 experiment tests and 223 existing server tests passed;
experiment lint/format checks passed.

## Open observation and next step

The saved prism screenshot appears clipped. It is supplementary evidence and
does not enter geometric acceptance. Capture framing needs a separate reproduction
and diagnosis before image comparison becomes an acceptance criterion.

Next: define and independently validate a through-hole task, preserving these
two passing cases. Autonomous plugin repair and reload remain later milestones.
