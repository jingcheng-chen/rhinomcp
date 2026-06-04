using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    private static readonly Dictionary<string, string> GhComponentAliases = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Slider"] = "Number Slider",
        ["NumSlider"] = "Number Slider",
        ["Num Slider"] = "Number Slider",
        ["Toggle"] = "Boolean Toggle",
        ["Bool Toggle"] = "Boolean Toggle",
        ["Text Panel"] = "Panel",
        ["ValueList"] = "Value List",
        ["Add"] = "Addition",
        ["Plus"] = "Addition",
        ["Subtract"] = "Subtraction",
        ["Minus"] = "Subtraction",
        ["Multiply"] = "Multiplication",
        ["Mult"] = "Multiplication",
        ["Divide"] = "Division",
        ["Div"] = "Division",
        ["Pt"] = "Point",
        ["Point Param"] = "Point",
        ["Curve Param"] = "Curve",
        ["Brep Param"] = "Brep",
        ["Circ"] = "Circle",
        ["Rect"] = "Rectangle",
        ["Ln"] = "Line",
        ["Vec"] = "Vector",
        ["Pt3d"] = "Construct Point",
        ["Mv"] = "Move",
        ["Rot"] = "Rotate",
        ["Scl"] = "Scale",
        ["ListItem"] = "List Item"
    };

    private static GH_Document GetActiveGrasshopperDocument(bool required = true, bool createIfMissing = false)
    {
        var canvas = Instances.ActiveCanvas;
        var doc = canvas?.Document;
        var server = Instances.DocumentServer;

        if (doc == null && server.DocumentCount > 0)
        {
            doc = server.NextAvailableDocument();
            if (doc == null && server.DocumentCount == 1)
            {
                doc = server[0];
            }
        }

        if (doc == null && createIfMissing)
        {
            doc = server.AddNewDocument();
            if (doc != null)
            {
                server.PromoteDocument(doc);
            }
        }

        if (doc != null && canvas != null && (canvas.Document == null || createIfMissing))
        {
            canvas.Document = doc;
            RedrawGrasshopperCanvas();
        }

        if (doc == null && required)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }
        return doc;
    }

    private static void RedrawGrasshopperCanvas(PointF? focus = null)
    {
        var canvas = Instances.ActiveCanvas;
        if (canvas == null)
        {
            return;
        }

        if (focus.HasValue)
        {
            canvas.Viewport.Focus(focus.Value);
        }
        Instances.InvalidateCanvas();
        Instances.RedrawCanvas();
    }

    private static void RunGrasshopperSolution(GH_Document doc, bool expireAllObjects)
    {
        if (expireAllObjects)
        {
            doc.ExpireSolution();
        }
        doc.NewSolution(expireAllObjects, GH_SolutionMode.CommandLine);
        doc.GetType()
            .GetMethod("SolveAllObjects", new[] { typeof(GH_SolutionMode) })
            ?.Invoke(doc, new object[] { GH_SolutionMode.CommandLine });
    }

    private static IGH_DocumentObject FindGhObject(GH_Document doc, JObject parameters, string prefix = "")
    {
        string instanceId = parameters[$"{prefix}instance_id"]?.ToString()
            ?? parameters[$"{prefix}id"]?.ToString()
            ?? (prefix == "" ? parameters["component_id"]?.ToString() : null);
        string nickname = parameters[$"{prefix}nickname"]?.ToString();

        if (string.IsNullOrEmpty(instanceId) && string.IsNullOrEmpty(nickname))
        {
            throw new ArgumentException($"Either {prefix}instance_id or {prefix}nickname is required.");
        }

        if (!string.IsNullOrEmpty(instanceId))
        {
            if (!Guid.TryParse(instanceId, out var guid))
            {
                throw new ArgumentException($"Invalid GUID format: {instanceId}");
            }
            var byId = doc.FindObject(guid, true);
            if (byId != null)
            {
                return byId;
            }
        }

        if (!string.IsNullOrEmpty(nickname))
        {
            var matches = doc.Objects
                .Where(o => o.NickName.Equals(nickname, StringComparison.OrdinalIgnoreCase))
                .ToList();
            if (matches.Count > 1)
            {
                throw new InvalidOperationException($"Nickname '{nickname}' is ambiguous; use instance_id instead.");
            }
            if (matches.Count == 1)
            {
                return matches[0];
            }
        }

        string identifier = !string.IsNullOrEmpty(instanceId) ? instanceId : nickname;
        throw new InvalidOperationException($"Grasshopper object '{identifier}' not found.");
    }

    private static bool HasAnySelector(JObject parameters)
    {
        return parameters["instance_id"] != null ||
            parameters["id"] != null ||
            parameters["component_id"] != null ||
            parameters["nickname"] != null;
    }

    private static int? GetParamIndex(JObject parameters, bool isOutput, string prefix = "")
    {
        if (isOutput)
        {
            return parameters[$"{prefix}output_index"]?.ToObject<int?>()
                ?? parameters[$"{prefix}output"]?.ToObject<int?>()
                ?? parameters[$"{prefix}param_index"]?.ToObject<int?>()
                ?? parameters["param_index"]?.ToObject<int?>();
        }
        return parameters[$"{prefix}input_index"]?.ToObject<int?>()
            ?? parameters[$"{prefix}input"]?.ToObject<int?>()
            ?? parameters[$"{prefix}param_index"]?.ToObject<int?>()
            ?? parameters["param_index"]?.ToObject<int?>();
    }

    private static string GetParamName(JObject parameters, bool isOutput, string prefix = "")
    {
        if (isOutput)
        {
            return parameters[$"{prefix}output_name"]?.ToString()
                ?? parameters[$"{prefix}param"]?.ToString()
                ?? parameters["param_name"]?.ToString();
        }
        return parameters[$"{prefix}input_name"]?.ToString()
            ?? parameters[$"{prefix}param"]?.ToString()
            ?? parameters["param_name"]?.ToString();
    }

    private static IGH_Param FindOutputParam(IGH_DocumentObject obj, int? paramIndex, string paramName)
    {
        if (obj is IGH_Component component)
        {
            return FindParam(component.Params.Output, paramIndex, paramName);
        }
        return obj as IGH_Param;
    }

    private static IGH_Param FindInputParam(IGH_DocumentObject obj, int? paramIndex, string paramName)
    {
        if (obj is IGH_Component component)
        {
            return FindParam(component.Params.Input, paramIndex, paramName);
        }
        return obj as IGH_Param;
    }

    private static IGH_Param FindParam(IList<IGH_Param> parameters, int? paramIndex, string paramName)
    {
        if (paramIndex.HasValue)
        {
            if (paramIndex.Value < 0 || paramIndex.Value >= parameters.Count)
            {
                return null;
            }
            return parameters[paramIndex.Value];
        }
        if (!string.IsNullOrEmpty(paramName))
        {
            return parameters.FirstOrDefault(p =>
                p.Name.Equals(paramName, StringComparison.OrdinalIgnoreCase) ||
                p.NickName.Equals(paramName, StringComparison.OrdinalIgnoreCase));
        }
        return parameters.Count > 0 ? parameters[0] : null;
    }

    private static JArray PivotToJson(IGH_DocumentObject obj)
    {
        if (obj.Attributes == null)
        {
            return new JArray { 0, 0 };
        }
        return new JArray { obj.Attributes.Pivot.X, obj.Attributes.Pivot.Y };
    }

    private static PointF ReadPosition(JObject parameters, string key, float defaultX, float defaultY)
    {
        var positionArray = parameters[key]?.ToObject<double[]>();
        if (positionArray == null)
        {
            return new PointF(defaultX, defaultY);
        }
        if (positionArray.Length != 2)
        {
            throw new ArgumentException($"{key} must be a two-number [x, y] array.");
        }
        return new PointF((float)positionArray[0], (float)positionArray[1]);
    }

    private static string OptionalString(JObject parameters, string key)
    {
        var token = parameters[key];
        return token == null || token.Type == JTokenType.Null ? null : token.ToString();
    }

    private static int OptionalInt(JObject parameters, string key, int defaultValue)
    {
        return parameters[key]?.ToObject<int>() ?? defaultValue;
    }

    private static bool OptionalBool(JObject parameters, string key, bool defaultValue)
    {
        return parameters[key]?.ToObject<bool>() ?? defaultValue;
    }

    private static int Clamp(int value, int min, int max)
    {
        return Math.Max(min, Math.Min(max, value));
    }
}
