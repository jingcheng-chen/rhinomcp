import json
from pathlib import Path

import pytest
from experiments.runner import save, sha256
from experiments.visual_runner import freeze_references, structural_report
from experiments import visual_mcp


def test_only_frozen_public_images_are_copied(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "front.png").write_bytes(b"public screenshot")
    (source / "held-out.png").write_bytes(b"private screenshot")
    save(
        source / "public.json",
        {
            "views": {
                "front": {"file": "front.png", "sha256": sha256(source / "front.png")}
            }
        },
    )
    target = tmp_path / "target"
    freeze_references(source, target, ["front"])
    assert {p.name for p in target.iterdir()} == {"public.json", "front.png"}


@pytest.mark.parametrize("fault", ["traversal", "hash", "extra_view"])
def test_reference_pack_rejects_invalid_boundaries(tmp_path, fault):
    source = tmp_path / "source"
    source.mkdir()
    (source / "front.png").write_bytes(b"png")
    save(
        source / "public.json",
        {
            "views": {
                "front": {
                    "file": "../front.png" if fault == "traversal" else "front.png",
                    "sha256": "bad"
                    if fault == "hash"
                    else sha256(source / "front.png"),
                }
            }
        },
    )
    with pytest.raises(ValueError):
        freeze_references(
            source,
            tmp_path / "target",
            ["front", "back"] if fault == "extra_view" else ["front"],
        )


@pytest.mark.parametrize("view", ["../held-out", "held-out", "front.png"])
def test_gateway_cannot_read_undeclared_reference(tmp_path, monkeypatch, view):
    save(tmp_path / "public.json", {"views": {}})
    monkeypatch.setenv("EXPERIMENT_REFERENCE_DIR", str(tmp_path))
    with pytest.raises(ValueError):
        visual_mcp.reference_bytes(view)


def test_review_gateway_rejects_modeling_even_if_tool_is_called(monkeypatch):
    monkeypatch.setattr(visual_mcp, "guard", lambda: None)
    monkeypatch.setenv("EXPERIMENT_READ_ONLY", "1")
    with pytest.raises(RuntimeError, match="cannot execute"):
        visual_mcp.modeling_command("create_object", {})


def test_arbitrary_execution_is_outside_gateway(monkeypatch):
    monkeypatch.setattr(visual_mcp, "guard", lambda: None)
    with pytest.raises(ValueError, match="outside"):
        visual_mcp.modeling_command(
            "execute_rhinocommon_csharp_code", {"code": "anything"}
        )


def test_valid_organized_geometry_does_not_pass_visual_acceptance():
    task = json.loads(
        (Path(__file__).parents[1] / "visual_tasks/barcelona_chair.json").read_text()
    )
    measured = {
        "units": "Millimeters",
        "dimensions": [1000, 900, 1100],
        "objects": [
            {"name": p + "part", "valid": True, "type": "Brep"}
            for p in task["part_prefixes"]
        ],
    }
    report = structural_report(task, measured)
    assert all(report["structural_checks"].values())
    assert report["status"] == "unscored"
    measured["objects"] = []
    assert not structural_report(task, measured)["structural_checks"]["nonempty"]
