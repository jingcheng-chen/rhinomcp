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
/// A group belongs to the client that began it. A client that sends a session
/// token on the command envelope (the rhinomcp server does, one per process)
/// owns it by that token, so the group survives the reconnect that follows a
/// timeout or a dropped socket. A client that sends none owns it by its
/// connection, and the group ends when that connection closes.
///
/// A record left open would fold every later edit into one stale undo step, so
/// a group also ends when its owner sends no command for the idle timeout
/// (other clients' commands do not count), and when its document closes or
/// another document becomes active. Any client can end it with force=true.
/// When a group ends without its owner asking, the owner's next mutating
/// command carries an _undo_group notice saying so.
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
    private const string UndoGroupForced = "forced";
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
        // Session token of the client that began the group, or null when it sent
        // none; then the connection id owns it (0 for a direct call, mcptest).
        public string OwnerSession;
        public int OwnerConnectionId;
        public string Owner;
        public TimeSpan IdleTimeout;
        public DateTime OpenedAt;
        public DateTime LastCommandAt;
        public int CommandCount;
        public Timer IdleTimer;
        // Set when the group ends.
        public string EndReason;
        public DateTime EndedAt;
        // The owner has been told the group ended without its asking.
        public bool OwnerTold;
    }

    private UndoGroup _undoGroup;
    // The last group that ended without its owner's end_undo_group, reported to
    // the owner's next mutating command and to the next end_undo_group that
    // finds no group open.
    private UndoGroup _undoGroupEndedUnasked;

    /// <summary>
    /// The connection whose command is running, or null for a direct call
    /// (mcptest). The dispatcher sets it around each command.
    /// </summary>
    internal ClientConnection CurrentClient { get; set; }

    /// <summary>
    /// The session token on the running command's envelope, or null. The
    /// dispatcher sets it around each command.
    /// </summary>
    internal string CurrentSession { get; set; }

    // ManagesUndo: the dispatcher must not wrap this command in its own record,
    // or Rhino would decline the group's record inside it.
    [McpCommand("begin_undo_group", ManagesUndo = true)]
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
                    : $"Undo groups do not nest. That group ends when its client ends it, or after {(int)open.IdleTimeout.TotalSeconds} seconds without commands from that client; end_undo_group with force=true ends it now.");
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
            OwnerSession = string.IsNullOrEmpty(CurrentSession) ? null : CurrentSession,
            OwnerConnectionId = client?.Id ?? 0,
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

    [McpCommand("end_undo_group", ManagesUndo = true)]
    public JObject EndUndoGroup(JObject parameters)
    {
        bool force = parameters["force"]?.Type == JTokenType.Boolean && parameters["force"].ToObject<bool>();
        var group = LiveUndoGroup();
        if (group == null)
        {
            var none = new JObject { ["ended"] = false, ["message"] = "No undo group is open." };
            var last = _undoGroupEndedUnasked;
            if (last != null)
            {
                if (OwnedByCaller(last)) last.OwnerTold = true;
                none["last_group"] = UndoGroupSummary(last);
                none["message"] = $"No undo group is open. '{last.Name}' already ended because "
                    + $"{UndoGroupEndReasonText(last)}; changes made after that have their own undo steps.";
            }
            return none;
        }

        bool owned = OwnedByCaller(group);
        if (!owned && !force)
        {
            throw new McpException(
                McpException.InvalidArgument,
                $"Undo group '{group.Name}' was begun by another client ({group.Owner})",
                $"That client ends it, or it ends after {(int)group.IdleTimeout.TotalSeconds} seconds without commands from that client. "
                + "If that client is gone, call end_undo_group with force=true.");
        }

        var summary = CloseUndoGroup(group, owned ? UndoGroupRequested : UndoGroupForced);
        summary.AddFirst(new JProperty("ended", true));
        summary["message"] = $"Undo group '{group.Name}' ended: one Undo reverts its changes ('MCP: {group.Name}').";
        return summary;
    }

    /// <summary>
    /// Called by the dispatcher when any command starts and when it finishes, so
    /// an active owner keeps its open group from idling out, including through
    /// one long command. Other clients' commands do not keep it alive.
    /// </summary>
    internal void KeepUndoGroupAlive()
    {
        var group = _undoGroup;
        if (group != null && OwnedByCaller(group))
            group.LastCommandAt = DateTime.UtcNow;
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
    /// Called by the dispatcher after a mutating command succeeded. If the
    /// caller's group ended without its asking and the caller has not been told,
    /// the result says so: this command and the ones before it since the group
    /// ended have their own undo steps.
    /// </summary>
    internal void AttachUndoGroupNotice(JObject result)
    {
        var last = _undoGroupEndedUnasked;
        if (result == null || last == null || last.OwnerTold || !OwnedByCaller(last))
            return;
        last.OwnerTold = true;
        var notice = UndoGroupSummary(last);
        notice["message"] = $"Undo group '{last.Name}' ended because {UndoGroupEndReasonText(last)}; "
            + "changes since then, this one included, have their own undo steps. "
            + "Call begin_undo_group again to group what follows.";
        result["_undo_group"] = notice;
    }

    /// <summary>
    /// Called on Rhino's UI thread after a client's connection closed. A group
    /// that connection owns ends, or every later edit would join its undo step.
    /// A group owned by a session token stays open: the same client reconnects
    /// after a timeout, and the idle timeout ends it if the client is gone.
    /// </summary>
    internal void ClientDisconnected(int connectionId)
    {
        var group = _undoGroup;
        if (group != null && group.OwnerSession == null && group.OwnerConnectionId == connectionId)
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
            OwnedByCaller(group)
                ? "Correct the last change with modify_object or delete_object instead. After end_undo_group, one undo reverts the whole group."
                : "Wait for that client to end the group, or call end_undo_group with force=true if that client is gone.");
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

        group.EndReason = reason;
        group.EndedAt = DateTime.UtcNow;
        if (reason == UndoGroupRequested)
        {
            RhinoApp.WriteLine($"RhinoMCP: undo group '{group.Name}' ended.");
        }
        else
        {
            _undoGroupEndedUnasked = group;
            RhinoApp.WriteLine($"RhinoMCP: undo group '{group.Name}' ended because {UndoGroupEndReasonText(group)}.");
        }
        return UndoGroupSummary(group);
    }

    private static JObject UndoGroupSummary(UndoGroup group) => new JObject
    {
        ["name"] = group.Name,
        ["end_reason"] = group.EndReason,
        ["command_count"] = group.CommandCount,
        ["duration_seconds"] = Math.Round((group.EndedAt - group.OpenedAt).TotalSeconds, 1),
    };

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

    private bool OwnedByCaller(UndoGroup group) =>
        group.OwnerSession != null
            ? string.Equals(group.OwnerSession, CurrentSession, StringComparison.Ordinal)
            : CurrentSession == null && group.OwnerConnectionId == (CurrentClient?.Id ?? 0);

    private string OwnerClause(UndoGroup group) =>
        OwnedByCaller(group) ? "" : $" (begun by {group.Owner})";

    private static string UndoGroupEndReasonText(UndoGroup group)
    {
        switch (group.EndReason)
        {
            case UndoGroupForced:
                return "another client ended it with force=true";
            case UndoGroupClientDisconnected:
                return "the client that began it disconnected";
            case UndoGroupIdleTimeout:
                return $"no command arrived from its client for {(int)group.IdleTimeout.TotalSeconds} seconds";
            case UndoGroupDocumentClosed:
                return "its document was closed";
            case UndoGroupDocumentChanged:
                return "another document became active";
            case UndoGroupRecordEndedElsewhere:
                return "Rhino ended its undo record";
            default:
                return group.EndReason;
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
        long seconds = token.Type == JTokenType.Integer ? token.ToObject<long>() : 0;
        if (seconds < 1 || seconds > MaxUndoGroupIdleSeconds)
        {
            throw McpException.InvalidArgumentError(
                $"idle_timeout_seconds must be a whole number from 1 to {MaxUndoGroupIdleSeconds}, got {token}",
                $"Leave it out for the default of {DefaultUndoGroupIdleSeconds} seconds.");
        }
        return (int)seconds;
    }
}
