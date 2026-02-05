using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoMCP.Shared.Serializers;

/// <summary>
/// Shared serialization utilities for converting Rhino objects to JSON.
/// Used by both RhinoMCP and GrasshopperMCP plugins.
/// </summary>
public static class Serializer
{
    // Layer name cache to avoid repeated lookups during batch serialization
    private static Dictionary<(uint docId, int layerIndex), string> _layerCache = new();
    private static Guid _cachedDocId = Guid.Empty;

    /// <summary>
    /// Get layer name with caching. Cache is automatically invalidated when document changes.
    /// </summary>
    public static string GetLayerName(RhinoDoc doc, int layerIndex)
    {
        // Invalidate cache if document changed
        if (doc.RuntimeSerialNumber != _cachedDocId.GetHashCode())
        {
            _layerCache.Clear();
            _cachedDocId = new Guid(doc.RuntimeSerialNumber, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
        }

        var key = (doc.RuntimeSerialNumber, layerIndex);
        if (!_layerCache.TryGetValue(key, out var layerName))
        {
            layerName = doc.Layers[layerIndex].Name;
            _layerCache[key] = layerName;
        }
        return layerName;
    }

    /// <summary>
    /// Clear the layer cache. Call this if layers are modified.
    /// </summary>
    public static void ClearLayerCache()
    {
        _layerCache.Clear();
    }

    /// <summary>
    /// Serialize a Color to JSON with r, g, b components.
    /// </summary>
    public static JObject SerializeColor(Color color)
    {
        return new JObject()
        {
            ["r"] = color.R,
            ["g"] = color.G,
            ["b"] = color.B
        };
    }

    /// <summary>
    /// Serialize a Point3d to a JSON array [x, y, z].
    /// Values are rounded to 2 decimal places.
    /// </summary>
    public static JArray SerializePoint(Point3d pt)
    {
        return new JArray
        {
            Math.Round(pt.X, 2),
            Math.Round(pt.Y, 2),
            Math.Round(pt.Z, 2)
        };
    }

    /// <summary>
    /// Serialize multiple Point3d to a JSON array of point arrays.
    /// </summary>
    public static JArray SerializePoints(IEnumerable<Point3d> pts)
    {
        return new JArray(pts.Select(p => SerializePoint(p)));
    }

    /// <summary>
    /// Serialize a Vector3d to a JSON array [x, y, z].
    /// </summary>
    public static JArray SerializeVector(Vector3d vec)
    {
        return new JArray
        {
            Math.Round(vec.X, 4),
            Math.Round(vec.Y, 4),
            Math.Round(vec.Z, 4)
        };
    }

    /// <summary>
    /// Serialize a Curve to JSON with type and geometry data.
    /// </summary>
    public static JObject SerializeCurve(Curve crv)
    {
        return new JObject
        {
            ["type"] = "Curve",
            ["geometry"] = new JObject
            {
                ["points"] = SerializePoints(crv.ControlPolygon().ToArray()),
                ["degree"] = crv.Degree.ToString()
            }
        };
    }

    /// <summary>
    /// Serialize a BoundingBox to JSON array [[min], [max]].
    /// </summary>
    public static JArray SerializeBBox(BoundingBox bbox)
    {
        return new JArray
        {
            new JArray { bbox.Min.X, bbox.Min.Y, bbox.Min.Z },
            new JArray { bbox.Max.X, bbox.Max.Y, bbox.Max.Z }
        };
    }

    /// <summary>
    /// Serialize a Layer to JSON.
    /// </summary>
    public static JObject SerializeLayer(Layer layer)
    {
        return new JObject
        {
            ["id"] = layer.Id.ToString(),
            ["name"] = layer.Name,
            ["color"] = SerializeColor(layer.Color),
            ["parent"] = layer.ParentLayerId.ToString()
        };
    }

    /// <summary>
    /// Serialize a Plane to JSON.
    /// </summary>
    public static JObject SerializePlane(Plane plane)
    {
        return new JObject
        {
            ["origin"] = SerializePoint(plane.Origin),
            ["x_axis"] = SerializeVector(plane.XAxis),
            ["y_axis"] = SerializeVector(plane.YAxis),
            ["z_axis"] = SerializeVector(plane.ZAxis)
        };
    }

    /// <summary>
    /// Get user strings from a RhinoObject as a JSON object.
    /// </summary>
    public static JObject RhinoObjectAttributes(RhinoObject obj)
    {
        var attributes = obj.Attributes.GetUserStrings();
        var attributesDict = new JObject();
        foreach (string key in attributes.AllKeys)
        {
            attributesDict[key] = attributes[key];
        }
        return attributesDict;
    }

    /// <summary>
    /// Serialize a RhinoObject to a comprehensive JSON representation.
    /// </summary>
    public static JObject RhinoObject(RhinoObject obj)
    {
        var doc = obj.Document ?? RhinoDoc.ActiveDoc;
        var objInfo = new JObject
        {
            ["id"] = obj.Id.ToString(),
            ["name"] = obj.Name ?? "(unnamed)",
            ["type"] = obj.ObjectType.ToString(),
            ["layer"] = GetLayerName(doc, obj.Attributes.LayerIndex),
            ["material"] = obj.Attributes.MaterialIndex.ToString(),
            ["color"] = SerializeColor(obj.Attributes.ObjectColor)
        };

        // Add bounding box
        BoundingBox bbox = obj.Geometry.GetBoundingBox(true);
        objInfo["bounding_box"] = SerializeBBox(bbox);

        // Add geometry data based on type
        if (obj.Geometry is Rhino.Geometry.Point point)
        {
            objInfo["type"] = "POINT";
            objInfo["geometry"] = SerializePoint(point.Location);
        }
        else if (obj.Geometry is Rhino.Geometry.LineCurve line)
        {
            objInfo["type"] = "LINE";
            objInfo["geometry"] = new JObject
            {
                ["start"] = SerializePoint(line.Line.From),
                ["end"] = SerializePoint(line.Line.To)
            };
        }
        else if (obj.Geometry is Rhino.Geometry.PolylineCurve polyline)
        {
            objInfo["type"] = "POLYLINE";
            objInfo["geometry"] = new JObject
            {
                ["points"] = SerializePoints(polyline.ToArray())
            };
        }
        else if (obj.Geometry is Rhino.Geometry.Curve curve)
        {
            var crv = SerializeCurve(curve);
            objInfo["type"] = crv["type"];
            objInfo["geometry"] = crv["geometry"];
        }
        else if (obj.Geometry is Rhino.Geometry.Extrusion extrusion)
        {
            objInfo["type"] = "EXTRUSION";
        }
        else if (obj.Geometry is Rhino.Geometry.Brep brep)
        {
            objInfo["type"] = "BREP";
            objInfo["geometry"] = new JObject
            {
                ["faces"] = brep.Faces.Count,
                ["edges"] = brep.Edges.Count,
                ["vertices"] = brep.Vertices.Count,
                ["is_solid"] = brep.IsSolid
            };
        }
        else if (obj.Geometry is Rhino.Geometry.Mesh mesh)
        {
            objInfo["type"] = "MESH";
            objInfo["geometry"] = new JObject
            {
                ["vertices"] = mesh.Vertices.Count,
                ["faces"] = mesh.Faces.Count
            };
        }
        else if (obj.Geometry is Rhino.Geometry.Surface surface)
        {
            objInfo["type"] = "SURFACE";
        }

        return objInfo;
    }
}
