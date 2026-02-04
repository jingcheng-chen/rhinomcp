"""
RhinoScript documentation tools - Context7-like approach for accurate code generation.

This module provides semantic search and comprehensive documentation retrieval
to prevent AI hallucination when writing RhinoScript Python code.
"""

from mcp.server.fastmcp import Context
from rhinomcp.server import mcp, logger
from rhinomcp.static.rhinoscriptsyntax import rhinoscriptsyntax_json
from typing import Any, List, Dict, Optional


def _score_match(query_terms: List[str], text: str) -> int:
    """Score how well query terms match the text."""
    text_lower = text.lower()
    score = 0
    for term in query_terms:
        if term in text_lower:
            score += 1
            # Bonus for exact word match
            if f" {term} " in f" {text_lower} " or text_lower.startswith(term) or text_lower.endswith(term):
                score += 1
    return score


def _search_functions(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Internal function to search RhinoScript functions by keyword.
    Returns matching functions sorted by relevance.
    """
    query_terms = query.lower().split()
    results = []

    for module in rhinoscriptsyntax_json:
        for func in module["functions"]:
            # Build searchable text from name and description
            searchable = f"{func['Name']} {func.get('Description', '')}".lower()

            # Score the match
            score = _score_match(query_terms, searchable)

            # Also check signature for parameter names
            signature = func.get('Signature', '')
            score += _score_match(query_terms, signature.lower())

            if score > 0:
                results.append({
                    "name": func["Name"],
                    "signature": func.get("Signature", func["Name"] + "()"),
                    "description": func.get("Description", "")[:300],
                    "module": module["ModuleName"],
                    "_score": score
                })

    # Sort by score descending, then by name
    results.sort(key=lambda x: (-x["_score"], x["name"]))

    # Remove internal score field
    for r in results:
        del r["_score"]

    return results[:limit]


def _get_function_details(function_name: str) -> Optional[Dict[str, Any]]:
    """Get full documentation for a specific function."""
    for module in rhinoscriptsyntax_json:
        for func in module["functions"]:
            if func["Name"].lower() == function_name.lower():
                return {
                    "name": func["Name"],
                    "module": module["ModuleName"],
                    "signature": func.get("Signature", ""),
                    "description": func.get("Description", ""),
                    "parameters": func.get("ArgumentDesc", ""),
                    "returns": func.get("Returns", ""),
                    "example": func.get("Example", []),
                }
    return None


@mcp.tool()
def search_rhinoscript_functions(ctx: Context, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search RhinoScript functions by keyword or description.

    Use this tool to find the correct function names before writing any RhinoScript code.

    Parameters:
    - query: What you want to do (e.g., "loft", "create surface from curves", "boolean union", "extrude")
    - limit: Maximum number of results to return (default: 10)

    Returns:
    - List of matching functions with name, signature, description, and module

    Example queries:
    - "loft surface" -> finds AddLoftSrf, etc.
    - "boolean" -> finds BooleanDifference, BooleanUnion, BooleanIntersection
    - "create curve" -> finds AddCurve, AddLine, AddArc, etc.
    - "rotate" -> finds RotateObject, RotateObjects, etc.

    IMPORTANT: Always use this tool BEFORE writing RhinoScript code to find correct function names.
    """
    try:
        results = _search_functions(query, limit)
        if not results:
            return [{
                "message": f"No functions found matching '{query}'. Try different keywords.",
                "suggestion": "Try broader terms like 'curve', 'surface', 'mesh', 'transform', etc."
            }]
        return results
    except Exception as e:
        logger.error(f"Error searching functions: {str(e)}")
        return [{"error": str(e)}]


@mcp.tool()
def get_rhinoscript_docs(
    ctx: Context,
    topic: str,
    include_examples: bool = True,
    max_functions: int = 5
) -> Dict[str, Any]:
    """
    Get comprehensive RhinoScript documentation for a topic.

    This is the PRIMARY tool to use before writing any RhinoScript Python code.
    It searches for relevant functions and returns complete documentation including
    signatures, parameters, return values, and examples.

    Parameters:
    - topic: What you want to accomplish (e.g., "loft surface between curves", "boolean operations", "extrude curve")
    - include_examples: Whether to include code examples (default: True)
    - max_functions: Maximum number of function docs to return (default: 5)

    Returns:
    - Comprehensive documentation for the most relevant functions

    CRITICAL: You MUST call this tool before using execute_rhinoscript_python_code.
    Using functions without checking their documentation leads to syntax errors.

    Example usage:
    1. User asks: "Create a loft surface between two curves"
    2. Call: get_rhinoscript_docs("loft surface curves")
    3. Read the returned documentation carefully
    4. Write code using ONLY the exact signatures shown
    """
    try:
        # Search for relevant functions
        search_results = _search_functions(topic, max_functions)

        if not search_results:
            return {
                "success": False,
                "message": f"No functions found for topic '{topic}'",
                "suggestion": "Try different keywords. Available modules: " +
                    ", ".join(sorted(set(m["ModuleName"] for m in rhinoscriptsyntax_json)))
            }

        # Get full documentation for each function
        functions = []
        for result in search_results:
            details = _get_function_details(result["name"])
            if details:
                if not include_examples:
                    details.pop("example", None)
                functions.append(details)

        return {
            "success": True,
            "topic": topic,
            "functions_found": len(functions),
            "documentation": functions,
            "usage_reminder": (
                "Use these EXACT function signatures when writing code. "
                "Import with: import rhinoscriptsyntax as rs"
            )
        }

    except Exception as e:
        logger.error(f"Error getting docs: {str(e)}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_rhinoscript_modules(ctx: Context) -> Dict[str, Any]:
    """
    List all available RhinoScript modules and their function counts.

    Use this to explore what's available in RhinoScript when you're not sure
    what module contains the functions you need.

    Returns:
    - List of all modules with function counts and descriptions
    """
    try:
        modules = []
        for module in rhinoscriptsyntax_json:
            module_name = module["ModuleName"]
            func_count = len(module["functions"])
            # Get first few function names as examples
            example_funcs = [f["Name"] for f in module["functions"][:5]]

            modules.append({
                "module": module_name,
                "function_count": func_count,
                "example_functions": example_funcs
            })

        # Sort by module name
        modules.sort(key=lambda x: x["module"])

        return {
            "total_modules": len(modules),
            "total_functions": sum(m["function_count"] for m in modules),
            "modules": modules
        }

    except Exception as e:
        logger.error(f"Error listing modules: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
def get_module_functions(ctx: Context, module_name: str) -> Dict[str, Any]:
    """
    Get all functions in a specific RhinoScript module with their signatures.

    Parameters:
    - module_name: The module name (e.g., "curve", "surface", "mesh", "transformation")

    Use list_rhinoscript_modules() first to see available modules.

    Returns:
    - All functions in the module with signatures and brief descriptions
    """
    try:
        module_name_lower = module_name.lower()

        for module in rhinoscriptsyntax_json:
            if module["ModuleName"].lower() == module_name_lower:
                functions = []
                for func in module["functions"]:
                    functions.append({
                        "name": func["Name"],
                        "signature": func.get("Signature", func["Name"] + "()"),
                        "description": func.get("Description", "")[:150]
                    })

                return {
                    "module": module["ModuleName"],
                    "function_count": len(functions),
                    "functions": functions
                }

        # Module not found
        available = sorted(set(m["ModuleName"] for m in rhinoscriptsyntax_json))
        return {
            "error": f"Module '{module_name}' not found",
            "available_modules": available
        }

    except Exception as e:
        logger.error(f"Error getting module functions: {str(e)}")
        return {"error": str(e)}
