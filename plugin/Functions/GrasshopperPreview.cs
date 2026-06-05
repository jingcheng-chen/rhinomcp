using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Special;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Display;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("gh_capture_preview", ReadOnly = true)]
    public JObject GhCapturePreview(JObject parameters)
    {
        var stopwatch = Stopwatch.StartNew();
        var rhinoDoc = RhinoDoc.ActiveDoc;
        if (rhinoDoc == null)
        {
            throw new InvalidOperationException("No active Rhino document. Please open or create a document.");
        }

        bool openCanvas = OptionalBool(parameters, "open_canvas", true);
        bool recompute = OptionalBool(parameters, "recompute", true);
        var doc = GetActiveGrasshopperDocument(openCanvas: openCanvas, makeActive: true);
        string graphId = OptionalString(parameters, "graph_id");
        bool includeHidden = OptionalBool(parameters, "include_hidden", false);

        string viewportTarget = parameters["viewport"]?.ToString()?.ToLower() ?? "perspective";
        int width = Clamp(parameters["width"]?.ToObject<int?>() ?? 800, 100, 4096);
        int height = Clamp(parameters["height"]?.ToObject<int?>() ?? 600, 100, 4096);
        bool showGrid = OptionalBool(parameters, "show_grid", true);
        bool showAxes = OptionalBool(parameters, "show_axes", true);
        bool showCplaneAxes = OptionalBool(parameters, "show_cplane_axes", false);
        double paddingFactor = Math.Max(1.0, parameters["padding_factor"]?.ToObject<double?>() ?? 1.15);

        RhinoView targetView = GetTargetView(rhinoDoc, viewportTarget);
        if (targetView == null)
        {
            throw new InvalidOperationException($"Viewport '{viewportTarget}' not found. Available viewports: Perspective, Top, Front, Right, Back, Left, Bottom, or use 'active' for the current view.");
        }

        long solutionDurationMs = 0;
        if (recompute)
        {
            var solutionStopwatch = Stopwatch.StartNew();
            RunGrasshopperSolution(doc, false);
            solutionStopwatch.Stop();
            solutionDurationMs = solutionStopwatch.ElapsedMilliseconds;
        }

        var candidates = ResolveGrasshopperPreviewCandidates(doc, graphId, parameters["targets"]);
        var capturedObjects = new JArray();
        int hiddenSkipped = 0;
        int incapableSkipped = 0;
        int invalidBoundsSkipped = 0;
        bool hasBounds = false;
        BoundingBox bounds = BoundingBox.Empty;

        foreach (var obj in candidates)
        {
            if (obj is not IGH_PreviewObject previewObject)
            {
                incapableSkipped++;
                continue;
            }
            if (!includeHidden && previewObject.Hidden)
            {
                hiddenSkipped++;
                continue;
            }
            if (!previewObject.IsPreviewCapable)
            {
                incapableSkipped++;
                continue;
            }

            var clippingBox = previewObject.ClippingBox;
            if (!clippingBox.IsValid)
            {
                invalidBoundsSkipped++;
                continue;
            }

            if (!hasBounds)
            {
                bounds = clippingBox;
                hasBounds = true;
            }
            else
            {
                bounds.Union(clippingBox);
            }

            capturedObjects.Add(new JObject
            {
                ["instance_id"] = obj.InstanceGuid.ToString(),
                ["alias"] = GraphMetadataValue(obj, GhMetaAlias),
                ["graph_id"] = GraphMetadataValue(obj, GhMetaGraphId),
                ["role"] = GraphMetadataValue(obj, GhMetaRole),
                ["name"] = obj.Name,
                ["nickname"] = obj.NickName,
                ["bounds"] = BoundingBoxToJson(clippingBox)
            });
        }

        if (!hasBounds)
        {
            throw new InvalidOperationException(
                "No visible Grasshopper preview bounds were found. " +
                "Check that the definition solved, preview is enabled, and graph_id/targets select preview-capable geometry.");
        }

        var paddedBounds = PadBoundingBox(bounds, paddingFactor);
        targetView.ActiveViewport.ZoomBoundingBox(paddedBounds);
        rhinoDoc.Views.Redraw();
        RedrawGrasshopperCanvas();

        string base64Data = CaptureViewToPngBase64(
            targetView,
            width,
            height,
            showGrid,
            showAxes,
            showCplaneAxes,
            "gh_capture_preview");

        stopwatch.Stop();
        return new JObject
        {
            ["image_data"] = base64Data,
            ["mime_type"] = "image/png",
            ["width"] = width,
            ["height"] = height,
            ["viewport_name"] = targetView.ActiveViewport.Name ?? viewportTarget,
            ["viewport_target"] = viewportTarget,
            ["show_grid"] = showGrid,
            ["show_axes"] = showAxes,
            ["show_cplane_axes"] = showCplaneAxes,
            ["graph_id"] = graphId,
            ["target_count"] = (parameters["targets"] as JArray)?.Count ?? 0,
            ["candidate_count"] = candidates.Count,
            ["captured_preview_object_count"] = capturedObjects.Count,
            ["hidden_skipped_count"] = hiddenSkipped,
            ["preview_incapable_skipped_count"] = incapableSkipped,
            ["invalid_bounds_skipped_count"] = invalidBoundsSkipped,
            ["bounds"] = BoundingBoxToJson(bounds),
            ["padded_bounds"] = BoundingBoxToJson(paddedBounds),
            ["padding_factor"] = paddingFactor,
            ["recomputed"] = recompute,
            ["solution_duration_ms"] = solutionDurationMs,
            ["duration_ms"] = stopwatch.ElapsedMilliseconds,
            ["preview_objects"] = capturedObjects,
            ["visibility"] = GrasshopperVisibilityState(doc)
        };
    }

    private static List<IGH_DocumentObject> ResolveGrasshopperPreviewCandidates(
        GH_Document doc,
        string graphId,
        JToken targetsToken)
    {
        var targets = ResolveGraphTargets(doc, null, targetsToken, "preview capture target");
        if (targets.Count > 0)
        {
            return targets;
        }
        if (!string.IsNullOrWhiteSpace(graphId))
        {
            return GetGraphObjects(doc, graphId).Where(o => o is not GH_Group).ToList();
        }
        return doc.Objects.Where(o => o is not GH_Group).ToList();
    }

    private static BoundingBox PadBoundingBox(BoundingBox box, double paddingFactor)
    {
        var center = box.Center;
        var diagonal = box.Diagonal;
        double minPadding = 0.5;
        double padX = Math.Max(Math.Abs(diagonal.X) * (paddingFactor - 1.0) / 2.0, minPadding);
        double padY = Math.Max(Math.Abs(diagonal.Y) * (paddingFactor - 1.0) / 2.0, minPadding);
        double padZ = Math.Max(Math.Abs(diagonal.Z) * (paddingFactor - 1.0) / 2.0, minPadding);

        return new BoundingBox(
            new Point3d(center.X - Math.Abs(diagonal.X) / 2.0 - padX, center.Y - Math.Abs(diagonal.Y) / 2.0 - padY, center.Z - Math.Abs(diagonal.Z) / 2.0 - padZ),
            new Point3d(center.X + Math.Abs(diagonal.X) / 2.0 + padX, center.Y + Math.Abs(diagonal.Y) / 2.0 + padY, center.Z + Math.Abs(diagonal.Z) / 2.0 + padZ));
    }

    private static JObject BoundingBoxToJson(BoundingBox box)
    {
        return new JObject
        {
            ["min"] = new JArray { box.Min.X, box.Min.Y, box.Min.Z },
            ["max"] = new JArray { box.Max.X, box.Max.Y, box.Max.Z },
            ["center"] = new JArray { box.Center.X, box.Center.Y, box.Center.Z },
            ["diagonal"] = new JArray { box.Diagonal.X, box.Diagonal.Y, box.Diagonal.Z }
        };
    }
}
