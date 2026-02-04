from mcp.server.fastmcp import Context
import json
from rhinomcp.server import get_rhino_connection, mcp, logger
from typing import Any, List, Dict, Optional


@mcp.tool()
def execute_rhinoscript_python_code(
    ctx: Context,
    code: str,
    verified_functions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Execute RhinoScript Python code in Rhino.

    CRITICAL - BEFORE USING THIS TOOL:
    =================================
    You MUST call get_rhinoscript_docs() or search_rhinoscript_functions() first
    to find the correct function signatures. DO NOT guess function names or parameters.

    Required Workflow:
    1. Call get_rhinoscript_docs("your goal") to find relevant functions
    2. Read the documentation carefully - note exact signatures and parameter types
    3. Write code using ONLY the documented signatures
    4. Call this tool with the code

    Parameters:
    - code: The RhinoScript Python code to execute
    - verified_functions: (Optional) List of function names you looked up in documentation.
                          Providing this helps ensure you've verified the syntax.

    Code Requirements:
    - Import rhinoscriptsyntax: `import rhinoscriptsyntax as rs`
    - Use print() to return output/results to the caller
    - Use EXACT function signatures from documentation
    - Handle None returns from functions that might fail

    Example Workflow:
    -----------------
    Task: "Create a loft surface between two curves"

    Step 1: get_rhinoscript_docs("loft surface curves")
            -> Returns AddLoftSrf documentation with exact signature

    Step 2: Read that AddLoftSrf takes object_ids (list of curve GUIDs)

    Step 3: Write and execute:
    ```python
    import rhinoscriptsyntax as rs

    # Get the curves (assumes they exist)
    curves = rs.GetObjects("Select curves for loft", rs.filter.curve)
    if curves:
        loft = rs.AddLoftSrf(curves)
        print(f"Created loft: {loft}")
    ```

    Common Mistakes to Avoid:
    - Using non-existent functions (ALWAYS verify with docs first)
    - Wrong parameter order (check signature carefully)
    - Wrong parameter types (e.g., passing Point3d when list expected)
    - Forgetting to import rhinoscriptsyntax

    Returns:
    - success: Whether the code executed successfully
    - output: Any print() output from the script
    - message: Error message if failed

    Any changes made to the document will be undone if the script fails.
    """
    try:
        # Log if verified_functions was provided (good practice indicator)
        if verified_functions:
            logger.info(f"Executing code with verified functions: {verified_functions}")
        else:
            logger.warning("Executing code without verified_functions - ensure docs were checked")

        # Get the global connection
        rhino = get_rhino_connection()

        return rhino.send_command("execute_rhinoscript_python_code", {"code": code})

    except Exception as e:
        logger.error(f"Error executing code: {str(e)}")
        return {"success": False, "message": str(e)}
