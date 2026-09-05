# Capture framing repair

Investigation and intermediate live checks in Rhino 8 on 2026-09-05, on `harness`.
**Final source awaits build/live verification because the Mac locked during restart.**

## Reproduction and diagnosis

The passing posed-prism candidate from `20260905-201608-54d92912` had a clipped
1000×750 screenshot. Its saved geometry was correct (SHA-256
`614a43d367a102d35e8c30e9279dbbeb69290aed78dadfbb8bbcc6b7daa5171d`).
Importing that unchanged file into a dedicated document reproduced the clipping.
Native-resolution and alternate-aspect captures localized the issue to fitting:
`ZoomExtents()` fits the on-screen viewport, while `CaptureToBitmap` captures
with the requested image aspect. Changing capture APIs alone did not fix it.

A new live checker uses that saved prism in black wireframe, with Perspective,
Top and Back views at 1000×750, 400×1000 and 1000×400. Back exercises temporary
projection/name changes in the standard four-view layout. The checker requires
nonempty dark geometry pixels and a five-pixel border, and compares view and
document state before and after each call. A no-fit capture checks preservation
without requiring framing; an invalid view must fail without changing state.
This is a controlled-fixture image check, not a general image or geometry oracle.

The baseline also exposed camera preservation defects. `SetViewProjection(...,
true)` recomputed the target instead of restoring it. Redrawing all document views
caused unrelated orthographic camera locations to move. These failures occurred
even though the original handler intended to be read-only.

## Change and comparison

`capture_viewport` now fits visible geometry using a temporary `ViewportInfo`,
sets its aspect from the requested image dimensions, and calls `DollyExtents`
with a 1.1 border. It refreshes the document display cache, waits for queued
redraws, and restores every viewport projection and exact saved camera target.
There is no additional redraw after restoration. Temporary viewport snapshots are
disposed. Python tool documentation and the command schema describe the same
visible-object fitting and restoration behavior. No geometry evaluator or task
acceptance threshold changed.

An intermediate candidate passed the imported-model fixture but produced an empty
image in fresh loop `20260905-203244-d5b83544`, despite passing geometry evaluation.
Removing all document redraws had left newly modeled geometry absent from the
capture cache; a target-view redraw alone was insufficient. The final candidate
retains one document refresh and snapshots/restores every view around it. The
checker now deliberately leaves newly imported geometry unrefreshed before its
first capture; its framing thresholds remain unchanged.

Both baseline and candidate were built, installed with Rhino closed, restarted,
and identified by the loaded assembly MVID:

| Version | Loaded MVID | Result |
| --- | --- | --- |
| Baseline | `243974ba-3378-4df8-88b6-fd4dba066ebc` | Four of nine fitted images clipped; all ten successful captures changed camera state |
| Intermediate, without refresh | `22e41162-15da-4cc4-9367-ce9b4c74be10` | Eleven initialized-fixture cases passed; fresh modeling capture was empty |
| Intermediate, with queued refresh | `6efd7016-3b1e-4ede-b5a9-5c9f28a73634` | Framing passed; camera preservation failed |
| Final source, waiting for refresh completion | Not yet built/loaded | Direct scripting experiment preserved state; full verification pending |

For the first intermediate candidate's 1000×750 perspective image, dark geometry spans X=45..954
and Y=185..592: the full controlled fixture is separated from every image edge.
All checked camera locations/targets/directions, projection frusta, names, sizes,
display modes, active view, document modified flag and geometry checksums were
preserved (floating-point comparison tolerance 1e-8).

## Verification and local evidence

- Intermediate C# Release builds: zero warnings/errors; each installed and loaded after restart.
  Final source adds `RhinoApp.Wait()` after redraw and still requires build/reload.
- 279 Python tests passed (56 experiment and 223 server tests).
- Contract/schema synchronization checks and relevant lint/format checks passed.
- All 26 independent saved-geometry fixtures returned their expected verdicts twice:
  six valid representations passed and twenty flawed representations failed.
- Baseline capture evidence: `runs/capture-validation-20260905-202746/`.
- First intermediate capture evidence: `runs/capture-validation-20260905-203035/`.
- Queued-refresh intermediate evidence: `runs/capture-validation-20260905-203734/`.
- Intermediate fresh loop: `runs/20260905-203244-d5b83544/` (geometry pass, empty PNG).
- Geometry regression evidence: `runs/evaluator-box-20260905-203206/`,
  `runs/evaluator-prism-20260905-203208/`, `runs/evaluator-hole-20260905-203210/`.
- Investigation images/logs: `runs/capture-investigation/`.

Raw run directories are local and ignored by Git. Reproduction instructions are
in `README.md`, under Capture regression. This verifies ordinary document geometry
in the tested wireframe views; render engines, custom display conduits, page/detail
views and arbitrary reference images are not covered by this fixture.

This repair was performed by the supervising development session. An isolated
builder, automated restart/rollback and autonomous code promotion are still future
work. The investigation supplies a real baseline/repair/retest example, with final
acceptance still pending. Resume from `CONTINUE.md`.

Operational lesson: stop the dedicated Rhino process before replacing its plugin
file. An exploratory in-place replacement while Rhino was running caused script
metadata errors; a clean restart restored operation. Disk replacement alone is
neither a reload nor a safe way to validate the loaded candidate.
