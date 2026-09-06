"""Frozen sweep capability checks; preserve the existing dedicated document."""

import json
from pathlib import Path

from experiments.bridge import assert_document, script
from experiments.runner import save
from experiments.strip_probe import evaluate, fingerprint, measure
from rhinomcp.server import get_rhino_connection

CASE_NAMES = [
    "sweep/default_open",
    "sweep/false_open",
    "sweep/cap_closed_false",
    "sweep/cap_closed_true",
    "sweep/reject_open_profile",
    "sweep/closed_rail_default",
    "sweep/closed_rail_cap",
]
BASELINE_FAILURES = CASE_NAMES[2:5]


def run_checks(directory, owner):
    """Caller holds Rhino lock. No planner or candidate-dependent expectations."""
    directory = Path(directory)
    directory.mkdir()
    before = fingerprint()
    save(directory / "before.json", before)
    created, cases, reports = [], {}, {}

    def command(name, params):
        assert_document(owner["document"], owner["marker"])
        try:
            result = get_rhino_connection().send_command(name, params)
        except Exception as error:
            with (directory / "commands.jsonl").open("a") as f:
                f.write(
                    json.dumps({"command": name, "params": params, "error": str(error)})
                    + "\n"
                )
            raise
        created.extend(
            [result["id"]] if name == "create_object" else result.get("result_ids", [])
        )
        save(directory / "created.json", {"owner": owner, "ids": created})
        with (directory / "commands.jsonl").open("a") as f:
            f.write(
                json.dumps({"command": name, "params": params, "result": result}) + "\n"
            )
        return result

    def create(kind, params):
        return command("create_object", {"type": kind, "params": params})["id"]

    def artifact(name, ids):
        path = directory / (name.split("/")[-1] + ".3dm")
        script(f"""
using(var file = new Rhino.FileIO.File3dm()) {{
 file.Settings.ModelUnitSystem=doc.ModelUnitSystem;
 foreach(var id in new string[] {{ {",".join(json.dumps(i) for i in ids)} }}) {{
  var obj=doc.Objects.Find(new Guid(id));
  file.Objects.Add(obj.Geometry, obj.Attributes);
 }}
 if(!file.Write({json.dumps(str(path))},8)) throw new Exception("Artifact write failed");
}}
""")
        a, b = measure(path), measure(path)
        reports[name] = {"measurements": a, "repeat_identical": a == b}
        return a, a == b

    try:
        rail = create("ARC", {"center": [0, 0, 0], "radius": 100, "angle": 90})
        profile = create(
            "POLYLINE",
            {
                "points": [
                    [90, 0, 0],
                    [110, 0, 0],
                    [110, 0, 10],
                    [90, 0, 10],
                    [90, 0, 0],
                ]
            },
        )
        for name, options in [
            (CASE_NAMES[0], {}),
            (CASE_NAMES[1], {"cap_planar_ends": False}),
            (CASE_NAMES[2], {"cap_planar_ends": True, "closed": False}),
            (CASE_NAMES[3], {"cap_planar_ends": True, "closed": True}),
        ]:
            result = command(
                "sweep1", {"rail_id": rail, "profile_ids": [profile], **options}
            )
            measured, repeat = artifact(name, result["result_ids"])
            if options.get("cap_planar_ends"):
                cases[name] = repeat and evaluate(measured)["status"] == "pass"
            else:
                objects = measured["objects"]
                cases[name] = (
                    repeat
                    and len(objects) == 1
                    and objects[0]["valid"]
                    and not objects[0]["solid"]
                    and objects[0]["naked_edges"] == 8
                    and evaluate(measured)["checks"]["bounds"]
                )
        open_profile = create("POLYLINE", {"points": [[90, 0, 0], [110, 0, 0]]})
        before_failure = fingerprint()
        error = None
        try:
            command(
                "sweep1",
                {
                    "rail_id": rail,
                    "profile_ids": [open_profile],
                    "cap_planar_ends": True,
                },
            )
        except Exception as caught:
            error = str(caught)
        reports[CASE_NAMES[4]] = {
            "error": error,
            "unchanged": fingerprint() == before_failure,
        }
        cases[CASE_NAMES[4]] = bool(
            error
            and "capping failed" in error.lower()
            and fingerprint() == before_failure
        )
        circle = create("CIRCLE", {"center": [0, 0, 0], "radius": 100})
        for name, options in [
            (CASE_NAMES[5], {}),
            (CASE_NAMES[6], {"cap_planar_ends": True}),
        ]:
            result = command(
                "sweep1", {"rail_id": circle, "profile_ids": [profile], **options}
            )
            measured, repeat = artifact(name, result["result_ids"])
            objects = measured["objects"]
            cases[name] = (
                repeat
                and len(objects) == 1
                and objects[0]["valid"]
                and objects[0]["solid"]
                and objects[0]["naked_edges"] == 0
            )
        reports["closed_rail_identical"] = (
            reports[CASE_NAMES[5]]["measurements"]
            == reports[CASE_NAMES[6]]["measurements"]
        )
        cases[CASE_NAMES[6]] = cases[CASE_NAMES[6]] and reports["closed_rail_identical"]
    finally:
        assert_document(owner["document"], owner["marker"])
        for identifier in created:
            if identifier in {obj["id"] for obj in before["objects"]}:
                raise RuntimeError("Refusing to delete pre-existing object")
            get_rhino_connection().send_command("delete_object", {"id": identifier})
        after = fingerprint()
        save(directory / "after.json", after)
        if before != after:
            raise RuntimeError("Sweep probe did not preserve document")
    save(
        directory / "result.json",
        {"cases": cases, "reports": reports, "document_preserved": True},
    )
    return cases
