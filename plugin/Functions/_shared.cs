using System;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Helpers shared by several handlers: viewport state and bounding box
/// serialization, framing box padding, parameter presence and lock checks.
/// </summary>
public partial class RhinoMCPFunctions
{
    // The viewport state get_context, capture_viewport, set_camera and zoom_to
    // report. Points use SerializePoint (2 dp); the unit up vector keeps 4 dp so
    // rounding does not bend it.
    private static JObject ViewportState(RhinoViewport viewport)
    {
        var up = viewport.CameraUp;
        return new JObject
        {
            ["viewport_name"] = viewport.Name,
            ["projection"] = viewport.IsParallelProjection ? "parallel" : "perspective",
            ["display_mode"] = viewport.DisplayMode?.EnglishName ?? "",
            ["camera_location"] = Serializer.SerializePoint(viewport.CameraLocation),
            ["camera_target"] = Serializer.SerializePoint(viewport.CameraTarget),
            ["camera_up"] = new JArray { Math.Round(up.X, 4), Math.Round(up.Y, 4), Math.Round(up.Z, 4) },
            ["lens_length"] = Math.Round(viewport.Camera35mmLensLength, 2),
        };
    }

    // A box as {"min": [x, y, z], "max": [x, y, z]} at SerializePoint precision,
    // or null when the box is not valid (for example an empty document).
    private static JObject SerializeMinMax(BoundingBox box)
    {
        if (!box.IsValid) return null;
        return new JObject
        {
            ["min"] = Serializer.SerializePoint(box.Min),
            ["max"] = Serializer.SerializePoint(box.Max),
        };
    }

    // A point or a flat object has a degenerate box, which ZoomBoundingBox and
    // DollyExtents cannot frame. Pad every zero-extent axis by a twentieth of the
    // largest extent, or by one unit on every axis when the box is a single point.
    private static BoundingBox PadForFraming(BoundingBox box)
    {
        var diagonal = box.Diagonal;
        double largest = Math.Max(diagonal.X, Math.Max(diagonal.Y, diagonal.Z));
        double pad = largest < RhinoMath.SqrtEpsilon ? 1.0 : largest * 0.05;
        var padded = box;
        padded.Inflate(
            diagonal.X < RhinoMath.SqrtEpsilon ? pad : 0,
            diagonal.Y < RhinoMath.SqrtEpsilon ? pad : 0,
            diagonal.Z < RhinoMath.SqrtEpsilon ? pad : 0);
        return padded;
    }

    // Present and non-empty: a missing key, null, "" and [] all count as absent.
    private static bool IsGiven(JObject parameters, string name)
    {
        var token = parameters[name];
        if (token == null || token.Type == JTokenType.Null) return false;
        if (token.Type == JTokenType.String) return token.ToString().Length > 0;
        if (token.Type == JTokenType.Array) return token.HasValues;
        return true;
    }

    // Locked as the user sees it: the object itself or the layer it sits on.
    private static bool IsObjectOrLayerLocked(RhinoDoc doc, RhinoObject obj) =>
        obj.IsLocked || doc.Layers[obj.Attributes.LayerIndex].IsLocked;
}
