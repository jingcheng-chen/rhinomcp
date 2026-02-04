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
    public JObject GetDocumentSummary(JObject parameters)
    {
        RhinoApp.WriteLine("Getting document summary...");
        var doc = RhinoDoc.ActiveDoc;

        var metaData = new JObject
        {
            ["name"] = doc.Name,
            ["date_created"] = doc.DateCreated,
            ["date_modified"] = doc.DateLastEdited,
            ["tolerance"] = doc.ModelAbsoluteTolerance,
            ["angle_tolerance"] = doc.ModelAngleToleranceDegrees,
            ["path"] = doc.Path,
            ["units"] = doc.ModelUnitSystem.ToString(),
        };

        // Count objects by type and layer
        var typeCounts = new Dictionary<string, int>();
        var layerCounts = new Dictionary<int, int>(); // Use layer index for counting
        BoundingBox modelBbox = BoundingBox.Empty;

        foreach (var obj in doc.Objects)
        {
            // Count by type
            string objType = GetNormalizedType(obj);
            if (!typeCounts.ContainsKey(objType))
                typeCounts[objType] = 0;
            typeCounts[objType]++;

            // Count by layer index
            int layerIndex = obj.Attributes.LayerIndex;
            if (!layerCounts.ContainsKey(layerIndex))
                layerCounts[layerIndex] = 0;
            layerCounts[layerIndex]++;

            // Update model bounding box
            BoundingBox objBbox = obj.Geometry.GetBoundingBox(true);
            modelBbox.Union(objBbox);
        }

        // Build type counts JSON (sorted by count descending)
        var typeCountsJson = new JObject();
        foreach (var kvp in typeCounts.OrderByDescending(x => x.Value))
        {
            typeCountsJson[kvp.Key] = kvp.Value;
        }

        // Build layer counts JSON using layer names
        var layerCountsJson = new JObject();
        foreach (var kvp in layerCounts.OrderByDescending(x => x.Value))
        {
            string layerName = doc.Layers[kvp.Key].Name;
            layerCountsJson[layerName] = kvp.Value;
        }

        // Build layer hierarchy
        var layerHierarchy = BuildLayerHierarchy(doc, layerCounts);

        var result = new JObject
        {
            ["meta_data"] = metaData,
            ["object_count"] = doc.Objects.Count,
            ["objects_by_type"] = typeCountsJson,
            ["objects_by_layer"] = layerCountsJson,
            ["model_bounding_box"] = modelBbox.IsValid ? Serializer.SerializeBBox(modelBbox) : null,
            ["layer_count"] = doc.Layers.Count,
            ["layer_hierarchy"] = layerHierarchy
        };

        RhinoApp.WriteLine($"Document summary collected: {doc.Objects.Count} objects");
        return result;
    }

    private string GetNormalizedType(RhinoObject obj)
    {
        if (obj.Geometry is Rhino.Geometry.Point) return "POINT";
        if (obj.Geometry is Rhino.Geometry.LineCurve) return "LINE";
        if (obj.Geometry is Rhino.Geometry.PolylineCurve) return "POLYLINE";
        if (obj.Geometry is Rhino.Geometry.ArcCurve arc)
        {
            if (arc.Arc.IsCircle) return "CIRCLE";
            return "ARC";
        }
        if (obj.Geometry is Rhino.Geometry.Curve) return "CURVE";
        if (obj.Geometry is Rhino.Geometry.Extrusion) return "EXTRUSION";
        if (obj.Geometry is Rhino.Geometry.Brep) return "BREP";
        if (obj.Geometry is Rhino.Geometry.Surface) return "SURFACE";
        if (obj.Geometry is Rhino.Geometry.Mesh) return "MESH";
        return obj.ObjectType.ToString().ToUpper();
    }

    private JArray BuildLayerHierarchy(RhinoDoc doc, Dictionary<int, int> layerCounts)
    {
        var rootLayers = new JArray();
        var layerDict = new Dictionary<Guid, JObject>();

        // First pass: create all layer nodes
        foreach (var layer in doc.Layers)
        {
            if (layer.IsDeleted) continue;

            int count = layerCounts.ContainsKey(layer.Index) ? layerCounts[layer.Index] : 0;

            var layerNode = new JObject
            {
                ["id"] = layer.Id.ToString(),
                ["name"] = layer.Name,
                ["full_path"] = layer.FullPath,
                ["color"] = Serializer.SerializeColor(layer.Color),
                ["visible"] = layer.IsVisible,
                ["locked"] = layer.IsLocked,
                ["object_count"] = count,
                ["parent_id"] = layer.ParentLayerId == Guid.Empty ? null : layer.ParentLayerId.ToString(),
                ["children"] = new JArray()
            };

            layerDict[layer.Id] = layerNode;
        }

        // Second pass: build hierarchy
        foreach (var layer in doc.Layers)
        {
            if (layer.IsDeleted) continue;

            if (layer.ParentLayerId == Guid.Empty)
            {
                rootLayers.Add(layerDict[layer.Id]);
            }
            else if (layerDict.ContainsKey(layer.ParentLayerId))
            {
                ((JArray)layerDict[layer.ParentLayerId]["children"]).Add(layerDict[layer.Id]);
            }
        }

        return rootLayers;
    }
}
