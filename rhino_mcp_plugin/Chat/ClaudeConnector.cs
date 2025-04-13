using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Threading;
using System.Threading.Tasks;
using System;

namespace RhinoMCPPlugin.Chat;

public class ClaudeConnector : IDisposable
{
    private NamedPipeClientStream _pipeClient;
    private StreamWriter _writer;
    private StreamReader _reader;
    private bool _disposed;

    public ClaudeConnector(string apiKey)
    {
        // StartAppInPipeMode();
        _pipeClient = new NamedPipeClientStream(".", "rhino-mcp-client-pipe", PipeDirection.InOut);
        SendMessageViaPipe("handshake");
    }

    private bool IsAppRunning()
    {
        Process[] processes = Process.GetProcessesByName("rhino_mcp_client");
        return processes.Length > 0;
    }

    // Start the standalone app in pipe server mode
    private void StartAppInPipeMode()
    {
        var process = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = "rhino_mcp_client",
                UseShellExecute = false,
                CreateNoWindow = true      // Run hidden (no console window)
            }
        };

        process.Start();

        // Give the process a moment to initialize
        Thread.Sleep(500);
    }

    private void EnsureConnected()
    {
        if (_pipeClient.IsConnected) return;

        // Start the process if not already running
        // if (!IsAppRunning())
        //     StartAppInPipeMode();

        _pipeClient.Connect(5000); // Wait up to 5 seconds

        _writer = new StreamWriter(_pipeClient) { AutoFlush = true };
        _reader = new StreamReader(_pipeClient);
    }

    private async Task<string> SendMessageViaPipe(string message)
    {
        EnsureConnected();

        // Send message
        await _writer.WriteLineAsync(message);

        // Read response until end marker
        var response = new System.Text.StringBuilder();
        string? line;
        while ((line = await _reader.ReadLineAsync()) != null)
        {
            if (line == "<<END_OF_MESSAGE>>")
                break;

            if (response.Length > 0)
                response.AppendLine();
            response.Append(line);
        }

        return response.ToString();
    }

    public async Task<string> SetApiKey(string apiKey)
    {
        return await SendMessageViaPipe($"apiKey:{apiKey}");
    }

    public async Task<string> SendMessage(string message)
    {
        return await SendMessageViaPipe($"claude:{message}");
    }

    public async Task<string> ClearHistory()
    {
        return await SendMessageViaPipe("claude_clear_history");
    }

    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (_disposed) return;

        if (disposing)
        {
            _writer?.Dispose();
            _reader?.Dispose();
            _pipeClient?.Dispose();
        }

        _disposed = true;
    }

    ~ClaudeConnector()
    {
        Dispose(false);
    }
}