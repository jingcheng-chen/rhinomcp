import copy
import math

import pytest

from experiments.cushion_probe import evaluate, height
from experiments.layer_probe import ZERO


@pytest.fixture
def measured():
    return {
        "units": "Millimeters",
        "layers": [
            dict(
                id=str(i),
                index=i,
                parent=str(i - 1) if i else ZERO,
                name=name,
                visible=True,
                locked=False,
            )
            for i, name in enumerate(["Cushion", "Upholstery", "Top"])
        ],
        "objects": [
            dict(
                name="cushion_top",
                layer=2,
                visible=True,
                mode="Normal",
                valid=True,
                faces=1,
                untrimmed=True,
                solid=False,
                smooth=True,
                min=[0, 0, 10],
                max=[100, 100, 30],
                points=[
                    [i * 2.5, j * 2.5, height(i * 2.5, j * 2.5)]
                    for i in range(41)
                    for j in range(41)
                ],
                distances=[0] * 441,
            )
        ],
    }


def test_height_lobes_and_seams():
    peak = 100 * (3 - math.sqrt(3)) / 6
    assert height(peak, peak) == pytest.approx(30)
    assert height(50, peak) == 10
    assert height(0, peak) == 10


@pytest.mark.parametrize(
    "fault",
    [
        "flat",
        "nan",
        "missing_samples",
        "missing_coverage",
        "crease",
        "split",
        "hidden",
        "cycle",
        "assignment",
        "trim",
        "position",
    ],
)
def test_rejects_geometry_and_organization_faults(measured, fault):
    assert evaluate(measured)["status"] == "pass"
    data = copy.deepcopy(measured)
    obj = data["objects"][0]
    if fault == "flat":
        for p in obj["points"]:
            p[2] = 10
    elif fault == "nan":
        obj["points"][0][2] = float("nan")
    elif fault == "missing_samples":
        obj["points"].pop()
    elif fault == "missing_coverage":
        obj["distances"].pop()
    elif fault == "crease":
        obj["smooth"] = False
    elif fault == "split":
        data["objects"].append(copy.deepcopy(obj))
    elif fault == "hidden":
        data["layers"][1]["visible"] = False
    elif fault == "cycle":
        data["layers"][0]["parent"] = "2"
    elif fault == "assignment":
        obj["layer"] = 1
    elif fault == "trim":
        obj["untrimmed"] = False
    elif fault == "position":
        obj["min"][0] = 5
    assert evaluate(data)["status"] == "fail"


def test_shaded_capture_restores_modes_on_failure(monkeypatch, tmp_path):
    from experiments import model_screenshots as module

    calls = []

    def script(code):
        calls.append(code)
        return '[{"id":"00000000-0000-0000-0000-000000000001","mode":"00000000-0000-0000-0000-000000000002"}]'

    class Connection:
        def send_command(self, *args):
            raise RuntimeError("capture failed")

    monkeypatch.setattr(module, "script", script)
    monkeypatch.setattr(module, "assert_document", lambda *args: None)
    monkeypatch.setattr(module, "get_rhino_connection", Connection)
    with pytest.raises(RuntimeError, match="capture failed"):
        module.capture_shaded(tmp_path, 1, "owned")
    assert any(
        "00000000-0000-0000-0000-000000000002" in c and "GetDisplayMode(new Guid" in c
        for c in calls
    )
    assert "doc.Views.Redraw();" in calls
    assert (tmp_path / "display-modes-restored.json").exists()
