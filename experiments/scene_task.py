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
            if not all(
                math.isfinite(a) and math.isfinite(b) and b > a
                for a, b in zip(p["min"], p["max"])
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
        "limitation": "Analytic eight-corner box assemblies only. Identity/CRC checks compare saved states; mutating-tool attempts are audited separately for inspection. Supervised local execution, not adversarial isolation.",
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
