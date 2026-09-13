"""Supervisor-only held-out allocation. Sealing is a workflow boundary, not M5 isolation."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


def encoded(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9_-]{0,95}", value
    ):
        raise ValueError("Use a stable lowercase identifier")
    return value


def read(bank):
    events = json.loads(bank.read_text())
    if not isinstance(events, list) or not events:
        raise ValueError("Empty or invalid allocation ledger")
    previous = None
    entries, excluded, validations = {}, set(), set()
    for index, event in enumerate(events):
        if set(event) != {"previous", "at", "body", "sha256"}:
            raise ValueError("Invalid ledger event")
        core = {k: event[k] for k in ("previous", "at", "body")}
        if event["previous"] != previous or event["sha256"] != digest(encoded(core)):
            raise ValueError("Allocation ledger hash mismatch")
        previous = event["sha256"]
        body = event["body"]
        kind = body["kind"]
        if index == 0:
            if kind != "initialize" or body["version"] != 1:
                raise ValueError("Missing ledger genesis")
            excluded = set(body["discovery_families"])
            continue
        if kind in {"seal", "historical_spend"}:
            key, family = identifier(body["id"]), identifier(body["family"])
            if (
                key in entries
                or family in excluded
                or any(e["family"] == family for e in entries.values())
            ):
                raise ValueError(
                    "Family is already known; renaming a case does not renew it"
                )
            replacement = body.get("replaces")
            if replacement is not None:
                if (
                    replacement not in entries
                    or entries[replacement]["state"] != "spent"
                    or any(e.get("replaces") == replacement for e in entries.values())
                ):
                    raise ValueError(
                        "Replacement must cover one previously spent family"
                    )
            entries[key] = {**body, "state": "available" if kind == "seal" else "spent"}
            if kind == "historical_spend":
                validations.add(body["validation"])
        elif kind == "spend":
            entry = entries[body["id"]]
            if entry["state"] != "available" or body["validation"] in validations:
                raise ValueError(
                    "A validation gets one fresh family; spent families cannot be reused"
                )
            entry.update(
                state="spent",
                validation=body["validation"],
                review_sha256=body["review_sha256"],
                retired=body.get("retired", False),
            )
            validations.add(body["validation"])
        elif kind == "close":
            entry = entries[body["id"]]
            if (
                entry["state"] != "spent"
                or "closure" in entry
                or not any(
                    e.get("replaces") == body["id"] and e["state"] == "available"
                    for e in entries.values()
                )
            ):
                raise ValueError(
                    "Closing requires a spent family and a sealed replacement"
                )
            if body["outcome"] not in {"kept", "rejected", "incomplete", "abandoned"}:
                raise ValueError("Unknown validation outcome")
            entry["closure"] = body
        else:
            raise ValueError("Unknown allocation event")
    return events, entries, excluded


def write(bank, events):
    bank.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=bank.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(json.dumps(events, indent=2).encode() + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    try:
        read(temporary)  # Validate the complete next state before replacing anything.
        os.replace(temporary, bank)
        descriptor = os.open(bank.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def locked(bank):
    bank.parent.mkdir(parents=True, exist_ok=True)
    with bank.with_suffix(bank.suffix + ".lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def append(bank, body):
    events = read(bank)[0] if bank.exists() else []
    core = {
        "previous": events[-1]["sha256"] if events else None,
        "at": datetime.now(timezone.utc).isoformat(),
        "body": body,
    }
    write(bank, [*events, {**core, "sha256": digest(encoded(core))}])


def initialize(bank, discovery_families):
    with locked(bank):
        if bank.exists():
            raise ValueError("Ledger already exists")
        families = sorted({identifier(f) for f in discovery_families})
        if not families:
            raise ValueError("Declare the discovery exclusion set")
        append(
            bank, {"kind": "initialize", "version": 1, "discovery_families": families}
        )


def payload(value):
    if set(value) != {
        "id",
        "family",
        "novelty_review",
        "calibration_required",
        "cases",
    }:
        raise ValueError("Invalid sealed bundle fields")
    identifier(value["id"])
    identifier(value["family"])
    if (
        not value["novelty_review"].strip()
        or value["calibration_required"] is not True
        or len(value["cases"]) < 2
    ):
        raise ValueError(
            "A reviewed bundle needs at least two cases and future calibration"
        )
    names = set()
    for case in value["cases"]:
        if (
            set(case) != {"id", "instruction", "parameters", "acceptance"}
            or not case["instruction"].strip()
            or not isinstance(case["parameters"], dict)
            or not case["parameters"]
            or not isinstance(case["acceptance"], list)
            or not case["acceptance"]
        ):
            raise ValueError(
                "Each case needs fixed parameters, instructions and acceptance"
            )
        name = identifier(case["id"])
        if name in names:
            raise ValueError("Duplicate case")
        names.add(name)
    return encoded(value)


def seal(bank, vault, value, replaces=None):
    data = payload(value)
    with locked(bank):
        events, entries, excluded = read(bank)
        if (
            value["family"] in excluded
            or value["id"] in entries
            or any(e["family"] == value["family"] for e in entries.values())
        ):
            raise ValueError("Family already known")
        if replaces is not None and (
            replaces not in entries
            or entries[replaces]["state"] != "spent"
            or any(e.get("replaces") == replaces for e in entries.values())
        ):
            raise ValueError("Replacement must cover one previously spent family")
        # Never overwrite private content, even if ledger registration previously failed.
        vault.mkdir(parents=True, exist_ok=True, mode=0o700)
        vault.chmod(0o700)
        path = vault / (value["id"] + ".json")
        with path.open("xb") as handle:
            os.chmod(path, 0o600)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        append(
            bank,
            {
                "kind": "seal",
                "id": value["id"],
                "family": value["family"],
                "payload_sha256": digest(data),
                "cases": len(value["cases"]),
                "novelty_review": value["novelty_review"],
                "calibration_required": True,
                "replaces": replaces,
            },
        )


def checked_payload(vault, entry):
    data = (vault / (identifier(entry["id"]) + ".json")).read_bytes()
    if digest(data) != entry["payload_sha256"]:
        raise ValueError("Sealed parameterization changed")
    value = json.loads(data)
    if (
        payload(value) != data
        or value["id"] != entry["id"]
        or value["family"] != entry["family"]
    ):
        raise ValueError("Bundle does not match its commitment")
    return data


def expose(bank, vault, key, validation, output, review=None):
    """Spend durably before disclosure; re-export only the same spent allocation."""
    identifier(validation)
    with locked(bank):
        entry = read(bank)[1][key]
        data = checked_payload(vault, entry)
        if review is not None:
            if not review.read_text().strip():
                raise ValueError("Predeclared validation review is required")
            append(
                bank,
                {
                    "kind": "spend",
                    "id": key,
                    "validation": validation,
                    "review_sha256": digest(review.read_bytes()),
                },
            )
        elif (
            entry["state"] != "spent"
            or entry.get("retired")
            or entry.get("validation") != validation
            or "closure" in entry
        ):
            raise ValueError("Recovery export must belong to the same open validation")
        # If this fails, the family remains spent. Never roll the allocation back.
        with output.open("xb") as handle:
            os.chmod(output, 0o600)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())


def retire(bank, key, validation, review):
    """Burn leaked/lost/damaged cases without requiring or revealing their payload."""
    identifier(validation)
    with locked(bank):
        if not review.read_text().strip():
            raise ValueError("Incident review required")
        append(
            bank,
            {
                "kind": "spend",
                "id": key,
                "validation": validation,
                "review_sha256": digest(review.read_bytes()),
                "retired": True,
            },
        )


def close(bank, key, outcome, report):
    with locked(bank):
        if not report.read_text().strip():
            raise ValueError("Preserved outcome report required")
        append(
            bank,
            {
                "kind": "close",
                "id": key,
                "outcome": outcome,
                "report_sha256": digest(report.read_bytes()),
            },
        )


def status(bank, vault):
    events, entries, excluded = read(bank)
    for entry in entries.values():
        if entry["kind"] != "seal":
            continue
        try:
            checked_payload(vault, entry)
            entry["payload_status"] = "verified"
        except FileNotFoundError:
            entry["payload_status"] = "unavailable"
        except ValueError:
            entry["payload_status"] = "changed"
    return {
        "ledger_sha256": digest(bank.read_bytes()),
        "head": events[-1]["sha256"],
        "discovery_families": sorted(excluded),
        "entries": entries,
        "ready_families": sum(
            e["state"] == "available" and e.get("payload_status") == "verified"
            for e in entries.values()
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bank", type=Path, default=Path("experiments/workflow/held-out-bank.json")
    )
    parser.add_argument(
        "--vault", type=Path, default=Path("experiments/held_out_private")
    )
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("status")
    p = commands.add_parser("seal")
    p.add_argument("bundle", type=Path)
    p.add_argument("--replaces")
    for action in ("spend", "export", "retire"):
        p = commands.add_parser(action)
        p.add_argument("id")
        p.add_argument("--validation", required=True)
        if action != "retire":
            p.add_argument("--output", type=Path, required=True)
        if action in {"spend", "retire"}:
            p.add_argument("--review-file", type=Path, required=True)
    p = commands.add_parser("close")
    p.add_argument("id")
    p.add_argument(
        "--outcome",
        choices=["kept", "rejected", "incomplete", "abandoned"],
        required=True,
    )
    p.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "seal":
        seal(args.bank, args.vault, json.loads(args.bundle.read_text()), args.replaces)
    elif args.action in {"spend", "export"}:
        expose(
            args.bank,
            args.vault,
            args.id,
            args.validation,
            args.output,
            getattr(args, "review_file", None),
        )
    elif args.action == "retire":
        retire(args.bank, args.id, args.validation, args.review_file)
    elif args.action == "close":
        close(args.bank, args.id, args.outcome, args.report)
    print(json.dumps(status(args.bank, args.vault), indent=2))
