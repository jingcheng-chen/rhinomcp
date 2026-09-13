"""Shared prepared-scene task adapter and independent saved-file box/identity judge."""

import json
import math

import jsonschema
from experiments.bridge import script, assert_document
from experiments.evaluator import near


def validate(task):
    from experiments.runner import ROOT

    jsonschema.validate(
        task,
        json.loads((ROOT / "experiments/tasks/workflow_scene.schema.json").read_text()),
    )
    for key in ("initial", "targets"):
        parts = task[key]
        if len({p["name"] for p in parts}) != len(parts):
            raise ValueError("Scene object names must be unique")
        for p in parts:
            if p.get("shape") in {"polyline", "point"}:
                points = p.get("points", [])
                if not points or not all(math.isfinite(v) for pt in points for v in pt):
                    raise ValueError("Finite explicit points required")
                if p["shape"] == "point" and len(points) != 1:
                    raise ValueError("Point shape needs one point")
                if p["shape"] == "polyline" and (
                    len(points) < 2
                    or any(math.dist(a, b) == 0 for a, b in zip(points, points[1:]))
                ):
                    raise ValueError("Polyline needs nonzero segments")
                if p["min"] != [min(pt[i] for pt in points) for i in range(3)] or p[
                    "max"
                ] != [max(pt[i] for pt in points) for i in range(3)]:
                    raise ValueError("Explicit point bounds disagree")
                if p["layer"] not in task["layers"]:
                    raise ValueError("Every object needs a declared layer")
                continue
            if "points" in p:
                raise ValueError("Explicit points require a point or polyline shape")
            curve = p.get("shape") in {"rectangle_curve", "rectangle_surface"}
            if not all(
                math.isfinite(a) and math.isfinite(b) and b > a
                for a, b in zip(
                    p["min"][: 2 if curve else 3], p["max"][: 2 if curve else 3]
                )
            ) or (
                curve and (not math.isfinite(p["min"][2]) or p["min"][2] != p["max"][2])
            ):
                raise ValueError("Scene bounds must be finite and positive")
            if not math.isfinite(math.prod(b - a for a, b in zip(p["min"], p["max"]))):
                raise ValueError("Scene volume must be finite")
            if p["layer"] not in task["layers"]:
                raise ValueError("Every object needs a declared layer")
    for name in task["layers"]:
        if "::" in name and name.rsplit("::", 1)[0] not in task["layers"]:
            raise ValueError("Declare all layer ancestors")
    initials = {p["name"] for p in task["initial"]}
    for p in task["targets"]:
        if p.get("preserve_from") and p["preserve_from"] not in initials:
            raise ValueError("Unknown identity to preserve")
        if p.get("unchanged") and not p.get("preserve_from"):
            raise ValueError("Unchanged object needs initial identity")
    if not set(task["inspection_names"]) <= initials:
        raise ValueError("Unknown inspection object")
    if task["family"] == "document-inspection" and not task["inspection_names"]:
        raise ValueError("Inspection task needs measurement targets")
    for k in ("linear_tolerance", "relative_volume_tolerance"):
        if not math.isfinite(task[k]):
            raise ValueError("Finite tolerance required")
    if "relative_length_tolerance" in task and not math.isfinite(
        task["relative_length_tolerance"]
    ):
        raise ValueError("Finite length tolerance required")
    return task


def layer_paths(layers):
    byid = {layer["id"]: layer for layer in layers}
    if len(byid) != len(layers):
        raise ValueError("Duplicate layer identity")

    def path(layer, seen=()):
        if layer["id"] in seen:
            raise ValueError("Cyclic layer tree")
        if layer["parent"] == "00000000-0000-0000-0000-000000000000":
            return layer["name"]
        return path(byid[layer["parent"]], (*seen, layer["id"])) + "::" + layer["name"]

    return {layer["index"]: path(layer) for layer in layers}


def measure(path, task=None):
    from experiments.runner import ROOT, sha256

    before = sha256(path)
    result = json.loads(
        script(
            (ROOT / "experiments/scene_measure.cs")
            .read_text()
            .replace("ARTIFACT_PATH", json.dumps(str(path)))
        )
    )
    if sha256(path) != before:
        raise RuntimeError("Scene artifact changed during measurement")
    return result


