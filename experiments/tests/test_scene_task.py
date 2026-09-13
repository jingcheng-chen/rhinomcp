import copy
import math

import pytest
from experiments.runner import ROOT, load_task
from experiments.scene_task import evaluate, validate, response_schema
from experiments.workflow.pilot import load_suite


def task(name="edit_existing"):
    return load_task(ROOT / f"experiments/tasks/{name}.json")


def measurements(t):
    zero = "00000000-0000-0000-0000-000000000000"
    layers = []
    for index, name in enumerate(sorted(t["layers"], key=lambda s: (s.count("::"), s))):
        parent = name.rsplit("::", 1)[0] if "::" in name else None
        layers.append(
            {
                "id": name,
                "parent": parent or zero,
                "index": index,
                "name": name.split("::")[-1],
                "visible": True,
                "locked": False,
            }
        )
    indexes = {layer["id"]: layer["index"] for layer in layers}

    def row(p, id):
        a, b = p["min"], p["max"]
        return {
            "id": id,
            "name": p["name"],
            "layer": indexes[p["layer"]],
            "visible": True,
            "mode": "Normal",
            "valid": True,
            "solid": True,
            "planar_faces": True,
            "min": a,
            "max": b,
            "volume": math.prod(y - x for x, y in zip(a, b)),
            "vertices": [
                [x, y, z]
                for x in [a[0], b[0]]
                for y in [a[1], b[1]]
                for z in [a[2], b[2]]
            ],
            "geometry_crc": p["name"],
            "attributes": p["name"],
        }

    initial = [row(p, p["name"] + "-id") for p in t["initial"]]
    rows = [row(p, p.get("preserve_from", p["name"]) + "-id") for p in t["targets"]]
    return {
        "units": "Millimeters",
        "layers": layers,
        "objects": rows,
        "initial": {
            "units": "Millimeters",
            "layers": copy.deepcopy(layers),
            "objects": initial,
        },
        "inspection": [
            {k: o[k] for k in ["name", "min", "max", "volume"]}
            for o in rows
            if o["name"] in t["inspection_names"]
        ],
        "inspection_no_write_calls": True,
    }


@pytest.mark.parametrize(
    "name",
    ["edit_existing", "table_assembly", "inspect_document", "recover_intermediate"],
)
def test_registered_scene_passes_analytic_controls(name):
    t = task(name)
    assert evaluate(t, measurements(t))["status"] == "pass"


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate_name",
        "wrong_bounds",
        "volume",
        "corners",
        "invalid",
        "open",
        "hidden",
        "layer",
        "new_id",
        "changed_reference",
    ],
)
def test_existing_edit_rejects_independent_failures(fault):
    t = task()
    m = measurements(t)
    if fault == "missing":
        m["objects"].pop()
    elif fault == "duplicate_name":
        m["objects"].append(copy.deepcopy(m["objects"][0]))
    elif fault == "wrong_bounds":
        m["objects"][0]["min"] = [99, -40, 15]
    elif fault == "volume":
        m["objects"][0]["volume"] *= 0.9
    elif fault == "corners":
        m["objects"][0]["vertices"] = m["objects"][0]["vertices"][:4]
    elif fault == "invalid":
        m["objects"][0]["valid"] = False
    elif fault == "open":
        m["objects"][0]["solid"] = False
    elif fault == "hidden":
        m["objects"][0]["visible"] = False
    elif fault == "layer":
        m["objects"][0]["layer"] = 100
    elif fault == "new_id":
        m["objects"][0]["id"] = "recreated"
    else:
        m["objects"][1]["geometry_crc"] = "changed"
    assert evaluate(t, m)["status"] == "fail"


