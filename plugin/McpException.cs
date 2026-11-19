using System;

namespace RhinoMCPPlugin;

/// <summary>
/// A handler failure that carries a machine-readable code (see errorResponse in
/// contracts/protocol.json) and one sentence of guidance. The dispatcher copies
/// both into the error reply; any other exception is reported with its message
/// only, so handlers can move to coded errors one at a time.
/// </summary>
public sealed class McpException : InvalidOperationException
{
    public const string InvalidArgument = "invalid_argument";
    public const string NotFound = "not_found";
    public const string RhinoError = "rhino_error";

    public string Code { get; }
    public string Guidance { get; }

    public McpException(string code, string message, string guidance = null) : base(message)
    {
        Code = code;
        Guidance = guidance;
    }

    public static McpException ObjectNotFound(string idOrName) => new McpException(
        NotFound,
        $"Object not found: {idOrName}",
        "Call get_objects or get_selected_objects_info to find a valid object id or name.");

    public static McpException LayerNotFound(string nameOrId) => new McpException(
        NotFound,
        $"Layer '{nameOrId}' not found",
        "Call get_document_summary to list existing layers, or create_layer to make it first.");

    public static McpException InvalidGuid(string text) => new McpException(
        InvalidArgument,
        $"Invalid GUID '{text}'",
        "Pass an id exactly as get_objects returns it, for example 12345678-1234-1234-1234-123456789012.");

    /// <summary>An invalid_argument error, for example a number outside its allowed range.</summary>
    public static McpException InvalidArgumentError(string message, string guidance) =>
        new McpException(InvalidArgument, message, guidance);

    /// <summary>Parse a GUID or throw invalid_argument.</summary>
    public static Guid ParseGuid(string text)
    {
        if (!Guid.TryParse(text, out var guid))
            throw InvalidGuid(text);
        return guid;
    }
}
