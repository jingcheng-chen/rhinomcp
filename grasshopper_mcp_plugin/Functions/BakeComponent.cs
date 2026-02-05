using System;
using System.Collections.Generic;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Bake geometry from a component to the Rhino document.
    /// </summary>
    public JObject BakeComponent(JObject parameters)
    {
        var ghDoc = Instances.ActiveCanvas?.Document;
        var rhinoDoc = RhinoDoc.ActiveDoc;

        if (ghDoc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        if (rhinoDoc == null)
        {
            throw new InvalidOperationException("No active Rhino document");
        }

        var componentId = parameters["component_id"]?.ToString();
        var paramName = parameters["param_name"]?.ToString();
        var paramIndex = parameters["param_index"]?.ToObject<int?>() ?? null;
        var layerName = parameters["layer"]?.ToString();

        if (string.IsNullOrEmpty(componentId))
        {
            throw new ArgumentException("component_id is required");
        }

        // Find component
        if (!Guid.TryParse(componentId, out var guid))
        {
            throw new ArgumentException($"Invalid component_id GUID: {componentId}");
        }
        var obj = ghDoc.FindObject(guid, true);
        if (obj == null)
        {
            throw new InvalidOperationException($"Component '{componentId}' not found");
        }

        // Get the output parameter to bake
        IGH_Param? outputParam = null;

        if (obj is IGH_Component component)
        {
            if (paramIndex.HasValue && paramIndex.Value < component.Params.Output.Count)
            {
                outputParam = component.Params.Output[paramIndex.Value];
            }
            else if (!string.IsNullOrEmpty(paramName))
            {
                outputParam = component.Params.Output
                    .FirstOrDefault(p => p.Name.Equals(paramName, StringComparison.OrdinalIgnoreCase)
                                      || p.NickName.Equals(paramName, StringComparison.OrdinalIgnoreCase));
            }
            else if (component.Params.Output.Count >= 1)
            {
                // Find first geometry output
                outputParam = component.Params.Output.FirstOrDefault(p =>
                    p.TypeName.Contains("Geometry") ||
                    p.TypeName.Contains("Curve") ||
                    p.TypeName.Contains("Surface") ||
                    p.TypeName.Contains("Brep") ||
                    p.TypeName.Contains("Mesh") ||
                    p.TypeName.Contains("Point"));

                if (outputParam == null)
                    outputParam = component.Params.Output[0];
            }
        }
        else if (obj is IGH_Param param)
        {
            outputParam = param;
        }

        if (outputParam == null)
        {
            throw new InvalidOperationException("Could not find output parameter to bake");
        }

        // Check if parameter supports baking
        if (!(outputParam is IGH_BakeAwareObject bakeAware))
        {
            throw new InvalidOperationException($"Parameter '{outputParam.Name}' does not support baking");
        }

        // Set up bake attributes
        var attributes = new ObjectAttributes();

        // Set layer if specified
        if (!string.IsNullOrEmpty(layerName))
        {
            var layerIndex = rhinoDoc.Layers.FindByFullPath(layerName, -1);
            if (layerIndex < 0)
            {
                // Create layer if it doesn't exist
                var layer = new Layer { Name = layerName };
                layerIndex = rhinoDoc.Layers.Add(layer);
            }
            attributes.LayerIndex = layerIndex;
        }

        // Bake the geometry
        var bakedIds = new List<Guid>();

        bakeAware.BakeGeometry(rhinoDoc, attributes, bakedIds);

        rhinoDoc.Views.Redraw();

        // Format result
        var resultIds = new JArray();
        foreach (var id in bakedIds)
        {
            resultIds.Add(id.ToString());
        }

        return new JObject
        {
            ["component_id"] = componentId,
            ["param_name"] = outputParam.Name,
            ["baked_count"] = bakedIds.Count,
            ["baked_ids"] = resultIds,
            ["layer"] = layerName ?? "Default",
            ["message"] = $"Baked {bakedIds.Count} object(s) from {obj.Name}.{outputParam.Name}"
        };
    }
}
