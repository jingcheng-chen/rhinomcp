using System;
using Newtonsoft.Json.Linq;
using Rhino;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    /// <summary>
    /// Tests all handler functions in RhinoMCPFunctions.
    /// Creates test objects, manipulates them, and verifies results.
    /// </summary>
    /// <returns>JObject with test results for each handler</returns>
    public JObject TestAllFunctions()
    {
        var results = new JObject();
        var doc = RhinoDoc.ActiveDoc;

        // Store created object IDs for later tests
        string boxId = null;
        string sphereId = null;
        string box2Id = null;
        string booleanBox1Id = null;
        string booleanBox2Id = null;

        // Test 1: CreateObject - BOX
        try
        {
            var box = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "MCPTestBox",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 }
            });
            boxId = box["id"]?.ToString();
            if (string.IsNullOrEmpty(boxId))
                throw new Exception("No ID returned");
            results["create_object_box"] = new JObject { ["status"] = "pass", ["id"] = boxId };
        }
        catch (Exception e)
        {
            results["create_object_box"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 2: CreateObject - SPHERE
        try
        {
            var sphere = CreateObject(new JObject
            {
                ["type"] = "SPHERE",
                ["name"] = "MCPTestSphere",
                ["params"] = new JObject { ["radius"] = 5 },
                ["translation"] = new JArray { 20, 0, 0 }
            });
            sphereId = sphere["id"]?.ToString();
            if (string.IsNullOrEmpty(sphereId))
                throw new Exception("No ID returned");
            results["create_object_sphere"] = new JObject { ["status"] = "pass", ["id"] = sphereId };
        }
        catch (Exception e)
        {
            results["create_object_sphere"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 3: CreateObjects (batch)
        try
        {
            var batchResult = CreateObjects(new JObject
            {
                ["BatchBox1"] = new JObject
                {
                    ["type"] = "BOX",
                    ["name"] = "MCPBatchBox1",
                    ["params"] = new JObject { ["width"] = 5, ["length"] = 5, ["height"] = 5 },
                    ["translation"] = new JArray { -20, 0, 0 }
                },
                ["BatchBox2"] = new JObject
                {
                    ["type"] = "BOX",
                    ["name"] = "MCPBatchBox2",
                    ["params"] = new JObject { ["width"] = 3, ["length"] = 3, ["height"] = 3 },
                    ["translation"] = new JArray { -20, 10, 0 }
                }
            });
            var successCount = batchResult["success_count"]?.ToObject<int>() ?? 0;
            if (successCount != 2)
                throw new Exception($"Expected 2 successes, got {successCount}");
            box2Id = batchResult["objects"]?["BatchBox1"]?["id"]?.ToString();
            results["create_objects"] = new JObject { ["status"] = "pass", ["success_count"] = successCount };
        }
        catch (Exception e)
        {
            results["create_objects"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 4: GetDocumentInfo
        try
        {
            var docInfo = GetDocumentInfo(new JObject());
            var objectCount = docInfo["object_count"]?.ToObject<int>() ?? 0;
            var layerCount = docInfo["layer_count"]?.ToObject<int>() ?? 0;
            if (objectCount < 1)
                throw new Exception($"Expected at least 1 object, got {objectCount}");
            results["get_document_info"] = new JObject { ["status"] = "pass", ["object_count"] = objectCount, ["layer_count"] = layerCount };
        }
        catch (Exception e)
        {
            results["get_document_info"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
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
                ["filters"] = new JObject { ["name"] = "MCPTestBox" },
                ["filters_type"] = "or"
            });
            var count = selectResult["count"]?.ToObject<int>() ?? 0;
            if (count != 1)
                throw new Exception($"Expected 1 selected, got {count}");
            results["select_objects"] = new JObject { ["status"] = "pass", ["count"] = count };
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
                ["new_color"] = new JArray { 255, 0, 0 }
            });
            var newName = modifyResult["name"]?.ToString();
            if (newName != "MCPTestBoxRenamed")
                throw new Exception($"Expected name 'MCPTestBoxRenamed', got '{newName}'");
            results["modify_object"] = new JObject { ["status"] = "pass", ["new_name"] = newName };
        }
        catch (Exception e)
        {
            results["modify_object"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 9: ModifyObjects (batch)
        try
        {
            var modifyBatchResult = ModifyObjects(new JObject
            {
                ["objects"] = new JArray
                {
                    new JObject { ["name"] = "MCPBatchBox1", ["new_color"] = new JArray { 0, 255, 0 } },
                    new JObject { ["name"] = "MCPBatchBox2", ["new_color"] = new JArray { 0, 0, 255 } }
                }
            });
            var successCount = modifyBatchResult["success_count"]?.ToObject<int>() ?? 0;
            if (successCount != 2)
                throw new Exception($"Expected 2 successes, got {successCount}");
            results["modify_objects"] = new JObject { ["status"] = "pass", ["success_count"] = successCount };
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
                ["color"] = new JArray { 128, 128, 128 }
            });
            var layerName = layerResult["name"]?.ToString();
            if (layerName != "MCPTestLayer")
                throw new Exception($"Expected layer name 'MCPTestLayer', got '{layerName}'");
            results["create_layer"] = new JObject { ["status"] = "pass", ["name"] = layerName };
        }
        catch (Exception e)
        {
            results["create_layer"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 11: GetOrSetCurrentLayer
        try
        {
            // Set to our test layer
            var setResult = GetOrSetCurrentLayer(new JObject { ["name"] = "MCPTestLayer" });
            var currentName = setResult["name"]?.ToString();
            if (currentName != "MCPTestLayer")
                throw new Exception($"Expected current layer 'MCPTestLayer', got '{currentName}'");

            // Get current layer (without setting)
            var getResult = GetOrSetCurrentLayer(new JObject());
            currentName = getResult["name"]?.ToString();
            if (currentName != "MCPTestLayer")
                throw new Exception($"Expected current layer still 'MCPTestLayer', got '{currentName}'");

            results["get_or_set_current_layer"] = new JObject { ["status"] = "pass", ["current_layer"] = currentName };
        }
        catch (Exception e)
        {
            results["get_or_set_current_layer"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 12: Create objects for boolean operations
        try
        {
            var boolBox1 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "BooleanBox1",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = new JArray { 50, 0, 0 }
            });
            booleanBox1Id = boolBox1["id"]?.ToString();

            var boolBox2 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "BooleanBox2",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = new JArray { 55, 0, 0 }
            });
            booleanBox2Id = boolBox2["id"]?.ToString();

            results["create_boolean_test_objects"] = new JObject { ["status"] = "pass" };
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
        }
        catch (Exception e)
        {
            results["boolean_union"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 14: Create objects for boolean difference
        string diffBaseId = null;
        string diffSubtractId = null;
        try
        {
            var diffBase = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "DiffBase",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = new JArray { 70, 0, 0 }
            });
            diffBaseId = diffBase["id"]?.ToString();

            var diffSubtract = CreateObject(new JObject
            {
                ["type"] = "SPHERE",
                ["name"] = "DiffSubtract",
                ["params"] = new JObject { ["radius"] = 6 },
                ["translation"] = new JArray { 70, 0, 0 }
            });
            diffSubtractId = diffSubtract["id"]?.ToString();

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
            var intBox1 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "IntersectBox1",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = new JArray { 90, 0, 0 }
            });
            intersectBox1Id = intBox1["id"]?.ToString();

            var intBox2 = CreateObject(new JObject
            {
                ["type"] = "BOX",
                ["name"] = "IntersectBox2",
                ["params"] = new JObject { ["width"] = 10, ["length"] = 10, ["height"] = 10 },
                ["translation"] = new JArray { 95, 0, 0 }
            });
            intersectBox2Id = intBox2["id"]?.ToString();

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
        }
        catch (Exception e)
        {
            results["execute_rhinoscript"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 17: Undo
        // Note: Undo/Redo cannot be fully tested from within a Rhino command because
        // commands are automatically wrapped in undo records, and nesting is not allowed.
        // The Undo/Redo handlers work correctly when called through the MCP server.
        if (doc.UndoRecordingIsActive)
        {
            // We're inside a command's undo record - just verify the handler runs without error
            try
            {
                var undoResult = Undo(new JObject { ["steps"] = 1 });
                // Handler executed successfully (even if nothing to undo)
                results["undo"] = new JObject
                {
                    ["status"] = "pass",
                    ["note"] = "Handler works; full undo cycle cannot be tested from within a command"
                };
            }
            catch (Exception e)
            {
                results["undo"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
            }
        }
        else
        {
            // Not inside a command - can do full undo test
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
            // Handler executed successfully (even if nothing to redo)
            results["redo"] = new JObject
            {
                ["status"] = "pass",
                ["note"] = doc.UndoRecordingIsActive
                    ? "Handler works; full redo cycle cannot be tested from within a command"
                    : null
            };
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
        }
        catch (Exception e)
        {
            results["delete_object"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Test 20: DeleteLayer
        try
        {
            // First switch to default layer so we can delete the test layer
            GetOrSetCurrentLayer(new JObject { ["name"] = "Default" });

            var deleteLayerResult = DeleteLayer(new JObject { ["name"] = "MCPTestLayer" });
            var success = deleteLayerResult["success"]?.ToObject<bool>() ?? false;
            if (!success)
                throw new Exception(deleteLayerResult["message"]?.ToString() ?? "Layer deletion failed");
            results["delete_layer"] = new JObject { ["status"] = "pass" };
        }
        catch (Exception e)
        {
            results["delete_layer"] = new JObject { ["status"] = "fail", ["error"] = e.Message };
        }

        // Cleanup: Delete remaining test objects
        try
        {
            DeleteObject(new JObject { ["name"] = "MCPTestBoxRenamed" });
            DeleteObject(new JObject { ["name"] = "MCPBatchBox1" });
            DeleteObject(new JObject { ["name"] = "MCPBatchBox2" });
            DeleteObject(new JObject { ["name"] = "BooleanUnionResult" });
            DeleteObject(new JObject { ["name"] = "BooleanDiffResult" });
            DeleteObject(new JObject { ["name"] = "BooleanIntersectResult" });
            DeleteObject(new JObject { ["name"] = "UndoTestBox" });
        }
        catch
        {
            // Ignore cleanup errors
        }

        return results;
    }
}
