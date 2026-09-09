# Precision comes from representation and measurement

The earlier 7×7 curve/loft workflow missed a 0.05 mm shape tolerance by about
0.44 mm, despite accurate supplied sample points. Increasing sample count alone
does not control interpolation error between samples.

A deterministic test now uses the existing SURFACE tool with a 3×3 interpolation
grid and degree [2,2]. For the symmetric biquadratic family
z=16*h*(x/w)*(1-x/w)*(y/d)*(1-y/d), the nine grid points have zero height except
the center at h. It reproduces the polynomial representation without the earlier
multi-curve loft approximation. Points are transformed rigidly into world coordinates.
No new modeling command or geometry capability was added.

`experiments/panel_precision_probe.py` constructs three saved models through the
existing production command, evaluates them, captures them, and restores the test
document. Raised, depressed, and the previously failed shallow panel all pass.
Maximum sampled errors are below 7e-14 mm. See panel-precision-results.json and
runs/panel-precision-20260909. These are deterministic feasibility checks, not
proof that fresh agents choose the method or a continuous certified error bound.

Guidance version 2 adds this scoped recipe to the existing verification topic.
The SURFACE description identifies interpolation points rather than control vertices
and links to that guide. Clean wheel and sdist package all six topics; real stdio
checks pass outside the repository without Rhino. Builds are local/unpublished.

For general tasks: prefer exact analytic/NURBS constructions when representable;
otherwise measure geometric deviation, refine and repeat. Separate construction
error, coordinate rounding, numerical measurement accuracy and acceptance tolerance.
A valid face or matching box does not certify shape. If the available tools cannot
measure a requirement, the agent must identify it as unverified. Generic numeric
comparison and refinement remain a product gap; finite samples can miss local error.

The new reserved case is in precision-guidance-suite.json. Its fresh-agent result
is recorded separately in precision-agent-results.json; do not infer that result
from the deterministic success above.

Fresh-agent outcome: the new case timed out after 180 seconds and two successful
guidance calls (overview and transforms), before creating geometry. It did not read
the verification recipe. No geometric score is assigned. The empty partial artifact,
source hashes, provider trace and preservation record are retained. The reason for
the long pause is not established. Discovery/prompt ergonomics and repeated bounded
sessions remain open; do not present the recipe as agent-validated transfer yet.
