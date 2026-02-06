using System;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Trigger a new solution in Grasshopper.
    /// </summary>
    public JObject RunSolution(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        // Check if we should expire all objects first
        var expireAll = parameters["expire_all"]?.ToObject<bool>() ?? false;

        if (expireAll)
        {
            foreach (var obj in doc.Objects)
            {
                obj.ExpireSolution(false);
            }
        }

        // Trigger solution
        doc.NewSolution(true);

        // Wait for solution to complete (with timeout)
        var timeout = parameters["timeout_ms"]?.ToObject<int>() ?? 5000;
        var startTime = DateTime.Now;

        while (doc.SolutionState == GH_ProcessStep.Process)
        {
            System.Threading.Thread.Sleep(50);
            if ((DateTime.Now - startTime).TotalMilliseconds > timeout)
            {
                return new JObject
                {
                    ["success"] = false,
                    ["message"] = "Solution timed out",
                    ["solution_state"] = doc.SolutionState.ToString()
                };
            }
        }

        // Get solution statistics and collect error/warning details
        var errorCount = 0;
        var warningCount = 0;
        var errors = new JArray();
        var warnings = new JArray();

        foreach (var obj in doc.Objects)
        {
            if (obj is IGH_ActiveObject activeObj)
            {
                var level = activeObj.RuntimeMessageLevel;

                if (level == GH_RuntimeMessageLevel.Error || level == GH_RuntimeMessageLevel.Warning)
                {
                    // Collect all runtime messages from this component
                    var messages = new JArray();
                    foreach (var msg in activeObj.RuntimeMessages(level))
                    {
                        messages.Add(msg);
                    }

                    var componentInfo = new JObject
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
                        errors.Add(componentInfo);
                    }
                    else
                    {
                        warningCount++;
                        warnings.Add(componentInfo);
                    }
                }
            }
        }

        var result = new JObject
        {
            ["success"] = errorCount == 0,
            ["solution_state"] = doc.SolutionState.ToString(),
            ["error_count"] = errorCount,
            ["warning_count"] = warningCount
        };

        // Include detailed error information
        if (errors.Count > 0)
        {
            result["errors"] = errors;
        }

        // Include warnings if present
        if (warnings.Count > 0)
        {
            result["warnings"] = warnings;
        }

        // Build helpful message
        if (errorCount > 0)
        {
            var errorSummary = string.Join("; ", errors.Take(3).Select(e =>
                $"{e["nickname"]}: {string.Join(", ", ((JArray)e["messages"]).Take(1))}"));
            result["message"] = $"Solution has {errorCount} error(s): {errorSummary}";
        }
        else if (warningCount > 0)
        {
            result["message"] = $"Solution completed with {warningCount} warning(s)";
        }
        else
        {
            result["message"] = "Solution completed successfully";
        }

        return result;
    }
}
