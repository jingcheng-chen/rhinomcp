using System;
using System.Threading;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Undo groups: one Rhino undo record kept open across commands, so a single
/// Undo reverts everything between begin_undo_group and end_undo_group instead
/// of one command at a time. MCP over stdio has no turn boundary, so the client
/// that knows one supplies it: a host around each agent turn, or an agent around
/// one multi-step edit.
///
/// While the group's record is open, Rhino declines every other BeginUndoRecord
/// (it returns 0), so each command's changes land in the group's record. The
/// record belongs to the document, not to the connection: changes from other
/// clients and edits the user makes in Rhino join the group too.
///
/// A record left open would fold every later edit into one stale undo step, so
/// a group also ends when the client that began it disconnects, when no command
/// arrives for its idle timeout, and when its document closes or another
/// document becomes active.
///
/// Rhino requires undo records to begin and end on its UI thread. Everything
/// here runs there: commands already do, and the idle timer and the disconnect
/// hook post to it.
/// </summary>
public partial class RhinoMCPFunctions
{
    public const int DefaultUndoGroupIdleSeconds = 120;
    public const int MaxUndoGroupIdleSeconds = 3600;
    private const int UndoGroupNameCap = 80;

    private const string UndoGroupRequested = "requested";
    private const string UndoGroupClientDisconnected = "client_disconnected";
    private const string UndoGroupIdleTimeout = "idle_timeout";
    private const string UndoGroupDocumentClosed = "document_closed";
    private const string UndoGroupDocumentChanged = "document_changed";
    private const string UndoGroupRecordEndedElsewhere = "record_ended_elsewhere";

    private sealed class UndoGroup
    {
        public RhinoDoc Doc;
        public uint DocSerial;
        public uint Record;
        public string Name;
        // Connection that began the group; 0 for a direct call such as mcptest.
        public int OwnerId;
        public string Owner;
        public TimeSpan IdleTimeout;
        public DateTime OpenedAt;
        public DateTime LastCommandAt;
        public int CommandCount;
        public Timer IdleTimer;
    }

    private UndoGroup _undoGroup;
    // The last group that ended without end_undo_group, and why, reported to
    // the next end_undo_group that finds no group open.
    private JObject _undoGroupEndedUnasked;
    private string _undoGroupEndedUnaskedBecause;

    /// <summary>
    /// The connection whose command is running, or null for a direct call
    /// (mcptest). The dispatcher sets it around each command.
    /// </summary>
    internal ClientConnection CurrentClient { get; set; }

    // ReadOnly: the dispatcher must not wrap this command in its own record,
    // or Rhino would decline the group's record inside it.
    [McpCommand("begin_undo_group", ReadOnly = true)]
    public JObject BeginUndoGroup(JObject parameters)
    {
        string name = UndoGroupName(parameters["name"]);
        int idleSeconds = UndoGroupIdleSeconds(parameters);

        var open = LiveUndoGroup();
        if (open != null)
        {
            throw new McpException(
                McpException.InvalidArgument,
                $"Undo group '{open.Name}' is already open{OwnerClause(open)}",
                OwnedByCaller(open)
                    ? "Undo groups do not nest: call end_undo_group, then begin the next group."
                    : $"Undo groups do not nest. That group ends when its client ends it or disconnects, or after {(int)open.IdleTimeout.TotalSeconds} seconds without commands.");
        }

        var doc = RhinoDoc.ActiveDoc ?? throw new McpException(
            McpException.NotFound, "No active document", "Open or create a model in Rhino, then retry.");

        string description = $"MCP: {name}";
        uint record = doc.BeginUndoRecord(description);
        if (record == 0)
        {
            // Declined: undo is off, or another record is open (usually that of a
            // Rhino command still running). That record is not ours to end.
            if (!doc.UndoRecordingEnabled)
                throw new McpException(
                    McpException.RhinoError,
                    "Undo is turned off in this document",
                    "Turn undo back on in Rhino, or make the change without an undo group.");
            throw new McpException(
                McpException.RhinoError,
                "Rhino is already recording an undo step, usually for a command that is still running",
                "Finish or cancel the command running in Rhino, then call begin_undo_group again.");
        }

        var now = DateTime.UtcNow;
        var client = CurrentClient;
        var group = new UndoGroup
        {
            Doc = doc,
            DocSerial = doc.RuntimeSerialNumber,
            Record = record,
            Name = name,
            OwnerId = client?.Id ?? 0,
            Owner = client?.Description ?? "Rhino",
            IdleTimeout = TimeSpan.FromSeconds(idleSeconds),
            OpenedAt = now,
            LastCommandAt = now,
        };
        group.IdleTimer = new Timer(
            _ => RhinoApp.InvokeOnUiThread(new Action(() => CheckUndoGroupIdle(group))),
            null, group.IdleTimeout, Timeout.InfiniteTimeSpan);
        _undoGroup = group;
        _undoGroupEndedUnasked = null;
        _undoGroupEndedUnaskedBecause = null;
        RhinoDoc.CloseDocument += OnUndoGroupDocumentClosing;
        RhinoDoc.ActiveDocumentChanged += OnUndoGroupActiveDocumentChanged;

        RhinoApp.WriteLine($"RhinoMCP: undo group '{name}' begun by {group.Owner}.");
        return new JObject
        {
            ["name"] = name,
            ["undo_description"] = description,
            ["document_name"] = string.IsNullOrEmpty(doc.Name) ? null : doc.Name,
            ["idle_timeout_seconds"] = idleSeconds,
            ["message"] = $"Undo group '{name}' is open: changes until end_undo_group are one undo step, '{description}'."
        };
    }

