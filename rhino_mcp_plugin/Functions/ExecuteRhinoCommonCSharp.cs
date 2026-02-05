using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using Microsoft.CodeAnalysis.CSharp.Scripting;
using Microsoft.CodeAnalysis.Scripting;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Globals available to C# scripts executed via ExecuteRhinoCommonCSharp
/// </summary>
public class CSharpScriptGlobals
{
    /// <summary>
    /// The active Rhino document
    /// </summary>
    public RhinoDoc doc { get; set; }

    /// <summary>
    /// StringBuilder to capture output (use output.AppendLine("..."))
    /// </summary>
    public StringBuilder output { get; set; }
}

public partial class RhinoMCPFunctions
{
    private static ScriptOptions _scriptOptions;
    private static bool _scriptOptionsInitialized = false;
    private static readonly object _scriptOptionsLock = new object();

    /// <summary>
    /// Get or create cached script options for C# execution
    /// </summary>
    private static ScriptOptions GetScriptOptions()
    {
        if (_scriptOptionsInitialized)
            return _scriptOptions;

        lock (_scriptOptionsLock)
        {
            if (_scriptOptionsInitialized)
                return _scriptOptions;

            // Build script options with necessary references and imports
            _scriptOptions = ScriptOptions.Default
                // Add assembly references
                .AddReferences(
                    typeof(object).Assembly,                    // mscorlib / System.Private.CoreLib
                    typeof(System.Linq.Enumerable).Assembly,    // System.Linq
                    typeof(List<>).Assembly,                    // System.Collections.Generic
                    typeof(RhinoDoc).Assembly,                  // RhinoCommon
                    typeof(Point3d).Assembly,                   // Rhino.Geometry (same as RhinoCommon)
                    Assembly.Load("System.Runtime")             // Required for some types
                )
                // Add common imports so users don't need to add using statements
                .AddImports(
                    "System",
                    "System.Collections.Generic",
                    "System.Linq",
                    "System.Text",
                    "Rhino",
                    "Rhino.Geometry",
                    "Rhino.DocObjects",
                    "Rhino.Commands"
                );

            _scriptOptionsInitialized = true;
            return _scriptOptions;
        }
    }

    public JObject ExecuteRhinoCommonCSharp(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        string code = parameters["code"]?.ToString();

        if (string.IsNullOrEmpty(code))
        {
            throw new Exception("Code is required");
        }

        var output = new StringBuilder();

        try
        {
            // Create the globals object that scripts can access
            var globals = new CSharpScriptGlobals
            {
                doc = doc,
                output = output
            };

            // Get cached script options
            var scriptOptions = GetScriptOptions();

            // Execute the script synchronously (we're already on the UI thread)
            var task = CSharpScript.EvaluateAsync(
                code,
                scriptOptions,
                globals,
                typeof(CSharpScriptGlobals)
            );

            // Wait for completion
            task.Wait();

            return new JObject
            {
                ["success"] = true,
                ["output"] = output.ToString(),
                ["result"] = $"Script successfully executed!"
            };
        }
        catch (AggregateException ae)
        {
            // Unwrap aggregate exceptions to get the real error
            var innerException = ae.InnerException;
            var errorMessage = FormatScriptError(innerException ?? ae, code);

            return new JObject
            {
                ["success"] = false,
                ["output"] = output.ToString(),
                ["message"] = errorMessage
            };
        }
        catch (CompilationErrorException ce)
        {
            // Format compilation errors nicely
            var errors = new StringBuilder();
            errors.AppendLine("Compilation failed:");
            foreach (var diagnostic in ce.Diagnostics)
            {
                errors.AppendLine($"  {diagnostic}");
            }

            return new JObject
            {
                ["success"] = false,
                ["output"] = output.ToString(),
                ["message"] = errors.ToString()
            };
        }
        catch (Exception e)
        {
            var errorMessage = FormatScriptError(e, code);

            return new JObject
            {
                ["success"] = false,
                ["output"] = output.ToString(),
                ["message"] = errorMessage
            };
        }
    }

    /// <summary>
    /// Format a script error with helpful context
    /// </summary>
    private string FormatScriptError(Exception e, string code)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"Script execution failed: {e.GetType().Name}");
        sb.AppendLine($"Message: {e.Message}");

        // Check for compilation errors
        if (e is CompilationErrorException ce)
        {
            sb.AppendLine("Compilation errors:");
            foreach (var diagnostic in ce.Diagnostics)
            {
                sb.AppendLine($"  {diagnostic}");
            }
        }

        // Add inner exception details if present
        if (e.InnerException != null)
        {
            sb.AppendLine($"Inner exception: {e.InnerException.Message}");
        }

        return sb.ToString();
    }
}
