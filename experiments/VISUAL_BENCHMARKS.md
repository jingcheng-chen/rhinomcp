# Screenshot benchmarks for general RhinoMCP improvement

The objective is a reusable improvement process across many modeling tasks.
The Barcelona chair is one complex diagnostic case. A chair-shaped output is not
sufficient evidence of general improvement, and chair-specific geometry must not
be hard-coded into the plugin. Preserve the fixed 43-case suite; add focused tasks
and other unseen objects to test transfer before claiming generalization.

## Diagnostic baseline runner

`visual_runner.py` uses fresh modeler and planner sessions through `visual_mcp.py`.
This is a separate diagnostic track from the exact analytic tasks in `runner.py`.
Its outputs are always `unscored`: structural checks and qualitative review are
reported separately. It cannot dispatch a builder or promote a candidate.

The modeler can read the explicitly named public PNGs, inspect its own model, and
invoke a fixed allowlist of existing RhinoMCP commands. Command schemas come from
`contracts/`; no arbitrary code execution, shell, model import or evaluator tools
are exposed. It can use curves, surfaces, extrusion, sweeps, lofts, primitive and
batch construction, booleans, transformations and attributes. The same gateway
can serve another object's benchmark without new object-specific operations.

Each call checks the dedicated Rhino process, document serial and run marker,
and counts against a call budget. The read-only planner gateway rejects modeling
commands in code as well as disabling them in client configuration. Input-image
basenames and hashes are checked; held-out images are not copied into the modeler
reference directory. These controls are application boundaries, not OS isolation.
The trusted evaluator still runs inside Rhino's process.

The runner saves the task, public reference copies, gateway events, session prompts,
agent events, installed binary identity, selected source snapshots/hashes, model,
structural measurements, five model screenshots and planner diagnosis. A failed or
timed-out modeler leaves a saved partial model for diagnosis; mutations are not
replayed. A completed run leaves the marked document and geometry intact for review.
Inspect the checkpoint and live ownership before clearing or starting another run.
If evaluation/review fails, retain that checkpoint and logs; there is no automatic
resume of an unfinished diagnostic run.

## Running another benchmark

1. Start from the repository runbook with the verified baseline plugin, exactly one
   dedicated empty unsaved document and `mcpstart`. Do not close unrelated work.
2. Create a task JSON using `visual_tasks/barcelona_chair.json` as the example.
   Define input names, coordinate/scale convention, named part prefixes, budget,
   scope and explicit reference limitations. These are trusted supervisor inputs.
3. Create a local reference directory containing only the public PNGs and
   `public.json` with `views: {name: {file: "basename.png", sha256: "…"}}`.
   Keep evaluation-only images in a separate directory. Preserve the source URL,
   capture date, authorship, hashes and camera/occlusion assumptions in a manifest.
4. Run from the repository root:

```sh
server/.venv/bin/python -m experiments.visual_runner \
  experiments/visual_tasks/barcelona_chair.json \
  /absolute/path/to/public-reference-directory
```

5. Read `evaluation.json`, `summary.json`, tool failures and the saved model.
   Review held-out images separately after the modeler is finished. Do not feed
   private evaluation details into a subsequent modeler and still call them held out.
6. Classify failures before repair: modeling choice, tool documentation/affordance,
   reproducible plugin defect, missing generic capability, or evaluator limitation.
   A geometric mismatch by itself does not establish a plugin bug. Use a focused
   reproduction, then the bounded builder and live trial controller when justified.

## What is measured

The independent saved-file audit checks nonempty output, units, validity, normalized
width, removal of construction curves and required naming groups. Names verify
organization only. It also records object types, bounds, solid flags and volumes.
These are useful diagnostics, not proof of chair proportions or part correctness.

Visual comparison is currently qualitative. Standard Rhino front/right/back/top
and perspective captures are not matched to the unknown Sketchfab cameras. There
is no silhouette threshold, automated visual score or calibrated acceptance gate.
The planner uses public reference views; the supervisor separately inspects the
reserved view. Camera matching, objective metrics, deliberate visual negatives,
repeatability and multiple held-out objects remain required before promotion.

## First reference pack

Local pack: `runs/chair-reference-20260906/`, captured from the user's Sketchfab
scene by ordinary browser orbit interaction. Four public screenshots: `front`,
`front-oblique`, `side`, `back-detail`. One separately reserved `rear-oblique` view.
View names are approximate perspectives. The ottoman stays visible but is excluded
from this first task. Rear detail/reserved views crop some feet. No source mesh
was extracted. Overall width 1000 mm is a normalization convention, not recovered
physical scale. Full image hashes and provenance are in the local manifest.

The initial baseline result is recorded in `CHAIR_BASELINE.md` after completion.
Local runs/images are ignored by Git and must be recreated or provided separately
on another machine. Checking out the branch restores behavior and task definitions,
not the local experiment evidence.
