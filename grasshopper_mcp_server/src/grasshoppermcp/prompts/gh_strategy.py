"""Grasshopper MCP strategy prompts."""

from grasshoppermcp.server import mcp


@mcp.prompt()
def gh_general_strategy() -> str:
    """Defines the preferred strategy for working with Grasshopper definitions"""
    return """
    ============================================================
    GRASSHOPPER MCP STRATEGY GUIDE
    ============================================================

    STEP 1: UNDERSTAND THE DOCUMENT
    -------------------------------
    Always start by calling get_gh_document_info() to understand:
    - Whether a document is open
    - Current component count
    - Component breakdown by category

    For detailed state, use get_canvas_state() to see:
    - All components and their positions
    - All connections between components
    - Groups and their contents


    STEP 2: FIND COMPONENT NAMES
    ----------------------------
    Before creating components, find the correct names:

    Search for components:
    └─ Use search_components(query="slider") to find matching components
       Returns: name, nickname, category, subcategory, description, guid

    List all categories:
    └─ Use list_component_categories() to see available categories

    Common component names:
    - "Number Slider" (not just "Slider")
    - "Point" (Params category for point input)
    - "Construct Point" (for creating points from X,Y,Z)
    - "Circle" (for circle geometry)


    STEP 3: CHOOSE THE RIGHT TOOL
    -----------------------------
    Use this decision tree:

    Creating a complete definition (RECOMMENDED for multiple components):
    └─ Use create_definition() to batch create components, connections, and values
       This is the most efficient way to create complex definitions.
       For sliders, you can specify: min, max, value, decimals

    Adding components:
    ├─ Need to add a component?
    │   └─ YES → Use add_component(component_name, position, nickname)
    │            Common names: "Point", "Circle", "Line", "Number Slider",
    │            "Panel", "Addition", "List Item", "Merge", "Loft"
    │
    └─ Need multiple components?
        └─ YES → Call add_component() multiple times with different positions

    Connecting components:
    ├─ Connect output to input?
    │   └─ YES → Use connect_components(source_nickname, target_nickname,
    │            source_output=0, target_input=0)
    │
    └─ Remove a connection?
        └─ YES → Use disconnect_components() with same parameters

    Setting values:
    ├─ Set a slider or parameter value?
    │   └─ YES → Use set_parameter_value(nickname, value)
    │
    └─ Read current values?
        └─ YES → Use get_parameter_value(nickname)

    Managing the solution:
    ├─ Force recomputation?
    │   └─ YES → Use run_solution()
    │
    ├─ Mark component as needing update?
    │   └─ YES → Use expire_solution(nickname)
    │
    └─ Bake geometry to Rhino?
        └─ YES → Use bake_component(nickname, layer_name)

    Querying:
    ├─ Get component details?
    │   └─ YES → Use get_component_info(nickname) or get_component_info(instance_id)
    │
    └─ List all components?
        └─ YES → Use list_components(category=..., name=...)


    STEP 4: BEST PRACTICES
    ----------------------
    1. NICKNAMES: Always give components meaningful nicknames for easy reference
       - Use add_component(..., nickname="MyCircle")
       - Nicknames are case-sensitive

    2. POSITIONING: Space components appropriately
       - Standard spacing: 150-200 units between components
       - Inputs on left, outputs on right
       - Vertical stacking: 80-100 units between rows

    3. CONNECTION FLOW: Build left to right
       - Parameters and inputs on the left
       - Processing in the middle
       - Outputs and bake targets on the right

    4. VERIFY CONNECTIONS: After connecting, use get_component_info()
       to verify the connection was made successfully

    5. BAKING: When baking to Rhino:
       - Specify layer_name to organize output
       - Bake only final results, not intermediate steps

    6. ERROR CHECKING: Check runtime_message_level in component info
       - "Blank" = OK
       - "Warning" = May need attention
       - "Error" = Must fix before proceeding


    EXAMPLE WORKFLOW: Create a circle and extrude it (using create_definition)
    ==========================================================================
    create_definition(
        components=[
            {"name": "Point", "nickname": "BasePoint", "position": [0, 0]},
            {"name": "Number Slider", "nickname": "RadiusSlider", "position": [0, 100],
             "min": 1, "max": 50, "value": 10, "decimals": 1},
            {"name": "Circle", "nickname": "MyCircle", "position": [200, 0]},
            {"name": "Unit Z", "nickname": "ZVector", "position": [200, 100]},
            {"name": "Extrude", "nickname": "MyExtrude", "position": [400, 50]}
        ],
        connections=[
            {"source": "BasePoint", "target": "MyCircle", "target_input": 0},
            {"source": "RadiusSlider", "target": "MyCircle", "target_input": 1},
            {"source": "MyCircle", "target": "MyExtrude", "target_input": 0},
            {"source": "ZVector", "target": "MyExtrude", "target_input": 1}
        ]
    )
    # Then bake the result
    bake_component(nickname="MyExtrude", layer_name="Extruded Circles")

    ALTERNATIVE: Step-by-step approach (use when debugging or modifying existing definitions)
    =======================================================================================
    1. add_component("Point", [0, 0], "BasePoint")
    2. add_component("Circle", [200, 0], "MyCircle")
    3. connect_components(source_nickname="BasePoint", target_nickname="MyCircle", target_input=0)
    4. set_parameter_value(nickname="MyCircle", input_name="Radius", value=10.0)
    5. get_component_info(nickname="MyCircle")  # Check for errors
    6. bake_component(nickname="MyCircle")
    """


