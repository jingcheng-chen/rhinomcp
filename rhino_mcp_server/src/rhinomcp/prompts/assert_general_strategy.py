from rhinomcp.server import mcp


@mcp.prompt()
def asset_general_strategy() -> str:
    """Defines the preferred strategy for working with Rhino objects"""
    return """
    ============================================================
    RHINO MCP STRATEGY GUIDE
    ============================================================

    STEP 1: UNDERSTAND THE DOCUMENT
    -------------------------------
    Always start by calling get_document_summary() to understand:
    - What objects already exist
    - Available layers
    - Current document state


    STEP 2: CHOOSE THE RIGHT TOOL
    -----------------------------
    Use this decision tree:

    Creating geometry:
    ├─ Simple primitives (box, sphere, cylinder, cone, point, line, circle, arc)?
    │   └─ YES → Use create_object() or create_objects()
    │
    ├─ Multiple similar objects (>3)?
    │   └─ YES → Use create_objects() in batches of 50 max
    │
    ├─ Loft surface through curves?
    │   └─ YES → Use loft(curve_ids=[...])
    │
    ├─ Extrude a curve along a direction?
    │   └─ YES → Use extrude_curve(curve_id, direction=[x,y,z])
    │
    ├─ Sweep profiles along a rail?
    │   └─ YES → Use sweep1(rail_id, profile_ids=[...])
    │
    ├─ Offset a curve?
    │   └─ YES → Use offset_curve(curve_id, distance)
    │
    ├─ Create a pipe/tube along a curve?
    │   └─ YES → Use pipe(curve_id, radius)
    │
    ├─ Boolean operations (union, difference, intersection)?
    │   └─ YES → Use boolean_union(), boolean_difference(), boolean_intersection()
    │
    └─ Other complex geometry (NURBS editing, mesh operations)?
        └─ YES → Use execute_rhinoscript_python_code()
                 (MUST call get_rhinoscript_docs() first!)

    Modifying geometry:
    ├─ Simple changes (rename, color, transform)?
    │   └─ YES → Use modify_object() or modify_objects()
    │
    └─ Complex modifications (rebuild, edit points, trim)?
        └─ YES → Use execute_rhinoscript_python_code()

    Querying:
    ├─ Know the object ID?
    │   └─ YES → Use get_object_info(id=...)
    │
    ├─ Know the object name?
    │   └─ YES → Use get_object_info(name=...)
    │
    ├─ Need objects by criteria (type, layer, color)?
    │   └─ YES → Use get_objects(filters=...)
    │
    └─ Need selected objects?
        └─ YES → Use get_selected_objects_info()


    STEP 3: BEST PRACTICES
    ----------------------
    1. NAMING: Always give objects meaningful names for future reference

    2. BATCHING: For many objects, use create_objects() with max 50 per call

    3. LAYERS: Organize objects on appropriate layers using create_layer()
       and set layer with modify_object()

    4. UNDO SAFETY: Complex operations can be undone with undo()

    5. VERIFICATION: After creation, use get_object_info() to verify success

    6. RHINOSCRIPT: When using execute_rhinoscript_python_code():
       - ALWAYS call get_rhinoscript_docs() first to verify syntax
       - See rhinoscript_workflow prompt for detailed steps
       - Never guess function names or parameters
    """


@mcp.prompt()
def rhinoscript_workflow() -> str:
    """
    CRITICAL: Workflow for writing RhinoScript Python code.
    Follow this workflow to avoid syntax errors and hallucination.
    """
    return """
    ============================================================
    RHINOSCRIPT PYTHON CODE WORKFLOW - MANDATORY STEPS
    ============================================================

    When writing RhinoScript Python code, you MUST follow this workflow:

    STEP 1: SEARCH FOR FUNCTIONS
    ----------------------------
    Before writing ANY code, call one of these tools:

    - get_rhinoscript_docs("your goal")
      Returns comprehensive documentation for relevant functions.
      Example: get_rhinoscript_docs("loft surface between curves")

    - search_rhinoscript_functions("keyword")
      Quick search to find function names.
      Example: search_rhinoscript_functions("boolean")

    - list_rhinoscript_modules()
      See all available modules when exploring.

    - get_module_functions("module_name")
      Get all functions in a specific module.


    STEP 2: READ DOCUMENTATION CAREFULLY
    ------------------------------------
    Pay attention to:
    - Exact function signature (parameter names and order)
    - Parameter types (point vs guid vs list)
    - Return types (what the function returns)
    - Example code (copy patterns from examples)


    STEP 3: WRITE CODE USING EXACT SIGNATURES
    ------------------------------------------
    - Import: import rhinoscriptsyntax as rs
    - Use print() to output results
    - Use ONLY functions you found in documentation
    - Match parameter types exactly


    STEP 4: EXECUTE WITH VERIFICATION
    ---------------------------------
    Call execute_rhinoscript_python_code() with:
    - code: Your Python code
    - verified_functions: List of function names you looked up

    Example:
    execute_rhinoscript_python_code(
        code="import rhinoscriptsyntax as rs\\nrs.AddLine([0,0,0], [10,0,0])",
        verified_functions=["AddLine"]
    )


    COMMON MISTAKES TO AVOID:
    ========================
    1. Guessing function names (ALWAYS verify first)
    2. Wrong parameter order (check signature)
    3. Wrong parameter types:
       - Points are lists [x, y, z], not tuples
       - Object references are GUIDs (strings), not objects
    4. Forgetting to import rhinoscriptsyntax
    5. Not handling None returns from failed operations


    NEVER HALLUCINATE FUNCTION NAMES OR SIGNATURES.
    The documentation tools are your source of truth.
    """
