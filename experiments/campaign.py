"""Finite, reviewed comparison queues with durable admission and stop decisions.

A campaign may dispatch already prepared comparisons. It cannot invent a candidate,
relax a gate, select source, or recover an uncertain modeling mutation.
"""

import argparse
from pathlib import Path
import subprocess
import sys
import time
import uuid

from experiments.runner import ROOT, sha256
from experiments.trial import locked, persist, read
from experiments.workflow import binary_compare as comparison, budget


def common(directory):
    contract = read(directory / "contract.json")
    if contract.get("evaluation_mode") != "trusted_baseline":
        raise ValueError("Campaigns require deferred trusted-baseline judging")
    return {
        "baseline": contract["binaries"]["baseline"]["identity"],
        "agent": contract["agent"],
        "suite": read(directory / "suite.json"),
        "acceptance": contract["acceptance"],
    }


def prepare(paths, limits, max_no_benefit, review):
    limits = budget.amounts(limits, positive=True)
    if not paths or len(set(paths)) != len(paths) or not review.strip():
        raise ValueError("A finite unique reviewed comparison queue is required")
    if type(max_no_benefit) is not int or max_no_benefit < 1:
        raise ValueError("Positive no-benefit stop count required")
    queue = []
    shared = None
    for path in paths:
        path = path.resolve(strict=True)
        path.relative_to(ROOT / "experiments/runs")
        comparison.check_pins(path)
        state = read(path / "state.json")
        resources = read(path / "resources.json")
        if (
            state["stage"] != "prepared"
            or state["rows"]
            or state["runtime_dirty"]
            or resources["pending"] is not None
            or resources["completed"]
        ):
            raise ValueError("Only fresh prepared comparisons enter a campaign")
        current = common(path)
        if shared is not None and current != shared:
            raise ValueError(
                "Campaign comparisons must share baseline, agent, tasks and gate"
            )
        shared = current
        queue.append(
            {
                "directory": str(path),
                "contract_sha256": sha256(path / "contract.json"),
                "limits": budget.amounts(resources["limits"], positive=True),
            }
        )
    directory = (
        ROOT
        / "experiments/runs"
        / (time.strftime("campaign-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
    )
    directory.mkdir()
    manifest = {
        "controller_sha256": sha256(Path(__file__)),
        "queue": queue,
        "limits": limits,
        "max_no_benefit": max_no_benefit,
        "common": shared,
        "review": review,
    }
    persist(directory / "manifest.json", manifest)
    persist(
        directory / "state.json",
        {
            "stage": "ready",
            "manifest_sha256": sha256(directory / "manifest.json"),
            "completed": [],
            "active": None,
            "used": dict.fromkeys(budget.KEYS, 0),
        },
    )
    return directory


def verify(directory):
    state = read(directory / "state.json")
    if sha256(directory / "manifest.json") != state["manifest_sha256"]:
        raise RuntimeError("Campaign manifest changed")
    manifest = read(directory / "manifest.json")
    if sha256(Path(__file__)) != manifest["controller_sha256"]:
        raise RuntimeError("Campaign controller changed")
    for item in manifest["queue"]:
        child = Path(item["directory"])
        if (
            sha256(child / "contract.json") != item["contract_sha256"]
            or common(child) != manifest["common"]
        ):
            raise RuntimeError("Reviewed comparison changed")
    used = dict.fromkeys(budget.KEYS, 0)
    for index, result in enumerate(state["completed"]):
        if result["directory"] != manifest["queue"][index]["directory"]:
            raise RuntimeError("Campaign completion order changed")
        child = Path(result["directory"])
        for name, digest in result["files"].items():
            if sha256(child / name) != digest:
                raise RuntimeError("Completed comparison evidence changed")
        for key in used:
            used[key] += result["used"][key]
    if used != state["used"]:
        raise RuntimeError("Campaign resource totals disagree")
    return state, manifest


def admit(directory):
    state, manifest = verify(directory)
    if state["active"] is not None:
        raise RuntimeError("Unaccounted comparison; reconcile before more dispatch")
    if state["stage"] != "ready":
        return None
    index = len(state["completed"])
    if index == len(manifest["queue"]):
        state["stage"] = "exhausted"
    elif index >= manifest["max_no_benefit"]:
        state["stage"] = "no_benefit_stop"
    else:
        item = manifest["queue"][index]
        if any(
            state["used"][key] + item["limits"][key] > manifest["limits"][key]
            for key in budget.KEYS
        ):
            state["stage"] = "resource_stop"
        else:
            child = Path(item["directory"])
            comparison.check_pins(child)
            if read(child / "state.json")["stage"] != "prepared":
                raise RuntimeError("Next comparison is no longer fresh")
            # Durable dispatch intent precedes starting another process.
            state.update(stage="running", active=index)
            persist(directory / "state.json", state)
            return child
    persist(directory / "state.json", state)
    return None


def reconcile(directory):
    """Account a completed child after process loss without executing it again."""
    state, manifest = verify(directory)
    if state["active"] is None:
        raise RuntimeError("No dispatched comparison to reconcile")
    index = state["active"]
    if index != len(state["completed"]):
        raise RuntimeError("Uncertain campaign order")
    child = Path(manifest["queue"][index]["directory"])
    comparison.check_pins(child)
    child_state = read(child / "state.json")
    resources = read(child / "resources.json")
    if (
        child_state["stage"] != "complete"
        or child_state["runtime_dirty"]
        or resources["pending"] is not None
    ):
        raise RuntimeError("Child is incomplete; restore/review it before continuation")
    report = read(child / "comparison.json")
    computed = comparison.summarize(child_state["rows"], read(child / "schedule.json"))
    if (
        computed["status"] != report["status"]
        or computed["tasks"] != report["tasks"]
        or computed["runs"] != report["runs"]
        or computed["status"] == "incomplete"
    ):
        raise RuntimeError("Incomplete or inconsistent comparison verdict")
    actual = budget.amounts(resources["used"])
    entries = resources["completed"]
    totals = {
        key: sum(budget.amounts(item["actual"])[key] for item in entries)
        for key in budget.KEYS
    }
    if (
        actual != totals
        or [item["name"] for item in entries]
        != [row["id"] for row in child_state["rows"]]
        or any(item["actual"]["sessions"] != 1 for item in entries)
        or actual["sessions"] != len(child_state["rows"])
    ):
        raise RuntimeError("Comparison usage does not account for every session")
    files = {
        str(path.relative_to(child)): sha256(path)
        for path in child.rglob("*")
        if path.is_file() and path.suffix != ".lock"
    }
    state["completed"].append(
        {
            "directory": str(child),
            "status": report["status"],
            "used": actual,
            "files": files,
        }
    )
    state["used"] = {key: state["used"][key] + actual[key] for key in budget.KEYS}
    over = resources["stopped"] or any(
        state["used"][key] > manifest["limits"][key] for key in budget.KEYS
    )
    state.update(
        active=None,
        stage="resource_stop"
        if over
        else "selection_review"
        if report["status"] == "benefit_observed"
        else "ready",
    )
    persist(directory / "state.json", state)
    return state


def handoff(previous, child):
    """Transfer only the prior completed comparison's verified empty document."""
    from experiments import rhino_trial
    from experiments.strip_probe import fingerprint

    with locked(ROOT / "experiments/runs/rhino.lock"):
        state = read(previous / "state.json")
        current = rhino_trial.runtime()
        rhino_trial.require_owned(current, read(previous / "runtime-owner.json"))
        expected = common(child)["baseline"]
        if (
            state["stage"] != "complete"
            or state["runtime_dirty"]
            or current["object_count"]
            or current.get("marker") is not None
            or {"mvid": current["mvid"], "sha256": sha256(Path(current["assembly"]))}
            != expected
        ):
            raise RuntimeError("Campaign handoff requires the empty owned baseline")
        last = previous / state["rows"][-1]["id"]
        if fingerprint() != read(last / "preservation.json")["after"]:
            raise RuntimeError("Document changed between comparisons")
        persist(
            child / "campaign-handoff.json",
            {"previous": str(previous), "runtime": current, "baseline": expected},
        )
        persist(
            child / "runtime-owner.json",
            {"pid": current["pid"], "document": current["document"]},
        )


def run(directory):
    with locked(directory / "writer.lock"):
        state, _ = verify(directory)
        if state["active"] is not None:
            reconcile(directory)  # A finished child is accounted, never rerun.
        while (child := admit(directory)) is not None:
            state, manifest = verify(directory)
            if state["active"]:
                handoff(
                    Path(manifest["queue"][state["active"] - 1]["directory"]), child
                )
            with (
                directory / f"comparison-{read(directory / 'state.json')['active']}.log"
            ).open("x") as log:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "experiments.workflow.binary_compare",
                        "run",
                        str(child),
                    ],
                    cwd=ROOT,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
            if result.returncode:
                persist(
                    directory / "failure.json",
                    {
                        "directory": str(child),
                        "returncode": result.returncode,
                        "action": "Restore and inspect the existing child; do not start another.",
                    },
                )
                raise RuntimeError("Comparison failed; campaign dispatch stopped")
            reconcile(directory)
        return read(directory / "state.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("contract", type=Path)
    for action in ("run", "reconcile", "status"):
        sub.add_parser(action).add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        spec = read(args.contract)
        print(
            prepare(
                [Path(p) for p in spec["comparisons"]],
                spec["limits"],
                spec["max_no_benefit"],
                spec["review"],
            )
        )
    elif args.action == "run":
        print(run(args.directory.resolve()))
    else:
        with locked(args.directory / "writer.lock"):
            print(
                reconcile(args.directory.resolve())
                if args.action == "reconcile"
                else verify(args.directory.resolve())[0]
            )
