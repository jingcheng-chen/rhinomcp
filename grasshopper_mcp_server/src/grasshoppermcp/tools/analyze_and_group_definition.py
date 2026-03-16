"""Analyze a Grasshopper definition and create semantic groups."""

from mcp.server.fastmcp import Context
from grasshoppermcp.server import get_grasshopper_connection, mcp, logger
from typing import Dict, Any


@mcp.tool()
def analyze_and_group_definition(
    strategy: str = "auto",
    min_group_size: int = 2,
    include_diagram: bool = True,
    color_palette: str = "default",
    remove_existing_groups: bool = False,
    reorganize_layout: bool = False,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Analyze a Grasshopper definition's component graph, classify components into
    semantic functional groups, create colored GH_Group objects on the canvas,
    and optionally reorganize the layout to visualize the workflow.

    Args:
        strategy: Grouping strategy. Options:
            - "auto" / "by_workflow" (default): Finds natural bottlenecks in the
              dataflow graph to identify functional workflow sections. Refines
              assignments based on connectivity. Best for most definitions.
            - "by_depth": One group per topological depth level, then merges small
              groups. Useful for strict depth-based analysis.
            - "by_category": Groups by component category (Math, Curve, Transform,
              etc.). Useful when functional sections align with GH categories.
        min_group_size: Minimum number of components per group. Smaller groups are
            merged into the most-connected neighbor. Default: 2.
        include_diagram: Whether to generate a Mermaid workflow diagram. Default: True.
        color_palette: Color palette for groups. Options:
            - "default": Balanced semi-transparent colors.
            - "pastel": Soft pastel tones.
            - "vivid": High-contrast vivid colors.
        remove_existing_groups: If True, removes all existing GH_Group objects before
            creating new ones. Default: False.
        reorganize_layout: If True, repositions all components on the canvas to
            arrange groups left-to-right with internal depth columns, creating a
            clean workflow visualization. Default: False.

    Returns:
        - summary: Text summary of the analysis
        - definition_purpose: Heuristic classification (e.g. "surface_modeling", "computational")
        - groups_created: Number of groups created on canvas
        - component_count: Total components analyzed
        - connection_count: Total connections found
        - subgraph_count: Number of disconnected subgraphs
        - layout_reorganized: Whether layout was changed
        - groups: List of group details (name, color, components, depth range)
        - workflow_diagram: Mermaid diagram string (if include_diagram is True)
        - message: Summary message

    Example:
        result = analyze_and_group_definition(strategy="auto", reorganize_layout=True)
        print(result["summary"])
        print(result["workflow_diagram"])
    """
    try:
        gh = get_grasshopper_connection()
        return gh.send_command(
            "analyze_and_group_definition",
            {
                "strategy": strategy,
                "min_group_size": min_group_size,
                "include_diagram": include_diagram,
                "color_palette": color_palette,
                "remove_existing_groups": remove_existing_groups,
                "reorganize_layout": reorganize_layout,
            },
        )
    except Exception as e:
        logger.error(f"Error analyzing definition: {str(e)}")
        return {"success": False, "message": str(e)}
