using System;
using Grasshopper;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Connect two components by wiring an output to an input.
    /// Supports both Python naming (source_instance_id, source_nickname, source_output)
    /// and C# naming (source_id, source_param_index).
    /// </summary>
    public JObject ConnectComponents(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        // Find source component - supports instance_id, nickname, or id
        var sourceObj = ComponentHelper.FindComponent(doc, parameters, "source_");

        // Find target component
        var targetObj = ComponentHelper.FindComponent(doc, parameters, "target_");

        // Get source output parameter index/name
        var sourceParamIndex = ComponentHelper.GetParamIndex(parameters, isOutput: true, "source_");
        var sourceParamName = ComponentHelper.GetParamName(parameters, isOutput: true, "source_");

        // Get target input parameter index/name
        var targetParamIndex = ComponentHelper.GetParamIndex(parameters, isOutput: false, "target_");
        var targetParamName = ComponentHelper.GetParamName(parameters, isOutput: false, "target_");

        // Find the output parameter
        var outputParam = ComponentHelper.FindOutputParam(sourceObj, sourceParamIndex, sourceParamName);
        if (outputParam == null)
        {
            throw new InvalidOperationException($"Could not find output parameter on source component '{sourceObj.NickName}'");
        }

        // Find the input parameter
        var inputParam = ComponentHelper.FindInputParam(targetObj, targetParamIndex, targetParamName);
        if (inputParam == null)
        {
            throw new InvalidOperationException($"Could not find input parameter on target component '{targetObj.NickName}'");
        }

        // Create the connection
        inputParam.AddSource(outputParam);

        // Trigger solution
        doc.NewSolution(false);

        return new JObject
        {
            ["source_id"] = sourceObj.InstanceGuid.ToString(),
            ["source_nickname"] = sourceObj.NickName,
            ["source_param"] = outputParam.Name,
            ["target_id"] = targetObj.InstanceGuid.ToString(),
            ["target_nickname"] = targetObj.NickName,
            ["target_param"] = inputParam.Name,
            ["message"] = $"Connected {sourceObj.NickName}.{outputParam.Name} to {targetObj.NickName}.{inputParam.Name}"
        };
    }
}
