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

    When creating rhinoscript python code:
    - do not hallucinate, only use the syntax that is supported by rhinoscriptsyntax or Rhino,Geometry.
    - double check the code if any of the code is not correct, and fix it.
    """
