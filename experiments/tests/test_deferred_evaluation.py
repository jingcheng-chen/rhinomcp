import pytest

from experiments.runner import sha256
from experiments.trial import persist, read
from experiments.workflow import pilot


def pending(tmp_path, monkeypatch):
    (tmp_path / "candidate.3dm").write_bytes(b"frozen model")
    (tmp_path / "baseline.rhp").write_bytes(b"trusted binary")
    persist(tmp_path / "task.json", {"id": "test", "type": "axis_aligned_box"})
    persist(tmp_path / "pins.json", {"judge": "fixed"})
    persist(
        tmp_path / "summary.json",
        {
            "status": "evaluation_pending",
            "modeler": {"complete": True},
            "promotion_authorized": False,
        },
    )
    persist(
        tmp_path / "artifact.json",
        {
            "sha256": sha256(tmp_path / "candidate.3dm"),
            "task_sha256": sha256(tmp_path / "task.json"),
            "evaluation_pending": True,
        },
    )
    identity = {"mvid": "baseline", "sha256": sha256(tmp_path / "baseline.rhp")}
    runtime = {
        "pid": 2,
        "document": 1,
        "mvid": "baseline",
        "assembly": str(tmp_path / "baseline.rhp"),
        "object_count": 0,
        "marker": None,
        "docs": [{}],
        "path": None,
    }
    monkeypatch.setattr(pilot, "source_pins", lambda: {"judge": "fixed"})
    monkeypatch.setattr(pilot, "runtime", lambda: dict(runtime))
    monkeypatch.setattr(pilot, "fingerprint", lambda: {"empty": True})
    monkeypatch.setattr(pilot, "measure", lambda p, t: {"independent": True})
    monkeypatch.setattr(
        pilot,
        "evaluate",
        lambda t, m: {
            "status": "fail",
            "checks": {"correct": False},
            "measurements": m,
        },
    )
    return identity, runtime


def test_saved_verdict_overrides_agent_claim_in_trusted_process(tmp_path, monkeypatch):
    identity, _ = pending(tmp_path, monkeypatch)
    result = pilot.evaluate_saved(tmp_path, identity)
    assert result["status"] == "fail"
    assert result["evaluation_runtime"]["pid"] == 2
    assert read(tmp_path / "summary.json")["status"] == "fail"
    assert not read(tmp_path / "artifact.json")["evaluation_pending"]
    with pytest.raises(RuntimeError, match="not pending"):
        pilot.evaluate_saved(tmp_path, identity)


@pytest.mark.parametrize("changed", ["artifact", "task", "sources", "binary", "work"])
def test_untrusted_or_changed_evaluation_rejected(tmp_path, monkeypatch, changed):
    identity, runtime = pending(tmp_path, monkeypatch)
    if changed == "artifact":
        (tmp_path / "candidate.3dm").write_bytes(b"changed")
    if changed == "task":
        persist(tmp_path / "task.json", {"changed": True})
    if changed == "sources":
        monkeypatch.setattr(pilot, "source_pins", lambda: {"judge": "changed"})
    if changed == "binary":
        runtime["mvid"] = "candidate"
    if changed == "work":
        runtime["object_count"] = 1
    with pytest.raises(RuntimeError):
        pilot.evaluate_saved(tmp_path, identity)
    assert not (tmp_path / "evaluation.json").exists()


def test_measurement_side_effect_cannot_produce_a_verdict(tmp_path, monkeypatch):
    identity, _ = pending(tmp_path, monkeypatch)

    def measure(path, task):
        path.write_bytes(b"changed during measurement")
        return {}

    monkeypatch.setattr(pilot, "measure", measure)
    with pytest.raises(RuntimeError, match="environment or artifact changed"):
        pilot.evaluate_saved(tmp_path, identity)
    assert not (tmp_path / "evaluation.json").exists()


def test_failed_model_is_retained_unscored_without_replacing_evidence(
    tmp_path, monkeypatch
):
    _, owner = pending(tmp_path, monkeypatch)
    monkeypatch.setattr(pilot, "assert_document", lambda *a: None)

    def save_model(path, *args):
        path.write_bytes(b"partial work")
        return sha256(path)

    monkeypatch.setattr(pilot, "save_candidate", save_model)
    monkeypatch.setattr(pilot, "capture", lambda *a: None)
    pilot.retain_failed_model(tmp_path, owner, "owned")
    assert (tmp_path / "failed-artifact/partial.3dm").read_bytes() == b"partial work"
    assert read(tmp_path / "failed-artifact/artifact.json")["scored"] is False
    assert (tmp_path / "candidate.3dm").read_bytes() == b"frozen model"
    with pytest.raises(FileExistsError):
        pilot.retain_failed_model(tmp_path, owner, "owned")
    assert not (tmp_path / "evaluation.json").exists()


def test_failed_model_cannot_snapshot_foreign_document(tmp_path, monkeypatch):
    _, owner = pending(tmp_path, monkeypatch)
    owner = {**owner, "document": 99}
    with pytest.raises(RuntimeError, match="not owned"):
        pilot.retain_failed_model(tmp_path, owner, "owned")
    assert not (tmp_path / "failed-artifact").exists()
