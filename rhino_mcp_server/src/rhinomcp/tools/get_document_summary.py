from mcp.server.fastmcp import Context
import json
from rhinomcp import get_rhino_connection, mcp, logger


@mcp.tool()
def get_document_summary(ctx: Context) -> str:
    """
    Get a lightweight summary of the current Rhino document.

    This returns aggregated statistics about the model without individual object details:
    - Document metadata (name, units, tolerance, dates)
    - Total object count
    - Object counts grouped by type (e.g., 50 curves, 30 surfaces)
    - Object counts grouped by layer
    - Model-wide bounding box encompassing all objects
    - Full layer hierarchy with parent-child relationships and per-layer object counts

    Use this tool first to understand the model composition before querying specific objects.
    For detailed object information, use get_objects with filters.
    """
    try:
        rhino = get_rhino_connection()
        result = rhino.send_command("get_document_summary")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting document summary from Rhino: {str(e)}")
        return f"Error getting document summary: {str(e)}"
