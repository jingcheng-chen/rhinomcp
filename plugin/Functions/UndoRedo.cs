using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Undo the last operation in the Rhino document.
    /// </summary>
    [McpCommand("undo", ReadOnly = true)]
    public JObject Undo(JObject parameters)
    {
        RefuseInsideUndoGroup("undo");
        var doc = RhinoDoc.ActiveDoc;

        // Get number of undo steps (default 1)
        int steps = parameters["steps"]?.ToObject<int>() ?? 1;

        uint openBefore = doc.CurrentUndoRecordSerialNumber;
        int undoneCount = 0;
        for (int i = 0; i < steps; i++)
        {
            bool undone = doc.Undo();
            EndUndoRecordLeftOpen(doc, openBefore);
            if (undone)
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
    [McpCommand("redo", ReadOnly = true)]
    public JObject Redo(JObject parameters)
    {
        RefuseInsideUndoGroup("redo");
        var doc = RhinoDoc.ActiveDoc;

        // Get number of redo steps (default 1)
        int steps = parameters["steps"]?.ToObject<int>() ?? 1;

        uint openBefore = doc.CurrentUndoRecordSerialNumber;
        int redoneCount = 0;
        for (int i = 0; i < steps; i++)
        {
            bool redone = doc.Redo();
            EndUndoRecordLeftOpen(doc, openBefore);
            if (redone)
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

    // Called outside a command, as the bridge calls them, RhinoDoc.Undo and
    // RhinoDoc.Redo leave the undo record Rhino opens for the step recording
    // (seen on Rhino 8.37 for macOS). Left open, every later change lands in
    // that record, the next Undo finds nothing to revert, and Rhino declines
    // every new record. End it after each step; a record that was already open
    // before (a running command's) is not ours to end.
    private static void EndUndoRecordLeftOpen(RhinoDoc doc, uint openBefore)
    {
        uint open = doc.CurrentUndoRecordSerialNumber;
        if (open != 0 && open != openBefore)
            doc.EndUndoRecord(open);
    }
}
