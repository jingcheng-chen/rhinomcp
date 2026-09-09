# Anchors, pivots and world transforms

Coordinates and translations use the document's length units. Rotation arguments
for modify_object are radians. Confirm units and use the particular tool's schema;
creation and modification do not necessarily share an anchor convention.

create_object boxes are centered at their location; cylinders are based at their
location. For a box with a required minimum corner, offset the center by half its
dimensions. Verify resulting world extents instead of inferring placement from a
successful creation response.

modify_object rotates around the center of the object's pre-edit world-axis-aligned
bounding box. It does not rotate around the world origin. Scale is anchored at the
pre-edit bounding-box minimum. A combined edit composes T * Rx * Ry * Rz * S: scale
acts first, then Z, Y and X rotations, then translation. Anchors are computed from
the geometry before this call; separate calls can therefore use different anchors.

For a rotation-only edit followed by a desired world translation t, let c be the
pre-rotation bounding-box center and R the desired rotation matrix. To obtain the
world-origin transform R*p + t through modify_object's center rotation, use the
translation vector t + R*c - c. This formula does not cover a combined scale.
Alternatively, construct coordinates directly in the desired world frame when the
creation tool supports them. Do not apply both strategies to the same geometry.

Check a known point, orientation and world position after transforming. Matching
size, area or volume alone cannot detect the wrong pivot. When feedback and visible
geometry disagree, investigate with independent measurements rather than moving or
flattening otherwise valid geometry to match a suspect response.
