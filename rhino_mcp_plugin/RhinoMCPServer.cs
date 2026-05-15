using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Rhino;
using Rhino.Commands;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;
using Rhino.UI;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Rhino.DocObjects;
using rhinomcp.Serializers;
using JsonException = Newtonsoft.Json.JsonException;
using Eto.Forms;
using RhinoMCPPlugin.Functions;

namespace RhinoMCPPlugin
{
    public class RhinoMCPServer
    {
        private string host;
        private int port;
        private bool running;
        private TcpListener listener;
        private Thread serverThread;
        private readonly object lockObject = new object();
        private RhinoMCPFunctions handler;

        public RhinoMCPServer(string host = "127.0.0.1", int port = 1999)
        {
            this.host = host;
            this.port = port;
            this.running = false;
            this.listener = null;
            this.serverThread = null;
            this.handler = new RhinoMCPFunctions();
        }


        public void Start()
        {
            lock (lockObject)
            {
                if (running)
                {
                    RhinoApp.WriteLine("Server is already running");
                    return;
                }

                running = true;
            }

            try
            {
                // Create TCP listener
                IPAddress ipAddress = IPAddress.Parse(host);
                listener = new TcpListener(ipAddress, port);
                listener.Start();

                // Start server thread
                serverThread = new Thread(ServerLoop);
                serverThread.IsBackground = true;
                serverThread.Start();

                RhinoApp.WriteLine($"RhinoMCP server started on {host}:{port}");
            }
            catch (Exception e)
            {
                RhinoApp.WriteLine($"Failed to start server: {e.Message}");
                Stop();
            }
        }

        public void Stop()
        {
            lock (lockObject)
            {
                running = false;
            }

            // Close listener
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

            // Wait for thread to finish
            if (serverThread != null && serverThread.IsAlive)
            {
                try
                {
                    serverThread.Join(1000); // Wait up to 1 second
                }
                catch
                {
                    // Ignore errors on join
                }
                serverThread = null;
            }

            RhinoApp.WriteLine("RhinoMCP server stopped");
        }

        private void ServerLoop()
        {
            RhinoApp.WriteLine("Server thread started");

            while (IsRunning())
            {
                try
                {
                    // Blocking accept; Stop() calls listener.Stop() which throws
                    // ObjectDisposedException or a SocketException(Interrupted),
                    // unblocking us cleanly instead of polling+sleeping.
                    TcpClient client = listener.AcceptTcpClient();
                    RhinoApp.WriteLine($"Connected to client: {client.Client.RemoteEndPoint}");

                    Thread clientThread = new Thread(() => HandleClient(client));
                    clientThread.IsBackground = true;
                    clientThread.Start();
                }
                catch (ObjectDisposedException)
                {
                    break;
                }
                catch (SocketException ex) when (!IsRunning() || ex.SocketErrorCode == SocketError.Interrupted)
                {
                    break;
                }
                catch (Exception e)
                {
                    RhinoApp.WriteLine($"Error in server loop: {e.Message}");
                    if (!IsRunning()) break;
                    Thread.Sleep(500);
                }
            }

            RhinoApp.WriteLine("Server thread stopped");
        }

        public bool IsRunning()
        {
            lock (lockObject)
            {
                return running;
            }
        }

        private void HandleClient(TcpClient client)
        {
            RhinoApp.WriteLine("Client handler started");

            byte[] buffer = new byte[8192];
            string incompleteData = string.Empty;

            try
            {
                NetworkStream stream = client.GetStream();

                while (IsRunning())
                {
                    try
                    {
                        // Check if there's data available to read
                        if (client.Available > 0 || stream.DataAvailable)
                        {
                            int bytesRead = stream.Read(buffer, 0, buffer.Length);
                            if (bytesRead == 0)
                            {
                                RhinoApp.WriteLine("Client disconnected");
                                break;
                            }

                            string data = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                            incompleteData += data;

                            try
                            {
                                // Try to parse as JSON
                                JObject command = JObject.Parse(incompleteData);
                                incompleteData = string.Empty;

                                // Execute command on Rhino's main thread
                                RhinoApp.InvokeOnUiThread(new Action(() =>
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
                                            RhinoApp.WriteLine("Failed to send response - client disconnected");
                                        }
                                    }
                                    catch (Exception e)
                                    {
                                        RhinoApp.WriteLine($"Error executing command: {e.Message}");
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
                                }));
                            }
                            catch (JsonException)
                            {
                                // Incomplete JSON data, wait for more
                            }
                        }
                        else
                        {
                            // No data available, sleep a bit to prevent CPU overuse
                            Thread.Sleep(50);
                        }
                    }
                    catch (Exception e)
                    {
                        RhinoApp.WriteLine($"Error receiving data: {e.Message}");
                        break;
                    }
                }
            }
            catch (Exception e)
            {
                RhinoApp.WriteLine($"Error in client handler: {e.Message}");
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
                RhinoApp.WriteLine("Client handler stopped");
            }
        }

        private JObject ExecuteCommand(JObject command)
        {
            try
            {
                string cmdType = command["type"]?.ToString();
                JObject parameters = command["params"] as JObject ?? new JObject();

                RhinoApp.WriteLine($"Executing command: {cmdType}");

                JObject result = ExecuteCommandInternal(cmdType, parameters);

                RhinoApp.WriteLine("Command execution complete");
                return result;
            }
            catch (Exception e)
            {
                RhinoApp.WriteLine($"Error executing command: {e.Message}");
                return new JObject
                {
                    ["status"] = "error",
                    ["message"] = e.Message
                };
            }
        }

        private JObject ExecuteCommandInternal(string cmdType, JObject parameters)
        {
            // Reflection-discovered dispatch table — see Functions/_Registry.cs.
            // Adding a new command means adding a [McpCommand("name")] method on
            // RhinoMCPFunctions; no edits to this file are required.
            var dispatch = this.handler.GetDispatchTable();

            if (!dispatch.TryGetValue(cmdType, out var entry))
            {
                return new JObject
                {
                    ["status"] = "error",
                    ["message"] = $"Unknown command type: {cmdType}"
                };
            }

            var doc = RhinoDoc.ActiveDoc;
            bool needsUndo = !entry.ReadOnly;
            uint record = 0;
            if (needsUndo)
            {
                record = doc.BeginUndoRecord($"MCP: {cmdType}");
            }

            try
            {
                JObject result = entry.Handler(parameters);
                return new JObject
                {
                    ["status"] = "success",
                    ["result"] = result
                };
            }
            catch (Exception e)
            {
                RhinoApp.WriteLine($"Error in handler: {e.Message}");
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
                    doc.EndUndoRecord(record);
                }
            }
        }
    }
}