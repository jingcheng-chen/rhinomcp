# Planar faces with openings

Use create_planar_region to create one open planar Brep face from an outer closed
curve and optional inner closed curves. An inner loop is a real surface opening;
a circle drawn on an intact face is not a hole.

All loops must be coplanar and valid. Inner loops must lie strictly inside the outer
loop and be mutually disjoint and nonnested. Do not pass duplicate IDs, intersecting
or touching loops, open curves, or curves on offset planes. Use the document's
appropriate tolerance; do not increase tolerance just to hide a geometry error.

The command preserves its input curves. Keep their IDs, verify the returned face and
loop counts, then delete only the construction curves belonging to this task if the
requested deliverable excludes them. Creating a planar face does not make a solid.

Check the outer boundary, hole locations and radii, trimmed area, and the final world
pose. A correct area or loop count can coexist with a wrongly positioned patch.
For a tilted or translated result, follow the transforms guide and check points in
the intended coordinate frame.
