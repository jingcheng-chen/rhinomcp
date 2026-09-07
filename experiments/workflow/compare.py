"""Counterbalanced description-only trials through the shared native task runner."""

import argparse
import asyncio
import json
from pathlib import Path
import statistics
import time
import uuid

from experiments.runner import ROOT, save, sha256
from experiments.trial import locked
from experiments.workflow.audit import audit_run
from experiments.workflow.native_mcp import Gateway
from experiments.workflow.pilot import load_suite, run_task, source_pins


def description_only(baseline, candidate):
    if len(baseline) != len(candidate):
        raise ValueError("Tool catalog changed")
    for a, b in zip(baseline, candidate, strict=True):
        expected = dict(b)
        if a["name"] == "create_object":
            if a["description"] == b["description"]:
                raise ValueError("No intervention")
            expected["description"] = a["description"]
        if a != expected:
            raise ValueError("Intervention must change only create_object description")


def summarize(rows, expected_count):
    complete = len(rows) == expected_count
    groups = {}
    for row in rows:
        groups.setdefault(row["family"], {"baseline": [], "candidate": []})[
            row["arm"]
        ].append(row)
    families = {}
    for family, arms in groups.items():
        values = {}
        for arm, items in arms.items():
            values[arm] = {
                "runs": len(items),
                "passes": sum(r["task_verdict"] == "pass" for r in items),
                "median_calls": statistics.median(
                    r["metrics"]["mcp_attempts"] for r in items
                )
                if items
                else None,
                "failed_calls": sum(r["metrics"]["failed_calls"] for r in items),
                "median_seconds": statistics.median(r["elapsed_seconds"] for r in items)
                if items
                else None,
            }
        a, b = values["baseline"], values["candidate"]
        accepted = bool(
            a["runs"]
            and a["runs"] == b["runs"]
            and a["passes"] == a["runs"]
            and b["passes"] == b["runs"]
            and b["median_calls"] < a["median_calls"]
            and b["failed_calls"] <= a["failed_calls"]
        )
        families[family] = {**values, "criterion_met": accepted}
    return {
        "status": "criterion_met"
        if complete and families and all(x["criterion_met"] for x in families.values())
        else "incomplete"
        if not complete
        else "criterion_not_met",
        "families": families,
        "runs": rows,
        "promotion_authorized": False,
        "limitations": [
            "Small discovery sample; no held-out validation",
            "Requested model/effort pinned; backend model snapshot unavailable",
            "Runtime and token counters include client/cache/guard effects; not dollar-cost estimates",
        ],
    }


def run(path):
    contract = json.loads(path.read_text())
    if (
        set(contract)
        != {
            "id",
            "suite",
            "agent",
            "description_suffix",
            "repeats",
            "design",
            "acceptance",
        }
        or contract["repeats"] != 2
    ):
        raise ValueError("This pilot requires two counterbalanced pairs per task")
    suite = load_suite(ROOT / contract["suite"])
    suffix_path = (ROOT / contract["description_suffix"]).resolve()
    suffix_path.relative_to(ROOT / "experiments/workflow")
    suffix = suffix_path.read_text()
    if not suffix.strip():
        raise ValueError("Empty intervention")
    runs = ROOT / "experiments/runs"
    with locked(runs / "rhino.lock"):
        directory = runs / (
            time.strftime("workflow-comparison-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
        )
        directory.mkdir()
        print(directory, flush=True)
        save(directory / "contract.json", contract)
        save(directory / "suite.json", suite)
        frozen_suffix = directory / "description-suffix.txt"
        frozen_suffix.write_text(suffix)
        pins = source_pins()
        for p in [path.resolve(), (ROOT / contract["suite"]).resolve(), suffix_path] + [
            (ROOT / e["path"]).resolve() for e in suite["tasks"]
        ]:
            pins[str(p.relative_to(ROOT))] = sha256(p)
        save(directory / "input-pins.json", pins)
        catalogs = {}
        for arm, text in [("baseline", ""), ("candidate", suffix)]:
            catalogs[arm] = [
                t.model_dump(mode="json", exclude_none=True)
                for t in asyncio.run(
                    Gateway(
                        0, "", 1, directory / "unused", description_suffix=text
                    ).definitions()
                )
            ]
            save(directory / f"{arm}-tools.json", catalogs[arm])
        description_only(catalogs["baseline"], catalogs["candidate"])
        rows = []
        environment_pin = None
        count = len(suite["tasks"]) * 4

        def check_pins():
            if (
                any(sha256(ROOT / name) != digest for name, digest in pins.items())
                or frozen_suffix.read_text() != suffix
            ):
                raise RuntimeError("Frozen comparison input changed")

        try:
            for task_index, entry in enumerate(suite["tasks"]):
                for repeat, order in enumerate(
                    [("baseline", "candidate"), ("candidate", "baseline")], 1
                ):
                    for arm in order:
                        check_pins()
                        child = directory / f"task-{task_index + 1}-pair-{repeat}-{arm}"
                        run_task(
                            child,
                            entry,
                            suite,
                            catalogs[arm],
                            contract["agent"],
                            frozen_suffix if arm == "candidate" else None,
                        )
                        check_pins()
                        environment = json.loads(
                            (child / "environment.json").read_text()
                        )
                        comparable = {
                            key: environment[key]
                            for key in (
                                "model",
                                "codex_version",
                                "plugin_sha256",
                                "call_budget",
                                "timeout_seconds",
                            )
                        }
                        comparable["mvid"] = environment["rhino"]["mvid"]
                        comparable["pid"] = environment["rhino"]["pid"]
                        if environment_pin is None:
                            environment_pin = comparable
                            save(directory / "environment-pin.json", comparable)
                        elif comparable != environment_pin:
                            raise RuntimeError("Comparison environment changed")
                        row = audit_run(
                            ROOT,
                            {
                                "id": child.name,
                                "family": entry["family"],
                                "run": str(child.relative_to(ROOT)),
                            },
                        )
                        row.update(arm=arm, pair=repeat, task=entry["path"])
                        row["comparison_blockers"] = [
                            "Requested model alias pinned; backend snapshot unavailable. Small discovery trial, not generalization."
                        ]
                        rows.append(row)
                        save(directory / "comparison.json", summarize(rows, count))
        except BaseException as error:
            save(
                directory / "failure.json",
                {"error": str(error), "completed_runs": len(rows)},
            )
            raise
        return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "contract",
        type=Path,
        nargs="?",
        default=ROOT / "experiments/workflow/placement-trial.json",
    )
    print(run(parser.parse_args().contract))
