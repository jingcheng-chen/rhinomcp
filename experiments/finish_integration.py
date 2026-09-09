"""Supervised comparison and cleanup of a completed owned integration diagnostic."""

import json
from experiments.bridge import script, assert_document
from experiments.compare_models import run as compare
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import ROOT, save, sha256
from experiments.strip_probe import fingerprint
from experiments.trial import locked


def run(directory):
    checkpoint = json.loads((directory / "checkpoint.json").read_text())
    if checkpoint["stage"] != "completed_diagnostic":
        raise RuntimeError("Finish only a completed diagnostic")
    compare(directory)
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = json.loads((directory / "environment.json").read_text())["rhino"]
        require_owned(runtime(), owner)
        assert_document(owner["document"], directory.name)
        summary = json.loads((directory / "summary.json").read_text())
        if sha256(directory / "candidate.3dm") != summary["artifact_sha256"]:
            raise RuntimeError("Saved artifact changed")
        before = json.loads((directory / "document-before.json").read_text())
        if before["objects"]:
            raise RuntimeError("Original document was not empty")
        ids = ",".join(
            "new Guid(" + json.dumps(layer["Id"]) + ")" for layer in before["layers"]
        )
        script(f"""
foreach(var o in doc.Objects.Where(o=>o!=null&&!o.IsDeleted).ToArray())doc.Objects.Delete(o.Id,true);
var keep=new HashSet<Guid>(new[]{{{ids}}});
foreach(var layer in doc.Layers.Where(l=>!l.IsDeleted&&!keep.Contains(l.Id)).OrderByDescending(l=>l.FullPath.Split(new[]{{"::"}},StringSplitOptions.None).Length).ToArray())
 if(!doc.Layers.Delete(layer.Index,true))throw new Exception("Layer cleanup failed");
doc.ModelAbsoluteTolerance={before["tolerance"]};doc.Strings.Delete("rhinomcp_experiment");
""")
        modes = json.loads((directory / "display-before.json").read_text())
        for mode in modes:
            script(
                f"""var v=doc.Views.First(v=>v.ActiveViewport.Id==new Guid({json.dumps(mode["id"])}));v.ActiveViewport.DisplayMode=Rhino.Display.DisplayModeDescription.GetDisplayMode(new Guid({json.dumps(mode["mode"])}));"""
            )
        after = fingerprint()
        actual_modes = json.loads(
            script(
                "output.AppendLine(Serialize(doc.Views.Select(v=>new {id=v.ActiveViewport.Id,mode=v.ActiveViewport.DisplayMode.Id}).ToArray()));"
            )
        )
        result = {
            "before": before,
            "after": after,
            "preserved": before == after,
            "display_modes_restored": modes == actual_modes,
            "runtime": runtime(),
        }
        save(directory / "cleanup.json", result)
        if not result["preserved"] or not result["display_modes_restored"]:
            raise RuntimeError("Cleanup verification failed")
        (directory / "finish-source.py").write_bytes(
            (ROOT / "experiments/finish_integration.py").read_bytes()
        )
        return result
