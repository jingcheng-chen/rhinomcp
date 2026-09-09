from rhinomcp.server import mcp


@mcp.prompt()
def asset_general_strategy() -> str:
    """Inspect, construct and verify Rhino geometry with the bundled modeling guide."""
    from rhinomcp.guidance import modeling_guidance

    return modeling_guidance("overview")["content"]


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


    STEP 4: EXECUTE
    ---------------
    Call execute_rhinoscript_python_code() with the verified code. The tool
    accepts a single `code` argument — there is no separate verified-functions
    field on the wire. The expectation is that you have already verified the
    signatures via get_rhinoscript_docs() / search_rhinoscript_functions().

    Example:
    execute_rhinoscript_python_code(
        code="import rhinoscriptsyntax as rs\\nrs.AddLine([0,0,0], [10,0,0])",
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