@pytest.mark.parametrize(
    "fault", ["volume", "bounds", "missing_report", "write", "attributes"]
)
def test_inspection_requires_true_measurements_and_preservation(fault):
    t = task("inspect_document")
    m = measurements(t)
    if fault == "volume":
        m["inspection"][0]["volume"] *= 2
    elif fault == "bounds":
        m["inspection"][0]["max"] = [0, 0, 0]
    elif fault == "missing_report":
        m["inspection"] = []
    elif fault == "write":
        m["inspection_no_write_calls"] = False
    else:
        m["objects"][0]["attributes"] = "changed"
    assert evaluate(t, m)["status"] == "fail"


def test_old_intermediate_identity_cannot_be_reused():
    t = task("recover_intermediate")
    m = measurements(t)
    m["objects"][0]["id"] = m["initial"]["objects"][0]["id"]
    assert evaluate(t, m)["checks"]["wrong_intermediate_removed"] is False


@pytest.mark.parametrize(
    "fault",
    [
        "nan",
        "negative",
        "unknown_identity",
        "unknown_layer",
        "missing_parent",
        "unchanged_without_id",
    ],
)
def test_bad_scene_contract_refused(fault):
    t = task()
    if fault == "nan":
        t["targets"][0]["min"][0] = float("nan")
    elif fault == "negative":
        t["targets"][0]["max"] = t["targets"][0]["min"]
    elif fault == "unknown_identity":
        t["targets"][0]["preserve_from"] = "missing"
    elif fault == "unknown_layer":
        t["targets"][0]["layer"] = "missing"
    elif fault == "missing_parent":
        t["layers"].append("Missing::Child")
    else:
        t["targets"][0].pop("preserve_from")
        t["targets"][0]["unchanged"] = True
    with pytest.raises(ValueError):
        validate(t)


def test_shared_pilot_and_structured_inspection_schema():
    suite = load_suite(ROOT / "experiments/workflow/m2-pilot.json")
    assert len({e["family"] for e in suite["tasks"]}) == 4
    assert "inspection" in response_schema()["required"]


@pytest.mark.parametrize("tamper", [None, "metadata", "artifact"])
def test_initial_evidence_is_hash_bound(tmp_path, tamper):
    import json
    from experiments.runner import sha256
    from experiments.scene_task import evaluation_context

    initial = tmp_path / "initial.3dm"
    initial.write_bytes(b"saved prepared scene")
    metadata = tmp_path / "initial.json"
    metadata.write_text(
        json.dumps({"sha256": sha256(initial), "measurements": {"objects": []}})
    )
    (tmp_path / "artifact.json").write_text(
        json.dumps({"initial_metadata_sha256": sha256(metadata)})
    )
    (tmp_path / "modeler").mkdir()
    (tmp_path / "modeler/result.json").write_text('{"inspection": []}')
    (tmp_path / "calls.jsonl").write_text('{"tool": "get_objects"}\n')
    if tamper == "metadata":
        metadata.write_text(metadata.read_text() + " ")
    elif tamper == "artifact":
        initial.write_bytes(b"replaced")
    definitions = [{"name": "get_objects", "annotations": {"readOnlyHint": True}}]
    if tamper:
        with pytest.raises(RuntimeError, match="changed"):
            evaluation_context(tmp_path, {}, definitions)
    else:
        assert (
            evaluation_context(tmp_path, {}, definitions)["inspection_no_write_calls"]
            is True
        )
        (tmp_path / "calls.jsonl").write_text('{"tool": "modify_object"}\n')
        assert (
            evaluation_context(tmp_path, {}, definitions)["inspection_no_write_calls"]
            is False
        )


def test_rectangle_curve_saved_calibration_verdicts():
    import json

    p = ROOT / "experiments/workflow/m3-curve-calibration.json"
    result = json.loads(p.read_text())
    assert (
        result["fixtures"] == 7 and result["unexpected"] == [] and result["preserved"]
    )
    for row in result["results"]:
        assert row["repeat_identical"] and row["actual"] == row["expected"]


def test_rectangle_curve_rejects_nonplanar_task_bounds():
    t = load_task(ROOT / "experiments/tasks/offset_outline.json")
    t["targets"][1]["max"][2] = 1
    with pytest.raises(ValueError):
        validate(t)