    [McpCommand("end_undo_group", ReadOnly = true)]
    public JObject EndUndoGroup(JObject parameters)
    {
        var group = LiveUndoGroup();
        if (group == null)
        {
            var none = new JObject { ["ended"] = false, ["message"] = "No undo group is open." };
            if (_undoGroupEndedUnasked != null)
            {
                none["last_group"] = _undoGroupEndedUnasked.DeepClone();
                none["message"] = $"No undo group is open. '{_undoGroupEndedUnasked["name"]}' already ended because "
                    + $"{_undoGroupEndedUnaskedBecause}; changes made after that have their own undo steps.";
            }
            return none;
        }

        if (!OwnedByCaller(group))
        {
            throw new McpException(
                McpException.InvalidArgument,
                $"Undo group '{group.Name}' was begun by another client ({group.Owner})",
                $"Only that client can end it. It also ends when that client disconnects, or after {(int)group.IdleTimeout.TotalSeconds} seconds without commands.");
        }

        var summary = CloseUndoGroup(group, UndoGroupRequested);
        summary.AddFirst(new JProperty("ended", true));
        summary["message"] = $"Undo group '{group.Name}' ended: one Undo reverts its changes ('MCP: {group.Name}').";
        return summary;
    }

    /// <summary>
    /// Called by the dispatcher when any command starts and when it finishes, so
    /// an active client keeps the open group from idling out, including through
    /// one long command.
    /// </summary>
    internal void KeepUndoGroupAlive()
    {
        if (_undoGroup != null)
            _undoGroup.LastCommandAt = DateTime.UtcNow;
    }

    /// <summary>
    /// Called by the dispatcher just before it opens a mutating command's own
    /// undo record. Drops a group whose record Rhino no longer has open, so the
    /// command gets its own record, and counts the command toward a live group.
    /// </summary>
    internal void NoteMutatingCommandForUndoGroup(RhinoDoc doc)
    {
        var group = LiveUndoGroup();
        if (group != null && doc != null && doc.RuntimeSerialNumber == group.DocSerial)
            group.CommandCount++;
    }

    /// <summary>
    /// Called on Rhino's UI thread after a client's connection closed. Its open
    /// group ends, or every later edit would join that group's undo step.
    /// </summary>
    internal void ClientDisconnected(int connectionId)
    {
        var group = _undoGroup;
        if (group != null && group.OwnerId == connectionId)
            CloseUndoGroup(group, UndoGroupClientDisconnected);
    }

    // undo and redo act on whole records. Inside an open group the newest record
    // is the group's own, still being recorded, so neither can revert one step.
    private void RefuseInsideUndoGroup(string command)
    {
        var group = LiveUndoGroup();
        if (group == null) return;
        throw new McpException(
            McpException.InvalidArgument,
            $"{command} is not available while undo group '{group.Name}' is open{OwnerClause(group)}",
            "Correct the last change with modify_object or delete_object instead. After end_undo_group, one undo reverts the whole group.");
    }

    // The open group, after ending one whose record Rhino no longer has open:
    // its document is gone, or something other than this group ended the record.
    private UndoGroup LiveUndoGroup()
    {
        var group = _undoGroup;
        if (group == null) return null;
        if (RhinoDoc.FromRuntimeSerialNumber(group.DocSerial) == null)
        {
            CloseUndoGroup(group, UndoGroupDocumentClosed);
            return null;
        }
        if (group.Doc.CurrentUndoRecordSerialNumber != group.Record)
        {
            CloseUndoGroup(group, UndoGroupRecordEndedElsewhere);
            return null;
        }
        return group;
    }

