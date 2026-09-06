"""Reproduce a returned flat bounding box with a non-flat interpolation input."""

import json
import time
from experiments.runner import ROOT, save
from experiments.bridge import script
from experiments.rhino_trial import runtime, require_owned
from experiments.strip_probe import fingerprint
from experiments.trial import locked
from rhinomcp.server import get_rhino_connection


def run():
    directory = (
        ROOT / "experiments/runs" / time.strftime("surface-bounds-%Y%m%d-%H%M%S")
    )
    directory.mkdir()
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        if owner["object_count"] or owner["marker"]:
            raise RuntimeError("Require empty document")
        before = fingerprint()
        params = {
            "type": "SURFACE",
            "name": "bounds_probe",
            "params": {
                "count": [3, 3],
                "points": [
                    [0, 0, 10],
                    [0, 50, 10],
                    [0, 100, 10],
                    [50, 0, 10],
                    [50, 50, 30],
                    [50, 100, 10],
                    [100, 0, 10],
                    [100, 50, 10],
                    [100, 100, 10],
                ],
                "degree": [2, 2],
                "closed": [False, False],
            },
        }
        result = get_rhino_connection().send_command("create_object", params)
        oid = json.dumps(result["id"])
        code = f"""var o=doc.Objects.FindId(new Guid({oid}));var b=o.Geometry as Brep;var s=b.Faces[0].UnderlyingSurface();
output.AppendLine(Serialize(new {{brep_bounds=b.GetBoundingBox(true),surface_bounds=s.GetBoundingBox(true),center=s.PointAt(s.Domain(0).Mid,s.Domain(1).Mid),solid=b.IsSolid,valid=b.IsValid}}));"""
        try:
            a = json.loads(script(code))
            b = json.loads(script(code))
            save(
                directory / "measurement.json",
                {
                    "request": params,
                    "tool_response": result,
                    "independent": a,
                    "repeat_identical": a == b,
                    "runtime": owner,
                },
            )
            (directory / "source.py").write_bytes(
                (ROOT / "experiments/surface_bounds_probe.py").read_bytes()
            )
            (directory / "source.cs").write_text(code)
        finally:
            require_owned(runtime(), owner)
            script(
                f'if(!doc.Objects.Delete(new Guid({oid}),true))throw new Exception("Probe cleanup failed");'
            )
            save(
                directory / "preservation.json",
                {"preserved": before == fingerprint(), "runtime": runtime()},
            )
            if before != fingerprint():
                raise RuntimeError("Document changed")
    return directory


if __name__ == "__main__":
    print(run())
