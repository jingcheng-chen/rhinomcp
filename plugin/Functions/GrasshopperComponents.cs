using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Special;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("gh_list_components", ReadOnly = true)]
    public JObject GhListComponents(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        string categoryFilter = OptionalString(parameters, "category");
        string nameFilter = OptionalString(parameters, "name");
        int limit = Clamp(OptionalInt(parameters, "limit", 100), 1, 1000);

        var query = doc.Objects.OfType<IGH_Component>().AsEnumerable();
        if (!string.IsNullOrEmpty(categoryFilter))
        {
            query = query.Where(c => c.Category?.Equals(categoryFilter, StringComparison.OrdinalIgnoreCase) == true);
        }
        if (!string.IsNullOrEmpty(nameFilter))
        {
            query = query.Where(c =>
                c.Name?.Contains(nameFilter, StringComparison.OrdinalIgnoreCase) == true ||
                c.NickName?.Contains(nameFilter, StringComparison.OrdinalIgnoreCase) == true);
        }

        var components = new JArray(query.Take(limit).Select(c =>
        {
            var item = new JObject
            {
                ["instance_id"] = c.InstanceGuid.ToString(),
                ["name"] = c.Name,
                ["nickname"] = c.NickName,
                ["category"] = c.Category,
                ["subcategory"] = c.SubCategory,
                ["description"] = c.Description,
                ["position"] = PivotToJson(c),
                ["input_count"] = c.Params.Input.Count,
                ["output_count"] = c.Params.Output.Count,
                ["runtime_message_level"] = c.RuntimeMessageLevel.ToString()
            };
            AddGraphMetadataFields(item, c);
            return item;
        }));

        return new JObject
        {
            ["count"] = components.Count,
            ["components"] = components
        };
    }

    [McpCommand("gh_get_component_info", ReadOnly = true)]
    public JObject GhGetComponentInfo(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        var obj = FindGhObject(doc, parameters);
        return DocumentObjectToDetailedJson(obj);
    }

    [McpCommand("gh_add_component")]
    public JObject GhAddComponent(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        string componentName = OptionalString(parameters, "component_name");
        string componentGuid = OptionalString(parameters, "component_guid");
        if (string.IsNullOrEmpty(componentName))
        {
            throw new ArgumentException("component_name is required.");
        }

        var position = parameters["position"] != null
            ? ReadPosition(parameters, "position", 0, 0)
            : FindNextGrasshopperSlot(doc);
        string nickname = OptionalString(parameters, "nickname");

        var obj = CreateGrasshopperObject(componentName, componentGuid, parameters);
        if (obj.Attributes == null)
        {
            obj.CreateAttributes();
        }
        obj.Attributes.Pivot = position;
        if (!string.IsNullOrEmpty(nickname))
        {
            obj.NickName = nickname;
        }

        doc.AddObject(obj, false);
        RunGrasshopperSolution(doc, false);
        RedrawGrasshopperCanvas(position);

        return new JObject
        {
            ["instance_id"] = obj.InstanceGuid.ToString(),
            ["name"] = obj.Name,
            ["nickname"] = obj.NickName,
            ["category"] = obj.Category,
            ["subcategory"] = obj.SubCategory,
            ["position"] = new JArray { position.X, position.Y },
            ["message"] = $"Added component '{obj.Name}' to canvas"
        };
    }

    [McpCommand("gh_layout_components")]
    public JObject GhLayoutComponents(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        bool includeGroups = OptionalBool(parameters, "include_groups", false);
        bool recompute = OptionalBool(parameters, "recompute", false);
        float xSpacing = (float)Math.Max(60, parameters["x_spacing"]?.ToObject<double>() ?? 220);
        float ySpacing = (float)Math.Max(40, parameters["y_spacing"]?.ToObject<double>() ?? 90);
        var start = ReadPosition(parameters, "start_position", 40, 40);
        var objects = GetLayoutObjects(doc, parameters, includeGroups);

        if (objects.Count == 0)
        {
            return new JObject
            {
                ["layout_count"] = 0,
                ["edge_count"] = 0,
                ["positions"] = new JArray(),
                ["recomputed"] = false,
                ["message"] = "No Grasshopper objects to layout"
            };
        }

        var layout = ApplyGrasshopperLayout(objects, start, xSpacing, ySpacing);

        if (recompute)
        {
            RunGrasshopperSolution(doc, false);
        }
        RedrawGrasshopperCanvas(start);

        return new JObject
        {
            ["layout_count"] = layout["layout_count"],
            ["edge_count"] = layout["edge_count"],
            ["positions"] = layout["positions"],
            ["recomputed"] = recompute,
            ["message"] = $"Laid out {objects.Count} Grasshopper object(s)"
        };
    }

    [McpCommand("gh_delete_component")]
    public JObject GhDeleteComponent(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        var obj = FindGhObject(doc, parameters);
        string id = obj.InstanceGuid.ToString();
        string name = obj.Name;
        string nickname = obj.NickName;

        doc.RemoveObject(obj, false);
        RunGrasshopperSolution(doc, false);

        return new JObject
        {
            ["deleted_id"] = id,
            ["name"] = name,
            ["nickname"] = nickname,
            ["message"] = $"Deleted component '{nickname}' ({name})"
        };
    }

    [McpCommand("gh_update_component")]
    public JObject GhUpdateComponent(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        var obj = FindGhObject(doc, parameters);

        if (parameters["new_nickname"] != null)
        {
            obj.NickName = parameters["new_nickname"]!.ToString();
        }
        if (parameters["position"] != null)
        {
            if (obj.Attributes == null)
            {
                obj.CreateAttributes();
            }
            obj.Attributes.Pivot = ReadPosition(parameters, "position", obj.Attributes.Pivot.X, obj.Attributes.Pivot.Y);
            obj.Attributes.ExpireLayout();
        }
        if (parameters["enabled"] != null && obj is IGH_ActiveObject activeObj)
        {
            activeObj.Locked = !parameters["enabled"]!.ToObject<bool>();
        }
        if (parameters["preview"] != null && obj is IGH_PreviewObject previewObj)
        {
            previewObj.Hidden = !parameters["preview"]!.ToObject<bool>();
        }

        obj.ExpireSolution(false);
        RunGrasshopperSolution(doc, false);

        return new JObject
        {
            ["instance_id"] = obj.InstanceGuid.ToString(),
            ["name"] = obj.Name,
            ["nickname"] = obj.NickName,
            ["position"] = PivotToJson(obj),
            ["message"] = $"Updated component '{obj.NickName}'"
        };
    }

    [McpCommand("gh_clear_canvas")]
    public JObject GhClearCanvas(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        bool includeGroups = OptionalBool(parameters, "include_groups", true);
        bool recompute = OptionalBool(parameters, "recompute", false);

        var objects = doc.Objects
            .Where(o => includeGroups || o is not GH_Group)
            .ToList();

        doc.RemoveObjects(objects, false);
        if (recompute)
        {
            RunGrasshopperSolution(doc, false);
        }

        return new JObject
        {
            ["deleted_count"] = objects.Count,
            ["include_groups"] = includeGroups,
            ["recomputed"] = recompute,
            ["message"] = $"Cleared {objects.Count} Grasshopper canvas object(s)"
        };
    }

    private static JObject DocumentObjectToDetailedJson(IGH_DocumentObject obj)
    {
        var result = new JObject
        {
            ["instance_id"] = obj.InstanceGuid.ToString(),
            ["name"] = obj.Name,
            ["nickname"] = obj.NickName,
            ["category"] = obj.Category,
            ["subcategory"] = obj.SubCategory,
            ["description"] = obj.Description,
            ["position"] = PivotToJson(obj),
            ["type"] = obj.GetType().Name
        };
        AddSpecialGrasshopperState(result, obj);
        AddGraphMetadataFields(result, obj);

        if (obj is IGH_Component component)
        {
            result["runtime_message_level"] = component.RuntimeMessageLevel.ToString();
            result["is_obsolete"] = component.Obsolete;
            result["inputs"] = ParamsToJson(component.Params.Input, includeSources: true);
            result["outputs"] = ParamsToJson(component.Params.Output, includeSources: true);
            result["runtime_messages"] = RuntimeMessagesToJson(component);
        }
        else if (obj is IGH_Param param)
        {
            result["type_name"] = param.TypeName;
            result["source_count"] = param.SourceCount;
            result["recipient_count"] = param.Recipients.Count;
            result["data_count"] = param.VolatileDataCount;
        }

        return result;
    }

    private static void AddSpecialGrasshopperState(JObject result, IGH_DocumentObject obj)
    {
        if (obj is IGH_PreviewObject previewObj)
        {
            result["preview"] = !previewObj.Hidden;
        }
        if (obj is IGH_ActiveObject activeObj)
        {
            result["enabled"] = !activeObj.Locked;
        }

        if (obj is GH_NumberSlider slider)
        {
            result["special_type"] = "number_slider";
            result["value"] = (double)slider.CurrentValue;
            result["min"] = (double)slider.Slider.Minimum;
            result["max"] = (double)slider.Slider.Maximum;
            result["decimals"] = slider.Slider.DecimalPlaces;
            result["expression"] = slider.Expression;
            return;
        }

        if (obj is GH_BooleanToggle toggle)
        {
            result["special_type"] = "boolean_toggle";
            result["value"] = toggle.Value;
            return;
        }

        if (obj is GH_Panel panel)
        {
            result["special_type"] = "panel";
            result["content"] = panel.UserText;
            return;
        }

        if (obj is GH_ValueList valueList)
        {
            result["special_type"] = "value_list";
            result["item_count"] = valueList.ListItems.Count;

            var items = new JArray();
            int selectedIndex = -1;
            for (int i = 0; i < valueList.ListItems.Count; i++)
            {
                var item = valueList.ListItems[i];
                if (item.Selected && selectedIndex < 0)
                {
                    selectedIndex = i;
                }
                items.Add(new JObject
                {
                    ["index"] = i,
                    ["name"] = item.Name,
                    ["expression"] = item.Expression,
                    ["selected"] = item.Selected
                });
            }

            result["selected_index"] = selectedIndex >= 0 ? selectedIndex : JValue.CreateNull();
            result["items"] = items;
        }
    }

    private static List<IGH_DocumentObject> GetLayoutObjects(GH_Document doc, JObject parameters, bool includeGroups)
    {
        var componentIds = parameters["component_ids"]?.ToObject<List<string>>() ?? new List<string>();
        if (componentIds.Count == 0)
        {
            return doc.Objects
                .Where(o => includeGroups || o is not GH_Group)
                .ToList();
        }

        var result = new List<IGH_DocumentObject>();
        foreach (string id in componentIds)
        {
            if (!Guid.TryParse(id, out var guid))
            {
                throw new ArgumentException($"Invalid component GUID: {id}");
            }
            var obj = doc.FindObject(guid, true);
            if (obj == null)
            {
                throw new InvalidOperationException($"Grasshopper object '{id}' not found.");
            }
            if (includeGroups || obj is not GH_Group)
            {
                result.Add(obj);
            }
        }
        return result;
    }

    private static IEnumerable<IGH_Param> GetInputParamsForLayout(IGH_DocumentObject obj)
    {
        if (obj is IGH_Component component)
        {
            return component.Params.Input;
        }
        if (obj is IGH_Param param)
        {
            return new[] { param };
        }
        return Enumerable.Empty<IGH_Param>();
    }

    private static JObject ApplyGrasshopperLayout(List<IGH_DocumentObject> objects, PointF start, float xSpacing, float ySpacing)
    {
        var objectSet = new HashSet<IGH_DocumentObject>(objects);
        var incoming = objects.ToDictionary(o => o, _ => new List<IGH_DocumentObject>());

        foreach (var target in objects)
        {
            foreach (var input in GetInputParamsForLayout(target))
            {
                foreach (var source in input.Sources)
                {
                    var sourceObj = source.Attributes?.GetTopLevel.DocObject;
                    if (sourceObj == null || sourceObj == target || !objectSet.Contains(sourceObj))
                    {
                        continue;
                    }
                    if (!incoming[target].Contains(sourceObj))
                    {
                        incoming[target].Add(sourceObj);
                    }
                }
            }
        }

        int edgeCount = incoming.Values.Sum(list => list.Count);
        var ordered = objects
            .OrderBy(o => PivotToJson(o)[0]?.ToObject<double>() ?? 0)
            .ThenBy(o => PivotToJson(o)[1]?.ToObject<double>() ?? 0)
            .ThenBy(o => o.NickName)
            .ToList();

        if (edgeCount == 0)
        {
            int rows = Math.Max(1, (int)Math.Ceiling(Math.Sqrt(ordered.Count)));
            for (int i = 0; i < ordered.Count; i++)
            {
                int column = i / rows;
                int row = i % rows;
                SetGrasshopperObjectPosition(
                    ordered[i],
                    new PointF(start.X + column * xSpacing, start.Y + row * ySpacing));
            }
        }
        else
        {
            var memo = new Dictionary<IGH_DocumentObject, int>();
            var visiting = new HashSet<IGH_DocumentObject>();

            int LevelOf(IGH_DocumentObject obj)
            {
                if (memo.TryGetValue(obj, out int level))
                {
                    return level;
                }
                if (!visiting.Add(obj))
                {
                    return 0;
                }

                int result = 0;
                foreach (var source in incoming[obj])
                {
                    result = Math.Max(result, LevelOf(source) + 1);
                }

                visiting.Remove(obj);
                memo[obj] = result;
                return result;
            }

            foreach (var group in ordered.GroupBy(LevelOf).OrderBy(g => g.Key))
            {
                int row = 0;
                foreach (var obj in group)
                {
                    SetGrasshopperObjectPosition(
                        obj,
                        new PointF(start.X + group.Key * xSpacing, start.Y + row * ySpacing));
                    row++;
                }
            }
        }

        var positions = new JArray(objects.Select(o => new JObject
        {
            ["instance_id"] = o.InstanceGuid.ToString(),
            ["name"] = o.Name,
            ["nickname"] = o.NickName,
            ["position"] = PivotToJson(o)
        }));

        return new JObject
        {
            ["layout_count"] = objects.Count,
            ["edge_count"] = edgeCount,
            ["positions"] = positions
        };
    }

    private static void SetGrasshopperObjectPosition(IGH_DocumentObject obj, PointF position)
    {
        if (obj.Attributes == null)
        {
            obj.CreateAttributes();
        }
        obj.Attributes.Pivot = position;
        obj.Attributes.ExpireLayout();
        obj.ExpireSolution(false);
    }

    private static PointF FindNextGrasshopperSlot(GH_Document doc)
    {
        var pivots = doc.Objects
            .Where(o => o.Attributes != null)
            .Select(o => o.Attributes.Pivot)
            .ToList();

        if (pivots.Count == 0)
        {
            return new PointF(40, 40);
        }

        float minY = pivots.Min(p => p.Y);
        float maxX = pivots.Max(p => p.X);
        return new PointF(maxX + 220, minY);
    }

    private static IGH_DocumentObject CreateGrasshopperObject(string componentName, string componentGuid, JObject parameters)
    {
        var obj = TryCreateSpecialGrasshopperObject(componentName, parameters);
        if (obj != null)
        {
            return obj;
        }

        var proxy = FindComponentProxy(componentName, componentGuid);
        if (proxy == null)
        {
            var suggestions = FindSimilarComponents(componentName ?? componentGuid ?? "", 3);
            string suffix = suggestions.Count > 0
                ? $". Did you mean: {string.Join(", ", suggestions)}?"
                : ". Use gh_search_components to find a valid component name or GUID.";
            throw new InvalidOperationException($"Component '{componentName ?? componentGuid}' not found{suffix}");
        }

        obj = proxy.CreateInstance();
        if (obj == null)
        {
            throw new InvalidOperationException($"Failed to create instance of component '{proxy.Desc.Name}'.");
        }
        InitializeSpecialComponent(obj, parameters);
        return obj;
    }

    private static IGH_DocumentObject TryCreateSpecialGrasshopperObject(string componentName, JObject parameters)
    {
        if (string.IsNullOrEmpty(componentName)) return null;
        var name = GhComponentAliases.TryGetValue(componentName, out var alias) ? alias : componentName;

        if (name.Equals("Number Slider", StringComparison.OrdinalIgnoreCase))
        {
            var slider = new GH_NumberSlider();
            InitializeNumberSlider(slider, parameters);
            return slider;
        }
        if (name.Equals("Boolean Toggle", StringComparison.OrdinalIgnoreCase))
        {
            return new GH_BooleanToggle { Value = parameters["value"]?.ToObject<bool>() ?? false };
        }
        if (name.Equals("Panel", StringComparison.OrdinalIgnoreCase))
        {
            var panel = new GH_Panel();
            string content = parameters["content"]?.ToString() ?? parameters["value"]?.ToString() ?? "";
            if (!string.IsNullOrEmpty(content))
            {
                panel.SetUserText(content);
            }
            return panel;
        }
        if (name.Equals("Value List", StringComparison.OrdinalIgnoreCase))
        {
            return new GH_ValueList();
        }
        if (name.Equals("Relay", StringComparison.OrdinalIgnoreCase))
        {
            return new GH_Relay();
        }
        if (name.Equals("Scribble", StringComparison.OrdinalIgnoreCase) ||
            name.Equals("Note", StringComparison.OrdinalIgnoreCase))
        {
            return new GH_Scribble
            {
                Text = parameters["text"]?.ToString() ?? parameters["content"]?.ToString() ?? "Note"
            };
        }

        return null;
    }

    private static void InitializeSpecialComponent(IGH_DocumentObject obj, JObject parameters)
    {
        if (obj is GH_NumberSlider slider)
        {
            InitializeNumberSlider(slider, parameters);
        }
        else if (obj is GH_BooleanToggle toggle && parameters["value"] != null)
        {
            toggle.Value = parameters["value"]!.ToObject<bool>();
        }
        else if (obj is GH_Panel panel)
        {
            string content = parameters["content"]?.ToString() ?? parameters["value"]?.ToString();
            if (!string.IsNullOrEmpty(content))
            {
                panel.SetUserText(content);
            }
        }
    }

    private static void InitializeNumberSlider(GH_NumberSlider slider, JObject parameters)
    {
        decimal min = parameters["min"]?.ToObject<decimal>() ?? 0;
        decimal max = parameters["max"]?.ToObject<decimal>() ?? 100;
        decimal value = parameters["value"]?.ToObject<decimal>() ?? (min + max) / 2;
        if (min > max)
        {
            throw new ArgumentException("Slider min must be less than or equal to max.");
        }
        if (value < min) value = min;
        if (value > max) value = max;

        slider.Slider.Minimum = min;
        slider.Slider.Maximum = max;
        SetNumberSliderValue(slider, value);
        slider.Slider.DecimalPlaces = Clamp(parameters["decimals"]?.ToObject<int>() ?? 2, 0, 12);
    }
}
