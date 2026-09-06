"""Calibrated saved-file layer diagnosis; no plugin repair or modeler shortcut."""

import json
import math
import time
import uuid

from experiments.bridge import script, assert_document
from experiments.rhino_trial import runtime, require_owned
from experiments.strip_probe import fingerprint
from experiments.runner import ROOT, save, sha256, run_session, PLANNER_SCHEMA
from experiments.trial import locked
from rhinomcp.server import get_rhino_connection

ZERO = "00000000-0000-0000-0000-000000000000"
EXPECTED = {
    "Assembly",
    "Assembly::Left",
    "Assembly::Right",
    "Assembly::Left::Part",
    "Assembly::Right::Part",
}


def evaluate(measured, root="Assembly"):
    layers = measured["layers"]
    by_id = {layer["id"]: layer for layer in layers}
    by_index = {layer["index"]: layer for layer in layers}

    def path(layer, seen=()):
        if layer["id"] in seen:
            raise ValueError("Cyclic layer tree")
        if layer["parent"] == ZERO:
            return layer["name"]
        return path(by_id[layer["parent"]], (*seen, layer["id"])) + "::" + layer["name"]

    checks = {"millimeters": measured["units"] == "Millimeters"}
    try:
        paths = {layer["index"]: path(layer) for layer in layers}
        checks["valid_tree"] = (
            len(by_id) == len(layers) == len(by_index) == len(set(paths.values()))
        )
        expected = {p.replace("Assembly", root, 1) for p in EXPECTED}
        checks["exact_tree"] = set(paths.values()) - {"Default"} == expected
        checks["visible_unlocked_layers"] = all(
            layer["visible"] and not layer["locked"]
            for layer in layers
            if paths[layer["index"]] in expected
        )
    except (KeyError, ValueError):
        paths = {}
        checks.update(valid_tree=False, exact_tree=False, visible_unlocked_layers=False)
    objects = measured["objects"]
    checks["exact_parts"] = len(objects) == 2 and {o["name"] for o in objects} == {
        "left_part",
        "right_part",
    }
    for i, (name, side) in enumerate((("left_part", "Left"), ("right_part", "Right"))):
        matches = [o for o in objects if o["name"] == name]
        obj = matches[0] if len(matches) == 1 else {}
        checks[name + "/layer"] = (
            paths.get(obj.get("layer")) == root + "::" + side + "::Part"
        )
        checks[name + "/visible_solid"] = (
            obj.get("visible") is True
            and obj.get("mode") == "Normal"
            and obj.get("valid") is True
            and obj.get("solid") is True
        )
        bounds = obj.get("min", []) + obj.get("max", [])
        target = [i * 30, 0, 0, i * 30 + 10, 10, 10]
        checks[name + "/bounds"] = len(bounds) == 6 and all(
            isinstance(a, (int, float)) and math.isfinite(a) and abs(a - b) <= 0.01
            for a, b in zip(bounds, target)
        )
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "measurements": measured,
    }


def measure(path):
    before = sha256(path)
    result = json.loads(
        script(
            (ROOT / "experiments/layer_measure.cs")
            .read_text()
            .replace("ARTIFACT_PATH", json.dumps(str(path)))
        )
    )
    if sha256(path) != before:
        raise RuntimeError("Layer artifact changed during reading")
    return result


