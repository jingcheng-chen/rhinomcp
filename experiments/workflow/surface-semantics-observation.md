# Surface input semantics observed during the binary comparison

Two candidate failures in `workflow-binary-20260908-181813-4eec688b` provide a
separate interface hypothesis. The raised input uses a local center height of 80 mm
for a requested 20 mm panel; the depressed input uses -60 mm for a requested -15 mm
panel. Saved-file evaluation measures those four-times-too-large heights. Both
agents treated interpolation inputs as Bezier control points.

The production description says only that points "define the surface". The C#
handler calls `NurbsSurface.CreateThroughPoints`. A general wording improvement
could clarify that the surface interpolates the supplied grid samples and that
these are not NURBS control vertices. This would explain the existing API without
supplying a task-specific construction recipe or changing geometry behavior.

This is a discovery hypothesis, not an adopted description or proof that wording
will resolve the failures. Do not change the ongoing binary trial or relabel those
failures as successes. Any description comparison requires its own frozen contract,
fresh sessions, unchanged evaluator and held-out validation. Keep the bounds repair
and description intervention separate.
