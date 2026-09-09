"""Reviewed binary comparisons; shared sessions and supervised lifecycle recovery.

This route consumes already-built, reviewed binaries. It neither rebuilds an old
trial nor promotes candidates. Interrupted sessions are retained, never replayed.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import uuid

from experiments import rhino_trial
from experiments.runner import ROOT, sha256
from experiments.trial import locked, persist, read
from experiments.workflow.audit import audit_run
from experiments.workflow import budget
from experiments.workflow.native_mcp import Gateway, TOOLS
from experiments.workflow.pilot import evaluate_saved, load_suite, run_task, source_pins


def schedule(suite):
    return [
        {
            "name": f"task-{i + 1}-pair-{pair}-{arm}",
            "entry": entry,
            "pair": pair,
            "arm": arm,
        }
        for i, entry in enumerate(suite["tasks"])
        for pair, order in enumerate(
            (("baseline", "candidate"), ("candidate", "baseline")), 1
        )
        for arm in order
    ]


def summarize(rows, plan):
    """Judge each task separately so pooled successes cannot hide a regression."""
    complete = [r["id"] for r in rows] == [s["name"] for s in plan]
    tasks = {}
    for step in plan:
        path = step["entry"]["path"]
        if path in tasks:
            continue
        arms = {}
        for arm in ("baseline", "candidate"):
            items = [r for r in rows if r["task"] == path and r["arm"] == arm]
            arms[arm] = {
                "runs": len(items),
                "passes": sum(r["task_verdict"] == "pass" for r in items),
                "failed_calls": sum(r["metrics"]["failed_calls"] for r in items),
                "median_calls": statistics.median(
                    r["metrics"]["mcp_attempts"] for r in items
                )
                if items
                else None,
                "median_seconds": statistics.median(r["elapsed_seconds"] for r in items)
                if items
                else None,
            }
        a, b = arms["baseline"], arms["candidate"]
        ready = a["runs"] == b["runs"] == 2
        regression = ready and b["passes"] < a["passes"]
        benefit = ready and (
            b["passes"] > a["passes"]
            or (
                a["passes"] == b["passes"] == 2
                and b["median_calls"] < a["median_calls"]
                and b["failed_calls"] <= a["failed_calls"]
            )
        )
        tasks[path] = {
            **arms,
            "family": step["entry"]["family"],
            "correctness_regression": regression,
            "observed_benefit": benefit,
        }
    signal = (
        complete
        and not any(t["correctness_regression"] for t in tasks.values())
        and any(t["observed_benefit"] for t in tasks.values())
    )
    return {
        "status": "incomplete"
        if not complete
        else "benefit_observed"
        if signal
        else "no_benefit_established",
        "tasks": tasks,
        "runs": rows,
        "promotion_authorized": False,
        "limitations": [
            "Two repeats per arm/task; descriptive evidence, not statistical proof.",
            "Requested model alias/effort pinned; backend snapshot unavailable.",
            "Panel discovery tasks are not held-out families.",
            "Evaluation runs in the reviewed candidate process; no adversarial isolation.",
            "Correctness precedes efficiency; tokens/time are secondary observations.",
        ],
    }


def identity(arm, directory):
    return read(directory / "contract.json")["binaries"][arm]["identity"]


def session_environment(directory):
    """Compare document settings across restarts without comparing random IDs."""
    env = read(directory / "environment.json")
    preservation = read(directory / "preservation.json")
    before = preservation["before"]
    if preservation["preserved"] is not True or before != preservation["after"]:
        raise RuntimeError("Session did not preserve its document")
    if before["objects"]:
        raise RuntimeError("Session did not start with an empty document")
    layers = before["layers"]
    indices = {layer["Id"]: index for index, layer in enumerate(layers)}
    return {
        **{
            k: env[k]
            for k in ("model", "codex_version", "call_budget", "timeout_seconds")
        },
        "units": before["units"],
        "tolerance": before["tolerance"],
        "layers": [
            {
                "name": layer["Name"],
                "parent": None
                if layer["ParentLayerId"] == "00000000-0000-0000-0000-000000000000"
                else indices[layer["ParentLayerId"]],
                "visible": layer["IsVisible"],
                "locked": layer["IsLocked"],
            }
            for layer in layers
        ],
    }


def check_pins(directory):
    state = read(directory / "state.json")
    if sha256(directory / "contract.json") != state["contract_sha256"]:
        raise RuntimeError("Frozen contract changed")
    pins = read(directory / "pins.json")
    for name, digest in pins.items():
        if sha256(ROOT / name) != digest:
            raise RuntimeError(f"Frozen source/input changed: {name}")
    for name, digest in state["frozen_files"].items():
        if sha256(directory / name) != digest:
            raise RuntimeError(f"Frozen artifact changed: {name}")
    current_sources = source_pins()
    for spec in read(directory / "contract.json").get("interfaces", {}).values():
        current_sources.update(source_pins(ROOT / spec["server_source"]))
    if set(current_sources) - set(pins):
        raise RuntimeError("Unpinned source additions appeared after preparation")
    for arm in ("baseline", "candidate"):
        if sha256(directory / f"{arm}.rhp") != identity(arm, directory)["sha256"]:
            raise RuntimeError(f"Frozen {arm} binary changed")


def native_catalog(server_source, extra_tools):
    """Read reviewed candidate-native schemas without changing production imports."""
    source = (ROOT / server_source).resolve(strict=True)
    source.relative_to(ROOT)
    source_pins(source)  # Validate the declared package path before importing it.
    names = [*TOOLS, *extra_tools]
    code = "import asyncio,json,sys,pathlib,rhinomcp; assert pathlib.Path(rhinomcp.__file__).resolve().parent == pathlib.Path(sys.argv[2])/'rhinomcp'; from experiments.workflow.native_mcp import Gateway; print(json.dumps([t.model_dump(mode='json',exclude_none=True) for t in asyncio.run(Gateway(0,'',1,'unused',tool_names=json.loads(sys.argv[1])).definitions())]))"
    output = subprocess.check_output(
        [sys.executable, "-c", code, json.dumps(names), str(source)],
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join([str(source), str(ROOT)]),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        text=True,
        timeout=30,
    )
    return json.loads(output)


def catalog_extension(baseline, candidate, additions):
    if (
        not additions
        or candidate[: len(baseline)] != baseline
        or [t["name"] for t in candidate[len(baseline) :]] != additions
    ):
        raise ValueError("Candidate catalog must add only its declared tools")


def prepare(path, review):
    contract = read(path)
    if (
        set(contract) - {"evaluation_mode", "interfaces", "resource_limits"}
        != {"id", "suite", "agent", "binaries", "repeats", "acceptance"}
        or contract["repeats"] != 2
        or not review.strip()
    ):
        raise ValueError(
            "Reviewed binary comparison requires two counterbalanced pairs"
        )
    if contract.get("evaluation_mode", "immediate") not in {
        "immediate",
        "trusted_baseline",
    }:
        raise ValueError("Unknown evaluation mode")
    agent = contract["agent"]
    if (
        set(agent) != {"model", "reasoning_effort"}
        or not agent["model"]
        or agent["reasoning_effort"] not in {"low", "medium", "high", "xhigh"}
    ):
        raise ValueError("Explicit agent configuration required")
    if contract["acceptance"] != "correctness_then_calls_v1":
        raise ValueError("Unknown acceptance rule")
    if set(contract["binaries"]) != {"baseline", "candidate"}:
        raise ValueError("Two binary arms required")
    suite = load_suite(ROOT / contract["suite"])
    allowance = {
        "sessions": 1,
        "tool_attempts": suite["call_budget"] + 1,
        "model_seconds": suite["timeout_seconds"] + 10,
    }
    limits = budget.amounts(
        contract.get(
            "resource_limits",
            {key: value * len(schedule(suite)) for key, value in allowance.items()},
        ),
        positive=True,
    )
    interfaces = contract.get("interfaces")
    if interfaces is not None:
        if (
            set(interfaces) != {"baseline", "candidate"}
            or any(
                set(spec) != {"server_source", "extra_tools"}
                for spec in interfaces.values()
            )
            or interfaces["baseline"]["extra_tools"]
        ):
            raise ValueError("Invalid reviewed interface declaration")
        if contract.get("evaluation_mode") != "trusted_baseline":
            raise ValueError(
                "New-capability comparisons require trusted baseline evaluation"
            )
    for spec in contract["binaries"].values():
        if set(spec) != {"path", "identity"} or set(spec["identity"]) != {
            "sha256",
            "mvid",
        }:
            raise ValueError("Binary path, SHA-256 and MVID required")
        if sha256(ROOT / spec["path"]) != spec["identity"]["sha256"]:
            raise ValueError("Reviewed binary hash mismatch")
    if (
        contract["binaries"]["baseline"]["identity"]
        == contract["binaries"]["candidate"]["identity"]
    ):
        raise ValueError("Identical binaries are not an intervention")
    runs = ROOT / "experiments/runs"
    with locked(runs / "rhino.lock"):
        directory = runs / (
            time.strftime("workflow-binary-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
        )
        directory.mkdir()
        persist(directory / "contract.json", contract)
        persist(directory / "suite.json", suite)
        persist(directory / "schedule.json", schedule(suite))
        budget.initialize(directory / "resources.json", limits)
        (directory / "review.txt").write_text(review)
        for arm, spec in contract["binaries"].items():
            shutil.copy2(ROOT / spec["path"], directory / f"{arm}.rhp")
        initial = rhino_trial.claim_empty(directory)
        if initial.get("marker") is not None or rhino_trial.probe(
            directory
        ) != identity("baseline", directory):
            raise RuntimeError("Initial runtime is not the empty reviewed baseline")
        persist(directory / "initial-runtime.json", initial)
        definitions = [
            t.model_dump(mode="json", exclude_none=True)
            for t in asyncio.run(Gateway(0, "", 1, directory / "unused").definitions())
        ]
        persist(directory / "tools.json", definitions)
        pins = source_pins()
        if interfaces is not None:
            catalogs = {
                arm: native_catalog(spec["server_source"], spec["extra_tools"])
                for arm, spec in interfaces.items()
            }
            catalog_extension(
                catalogs["baseline"],
                catalogs["candidate"],
                interfaces["candidate"]["extra_tools"],
            )
            persist(directory / "tools.json", catalogs)
            for spec in interfaces.values():
                pins.update(source_pins(ROOT / spec["server_source"]))
        for p in [path, ROOT / contract["suite"]] + [
            ROOT / e["path"] for e in suite["tasks"]
        ]:
            pins[str(p.resolve().relative_to(ROOT))] = sha256(p)
        persist(directory / "pins.json", pins)
        persist(
            directory / "state.json",
            {
                "stage": "prepared",
                "runtime_dirty": False,
                "promoted": False,
                "contract_sha256": sha256(directory / "contract.json"),
                "frozen_files": {
                    name: sha256(directory / name)
                    for name in (
                        "suite.json",
                        "schedule.json",
                        "tools.json",
                        "pins.json",
                        "review.txt",
                    )
                },
                "rows": [],
                "transitions": [],
            },
        )
        return directory


def transition(directory, arm):
    state = read(directory / "state.json")
    expected = identity(arm, directory)
    if sha256(directory / f"{arm}.rhp") != expected["sha256"]:
        raise RuntimeError("Refuse lifecycle with changed binary")
    # Persist uncertainty before issuing a ticket; even a killed install needs recovery.
    state.update(stage=f"{arm}_transition_pending", runtime_dirty=True)
    path = directory / (
        f"transition-{len(state['transitions']) + 1}-{arm}-{uuid.uuid4().hex[:6]}.json"
    )
    state["transitions"].append(path.name)
    persist(directory / "state.json", state)
    request = {
        "trial": str(directory),
        "action": "install" if arm == "candidate" else "restore",
        "candidate_binary": str(directory / "candidate.rhp"),
        "baseline_binary": str(directory / "baseline.rhp"),
        "expected_identity": expected,
    }
    persist(path, request)
    result = rhino_trial.lifecycle(request, path)
    persist(path.with_name(path.stem + "-response.json"), result)
    if rhino_trial.probe(directory) != expected:
        raise RuntimeError("Lifecycle identity mismatch")
    state.update(stage=f"{arm}_ready", runtime_dirty=arm == "candidate")
    persist(directory / "state.json", state)


def recover(directory):
    """Recovery is separate from resuming/replaying any modeling work."""
    state = read(directory / "state.json")
    if sha256(directory / "contract.json") != state["contract_sha256"]:
        raise RuntimeError("Cannot trust changed recovery contract")
    if state["runtime_dirty"]:
        transition(directory, "baseline")
    if rhino_trial.probe(directory) != identity("baseline", directory):
        raise RuntimeError("Restoration is not verified")
    current = rhino_trial.runtime()
    if current["object_count"] or current.get("marker") is not None:
        raise RuntimeError("Recovery requires reviewed cleanup of unfinished task")
    persist(directory / "final-runtime.json", current)
    state = read(directory / "state.json")
    state.update(stage="restored", runtime_dirty=False)
    persist(directory / "state.json", state)


def checkpoint_files(child):
    # Deferred evaluation changes artifact and summary records. Freeze all modeling inputs,
    # outputs and logs; validate the evaluation state separately before resume.
    mutable = {"artifact.json", "summary.json"}
    return {
        str(path.relative_to(child)): sha256(path)
        for path in sorted(child.rglob("*"))
        if path.is_file() and str(path.relative_to(child)) not in mutable
    }


def checkpoint(directory):
    state = read(directory / "state.json")
    resources = read(directory / "resources.json")
    if state.get("active_session") or resources["pending"] is not None:
        raise RuntimeError("Cannot checkpoint unfinished modeling")
    name = f"checkpoints/modeling-{len(state['rows'])}.json"
    path = directory / name
    if path.exists():
        raise RuntimeError("A modeling checkpoint cannot be overwritten")
    path.parent.mkdir(exist_ok=True)
    persist(
        path,
        {
            "rows": state["rows"],
            "resources": resources,
            "environment": read(directory / "environment-pin.json"),
            "files": {
                row["id"]: checkpoint_files(directory / row["id"])
                for row in state["rows"]
            },
        },
    )
    state["checkpoint"] = {"path": name, "sha256": sha256(path)}
    persist(directory / "state.json", state)


def resume_index(directory, plan):
    """Resume only a verified completed prefix, never an uncertain operation."""
    state = read(directory / "state.json")
    if state["stage"] == "complete" or state.get("active_session"):
        raise RuntimeError("Completed or uncertain sessions cannot be resumed")
    receipt = state.get("checkpoint")
    if not receipt:
        raise RuntimeError("No verified modeling checkpoint")
    expected_name = f"checkpoints/modeling-{len(state['rows'])}.json"
    if (
        receipt["path"] != expected_name
        or sha256(directory / expected_name) != receipt["sha256"]
    ):
        raise RuntimeError("Checkpoint receipt changed")
    saved = read(directory / expected_name)
    resources = read(directory / "resources.json")
    count = len(saved["rows"])
    names = [step["name"] for step in plan[:count]]
    if (
        not count
        or count > len(plan)
        or [row["id"] for row in saved["rows"]] != names
        or state["rows"] != saved["rows"]
        or resources != saved["resources"]
        or resources["pending"] is not None
        or resources["stopped"]
        or [entry["name"] for entry in resources["completed"]] != names
        or read(directory / "environment-pin.json") != saved["environment"]
    ):
        raise RuntimeError("Checkpoint, schedule or resource ledger disagree")
    deferred = (
        read(directory / "contract.json").get("evaluation_mode") == "trusted_baseline"
    )
    for step in plan[:count]:
        child = directory / step["name"]
        if checkpoint_files(child) != saved["files"][step["name"]]:
            raise RuntimeError("Completed modeling evidence changed")
        record = read(child / "artifact.json")
        if (
            sha256(child / "candidate.3dm") != record["sha256"]
            or sha256(child / "task.json") != record["task_sha256"]
            or (
                deferred
                and (
                    not record["evaluation_pending"]
                    or (child / "evaluation.json").exists()
                )
            )
        ):
            raise RuntimeError("Artifact changed or evaluation already started")
        if session_environment(child) != saved["environment"]:
            raise RuntimeError("Completed environment changed")
    if any((directory / step["name"]).exists() for step in plan[count:]):
        raise RuntimeError("Uncheckpointed session exists; never replay uncertain work")
    return count


def run(directory, resume=False, max_sessions=None):
    if max_sessions is not None and (type(max_sessions) is not int or max_sessions < 1):
        raise ValueError("Pause interval must be a positive session count")
    with (
        locked(ROOT / "experiments/runs/rhino.lock"),
        locked(directory / "writer.lock"),
    ):
        state = read(directory / "state.json")
        if not resume and state["stage"] != "prepared":
            raise RuntimeError("Run is not fresh; use resume or recovery")
        check_pins(directory)
        contract, suite = (
            read(directory / "contract.json"),
            read(directory / "suite.json"),
        )
        plan, definitions = (
            read(directory / "schedule.json"),
            read(directory / "tools.json"),
        )
        start = resume_index(directory, plan) if resume else 0
        if resume:
            recover(directory)
            state = read(directory / "state.json")
        state["stage"] = "running"
        persist(directory / "state.json", state)
        environment_pin = read(directory / "environment-pin.json") if start else None
        completed = False
        deferred = contract.get("evaluation_mode") == "trusted_baseline"
        try:
            for offset, step in enumerate(plan[start:]):
                if max_sessions is not None and offset >= max_sessions:
                    break
                check_pins(directory)
                budget.reserve(
                    directory / "resources.json",
                    step["name"],
                    {
                        "sessions": 1,
                        "tool_attempts": suite["call_budget"] + 1,
                        "model_seconds": suite["timeout_seconds"] + 10,
                    },
                )
                observed = rhino_trial.probe(directory)
                if observed != identity(step["arm"], directory):
                    other = "candidate" if step["arm"] == "baseline" else "baseline"
                    if observed != identity(other, directory):
                        raise RuntimeError("Unexpected runtime identity")
                    transition(directory, step["arm"])
                check_pins(directory)
                child = directory / step["name"]
                state = read(directory / "state.json")
                state["active_session"] = step["name"]
                persist(directory / "state.json", state)
                run_task(
                    child,
                    step["entry"],
                    suite,
                    definitions[step["arm"]]
                    if "interfaces" in contract
                    else definitions,
                    contract["agent"],
                    defer_evaluation=deferred,
                    server_source=ROOT
                    / contract["interfaces"][step["arm"]]["server_source"]
                    if "interfaces" in contract
                    else None,
                    tool_names=[
                        *TOOLS,
                        *contract["interfaces"][step["arm"]]["extra_tools"],
                    ]
                    if "interfaces" in contract
                    else None,
                )
                check_pins(directory)
                if rhino_trial.probe(directory) != identity(step["arm"], directory):
                    raise RuntimeError("Wrong arm after session")
                env = read(child / "environment.json")
                expected = identity(step["arm"], directory)
                if (
                    env["plugin_sha256"] != expected["sha256"]
                    or env["rhino"]["mvid"] != expected["mvid"]
                ):
                    raise RuntimeError("Session ran the wrong binary")
                comparable = session_environment(child)
                if environment_pin is None:
                    environment_pin = comparable
                    persist(directory / "environment-pin.json", comparable)
                elif environment_pin != comparable:
                    raise RuntimeError("Non-intervention environment changed")
                row = audit_run(
                    ROOT,
                    {
                        "id": step["name"],
                        "family": step["entry"]["family"],
                        "run": str(child.relative_to(ROOT)),
                    },
                )
                row.update(
                    arm=step["arm"], pair=step["pair"], task=step["entry"]["path"]
                )
                state = read(directory / "state.json")
                state["rows"].append(row)
                state.pop("active_session", None)
                persist(directory / "state.json", state)
                resources = budget.settle(
                    directory / "resources.json",
                    step["name"],
                    {
                        "sessions": 1,
                        "tool_attempts": row["metrics"]["mcp_attempts"],
                        "model_seconds": row["elapsed_seconds"],
                    },
                )
                if resources["stopped"]:
                    raise RuntimeError(
                        "Observed modeling usage exceeded its resource limit"
                    )
                checkpoint(directory)
                if not deferred:
                    persist(
                        directory / "comparison.json", summarize(state["rows"], plan)
                    )
            completed = len(read(directory / "state.json")["rows"]) == len(plan)
        except BaseException as error:
            persist(
                directory / "failure.json",
                {"error": str(error), "type": type(error).__name__},
            )
            raise
        finally:
            recover(directory)
        if not completed:
            state = read(directory / "state.json")
            state["stage"] = "paused"
            persist(directory / "state.json", state)
            return directory
        if completed and deferred:
            try:
                rows = []
                for step in plan:
                    check_pins(directory)
                    child = directory / step["name"]
                    evaluate_saved(child, identity("baseline", directory))
                    row = audit_run(
                        ROOT,
                        {
                            "id": step["name"],
                            "family": step["entry"]["family"],
                            "run": str(child.relative_to(ROOT)),
                        },
                    )
                    row.update(
                        arm=step["arm"], pair=step["pair"], task=step["entry"]["path"]
                    )
                    rows.append(row)
                check_pins(directory)
                state = read(directory / "state.json")
                state["rows"] = rows
                persist(directory / "state.json", state)
                result = summarize(rows, plan)
                result["evaluation_mode"] = "trusted_baseline"
                result["limitations"] = [
                    text
                    for text in result["limitations"]
                    if not text.startswith("Evaluation runs")
                ]
                result["limitations"].append(
                    "Evaluation uses a fresh trusted baseline process after candidate shutdown; this is not an adversarial OS sandbox."
                )
                persist(directory / "comparison.json", result)
            except BaseException as error:
                persist(
                    directory / "evaluation-failure.json",
                    {"error": str(error), "type": type(error).__name__},
                )
                raise
        state = read(directory / "state.json")
        state["stage"] = "complete"
        persist(directory / "state.json", state)
        return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("contract", type=Path)
    prepare_parser.add_argument("--review-file", type=Path, required=True)
    for action in ("run", "resume", "recover"):
        command_parser = sub.add_parser(action)
        command_parser.add_argument("directory", type=Path)
        if action != "recover":
            command_parser.add_argument("--max-sessions", type=int)
    args = parser.parse_args()
    if args.action == "prepare":
        print(
            prepare(args.contract.resolve(), args.review_file.read_text()), flush=True
        )
    elif args.action in {"run", "resume"}:
        print(
            run(
                args.directory.resolve(),
                resume=args.action == "resume",
                max_sessions=args.max_sessions,
            ),
            flush=True,
        )
    else:
        with (
            locked(ROOT / "experiments/runs/rhino.lock"),
            locked(args.directory / "writer.lock"),
        ):
            recover(args.directory.resolve())
