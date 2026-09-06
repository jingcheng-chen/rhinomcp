import json

import pytest

from experiments import layer_modeler_mcp as gateway
from experiments.layer_checks import CASE_NAMES
from experiments.runner import ROOT
from experiments.trial import baseline_expectations


def test_layer_contract_preserves_52_and_records_six_measured_failures():
    old = json.loads(
        (ROOT / "experiments/harness/trial-preservation-v2.json").read_text()
    )
    new = json.loads((ROOT / "experiments/harness/trial-layer-parent.json").read_text())
    assert new["cases"] == old["cases"] + CASE_NAMES
    expected = baseline_expectations(new)
    assert all(expected[name] for name in old["cases"])
    assert len(expected) == 61 and sum(not value for value in expected.values()) == 6
    accepted = json.loads(
        (ROOT / "experiments/harness/trial-preservation-v3.json").read_text()
    )
    assert accepted["cases"] == new["cases"]
    assert all(baseline_expectations(accepted).values())


def test_assembly_gateway_rejects_execution_before_transport(monkeypatch):
    calls = []
    monkeypatch.setattr(gateway, "guard", lambda: calls.append("guard"))
    monkeypatch.setattr(
        gateway, "get_rhino_connection", lambda: pytest.fail("must not reach transport")
    )
    with pytest.raises(ValueError, match="outside assembly scope"):
        gateway.assembly_command(
            "execute_rhinocommon_csharp_code", {"code": "anything"}
        )
    assert calls == ["guard"]


def test_assembly_gateway_records_plugin_errors(monkeypatch):
    monkeypatch.setattr(gateway, "guard", lambda: None)
    monkeypatch.setattr(gateway, "validate_command", lambda *args: None)
    records = []
    monkeypatch.setattr(gateway, "record", records.append)

    class Connection:
        def send_command(self, *args):
            raise RuntimeError("Parent layer not found")

    monkeypatch.setattr(gateway, "get_rhino_connection", Connection)
    with pytest.raises(RuntimeError, match="not found"):
        gateway.assembly_command("create_layer", {"parent": "absent"})
    assert records == [
        {
            "command": "create_layer",
            "params": {"parent": "absent"},
            "error": "Parent layer not found",
        }
    ]
