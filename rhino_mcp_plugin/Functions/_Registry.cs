using System;
using System.Collections.Generic;
using System.Reflection;
using Newtonsoft.Json.Linq;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Reflection-based dispatch registry for RhinoMCPFunctions.
/// Scans methods decorated with [McpCommand] once and caches the lookup table.
/// </summary>
public partial class RhinoMCPFunctions
{
    public readonly struct DispatchEntry
    {
        public readonly Func<JObject, JObject> Handler;
        public readonly bool ReadOnly;

        public DispatchEntry(Func<JObject, JObject> handler, bool readOnly)
        {
            Handler = handler;
            ReadOnly = readOnly;
        }
    }

    private IReadOnlyDictionary<string, DispatchEntry> _dispatchTable;

    /// <summary>
    /// Returns a dispatch table built by reflecting over methods on this instance
    /// decorated with [McpCommand]. Built lazily on first access, then cached.
    /// </summary>
    public IReadOnlyDictionary<string, DispatchEntry> GetDispatchTable()
    {
        if (_dispatchTable != null) return _dispatchTable;

        var table = new Dictionary<string, DispatchEntry>(StringComparer.Ordinal);
        var methods = typeof(RhinoMCPFunctions).GetMethods(
            BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly);

        foreach (var method in methods)
        {
            var attr = method.GetCustomAttribute<McpCommandAttribute>();
            if (attr == null) continue;

            var handler = (Func<JObject, JObject>)Delegate.CreateDelegate(
                typeof(Func<JObject, JObject>), this, method);

            if (table.ContainsKey(attr.Name))
            {
                throw new InvalidOperationException(
                    $"Duplicate [McpCommand(\"{attr.Name}\")] on {method.Name}.");
            }
            table[attr.Name] = new DispatchEntry(handler, attr.ReadOnly);
        }

        _dispatchTable = table;
        return _dispatchTable;
    }
}
