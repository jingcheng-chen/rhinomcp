"""Calibrate the fixed cushion judge with independent saved Bezier fixtures."""

import json
import time
import uuid

from experiments.bridge import script
from experiments.cushion_body_probe import measure, evaluate
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import ROOT, save, sha256
from experiments.strip_probe import fingerprint
from experiments.trial import locked


def run():
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        if owner["object_count"] or owner["marker"]:
            raise RuntimeError("Use the dedicated empty unsaved document")
        before = fingerprint()
        directory = (
            ROOT
            / "experiments/runs"
            / (
                time.strftime("cushion-body-calibration-%Y%m%d-%H%M%S-")
                + uuid.uuid4().hex[:8]
            )
        )
        directory.mkdir()
        print(directory, flush=True)
        names = [
            "cushion_body_probe.py",
            "cushion_probe.py",
            "cushion_body_measure.cs",
            "cushion_body_controls.cs",
            "cushion_body_task.json",
            "validate_cushion_body.py",
            "layer_probe.py",
            "bridge.py",
        ]
        pins = {n: sha256(ROOT / "experiments" / n) for n in names}
        save(directory / "inputs.json", pins)
        save(directory / "environment.json", owner)
        for n in names:
            p = directory / "source" / n
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((ROOT / "experiments" / n).read_bytes())
        script(
            (ROOT / "experiments/cushion_body_controls.cs")
            .read_text()
            .replace("OUTPUT_DIRECTORY", json.dumps(str(directory)))
        )
        paths = sorted(directory.glob("*.3dm"))
        if len(paths) != 11:
            raise RuntimeError("Expected eleven calibration files")
        reports = {}
        for path in paths:
            scale = 0.75 if path.stem == "scaled_correct" else 1.0
            a, b = measure(path, scale), measure(path, scale)
            r = evaluate(a, scale)
            r.update(repeat_identical=a == b, artifact_sha256=sha256(path))
            reports[path.stem] = r
        reports["scaled_at_wrong_scale"] = evaluate(
            measure(directory / "scaled_correct.3dm"), 1.0
        )
        reports["scaled_at_wrong_scale"]["repeat_identical"] = (
            measure(directory / "scaled_correct.3dm")
            == reports["scaled_at_wrong_scale"]["measurements"]
        )
        after = fingerprint()
        save(directory / "validation.json", reports)
        save(
            directory / "preservation.json",
            {"before": before, "after": after, "preserved": before == after},
        )
        expected = all(
            r["repeat_identical"]
            and r["status"]
            == ("pass" if name in {"correct", "scaled_correct"} else "fail")
            for name, r in reports.items()
        )
        save(
            directory / "summary.json",
            {
                "cases": len(reports),
                "expected_verdicts": expected,
                "document_preserved": before == after,
            },
        )
        if (
            not expected
            or before != after
            or pins != {n: sha256(ROOT / "experiments" / n) for n in names}
        ):
            raise RuntimeError("Calibration or integrity check failed")
        print(directory, flush=True)
        return directory


if __name__ == "__main__":
    run()
