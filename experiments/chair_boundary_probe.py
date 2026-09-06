"""Read paired naked-edge distances from a saved back_body; never alter the file."""

import json
import time
import sys
from pathlib import Path
from experiments.runner import ROOT, save, sha256
from experiments.bridge import script
from experiments.rhino_trial import runtime, require_owned
from experiments.strip_probe import fingerprint
from experiments.trial import locked


def run(artifact):
    directory = (
        ROOT / "experiments/runs" / time.strftime("chair-boundary-%Y%m%d-%H%M%S")
    )
    directory.mkdir()
    code = (ROOT / "experiments/chair_boundary_probe.cs").read_text()
    (directory / "source.cs").write_text(code)
    (directory / "source.py").write_bytes(Path(__file__).read_bytes())
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        before = fingerprint()
        digest = sha256(artifact)
        code = code.replace("ARTIFACT_PATH", json.dumps(str(artifact)))
        a, b = json.loads(script(code)), json.loads(script(code))
        save(directory / "measurement.json", a)
        report = {
            "repeat_identical": a == b,
            "artifact_preserved": digest == sha256(artifact),
            "document_preserved": before == fingerprint(),
            "runtime": runtime(),
            "artifact_sha256": digest,
        }
        save(directory / "summary.json", report)
        if not all(
            report[k]
            for k in ["repeat_identical", "artifact_preserved", "document_preserved"]
        ):
            raise RuntimeError("Boundary measurement integrity failure")
    return directory


if __name__ == "__main__":
    print(run(Path(sys.argv[1]).resolve()))