def same_edges(actual, expected, tolerance):
    """One-to-one undirected segment matching; duplicates and bridges fail."""
    if len(actual) != len(expected) or len(actual) < 2:
        return False
    if any(len(p) != 3 for p in actual):
        return False
    remaining = list(zip(expected, expected[1:]))

    def close(a, b):
        return near(math.dist(a, b), 0, tolerance)

    for a, b in zip(actual, actual[1:]):
        matches = [
            i
            for i, (c, d) in enumerate(remaining)
            if (close(a, c) and close(b, d)) or (close(a, d) and close(b, c))
        ]
        if len(matches) != 1:
            return False
        remaining.pop(matches[0])
    return not remaining


def evaluate(task, measured):
    initial = measured.get("initial", {})
    rows = measured.get("objects", [])
    objects = {o.get("name"): o for o in rows}
    original = {o.get("name"): o for o in initial.get("objects", [])}
    checks = {
        "millimeters": measured.get("units") == "Millimeters",
        "exact_objects": len(objects) == len(rows) == len(task["targets"])
        and set(objects) == {p["name"] for p in task["targets"]},
    }
    try:
        paths = layer_paths(measured["layers"])
        original_paths = layer_paths(initial["layers"])
        checks["exact_layers"] = set(paths.values()) == set(
            original_paths.values()
        ) | set(task["layers"])
        after_layers = {layer["id"]: layer for layer in measured["layers"]}
        checks["original_layers_unchanged"] = all(
            after_layers.get(layer["id"]) == layer for layer in initial["layers"]
        )
    except (KeyError, ValueError):
        paths = {}
        checks["exact_layers"] = False
        checks["original_layers_unchanged"] = False
    tol = task["linear_tolerance"]
    for target in task["targets"]:
        name = target["name"]
        o = objects.get(name, {})
        volume = math.prod(b - a for a, b in zip(target["min"], target["max"]))
        corners = [
            [x, y, z]
            for x in (target["min"][0], target["max"][0])
            for y in (target["min"][1], target["max"][1])
            for z in (target["min"][2], target["max"][2])
        ]
        vertices = o.get("vertices") or []
        checks[name + "/solid_box"] = (
            o.get("valid") is True
            and o.get("solid") is True
            and o.get("planar_faces") is True
            and len(vertices) == 8
            and all(
                any(
                    len(v) == 3 and all(near(a, b, tol) for a, b in zip(v, c))
                    for v in vertices
                )
                for c in corners
            )
        )
        for bound in ("min", "max"):
            checks[name + "/" + bound] = len(o.get(bound, [])) == 3 and all(
                near(a, b, tol) for a, b in zip(o.get(bound, []), target[bound])
            )
        checks[name + "/volume"] = near(
            o.get("volume"), volume, volume * task["relative_volume_tolerance"]
        )
        if target.get("shape") == "rectangle_surface":
            del checks[name + "/solid_box"], checks[name + "/volume"]
            checks[name + "/planar_rectangle"] = (
                o.get("valid") is True
                and o.get("face_count") == 1
                and o.get("planar_faces") is True
                and len(vertices) == 4
                and all(
                    any(
                        len(v) == 3 and all(near(a, b, tol) for a, b in zip(v, c))
                        for v in vertices
                    )
                    for c in corners[::2]
                )
            )
            area = (target["max"][0] - target["min"][0]) * (
                target["max"][1] - target["min"][1]
            )
            checks[name + "/surface_area"] = near(
                o.get("surface_area"), area, area * task["relative_volume_tolerance"]
            )
        if target.get("shape") == "rectangle_curve":
            del checks[name + "/solid_box"], checks[name + "/volume"]
            points = o.get("polyline") or []
            expected = [c for c in corners[::2]]
            checks[name + "/rectangle_curve"] = (
                o.get("valid") is True
                and o.get("curve_closed") is True
                and o.get("curve_planar") is True
                and len(points) == 5
                and all(near(a, b, tol) for a, b in zip(points[0], points[-1]))
                and all(
                    any(all(near(a, b, tol) for a, b in zip(c, p)) for p in points[:-1])
                    for c in expected
                )
            )
            width, height = [target["max"][i] - target["min"][i] for i in (0, 1)]
            checks[name + "/curve_length"] = near(
                o.get("curve_length"),
                2 * (width + height),
                2 * (width + height) * task["relative_volume_tolerance"],
            )
            checks[name + "/curve_area"] = near(
                o.get("curve_area"),
                width * height,
                width * height * task["relative_volume_tolerance"],
            )
        if target.get("shape") in {"polyline", "point"}:
            del checks[name + "/solid_box"], checks[name + "/volume"]
            expected = target["points"]
            if target["shape"] == "point":
                checks[name + "/point"] = (
                    o.get("valid") is True and o.get("is_point") is True
                )
            else:
                checks[name + "/edges"] = o.get("valid") is True and same_edges(
                    o.get("polyline") or [], expected, tol
                )
                checks[name + "/closure"] = o.get("curve_closed") is (
                    expected[0] == expected[-1]
                )
                length = sum(math.dist(a, b) for a, b in zip(expected, expected[1:]))
                checks[name + "/curve_length"] = near(
                    o.get("curve_length"),
                    length,
                    length
                    * task.get(
                        "relative_length_tolerance", task["relative_volume_tolerance"]
                    ),
                )
        checks[name + "/attributes"] = (
            paths.get(o.get("layer")) == target["layer"]
            and o.get("visible") is True
            and o.get("mode") == "Normal"
        )
        if target.get("preserve_from"):
            old = original.get(target["preserve_from"], {})
            checks[name + "/identity"] = (
                bool(old.get("id")) and o.get("id") == old["id"]
            )
            if target.get("unchanged"):
                checks[name + "/unchanged"] = bool(old) and all(
                    o.get(k) == old.get(k) for k in ("id", "geometry_crc", "attributes")
                )
    if task["family"] == "recovery":
        removed = {
            o["id"]
            for name, o in original.items()
            if name not in {p.get("preserve_from") for p in task["targets"]}
        }
        checks["wrong_intermediate_removed"] = not removed & {o.get("id") for o in rows}
    if task["family"] == "document-inspection":
        submitted = measured.get("inspection", [])
        reports = {r.get("name"): r for r in submitted}
        checks["inspection_names"] = len(reports) == len(submitted) == len(
            task["inspection_names"]
        ) and set(reports) == set(task["inspection_names"])
        checks["inspection_no_write_calls"] = (
            measured.get("inspection_no_write_calls") is True
        )
        for name in task["inspection_names"]:
            observed = objects.get(name, {})
            r = reports.get(name, {})
            v = observed.get("volume")
            checks[name + "/reported_volume"] = (
                near(r.get("volume"), v, abs(v) * task["relative_volume_tolerance"])
                if isinstance(v, (int, float))
                else False
            )
            for b in ("min", "max"):
                checks[name + "/reported_" + b] = (
                    len(r.get(b, [])) == 3
                    and all(
                        near(a, c, tol)
                        for a, c in zip(r.get(b, []), observed.get(b, []))
                    )
                    and len(observed.get(b, [])) == 3
                )
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "measurements": measured,
        "limitation": "Analytic boxes, horizontal rectangular faces, rectangular curves, explicit polyline edge sets and points. Identity/CRC checks compare saved states; mutating-tool attempts are audited separately for inspection. Supervised local execution, not adversarial isolation.",
    }


