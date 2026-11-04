using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;

namespace RhinoMCPPlugin
{
    /// <summary>
    /// Best-effort answer to "which MCP client is this connection?" on Windows.
    /// The TCP table gives the process that owns the client socket (the Python
    /// rhinomcp server); walking up its parents past uv/uvx/python/shells gives
    /// the MCP client itself, e.g. one Claude Code session, whose working
    /// directory names the project it is working in. Every step is read-only
    /// and may fail (other user, 32-bit process, process already gone); callers
    /// then fall back to the bare endpoint.
    /// </summary>
    static class ClientIdentity
    {
        // Launchers and interpreters between the MCP client and the socket.
        private static readonly HashSet<string> Intermediates = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "rhinomcp.exe", "python.exe", "pythonw.exe", "py.exe", "uv.exe", "uvx.exe",
            "cmd.exe", "conhost.exe", "powershell.exe", "pwsh.exe", "bash.exe", "sh.exe",
        };

        public static string Describe(IPEndPoint client, int serverPort)
        {
            if (!OperatingSystem.IsWindows() || client == null) return null;
            try
            {
                int socketOwner = FindSocketOwner(client, serverPort);
                if (socketOwner <= 0) return null;

                var processes = SnapshotProcesses();
                int pid = socketOwner;
                for (int depth = 0; depth < 16 && processes.TryGetValue(pid, out var entry); depth++)
                {
                    if (!Intermediates.Contains(entry.Exe))
                    {
                        string app = string.Equals(entry.Exe, "claude.exe", StringComparison.OrdinalIgnoreCase)
                            ? "Claude Code"
                            : Path.GetFileNameWithoutExtension(entry.Exe);
                        string folder = WorkingDirectoryName(pid) ?? WorkingDirectoryName(socketOwner);
                        return folder == null ? $"{app} (PID {pid})" : $"{app} · {folder} (PID {pid})";
                    }
                    pid = entry.ParentPid;
                }

                string ownerName = processes.TryGetValue(socketOwner, out var owner) ? owner.Exe : "process";
                return $"{ownerName} (PID {socketOwner})";
            }
            catch
            {
                return null;
            }
        }

        // --- TCP table: which process owns the client end of our connection ---

        private const int AF_INET = 2;
        private const int TCP_TABLE_OWNER_PID_CONNECTIONS = 4;

        [StructLayout(LayoutKind.Sequential)]
        private struct MIB_TCPROW_OWNER_PID
        {
            public uint State;
            public uint LocalAddr;
            public uint LocalPort;
            public uint RemoteAddr;
            public uint RemotePort;
            public uint OwningPid;
        }

        [DllImport("iphlpapi.dll", SetLastError = true)]
        private static extern uint GetExtendedTcpTable(IntPtr pTcpTable, ref int pdwSize, bool bOrder, int ulAf, int tableClass, uint reserved);

        private static int FindSocketOwner(IPEndPoint client, int serverPort)
        {
            int size = 0;
            GetExtendedTcpTable(IntPtr.Zero, ref size, false, AF_INET, TCP_TABLE_OWNER_PID_CONNECTIONS, 0);
            IntPtr table = Marshal.AllocHGlobal(size);
            try
            {
                if (GetExtendedTcpTable(table, ref size, false, AF_INET, TCP_TABLE_OWNER_PID_CONNECTIONS, 0) != 0) return -1;

                int count = Marshal.ReadInt32(table);
                int rowSize = Marshal.SizeOf<MIB_TCPROW_OWNER_PID>();
                IntPtr row = table + 4;
                for (int i = 0; i < count; i++, row += rowSize)
                {
                    var r = Marshal.PtrToStructure<MIB_TCPROW_OWNER_PID>(row);
                    // The client's local port is our remote port, and vice versa.
                    if (NetworkPort(r.LocalPort) == client.Port && NetworkPort(r.RemotePort) == serverPort)
                    {
                        return (int)r.OwningPid;
                    }
                }
                return -1;
            }
            finally
            {
                Marshal.FreeHGlobal(table);
            }
        }

        private static int NetworkPort(uint value) => (int)(((value & 0xFF) << 8) | ((value >> 8) & 0xFF));

        // --- Process tree ---

        private struct ProcessEntry
        {
            public int ParentPid;
            public string Exe;
        }

