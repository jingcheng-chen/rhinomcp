using System;
using Rhino;
using RhinoMCP.Shared.SocketServer;
using RhinoMCPPlugin.Functions;

namespace RhinoMCPPlugin;

/// <summary>
/// Rhino-specific MCP server implementation.
/// Extends the shared BaseSocketServer with Rhino-specific UI thread handling and undo support.
/// </summary>
public class RhinoMCPServer : BaseSocketServer
{
    private readonly RhinoMCPFunctions handler;

    public override string ServerName => "RhinoMCP";

    public RhinoMCPServer(string host = "127.0.0.1", int port = 1999)
        : base(host, port)
    {
        this.handler = new RhinoMCPFunctions();
    }

    public override ICommandHandler GetHandler() => handler;

    public override void InvokeOnMainThread(Action action)
    {
        // Use Rhino's UI thread invocation
        RhinoApp.InvokeOnUiThread(action);
    }

    public override uint BeginUndoRecord(string commandName)
    {
        return RhinoDoc.ActiveDoc.BeginUndoRecord(commandName);
    }

    public override void EndUndoRecord(uint recordId)
    {
        RhinoDoc.ActiveDoc.EndUndoRecord(recordId);
    }
}
