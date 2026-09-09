import pytest

from experiments.trial import persist, read
from experiments.workflow import binary_compare as bc


def suite():
    return {
        "tasks": [{"path": "a", "family": "panels"}, {"path": "b", "family": "panels"}]
    }


def rows(plan):
    return [
        {
            "id": s["name"],
            "task": s["entry"]["path"],
            "arm": s["arm"],
            "task_verdict": "pass",
            "metrics": {"mcp_attempts": 4, "failed_calls": 0},
            "elapsed_seconds": 10,
        }
        for s in plan
    ]


def test_counterbalanced_schedule_and_incomplete_results():
    plan = bc.schedule(suite())
    assert [s["arm"] for s in plan] == [
        "baseline",
        "candidate",
        "candidate",
        "baseline",
    ] * 2
    assert bc.summarize(rows(plan)[:-1], plan)["status"] == "incomplete"
    assert bc.summarize(rows(plan)[::-1], plan)["status"] == "incomplete"
    assert bc.summarize(rows(plan), plan)["status"] == "no_benefit_established"


def test_pooled_success_cannot_hide_another_task_regression():
    plan = bc.schedule(suite())
    data = rows(plan)
    data[0]["task_verdict"] = "fail"  # candidate improves a
    data[5]["task_verdict"] = "fail"  # candidate regresses b
    result = bc.summarize(data, plan)
    assert result["tasks"]["a"]["observed_benefit"]
    assert result["tasks"]["b"]["correctness_regression"]
    assert result["status"] == "no_benefit_established"
    assert result["promotion_authorized"] is False


def test_failed_fast_cannot_pass_but_correctness_gain_is_reported():
    plan = bc.schedule(suite())
    data = rows(plan)
    data[1]["metrics"]["mcp_attempts"] = 1
    data[2]["metrics"]["mcp_attempts"] = 1
    data[1]["task_verdict"] = "fail"
    assert bc.summarize(data, plan)["status"] == "no_benefit_established"
    data = rows(plan)
    data[0]["task_verdict"] = "fail"
    assert bc.summarize(data, plan)["status"] == "benefit_observed"


def setup_run(tmp_path):
    baseline = {"mvid": "old", "sha256": "a"}
    candidate = {"mvid": "new", "sha256": "b"}
    persist(
        tmp_path / "contract.json",
        {
            "binaries": {
                "baseline": {"identity": baseline},
                "candidate": {"identity": candidate},
            }
        },
    )
    state = {
        "stage": "prepared",
        "runtime_dirty": False,
        "transitions": [],
        "rows": [],
        "contract_sha256": bc.sha256(tmp_path / "contract.json"),
    }
    persist(tmp_path / "state.json", state)
    return baseline, candidate


def test_install_records_dirty_before_side_effect_and_failure_retained(
    tmp_path, monkeypatch
):
    _, candidate = setup_run(tmp_path)
    monkeypatch.setattr(bc, "sha256", lambda p: candidate["sha256"])

    def lifecycle(request, path):
        assert read(tmp_path / "state.json")["runtime_dirty"] is True
        assert read(path)["expected_identity"] == candidate
        raise TimeoutError("operator absent")

    monkeypatch.setattr(bc.rhino_trial, "lifecycle", lifecycle)
    with pytest.raises(TimeoutError):
        bc.transition(tmp_path, "candidate")
    assert read(tmp_path / "state.json")["stage"] == "candidate_transition_pending"


def test_recovery_never_dispatches_candidate_or_replays_task(tmp_path, monkeypatch):
    baseline, _ = setup_run(tmp_path)
    state = read(tmp_path / "state.json")
    state.update(
        stage="candidate_transition_pending",
        runtime_dirty=True,
        active_session="interrupted",
    )
    persist(tmp_path / "state.json", state)
    transitions = []
    monkeypatch.setattr(bc, "transition", lambda d, arm: transitions.append(arm))
    monkeypatch.setattr(bc.rhino_trial, "probe", lambda d: baseline)
    monkeypatch.setattr(
        bc.rhino_trial, "runtime", lambda: {"object_count": 0, "marker": None}
    )
    monkeypatch.setattr(bc, "run_task", lambda *a: pytest.fail("replayed task"))
    bc.recover(tmp_path)
    assert transitions == ["baseline"]
    assert read(tmp_path / "state.json")["stage"] == "restored"
    assert read(tmp_path / "state.json")["active_session"] == "interrupted"


