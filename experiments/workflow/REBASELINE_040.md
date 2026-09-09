# Released 0.4.0 baseline preparation

Status: **M0 complete.** Released runtime selected and one fresh baseline run per
family recorded. These are discovery observations, not an improvement comparison.

## Verified state (2026-09-09)

The clean `harness` checkout started at `8ae969b`; the installed Python server
reports 0.4.0. `describe_capabilities` reports plugin 0.3.2 and advises updating
Rhino's plugin. The loaded assembly MVID is
`addb4d4c-9ce9-4021-b777-53b34874e663`, matching the previously recorded local
overlay. Rhino PID 58823 has one unsaved document (serial 268435457), zero objects,
no experiment marker, and **Modified=true**. This is an observation, not ongoing
permission or a reusable ownership claim.

The user subsequently authorized continuation. On recheck Rhino was already
closed and the old app-bundle plugin file was absent. Production files matched
`releases/0.4.0` (`a4bb8bbf00fc97bdf5d9b6dfab0c02b8c026dd3b`) with no differences.
The Release build passed with zero warnings/errors and was copied into the local
Rhino installation. A newly launched session and New Model were verified empty,
unsaved, unclaimed and unmodified before claiming the dedicated test session.

`describe_capabilities` now reports server and plugin 0.4.0, with no update advice.
Loaded MVID: `ee66d5ce-fb32-4807-9d17-5af8fe1458d2`.
Binary SHA256: `a1a9f9526df9a5d74e49c75dd505f0002c3d86116656c4192ce91b0644ab1d5e`.
The prior baseline, including its overlays, is preserved in `baseline-history.json`.

The existing selection journal now has a `select_release` entry point for an
already-installed release. It verifies tag/source equality, both runtime versions,
fresh document state and expected binary identity, then uses the existing
`confirm_runtime` transition. It makes no production source writes and grants no
candidate promotion. Its journal is
`experiments/runs/selection-release-20260909-224356-1a5b7a48`. Regression tests
reject source edits, untracked production files, wrong versions/binaries,
nonempty/claimed/modified documents and tampered snapshots.

## Frozen task declarations

The pilot's default is now `release-pilot.json`, with one discovery task in each
of five families: primitives, subtractive solids, posed solids, trimmed patches,
and curved panels. All entries reference new `_v2.json` files. Nine task variants
were redeclared; all prior task files and historical suite manifests are retained.
`unseen_precision_panel.json` is historical only and absent from the active suite.
Other names containing `unseen` or `reserved` do not confer held-out status: these
families have already been spent according to CONTINUE.md.

Tolerances were set before any new modeler run:

- Analytic solids use 0.001 mm for position/dimensions and absolute volume/area
  budgets computed as 1% of the target measurements.
- Curved panels use 0.001 mm for local bounds and rectangular boundaries, and a
  separate `shape_tolerance` equal to 0.5% of the largest task dimension for the
  two sampled surface-deviation checks (0.5 mm on the 100 mm panels).
- Trimmed patches are analytic planes with exact rectangular/circular boundaries:
  their plane, local bounds and boundaries use 0.001 mm, their area budget is 1%
  of the target trimmed area, and their topology and occupancy requirements remain.
  The freeform deviation allowance does not relax these analytic boundary checks.

The optional shape tolerance is restricted to panel tasks and must be positive
and finite. Its absence preserves the original evaluator behavior. The document
absolute tolerance continues to use `linear_tolerance`; allowing a 0.5 mm shape
deviation therefore does not alter Rhino's construction tolerance. Open surfaces
retain the required legacy volume field, which their evaluators do not use.

A surface-only failure remains a failed geometry verdict. During the M1 trace
audit it should be recorded as fidelity, not workflow friction, unless there is
independent evidence that a tool misled the agent. No verdict is silently converted
to a pass. Bounds/topology/boundary checks remain separately visible.

## Verification and next action

Regression tests accept a 0.4 mm panel deviation under v2 and reject that same
measurement under v1, while independently rejecting wrong bounds, a misplaced
boundary, holes and a 0.51 mm deviation under v2. Task validation rejects
nonpositive/nonfinite shape tolerances and use on analytic solids. Suite tests
check all five families and the declared percentage budgets.

Full verification: 285 server tests, 371 experiment tests and 13 contract tests
passed; server Ruff checks passed. Contract tests retain their pre-existing pytest
return-value warnings. Plugin build passed with zero warnings/errors.

## Fresh baseline observations

One run per family, no retries, all with Codex `gpt-5.6-terra`, medium reasoning,
a 30-call budget and 240-second timeout. The shared native gateway exposed the
same 14 tools throughout. CLI version, source hashes, tool catalog, task, binary
and evaluator pins are retained in [portable results](release-040-results.json).
The resolved backend model snapshot remains unavailable.

| Family | Saved-file verdict | Tool calls | Failed calls | Session seconds |
| --- | --- | ---: | ---: | ---: |
| Primitives | Pass | 3 | 0 | 21.7 |
| Subtractive solids | Pass | 8 | 0 | 46.4 |
| Posed solids | Pass | 8 | 0 | 37.5 |
| Trimmed patches | Pass | 12 | 0 | 50.5 |
| Curved panels | Pass | 9 | 0 | 50.9 |

All 40 agent calls succeeded, and all independent saved-file predicates passed.
Agent completion claims are retained separately. These five observations do not
establish broad tool reliability or a gain against a candidate. Infrastructure
capability handshakes are not included in the agent call count.

The [run registry](release-040-runs.json) points to the retained local models,
full agent traces, measurements, screenshots and preservation records under
`experiments/runs/workflow-baseline-20260909-224405-9db2a702`. Actual screenshots
for all five outputs are included in [the roadmap](../roadmap.html#model-progress)
and `assets/model-progress.json`, with source paths and hashes.

The pilot preserved its geometry/units/tolerance/layer fingerprint after every
run. Its cleanup left the empty document marked modified. A supervisor attempt
to clear that flag did not persist across the command; the empty checkpoint was
saved and closed, then a fresh empty, unclaimed, unmodified document was opened
and independently verified. The earlier `Objects.Count` guard counted deleted
objects and refused before mutation; a nondeleted-object enumeration corrected
that guard. These are supervisor/harness observations, not failed agent calls.
The local checkpoint is `experiments/runs/release-040-install-20260909/empty-after-pilot.3dm`.
No controller or modeler remains running. Rhino remains available with 0.4.0.

## Next milestone

Proceed to M1: classify and rank flaws from historical traces and this new
registry. Investigate inspection redundancy and guidance discovery as hypotheses,
not assumed defects: passing runs include repeated reads, and the panel consulted
four guidance topics. The saved-file verdict must remain separate from friction.
The modified-document cleanup issue belongs to harness recovery, not a production
modeling defect. Do not rerun these tasks to manufacture failures or gains.
