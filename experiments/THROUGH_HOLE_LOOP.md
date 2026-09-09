# Through-hole milestone — 2026-09-05

## Result

The through-hole task and both existing geometry tasks passed fresh live
modeler → independent saved-file evaluation → planner cycles on `harness`.
The modeler created a block and an oversized cylinder, subtracted the cutter,
and inspected the result in four MCP calls. No production plugin change was needed.

| Requirement | Measured result |
| --- | --- |
| Block minimum / dimensions | (0,0,0) / 100 × 60 × 20 mm |
| Complete object count / valid closed solid | 1 / pass |
| Hole axis / radius | World Z through XY (30,20) / 6 mm |
| Trimmed hole extent | Z=0 through Z=20 mm |
| Centerline intersection / overlap count | 0 / 0, successful intersection query |
| Volume | 117,738.053289983 mm³ |
| Surface area | 18,927.7875659734 mm² |

All nonplanar faces must belong to the required cylinder; planar faces must lie
on the six outer block planes. These requirements, full-height coverage and the
clear centerline reject blind holes without relying solely on mass properties.

## A genuine feedback-driven correction

The first model was correct, but the new evaluator rejected it on hole height.
The planner noticed that all other predicates passed and that the reported hole
extent was -1 to 21 mm: the bounds of the oversized cutter's underlying surface.
Its recommendation was to inspect trimmed-face measurement, not remodel the part.

The supervising development session then:

1. Independently queried the saved candidate: underlying face bounds were -1..21;
   duplicated trimmed-face bounds and adjacent-edge bounds were both 0..20.
2. Added a correct oversized-cutter fixture and observed its expected failure with
   the old evaluator. The failing report is retained.
3. Changed `face.GetBoundingBox(true)` to bounds from
   `face.DuplicateFace(false)`, measuring the actual trimmed boundary.
4. Verified all positive and negative fixtures again, including an equal-volume
   blind hole, without changing requirements or passing thresholds.
5. Re-evaluated the original saved candidate successfully, with its hash unchanged.
6. Ran a fresh through-hole session with prior planner feedback and both regressions.

This was a supervisor-reviewed evaluator repair informed by agent feedback, not
autonomous plugin-code repair. The original failed verdict remains intact. The
planner's current enum labels the recommendation `plugin_issue` because a distinct
evaluator-issue action has not yet been implemented; that is a known routing gap.

## Verification and records

All 56 experiment tests and 223 existing server tests passed, as did experiment
lint/format checks. All 26 live fixtures produced the expected verdict twice:
six valid representations passed and twenty flawed models failed. Correct hole
references use an extrusion with an inner profile independently of the production
boolean wrapper. The oversized-cutter case additionally covers boolean trimming.
A blind hole with radius √48 mm and 15 mm depth has the correct removed volume
but fails radius, full-height, centerline, boundary-plane and area checks.

Local records, intentionally ignored by Git:

- Original failed verdict: `runs/20260905-200903-0254432a/`
- Newly reproduced evaluator failure: `runs/evaluator-hole-20260905-201148/`
- Corrected evaluation of the same file: `runs/reevaluation-hole-20260905-2013/`
- Fresh through-hole pass: `runs/20260905-201324-306962d7/`
- Box regression pass: `runs/20260905-201430-8f8ab13d/`
- Prism regression pass: `runs/20260905-201608-54d92912/`
- Full fixture checks: `runs/evaluator-box-20260905-201232/`,
  `runs/evaluator-prism-20260905-201234/`, `runs/evaluator-hole-20260905-201237/`

Original candidate SHA-256, unchanged across evaluator correction:
`794c0f459b5fbd26a14cf9412fe3a9781935b45076da1df55a51cd37f328f3ff`.
Fresh passing through-hole artifact SHA-256:
`e954b69c9e9cf9ec748922bd6f92b218b788d17cfcc0999520cc289895b4b820`.

Starting with the fresh passing runs, the runner stores evaluator source snapshots
and hashes alongside each verdict. This makes subsequent evaluator changes visible
and prevents attributing a changed verdict to plugin improvement when the scoring
implementation changed instead.

## Next milestone

Reproduce and diagnose the earlier clipped prism capture before adding generated
reference-image reconstruction. Preserve all three geometry cases. Automatic plugin
builder sessions, isolated candidate deployment and rollback remain future work.
