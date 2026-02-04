using Rhino;
using Rhino.Commands;
using Rhino.Input;
using Rhino.Input.Custom;

namespace RhinoMCPPlugin.Commands
{
    public class MCPTestCommand : Command
    {
        public MCPTestCommand()
        {
            Instance = this;
        }

        public static MCPTestCommand Instance { get; private set; }

        public override string EnglishName => "mcptest";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            // Parse options
            var visualOption = new OptionToggle(false, "Off", "On");
            var delayOption = new OptionInteger(500, 0, 5000);

            var go = new GetOption();
            go.SetCommandPrompt("MCP Test options (press Enter to run with defaults)");
            go.AddOptionToggle("Visual", ref visualOption);
            go.AddOptionInteger("Delay", ref delayOption);
            go.AcceptNothing(true);

            while (true)
            {
                var result = go.Get();
                if (result == GetResult.Nothing || result == GetResult.Cancel)
                    break;
                if (result != GetResult.Option)
                    break;
            }

            bool visualMode = visualOption.CurrentValue;
            int delayMs = delayOption.CurrentValue;

            if (visualMode)
            {
                RhinoApp.WriteLine($"Running MCP function tests in VISUAL MODE (delay: {delayMs}ms)...");
            }
            else
            {
                RhinoApp.WriteLine("Running MCP function tests...");
            }
            RhinoApp.WriteLine("========================================");

            var functions = new Functions.RhinoMCPFunctions();
            var results = functions.TestAllFunctions(visualMode, delayMs);

            // Print summary
            RhinoApp.WriteLine("========================================");
            RhinoApp.WriteLine("Test Summary:");

            int passed = 0;
            int failed = 0;

            foreach (var prop in results.Properties())
            {
                var status = prop.Value["status"]?.ToString();
                if (status == "pass")
                {
                    passed++;
                    var note = prop.Value["note"]?.ToString();
                    if (!string.IsNullOrEmpty(note))
                        RhinoApp.WriteLine($"  [PASS] {prop.Name} ({note})");
                    else
                        RhinoApp.WriteLine($"  [PASS] {prop.Name}");
                }
                else
                {
                    failed++;
                    var error = prop.Value["error"]?.ToString() ?? "Unknown error";
                    RhinoApp.WriteLine($"  [FAIL] {prop.Name}: {error}");
                }
            }

            RhinoApp.WriteLine("========================================");
            RhinoApp.WriteLine($"Results: {passed} passed, {failed} failed, {passed + failed} total");

            if (failed == 0)
            {
                RhinoApp.WriteLine("All tests passed!");
                return Result.Success;
            }
            else
            {
                RhinoApp.WriteLine("Some tests failed. Check output above for details.");
                return Result.Failure;
            }
        }
    }
}
