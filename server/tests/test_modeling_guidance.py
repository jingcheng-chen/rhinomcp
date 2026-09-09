"""Distribution-facing guide interfaces must agree and work without Rhino."""

import pytest
import rhinomcp
from rhinomcp.guidance import modeling_guidance, TOPICS, SERVER_INSTRUCTIONS
from rhinomcp.prompts.assert_general_strategy import asset_general_strategy
from rhinomcp.tools.get_modeling_guidance import (
    get_modeling_guidance,
    modeling_guidance_resource,
)


@pytest.mark.parametrize("topic", TOPICS)
def test_offline_interfaces_share_packaged_content(topic, monkeypatch):
    def fail():
        pytest.fail("Documentation attempted a Rhino connection")

    monkeypatch.setattr("rhinomcp.server.get_rhino_connection", fail)
    result = get_modeling_guidance(topic)
    assert result["guidance_version"] == "2"
    assert result["package_version"]
    assert result["content"].startswith("# ")
    assert result["content"] == modeling_guidance_resource(topic)
    assert result["available_topics"] == list(TOPICS)
    if topic == "overview":
        assert asset_general_strategy() == result["content"]


@pytest.mark.parametrize(
    "topic", ["../server", "/etc/passwd", "https://example.com", "", "unknown"]
)
def test_unknown_topics_never_become_paths(topic):
    with pytest.raises(ValueError, match="Unknown guidance topic"):
        modeling_guidance(topic)


@pytest.mark.asyncio
async def test_mcp_discovery_exposes_readonly_guide_and_topic_enum():
    tool = next(
        t for t in await rhinomcp.mcp.list_tools() if t.name == "get_modeling_guidance"
    )
    assert tool.annotations.readOnlyHint is True
    assert tool.annotations.openWorldHint is False
    assert set(tool.inputSchema["properties"]["topic"]["enum"]) == set(TOPICS)
    assert rhinomcp.mcp.instructions == SERVER_INSTRUCTIONS
    templates = await rhinomcp.mcp.list_resource_templates()
    assert "rhinomcp://guidance/{topic}" in {str(t.uriTemplate) for t in templates}
