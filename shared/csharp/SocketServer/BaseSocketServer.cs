using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCP.Shared.SocketServer;

/// <summary>
/// Abstract base class for MCP socket servers.
/// Provides TCP server infrastructure, JSON command parsing, and thread management.
/// Subclasses implement plugin-specific UI thread invocation and command handlers.
/// </summary>
public abstract class BaseSocketServer
{
    protected string host;
    protected int port;
    protected bool running;
    protected TcpListener? listener;
    protected Thread? serverThread;
    protected readonly object lockObject = new object();

    /// <summary>
    /// Name of this server for logging purposes.
    /// </summary>
    public abstract string ServerName { get; }

    /// <summary>
    /// Get the command handler for this server.
    /// </summary>
    public abstract ICommandHandler GetHandler();

    /// <summary>
    /// Invoke an action on the main UI thread.
    /// Different plugins may have different UI thread requirements.
    /// </summary>
    public abstract void InvokeOnMainThread(Action action);

    /// <summary>
    /// Called before a write command executes. Returns an undo record ID.
    /// </summary>
    public abstract uint BeginUndoRecord(string commandName);

    /// <summary>
    /// Called after a command executes to close the undo record.
    /// </summary>
    public abstract void EndUndoRecord(uint recordId);

    /// <summary>
    /// Log a message. Override to customize logging behavior.
    /// </summary>
    protected virtual void Log(string message)
    {
        Log($": {message}");
    }

    protected BaseSocketServer(string host = "127.0.0.1", int port = 1999)
    {
        this.host = host;
        this.port = port;
        this.running = false;
        this.listener = null;
        this.serverThread = null;
    }

    public void Start()
    {
        lock (lockObject)
        {
            if (running)
            {
                Log($" server is already running");
                return;
            }

            running = true;
        }

        try
        {
            IPAddress ipAddress = IPAddress.Parse(host);
            listener = new TcpListener(ipAddress, port);
            listener.Start();

            serverThread = new Thread(ServerLoop);
            serverThread.IsBackground = true;
            serverThread.Start();

            Log($" server started on {host}:{port}");
        }
        catch (Exception e)
        {
            RhinoApp.WriteLine($"Failed to start {ServerName} server: {e.Message}");
            Stop();
        }
    }

    public void Stop()
    {
        lock (lockObject)
        {
            running = false;
        }

        if (listener != null)
        {
            try
            {
                listener.Stop();
            }
            catch
            {
                // Ignore errors on closing
            }
            listener = null;
        }

        if (serverThread != null && serverThread.IsAlive)
        {
            try
            {
                serverThread.Join(1000);
            }
            catch
            {
                // Ignore errors on join
            }
            serverThread = null;
        }

        Log($" server stopped");
    }

    public bool IsRunning()
    {
        lock (lockObject)
        {
            return running;
        }
    }

    private void ServerLoop()
    {
        Log($" server thread started");

        while (IsRunning())
        {
            try
            {
                if (listener == null) break;

                listener.Server.ReceiveTimeout = 1000;
                listener.Server.SendTimeout = 1000;

                if (listener.Pending())
                {
                    TcpClient client = listener.AcceptTcpClient();
                    Log($": Connected to client: {client.Client.RemoteEndPoint}");

                    Thread clientThread = new Thread(() => HandleClient(client));
                    clientThread.IsBackground = true;
                    clientThread.Start();
                }
                else
                {
                    Thread.Sleep(100);
                }
            }
            catch (Exception e)
            {
                Log($": Error in server loop: {e.Message}");

                if (!IsRunning())
                    break;

                Thread.Sleep(500);
            }
        }

        Log($" server thread stopped");
    }

    private void HandleClient(TcpClient client)
    {
        Log($": Client handler started");

        byte[] buffer = new byte[8192];
        string incompleteData = string.Empty;

        try
        {
            NetworkStream stream = client.GetStream();

            while (IsRunning())
            {
                try
                {
                    if (client.Available > 0 || stream.DataAvailable)
                    {
                        int bytesRead = stream.Read(buffer, 0, buffer.Length);
                        if (bytesRead == 0)
                        {
                            Log($": Client disconnected");
                            break;
                        }

                        string data = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                        incompleteData += data;

                        try
                        {
                            JObject command = JObject.Parse(incompleteData);
                            incompleteData = string.Empty;

                            InvokeOnMainThread(() =>
                            {
                                try
                                {
                                    JObject response = ExecuteCommand(command);
                                    string responseJson = JsonConvert.SerializeObject(response);

                                    try
                                    {
                                        byte[] responseBytes = Encoding.UTF8.GetBytes(responseJson);
                                        stream.Write(responseBytes, 0, responseBytes.Length);
                                    }
                                    catch
                                    {
                                        Log($": Failed to send response - client disconnected");
                                    }
                                }
                                catch (Exception e)
                                {
                                    Log($": Error executing command: {e.Message}");
                                    try
                                    {
                                        JObject errorResponse = new JObject
                                        {
                                            ["status"] = "error",
                                            ["message"] = e.Message
                                        };

                                        byte[] errorBytes = Encoding.UTF8.GetBytes(errorResponse.ToString());
                                        stream.Write(errorBytes, 0, errorBytes.Length);
                                    }
                                    catch
                                    {
                                        // Ignore send errors
                                    }
                                }
                            });
                        }
                        catch (JsonException)
                        {
                            // Incomplete JSON data, wait for more
                        }
                    }
                    else
                    {
                        Thread.Sleep(50);
                    }
                }
                catch (Exception e)
                {
                    Log($": Error receiving data: {e.Message}");
                    break;
                }
            }
        }
        catch (Exception e)
        {
            Log($": Error in client handler: {e.Message}");
        }
        finally
        {
            try
            {
                client.Close();
            }
            catch
            {
                // Ignore errors on close
            }
            Log($": Client handler stopped");
        }
    }

    private JObject ExecuteCommand(JObject command)
    {
        try
        {
            string? cmdType = command["type"]?.ToString();
            JObject parameters = command["params"] as JObject ?? new JObject();

            if (string.IsNullOrEmpty(cmdType))
            {
                return new JObject
                {
                    ["status"] = "error",
                    ["message"] = "Command type is required"
                };
            }

            Log($": Executing command: {cmdType}");

            var handler = GetHandler();
            var handlers = handler.GetHandlers();
            var readOnlyCommands = handler.GetReadOnlyCommands();

            if (handlers.TryGetValue(cmdType, out var handlerFunc))
            {
                bool needsUndo = !readOnlyCommands.Contains(cmdType);
                uint record = 0;

                if (needsUndo)
                {
                    record = BeginUndoRecord($"MCP: {cmdType}");
                }

                try
                {
                    JObject result = handlerFunc(parameters);
                    Log($": Command execution complete");
                    return new JObject
                    {
                        ["status"] = "success",
                        ["result"] = result
                    };
                }
                catch (Exception e)
                {
                    Log($": Error in handler: {e.Message}");
                    return new JObject
                    {
                        ["status"] = "error",
                        ["message"] = e.Message
                    };
                }
                finally
                {
                    if (needsUndo)
                    {
                        EndUndoRecord(record);
                    }
                }
            }
            else
            {
                return new JObject
                {
                    ["status"] = "error",
                    ["message"] = $"Unknown command type: {cmdType}"
                };
            }
        }
        catch (Exception e)
        {
            Log($": Error executing command: {e.Message}");
            return new JObject
            {
                ["status"] = "error",
                ["message"] = e.Message
            };
        }
    }
}
