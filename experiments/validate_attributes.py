"""Controller-only attribute contract probes; preserve each response and saved state."""

import json
import time
from experiments.bridge import script, assert_document
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import ROOT, save, save_candidate
from experiments.scene_task import creation_code, measure
from experiments.strip_probe import fingerprint
from experiments.trial import locked
from rhinomcp.server import get_rhino_connection


def run():
    directory = (
        ROOT / "experiments/runs" / time.strftime("attribute-probe-%Y%m%d-%H%M%S")
    )
    directory.mkdir()
    cases = [
        ("layer", {"layer": "Layer 01"}, {"layer": "Layer 01"}),
        (
            "rename_color",
            {"new_name": "renamed", "color": [13, 27, 91]},
            {"name": "renamed", "color": [13, 27, 91]},
        ),
        (
            "strings",
            {
                "user_strings": {
                    "text": 'quoted "value"',
                    "integer": 42,
                    "decimal": 1.25,
                    "true": True,
                    "false": False,
                    "remove": None,
                }
            },
            {
                "strings": {
                    "text": 'quoted "value"',
                    "integer": "42",
                    "decimal": "1.25",
                    "true": "true",
                    "false": "false",
                }
            },
        ),
        ("remove", {"delete_user_strings": ["old"]}, {"strings": {}}),
        ("clear", {"clear_user_strings": True}, {"strings": {}}),
        ("hide", {"visible": False}, {"mode": "Hidden"}),
        ("lock", {"locked": True}, {"mode": "Locked"}),
        ("material_from_layer", {"material_index": -1}, {"material": -1}),
        ("reject_array", {"user_strings": {"a": [1]}}, {"error": True}),
        ("reject_object", {"user_strings": {"a": {"x": 1}}}, {"error": True}),
        ("reject_hidden_locked", {"visible": False, "locked": True}, {"error": True}),
        ("reject_missing_layer", {"layer": "DefinitelyAbsent"}, {"error": True}),
        ("reject_material", {"material_index": 99999}, {"error": True}),
        ("reject_no_updates", {}, {"error": True}),
    ]
    results = []
    with locked(ROOT / "experiments/runs/rhino.lock"):
        owner = runtime()
        require_owned(owner, owner)
        if owner["object_count"] or owner["marker"]:
            raise RuntimeError("Empty unclaimed document required")
        before = fingerprint()
        marker = directory.name
        script(
            'doc.Strings.SetString("rhinomcp_experiment",' + json.dumps(marker) + ");"
        )
        try:
            for name, params, expected in cases:
                part = {
                    "name": "probe",
                    "layer": "Default",
                    "min": [0, 0, 0],
                    "max": [10, 20, 30],
                }
                script(creation_code([part]))
                old = json.loads(
                    script(
                        'var o=doc.Objects.First(x=>x.Attributes.Name=="probe");var a=o.Attributes.Duplicate();a.SetUserString("old","value");doc.Objects.ModifyAttributes(o.Id,a,true);output.AppendLine(Serialize(new {id=o.Id.ToString(),crc=o.Geometry.DataCRC(0)}));'
                    )
                )
                assert_document(owner["document"], marker)
                result = None
                error = None
                try:
                    result = get_rhino_connection().send_command(
                        "update_object_attributes", {"id": old["id"], **params}
                    )
                except Exception as exc:
                    error = str(exc)
                digest = save_candidate(
                    directory / (name + ".3dm"), owner["document"], marker
                )
                saved = measure(directory / (name + ".3dm"))["objects"][0]
                attrs = json.loads(
                    script(
                        "var o=doc.Objects.FindId(new Guid("
                        + json.dumps(old["id"])
                        + "));var a=o.Attributes;output.AppendLine(Serialize(new {name=a.Name,layer=doc.Layers[a.LayerIndex].FullPath,color=new int[]{a.ObjectColor.R,a.ObjectColor.G,a.ObjectColor.B},mode=a.Mode.ToString(),material=a.MaterialIndex,strings=a.GetUserStrings().AllKeys.ToDictionary(k=>k,k=>a.GetUserString(k))}));"
                    )
                )
                if name == "strings":
                    expected["strings"]["old"] = "value"
                checks = {
                    "geometry_identity": saved["id"] == old["id"]
                    and saved["geometry_crc"] == old["crc"],
                    "response": bool(error) == expected.get("error", False),
                }
                checks.update(
                    {k: attrs[k] == v for k, v in expected.items() if k != "error"}
                )
                results.append(
                    {
                        "case": name,
                        "params": params,
                        "expected": expected,
                        "response": result,
                        "error": error,
                        "attributes": attrs,
                        "checks": checks,
                        "pass": all(checks.values()),
                        "artifact_sha256": digest,
                    }
                )
                script(
                    "var o=doc.Objects.FindId(new Guid("
                    + json.dumps(old["id"])
                    + '));doc.Objects.Unlock(o.Id,true);doc.Objects.Show(o.Id,true);if(!doc.Objects.Delete(o.Id,true))throw new Exception("Cleanup failed");'
                )
        finally:
            assert_document(owner["document"], marker)
            script('doc.Strings.Delete("rhinomcp_experiment");')
            after = fingerprint()
            save(
                directory / "preservation.json",
                {"before": before, "after": after, "preserved": before == after},
            )
        save(
            directory / "summary.json",
            {
                "runtime": owner,
                "results": results,
                "passes": sum(r["pass"] for r in results),
                "total": len(results),
                "preserved": before == after,
            },
        )
    return directory


if __name__ == "__main__":
    print(run())
