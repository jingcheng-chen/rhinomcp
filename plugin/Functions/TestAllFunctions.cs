using System;
using System.Threading;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Display;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    // Grid layout settings for visual mode
    private const double GridSpacingX = 30;
    private const double GridSpacingY = 30;
    private int _visualTestRow = 0;
    private int _visualTestCol = 0;

    /// <summary>
    /// Tests all handler functions in RhinoMCPFunctions.
    /// Creates test objects, manipulates them, and verifies results.
    /// </summary>
    /// <param name="visualMode">If true, displays each test visually with updates and optional delays</param>
    /// <param name="delayMs">Delay in milliseconds between tests in visual mode (0 = no delay)</param>
    /// <returns>JObject with test results for each handler</returns>
    public JObject TestAllFunctions(bool visualMode = false, int delayMs = 500)
    {
        var results = new JObject();
        var doc = RhinoDoc.ActiveDoc;

        // Reset grid position for visual mode
        _visualTestRow = 0;
        _visualTestCol = 0;

        // Store created object IDs for later tests
        string boxId = null;
        string sphereId = null;
        string batchBox1Id = null;
        string batchBox2Id = null;
        string box2Id = null;
        string booleanBox1Id = null;
        string booleanBox2Id = null;

        if (visualMode)
        {
            RhinoApp.WriteLine("Visual mode enabled - objects will be arranged in a grid");
            doc.Views.Redraw();
        }

        // Helper to get next grid position
        JArray GetNextPosition()
        {
            var pos = new JArray { _visualTestCol * GridSpacingX, _visualTestRow * GridSpacingY, 0 };
            _visualTestCol++;
            if (_visualTestCol >= 5) // 5 columns per row
            {
                _visualTestCol = 0;
                _visualTestRow++;
            }
            return pos;
        }

        // Helper to update view in visual mode
        void VisualUpdate(string testName)
        {
            if (!visualMode) return;

            RhinoApp.WriteLine($"  >> {testName}");

            // Zoom to fit all objects
            foreach (var view in doc.Views)
            {
                view.ActiveViewport.ZoomExtents();
            }

            doc.Views.Redraw();

            // Use RhinoApp.Wait() to process UI events and allow the viewport to actually update
            // This is necessary because Thread.Sleep blocks the UI thread
            if (delayMs > 0)
            {
                var stopwatch = System.Diagnostics.Stopwatch.StartNew();
                while (stopwatch.ElapsedMilliseconds < delayMs)
                {
                    RhinoApp.Wait(); // Process UI messages
                    Thread.Sleep(10); // Small sleep to prevent CPU spinning
                }
            }
            else
            {
                RhinoApp.Wait(); // At least process one round of UI messages
            }
        }

        // Test 1: CreateObject - BOX
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 0, 0, 0 };
            var box = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPTestBox",
                ["color"] = new JArray { 255, 100, 100 }, // Red-ish
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos
            });
            boxId = box["id"]?.ToString();
            if (string.IsNullOrEmpty(boxId))
                throw new Exception("No ID returned");
            results["create_object_box"] = new JObject { ["status"] = "pass", ["id"] = boxId };
            VisualUpdate("Created BOX");
        }
        catch (Exception e)
        {
            results["create_object_box"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 2: CreateObject - SPHERE
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 20, 0, 0 };
            var sphere = CreateObject(new JObject
            {
                ["type"] = "SPHERE",
                ["name"] = "MCPTestSphere",
                ["color"] = new JArray { 100, 100, 255 }, // Blue-ish
                ["params"] = new JObject { ["radius"] = 5 },
                ["translation"] = pos
            });
            sphereId = sphere["id"]?.ToString();
            if (string.IsNullOrEmpty(sphereId))
                throw new Exception("No ID returned");
            results["create_object_sphere"] = new JObject { ["status"] = "pass", ["id"] = sphereId };
            VisualUpdate("Created SPHERE");
        }
        catch (Exception e)
        {
            results["create_object_sphere"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 3: CreateObjects (batch)
        try
        {
            var pos1 = visualMode ? GetNextPosition() : new JArray { -20, 0, 0 };
            var pos2 = visualMode ? GetNextPosition() : new JArray { -20, 10, 0 };
            var batchResult = CreateObjects(new JObject
            {
                ["BatchBox1"] = new JObject
                {
                    ["type"] = "BOX",
                    ["name"] = "MCPBatchBox1",
                    ["color"] = new JArray { 100, 255, 100 }, // Green
                    ["params"] = new JObject { ["width"] = 5, ["length"] = 5, ["height"] = 5 },
                    ["translation"] = pos1
                },
                ["BatchBox2"] = new JObject
                {
                    ["type"] = "BOX",
                    ["name"] = "MCPBatchBox2",
                    ["color"] = new JArray { 100, 255, 150 }, // Green variant
                    ["params"] = new JObject { ["width"] = 3, ["length"] = 3, ["height"] = 3 },
                    ["translation"] = pos2
                }
            });
            var successCount = batchResult["success_count"]?.ToObject<int>() ?? 0;
            if (successCount != 2)
                throw new Exception($"Expected 2 successes, got {successCount}");
            batchBox1Id = batchResult["objects"]?["BatchBox1"]?["id"]?.ToString();
            batchBox2Id = batchResult["objects"]?["BatchBox2"]?["id"]?.ToString();
            if (string.IsNullOrEmpty(batchBox1Id) || string.IsNullOrEmpty(batchBox2Id))
                throw new Exception("Batch-created boxes did not return object IDs");
            box2Id = batchBox1Id;
            results["create_objects"] = new JObject { ["status"] = "pass", ["success_count"] = successCount };
            VisualUpdate("Created batch objects (2 boxes)");
        }
        catch (Exception e)
        {
            results["create_objects"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 4: GetDocumentSummary
        try
        {
            var docSummary = GetDocumentSummary(new JObject());
            var objectCount = docSummary["object_count"]?.ToObject<int>() ?? 0;
            var layerCount = docSummary["layer_count"]?.ToObject<int>() ?? 0;
            if (objectCount < 1)
                throw new Exception($"Expected at least 1 object, got {objectCount}");
            results["get_document_summary"] = new JObject { ["status"] = "pass", ["object_count"] = objectCount, ["layer_count"] = layerCount };
            VisualUpdate($"Got document summary: {objectCount} objects");
        }
        catch (Exception e)
        {
            results["get_document_summary"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 5: GetObjectInfo
        try
        {
            if (string.IsNullOrEmpty(boxId))
                throw new Exception("No box ID available from previous test");
            var objInfo = GetObjectInfo(new JObject { ["id"] = boxId });
            var name = objInfo["name"]?.ToString();
            if (name != "MCPTestBox")
                throw new Exception($"Expected name 'MCPTestBox', got '{name}'");
            results["get_object_info"] = new JObject { ["status"] = "pass", ["name"] = name };
            VisualUpdate("Got object info");
        }
        catch (Exception e)
        {
            results["get_object_info"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 6: SelectObjects
        try
        {
            var selectResult = SelectObjects(new JObject
            {
                ["filters"] = new JObject { ["name"] = new JArray { "MCPTestBox" } },
                ["filters_type"] = "or"
            });
            var count = selectResult["count"]?.ToObject<int>() ?? 0;
            if (count != 1)
                throw new Exception($"Expected 1 selected, got {count}");
            results["select_objects"] = new JObject { ["status"] = "pass", ["count"] = count };
            VisualUpdate("Selected MCPTestBox");
        }
        catch (Exception e)
        {
            results["select_objects"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 7: GetSelectedObjectsInfo
        try
        {
            var selectedInfo = GetSelectedObjectsInfo(new JObject { ["include_attributes"] = true });
            var selectedObjects = selectedInfo["selected_objects"] as JArray;
            if (selectedObjects == null || selectedObjects.Count == 0)
                throw new Exception("No selected objects returned");
            results["get_selected_objects_info"] = new JObject { ["status"] = "pass", ["count"] = selectedObjects.Count };
            VisualUpdate("Got selected objects info");
        }
        catch (Exception e)
        {
            results["get_selected_objects_info"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 8: ModifyObject
        try
        {
            if (string.IsNullOrEmpty(boxId))
                throw new Exception("No box ID available from previous test");
            var modifyResult = ModifyObject(new JObject
            {
                ["id"] = boxId,
                ["new_name"] = "MCPTestBoxRenamed",
                ["new_color"] = new JArray { 255, 0, 0 } // Bright red
            });
            var newName = modifyResult["name"]?.ToString();
            if (newName != "MCPTestBoxRenamed")
                throw new Exception($"Expected name 'MCPTestBoxRenamed', got '{newName}'");
            results["modify_object"] = new JObject { ["status"] = "pass", ["new_name"] = newName };
            VisualUpdate("Modified box (renamed, changed to bright red)");
        }
        catch (Exception e)
        {
            results["modify_object"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 9: ModifyObjects (batch)
        try
        {
            if (string.IsNullOrEmpty(batchBox1Id) || string.IsNullOrEmpty(batchBox2Id))
                throw new Exception("No batch object IDs available from create_objects test");
            var modifyBatchResult = ModifyObjects(new JObject
            {
                ["objects"] = new JArray
                {
                    new JObject { ["id"] = batchBox1Id, ["new_color"] = new JArray { 0, 255, 0 } }, // Bright green
                    new JObject { ["id"] = batchBox2Id, ["new_color"] = new JArray { 0, 0, 255 } }  // Bright blue
                }
            });
            var successCount = modifyBatchResult["success_count"]?.ToObject<int>() ?? 0;
            if (successCount != 2)
                throw new Exception($"Expected 2 successes, got {successCount}");
            results["modify_objects"] = new JObject { ["status"] = "pass", ["success_count"] = successCount };
            VisualUpdate("Modified batch boxes (green and blue)");
        }
        catch (Exception e)
        {
            results["modify_objects"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 10: CreateLayer
        try
        {
            var layerResult = CreateLayer(new JObject
            {
                ["name"] = "MCPTestLayer",
                ["color"] = new JArray { 255, 128, 0 } // Orange
            });
            var layerName = layerResult["name"]?.ToString();
            if (layerName != "MCPTestLayer")
                throw new Exception($"Expected layer name 'MCPTestLayer', got '{layerName}'");
            results["create_layer"] = new JObject { ["status"] = "pass", ["name"] = layerName };
            VisualUpdate("Created layer 'MCPTestLayer'");
        }
        catch (Exception e)
        {
            results["create_layer"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 11: GetOrSetCurrentLayer
        try
        {
            var setResult = GetOrSetCurrentLayer(new JObject { ["name"] = "MCPTestLayer" });
            var currentName = setResult["name"]?.ToString();
            if (currentName != "MCPTestLayer")
                throw new Exception($"Expected current layer 'MCPTestLayer', got '{currentName}'");

            var getResult = GetOrSetCurrentLayer(new JObject());
            currentName = getResult["name"]?.ToString();
            if (currentName != "MCPTestLayer")
                throw new Exception($"Expected current layer still 'MCPTestLayer', got '{currentName}'");

            results["get_or_set_current_layer"] = new JObject { ["status"] = "pass", ["current_layer"] = currentName };
            VisualUpdate("Set current layer to 'MCPTestLayer'");
        }
        catch (Exception e)
        {
            results["get_or_set_current_layer"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 12: Create objects for boolean operations
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 50, 0, 0 };
            var boolBox1 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "BooleanBox1",
                ["color"] = new JArray { 255, 200, 100 }, // Orange-ish
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos
            });
            booleanBox1Id = boolBox1["id"]?.ToString();

            // Offset second box to overlap with first
            var pos2 = new JArray { ((JArray)pos)[0].ToObject<double>() + 5, ((JArray)pos)[1].ToObject<double>(), 0 };
            var boolBox2 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "BooleanBox2",
                ["color"] = new JArray { 100, 200, 255 }, // Light blue
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos2
            });
            booleanBox2Id = boolBox2["id"]?.ToString();

            results["create_boolean_test_objects"] = new JObject { ["status"] = "pass" };
            VisualUpdate("Created overlapping boxes for boolean union");
        }
        catch (Exception e)
        {
            results["create_boolean_test_objects"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 13: BooleanUnion
        try
        {
            if (string.IsNullOrEmpty(booleanBox1Id) || string.IsNullOrEmpty(booleanBox2Id))
                throw new Exception("Boolean test objects not created");

            var unionResult = BooleanUnion(new JObject
            {
                ["object_ids"] = new JArray { booleanBox1Id, booleanBox2Id },
                ["name"] = "BooleanUnionResult",
                ["delete_sources"] = true
            });
            var resultCount = unionResult["count"]?.ToObject<int>() ?? 0;
            if (resultCount < 1)
                throw new Exception($"Expected at least 1 result, got {resultCount}");
            results["boolean_union"] = new JObject { ["status"] = "pass", ["result_count"] = resultCount };
            VisualUpdate("Boolean UNION - merged boxes");
        }
        catch (Exception e)
        {
            results["boolean_union"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 14: Boolean Difference
        string diffBaseId = null;
        string diffSubtractId = null;
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 70, 0, 0 };
            var diffBase = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "DiffBase",
                ["color"] = new JArray { 200, 200, 200 }, // Gray
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos
            });
            diffBaseId = diffBase["id"]?.ToString();

            var diffSubtract = CreateObject(new JObject
            {
                ["type"] = "SPHERE",
                ["name"] = "DiffSubtract",
                ["color"] = new JArray { 255, 50, 50 }, // Red
                ["params"] = new JObject { ["radius"] = 6 },
                ["translation"] = pos
            });
            diffSubtractId = diffSubtract["id"]?.ToString();
            VisualUpdate("Created box and sphere for boolean difference");

            var diffResult = BooleanDifference(new JObject
            {
                ["base_id"] = diffBaseId,
                ["subtract_ids"] = new JArray { diffSubtractId },
                ["name"] = "BooleanDiffResult",
                ["delete_sources"] = true
            });
            var resultCount = diffResult["count"]?.ToObject<int>() ?? 0;
            if (resultCount < 1)
                throw new Exception($"Expected at least 1 result, got {resultCount}");
            results["boolean_difference"] = new JObject { ["status"] = "pass", ["result_count"] = resultCount };
            VisualUpdate("Boolean DIFFERENCE - sphere carved from box");
        }
        catch (Exception e)
        {
            results["boolean_difference"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 15: BooleanIntersection
        string intersectBox1Id = null;
        string intersectBox2Id = null;
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 90, 0, 0 };
            var intBox1 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "IntersectBox1",
                ["color"] = new JArray { 255, 150, 255 }, // Pink
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos
            });
            intersectBox1Id = intBox1["id"]?.ToString();

            var pos2 = new JArray { ((JArray)pos)[0].ToObject<double>() + 5, ((JArray)pos)[1].ToObject<double>(), 0 };
            var intBox2 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "IntersectBox2",
                ["color"] = new JArray { 150, 255, 255 }, // Cyan
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos2
            });
            intersectBox2Id = intBox2["id"]?.ToString();
            VisualUpdate("Created overlapping boxes for boolean intersection");

            var intersectResult = BooleanIntersection(new JObject
            {
                ["object_ids"] = new JArray { intersectBox1Id, intersectBox2Id },
                ["name"] = "BooleanIntersectResult",
                ["delete_sources"] = true
            });
            var resultCount = intersectResult["count"]?.ToObject<int>() ?? 0;
            if (resultCount < 1)
                throw new Exception($"Expected at least 1 result, got {resultCount}");
            results["boolean_intersection"] = new JObject { ["status"] = "pass", ["result_count"] = resultCount };
            VisualUpdate("Boolean INTERSECTION - only overlapping volume");
        }
        catch (Exception e)
        {
            results["boolean_intersection"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 16: ExecuteRhinoscript
        try
        {
            var scriptResult = ExecuteRhinoscript(new JObject
            {
                ["code"] = "print('MCP Test Script Executed')"
            });
            var success = scriptResult["success"]?.ToObject<bool>() ?? false;
            if (!success)
                throw new Exception(scriptResult["message"]?.ToString() ?? "Script execution failed");
            results["execute_rhinoscript"] = new JObject { ["status"] = "pass" };
            VisualUpdate("Executed Python script");
        }
        catch (Exception e)
        {
            results["execute_rhinoscript"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 17: Undo
        if (doc.UndoRecordingIsActive)
        {
            try
            {
                var undoResult = Undo(new JObject { ["steps"] = 1 });
                results["undo"] = new JObject
                {
                    ["status"] = "pass",
                    ["note"] = "Handler works; full undo cycle cannot be tested from within a command"
                };
                VisualUpdate("Undo handler tested");
            }
            catch (Exception e)
            {
                results["undo"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
            }
        }
        else
        {
            try
            {
                var undoRecordId = doc.BeginUndoRecord("MCPTest_AddPoint");
                var pointId = doc.Objects.AddPoint(new Rhino.Geometry.Point3d(999, 999, 999));
                doc.EndUndoRecord(undoRecordId);

                var undoResult = Undo(new JObject { ["steps"] = 1 });
                var undoneSteps = undoResult["undone_steps"]?.ToObject<int>() ?? 0;
                if (undoneSteps < 1)
                    throw new Exception($"Expected at least 1 undone step, got {undoneSteps}");
                results["undo"] = new JObject { ["status"] = "pass", ["undone_steps"] = undoneSteps };
                VisualUpdate("Undo test passed");
            }
            catch (Exception e)
            {
                results["undo"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
            }
        }

        // Test 18: Redo
        try
        {
            var redoResult = Redo(new JObject { ["steps"] = 1 });
            results["redo"] = new JObject
            {
                ["status"] = "pass",
                ["note"] = doc.UndoRecordingIsActive
                    ? "Handler works; full redo cycle cannot be tested from within a command"
                    : null
            };
            VisualUpdate("Redo handler tested");
        }
        catch (Exception e)
        {
            results["redo"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: undo groups. mcptest runs inside a Rhino command whose undo
        // record is open, so Rhino declines the group's record there:
        // begin_undo_group must refuse with rhino_error and leave the command's
        // record open. Outside a command the full cycle runs: two changes made
        // inside a group revert with one undo.
        try
        {
            void ExpectMcpError(Func<JObject> call, string code, string label)
            {
                try
                {
                    call();
                }
                catch (McpException e)
                {
                    if (e.Code == code) return;
                    throw new Exception($"{label}: expected {code}, got {e.Code}: {e.Message}");
                }
                throw new Exception($"{label}: expected a {code} error, got none");
            }

            var none = EndUndoGroup(new JObject());
            if (none["ended"]?.ToObject<bool>() != false)
                throw new Exception("end_undo_group with no open group should report ended=false");
            ExpectMcpError(() => BeginUndoGroup(new JObject { ["name"] = "  " }),
                McpException.InvalidArgument, "blank name");
            ExpectMcpError(() => BeginUndoGroup(new JObject { ["name"] = "MCPTest group", ["idle_timeout_seconds"] = 0 }),
                McpException.InvalidArgument, "zero idle timeout");

            if (doc.UndoRecordingIsActive)
            {
                uint commandRecord = doc.CurrentUndoRecordSerialNumber;
                ExpectMcpError(() => BeginUndoGroup(new JObject { ["name"] = "MCPTest group" }),
                    McpException.RhinoError, "begin inside a command");
                if (doc.CurrentUndoRecordSerialNumber != commandRecord)
                    throw new Exception("a declined begin_undo_group changed the open undo record");
                results["undo_group"] = new JObject
                {
                    ["status"] = "pass",
                    ["note"] = "Declined inside a command as expected; the full undo cycle cannot be tested from within a command"
                };
            }
            else
            {
                BeginUndoGroup(new JObject { ["name"] = "MCPTest group" });
                Guid first, second;
                JObject ended;
                try
                {
                    first = doc.Objects.AddPoint(new Point3d(901, 901, 901));
                    second = doc.Objects.AddPoint(new Point3d(902, 902, 902));
                    ExpectMcpError(() => BeginUndoGroup(new JObject { ["name"] = "MCPTest nested" }),
                        McpException.InvalidArgument, "nested begin");
                    ExpectMcpError(() => Undo(new JObject()), McpException.InvalidArgument, "undo inside a group");
                    ended = EndUndoGroup(new JObject());
                }
                finally
                {
                    // A failed check must not leave the record open.
                    if (_undoGroup != null)
                        CloseUndoGroup(_undoGroup, UndoGroupRequested);
                }
                if (ended["ended"]?.ToObject<bool>() != true || ended["end_reason"]?.ToString() != "requested")
                    throw new Exception($"end_undo_group did not end the group: {ended}");
                Undo(new JObject { ["steps"] = 1 });
                if (doc.Objects.Find(first) != null || doc.Objects.Find(second) != null)
                    throw new Exception("one undo did not revert both points added inside the group");
                results["undo_group"] = new JObject { ["status"] = "pass" };
            }
            VisualUpdate("Undo group handlers tested");
        }
        catch (Exception e)
        {
            results["undo_group"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 19: DeleteObject
        try
        {
            if (string.IsNullOrEmpty(sphereId))
                throw new Exception("No sphere ID available from previous test");

            var deleteResult = DeleteObject(new JObject { ["id"] = sphereId });
            var deleted = deleteResult["deleted"]?.ToObject<bool>() ?? false;
            if (!deleted)
                throw new Exception("Object was not deleted");
            results["delete_object"] = new JObject { ["status"] = "pass" };
            VisualUpdate("Deleted sphere");
        }
        catch (Exception e)
        {
            results["delete_object"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 19b: deleting an UNNAMED object must report the "(unnamed)"
        // fallback, never null. A null name made delete_result fail response
        // validation under strict mode.
        try
        {
            var lineId = doc.Objects.AddLine(
                new Rhino.Geometry.Point3d(0, 0, 0), new Rhino.Geometry.Point3d(3, 0, 0));
            if (lineId == Guid.Empty)
                throw new Exception("could not add an unnamed line to test with");

            var res = DeleteObject(new JObject { ["id"] = lineId.ToString() });
            if (!(res["deleted"]?.ToObject<bool>() ?? false))
                throw new Exception("unnamed object was not deleted");
            var name = res["name"]?.ToString();
            if (name != "(unnamed)")
                throw new Exception("expected name '(unnamed)' for a nameless object, got '" + (name ?? "null") + "'");
            results["delete_unnamed_object"] = new JObject { ["status"] = "pass", ["name"] = name };
            VisualUpdate("Deleted unnamed object reports (unnamed)");
        }
        catch (Exception e)
        {
            results["delete_unnamed_object"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 20: DeleteLayer
        try
        {
            GetOrSetCurrentLayer(new JObject { ["name"] = "Default" });

            var deleteLayerResult = DeleteLayer(new JObject { ["name"] = "MCPTestLayer" });
            var success = deleteLayerResult["success"]?.ToObject<bool>() ?? false;
            if (!success)
                throw new Exception(deleteLayerResult["message"]?.ToString() ?? "Layer deletion failed");
            results["delete_layer"] = new JObject { ["status"] = "pass" };
            VisualUpdate("Deleted layer 'MCPTestLayer'");
        }
        catch (Exception e)
        {
            results["delete_layer"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 21: ProjectCurve
        string projCurveId = null;
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 110, 0, 0 };
            
            // Create a target surface
            var surface = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "ProjTarget",
                ["color"] = new JArray { 200, 200, 200 },
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 2 },
                ["translation"] = pos
            });
            var targetId = surface["id"]?.ToString();

            // Create a curve above it
            var curvePos = new JArray { ((JArray)pos)[0].ToObject<double>() + 2, ((JArray)pos)[1].ToObject<double>() + 2, 10 };
            var curve = CreateObject(new JObject
            {
                ["type"] = "CIRCLE",
                ["name"] = "ProjSource",
                ["params"] = new JObject { ["center"] = new JArray { 0, 0, 0 }, ["radius"] = 3 },
                ["translation"] = curvePos
            });
            var sourceId = curve["id"]?.ToString();

            var projResult = ProjectCurve(new JObject
            {
                ["curve_id"] = sourceId,
                ["target_ids"] = new JArray { targetId },
                ["direction"] = new JArray { 0, 0, -1 },
                ["name"] = "ProjectedCurve"
            });
            var projIds = projResult["result_ids"] as JArray;
            if (projIds == null || projIds.Count == 0)
                throw new Exception("No curves projected");
            
            projCurveId = projIds[0].ToString();
            results["project_curve"] = new JObject { ["status"] = "pass", ["count"] = projIds.Count };
            VisualUpdate("Projected circle onto box");
        }
        catch (Exception e)
        {
            results["project_curve"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 22: IntersectCurves
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 130, 0, 0 };
            
            // Create two intersecting lines
            var line1 = CreateObject(new JObject
            {
                ["type"] = "LINE",
                ["name"] = "IntLine1",
                ["params"] = new JObject { ["start"] = new JArray { 0, 0, 0 }, ["end"] = new JArray { 10, 10, 0 } },
                ["translation"] = pos
            });
            var line2 = CreateObject(new JObject
            {
                ["type"] = "LINE",
                ["name"] = "IntLine2",
                ["params"] = new JObject { ["start"] = new JArray { 0, 10, 0 }, ["end"] = new JArray { 10, 0, 0 } },
                ["translation"] = pos
            });

            var intResult = IntersectCurves(new JObject
            {
                ["curve_id_a"] = line1["id"]?.ToString(),
                ["curve_id_b"] = line2["id"]?.ToString(),
                ["name"] = "IntersectionPoint"
            });
            var ptIds = intResult["point_ids"] as JArray;
            if (ptIds == null || ptIds.Count == 0)
                throw new Exception("No intersection points found");
            
            results["intersect_curves"] = new JObject { ["status"] = "pass", ["count"] = ptIds.Count };
            VisualUpdate("Found intersection between two lines");
        }
        catch (Exception e)
        {
            results["intersect_curves"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 23: SplitCurve
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 150, 0, 0 };
            
            // Create a line to split
            var line = CreateObject(new JObject
            {
                ["type"] = "LINE",
                ["name"] = "SplitLine",
                ["params"] = new JObject { ["start"] = new JArray { 0, 0, 0 }, ["end"] = new JArray { 10, 0, 0 } },
                ["translation"] = pos
            });
            
            // Split at mid-parameter (0.5 for a line)
            var splitResult = SplitCurve(new JObject
            {
                ["curve_id"] = line["id"]?.ToString(),
                ["parameters"] = new JArray { 0.5 },
                ["name"] = "SplitSegment",
                ["delete_source"] = true
            });
            var segIds = splitResult["result_ids"] as JArray;
            if (segIds == null || segIds.Count != 2)
                throw new Exception($"Expected 2 segments, got {segIds?.Count ?? 0}");
            
            results["split_curve"] = new JObject { ["status"] = "pass", ["count"] = segIds.Count };
            VisualUpdate("Split line into two segments");
        }
        catch (Exception e)
        {
            results["split_curve"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 24: CaptureViewport must not move the user's camera (ReadOnly contract)
        try
        {
            var activeViewport = doc.Views.ActiveView?.ActiveViewport;
            if (activeViewport == null)
                throw new Exception("No active viewport to test against");

            // zoom_to_fit, a temporary display mode, camera, lens and framing all
            // move the view; a correct ReadOnly handler restores every one of them.
            var captures = new[]
            {
                new JObject { ["zoom_to_fit"] = true },
                new JObject
                {
                    ["display_mode"] = "Wireframe",
                    ["camera_location"] = new JArray { 37.0, -53.0, 21.0 },
                    ["camera_target"] = new JArray { 1.0, 2.0, 3.0 },
                    ["lens_length"] = 85.0
                },
                new JObject
                {
                    ["display_mode"] = "Ghosted",
                    ["frame_bbox"] = new JObject { ["min"] = new JArray { 0.0, 0.0, 0.0 }, ["max"] = new JArray { 3.0, 4.0, 5.0 } },
                    ["format"] = "jpeg"
                },
            };
            double cameraDrift = 0, frustumDrift = 0;
            foreach (var capture in captures)
            {
                string nameBefore = activeViewport.Name;
                var modeBefore = activeViewport.DisplayMode?.Id;
                var before = new Rhino.DocObjects.ViewportInfo(activeViewport);
                before.GetFrustum(out double bl, out double br, out double bb, out double bt, out _, out _);

                capture["viewport"] = "active";
                capture["width"] = 200;
                capture["height"] = 200;
                var result = CaptureViewport(capture);
                if (result["display_mode"] == null || result["camera_up"] == null || result["total_object_count"] == null)
                    throw new Exception("capture_viewport metadata is missing fields");

                var after = new Rhino.DocObjects.ViewportInfo(activeViewport);
                after.GetFrustum(out double al, out double ar, out double ab, out double at, out _, out _);

                cameraDrift = Math.Max(cameraDrift, before.CameraLocation.DistanceTo(after.CameraLocation)
                    + before.TargetPoint.DistanceTo(after.TargetPoint)
                    + (before.CameraUp - after.CameraUp).Length
                    + Math.Abs(before.Camera35mmLensLength - after.Camera35mmLensLength));
                frustumDrift = Math.Max(frustumDrift, Math.Abs(bl - al) + Math.Abs(br - ar) + Math.Abs(bb - ab) + Math.Abs(bt - at));
                bool kept = activeViewport.Name == nameBefore
                    && activeViewport.DisplayMode?.Id == modeBefore
                    && before.IsPerspectiveProjection == after.IsPerspectiveProjection;
                if (cameraDrift > 1e-6 || frustumDrift > 1e-6 || !kept)
                    throw new Exception($"capture_viewport {capture.ToString(Newtonsoft.Json.Formatting.None, Array.Empty<Newtonsoft.Json.JsonConverter>())} changed the active view (cameraDrift={cameraDrift:G4}, frustumDrift={frustumDrift:G4}, nameModeProjectionKept={kept})");
            }

            results["capture_viewport_readonly"] = new JObject
            {
                ["status"] = "pass",
                ["camera_drift"] = cameraDrift,
                ["frustum_drift"] = frustumDrift
            };
            VisualUpdate("capture_viewport left the camera unchanged");
        }
        catch (Exception e)
        {
            results["capture_viewport_readonly"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 25: change-delta helpers (Scene Perception Layer). The dispatch
        // path that attaches _delta is private to RhinoMCPServer, so assert the
        // public helpers directly: BuildDelta as a pure set diff, and a real
        // before/after snapshot around a create.
        try
        {
            var idA = Guid.NewGuid();
            var idB = Guid.NewGuid();
            var idC = Guid.NewGuid();
            var pure = BuildDelta(
                new System.Collections.Generic.HashSet<Guid> { idA, idB },
                new System.Collections.Generic.HashSet<Guid> { idB, idC });
            if ((int)pure["created_count"] != 1 || (int)pure["deleted_count"] != 1)
                throw new Exception("BuildDelta counts incorrect");
            var created = (JArray)pure["created_ids"];
            var deleted = (JArray)pure["deleted_ids"];
            if (created.Count != 1 || created[0].ToString() != idC.ToString())
                throw new Exception("BuildDelta created_ids incorrect");
            if (deleted.Count != 1 || deleted[0].ToString() != idA.ToString())
                throw new Exception("BuildDelta deleted_ids incorrect");
            if ((bool)pure["truncated"])
                throw new Exception("BuildDelta marked a small delta truncated");

            // Over the cap: counts stay exact, id lists are dropped, truncated set.
            var bigBefore = new System.Collections.Generic.HashSet<Guid>();
            var bigAfter = new System.Collections.Generic.HashSet<Guid>();
            for (int i = 0; i < DeltaIdListCap + 10; i++) bigAfter.Add(Guid.NewGuid());
            var big = BuildDelta(bigBefore, bigAfter);
            if ((int)big["created_count"] != DeltaIdListCap + 10)
                throw new Exception("BuildDelta dropped the count when truncating");
            if (big["created_ids"] != null)
                throw new Exception("BuildDelta included an over-cap id list");
            if (!(bool)big["truncated"])
                throw new Exception("BuildDelta did not set truncated for an over-cap list");

            var idsBefore = SnapshotObjectIds(doc);
            var probe = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPDeltaProbe",
                ["params"] = new JObject { ["width"] = 1, ["length"] = 1, ["height"] = 1 }
            });
            string probeId = probe["id"]?.ToString();
            var live = BuildDelta(idsBefore, SnapshotObjectIds(doc));
            bool sawProbe = false;
            foreach (var t in (JArray)live["created_ids"])
                if (t.ToString() == probeId) sawProbe = true;
            if (!sawProbe)
                throw new Exception("snapshot/delta did not report the created object");
            if ((int)live["count_after"] != (int)live["count_before"] + 1)
                throw new Exception("live delta count did not rise by exactly 1");

            DeleteObject(new JObject { ["id"] = probeId });
            results["change_delta"] = new JObject
            {
                ["status"] = "pass",
                ["created_reported"] = (int)live["created_count"]
            };
            VisualUpdate("change-delta helpers report created/deleted ids");
        }
        catch (Exception e)
        {
            results["change_delta"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: a serialized object's layer name is read live, so renaming a
        // layer is reflected immediately instead of being served stale from a
        // cache. Calls the serializer directly and renames the layer between two
        // reads of the same object.
        try
        {
            var ld = RhinoDoc.ActiveDoc;
            int li = ld.Layers.Add("MCPLayerCacheProbe", System.Drawing.Color.Gray);
            if (li < 0)
                throw new Exception("could not add probe layer");
            var attr = new Rhino.DocObjects.ObjectAttributes { LayerIndex = li };
            var gid = ld.Objects.AddPoint(new Rhino.Geometry.Point3d(0, 0, 0), attr);
            var lo = ld.Objects.Find(gid);

            string before = rhinomcp.Serializers.Serializer.RhinoObject(lo)["layer"]?.ToString();
            ld.Layers[li].Name = "MCPLayerCacheProbeRenamed";
            string after = rhinomcp.Serializers.Serializer.RhinoObject(lo)["layer"]?.ToString();

            ld.Objects.Delete(gid, true);
            ld.Layers.Delete(li, true);

            if (before != "MCPLayerCacheProbe")
                throw new Exception("layer before rename was " + before);
            if (after != "MCPLayerCacheProbeRenamed")
                throw new Exception("stale layer name after rename: " + after);
            results["layer_name_live"] = new JObject { ["status"] = "pass" };
            VisualUpdate("serialized layer name reads live after rename");
        }
        catch (Exception e)
        {
            results["layer_name_live"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 26: change-health helper (Scene Perception Layer). BuildHealth runs
        // GeometryBase.IsValidWithLog over the newly-created objects. Create one
        // valid object and add one genuinely invalid curve (a zero-length line,
        // which the document accepts but reports invalid), then assert only the
        // bad one is listed, with a reason, and the counts are exact.
        try
        {
            var healthBefore = SnapshotObjectIds(doc);
            var okBox = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPHealthOk",
                ["params"] = new JObject { ["width"] = 1, ["length"] = 1, ["height"] = 1 }
            });
            string okId = okBox["id"]?.ToString();
            var badId = doc.Objects.AddCurve(new Rhino.Geometry.LineCurve(
                new Rhino.Geometry.Point3d(0, 0, 0), new Rhino.Geometry.Point3d(0, 0, 0)));

            var health = BuildHealth(doc, healthBefore, SnapshotObjectIds(doc));
            if ((int)health["checked_count"] != 2)
                throw new Exception("BuildHealth checked_count should be 2, got " + health["checked_count"]);
            if ((int)health["invalid_count"] != 1)
                throw new Exception("BuildHealth invalid_count should be 1, got " + health["invalid_count"]);
            if ((bool)health["truncated"])
                throw new Exception("BuildHealth marked a single issue truncated");
            var issues = (JArray)health["issues"];
            if (issues.Count != 1)
                throw new Exception("BuildHealth should list exactly one issue, got " + issues.Count);
            if (issues[0]["id"].ToString() != badId.ToString())
                throw new Exception("BuildHealth flagged the wrong object");
            if (string.IsNullOrWhiteSpace(issues[0]["reason"]?.ToString()))
                throw new Exception("BuildHealth issue is missing a reason");
            foreach (var it in issues)
                if (it["id"].ToString() == okId)
                    throw new Exception("BuildHealth listed the valid object as an issue");

            doc.Objects.Delete(badId, true);
            DeleteObject(new JObject { ["id"] = okId });
            results["change_health"] = new JObject
            {
                ["status"] = "pass",
                ["reason"] = issues[0]["reason"]
            };
            VisualUpdate("change-health flags invalid created geometry");
        }
        catch (Exception e)
        {
            results["change_health"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: measure_objects reports clash and bounding-box gap. Two 2x2x2
        // boxes 10 apart on X must not clash (positive gap, brep method); a box
        // overlapping the first must clash with a zero gap.
        try
        {
            var mA = CreateObject(new JObject
            {
                ["type"] = "BOX", ["name"] = "MCPMeasureA",
                ["params"] = new JObject { ["width"] = 2, ["length"] = 2, ["height"] = 2 }
            });
            var mB = CreateObject(new JObject
            {
                ["type"] = "BOX", ["name"] = "MCPMeasureB",
                ["params"] = new JObject { ["width"] = 2, ["length"] = 2, ["height"] = 2 },
                ["translation"] = new JArray { 10, 0, 0 }
            });
            var mC = CreateObject(new JObject
            {
                ["type"] = "BOX", ["name"] = "MCPMeasureC",
                ["params"] = new JObject { ["width"] = 2, ["length"] = 2, ["height"] = 2 },
                ["translation"] = new JArray { 1, 0, 0 }
            });
            string mAId = mA["id"]?.ToString();
            string mBId = mB["id"]?.ToString();
            string mCId = mC["id"]?.ToString();

            var apart = MeasureObjects(new JObject { ["object_ids"] = new JArray { mAId, mBId } });
            if (apart["clash"].ToObject<bool>())
                throw new Exception("measure_objects reported a clash for boxes 10 apart");
            if (apart["method"]?.ToString() != "brep")
                throw new Exception("measure_objects expected brep method, got " + apart["method"]);
            if (apart["bbox_gap"].ToObject<double>() <= 0)
                throw new Exception("measure_objects expected a positive bbox_gap for separated boxes");

            var overlap = MeasureObjects(new JObject { ["object_ids"] = new JArray { mAId, mCId } });
            if (!overlap["clash"].ToObject<bool>())
                throw new Exception("measure_objects missed a clash for overlapping boxes");
            if (overlap["bbox_gap"].ToObject<double>() != 0.0)
                throw new Exception("measure_objects expected a zero bbox_gap for overlapping boxes");

            // A small box fully inside a large box clashes even though their
            // surfaces never cross (containment).
            var mBig = CreateObject(new JObject
            {
                ["type"] = "BOX", ["name"] = "MCPMeasureBig",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 }
            });
            var mSmall = CreateObject(new JObject
            {
                ["type"] = "BOX", ["name"] = "MCPMeasureSmall",
                ["params"] = new JObject { ["width"] = 2, ["length"] = 2, ["height"] = 2 }
            });
            string mBigId = mBig["id"]?.ToString();
            string mSmallId = mSmall["id"]?.ToString();
            var contained = MeasureObjects(new JObject { ["object_ids"] = new JArray { mBigId, mSmallId } });
            DeleteObject(new JObject { ["id"] = mBigId });
            DeleteObject(new JObject { ["id"] = mSmallId });
            if (!contained["clash"].ToObject<bool>())
                throw new Exception("measure_objects missed containment (small box fully inside big box)");

            DeleteObject(new JObject { ["id"] = mAId });
            DeleteObject(new JObject { ["id"] = mBId });
            DeleteObject(new JObject { ["id"] = mCId });
            results["measure_objects"] = new JObject
            {
                ["status"] = "pass",
                ["gap_apart"] = apart["bbox_gap"]
            };
            VisualUpdate("measure_objects clash + bbox gap");
        }
        catch (Exception e)
        {
            results["measure_objects"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: modify_object with a rotation and a non-uniform scale must not
        // shear. A box rotated 45 deg about Z and scaled 3x in X stays a right
        // box, so its three edge directions at a corner stay mutually
        // perpendicular. Before the fix this sheared to ~0.8 off-orthogonal.
        try
        {
            var sh = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPShearBox",
                ["params"] = new JObject { ["width"] = 2, ["length"] = 2, ["height"] = 2 }
            });
            string shId = sh["id"]?.ToString();
            ModifyObject(new JObject
            {
                ["id"] = shId,
                ["rotation"] = new JArray { 0, 0, Math.PI / 4 },
                ["scale"] = new JArray { 3, 1, 1 }
            });

            var shObj = doc.Objects.Find(new Guid(shId));
            var shBrep = shObj.Geometry as Brep;
            if (shBrep == null)
                throw new Exception("modified object is not a brep");

            double worst = -1.0;
            foreach (var v in shBrep.Vertices)
            {
                var ei = v.EdgeIndices();
                if (ei.Length != 3) continue;
                var d = new Vector3d[3];
                for (int k = 0; k < 3; k++)
                {
                    var e = shBrep.Edges[ei[k]];
                    Point3d p0 = e.PointAtStart, p1 = e.PointAtEnd;
                    var dir = v.Location.DistanceTo(p0) <= v.Location.DistanceTo(p1)
                        ? p1 - v.Location
                        : p0 - v.Location;
                    dir.Unitize();
                    d[k] = dir;
                }
                worst = Math.Max(Math.Abs(d[0] * d[1]), Math.Max(Math.Abs(d[1] * d[2]), Math.Abs(d[0] * d[2])));
                break;
            }

            DeleteObject(new JObject { ["id"] = shId });
            if (worst < 0)
                throw new Exception("could not find a 3-edge vertex on the modified box");
            if (worst > 1e-6)
                throw new Exception("modify_object sheared the box: max off-orthogonality " + worst);
            results["modify_object_no_shear"] = new JObject { ["status"] = "pass", ["max_offorth"] = worst };
            VisualUpdate("modify_object rotation + scale stays orthogonal");
        }
        catch (Exception e)
        {
            results["modify_object_no_shear"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: get_document_summary.object_count reports active objects only, so
        // it equals objects_by_type and is not inflated by undoable-deleted
        // entries. Create three, delete one (leaving a tombstone), and check.
        try
        {
            var beforeSummary = GetDocumentSummary(new JObject());
            int beforeCount = (int)beforeSummary["object_count"];
            var countIds = new string[3];
            for (int i = 0; i < 3; i++)
            {
                var o = CreateObject(new JObject
                {
                    ["type"] = "BOX",
                    ["name"] = "MCPCountProbe" + i,
                    ["params"] = new JObject { ["width"] = 1, ["length"] = 1, ["height"] = 1 }
                });
                countIds[i] = o["id"]?.ToString();
            }
            DeleteObject(new JObject { ["id"] = countIds[0] });   // leaves an undoable tombstone
            var afterSummary = GetDocumentSummary(new JObject());
            int afterCount = (int)afterSummary["object_count"];
            int typeSum = 0;
            foreach (var kv in (JObject)afterSummary["objects_by_type"]) typeSum += (int)kv.Value;
            DeleteObject(new JObject { ["id"] = countIds[1] });
            DeleteObject(new JObject { ["id"] = countIds[2] });
            if (afterCount != typeSum)
                throw new Exception("object_count " + afterCount + " != objects_by_type sum " + typeSum);
            if (afterCount != beforeCount + 2)
                throw new Exception("object_count net change wrong: " + beforeCount + " -> " + afterCount);
            results["live_object_count"] = new JObject { ["status"] = "pass", ["count"] = afterCount };
            VisualUpdate("object_count counts active objects, matches breakdown");
        }
        catch (Exception e)
        {
            results["live_object_count"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: describe_capabilities reports the live dispatch table with
        // read-only and dry_run flags, the perception envelope flags, and the
        // version. The command list is reflection-driven, so it must include the
        // commands we exercise here and describe_capabilities itself, with the
        // flags the dispatcher gates on. A client reads supports_dry_run before
        // sending a preview, so a wrong flag here would cost source objects.
        try
        {
            var caps = DescribeCapabilities(new JObject());
            var cmds = (JArray)caps["commands"];
            if ((int)caps["command_count"] != cmds.Count)
                throw new Exception("command_count does not match the commands array length");
            if (string.IsNullOrWhiteSpace(caps["version"]?.ToString()))
                throw new Exception("version is empty");

            var readOnly = new System.Collections.Generic.Dictionary<string, bool>();
            var dryRun = new System.Collections.Generic.Dictionary<string, bool>();
            foreach (var c in cmds)
            {
                readOnly[c["name"].ToString()] = (bool)c["read_only"];
                dryRun[c["name"].ToString()] = (bool)c["supports_dry_run"];
            }

            if (!readOnly.ContainsKey("describe_capabilities") || !readOnly["describe_capabilities"])
                throw new Exception("describe_capabilities should list itself as read_only");
            if (!readOnly.ContainsKey("create_object") || readOnly["create_object"])
                throw new Exception("create_object should be present and not read_only");
            if (!readOnly.ContainsKey("get_document_summary") || !readOnly["get_document_summary"])
                throw new Exception("get_document_summary should be present and read_only");

            foreach (var booleanCmd in new[] { "boolean_union", "boolean_difference", "boolean_intersection" })
            {
                if (!dryRun.ContainsKey(booleanCmd) || !dryRun[booleanCmd])
                    throw new Exception(booleanCmd + " should advertise supports_dry_run");
            }
            if (!dryRun.ContainsKey("create_object") || dryRun["create_object"])
                throw new Exception("create_object should be present and not advertise supports_dry_run");

            bool hasDelta = false, hasHealth = false;
            foreach (var f in (JArray)caps["perception"]["envelope_flags"])
            {
                if (f["flag"]?.ToString() == "include_delta") hasDelta = true;
                if (f["flag"]?.ToString() == "include_health") hasHealth = true;
            }
            if (!hasDelta)
                throw new Exception("perception should advertise include_delta");
            if (!hasHealth)
                throw new Exception("perception should advertise include_health");

            results["describe_capabilities"] = new JObject
            {
                ["status"] = "pass",
                ["command_count"] = (int)caps["command_count"],
                ["version"] = caps["version"]
            };
            VisualUpdate("describe_capabilities lists the command surface");
        }
        catch (Exception e)
        {
            results["describe_capabilities"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: section_profile cuts a plane through objects and measures the
        // cross-section without creating anything. A 4x2x2 box centred on the
        // origin, cut at Z=0, gives one closed loop of area 8. Two boxes cut
        // together give two loops whose areas sum. An open surface cut gives an
        // open section with a perimeter and no area. A profile of a prismatic box
        // gives `count` equal-area slices.
        try
        {
            var sBoxA = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPSectionBoxA",
                ["params"] = new JObject { ["width"] = 4, ["length"] = 2, ["height"] = 2 }
            });
            var sBoxB = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPSectionBoxB",
                ["params"] = new JObject { ["width"] = 2, ["length"] = 2, ["height"] = 2 },
                ["translation"] = new JArray { 10, 0, 0 }
            });
            string sAId = sBoxA["id"]?.ToString();
            string sBId = sBoxB["id"]?.ToString();

            // Single box at mid-height: one closed loop, area = 4 * 2 = 8.
            var oneCut = SectionProfile(new JObject
            {
                ["id"] = sAId,
                ["plane"] = new JObject { ["axis"] = "Z", ["value"] = 0 }
            });
            if (oneCut["mode"]?.ToString() != "plane")
                throw new Exception("section_profile mode was not 'plane'");
            var profA = (JObject)((JArray)oneCut["profiles"])[0];
            if ((int)profA["loop_count"] != 1)
                throw new Exception("section_profile expected 1 loop on a box, got " + profA["loop_count"]);
            double areaA = (double)profA["section_area"];
            if (Math.Abs(areaA - 8.0) > 1e-6)
                throw new Exception("section_profile box area expected 8, got " + areaA);
            if (!(bool)((JObject)((JArray)profA["loops"])[0])["closed"])
                throw new Exception("section_profile box loop should be closed");

            // Two boxes cut together: two loops, areas summed (8 + 4 = 12).
            var twoCut = SectionProfile(new JObject
            {
                ["object_ids"] = new JArray { sAId, sBId },
                ["plane"] = new JObject { ["axis"] = "Z", ["value"] = 0 }
            });
            if ((int)twoCut["total_loop_count"] != 2)
                throw new Exception("section_profile expected 2 loops across two boxes");
            double total = (double)twoCut["total_section_area"];
            if (Math.Abs(total - 12.0) > 1e-6)
                throw new Exception("section_profile two-box total area expected 12, got " + total);

            // Open surface: a vertical bilinear quad cut by a horizontal plane is
            // an open section, so it must report a perimeter and no area.
            var sSurf = CreateObject(new JObject
            {
                ["type"] = "SURFACE",
                ["name"] = "MCPSectionSurface",
                ["params"] = new JObject
                {
                    ["count"] = new JArray { 2, 2 },
                    ["degree"] = new JArray { 1, 1 },
                    ["points"] = new JArray
                    {
                        new JArray { 0, 0, -1 }, new JArray { 4, 0, -1 },
                        new JArray { 0, 0, 1 }, new JArray { 4, 0, 1 }
                    }
                }
            });
            string sSurfId = sSurf["id"]?.ToString();
            var surfCut = SectionProfile(new JObject
            {
                ["id"] = sSurfId,
                ["plane"] = new JObject { ["axis"] = "Z", ["value"] = 0 }
            });
            var surfProf = (JObject)((JArray)surfCut["profiles"])[0];
            if ((double)surfProf["section_area"] != 0.0)
                throw new Exception("section_profile open surface must report no area");
            foreach (var l in (JArray)surfProf["loops"])
                if ((bool)((JObject)l)["closed"])
                    throw new Exception("section_profile open surface should not report a closed loop");

            // Profile mode: a prismatic box sliced along Z gives `count` equal slices.
            var prof = SectionProfile(new JObject
            {
                ["id"] = sAId,
                ["profile"] = new JObject { ["axis"] = "Z", ["count"] = 4 }
            });
            if (prof["mode"]?.ToString() != "profile")
                throw new Exception("section_profile profile mode label wrong");
            var slices = (JArray)prof["sections"];
            if (slices.Count != 4)
                throw new Exception("section_profile profile expected 4 slices, got " + slices.Count);
            foreach (var s in slices)
            {
                double sa = (double)((JObject)s)["total_section_area"];
                if (Math.Abs(sa - 8.0) > 1e-6)
                    throw new Exception("section_profile profile slice area expected 8, got " + sa);
            }

            // Hollow solid: a square tube (a 10x10x10 box minus a 6x6 box poking
            // through it) sections to an annulus. The inner loop is a hole, so its
            // area must be subtracted: 10*10 - 6*6 = 64, not 136.
            var tubeBig = CreateObject(new JObject
            {
                ["type"] = "BOX", ["name"] = "MCPSectTubeBig",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 }
            });
            var tubeSmall = CreateObject(new JObject
            {
                ["type"] = "BOX", ["name"] = "MCPSectTubeSmall",
                ["params"] = new JObject { ["width"] = 6, ["length"] = 6, ["height"] = 12 }
            });
            var bd = BooleanDifference(new JObject
            {
                ["base_id"] = tubeBig["id"],
                ["subtract_ids"] = new JArray { tubeSmall["id"] }
            });
            string tubeId = ((JArray)bd["result_ids"])[0].ToString();
            var hollow = SectionProfile(new JObject
            {
                ["id"] = tubeId,
                ["plane"] = new JObject { ["axis"] = "Z", ["value"] = 0 }
            });
            var hp = (JObject)((JArray)hollow["profiles"])[0];
            int holeCount = 0;
            foreach (var l in (JArray)hp["loops"])
                if ((bool)((JObject)l)["is_hole"]) holeCount++;
            double hollowArea = (double)hp["section_area"];
            DeleteObject(new JObject { ["id"] = tubeId });
            if ((int)hp["loop_count"] != 2)
                throw new Exception("section_profile hollow tube expected 2 loops, got " + hp["loop_count"]);
            if (holeCount != 1)
                throw new Exception("section_profile hollow tube expected 1 hole loop, got " + holeCount);
            if (Math.Abs(hollowArea - 64.0) > 1e-3)
                throw new Exception("section_profile hollow area expected 64 (100-36), got " + hollowArea);

            DeleteObject(new JObject { ["id"] = sAId });
            DeleteObject(new JObject { ["id"] = sBId });
            DeleteObject(new JObject { ["id"] = sSurfId });
            results["section_profile"] = new JObject
            {
                ["status"] = "pass",
                ["box_area"] = areaA,
                ["two_box_total"] = total
            };
            VisualUpdate("section_profile cross-section area + profile");
        }
        catch (Exception e)
        {
            results["section_profile"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: boolean_union must reject a non-brep input instead of silently
        // deleting it. Two overlapping boxes plus a line: the union appended
        // every input to the delete list before extracting a brep, so under the
        // default delete_sources it destroyed the line. It must now throw and
        // leave all three inputs in the document.
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 170, 0, 0 };
            var ub1 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPBoolRejectUnionBox1",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos
            });
            var pos2 = new JArray { ((JArray)pos)[0].ToObject<double>() + 5, ((JArray)pos)[1].ToObject<double>(), 0 };
            var ub2 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPBoolRejectUnionBox2",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos2
            });
            var uLine = CreateObject(new JObject
            {
                ["type"] = "LINE",
                ["name"] = "MCPBoolRejectUnionLine",
                ["params"] = new JObject { ["start"] = new JArray { 0, 0, 0 }, ["end"] = new JArray { 10, 10, 0 } },
                ["translation"] = pos
            });
            string ub1Id = ub1["id"]?.ToString();
            string ub2Id = ub2["id"]?.ToString();
            string uLineId = uLine["id"]?.ToString();

            bool threw = false;
            try
            {
                BooleanUnion(new JObject
                {
                    ["object_ids"] = new JArray { ub1Id, ub2Id, uLineId },
                    ["delete_sources"] = true
                });
            }
            catch (Exception)
            {
                threw = true;
            }

            bool allResolve = doc.Objects.Find(new Guid(ub1Id)) != null
                && doc.Objects.Find(new Guid(ub2Id)) != null
                && doc.Objects.Find(new Guid(uLineId)) != null;

            DeleteObject(new JObject { ["id"] = ub1Id });
            DeleteObject(new JObject { ["id"] = ub2Id });
            DeleteObject(new JObject { ["id"] = uLineId });

            if (!threw)
                throw new Exception("boolean_union accepted a non-brep input instead of throwing");
            if (!allResolve)
                throw new Exception("boolean_union deleted an input after rejecting a non-brep");
            results["boolean_union_rejects_non_brep"] = new JObject { ["status"] = "pass" };
            VisualUpdate("boolean_union rejects a non-brep and deletes nothing");
        }
        catch (Exception e)
        {
            results["boolean_union_rejects_non_brep"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: boolean_difference must reject a non-brep in subtract_ids the
        // same way, leaving the base and both subtract inputs in the document.
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 190, 0, 0 };
            var dBase = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPBoolRejectDiffBase",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos
            });
            var pos2 = new JArray { ((JArray)pos)[0].ToObject<double>() + 5, ((JArray)pos)[1].ToObject<double>(), 0 };
            var dSub = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPBoolRejectDiffSub",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos2
            });
            var dLine = CreateObject(new JObject
            {
                ["type"] = "LINE",
                ["name"] = "MCPBoolRejectDiffLine",
                ["params"] = new JObject { ["start"] = new JArray { 0, 0, 0 }, ["end"] = new JArray { 10, 10, 0 } },
                ["translation"] = pos
            });
            string dBaseId = dBase["id"]?.ToString();
            string dSubId = dSub["id"]?.ToString();
            string dLineId = dLine["id"]?.ToString();

            bool threw = false;
            try
            {
                BooleanDifference(new JObject
                {
                    ["base_id"] = dBaseId,
                    ["subtract_ids"] = new JArray { dSubId, dLineId },
                    ["delete_sources"] = true
                });
            }
            catch (Exception)
            {
                threw = true;
            }

            bool allResolve = doc.Objects.Find(new Guid(dBaseId)) != null
                && doc.Objects.Find(new Guid(dSubId)) != null
                && doc.Objects.Find(new Guid(dLineId)) != null;

            DeleteObject(new JObject { ["id"] = dBaseId });
            DeleteObject(new JObject { ["id"] = dSubId });
            DeleteObject(new JObject { ["id"] = dLineId });

            if (!threw)
                throw new Exception("boolean_difference accepted a non-brep subtract input instead of throwing");
            if (!allResolve)
                throw new Exception("boolean_difference deleted an input after rejecting a non-brep");
            results["boolean_difference_rejects_non_brep"] = new JObject { ["status"] = "pass" };
            VisualUpdate("boolean_difference rejects a non-brep and deletes nothing");
        }
        catch (Exception e)
        {
            results["boolean_difference_rejects_non_brep"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: boolean_intersection must reject a non-brep input the same way,
        // leaving both boxes and the line in the document.
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 210, 0, 0 };
            var ib1 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPBoolRejectIntBox1",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos
            });
            var pos2 = new JArray { ((JArray)pos)[0].ToObject<double>() + 5, ((JArray)pos)[1].ToObject<double>(), 0 };
            var ib2 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPBoolRejectIntBox2",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos2
            });
            var iLine = CreateObject(new JObject
            {
                ["type"] = "LINE",
                ["name"] = "MCPBoolRejectIntLine",
                ["params"] = new JObject { ["start"] = new JArray { 0, 0, 0 }, ["end"] = new JArray { 10, 10, 0 } },
                ["translation"] = pos
            });
            string ib1Id = ib1["id"]?.ToString();
            string ib2Id = ib2["id"]?.ToString();
            string iLineId = iLine["id"]?.ToString();

            bool threw = false;
            try
            {
                BooleanIntersection(new JObject
                {
                    ["object_ids"] = new JArray { ib1Id, ib2Id, iLineId },
                    ["delete_sources"] = true
                });
            }
            catch (Exception)
            {
                threw = true;
            }

            bool allResolve = doc.Objects.Find(new Guid(ib1Id)) != null
                && doc.Objects.Find(new Guid(ib2Id)) != null
                && doc.Objects.Find(new Guid(iLineId)) != null;

            DeleteObject(new JObject { ["id"] = ib1Id });
            DeleteObject(new JObject { ["id"] = ib2Id });
            DeleteObject(new JObject { ["id"] = iLineId });

            if (!threw)
                throw new Exception("boolean_intersection accepted a non-brep input instead of throwing");
            if (!allResolve)
                throw new Exception("boolean_intersection deleted an input after rejecting a non-brep");
            results["boolean_intersection_rejects_non_brep"] = new JObject { ["status"] = "pass" };
            VisualUpdate("boolean_intersection rejects a non-brep and deletes nothing");
        }
        catch (Exception e)
        {
            results["boolean_intersection_rejects_non_brep"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: a dry_run boolean previews the result Brep's metrics and leaves
        // the document untouched, then a real run on the same inputs commits.
        // Two 10-unit boxes overlapping by 5 along X share full Y and Z extents,
        // so their union is a single 15x10x10 solid (volume 1500); the prediction
        // reports that count, solidity, and volume while adding and deleting
        // nothing.
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 230, 0, 0 };
            var db1 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPDryRunBox1",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos
            });
            var pos2 = new JArray { ((JArray)pos)[0].ToObject<double>() + 5, ((JArray)pos)[1].ToObject<double>(), 0 };
            var db2 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPDryRunBox2",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos2
            });
            string db1Id = db1["id"]?.ToString();
            string db2Id = db2["id"]?.ToString();

            var before = SnapshotObjectIds(doc);
            var prediction = BooleanUnion(new JObject
            {
                ["object_ids"] = new JArray { db1Id, db2Id },
                ["dry_run"] = true
            });
            var after = SnapshotObjectIds(doc);

            bool predDryRun = prediction["dry_run"]?.ToObject<bool>() ?? false;
            bool predWouldSucceed = prediction["would_succeed"]?.ToObject<bool>() ?? false;
            bool predHasResultIds = prediction["result_ids"] != null;
            int predCount = prediction["count"]?.ToObject<int>() ?? 0;
            var predResults = prediction["results"] as JArray;
            JObject predFirst = (predResults != null && predResults.Count > 0) ? (JObject)predResults[0] : null;
            bool predValid = predFirst?["valid"]?.ToObject<bool>() ?? false;
            bool predIsSolid = predFirst?["is_solid"]?.ToObject<bool>() ?? false;
            bool predHasArea = predFirst?["area"] != null;
            bool predHasBBox = predFirst?["bounding_box"] != null;
            double predVolume = predFirst?["volume"]?.ToObject<double>() ?? 0;

            bool inputsRemain = doc.Objects.Find(new Guid(db1Id)) != null
                && doc.Objects.Find(new Guid(db2Id)) != null;
            bool docUnchanged = before.SetEquals(after);

            var real = BooleanUnion(new JObject
            {
                ["object_ids"] = new JArray { db1Id, db2Id },
                ["name"] = "MCPDryRunUnionResult",
                ["delete_sources"] = true
            });
            int realCount = real["count"]?.ToObject<int>() ?? 0;

            DeleteObject(new JObject { ["name"] = "MCPDryRunUnionResult" });
            if (doc.Objects.Find(new Guid(db1Id)) != null) DeleteObject(new JObject { ["id"] = db1Id });
            if (doc.Objects.Find(new Guid(db2Id)) != null) DeleteObject(new JObject { ["id"] = db2Id });

            if (!predDryRun)
                throw new Exception("dry_run union response missing dry_run=true");
            if (!predWouldSucceed)
                throw new Exception("dry_run union did not report would_succeed");
            if (predHasResultIds)
                throw new Exception("dry_run union returned result_ids instead of a prediction");
            if (predCount != 1)
                throw new Exception($"dry_run union predicted count {predCount}, expected 1");
            if (predFirst == null)
                throw new Exception("dry_run union prediction had no result entry");
            if (!predValid)
                throw new Exception("dry_run union predicted an invalid result");
            if (!predIsSolid)
                throw new Exception("dry_run union predicted a non-solid result");
            if (!predHasArea)
                throw new Exception("dry_run union prediction missing area");
            if (!predHasBBox)
                throw new Exception("dry_run union prediction missing bounding_box");
            if (Math.Abs(predVolume - 1500.0) > 1.0)
                throw new Exception($"dry_run union predicted volume {predVolume}, expected ~1500");
            if (!inputsRemain)
                throw new Exception("dry_run union deleted an input");
            if (!docUnchanged)
                throw new Exception("dry_run union changed the document object set");
            if (realCount != 1)
                throw new Exception($"real union after dry_run created {realCount} object(s), expected 1");
            results["boolean_dry_run_predicts_and_leaves_doc"] = new JObject { ["status"] = "pass", ["predicted_volume"] = predVolume };
            VisualUpdate("dry_run union predicts metrics and leaves the document");
        }
        catch (Exception e)
        {
            results["boolean_dry_run_predicts_and_leaves_doc"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test: dry_run also previews difference and intersection without mutating
        // the document, returning the same prediction envelope and no result_ids.
        try
        {
            var pos = visualMode ? GetNextPosition() : new JArray { 250, 0, 0 };
            var dBase = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPDryRunDiffBase",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = pos
            });
            var dSub = CreateObject(new JObject
            {
                ["type"] = "SPHERE",
                ["name"] = "MCPDryRunDiffSub",
                ["params"] = new JObject { ["radius"] = 6 },
                ["translation"] = pos
            });
            string dBaseId = dBase["id"]?.ToString();
            string dSubId = dSub["id"]?.ToString();

            var beforeDiff = SnapshotObjectIds(doc);
            var diffPrediction = BooleanDifference(new JObject
            {
                ["base_id"] = dBaseId,
                ["subtract_ids"] = new JArray { dSubId },
                ["dry_run"] = true
            });
            var afterDiff = SnapshotObjectIds(doc);

            bool diffDryRun = diffPrediction["dry_run"]?.ToObject<bool>() ?? false;
            bool diffHasResultIds = diffPrediction["result_ids"] != null;
            int diffCount = diffPrediction["count"]?.ToObject<int>() ?? 0;
            var diffResults = diffPrediction["results"] as JArray;
            bool diffHasBBox = diffResults != null && diffResults.Count > 0 && diffResults[0]["bounding_box"] != null;
            bool diffDocUnchanged = beforeDiff.SetEquals(afterDiff);
            bool diffInputsRemain = doc.Objects.Find(new Guid(dBaseId)) != null
                && doc.Objects.Find(new Guid(dSubId)) != null;

            var ipos = visualMode ? GetNextPosition() : new JArray { 270, 0, 0 };
            var ib1 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPDryRunIntBox1",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = ipos
            });
            var ipos2 = new JArray { ((JArray)ipos)[0].ToObject<double>() + 5, ((JArray)ipos)[1].ToObject<double>(), 0 };
            var ib2 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPDryRunIntBox2",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = ipos2
            });
            string ib1Id = ib1["id"]?.ToString();
            string ib2Id = ib2["id"]?.ToString();

            var beforeInt = SnapshotObjectIds(doc);
            var intPrediction = BooleanIntersection(new JObject
            {
                ["object_ids"] = new JArray { ib1Id, ib2Id },
                ["dry_run"] = true
            });
            var afterInt = SnapshotObjectIds(doc);

            bool intDryRun = intPrediction["dry_run"]?.ToObject<bool>() ?? false;
            bool intHasResultIds = intPrediction["result_ids"] != null;
            int intCount = intPrediction["count"]?.ToObject<int>() ?? 0;
            var intResults = intPrediction["results"] as JArray;
            JObject intFirst = (intResults != null && intResults.Count > 0) ? (JObject)intResults[0] : null;
            bool intIsSolid = intFirst?["is_solid"]?.ToObject<bool>() ?? false;
            double intVolume = intFirst?["volume"]?.ToObject<double>() ?? 0;
            bool intDocUnchanged = beforeInt.SetEquals(afterInt);
            bool intInputsRemain = doc.Objects.Find(new Guid(ib1Id)) != null
                && doc.Objects.Find(new Guid(ib2Id)) != null;

            DeleteObject(new JObject { ["id"] = dBaseId });
            DeleteObject(new JObject { ["id"] = dSubId });
            DeleteObject(new JObject { ["id"] = ib1Id });
            DeleteObject(new JObject { ["id"] = ib2Id });

            if (!diffDryRun)
                throw new Exception("dry_run difference missing dry_run=true");
            if (diffHasResultIds)
                throw new Exception("dry_run difference returned result_ids instead of a prediction");
            if (diffCount < 1)
                throw new Exception("dry_run difference predicted no result");
            if (!diffHasBBox)
                throw new Exception("dry_run difference prediction missing bounding_box");
            if (!diffDocUnchanged)
                throw new Exception("dry_run difference changed the document object set");
            if (!diffInputsRemain)
                throw new Exception("dry_run difference deleted an input");
            if (!intDryRun)
                throw new Exception("dry_run intersection missing dry_run=true");
            if (intHasResultIds)
                throw new Exception("dry_run intersection returned result_ids instead of a prediction");
            if (intCount < 1)
                throw new Exception("dry_run intersection predicted no result");
            if (intFirst == null)
                throw new Exception("dry_run intersection prediction had no result entry");
            if (!intIsSolid)
                throw new Exception("dry_run intersection predicted a non-solid result");
            if (intVolume <= 0)
                throw new Exception($"dry_run intersection predicted volume {intVolume}, expected a positive solid volume");
            if (!intDocUnchanged)
                throw new Exception("dry_run intersection changed the document object set");
            if (!intInputsRemain)
                throw new Exception("dry_run intersection deleted an input");
            results["boolean_dry_run_difference_and_intersection"] = new JObject { ["status"] = "pass" };
            VisualUpdate("dry_run difference and intersection preview without mutating");
        }
        catch (Exception e)
        {
            results["boolean_dry_run_difference_and_intersection"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Cleanup
        if (!visualMode)
        {
            try
            {
                DeleteObject(new JObject { ["name"] = "MCPTestBoxRenamed" });
                DeleteObject(new JObject { ["name"] = "MCPBatchBox1" });
                DeleteObject(new JObject { ["name"] = "MCPBatchBox2" });
                DeleteObject(new JObject { ["name"] = "BooleanUnionResult" });
                DeleteObject(new JObject { ["name"] = "BooleanDiffResult" });
                DeleteObject(new JObject { ["name"] = "BooleanIntersectResult" });
                DeleteObject(new JObject { ["name"] = "UndoTestBox" });
                DeleteObject(new JObject { ["name"] = "ProjTarget" });
                DeleteObject(new JObject { ["name"] = "ProjSource" });
                DeleteObject(new JObject { ["name"] = "ProjectedCurve" });
                DeleteObject(new JObject { ["name"] = "IntLine1" });
                DeleteObject(new JObject { ["name"] = "IntLine2" });
                DeleteObject(new JObject { ["name"] = "IntersectionPoint_point" });
                DeleteObject(new JObject { ["name"] = "SplitSegment" });
                DeleteObject(new JObject { ["name"] = "MCPDeltaProbe" });
                DeleteObject(new JObject { ["name"] = "MCPHealthOk" });
                DeleteObject(new JObject { ["name"] = "MCPMeasureA" });
                DeleteObject(new JObject { ["name"] = "MCPMeasureB" });
                DeleteObject(new JObject { ["name"] = "MCPMeasureC" });
                DeleteObject(new JObject { ["name"] = "MCPMeasureBig" });
                DeleteObject(new JObject { ["name"] = "MCPMeasureSmall" });
                DeleteObject(new JObject { ["name"] = "MCPShearBox" });
                DeleteObject(new JObject { ["name"] = "MCPCountProbe0" });
                DeleteObject(new JObject { ["name"] = "MCPCountProbe1" });
                DeleteObject(new JObject { ["name"] = "MCPCountProbe2" });
                DeleteObject(new JObject { ["name"] = "MCPSectionBoxA" });
                DeleteObject(new JObject { ["name"] = "MCPSectionBoxB" });
                DeleteObject(new JObject { ["name"] = "MCPSectionSurface" });
                DeleteObject(new JObject { ["name"] = "MCPSectTubeBig" });
                DeleteObject(new JObject { ["name"] = "MCPSectTubeSmall" });
                DeleteObject(new JObject { ["name"] = "MCPBoolRejectUnionBox1" });
                DeleteObject(new JObject { ["name"] = "MCPBoolRejectUnionBox2" });
                DeleteObject(new JObject { ["name"] = "MCPBoolRejectUnionLine" });
                DeleteObject(new JObject { ["name"] = "MCPBoolRejectDiffBase" });
                DeleteObject(new JObject { ["name"] = "MCPBoolRejectDiffSub" });
                DeleteObject(new JObject { ["name"] = "MCPBoolRejectDiffLine" });
                DeleteObject(new JObject { ["name"] = "MCPBoolRejectIntBox1" });
                DeleteObject(new JObject { ["name"] = "MCPBoolRejectIntBox2" });
                DeleteObject(new JObject { ["name"] = "MCPBoolRejectIntLine" });
                DeleteObject(new JObject { ["name"] = "MCPDryRunBox1" });
                DeleteObject(new JObject { ["name"] = "MCPDryRunBox2" });
                DeleteObject(new JObject { ["name"] = "MCPDryRunUnionResult" });
                DeleteObject(new JObject { ["name"] = "MCPDryRunDiffBase" });
                DeleteObject(new JObject { ["name"] = "MCPDryRunDiffSub" });
                DeleteObject(new JObject { ["name"] = "MCPDryRunIntBox1" });
                DeleteObject(new JObject { ["name"] = "MCPDryRunIntBox2" });
            }
            catch
            {
                // Ignore cleanup errors
            }
        }
        else
        {
            RhinoApp.WriteLine("Visual mode: Test objects left in document for inspection");
            doc.Views.Redraw();
            foreach (var view in doc.Views)
            {
                view.ActiveViewport.ZoomExtents();
            }
        }

        return results;
    }
}
