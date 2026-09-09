"""Render saved models with common framing; preserve live document and source files."""

import json
from experiments.bridge import script, assert_document
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import ROOT, sha256, save
from experiments.strip_probe import fingerprint
from experiments.trial import locked


def run(directory):
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = json.loads((directory / "environment.json").read_text())["rhino"]
        require_owned(runtime(), owner)
        assert_document(owner["document"], directory.name)
        before = fingerprint()
        baseline = (
            ROOT / "experiments/runs/visual-20260906-084828-2fc89506/candidate.3dm"
        )
        candidate = directory / "candidate.3dm"
        hashes = {str(p): sha256(p) for p in [baseline, candidate]}
        output = directory / "comparison"
        output.mkdir()
        code = (ROOT / "experiments/compare_models.cs").read_text()
        (output / "source.cs").write_text(code)
        (output / "source.py").write_bytes(
            (ROOT / "experiments/compare_models.py").read_bytes()
        )
        for token, path in [
            ("BASELINE_PATH", baseline),
            ("CANDIDATE_PATH", candidate),
            ("OUTPUT_DIRECTORY", output),
        ]:
            code = code.replace(token, json.dumps(str(path)))
        cameras = json.loads(script(code))
        after = fingerprint()
        save(
            output / "preservation.json",
            {"before": before, "after": after, "preserved": before == after},
        )
        if before != after or hashes != {
            str(p): sha256(p) for p in [baseline, candidate]
        }:
            raise RuntimeError("Comparison changed document or model")
        if not all(v["frames"][0] == v["frames"][1] for v in cameras):
            raise RuntimeError("Comparison cameras changed")
        save(
            output / "manifest.json",
            {
                "sources": hashes,
                "alignment": "Neutral-gray display copies centered in XY and moved to ground Z=0; no scaling or rotation. Same padded union bounds and projection per view. Reference cameras remain unmatched.",
                "cameras": cameras,
                "images": {p.name: sha256(p) for p in output.glob("*.png")},
                "visual_acceptance": "unscored",
            },
        )
        return output
