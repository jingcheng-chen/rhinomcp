"""Every tool a client lists carries a title, a read-only hint and a
destructive hint, so clients can display and gate tools consistently."""

import pytest

import rhinomcp

READ_ONLY_PREFIXES = (
    "get_",
    "describe_",
    "search_",
    "list_",
    "capture_",
    "gh_get_",
    "gh_search_",
    "gh_list_",
    "gh_batch_get_",
    "gh_batch_search_",
    "gh_capture_",
)
# Inspection tools whose names do not start with a read-only verb.
ALSO_READ_ONLY = {"analyze_objects", "measure_objects", "section_profile"}
# Named like a getter, but changes the document's current layer.
NOT_READ_ONLY = {"get_or_set_current_layer"}
DESTRUCTIVE = {
    "execute_rhinoscript_python_code",
    "execute_rhinocommon_csharp_code",
    "run_command",
    "delete_object",
    "delete_layer",
    "boolean_union",
    "boolean_difference",
    "boolean_intersection",
    "gh_clear_canvas",
    "gh_clear_graph",
    "gh_delete_component",
}


async def _tools():
    # rhinomcp.mcp, not rhinomcp.server.mcp: some tests reload the server module.
    return await rhinomcp.mcp.list_tools()


@pytest.mark.asyncio
async def test_every_tool_has_a_title_and_both_hints():
    tools = await _tools()
    assert len(tools) >= 70
    missing = [
        t.name
        for t in tools
        if not t.title
        or t.annotations is None
        or not t.annotations.title
        or t.annotations.read_only_hint is None
        or t.annotations.destructive_hint is None
        or t.annotations.open_world_hint is not False
    ]
    assert missing == []


@pytest.mark.asyncio
async def test_hints_follow_the_tool_kind():
    wrong = []
    for t in await _tools():
        read_only = (
            t.name.startswith(READ_ONLY_PREFIXES) or t.name in ALSO_READ_ONLY
        ) and t.name not in NOT_READ_ONLY
        destructive = t.name in DESTRUCTIVE
        if t.annotations.read_only_hint is not read_only:
            wrong.append((t.name, "read_only_hint", t.annotations.read_only_hint))
        if t.annotations.destructive_hint is not destructive:
            wrong.append((t.name, "destructive_hint", t.annotations.destructive_hint))
    assert wrong == []
