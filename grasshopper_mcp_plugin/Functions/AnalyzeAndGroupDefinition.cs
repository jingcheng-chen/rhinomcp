using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Special;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    // ── Internal types ───────────────────────────────────────────────

    private class GraphNode
    {
        public Guid Id { get; set; }
        public string Name { get; set; } = "";
        public string NickName { get; set; } = "";
        public string Category { get; set; } = "";
        public int SubgraphId { get; set; } = -1;
        public int Depth { get; set; } = -1;
        public float PositionX { get; set; }
        public float PositionY { get; set; }
        public HashSet<Guid> Predecessors { get; } = new();
        public HashSet<Guid> Successors { get; } = new();
    }

    private class ComponentGroup
    {
        public string Name { get; set; } = "";
        public string Description { get; set; } = "";
        public Color Color { get; set; }
        public List<Guid> ComponentIds { get; } = new();
        public List<string> ComponentNames { get; } = new();
        public string DominantCategory { get; set; } = "";
        public int DepthMin { get; set; }
        public int DepthMax { get; set; }
    }

    // ── Color palettes ───────────────────────────────────────────────

    private static readonly Dictionary<string, Color[]> ColorPalettes = new(StringComparer.OrdinalIgnoreCase)
    {
        ["default"] = new[]
        {
            Color.FromArgb(80, 255, 119, 119),  // red
            Color.FromArgb(80, 119, 172, 255),  // blue
            Color.FromArgb(80, 119, 221, 119),  // green
            Color.FromArgb(80, 255, 204, 102),  // orange
            Color.FromArgb(80, 187, 136, 255),  // purple
            Color.FromArgb(80, 102, 221, 204),  // teal
            Color.FromArgb(80, 255, 153, 204),  // pink
            Color.FromArgb(80, 204, 204, 102),  // olive
            Color.FromArgb(80, 255, 170, 119),  // coral
            Color.FromArgb(80, 136, 187, 255),  // periwinkle
        },
        ["pastel"] = new[]
        {
            Color.FromArgb(80, 255, 179, 186),
            Color.FromArgb(80, 186, 225, 255),
            Color.FromArgb(80, 186, 255, 201),
            Color.FromArgb(80, 255, 255, 186),
            Color.FromArgb(80, 218, 186, 255),
            Color.FromArgb(80, 186, 255, 255),
            Color.FromArgb(80, 255, 218, 186),
            Color.FromArgb(80, 230, 230, 250),
            Color.FromArgb(80, 255, 228, 196),
            Color.FromArgb(80, 200, 255, 200),
        },
        ["vivid"] = new[]
        {
            Color.FromArgb(80, 255, 0, 0),
            Color.FromArgb(80, 0, 100, 255),
            Color.FromArgb(80, 0, 200, 0),
            Color.FromArgb(80, 255, 165, 0),
            Color.FromArgb(80, 148, 0, 211),
            Color.FromArgb(80, 0, 200, 200),
            Color.FromArgb(80, 255, 20, 147),
            Color.FromArgb(80, 184, 184, 0),
            Color.FromArgb(80, 255, 100, 50),
            Color.FromArgb(80, 0, 150, 255),
        }
    };

    // ── Category classification ──────────────────────────────────────

    private static readonly Dictionary<string, string> CategoryAliases = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Params"] = "Params",
        ["Primitive"] = "Params",
        ["Input"] = "Params",
        ["Maths"] = "Math",
        ["Math"] = "Math",
        ["Script"] = "Math",
        ["Sets"] = "Sets",
        ["List"] = "Sets",
        ["Tree"] = "Sets",
        ["Curve"] = "Curve",
        ["Surface"] = "Surface",
        ["Brep"] = "Surface",
        ["Mesh"] = "Mesh",
        ["Transform"] = "Transform",
        ["Vector"] = "Vector",
        ["Point"] = "Vector",
        ["Intersect"] = "Intersect",
        ["Display"] = "Display",
    };

    // ── Purpose heuristic ────────────────────────────────────────────

    private static string ClassifyPurpose(Dictionary<string, int> categoryCounts)
    {
        if (categoryCounts.Count == 0) return "unknown";

        var dominant = categoryCounts.OrderByDescending(kv => kv.Value).First().Key;
        var hasMultipleCurves = categoryCounts.GetValueOrDefault("Curve", 0) > 2;
        var hasMultipleSurfaces = categoryCounts.GetValueOrDefault("Surface", 0) > 2;
        var hasTransforms = categoryCounts.GetValueOrDefault("Transform", 0) > 0;
        var hasMesh = categoryCounts.GetValueOrDefault("Mesh", 0) > 0;

        if (hasMultipleSurfaces && hasTransforms) return "surface_modeling";
        if (hasMultipleCurves && hasTransforms) return "curve_modeling";
        if (hasMesh) return "mesh_processing";
        if (dominant == "Math") return "computational";
        if (dominant == "Sets") return "data_processing";
        if (dominant == "Params") return "parametric_input";
        if (dominant == "Transform") return "transformation";
        if (dominant == "Display") return "visualization";
        return "general";
    }

    // ── Main entry point ─────────────────────────────────────────────

    /// <summary>
    /// Analyze a Grasshopper definition's component graph, create colored groups,
    /// optionally reorganize layout, and generate a Mermaid workflow diagram.
    /// </summary>
    public JObject AnalyzeAndGroupDefinition(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;
        if (doc == null)
            throw new InvalidOperationException("No active Grasshopper document");

        // Parse parameters
        var strategy = parameters["strategy"]?.ToString() ?? "auto";
        var minGroupSize = parameters["min_group_size"]?.ToObject<int>() ?? 2;
        var includeDiagram = parameters["include_diagram"]?.ToObject<bool>() ?? true;
        var colorPalette = parameters["color_palette"]?.ToString() ?? "default";
        var removeExisting = parameters["remove_existing_groups"]?.ToObject<bool>() ?? false;
        var reorganizeLayout = parameters["reorganize_layout"]?.ToObject<bool>() ?? false;

        if (!ColorPalettes.ContainsKey(colorPalette))
            colorPalette = "default";

        // Phase 0: Optionally remove existing groups
        if (removeExisting)
        {
            var existingGroups = doc.Objects.OfType<GH_Group>().ToList();
            doc.RemoveObjects(existingGroups, false);
        }

        // Phase 1: Build graph
        var graph = BuildGraph(doc);
        if (graph.Count == 0)
        {
            return new JObject
            {
                ["summary"] = "Empty definition -- nothing to analyze",
                ["definition_purpose"] = "empty",
                ["groups_created"] = 0,
                ["component_count"] = 0,
                ["connection_count"] = 0,
                ["subgraph_count"] = 0,
                ["groups"] = new JArray(),
                ["message"] = "No components found on canvas"
            };
        }

        // Count connections
        int connectionCount = graph.Values.Sum(n => n.Successors.Count);

        // Phase 2: Identify disconnected subgraphs
        int subgraphCount = LabelSubgraphs(graph);

        // Phase 3: Compute topological depth
        ComputeDepths(graph);

        // Phase 4: Group components
        var groups = strategy switch
        {
            "by_depth" => GroupByDepth(graph, minGroupSize),
            "by_category" => GroupByCategory(graph, minGroupSize),
            _ => GroupByWorkflow(graph, minGroupSize)  // "auto" and "by_workflow"
        };

        // Phase 5: Assign colors & names
        _currentGraph = graph;
        var palette = ColorPalettes[colorPalette];
        AssignColorsAndNames(groups, palette);
        _currentGraph = null;

        // Phase 6: Reorganize layout if requested
        bool layoutChanged = false;
        if (reorganizeLayout)
        {
            layoutChanged = RepositionComponents(doc, graph, groups);
        }

        // Phase 7: Create GH_Group objects
        int groupsCreated = CreateGHGroups(doc, groups);

        // Phase 8: Generate Mermaid diagram
        string? mermaid = includeDiagram ? GenerateMermaid(graph, groups) : null;

        // Phase 9: Build response
        var categoryCounts = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        foreach (var node in graph.Values)
        {
            var cat = NormalizeCategory(node.Category);
            categoryCounts[cat] = categoryCounts.GetValueOrDefault(cat, 0) + 1;
        }

        var purpose = ClassifyPurpose(categoryCounts);

        var groupsArray = new JArray();
        foreach (var g in groups)
        {
            var gObj = new JObject
            {
                ["name"] = g.Name,
                ["description"] = g.Description,
                ["color"] = ColorToHex(g.Color),
                ["color_alpha"] = g.Color.A,
                ["component_count"] = g.ComponentIds.Count,
                ["component_ids"] = new JArray(g.ComponentIds.Select(id => id.ToString())),
                ["component_names"] = new JArray(g.ComponentNames),
                ["depth_range"] = $"{g.DepthMin}-{g.DepthMax}",
                ["dominant_category"] = g.DominantCategory
            };
            groupsArray.Add(gObj);
        }

        var summary = $"Definition with {graph.Count} components, {connectionCount} connections, " +
                       $"{subgraphCount} subgraph(s). Created {groupsCreated} group(s) using '{strategy}' strategy.";
        if (layoutChanged)
            summary += " Layout reorganized.";

        var result = new JObject
        {
            ["summary"] = summary,
            ["definition_purpose"] = purpose,
            ["groups_created"] = groupsCreated,
            ["component_count"] = graph.Count,
            ["connection_count"] = connectionCount,
            ["subgraph_count"] = subgraphCount,
            ["layout_reorganized"] = layoutChanged,
            ["groups"] = groupsArray,
            ["message"] = $"Analyzed {graph.Count} components, created {groupsCreated} groups"
        };

        if (mermaid != null)
            result["workflow_diagram"] = mermaid;

        return result;
    }

    // ── Phase 1: Build Graph ─────────────────────────────────────────

    private Dictionary<Guid, GraphNode> BuildGraph(GH_Document doc)
    {
        var graph = new Dictionary<Guid, GraphNode>();

        // Add components
        foreach (var comp in doc.Objects.OfType<IGH_Component>())
        {
            var node = new GraphNode
            {
                Id = comp.InstanceGuid,
                Name = comp.Name,
                NickName = comp.NickName,
                Category = comp.Category,
                PositionX = comp.Attributes.Pivot.X,
                PositionY = comp.Attributes.Pivot.Y
            };
            graph[comp.InstanceGuid] = node;
        }

        // Add standalone params (not part of a component)
        foreach (var param in doc.Objects.OfType<IGH_Param>())
        {
            if (param is IGH_Component) continue;
            if (param.Attributes.GetTopLevel.DocObject is IGH_Component) continue;
            if (param is GH_Group) continue;

            if (!graph.ContainsKey(param.InstanceGuid))
            {
                var node = new GraphNode
                {
                    Id = param.InstanceGuid,
                    Name = param.Name,
                    NickName = param.NickName,
                    Category = "Params",
                    PositionX = param.Attributes.Pivot.X,
                    PositionY = param.Attributes.Pivot.Y
                };
                graph[param.InstanceGuid] = node;
            }
        }

        // Build edges from component inputs
        foreach (var comp in doc.Objects.OfType<IGH_Component>())
        {
            foreach (var input in comp.Params.Input)
            {
                foreach (var source in input.Sources)
                {
                    var sourceId = source.Attributes.GetTopLevel.DocObject.InstanceGuid;
                    if (graph.ContainsKey(sourceId) && graph.ContainsKey(comp.InstanceGuid))
                    {
                        graph[sourceId].Successors.Add(comp.InstanceGuid);
                        graph[comp.InstanceGuid].Predecessors.Add(sourceId);
                    }
                }
            }
        }

        // Edges for standalone params
        foreach (var param in doc.Objects.OfType<IGH_Param>())
        {
            if (param is IGH_Component) continue;
            if (param.Attributes.GetTopLevel.DocObject is IGH_Component) continue;
            if (param is GH_Group) continue;
            if (!graph.ContainsKey(param.InstanceGuid)) continue;

            foreach (var source in param.Sources)
            {
                var sourceId = source.Attributes.GetTopLevel.DocObject.InstanceGuid;
                if (graph.ContainsKey(sourceId))
                {
                    graph[sourceId].Successors.Add(param.InstanceGuid);
                    graph[param.InstanceGuid].Predecessors.Add(sourceId);
                }
            }
        }

        return graph;
    }

    // ── Phase 2: Subgraph labeling ───────────────────────────────────

    private int LabelSubgraphs(Dictionary<Guid, GraphNode> graph)
    {
        int subgraphId = 0;
        var visited = new HashSet<Guid>();

        foreach (var nodeId in graph.Keys)
        {
            if (visited.Contains(nodeId)) continue;

            var queue = new Queue<Guid>();
            queue.Enqueue(nodeId);
            visited.Add(nodeId);

            while (queue.Count > 0)
            {
                var current = queue.Dequeue();
                graph[current].SubgraphId = subgraphId;

                foreach (var neighbor in graph[current].Predecessors.Concat(graph[current].Successors))
                {
                    if (!visited.Contains(neighbor) && graph.ContainsKey(neighbor))
                    {
                        visited.Add(neighbor);
                        queue.Enqueue(neighbor);
                    }
                }
            }

            subgraphId++;
        }

        return subgraphId;
    }

    // ── Phase 3: Compute depth (longest path from sources) ───────────

    private void ComputeDepths(Dictionary<Guid, GraphNode> graph)
    {
        var sources = graph.Values
            .Where(n => n.Predecessors.Count == 0 || !n.Predecessors.Any(p => graph.ContainsKey(p)))
            .ToList();

        foreach (var node in graph.Values)
            node.Depth = 0;

        var queue = new Queue<Guid>();
        foreach (var src in sources)
        {
            src.Depth = 0;
            queue.Enqueue(src.Id);
        }

        while (queue.Count > 0)
        {
            var current = queue.Dequeue();
            var currentNode = graph[current];

            foreach (var succId in currentNode.Successors)
            {
                if (!graph.ContainsKey(succId)) continue;
                var succ = graph[succId];
                var newDepth = currentNode.Depth + 1;
                if (newDepth > succ.Depth)
                {
                    succ.Depth = newDepth;
                    queue.Enqueue(succId);
                }
            }
        }
    }

    // ── Phase 4a: Workflow grouping (default "auto") ─────────────────
    //
    // Finds natural bottlenecks in the dataflow graph by counting edges
    // that cross each depth boundary. Cuts at boundaries with the fewest
    // crossing edges, producing functional workflow sections.
    // Then refines assignments by checking each node's connectivity.

    private List<ComponentGroup> GroupByWorkflow(Dictionary<Guid, GraphNode> graph, int minGroupSize)
    {
        var maxDepth = graph.Values.Max(n => n.Depth);

        // Shallow graphs: one group per subgraph
        if (maxDepth <= 2)
            return GroupBySubgraph(graph);

        // Step 1: Count edges crossing each depth boundary.
        // crossingEdges[d] = number of edges from a node at depth <= d to a node at depth > d
        var crossingEdges = new double[maxDepth]; // index d represents the boundary between depth d and d+1
        foreach (var node in graph.Values)
        {
            foreach (var succId in node.Successors)
            {
                if (!graph.ContainsKey(succId)) continue;
                var succ = graph[succId];
                var lo = Math.Min(node.Depth, succ.Depth);
                var hi = Math.Max(node.Depth, succ.Depth);
                for (int d = lo; d < hi && d < maxDepth; d++)
                    crossingEdges[d]++;
            }
        }

        // Step 2: Find candidate cut points (local minima and zero-crossings)
        var candidates = new List<(int depth, double score)>();

        for (int d = 0; d < maxDepth; d++)
        {
            if (crossingEdges[d] == 0)
            {
                candidates.Add((d, double.MaxValue)); // definite cut
                continue;
            }

            // Local minimum: value <= both neighbors
            double left = d > 0 ? crossingEdges[d - 1] : double.MaxValue;
            double right = d < maxDepth - 1 ? crossingEdges[d + 1] : double.MaxValue;

            if (crossingEdges[d] <= left && crossingEdges[d] <= right)
            {
                // Score = how deep the valley is relative to its neighbors
                double neighborAvg = (left == double.MaxValue ? right : right == double.MaxValue ? left : (left + right) / 2.0);
                double score = crossingEdges[d] > 0 ? neighborAvg / crossingEdges[d] : double.MaxValue;
                if (score > 1.2) // at least 20% deeper than neighbors
                    candidates.Add((d, score));
            }
        }

        // Step 3: Select cut points. Target 3-6 groups.
        int targetCuts = Math.Clamp((maxDepth + 1) / 3, 2, 6);

        var selectedCuts = candidates
            .OrderByDescending(c => c.score)
            .Take(targetCuts)
            .Select(c => c.depth)
            .OrderBy(d => d)
            .ToList();

        // Remove cuts too close together (within 1 depth of each other)
        var filteredCuts = new List<int>();
        foreach (var cp in selectedCuts)
        {
            if (filteredCuts.Count == 0 || cp - filteredCuts.Last() > 1)
                filteredCuts.Add(cp);
        }

        // If no natural cuts found, split at even intervals
        if (filteredCuts.Count == 0 && maxDepth > 3)
        {
            int numGroups = Math.Min(4, (maxDepth + 2) / 3);
            int interval = (maxDepth + 1) / numGroups;
            for (int i = 1; i < numGroups; i++)
                filteredCuts.Add(i * interval - 1);
        }

        // Step 4: Build groups from depth ranges
        var depthRanges = new List<(int start, int end)>();
        int rangeStart = 0;
        foreach (var cut in filteredCuts)
        {
            if (cut >= rangeStart)
            {
                depthRanges.Add((rangeStart, cut));
                rangeStart = cut + 1;
            }
        }
        if (rangeStart <= maxDepth)
            depthRanges.Add((rangeStart, maxDepth));

        if (depthRanges.Count == 0)
            depthRanges.Add((0, maxDepth));

        // Assign each node to a group based on depth range
        var nodeGroupIndex = new Dictionary<Guid, int>();
        var groups = new List<ComponentGroup>();

        for (int gi = 0; gi < depthRanges.Count; gi++)
        {
            var (start, end) = depthRanges[gi];
            var nodesInRange = graph.Values.Where(n => n.Depth >= start && n.Depth <= end).ToList();
            if (nodesInRange.Count == 0) continue;

            var g = new ComponentGroup();
            foreach (var n in nodesInRange)
            {
                g.ComponentIds.Add(n.Id);
                g.ComponentNames.Add(string.IsNullOrEmpty(n.NickName) ? n.Name : n.NickName);
                nodeGroupIndex[n.Id] = groups.Count;
            }
            g.DominantCategory = GetDominantCategory(nodesInRange);
            g.DepthMin = start;
            g.DepthMax = end;
            groups.Add(g);
        }

        // Step 5: Connectivity-based reassignment.
        // If a node has > 2x more connections to a neighboring group than its own,
        // move it to that neighboring group.
        bool changed = true;
        int iterations = 0;
        while (changed && iterations < 3)
        {
            changed = false;
            iterations++;

            foreach (var node in graph.Values)
            {
                if (!nodeGroupIndex.ContainsKey(node.Id)) continue;
                int currentGi = nodeGroupIndex[node.Id];

                // Count connections to each group
                var connectionsByGroup = new Dictionary<int, int>();
                foreach (var neighborId in node.Predecessors.Concat(node.Successors))
                {
                    if (nodeGroupIndex.TryGetValue(neighborId, out var ngi))
                        connectionsByGroup[ngi] = connectionsByGroup.GetValueOrDefault(ngi, 0) + 1;
                }

                int internalConns = connectionsByGroup.GetValueOrDefault(currentGi, 0);

                // Check neighboring groups (adjacent index only)
                foreach (var (gi, conns) in connectionsByGroup)
                {
                    if (gi == currentGi) continue;
                    if (Math.Abs(gi - currentGi) > 1) continue; // only adjacent groups

                    if (conns > internalConns * 2 && conns >= 2)
                    {
                        // Move node from currentGi to gi
                        groups[currentGi].ComponentIds.Remove(node.Id);
                        var name = string.IsNullOrEmpty(node.NickName) ? node.Name : node.NickName;
                        groups[currentGi].ComponentNames.Remove(name);

                        groups[gi].ComponentIds.Add(node.Id);
                        groups[gi].ComponentNames.Add(name);
                        nodeGroupIndex[node.Id] = gi;
                        changed = true;
                        break;
                    }
                }
            }
        }

        // Remove empty groups and recalculate metadata
        groups.RemoveAll(g => g.ComponentIds.Count == 0);
        foreach (var g in groups)
        {
            var nodes = g.ComponentIds
                .Where(id => graph.ContainsKey(id))
                .Select(id => graph[id])
                .ToList();
            if (nodes.Count > 0)
            {
                g.DominantCategory = GetDominantCategory(nodes);
                g.DepthMin = nodes.Min(n => n.Depth);
                g.DepthMax = nodes.Max(n => n.Depth);
            }
        }

        MergeSmallGroups(groups, graph, minGroupSize);
        return groups;
    }

    // ── Subgraph grouping (fallback for shallow graphs) ──────────────

    private List<ComponentGroup> GroupBySubgraph(Dictionary<Guid, GraphNode> graph)
    {
        var groups = new List<ComponentGroup>();
        var bySubgraph = graph.Values.GroupBy(n => n.SubgraphId);

        foreach (var sg in bySubgraph)
        {
            var g = new ComponentGroup();
            foreach (var n in sg)
            {
                g.ComponentIds.Add(n.Id);
                g.ComponentNames.Add(string.IsNullOrEmpty(n.NickName) ? n.Name : n.NickName);
            }
            g.DominantCategory = GetDominantCategory(sg.ToList());
            g.DepthMin = sg.Min(n => n.Depth);
            g.DepthMax = sg.Max(n => n.Depth);
            groups.Add(g);
        }

        return groups;
    }

    // ── Phase 4b: Depth grouping (one group per depth level) ─────────

    private List<ComponentGroup> GroupByDepth(Dictionary<Guid, GraphNode> graph, int minGroupSize)
    {
        var maxDepth = graph.Values.Max(n => n.Depth);
        var groups = new List<ComponentGroup>();

        for (int d = 0; d <= maxDepth; d++)
        {
            var nodesAtDepth = graph.Values.Where(n => n.Depth == d).ToList();
            if (nodesAtDepth.Count == 0) continue;

            var g = new ComponentGroup();
            foreach (var n in nodesAtDepth)
            {
                g.ComponentIds.Add(n.Id);
                g.ComponentNames.Add(string.IsNullOrEmpty(n.NickName) ? n.Name : n.NickName);
            }
            g.DominantCategory = GetDominantCategory(nodesAtDepth);
            g.DepthMin = d;
            g.DepthMax = d;
            groups.Add(g);
        }

        MergeSmallGroups(groups, graph, minGroupSize);
        return groups;
    }

    // ── Phase 4c: Category grouping ──────────────────────────────────

    private List<ComponentGroup> GroupByCategory(Dictionary<Guid, GraphNode> graph, int minGroupSize)
    {
        var byCategory = graph.Values.GroupBy(n => NormalizeCategory(n.Category));
        var groups = new List<ComponentGroup>();

        foreach (var catGroup in byCategory)
        {
            var g = new ComponentGroup();
            foreach (var n in catGroup)
            {
                g.ComponentIds.Add(n.Id);
                g.ComponentNames.Add(string.IsNullOrEmpty(n.NickName) ? n.Name : n.NickName);
            }
            g.DominantCategory = catGroup.Key;
            g.DepthMin = catGroup.Min(n => n.Depth);
            g.DepthMax = catGroup.Max(n => n.Depth);
            groups.Add(g);
        }

        MergeSmallGroups(groups, graph, minGroupSize);
        return groups;
    }

    // ── Merge small groups ───────────────────────────────────────────

    private void MergeSmallGroups(List<ComponentGroup> groups, Dictionary<Guid, GraphNode> graph, int minGroupSize)
    {
        bool merged = true;
        while (merged)
        {
            merged = false;
            for (int i = groups.Count - 1; i >= 0; i--)
            {
                if (groups[i].ComponentIds.Count >= minGroupSize || groups.Count <= 1)
                    continue;

                int bestIdx = -1;
                int bestScore = -1;

                for (int j = 0; j < groups.Count; j++)
                {
                    if (j == i) continue;
                    int score = 0;

                    // Count actual connections between these two groups
                    foreach (var id in groups[i].ComponentIds)
                    {
                        if (!graph.ContainsKey(id)) continue;
                        var node = graph[id];
                        foreach (var neighborId in node.Predecessors.Concat(node.Successors))
                        {
                            if (groups[j].ComponentIds.Contains(neighborId))
                                score += 10;
                        }
                    }

                    // Same category bonus
                    if (groups[j].DominantCategory == groups[i].DominantCategory)
                        score += 5;

                    // Adjacent depth bonus
                    if (Math.Abs(groups[j].DepthMin - groups[i].DepthMax) <= 1 ||
                        Math.Abs(groups[i].DepthMin - groups[j].DepthMax) <= 1)
                        score += 3;

                    if (score > bestScore)
                    {
                        bestScore = score;
                        bestIdx = j;
                    }
                }

                if (bestIdx >= 0)
                {
                    groups[bestIdx].ComponentIds.AddRange(groups[i].ComponentIds);
                    groups[bestIdx].ComponentNames.AddRange(groups[i].ComponentNames);
                    groups[bestIdx].DepthMin = Math.Min(groups[bestIdx].DepthMin, groups[i].DepthMin);
                    groups[bestIdx].DepthMax = Math.Max(groups[bestIdx].DepthMax, groups[i].DepthMax);

                    // Recalculate dominant category
                    var allNodes = groups[bestIdx].ComponentIds
                        .Where(id => graph.ContainsKey(id))
                        .Select(id => graph[id])
                        .ToList();
                    groups[bestIdx].DominantCategory = GetDominantCategory(allNodes);

                    groups.RemoveAt(i);
                    merged = true;
                }
            }
        }
    }

    // ── Phase 5: Assign colors and names ─────────────────────────────

    private void AssignColorsAndNames(List<ComponentGroup> groups, Color[] palette)
    {
        // Sort groups by average depth so names flow left-to-right
        var sortedIndices = groups
            .Select((g, i) => (group: g, index: i, avgDepth: (g.DepthMin + g.DepthMax) / 2.0))
            .OrderBy(x => x.avgDepth)
            .ToList();

        // Build workflow stage labels
        var stageLabels = new string[] { "Input", "Processing", "Intermediate", "Output" };
        var nameCount = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);

        for (int rank = 0; rank < sortedIndices.Count; rank++)
        {
            var g = sortedIndices[rank].group;
            g.Color = palette[rank % palette.Length];

            // Build a descriptive name from the group's content
            string baseName;

            // First/last groups get special names if they match
            bool isFirst = rank == 0;
            bool isLast = rank == sortedIndices.Count - 1;

            if (isFirst && (g.DominantCategory == "Params" || g.DominantCategory == "Mesh" || g.DominantCategory == "Surface"))
                baseName = "Setup & Inputs";
            else if (isLast && (g.DominantCategory == "Display" || g.DominantCategory == "Sets"))
                baseName = "Output & Visualization";
            else
            {
                // Use dominant category + secondary categories for distinctiveness
                var catCounts = g.ComponentIds
                    .Where(id => _currentGraph != null && _currentGraph.ContainsKey(id))
                    .Select(id => NormalizeCategory(_currentGraph![id].Category))
                    .GroupBy(c => c)
                    .OrderByDescending(c => c.Count())
                    .ToList();

                baseName = catCounts.Count > 0 ? catCounts[0].Key : "Processing";

                // If second category is significant, include it
                if (catCounts.Count > 1 && catCounts[1].Count() >= catCounts[0].Count() / 2)
                    baseName = $"{catCounts[0].Key} & {catCounts[1].Key}";
            }

            // Deduplicate names
            if (nameCount.ContainsKey(baseName))
            {
                nameCount[baseName]++;
                g.Name = $"{baseName} ({rank + 1})";
            }
            else
            {
                nameCount[baseName] = 1;
                g.Name = baseName;
            }

            g.Description = $"{g.DominantCategory} (depth {g.DepthMin}-{g.DepthMax}, {g.ComponentIds.Count} components)";
        }

        // Fix first occurrence of duplicated names
        foreach (var kvp in nameCount.Where(kv => kv.Value > 1))
        {
            var first = groups.FirstOrDefault(g => g.Name == kvp.Key);
            if (first != null)
            {
                var rank = sortedIndices.FindIndex(x => x.group == first);
                first.Name = $"{kvp.Key} ({rank + 1})";
            }
        }
    }

    // Temporary reference used during naming
    private Dictionary<Guid, GraphNode>? _currentGraph;

    // ── Phase 6: Reorganize layout ───────────────────────────────────

    private bool RepositionComponents(GH_Document doc, Dictionary<Guid, GraphNode> graph, List<ComponentGroup> groups)
    {
        const float groupSpacingX = 300f;   // horizontal gap between groups
        const float columnSpacingX = 180f;  // horizontal gap between depth columns
        const float rowSpacingY = 120f;     // vertical gap between components

        // Sort groups by average depth
        var sortedGroups = groups
            .OrderBy(g => (g.DepthMin + g.DepthMax) / 2.0)
            .ThenBy(g => g.DepthMin)
            .ToList();

        float currentX = 0;

        foreach (var group in sortedGroups)
        {
            // Get nodes in this group, organized by depth
            var nodesByDepth = group.ComponentIds
                .Where(id => graph.ContainsKey(id))
                .Select(id => graph[id])
                .GroupBy(n => n.Depth)
                .OrderBy(g => g.Key)
                .ToList();

            float groupStartX = currentX;

            foreach (var depthGroup in nodesByDepth)
            {
                var nodesAtDepth = depthGroup
                    .OrderBy(n => n.PositionY) // preserve relative vertical order
                    .ToList();

                // Center vertically
                float totalHeight = (nodesAtDepth.Count - 1) * rowSpacingY;
                float startY = -totalHeight / 2f;

                for (int i = 0; i < nodesAtDepth.Count; i++)
                {
                    var node = nodesAtDepth[i];
                    float newX = currentX;
                    float newY = startY + i * rowSpacingY;

                    var obj = doc.FindObject(node.Id, true);
                    if (obj != null)
                    {
                        obj.Attributes.Pivot = new PointF(newX, newY);
                    }
                }

                currentX += columnSpacingX;
            }

            // Ensure minimum group width
            currentX = Math.Max(currentX, groupStartX + columnSpacingX);
            currentX += groupSpacingX;
        }

        // Trigger layout refresh
        doc.NewSolution(false);

        return true;
    }

    // ── Phase 7: Create GH_Group objects ─────────────────────────────

    private int CreateGHGroups(GH_Document doc, List<ComponentGroup> groups)
    {
        int created = 0;
        foreach (var g in groups)
        {
            try
            {
                var ghGroup = new GH_Group();
                ghGroup.CreateAttributes();
                ghGroup.NickName = g.Name;
                ghGroup.Colour = g.Color;

                foreach (var id in g.ComponentIds)
                {
                    ghGroup.AddObject(id);
                }

                doc.AddObject(ghGroup, false);
                created++;
            }
            catch
            {
                // Individual group creation errors should not block others
            }
        }

        return created;
    }

    // ── Phase 8: Generate Mermaid diagram ────────────────────────────

    private string GenerateMermaid(Dictionary<Guid, GraphNode> graph, List<ComponentGroup> groups)
    {
        var sb = new StringBuilder();
        sb.AppendLine("graph LR");

        // Emit subgraph blocks (sorted by depth for readable left-to-right flow)
        var sortedGroups = groups
            .OrderBy(g => (g.DepthMin + g.DepthMax) / 2.0)
            .ToList();

        for (int i = 0; i < sortedGroups.Count; i++)
        {
            var g = sortedGroups[i];
            var safeName = SanitizeMermaid(g.Name);
            sb.AppendLine($"    subgraph {safeName}");

            foreach (var id in g.ComponentIds)
            {
                if (graph.TryGetValue(id, out var node))
                {
                    var shortId = ShortId(id);
                    var label = SanitizeMermaid(string.IsNullOrEmpty(node.NickName) ? node.Name : node.NickName);
                    sb.AppendLine($"        {shortId}[\"{label}\"]");
                }
            }

            sb.AppendLine("    end");
        }

        // Emit edges
        foreach (var node in graph.Values)
        {
            foreach (var succId in node.Successors)
            {
                if (!graph.ContainsKey(succId)) continue;
                sb.AppendLine($"    {ShortId(node.Id)} --> {ShortId(succId)}");
            }
        }

        return sb.ToString().TrimEnd();
    }

    // ── Helpers ──────────────────────────────────────────────────────

    private static string NormalizeCategory(string category)
    {
        if (string.IsNullOrEmpty(category)) return "Other";
        if (CategoryAliases.TryGetValue(category, out var normalized))
            return normalized;
        return category;
    }

    private static string GetDominantCategory(List<GraphNode> nodes)
    {
        if (nodes.Count == 0) return "Other";
        return nodes
            .GroupBy(n => NormalizeCategory(n.Category))
            .OrderByDescending(g => g.Count())
            .First()
            .Key;
    }

    private static string ShortId(Guid id)
    {
        return "n" + id.ToString("N").Substring(0, 8);
    }

    private static string SanitizeMermaid(string text)
    {
        return text
            .Replace("\"", "'")
            .Replace("[", "(")
            .Replace("]", ")")
            .Replace("{", "(")
            .Replace("}", ")")
            .Replace("<", "")
            .Replace(">", "")
            .Replace("|", "/")
            .Replace("#", "")
            .Replace(";", ",");
    }

    private static string ColorToHex(Color c)
    {
        return $"#{c.R:X2}{c.G:X2}{c.B:X2}";
    }
}