def creation_code(parts, destination="doc", preserved_ids=None):
    """Controller fixture construction, never exposed as an agent recipe."""
    code = ["var layerIds=new System.Collections.Generic.Dictionary<string,int>();"]
    all_layers = set()
    for p in parts:
        bits = p["layer"].split("::")
        all_layers.update("::".join(bits[:i]) for i in range(1, len(bits) + 1))
    for name in sorted(all_layers, key=lambda s: (s.count("::"), s)):
        parent = name.rsplit("::", 1)[0] if "::" in name else None
        # Dedicated fixtures only: newly required layers must not collide.
        code.append(
            "{var l=new Rhino.DocObjects.Layer {Name="
            + json.dumps(name.split("::")[-1])
            + "};"
        )
        if parent:
            code.append(
                f"l.ParentLayerId={destination}.Layers[layerIds[{json.dumps(parent)}]].Id;"
            )
        code.append(
            f"var existing={destination}.Layers.FirstOrDefault(x=>x.Name==l.Name && x.ParentLayerId==l.ParentLayerId);if(existing==null){{{destination}.Layers.Add(l);existing={destination}.Layers.First(x=>x.Name==l.Name && x.ParentLayerId==l.ParentLayerId);}}layerIds[{json.dumps(name)}]=existing.Index;}}"
        )
    for p in parts:
        a, b = p["min"], p["max"]
        code.append(
            "{var attr=new Rhino.DocObjects.ObjectAttributes {Name="
            + json.dumps(p["name"])
            + ",LayerIndex=layerIds["
            + json.dumps(p["layer"])
            + "]};"
        )
        if preserved_ids and p.get("preserve_from") in preserved_ids:
            code.append(
                "attr.ObjectId=new Guid("
                + json.dumps(preserved_ids[p["preserve_from"]])
                + ");"
            )
        if p.get("shape") in {"polyline", "point"}:
            literal = ",".join(f"new Point3d({x},{y},{z})" for x, y, z in p["points"])
            if p["shape"] == "point":
                code.append(f"{destination}.Objects.AddPoint({literal},attr);}}")
            else:
                code.append(
                    f"{destination}.Objects.AddCurve(new PolylineCurve(new []{{{literal}}}),attr);}}"
                )
        elif p.get("shape") == "rectangle_surface":
            code.append(
                f"var surface=new PlaneSurface(new Plane(new Point3d(0,0,{a[2]}),Vector3d.ZAxis),new Interval({a[0]},{b[0]}),new Interval({a[1]},{b[1]}));{destination}.Objects.AddBrep(surface.ToBrep(),attr);}}"
            )
        elif p.get("shape") == "rectangle_curve":
            points = [
                (a[0], a[1], a[2]),
                (b[0], a[1], a[2]),
                (b[0], b[1], a[2]),
                (a[0], b[1], a[2]),
                (a[0], a[1], a[2]),
            ]
            literal = ",".join(f"new Point3d({x},{y},{z})" for x, y, z in points)
            code.append(
                f"{destination}.Objects.AddCurve(new PolylineCurve(new []{{{literal}}}),attr);}}"
            )
        else:
            code.append(
                f"var box=new Box(Plane.WorldXY,new Interval({a[0]},{b[0]}),new Interval({a[1]},{b[1]}),new Interval({a[2]},{b[2]}));"
            )
            code.append(f"{destination}.Objects.AddBrep(box.ToBrep(),attr);}}")
    return "\n".join(code)


