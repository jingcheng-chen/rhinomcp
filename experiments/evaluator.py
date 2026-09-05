"""Analytic acceptance checks; no agent-written scores are trusted."""

import math


def evaluate(task, measurements):
    objects = measurements.get("objects", [])
    checks = {
        "units": measurements.get("units") == task["units"],
        "object_count": len(objects) == 1,
    }
    if len(objects) == 1:
        obj = objects[0]
        checks.update(valid=obj.get("valid") is True, solid=obj.get("solid") is True)
        for key in ("minimum", "dimensions"):
            values = obj.get(key, [])
            checks[key] = len(values) == 3 and all(
                isinstance(actual, (int, float))
                and math.isfinite(actual)
                and abs(actual - expected) <= task["linear_tolerance"]
                for actual, expected in zip(values, task[key])
            )
        volume = obj.get("volume")
        checks["volume"] = (
            isinstance(volume, (int, float))
            and math.isfinite(volume)
            and abs(volume - math.prod(task["dimensions"])) <= task["volume_tolerance"]
        )
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "measurements": measurements,
    }
