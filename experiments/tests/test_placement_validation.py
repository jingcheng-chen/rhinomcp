import json
from experiments.runner import ROOT, load_task, sha256
from experiments.workflow.pilot import load_suite


def test_reserved_cases_change_dimensions_and_offsets_without_changing_judge():
    discovery = load_suite(ROOT / "experiments/workflow/pilot.json")
    validation = load_suite(
        ROOT / "experiments/workflow/placement-validation-suite.json"
    )
    assert len(validation["tasks"]) == 2
    for old, new in zip(discovery["tasks"], validation["tasks"], strict=True):
        a, b = load_task(ROOT / old["path"]), load_task(ROOT / new["path"])
        assert old["family"] == new["family"]
        assert a["type"] == b["type"]
        assert a["id"] != b["id"]
        assert a["dimensions"] != b["dimensions"]
        assert a["minimum"] != b["minimum"]
        assert all(
            a[k] == b[k] for k in ("units", "linear_tolerance", "volume_tolerance")
        )


def test_validation_keeps_the_discovery_candidate_and_agent():
    folder = ROOT / "experiments/workflow"
    original = json.loads((folder / "placement-trial.json").read_text())
    validation = json.loads((folder / "placement-validation-trial.json").read_text())
    pins = json.loads((folder / "placement-input-pins.json").read_text())
    assert validation["agent"] == original["agent"]
    assert validation["description_suffix"] == original["description_suffix"]
    assert validation["repeats"] == original["repeats"] == 2
    assert (
        sha256(ROOT / validation["description_suffix"])
        == pins[validation["description_suffix"]]
    )
