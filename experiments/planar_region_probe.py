"""Independent live contract for the declared planar-region capability."""

import json
import math
from pathlib import Path
from rhinomcp.server import get_rhino_connection
from experiments.bridge import script, assert_document
from experiments.runner import save, sha256, capture
from experiments.rhino_trial import runtime, require_owned
from experiments.strip_probe import fingerprint
from experiments.workflow.pilot import cleanup

CASES = (
    "outer_only",
    "one_hole",
    "two_holes",
    "reversed",
    "posed",
    "open_outer",
    "nonplanar_outer",
    "offset_inner",
    "tilted_inner",
    "outside_inner",
    "touching_inner",
    "crossing_inner",
    "nested_inners",
    "overlapping_inners",
    "duplicate_ids",
    "missing_id",
    "noncurve",
    "self_intersecting",
)
POSITIVE = {"outer_only", "one_hole", "two_holes", "reversed", "posed"}


def fixture_code(case):
    outer = "new PolylineCurve(new[]{new Point3d(0,0,0),new Point3d(100,0,0),new Point3d(100,80,0),new Point3d(0,80,0),new Point3d(0,0,0)})"
    if case == "open_outer":
        outer = "new LineCurve(new Point3d(0,0,0),new Point3d(100,0,0))"
    if case == "nonplanar_outer":
        outer = outer.replace("100,80,0", "100,80,5")
    if case == "self_intersecting":
        outer = "new PolylineCurve(new[]{new Point3d(0,0,0),new Point3d(100,80,0),new Point3d(100,0,0),new Point3d(0,80,0),new Point3d(0,0,0)})"
    x, y, z, r = 30, 45, 0, 12
    if case == "offset_inner":
        z = 3
    if case == "outside_inner":
        x = 130
    if case == "touching_inner":
        x = 12
    if case == "crossing_inner":
        x = 6
    second = ""
    if case == "two_holes":
        second = "curves.Add(new Circle(new Point3d(75,25,0),8).ToNurbsCurve());"
    if case == "nested_inners":
        second = "curves.Add(new Circle(new Point3d(30,45,0),4).ToNurbsCurve());"
    if case == "overlapping_inners":
        second = "curves.Add(new Circle(new Point3d(40,45,0),12).ToNurbsCurve());"
    return f"""
var curves=new List<Curve>{{{outer}}};
{"" if case == "outer_only" else f"curves.Add(new Circle(new Point3d({x},{y},{z}),{r}).ToNurbsCurve());"}
{second}
{"curves[1].Transform(Transform.Rotation(0.008,Vector3d.XAxis,new Point3d(30,45,0)));" if case == "tilted_inner" else ""}
{"foreach(var c in curves)c.Reverse();" if case == "reversed" else ""}
{"foreach(var c in curves){c.Transform(Transform.Rotation(Math.PI/6,Vector3d.XAxis,Point3d.Origin));c.Translate(20,-30,10);}" if case == "posed" else ""}
var ids=new List<string>();
foreach(var c in curves){{var a=new Rhino.DocObjects.ObjectAttributes();a.Name="preserved_boundary";ids.Add(doc.Objects.AddCurve(c,a).ToString());c.Dispose();}}
{"ids[0]=doc.Objects.AddPoint(Point3d.Origin).ToString();" if case == "noncurve" else ""}
{"ids[0]=Guid.NewGuid().ToString();" if case == "missing_id" else ""}
{"ids.Add(ids[1]);" if case == "duplicate_ids" else ""}
output.AppendLine(Serialize(ids));
"""


def inspect_result(identifier, posed, target):
    return json.loads(
        script(f"""
var obj=doc.Objects.Find(new Guid({json.dumps(identifier)}));
var source=obj?.Geometry as Brep;
if(source==null)throw new Exception("Result is not a Brep");
using(var file=new Rhino.FileIO.File3dm()){{file.Settings.ModelUnitSystem=UnitSystem.Millimeters;file.Objects.AddBrep(source,obj.Attributes);if(!file.Write({json.dumps(str(target))},8))throw new Exception("Save failed");}}
using(var b=source.DuplicateBrep()){{
{"b.Translate(-20,30,-10);b.Transform(Transform.Rotation(-Math.PI/6,Vector3d.XAxis,Point3d.Origin));" if posed else ""}
var box=b.GetBoundingBox(true);
using(var area=AreaMassProperties.Compute(b)){{
output.AppendLine(Serialize(new{{valid=b.IsValid,solid=b.IsSolid,faces=b.Faces.Count,planar=b.Faces.Count==1&&b.Faces[0].IsPlanar(0.01),inner=b.Loops.Count(l=>l.LoopType==BrepLoopType.Inner),outer=b.Loops.Count(l=>l.LoopType==BrepLoopType.Outer),area=area==null?-1:area.Area,min=new[]{{box.Min.X,box.Min.Y,box.Min.Z}},max=new[]{{box.Max.X,box.Max.Y,box.Max.Z}}}}));
}}
}}
""")
    )


