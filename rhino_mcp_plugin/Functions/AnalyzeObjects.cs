using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using rhinomcp.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    [McpCommand("analyze_objects", ReadOnly = true)]
    public JObject AnalyzeObjects(JObject parameters)
    {
        var objects = ResolveAnalysisTargets(parameters);
        var analyses = new JArray();

        foreach (var obj in objects)
        {
            analyses.Add(AnalyzeRhinoObject(obj));
        }

        return new JObject
        {
            ["object_count"] = analyses.Count,
            ["analyses"] = analyses
        };
    }

    private List<RhinoObject> ResolveAnalysisTargets(JObject parameters)
    {
        var doc = RhinoDoc.ActiveDoc;
        var selectorCount = 0;
        if (parameters.ContainsKey("id")) selectorCount++;
        if (parameters.ContainsKey("name")) selectorCount++;
        if (parameters.ContainsKey("object_ids")) selectorCount++;
        if (parameters["selected"]?.ToObject<bool>() == true) selectorCount++;

        if (selectorCount != 1)
            throw new ArgumentException("analyze_objects requires exactly one of id, name, object_ids, or selected=true.");

        if (parameters.ContainsKey("id") || parameters.ContainsKey("name"))
            return new List<RhinoObject> { getObjectByIdOrName(parameters) };

        if (parameters["selected"]?.ToObject<bool>() == true)
            return doc.Objects.GetSelectedObjects(false, false).ToList();

        var ids = parameters["object_ids"]?.ToObject<List<string>>() ?? new List<string>();
        if (ids.Count == 0)
            throw new ArgumentException("analyze_objects object_ids must contain at least one id.");

        var objects = new List<RhinoObject>();
        foreach (var id in ids)
        {
            if (!Guid.TryParse(id, out var guid))
                throw new InvalidOperationException($"Invalid GUID '{id}'.");

            var obj = doc.Objects.Find(guid);
            if (obj == null)
                throw new InvalidOperationException($"Object with id {id} not found.");

            objects.Add(obj);
        }
        return objects;
    }

    private JObject AnalyzeRhinoObject(RhinoObject obj)
    {
        var doc = obj.Document ?? RhinoDoc.ActiveDoc;
        var geometry = obj.Geometry;
        var bbox = geometry.GetBoundingBox(true);
        var valid = geometry.IsValid;
        var validityLog = string.Empty;

        try
        {
            valid = geometry.IsValidWithLog(out validityLog);
        }
        catch
        {
            validityLog = string.Empty;
        }

        var analysis = new JObject
        {
            ["id"] = obj.Id.ToString(),
            ["name"] = obj.Name ?? string.Empty,
            ["type"] = GetNormalizedType(obj),
            ["layer"] = doc.Layers[obj.Attributes.LayerIndex].Name,
            ["valid"] = valid,
            ["validity_log"] = string.IsNullOrWhiteSpace(validityLog) ? null : validityLog,
            ["bounding_box"] = Serializer.SerializeBBox(bbox),
            ["bbox_dimensions"] = new JArray
            {
                bbox.Max.X - bbox.Min.X,
                bbox.Max.Y - bbox.Min.Y,
                bbox.Max.Z - bbox.Min.Z
            },
            ["metrics"] = AnalyzeGeometry(geometry)
        };

        return analysis;
    }

    private JObject AnalyzeGeometry(GeometryBase geometry)
    {
        var metrics = new JObject();

        if (geometry is Rhino.Geometry.Point point)
        {
            metrics["location"] = Serializer.SerializePoint(point.Location);
            return metrics;
        }

        if (geometry is Curve curve)
        {
            AddCurveMetrics(metrics, curve);
            return metrics;
        }

        if (geometry is Brep brep)
        {
            AddBrepMetrics(metrics, brep);
            return metrics;
        }

        if (geometry is Extrusion extrusion)
        {
            var extrusionBrep = extrusion.ToBrep();
            if (extrusionBrep != null)
            {
                AddBrepMetrics(metrics, extrusionBrep);
                metrics["source_geometry"] = "EXTRUSION";
            }
            return metrics;
        }

        if (geometry is Surface surface)
        {
            var surfaceBrep = surface.ToBrep();
            if (surfaceBrep != null)
            {
                AddBrepMetrics(metrics, surfaceBrep);
                metrics["source_geometry"] = "SURFACE";
            }
            return metrics;
        }

        if (geometry is Mesh mesh)
        {
            AddMeshMetrics(metrics, mesh);
        }

        return metrics;
    }

    private void AddCurveMetrics(JObject metrics, Curve curve)
    {
        metrics["length"] = curve.GetLength();
        metrics["is_closed"] = curve.IsClosed;
        metrics["is_periodic"] = curve.IsPeriodic;
        metrics["degree"] = curve.Degree;
        metrics["span_count"] = curve.SpanCount;
        metrics["start_point"] = Serializer.SerializePoint(curve.PointAtStart);
        metrics["end_point"] = Serializer.SerializePoint(curve.PointAtEnd);

        var area = AreaMassProperties.Compute(curve);
        if (area != null)
        {
            metrics["area"] = area.Area;
            metrics["centroid"] = Serializer.SerializePoint(area.Centroid);
        }
    }

    private void AddBrepMetrics(JObject metrics, Brep brep)
    {
        metrics["is_solid"] = brep.IsSolid;
        metrics["face_count"] = brep.Faces.Count;
        metrics["edge_count"] = brep.Edges.Count;
        metrics["vertex_count"] = brep.Vertices.Count;
        metrics["naked_edge_count"] = brep.DuplicateNakedEdgeCurves(true, false)?.Length ?? 0;

        var area = AreaMassProperties.Compute(brep);
        if (area != null)
        {
            metrics["area"] = area.Area;
            metrics["area_centroid"] = Serializer.SerializePoint(area.Centroid);
        }

        var volume = VolumeMassProperties.Compute(brep);
        if (volume != null)
        {
            metrics["volume"] = volume.Volume;
            metrics["volume_centroid"] = Serializer.SerializePoint(volume.Centroid);
        }
    }

    private void AddMeshMetrics(JObject metrics, Mesh mesh)
    {
        metrics["is_closed"] = mesh.IsClosed;
        metrics["face_count"] = mesh.Faces.Count;
        metrics["vertex_count"] = mesh.Vertices.Count;
        metrics["edge_count"] = mesh.TopologyEdges.Count;
        metrics["naked_edge_count"] = mesh.GetNakedEdges()?.Length ?? 0;

        var area = AreaMassProperties.Compute(mesh);
        if (area != null)
        {
            metrics["area"] = area.Area;
            metrics["area_centroid"] = Serializer.SerializePoint(area.Centroid);
        }

        var volume = VolumeMassProperties.Compute(mesh);
        if (volume != null)
        {
            metrics["volume"] = volume.Volume;
            metrics["volume_centroid"] = Serializer.SerializePoint(volume.Centroid);
        }
    }
}
