using System;
using System.Collections.Generic;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// List all components on the active Grasshopper canvas.
    /// </summary>
    public JObject ListComponents(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        // Get optional filters
        var categoryFilter = parameters["category"]?.ToString();
        var nameFilter = parameters["name"]?.ToString();
        var limit = parameters["limit"]?.ToObject<int>() ?? 100;

        var components = new JArray();
        var query = doc.Objects.OfType<IGH_Component>().AsEnumerable();

        // Apply filters
        if (!string.IsNullOrEmpty(categoryFilter))
        {
            query = query.Where(c => c.Category?.Equals(categoryFilter, StringComparison.OrdinalIgnoreCase) == true);
        }

        if (!string.IsNullOrEmpty(nameFilter))
        {
            query = query.Where(c => c.Name?.Contains(nameFilter, StringComparison.OrdinalIgnoreCase) == true);
        }

        foreach (var component in query.Take(limit))
        {
            var compInfo = new JObject
            {
                ["instance_id"] = component.InstanceGuid.ToString(),
                ["name"] = component.Name,
                ["nickname"] = component.NickName,
                ["category"] = component.Category,
                ["subcategory"] = component.SubCategory,
                ["description"] = component.Description,
                ["position"] = new JArray { component.Attributes.Pivot.X, component.Attributes.Pivot.Y },
                ["input_count"] = component.Params.Input.Count,
                ["output_count"] = component.Params.Output.Count,
                ["runtime_message_level"] = component.RuntimeMessageLevel.ToString()
            };

            components.Add(compInfo);
        }

        return new JObject
        {
            ["count"] = components.Count,
            ["components"] = components
        };
    }
}
