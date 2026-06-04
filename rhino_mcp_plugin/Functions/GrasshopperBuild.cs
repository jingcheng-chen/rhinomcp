using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("gh_build_graph")]
    public JObject GhBuildGraph(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument(createIfMissing: true);
        bool recompute = OptionalBool(parameters, "recompute", true);
        bool rollbackOnError = OptionalBool(parameters, "rollback_on_error", true);

        var componentSpecs = parameters["components"] as JArray
            ?? throw new ArgumentException("components is required.");
        if (componentSpecs.Count == 0)
        {
            throw new ArgumentException("components must contain at least one component.");
        }

        var aliases = new Dictionary<string, IGH_DocumentObject>(StringComparer.OrdinalIgnoreCase);
        var created = new List<IGH_DocumentObject>();
        int connectionCount = 0;
        int valueCount = 0;
        JObject layoutResult = null;
        var startPosition = new PointF(40, 40);

        try
        {
            bool? bulkPreview = (parameters["preview_updates"] as JObject)?["enabled"]?.ToObject<bool?>();

            foreach (var specToken in componentSpecs)
            {
                if (specToken is not JObject spec)
                {
                    throw new ArgumentException("Each component entry must be an object.");
                }

                string alias = OptionalString(spec, "alias");
                string componentName = OptionalString(spec, "component_name");
                string componentGuid = OptionalString(spec, "component_guid");
                if (string.IsNullOrWhiteSpace(alias))
                {
                    throw new ArgumentException("Every gh_build_graph component requires an alias.");
                }
                if (aliases.ContainsKey(alias))
                {
                    throw new InvalidOperationException($"Duplicate Grasshopper build alias '{alias}'.");
                }
                if (string.IsNullOrWhiteSpace(componentName))
                {
                    throw new ArgumentException($"Component '{alias}' is missing component_name.");
                }

                var obj = CreateGrasshopperObject(componentName, componentGuid, spec);
                if (obj.Attributes == null)
                {
                    obj.CreateAttributes();
                }

                var position = spec["position"] != null
                    ? ReadPosition(spec, "position", 0, 0)
                    : FindNextGrasshopperSlot(doc);
                obj.Attributes.Pivot = position;
                startPosition = position;

                string nickname = OptionalString(spec, "nickname");
                if (!string.IsNullOrEmpty(nickname))
                {
                    obj.NickName = nickname;
                }

                if (bulkPreview.HasValue && obj is IGH_PreviewObject bulkPreviewObj)
                {
                    bulkPreviewObj.Hidden = !bulkPreview.Value;
                }
                if (spec["preview"] != null && obj is IGH_PreviewObject previewObj)
                {
                    previewObj.Hidden = !spec["preview"]!.ToObject<bool>();
                }
                if (spec["enabled"] != null && obj is IGH_ActiveObject activeObj)
                {
                    activeObj.Locked = !spec["enabled"]!.ToObject<bool>();
                }

                doc.AddObject(obj, false);
                aliases[alias] = obj;
                created.Add(obj);
            }

            foreach (var valueToken in parameters["values"] as JArray ?? new JArray())
            {
                if (valueToken is not JObject valueSpec)
                {
                    throw new ArgumentException("Each value entry must be an object.");
                }
                ApplyBuildGraphValue(doc, aliases, valueSpec);
                valueCount++;
            }

            foreach (var connectionToken in parameters["connections"] as JArray ?? new JArray())
            {
                if (connectionToken is not JObject connectionSpec)
                {
                    throw new ArgumentException("Each connection entry must be an object.");
                }
                ApplyBuildGraphConnection(doc, aliases, connectionSpec);
                connectionCount++;
            }

            if (BuildGraphLayoutEnabled(parameters["layout"]))
            {
                var layoutParams = parameters["layout"] as JObject ?? new JObject();
                float xSpacing = (float)Math.Max(60, layoutParams["x_spacing"]?.ToObject<double>() ?? 220);
                float ySpacing = (float)Math.Max(40, layoutParams["y_spacing"]?.ToObject<double>() ?? 90);
                var layoutStart = layoutParams["start_position"] != null
                    ? ReadPosition(layoutParams, "start_position", 40, 40)
                    : new PointF(40, 40);
                layoutResult = ApplyGrasshopperLayout(created, layoutStart, xSpacing, ySpacing);
                startPosition = layoutStart;
            }

            if (recompute)
            {
                foreach (var obj in created)
                {
                    obj.ExpireSolution(true);
                }
                RunGrasshopperSolution(doc, false);
            }

            RedrawGrasshopperCanvas(startPosition);

            var components = new JArray(created.Select(obj => new JObject
            {
                ["instance_id"] = obj.InstanceGuid.ToString(),
                ["name"] = obj.Name,
                ["nickname"] = obj.NickName,
                ["category"] = obj.Category,
                ["subcategory"] = obj.SubCategory,
                ["position"] = PivotToJson(obj)
            }));
            var aliasIds = new JObject(aliases.Select(pair => new JProperty(pair.Key, pair.Value.InstanceGuid.ToString())));

            return new JObject
            {
                ["success"] = true,
                ["component_count"] = created.Count,
                ["connection_count"] = connectionCount,
                ["value_count"] = valueCount,
                ["recomputed"] = recompute,
                ["rolled_back"] = false,
                ["aliases"] = aliasIds,
                ["components"] = components,
                ["layout"] = layoutResult,
                ["message"] = $"Built Grasshopper graph with {created.Count} component(s) and {connectionCount} connection(s)"
            };
        }
        catch
        {
            if (rollbackOnError && created.Count > 0)
            {
                doc.RemoveObjects(created, false);
                RunGrasshopperSolution(doc, false);
                RedrawGrasshopperCanvas();
            }
            throw;
        }
    }

    private static bool BuildGraphLayoutEnabled(JToken layoutToken)
    {
        if (layoutToken == null || layoutToken.Type == JTokenType.Null)
        {
            return false;
        }
        if (layoutToken.Type == JTokenType.Boolean)
        {
            return layoutToken.ToObject<bool>();
        }
        return (layoutToken as JObject)?["enabled"]?.ToObject<bool?>() ?? true;
    }

    private static void ApplyBuildGraphValue(
        GH_Document doc,
        Dictionary<string, IGH_DocumentObject> aliases,
        JObject valueSpec)
    {
        string target = OptionalString(valueSpec, "target");
        var obj = ResolveBuildGraphObject(doc, aliases, target, "value target");
        var value = valueSpec["value"] ?? throw new ArgumentException("value update is missing value.");

        if (TrySetSpecialComponentValue(obj, value, valueSpec, out _))
        {
            return;
        }

        var inputParam = FindInputParam(
            obj,
            GetParamIndex(valueSpec, isOutput: false),
            GetParamName(valueSpec, isOutput: false));
        if (inputParam == null)
        {
            throw new InvalidOperationException($"Could not find input parameter on component '{obj.NickName}'.");
        }

        SetParamValue(inputParam, value);
    }

    private static void ApplyBuildGraphConnection(
        GH_Document doc,
        Dictionary<string, IGH_DocumentObject> aliases,
        JObject connectionSpec)
    {
        var sourceObj = ResolveBuildGraphObject(
            doc,
            aliases,
            OptionalString(connectionSpec, "source"),
            "connection source");
        var targetObj = ResolveBuildGraphObject(
            doc,
            aliases,
            OptionalString(connectionSpec, "target"),
            "connection target");

        var outputParam = FindOutputParam(
            sourceObj,
            GetParamIndex(connectionSpec, isOutput: true, "source_"),
            GetParamName(connectionSpec, isOutput: true, "source_"));
        if (outputParam == null)
        {
            throw new InvalidOperationException($"Could not find output parameter on source component '{sourceObj.NickName}'.");
        }

        var inputParam = FindInputParam(
            targetObj,
            GetParamIndex(connectionSpec, isOutput: false, "target_"),
            GetParamName(connectionSpec, isOutput: false, "target_"));
        if (inputParam == null)
        {
            throw new InvalidOperationException($"Could not find input parameter on target component '{targetObj.NickName}'.");
        }

        inputParam.AddSource(outputParam);
        EnsureParamHasData(outputParam);
        targetObj.ExpireSolution(true);
    }

    private static IGH_DocumentObject ResolveBuildGraphObject(
        GH_Document doc,
        Dictionary<string, IGH_DocumentObject> aliases,
        string selector,
        string role)
    {
        if (string.IsNullOrWhiteSpace(selector))
        {
            throw new ArgumentException($"Missing Grasshopper {role} selector.");
        }

        if (aliases.TryGetValue(selector, out var aliased))
        {
            return aliased;
        }

        if (Guid.TryParse(selector, out var guid))
        {
            var byId = doc.FindObject(guid, true);
            if (byId != null)
            {
                return byId;
            }
        }

        var matches = doc.Objects
            .Where(o => o.NickName.Equals(selector, StringComparison.OrdinalIgnoreCase))
            .ToList();
        if (matches.Count > 1)
        {
            throw new InvalidOperationException($"Grasshopper {role} selector '{selector}' is ambiguous; use an alias or GUID.");
        }
        if (matches.Count == 1)
        {
            return matches[0];
        }

        throw new InvalidOperationException($"Grasshopper {role} selector '{selector}' was not found.");
    }
}
