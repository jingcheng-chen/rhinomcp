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


def through_hole_checks(task, obj):
    tolerance = task["linear_tolerance"]
    minimum = task["minimum"]
    maximum = [a + b for a, b in zip(minimum, task["dimensions"])]
    faces = obj.get("faces", [])
    planes = [f for f in faces if f.get("kind") == "plane"]
    cylinders = [f for f in faces if f.get("kind") == "cylinder"]
    boundaries = set()
    planes_on_boundary = bool(planes)
    for face in planes:
        normal, origin = face.get("normal", []), face.get("origin", [])
        match = None
        if len(normal) == len(origin) == 3:
            for axis in range(3):
                if near(abs(normal[axis]), 1, 1e-7) and all(
                    near(normal[i], 0, 1e-7) for i in range(3) if i != axis
                ):
                    for side, corner in enumerate((minimum, maximum)):
                        if near(origin[axis], corner[axis], tolerance):
                            match = (axis, side)
        if match is None:
            planes_on_boundary = False
        else:
            boundaries.add(match)
    intervals = [f.get("z_range", []) for f in cylinders]
    spans_height = bool(intervals) and all(
        len(v) == 2
        and all(near(n, n, 0) for n in v)
        and minimum[2] - tolerance <= v[0] <= v[1] <= maximum[2] + tolerance
        for v in intervals
    )
    if spans_height:
        reached = minimum[2]
        for start, end in sorted(intervals):
            if start > reached + tolerance:
                spans_height = False
                break
            reached = max(reached, end)
        spans_height = spans_height and near(reached, maximum[2], tolerance)
    width, depth, height = task["dimensions"]
    radius = task["hole_radius"]
    return {
        "supported_faces": bool(faces) and len(planes) + len(cylinders) == len(faces),
        "outer_boundary_planes": planes_on_boundary and len(boundaries) == 6,
        "hole_axis": bool(cylinders)
        and all(
            len(f.get("center", [])) == 3
            and len(f.get("axis", [])) == 3
            and all(
                near(f["center"][i], task["hole_center"][i], tolerance) for i in (0, 1)
            )
            and near(f["axis"][0], 0, 1e-7)
            and near(f["axis"][1], 0, 1e-7)
            and near(abs(f["axis"][2]), 1, 1e-7)
            for f in cylinders
        ),
        "hole_radius": bool(cylinders)
        and all(near(f.get("radius"), radius, tolerance) for f in cylinders),
        "hole_full_height": spans_height,
        "hole_axis_clear": bool(cylinders)
        and all(
            f.get("axis_probe_ok") is True
            and f.get("axis_hits") == 0
            and f.get("axis_overlaps") == 0
            for f in cylinders
        ),
        "area": near(
            obj.get("area"),
            2 * (width * depth + width * height + depth * height)
            - 2 * math.pi * radius**2
            + 2 * math.pi * radius * height,
            task["area_tolerance"],
        ),
    }


def evaluate(task, measurements):
    if task["type"] == "workflow_scene":
        from experiments.scene_task import evaluate as evaluate_scene

        return evaluate_scene(task, measurements)
    if task["type"] == "trimmed_planar_patch":
        from experiments.trimmed_task import evaluate as evaluate_trimmed

        return evaluate_trimmed(task, measurements)

    if task["type"] == "biquadratic_panel":
        from experiments.panel_task import evaluate as evaluate_panel

        return evaluate_panel(task, measurements)

    if task["type"] == "quarter_annular_strip":
        from experiments.strip_task import evaluate as evaluate_strip

        return evaluate_strip(task, measurements)
    kind = task["type"]
    if kind not in ("axis_aligned_box", "triangular_prism_pose", "box_through_hole"):
        raise ValueError(f"Unsupported evaluation task type: {kind}")
    objects = measurements.get("objects", [])
    checks = {
        "units": measurements.get("units") == task["units"],
        "object_count": len(objects) == 1,
    }
    if len(objects) == 1:
        obj = objects[0]
        checks.update(valid=obj.get("valid") is True, solid=obj.get("solid") is True)
        if kind in ("axis_aligned_box", "box_through_hole"):
            for key in ("minimum", "dimensions"):
                values = obj.get(key, [])
                checks[key] = len(values) == 3 and all(
                    near(actual, expected, task["linear_tolerance"])
                    for actual, expected in zip(values, task[key])
                )
        if kind == "triangular_prism_pose":
            checks.update(prism_pose_checks(task, obj))
        elif kind == "box_through_hole":
            checks.update(through_hole_checks(task, obj))
        volume = obj.get("volume")
        expected_volume = math.prod(task["dimensions"]) * (
            0.5 if kind == "triangular_prism_pose" else 1
        )
        if kind == "box_through_hole":
            expected_volume -= (
                math.pi * task["hole_radius"] ** 2 * task["dimensions"][2]
            )
        checks["volume"] = near(volume, expected_volume, task["volume_tolerance"])
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "measurements": measurements,
    }