def run():
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        if owner["object_count"] or owner["marker"]:
            raise RuntimeError(
                "Layer probe requires the verified empty dedicated document"
            )
        before = fingerprint()
        directory = (
            ROOT
            / "experiments/runs"
            / (time.strftime("layers-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
        )
        directory.mkdir()
        print(directory, flush=True)
        save(directory / "environment.json", owner)
        save(directory / "before.json", before)
        sources = [
            "experiments/layer_probe.py",
            "experiments/layer_measure.cs",
            "experiments/layer_controls.cs",
            "plugin/Functions/CreateLayer.cs",
            "plugin/Functions/ObjectAttributes.cs",
            "contracts/commands/create_layer.json",
        ]
        pins = {name: sha256(ROOT / name) for name in sources}
        save(directory / "inputs.json", pins)
        for name in sources:
            dest = directory / "source" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((ROOT / name).read_bytes())
        script(
            (ROOT / "experiments/layer_controls.cs")
            .read_text()
            .replace("OUTPUT_DIRECTORY", json.dumps(str(directory)))
        )
        reports = {}
        for path in sorted(directory.glob("*.3dm")):
            first, second = measure(path), measure(path)
            report = evaluate(first)
            report.update(
                repeat_identical=first == second, artifact_sha256=sha256(path)
            )
            reports[path.stem] = report
        save(directory / "calibration.json", reports)
        if len(reports) != 9 or not all(
            r["repeat_identical"]
            and r["status"] == ("pass" if n == "correct" else "fail")
            for n, r in reports.items()
        ):
            raise RuntimeError(
                "Unexpected calibration verdict; no live mutations permitted"
            )
        if fingerprint() != before:
            raise RuntimeError("Calibration changed active document")
        root = "LayerProbe_" + uuid.uuid4().hex[:10]
        created_layers, created_objects, calls = [], [], []

        def command(name, params):
            require_owned(runtime(), owner)
            assert_document(owner["document"], owner["marker"])
            try:
                result = get_rhino_connection().send_command(name, params)
            except Exception as exc:
                calls.append({"command": name, "params": params, "error": str(exc)})
                save(directory / "calls.json", calls)
                raise
            calls.append({"command": name, "params": params, "result": result})
            save(directory / "calls.json", calls)
            return result

        def layer(name, parent=None):
            result = command(
                "create_layer", {"name": name, **({"parent": parent} if parent else {})}
            )
            created_layers.append(result["id"])
            return result

        try:
            layer(root)
            layer("Left", root)
            layer("Right", root)
            # Exact full paths must address the intended branch, including duplicate leaves.
            for side in ("Left", "Right"):
                try:
                    layer("Part", root + "::" + side)
                except Exception:
                    pass  # Failure is evidence; inspect and save the actual result.
            for i, side in enumerate(("Left", "Right")):
                result = command(
                    "create_object",
                    {
                        "type": "BOX",
                        "name": side.lower() + "_part",
                        "params": {"width": 10, "length": 10, "height": 10},
                        "translation": [i * 30 + 5, 5, 5],
                    },
                )
                created_objects.append(result["id"])
                try:
                    command(
                        "update_object_attributes",
                        {"id": result["id"], "layer": root + "::" + side + "::Part"},
                    )
                except Exception as exc:
                    calls.append({"assignment_error": str(exc)})
                    save(directory / "calls.json", calls)
            artifact = directory / "mcp_full_paths.3dm"
            script(
                f'if(!doc.WriteFile({json.dumps(str(artifact))},new Rhino.FileIO.FileWriteOptions())) throw new Exception("Save failed");'
            )
            a, b = measure(artifact), measure(artifact)
            live = evaluate(a, root)
            live.update(repeat_identical=a == b, artifact_sha256=sha256(artifact))
            save(directory / "live.json", live)
            # Missing parent must not silently create an unrelated root layer.
            layer("MissingParentChild_" + root, root + "::Absent")
        finally:
            require_owned(runtime(), owner)
            assert_document(owner["document"], owner["marker"])
            for identifier in created_objects:
                command("delete_object", {"id": identifier})
            for identifier in reversed(created_layers):
                script(
                    f'var l=doc.Layers.FindId(new Guid({json.dumps(identifier)})); if(l!=null && !l.IsDeleted && !doc.Layers.Delete(l.Index,true)) throw new Exception("Layer cleanup failed");'
                )
            after = fingerprint()
            save(directory / "after.json", after)
            if after != before:
                raise RuntimeError(
                    "Document fingerprint changed; inspect before continuing"
                )
        if pins != {name: sha256(ROOT / name) for name in sources}:
            raise RuntimeError("Pinned inputs changed")
        planner = run_session(
            directory / "planner",
            "Diagnose this general RhinoMCP layer-tree capability probe. No code changes authorized in this session. Task: Assembly::Left::Part and Assembly::Right::Part, each with its named 10mm cube, visible and unlocked. Independent File3dm fixtures calibrate parent-ID reconstruction, object layer indexes, visibility, geometry and wrong cases. Live calls used exact full paths. create_layer currently calls FindName(parent) and silently creates a root if unresolved; update_object_attributes has a full-path fallback. Recommend a bounded reusable repair and preservation requirements, distinguish unsupported full-path handling from agent modeling errors. Preserve all 52 accepted checks; propose full-path and ambiguous/missing-parent tests. No chair visual improvement claimed.\n"
            + json.dumps(
                {
                    "calibration": {n: r["status"] for n, r in reports.items()},
                    "live": live,
                    "calls": calls,
                }
            ),
            PLANNER_SCHEMA,
            180,
        )
        summary = {
            "calibration_cases": 9,
            "calibration_expected": True,
            "live_status": live["status"],
            "repeat_identical": live["repeat_identical"],
            "document_preserved": True,
            "planner": planner,
            "plugin_changed": False,
            "promoted": False,
        }
        save(directory / "summary.json", summary)
        print(json.dumps(summary), flush=True)
        return directory


if __name__ == "__main__":
    run()