@mcp.prompt()
def gh_workflow() -> str:
    """
    Workflow for building Grasshopper definitions programmatically.
    """
    return """
    ============================================================
    GRASSHOPPER DEFINITION BUILDING WORKFLOW
    ============================================================

    When building a Grasshopper definition, follow this workflow:

    PHASE 1: PLAN YOUR DEFINITION
    -----------------------------
    Before adding any components:
    1. Identify inputs (sliders, points, curves from Rhino)
    2. Identify processing steps (what operations to perform)
    3. Identify outputs (geometry to preview/bake)
    4. Sketch the data flow from inputs to outputs


    PHASE 2: ADD INPUT COMPONENTS
    -----------------------------
    Add parameter and input components first:

    - Number Slider: For numeric inputs
      add_component("Number Slider", [0, 0], "RadiusSlider")

    - Point: For point inputs
      add_component("Point", [0, 100], "CenterPoint")

    - Panel: For text/data display
      add_component("Panel", [0, 200], "InfoPanel")

    - Curve/Geometry from Rhino: Reference existing geometry
      add_component("Curve", [0, 300], "InputCurve")


    PHASE 3: ADD PROCESSING COMPONENTS
    ----------------------------------
    Add components that process the inputs:

    Position them to the right of inputs (x offset ~150-200)

    Common processing components:
    - Geometry: Circle, Line, Rectangle, Box, Sphere
    - Curves: Interpolate, Polyline, Divide Curve
    - Surfaces: Loft, Extrude, Sweep1, Sweep2
    - Transforms: Move, Rotate, Scale, Mirror
    - Math: Addition, Multiplication, Series, Range
    - Lists: List Item, Merge, Flatten, Graft


    PHASE 4: CONNECT COMPONENTS
    ---------------------------
    Connect in data flow order:

    1. Identify source output index (usually 0)
    2. Identify target input index (check component docs)
    3. Connect:
       connect_components(
           source_nickname="MySlider",
           target_nickname="MyCircle",
           source_output=0,
           target_input=1  # Radius input
       )


    PHASE 5: SET VALUES AND TEST
    ----------------------------
    1. Set initial parameter values:
       set_parameter_value(nickname="RadiusSlider", value=5.0)

    2. Run the solution:
       run_solution()

    3. Check for errors:
       info = get_component_info(nickname="MyCircle")
       if info["runtime_message_level"] != "Blank":
           print(info["runtime_messages"])


    PHASE 6: BAKE RESULTS
    ---------------------
    When the definition works correctly:

    bake_component(
        nickname="FinalGeometry",
        output_index=0,
        layer_name="GH Output"
    )


    COMMON COMPONENT NAMES
    ======================
    Primitives:
    - "Point", "Line", "Circle", "Rectangle", "Arc"
    - "Box", "Sphere", "Cylinder", "Cone"

    Parameters:
    - "Number Slider", "Panel", "Boolean Toggle"
    - "Point" (Params), "Curve" (Params), "Surface" (Params)

    Curves:
    - "Polyline", "Interpolate", "Nurbs Curve"
    - "Divide Curve", "Evaluate Curve", "Curve Length"
    - "Offset Curve", "Fillet", "Extend Curve"

    Surfaces:
    - "Loft", "Sweep1", "Sweep2", "Extrude"
    - "Revolution", "Pipe", "Offset Surface"
    - "Boundary Surfaces", "Patch"

    Transforms:
    - "Move", "Rotate", "Scale", "Mirror"
    - "Orient", "Project"

    Math:
    - "Addition", "Subtraction", "Multiplication", "Division"
    - "Series", "Range", "Random"

    Lists:
    - "List Item", "List Length", "Reverse List"
    - "Merge", "Flatten", "Graft", "Simplify"


    TIPS
    ====
    - Use get_canvas_state() to see entire definition structure
    - Use list_components() filtered by category to find specific components
    - Runtime errors usually indicate missing inputs or type mismatches
    - Position components logically: inputs left, outputs right
    """
