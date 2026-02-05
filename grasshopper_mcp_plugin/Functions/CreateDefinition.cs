using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Special;
using Grasshopper.Kernel.Types;
using Newtonsoft.Json.Linq;
using Rhino.Geometry;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Known component name aliases for common variations.
    /// Maps user-friendly names to actual Grasshopper component names.
    /// </summary>
    private static readonly Dictionary<string, string> ComponentAliases = new(StringComparer.OrdinalIgnoreCase)
    {
        // Sliders
        ["Slider"] = "Number Slider",
        ["NumSlider"] = "Number Slider",
        ["Num Slider"] = "Number Slider",

        // Parameters
        ["Pt"] = "Point",
        ["Point Param"] = "Point",
        ["Point Parameter"] = "Point",
        ["Crv"] = "Curve",
        ["Curve Param"] = "Curve",
        ["Srf"] = "Surface",
        ["Brep Param"] = "Brep",

        // Math
        ["Add"] = "Addition",
        ["Sum"] = "Addition",
        ["Plus"] = "Addition",
        ["Subtract"] = "Subtraction",
        ["Minus"] = "Subtraction",
        ["Multiply"] = "Multiplication",
        ["Mult"] = "Multiplication",
        ["Times"] = "Multiplication",
        ["Divide"] = "Division",
        ["Div"] = "Division",

        // Common geometry
        ["Circ"] = "Circle",
        ["Rect"] = "Rectangle",
        ["Ln"] = "Line",
        ["Pln"] = "Plane",
        ["Vec"] = "Vector",
        ["Pt3d"] = "Construct Point",

        // Transforms
        ["Mv"] = "Move",
        ["Rot"] = "Rotate",
        ["Scl"] = "Scale",

        // Lists
        ["Lst"] = "List Item",
        ["ListItem"] = "List Item",
        ["Flatten"] = "Flatten Tree",
        ["Graft"] = "Graft Tree",
    };

    /// <summary>
    /// Names that map to special components that need direct instantiation.
    /// These are in Grasshopper.Kernel.Special namespace.
    /// </summary>
    private static readonly HashSet<string> SpecialComponentNames = new(StringComparer.OrdinalIgnoreCase)
    {
        "Number Slider", "Slider", "NumSlider", "Num Slider",
        "Boolean Toggle", "Toggle", "Bool Toggle",
        "Panel", "Text Panel",
        "Value List", "ValueList",
        "Colour Swatch", "Color Swatch", "ColourSwatch", "ColorSwatch",
        "Gradient", "Gradient Control",
        "Data Recorder", "DataRecorder", "Recorder",
        "Timer",
        "Data Dam", "DataDam", "Dam",
        "Relay",
        "Cluster Input", "ClusterInput",
        "Cluster Output", "ClusterOutput",
        "Scribble", "Text", "Note",
        "Group",
        "Jump",
    };

    /// <summary>
    /// Try to create a special component directly (sliders, toggles, panels, etc.).
    /// Returns null if this is not a special component name.
    /// </summary>
    private IGH_DocumentObject? TryCreateSpecialComponent(string componentName, JObject spec)
    {
        // Normalize the name through aliases
        var normalizedName = ComponentAliases.TryGetValue(componentName, out var aliased) ? aliased : componentName;

        // Number Slider
        if (normalizedName.Equals("Number Slider", StringComparison.OrdinalIgnoreCase))
        {
            var slider = new GH_NumberSlider();
            var min = spec["min"]?.ToObject<decimal>() ?? 0;
            var max = spec["max"]?.ToObject<decimal>() ?? 100;
            var value = spec["value"]?.ToObject<decimal>() ?? (min + max) / 2;
            var decimals = spec["decimals"]?.ToObject<int>() ?? 2;

            slider.Slider.Minimum = min;
            slider.Slider.Maximum = max;
            slider.Slider.Value = value;
            slider.Slider.DecimalPlaces = decimals;
            return slider;
        }

        // Boolean Toggle
        if (normalizedName.Equals("Boolean Toggle", StringComparison.OrdinalIgnoreCase) ||
            normalizedName.Equals("Toggle", StringComparison.OrdinalIgnoreCase) ||
            normalizedName.Equals("Bool Toggle", StringComparison.OrdinalIgnoreCase))
        {
            var toggle = new GH_BooleanToggle();
            var value = spec["value"]?.ToObject<bool>() ?? false;
            toggle.Value = value;
            return toggle;
        }

        // Panel
        if (normalizedName.Equals("Panel", StringComparison.OrdinalIgnoreCase) ||
            normalizedName.Equals("Text Panel", StringComparison.OrdinalIgnoreCase))
        {
            var panel = new GH_Panel();
            var content = spec["content"]?.ToString() ?? spec["value"]?.ToString() ?? "";
            if (!string.IsNullOrEmpty(content))
            {
                panel.SetUserText(content);
            }
            return panel;
        }

        // Value List
        if (normalizedName.Equals("Value List", StringComparison.OrdinalIgnoreCase) ||
            normalizedName.Equals("ValueList", StringComparison.OrdinalIgnoreCase))
        {
            var valueList = new GH_ValueList();
            return valueList;
        }

        // Colour Swatch
        if (normalizedName.Equals("Colour Swatch", StringComparison.OrdinalIgnoreCase) ||
            normalizedName.Equals("Color Swatch", StringComparison.OrdinalIgnoreCase) ||
            normalizedName.Equals("ColourSwatch", StringComparison.OrdinalIgnoreCase) ||
            normalizedName.Equals("ColorSwatch", StringComparison.OrdinalIgnoreCase))
        {
            var swatch = new GH_ColourSwatch();
            return swatch;
        }

        // Relay
        if (normalizedName.Equals("Relay", StringComparison.OrdinalIgnoreCase))
        {
            var relay = new GH_Relay();
            return relay;
        }

        // Scribble (text annotation)
        if (normalizedName.Equals("Scribble", StringComparison.OrdinalIgnoreCase) ||
            normalizedName.Equals("Note", StringComparison.OrdinalIgnoreCase))
        {
            var scribble = new GH_Scribble();
            var text = spec["text"]?.ToString() ?? spec["content"]?.ToString() ?? "Note";
            scribble.Text = text;
            return scribble;
        }

        // Group
        if (normalizedName.Equals("Group", StringComparison.OrdinalIgnoreCase))
        {
            var group = new GH_Group();
            var name = spec["group_name"]?.ToString() ?? spec["name"]?.ToString() ?? "";
            if (!string.IsNullOrEmpty(name))
            {
                group.NickName = name;
            }
            return group;
        }

        // Not a known special component
        return null;
    }
    /// <summary>
    /// Create a complete Grasshopper definition from a JSON specification.
    /// This allows creating multiple components, connections, and setting values in one batch operation.
    /// </summary>
    public JObject CreateDefinition(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        var components = parameters["components"] as JArray ?? new JArray();
        var connections = parameters["connections"] as JArray ?? new JArray();
        var values = parameters["values"] as JArray ?? new JArray();
        var clearCanvas = parameters["clear_canvas"]?.ToObject<bool>() ?? false;

        // Track created components by nickname for connection resolution
        var createdComponents = new Dictionary<string, IGH_DocumentObject>(StringComparer.OrdinalIgnoreCase);
        var results = new JObject();
        var componentResults = new JArray();
        var connectionResults = new JArray();
        var valueResults = new JArray();
        var errors = new JArray();

        // Clear canvas if requested
        if (clearCanvas)
        {
            doc.RemoveObjects(doc.Objects.ToList(), false);
        }

        // Phase 1: Create all components
        foreach (var compSpec in components)
        {
            try
            {
                var compResult = CreateSingleComponent(doc, compSpec as JObject, createdComponents);
                componentResults.Add(compResult);
            }
            catch (Exception ex)
            {
                errors.Add(new JObject
                {
                    ["phase"] = "component_creation",
                    ["spec"] = compSpec,
                    ["error"] = ex.Message
                });
            }
        }

        // Phase 2: Create all connections
        foreach (var connSpec in connections)
        {
            try
            {
                var connResult = CreateSingleConnection(doc, connSpec as JObject, createdComponents);
                connectionResults.Add(connResult);
            }
            catch (Exception ex)
            {
                errors.Add(new JObject
                {
                    ["phase"] = "connection",
                    ["spec"] = connSpec,
                    ["error"] = ex.Message
                });
            }
        }

        // Phase 3: Set all values
        foreach (var valSpec in values)
        {
            try
            {
                var valResult = SetSingleValue(doc, valSpec as JObject, createdComponents);
                valueResults.Add(valResult);
            }
            catch (Exception ex)
            {
                errors.Add(new JObject
                {
                    ["phase"] = "set_value",
                    ["spec"] = valSpec,
                    ["error"] = ex.Message
                });
            }
        }

        // Trigger solution
        doc.NewSolution(false);

        results["components_created"] = componentResults.Count;
        results["connections_created"] = connectionResults.Count;
        results["values_set"] = valueResults.Count;
        results["error_count"] = errors.Count;
        results["components"] = componentResults;
        results["connections"] = connectionResults;
        results["values"] = valueResults;

        if (errors.Count > 0)
        {
            results["errors"] = errors;
        }

        results["message"] = errors.Count == 0
            ? $"Successfully created definition with {componentResults.Count} components, {connectionResults.Count} connections, {valueResults.Count} values"
            : $"Created definition with {errors.Count} error(s)";

        return results;
    }

    /// <summary>
    /// Create a single component from specification.
    /// </summary>
    private JObject CreateSingleComponent(GH_Document doc, JObject? spec, Dictionary<string, IGH_DocumentObject> createdComponents)
    {
        if (spec == null)
            throw new ArgumentException("Component specification is null");

        var componentName = spec["name"]?.ToString();
        var nickname = spec["nickname"]?.ToString();
        var positionArray = spec["position"] as JArray;
        var componentGuid = spec["component_guid"]?.ToString();

        if (string.IsNullOrEmpty(componentName))
            throw new ArgumentException("Component name is required");

        // Default position
        float x = 0, y = 0;
        if (positionArray != null && positionArray.Count >= 2)
        {
            x = positionArray[0].ToObject<float>();
            y = positionArray[1].ToObject<float>();
        }

        IGH_DocumentObject? obj = null;

        // First try to create special components directly (sliders, toggles, panels, etc.)
        // These are in Grasshopper.Kernel.Special and may not be found through proxy lookup
        obj = TryCreateSpecialComponent(componentName, spec);

        // If not a special component, use proxy lookup
        if (obj == null)
        {
            var proxy = FindComponentProxy(componentName, componentGuid);

            if (proxy == null)
            {
                // Build helpful error message with suggestions
                var suggestions = FindSimilarComponents(componentName, 3);
                var suggestionText = suggestions.Any()
                    ? $". Did you mean: {string.Join(", ", suggestions)}?"
                    : ". Use search_components tool to find valid component names.";
                throw new InvalidOperationException($"Component '{componentName}' not found in Grasshopper library{suggestionText}");
            }

            obj = proxy.CreateInstance();
            if (obj == null)
                throw new InvalidOperationException($"Failed to create instance of component '{componentName}'");

            // Initialize special components that were found via proxy (may have sliders, etc. from plugins)
            InitializeSpecialComponent(obj, spec);
        }

        // Ensure attributes are created (required for newly instantiated special components)
        if (obj.Attributes == null)
        {
            obj.CreateAttributes();
        }

        // Set position
        obj.Attributes.Pivot = new PointF(x, y);

        // Set nickname if provided
        if (!string.IsNullOrEmpty(nickname))
        {
            obj.NickName = nickname;
        }

        // Add to document
        doc.AddObject(obj, false);

        // Track for later connection resolution
        var key = !string.IsNullOrEmpty(nickname) ? nickname : obj.InstanceGuid.ToString();
        createdComponents[key] = obj;

        // Also track by instance_id
        createdComponents[obj.InstanceGuid.ToString()] = obj;

        return new JObject
        {
            ["instance_id"] = obj.InstanceGuid.ToString(),
            ["name"] = obj.Name,
            ["nickname"] = obj.NickName,
            ["position"] = new JArray { x, y }
        };
    }

    /// <summary>
    /// Find a component proxy using multiple search strategies.
    /// </summary>
    private IGH_ObjectProxy? FindComponentProxy(string componentName, string? componentGuid)
    {
        IGH_ObjectProxy? proxy = null;

        // Strategy 1: Try by GUID first
        if (!string.IsNullOrEmpty(componentGuid) && Guid.TryParse(componentGuid, out var guid))
        {
            proxy = Instances.ComponentServer.ObjectProxies.FirstOrDefault(p => p.Guid == guid);
            if (proxy != null) return proxy;
        }

        // Strategy 2: Try alias lookup
        if (ComponentAliases.TryGetValue(componentName, out var aliasedName))
        {
            proxy = Instances.ComponentServer.FindObjectByName(aliasedName, true, true);
            if (proxy != null) return proxy;
        }

        // Strategy 3: Try exact name match
        proxy = Instances.ComponentServer.FindObjectByName(componentName, true, true);
        if (proxy != null) return proxy;

        // Strategy 4: Try case-insensitive exact match on Name
        proxy = Instances.ComponentServer.ObjectProxies
            .FirstOrDefault(p => p.Desc.Name.Equals(componentName, StringComparison.OrdinalIgnoreCase));
        if (proxy != null) return proxy;

        // Strategy 5: Try case-insensitive exact match on NickName
        proxy = Instances.ComponentServer.ObjectProxies
            .FirstOrDefault(p => p.Desc.NickName?.Equals(componentName, StringComparison.OrdinalIgnoreCase) == true);
        if (proxy != null) return proxy;

        // Strategy 6: Try partial match on Name (contains)
        proxy = Instances.ComponentServer.ObjectProxies
            .FirstOrDefault(p => p.Desc.Name.Contains(componentName, StringComparison.OrdinalIgnoreCase));
        if (proxy != null) return proxy;

        // Strategy 7: Try partial match on NickName (contains)
        proxy = Instances.ComponentServer.ObjectProxies
            .FirstOrDefault(p => p.Desc.NickName?.Contains(componentName, StringComparison.OrdinalIgnoreCase) == true);

        return proxy;
    }

    /// <summary>
    /// Find similar component names for suggestions.
    /// </summary>
    private List<string> FindSimilarComponents(string searchName, int maxResults)
    {
        return Instances.ComponentServer.ObjectProxies
            .Where(p => p.Desc.Name.Contains(searchName.Substring(0, Math.Min(3, searchName.Length)), StringComparison.OrdinalIgnoreCase))
            .Take(maxResults)
            .Select(p => p.Desc.Name)
            .ToList();
    }

    /// <summary>
    /// Initialize special components that need extra setup (sliders, etc.).
    /// </summary>
    private void InitializeSpecialComponent(IGH_DocumentObject obj, JObject spec)
    {
        // Handle Number Slider initialization
        if (obj is GH_NumberSlider slider)
        {
            var min = spec["min"]?.ToObject<decimal>() ?? 0;
            var max = spec["max"]?.ToObject<decimal>() ?? 100;
            var value = spec["value"]?.ToObject<decimal>() ?? (min + max) / 2;
            var decimals = spec["decimals"]?.ToObject<int>() ?? 2;

            slider.Slider.Minimum = min;
            slider.Slider.Maximum = max;
            slider.Slider.Value = value;
            slider.Slider.DecimalPlaces = decimals;
        }

        // Handle Boolean Toggle initialization
        if (obj is GH_BooleanToggle toggle)
        {
            var value = spec["value"]?.ToObject<bool>() ?? false;
            toggle.Value = value;
        }

        // Handle Panel initialization
        if (obj is GH_Panel panel)
        {
            var content = spec["content"]?.ToString() ?? spec["value"]?.ToString();
            if (!string.IsNullOrEmpty(content))
            {
                panel.SetUserText(content);
            }
        }
    }

    /// <summary>
    /// Create a single connection from specification.
    /// </summary>
    private JObject CreateSingleConnection(GH_Document doc, JObject? spec, Dictionary<string, IGH_DocumentObject> createdComponents)
    {
        if (spec == null)
            throw new ArgumentException("Connection specification is null");

        // Get source component
        var sourceRef = spec["source"]?.ToString()
                     ?? spec["source_nickname"]?.ToString()
                     ?? spec["source_instance_id"]?.ToString();
        var sourceOutput = spec["source_output"]?.ToObject<int>() ?? 0;

        // Get target component
        var targetRef = spec["target"]?.ToString()
                     ?? spec["target_nickname"]?.ToString()
                     ?? spec["target_instance_id"]?.ToString();
        var targetInput = spec["target_input"]?.ToObject<int>() ?? 0;

        if (string.IsNullOrEmpty(sourceRef))
            throw new ArgumentException("Source component reference is required");
        if (string.IsNullOrEmpty(targetRef))
            throw new ArgumentException("Target component reference is required");

        // Find source component
        if (!createdComponents.TryGetValue(sourceRef, out var sourceObj))
        {
            // Try finding in document
            sourceObj = FindComponentByReference(doc, sourceRef);
        }
        if (sourceObj == null)
            throw new InvalidOperationException($"Source component '{sourceRef}' not found");

        // Find target component
        if (!createdComponents.TryGetValue(targetRef, out var targetObj))
        {
            targetObj = FindComponentByReference(doc, targetRef);
        }
        if (targetObj == null)
            throw new InvalidOperationException($"Target component '{targetRef}' not found");

        // Get output parameter
        var outputParam = ComponentHelper.FindOutputParam(sourceObj, sourceOutput, null);
        if (outputParam == null)
            throw new InvalidOperationException($"Output parameter {sourceOutput} not found on '{sourceRef}'");

        // Get input parameter
        var inputParam = ComponentHelper.FindInputParam(targetObj, targetInput, null);
        if (inputParam == null)
            throw new InvalidOperationException($"Input parameter {targetInput} not found on '{targetRef}'");

        // Create connection
        inputParam.AddSource(outputParam);

        return new JObject
        {
            ["source"] = sourceObj.NickName,
            ["source_output"] = outputParam.Name,
            ["target"] = targetObj.NickName,
            ["target_input"] = inputParam.Name
        };
    }

    /// <summary>
    /// Set a single value from specification.
    /// </summary>
    private JObject SetSingleValue(GH_Document doc, JObject? spec, Dictionary<string, IGH_DocumentObject> createdComponents)
    {
        if (spec == null)
            throw new ArgumentException("Value specification is null");

        var componentRef = spec["component"]?.ToString()
                        ?? spec["nickname"]?.ToString()
                        ?? spec["instance_id"]?.ToString();
        var inputIndex = spec["input"]?.Type == JTokenType.Integer
            ? spec["input"]?.ToObject<int>()
            : (int?)null;
        var inputName = spec["input"]?.Type == JTokenType.String
            ? spec["input"]?.ToString()
            : spec["input_name"]?.ToString();
        var value = spec["value"];

        if (string.IsNullOrEmpty(componentRef))
            throw new ArgumentException("Component reference is required");
        if (value == null)
            throw new ArgumentException("Value is required");

        // Find component
        if (!createdComponents.TryGetValue(componentRef, out var obj))
        {
            obj = FindComponentByReference(doc, componentRef);
        }
        if (obj == null)
            throw new InvalidOperationException($"Component '{componentRef}' not found");

        // Find input parameter
        IGH_Param? inputParam = null;

        if (inputIndex.HasValue)
        {
            inputParam = ComponentHelper.FindInputParam(obj, inputIndex, null);
        }
        else if (!string.IsNullOrEmpty(inputName))
        {
            inputParam = ComponentHelper.FindInputParam(obj, null, inputName);
        }
        else
        {
            // Default to first input
            inputParam = ComponentHelper.FindInputParam(obj, 0, null);
        }

        if (inputParam == null)
            throw new InvalidOperationException($"Input parameter not found on '{componentRef}'");

        // Set the value
        SetParamValue(inputParam, value);

        return new JObject
        {
            ["component"] = obj.NickName,
            ["input"] = inputParam.Name,
            ["value_type"] = value.Type.ToString()
        };
    }

    /// <summary>
    /// Find a component by reference (nickname or GUID).
    /// </summary>
    private IGH_DocumentObject? FindComponentByReference(GH_Document doc, string reference)
    {
        // Try as GUID
        if (Guid.TryParse(reference, out var guid))
        {
            return doc.FindObject(guid, true);
        }

        // Try as nickname
        return doc.Objects.FirstOrDefault(o =>
            o.NickName.Equals(reference, StringComparison.OrdinalIgnoreCase));
    }
}