def seed(task, directory, owner, marker):
    from experiments.runner import save_candidate, save

    assert_document(owner["document"], marker)
    if task["initial"]:
        script(creation_code(task["initial"]))
    path = directory / "initial.3dm"
    digest = save_candidate(path, owner["document"], marker)
    measured = measure(path)
    save(directory / "initial.json", {"sha256": digest, "measurements": measured})
    return measured


def evaluation_context(directory, measured, definitions):
    from experiments.runner import sha256

    record = json.loads((directory / "initial.json").read_text())
    artifact = json.loads((directory / "artifact.json").read_text())
    if sha256(directory / "initial.json") != artifact.get("initial_metadata_sha256"):
        raise RuntimeError("Starting measurement metadata changed")
    if sha256(directory / "initial.3dm") != record["sha256"]:
        raise RuntimeError("Starting artifact changed")
    measured["initial"] = record["measurements"]
    result = json.loads((directory / "modeler/result.json").read_text())
    measured["inspection"] = result.get("inspection", [])
    read_only = {
        d["name"]
        for d in definitions
        if d.get("annotations", {}).get("readOnlyHint") is True
    }
    calls = [
        json.loads(line)
        for line in (directory / "calls.jsonl").read_text().splitlines()
    ]
    measured["inspection_no_write_calls"] = all(c["tool"] in read_only for c in calls)
    return measured


def response_schema():
    from experiments.runner import schema

    vector = {
        "type": "array",
        "items": {"type": "number"},
        "minItems": 3,
        "maxItems": 3,
    }
    return schema(
        {
            "summary": {"type": "string"},
            "complete": {"type": "boolean"},
            "inspection": {
                "type": "array",
                "items": schema(
                    {
                        "name": {"type": "string"},
                        "volume": {"type": "number"},
                        "min": vector,
                        "max": vector,
                    }
                ),
            },
        }
    )