def run_checks(directory, owner):
    directory = Path(directory)
    directory.mkdir(parents=True)
    require_owned(runtime(), owner)
    if owner["object_count"] or owner["marker"]:
        raise RuntimeError("Planar probe requires empty unclaimed document")
    original = fingerprint()
    marker = directory.parent.name + "-planar-probe"
    script(
        f'doc.Strings.SetString("rhinomcp_experiment",{json.dumps(marker)});doc.ModelUnitSystem=UnitSystem.Millimeters;doc.ModelAbsoluteTolerance=0.01;'
    )
    supported = json.loads(
        script(
            'output.AppendLine(Serialize(AppDomain.CurrentDomain.GetAssemblies().Single(a=>a.GetName().Name=="rhinomcp").GetType("RhinoMCPPlugin.Functions.RhinoMCPFunctions").GetMethod("CreatePlanarRegion")!=null));'
        )
    )
    verdicts = {}
    details = {}
    try:
        for case in CASES:
            child = directory / case
            child.mkdir()
            assert_document(owner["document"], marker)
            code = fixture_code(case)
            (child / "fixture.cs").write_text(code)
            ids = json.loads(script(code))
            before = fingerprint()
            result = None
            error = None
            try:
                result = get_rhino_connection().send_command(
                    "create_planar_region",
                    {
                        "outer_curve_id": ids[0],
                        "inner_curve_ids": ids[1:],
                        "name": "planar_region_result",
                    },
                )
            except Exception as exc:
                error = str(exc)
            after = fingerprint()
            before_ids = {o["id"] for o in before["objects"]}
            after_sources = [o for o in after["objects"] if o["id"] in before_ids]
            preserved = after_sources == before["objects"] and all(
                after[k] == before[k] for k in ("units", "tolerance", "layers")
            )
            added = [o["id"] for o in after["objects"] if o["id"] not in before_ids]
            measurements = None
            if case in POSITIVE:
                geometry_ok = False
                if result and len(added) == 1 and added[0] == result.get("id"):
                    measurements = inspect_result(
                        added[0], case == "posed", child / "result.3dm"
                    )
                    holes = (
                        0 if case == "outer_only" else 2 if case == "two_holes" else 1
                    )
                    area = (
                        8000
                        - (math.pi * 144 if holes else 0)
                        - (math.pi * 64 if holes == 2 else 0)
                    )
                    geometry_ok = (
                        measurements["valid"]
                        and not measurements["solid"]
                        and measurements["faces"] == 1
                        and measurements["planar"]
                        and measurements["inner"] == holes
                        and measurements["outer"] == 1
                        and abs(measurements["area"] - area) < 0.1
                        and all(
                            abs(a - b) < 0.01
                            for a, b in zip(
                                measurements["min"] + measurements["max"],
                                [0, 0, 0, 100, 80, 0],
                            )
                        )
                    )
                passed = bool(supported and error is None and preserved and geometry_ok)
            else:
                passed = bool(
                    supported and error is not None and not added and preserved
                )
            capture(child, owner["document"], marker)
            details[case] = {
                "supported": supported,
                "passed": passed,
                "error": error,
                "response": result,
                "sources_preserved": preserved,
                "added_ids": added,
                "measurements": measurements,
            }
            if (child / "result.3dm").exists():
                details[case]["artifact_sha256"] = sha256(child / "result.3dm")
            verdicts["planar_region/" + case] = passed
            save(directory / "result.json", {"cases": verdicts, "details": details})
            # All objects belong to this initially empty, marked probe document.
            script(
                'foreach(var obj in doc.Objects.GetObjectList(new Rhino.DocObjects.ObjectEnumeratorSettings{NormalObjects=true,HiddenObjects=true,LockedObjects=true,ReferenceObjects=true,IncludeLights=true}).Where(o=>o!=null&&!o.IsDeleted).ToArray())if(!doc.Objects.Delete(obj.Id,true))throw new Exception("Probe cleanup failed");'
            )
    finally:
        after = cleanup(owner, marker, original)
        save(
            directory / "preservation.json",
            {"before": original, "after": after, "preserved": True},
        )
    return verdicts
