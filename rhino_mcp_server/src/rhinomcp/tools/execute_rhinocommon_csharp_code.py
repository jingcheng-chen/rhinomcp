from mcp.server.fastmcp import Context
from rhinomcp.server import get_rhino_connection, mcp, logger
from typing import Any, List, Dict, Optional


@mcp.tool()
def execute_rhinocommon_csharp_code(
    ctx: Context,
    code: str,
) -> Dict[str, Any]:
    """
    Execute RhinoCommon C# code directly in Rhino.

    This tool allows you to execute C# code that uses the RhinoCommon API directly.
    The code is compiled and executed at runtime using Roslyn.

    IMPORTANT NOTES:
    ================
    1. The code runs in a scripting context with the following globals available:
       - `doc`: The active RhinoDoc (Rhino.RhinoDoc)
       - `output`: A StringBuilder to capture output (use output.AppendLine("..."))

    2. Common namespaces are pre-imported:
       - System, System.Collections.Generic, System.Linq
       - Rhino, Rhino.Geometry, Rhino.DocObjects, Rhino.Commands

    3. Use `output.AppendLine()` to return results to the caller (like print() in Python)

    Parameters:
    - code: The C# code to execute

    Example Usage:
    --------------
    Task: "Create a sphere at the origin"

    ```csharp
    var sphere = new Sphere(Point3d.Origin, 5.0);
    var brep = sphere.ToBrep();
    doc.Objects.AddBrep(brep);
    doc.Views.Redraw();
    output.AppendLine($"Created sphere with radius 5 at origin");
    ```

    Task: "List all curves in the document"

    ```csharp
    var curves = doc.Objects.FindByObjectType(ObjectType.Curve);
    output.AppendLine($"Found {curves.Length} curves:");
    foreach (var obj in curves)
    {
        output.AppendLine($"  - {obj.Id}: {obj.Name ?? "(unnamed)"}");
    }
    ```

    Task: "Create a line between two points"

    ```csharp
    var start = new Point3d(0, 0, 0);
    var end = new Point3d(10, 10, 0);
    var line = new Line(start, end);
    doc.Objects.AddLine(line);
    doc.Views.Redraw();
    output.AppendLine($"Created line from {start} to {end}");
    ```

    Common Mistakes to Avoid:
    - Forgetting to use `output.AppendLine()` to return results
    - Not calling `doc.Views.Redraw()` after adding objects
    - Using types without their namespace (use Point3d, not Rhino.Geometry.Point3d)

    Returns:
    - success: Whether the code executed successfully
    - output: Any output from output.AppendLine() calls
    - message: Error message if failed (includes compilation errors)

    Any changes made to the document will be undone if the script fails.
    """
    try:
        logger.info("Executing RhinoCommon C# code")

        # Get the global connection
        rhino = get_rhino_connection()

        return rhino.send_command("execute_rhinocommon_csharp_code", {"code": code})

    except Exception as e:
        logger.error(f"Error executing C# code: {str(e)}")
        return {"success": False, "message": str(e)}
