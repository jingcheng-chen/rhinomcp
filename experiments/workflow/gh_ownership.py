"""Trusted supervisor GH document identity; no agent-authored code is evaluated."""

import json
from experiments.bridge import script, assert_document
from rhinomcp.server import get_rhino_connection

PREFIX = """
var assembly=AppDomain.CurrentDomain.GetAssemblies().Single(a=>a.GetName().Name=="Grasshopper");
var instances=assembly.GetType("Grasshopper.Instances");
var server=instances.GetProperty("DocumentServer").GetValue(null);
var canvas=instances.GetProperty("ActiveCanvas").GetValue(null);
var active=canvas==null?null:canvas.GetType().GetProperty("Document").GetValue(canvas);
"""


def command(name, params=None):
    return get_rhino_connection().send_command(name, params or {})


def state():
    return json.loads(
        script(
            PREFIX
            + """
output.AppendLine(Serialize(new { count=(int)server.GetType().GetProperty("DocumentCount").GetValue(server),
 id=active==null?null:active.GetType().GetProperty("DocumentID").GetValue(active).ToString(),
 objects=active==null?0:(int)active.GetType().GetProperty("ObjectCount").GetValue(active) }));
"""
        )
    )


def claim(serial, marker):
    rhino = assert_document(serial, marker)
    if rhino["object_count"] or state() != {"count": 0, "id": None, "objects": 0}:
        raise RuntimeError(
            "A dedicated empty Rhino and no existing GH documents are required"
        )
    command(
        "gh_create_document",
        {"new_if_missing": True, "make_active": True, "open_canvas": True},
    )
    current = state()
    if current["count"] != 1 or not current["id"] or current["objects"]:
        raise RuntimeError("Could not claim a fresh empty Grasshopper document")
    return current["id"]


def guard(serial, marker, document_id):
    rhino = assert_document(serial, marker)
    current = state()
    if rhino["object_count"] or current["count"] != 1 or current["id"] != document_id:
        raise RuntimeError(
            "Owned empty Rhino or active Grasshopper document changed; refusing operation"
        )
    return current


def cleanup(serial, marker, document_id):
    guard(serial, marker, document_id)
    command("gh_clear_canvas", {"recompute": False})
    current = guard(serial, marker, document_id)
    if current["objects"]:
        raise RuntimeError("Grasshopper clear did not remove every object")
    script(
        PREFIX
        + f"""
if(active==null || active.GetType().GetProperty("DocumentID").GetValue(active).ToString()!={json.dumps(document_id)}) throw new Exception("GH ownership changed");
canvas.GetType().GetProperty("Document").SetValue(canvas,null);
server.GetType().GetMethod("RemoveDocument").Invoke(server,new[]{{active}});
"""
    )
    after = state()
    if after != {"count": 0, "id": None, "objects": 0}:
        raise RuntimeError("Grasshopper document cleanup did not restore empty server")
    return after
