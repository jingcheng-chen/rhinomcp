using Newtonsoft.Json.Linq;
using Rhino;
using RhinoMCP.Shared.Serializers;

namespace RhinoMCPPlugin.Functions;

public partial class RhinoMCPFunctions
{
    public JObject GetSelectedObjectsInfo(JObject parameters)
    {
        var includeAttributes = parameters["include_attributes"]?.ToObject<bool>() ?? false;
        var doc = RhinoDoc.ActiveDoc;
        var selectedObjs = doc.Objects.GetSelectedObjects(false, false);

        var result = new JArray();
        foreach (var obj in selectedObjs)
        {
            var data = Serializer.RhinoObject(obj);
            if (includeAttributes)
            {
                data["attributes"] = Serializer.RhinoObjectAttributes(obj);
            }
            result.Add(data);
        }

        return new JObject
        {
            ["selected_objects"] = result
        };
    }
}