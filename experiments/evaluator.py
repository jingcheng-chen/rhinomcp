"""Analytic acceptance checks; no agent-written scores are trusted."""

import math


def near(actual, expected, tolerance):
    return (
        isinstance(actual, (int, float))
        and not isinstance(actual, bool)
        and math.isfinite(actual)
        and abs(actual - expected) <= tolerance
    )


def prism_pose_checks(task, obj):
    """Validate a scalene triangular prism in its prescribed local frame.

    Extra vertices from equivalent split planar faces are allowed. All six true
    corners must exist, all vertices must be inside the reference convex prism,
    faces/edges must be planar/straight, and area and volume must agree.
    """
    width, depth, height = task["dimensions"]
    tolerance = task["linear_tolerance"]
    angle = math.radians(task["rotation_z_degrees"])
    cosine, sine = math.cos(angle), math.sin(angle)
    vertices = obj.get("vertices", [])
    complete = bool(vertices) and all(
        isinstance(v, list)
        and len(v) == 3
        and all(
            isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)
            for n in v
        )
        for v in vertices
    )
    local = []
    if complete:
        for point in vertices:
            x, y, z = [a - b for a, b in zip(point, task["translation"])]
            local.append((cosine * x + sine * y, -sine * x + cosine * y, z))
    expected = [
        (x, y, z) for z in (0, height) for x, y in ((0, 0), (width, 0), (0, depth))
    ]
    # Convert linear tolerance to a distance tolerance on the sloping plane.
    diagonal_tolerance = tolerance * math.hypot(1 / width, 1 / depth)
    return {
        "pose_corners": complete
        and all(
            any(math.dist(corner, vertex) <= tolerance for vertex in local)
            for corner in expected
        ),
        "vertices_inside": complete
        and all(
            x >= -tolerance
            and y >= -tolerance
            and -tolerance <= z <= height + tolerance
            and x / width + y / depth <= 1 + diagonal_tolerance
            for x, y, z in local
        ),
        "planar_faces": obj.get("planar_faces") is True,
        "straight_edges": obj.get("straight_edges") is True,
        "area": near(
            obj.get("area"),
            width * depth + height * (width + depth + math.hypot(width, depth)),
            task["area_tolerance"],
        ),
    }


def evaluate(task, measurements):
    kind = task["type"]
    if kind not in ("axis_aligned_box", "triangular_prism_pose"):
        raise ValueError(f"Unsupported evaluation task type: {kind}")
    objects = measurements.get("objects", [])
    checks = {
        "units": measurements.get("units") == task["units"],
        "object_count": len(objects) == 1,
    }
    if len(objects) == 1:
        obj = objects[0]
        checks.update(valid=obj.get("valid") is True, solid=obj.get("solid") is True)
        if kind == "axis_aligned_box":
            for key in ("minimum", "dimensions"):
                values = obj.get(key, [])
                checks[key] = len(values) == 3 and all(
                    near(actual, expected, task["linear_tolerance"])
                    for actual, expected in zip(values, task[key])
                )
        else:
            checks.update(prism_pose_checks(task, obj))
        volume = obj.get("volume")
        expected_volume = math.prod(task["dimensions"]) * (
            0.5 if kind == "triangular_prism_pose" else 1
        )
        checks["volume"] = near(volume, expected_volume, task["volume_tolerance"])
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "measurements": measurements,
    }
