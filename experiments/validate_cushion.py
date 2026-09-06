"""Calibrate the fixed cushion judge with independent saved Bezier fixtures."""

import json
import time
import uuid

from experiments.bridge import script
from experiments.cushion_probe import measure, evaluate
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
                time.strftime("cushion-calibration-%Y%m%d-%H%M%S-")
                + uuid.uuid4().hex[:8]
            )
        )
        directory.mkdir()
        print(directory, flush=True)
        names = [
            "cushion_probe.py",
            "cushion_measure.cs",
            "cushion_controls.cs",
            "cushion_task.json",
            "validate_cushion.py",
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
            (ROOT / "experiments/cushion_controls.cs")
            .read_text()
            .replace("OUTPUT_DIRECTORY", json.dumps(str(directory)))
        )
        paths = sorted(directory.glob("*.3dm"))
        if len(paths) != 12:
            raise RuntimeError("Expected twelve calibration files")
        reports = {}
        for path in paths:
            a, b = measure(path), measure(path)
            r = evaluate(a)
            r.update(repeat_identical=a == b, artifact_sha256=sha256(path))
            reports[path.stem] = r
        after = fingerprint()
        save(directory / "validation.json", reports)
        save(
            directory / "preservation.json",
            {"before": before, "after": after, "preserved": before == after},
        )
        expected = all(
            r["repeat_identical"]
            and r["status"]
            == ("pass" if name in {"correct", "reparameterized"} else "fail")
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
