"""Reviewed stock-component boundary for supervised GH trials, not M5 isolation."""

import json
import math
from pathlib import Path

CATALOG = Path(__file__).with_name("gh-reviewed-components.json")
REVIEWED_TOOLS = frozenset(
    """gh_create_document gh_get_document_info gh_get_canvas_state gh_search_components gh_batch_search_components gh_list_component_categories gh_get_available_components gh_get_component_type_info gh_batch_get_component_type_info gh_list_components gh_get_component_info gh_add_component gh_layout_components gh_delete_component gh_update_component gh_clear_canvas gh_run_solution gh_expire_solution gh_capture_preview gh_set_parameter_value gh_get_parameter_value gh_build_graph gh_mutate_graph gh_get_graph gh_clear_graph gh_connect_components gh_disconnect_components""".split()
)


def validate_call(name, arguments, object_count):
    if name not in REVIEWED_TOOLS:
        raise ValueError("Tool outside reviewed Grasshopper scope")
    catalog = json.loads(CATALOG.read_text())
    guids = {c["guid"] for c in catalog}
    names = {c["name"] for c in catalog}

    def bounded(v, depth=0):
        if depth > 12:
            raise ValueError("GH argument nesting budget exceeded")
        if (
            isinstance(v, (int, float))
            and not isinstance(v, bool)
            and (not math.isfinite(v) or abs(v) > 10000)
        ):
            raise ValueError("Finite bounded GH inputs required")
        if isinstance(v, str) and len(v) > 2000:
            raise ValueError("GH text budget exceeded")
        if isinstance(v, (dict, list)):
            if len(v) > 100:
                raise ValueError("GH collection budget exceeded")
            for child in v.values() if isinstance(v, dict) else v:
                bounded(child, depth + 1)

    bounded(arguments)
    specs = []
    if name == "gh_add_component":
        specs = [arguments]
    if name == "gh_build_graph":
        specs = arguments.get("components", [])
    if name == "gh_mutate_graph":
        specs = [
            op for op in arguments.get("operations", []) if op.get("op") == "create"
        ]
    if object_count + len(specs) > 32:
        raise ValueError("GH object budget exceeded")
    if name == "gh_get_component_type_info":
        specs = [arguments]
    elif name == "gh_batch_get_component_type_info":
        specs = arguments.get("components", [])
    for spec in specs:
        guid = spec.get("guid") or spec.get("component_guid")
        if (guid and guid.lower() not in guids) or (
            not guid and (spec.get("name") or spec.get("component_name")) not in names
        ):
            raise ValueError(
                "Component outside reviewed stock math/geometry catalog; script, file and external plugin components refused on host"
            )
    if name == "gh_create_document" and any(
        arguments.get(k, True) is not True
        for k in ["new_if_missing", "make_active", "open_canvas"]
    ):
        raise ValueError("GH document creation must keep the owned canvas active")
