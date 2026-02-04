using Rhino;
using Rhino.Commands;

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
            RhinoApp.WriteLine("Running MCP function tests...");
            RhinoApp.WriteLine("========================================");

            var functions = new Functions.RhinoMCPFunctions();
            var results = functions.TestAllFunctions();

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
