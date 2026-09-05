# Generated-reference reconstruction loop

Verified in Rhino 8 on 2026-09-05 on the `harness` branch.

## Implemented input and information boundary

`tasks/reference_box.json` adds a generated-reference input mode to the existing
axis-aligned-box evaluator. Its public brief states the shape class (one solid
cuboid), axis alignment, origin, millimeter units, and a 10 mm dimension grid.
It does not state the target dimensions. This deliberately constrained first
image task has an objectively recoverable answer; it is not photo reconstruction.

The controller creates a hidden `.3dm` reference in memory, saves it separately,
and independently measures/evaluates that file before starting the modeler. It
renders three calibrated orthographic **drawings from the saved box bounds**, not
Rhino viewport screenshots. The mapping is explicit: image u = 100 + 5×horizontal
coordinate and v = 500 − 5×vertical coordinate, in pixels for millimeter world
coordinates. Top shows X/Y, Front X/Z and Right Y/Z. All images are 700×600 pixels;
grid lines and labels represent 10 mm. The schema restricts dimensions to multiples
of 10 mm between 10 and 80 mm so the drawings are readable and fit the canvas.

The narrow MCP gateway exposes `get_reference_image(top|front|right)` only for
reference tasks. It accepts no paths and returns only the selected PNG. The
hidden model, numeric expected dimensions, generator source and evaluator are not
exposed through gateway tools. The modeler's shell and unrelated tools remain
disabled. This is the existing tool boundary, not a new operating-system sandbox.

The controller saves image/model hashes and calibration metadata; the renderer
source is retained with the run. PNG hashes are checked before serving and again
before evaluation. The hidden model hash is also checked before acceptance.
The planner runs later in a separate session and sees the full evaluation/task.
`--feedback` is rejected for reference tasks because that planner output can reveal
the hidden answer. Redacted feedback remains future work.

## Live results

| Run | Input dimensions, hidden from modeler | Outcome |
| --- | --- | --- |
| `20260905-210251-4e4dc288` | X=70, Y=40, Z=30 mm | Retrieved all three images; built the correct single solid; evaluator passed; planner accepted |
| `20260905-210451-b56b2480` | X=40, Y=70, Z=30 mm | Retrieved reference images and reconstructed the swapped axes; evaluator passed; planner accepted |

Both candidates have volume 84,000 mm³. Re-evaluating the second candidate against
the first task **fails on dimensions while passing volume**. The control therefore
distinguishes shape extent/axis correspondence from a volume-only success.
The modeler prompts have the same public instruction text; the expected dimensions
were supplied only through different images. Tool logs record image retrieval and
BOX calls with the correct, different width/length values.

Candidate `.3dm` hashes:

- First: `06f071f9253a0eed7036841a40641a3b169e2863f8a79ac404b07cb2880222ec`.
- Swapped: `e199503d20210214990884ceadbaa2421f8791fd9413ce14cef7b98bf88a02c5`.

Full local evidence is under `runs/<run>/`: reference PNGs and `.3dm`, calibration,
source/hash records, modeler/planner events and prompts, and candidate evaluation.
The negative control is `runs/reference-swapped-negative-control.json`. Raw runs
are ignored by Git; the recipe and code are portable.

## Verification and limits

- 286 Python tests passed: 63 experiment tests and 223 server tests.
- New tests exercise hidden-answer feedback refusal, image-path/tamper rejection,
  schema limits, public prompt separation, and image-tool availability by task.
- All 26 existing live geometry fixtures returned the expected verdict twice
  (`evaluator-box-20260905-210630`, `evaluator-prism-20260905-210636`,
  `evaluator-hole-20260905-210644`). No geometric acceptance rule was relaxed.
- Experiment lint and format checks pass. Production plugin code/protocol did not
  change in this milestone; the previously verified capture assembly remains loaded.

Two successful cuboid examples do not establish general visual reconstruction.
The shape class, origin, axes and dimension quantization are supplied explicitly.
There are no occlusions, perspective distortions, hidden cavities or noisy pixels.
These images are a first objective input/evaluation test, not evidence of trained
model self-improvement or autonomous plugin-code repair.

To reproduce the control, copy `tasks/reference_box.json` to a local task file,
change its id and dimensions to `[40,70,30]`, and run it in a fresh empty Rhino
document using the same runner command. Do not put the changed dimensions into the
public instruction. The renderer and evaluator consume the private task fields.
