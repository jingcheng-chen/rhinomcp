using System;
using System.Threading;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Display;

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

            // zoom_to_fit moves the camera; a correct ReadOnly handler restores it.
            string nameBefore = activeViewport.Name;
            var before = new Rhino.DocObjects.ViewportInfo(activeViewport);
            before.GetFrustum(out double bl, out double br, out double bb, out double bt, out _, out _);

            CaptureViewport(new JObject
            {
                ["viewport"] = "active",
                ["zoom_to_fit"] = true,
                ["width"] = 200,
                ["height"] = 200
            });

            var after = new Rhino.DocObjects.ViewportInfo(activeViewport);
            after.GetFrustum(out double al, out double ar, out double ab, out double at, out _, out _);

            double cameraDrift = before.CameraLocation.DistanceTo(after.CameraLocation);
            double frustumDrift = Math.Abs(bl - al) + Math.Abs(br - ar) + Math.Abs(bb - ab) + Math.Abs(bt - at);
            bool nameKept = activeViewport.Name == nameBefore;
            if (cameraDrift > 1e-6 || frustumDrift > 1e-6 || !nameKept)
                throw new Exception($"capture_viewport changed the active view (cameraDrift={cameraDrift:G4}, frustumDrift={frustumDrift:G4}, nameKept={nameKept})");

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
                DeleteObject(new JObject { ["name"] = "MCPMeasureA" });
                DeleteObject(new JObject { ["name"] = "MCPMeasureB" });
                DeleteObject(new JObject { ["name"] = "MCPMeasureC" });
                DeleteObject(new JObject { ["name"] = "MCPMeasureBig" });
                DeleteObject(new JObject { ["name"] = "MCPMeasureSmall" });
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
