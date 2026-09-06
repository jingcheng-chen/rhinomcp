"""Recalibrate legacy and deeper assembly fixtures before fresh modeling."""

import json
import time
import uuid

from experiments.assembly_task import load
from experiments.bridge import script
from experiments.layer_probe import measure, evaluate
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import ROOT, save, sha256
from experiments.strip_probe import fingerprint
from experiments.trial import locked


def run():
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        before = fingerprint()
        directory = (
            ROOT
            / "experiments/runs"
            / (
                time.strftime("deep-layer-calibration-%Y%m%d-%H%M%S-")
                + uuid.uuid4().hex[:8]
            )
        )
        directory.mkdir()
        save(directory / "environment.json", owner)
        files = [
            "layer_probe.py",
            "layer_measure.cs",
            "layer_controls.cs",
            "deep_layer_controls.cs",
            "assembly_task.py",
            "assembly_tasks/schema.json",
            "assembly_tasks/deep_stand.json",
            "validate_deep_layers.py",
        ]
        pins = {name: sha256(ROOT / "experiments" / name) for name in files}
        save(directory / "inputs.json", pins)
        for name in files:
            dst = directory / "source" / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((ROOT / "experiments" / name).read_bytes())
        reports = {}
        for kind, source, task, count in [
            ("legacy", "layer_controls.cs", None, 9),
            (
                "deep",
                "deep_layer_controls.cs",
                load(ROOT / "experiments/assembly_tasks/deep_stand.json"),
                10,
            ),
        ]:
            target = directory / kind
            target.mkdir()
            script(
                (ROOT / "experiments" / source)
                .read_text()
                .replace("OUTPUT_DIRECTORY", json.dumps(str(target)))
            )
            paths = list(target.glob("*.3dm"))
            if len(paths) != count:
                raise RuntimeError("Fixture count mismatch")
            for path in sorted(paths):
                a, b = measure(path), measure(path)
                result = evaluate(a, task=task)
                result.update(repeat_identical=a == b, artifact_sha256=sha256(path))
                reports[kind + "/" + path.stem] = result
        after = fingerprint()
        save(directory / "validation.json", reports)
        save(
            directory / "preservation.json",
            {"before": before, "after": after, "preserved": before == after},
        )
        expected = all(
            r["repeat_identical"]
            and r["status"] == ("pass" if name.endswith("/correct") else "fail")
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
            or pins != {name: sha256(ROOT / "experiments" / name) for name in files}
        ):
            raise RuntimeError("Calibration or integrity check failed")
        print(directory, flush=True)
        return directory


if __name__ == "__main__":
    run()
