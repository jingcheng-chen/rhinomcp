"""Transport and input contract for strict parent-layer resolution."""

import importlib
from unittest.mock import MagicMock

import pytest
from jsonschema import ValidationError
from rhinomcp.validation import validate_command


@pytest.mark.parametrize("parent", ["Assembly::Left", "aSSEMBLY::lEFT", "UniqueParent"])
def test_parent_reference_is_forwarded_exactly(monkeypatch, parent):
    module = importlib.import_module("rhinomcp.tools.create_layer")
    connection = MagicMock()
    connection.send_command.return_value = {"name": "Part"}
    monkeypatch.setattr(module, "get_rhino_connection", lambda: connection)
    assert (
        module.create_layer(None, name="Part", parent=parent) == "Created layer: Part"
    )
    connection.send_command.assert_called_once_with(
        "create_layer", {"name": "Part", "parent": parent}
    )


def test_automatic_name_omits_optional_fields(monkeypatch):
    module = importlib.import_module("rhinomcp.tools.create_layer")
    connection = MagicMock()
    connection.send_command.return_value = {"name": "Layer 06"}
    monkeypatch.setattr(module, "get_rhino_connection", lambda: connection)
    assert module.create_layer(None) == "Created layer: Layer 06"
    connection.send_command.assert_called_once_with("create_layer", {})


def test_parent_failure_is_reported_without_retry(monkeypatch):
    module = importlib.import_module("rhinomcp.tools.create_layer")
    connection = MagicMock()
    connection.send_command.side_effect = RuntimeError(
        "Parent name is ambiguous; use the full path"
    )
    monkeypatch.setattr(module, "get_rhino_connection", lambda: connection)
    assert "ambiguous" in module.create_layer(None, name="Part", parent="Left")
    assert connection.send_command.call_count == 1


@pytest.mark.parametrize("params", [{}, {"name": "Part", "parent": "Assembly::Left"}])
def test_valid_layer_creation_contract(params):
    validate_command("create_layer", params)


@pytest.mark.parametrize(
    "params", [{"unexpected": True}, {"parent": None}, {"parent": 123}]
)
def test_invalid_layer_creation_contract(params):
    with pytest.raises(ValidationError):
        validate_command("create_layer", params)
