using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using RhinoMCP.Shared.SocketServer;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Partial class implementing ICommandHandler for the Rhino MCP plugin.
/// This connects the RhinoMCPFunctions methods to the shared command routing infrastructure.
/// </summary>
public partial class RhinoMCPFunctions : ICommandHandler
{
    /// <summary>
    /// Get the dictionary mapping command type strings to handler functions.
    /// </summary>
    public Dictionary<string, Func<JObject, JObject>> GetHandlers()
    {
        return new Dictionary<string, Func<JObject, JObject>>
        {
            // Document operations
            ["get_document_summary"] = GetDocumentSummary,
            ["get_objects"] = GetObjects,

            // Object CRUD
            ["create_object"] = CreateObject,
            ["create_objects"] = CreateObjects,
            ["get_object_info"] = GetObjectInfo,
            ["get_selected_objects_info"] = GetSelectedObjectsInfo,
            ["delete_object"] = DeleteObject,
            ["modify_object"] = ModifyObject,
            ["modify_objects"] = ModifyObjects,
            ["select_objects"] = SelectObjects,

            // Code execution
            ["execute_rhinoscript_python_code"] = ExecuteRhinoscript,
            ["execute_rhinocommon_csharp_code"] = ExecuteRhinoCommonCSharp,

            // Layer operations
            ["create_layer"] = CreateLayer,
            ["get_or_set_current_layer"] = GetOrSetCurrentLayer,
            ["delete_layer"] = DeleteLayer,

            // Undo/Redo
            ["undo"] = Undo,
            ["redo"] = Redo,

            // Boolean operations
            ["boolean_union"] = BooleanUnion,
            ["boolean_difference"] = BooleanDifference,
            ["boolean_intersection"] = BooleanIntersection,

            // Advanced geometry
            ["loft"] = Loft,
            ["extrude_curve"] = ExtrudeCurve,
            ["sweep1"] = Sweep1,
            ["offset_curve"] = OffsetCurve,
            ["pipe"] = Pipe,

            // Viewport
            ["capture_viewport"] = CaptureViewport
        };
    }

    /// <summary>
    /// Get the set of command types that don't modify the document.
    /// These commands won't create undo records.
    /// </summary>
    public HashSet<string> GetReadOnlyCommands()
    {
        return new HashSet<string>
        {
            "get_document_summary",
            "get_objects",
            "get_object_info",
            "get_selected_objects_info",
            "undo",
            "redo",
            "capture_viewport"
        };
    }
}
