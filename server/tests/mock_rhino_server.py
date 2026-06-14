"""
Mock Rhino Server for testing.

This provides a fake Rhino server that responds to MCP commands,
allowing integration testing without running actual Rhino.

Usage:
    python -m tests.mock_rhino_server

Or in tests:
    from tests.mock_rhino_server import MockRhinoServer
    server = MockRhinoServer()
    server.start()
    # ... run tests ...
    server.stop()
"""

import json
import socket
import threading
import uuid
from typing import Dict, Any, Optional


class MockRhinoServer:
    """A mock Rhino server for testing MCP commands."""

    def __init__(self, host: str = "127.0.0.1", port: int = 1999):
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Mock document state
        self.objects: Dict[str, Dict[str, Any]] = {}
        # Shaped like the plugin's SerializeLayer output (layer_info.json):
        # color is an {r,g,b} object, parent is a guid.
        self.layers: Dict[str, Dict[str, Any]] = {
            "Default": {
                "id": str(uuid.uuid4()),
                "name": "Default",
                "color": {"r": 0, "g": 0, "b": 0},
                "parent": "00000000-0000-0000-0000-000000000000",
            }
        }
        self.current_layer = "Default"
        self.undo_stack: list = []
        self.redo_stack: list = []

    def start(self):
        """Start the mock server in a background thread."""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)

        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        print(f"Mock Rhino server started on {self.host}:{self.port}")

    def stop(self):
        """Stop the mock server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.thread:
            self.thread.join(timeout=2.0)
        print("Mock Rhino server stopped")

    def _run(self):
        """Server main loop."""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")

    # Mirrors the plugin's wire protocol (RhinoMCPServer.cs): messages are a
    # 4-byte big-endian length header plus UTF-8 JSON in both directions;
    # legacy clients that open with bare JSON ('{' or whitespace) get the old
    # unframed behavior for the whole connection.
    FRAME_HEADER_SIZE = 4
    MAX_FRAME_SIZE = 64 * 1024 * 1024
    _LEGACY_FIRST_BYTES = b"{ \t\r\n"

    def _handle_client(self, client_socket: socket.socket):
        """Handle a client connection, sniffing framed vs legacy protocol."""
        pending = bytearray()
        framed: Optional[bool] = None
        try:
            while self.running:
                data = client_socket.recv(65536)
                if not data:
                    break
                pending.extend(data)

                if framed is None:
                    framed = pending[0:1] not in [
                        bytes([b]) for b in self._LEGACY_FIRST_BYTES
                    ]

                if framed:
                    # Drain every complete frame so pipelined commands all
                    # execute, in order — same as the plugin.
                    while len(pending) >= self.FRAME_HEADER_SIZE:
                        frame_length = int.from_bytes(
                            pending[: self.FRAME_HEADER_SIZE], "big"
                        )
                        if frame_length <= 0 or frame_length > self.MAX_FRAME_SIZE:
                            raise ValueError(
                                f"Invalid frame length {frame_length}"
                            )
                        if len(pending) < self.FRAME_HEADER_SIZE + frame_length:
                            break
                        payload = bytes(
                            pending[
                                self.FRAME_HEADER_SIZE : self.FRAME_HEADER_SIZE
                                + frame_length
                            ]
                        )
                        del pending[: self.FRAME_HEADER_SIZE + frame_length]
                        self._respond(client_socket, payload, framed=True)
                else:
                    # Legacy: try the whole accumulation, wait for more on
                    # incomplete JSON.
                    try:
                        json.loads(pending.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                    payload = bytes(pending)
                    pending.clear()
                    self._respond(client_socket, payload, framed=False)
        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            client_socket.close()

    def _respond(self, client_socket: socket.socket, payload: bytes, framed: bool):
        """Process one command payload and write the response in the
        connection's protocol."""
        try:
            command = json.loads(payload.decode("utf-8"))
            response = self._process_command(command)
        except json.JSONDecodeError as e:
            response = {"status": "error", "message": f"Invalid JSON: {e}"}

        body = json.dumps(response).encode("utf-8")
        if framed:
            client_socket.sendall(
                len(body).to_bytes(self.FRAME_HEADER_SIZE, "big") + body
            )
        else:
            client_socket.sendall(body)

    # Commands the plugin treats as mutating (non-ReadOnly). Only these get a
    # _delta attached when include_delta is set, mirroring the plugin's
    # ExecuteCommandInternal (read-only commands never carry a delta).
    _MUTATING_COMMANDS = {
        "create_object", "create_objects", "modify_object", "modify_objects",
        "delete_object", "boolean_union", "boolean_difference",
        "boolean_intersection", "loft", "extrude_curve", "sweep1",
        "offset_curve", "pipe", "run_command",
        "execute_rhinoscript_python_code", "execute_rhinocommon_csharp_code",
        "undo", "redo", "create_layer", "delete_layer",
    }

    def _process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a command and return a response."""
        cmd_type = command.get("type", "")
        params = command.get("params", {})

        handlers = {
            "get_document_summary": self._get_document_summary,
            "get_objects": self._get_objects,
            "create_object": self._create_object,
            "create_objects": self._create_objects,
            "get_object_info": self._get_object_info,
            "get_object_attributes": self._get_object_attributes,
            "update_object_attributes": self._update_object_attributes,
            "analyze_objects": self._analyze_objects,
            "modify_object": self._modify_object,
            "modify_objects": self._modify_objects,
            "delete_object": self._delete_object,
            "select_objects": self._select_objects,
            "create_layer": self._create_layer,
            "delete_layer": self._delete_layer,
            "get_or_set_current_layer": self._get_or_set_current_layer,
            "undo": self._undo,
            "redo": self._redo,
            "boolean_union": self._boolean_union,
            "boolean_difference": self._boolean_difference,
            "boolean_intersection": self._boolean_intersection,
            "run_command": self._run_command,
            "get_commands": self._get_commands,
            "execute_rhinoscript_python_code": self._execute_script,
            "execute_rhinocommon_csharp_code": self._execute_csharp,
            "capture_viewport": self._capture_viewport,
            "loft": self._loft,
            "extrude_curve": self._extrude_curve,
            "sweep1": self._sweep1,
            "offset_curve": self._offset_curve,
            "pipe": self._pipe,
        }

        handler = handlers.get(cmd_type)
        if not handler:
            return {"status": "error", "message": f"Unknown command: {cmd_type}"}

        try:
            # Mirror the plugin: when the client asks for a delta, snapshot the
            # object id set around a mutating handler and attach what changed.
            track_delta = bool(command.get("include_delta")) and (
                cmd_type in self._MUTATING_COMMANDS
            )
            before = set(self.objects.keys()) if track_delta else None
            result = handler(params)
            if track_delta and isinstance(result, dict):
                after = set(self.objects.keys())
                result["_delta"] = {
                    "created_ids": [k for k in after if k not in before],
                    "deleted_ids": [k for k in before if k not in after],
                    "count_before": len(before),
                    "count_after": len(after),
                }
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_document_summary(self, params: Dict) -> Dict:
        """Return document summary."""
        # Count objects by type
        type_counts = {}
        layer_counts = {}
        for obj in self.objects.values():
            obj_type = obj.get("type", "UNKNOWN")
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            layer = obj.get("layer", "Default")
            layer_counts[layer] = layer_counts.get(layer, 0) + 1

        return {
            "meta_data": {"name": "mock.3dm", "units": "Millimeters", "tolerance": 0.001},
            "object_count": len(self.objects),
            "objects_by_type": type_counts,
            "objects_by_layer": layer_counts,
            "model_bounding_box": [[0, 0, 0], [100, 100, 100]] if self.objects else None,
            "layer_count": len(self.layers),
            "layer_hierarchy": [
                {"id": layer["id"], "name": layer["name"], "full_path": layer["name"],
                 "object_count": layer_counts.get(layer["name"], 0), "children": []}
                for layer in self.layers.values()
            ]
        }

    def _get_objects(self, params: Dict) -> Dict:
        """Return objects with filtering and pagination."""
        offset = params.get("offset", 0)
        limit = params.get("limit", 50)
        layer_filter = params.get("layer_filter")
        type_filter = params.get("type_filter")

        # Filter objects
        filtered = list(self.objects.values())
        if layer_filter:
            filtered = [o for o in filtered if o.get("layer") == layer_filter]
        if type_filter:
            filtered = [o for o in filtered if o.get("type", "").upper() == type_filter.upper()]

        total = len(filtered)
        paged = filtered[offset:offset + limit]

        return {
            "objects": paged,
            "total_matching": total,
            "offset": offset,
            "limit": limit,
            "has_more": offset + len(paged) < total
        }

    def _create_object(self, params: Dict) -> Dict:
        """Create a mock object."""
        obj_id = str(uuid.uuid4())
        obj_type = params.get("type", "BOX")
        name = params.get("name", f"{obj_type}_{len(self.objects)}")

        obj = {
            "id": obj_id,
            "name": name,
            "type": obj_type,
            "layer": self.current_layer,
            "color": {"r": 0, "g": 0, "b": 0},
            "material_index": -1,
            "material_source": "MaterialFromLayer",
            "color_source": "ColorFromLayer",
            "visible": True,
            "locked": False,
            "user_strings": {},
            "bounding_box": [[-1, -1, -1], [1, 1, 1]],
            "geometry": params.get("params", {})
        }

        if params.get("color"):
            color = params["color"]
            obj["color"] = {"r": color[0], "g": color[1], "b": color[2]}
            obj["color_source"] = "ColorFromObject"

        self.objects[obj_id] = obj
        self._push_undo(("delete", obj_id))

        return obj

    def _create_objects(self, params: Dict) -> Dict:
        """Create multiple objects."""
        results = {}
        success_count = 0
        failure_count = 0
        errors = []

        for key, obj_params in params.items():
            try:
                result = self._create_object(obj_params)
                results[key] = result
                success_count += 1
            except Exception as e:
                results[key] = {"status": "error", "error": str(e)}
                errors.append({"name": key, "error": str(e)})
                failure_count += 1

        return {
            "objects": results,
            "success_count": success_count,
            "failure_count": failure_count,
            "total": success_count + failure_count,
            "errors": errors
        }

    def _get_object_info(self, params: Dict) -> Dict:
        """Get object info by ID or name."""
        obj_id = params.get("id")
        name = params.get("name")

        if obj_id and obj_id in self.objects:
            return self.objects[obj_id]

        if name:
            for obj in self.objects.values():
                if obj["name"] == name:
                    return obj

        raise Exception(f"Object not found")

    def _object_attributes_payload(self, obj: Dict) -> Dict:
        """Return the compact attribute payload used by the real plugin."""
        layer_name = obj.get("layer", "Default")
        layer = self.layers.get(layer_name, {"id": "", "name": layer_name})
        visible = obj.get("visible", True)
        locked = obj.get("locked", False)
        return {
            "id": obj["id"],
            "name": obj.get("name", ""),
            "type": obj.get("type", "UNKNOWN"),
            "layer": {
                "index": 0,
                "id": layer.get("id", ""),
                "name": layer_name,
                "full_path": layer_name,
            },
            "color": obj.get("color", {"r": 0, "g": 0, "b": 0}),
            "color_source": obj.get("color_source", "ColorFromLayer"),
            "material_index": obj.get("material_index", -1),
            "material_source": obj.get("material_source", "MaterialFromLayer"),
            "visible": visible,
            "locked": locked,
            "hidden": not visible,
            "normal": visible and not locked,
            "user_strings": obj.get("user_strings", {}),
        }

    def _get_object_attributes(self, params: Dict) -> Dict:
        """Get lightweight object attributes."""
        return self._object_attributes_payload(self._get_object_info(params))

    def _update_object_attributes(self, params: Dict) -> Dict:
        """Update lightweight object attributes."""
        update_keys = {
            "new_name",
            "layer",
            "color",
            "material_index",
            "visible",
            "locked",
            "user_strings",
            "delete_user_strings",
            "clear_user_strings",
        }
        if not any(key in params for key in update_keys):
            raise Exception("update_object_attributes requires at least one attribute update.")
        if params.get("visible") is False and params.get("locked") is True:
            raise Exception("Object cannot be hidden and locked at the same time.")

        obj = self._get_object_info(params)
        if params.get("visible") is False and obj.get("locked") is True and params.get("locked") is not False:
            raise Exception("Locked objects cannot be hidden; set locked=false in the same update.")

        if "new_name" in params:
            obj["name"] = params["new_name"]
        if "layer" in params:
            layer = params["layer"]
            if layer not in self.layers:
                raise Exception(f"Layer '{layer}' not found.")
            obj["layer"] = layer
        if "color" in params:
            color = params["color"]
            obj["color"] = {"r": color[0], "g": color[1], "b": color[2]}
            obj["color_source"] = "ColorFromObject"
        if "material_index" in params:
            obj["material_index"] = params["material_index"]
            obj["material_source"] = "MaterialFromLayer" if params["material_index"] == -1 else "MaterialFromObject"

        user_strings = obj.setdefault("user_strings", {})
        if params.get("clear_user_strings"):
            user_strings.clear()
        for key in params.get("delete_user_strings", []):
            user_strings.pop(key, None)
        for key, value in params.get("user_strings", {}).items():
            if value is None:
                user_strings.pop(key, None)
            elif isinstance(value, (dict, list)):
                raise Exception("User string values must be strings, numbers, booleans, or null.")
            else:
                user_strings[key] = str(value).lower() if isinstance(value, bool) else str(value)

        if "locked" in params and params["locked"] is False:
            obj["locked"] = False
        if "visible" in params:
            obj["visible"] = params["visible"]
        if "locked" in params and params["locked"] is True:
            obj["visible"] = True
            obj["locked"] = True

        self.objects[obj["id"]] = obj
        return self._object_attributes_payload(obj)

    def _analyze_objects(self, params: Dict) -> Dict:
        """Analyze mock object validity and simple geometry measurements."""
        selectors = [
            "id" in params,
            "name" in params,
            "object_ids" in params,
            params.get("selected") is True,
        ]
        if sum(1 for selector in selectors if selector) != 1:
            raise Exception("analyze_objects requires exactly one of id, name, object_ids, or selected=true.")

        if params.get("selected") is True:
            targets = []
        elif "object_ids" in params:
            if len(params["object_ids"]) == 0:
                raise Exception("analyze_objects object_ids must contain at least one id.")
            targets = [self._get_object_info({"id": obj_id}) for obj_id in params["object_ids"]]
        else:
            targets = [self._get_object_info(params)]

        analyses = [self._analysis_payload(obj) for obj in targets]
        return {"object_count": len(analyses), "analyses": analyses}

    def _analysis_payload(self, obj: Dict) -> Dict:
        bbox = obj.get("bounding_box", [[0, 0, 0], [0, 0, 0]])
        dims = [
            bbox[1][0] - bbox[0][0],
            bbox[1][1] - bbox[0][1],
            bbox[1][2] - bbox[0][2],
        ]
        return {
            "id": obj["id"],
            "name": obj.get("name", ""),
            "type": obj.get("type", "UNKNOWN"),
            "layer": obj.get("layer", "Default"),
            "valid": True,
            "validity_log": None,
            "bounding_box": bbox,
            "bbox_dimensions": dims,
            "metrics": self._analysis_metrics(obj),
        }

    def _analysis_metrics(self, obj: Dict) -> Dict:
        obj_type = obj.get("type", "UNKNOWN").upper()
        geometry = obj.get("geometry", {})
        if obj_type == "LINE":
            start = geometry.get("start", [0, 0, 0])
            end = geometry.get("end", [0, 0, 0])
            length = sum((end[i] - start[i]) ** 2 for i in range(3)) ** 0.5
            return {
                "length": length,
                "is_closed": False,
                "start_point": start,
                "end_point": end,
            }
        if obj_type == "BOX":
            width = geometry.get("width", 1)
            length = geometry.get("length", 1)
            height = geometry.get("height", 1)
            return {
                "is_solid": True,
                "volume": width * length * height,
                "face_count": 6,
                "edge_count": 12,
                "vertex_count": 8,
                "naked_edge_count": 0,
            }
        return {}

    def _modify_object(self, params: Dict) -> Dict:
        """Modify an object."""
        obj = self._get_object_info(params)
        obj_id = obj["id"]

        if params.get("new_name"):
            obj["name"] = params["new_name"]
        if params.get("new_color"):
            color = params["new_color"]
            obj["color"] = {"r": color[0], "g": color[1], "b": color[2]}

        self.objects[obj_id] = obj
        return obj

    def _delete_object(self, params: Dict) -> Dict:
        """Delete an object. Mirrors the C# handler's contract:
        - all=true returns {deleted, count, scope: "all"} and rejects mixed selectors.
        - id/name return {id, name, deleted}.
        """
        all_flag = params.get("all") is True
        has_selector = ("id" in params) or ("name" in params)
        if all_flag and has_selector:
            raise Exception("delete_object: 'all' cannot be combined with 'id' or 'name'.")
        if all_flag:
            count = len(self.objects)
            self.objects.clear()
            return {"deleted": True, "count": count, "scope": "all"}
        if not has_selector:
            raise Exception("delete_object requires id, name, or all=true.")

        obj = self._get_object_info(params)
        obj_id = obj["id"]
        del self.objects[obj_id]
        return {"id": obj_id, "name": obj["name"], "deleted": True}

    def _select_objects(self, params: Dict) -> Dict:
        """Select objects with the same and/or semantics as the C# handler
        for name and color. Rejects invalid filters_type so wrapper tests
        catch shape regressions.

        Note: this mock doesn't model Rhino user-string attributes, so
        custom-attribute filters never match here. Integration tests for
        custom-attribute selection should target the real plugin instead.
        """
        filters = params.get("filters", {})
        filters_type = params.get("filters_type", "and")
        if filters_type not in ("and", "or"):
            raise Exception(f"Invalid filters_type '{filters_type}': expected 'and' or 'or'.")

        if not filters:
            return {"count": len(self.objects)}

        name_values = filters.get("name")
        color = filters.get("color")
        custom = {k: v for k, v in filters.items() if k not in ("name", "color")}

        def color_matches(o):
            c = o.get("color", {})
            return [c.get("r"), c.get("g"), c.get("b")] == color

        count = 0
        for obj in self.objects.values():
            if filters_type == "and":
                ok = True
                if name_values is not None and obj.get("name") not in name_values:
                    ok = False
                if ok and color is not None and not color_matches(obj):
                    ok = False
                # Custom attribute filtering is not modeled in the mock document.
                # Treat unknown attrs as not-matching to keep AND strict.
                if ok and custom:
                    ok = False
            else:
                ok = False
                if name_values is not None and obj.get("name") in name_values:
                    ok = True
                if not ok and color is not None and color_matches(obj):
                    ok = True
                # custom attrs not modeled — OR ignores them silently
            if ok:
                count += 1
        return {"count": count}

    def _create_layer(self, params: Dict) -> Dict:
        """Create a layer."""
        layer_id = str(uuid.uuid4())
        name = params.get("name", f"Layer {len(self.layers)}")

        layer = {
            "id": layer_id,
            "name": name,
            "color": {"r": 0, "g": 0, "b": 0},
            "parent": "00000000-0000-0000-0000-000000000000"
        }

        if params.get("color"):
            color = params["color"]
            layer["color"] = {"r": color[0], "g": color[1], "b": color[2]}

        self.layers[name] = layer
        return layer

    def _delete_layer(self, params: Dict) -> Dict:
        """Delete a layer."""
        name = params.get("name")
        if name and name in self.layers:
            layer = self.layers.pop(name)
            return {"name": name, "deleted": True}
        raise Exception(f"Layer '{name}' not found")

    def _get_or_set_current_layer(self, params: Dict) -> Dict:
        """Get or set current layer."""
        if params.get("name"):
            if params["name"] in self.layers:
                self.current_layer = params["name"]
            else:
                raise Exception(f"Layer '{params['name']}' not found")

        return self.layers.get(self.current_layer, {"name": self.current_layer})

    def _push_undo(self, action):
        """Push an action to the undo stack."""
        self.undo_stack.append(action)
        self.redo_stack.clear()

    def _undo(self, params: Dict) -> Dict:
        """Undo operations."""
        steps = params.get("steps", 1)
        undone = 0

        for _ in range(steps):
            if not self.undo_stack:
                break
            action = self.undo_stack.pop()
            self.redo_stack.append(action)
            undone += 1

        return {
            "undone_steps": undone,
            "requested_steps": steps,
            "message": f"Undid {undone} operation(s)" if undone else "Nothing to undo"
        }

    def _redo(self, params: Dict) -> Dict:
        """Redo operations."""
        steps = params.get("steps", 1)
        redone = 0

        for _ in range(steps):
            if not self.redo_stack:
                break
            action = self.redo_stack.pop()
            self.undo_stack.append(action)
            redone += 1

        return {
            "redone_steps": redone,
            "requested_steps": steps,
            "message": f"Redid {redone} operation(s)" if redone else "Nothing to redo"
        }

    def _boolean_union(self, params: Dict) -> Dict:
        """Mock boolean union."""
        object_ids = params.get("object_ids", [])
        if len(object_ids) < 2:
            raise Exception("Boolean union requires at least 2 objects")

        result_id = str(uuid.uuid4())
        result = {
            "id": result_id,
            "name": params.get("name", "BooleanUnion"),
            "type": "BREP",
            "layer": self.current_layer,
            "color": {"r": 0, "g": 0, "b": 0},
            "bounding_box": [[-2, -2, -2], [2, 2, 2]],
            "geometry": {}
        }

        if params.get("delete_sources", True):
            for obj_id in object_ids:
                self.objects.pop(obj_id, None)

        self.objects[result_id] = result
        return {"result_ids": [result_id], "count": 1, "message": "Boolean union created 1 object(s)"}

    def _boolean_difference(self, params: Dict) -> Dict:
        """Mock boolean difference."""
        base_id = params.get("base_id")
        subtract_ids = params.get("subtract_ids", [])

        if not base_id or not subtract_ids:
            raise Exception("Boolean difference requires base_id and subtract_ids")

        result_id = str(uuid.uuid4())
        result = {
            "id": result_id,
            "name": params.get("name", "BooleanDifference"),
            "type": "BREP",
            "layer": self.current_layer,
            "color": {"r": 0, "g": 0, "b": 0},
            "bounding_box": [[-1, -1, -1], [1, 1, 1]],
            "geometry": {}
        }

        if params.get("delete_sources", True):
            self.objects.pop(base_id, None)
            for obj_id in subtract_ids:
                self.objects.pop(obj_id, None)

        self.objects[result_id] = result
        return {"result_ids": [result_id], "count": 1, "message": "Boolean difference created 1 object(s)"}

    def _boolean_intersection(self, params: Dict) -> Dict:
        """Mock boolean intersection."""
        object_ids = params.get("object_ids", [])
        if len(object_ids) < 2:
            raise Exception("Boolean intersection requires at least 2 objects")

        result_id = str(uuid.uuid4())
        result = {
            "id": result_id,
            "name": params.get("name", "BooleanIntersection"),
            "type": "BREP",
            "layer": self.current_layer,
            "color": {"r": 0, "g": 0, "b": 0},
            "bounding_box": [[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
            "geometry": {}
        }

        if params.get("delete_sources", True):
            for obj_id in object_ids:
                self.objects.pop(obj_id, None)

        self.objects[result_id] = result
        return {"result_ids": [result_id], "count": 1, "message": "Boolean intersection created 1 object(s)"}


    def _run_command(self, params: Dict) -> Dict:
        """Mock Rhino command execution. Returns a fake captured output."""
        command = params.get("command", "")
        if not command:
            raise Exception("command is required")
        return {
            "success": True,
            "command": command,
            "output": f"Mock executed: {command}"
        }

    def _execute_script(self, params: Dict) -> Dict:
        """Mock Python script execution. Returns the new {success, output, message} shape."""
        code = params.get("code", "")
        if not code:
            raise Exception("code is required")
        # Mock heuristic: code containing "raise" or "syntax error" simulates a failure.
        lowered = code.lower()
        if "raise" in lowered or "syntax error" in lowered:
            return {
                "success": False,
                "output": "partial output before error\n",
                "message": "ScriptError: simulated failure"
            }
        return {
            "success": True,
            "output": "Mock script ran.\n"
        }

    def _modify_objects(self, params: Dict) -> Dict:
        """Mock batch modify. Mirrors the C# return shape:
        {success_count, failure_count, total, errors}."""
        objects = params.get("objects", [])
        all_flag = bool(params.get("all"))
        success = 0
        failures: list = []

        targets: list
        if all_flag and objects:
            template = objects[0]
            targets = [{**template, "id": obj_id} for obj_id in list(self.objects.keys())]
        else:
            targets = objects

        for item in targets:
            try:
                obj_id = item.get("id")
                if obj_id and obj_id in self.objects:
                    if "new_color" in item:
                        c = item["new_color"]
                        self.objects[obj_id]["color"] = {"r": c[0], "g": c[1], "b": c[2]}
                    if "new_name" in item:
                        self.objects[obj_id]["name"] = item["new_name"]
                    success += 1
                else:
                    failures.append({"id": obj_id, "error": "not found"})
            except Exception as e:
                failures.append({"id": item.get("id"), "error": str(e)})

        return {
            "success_count": success,
            "failure_count": len(failures),
            "total": success + len(failures),
            "errors": failures,
        }

    def _execute_csharp(self, params: Dict) -> Dict:
        """Mock C# execution. Mirrors the {success, output, message} shape used
        by execute_rhinoscript_python_code so wrapper tests can share fixtures."""
        code = params.get("code", "")
        if not code:
            raise Exception("code is required")
        lowered = code.lower()
        if "throw" in lowered or "syntax error" in lowered:
            return {
                "success": False,
                "output": "partial output before error\n",
                "message": "CompileError: simulated failure",
            }
        return {"success": True, "output": "Mock C# ran.\n"}

    def _capture_viewport(self, params: Dict) -> Dict:
        """Mock viewport capture. Returns a 1x1 transparent PNG so callers
        that decode base64 image_data succeed without dragging in real image
        data. The wrapper logs viewport_name/width/height — surface them."""
        # 1x1 transparent PNG (precomputed)
        png_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgAAIAAAUAAeImBZsAAAAASUVORK5CYII="
        )
        return {
            "image_data": png_b64,
            "mime_type": "image/png",
            "viewport_name": params.get("viewport", "active"),
            "width": params.get("width", 800),
            "height": params.get("height", 600),
        }

    def _make_result_object(self, name: str, type_name: str = "BREP") -> str:
        """Helper: register a placeholder result object and return its id."""
        rid = str(uuid.uuid4())
        self.objects[rid] = {
            "id": rid,
            "name": name,
            "type": type_name,
            "layer": self.current_layer,
            "color": {"r": 0, "g": 0, "b": 0},
            "bounding_box": [[0, 0, 0], [1, 1, 1]],
            "geometry": {},
        }
        return rid

    def _loft(self, params: Dict) -> Dict:
        curves = params.get("curve_ids", [])
        if len(curves) < 2:
            raise Exception("Loft requires at least 2 curves")
        rid = self._make_result_object(params.get("name") or "Loft", "SURFACE")
        return {"result_ids": [rid], "count": 1, "message": "Loft created 1 object(s)"}

    def _extrude_curve(self, params: Dict) -> Dict:
        if not params.get("curve_id"):
            raise Exception("curve_id is required")
        direction = params.get("direction")
        if not (isinstance(direction, list) and len(direction) == 3):
            raise Exception("direction must be [x, y, z]")
        rid = self._make_result_object(params.get("name") or "Extrusion", "EXTRUSION")
        return {"result_id": rid, "message": "Extrusion created"}

    def _sweep1(self, params: Dict) -> Dict:
        if not params.get("rail_id"):
            raise Exception("rail_id is required")
        profiles = params.get("profile_ids", [])
        if not profiles:
            raise Exception("at least one profile_id required")
        rid = self._make_result_object(params.get("name") or "Sweep", "SURFACE")
        return {"result_ids": [rid], "count": 1, "message": "Sweep created 1 object(s)"}

    def _offset_curve(self, params: Dict) -> Dict:
        if not params.get("curve_id"):
            raise Exception("curve_id is required")
        rid = self._make_result_object(params.get("name") or "Offset", "CURVE")
        return {"result_ids": [rid], "count": 1, "message": "Offset created 1 object(s)"}

    def _pipe(self, params: Dict) -> Dict:
        if not params.get("curve_id"):
            raise Exception("curve_id is required")
        radius = params.get("radius")
        if not isinstance(radius, (int, float)) or radius <= 0:
            raise Exception("radius must be a positive number")
        rid = self._make_result_object(params.get("name") or "Pipe", "BREP")
        return {"result_ids": [rid], "count": 1, "message": "Pipe created 1 object(s)"}

    def _get_commands(self, params: Dict) -> Dict:
        """Mock listing of Rhino command names."""
        all_commands = ["Box", "Circle", "Sphere", "BooleanUnion", "BooleanDifference", "Line"]
        filter_str = (params.get("filter") or "").lower()
        if filter_str:
            matched = [c for c in all_commands if filter_str in c.lower()]
        else:
            matched = list(all_commands)
        matched.sort(key=str.lower)
        return {"count": len(matched), "commands": matched}


if __name__ == "__main__":
    server = MockRhinoServer()
    server.start()

    print("\nMock Rhino server running. Press Ctrl+C to stop.\n")
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
