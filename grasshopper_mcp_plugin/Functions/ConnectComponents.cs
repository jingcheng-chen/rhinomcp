using System;
using System.Linq;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Connect two components by wiring an output to an input.
    /// </summary>
    public JObject ConnectComponents(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        // Get source component and parameter
        var sourceId = parameters["source_id"]?.ToString();
        var sourceParam = parameters["source_param"]?.ToString();
        var sourceParamIndex = parameters["source_param_index"]?.ToObject<int?>() ?? null;

        // Get target component and parameter
        var targetId = parameters["target_id"]?.ToString();
        var targetParam = parameters["target_param"]?.ToString();
        var targetParamIndex = parameters["target_param_index"]?.ToObject<int?>() ?? null;

        if (string.IsNullOrEmpty(sourceId) || string.IsNullOrEmpty(targetId))
        {
            throw new ArgumentException("Both source_id and target_id are required");
        }

        // Find source component
        if (!Guid.TryParse(sourceId, out var sourceGuid))
        {
            throw new ArgumentException($"Invalid source_id GUID: {sourceId}");
        }
        var sourceObj = doc.FindObject(sourceGuid, true);
        if (sourceObj == null)
        {
            throw new InvalidOperationException($"Source component '{sourceId}' not found");
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

        // Get output parameter from source
        IGH_Param? outputParam = null;

        if (sourceObj is IGH_Component sourceComp)
        {
            if (sourceParamIndex.HasValue && sourceParamIndex.Value < sourceComp.Params.Output.Count)
            {
                outputParam = sourceComp.Params.Output[sourceParamIndex.Value];
            }
            else if (!string.IsNullOrEmpty(sourceParam))
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

        if (outputParam == null)
        {
            throw new InvalidOperationException($"Could not find output parameter '{sourceParam}' on source component");
        }

        // Get input parameter from target
        IGH_Param? inputParam = null;

        if (targetObj is IGH_Component targetComp)
        {
            if (targetParamIndex.HasValue && targetParamIndex.Value < targetComp.Params.Input.Count)
            {
                inputParam = targetComp.Params.Input[targetParamIndex.Value];
            }
            else if (!string.IsNullOrEmpty(targetParam))
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

        // Create the connection
        inputParam.AddSource(outputParam);

        // Trigger solution
        doc.NewSolution(false);

        return new JObject
        {
            ["source_id"] = sourceId,
            ["source_param"] = outputParam.Name,
            ["target_id"] = targetId,
            ["target_param"] = inputParam.Name,
            ["message"] = $"Connected {sourceObj.Name}.{outputParam.Name} to {targetObj.Name}.{inputParam.Name}"
        };
    }
}
