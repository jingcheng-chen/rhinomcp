"""Live regression: count hidden/locked objects and preserve a hidden comparison sentinel."""

import json
import time
from experiments.runner import ROOT, save, sha256
from experiments.bridge import script, assert_document
from experiments.rhino_trial import runtime, require_owned
from experiments.strip_probe import fingerprint
from experiments.compare_models import run as compare
from experiments.trial import locked


def run(candidate):
    directory = (
        ROOT
        / "experiments/runs"
        / time.strftime("comparison-cleanup-validation-%Y%m%d-%H%M%S")
    )
    directory.mkdir()
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        if owner["object_count"] or owner["marker"]:
            raise RuntimeError("Require a truly empty dedicated document")
        before = fingerprint()
        save(directory / "environment.json", {"rhino": owner})
        save(directory / "before.json", before)
        (directory / "candidate.3dm").write_bytes(candidate.read_bytes())
        ids = json.loads(
            script("""
var normal=doc.Objects.AddPoint(new Point3d(1,2,3));
var hidden=doc.Objects.AddPoint(new Point3d(4,5,6));doc.Objects.Hide(hidden,true);
var locked=doc.Objects.AddPoint(new Point3d(7,8,9));doc.Objects.Lock(locked,true);
output.AppendLine(Serialize(new[]{normal,hidden,locked}));
""")
        )
        counted = runtime()["object_count"] == 3 and len(fingerprint()["objects"]) == 3
        # Keep the hidden sentinel through both view-switch and copy-cleanup paths.
        script(
            f'doc.Objects.Delete(new Guid({json.dumps(ids[0])}),true);doc.Objects.Unlock(new Guid({json.dumps(ids[2])}),true);doc.Objects.Delete(new Guid({json.dumps(ids[2])}),true);doc.Strings.SetString("rhinomcp_experiment",{json.dumps(directory.name)});'
        )
    try:
        comparison = compare(directory)
        with locked(ROOT / "experiments/runs/rhino.lock"):
            require_owned(runtime(), owner)
            assert_document(owner["document"], directory.name)
            still_hidden = (
                len(fingerprint()["objects"]) == 1 and runtime()["object_count"] == 1
            )
            save(
                directory / "summary.json",
                {
                    "hidden_locked_counted": counted,
                    "hidden_sentinel_preserved": still_hidden,
                    "comparison_preserved": json.loads(
                        (comparison / "preservation.json").read_text()
                    )["preserved"],
                    "candidate_sha256": sha256(candidate),
                },
            )
            if not counted or not still_hidden:
                raise RuntimeError("Hidden-object regression failed")
    finally:
        with locked(ROOT / "experiments/runs/rhino.lock"):
            require_owned(runtime(), owner)
            assert_document(owner["document"], directory.name)
            script(
                f'var id=new Guid({json.dumps(ids[1])});doc.Objects.Show(id,true);if(!doc.Objects.Delete(id,true))throw new Exception("Sentinel cleanup failed");doc.Strings.Delete("rhinomcp_experiment");'
            )
            after = fingerprint()
            save(
                directory / "cleanup.json",
                {"preserved": before == after, "runtime": runtime()},
            )
            if before != after:
                raise RuntimeError("Cleanup changed the starting document")
    return directory


if __name__ == "__main__":
    import sys
    from pathlib import Path

    print(run(Path(sys.argv[1]).resolve()))
