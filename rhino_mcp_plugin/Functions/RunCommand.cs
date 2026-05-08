using System;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject RunCommand(JObject parameters)
    {
        string command = parameters["command"]?.ToString();
        if (string.IsNullOrEmpty(command))
        {
            throw new Exception("command is required");
        }

        bool echo = parameters["echo"]?.ToObject<bool>() ?? false;

        bool previousCapture = RhinoApp.CommandWindowCaptureEnabled;
        RhinoApp.CommandWindowCaptureEnabled = true;
        bool ran = false;
        string[] lines = Array.Empty<string>();
        Exception runError = null;
        try
        {
            try
            {
                ran = RhinoApp.RunScript(command, echo);
            }
            catch (Exception ex)
            {
                runError = ex;
            }
            // Read captured output BEFORE restoring capture state, so output is
            // available even when RunScript threw.
            lines = RhinoApp.CapturedCommandWindowStrings(true) ?? Array.Empty<string>();
        }
        finally
        {
            RhinoApp.CommandWindowCaptureEnabled = previousCapture;
        }

        string output = lines.Length > 0 ? string.Join("\n", lines) : "";
        if (runError != null)
        {
            // Surface the exception alongside any captured output so the agent
            // sees the full picture. success=false signals the failure.
            output = string.IsNullOrEmpty(output)
                ? $"Exception: {runError.Message}"
                : $"{output}\nException: {runError.Message}";
            ran = false;
        }

        return new JObject
        {
            ["success"] = ran,
            ["command"] = command,
            ["output"] = output
        };
    }
}
