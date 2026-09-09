# First live loop — 2026-09-05

## Result

A fresh Codex modeler session used the restricted RhinoMCP gateway to create and
inspect an actual Rhino box. Independent evaluation of the saved `.3dm` passed
every mandatory check. A separate fresh planner session accepted the evidence.
No production plugin fix was necessary or claimed.

| Check | Measured result |
| --- | --- |
| Document units | Millimeters |
| Complete document object count | 1 |
| Valid geometry | True |
| Closed solid | True |
| World minimum corner | (0, 0, 0) mm |
| World XYZ dimensions | (100, 50, 30) mm |
| Volume | 150,000 mm³ |

The modeler initially created a centered box, read its returned bounding box,
translated it by (50, 25, 15), and inspected it. This was modeling-time correction
using tool feedback, not a change to model weights or the plugin implementation.

## Feedback and retry

The initial attempt produced no geometry because non-interactive client approval
configuration canceled its creation calls. The evaluator rejected the empty file;
the planner requested another modeling attempt and did not invent a plugin defect.
The supervising implementation session corrected the gateway's scoped approval
configuration. A new run consumed the first planner's feedback and succeeded.
This demonstrates evidence transfer across sessions, with an infrastructure fix
made by the supervising session. It does not demonstrate autonomous plugin repair.

## Local evidence

These generated files are intentionally ignored by Git:

- Failed attempt: `runs/20260905-184111-8b06e0e8/`
- Passing attempt: `runs/20260905-184415-34495492/`
- Evaluator fixtures: `runs/evaluator-20260905-184305/`

The passing directory contains the `.3dm`, screenshot, evaluation, planner output,
previous feedback, and separate modeler/planner event streams. Its artifact SHA-256
is `0026ee61462445e1b282d67d9164f99dec3da0c54eee02811b41fc3a5b70521f`.

Rhino reported the loaded plugin assembly from the local app installation, version
0.3.2.0 and module ID `edc9d197-af0b-4304-850b-1e3dec61b623`. The plugin was built
and installed before launching this dedicated Rhino session.

The independent live evaluator accepted a correct fixture and rejected wrong
scale, wrong position, extra geometry, an open surface, and wrong units. Every
fixture produced identical evaluation results on two consecutive measurements.

## Remaining work

Extend the suite beyond boxes and add the plugin-builder stage, verified candidate
reload, stronger isolation, and regression-based candidate selection. Rhino startup
was performed by the supervising desktop agent using the documented runbook;
the Python runner currently requires Rhino's listener to be running.
