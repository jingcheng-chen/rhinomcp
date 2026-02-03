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
        self.layers: Dict[str, Dict[str, Any]] = {
            "Default": {"id": str(uuid.uuid4()), "name": "Default", "color": [0, 0, 0]}
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

    def _handle_client(self, client_socket: socket.socket):
        """Handle a client connection."""
        try:
            while self.running:
                data = client_socket.recv(65536)
                if not data:
                    break

                try:
                    command = json.loads(data.decode('utf-8'))
                    response = self._process_command(command)
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                except json.JSONDecodeError as e:
                    error_response = {"status": "error", "message": f"Invalid JSON: {e}"}
                    client_socket.sendall(json.dumps(error_response).encode('utf-8'))
        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            client_socket.close()

    def _process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a command and return a response."""
        cmd_type = command.get("type", "")
        params = command.get("params", {})

        handlers = {
            "get_document_info": self._get_document_info,
            "create_object": self._create_object,
            "create_objects": self._create_objects,
            "get_object_info": self._get_object_info,
            "modify_object": self._modify_object,
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
        }

        handler = handlers.get(cmd_type)
        if handler:
            try:
                result = handler(params)
                return {"status": "success", "result": result}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command: {cmd_type}"}

    def _get_document_info(self, params: Dict) -> Dict:
        """Return document info."""
        return {
            "objects": list(self.objects.values())[:30],
            "layers": list(self.layers.values())[:30],
            "object_count": len(self.objects),
            "layer_count": len(self.layers)
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
            "bounding_box": [[-1, -1, -1], [1, 1, 1]],
            "geometry": params.get("params", {})
        }

        if params.get("color"):
            color = params["color"]
            obj["color"] = {"r": color[0], "g": color[1], "b": color[2]}

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
        """Delete an object."""
        if params.get("all"):
            count = len(self.objects)
            self.objects.clear()
            return {"deleted": True, "count": count}

        obj = self._get_object_info(params)
        obj_id = obj["id"]
        del self.objects[obj_id]
        return {"id": obj_id, "name": obj["name"], "deleted": True}

    def _select_objects(self, params: Dict) -> Dict:
        """Select objects (mock - just returns count)."""
        filters = params.get("filters", {})
        if not filters:
            return {"count": len(self.objects)}

        # Simple mock filtering
        count = 0
        for obj in self.objects.values():
            if "name" in filters and obj["name"] in filters["name"]:
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
