"""Live MCP strip closure probe; preserves all pre-existing Rhino geometry."""

import json
import math
import time
import uuid

from experiments.bridge import script, assert_document
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import ROOT, save, sha256, run_session, PLANNER_SCHEMA
from experiments.trial import locked
from rhinomcp.server import get_rhino_connection

GRID = [-20, 10, 30, 50, 70, 95, 105, 125]
EXPECTED_MEMBERSHIP = [
    0 < z < 10 and x > 0 and y > 0 and 90**2 < x * x + y * y < 110**2
    for z in [-2, 5, 12]
    for x in GRID
    for y in GRID
]
EXPECTED_PASS = {
    "independent_correct",
    "independent_outward",
    "supervisor_capped_control",
}
CASES = {
    "mcp_closed_false",
    "mcp_closed_true",
    "supervisor_capped_control",
    "independent_correct",
    "independent_outward",
    "wrong_width",
    "equal_volume_wrong_radius",
    "wrong_position",
    "extra_object",
}


def evaluate(measured):
    objects = measured["objects"]
    one = objects[0] if len(objects) == 1 else {}

    def close(value, target):
        return (
            isinstance(value, (int, float))
            and math.isfinite(value)
            and abs(value - target) <= max(0.01, abs(target) * 1e-5)
        )

    checks = {
        "one_object": len(objects) == 1,
        "millimeters": measured["units"] == "Millimeters",
        "valid": one.get("valid") is True,
        "closed_solid": one.get("solid") is True,
        "no_naked_edges": one.get("naked_edges") == 0,
        "volume": close(one.get("volume"), 10000 * math.pi),
        "area": close(one.get("area"), 3000 * math.pi + 400),
        "bounds": all(
            close(a, b)
            for a, b in zip(
                one.get("min", []) + one.get("max", []), [0, 0, 0, 110, 110, 10]
            )
        )
        and len(one.get("min", []) + one.get("max", [])) == 6,
        "membership": one.get("membership") == EXPECTED_MEMBERSHIP,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "measurements": measured,
    }


def fingerprint():
    return json.loads(
        script("""
output.AppendLine(Serialize(new {
 objects=doc.Objects.GetObjectList(new Rhino.DocObjects.ObjectEnumeratorSettings { NormalObjects=true, HiddenObjects=true, LockedObjects=true, ReferenceObjects=true, IncludeLights=true }).Where(o=>o!=null && !o.IsDeleted).OrderBy(o=>o.Id).Select(o=>new {id=o.Id,geometry=o.Geometry.DataCRC(0),attributes=o.Attributes.ToJSON(new Rhino.FileIO.SerializationOptions())}).ToArray(),
 layers=doc.Layers.Where(l=>!l.IsDeleted).Select(l=>new {l.Id,l.Name,l.ParentLayerId,l.IsVisible,l.IsLocked}).ToArray(),
 units=doc.ModelUnitSystem.ToString(),tolerance=doc.ModelAbsoluteTolerance
}));
""")
    )


def measure(path):
    before = sha256(path)
    result = json.loads(
        script(
            (ROOT / "experiments/strip_measure.cs")
            .read_text()
            .replace("ARTIFACT_PATH", json.dumps(str(path)))
        )
    )
    if sha256(path) != before:
        raise RuntimeError("Fixture changed during measurement")
    return result


