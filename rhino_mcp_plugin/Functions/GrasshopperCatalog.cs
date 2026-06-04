using System;
using System.Collections.Generic;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("gh_search_components", ReadOnly = true)]
    public JObject GhSearchComponents(JObject parameters)
    {
        string query = OptionalString(parameters, "query");
        string category = OptionalString(parameters, "category");
        int limit = Clamp(OptionalInt(parameters, "limit", 50), 1, 500);

        var filtered = FilterComponentProxies(query, category);
        if (!string.IsNullOrEmpty(query))
        {
            filtered = filtered
                .OrderByDescending(p => p.Desc.Name.Equals(query, StringComparison.OrdinalIgnoreCase))
                .ThenByDescending(p => p.Desc.NickName?.Equals(query, StringComparison.OrdinalIgnoreCase) == true)
                .ThenBy(p => p.Desc.Name);
        }
        else
        {
            filtered = filtered.OrderBy(p => p.Desc.Category).ThenBy(p => p.Desc.Name);
        }

        var components = new JArray(filtered.Take(limit).Select(p => ComponentProxyToJson(p)));
        return new JObject
        {
            ["count"] = components.Count,
            ["query"] = query,
            ["category"] = category,
            ["components"] = components
        };
    }

    [McpCommand("gh_batch_search_components", ReadOnly = true)]
    public JObject GhBatchSearchComponents(JObject parameters)
    {
        var queries = parameters["queries"]?.ToObject<List<string>>() ?? new List<string>();
        var proxies = Instances.ComponentServer.ObjectProxies.ToList();
        var results = new JObject();
        var notFound = new JArray();
        int foundCount = 0;

        foreach (string query in queries.Where(q => !string.IsNullOrWhiteSpace(q)))
        {
            var proxy = FindComponentProxy(query, null, proxies);
            if (proxy == null)
            {
                results[query] = null;
                notFound.Add(query);
                continue;
            }

            results[query] = ComponentProxyToJson(proxy, includeDescription: false);
            foundCount++;
        }

        return new JObject
        {
            ["results"] = results,
            ["found_count"] = foundCount,
            ["total_queries"] = queries.Count,
            ["not_found"] = notFound
        };
    }

    [McpCommand("gh_list_component_categories", ReadOnly = true)]
    public JObject GhListComponentCategories(JObject parameters)
    {
        var categories = Instances.ComponentServer.ObjectProxies
            .Where(p => !string.IsNullOrEmpty(p.Desc.Category))
            .GroupBy(p => p.Desc.Category)
            .OrderBy(g => g.Key)
            .Select(g => new JObject
            {
                ["category"] = g.Key,
                ["component_count"] = g.Count(),
                ["subcategories"] = new JArray(
                    g.Where(p => !string.IsNullOrEmpty(p.Desc.SubCategory))
                        .Select(p => p.Desc.SubCategory)
                        .Distinct()
                        .OrderBy(s => s)
                )
            });

        var array = new JArray(categories);
        return new JObject
        {
            ["category_count"] = array.Count,
            ["categories"] = array
        };
    }

    [McpCommand("gh_get_available_components", ReadOnly = true)]
    public JObject GhGetAvailableComponents(JObject parameters)
    {
        string category = OptionalString(parameters, "category");
        bool includeDescription = OptionalBool(parameters, "include_description", false);
        int limit = Clamp(OptionalInt(parameters, "limit", 500), 1, 2000);

        var filtered = FilterComponentProxies(null, category)
            .OrderBy(p => p.Desc.Category)
            .ThenBy(p => p.Desc.Name)
            .ToList();

        var categories = filtered
            .Select(p => p.Desc.Category)
            .Where(c => !string.IsNullOrEmpty(c))
            .Distinct()
            .OrderBy(c => c);

        var components = new JArray(filtered.Take(limit).Select(p => ComponentProxyToJson(p, includeDescription)));
        return new JObject
        {
            ["count"] = components.Count,
            ["total_available"] = Instances.ComponentServer.ObjectProxies.Count(),
            ["category_filter"] = category,
            ["categories"] = new JArray(categories),
            ["components"] = components
        };
    }

    [McpCommand("gh_get_component_type_info", ReadOnly = true)]
    public JObject GhGetComponentTypeInfo(JObject parameters)
    {
        string name = OptionalString(parameters, "name");
        string guid = OptionalString(parameters, "guid");
        if (string.IsNullOrEmpty(name) && string.IsNullOrEmpty(guid))
        {
            throw new ArgumentException("Either name or guid is required.");
        }

        var proxy = FindComponentProxy(name, guid);
        if (proxy == null)
        {
            return new JObject
            {
                ["success"] = false,
                ["message"] = $"Component '{name ?? guid}' not found",
                ["suggestions"] = new JArray(FindSimilarComponents(name ?? guid ?? "", 5))
            };
        }

        var result = ComponentProxyToJson(proxy, includeDescription: true);
        result["success"] = true;

        try
        {
            var instance = proxy.CreateInstance();
            if (instance is IGH_Component component)
            {
                result["inputs"] = ParamsToJson(component.Params.Input, includeSources: false);
                result["outputs"] = ParamsToJson(component.Params.Output, includeSources: false);
                result["input_count"] = component.Params.Input.Count;
                result["output_count"] = component.Params.Output.Count;
                AddComponentWarnings(result, proxy.Desc.Name);
            }
            else if (instance is IGH_Param param)
            {
                result["is_parameter"] = true;
                result["type_name"] = param.TypeName;
                result["inputs"] = new JArray();
                result["outputs"] = new JArray { ParamToJson(param, 0, includeSources: false) };
                result["input_count"] = 0;
                result["output_count"] = 1;
            }
        }
        catch (Exception ex)
        {
            result["warning"] = $"Could not create a temporary instance for detailed type info: {ex.Message}";
        }

        return result;
    }

    private static IEnumerable<IGH_ObjectProxy> FilterComponentProxies(string query, string category)
    {
        IEnumerable<IGH_ObjectProxy> filtered = Instances.ComponentServer.ObjectProxies;
        if (!string.IsNullOrEmpty(category))
        {
            filtered = filtered.Where(p => p.Desc.Category?.Contains(category, StringComparison.OrdinalIgnoreCase) == true);
        }
        if (!string.IsNullOrEmpty(query))
        {
            filtered = filtered.Where(p =>
                p.Desc.Name?.Contains(query, StringComparison.OrdinalIgnoreCase) == true ||
                p.Desc.NickName?.Contains(query, StringComparison.OrdinalIgnoreCase) == true ||
                p.Desc.Description?.Contains(query, StringComparison.OrdinalIgnoreCase) == true);
        }
        return filtered;
    }

    private static JObject ComponentProxyToJson(IGH_ObjectProxy proxy, bool includeDescription = true)
    {
        var result = new JObject
        {
            ["name"] = proxy.Desc.Name,
            ["nickname"] = proxy.Desc.NickName,
            ["category"] = proxy.Desc.Category,
            ["subcategory"] = proxy.Desc.SubCategory,
            ["guid"] = proxy.Guid.ToString()
        };
        if (includeDescription)
        {
            result["description"] = proxy.Desc.Description;
        }
        return result;
    }

    private static IGH_ObjectProxy FindComponentProxy(string componentName, string componentGuid, List<IGH_ObjectProxy> proxies = null)
    {
        proxies ??= Instances.ComponentServer.ObjectProxies.ToList();

        if (!string.IsNullOrEmpty(componentGuid))
        {
            if (!Guid.TryParse(componentGuid, out var guid))
            {
                throw new ArgumentException($"Invalid component GUID: {componentGuid}");
            }
            var byGuid = proxies.FirstOrDefault(p => p.Guid == guid);
            if (byGuid != null) return byGuid;
        }

        if (string.IsNullOrEmpty(componentName))
        {
            return null;
        }

        if (GhComponentAliases.TryGetValue(componentName, out var alias))
        {
            var aliased = Instances.ComponentServer.FindObjectByName(alias, true, true);
            if (aliased != null) return aliased;
        }

        var direct = Instances.ComponentServer.FindObjectByName(componentName, true, true);
        if (direct != null) return direct;

        return proxies.FirstOrDefault(p => p.Desc.Name.Equals(componentName, StringComparison.OrdinalIgnoreCase))
            ?? proxies.FirstOrDefault(p => p.Desc.NickName?.Equals(componentName, StringComparison.OrdinalIgnoreCase) == true)
            ?? proxies.FirstOrDefault(p => p.Desc.Name.Contains(componentName, StringComparison.OrdinalIgnoreCase))
            ?? proxies.FirstOrDefault(p => p.Desc.NickName?.Contains(componentName, StringComparison.OrdinalIgnoreCase) == true);
    }

    private static List<string> FindSimilarComponents(string searchName, int maxResults)
    {
        if (string.IsNullOrEmpty(searchName))
        {
            return new List<string>();
        }
        string prefix = searchName.Substring(0, Math.Min(3, searchName.Length));
        return Instances.ComponentServer.ObjectProxies
            .Where(p => p.Desc.Name.Contains(prefix, StringComparison.OrdinalIgnoreCase))
            .Take(maxResults)
            .Select(p => p.Desc.Name)
            .ToList();
    }

    private static void AddComponentWarnings(JObject result, string componentName)
    {
        var warnings = new JArray();

        if (componentName.Equals("Expression", StringComparison.OrdinalIgnoreCase) ||
            componentName.Equals("Evaluate", StringComparison.OrdinalIgnoreCase))
        {
            warnings.Add("Expression components have dynamic inputs; inspect after creation before wiring.");
            result["dynamic_inputs"] = true;
        }
        if (componentName.Equals("Python", StringComparison.OrdinalIgnoreCase) ||
            componentName.Contains("Script", StringComparison.OrdinalIgnoreCase))
        {
            warnings.Add("Script components have configurable inputs and outputs; default sockets may differ.");
        }
        if (componentName.Equals("Cluster", StringComparison.OrdinalIgnoreCase))
        {
            warnings.Add("Cluster inputs and outputs depend on the cluster definition.");
        }

        if (warnings.Count > 0)
        {
            result["warnings"] = warnings;
        }
    }
}
