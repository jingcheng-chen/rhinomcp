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
    assert result["guidance_version"] == "3"
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
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.open_world_hint is False
    assert set(tool.input_schema["properties"]["topic"]["enum"]) == set(TOPICS)
    assert rhinomcp.mcp.instructions == SERVER_INSTRUCTIONS
    templates = await rhinomcp.mcp.list_resource_templates()
    assert "rhinomcp://guidance/{topic}" in {str(t.uri_template) for t in templates}


def _section(text, start, end):
    """The part of text from the first `start` up to the next `end`."""
    head = text.index(start)
    return text[head : text.index(end, head)]


def test_instructions_ground_first_and_verify_with_capture_metadata():
    # Sent to every client every session: grounding and verification must be
    # named there, not left for the agent to discover.
    instructions = rhinomcp.mcp.instructions
    assert "Call get_context before the first edit" in instructions
    assert "after large changes" in instructions
    assert "capture_viewport metadata" in instructions
    assert len(instructions) < 900


def test_overview_names_get_context_as_the_first_call():
    content = modeling_guidance("overview")["content"]
    first_step = _section(content, "1. ", "\n2. ")
    assert "get_context" in first_step
    assert "get_document_summary" in first_step
    assert "set_camera" in content and "zoom_to" in content
    # Same words as the server instructions, so every entry point agrees.
    assert "Call get_context before the first edit" in content


@pytest.mark.parametrize("topic", ["overview", "verification"])
def test_grounding_and_metadata_sentences_match_across_topics(topic):
    # One wording on every topic that names them, so the entry points agree.
    content = " ".join(modeling_guidance(topic)["content"].split())
    assert "Call get_context before the first edit" in content
    assert "Read the capture_viewport metadata before trusting a picture." in content


def test_verification_grounds_first_in_its_opening_paragraph():
    content = modeling_guidance("verification")["content"]
    opening = content.split("\n\n")[1]
    assert "Call get_context before the first edit" in " ".join(opening.split())


def test_verification_reads_capture_metadata_before_trusting_the_picture():
    content = modeling_guidance("verification")["content"]
    for field in (
        "viewport_name",
        "display_mode",
        "projection",
        "camera_location",
        "camera_target",
        "camera_up",
        "lens_length",
        "scene_bounding_box",
        "visible_object_count",
        "total_object_count",
    ):
        assert field in content, field
    assert "capture_viewport metadata" in content
    assert "frame_object_ids" in content
    assert "never moves the user's view" in content
    assert "code: message" in content