def test_wrong_binary_or_unfinished_work_cannot_complete_recovery(
    tmp_path, monkeypatch
):
    baseline, candidate = setup_run(tmp_path)
    monkeypatch.setattr(bc.rhino_trial, "probe", lambda d: candidate)
    with pytest.raises(RuntimeError, match="not verified"):
        bc.recover(tmp_path)
    monkeypatch.setattr(bc.rhino_trial, "probe", lambda d: baseline)
    monkeypatch.setattr(
        bc.rhino_trial, "runtime", lambda: {"object_count": 1, "marker": "unfinished"}
    )
    with pytest.raises(RuntimeError, match="cleanup"):
        bc.recover(tmp_path)


def test_changed_contract_blocks_recovery(tmp_path):
    setup_run(tmp_path)
    persist(tmp_path / "contract.json", {})
    with pytest.raises(RuntimeError, match="recovery contract"):
        bc.recover(tmp_path)


def test_frozen_artifact_and_source_changes_fail(tmp_path, monkeypatch):
    setup_run(tmp_path)
    (tmp_path / "task.json").write_text("original")
    persist(tmp_path / "pins.json", {})
    state = read(tmp_path / "state.json")
    state["frozen_files"] = {"task.json": bc.sha256(tmp_path / "task.json")}
    persist(tmp_path / "state.json", state)
    (tmp_path / "task.json").write_text("changed")
    with pytest.raises(RuntimeError, match="Frozen artifact"):
        bc.check_pins(tmp_path)


def test_catalog_extension_preserves_every_existing_definition():
    base = [{"name": "create_object", "description": "unchanged", "inputSchema": {}}]
    added = {"name": "create_planar_region", "inputSchema": {}}
    bc.catalog_extension(base, base + [added], ["create_planar_region"])
    with pytest.raises(ValueError):
        bc.catalog_extension(
            base,
            [{"name": "create_object", "description": "changed"}] + [added],
            ["create_planar_region"],
        )
    with pytest.raises(ValueError):
        bc.catalog_extension(base, base + [added], ["undeclared"])


def test_environment_compares_units_tolerance_and_layers_across_restarts(tmp_path):
    import copy

    env = dict(
        model={"model": "pinned"}, codex_version="1", call_budget=10, timeout_seconds=60
    )
    persist(tmp_path / "environment.json", env)
    before = dict(
        objects=[],
        units="Millimeters",
        tolerance=0.001,
        layers=[
            dict(
                Id="a",
                Name="Default",
                ParentLayerId="00000000-0000-0000-0000-000000000000",
                IsVisible=True,
                IsLocked=False,
            )
        ],
    )

    def put(value):
        persist(
            tmp_path / "preservation.json",
            dict(before=value, after=value, preserved=True),
        )

    put(before)
    original = bc.session_environment(tmp_path)
    changed = copy.deepcopy(before)
    changed["layers"][0]["Id"] = "new-runtime-id"
    put(changed)
    assert bc.session_environment(tmp_path) == original
    for key, value in [("units", "Meters"), ("tolerance", 0.1)]:
        changed = copy.deepcopy(before)
        changed[key] = value
        put(changed)
        assert bc.session_environment(tmp_path) != original
    persist(
        tmp_path / "preservation.json",
        dict(before=before, after=changed, preserved=True),
    )
    with pytest.raises(RuntimeError, match="preserve"):
        bc.session_environment(tmp_path)


def test_new_source_file_cannot_bypass_frozen_input_checks(tmp_path, monkeypatch):
    setup_run(tmp_path)
    persist(tmp_path / "pins.json", {})
    state = read(tmp_path / "state.json")
    state["frozen_files"] = {}
    persist(tmp_path / "state.json", state)
    monkeypatch.setattr(
        bc, "source_pins", lambda: {"server/src/rhinomcp/tools/added.py": "new"}
    )
    with pytest.raises(RuntimeError, match="Unpinned source additions"):
        bc.check_pins(tmp_path)
