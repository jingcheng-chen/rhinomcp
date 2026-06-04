using System;
using System.Collections.Generic;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("gh_run_solution")]
    public JObject GhRunSolution(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        bool expireAll = OptionalBool(parameters, "expire_all", false);

        var start = DateTime.UtcNow;
        RunGrasshopperSolution(doc, expireAll);

        var runtime = CollectRuntimeMessages(doc);
        runtime["solution_state"] = doc.SolutionState.ToString();
        runtime["duration_ms"] = (int)(DateTime.UtcNow - start).TotalMilliseconds;
        runtime["message"] = BuildSolutionMessage(runtime);
        return runtime;
    }

    [McpCommand("gh_expire_solution")]
    public JObject GhExpireSolution(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        bool expireDownstream = OptionalBool(parameters, "expire_downstream", true);
        bool recompute = OptionalBool(parameters, "recompute", false);
        int expiredCount = 0;

        var componentIds = parameters["component_ids"]?.ToObject<List<string>>() ?? new List<string>();
        if (componentIds.Count > 0)
        {
            foreach (string id in componentIds)
            {
                if (!Guid.TryParse(id, out var guid))
                {
                    throw new ArgumentException($"Invalid component GUID: {id}");
                }
                var obj = doc.FindObject(guid, true);
                if (obj != null)
                {
                    obj.ExpireSolution(expireDownstream);
                    expiredCount++;
                }
            }
        }
        else if (HasAnySelector(parameters))
        {
            var obj = FindGhObject(doc, parameters);
            obj.ExpireSolution(expireDownstream);
            expiredCount = 1;
        }
        else
        {
            foreach (var obj in doc.Objects)
            {
                obj.ExpireSolution(false);
                expiredCount++;
            }
        }

        if (recompute)
        {
            RunGrasshopperSolution(doc, false);
        }

        return new JObject
        {
            ["expired_count"] = expiredCount,
            ["recomputed"] = recompute,
            ["message"] = $"Expired {expiredCount} Grasshopper object(s)" + (recompute ? " and triggered recompute" : "")
        };
    }

    private static JObject CollectRuntimeMessages(GH_Document doc)
    {
        int errorCount = 0;
        int warningCount = 0;
        var errors = new JArray();
        var warnings = new JArray();

        foreach (var obj in doc.Objects)
        {
            if (obj is not IGH_ActiveObject activeObj)
            {
                continue;
            }

            var level = activeObj.RuntimeMessageLevel;
            if (level != GH_RuntimeMessageLevel.Error && level != GH_RuntimeMessageLevel.Warning)
            {
                continue;
            }

            var messages = new JArray(activeObj.RuntimeMessages(level));
            var info = new JObject
            {
                ["instance_id"] = obj.InstanceGuid.ToString(),
                ["name"] = obj.Name,
                ["nickname"] = obj.NickName,
                ["category"] = obj.Category,
                ["messages"] = messages
            };

            if (level == GH_RuntimeMessageLevel.Error)
            {
                errorCount++;
                errors.Add(info);
            }
            else
            {
                warningCount++;
                warnings.Add(info);
            }
        }

        return new JObject
        {
            ["success"] = errorCount == 0,
            ["error_count"] = errorCount,
            ["warning_count"] = warningCount,
            ["errors"] = errors,
            ["warnings"] = warnings
        };
    }

    private static string BuildSolutionMessage(JObject runtime)
    {
        int errors = runtime["error_count"]?.ToObject<int>() ?? 0;
        int warnings = runtime["warning_count"]?.ToObject<int>() ?? 0;
        if (errors > 0)
        {
            return $"Solution has {errors} error(s)";
        }
        if (warnings > 0)
        {
            return $"Solution completed with {warnings} warning(s)";
        }
        return "Solution completed successfully";
    }

    private static JArray RuntimeMessagesToJson(IGH_ActiveObject obj)
    {
        var messages = new JArray();
        foreach (var level in new[] { GH_RuntimeMessageLevel.Error, GH_RuntimeMessageLevel.Warning, GH_RuntimeMessageLevel.Remark })
        {
            foreach (string message in obj.RuntimeMessages(level))
            {
                messages.Add(new JObject
                {
                    ["level"] = level.ToString(),
                    ["message"] = message
                });
            }
        }
        return messages;
    }
}
