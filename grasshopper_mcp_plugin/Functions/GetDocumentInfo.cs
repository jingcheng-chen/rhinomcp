using System;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Get information about the active Grasshopper document.
    /// </summary>
    public JObject GetDocumentInfo(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            return new JObject
            {
                ["has_document"] = false,
                ["message"] = "No active Grasshopper document"
            };
        }

        // Count components by category
        var componentsByCategory = doc.Objects
            .OfType<IGH_Component>()
            .GroupBy(c => c.Category ?? "Unknown")
            .ToDictionary(g => g.Key, g => g.Count());

        // Count parameters
        var parameterCount = doc.Objects.OfType<IGH_Param>().Count();

        // Get document properties
        var result = new JObject
        {
            ["has_document"] = true,
            ["file_path"] = doc.FilePath ?? "(unsaved)",
            ["is_modified"] = doc.IsModified,
            ["object_count"] = doc.ObjectCount,
            ["component_count"] = doc.Objects.OfType<IGH_Component>().Count(),
            ["parameter_count"] = parameterCount,
            ["group_count"] = doc.Objects.OfType<Grasshopper.Kernel.Special.GH_Group>().Count(),
            ["components_by_category"] = JObject.FromObject(componentsByCategory)
        };

        return result;
    }
}
