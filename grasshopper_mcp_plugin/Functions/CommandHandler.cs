using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using RhinoMCP.Shared.SocketServer;

namespace GrasshopperMCPPlugin.Functions;

/// <summary>
/// Main command handler for GrasshopperMCP.
/// Implements ICommandHandler to route commands to specific function handlers.
/// </summary>
public partial class GrasshopperMCPFunctions : ICommandHandler
{
    /// <summary>
    /// Get the dictionary mapping command type strings to handler functions.
    /// </summary>
    public Dictionary<string, Func<JObject, JObject>> GetHandlers()
    {
        return new Dictionary<string, Func<JObject, JObject>>
        {
            // Document operations
            ["get_gh_document_info"] = GetDocumentInfo,

            // Component operations
            ["list_components"] = ListComponents,
            ["add_component"] = AddComponent,
            ["delete_component"] = DeleteComponent,
            ["get_component_info"] = GetComponentInfo,

            // Connection operations
            ["connect_components"] = ConnectComponents,
            ["disconnect_components"] = DisconnectComponents,

            // Parameter operations
            ["set_parameter_value"] = SetParameterValue,
            ["get_parameter_value"] = GetParameterValue,

            // Solution operations
            ["run_solution"] = RunSolution,
            ["expire_solution"] = ExpireSolution,

            // Utility operations
            ["bake_component"] = BakeComponent,
            ["get_canvas_state"] = GetCanvasState,

            // Batch operations
            ["create_definition"] = CreateDefinition,

            // Search operations
            ["search_components"] = SearchComponents,
            ["batch_search_components"] = BatchSearchComponents,
            ["list_component_categories"] = ListComponentCategories,
            ["get_available_components"] = GetAvailableComponents
        };
    }

    /// <summary>
    /// Get the set of command types that don't modify the document.
    /// </summary>
    public HashSet<string> GetReadOnlyCommands()
    {
        return new HashSet<string>
        {
            "get_gh_document_info",
            "list_components",
            "get_component_info",
            "get_parameter_value",
            "get_canvas_state",
            "search_components",
            "batch_search_components",
            "list_component_categories",
            "get_available_components"
        };
    }
}
