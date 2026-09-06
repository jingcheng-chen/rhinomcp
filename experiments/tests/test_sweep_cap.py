"""The new trial cannot weaken any of the historical preservation requirements."""

import json

from experiments.runner import ROOT
from experiments.sweep_cap_probe import BASELINE_FAILURES, CASE_NAMES
from experiments.trial import baseline_expectations


def test_sweep_contract_preserves_old_cases_and_records_only_measured_failures():
    original = json.loads((ROOT / "experiments/harness/trial-suite.json").read_text())
    expanded = json.loads(
        (ROOT / "experiments/harness/trial-sweep-cap.json").read_text()
    )
    assert expanded["cases"] == original["cases"] + CASE_NAMES
    expectations = baseline_expectations(expanded)
    assert all(expectations[name] for name in original["cases"])
    assert {name for name, passed in expectations.items() if not passed} == set(
        BASELINE_FAILURES
    )
    assert len(expectations) == 50
