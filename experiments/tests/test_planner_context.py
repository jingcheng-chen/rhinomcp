import json
from experiments.posed_cushion_modeler import planner_context


def test_failed_large_geometry_has_bounded_planner_feedback():
    report = {
        "status": "fail",
        "checks": {"closed_solid": False},
        "repeat_identical": True,
        "artifact_sha256": "x" * 64,
        "max_height_error_mm": None,
        "full_measurements": {
            "objects": [
                {
                    "name": "x" * 10000,
                    "solid": False,
                    "naked_edges": 4,
                    "points": ["x" * 10000] * 100,
                }
                for _ in range(42)
            ]
        },
    }
    result = planner_context(
        "fixed task", {"complete": False, "summary": "x" * 2000000}, report
    )
    assert len(json.dumps(result)) < 10000
    assert result["object_count"] == 42
    assert result["evaluation"]["checks"]["closed_solid"] is False
    assert len(result["first_ten_objects"]) == 10
