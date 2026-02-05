using System;
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

        // Get solution statistics
        var errorCount = 0;
        var warningCount = 0;

        foreach (var obj in doc.Objects)
        {
            if (obj is IGH_ActiveObject activeObj)
            {
                if (activeObj.RuntimeMessageLevel == GH_RuntimeMessageLevel.Error)
                    errorCount++;
                else if (activeObj.RuntimeMessageLevel == GH_RuntimeMessageLevel.Warning)
                    warningCount++;
            }
        }

        return new JObject
        {
            ["success"] = true,
            ["solution_state"] = doc.SolutionState.ToString(),
            ["error_count"] = errorCount,
            ["warning_count"] = warningCount,
            ["message"] = errorCount > 0
                ? $"Solution completed with {errorCount} error(s) and {warningCount} warning(s)"
                : "Solution completed successfully"
        };
    }
}
