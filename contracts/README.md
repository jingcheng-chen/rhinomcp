# RhinoMCP Contracts

This directory contains JSON Schema definitions for the RhinoMCP protocol. These schemas serve as the **single source of truth** for data exchange between the Python MCP server and the C# Rhino plugin.

## Directory Structure

```
contracts/
├── protocol.json           # Protocol envelope (command/response wrapper)
├── common/
│   └── definitions.json    # Shared type definitions (color, point3d, etc.)
├── commands/               # Command parameter schemas
│   ├── create_object.json
│   ├── modify_object.json
│   ├── delete_object.json
│   ├── get_object_info.json
│   ├── get_document_info.json
│   ├── get_selected_objects_info.json
│   ├── select_objects.json
│   ├── create_layer.json
│   ├── delete_layer.json
│   ├── get_or_set_current_layer.json
│   └── execute_rhinoscript_python_code.json
└── responses/              # Response schemas
    ├── object_info.json
    ├── layer_info.json
    ├── document_info.json
    ├── delete_result.json
    ├── select_result.json
    └── execute_script_result.json
```

## Protocol Format

### Command (Python → C#)

```json
{
  "type": "command_name",
  "params": { /* command-specific parameters */ }
}
```

### Response (C# → Python)

**Success:**
```json
{
  "status": "success",
  "result": { /* command-specific result */ }
}
```

**Error:**
```json
{
  "status": "error",
  "message": "Error description"
}
```

## Common Types

| Type | Format | Example |
|------|--------|---------|
| `color` | `[r, g, b]` (0-255) | `[255, 0, 0]` |
| `colorObject` | `{r, g, b}` | `{"r": 255, "g": 0, "b": 0}` |
| `point3d` | `[x, y, z]` | `[1.0, 2.5, 3.0]` |
| `vector3d` | `[x, y, z]` | `[0.0, 0.0, 1.0]` |
| `guid` | UUID string | `"12345678-1234-1234-1234-123456789012"` |
| `boundingBox` | `[[min], [max]]` | `[[0,0,0], [1,1,1]]` |

## Usage

### Python Validation

```python
from rhinomcp.validation import validate_command, validate_response

# Validate before sending
params = {"type": "BOX", "params": {"width": 1, "length": 1, "height": 1}}
validate_command("create_object", params)  # Raises on invalid

# Validate received response
validate_response("create_object", response_data)
```

### C# Validation

Use the generated contract classes or validate with NJsonSchema:

```csharp
var schema = await JsonSchema.FromFileAsync("contracts/commands/create_object.json");
var errors = schema.Validate(jsonString);
```

## Adding New Commands

1. Create command schema in `contracts/commands/new_command.json`
2. Create response schema in `contracts/responses/new_result.json` (if needed)
3. Add command type to `protocol.json` enum
4. Implement in both Python (`tools/new_command.py`) and C# (`Functions/NewCommand.cs`)
5. Run validation tests

## Schema Validation

Test schemas are valid JSON Schema:

```bash
# Using ajv-cli
npx ajv-cli validate -s contracts/commands/create_object.json -d test_data.json
```
