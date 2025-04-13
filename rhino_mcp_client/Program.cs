using System;
using System.IO;
using System.IO.Pipes;
using RhinoMCPClient;
using System.Threading.Tasks;


var server = new NamedPipeServerStream("rhino-mcp-client-pipe", PipeDirection.InOut);
Console.WriteLine("Pipe server started. Waiting for connection...");
string _apiKey = string.Empty;
Claude? _claude = null;


while (true)
{
    await server.WaitForConnectionAsync();

    StreamReader reader = new StreamReader(server);
    StreamWriter writer = new StreamWriter(server) { AutoFlush = true };

    try
    {
        while (server.IsConnected)
        {
            // Read request
            string? message = await reader.ReadLineAsync();
            if (message == null)
            {
                await writer.WriteLineAsync("Invalid message received");
                continue;
            }

            // Process and send response
            string response = await ProcessMessage(message);
            await writer.WriteAsync(response);
            await writer.WriteLineAsync("\n<<END_OF_MESSAGE>>");
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Error handling connection: {ex.Message}");
    }
    finally
    {
        reader.Dispose();
        writer.Dispose();
        if (server.IsConnected)
        {
            server.Disconnect();
        }
    }
}

async Task<string> ProcessMessage(string message)
{

    if (message == "handshake")
    {
        return "Successfully started MCP client";
    }
    else if (message.StartsWith("apiKey:"))
    {
        _apiKey = message.Substring("apiKey:".Length);
        _claude = new Claude(_apiKey);
        return _claude.IsConnected ? "Connected to Claude" : "Failed to connect to Claude";
    }
    else if (message.StartsWith("claude:"))
    {
        if (string.IsNullOrEmpty(_apiKey))
        {
            return "No API key provided";
        }
        if (_claude == null || !_claude.IsConnected)
        {
            return "Not connected to Claude";
        }
        var response = await _claude.MessageAsync(message.Substring("claude:".Length));
        return response ?? "No response from Claude";
    }
    else if (message == "claude_clear_history")
    {
        if (_claude == null || !_claude.IsConnected)
        {
            return "Not connected to Claude";
        }
        _claude.ClearHistory();
        return "History cleared";
    }

    return "Unknown command";
}