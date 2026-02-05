using System;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Types;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Get the value of a component's output parameter.
    /// Supports both Python naming (instance_id, nickname, output_index, output_name)
    /// and C# naming (component_id, param_index, param_name).
    /// </summary>
    public JObject GetParameterValue(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        var maxItems = parameters["max_items"]?.ToObject<int>() ?? 100;

        // Find component - supports instance_id, nickname, or component_id
        var obj = ComponentHelper.FindComponent(doc, parameters);

        // Get output parameter
        var paramIndex = ComponentHelper.GetParamIndex(parameters, isOutput: true);
        var paramName = ComponentHelper.GetParamName(parameters, isOutput: true);

        var outputParam = ComponentHelper.FindOutputParam(obj, paramIndex, paramName);

        if (outputParam == null)
        {
            throw new InvalidOperationException($"Could not find output parameter on component '{obj.NickName}'");
        }

        // Get the data
        var data = outputParam.VolatileData;
        var result = new JObject
        {
            ["instance_id"] = obj.InstanceGuid.ToString(),
            ["nickname"] = obj.NickName,
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
