using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Undo the last operation in the Rhino document.
    /// </summary>
    public JObject Undo(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;

        // Get number of undo steps (default 1)
        int steps = parameters["steps"]?.ToObject<int>() ?? 1;

        int undoneCount = 0;
        for (int i = 0; i < steps; i++)
        {
            if (doc.Undo())
            {
                undoneCount++;
            }
            else
            {
                break; // No more undo records available
            }
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["undone_steps"] = undoneCount,
            ["requested_steps"] = steps,
            ["message"] = undoneCount > 0
                ? $"Undid {undoneCount} operation(s)"
                : "Nothing to undo"
        };
    }

    /// <summary>
    /// Redo the last undone operation in the Rhino document.
    /// </summary>
    public JObject Redo(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;

        // Get number of redo steps (default 1)
        int steps = parameters["steps"]?.ToObject<int>() ?? 1;

        int redoneCount = 0;
        for (int i = 0; i < steps; i++)
        {
            if (doc.Redo())
            {
                redoneCount++;
            }
            else
            {
                break; // No more redo records available
            }
        }

        doc.Views.Redraw();

        return new JObject
        {
            ["redone_steps"] = redoneCount,
            ["requested_steps"] = steps,
            ["message"] = redoneCount > 0
                ? $"Redid {redoneCount} operation(s)"
                : "Nothing to redo"
        };
    }
}
