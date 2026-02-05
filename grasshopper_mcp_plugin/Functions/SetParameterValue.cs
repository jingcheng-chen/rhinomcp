using System;
using System.Collections.Generic;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Types;
using Newtonsoft.Json.Linq;
using Rhino.Geometry;

namespace GrasshopperMCPPlugin.Functions;

public partial class GrasshopperMCPFunctions
{
    /// <summary>
    /// Set the value of a component's input parameter.
    /// Supports both Python naming (instance_id, nickname, input_index, input_name)
    /// and C# naming (component_id, param_index, param_name).
    /// </summary>
    public JObject SetParameterValue(JObject parameters)
    {
        var doc = Instances.ActiveCanvas?.Document;

        if (doc == null)
        {
            throw new InvalidOperationException("No active Grasshopper document");
        }

        var value = parameters["value"];

        if (value == null)
        {
            throw new ArgumentException("value is required");
        }

        // Find component - supports instance_id, nickname, or component_id
        var obj = ComponentHelper.FindComponent(doc, parameters);

        // Get input parameter
        var paramIndex = ComponentHelper.GetParamIndex(parameters, isOutput: false);
        var paramName = ComponentHelper.GetParamName(parameters, isOutput: false);

        var inputParam = ComponentHelper.FindInputParam(obj, paramIndex, paramName);

        if (inputParam == null)
        {
            throw new InvalidOperationException($"Could not find input parameter on component '{obj.NickName}'");
        }

        // Set the value based on parameter type
        SetParamValue(inputParam, value);

        // Trigger solution
        doc.NewSolution(false);

        return new JObject
        {
            ["instance_id"] = obj.InstanceGuid.ToString(),
            ["nickname"] = obj.NickName,
            ["param_name"] = inputParam.Name,
            ["message"] = $"Set value on {obj.NickName}.{inputParam.Name}"
        };
    }

    /// <summary>
    /// Helper to set parameter value based on type.
    /// </summary>
    private void SetParamValue(IGH_Param param, JToken value)
    {
        // Clear existing persistent data
        param.RemoveAllSources();

        // Handle based on parameter type
        if (param is Param_Number numParam)
        {
            if (value.Type == JTokenType.Array)
            {
                var values = value.ToObject<List<double>>() ?? new List<double>();
                numParam.PersistentData.ClearData();
                foreach (var v in values)
                {
                    numParam.PersistentData.Append(new GH_Number(v));
                }
            }
            else
            {
                numParam.PersistentData.ClearData();
                numParam.PersistentData.Append(new GH_Number(value.ToObject<double>()));
            }
        }
        else if (param is Param_Integer intParam)
        {
            if (value.Type == JTokenType.Array)
            {
                var values = value.ToObject<List<int>>() ?? new List<int>();
                intParam.PersistentData.ClearData();
                foreach (var v in values)
                {
                    intParam.PersistentData.Append(new GH_Integer(v));
                }
            }
            else
            {
                intParam.PersistentData.ClearData();
                intParam.PersistentData.Append(new GH_Integer(value.ToObject<int>()));
            }
        }
        else if (param is Param_Boolean boolParam)
        {
            boolParam.PersistentData.ClearData();
            boolParam.PersistentData.Append(new GH_Boolean(value.ToObject<bool>()));
        }
        else if (param is Param_String strParam)
        {
            if (value.Type == JTokenType.Array)
            {
                var values = value.ToObject<List<string>>() ?? new List<string>();
                strParam.PersistentData.ClearData();
                foreach (var v in values)
                {
                    strParam.PersistentData.Append(new GH_String(v));
                }
            }
            else
            {
                strParam.PersistentData.ClearData();
                strParam.PersistentData.Append(new GH_String(value.ToString()));
            }
        }
        else if (param is Param_Point ptParam)
        {
            ptParam.PersistentData.ClearData();
            if (value.Type == JTokenType.Array && value.First?.Type == JTokenType.Array)
            {
                // Array of points
                foreach (var ptArray in value)
                {
                    var coords = ptArray.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
                    var pt = new Point3d(coords[0], coords.Length > 1 ? coords[1] : 0, coords.Length > 2 ? coords[2] : 0);
                    ptParam.PersistentData.Append(new GH_Point(pt));
                }
            }
            else if (value.Type == JTokenType.Array)
            {
                // Single point as array
                var coords = value.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
                var pt = new Point3d(coords[0], coords.Length > 1 ? coords[1] : 0, coords.Length > 2 ? coords[2] : 0);
                ptParam.PersistentData.Append(new GH_Point(pt));
            }
        }
        else if (param is Param_Vector vecParam)
        {
            vecParam.PersistentData.ClearData();
            var coords = value.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
            var vec = new Vector3d(coords[0], coords.Length > 1 ? coords[1] : 0, coords.Length > 2 ? coords[2] : 0);
            vecParam.PersistentData.Append(new GH_Vector(vec));
        }
        else if (param is Param_Plane planeParam)
        {
            planeParam.PersistentData.ClearData();
            if (value is JObject planeObj)
            {
                var origin = planeObj["origin"]?.ToObject<double[]>() ?? new double[] { 0, 0, 0 };
                var plane = new Plane(
                    new Point3d(origin[0], origin.Length > 1 ? origin[1] : 0, origin.Length > 2 ? origin[2] : 0),
                    Vector3d.ZAxis
                );
                planeParam.PersistentData.Append(new GH_Plane(plane));
            }
        }
        else
        {
            throw new InvalidOperationException($"Unsupported parameter type: {param.GetType().Name}. Use connect_components to wire data from another component.");
        }

        param.ExpireSolution(true);
    }
}
