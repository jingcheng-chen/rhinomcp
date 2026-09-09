"""Frozen layer-parent compatibility and failure checks for candidate comparison."""

import json
import uuid

from experiments.bridge import script, assert_document
from experiments.layer_probe import evaluate, measure
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import save, sha256
from experiments.strip_probe import fingerprint
from rhinomcp.server import get_rhino_connection

CASE_NAMES = [
    "layers/root",
    "layers/automatic_name",
    "layers/unique_short_parent",
    "layers/full_path_parent",
    "layers/saved_assembly",
    "layers/case_insensitive_path",
    "layers/missing_parent",
    "layers/ambiguous_parent",
    "layers/duplicate_sibling",
]


def run_checks(directory, owner):
    directory.mkdir()
    before = fingerprint()
    if before["objects"]:
        raise RuntimeError("Layer trial requires an empty owned document")
    prefix = "Trial_" + uuid.uuid4().hex[:10]
    objects, calls, cases = [], [], {}
    original_ids = {layer["Id"] for layer in before["layers"]}

    def guard():
        require_owned(runtime(), owner)
        assert_document(owner["document"], owner["marker"])

    def command(name, params):
        guard()
        try:
            result = get_rhino_connection().send_command(name, params)
            calls.append({"command": name, "params": params, "result": result})
        except Exception as exc:
            result = None
            calls.append({"command": name, "params": params, "error": str(exc)})
        save(directory / "calls.json", calls)
        return result

    def add(name=None, parent=None):
        return command(
            "create_layer",
            {
                **({"name": name} if name else {}),
                **({"parent": parent} if parent else {}),
            },
        )

    def rejected(name, parent, words):
        prior = fingerprint()
        result = add(name, parent)
        error = calls[-1].get("error", "").lower()
        return (
            result is None
            and any(word in error for word in words)
            and fingerprint() == prior
        )

    try:
        root = prefix + "Assembly"
        root_result = add(root)
        cases["layers/root"] = bool(
            root_result
            and root_result["parent"] == "00000000-0000-0000-0000-000000000000"
        )
        left, right = add("Left", root), add("Right", root)
        cases["layers/unique_short_parent"] = bool(
            root_result
            and left
            and right
            and left["parent"] == right["parent"] == root_result["id"]
        )
        task_ids = {r["id"] for r in (root_result, left, right) if r}
        children = [add("Part", root + "::" + side) for side in ("Left", "Right")]
        task_ids.update(r["id"] for r in children if r)
        cases["layers/full_path_parent"] = bool(
            left
            and right
            and all(children)
            and children[0]["parent"] == left["id"]
            and children[1]["parent"] == right["id"]
        )
        for i, side in enumerate(("Left", "Right")):
            obj = command(
                "create_object",
                {
                    "type": "BOX",
                    "name": side.lower() + "_part",
                    "params": {"width": 10, "length": 10, "height": 10},
                    "translation": [i * 30 + 5, 5, 5],
                },
            )
            if obj:
                objects.append(obj["id"])
                command(
                    "update_object_attributes",
                    {"id": obj["id"], "layer": root + "::" + side + "::Part"},
                )
        artifact = directory / "assembly.3dm"
        guard()
        script(
            f'if(!doc.WriteFile({json.dumps(str(artifact))},new Rhino.FileIO.FileWriteOptions())) throw new Exception("Save failed");'
        )
        first, second = measure(artifact), measure(artifact)
        # Evaluate every layer created for this assembly, including misplaced roots.
        # Pre-existing empty document layers are outside the task; object checks still
        # reject assignments to any layer outside the required assembly branches.
        selected = {
            **first,
            "layers": [layer for layer in first["layers"] if layer["id"] in task_ids],
        }
        report = evaluate(selected, root)
        report.update(
            repeat_identical=first == second,
            artifact_sha256=sha256(artifact),
            selected_layer_ids=sorted(task_ids),
            full_measurements=first,
        )
        save(directory / "assembly.json", report)
        cases["layers/saved_assembly"] = (
            report["status"] == "pass" and report["repeat_identical"]
        )
        for identifier in objects:
            if command("delete_object", {"id": identifier}) is None:
                raise RuntimeError("Object cleanup failed")
        objects.clear()
        automatic = add()
        cases["layers/automatic_name"] = bool(
            automatic
            and automatic["name"]
            and automatic["parent"] == "00000000-0000-0000-0000-000000000000"
        )
        case_child = add("CaseChild", (root + "::Left").swapcase())
        cases["layers/case_insensitive_path"] = bool(
            case_child and left and case_child["parent"] == left["id"]
        )
        cases["layers/missing_parent"] = rejected(
            prefix + "Missing",
            prefix + "::Absent",
            ["not found", "does not exist", "missing"],
        )
        other = add(prefix + "Other")
        duplicate_parent = add("Left", prefix + "Other")
        cases["layers/ambiguous_parent"] = bool(
            other and duplicate_parent
        ) and rejected(prefix + "Ambiguous", "Left", ["ambiguous", "multiple"])
        cases["layers/duplicate_sibling"] = rejected(
            "Left", root, ["already exists", "duplicate"]
        )
    finally:
        guard()
        for identifier in objects:
            command("delete_object", {"id": identifier})
        # Collect actual new IDs even if a failed command inserted an unexpected layer.
        # Never delete a pre-existing layer; do not assume failed insertion was atomic.
        state = fingerprint()
        new_ids = [
            layer["Id"] for layer in state["layers"] if layer["Id"] not in original_ids
        ]
        code = f"""
var ids=new HashSet<Guid>(new[]{{{",".join("new Guid(" + json.dumps(i) + ")" for i in new_ids)}}});
foreach(var layer in doc.Layers.Where(l=>!l.IsDeleted && ids.Contains(l.Id)).OrderByDescending(l=>l.FullPath.Split(new[]{{"::"}},StringSplitOptions.None).Length).ToArray())
 if(!doc.Layers.Delete(layer.Index,true)) throw new Exception("Layer cleanup failed");
"""
        if new_ids:
            script(code)
        after = fingerprint()
        save(
            directory / "preservation.json",
            {"before": before, "after": after, "preserved": before == after},
        )
        if before != after:
            raise RuntimeError("Layer checks changed pre-existing document")
    if set(cases) != set(CASE_NAMES):
        raise RuntimeError("Incomplete layer check vector")
    save(directory / "result.json", cases)
    return cases
