from rhinomcp.server import mcp


@mcp.prompt()
def asset_general_strategy() -> str:
    """Defines the preferred strategy for creating assets in Rhino"""
    return """

    QUERY STRATEGY:
    - if the id of the object is known, use the id to query the object.
    - if the id is not known, use the name of the object to query the object.


    CREATION STRATEGY:

    0. Before anything, always check the document from get_document_summary().
    1. If the execute_rhinoscript_python_code() function is not able to create the objects, use the create_objects() function.
    2. If there are multiple objects, use the method create_objects() to create multiple objects at once. Do not attempt to create them one by one if they are more than 10.
    3. When including an object into document, ALWAYS make sure that the name of the object is meanful.
    4. Try to include as many objects as possible accurately and efficiently. If the command is not able to include so many data, try to create the objects in batches.
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
