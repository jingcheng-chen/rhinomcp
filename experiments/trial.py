"""Durable, review-gated candidate trials using a trusted local runtime adapter.

Adapters implement build/probe/install/test/restore on their own machine. This
controller never promotes a candidate: every installed trial ends in restoration.
The adapter and candidate remain reviewed code, not an OS security boundary.
"""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid

from experiments.repair import check_candidate, inventory
from experiments.runner import save, sha256


@contextmanager
def locked(path):
    with path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def persist(path, value):
    """Persist transitions before side effects, including across process crashes."""
    save(path, value)
    with path.open("rb") as handle:
        os.fsync(handle.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read(path):
    return json.loads(path.read_text())


def prepare(repair, baseline, baseline_mvid, suite, adapter, runtime_lock, review):
    repair = repair.resolve(strict=True)
    adapter = adapter.resolve(strict=True)
    baseline = baseline.resolve(strict=True)
    runtime_lock = runtime_lock.absolute()
    if not review.strip() or not baseline_mvid.strip():
        raise ValueError("A review record and verified baseline MVID are required")
    contract = read(suite)
    cases = contract.get("cases")
    if (
        not isinstance(cases, list)
        or not cases
        or not all(isinstance(case, str) and case for case in cases)
        or len(set(cases)) != len(cases)
    ):
        raise ValueError("Suite requires unique nonempty case names")
    inputs = contract.get("inputs", [])
    if not isinstance(inputs, list) or not all(
        isinstance(name, str) for name in inputs
    ):
        raise ValueError("Suite inputs must be a list of file paths")
    pinned_inputs = {}
    for name in inputs:
        path = (suite.resolve().parent / name).resolve(strict=True)
        if not path.is_file():
            raise ValueError("Suite input must be a file")
        pinned_inputs[str(path)] = sha256(path)
    with locked(repair / "writer.lock"):
        checkpoint = read(repair / "checkpoint.json")
        source = repair / "candidate"
        if checkpoint.get("stage") != "candidate_ready_for_review" or checkpoint.get(
            "executed"
        ):
            raise ValueError("Trial requires an unexecuted candidate ready for review")
        check_candidate(source, read(repair / "baseline_inventory.json"))
        if inventory(source) != checkpoint["candidate_inventory"]:
            raise ValueError("Candidate changed since builder checkpoint")
        patch = subprocess.check_output(
            ["git", "diff", "--no-ext-diff", "--binary"], cwd=source
        )
        patch_hash = hashlib.sha256(patch).hexdigest()
        if (
            patch_hash != checkpoint["patch_sha256"]
            or sha256(repair / "candidate.patch") != patch_hash
        ):
            raise ValueError("Reviewed patch identity does not match source")
        directory = repair / ("trial-" + uuid.uuid4().hex[:8])
        directory.mkdir()
        shutil.copytree(
            source, directory / "source", ignore=shutil.ignore_patterns(".git")
        )
        shutil.copy2(baseline, directory / "baseline.rhp")
        shutil.copy2(repair / "candidate.patch", directory / "reviewed.patch")
        save(directory / "suite.json", contract)
        (directory / "review.txt").write_text(review)
        manifest = {
            "version": 1,
            "repair": str(repair),
            "patch_sha256": patch_hash,
            "source_inventory": inventory(directory / "source"),
            "baseline": {
                "sha256": sha256(directory / "baseline.rhp"),
                "mvid": baseline_mvid,
            },
            "suite_sha256": sha256(directory / "suite.json"),
            "suite_inputs": pinned_inputs,
            "review_sha256": sha256(directory / "review.txt"),
            "adapter": str(adapter),
            "adapter_sha256": sha256(adapter),
            "python": str(Path(sys.executable).absolute()),
            "python_binary": str(Path(sys.executable).resolve()),
            "python_sha256": sha256(Path(sys.executable).resolve()),
            "runtime_lock": str(runtime_lock),
        }
        persist(directory / "manifest.json", manifest)
        persist(
            directory / "state.json",
            {
                "stage": "ready",
                "runtime_dirty": False,
                "events": [],
                "manifest_sha256": sha256(directory / "manifest.json"),
                "promoted": False,
            },
        )
        checkpoint.update(stage="validation_registered", trial=str(directory))
        persist(repair / "checkpoint.json", checkpoint)
    return directory


class Trial:
    def __init__(self, directory, timeout=180):
        self.directory = directory.resolve(strict=True)
        self.manifest = read(self.directory / "manifest.json")
        self.state = read(self.directory / "state.json")
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        self.timeout = timeout

    def record(self, stage, **values):
        self.state.update(stage=stage, **values)
        self.state["events"].append({"stage": stage, "time": time.time()})
        persist(self.directory / "state.json", self.state)

    def guards(self, source=True):
        if Path(self.manifest["python"]).resolve() != Path(
            self.manifest["python_binary"]
        ):
            raise ValueError("Pinned Python interpreter target changed")
        pairs = {
            self.directory / "manifest.json": self.state["manifest_sha256"],
            self.directory / "baseline.rhp": self.manifest["baseline"]["sha256"],
            Path(self.manifest["adapter"]): self.manifest["adapter_sha256"],
            Path(self.manifest["python_binary"]): self.manifest["python_sha256"],
            self.directory / "suite.json": self.manifest["suite_sha256"],
        }
        pairs.update(
            {
                Path(path): digest
                for path, digest in self.manifest["suite_inputs"].items()
            }
        )
        if source:
            pairs[self.directory / "reviewed.patch"] = self.manifest["patch_sha256"]
            pairs[self.directory / "review.txt"] = self.manifest["review_sha256"]
            if (
                inventory(self.directory / "source")
                != self.manifest["source_inventory"]
            ):
                raise ValueError("Reviewed source changed")
            if "candidate" in self.state:
                pairs[self.directory / "candidate.rhp"] = self.state["candidate"][
                    "sha256"
                ]
        if any(
            not path.is_file() or path.is_symlink() or sha256(path) != expected
            for path, expected in pairs.items()
        ):
            raise ValueError("Pinned trial input changed")

    def invoke(self, action, expected=None, recovery=False):
        self.guards(source=not recovery)
        identifier = f"{len(self.state['events']):03}-{action}-{uuid.uuid4().hex[:6]}"
        request_path = self.directory / (identifier + "-request.json")
        response_path = self.directory / (identifier + "-response.json")
        save(
            request_path,
            {
                "action": action,
                "trial": str(self.directory),
                "source": str(self.directory / "source"),
                "baseline_binary": str(self.directory / "baseline.rhp"),
                "candidate_binary": str(self.directory / "candidate.rhp"),
                "suite": str(self.directory / "suite.json"),
                "suite_inputs": self.manifest["suite_inputs"],
                "expected_identity": expected,
            },
        )
        self.record(action, pending=identifier)
        with (self.directory / (identifier + ".log")).open("wb") as output:
            process = subprocess.Popen(
                [
                    self.manifest["python"],
                    self.manifest["adapter"],
                    str(request_path),
                    str(response_path),
                ],
                cwd=self.directory,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            self.state["child_pid"] = process.pid
            self.state["child_group"] = process.pid
            persist(self.directory / "state.json", self.state)
            try:
                code = process.wait(timeout=self.timeout)
            except BaseException:
                # Kill the complete adapter process group before any restoration.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise
            finally:
                self.state.pop("child_pid", None)
                self.state.pop("child_group", None)
                persist(self.directory / "state.json", self.state)
        if code:
            raise RuntimeError(
                f"{action} failed with exit code {code}; see {identifier}.log"
            )
        response = read(response_path)
        self.guards(source=not recovery)
        self.state.pop("pending", None)
        self.record(
            action + "_done",
            last_response={"path": response_path.name, "sha256": sha256(response_path)},
        )
        return response

    def probe(self, expected, recovery=False):
        actual = self.invoke("probe", expected, recovery)
        if actual != expected:
            raise ValueError("Loaded runtime identity does not match expected binary")

    def test(self, expected, recovery=False):
        result = self.invoke("test", expected, recovery)
        cases = read(self.directory / "suite.json")["cases"]
        if result.get("identity") != expected:
            raise ValueError("Test evidence belongs to another runtime")
        outcomes = result.get("cases", {})
        if set(outcomes) != set(cases) or any(
            type(v) is not bool for v in outcomes.values()
        ):
            raise ValueError("Test evidence has missing, extra or non-boolean verdicts")
        return outcomes

    def restore(self):
        self.record("recovery_required")
        baseline = self.manifest["baseline"]
        self.invoke("restore", baseline, recovery=True)
        self.probe(baseline, recovery=True)
        outcomes = self.test(baseline, recovery=True)
        self.probe(baseline, recovery=True)
        if not all(outcomes.values()):
            raise ValueError("Restored baseline failed its fixed suite")
        self.record("restored", runtime_dirty=False, restored_cases=outcomes)

    def run(self):
        with (
            locked(self.directory / "trial.lock"),
            locked(Path(self.manifest["runtime_lock"])),
        ):
            # Reload after taking locks, so stale Trial objects cannot repeat work.
            self.state = read(self.directory / "state.json")
            self.manifest = read(self.directory / "manifest.json")
            if self.state["stage"] in ("accepted_trial", "rejected"):
                return self.state
            if self.state.get("child_group") or self.state.get("pending"):
                # A controller SIGKILL may leave a detached adapter alive. Never kill
                # a possibly recycled PID or restore concurrently with unknown work.
                self.record(
                    "operator_required",
                    error="Confirm the recorded adapter process has stopped; use --ack-child-stopped",
                )
                return self.state
            try:
                if self.state["stage"] != "ready":
                    raise RuntimeError(
                        "Interrupted trial: reject; do not replay pending action"
                    )
                baseline = self.manifest["baseline"]
                self.probe(baseline)
                baseline_cases = self.test(baseline)
                if not all(baseline_cases.values()):
                    raise ValueError("Baseline does not pass the frozen suite")
                self.record("baseline_verified", baseline_cases=baseline_cases)
                build = self.invoke("build")
                binary = self.directory / "candidate.rhp"
                if (
                    not binary.is_file()
                    or binary.is_symlink()
                    or not isinstance(build.get("mvid"), str)
                    or not build["mvid"]
                ):
                    raise ValueError("Build did not return a candidate binary and MVID")
                candidate = {"sha256": sha256(binary), "mvid": build["mvid"]}
                if build != candidate:
                    raise ValueError("Build identity does not match output bytes")
                self.record("built", candidate=candidate)
                self.guards()
                # Mark uncertainty before installation; even a failed install must recover.
                self.record("install_pending", runtime_dirty=True)
                self.invoke("install", candidate)
                self.probe(candidate)
                outcomes = self.test(candidate)
                self.probe(candidate)
                comparison = {
                    "baseline": baseline_cases,
                    "candidate": outcomes,
                    "regressions": [name for name in outcomes if not outcomes[name]],
                }
                persist(self.directory / "comparison.json", comparison)
                self.record("compared", candidate_passed=all(outcomes.values()))
                if not all(outcomes.values()):
                    raise ValueError("Candidate regressed on the frozen suite")
                self.restore()
                self.record("accepted_trial", promoted=False)
            except Exception as error:
                self.record("failed", error=f"{type(error).__name__}: {error}")
                try:
                    if self.state["runtime_dirty"]:
                        self.restore()
                    else:
                        self.probe(self.manifest["baseline"], recovery=True)
                    self.record("rejected", promoted=False)
                except Exception as recovery_error:
                    self.record("recovery_required", recovery_error=str(recovery_error))
            return self.state

    def acknowledge_child_stopped(self):
        """Operator attestation only; never infer completion from an old process ID."""
        with (
            locked(self.directory / "trial.lock"),
            locked(Path(self.manifest["runtime_lock"])),
        ):
            self.state = read(self.directory / "state.json")
            if self.state["stage"] != "operator_required":
                raise ValueError("No unresolved child process to acknowledge")
            self.state.pop("child_pid", None)
            self.state.pop("child_group", None)
            self.state.pop("pending", None)
            self.record("interrupted", child_stop_acknowledged=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("prepare")
    for name in ("repair", "baseline", "suite", "adapter", "runtime-lock", "review"):
        new.add_argument("--" + name, type=Path, required=True)
    new.add_argument("--baseline-mvid", required=True)
    run = sub.add_parser("run")
    run.add_argument("directory", type=Path)
    run.add_argument("--timeout", type=float, default=180)
    run.add_argument("--ack-child-stopped", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        print(
            prepare(
                args.repair,
                args.baseline,
                args.baseline_mvid,
                args.suite,
                args.adapter,
                args.runtime_lock,
                args.review.read_text(),
            )
        )
        return 0
    trial = Trial(args.directory, args.timeout)
    if args.ack_child_stopped:
        trial.acknowledge_child_stopped()
    result = trial.run()
    print(json.dumps(result, indent=2))
    return 0 if result["stage"] == "accepted_trial" else 1


if __name__ == "__main__":
    raise SystemExit(main())
