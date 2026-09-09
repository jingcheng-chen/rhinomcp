"""Versioned modeling knowledge shipped with the server, independent of Rhino."""

from importlib import metadata, resources

GUIDANCE_VERSION = "1"
TOPICS = (
    "overview",
    "transforms",
    "planar_regions",
    "organization",
    "verification",
    "recovery",
)
SERVER_INSTRUCTIONS = (
    "RhinoMCP provides Rhino modeling tools and bundled workflow guidance. "
    "Use get_modeling_guidance(topic) for overview, transforms, planar_regions, "
    "organization, verification or recovery when relevant. Consult transforms "
    "before composing world poses. Inspect existing user work before edits, and "
    "verify geometry against the request instead of treating tool success as acceptance."
)


def modeling_guidance(topic="overview"):
    """Read a fixed packaged topic; never accept arbitrary paths or URLs."""
    if topic not in TOPICS:
        raise ValueError(
            f"Unknown guidance topic {topic!r}; choose from {', '.join(TOPICS)}"
        )
    try:
        package_version = metadata.version("rhinomcp")
    except metadata.PackageNotFoundError:
        package_version = "0+unknown"
    content = (
        resources.files("rhinomcp")
        .joinpath("guides", f"{topic}.md")
        .read_text(encoding="utf-8")
    )
    return {
        "guidance_version": GUIDANCE_VERSION,
        "package_version": package_version,
        "topic": topic,
        "available_topics": list(TOPICS),
        "content": content,
    }