        private const uint TH32CS_SNAPPROCESS = 0x2;

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct PROCESSENTRY32W
        {
            public uint dwSize;
            public uint cntUsage;
            public uint th32ProcessID;
            public IntPtr th32DefaultHeapID;
            public uint th32ModuleID;
            public uint cntThreads;
            public uint th32ParentProcessID;
            public int pcPriClassBase;
            public uint dwFlags;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
            public string szExeFile;
        }

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr CreateToolhelp32Snapshot(uint dwFlags, uint th32ProcessID);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern bool Process32FirstW(IntPtr hSnapshot, ref PROCESSENTRY32W lppe);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern bool Process32NextW(IntPtr hSnapshot, ref PROCESSENTRY32W lppe);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(IntPtr hObject);

        private static Dictionary<int, ProcessEntry> SnapshotProcesses()
        {
            var result = new Dictionary<int, ProcessEntry>();
            IntPtr snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
            if (snapshot == IntPtr.Zero || snapshot == new IntPtr(-1)) return result;
            try
            {
                var entry = new PROCESSENTRY32W { dwSize = (uint)Marshal.SizeOf<PROCESSENTRY32W>() };
                for (bool ok = Process32FirstW(snapshot, ref entry); ok; ok = Process32NextW(snapshot, ref entry))
                {
                    result[(int)entry.th32ProcessID] = new ProcessEntry
                    {
                        ParentPid = (int)entry.th32ParentProcessID,
                        Exe = entry.szExeFile,
                    };
                }
            }
            finally
            {
                CloseHandle(snapshot);
            }
            return result;
        }

        // --- Working directory of another (64-bit, same user) process ---

        private const uint PROCESS_QUERY_INFORMATION = 0x0400;
        private const uint PROCESS_VM_READ = 0x0010;
        // x64 layouts: PEB.ProcessParameters, and
        // RTL_USER_PROCESS_PARAMETERS.CurrentDirectory.DosPath (a UNICODE_STRING).
        private const int PebProcessParametersOffset = 0x20;
        private const int ParametersCurrentDirectoryOffset = 0x38;

        [StructLayout(LayoutKind.Sequential)]
        private struct PROCESS_BASIC_INFORMATION
        {
            public IntPtr ExitStatus;
            public IntPtr PebBaseAddress;
            public IntPtr AffinityMask;
            public IntPtr BasePriority;
            public IntPtr UniqueProcessId;
            public IntPtr InheritedFromUniqueProcessId;
        }

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr OpenProcess(uint dwDesiredAccess, bool bInheritHandle, int dwProcessId);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool IsWow64Process(IntPtr hProcess, out bool wow64Process);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool ReadProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, IntPtr nSize, out IntPtr lpNumberOfBytesRead);

        [DllImport("ntdll.dll")]
        private static extern int NtQueryInformationProcess(IntPtr processHandle, int processInformationClass, ref PROCESS_BASIC_INFORMATION processInformation, int processInformationLength, out int returnLength);

        private static string WorkingDirectoryName(int pid)
        {
            if (!Environment.Is64BitProcess) return null;

            IntPtr process = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, false, pid);
            if (process == IntPtr.Zero) return null;
            try
            {
                if (!IsWow64Process(process, out bool wow64) || wow64) return null;

                var info = new PROCESS_BASIC_INFORMATION();
                if (NtQueryInformationProcess(process, 0, ref info, Marshal.SizeOf<PROCESS_BASIC_INFORMATION>(), out _) != 0) return null;

                byte[] pointer = Read(process, info.PebBaseAddress + PebProcessParametersOffset, 8);
                if (pointer == null) return null;
                var parameters = new IntPtr(BitConverter.ToInt64(pointer, 0));

                byte[] unicodeString = Read(process, parameters + ParametersCurrentDirectoryOffset, 16);
                if (unicodeString == null) return null;
                int length = BitConverter.ToUInt16(unicodeString, 0);
                var buffer = new IntPtr(BitConverter.ToInt64(unicodeString, 8));
                if (length == 0 || length > 4096) return null;

                byte[] text = Read(process, buffer, length);
                if (text == null) return null;
                string directory = System.Text.Encoding.Unicode.GetString(text).TrimEnd('\\');
                string name = Path.GetFileName(directory);
                return string.IsNullOrEmpty(name) ? directory : name;
            }
            finally
            {
                CloseHandle(process);
            }
        }

        private static byte[] Read(IntPtr process, IntPtr address, int count)
        {
            var buffer = new byte[count];
            return ReadProcessMemory(process, address, buffer, new IntPtr(count), out IntPtr read) && read.ToInt64() == count
                ? buffer
                : null;
        }
    }
}
