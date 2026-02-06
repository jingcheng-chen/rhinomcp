using System;
using System.Collections.Generic;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Search for components in the Grasshopper library.
    /// Returns component names, categories, and GUIDs that can be used with add_component or create_definition.
    /// </summary>
    public JObject SearchComponents(JObject parameters)
    {
        var query = parameters["query"]?.ToString();
        var category = parameters["category"]?.ToString();
        var limit = parameters["limit"]?.ToObject<int>() ?? 50;

        var results = new JArray();
        var proxies = Instances.ComponentServer.ObjectProxies;

        IEnumerable<IGH_ObjectProxy> filtered = proxies;

        // Filter by category if specified
        if (!string.IsNullOrEmpty(category))
        {
            filtered = filtered.Where(p =>
                p.Desc.Category?.Contains(category, StringComparison.OrdinalIgnoreCase) == true);
        }

        // Filter by query if specified
        if (!string.IsNullOrEmpty(query))
        {
            filtered = filtered.Where(p =>
                p.Desc.Name?.Contains(query, StringComparison.OrdinalIgnoreCase) == true ||
                p.Desc.NickName?.Contains(query, StringComparison.OrdinalIgnoreCase) == true ||
                p.Desc.Description?.Contains(query, StringComparison.OrdinalIgnoreCase) == true);
        }

        // Order by relevance (exact name match first, then by name)
        if (!string.IsNullOrEmpty(query))
        {
            filtered = filtered.OrderByDescending(p =>
                p.Desc.Name?.Equals(query, StringComparison.OrdinalIgnoreCase) == true)
                .ThenBy(p => p.Desc.Name);
        }
        else
        {
            filtered = filtered.OrderBy(p => p.Desc.Category).ThenBy(p => p.Desc.Name);
        }

        foreach (var proxy in filtered.Take(limit))
        {
            results.Add(new JObject
            {
                ["name"] = proxy.Desc.Name,
                ["nickname"] = proxy.Desc.NickName,
                ["category"] = proxy.Desc.Category,
                ["subcategory"] = proxy.Desc.SubCategory,
                ["description"] = proxy.Desc.Description,
                ["guid"] = proxy.Guid.ToString()
            });
        }

        return new JObject
        {
            ["count"] = results.Count,
            ["query"] = query,
            ["category"] = category,
            ["components"] = results,
            ["message"] = $"Found {results.Count} component(s)"
        };
    }

    /// <summary>
    /// Get all available components from the Grasshopper library.
    /// Returns everything installed, including third-party plugins.
    /// </summary>
    public JObject GetAvailableComponents(JObject parameters)
    {
        var category = parameters["category"]?.ToString();
        var limit = parameters["limit"]?.ToObject<int>() ?? 500;
        var includeDescription = parameters["include_description"]?.ToObject<bool>() ?? false;

        var results = new JArray();
        var proxies = Instances.ComponentServer.ObjectProxies;
        var categories = new HashSet<string>();

        IEnumerable<IGH_ObjectProxy> filtered = proxies;

        // Filter by category if specified
        if (!string.IsNullOrEmpty(category))
        {
            filtered = filtered.Where(p =>
                p.Desc.Category?.Contains(category, StringComparison.OrdinalIgnoreCase) == true);
        }

        // Order by category then name
        filtered = filtered.OrderBy(p => p.Desc.Category).ThenBy(p => p.Desc.Name);

        foreach (var proxy in filtered.Take(limit))
        {
            if (!string.IsNullOrEmpty(proxy.Desc.Category))
            {
                categories.Add(proxy.Desc.Category);
            }

            var comp = new JObject
            {
                ["name"] = proxy.Desc.Name,
                ["nickname"] = proxy.Desc.NickName,
                ["category"] = proxy.Desc.Category,
                ["subcategory"] = proxy.Desc.SubCategory,
                ["guid"] = proxy.Guid.ToString()
            };

            if (includeDescription)
            {
                comp["description"] = proxy.Desc.Description;
            }

            results.Add(comp);
        }

        return new JObject
        {
            ["count"] = results.Count,
            ["total_available"] = proxies.Count(),
            ["category_filter"] = category,
            ["categories"] = new JArray(categories.OrderBy(c => c)),
            ["components"] = results,
            ["message"] = $"Found {results.Count} components" + (category != null ? $" in category '{category}'" : "")
        };
    }

    /// <summary>
    /// Batch search for multiple components at once.
    /// More efficient than multiple individual searches.
    /// </summary>
    public JObject BatchSearchComponents(JObject parameters)
    {
        var queries = parameters["queries"]?.ToObject<List<string>>() ?? new List<string>();

        if (queries.Count == 0)
        {
            return new JObject
            {
                ["results"] = new JObject(),
                ["found_count"] = 0,
                ["not_found"] = new JArray(),
                ["message"] = "No queries provided"
            };
        }

        var results = new JObject();
        var notFound = new JArray();
        var foundCount = 0;

        var proxies = Instances.ComponentServer.ObjectProxies.ToList();

        foreach (var query in queries)
        {
            if (string.IsNullOrWhiteSpace(query)) continue;

            // Try exact match first
            var match = proxies.FirstOrDefault(p =>
                p.Desc.Name.Equals(query, StringComparison.OrdinalIgnoreCase));

            // Try nickname match
            if (match == null)
            {
                match = proxies.FirstOrDefault(p =>
                    p.Desc.NickName?.Equals(query, StringComparison.OrdinalIgnoreCase) == true);
            }

            // Try contains match
            if (match == null)
            {
                match = proxies.FirstOrDefault(p =>
                    p.Desc.Name.Contains(query, StringComparison.OrdinalIgnoreCase));
            }

            if (match != null)
            {
                results[query] = new JObject
                {
                    ["name"] = match.Desc.Name,
                    ["nickname"] = match.Desc.NickName,
                    ["category"] = match.Desc.Category,
                    ["subcategory"] = match.Desc.SubCategory,
                    ["guid"] = match.Guid.ToString()
                };
                foundCount++;
            }
            else
            {
                results[query] = null;
                notFound.Add(query);
            }
        }

        return new JObject
        {
            ["results"] = results,
            ["found_count"] = foundCount,
            ["total_queries"] = queries.Count,
            ["not_found"] = notFound,
            ["message"] = notFound.Count == 0
                ? $"Found all {foundCount} components"
                : $"Found {foundCount}/{queries.Count} components. Not found: {string.Join(", ", notFound)}"
        };
    }

    /// <summary>
    /// List all component categories in Grasshopper.
    /// </summary>
    public JObject ListComponentCategories(JObject parameters)
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
            })
            .ToList();

        return new JObject
        {
            ["category_count"] = categories.Count,
            ["categories"] = new JArray(categories)
        };
    }
}
