"""Grasshopper saved graph adapter: trusted outputs, topology and analytical targets."""

import base64
import json
import math
from pathlib import Path
import jsonschema

SCHEMA = Path(__file__).with_name("tasks") / "gh_definition.schema.json"


def validate(task):
    jsonschema.validate(task, json.loads(SCHEMA.read_text()))

    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Finite GH task values required")
        if isinstance(value, dict):
            for v in value.values():
                finite(v)
        if isinstance(value, list):
            for v in value:
                finite(v)

    finite(task)
    names = [c["nickname"] for c in task["components"]]
    if len(set(names)) != len(names):
        raise ValueError("Unique required component nicknames required")
    outputs = [o["id"] for o in task["outputs"]]
    if len(set(outputs)) != len(outputs):
        raise ValueError("Unique output IDs required")
    for edge in task["connections"]:
        if edge["source"] not in names or edge["target"] not in names:
            raise ValueError("Connection references unknown required component")
    for o in task["outputs"]:
        if o["nickname"] not in names or len(o["values"]) != o["count"]:
            raise ValueError("Output selector/count inconsistent")
    return task


def matches(actual, expected, tolerance):
    if isinstance(expected, bool):
        return actual is expected
    if isinstance(expected, (float, int)):
        return (
            isinstance(actual, (float, int))
            and not isinstance(actual, bool)
            and math.isfinite(actual)
            and abs(actual - expected) <= tolerance
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(matches(a, e, tolerance) for a, e in zip(actual, expected))
        )
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            k in actual and matches(actual[k], v, tolerance)
            for k, v in expected.items()
        )
    return actual == expected


def evaluate(task, saved):
    checks = {}
    canvas, graph = saved.get("canvas", {}), saved.get("graph", {})
    nodes = canvas.get("components", []) + canvas.get("standalone_parameters", [])
    by_id = {n["instance_id"]: n for n in nodes}
    by_name = {}
    for n in nodes:
        by_name.setdefault(n.get("nickname"), []).append(n)
    solution = saved.get("solution", {})
    checks["solution"] = (
        solution.get("success") is True
        and solution.get("error_count") == 0
        and solution.get("warning_count") == 0
    )
    checks["document"] = (
        saved.get("document", {}).get("has_document") is True
        and saved["document"].get("object_count")
        == len(nodes) + len(canvas.get("groups", []))
        == canvas.get("object_count")
        and len(nodes) == len(by_id)
    )
    graph_ids = {
        n["instance_id"]
        for n in graph.get("components", []) + graph.get("standalone_parameters", [])
    }
    checks["graph_membership"] = (
        graph.get("graph_id") == task["graph_id"]
        and graph_ids == set(by_id)
        and bool(nodes)
    )
    for wanted in task["components"]:
        hits = by_name.get(wanted["nickname"], [])
        checks["component:" + wanted["nickname"]] = (
            len(hits) == 1
            and hits[0]["name"] == wanted["name"]
            and hits[0].get("enabled", True) is True
        )

    def selected(nickname):
        hits = by_name.get(nickname, [])
        return hits[0] if len(hits) == 1 else {}

    adjacency = {key: set() for key in by_id}
    for target in nodes:
        for port in target.get("inputs", []):
            for source in port.get("sources", []):
                if source["component_id"] in adjacency:
                    adjacency[source["component_id"]].add(target["instance_id"])
    # Standalone sources are represented by recipient lists on component outputs.
    for source in nodes:
        for port in source.get("outputs", []):
            for target in port.get("recipients", []):
                if target["component_id"] in by_id:
                    adjacency[source["instance_id"]].add(target["component_id"])
    for i, edge in enumerate(task["connections"]):
        source, target = selected(edge["source"]), selected(edge["target"])
        sp = next(
            (
                p
                for p in source.get("outputs", [])
                if p["index"] == edge["output_index"]
            ),
            None,
        )
        tp = next(
            (p for p in target.get("inputs", []) if p["index"] == edge["input_index"]),
            None,
        )
        checks[f"connection:{i}"] = bool(
            sp
            and tp
            and any(
                s["component_id"] == source.get("instance_id")
                and s["param_name"] == sp["name"]
                for s in tp.get("sources", [])
            )
        )
    sinks = {selected(o["nickname"]).get("instance_id") for o in task["outputs"]}

    def reaches_output(key):
        visited = set()
        todo = [key]
        while todo:
            n = todo.pop()
            if n in sinks:
                return True
            if n not in visited:
                visited.add(n)
                todo.extend(adjacency.get(n, ()))
        return False

    checks["no_orphans"] = bool(nodes) and all(reaches_output(key) for key in by_id)
    for target in task["outputs"]:
        data = saved.get("outputs", {}).get(target["id"], {})
        values = [v for b in data.get("values", []) for v in b.get("items", [])]
        checks["output:" + target["id"]] = (
            data.get("instance_id") == selected(target["nickname"]).get("instance_id")
            and data.get("param_name") == target["parameter_name"]
            and data.get("truncated") is False
            and data.get("data_count") == len(values) == target["count"]
            and matches(values, target["values"], target["tolerance"])
        )
        if "bounds" in target:
            points = values
            try:
                bounds = [
                    [min(p[i] for p in points) for i in range(3)],
                    [max(p[i] for p in points) for i in range(3)],
                ]
                checks["bounds:" + target["id"]] = matches(
                    bounds, target["bounds"], target["tolerance"]
                )
            except (TypeError, IndexError, ValueError):
                checks["bounds:" + target["id"]] = False
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "failed": [k for k, v in checks.items() if not v],
        "family": task["family"],
    }


def snapshot(task, serial, marker, document_id):
    from experiments.workflow.gh_ownership import command, guard

    def read(name, params=None):
        guard(serial, marker, document_id)
        result = command(name, params)
        guard(serial, marker, document_id)
        return result

    saved = {
        "solution": read("gh_run_solution", {"expire_all": True}),
        "document": read("gh_get_document_info"),
        "graph": read(
            "gh_get_graph", {"graph_id": task["graph_id"], "include_values": False}
        ),
        "canvas": read(
            "gh_get_canvas_state",
            {"include_connections": True, "include_values": False},
        ),
        "outputs": {},
    }
    for o in task["outputs"]:
        try:
            saved["outputs"][o["id"]] = read(
                "gh_get_parameter_value",
                {
                    "nickname": o["nickname"],
                    "output_index": o["output_index"],
                    "max_items": 1000,
                },
            )
        except Exception as error:
            guard(serial, marker, document_id)
            saved["outputs"][o["id"]] = {"error": str(error)}
    return saved


def capture(directory, serial, marker, document_id):
    from experiments.workflow.gh_ownership import command, guard

    guard(serial, marker, document_id)
    try:
        result = command("gh_capture_preview", {"width": 1000, "height": 750})
        (directory / "perspective.png").write_bytes(
            base64.b64decode(result["image_data"])
        )
    except Exception as error:
        (directory / "preview-error.json").write_text(json.dumps({"error": str(error)}))
    guard(serial, marker, document_id)
