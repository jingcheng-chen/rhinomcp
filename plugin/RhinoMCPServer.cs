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
        // Wire framing: a 4-byte big-endian length header followed by UTF-8
        // JSON, in both directions. Legacy (pre-framing) clients send bare
        // JSON instead; the first byte of a connection decides which protocol
        // that connection speaks. The size cap bounds memory per frame and
        // keeps the header's first byte below any byte a legacy client could
        // open with ('{' or whitespace), so the sniff is unambiguous.
        private const int FrameHeaderSize = 4;
        private const int MaxFrameSize = 64 * 1024 * 1024;

        private enum ClientProtocol
        {
            Undecided,
            Framed,
            Legacy
        }

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
            var pending = new List<byte>();
            ClientProtocol protocol = ClientProtocol.Undecided;

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

                            for (int i = 0; i < bytesRead; i++)
                            {
                                pending.Add(buffer[i]);
                            }

                            if (protocol == ClientProtocol.Undecided)
                            {
                                protocol = SniffProtocol(pending[0]);
                            }

                            if (protocol == ClientProtocol.Framed)
                            {
                                // Drain every complete frame in the buffer so
                                // pipelined commands all execute in order
                                // instead of wedging the connection.
                                while (TryExtractFrame(pending, out string framedJson))
                                {
                                    JObject framedCommand;
                                    try
                                    {
                                        framedCommand = JObject.Parse(framedJson);
                                    }
                                    catch (JsonException ex)
                                    {
                                        // The frame was well-formed (its length
                                        // matched) but the payload isn't valid
                                        // JSON. Framing already located the next
                                        // frame, so answer this one with an error
                                        // and keep the connection instead of
                                        // dropping every command queued behind it.
                                        // Routed through the UI thread like every
                                        // other write so responses stay
                                        // single-writer and in send order.
                                        string detail = ex.Message;
                                        RhinoApp.InvokeOnUiThread(new Action(() =>
                                        {
                                            try
                                            {
                                                WriteMessage(stream, new JObject
                                                {
                                                    ["status"] = "error",
                                                    ["message"] = $"Invalid JSON in framed message: {detail}"
                                                }.ToString(), framed: true);
                                            }
                                            catch
                                            {
                                                RhinoApp.WriteLine("Failed to send error response - client disconnected");
                                            }
                                        }));
                                        continue;
                                    }
                                    DispatchCommand(framedCommand, stream, framed: true);
                                }
                            }
                            else
                            {
                                // Legacy client: bare JSON, no framing. Keep
                                // the original semantics: try to parse the
                                // whole accumulation, wait for more on failure.
                                string incompleteData = Encoding.UTF8.GetString(pending.ToArray());
                                try
                                {
                                    JObject command = JObject.Parse(incompleteData);
                                    pending.Clear();
                                    DispatchCommand(command, stream, framed: false);
                                }
                                catch (JsonException)
                                {
                                    // Incomplete JSON data, wait for more
                                }
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

        private static ClientProtocol SniffProtocol(byte firstByte)
        {
            // Legacy clients open with bare JSON: '{', possibly preceded by
            // whitespace. A frame header's first byte is the high byte of the
            // message length, which MaxFrameSize caps at 0x04 — below '{'
            // (0x7B) and every whitespace byte (0x09, 0x0A, 0x0D, 0x20).
            if (firstByte == (byte)'{' || firstByte == (byte)' ' ||
                firstByte == (byte)'\t' || firstByte == (byte)'\r' ||
                firstByte == (byte)'\n')
            {
                return ClientProtocol.Legacy;
            }
            return ClientProtocol.Framed;
        }

        private static bool TryExtractFrame(List<byte> pending, out string payloadJson)
        {
            // Frame de-chunking only: pulls the bytes of one complete frame off
            // the buffer and returns them as a string. JSON parsing happens in
            // the caller, on purpose — a well-framed message whose payload is
            // bad JSON should be a per-message error, not a dropped connection,
            // and that's only recoverable once the frame bytes are consumed.
            payloadJson = null;
            if (pending.Count < FrameHeaderSize) return false;

            int frameLength = (pending[0] << 24) | (pending[1] << 16) |
                              (pending[2] << 8) | pending[3];
            if (frameLength <= 0 || frameLength > MaxFrameSize)
            {
                // A bad length means framing sync is lost: we can't tell where
                // the next frame starts, so this one stays fatal. The caller
                // logs and drops the connection.
                throw new InvalidOperationException(
                    $"Invalid frame length {frameLength} (limit {MaxFrameSize} bytes)");
            }

            if (pending.Count < FrameHeaderSize + frameLength) return false;

            payloadJson = Encoding.UTF8.GetString(
                pending.GetRange(FrameHeaderSize, frameLength).ToArray());
            pending.RemoveRange(0, FrameHeaderSize + frameLength);
            return true;
        }

        private void DispatchCommand(JObject command, NetworkStream stream, bool framed)
        {
            // Execute command on Rhino's main thread. Posts are processed in
            // order, so pipelined framed commands get their responses in the
            // order the commands were sent.
            RhinoApp.InvokeOnUiThread(new Action(() =>
            {
                try
                {
                    JObject response = ExecuteCommand(command);
                    string responseJson = JsonConvert.SerializeObject(response);

                    try
                    {
                        WriteMessage(stream, responseJson, framed);
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

                        WriteMessage(stream, errorResponse.ToString(), framed);
                    }
                    catch
                    {
                        // Ignore send errors
                    }
                }
            }));
        }

        private static void WriteMessage(NetworkStream stream, string json, bool framed)
        {
            byte[] payload = Encoding.UTF8.GetBytes(json);
            if (!framed)
            {
                stream.Write(payload, 0, payload.Length);
                return;
            }

            // One write for header + payload keeps the frame contiguous.
            byte[] message = new byte[FrameHeaderSize + payload.Length];
            message[0] = (byte)((payload.Length >> 24) & 0xFF);
            message[1] = (byte)((payload.Length >> 16) & 0xFF);
            message[2] = (byte)((payload.Length >> 8) & 0xFF);
            message[3] = (byte)(payload.Length & 0xFF);
            Buffer.BlockCopy(payload, 0, message, FrameHeaderSize, payload.Length);
            stream.Write(message, 0, message.Length);
        }

        private JObject ExecuteCommand(JObject command)
        {
            try
            {
                string cmdType = command["type"]?.ToString();
                JObject parameters = command["params"] as JObject ?? new JObject();
                // Opt-in perception flag, carried on the envelope (not in params)
                // so it never collides with a command's own parameters. Defaults
                // off, so behavior is unchanged unless a client asks for it.
                bool includeDelta = command["include_delta"]?.ToObject<bool>() ?? false;

                RhinoApp.WriteLine($"Executing command: {cmdType}");

                JObject result = ExecuteCommandInternal(cmdType, parameters, includeDelta);

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

        private JObject ExecuteCommandInternal(string cmdType, JObject parameters, bool includeDelta)
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

            // A change-delta only makes sense for a mutating command, and only
            // when the client asked for it. Snapshot the document's object ids
            // just before the handler runs so we can diff against the post-state.
            // This is the one place every mutator funnels through, so it covers
            // them all (including multi-effect ones like run_command and booleans
            // with delete_sources) with no per-handler changes.
            bool wantDelta = includeDelta && needsUndo && doc != null;
            HashSet<Guid> idsBefore = wantDelta ? this.handler.SnapshotObjectIds(doc) : null;

            uint record = 0;
            if (needsUndo)
            {
                record = doc.BeginUndoRecord($"MCP: {cmdType}");
            }

            try
            {
                JObject result = entry.Handler(parameters);
                if (wantDelta && result != null)
                {
                    result["_delta"] = this.handler.BuildDelta(
                        idsBefore, this.handler.SnapshotObjectIds(doc));
                }
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