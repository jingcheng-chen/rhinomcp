using System;

namespace RhinoMCPPlugin;

/// <summary>
/// Marks a method on RhinoMCPFunctions as the handler for a JSON command type.
/// The reflection-based registry in RhinoMCPFunctions.GetDispatchTable() uses
/// these attributes to build the dispatch table at startup. To add a new command,
/// add a new method with this attribute — no other wiring needed.
/// </summary>
[AttributeUsage(AttributeTargets.Method, AllowMultiple = false, Inherited = false)]
public sealed class McpCommandAttribute : Attribute
{
    /// <summary>The JSON command type, e.g. "create_object". Conventionally snake_case.</summary>
    public string Name { get; }

    /// <summary>
    /// If true, the dispatcher does not wrap the handler in a Rhino undo record.
    /// Use for purely introspective commands (get_*, undo, redo, capture_viewport).
    /// Settable so call sites can use named-argument syntax: [McpCommand("foo", ReadOnly = true)].
    /// </summary>
    public bool ReadOnly { get; set; }

    public McpCommandAttribute(string name)
    {
        Name = name;
    }
}
