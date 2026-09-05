"""Controller-only access and evidence helpers."""

import json
from rhinomcp.server import get_rhino_connection


def script(code):
    code = (
        """
string Serialize(object value) {
    var type = AppDomain.CurrentDomain.GetAssemblies()
        .Select(a => a.GetType("Newtonsoft.Json.JsonConvert"))
        .First(t => t != null);
    return (string)type.GetMethod("SerializeObject", new[] { typeof(object) })
        .Invoke(null, new[] { value });
}
"""
        + code
    )
    result = get_rhino_connection().send_command(
        "execute_rhinocommon_csharp_code", {"code": code}
    )
    if not result.get("success"):
        raise RuntimeError(result.get("message", "Rhino script failed"))
    return result["output"].strip()


def identity():
    return json.loads(
        script("""
var asm = AppDomain.CurrentDomain.GetAssemblies().Single(a => a.GetName().Name == "rhinomcp");
output.AppendLine(Serialize(new {
    document = doc.RuntimeSerialNumber,
    marker = doc.Strings.GetValue("rhinomcp_experiment"),
    object_count = doc.Objects.Count(o => o != null && !o.IsDeleted),
    path = doc.Path,
    assembly = asm.Location,
    mvid = asm.ManifestModule.ModuleVersionId.ToString(),
    version = asm.GetName().Version.ToString()
}));
""")
    )


def assert_document(serial, marker):
    state = identity()
    if state["document"] != serial or state["marker"] != marker:
        raise RuntimeError("Active Rhino document changed; refusing this operation")
    return state
