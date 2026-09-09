"""Shared creation-feedback regressions: extrema, pivots, and trimmed solids."""

from contextlib import nullcontext
import json
import math
import time
from experiments.bridge import script
from experiments.runner import ROOT, save, save_candidate, capture
from experiments.rhino_trial import runtime, require_owned
from experiments.strip_probe import fingerprint
from experiments.trial import locked
from rhinomcp.server import get_rhino_connection


def near(a, b):
    return len(a) == len(b) and all(abs(x - y) < 1e-6 for x, y in zip(a, b))


def run(*, acquire_lock=True):
    directory = (
        ROOT / "experiments/runs" / time.strftime("surface-feedback-%Y%m%d-%H%M%S")
    )
    directory.mkdir()
    cases = [
        ("raised", 30, {}, [[0, 0, 10], [100, 100, 30]], [50, 50, 30]),
        ("depressed", -10, {}, [[0, 0, -10], [100, 100, 10]], [50, 50, -10]),
        (
            "rotated",
            30,
            {"rotation": [math.pi / 2, 0, 0]},
            [[0, 40, -30], [100, 60, 70]],
            [50, 40, 20],
        ),
        (
            "scaled",
            -10,
            {"scale": [1, 1, 2]},
            [[0, 0, -10], [100, 100, 30]],
            [50, 50, -10],
        ),
    ]
    results = {}
    with (
        locked(ROOT / "experiments/runs/rhino.lock") if acquire_lock else nullcontext()
    ):
        owner = runtime()
        require_owned(owner, owner)
        if owner["object_count"] or owner["marker"]:
            raise RuntimeError("Require empty dedicated document")
        before = fingerprint()
        for name, peak, transform, expected, center in cases:
            params = {
                "type": "SURFACE",
                "name": name,
                "params": {
                    "count": [3, 3],
                    "degree": [2, 2],
                    "closed": [False, False],
                    "points": [
                        [i * 50, j * 50, peak if i == j == 1 else 10]
                        for i in range(3)
                        for j in range(3)
                    ],
                },
                **transform,
            }
            response = get_rhino_connection().send_command("create_object", params)
            oid = json.dumps(response["id"])
            try:
                code = f"""var b=(Brep)doc.Objects.FindId(new Guid({oid})).Geometry;
using(var copy=b.DuplicateBrep()){{
var box=copy.GetBoundingBox(true);var s=copy.Faces[0].UnderlyingSurface();
var p=s.PointAt(s.Domain(0).Mid,s.Domain(1).Mid);
output.AppendLine(Serialize(new{{bounds=new[]{{new[]{{box.Min.X,box.Min.Y,box.Min.Z}},new[]{{box.Max.X,box.Max.Y,box.Max.Z}}}},center=new[]{{p.X,p.Y,p.Z}}}}));
}}"""
                measured = json.loads(script(code))
                repeated = json.loads(script(code))
                results[name] = {
                    "request": params,
                    "response": response,
                    "measured": measured,
                    "expected_bounds": expected,
                    "expected_center": center,
                    "checks": {
                        "response_bounds": all(
                            near(a, b)
                            for a, b in zip(response["bounding_box"], expected)
                        ),
                        "geometry_bounds": all(
                            near(a, b) for a, b in zip(measured["bounds"], expected)
                        ),
                        "geometry_center": near(measured["center"], center),
                        "repeat_identical": measured == repeated,
                    },
                }
                (directory / f"{name}-measure.cs").write_text(code)
                artifacts = directory / name
                artifacts.mkdir()
                results[name]["artifact_sha256"] = save_candidate(
                    artifacts / "candidate.3dm", owner["document"], owner["marker"]
                )
                capture(artifacts, owner["document"], owner["marker"])
            finally:
                require_owned(runtime(), owner)
                script(
                    f'if(!doc.Objects.Delete(new Guid({oid}),true))throw new Exception("Cleanup failed");'
                )
        trim_code = """var solid=new Box(Plane.WorldXY,new Interval(0,100),new Interval(0,60),new Interval(0,20)).ToBrep();
var cutter=new Cylinder(new Circle(new Point3d(30,20,-10),6),40).ToBrep(true,true);
var cut=Brep.CreateBooleanDifference(solid,cutter,0.001)[0];var crc=cut.DataCRC(0);
using(var copy=cut.DuplicateBrep()) {var box=copy.GetBoundingBox(true);
output.AppendLine(Serialize(new {bounds=new[]{new[]{box.Min.X,box.Min.Y,box.Min.Z},new[]{box.Max.X,box.Max.Y,box.Max.Z}},source_unchanged=crc==cut.DataCRC(0),solid=copy.IsSolid}));}"""
        trim = json.loads(script(trim_code))
        (directory / "trimmed-control.cs").write_text(trim_code)
        results["trimmed_solid"] = {
            "measured": trim,
            "checks": {
                "bounds": all(
                    near(a, b)
                    for a, b in zip(trim["bounds"], [[0, 0, 0], [100, 60, 20]])
                ),
                "source_unchanged": trim["source_unchanged"],
                "solid": trim["solid"],
            },
        }
        if fingerprint() != before:
            raise RuntimeError("Document changed")
        save(directory / "preservation.json", {"preserved": True, "runtime": runtime()})
    save(directory / "results.json", results)
    (directory / "source.py").write_bytes(
        (ROOT / "experiments/surface_feedback_probe.py").read_bytes()
    )
    print(directory)
    return directory


if __name__ == "__main__":
    run()
