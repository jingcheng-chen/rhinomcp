# Hierarchical layer diagnosis

The next organization benchmark is a small two-part assembly:

```text
Assembly
├── Left
│   └── Part → left_part
└── Right
    └── Part → right_part
```

Each part is a visible, unlocked, valid solid cube, 10 mm on each side. The left
cube spans (0,0,0)–(10,10,10); the right spans (30,0,0)–(40,10,10).
Duplicate leaf names are intentional: an agent must address full paths accurately.
This is an organization capability test, not a chair reconstruction score.

## Independent evaluation

`layer_controls.cs` creates saved fixtures directly through File3dm, without
calling the plugin's layer creation handler or altering the active document.
`layer_measure.cs` reopens each file and reads parent IDs, layer indices, visibility,
lock state, object attributes, solid validity and world bounds. `layer_probe.py`
reconstructs full paths from parent IDs, detects invalid trees, and checks exact
part assignments. Repeated reads must agree and leave file hashes unchanged.

Nine calibrated fixtures: correct hierarchy passes; flattened hierarchy, wrong
parent, wrong assignment, hidden parent, locked child, Default-layer geometry,
extra object and wrong geometry fail. This verifies persistence through saving and
independent file reopening, not a desktop UI close/reopen operation. It does not
measure general editability or shape equivalence beyond the specified cubes.

## Observed live behavior

The live probe uses a unique root and actual MCP commands. Creating `Left` and
`Right` under that root succeeds. Requesting `Part` under `root::Left` instead
creates a top-level `Part`. The second `Part` request collides with that unintended
root name and errors. Assigning objects to the requested full paths then fails
because those layers do not exist. A missing-parent request likewise succeeds with an empty parent ID, silently
creating an unrelated top-level layer.

The source explains the first failure: `CreateLayer` calls `FindName(parent)` and
leaves ParentLayerId empty when lookup fails. It also does not check a failed Add
before serializing the result. Object attribute assignment already has a full-path
fallback; failures here do not alone demonstrate a defect in that separate handler.

Existing empty document layers are retained in the diagnostic saved file, so its
strict exact-tree check also reports those extra layers. The targeted evidence is
the returned empty parent ID, failed full-path assignments and actual saved parent
relationships. A future fresh modeling task should use a defined clean layer table.
No production code, accepted 52-case contract, or chair artifact is changed.

## Next bounded repair

Use a fresh planner's diagnosis to review a narrow builder scope. Resolve exact
full paths; retain unambiguous short-name use. Missing or ambiguous parents should
fail clearly without adding layers. Handle duplicate siblings and failed insertion
without a null-reference error. Keep Python documentation, C# behavior and schema
in the same change. Verify duplicate child names beneath different parents,
full-path assignments and saved parent-ID relationships. Add positive and negative
live requirements while preserving all 52 accepted baseline checks. Only then run
a fresh modeling agent on this assembly task and assess benefit.

## Evidence and limitations

The run records include frozen source copies, calibration artifacts, command
responses, two saved-file measurements, before/after document fingerprints and a
fresh planner's output. Probe cleanup deletes only returned IDs and checks that
pre-existing geometry, layers, units and tolerance are preserved. Earlier failed
setup attempts remain recorded; they are not counted as completed live diagnoses.
Full local logs are ignored by Git; this report and the evaluator are portable.

Completed live diagnosis: `runs/layers-20260906-144144-a4abc4d4/`.
The fresh planner returns `plugin_issue`; all nine calibration verdicts are expected,
all repeated measurements agree, and the before/after document fingerprints match.
**404 developer tests pass** (163 experiment, 228 server, 13 contract); 12 existing
contract return-value warnings remain. Experiment lint/format checks pass. A final
Python local-variable rename for lint does not change the measured evaluator rules;
the run retains its exact original source snapshot.

The previously accepted capping runtime remains active (PID 94887 at this run,
MVID `79b1500e-e20d-47af-9c83-6f915729a712`). Recheck live identity and ownership
before the next operation. The accepted 52-case suite was not rerun for this
harness-only diagnostic; its prior result is preserved, not claimed as a new run.
