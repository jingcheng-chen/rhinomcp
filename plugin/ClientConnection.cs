using System;
using System.Net;
using System.Net.Sockets;
using System.Threading;

namespace RhinoMCPPlugin
{
    /// <summary>
    /// One open MCP client connection, as shown by mcpstatus and the status window.
    /// </summary>
    public class ClientConnection
    {
        private int commandCount;
        private volatile string lastCommand;
        private long lastCommandTicks;
        private volatile string description;

        public ClientConnection(int id, TcpClient tcp)
        {
            Id = id;
            Tcp = tcp;
            ConnectedAt = DateTime.Now;
            try
            {
                RemoteEndPoint = tcp.Client.RemoteEndPoint as IPEndPoint;
            }
            catch (ObjectDisposedException)
            {
                // Closed before we looked; the handler removes it right away.
            }
        }

        public int Id { get; }
        public TcpClient Tcp { get; }
        public IPEndPoint RemoteEndPoint { get; }
        public DateTime ConnectedAt { get; }
        public int CommandCount => Volatile.Read(ref commandCount);
        public string LastCommand => lastCommand;
        public DateTime? LastCommandAt
        {
            get
            {
                long ticks = Interlocked.Read(ref lastCommandTicks);
                return ticks == 0 ? (DateTime?)null : new DateTime(ticks, DateTimeKind.Local);
            }
        }

        /// <summary>Who is on the other end ("Claude Code · project (PID n)"),
        /// or the endpoint until/unless ClientIdentity can tell.</summary>
        public string Description
        {
            get => description ?? RemoteEndPoint?.ToString() ?? $"#{Id}";
            set => description = value;
        }

        public void RecordCommand(string commandType)
        {
            Interlocked.Increment(ref commandCount);
            lastCommand = commandType;
            Interlocked.Exchange(ref lastCommandTicks, DateTime.Now.Ticks);
        }
    }
}
