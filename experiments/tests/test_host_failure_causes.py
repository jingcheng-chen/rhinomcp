import pytest
from experiments.workflow.flaws import cause


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (
            "Execution tools are refused during supervised host trials until M5 isolation is verified; attempt recorded",
            "host_execution_refusal",
        ),
        (
            "Error executing tool update_object_attributes: Communication error with Rhino: Layer 'Joined' not found.",
            "missing_layer",
        ),
        (
            "Communication error with Rhino: Object lookup requires 'id' or 'name'.",
            "schema_input",
        ),
        ("Object 'missing' not found.", "missing_object"),
    ],
)
def test_host_rejections_and_layer_errors_are_not_plugin_object_failures(
    message, expected
):
    assert (
        cause({"result": {"content": [{"type": "text", "text": message}]}}) == expected
    )
