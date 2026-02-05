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
    /// Supports both Python naming (instance_id, nickname, output_index)
    /// and C# naming (component_id, param_index).
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

        // Find component - supports instance_id, nickname, or component_id
        var obj = ComponentHelper.FindComponent(ghDoc, parameters);

        // Get layer name (support both layer_name and layer)
        var layerName = parameters["layer_name"]?.ToString()
                     ?? parameters["layer"]?.ToString();

        // Get output parameter
        var paramIndex = ComponentHelper.GetParamIndex(parameters, isOutput: true);
        var paramName = ComponentHelper.GetParamName(parameters, isOutput: true);

        var outputParam = ComponentHelper.FindOutputParam(obj, paramIndex, paramName);

        // If no specific output found, try to find first geometry output
        if (outputParam == null && obj is IGH_Component component)
        {
            outputParam = component.Params.Output.FirstOrDefault(p =>
                p.TypeName.Contains("Geometry") ||
                p.TypeName.Contains("Curve") ||
                p.TypeName.Contains("Surface") ||
                p.TypeName.Contains("Brep") ||
                p.TypeName.Contains("Mesh") ||
                p.TypeName.Contains("Point"));

            if (outputParam == null && component.Params.Output.Count > 0)
                outputParam = component.Params.Output[0];
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
            ["instance_id"] = obj.InstanceGuid.ToString(),
            ["nickname"] = obj.NickName,
            ["param_name"] = outputParam.Name,
            ["baked_count"] = bakedIds.Count,
            ["object_ids"] = resultIds,
            ["layer"] = layerName ?? "Default",
            ["message"] = $"Baked {bakedIds.Count} object(s) from {obj.NickName}.{outputParam.Name}"
        };
    }
}
