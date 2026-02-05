using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;

namespace RhinoMCP.Shared.SocketServer;

/// <summary>
/// Interface for command handlers that process MCP commands.
/// Implement this interface in plugin-specific function classes.
/// </summary>
public interface ICommandHandler
{
    /// <summary>
    /// Get the dictionary mapping command type strings to handler functions.
    /// </summary>
    /// <returns>Dictionary of command handlers</returns>
    Dictionary<string, Func<JObject, JObject>> GetHandlers();

    /// <summary>
    /// Get the set of command types that don't modify the document.
    /// These commands won't create undo records.
    /// </summary>
    /// <returns>Set of read-only command names</returns>
    HashSet<string> GetReadOnlyCommands();
}
