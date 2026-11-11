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
    /// Use for purely introspective commands (get_*, capture_viewport) and for
    /// commands that act on undo records themselves (undo, redo, begin_undo_group,
    /// end_undo_group).
    /// Settable so call sites can use named-argument syntax: [McpCommand("foo", ReadOnly = true)].
    /// </summary>
    public bool ReadOnly { get; set; }

    /// <summary>
    /// If true, the handler honors a params-level dry_run flag by previewing its
    /// result without mutating the document. The dispatcher rejects dry_run on any
    /// command that does not set this, and for one that does it skips the undo
    /// record and the perception blocks since a preview changes nothing.
    /// Settable for named-argument syntax: [McpCommand("foo", SupportsDryRun = true)].
    /// </summary>
    public bool SupportsDryRun { get; set; }

    public McpCommandAttribute(string name)
    {
        Name = name;
    }
}
