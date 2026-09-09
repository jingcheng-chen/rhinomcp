# Generic panel benchmarks — evaluator calibration and discovery

These tasks measure ordinary agent use of RhinoMCP on curved surfaces. They are
inputs to the existing shared native runner, not separate modeling scripts or
chair-specific construction recipes. The surface-bounds candidate remains unadopted.

## Implemented

`biquadratic_panel` registers a rectangular analytic surface in a public world pose.
The height is `16*h*(x/w)*(1-x/w)*(y/d)*(1-y/d)`. Raised and depressed tasks use
different signed heights, X rotations and world translations. The instruction defines
the desired geometry; agents choose their construction and recovery strategies.
The same 12 native tools and unchanged production descriptions serve both tasks.

`panel_task.py` and `panel_measure.cs` read the saved file and transform only a deep
copy into the task's local frame. Checks cover all objects (including hidden extras),
units, validity, one open Brep face, one outer/no inner loops, local bounds,
bidirectional shape samples and the rectangular boundary. The geometric tolerance
is 0.05 mm. Fidelity uses 41×41 samples and 41 samples per edge, not a continuous
Hausdorff-distance guarantee; pathological features between samples may escape.
The required single-face representation is an explicit benchmark restriction.

`pilot.py` dispatches through the shared `measure(artifact, task)`/`evaluate` path.
It now offers paired `--model` and `--reasoning-effort` options. Existing default
behavior and solid tasks remain available. New evaluator sources are included in
saved source pins. No production tool, schema, plugin source or binary is changed.

## Calibration

Run `panel-calibration-20260908-093337` has **22 expected verdicts out of 22**, with
identical repeat measurements. Four valid controls (including different UV domains)
pass. Eighteen flaws fail: flat/wrong height/sign, wrong pose/scale, clipped geometry,
extra/hidden objects and wrong units. Fixtures use independent Bernstein control
nets, not the native MCP creation path. Runtime/document preservation passes.
[Portable fixture verdicts](panel-calibration.json) retain artifact hashes.

Development suite: **503 tests pass**. This count is separate from live calibration.

## Discovery and comparison boundary

The first two fresh baseline sessions use `gpt-5.6-terra`, medium reasoning, 24 calls
and 240 seconds per task. The requested alias is pinned; a resolved backend snapshot
is unavailable. Saved tasks, prompts, tool definitions, evaluator/source hashes,
binary identity, agent logs and screenshots are retained by the shared runner.

These are **discovery runs**, not completed baseline/candidate pairs. Both tasks
belong to one curved-panel family; they are not independent family-transfer evidence.
Trimmed-patch construction/evaluation is still pending. The existing through-hole
and sweep contracts provide preservation evidence but do not substitute for a new
trimmed-patch workflow comparison.

Before comparison, freeze the task suite, settings, tool catalog, evaluator and
candidate binary. Use fresh sessions in baseline/candidate then candidate/baseline
order per task, retaining failures and recovery costs. Report success before call
count, failed calls, time or token comparisons. Do not require agents to choose a
particular construction path to manufacture a benefit. Keep the source repair
unchanged. Use reviewed supervised installation/restoration; the earlier accepted
trial is an immutable record and cannot simply be rerun as a different experiment.
If both arms perform similarly, report that result without claiming broad improvement.

## Recorded discovery result

Run: `runs/workflow-baseline-20260908-093443-2dc0c8bc` on restored baseline MVID
`326aaa12-b851-4c6a-afcb-45291e734a5c`. Both sessions finish normally and preserve
the document. Raised panel: pass, eight calls, zero call failures, 140.29 seconds.
Depressed panel: fail, eight calls, zero call failures, 114.58 seconds. Its completion
claim is rejected: sampled shape error is about 4.15 mm and local bounds are wrong.
[Discovery results and images](panel-discovery.json) retain the complete observations.

Trace inspection shows the depressed agent initially treated the center like a control
point and rebuilt the surface. In the final input it changed the world Z center but
left its world Y center at the uncurved midline. The intended transformed center is
approximately (-10,107.141,12.010); it supplied (-10,114.641,12.010). This is a modeling
input error, not evidence that the bounds repair fixes this particular failure.
Neither session used creation-time rotation/scale parameters; they transformed points
themselves. Keep this evidence and allow agents the same freedom in the comparison.
Do not rewrite task instructions or force transform calls after seeing this result.

Next: freeze a repeated baseline/candidate comparison, keeping these two discovery
runs separate. The existing comparison command changes descriptions only; it cannot
switch plugin binaries. Add a reviewed binary-trial orchestration path that reuses
`pilot.run_task` and the existing ownership/identity/recovery checks. Do not duplicate
a modeling runner or reinterpret discovery as paired evidence.

## Replay

From the repository root, with one empty unclaimed dedicated Rhino document:

```sh
PYTHONPATH=. server/.venv/bin/python -m experiments.validate_panel
PYTHONPATH=. server/.venv/bin/python -m experiments.workflow.pilot experiments/workflow/panel-pilot.json --model gpt-5.6-terra --reasoning-effort medium
```

Never run these concurrently against the same Rhino instance. Source changes during
an agent session invalidate that run. Future development should extend evaluator
registrations rather than create an orchestration script for each object.
