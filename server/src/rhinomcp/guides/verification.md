# Verify geometry against the task

Use analyze_objects with one explicit target selector. Check validity, intended
surface/solid status, dimensions, world bounds and available topology measurements.
A closed solid alone does not establish correct geometry. Volume alone cannot prove
hole placement, and area alone cannot prove a surface's boundary or world position.

For solids, check closure and volume together with bounds and representative interior
or exterior points when available. For surfaces, check face/loop counts, boundaries,
area and sampled shape. Use measurements suitable for the particular geometry;
finite samples are evidence, not a guarantee between every sampled point.

Inspect the whole deliverable for extra construction geometry, including hidden or
locked objects. Do not confuse a filtered object list with the entire document.
Compare the actual count with the requested final count while preserving unrelated
user objects. Check layers and intended names separately from shape.

Use screenshots to inspect appearance and clearly label the view. Auto-fitted views
can hide a wrong translation or scale. Pictures do not replace numeric world-pose
checks, topology or a saved-file audit. Preserve the user's camera and display setup
when changing views for inspection.

For deliverables, verify the saved model when practical rather than accepting only
the live viewport. Report passing checks, failures and unmeasured requirements
separately. Do not claim a tool improvement from one successful model or claim broad
reliability from a small collection of examples.

## Construct for accuracy before increasing sample count

For an analytic target, choose a representation that can reproduce its degree and
boundary exactly when possible. More interpolation points or a denser loft do not
by themselves bound error. `create_object(type="SURFACE")` takes interpolation
points, not control vertices. A generic cubic loft through accurate section points
can still miss the intended shape between them.

A tested special case is the rectangular biquadratic panel
`z = 16*h*(x/w)*(1-x/w)*(y/d)*(1-y/d)` on `0<=x<=w, 0<=y<=d`.
Use SURFACE with `count=[3,3]`, `degree=[2,2]`, `closed=[false,false]`.
List points with x as the outer index and y as the inner index:
`(0,0,0), (0,d/2,0), (0,d,0), (w/2,0,0), (w/2,d/2,h),
(w/2,d,0), (w,0,0), (w,d/2,0), (w,d,0)`.
Apply the requested rigid world transform to each point before creation if that
avoids pivot ambiguity. Retain sufficient coordinate precision relative to the
requested tolerance. This symmetric degree-two grid reproduced three raised and
depressed panel cases within numerical roundoff in saved-file sampled checks.
This recipe is specific to this polynomial family, not arbitrary curved surfaces.

Check both the boundary and interior against the target, in both directions when
possible. A bounding box and valid-face result alone cannot certify shape accuracy.
For approximation, measure deviation, refine the representation, and repeat. If
available tools cannot measure the required error, report it as unverified; never
claim compliance solely from topology, screenshots, or a successful tool response.
Finite samples do not certify the maximum error everywhere between samples. A
continuous guarantee requires suitable analytic bounds or a certified comparison.