def run():
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        before = fingerprint()
        directory = (
            ROOT
            / "experiments/runs"
            / (time.strftime("strip-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
        )
        directory.mkdir()
        print(directory, flush=True)
        save(directory / "before.json", before)
        save(directory / "environment.json", owner)
        pins = {
            name: sha256(ROOT / "experiments" / name)
            for name in ["strip_probe.py", "strip_measure.cs", "strip_controls.cs"]
        }
        save(directory / "inputs.json", pins)
        for name in pins:
            (directory / name).write_bytes((ROOT / "experiments" / name).read_bytes())
        created = []

        def command(name, params):
            require_owned(runtime(), owner)
            assert_document(owner["document"], owner["marker"])
            result = get_rhino_connection().send_command(name, params)
            with (directory / "commands.jsonl").open("a") as f:
                f.write(
                    json.dumps({"command": name, "params": params, "result": result})
                    + "\n"
                )
            ids = (
                [result["id"]]
                if name == "create_object"
                else result.get("result_ids", [])
            )
            created.extend(ids)
            save(
                directory / "checkpoint.json",
                {"stage": "probing", "created_ids": created, "owner": owner},
            )
            return result

        try:
            rail = command(
                "create_object",
                {
                    "type": "ARC",
                    "name": directory.name + "_rail",
                    "params": {"center": [0, 0, 0], "radius": 100, "angle": 90},
                },
            )["id"]
            profile = command(
                "create_object",
                {
                    "type": "POLYLINE",
                    "name": directory.name + "_profile",
                    "params": {
                        "points": [
                            [90, 0, 0],
                            [110, 0, 0],
                            [110, 0, 10],
                            [90, 0, 10],
                            [90, 0, 0],
                        ]
                    },
                },
            )["id"]
            for closed in [False, True]:
                result = command(
                    "sweep1",
                    {
                        "rail_id": rail,
                        "profile_ids": [profile],
                        "closed": closed,
                        "name": directory.name + "_strip",
                    },
                )
                if len(result["result_ids"]) != 1:
                    raise RuntimeError("Expected one swept strip")
                identifier = result["result_ids"][0]
                path = directory / ("mcp_closed_" + str(closed).lower() + ".3dm")
                script(f"""
var brep=doc.Objects.Find(new Guid({json.dumps(identifier)})).Geometry as Brep;
using(var f=new Rhino.FileIO.File3dm()) {{
 f.Settings.ModelUnitSystem=UnitSystem.Millimeters;f.Objects.AddBrep(brep.DuplicateBrep(),new ObjectAttributes());f.Write({json.dumps(str(path))},8);
}}
""")
                if not closed:
                    # Supervisor-only diagnostic control, never part of the modeler's toolset.
                    script(f"""
var original=doc.Objects.Find(new Guid({json.dumps(identifier)})).Geometry as Brep;
var capped=original.DuplicateBrep().CapPlanarHoles(0.001);
if(capped==null) throw new Exception("Diagnostic capping failed");
using(var f=new Rhino.FileIO.File3dm()) {{
 f.Settings.ModelUnitSystem=UnitSystem.Millimeters;f.Objects.AddBrep(capped,new ObjectAttributes());f.Write({json.dumps(str(directory / "supervisor_capped_control.3dm"))},8);
}}
""")
        finally:
            require_owned(runtime(), owner)
            assert_document(owner["document"], owner["marker"])
            # Delete only IDs returned by our create/sweep calls, never baseline objects.
            for identifier in created:
                if identifier in {o["id"] for o in before["objects"]}:
                    raise RuntimeError("Refuse deletion of a baseline object")
                get_rhino_connection().send_command("delete_object", {"id": identifier})
            after = fingerprint()
            save(directory / "after.json", after)
            if before != after:
                raise RuntimeError(
                    "Pre-existing document changed; inspect saved evidence"
                )
            save(
                directory / "checkpoint.json",
                {"stage": "document_preserved", "owner": owner},
            )
        script(
            (ROOT / "experiments/strip_controls.cs")
            .read_text()
            .replace("OUTPUT_DIRECTORY", json.dumps(str(directory)))
        )
        reports = {}
        for name in sorted(CASES):
            path = directory / (name + ".3dm")
            a = measure(path)
            b = measure(path)
            report = evaluate(a)
            report["repeat_identical"] = a == b
            report["artifact_sha256"] = sha256(path)
            reports[name] = report
        if pins != {name: sha256(ROOT / "experiments" / name) for name in pins}:
            raise RuntimeError("Probe source changed")
        save(directory / "validation.json", reports)
        expected = all(
            r["status"] == ("pass" if name in EXPECTED_PASS else "fail")
            and r["repeat_identical"]
            for name, r in reports.items()
        )
        save(
            directory / "checkpoint.json",
            {
                "stage": "validated" if expected else "unexpected_verdict",
                "owner": owner,
            },
        )
        if not expected:
            raise RuntimeError(
                "Unexpected fixture verdict; investigate evaluator before planning repair"
            )
        planner = run_session(
            directory / "planner",
            "You are a planner for a general RhinoMCP self-improvement harness. Diagnose the attached fixed quarter-annular rectangular-strip experiment. Required: one valid closed solid, R=100, radial width=20, height=10, angle=90 degrees, fixed origin and units. Two live MCP sweeps differ only in closed=false/true. The existing handler reads closed but does not use it, uses RoadlikeTop PerformSweep and does not cap. Supervisor-only capping and an independently extruded annular-sector profile are diagnostic controls; neither is an available modeler repair. No existing geometry was altered. Distinguish unsupported end-capping from a regression; closed sweep is not synonymous with planar end caps. Propose one bounded generic capability change or evidence-driven alternative, with positive/negative tests and preservation of the existing 43 cases. Do not write code or claim a change has been implemented. Layer hierarchy is a separate requested roadmap item.\n"
            + json.dumps(reports),
            PLANNER_SCHEMA,
            180,
        )
        summary = {
            "expected_verdicts": expected,
            "document_preserved": True,
            "cases": {name: r["status"] for name, r in reports.items()},
            "planner": planner,
            "plugin_changed": False,
            "promoted": False,
        }
        save(directory / "summary.json", summary)
        save(directory / "checkpoint.json", {"stage": "completed", "owner": owner})
        print(json.dumps(summary), flush=True)
        return directory


if __name__ == "__main__":
    run()
