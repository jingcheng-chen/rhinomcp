"""Durable admission limits for sequential modeling sessions.

Reservations bound further dispatch, not provider billing. Session timeouts and
gateway call allowances remain the enforcement mechanisms inside each session.
An unaccounted reservation blocks new work after an interruption.
"""

import math

from experiments.trial import locked, persist, read


KEYS = {"sessions", "tool_attempts", "model_seconds"}


def amounts(value, positive=False):
    if set(value) != KEYS or any(
        type(n) not in (int, float)
        or not math.isfinite(n)
        or n < 0
        or (positive and n == 0)
        for n in value.values()
    ):
        raise ValueError("Finite nonnegative resource amounts are required")
    if any(type(value[k]) is not int for k in ("sessions", "tool_attempts")):
        raise ValueError("Session and call counts must be integers")
    return dict(value)


def initialize(path, limits):
    limits = amounts(limits, positive=True)
    with locked(path.with_suffix(".lock")):
        if path.exists():
            raise ValueError("Resource ledger already exists")
        persist(
            path,
            {
                "limits": limits,
                "used": dict.fromkeys(KEYS, 0),
                "pending": None,
                "completed": [],
                "stopped": False,
            },
        )


def reserve(path, name, allowance):
    allowance = amounts(allowance, positive=True)
    with locked(path.with_suffix(".lock")):
        state = read(path)
        if state["pending"] is not None:
            raise RuntimeError("Unaccounted session blocks further dispatch")
        if name in [entry["name"] for entry in state["completed"]]:
            raise RuntimeError("Session must not be replayed")
        if state["stopped"] or any(
            state["used"][k] + allowance[k] > state["limits"][k] for k in KEYS
        ):
            state["stopped"] = True
            persist(path, state)
            raise RuntimeError("Modeling resource limit reached")
        state["pending"] = {"name": name, "allowance": allowance}
        persist(path, state)


def settle(path, name, actual):
    actual = amounts(actual)
    with locked(path.with_suffix(".lock")):
        state = read(path)
        if state["pending"] is None or state["pending"]["name"] != name:
            raise RuntimeError("No matching resource reservation")
        if actual["sessions"] != 1:
            raise ValueError("A completed dispatch accounts for one session")
        state["completed"].append(
            {"name": name, "actual": actual, "allowance": state["pending"]["allowance"]}
        )
        state["used"] = {k: state["used"][k] + actual[k] for k in KEYS}
        state["pending"] = None
        # Record overshoots honestly and stop; never clamp the observed usage.
        state["stopped"] = any(state["used"][k] > state["limits"][k] for k in KEYS)
        persist(path, state)
        return state
