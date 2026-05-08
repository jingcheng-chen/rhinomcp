using System;
using System.Text;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Runtime;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject ExecuteRhinoscript(JObject parameters)
    {
        string code = parameters["code"]?.ToString();
        if (string.IsNullOrEmpty(code))
        {
            throw new Exception("code is required");
        }

        var doc = RhinoDoc.ActiveDoc;
        var printOutput = new StringBuilder();

        PythonScript pythonScript = PythonScript.Create();
        pythonScript.Output += (message) => printOutput.Append(message);
        if (doc != null)
            pythonScript.SetupScriptContext(doc);

        // Dual capture:
        //   - pythonScript.Output → Python print() output
        //   - RhinoApp command-window capture → Rhino API output (rs.Command(...), etc.)
        bool previousCapture = RhinoApp.CommandWindowCaptureEnabled;
        RhinoApp.CommandWindowCaptureEnabled = true;
        bool ok = false;
        Exception scriptError = null;
        string[] rhinoLines = Array.Empty<string>();
        try
        {
            try
            {
                ok = pythonScript.ExecuteScript(code);
            }
            catch (Exception ex)
            {
                scriptError = ex;
            }
            // Read captured Rhino output BEFORE restoring capture state, so output
            // is preserved even when ExecuteScript threw.
            rhinoLines = RhinoApp.CapturedCommandWindowStrings(true) ?? Array.Empty<string>();
        }
        finally
        {
            RhinoApp.CommandWindowCaptureEnabled = previousCapture;
        }

        // Note: print() output is grouped before Rhino command-window lines.
        // Rhino's CommandWindowCaptureEnabled accumulates internally with no per-line
        // callback, so true chronological interleaving with PythonScript.Output is not
        // available. If a script alternates print() and rs.Command(...), the returned
        // order will not match execution order.
        var combined = new StringBuilder();
        if (printOutput.Length > 0)
        {
            combined.Append(printOutput);
        }
        if (rhinoLines.Length > 0)
        {
            if (combined.Length > 0 && combined[combined.Length - 1] != '\n')
                combined.Append('\n');
            combined.Append(string.Join("\n", rhinoLines));
        }

        var response = new JObject
        {
            ["success"] = ok && scriptError == null,
            ["output"] = combined.ToString()
        };
        if (scriptError != null)
        {
            response["message"] = scriptError.Message;
        }
        else if (!ok)
        {
            response["message"] = "Script execution returned false (no exception raised).";
        }
        return response;
    }
}
