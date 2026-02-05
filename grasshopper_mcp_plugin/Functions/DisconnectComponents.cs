using System;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Disconnect a wire between two components.
    /// </summary>
    public JObject DisconnectComponents(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        // Get source component and parameter
        var sourceId = parameters["source_id"]?.ToString();
        var sourceParam = parameters["source_param"]?.ToString();

        // Get target component and parameter
        var targetId = parameters["target_id"]?.ToString();
        var targetParam = parameters["target_param"]?.ToString();

        // Option to disconnect all sources from a target
        var disconnectAll = parameters["disconnect_all"]?.ToObject<bool>() ?? false;

        if (string.IsNullOrEmpty(targetId))
        {
            throw new ArgumentException("target_id is required");
        }

        // Find target component
        if (!Guid.TryParse(targetId, out var targetGuid))
        {
            throw new ArgumentException($"Invalid target_id GUID: {targetId}");
        }
        var targetObj = doc.FindObject(targetGuid, true);
        if (targetObj == null)
        {
            throw new InvalidOperationException($"Target component '{targetId}' not found");
        }

        // Get input parameter from target
        IGH_Param? inputParam = null;

        if (targetObj is IGH_Component targetComp)
        {
            if (!string.IsNullOrEmpty(targetParam))
            {
                inputParam = targetComp.Params.Input
                    .FirstOrDefault(p => p.Name.Equals(targetParam, StringComparison.OrdinalIgnoreCase)
                                      || p.NickName.Equals(targetParam, StringComparison.OrdinalIgnoreCase));
            }
            else if (targetComp.Params.Input.Count == 1)
            {
                inputParam = targetComp.Params.Input[0];
            }
        }
        else if (targetObj is IGH_Param targetP)
        {
            inputParam = targetP;
        }

        if (inputParam == null)
        {
            throw new InvalidOperationException($"Could not find input parameter '{targetParam}' on target component");
        }

        int disconnectedCount = 0;

        if (disconnectAll)
        {
            // Disconnect all sources
            disconnectedCount = inputParam.SourceCount;
            inputParam.RemoveAllSources();
        }
        else if (!string.IsNullOrEmpty(sourceId))
        {
            // Find and disconnect specific source
            if (!Guid.TryParse(sourceId, out var sourceGuid))
            {
                throw new ArgumentException($"Invalid source_id GUID: {sourceId}");
            }
            var sourceObj = doc.FindObject(sourceGuid, true);
            if (sourceObj == null)
            {
                throw new InvalidOperationException($"Source component '{sourceId}' not found");
            }

            // Get output parameter from source
            IGH_Param? outputParam = null;

            if (sourceObj is IGH_Component sourceComp)
            {
                if (!string.IsNullOrEmpty(sourceParam))
                {
                    outputParam = sourceComp.Params.Output
                        .FirstOrDefault(p => p.Name.Equals(sourceParam, StringComparison.OrdinalIgnoreCase)
                                          || p.NickName.Equals(sourceParam, StringComparison.OrdinalIgnoreCase));
                }
                else if (sourceComp.Params.Output.Count == 1)
                {
                    outputParam = sourceComp.Params.Output[0];
                }
            }
            else if (sourceObj is IGH_Param sourceP)
            {
                outputParam = sourceP;
            }

            if (outputParam != null && inputParam.Sources.Contains(outputParam))
            {
                inputParam.RemoveSource(outputParam);
                disconnectedCount = 1;
            }
        }
        else
        {
            throw new ArgumentException("Either source_id or disconnect_all=true is required");
        }

        // Trigger solution
        doc.NewSolution(false);

        return new JObject
        {
            ["target_id"] = targetId,
            ["target_param"] = inputParam.Name,
            ["disconnected_count"] = disconnectedCount,
            ["message"] = disconnectedCount > 0
                ? $"Disconnected {disconnectedCount} connection(s) from {targetObj.Name}.{inputParam.Name}"
                : "No connections were disconnected"
        };
    }
}
