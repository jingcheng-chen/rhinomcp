using System;
using System.Collections.Generic;
using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Special;
using Grasshopper.Kernel.Types;
using Newtonsoft.Json.Linq;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("gh_set_parameter_value")]
    public JObject GhSetParameterValue(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        var value = parameters["value"] ?? throw new ArgumentException("value is required.");
        var obj = FindGhObject(doc, parameters);

        if (TrySetSpecialComponentValue(obj, value, parameters, out var specialResult))
        {
            doc.NewSolution(false);
            return specialResult;
        }

        var inputParam = FindInputParam(
            obj,
            GetParamIndex(parameters, isOutput: false),
            GetParamName(parameters, isOutput: false));
        if (inputParam == null)
        {
            throw new InvalidOperationException($"Could not find input parameter on component '{obj.NickName}'.");
        }

        SetParamValue(inputParam, value);
        doc.NewSolution(false);

        return new JObject
        {
            ["instance_id"] = obj.InstanceGuid.ToString(),
            ["nickname"] = obj.NickName,
            ["param_name"] = inputParam.Name,
            ["message"] = $"Set value on {obj.NickName}.{inputParam.Name}"
        };
    }

    [McpCommand("gh_get_parameter_value", ReadOnly = true)]
    public JObject GhGetParameterValue(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        int maxItems = Clamp(OptionalInt(parameters, "max_items", 100), 0, 10000);
        var obj = FindGhObject(doc, parameters);
        var outputParam = FindOutputParam(
            obj,
            GetParamIndex(parameters, isOutput: true),
            GetParamName(parameters, isOutput: true));
        if (outputParam == null)
        {
            throw new InvalidOperationException($"Could not find output parameter on component '{obj.NickName}'.");
        }

        return ParamValueToJson(obj, outputParam, maxItems);
    }

    private static JArray ParamsToJson(IList<IGH_Param> parameters, bool includeSources, bool includeValues = false, int maxItems = 20)
    {
        var result = new JArray();
        for (int i = 0; i < parameters.Count; i++)
        {
            result.Add(ParamToJson(parameters[i], i, includeSources, includeValues, maxItems));
        }
        return result;
    }

    private static JObject ParamToJson(IGH_Param param, int index, bool includeSources, bool includeValues = false, int maxItems = 20)
    {
        var result = new JObject
        {
            ["index"] = index,
            ["name"] = param.Name,
            ["nickname"] = param.NickName,
            ["description"] = param.Description,
            ["type"] = param.TypeName,
            ["access"] = param.Access.ToString(),
            ["optional"] = param.Optional,
            ["source_count"] = param.SourceCount,
            ["recipient_count"] = param.Recipients.Count,
            ["has_data"] = param.VolatileDataCount > 0
        };

        if (includeSources && param.SourceCount > 0)
        {
            result["sources"] = new JArray(param.Sources.Select(source => new JObject
            {
                ["component_id"] = source.Attributes?.GetTopLevel.DocObject.InstanceGuid.ToString(),
                ["param_name"] = source.Name,
                ["param_nickname"] = source.NickName
            }));
        }
        if (includeSources && param.Recipients.Count > 0)
        {
            result["recipients"] = new JArray(param.Recipients.Select(recipient => new JObject
            {
                ["component_id"] = recipient.Attributes?.GetTopLevel.DocObject.InstanceGuid.ToString(),
                ["param_name"] = recipient.Name,
                ["param_nickname"] = recipient.NickName
            }));
        }
        if (includeValues)
        {
            result["value"] = ParamVolatileDataToJson(param, maxItems);
        }

        return result;
    }

    private static JObject ParamValueToJson(IGH_DocumentObject obj, IGH_Param param, int maxItems)
    {
        var result = ParamVolatileDataToJson(param, maxItems);
        result["instance_id"] = obj.InstanceGuid.ToString();
        result["nickname"] = obj.NickName;
        result["param_name"] = param.Name;
        result["type_name"] = param.TypeName;
        return result;
    }

    private static JObject ParamVolatileDataToJson(IGH_Param param, int maxItems)
    {
        var data = param.VolatileData;
        var branches = new JArray();
        int itemCount = 0;

        foreach (GH_Path path in data.Paths)
        {
            var branch = data.get_Branch(path);
            var items = new JArray();
            foreach (var item in branch)
            {
                if (itemCount >= maxItems)
                {
                    break;
                }
                items.Add(ExtractGrasshopperValue(item));
                itemCount++;
            }
            branches.Add(new JObject
            {
                ["path"] = path.ToString(),
                ["items"] = items
            });
            if (itemCount >= maxItems)
            {
                break;
            }
        }

        return new JObject
        {
            ["data_count"] = data.DataCount,
            ["branch_count"] = data.PathCount,
            ["values"] = branches,
            ["truncated"] = data.DataCount > maxItems
        };
    }

    private static JToken ExtractGrasshopperValue(object item)
    {
        if (item == null) return JValue.CreateNull();
        if (item is GH_Number number) return number.Value;
        if (item is GH_Integer integer) return integer.Value;
        if (item is GH_Boolean boolean) return boolean.Value;
        if (item is GH_String text) return text.Value;
        if (item is GH_Point point) return new JArray { point.Value.X, point.Value.Y, point.Value.Z };
        if (item is GH_Vector vector) return new JArray { vector.Value.X, vector.Value.Y, vector.Value.Z };
        if (item is GH_Plane plane)
        {
            return new JObject
            {
                ["origin"] = new JArray { plane.Value.Origin.X, plane.Value.Origin.Y, plane.Value.Origin.Z },
                ["x_axis"] = new JArray { plane.Value.XAxis.X, plane.Value.XAxis.Y, plane.Value.XAxis.Z },
                ["y_axis"] = new JArray { plane.Value.YAxis.X, plane.Value.YAxis.Y, plane.Value.YAxis.Z },
                ["z_axis"] = new JArray { plane.Value.ZAxis.X, plane.Value.ZAxis.Y, plane.Value.ZAxis.Z }
            };
        }
        if (item is GH_Line line)
        {
            return new JObject
            {
                ["from"] = new JArray { line.Value.From.X, line.Value.From.Y, line.Value.From.Z },
                ["to"] = new JArray { line.Value.To.X, line.Value.To.Y, line.Value.To.Z }
            };
        }
        if (item is GH_Circle circle)
        {
            return new JObject
            {
                ["center"] = new JArray { circle.Value.Center.X, circle.Value.Center.Y, circle.Value.Center.Z },
                ["radius"] = circle.Value.Radius
            };
        }
        if (item is GH_Curve curve)
        {
            return new JObject
            {
                ["type"] = "Curve",
                ["is_closed"] = curve.Value?.IsClosed ?? false,
                ["length"] = curve.Value?.GetLength() ?? 0
            };
        }
        if (item is GH_Surface)
        {
            return new JObject { ["type"] = "Surface" };
        }
        if (item is GH_Brep brep)
        {
            return new JObject
            {
                ["type"] = "Brep",
                ["is_solid"] = brep.Value?.IsSolid ?? false,
                ["faces"] = brep.Value?.Faces.Count ?? 0
            };
        }
        if (item is GH_Mesh mesh)
        {
            return new JObject
            {
                ["type"] = "Mesh",
                ["vertices"] = mesh.Value?.Vertices.Count ?? 0,
                ["faces"] = mesh.Value?.Faces.Count ?? 0
            };
        }
        if (item is IGH_Goo goo)
        {
            return new JObject
            {
                ["type"] = goo.TypeName,
                ["description"] = goo.ToString()
            };
        }
        return item.ToString() ?? "null";
    }

    private static bool TrySetSpecialComponentValue(IGH_DocumentObject obj, JToken value, JObject parameters, out JObject result)
    {
        result = new JObject();

        if (obj is GH_NumberSlider slider)
        {
            if (parameters["min"] != null) slider.Slider.Minimum = parameters["min"]!.ToObject<decimal>();
            if (parameters["max"] != null) slider.Slider.Maximum = parameters["max"]!.ToObject<decimal>();
            if (parameters["decimals"] != null) slider.Slider.DecimalPlaces = Clamp(parameters["decimals"]!.ToObject<int>(), 0, 12);

            decimal numericValue = value.ToObject<decimal>();
            if (numericValue < slider.Slider.Minimum) numericValue = slider.Slider.Minimum;
            if (numericValue > slider.Slider.Maximum) numericValue = slider.Slider.Maximum;
            slider.Slider.Value = numericValue;
            slider.ExpireSolution(true);

            result = new JObject
            {
                ["instance_id"] = obj.InstanceGuid.ToString(),
                ["nickname"] = obj.NickName,
                ["value"] = (double)numericValue,
                ["min"] = (double)slider.Slider.Minimum,
                ["max"] = (double)slider.Slider.Maximum,
                ["message"] = $"Set slider '{obj.NickName}' to {numericValue}"
            };
            return true;
        }

        if (obj is GH_BooleanToggle toggle)
        {
            toggle.Value = value.ToObject<bool>();
            toggle.ExpireSolution(true);
            result = new JObject
            {
                ["instance_id"] = obj.InstanceGuid.ToString(),
                ["nickname"] = obj.NickName,
                ["value"] = toggle.Value,
                ["message"] = $"Set toggle '{obj.NickName}' to {toggle.Value}"
            };
            return true;
        }

        if (obj is GH_Panel panel)
        {
            panel.SetUserText(value.ToString());
            panel.ExpireSolution(true);
            result = new JObject
            {
                ["instance_id"] = obj.InstanceGuid.ToString(),
                ["nickname"] = obj.NickName,
                ["value"] = value.ToString(),
                ["message"] = $"Set panel '{obj.NickName}' content"
            };
            return true;
        }

        if (obj is GH_ValueList valueList)
        {
            if (value.Type == JTokenType.Integer)
            {
                int index = value.ToObject<int>();
                if (index < 0 || index >= valueList.ListItems.Count)
                {
                    throw new ArgumentOutOfRangeException(nameof(value), $"Value list index {index} is out of range.");
                }
                valueList.SelectItem(index);
            }
            else
            {
                string requested = value.ToString();
                var item = valueList.ListItems.FirstOrDefault(i =>
                    i.Name.Equals(requested, StringComparison.OrdinalIgnoreCase) ||
                    i.Expression.Equals(requested, StringComparison.OrdinalIgnoreCase));
                if (item == null)
                {
                    throw new InvalidOperationException($"Value list item '{requested}' not found.");
                }
                valueList.SelectItem(valueList.ListItems.IndexOf(item));
            }
            valueList.ExpireSolution(true);
            result = new JObject
            {
                ["instance_id"] = obj.InstanceGuid.ToString(),
                ["nickname"] = obj.NickName,
                ["message"] = $"Set value list '{obj.NickName}' selection"
            };
            return true;
        }

        return false;
    }

    private static void SetParamValue(IGH_Param param, JToken value)
    {
        param.RemoveAllSources();

        if (param is Param_Number numberParam)
        {
            numberParam.PersistentData.ClearData();
            foreach (double item in TokenToList(value, token => token.ToObject<double>()))
            {
                numberParam.PersistentData.Append(new GH_Number(item));
            }
        }
        else if (param is Param_Integer intParam)
        {
            intParam.PersistentData.ClearData();
            foreach (int item in TokenToList(value, token => token.ToObject<int>()))
            {
                intParam.PersistentData.Append(new GH_Integer(item));
            }
        }
        else if (param is Param_Boolean boolParam)
        {
            boolParam.PersistentData.ClearData();
            boolParam.PersistentData.Append(new GH_Boolean(value.ToObject<bool>()));
        }
        else if (param is Param_String stringParam)
        {
            stringParam.PersistentData.ClearData();
            foreach (string item in TokenToList(value, token => token.ToString()))
            {
                stringParam.PersistentData.Append(new GH_String(item));
            }
        }
        else if (param is Param_Point pointParam)
        {
            pointParam.PersistentData.ClearData();
            if (value.Type == JTokenType.Array && value.First?.Type == JTokenType.Array)
            {
                foreach (var pointToken in value)
                {
                    pointParam.PersistentData.Append(new GH_Point(TokenToPoint(pointToken)));
                }
            }
            else
            {
                pointParam.PersistentData.Append(new GH_Point(TokenToPoint(value)));
            }
        }
        else if (param is Param_Vector vectorParam)
        {
            vectorParam.PersistentData.ClearData();
            vectorParam.PersistentData.Append(new GH_Vector(TokenToVector(value)));
        }
        else if (param is Param_Plane planeParam)
        {
            planeParam.PersistentData.ClearData();
            planeParam.PersistentData.Append(new GH_Plane(TokenToPlane(value)));
        }
        else
        {
            throw new InvalidOperationException($"Unsupported parameter type: {param.GetType().Name}. Use gh_connect_components to wire data from another component.");
        }

        param.ExpireSolution(true);
    }

    private static IEnumerable<T> TokenToList<T>(JToken value, Func<JToken, T> convert)
    {
        if (value.Type == JTokenType.Array)
        {
            foreach (var item in value)
            {
                yield return convert(item);
            }
        }
        else
        {
            yield return convert(value);
        }
    }

    private static Point3d TokenToPoint(JToken token)
    {
        var values = token.ToObject<double[]>() ?? Array.Empty<double>();
        return new Point3d(
            values.Length > 0 ? values[0] : 0,
            values.Length > 1 ? values[1] : 0,
            values.Length > 2 ? values[2] : 0);
    }

    private static Vector3d TokenToVector(JToken token)
    {
        var values = token.ToObject<double[]>() ?? Array.Empty<double>();
        return new Vector3d(
            values.Length > 0 ? values[0] : 0,
            values.Length > 1 ? values[1] : 0,
            values.Length > 2 ? values[2] : 0);
    }

    private static Plane TokenToPlane(JToken token)
    {
        if (token is JObject planeObject)
        {
            return new Plane(TokenToPoint(planeObject["origin"] ?? new JArray { 0, 0, 0 }), Vector3d.ZAxis);
        }
        return Plane.WorldXY;
    }
}
