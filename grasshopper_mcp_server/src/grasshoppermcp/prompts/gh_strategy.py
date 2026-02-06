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


    STEP 2: FIND COMPONENT NAMES (EFFICIENT APPROACH)
    ------------------------------------------------
    IMPORTANT: Do NOT call search_components multiple times for each component!

    RECOMMENDED WORKFLOW:
    1. Use common component names directly (listed below) - they are verified to work
    2. For uncommon components, use batch_search_components(queries=["A", "B", "C"])
       to search multiple at once

    COMMON COMPONENT NAMES (use exactly as shown - no search needed):

    Inputs:
    - "Number Slider" - numeric input (with min/max/value/decimals)
    - "Boolean Toggle" - true/false input
    - "Panel" - text display/input
    - "Point" - point parameter

    Primitives:
    - "Construct Point" - point from X,Y,Z
    - "Line" - line from two points
    - "Circle" - circle from plane and radius
    - "Rectangle" - rectangle from plane and size
    - "Arc" - arc from plane, radius, angle
    - "Polyline" - polyline from points

    Surfaces:
    - "Extrude" - extrude curve along vector
    - "Loft" - surface from curves
    - "Sweep1" - sweep along one rail
    - "Pipe" - pipe along curve
    - "Boundary Surfaces" - surface from closed curves

    Transforms:
    - "Move" - translate geometry
    - "Rotate" - rotate around axis
    - "Scale" - scale geometry
    - "Mirror" - mirror across plane

    Math:
    - "Addition" - add values
    - "Multiplication" - multiply values
    - "Division" - divide values
    - "Series" - generate number sequence
    - "Range" - numbers in domain
    - "Random" - random numbers
    - "Sine" - sine of angle (USE THIS for trig, not Expression!)
    - "Cosine" - cosine of angle
    - "Tangent" - tangent of angle

    Lists:
    - "List Item" - get item by index
    - "Merge" - combine data streams
    - "Flatten" - flatten tree
    - "Graft" - graft to branches

    Vectors:
    - "Unit X" / "Unit Y" / "Unit Z" - unit vectors
    - "Vector XYZ" - vector from components
    - "Amplitude" - set vector length

    ONLY USE SEARCH FOR UNCOMMON COMPONENTS:
    └─ batch_search_components(queries=["ComponentA", "ComponentB"]) - search multiple at once
    └─ search_components(query="specific") - only for single unusual component

    TIP: For trigonometry, use "Sine", "Cosine", "Tangent" components (not Expression)


    STEP 3: CHOOSE THE RIGHT TOOL
    -----------------------------
    Use this decision tree:

    Creating a complete definition (RECOMMENDED - ALWAYS USE THIS):
    └─ Use create_definition() to create EVERYTHING in ONE call:
       - ALL sliders
       - ALL processing components (Series, Sine, Multiplication, etc.)
       - ALL geometry (Construct Point, Interpolate, Extrude, etc.)
       - ALL connections between them

       DO NOT split into multiple calls! Build the entire definition at once.
       Native GH components CAN handle complex patterns - no scripts needed!

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
    ├─ Set a slider value?
    │   └─ YES → Use set_parameter_value(nickname, value)
    │            Also supports: min, max to adjust range
    │
    ├─ Set panel content?
    │   └─ YES → Use set_parameter_value(nickname, "text content")
    │
    ├─ Set expression formula?
    │   └─ YES → Use set_parameter_value(nickname, "x*sin(y)")
    │            The expression uses variable names from inputs (x, y, z, etc.)
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


    STEP 4: CONFIGURING SPECIAL COMPONENTS
    --------------------------------------
    Number Sliders - FULLY SUPPORTED in create_definition:
    {"name": "Number Slider", "nickname": "Amp", "position": [0,0],
     "min": 0, "max": 10, "value": 5, "decimals": 2}

    After creation, adjust with: set_parameter_value(nickname="Amp", value=7.5)

    For trigonometry, use dedicated components:
    - "Sine" for sin(x), "Cosine" for cos(x), "Tangent" for tan(x)
    - Chain with "Multiplication", "Addition" for complex formulas
    - These are easier than Expression and work reliably via MCP

    Panel - set content during creation OR after:
    {"name": "Panel", "nickname": "Info", "position": [0,0], "content": "Hello"}


    STEP 5: BEST PRACTICES
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


    EXAMPLE: PARAMETRIC SINE WAVE (complete in ONE call!)
    =====================================================
    create_definition(
        clear_canvas=True,
        components=[
            # All sliders
            {"name": "Number Slider", "nickname": "Count", "min": 10, "max": 100, "value": 50},
            {"name": "Number Slider", "nickname": "Amplitude", "min": 1, "max": 10, "value": 3},
            {"name": "Number Slider", "nickname": "Frequency", "min": 0.1, "max": 1, "value": 0.2},
            # All processing components
            {"name": "Series", "nickname": "XValues", "position": [200, 0]},
            {"name": "Multiplication", "nickname": "FreqX", "position": [350, 30]},
            {"name": "Sine", "nickname": "SineWave", "position": [500, 30]},
            {"name": "Multiplication", "nickname": "AmpY", "position": [650, 30]},
            # Geometry
            {"name": "Construct Point", "nickname": "Points", "position": [800, 0]},
            {"name": "Interpolate", "nickname": "Curve", "position": [950, 0]},
            {"name": "Unit Z", "nickname": "ExtVec", "position": [950, 80]},
            {"name": "Extrude", "nickname": "Surface", "position": [1100, 40]}
        ],
        connections=[
            {"source": "Count", "target": "XValues", "target_input": 2},
            {"source": "XValues", "target": "FreqX", "target_input": 0},
            {"source": "Frequency", "target": "FreqX", "target_input": 1},
            {"source": "FreqX", "target": "SineWave", "target_input": 0},
            {"source": "SineWave", "target": "AmpY", "target_input": 0},
            {"source": "Amplitude", "target": "AmpY", "target_input": 1},
            {"source": "XValues", "target": "Points", "target_input": 0},
            {"source": "AmpY", "target": "Points", "target_input": 1},
            {"source": "Points", "target": "Curve", "target_input": 0},
            {"source": "Curve", "target": "Surface", "target_input": 0},
            {"source": "ExtVec", "target": "Surface", "target_input": 1}
        ]
    )
    # Bake result
    bake_component(nickname="Surface", layer_name="Sine Wave")

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
