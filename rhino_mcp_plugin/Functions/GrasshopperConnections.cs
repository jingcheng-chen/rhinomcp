using System;
using Grasshopper.Kernel;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("gh_connect_components")]
    public JObject GhConnectComponents(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        var sourceObj = FindGhObject(doc, parameters, "source_");
        var targetObj = FindGhObject(doc, parameters, "target_");

        var outputParam = FindOutputParam(
            sourceObj,
            GetParamIndex(parameters, isOutput: true, "source_"),
            GetParamName(parameters, isOutput: true, "source_"));
        if (outputParam == null)
        {
            throw new InvalidOperationException($"Could not find output parameter on source component '{sourceObj.NickName}'.");
        }

        var inputParam = FindInputParam(
            targetObj,
            GetParamIndex(parameters, isOutput: false, "target_"),
            GetParamName(parameters, isOutput: false, "target_"));
        if (inputParam == null)
        {
            throw new InvalidOperationException($"Could not find input parameter on target component '{targetObj.NickName}'.");
        }

        inputParam.AddSource(outputParam);
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

    [McpCommand("gh_disconnect_components")]
    public JObject GhDisconnectComponents(JObject parameters)
    {
        var doc = GetActiveGrasshopperDocument();
        bool disconnectAll = OptionalBool(parameters, "disconnect_all", false);
        var targetObj = FindGhObject(doc, parameters, "target_");
        var inputParam = FindInputParam(
            targetObj,
            GetParamIndex(parameters, isOutput: false, "target_"),
            GetParamName(parameters, isOutput: false, "target_"));
        if (inputParam == null)
        {
            throw new InvalidOperationException($"Could not find input parameter on target component '{targetObj.NickName}'.");
        }

        int disconnectedCount = 0;
        if (disconnectAll)
        {
            disconnectedCount = inputParam.SourceCount;
            inputParam.RemoveAllSources();
        }
        else
        {
            var sourceObj = FindGhObject(doc, parameters, "source_");
            var outputParam = FindOutputParam(
                sourceObj,
                GetParamIndex(parameters, isOutput: true, "source_"),
                GetParamName(parameters, isOutput: true, "source_"));
            if (outputParam != null && inputParam.Sources.Contains(outputParam))
            {
                inputParam.RemoveSource(outputParam);
                disconnectedCount = 1;
            }
        }

        doc.NewSolution(false);

        return new JObject
        {
            ["target_id"] = targetObj.InstanceGuid.ToString(),
            ["target_nickname"] = targetObj.NickName,
            ["target_param"] = inputParam.Name,
            ["disconnected_count"] = disconnectedCount,
            ["message"] = disconnectedCount > 0
                ? $"Disconnected {disconnectedCount} connection(s) from {targetObj.NickName}.{inputParam.Name}"
                : "No connections were disconnected"
        };
    }
}
