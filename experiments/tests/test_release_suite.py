"""Pre-run declarations for the released baseline, without spending live cases."""

import math

import pytest

from experiments.runner import ROOT, load_task
from experiments.workflow.pilot import load_suite


def test_released_suite_has_five_families_and_versioned_tolerances():
    suite = load_suite(ROOT / "experiments/workflow/release-pilot.json")
    assert {entry["family"] for entry in suite["tasks"]} == {
        "primitives",
        "subtractive-solids",
        "posed-solids",
        "trimmed-patches",
        "curved-panels",
    }
    for entry in suite["tasks"]:
        assert entry["path"].endswith("_v2.json")
        task = load_task(ROOT / entry["path"])
        assert task["id"].endswith("-v2")
        assert task["linear_tolerance"] == 0.001
        w, d, h = task["dimensions"]
        if task["type"] == "biquadratic_panel":
            assert task["shape_tolerance"] == 0.005 * max(task["dimensions"])
        elif task["type"] == "trimmed_planar_patch":
            assert task["area_tolerance"] == pytest.approx(
                0.01 * (w * d - math.pi * task["hole_radius"] ** 2)
            )
        else:
            volume = w * d * h
            if task["type"] == "triangular_prism_pose":
                volume /= 2
            elif task["type"] == "box_through_hole":
                volume -= math.pi * task["hole_radius"] ** 2 * h
            assert task["volume_tolerance"] == pytest.approx(volume * 0.01)
    assert all("precision" not in entry["path"] for entry in suite["tasks"])


def test_other_redeclared_surfaces_remain_loadable():
    for name in [
        "panel_depressed",
        "trimmed_reserved",
        "unseen_shallow_panel",
        "unseen_steep_patch",
    ]:
        task = load_task(ROOT / f"experiments/tasks/{name}_v2.json")
        assert task["id"].endswith("-v2")
        assert task["linear_tolerance"] == 0.001
