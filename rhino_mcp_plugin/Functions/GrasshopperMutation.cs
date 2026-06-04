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
    private sealed class GhConnectionRollback
    {
        public IGH_Param Input { get; init; }
        public IGH_Param Output { get; init; }
    }

    private sealed class GhDisconnectRollback
    {
        public IGH_Param Input { get; init; }
        public List<IGH_Param> Sources { get; init; } = new();
    }

    [McpCommand("gh_mutate_graph")]
    public JObject GhMutateGraph(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument(createIfMissing: true);
        string graphId = CreateGraphId(OptionalString(parameters, "graph_id"));
        bool recompute = OptionalBool(parameters, "recompute", true);
        bool rollbackOnError = OptionalBool(parameters, "rollback_on_error", true);

        var operations = parameters["operations"] as JArray
            ?? throw new ArgumentException("operations is required.");
        if (operations.Count == 0)
        {
            throw new ArgumentException("operations must contain at least one operation.");
        }

        var aliases = new Dictionary<string, IGH_DocumentObject>(StringComparer.OrdinalIgnoreCase);
        var created = new List<IGH_DocumentObject>();
        var touched = new List<IGH_DocumentObject>();
        var snapshots = new Dictionary<Guid, GhObjectSnapshot>();
        var addedConnections = new List<GhConnectionRollback>();
        var removedConnections = new List<GhDisconnectRollback>();
        var pendingDeletes = new List<IGH_DocumentObject>();
        var opResults = new JArray();
        bool forceRecompute = false;
        JObject layoutResult = null;
        JObject previewResult = null;
        JObject verification = null;
        JArray groups = null;

        void Touch(IGH_DocumentObject obj)
        {
            if (obj != null && !touched.Contains(obj))
            {
                touched.Add(obj);
            }
        }

        void Snapshot(IGH_DocumentObject obj)
        {
            if (obj != null && !snapshots.ContainsKey(obj.InstanceGuid))
            {
                snapshots[obj.InstanceGuid] = CaptureObjectSnapshot(obj);
            }
        }

        try
        {
            foreach (var operationToken in operations)
            {
                if (operationToken is not JObject operation)
                {
                    throw new ArgumentException("Each mutation operation must be an object.");
                }

                string op = OptionalString(operation, "op");
                if (string.IsNullOrWhiteSpace(op))
                {
                    throw new ArgumentException("Each mutation operation requires op.");
                }

                switch (op.ToLowerInvariant())
                {
                    case "create":
                    {
                        string alias = OptionalString(operation, "alias");
                        string componentName = OptionalString(operation, "component_name");
                        string componentGuid = OptionalString(operation, "component_guid");
                        if (string.IsNullOrWhiteSpace(alias))
                        {
                            throw new ArgumentException("create operation requires alias.");
                        }
                        if (string.IsNullOrWhiteSpace(componentName))
                        {
                            throw new ArgumentException("create operation requires component_name.");
                        }
                        if (aliases.ContainsKey(alias))
                        {
                            throw new InvalidOperationException($"Duplicate mutation alias '{alias}'.");
                        }

                        var obj = CreateGrasshopperObject(componentName, componentGuid, operation);
                        if (obj.Attributes == null)
                        {
                            obj.CreateAttributes();
                        }
                        obj.Attributes.Pivot = operation["position"] != null
                            ? ReadPosition(operation, "position", 0, 0)
                            : FindNextGrasshopperSlot(doc);

                        string nickname = OptionalString(operation, "nickname");
                        if (!string.IsNullOrWhiteSpace(nickname))
                        {
                            obj.NickName = nickname;
                        }
                        if (operation["preview"] != null && obj is IGH_PreviewObject previewObj)
                        {
                            previewObj.Hidden = !operation["preview"]!.ToObject<bool>();
                        }
                        if (operation["enabled"] != null && obj is IGH_ActiveObject activeObj)
                        {
                            activeObj.Locked = !operation["enabled"]!.ToObject<bool>();
                        }

                        doc.AddObject(obj, false);
                        string objectGraphId = OptionalString(operation, "graph_id") ?? graphId;
                        ApplyGraphMetadata(obj, alias, objectGraphId, OptionalString(operation, "role"));
                        aliases[alias] = obj;
                        created.Add(obj);
                        Touch(obj);
                        opResults.Add(new JObject
                        {
                            ["op"] = "create",
                            ["alias"] = alias,
                            ["instance_id"] = obj.InstanceGuid.ToString(),
                            ["name"] = obj.Name,
                            ["nickname"] = obj.NickName
                        });
                        break;
                    }

                    case "connect":
                    {
                        var sourceObj = ResolveGraphObject(doc, aliases, OptionalString(operation, "source"), "connection source");
                        var targetObj = ResolveGraphObject(doc, aliases, OptionalString(operation, "target"), "connection target");
                        var outputParam = FindOutputParam(
                            sourceObj,
                            GetParamIndex(operation, isOutput: true, "source_"),
                            GetParamName(operation, isOutput: true, "source_"));
                        var inputParam = FindInputParam(
                            targetObj,
                            GetParamIndex(operation, isOutput: false, "target_"),
                            GetParamName(operation, isOutput: false, "target_"));
                        if (outputParam == null || inputParam == null)
                        {
                            throw new InvalidOperationException("connect operation could not resolve source output or target input.");
                        }
                        inputParam.AddSource(outputParam);
                        EnsureParamHasData(outputParam);
                        targetObj.ExpireSolution(true);
                        addedConnections.Add(new GhConnectionRollback { Input = inputParam, Output = outputParam });
                        Touch(sourceObj);
                        Touch(targetObj);
                        opResults.Add(new JObject
                        {
                            ["op"] = "connect",
                            ["source_id"] = sourceObj.InstanceGuid.ToString(),
                            ["target_id"] = targetObj.InstanceGuid.ToString(),
                            ["source_param"] = outputParam.Name,
                            ["target_param"] = inputParam.Name
                        });
                        break;
                    }

                    case "set":
                    {
                        var obj = ResolveGraphObject(doc, aliases, OptionalString(operation, "target"), "set target");
                        Snapshot(obj);
                        ApplyBuildGraphValue(doc, aliases, operation);
                        Touch(obj);
                        opResults.Add(new JObject
                        {
                            ["op"] = "set",
                            ["target_id"] = obj.InstanceGuid.ToString(),
                            ["target"] = obj.NickName
                        });
                        break;
                    }

                    case "update":
                    {
                        var obj = ResolveGraphObject(doc, aliases, OptionalString(operation, "target"), "update target");
                        Snapshot(obj);

                        string newNickname = OptionalString(operation, "new_nickname") ?? OptionalString(operation, "nickname");
                        if (!string.IsNullOrWhiteSpace(newNickname))
                        {
                            obj.NickName = newNickname;
                        }
                        if (operation["position"] != null)
                        {
                            if (obj.Attributes == null)
                            {
                                obj.CreateAttributes();
                            }
                            obj.Attributes.Pivot = ReadPosition(operation, "position", obj.Attributes.Pivot.X, obj.Attributes.Pivot.Y);
                            obj.Attributes.ExpireLayout();
                        }
                        if (operation["preview"] != null && obj is IGH_PreviewObject previewObj)
                        {
                            previewObj.Hidden = !operation["preview"]!.ToObject<bool>();
                        }
                        if (operation["enabled"] != null && obj is IGH_ActiveObject activeObj)
                        {
                            activeObj.Locked = !operation["enabled"]!.ToObject<bool>();
                        }
                        string alias = OptionalString(operation, "alias");
                        string objectGraphId = OptionalString(operation, "graph_id");
                        string role = OptionalString(operation, "role");
                        if (!string.IsNullOrWhiteSpace(alias) || !string.IsNullOrWhiteSpace(objectGraphId) || !string.IsNullOrWhiteSpace(role))
                        {
                            ApplyGraphMetadata(obj, alias, objectGraphId ?? graphId, role);
                            if (!string.IsNullOrWhiteSpace(alias))
                            {
                                aliases[alias] = obj;
                            }
                        }
                        obj.ExpireSolution(false);
                        Touch(obj);
                        opResults.Add(new JObject
                        {
                            ["op"] = "update",
                            ["target_id"] = obj.InstanceGuid.ToString(),
                            ["target"] = obj.NickName
                        });
                        break;
                    }

                    case "disconnect":
                    {
                        var targetObj = ResolveGraphObject(doc, aliases, OptionalString(operation, "target"), "disconnect target");
                        var inputParam = FindInputParam(
                            targetObj,
                            GetParamIndex(operation, isOutput: false, "target_"),
                            GetParamName(operation, isOutput: false, "target_"));
                        if (inputParam == null)
                        {
                            throw new InvalidOperationException($"Could not find disconnect input parameter on '{targetObj.NickName}'.");
                        }

                        var removed = new List<IGH_Param>();
                        if (OptionalBool(operation, "disconnect_all", false))
                        {
                            removed.AddRange(inputParam.Sources);
                            inputParam.RemoveAllSources();
                        }
                        else
                        {
                            var sourceObj = ResolveGraphObject(doc, aliases, OptionalString(operation, "source"), "disconnect source");
                            var outputParam = FindOutputParam(
                                sourceObj,
                                GetParamIndex(operation, isOutput: true, "source_"),
                                GetParamName(operation, isOutput: true, "source_"));
                            if (outputParam != null && inputParam.Sources.Contains(outputParam))
                            {
                                inputParam.RemoveSource(outputParam);
                                removed.Add(outputParam);
                            }
                        }
                        if (removed.Count > 0)
                        {
                            removedConnections.Add(new GhDisconnectRollback { Input = inputParam, Sources = removed });
                        }
                        targetObj.ExpireSolution(true);
                        Touch(targetObj);
                        opResults.Add(new JObject
                        {
                            ["op"] = "disconnect",
                            ["target_id"] = targetObj.InstanceGuid.ToString(),
                            ["disconnected_count"] = removed.Count
                        });
                        break;
                    }

                    case "delete":
                    {
                        var obj = ResolveGraphObject(doc, aliases, OptionalString(operation, "target"), "delete target");
                        if (!pendingDeletes.Contains(obj))
                        {
                            pendingDeletes.Add(obj);
                        }
                        Touch(obj);
                        opResults.Add(new JObject
                        {
                            ["op"] = "delete",
                            ["target_id"] = obj.InstanceGuid.ToString(),
                            ["target"] = obj.NickName,
                            ["rollback"] = "limited"
                        });
                        break;
                    }

                    case "recompute":
                        forceRecompute = true;
                        opResults.Add(new JObject { ["op"] = "recompute" });
                        break;

                    default:
                        throw new ArgumentException($"Unsupported gh_mutate_graph operation '{op}'.");
                }
            }

            if (parameters["groups"] is JArray groupSpecs)
            {
                groups = CreateGrasshopperGroups(doc, groupSpecs, aliases, touched.Where(o => !pendingDeletes.Contains(o)), graphId, created);
                foreach (var groupId in groups.Select(g => g?["instance_id"]?.ToString()).Where(id => !string.IsNullOrEmpty(id)))
                {
                    var group = ResolveGraphObject(doc, aliases, groupId, "created group");
                    Touch(group);
                }
            }
            else
            {
                groups = new JArray();
            }

            if (BuildGraphLayoutEnabled(parameters["layout"]))
            {
                var layoutParams = parameters["layout"] as JObject ?? new JObject();
                var layoutTargets = ResolveGraphTargets(doc, aliases, layoutParams["targets"], "layout target");
                if (layoutTargets.Count == 0)
                {
                    layoutTargets = touched.Where(o => !pendingDeletes.Contains(o) && o is not GH_Group).Distinct().ToList();
                }
                if (layoutTargets.Count == 0)
                {
                    layoutTargets = GetGraphObjects(doc, graphId).Where(o => o is not GH_Group).ToList();
                }
                if (layoutTargets.Count > 0)
                {
                    float xSpacing = (float)Math.Max(60, layoutParams["x_spacing"]?.ToObject<double>() ?? 220);
                    float ySpacing = (float)Math.Max(40, layoutParams["y_spacing"]?.ToObject<double>() ?? 90);
                    var layoutStart = layoutParams["start_position"] != null
                        ? ReadPosition(layoutParams, "start_position", 40, 40)
                        : new PointF(40, 40);
                    layoutResult = ApplyGrasshopperLayout(layoutTargets, layoutStart, xSpacing, ySpacing);
                }
            }

            previewResult = ApplyPreviewPolicy(doc, aliases, parameters["preview_policy"] as JObject, touched, graphId);

            if (pendingDeletes.Count > 0)
            {
                doc.RemoveObjects(pendingDeletes, false);
            }

            if (recompute || forceRecompute)
            {
                foreach (var obj in touched.Where(o => !pendingDeletes.Contains(o)))
                {
                    obj.ExpireSolution(true);
                }
                RunGrasshopperSolution(doc, false);
            }

            verification = VerifyGrasshopperOutputs(doc, aliases, parameters["verify"] as JObject);
            var summaryObjects = touched
                .Where(o => !pendingDeletes.Contains(o))
                .Concat(GetGraphObjects(doc, graphId))
                .Distinct()
                .ToList();

            RedrawGrasshopperCanvas();

            return new JObject
            {
                ["success"] = true,
                ["graph_id"] = graphId,
                ["operation_count"] = operations.Count,
                ["created_count"] = created.Count,
                ["deleted_count"] = pendingDeletes.Count,
                ["recomputed"] = recompute || forceRecompute,
                ["rollback_on_error"] = rollbackOnError,
                ["operations"] = opResults,
                ["groups"] = groups,
                ["layout"] = layoutResult,
                ["preview_policy"] = previewResult,
                ["verification"] = verification,
                ["summary"] = BuildGraphSummary(doc, summaryObjects, graphId, verification),
                ["message"] = $"Mutated Grasshopper graph with {operations.Count} operation(s)"
            };
        }
        catch
        {
            if (rollbackOnError)
            {
                foreach (var added in addedConnections.AsEnumerable().Reverse())
                {
                    if (added.Input.Sources.Contains(added.Output))
                    {
                        added.Input.RemoveSource(added.Output);
                    }
                }
                foreach (var removed in removedConnections.AsEnumerable().Reverse())
                {
                    foreach (var source in removed.Sources)
                    {
                        if (!removed.Input.Sources.Contains(source))
                        {
                            removed.Input.AddSource(source);
                        }
                    }
                }
                foreach (var snapshot in snapshots.Values.Reverse())
                {
                    RestoreObjectSnapshot(snapshot);
                }
                if (created.Count > 0)
                {
                    doc.RemoveObjects(created, false);
                }
                RunGrasshopperSolution(doc, false);
                RedrawGrasshopperCanvas();
            }
            throw;
        }
    }
}
