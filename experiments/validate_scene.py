"""Calibrate four workflow cases using saved positive and negative Rhino fixtures."""

import copy
import json
import time
from experiments.bridge import script
from experiments.runner import ROOT, load_task, save, sha256
from experiments.scene_task import creation_code, measure, evaluate
from experiments.rhino_trial import runtime, require_owned
from experiments.strip_probe import fingerprint
from experiments.trial import locked


def run(task_names=None):
    directory = (
        ROOT / "experiments/runs" / time.strftime("scene-calibration-%Y%m%d-%H%M%S")
    )
    directory.mkdir()
    results = []
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        before = fingerprint()
        for name in task_names or (
            "edit_existing",
            "table_assembly",
            "inspect_document",
            "recover_intermediate",
        ):
            task = load_task(ROOT / f"experiments/tasks/{name}.json")
            initial_path = directory / (name + "-initial.3dm")
            code = (
                "using(var f=new Rhino.FileIO.File3dm()){f.Settings.ModelUnitSystem=UnitSystem.Millimeters;"
                + creation_code(task["initial"], "f")
                + "if(!f.Write("
                + json.dumps(str(initial_path))
                + ',8))throw new Exception("write failed");}'
            )
            script(code)
            initial = measure(initial_path)
            ids = {o["name"]: o["id"] for o in initial["objects"]}
            variants = [
                "correct",
                "wrong_bounds",
                "extra_object",
                "wrong_layer",
                "wrong_units",
                "missing_object",
            ]
            if any(
                t.get("shape") == "rectangle_curve" and not t.get("unchanged")
                for t in task["targets"]
            ):
                variants.append("wrong_curve_height")
            if task["initial"]:
                variants.append("replaced_id")
            if task["family"] == "recovery":
                variants.append("wrong_intermediate_retained")
            if task["family"] == "document-inspection":
                variants += ["wrong_report", "write_attempt"]
            for variant in variants:
                path = directory / f"{name}-{variant}.3dm"
                targets = copy.deepcopy(task["targets"])
                preserve = ids
                if variant == "wrong_curve_height":
                    curve = next(
                        t
                        for t in targets
                        if t.get("shape") == "rectangle_curve"
                        and not t.get("unchanged")
                    )
                    curve["min"][2] += 3
                    curve["max"][2] += 3
                if variant == "wrong_bounds":
                    targets[0]["max"][0] += 3
                if variant == "extra_object":
                    targets.append(
                        {
                            "name": "extra",
                            "layer": targets[0]["layer"],
                            "min": [300, 0, 0],
                            "max": [301, 1, 1],
                        }
                    )
                if variant == "wrong_layer":
                    targets[0]["layer"] = "Unexpected"
                if variant == "missing_object":
                    targets = targets[1:]
                if variant == "replaced_id":
                    preserve = {}
                if variant == "wrong_intermediate_retained":
                    targets += task["initial"][:1]
                code = (
                    "using(var f=Rhino.FileIO.File3dm.Read("
                    + json.dumps(str(initial_path))
                    + ")){foreach(var id in f.Objects.Where(o=>o!=null).Select(o=>o.Attributes.ObjectId).ToArray())f.Objects.Delete(id);"
                )
                if variant == "wrong_units":
                    code += "f.Settings.ModelUnitSystem=UnitSystem.Meters;"
                code += creation_code(targets, "f", preserve)
                code += (
                    "if(!f.Write("
                    + json.dumps(str(path))
                    + ',8))throw new Exception("write failed");}'
                )
                (directory / f"{name}-{variant}.cs").write_text(code)
                script(code)
                first = measure(path)
                second = measure(path)
                first["initial"] = initial
                first["inspection"] = [
                    {k: o[k] for k in ("name", "volume", "min", "max")}
                    for o in first["objects"]
                    if o["name"] in task["inspection_names"]
                ]
                first["inspection_no_write_calls"] = variant != "write_attempt"
                if variant == "wrong_report":
                    first["inspection"][0]["volume"] *= 2
                verdict = evaluate(task, first)
                repeat = {
                    k: v
                    for k, v in first.items()
                    if k not in {"initial", "inspection", "inspection_no_write_calls"}
                } == second
                results.append(
                    {
                        "task": task["id"],
                        "variant": variant,
                        "expected": "pass" if variant == "correct" else "fail",
                        "actual": verdict["status"],
                        "checks": verdict["checks"],
                        "repeat_identical": repeat,
                        "artifact": str(path.relative_to(ROOT)),
                        "artifact_sha256": sha256(path),
                    }
                )
                save(directory / "results.json", results)
        require_owned(runtime(), owner)
        if before != fingerprint():
            raise RuntimeError("Calibration changed active document")
    unexpected = [
        r for r in results if r["expected"] != r["actual"] or not r["repeat_identical"]
    ]
    save(
        directory / "summary.json",
        {
            "fixtures": len(results),
            "unexpected": unexpected,
            "preserved": True,
            "results": results,
        },
    )
    print(directory, flush=True)
    if unexpected:
        raise RuntimeError(json.dumps(unexpected))
    return directory


if __name__ == "__main__":
    run()
