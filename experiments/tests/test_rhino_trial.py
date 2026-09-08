import pytest

from experiments.rhino_trial import require_owned, fixture_verdicts


def state(**values):
    return {"pid": 10, "document": 20, "path": None, "docs": [{}], **values}


@pytest.mark.parametrize(
    "change",
    [
        {"pid": 11},
        {"document": 21},
        {"path": "user.3dm"},
        {"docs": [{}, {}]},
    ],
)
def test_refuses_unowned_runtime_or_unrelated_document(change):
    with pytest.raises(RuntimeError):
        require_owned(state(**change), {"pid": 10, "document": 20})


def test_fixture_failure_is_expected_only_for_negative_cases():
    cases = fixture_verdicts(
        "box",
        {
            "correct": {"status": "pass", "repeat_identical": True},
            "wrong_scale": {"status": "fail", "repeat_identical": True},
            "wrong_position": {"status": "pass", "repeat_identical": True},
            "open_surface": {"status": "fail", "repeat_identical": False},
        },
    )
    assert cases == {
        "geometry/box/correct": True,
        "geometry/box/wrong_scale": True,
        "geometry/box/wrong_position": False,
        "geometry/box/open_surface": False,
    }


@pytest.mark.parametrize("fault", ["wrong_ack", "same_process", "wrong_binary", "none"])
def test_lifecycle_requires_matching_handoff_and_restarted_binary(
    tmp_path, monkeypatch, fault
):
    from experiments import rhino_trial
    from experiments.runner import save, sha256

    expected = {"sha256": "expected", "mvid": "candidate"}
    from types import SimpleNamespace

    disconnected = []
    monkeypatch.setattr(
        rhino_trial,
        "get_rhino_connection",
        lambda: SimpleNamespace(disconnect=lambda: disconnected.append(True)),
    )
    before = state(object_count=0, docs=[{"modified": False}])
    monkeypatch.setattr(rhino_trial, "runtime", lambda: before)
    save(tmp_path / "runtime-owner.json", {"pid": 10, "document": 20})
    request = {
        "trial": str(tmp_path),
        "action": "install",
        "candidate_binary": "candidate.rhp",
        "expected_identity": expected,
    }
    request_path = tmp_path / "request.json"
    save(request_path, request)
    save(
        tmp_path / "request-ack.json",
        {"request_sha256": "wrong" if fault == "wrong_ack" else sha256(request_path)},
    )

    def claim_after_disconnect(_):
        assert disconnected == [True]
        return {"pid": 10 if fault == "same_process" else 11}

    monkeypatch.setattr(rhino_trial, "claim_empty", claim_after_disconnect)
    monkeypatch.setattr(
        rhino_trial,
        "probe",
        lambda _: {"sha256": "wrong"} if fault == "wrong_binary" else expected,
    )
    if fault == "none":
        assert rhino_trial.lifecycle(request, request_path) == {
            "restarted": True,
            "pid": 11,
        }
    else:
        with pytest.raises((RuntimeError, ValueError)):
            rhino_trial.lifecycle(request, request_path)


def test_stopped_rhino_can_request_supervised_restoration(tmp_path, monkeypatch):
    from experiments import rhino_trial
    from experiments.runner import save, sha256

    def stopped():
        raise ConnectionError("Dedicated Rhino has stopped")

    expected = {"sha256": "baseline", "mvid": "baseline"}
    monkeypatch.setattr(rhino_trial, "runtime", stopped)
    save(tmp_path / "runtime-owner.json", {"pid": 10, "document": 20})
    request = {
        "trial": str(tmp_path),
        "action": "restore",
        "baseline_binary": "baseline.rhp",
        "expected_identity": expected,
    }
    path = tmp_path / "request.json"
    save(path, request)
    save(tmp_path / "request-ack.json", {"request_sha256": sha256(path)})
    monkeypatch.setattr(rhino_trial, "claim_empty", lambda _: {"pid": 11})
    monkeypatch.setattr(rhino_trial, "probe", lambda _: expected)
    assert rhino_trial.lifecycle(request, path)["restarted"] is True


def test_host_pixel_scan_preserves_strict_rgb_threshold(tmp_path):
    from PIL import Image
    from experiments.validate_capture import pixel_bounds

    image = Image.new("RGB", (4, 3), "white")
    image.putpixel((1, 1), (79, 79, 79))
    image.putpixel((2, 1), (0, 80, 0))
    path = tmp_path / "pixels.png"
    image.save(path)
    assert pixel_bounds(path) == {
        "left": 1,
        "right": 1,
        "top": 1,
        "bottom": 1,
        "count": 1,
        "width": 4,
        "height": 3,
    }
    image = Image.new("RGB", (4, 3), "white")
    image.save(path)
    assert pixel_bounds(path) == {
        "left": 4,
        "right": -1,
        "top": 3,
        "bottom": -1,
        "count": 0,
        "width": 4,
        "height": 3,
    }


def test_surface_trial_preserves_contract_and_known_baseline_failures():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    old = json.loads((root / "harness/trial-preservation-v3.json").read_text())
    new = json.loads((root / "harness/trial-surface-feedback.json").read_text())
    baseline = json.loads(
        (root / "workflow/surface-feedback-baseline.json").read_text()
    )["results"]
    surface = {
        f"surface/{name}/{check}": passed
        for name, result in baseline.items()
        for check, passed in result["checks"].items()
    }
    assert len(surface) == 19
    assert len(new["cases"]) == len(set(new["cases"])) == 80
    assert set(new["cases"]) == set(old["cases"]) | set(surface)
    assert new["baseline_expectations"] == {
        key: value for key, value in surface.items() if not value
    }
    assert len(new["baseline_expectations"]) == 8
    assert set(old["inputs"]) <= set(new["inputs"])
    assert "../surface_feedback_probe.py" in new["inputs"]
