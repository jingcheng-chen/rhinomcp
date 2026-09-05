# Capture framing repair

Verified live in Rhino 8 on 2026-09-05, on the `harness` branch.

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

An intermediate candidate without redraw passed the initialized-model fixture.
Its fresh-loop screenshot appeared empty in the preview and was initially
misdiagnosed as a display-cache failure. A later audit of the unchanged saved PNG
found 11,807 dark pixels, valid margins, and the exact same SHA-256 as the final
candidate's image. **The empty-image diagnosis was incorrect.** A document refresh
is retained from the original handler; this investigation did not establish that
removing it prevents newly created geometry from being captured.

Retaining that refresh exposed a separately measured issue: Rhino queues redraws,
so camera adjustments could occur after synchronous restoration. Waiting for the
refresh before fitting/restoring fixes that ordering. The checker deliberately
leaves imported geometry unrefreshed before the first capture; framing and state
thresholds remain unchanged. Saved-image pixels and hashes take precedence over
an unreliable inline preview.

Both baseline and candidate were built, installed with Rhino closed, restarted,
and identified by the loaded assembly MVID:

| Version | Loaded MVID | Result |
| --- | --- | --- |
| Baseline | `243974ba-3378-4df8-88b6-fd4dba066ebc` | Four of nine fitted images clipped; all ten successful captures changed camera state |
| Intermediate, without refresh | `22e41162-15da-4cc4-9367-ce9b4c74be10` | Eleven initialized-fixture cases passed; fresh PNG later confirmed valid |
| Intermediate, with queued refresh | `6efd7016-3b1e-4ede-b5a9-5c9f28a73634` | Framing passed; camera preservation failed |
| Final, waiting for refresh completion | `90d87782-2887-435e-a8b2-02467f0c5094` | All eleven cases passed, starting with unrefreshed geometry |

For the final candidate's 1000×750 perspective image, dark geometry spans X=45..954
and Y=185..592: the full controlled fixture is separated from every image edge.
All checked camera locations/targets/directions, projection frusta, names, sizes,
display modes, active view, document modified flag and geometry checksums were
preserved (floating-point comparison tolerance 1e-8).

## Verification and local evidence

- Final C# Release build: zero warnings/errors; installed with Rhino closed and
  loaded after restart, with the candidate MVID verified through the live bridge.
- 279 Python tests passed (56 experiment and 223 server tests).
- Contract/schema synchronization checks and relevant lint/format checks passed.
- All 26 independent saved-geometry fixtures returned their expected verdicts twice:
  six valid representations passed and twenty flawed representations failed.
- Baseline capture evidence: `runs/capture-validation-20260905-202746/`.
- First intermediate capture evidence: `runs/capture-validation-20260905-203035/`.
- Queued-refresh intermediate evidence: `runs/capture-validation-20260905-203734/`.
- Intermediate fresh loop: `runs/20260905-203244-d5b83544/` (geometry and PNG pass;
  the earlier empty-preview interpretation was disproved by a pixel/hash audit).
- Final capture evidence: `runs/capture-validation-20260905-205236/`.
- Final geometry regression evidence: `runs/evaluator-box-20260905-205401/`,
  `runs/evaluator-prism-20260905-205403/`, `runs/evaluator-hole-20260905-205406/`.
- Final fresh modeler/evaluator/planner loop: `runs/20260905-205440-a9e6b334/`.
  Geometry passed and the planner accepted. Candidate `.3dm` SHA-256:
  `63d768932b07c8715b927cba3694c7eb1f6e07736cedc406fa7f8bed72767cfd`.
  The PNG has 11,807 dark pixels with bounds X=45..954, Y=185..592, preserving
  margins on all sides. PNG SHA-256:
  `aba0bef0fc2711cfdf6e5231d94e306e6618cf11a81f9be212152ea30ca5c72d`.
- Intermediate image audit: `runs/capture-investigation/intermediate-pixel-audit.json`.
- Investigation images/logs: `runs/capture-investigation/`.

Raw run directories are local and ignored by Git. Reproduction instructions are
in `README.md`, under Capture regression. This verifies ordinary document geometry
in the tested wireframe views; render engines, custom display conduits, page/detail
views and arbitrary reference images are not covered by this fixture.

This repair was performed by the supervising development session. An isolated
builder, automated restart/rollback and autonomous code promotion are still future
work. The result supplies a verified baseline/repair/retest example for that next stage.
Resume development from `CONTINUE.md`.

Operational lesson: stop the dedicated Rhino process before replacing its plugin
file. An exploratory in-place replacement while Rhino was running caused script
metadata errors; a clean restart restored operation. Disk replacement alone is
neither a reload nor a safe way to validate the loaded candidate.
