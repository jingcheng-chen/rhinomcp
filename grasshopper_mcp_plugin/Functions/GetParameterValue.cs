using System;
using System.Collections.Generic;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;
using Newtonsoft.Json.Linq;
using Rhino.Geometry;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Get the value of a component's output parameter.
    /// </summary>
    public JObject GetParameterValue(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        var componentId = parameters["component_id"]?.ToString();
        var paramName = parameters["param_name"]?.ToString();
        var paramIndex = parameters["param_index"]?.ToObject<int?>() ?? null;
        var maxItems = parameters["max_items"]?.ToObject<int>() ?? 100;

        if (string.IsNullOrEmpty(componentId))
        {
            throw new ArgumentException("component_id is required");
        }

        // Find component
        if (!Guid.TryParse(componentId, out var guid))
        {
            throw new ArgumentException($"Invalid component_id GUID: {componentId}");
        }
        var obj = doc.FindObject(guid, true);
        if (obj == null)
        {
            throw new InvalidOperationException($"Component '{componentId}' not found");
        }

        // Get the output parameter
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
            else if (component.Params.Output.Count == 1)
            {
                outputParam = component.Params.Output[0];
            }
        }
        else if (obj is IGH_Param param)
        {
            outputParam = param;
        }

        if (outputParam == null)
        {
            throw new InvalidOperationException($"Could not find output parameter '{paramName}' on component");
        }

        // Get the data
        var data = outputParam.VolatileData;
        var result = new JObject
        {
            ["component_id"] = componentId,
            ["param_name"] = outputParam.Name,
            ["type_name"] = outputParam.TypeName,
            ["data_count"] = data.DataCount,
            ["branch_count"] = data.PathCount
        };

        // Extract values
        var values = new JArray();
        int itemCount = 0;

        foreach (var path in data.Paths)
        {
            var branch = data.get_Branch(path);
            var branchValues = new JObject
            {
                ["path"] = path.ToString()
            };
            var items = new JArray();

            foreach (var item in branch)
            {
                if (itemCount >= maxItems) break;

                var itemValue = ExtractGHValue(item);
                items.Add(itemValue);
                itemCount++;
            }

            branchValues["items"] = items;
            values.Add(branchValues);

            if (itemCount >= maxItems) break;
        }

        result["values"] = values;
        result["truncated"] = data.DataCount > maxItems;

        return result;
    }

    /// <summary>
    /// Extract a serializable value from a GH_Goo object.
    /// </summary>
    private JToken ExtractGHValue(object? item)
    {
        if (item == null) return JValue.CreateNull();

        // Handle common GH types
        if (item is GH_Number num)
        {
            return num.Value;
        }
        else if (item is GH_Integer intVal)
        {
            return intVal.Value;
        }
        else if (item is GH_Boolean boolVal)
        {
            return boolVal.Value;
        }
        else if (item is GH_String strVal)
        {
            return strVal.Value;
        }
        else if (item is GH_Point ptVal)
        {
            return new JArray { ptVal.Value.X, ptVal.Value.Y, ptVal.Value.Z };
        }
        else if (item is GH_Vector vecVal)
        {
            return new JArray { vecVal.Value.X, vecVal.Value.Y, vecVal.Value.Z };
        }
        else if (item is GH_Plane planeVal)
        {
            return new JObject
            {
                ["origin"] = new JArray { planeVal.Value.Origin.X, planeVal.Value.Origin.Y, planeVal.Value.Origin.Z },
                ["x_axis"] = new JArray { planeVal.Value.XAxis.X, planeVal.Value.XAxis.Y, planeVal.Value.XAxis.Z },
                ["y_axis"] = new JArray { planeVal.Value.YAxis.X, planeVal.Value.YAxis.Y, planeVal.Value.YAxis.Z },
                ["z_axis"] = new JArray { planeVal.Value.ZAxis.X, planeVal.Value.ZAxis.Y, planeVal.Value.ZAxis.Z }
            };
        }
        else if (item is GH_Line lineVal)
        {
            return new JObject
            {
                ["from"] = new JArray { lineVal.Value.From.X, lineVal.Value.From.Y, lineVal.Value.From.Z },
                ["to"] = new JArray { lineVal.Value.To.X, lineVal.Value.To.Y, lineVal.Value.To.Z }
            };
        }
        else if (item is GH_Circle circleVal)
        {
            return new JObject
            {
                ["center"] = new JArray { circleVal.Value.Center.X, circleVal.Value.Center.Y, circleVal.Value.Center.Z },
                ["radius"] = circleVal.Value.Radius
            };
        }
        else if (item is GH_Curve curveVal)
        {
            return new JObject
            {
                ["type"] = "Curve",
                ["is_closed"] = curveVal.Value?.IsClosed ?? false,
                ["length"] = curveVal.Value?.GetLength() ?? 0
            };
        }
        else if (item is GH_Surface surfVal)
        {
            return new JObject
            {
                ["type"] = "Surface"
            };
        }
        else if (item is GH_Brep brepVal)
        {
            return new JObject
            {
                ["type"] = "Brep",
                ["is_solid"] = brepVal.Value?.IsSolid ?? false,
                ["faces"] = brepVal.Value?.Faces.Count ?? 0
            };
        }
        else if (item is GH_Mesh meshVal)
        {
            return new JObject
            {
                ["type"] = "Mesh",
                ["vertices"] = meshVal.Value?.Vertices.Count ?? 0,
                ["faces"] = meshVal.Value?.Faces.Count ?? 0
            };
        }
        else if (item is IGH_Goo goo)
        {
            // Generic fallback
            return new JObject
            {
                ["type"] = goo.TypeName,
                ["description"] = goo.ToString()
            };
        }

        return item.ToString() ?? "null";
    }
}
