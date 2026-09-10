import copy
import json

import pytest

from experiments.workflow import held_out as bank


def bundle(key="joining", family="curve-network-joining"):
    return {
        "id": key,
        "family": family,
        "novelty_review": "Synthetic test family absent from the supplied discovery set.",
        "calibration_required": True,
        "cases": [
            {
                "id": f"case-{i}",
                "instruction": "Synthetic fixture",
                "parameters": {"length": 10 + i},
                "acceptance": ["Preserve inputs"],
            }
            for i in range(2)
        ],
    }


@pytest.fixture
def setup(tmp_path):
    path, vault = tmp_path / "bank.json", tmp_path / "private"
    bank.initialize(path, ["primitives", "document-inspection"])
    review = tmp_path / "review.md"
    review.write_text("Frozen independent validation plan, before exposure")
    return path, vault, review


def test_seal_status_hides_parameters_and_missing_vault_is_not_ready(setup, tmp_path):
    path, vault, _ = setup
    bank.seal(path, vault, bundle())
    result = bank.status(path, vault)
    assert result["ready_families"] == 1
    assert "length" not in path.read_text()
    assert "instruction" not in path.read_text()
    assert bank.status(path, tmp_path / "missing")["ready_families"] == 0
    assert (vault / "joining.json").stat().st_mode & 0o777 == 0o600


def test_spend_before_export_failure_cannot_be_undone_or_reallocated(setup, tmp_path):
    path, vault, review = setup
    bank.seal(path, vault, bundle())
    output = tmp_path / "already-exists"
    output.write_text("do not overwrite")
    with pytest.raises(FileExistsError):
        bank.expose(path, vault, "joining", "cycle-a", output, review)
    assert bank.status(path, vault)["entries"]["joining"]["state"] == "spent"
    assert output.read_text() == "do not overwrite"
    with pytest.raises(ValueError):
        bank.expose(path, vault, "joining", "cycle-b", tmp_path / "wrong", review)
    with pytest.raises(ValueError):
        bank.expose(path, vault, "joining", "cycle-b", tmp_path / "wrong")
    bank.expose(path, vault, "joining", "cycle-a", tmp_path / "recovered")
    assert (tmp_path / "recovered").read_bytes() == (
        vault / "joining.json"
    ).read_bytes()


def test_second_family_in_same_validation_refused(setup, tmp_path):
    path, vault, review = setup
    bank.seal(path, vault, bundle())
    bank.seal(path, vault, bundle("blocks", "instance-block-reuse"))
    bank.expose(path, vault, "joining", "cycle-a", tmp_path / "a", review)
    with pytest.raises(ValueError):
        bank.expose(path, vault, "blocks", "cycle-a", tmp_path / "b", review)
    assert bank.status(path, vault)["entries"]["blocks"]["state"] == "available"


@pytest.mark.parametrize("outcome", ["kept", "rejected", "incomplete", "abandoned"])
def test_closure_requires_replacement_and_never_restores_spent_family(
    setup, tmp_path, outcome
):
    path, vault, review = setup
    bank.seal(path, vault, bundle())
    bank.expose(path, vault, "joining", "cycle-a", tmp_path / "opened", review)
    with pytest.raises(ValueError, match="replacement"):
        bank.close(path, "joining", outcome, review)
    bank.seal(path, vault, bundle("blocks", "instance-block-reuse"), replaces="joining")
    bank.close(path, "joining", outcome, review)
    status = bank.status(path, vault)
    assert status["entries"]["joining"]["state"] == "spent"
    assert status["entries"]["joining"]["closure"]["outcome"] == outcome
    assert status["ready_families"] == 1
    with pytest.raises(ValueError):
        bank.close(path, "joining", outcome, review)
    with pytest.raises(ValueError):
        bank.expose(path, vault, "joining", "cycle-a", tmp_path / "late-export")


def test_changed_private_payload_or_public_history_is_rejected(setup, tmp_path):
    path, vault, review = setup
    bank.seal(path, vault, bundle())
    private = vault / "joining.json"
    private.write_bytes(private.read_bytes() + b" ")
    with pytest.raises(ValueError, match="changed"):
        bank.expose(path, vault, "joining", "cycle-a", tmp_path / "output", review)
    assert not (tmp_path / "output").exists()
    events = json.loads(path.read_text())
    events[0]["body"]["discovery_families"] = []
    path.write_text(json.dumps(events))
    with pytest.raises(ValueError, match="hash"):
        bank.read(path)


def test_discovery_overlap_renaming_and_invalid_parameters_refused(setup):
    path, vault, _ = setup
    with pytest.raises(ValueError):
        bank.seal(path, vault, bundle(family="primitives"))
    bank.seal(path, vault, bundle())
    with pytest.raises(ValueError):
        bank.seal(path, vault, bundle("renamed"))
    invalid = bundle("other", "new-family")
    invalid["cases"][0]["parameters"]["length"] = float("nan")
    with pytest.raises(ValueError):
        bank.seal(path, vault, invalid)
    invalid = copy.deepcopy(bundle("../escape", "new-family"))
    with pytest.raises(ValueError):
        bank.seal(path, vault, invalid)


def test_concurrent_writer_is_refused_and_genesis_cannot_be_replaced(setup):
    path, vault, _ = setup
    with bank.locked(path):
        with pytest.raises(BlockingIOError):
            bank.seal(path, vault, bundle())
    with pytest.raises(ValueError):
        bank.initialize(path, ["replacement-history"])


def test_invalid_replacement_does_not_leave_private_orphan(setup):
    path, vault, _ = setup
    with pytest.raises(ValueError):
        bank.seal(path, vault, bundle(), replaces="absent")
    assert not (vault / "joining.json").exists()
    bank.seal(path, vault, bundle())
    with pytest.raises(ValueError):
        bank.seal(
            path, vault, bundle("blocks", "instance-block-reuse"), replaces="joining"
        )
    assert not (vault / "blocks.json").exists()


def test_closing_needs_a_still_available_replacement(setup, tmp_path):
    path, vault, review = setup
    bank.seal(path, vault, bundle())
    bank.expose(path, vault, "joining", "cycle-a", tmp_path / "a", review)
    bank.seal(path, vault, bundle("blocks", "instance-block-reuse"), replaces="joining")
    bank.expose(path, vault, "blocks", "cycle-b", tmp_path / "b", review)
    with pytest.raises(ValueError, match="replacement"):
        bank.close(path, "joining", "kept", review)


@pytest.mark.parametrize("damage", ["missing", "changed"])
def test_lost_or_changed_bundle_can_be_retired_without_export(setup, tmp_path, damage):
    path, vault, review = setup
    bank.seal(path, vault, bundle())
    private = vault / "joining.json"
    if damage == "missing":
        private.unlink()
    else:
        private.write_text("changed")
    assert bank.status(path, vault)["ready_families"] == 0
    bank.retire(path, "joining", "incident-a", review)
    assert bank.read(path)[1]["joining"]["retired"] is True
    private.write_bytes(bank.payload(bundle()))
    with pytest.raises(ValueError):
        bank.expose(path, vault, "joining", "incident-a", tmp_path / "output")
    assert not (tmp_path / "output").exists()
