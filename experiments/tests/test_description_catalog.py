"""Catalog boundaries for a reviewed source-only description comparison."""

from copy import deepcopy

import pytest

from experiments.workflow.binary_compare import catalog_descriptions


def catalogs():
    baseline = [
        {
            "name": "lookup",
            "description": "Old selector wording",
            "inputSchema": {"type": "object"},
        },
        {"name": "create", "description": "Create geometry", "inputSchema": {}},
    ]
    candidate = deepcopy(baseline)
    candidate[0]["description"] = "Use id or name"
    return baseline, candidate


def test_declared_description_preserves_catalog_and_inputs():
    baseline, candidate = catalogs()
    before = deepcopy((baseline, candidate))
    catalog_descriptions(baseline, candidate, ["lookup"])
    assert (baseline, candidate) == before


@pytest.mark.parametrize(
    "mutation", ["schema", "other_description", "addition", "removal", "order", "empty"]
)
def test_description_review_rejects_undeclared_catalog_drift(mutation):
    baseline, candidate = catalogs()
    if mutation == "schema":
        candidate[0]["inputSchema"]["required"] = ["id"]
    elif mutation == "other_description":
        candidate[1]["description"] = "Different creation behavior"
    elif mutation == "addition":
        candidate.append({"name": "new_tool"})
    elif mutation == "removal":
        candidate.pop()
    elif mutation == "order":
        candidate.reverse()
    else:
        candidate[0]["description"] = " "
    with pytest.raises(ValueError):
        catalog_descriptions(baseline, candidate, ["lookup"])


@pytest.mark.parametrize(
    "names",
    [[], ["lookup", "lookup"], ["absent"], ["lookup", "create"], "lookup", [None]],
)
def test_description_review_requires_exact_nonempty_intervention(names):
    baseline, candidate = catalogs()
    with pytest.raises(ValueError):
        catalog_descriptions(baseline, candidate, names)
    with pytest.raises(ValueError):
        catalog_descriptions(baseline, baseline, ["lookup"])
