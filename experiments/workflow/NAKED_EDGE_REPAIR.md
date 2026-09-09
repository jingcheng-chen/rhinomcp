# Count inner naked edges — 2026-09-09

Fresh-task feedback exposed `analyze_objects.naked_edge_count` excluding inner
hole boundaries. The handler now counts Brep edges with Naked valence directly,
including inner boundaries without counting seams or allocating duplicate curves.
The Python tool description states the semantics. No parameters or envelope changed.

`experiments/naked_edge_probe.py` invokes the loaded plugin's actual Brep metrics
method on six in-memory fixtures, preserving the document. Baseline results:
outer=4, one-hole=4 (expected5), two-hole=4 (expected6), box=0, sphere=0,
open-cylinder=2. Candidate passes all six including closed/seam preservation.
Portable results: naked-edge-baseline.json and naked-edge-candidate.json.

Release build passed with zero warnings/errors. The previous binary was archived,
the empty document saved, Rhino shut down, and the rebuilt plugin copied to the
local app bundle before restart. Loaded candidate MVID:
addb4d4c-9ce9-4021-b777-53b34874e663. This is local validation, not publication.
The test initially required a fix for Newtonsoft assembly-context serialization;
only the final probe with parsed numeric metrics provides the regression evidence.
