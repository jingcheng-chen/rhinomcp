# Surface feedback repair — live validation

Status (2026-09-08): **controlled trial accepted; baseline restored; candidate not adopted**.
Production placement guidance remains adopted. No general agent-efficiency gain is established.

A newly inserted curved Brep can report flat bounds even though its interior rises or falls.
Rotation and scaling use those bounds for their pivots, so the defect also changes resulting
geometry. The repair improves a shared plugin operation, independent of chair construction.

## Result

| Checks | Baseline | Candidate | Restored baseline |
| --- | ---: | ---: | ---: |
| Prior preservation requirements | 61/61 | 61/61 | 61/61 |
| Surface predicates | 11/19 | 19/19 | 11/19 |
| Total true predicates | 72/80 | 80/80 | 72/80 |
| Expected phase verdicts matched | 80/80 | 80/80 | 80/80 |

Exactly eight surface predicates improve, with no regressions: raised/depressed creation
responses and the response/bounds/center checks for rotated and scaled surfaces. The trimmed
through-hole control retains tight bounds, solid geometry and unchanged source data.
Screenshots alone do not prove placement: each view fits its own model. Numeric bounds
and center points establish the repair. Raised/depressed untransformed geometry is unchanged.

All three phases run the original 61-case contract, including 26 geometry fixtures,
11 viewport checks, seven fresh modeling sessions, the equal-volume negative reference
control, seven sweep checks and nine layer checks. The 21 modeling sessions preserve
correctness; their default agent settings are not a pinned efficiency comparison.

## Evidence and controller

Trial: `runs/repair-20260907-171657-ec239178/trial-9983c15f`.
Phase reports: `live-615e844d` (baseline), `live-945072a1` (candidate),
`live-30fb2b65` (restored). Terminal state: `accepted_trial`, `runtime_dirty=false`,
`promoted=false`. A successful trial always restores baseline; acceptance is not promotion.

The frozen `harness/trial-surface-feedback.json` preserves the prior 61 cases and adds
19 unchanged analytic surface predicates, recording eight false baseline expectations.
The adapter, suite inputs, candidate inventory and binary identities are pinned.
The surface probe runs under the adapter's existing lock; standalone use retains its lock.
[Portable results and image/model provenance](surface-feedback-trial.json) include all
33 diagnostic/modeling screenshots across the three phases. Full models and agent traces
remain in ignored local runs; missing evidence on another machine must not be assumed present.

| Binary | Loaded MVID | SHA-256 |
| --- | --- | --- |
| Baseline/restored | 326aaa12-b851-4c6a-afcb-45291e734a5c | a8791fdfd00500113f138375a6b196d32b191873a1c5ef228e4fe1fd1df193e1 |
| Candidate | 606ab732-416a-4b80-b041-19a264b21b2f | 3a79ef7ffde3194d21ffca8274b58837c7eade562c5e9c6d630b18de88a74677 |

Supervisor verified empty owned documents before both restarts and copied the reviewed
build output according to local installation instructions. Final observed baseline process
66421 has one empty unsaved unclaimed document, 268435457. Recheck before further work.

## Diagnosis and bounded repair

Insertion isolation (`runs/bounds-insert-20260907-171221`) found that redraw, identity-transform
bounds and pre-reading bounds did not repair the initial result. Deep DuplicateBrep bounds
were correct immediately; in-memory construction was already correct. The repair retains
trims rather than measuring oversized underlying surfaces.

Fresh planner: `runs/surface-feedback-plan-20260907-171559`, classification `plugin_issue`.
Fresh builder: `runs/repair-20260907-171657-ec239178`, baseline revision
`69aa2298c450ee48f864c7ef78e84d83d5b59f47`.
Scope: `harness/repairs/surface-feedback.json`; [reviewed patch](surface-feedback-candidate.patch).
Exactly two source files change: a shared Serializer helper computes accurate bounds on a
disposed deep Brep copy; serialization and rotation/scaling pivots call it. Other geometry
keeps its existing bounds path. Schemas, transform order and placement descriptions are unchanged.

Candidate C# build: zero warnings/errors. Candidate Python/schema tests: 251 pass; lint passes.
Development suite: 492 pass, including a test preserving the frozen case inventory and known
baseline failures. These counts are distinct from the live trial outcomes.

## Copy cost and limits

`runs/bounds-cost-20260908-090849` compares warmed direct bounds with deep-copy bounds on
three saved Breps. Ten alternating-order blocks of 100 operations per condition, per object;
medians in milliseconds per operation:

| Saved Brep | Faces | Direct | Deep copy + bounds |
| --- | ---: | ---: | ---: |
| Raised surface | 1 | 0.00378 | 0.00647 |
| Through-hole solid | 7 | 0.00824 | 0.02739 |
| Quarter sweep | 6 | 0.05795 | 0.07493 |

Bounds agree in the probe; source geometry and the Rhino document remain unchanged.
This measures the added operation on small warmed inputs, using restored baseline Rhino.
It does not measure cold insertion, whole MCP latency, large assemblies, memory peaks or
agent efficiency. Duplication is measurably more expensive; large-model cost remains unknown.
The evaluator still runs inside the plugin's Rhino process, so this is supervised trusted-code
validation, not protection against a malicious candidate.

## Next milestone

Register generic curved-panel and trimmed-patch benchmarks with the shared native runner.
Calibrate correct and flawed fixtures, freeze tasks and agent settings, then compare repeated
baseline/candidate workflows. Reuse the unchanged candidate through a supervised transition
and preserve recovery. Decide adoption from correctness and workflow evidence together.
New-tool builder support and automatic promotion remain pending.