    private JObject CloseUndoGroup(UndoGroup group, string reason)
    {
        _undoGroup = null;
        group.IdleTimer.Dispose();
        RhinoDoc.CloseDocument -= OnUndoGroupDocumentClosing;
        RhinoDoc.ActiveDocumentChanged -= OnUndoGroupActiveDocumentChanged;

        // End the record only while Rhino still records into it; a closed
        // document took its undo stack along, and a record ended elsewhere is
        // gone already.
        if (RhinoDoc.FromRuntimeSerialNumber(group.DocSerial) != null
            && group.Doc.CurrentUndoRecordSerialNumber == group.Record)
        {
            group.Doc.EndUndoRecord(group.Record);
        }

        var summary = new JObject
        {
            ["name"] = group.Name,
            ["end_reason"] = reason,
            ["command_count"] = group.CommandCount,
            ["duration_seconds"] = Math.Round((DateTime.UtcNow - group.OpenedAt).TotalSeconds, 1),
        };
        if (reason == UndoGroupRequested)
        {
            RhinoApp.WriteLine($"RhinoMCP: undo group '{group.Name}' ended.");
        }
        else
        {
            string because = UndoGroupEndReasonText(reason, group);
            _undoGroupEndedUnasked = (JObject)summary.DeepClone();
            _undoGroupEndedUnaskedBecause = because;
            RhinoApp.WriteLine($"RhinoMCP: undo group '{group.Name}' ended because {because}.");
        }
        return summary;
    }

    private void CheckUndoGroupIdle(UndoGroup group)
    {
        if (_undoGroup != group) return;
        var idle = DateTime.UtcNow - group.LastCommandAt;
        if (idle >= group.IdleTimeout)
            CloseUndoGroup(group, UndoGroupIdleTimeout);
        else
            group.IdleTimer.Change(group.IdleTimeout - idle, Timeout.InfiniteTimeSpan);
    }

    private void OnUndoGroupDocumentClosing(object sender, DocumentEventArgs e)
    {
        var group = _undoGroup;
        if (group != null && e.DocumentSerialNumber == group.DocSerial)
            CloseUndoGroup(group, UndoGroupDocumentClosed);
    }

    // Commands act on the active document, so after a switch they would edit a
    // document the group does not cover.
    private void OnUndoGroupActiveDocumentChanged(object sender, DocumentEventArgs e)
    {
        var group = _undoGroup;
        if (group != null && e.DocumentSerialNumber != group.DocSerial)
            CloseUndoGroup(group, UndoGroupDocumentChanged);
    }

    private bool OwnedByCaller(UndoGroup group) => group.OwnerId == (CurrentClient?.Id ?? 0);

    private string OwnerClause(UndoGroup group) =>
        OwnedByCaller(group) ? "" : $" (begun by {group.Owner})";

    private static string UndoGroupEndReasonText(string reason, UndoGroup group)
    {
        switch (reason)
        {
            case UndoGroupClientDisconnected:
                return "the client that began it disconnected";
            case UndoGroupIdleTimeout:
                return $"no command arrived for {(int)group.IdleTimeout.TotalSeconds} seconds";
            case UndoGroupDocumentClosed:
                return "its document was closed";
            case UndoGroupDocumentChanged:
                return "another document became active";
            case UndoGroupRecordEndedElsewhere:
                return "Rhino ended its undo record";
            default:
                return reason;
        }
    }

    // One trimmed line, capped, so Rhino's undo list reads "MCP: Build chair frame".
    private static string UndoGroupName(JToken token)
    {
        string line = token?.Type == JTokenType.String ? token.ToString().Trim() : "";
        int newline = line.IndexOfAny(new[] { '\r', '\n' });
        if (newline >= 0)
            line = line.Substring(0, newline).Trim();
        if (line.Length == 0)
            throw McpException.InvalidArgumentError(
                "begin_undo_group needs a name",
                "Pass a short name for the change, for example \"Build chair frame\"; Rhino shows it in the undo list.");
        return line.Length > UndoGroupNameCap ? line.Substring(0, UndoGroupNameCap).TrimEnd() + "…" : line;
    }

    private static int UndoGroupIdleSeconds(JObject parameters)
    {
        var token = parameters["idle_timeout_seconds"];
        if (token == null || token.Type == JTokenType.Null)
            return DefaultUndoGroupIdleSeconds;
        if (token.Type != JTokenType.Integer
            || token.ToObject<long>() < 1
            || token.ToObject<long>() > MaxUndoGroupIdleSeconds)
        {
            throw McpException.InvalidArgumentError(
                $"idle_timeout_seconds must be a whole number from 1 to {MaxUndoGroupIdleSeconds}, got {token}",
                $"Leave it out for the default of {DefaultUndoGroupIdleSeconds} seconds.");
        }
        return token.ToObject<int>();
    }
}
