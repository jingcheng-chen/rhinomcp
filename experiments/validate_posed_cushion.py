"""Independent analytic fixtures posed before fixed local checks; no live objects."""

import json
import time
from experiments.runner import ROOT, save, sha256
from experiments.bridge import script
from experiments.rhino_trial import runtime, require_owned
from experiments.strip_probe import fingerprint
from experiments.trial import locked
from experiments.posed_cushion_probe import measure, evaluate, forward_code


def posed_copy(source, target, pose):
    return f"""using(var src=Rhino.FileIO.File3dm.Read({json.dumps(str(source))}))
using(var dst=new Rhino.FileIO.File3dm()) {{
 dst.Settings.ModelUnitSystem=src.Settings.ModelUnitSystem;
 dst.Settings.ModelAbsoluteTolerance=src.Settings.ModelAbsoluteTolerance;
 foreach(var layer in src.AllLayers)dst.AllLayers.Add(layer);
 foreach(var o in src.Objects){{var g=o.Geometry.Duplicate();if(!g.Transform({forward_code(pose)}))throw new Exception("Transform failed");dst.Objects.Add(g,o.Attributes);}}
 if(!dst.Write({json.dumps(str(target))},8))throw new Exception("Save failed");
}}"""


def run():
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        if owner["object_count"] or owner["marker"]:
            raise RuntimeError("Require empty dedicated document")
        before = fingerprint()
        directory = (
            ROOT
            / "experiments/runs"
            / time.strftime("posed-cushion-calibration-%Y%m%d-%H%M%S")
        )
        directory.mkdir()
        local = directory / "local"
        local.mkdir()
        print(directory, flush=True)
        names = [
            "posed_cushion_probe.py",
            "validate_posed_cushion.py",
            "cushion_body_controls.cs",
            "cushion_body_measure.cs",
            "cushion_body_probe.py",
            "cushion_probe.py",
            "layer_probe.py",
            "bridge.py",
        ]
        pins = {n: sha256(ROOT / "experiments" / n) for n in names}
        save(directory / "inputs.json", pins)
        for n in names:
            p = directory / "source" / n
            p.parent.mkdir(exist_ok=True)
            p.write_bytes((ROOT / "experiments" / n).read_bytes())
        script(
            (ROOT / "experiments/cushion_body_controls.cs")
            .read_text()
            .replace("OUTPUT_DIRECTORY", json.dumps(str(local)))
        )
        reports = {}
        for path in sorted(local.glob("*.3dm")):
            target = directory / path.name
            script(posed_copy(path, target, "reclined"))
            a, b = measure(target), measure(target)
            reports[path.stem] = {**evaluate(a), "repeat_identical": a == b}
        # Correct shape at another pose must pass its own target and fail the first.
        target = directory / "alternate.3dm"
        script(posed_copy(local / "correct.3dm", target, "alternate"))
        for name, pose in [("alternate", "alternate"), ("wrong_pose", "reclined")]:
            a, b = measure(target, pose), measure(target, pose)
            reports[name] = {**evaluate(a, pose), "repeat_identical": a == b}
        ok = len(reports) == 13 and all(
            r["repeat_identical"]
            and r["status"] == ("pass" if name in {"correct", "alternate"} else "fail")
            for name, r in reports.items()
        )
        save(directory / "validation.json", reports)
        save(
            directory / "summary.json",
            {
                "cases": len(reports),
                "expected_verdicts": ok,
                "document_preserved": before == fingerprint(),
                "runtime": runtime(),
            },
        )
        if not (
            ok
            and before == fingerprint()
            and pins == {n: sha256(ROOT / "experiments" / n) for n in names}
        ):
            raise RuntimeError("Calibration or preservation failed")
        return directory


if __name__ == "__main__":
    run()
