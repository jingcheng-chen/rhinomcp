# M2 — Prepared scenes and workflow families

Four workflow families now share the existing pilot, task loader and saved-file
evaluator registry: editing existing geometry, small assemblies, inspection and
recovery. These are discovery cases on released RhinoMCP 0.4.0. No production tool
has changed and no candidate improvement is claimed.

## Task and evaluator scope

| Family | Required outcome | Preservation |
| --- | --- | --- |
| Editing existing geometry | Resize and move a prepared housing | Housing identity; exact reference geometry and attributes |
| Small assembly | Five separate table parts, named and placed on nested layers | Existing document layers |
| Document inspection | Find two prepared solids and report volumes and world bounds | Object identities, geometry and attributes; only read-only tool calls |
| Recovery | Delete a wrong intermediate and create the corrected solid | Reference unchanged; wrong intermediate identity absent |

`tasks/workflow_scene.schema.json` describes analytic box scenes. The adapter in
`scene_task.py` measures saved `.3dm` files with `scene_measure.cs`, separately from
agent claims and analysis responses. Checks include exact object/name/layer sets,
valid closed planar eight-corner solids, world bounds, volume, visibility, identity
and unchanged reference data. Structured inspection answers are compared with those
independent measurements. Starting-file and measurement hashes are checked before
judging. Cleanup restores the original object/layer/unit/tolerance fingerprint.

The tolerance is fixed at 0.001 mm for analytic dimensions and position, and 1% for
volume, following the existing tolerance policy. This is an assembly/workflow
benchmark, not a general freeform shape judge. CRC and attribute comparisons check
saved states, not every transient action. Inspection additionally rejects attempts
through tools not marked read-only. The local execution remains supervised and is
not adversarial isolation.

## Calibration

Before agent discovery, 30 independent saved-file controls matched all expected
verdicts: four correct scenes passed and 26 flawed variants failed. Every fixture
was measured twice with identical results, and the active document fingerprint was
preserved. Controls cover wrong bounds, extra/missing objects, wrong layers/units,
replaced identities, retained wrong intermediates, incorrect inspection answers
and mutation attempts. See [portable calibration](scene-calibration.json).

The successful calibration is `scene-calibration-20260909-232602`. Three earlier
fixture-adapter attempts (`232309`, `232331`, `232417`) are retained under local
`experiments/runs/`: File3dm's layer-add return type and its object collection's LINQ
iterator needed corrections. No modeler was launched in those attempts. They are
fixture implementation failures, not agent retries.

## Fresh discovery protocol

Each family runs once with 17 native tools and once with all 70 production tool
definitions, using fresh Codex sessions, `gpt-5.6-terra`, medium reasoning, a 50-call
budget and 240-second timeout. The full catalog exposes unchanged production schemas
and permits document-scoped Rhino scripting/macros. Grasshopper schemas are visible
but calls are refused because these tasks own only a Rhino document. This is full
catalog discovery under Rhino task permissions, not a Grasshopper benchmark.

The subset adds layer creation and attribute read/update to the previous 14 tools.
All four families receive the same subset. The full mode checks document ownership
before and after calls. Source, catalog, task, prompt, runtime and artifact pins are
retained. Native runs precede full runs; there are no repeats or randomized pairs,
and the model alias is not an immutable backend model snapshot. Differences cannot
establish a causal advantage for either catalog.

[Held-out families](HELD_OUT.md) were declared before discovery. Small assemblies
overlap historical layer-organization work and are not claimed as unseen. Reserved
curve-editing and section-extraction families remain unrun.

Replay commands (each launches new discovery observations, never replaces evidence):

```sh
PYTHONPATH="$PWD" server/.venv/bin/python -m experiments.workflow.pilot experiments/workflow/m2-pilot.json --model gpt-5.6-terra --reasoning-effort medium
PYTHONPATH="$PWD" server/.venv/bin/python -m experiments.workflow.pilot experiments/workflow/m2-pilot.json --model gpt-5.6-terra --reasoning-effort medium --full-catalog
```

## Results — completed 2026-09-10

