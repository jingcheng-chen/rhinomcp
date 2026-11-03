using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

namespace RhinoMCPTray
{
    /// <summary>One Rhino running a RhinoMCP server, as written by the plug-in.</summary>
    class RhinoInstance
    {
        public int Pid;
        public int Port;
        public DateTime StartedAt;
        public string PortSource;
        /// <summary>Rhino's UI language, e.g. "it-IT".</summary>
        public string Language;
        public string Document;
        /// <summary>null = Grasshopper not loaded, "" = loaded without a definition.</summary>
        public string Grasshopper;
        public List<ClientInfo> Clients = new List<ClientInfo>();
        /// <summary>Claude Code MCP entries (~/.claude.json) that talk to this port.</summary>
        public IReadOnlyList<string> McpEntries = Array.Empty<string>();
    }

    class ClientInfo
    {
        public string App;
        public string Folder;
        public DateTime ConnectedAt;
        public int Commands;
        public string LastCommand;
        public DateTime? LastCommandAt;

        // ClientIdentity on the plug-in side writes "App · folder (PID n)".
        private static readonly Regex DescriptionPattern =
            new Regex(@"^(?<app>.+?)(?: · (?<folder>.+?))?(?: \(PID \d+\))?$", RegexOptions.CultureInvariant);

        public static ClientInfo Parse(string description)
        {
            var match = DescriptionPattern.Match(description ?? "");
            return new ClientInfo
            {
                App = match.Success ? match.Groups["app"].Value : description,
                Folder = match.Success && match.Groups["folder"].Success ? match.Groups["folder"].Value : null,
            };
        }
    }

    static class InstanceDirectory
    {
        public static string Folder => Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RhinoMCP", "instances");

        private static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };

        /// <summary>Running instances sorted by port. Files left by a Rhino that is
        /// gone (crash, killed) are deleted.</summary>
        public static List<RhinoInstance> Read()
        {
            var result = new List<RhinoInstance>();
            if (!Directory.Exists(Folder)) return result;

            foreach (string file in Directory.GetFiles(Folder, "*.json"))
            {
                Dictionary<string, object> data;
                try
                {
                    data = Json.DeserializeObject(File.ReadAllText(file)) as Dictionary<string, object>;
                }
                catch (Exception)
                {
                    continue; // Being rewritten right now.
                }
                if (data == null) continue;

                int pid = Int(data, "pid");
                if (!IsAlive(pid, Str(data, "processStart")))
                {
                    TryDelete(file);
                    continue;
                }

                var instance = new RhinoInstance
                {
                    Pid = pid,
                    Port = Int(data, "port"),
                    StartedAt = Date(data, "startedAt") ?? DateTime.Now,
                    PortSource = Str(data, "portSource"),
                    Language = Str(data, "language"),
                    Document = Str(data, "document"),
                    Grasshopper = Str(data, "grasshopper"),
                    McpEntries = ClaudeConfig.EntriesFor(Int(data, "port")),
                };
                if (data.TryGetValue("clients", out object clients) && clients is object[] list)
                {
                    foreach (var item in list.OfType<Dictionary<string, object>>())
                    {
                        var client = ClientInfo.Parse(Str(item, "description"));
                        client.ConnectedAt = Date(item, "connectedAt") ?? DateTime.Now;
                        client.Commands = Int(item, "commands");
                        client.LastCommand = Str(item, "lastCommand");
                        client.LastCommandAt = Date(item, "lastCommandAt");
                        instance.Clients.Add(client);
                    }
                }
                result.Add(instance);
            }
            return result.OrderBy(i => i.Port).ToList();
        }

        private static bool IsAlive(int pid, string processStart)
        {
            if (pid <= 0) return false;
            try
            {
                using (var process = Process.GetProcessById(pid))
                {
                    if (process.HasExited) return false;
                    if (!DateTime.TryParse(processStart, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind, out DateTime start))
                        return true;
                    // Same PID reused by another process after Rhino exited?
                    return Math.Abs((process.StartTime.ToUniversalTime() - start.ToUniversalTime()).TotalSeconds) < 2;
                }
            }
            catch (ArgumentException)
            {
                return false; // No such process.
            }
            catch (Exception)
            {
                return true; // Exists, but we may not query it.
            }
        }

        private static void TryDelete(string file)
        {
            try { File.Delete(file); } catch (Exception) { }
        }

        private static string Str(Dictionary<string, object> data, string key) =>
            data.TryGetValue(key, out object value) ? value as string : null;

        private static int Int(Dictionary<string, object> data, string key) =>
            data.TryGetValue(key, out object value) && value is int number ? number : 0;

        private static DateTime? Date(Dictionary<string, object> data, string key) =>
            DateTime.TryParse(Str(data, key), CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind, out DateTime date)
                ? (date.Kind == DateTimeKind.Unspecified ? date : date.ToLocalTime()) // no offset = Rhino's local time
                : (DateTime?)null;
    }

    /// <summary>
    /// Which Claude Code MCP entries point at which port: entries whose command
    /// runs rhinomcp, keyed by RHINO_MCP_PORT (1999 when unset). Re-read only
    /// when ~/.claude.json changes.
    /// </summary>
    static class ClaudeConfig
    {
        private const int DefaultPort = 1999;
        private static DateTime lastWrite;
        private static Dictionary<int, List<string>> entries = new Dictionary<int, List<string>>();

        private static string ConfigPath => Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".claude.json");

        public static IReadOnlyList<string> EntriesFor(int port)
        {
            Refresh();
            return entries.TryGetValue(port, out var names) ? names : (IReadOnlyList<string>)Array.Empty<string>();
        }

        private static void Refresh()
        {
            try
            {
                var info = new FileInfo(ConfigPath);
                if (!info.Exists)
                {
                    entries.Clear();
                    return;
                }
                if (info.LastWriteTimeUtc == lastWrite) return;

                string text;
                using (var stream = new FileStream(ConfigPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
                using (var reader = new StreamReader(stream))
                {
                    text = reader.ReadToEnd();
                }
                var root = new JavaScriptSerializer { MaxJsonLength = int.MaxValue }.DeserializeObject(text) as Dictionary<string, object>;
                var found = new Dictionary<int, List<string>>();
                if (root != null && root.TryGetValue("mcpServers", out object servers) && servers is Dictionary<string, object> map)
                {
                    foreach (var entry in map)
                    {
                        if (!(entry.Value is Dictionary<string, object> server)) continue;
                        string commandLine = (server.TryGetValue("command", out object command) ? command as string : "") + " " +
                                             (server.TryGetValue("args", out object args) && args is object[] list
                                                 ? string.Join(" ", list.OfType<string>())
                                                 : "");
                        if (commandLine.IndexOf("rhinomcp", StringComparison.OrdinalIgnoreCase) < 0) continue;

                        int port = DefaultPort;
                        if (server.TryGetValue("env", out object env) && env is Dictionary<string, object> vars &&
                            vars.TryGetValue("RHINO_MCP_PORT", out object value) &&
                            int.TryParse(Convert.ToString(value, CultureInfo.InvariantCulture), out int parsed))
                        {
                            port = parsed;
                        }
                        if (!found.TryGetValue(port, out var names)) found[port] = names = new List<string>();
                        names.Add(entry.Key);
                    }
                }
                entries = found;
                lastWrite = info.LastWriteTimeUtc;
            }
            catch (Exception)
            {
                // Claude Code is writing it; keep what we had and retry next tick.
            }
        }
    }
}
