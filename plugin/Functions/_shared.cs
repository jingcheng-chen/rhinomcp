using System;
using Rhino;
using Rhino.Geometry;

namespace RhinoMCPPlugin.Functions;

/// <summary>
/// Helpers shared by several handlers.
/// </summary>
public partial class RhinoMCPFunctions
{
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
}