| Catalog | Family | Saved-file verdict | Calls | Failed calls | Agent seconds |
| --- | --- | --- | ---: | ---: | ---: |
| Native (17) | Editing | Pass | 12 | 0 | 44.5 |
| Native (17) | Assembly | Fail: five wrong layers | 23 | 6 | 60.1 |
| Native (17) | Inspection | Pass | 5 | 0 | 23.1 |
| Native (17) | Recovery | Fail: corrected object on wrong layer | 9 | 2 | 47.3 |
| Full (70) | Editing | Pass | 14 | 1 | 59.7 |
| Full (70) | Assembly | Pass, script workaround | 24 | 5 | 88.2 |
| Full (70) | Inspection | Pass | 6 | 0 | 26.2 |
| Full (70) | Recovery | Pass, script workaround | 11 | 2 | 75.2 |

Six passes and two retained failures, 104 calls and 16 failed calls. Both failed
agents reported incomplete work. All eight sessions completed, with no modeler
reruns, and all eight document fingerprints were restored. The full and native
captures look alike for the assembly; a screenshot cannot prove layer assignment.
Actual captures are in [the model gallery](../roadmap.html#model-progress).

Evidence: [run registry with reviewed fallback annotations](m2-runs.json),
[portable results and source/artifact pins](m2-results.json),
[ranked trace audit](m2-audit.json), and [final runtime](m2-final-runtime.json).
The two source run directories are `workflow-baseline-20260909-235243-2ca8879e`
and `workflow-baseline-20260909-235618-5aa1776e`. Raw events and saved files remain
local under `experiments/runs/`; portable summaries preserve their hashes.

### Leading current-runtime findings

1. **Attribute-update runtime failure:** 15 calls across five runs and three
   families return `Method not found: 'System.String Newtonsoft.Json.Linq.JToken.ToString(Newtonsoft.Json.Formatting)'`.
   All are `update_object_attributes` calls. In native assembly and recovery this
   prevents the required layer assignment; the independent model checks reject
   only those object-attribute checks. The production handler references that
   overload in `plugin/Functions/ObjectAttributes.cs:126`; the trace establishes
   the missing-method failure, while the exact dependency-binding cause still
   needs a bounded M3 investigation.
2. **Typed operation replaced by scripts:** full assembly uses `rs.ObjectLayer`
   and full recovery uses `doc.Objects.ModifyAttributes` after the typed tool fails.
   These two reviewed annotations are tied to event, call-log and exposed-catalog
   hashes. The tool was available, so these are not subset-gateway artifacts.
3. **Additional script-input failure:** full recovery's later inspection script
   references nonexistent `RhinoObject.IsVisible` and fails compilation. It is the
   sixteenth failed call, despite the gateway recording a returned envelope;
   the trace audit correctly reads the inner `success: false`. The saved scene
   still passes. This is one observed API-input error, not another established
   cross-task product defect.

The trace classifier now recognizes `method not found` as a runtime exception
instead of matching `object ... not found` across the tool name. A regression test
protects that distinction. This post-run reporting correction leaves raw traces
and saved-file verdicts untouched; the original per-suite audit snapshots remain
local. To regenerate the portable audit:

```sh
server/.venv/bin/python -m experiments.workflow.audit experiments/workflow/m2-runs.json --output experiments/workflow/m2-audit.json
```

M3 should begin with the attribute-update failure and validate across assembly and
recovery plus a predeclared held-out family. The two script workarounds are symptoms
of the same defect, not two independently established improvement opportunities.
No release, installation or product edit was made in M2.

## Verification and final state

Thirty calibration fixtures match expected verdicts; 285 server, 441 experiment
and 13 contract tests pass (739 total). Server lint and changed experiment lint
pass. Plugin source is unchanged, so no plugin rebuild was needed.

The released binary stayed at MVID `ee66d5ce-fb32-4807-9d17-5af8fe1458d2`, SHA256
`a1a9f9526df9a5d74e49c75dd505f0002c3d86116656c4192ce91b0644ab1d5e`.
Final dedicated Rhino document: zero objects, no experiment marker, no path,
original layers restored. The document remains marked modified after cleanup, as
in M0; no controller or modeler remains running. M5 hard isolation remains pending.
