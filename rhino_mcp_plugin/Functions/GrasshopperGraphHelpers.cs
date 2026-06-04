using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Reflection;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Special;
using Grasshopper.Kernel.Types;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    private const string GhMetaAlias = "rhinomcp.alias";
    private const string GhMetaGraphId = "rhinomcp.graph_id";
    private const string GhMetaRole = "rhinomcp.role";
    private static readonly MethodInfo GhSetStringValueMethod = typeof(GH_DocumentObject).GetMethod(
        "SetValue",
        BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic,
        null,
        new[] { typeof(string), typeof(string) },
        null);
    private static readonly MethodInfo GhGetStringValueMethod = typeof(GH_DocumentObject).GetMethod(
        "GetValue",
        BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic,
        null,
        new[] { typeof(string), typeof(string) },
        null);

    private sealed class GhObjectSnapshot
    {
        public IGH_DocumentObject Object { get; init; }
        public string NickName { get; init; }
        public bool HasAttributes { get; init; }
        public PointF Pivot { get; init; }
        public bool? Preview { get; init; }
        public bool? Enabled { get; init; }
        public string Alias { get; init; }
        public string GraphId { get; init; }
        public string Role { get; init; }
        public JObject Special { get; init; }
    }

    private static string CreateGraphId(string requestedGraphId)
    {
        return string.IsNullOrWhiteSpace(requestedGraphId)
            ? $"MCPGraph_{DateTime.UtcNow:yyyyMMddHHmmssfff}"
            : requestedGraphId.Trim();
    }

    private static void ApplyGraphMetadata(IGH_DocumentObject obj, string alias, string graphId, string role = null)
    {
        if (obj is not GH_DocumentObject docObject)
        {
            return;
        }
        if (!string.IsNullOrWhiteSpace(alias))
        {
            SetGraphMetadataValue(docObject, GhMetaAlias, alias.Trim());
        }
        if (!string.IsNullOrWhiteSpace(graphId))
        {
            SetGraphMetadataValue(docObject, GhMetaGraphId, graphId.Trim());
        }
        if (!string.IsNullOrWhiteSpace(role))
        {
            SetGraphMetadataValue(docObject, GhMetaRole, role.Trim());
        }
    }

    private static string GraphMetadataValue(IGH_DocumentObject obj, string key)
    {
        return obj is GH_DocumentObject docObject ? GetGraphMetadataValue(docObject, key) : "";
    }

    private static void SetGraphMetadataValue(GH_DocumentObject docObject, string key, string value)
    {
        GhSetStringValueMethod?.Invoke(docObject, new object[] { key, value ?? "" });
    }

    private static string GetGraphMetadataValue(GH_DocumentObject docObject, string key)
    {
        return GhGetStringValueMethod?.Invoke(docObject, new object[] { key, "" })?.ToString() ?? "";
    }

    private static JObject GraphMetadataToJson(IGH_DocumentObject obj)
    {
        var metadata = new JObject();
        string alias = GraphMetadataValue(obj, GhMetaAlias);
        string graphId = GraphMetadataValue(obj, GhMetaGraphId);
        string role = GraphMetadataValue(obj, GhMetaRole);
        if (!string.IsNullOrEmpty(alias)) metadata["alias"] = alias;
        if (!string.IsNullOrEmpty(graphId)) metadata["graph_id"] = graphId;
        if (!string.IsNullOrEmpty(role)) metadata["role"] = role;
        return metadata;
    }

    private static GhObjectSnapshot CaptureObjectSnapshot(IGH_DocumentObject obj)
    {
        return new GhObjectSnapshot
        {
            Object = obj,
            NickName = obj.NickName,
            HasAttributes = obj.Attributes != null,
            Pivot = obj.Attributes?.Pivot ?? PointF.Empty,
            Preview = obj is IGH_PreviewObject previewObj ? !previewObj.Hidden : null,
            Enabled = obj is IGH_ActiveObject activeObj ? !activeObj.Locked : null,
            Alias = GraphMetadataValue(obj, GhMetaAlias),
            GraphId = GraphMetadataValue(obj, GhMetaGraphId),
            Role = GraphMetadataValue(obj, GhMetaRole),
            Special = CaptureSpecialComponentValue(obj)
        };
    }

    private static void RestoreObjectSnapshot(GhObjectSnapshot snapshot)
    {
        var obj = snapshot.Object;
        obj.NickName = snapshot.NickName;
        if (snapshot.HasAttributes)
        {
            if (obj.Attributes == null)
            {
                obj.CreateAttributes();
            }
            obj.Attributes.Pivot = snapshot.Pivot;
            obj.Attributes.ExpireLayout();
        }
        if (snapshot.Preview.HasValue && obj is IGH_PreviewObject previewObj)
        {
            previewObj.Hidden = !snapshot.Preview.Value;
        }
        if (snapshot.Enabled.HasValue && obj is IGH_ActiveObject activeObj)
        {
            activeObj.Locked = !snapshot.Enabled.Value;
        }
        if (obj is GH_DocumentObject docObject)
        {
            SetGraphMetadataValue(docObject, GhMetaAlias, snapshot.Alias ?? "");
            SetGraphMetadataValue(docObject, GhMetaGraphId, snapshot.GraphId ?? "");
            SetGraphMetadataValue(docObject, GhMetaRole, snapshot.Role ?? "");
        }
        RestoreSpecialComponentValue(obj, snapshot.Special);
        obj.ExpireSolution(true);
    }

    private static JObject CaptureSpecialComponentValue(IGH_DocumentObject obj)
    {
        if (obj is GH_NumberSlider slider)
        {
            return new JObject
            {
                ["type"] = "number_slider",
                ["value"] = (double)slider.CurrentValue,
                ["min"] = (double)slider.Slider.Minimum,
                ["max"] = (double)slider.Slider.Maximum,
                ["decimals"] = slider.Slider.DecimalPlaces
            };
        }
        if (obj is GH_BooleanToggle toggle)
        {
            return new JObject
            {
                ["type"] = "boolean_toggle",
                ["value"] = toggle.Value
            };
        }
        if (obj is GH_Panel panel)
        {
            return new JObject
            {
                ["type"] = "panel",
                ["content"] = panel.UserText
            };
        }
        if (obj is GH_ValueList valueList)
        {
            int selectedIndex = -1;
            for (int i = 0; i < valueList.ListItems.Count; i++)
            {
                if (valueList.ListItems[i].Selected)
                {
                    selectedIndex = i;
                    break;
                }
            }
            return new JObject
            {
                ["type"] = "value_list",
                ["selected_index"] = selectedIndex
            };
        }
        return null;
    }

    private static void RestoreSpecialComponentValue(IGH_DocumentObject obj, JObject snapshot)
    {
        if (snapshot == null)
        {
            return;
        }

        string type = OptionalString(snapshot, "type");
        if (type == "number_slider" && obj is GH_NumberSlider slider)
        {
            slider.Slider.Minimum = snapshot["min"]?.ToObject<decimal>() ?? slider.Slider.Minimum;
            slider.Slider.Maximum = snapshot["max"]?.ToObject<decimal>() ?? slider.Slider.Maximum;
            slider.Slider.DecimalPlaces = Clamp(snapshot["decimals"]?.ToObject<int>() ?? slider.Slider.DecimalPlaces, 0, 12);
            SetNumberSliderValue(slider, snapshot["value"]?.ToObject<decimal>() ?? slider.CurrentValue);
        }
        else if (type == "boolean_toggle" && obj is GH_BooleanToggle toggle)
        {
            toggle.Value = snapshot["value"]?.ToObject<bool>() ?? toggle.Value;
            toggle.ExpireSolution(true);
        }
        else if (type == "panel" && obj is GH_Panel panel)
        {
            panel.SetUserText(snapshot["content"]?.ToString() ?? "");
            panel.ExpireSolution(true);
        }
        else if (type == "value_list" && obj is GH_ValueList valueList)
        {
            int selectedIndex = snapshot["selected_index"]?.ToObject<int>() ?? -1;
            if (selectedIndex >= 0 && selectedIndex < valueList.ListItems.Count)
            {
                valueList.SelectItem(selectedIndex);
            }
            valueList.ExpireSolution(true);
        }
    }

    private static IGH_DocumentObject ResolveGraphObject(
        GH_Document doc,
        Dictionary<string, IGH_DocumentObject> aliases,
        string selector,
        string role)
    {
        if (string.IsNullOrWhiteSpace(selector))
        {
            throw new ArgumentException($"Missing Grasshopper {role} selector.");
        }

        if (aliases != null && aliases.TryGetValue(selector, out var aliased))
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

        var aliasMatches = doc.Objects
            .Where(o => GraphMetadataValue(o, GhMetaAlias).Equals(selector, StringComparison.OrdinalIgnoreCase))
            .ToList();
        if (aliasMatches.Count > 1)
        {
            throw new InvalidOperationException($"Grasshopper {role} selector alias '{selector}' is ambiguous; use a GUID.");
        }
        if (aliasMatches.Count == 1)
        {
            return aliasMatches[0];
        }

        var nicknameMatches = doc.Objects
            .Where(o => o.NickName.Equals(selector, StringComparison.OrdinalIgnoreCase))
            .ToList();
        if (nicknameMatches.Count > 1)
        {
            throw new InvalidOperationException($"Grasshopper {role} selector nickname '{selector}' is ambiguous; use an alias or GUID.");
        }
        if (nicknameMatches.Count == 1)
        {
            return nicknameMatches[0];
        }

        throw new InvalidOperationException($"Grasshopper {role} selector '{selector}' was not found.");
    }

    private static List<IGH_DocumentObject> ResolveGraphTargets(
        GH_Document doc,
        Dictionary<string, IGH_DocumentObject> aliases,
        JToken targetsToken,
        string role)
    {
        var targets = targetsToken as JArray;
        if (targets == null || targets.Count == 0)
        {
            return new List<IGH_DocumentObject>();
        }
        return targets.Select(token => ResolveGraphObject(doc, aliases, token.ToString(), role)).Distinct().ToList();
    }

    private static List<IGH_DocumentObject> GetGraphObjects(GH_Document doc, string graphId)
    {
        if (string.IsNullOrWhiteSpace(graphId))
        {
            return new List<IGH_DocumentObject>();
        }
        return doc.Objects
            .Where(o => GraphMetadataValue(o, GhMetaGraphId).Equals(graphId, StringComparison.OrdinalIgnoreCase))
            .ToList();
    }

    private static JArray CreateGrasshopperGroups(
        GH_Document doc,
        JArray groupSpecs,
        Dictionary<string, IGH_DocumentObject> aliases,
        IEnumerable<IGH_DocumentObject> defaultObjects,
        string graphId,
        List<IGH_DocumentObject> createdObjects = null)
    {
        var createdGroups = new JArray();
        if (groupSpecs == null)
        {
            return createdGroups;
        }

        foreach (var specToken in groupSpecs)
        {
            if (specToken is not JObject spec)
            {
                throw new ArgumentException("Each group entry must be an object.");
            }

            string name = OptionalString(spec, "name") ?? OptionalString(spec, "label") ?? OptionalString(spec, "nickname");
            if (string.IsNullOrWhiteSpace(name))
            {
                throw new ArgumentException("Group name is required.");
            }

            var targets = ResolveGraphTargets(doc, aliases, spec["targets"], $"group '{name}' target");
            if (targets.Count == 0)
            {
                targets = defaultObjects?.Where(o => o is not GH_Group).Distinct().ToList() ?? new List<IGH_DocumentObject>();
            }
            if (targets.Count == 0)
            {
                continue;
            }

            var group = new GH_Group { NickName = name };
            var colorArray = spec["color"]?.ToObject<int[]>();
            if (colorArray != null && colorArray.Length >= 3)
            {
                group.Colour = Color.FromArgb(
                    Clamp(colorArray[0], 0, 255),
                    Clamp(colorArray[1], 0, 255),
                    Clamp(colorArray[2], 0, 255));
            }
            foreach (var target in targets)
            {
                group.AddObject(target.InstanceGuid);
            }

            ApplyGraphMetadata(group, OptionalString(spec, "alias"), graphId, OptionalString(spec, "role") ?? "group");
            doc.AddObject(group, false);
            createdObjects?.Add(group);
            if (!string.IsNullOrWhiteSpace(OptionalString(spec, "alias")))
            {
                aliases[OptionalString(spec, "alias")] = group;
            }
            createdGroups.Add(new JObject
            {
                ["instance_id"] = group.InstanceGuid.ToString(),
                ["name"] = group.NickName,
                ["object_count"] = targets.Count,
                ["metadata"] = GraphMetadataToJson(group)
            });
        }
        return createdGroups;
    }

    private static JObject ApplyPreviewPolicy(
        GH_Document doc,
        Dictionary<string, IGH_DocumentObject> aliases,
        JObject policy,
        IEnumerable<IGH_DocumentObject> touchedObjects,
        string graphId)
    {
        if (policy == null)
        {
            return null;
        }

        string mode = OptionalString(policy, "mode") ?? "show";
        var targets = ResolveGraphTargets(doc, aliases, policy["targets"], "preview target");
        var changed = new JArray();

        void SetPreview(IGH_DocumentObject obj, bool visible)
        {
            if (obj is not IGH_PreviewObject previewObj)
            {
                return;
            }
            previewObj.Hidden = !visible;
            changed.Add(new JObject
            {
                ["instance_id"] = obj.InstanceGuid.ToString(),
                ["alias"] = GraphMetadataValue(obj, GhMetaAlias),
                ["nickname"] = obj.NickName,
                ["preview"] = visible
            });
        }

        if (mode.Equals("only", StringComparison.OrdinalIgnoreCase))
        {
            var scope = ResolveGraphTargets(doc, aliases, policy["scope"], "preview scope");
            if (scope.Count == 0)
            {
                string scopeGraphId = OptionalString(policy, "graph_id") ?? graphId;
                scope = GetGraphObjects(doc, scopeGraphId);
            }
            if (scope.Count == 0 && touchedObjects != null)
            {
                scope = touchedObjects.Distinct().ToList();
            }

            foreach (var obj in scope)
            {
                SetPreview(obj, false);
            }
            foreach (var obj in targets)
            {
                SetPreview(obj, true);
            }
        }
        else
        {
            bool visible = !mode.Equals("hide", StringComparison.OrdinalIgnoreCase);
            foreach (var obj in targets)
            {
                SetPreview(obj, visible);
            }
        }

        return new JObject
        {
            ["mode"] = mode,
            ["changed_count"] = changed.Count,
            ["changed"] = changed
        };
    }

    private static JObject VerifyGrasshopperOutputs(
        GH_Document doc,
        Dictionary<string, IGH_DocumentObject> aliases,
        JObject verifySpec)
    {
        if (verifySpec == null)
        {
            return null;
        }

        if (OptionalBool(verifySpec, "run_solution", false))
        {
            RunGrasshopperSolution(doc, true);
        }

        var checks = new JArray();
        bool allPassed = true;
        foreach (var outputToken in verifySpec["outputs"] as JArray ?? new JArray())
        {
            if (outputToken is not JObject outputSpec)
            {
                throw new ArgumentException("Each verification output must be an object.");
            }

            var obj = ResolveGraphObject(doc, aliases, OptionalString(outputSpec, "target") ?? OptionalString(outputSpec, "alias"), "verification target");
            var outputParam = FindOutputParam(
                obj,
                GetParamIndex(outputSpec, isOutput: true),
                GetParamName(outputSpec, isOutput: true));
            if (outputParam == null)
            {
                throw new InvalidOperationException($"Could not find verification output parameter on '{obj.NickName}'.");
            }
            if (!ParamHasData(outputParam))
            {
                EnsureInputSourcesHaveData(obj);
                ComputeGrasshopperObject(obj);
            }
            if (!ParamHasData(outputParam))
            {
                obj.ExpireSolution(true);
                RunGrasshopperSolution(doc, false);
            }

            var itemInfos = GrasshopperDataItems(outputParam).ToList();
            int dataCount = outputParam.VolatileData.DataCount;
            bool passed = true;
            var failures = new JArray();

            int? expectCountMin = outputSpec["expect_count_min"]?.ToObject<int?>();
            if (expectCountMin.HasValue && dataCount < expectCountMin.Value)
            {
                passed = false;
                failures.Add($"Expected at least {expectCountMin.Value} item(s), got {dataCount}.");
            }

            string expectType = OptionalString(outputSpec, "expect_type");
            if (!string.IsNullOrEmpty(expectType) && !itemInfos.Any(item => item.Type.Equals(expectType, StringComparison.OrdinalIgnoreCase)))
            {
                passed = false;
                failures.Add($"Expected output type '{expectType}'.");
            }

            bool? expectSolid = outputSpec["expect_solid"]?.ToObject<bool?>();
            if (expectSolid.HasValue && !itemInfos.Any(item => item.IsSolid == expectSolid.Value))
            {
                passed = false;
                failures.Add($"Expected solid={expectSolid.Value}.");
            }

            if (!passed)
            {
                allPassed = false;
            }

            int maxItems = Clamp(OptionalInt(outputSpec, "max_items", 5), 0, 100);
            checks.Add(new JObject
            {
                ["target"] = obj.NickName,
                ["alias"] = GraphMetadataValue(obj, GhMetaAlias),
                ["instance_id"] = obj.InstanceGuid.ToString(),
                ["param_name"] = outputParam.Name,
                ["passed"] = passed,
                ["data_count"] = dataCount,
                ["branch_count"] = outputParam.VolatileData.PathCount,
                ["sample"] = new JArray(itemInfos.Take(maxItems).Select(item => item.Json)),
                ["failures"] = failures
            });
        }

        return new JObject
        {
            ["passed"] = allPassed,
            ["check_count"] = checks.Count,
            ["checks"] = checks
        };
    }

    private sealed class GrasshopperDataItemInfo
    {
        public string Type { get; init; }
        public bool? IsSolid { get; init; }
        public JToken Json { get; init; }
    }

    private static IEnumerable<GrasshopperDataItemInfo> GrasshopperDataItems(IGH_Param param)
    {
        foreach (var path in param.VolatileData.Paths)
        {
            foreach (var item in param.VolatileData.get_Branch(path))
            {
                yield return new GrasshopperDataItemInfo
                {
                    Type = GrasshopperItemType(item),
                    IsSolid = item is GH_Brep brep ? brep.Value?.IsSolid : null,
                    Json = ExtractGrasshopperValue(item)
                };
            }
        }
    }

    private static string GrasshopperItemType(object item)
    {
        if (item is GH_Number) return "Number";
        if (item is GH_Integer) return "Integer";
        if (item is GH_Boolean) return "Boolean";
        if (item is GH_String) return "String";
        if (item is GH_Point) return "Point";
        if (item is GH_Vector) return "Vector";
        if (item is GH_Plane) return "Plane";
        if (item is GH_Line) return "Line";
        if (item is GH_Circle) return "Circle";
        if (item is GH_Curve) return "Curve";
        if (item is GH_Surface) return "Surface";
        if (item is GH_Brep) return "Brep";
        if (item is GH_Mesh) return "Mesh";
        return item is IGH_Goo goo ? goo.TypeName : item?.GetType().Name ?? "Null";
    }

    private static JObject BuildGraphSummary(
        GH_Document doc,
        IEnumerable<IGH_DocumentObject> preferredObjects,
        string graphId,
        JObject verification)
    {
        var objects = preferredObjects?.Distinct().ToList() ?? new List<IGH_DocumentObject>();
        if (objects.Count == 0)
        {
            objects = GetGraphObjects(doc, graphId);
        }

        var controls = new JArray();
        var outputs = new JArray();
        foreach (var obj in objects)
        {
            string role = GraphMetadataValue(obj, GhMetaRole);
            bool isControl = obj is GH_NumberSlider || obj is GH_BooleanToggle || obj is GH_ValueList;
            bool isOutput = role.Equals("output", StringComparison.OrdinalIgnoreCase) || obj is GH_Panel;
            if (isControl)
            {
                var control = new JObject
                {
                    ["alias"] = GraphMetadataValue(obj, GhMetaAlias),
                    ["name"] = obj.Name,
                    ["nickname"] = obj.NickName,
                    ["instance_id"] = obj.InstanceGuid.ToString()
                };
                AddSpecialGrasshopperState(control, obj);
                controls.Add(control);
            }
            if (isOutput)
            {
                outputs.Add(new JObject
                {
                    ["alias"] = GraphMetadataValue(obj, GhMetaAlias),
                    ["name"] = obj.Name,
                    ["nickname"] = obj.NickName,
                    ["instance_id"] = obj.InstanceGuid.ToString(),
                    ["role"] = role
                });
            }
        }

        return new JObject
        {
            ["graph_id"] = graphId,
            ["object_count"] = objects.Count,
            ["controls"] = controls,
            ["adjustable_parameters"] = controls.DeepClone(),
            ["outputs"] = outputs,
            ["verification"] = verification
        };
    }
}
