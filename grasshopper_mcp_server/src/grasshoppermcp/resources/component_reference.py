"""Grasshopper component reference resource for MCP."""

from grasshoppermcp.server import mcp

# Common Grasshopper components organized by category
# These are the most frequently used components with their exact names
COMPONENT_REFERENCE = {
    "Params": {
        "Geometry": [
            {"name": "Point", "description": "Contains a collection of 3D points", "inputs": [], "outputs": ["Point"]},
            {"name": "Vector", "description": "Contains a collection of 3D vectors", "inputs": [], "outputs": ["Vector"]},
            {"name": "Plane", "description": "Contains a collection of planes", "inputs": [], "outputs": ["Plane"]},
            {"name": "Line", "description": "Contains a collection of lines", "inputs": [], "outputs": ["Line"]},
            {"name": "Circle", "description": "Contains a collection of circles", "inputs": [], "outputs": ["Circle"]},
            {"name": "Curve", "description": "Contains a collection of curves", "inputs": [], "outputs": ["Curve"]},
            {"name": "Surface", "description": "Contains a collection of surfaces", "inputs": [], "outputs": ["Surface"]},
            {"name": "Brep", "description": "Contains a collection of Breps (boundary representations)", "inputs": [], "outputs": ["Brep"]},
            {"name": "Mesh", "description": "Contains a collection of meshes", "inputs": [], "outputs": ["Mesh"]},
            {"name": "Box", "description": "Contains a collection of boxes", "inputs": [], "outputs": ["Box"]},
            {"name": "Geometry", "description": "Contains a collection of generic geometry", "inputs": [], "outputs": ["Geometry"]},
        ],
        "Primitive": [
            {"name": "Number", "description": "Contains a collection of numbers", "inputs": [], "outputs": ["Number"]},
            {"name": "Integer", "description": "Contains a collection of integers", "inputs": [], "outputs": ["Integer"]},
            {"name": "Boolean", "description": "Contains a collection of booleans", "inputs": [], "outputs": ["Boolean"]},
            {"name": "Text", "description": "Contains a collection of text strings", "inputs": [], "outputs": ["Text"]},
        ],
        "Input": [
            {"name": "Number Slider", "description": "Numeric slider for input values", "special": True,
             "properties": {"min": "Minimum value", "max": "Maximum value", "value": "Current value", "decimals": "Decimal places"}},
            {"name": "Boolean Toggle", "description": "Toggle between true/false", "special": True},
            {"name": "Panel", "description": "Text panel for input/output display", "special": True},
            {"name": "Value List", "description": "List of predefined values to choose from", "special": True},
            {"name": "Colour Swatch", "description": "Color picker", "special": True},
        ],
    },
    "Maths": {
        "Operators": [
            {"name": "Addition", "nickname": "Add", "description": "Add two or more values", "inputs": ["A", "B"], "outputs": ["Result"]},
            {"name": "Subtraction", "nickname": "Sub", "description": "Subtract two values", "inputs": ["A", "B"], "outputs": ["Result"]},
            {"name": "Multiplication", "nickname": "Mul", "description": "Multiply two or more values", "inputs": ["A", "B"], "outputs": ["Result"]},
            {"name": "Division", "nickname": "Div", "description": "Divide two values", "inputs": ["A", "B"], "outputs": ["Result"]},
            {"name": "Modulus", "nickname": "Mod", "description": "Remainder of division", "inputs": ["A", "B"], "outputs": ["Result"]},
            {"name": "Power", "nickname": "Pow", "description": "Raise to power", "inputs": ["Base", "Exponent"], "outputs": ["Result"]},
            {"name": "Absolute", "nickname": "Abs", "description": "Absolute value", "inputs": ["Value"], "outputs": ["Result"]},
            {"name": "Negative", "nickname": "Neg", "description": "Negate value", "inputs": ["Value"], "outputs": ["Result"]},
        ],
        "Domain": [
            {"name": "Construct Domain", "description": "Create a numeric domain from min/max", "inputs": ["A", "B"], "outputs": ["Domain"]},
            {"name": "Deconstruct Domain", "description": "Extract min/max from domain", "inputs": ["Domain"], "outputs": ["Start", "End"]},
            {"name": "Remap Numbers", "description": "Remap values from one domain to another", "inputs": ["Value", "Source", "Target"], "outputs": ["Mapped"]},
        ],
        "Trig": [
            {"name": "Sine", "nickname": "Sin", "description": "Sine of angle", "inputs": ["Value"], "outputs": ["Result"]},
            {"name": "Cosine", "nickname": "Cos", "description": "Cosine of angle", "inputs": ["Value"], "outputs": ["Result"]},
            {"name": "Tangent", "nickname": "Tan", "description": "Tangent of angle", "inputs": ["Value"], "outputs": ["Result"]},
        ],
        "Util": [
            {"name": "Pi", "description": "Pi constant", "inputs": ["Factor"], "outputs": ["Pi"]},
            {"name": "Random", "description": "Random number generator", "inputs": ["Domain", "Seed"], "outputs": ["Random"]},
            {"name": "Series", "description": "Create a series of numbers", "inputs": ["Start", "Step", "Count"], "outputs": ["Series"]},
            {"name": "Range", "description": "Create a range of numbers", "inputs": ["Domain", "Steps"], "outputs": ["Range"]},
            {"name": "Fibonacci", "description": "Fibonacci sequence", "inputs": ["Seed0", "Seed1", "Count"], "outputs": ["Series"]},
        ],
    },
    "Sets": {
        "List": [
            {"name": "List Item", "description": "Get item from list by index", "inputs": ["List", "Index"], "outputs": ["Item"]},
            {"name": "List Length", "description": "Get length of list", "inputs": ["List"], "outputs": ["Length"]},
            {"name": "Reverse List", "description": "Reverse order of list", "inputs": ["List"], "outputs": ["List"]},
            {"name": "Sort List", "description": "Sort a list", "inputs": ["Keys", "Values"], "outputs": ["Keys", "Values"]},
            {"name": "Shift List", "description": "Shift list items", "inputs": ["List", "Shift"], "outputs": ["List"]},
            {"name": "Insert Items", "description": "Insert items into list", "inputs": ["List", "Item", "Index"], "outputs": ["List"]},
            {"name": "Cull Index", "description": "Remove items by index", "inputs": ["List", "Indices"], "outputs": ["List"]},
            {"name": "Cull Pattern", "description": "Remove items by pattern", "inputs": ["List", "Pattern"], "outputs": ["List"]},
        ],
        "Tree": [
            {"name": "Merge", "description": "Merge multiple data streams", "inputs": ["D1", "D2"], "outputs": ["Result"]},
            {"name": "Entwine", "description": "Entwine multiple data streams", "inputs": ["Branch"], "outputs": ["Result"]},
            {"name": "Flatten", "description": "Flatten data tree to list", "inputs": ["Tree"], "outputs": ["List"]},
            {"name": "Graft", "description": "Graft data into individual branches", "inputs": ["Tree"], "outputs": ["Tree"]},
            {"name": "Simplify", "description": "Simplify data tree paths", "inputs": ["Tree"], "outputs": ["Tree"]},
            {"name": "Path Mapper", "description": "Remap tree paths with lexical rules", "inputs": ["Tree"], "outputs": ["Tree"]},
        ],
        "Sequence": [
            {"name": "Repeat Data", "description": "Repeat data a number of times", "inputs": ["Data", "Number"], "outputs": ["Data"]},
            {"name": "Duplicate Data", "description": "Duplicate data", "inputs": ["Data", "Number"], "outputs": ["Data"]},
            {"name": "Jitter", "description": "Randomly shuffle list", "inputs": ["List", "Jitter", "Seed"], "outputs": ["List"]},
        ],
    },
    "Vector": {
        "Point": [
            {"name": "Construct Point", "nickname": "Pt", "description": "Create point from X,Y,Z", "inputs": ["X", "Y", "Z"], "outputs": ["Point"]},
            {"name": "Deconstruct Point", "nickname": "pDecon", "description": "Extract X,Y,Z from point", "inputs": ["Point"], "outputs": ["X", "Y", "Z"]},
            {"name": "Point XYZ", "description": "Point from coordinates", "inputs": ["X", "Y", "Z"], "outputs": ["Point"]},
            {"name": "Numbers to Points", "description": "Create points from number lists", "inputs": ["X", "Y", "Z"], "outputs": ["Points"]},
            {"name": "Distance", "description": "Distance between two points", "inputs": ["A", "B"], "outputs": ["Distance"]},
        ],
        "Vector": [
            {"name": "Unit X", "description": "Unit vector in X direction", "inputs": ["Factor"], "outputs": ["Vector"]},
            {"name": "Unit Y", "description": "Unit vector in Y direction", "inputs": ["Factor"], "outputs": ["Vector"]},
            {"name": "Unit Z", "description": "Unit vector in Z direction", "inputs": ["Factor"], "outputs": ["Vector"]},
            {"name": "Vector XYZ", "description": "Create vector from components", "inputs": ["X", "Y", "Z"], "outputs": ["Vector"]},
            {"name": "Deconstruct Vector", "description": "Extract vector components", "inputs": ["Vector"], "outputs": ["X", "Y", "Z"]},
            {"name": "Vector Length", "description": "Length of vector", "inputs": ["Vector"], "outputs": ["Length"]},
            {"name": "Amplitude", "description": "Set vector amplitude", "inputs": ["Vector", "Amplitude"], "outputs": ["Vector"]},
            {"name": "Cross Product", "description": "Cross product of vectors", "inputs": ["A", "B"], "outputs": ["Vector"]},
            {"name": "Dot Product", "description": "Dot product of vectors", "inputs": ["A", "B"], "outputs": ["Dot"]},
        ],
        "Plane": [
            {"name": "XY Plane", "description": "World XY plane", "inputs": ["Origin"], "outputs": ["Plane"]},
            {"name": "XZ Plane", "description": "World XZ plane", "inputs": ["Origin"], "outputs": ["Plane"]},
            {"name": "YZ Plane", "description": "World YZ plane", "inputs": ["Origin"], "outputs": ["Plane"]},
            {"name": "Construct Plane", "description": "Create plane from origin and axes", "inputs": ["Origin", "X", "Y"], "outputs": ["Plane"]},
            {"name": "Deconstruct Plane", "description": "Extract plane components", "inputs": ["Plane"], "outputs": ["Origin", "X", "Y", "Z"]},
        ],
        "Grid": [
            {"name": "Square Grid", "description": "2D grid of points", "inputs": ["Plane", "Size", "ExtX", "ExtY"], "outputs": ["Cells", "Points"]},
            {"name": "Rectangular Grid", "description": "Rectangular grid of points", "inputs": ["Plane", "SizeX", "SizeY", "ExtX", "ExtY"], "outputs": ["Cells", "Points"]},
            {"name": "Hexagonal Grid", "description": "Hexagonal grid of points", "inputs": ["Plane", "Size", "ExtX", "ExtY"], "outputs": ["Cells", "Points"]},
        ],
    },
    "Curve": {
        "Primitive": [
            {"name": "Line", "description": "Create line from two points", "inputs": ["Start", "End"], "outputs": ["Line"]},
            {"name": "Line SDL", "description": "Line from start, direction, length", "inputs": ["Start", "Direction", "Length"], "outputs": ["Line"]},
            {"name": "Circle", "description": "Create circle", "inputs": ["Plane", "Radius"], "outputs": ["Circle"]},
            {"name": "Circle CNR", "description": "Circle from center, normal, radius", "inputs": ["Center", "Normal", "Radius"], "outputs": ["Circle"]},
            {"name": "Arc", "description": "Create arc", "inputs": ["Plane", "Radius", "Angle"], "outputs": ["Arc"]},
            {"name": "Arc 3Pt", "description": "Arc through three points", "inputs": ["A", "B", "C"], "outputs": ["Arc"]},
            {"name": "Rectangle", "description": "Create rectangle", "inputs": ["Plane", "X", "Y"], "outputs": ["Rectangle"]},
            {"name": "Polygon", "description": "Create polygon", "inputs": ["Plane", "Radius", "Segments"], "outputs": ["Polygon"]},
        ],
        "Spline": [
            {"name": "Interpolate", "description": "Create curve through points", "inputs": ["Vertices", "Degree", "Periodic"], "outputs": ["Curve"]},
            {"name": "Nurbs Curve", "description": "Create NURBS curve", "inputs": ["Vertices", "Degree", "Periodic"], "outputs": ["Curve"]},
            {"name": "Polyline", "description": "Create polyline through points", "inputs": ["Vertices", "Closed"], "outputs": ["Polyline"]},
            {"name": "Bezier Span", "description": "Create Bezier curve", "inputs": ["Vertices"], "outputs": ["Curve"]},
        ],
        "Analysis": [
            {"name": "Evaluate Curve", "description": "Evaluate curve at parameter", "inputs": ["Curve", "Parameter"], "outputs": ["Point", "Tangent", "Curvature"]},
            {"name": "Curve Length", "description": "Length of curve", "inputs": ["Curve"], "outputs": ["Length"]},
            {"name": "Curve Domain", "description": "Domain of curve", "inputs": ["Curve"], "outputs": ["Domain"]},
            {"name": "End Points", "description": "Start and end of curve", "inputs": ["Curve"], "outputs": ["Start", "End"]},
        ],
        "Division": [
            {"name": "Divide Curve", "description": "Divide curve into segments", "inputs": ["Curve", "Count"], "outputs": ["Points", "Tangents", "Parameters"]},
            {"name": "Divide Distance", "description": "Divide curve by distance", "inputs": ["Curve", "Distance"], "outputs": ["Points", "Tangents", "Parameters"]},
            {"name": "Divide Length", "description": "Divide curve by length", "inputs": ["Curve", "Length"], "outputs": ["Points", "Tangents", "Parameters"]},
            {"name": "Shatter", "description": "Break curve at parameters", "inputs": ["Curve", "Parameters"], "outputs": ["Segments"]},
        ],
        "Util": [
            {"name": "Join Curves", "description": "Join curves into polycurves", "inputs": ["Curves"], "outputs": ["Curves"]},
            {"name": "Flip Curve", "description": "Reverse curve direction", "inputs": ["Curve"], "outputs": ["Curve"]},
            {"name": "Offset Curve", "description": "Offset curve", "inputs": ["Curve", "Distance", "Plane"], "outputs": ["Curve"]},
            {"name": "Fillet", "description": "Fillet curve corners", "inputs": ["Curve", "Radius"], "outputs": ["Curve"]},
            {"name": "Project Curve", "description": "Project curve to Brep", "inputs": ["Curve", "Brep", "Direction"], "outputs": ["Curve"]},
        ],
    },
    "Surface": {
        "Primitive": [
            {"name": "Sphere", "description": "Create sphere", "inputs": ["Base", "Radius"], "outputs": ["Sphere"]},
            {"name": "Box", "description": "Create box", "inputs": ["Base", "X", "Y", "Z"], "outputs": ["Box"]},
            {"name": "Cylinder", "description": "Create cylinder", "inputs": ["Base", "Radius", "Length"], "outputs": ["Cylinder"]},
            {"name": "Cone", "description": "Create cone", "inputs": ["Base", "Radius", "Length"], "outputs": ["Cone"]},
            {"name": "Center Box", "description": "Box centered on point", "inputs": ["Base", "X", "Y", "Z"], "outputs": ["Box"]},
        ],
        "Freeform": [
            {"name": "Loft", "description": "Create surface from curves", "inputs": ["Curves", "Options"], "outputs": ["Loft"]},
            {"name": "Sweep1", "description": "Sweep along one rail", "inputs": ["Rail", "Sections"], "outputs": ["Brep"]},
            {"name": "Sweep2", "description": "Sweep along two rails", "inputs": ["Rail1", "Rail2", "Sections"], "outputs": ["Brep"]},
            {"name": "Extrude", "description": "Extrude curve along vector", "inputs": ["Base", "Direction"], "outputs": ["Extrusion"]},
            {"name": "Extrude Point", "description": "Extrude to point", "inputs": ["Base", "Point"], "outputs": ["Extrusion"]},
            {"name": "Revolution", "description": "Revolve curve around axis", "inputs": ["Curve", "Axis", "Angle"], "outputs": ["Brep"]},
            {"name": "Pipe", "description": "Create pipe along curve", "inputs": ["Curve", "Radius"], "outputs": ["Brep"]},
            {"name": "Boundary Surfaces", "description": "Create surface from boundary curves", "inputs": ["Edges"], "outputs": ["Surfaces"]},
        ],
        "Analysis": [
            {"name": "Evaluate Surface", "description": "Evaluate surface at UV", "inputs": ["Surface", "UV"], "outputs": ["Point", "Normal", "Frame"]},
            {"name": "Surface Domain", "description": "Get surface domain", "inputs": ["Surface"], "outputs": ["U Domain", "V Domain"]},
            {"name": "Area", "description": "Calculate area", "inputs": ["Geometry"], "outputs": ["Area", "Centroid"]},
            {"name": "Volume", "description": "Calculate volume", "inputs": ["Geometry"], "outputs": ["Volume", "Centroid"]},
        ],
        "Util": [
            {"name": "Offset Surface", "description": "Offset surface", "inputs": ["Surface", "Distance"], "outputs": ["Surface"]},
            {"name": "Isotrim", "description": "Extract surface subset", "inputs": ["Surface", "Domain"], "outputs": ["Surface"]},
            {"name": "Divide Surface", "description": "Divide surface into points", "inputs": ["Surface", "U", "V"], "outputs": ["Points", "Normals", "Parameters"]},
            {"name": "Brep Join", "description": "Join Breps into solid", "inputs": ["Breps"], "outputs": ["Brep"]},
            {"name": "Cap Holes", "description": "Cap planar holes in Brep", "inputs": ["Brep"], "outputs": ["Brep"]},
        ],
    },
    "Mesh": {
        "Primitive": [
            {"name": "Mesh Box", "description": "Create mesh box", "inputs": ["Box", "X", "Y", "Z"], "outputs": ["Mesh"]},
            {"name": "Mesh Sphere", "description": "Create mesh sphere", "inputs": ["Base", "Radius", "U", "V"], "outputs": ["Mesh"]},
            {"name": "Mesh Plane", "description": "Create mesh plane", "inputs": ["Plane", "W", "H", "U", "V"], "outputs": ["Mesh"]},
        ],
        "Util": [
            {"name": "Mesh Brep", "description": "Convert Brep to mesh", "inputs": ["Brep", "Settings"], "outputs": ["Mesh"]},
            {"name": "Mesh Join", "description": "Join meshes", "inputs": ["Meshes"], "outputs": ["Mesh"]},
            {"name": "Mesh Faces", "description": "Extract mesh faces", "inputs": ["Mesh"], "outputs": ["Faces"]},
            {"name": "Mesh Vertices", "description": "Extract mesh vertices", "inputs": ["Mesh"], "outputs": ["Vertices"]},
            {"name": "Deconstruct Mesh", "description": "Deconstruct mesh", "inputs": ["Mesh"], "outputs": ["Vertices", "Faces", "Colors", "Normals"]},
            {"name": "Construct Mesh", "description": "Create mesh from vertices and faces", "inputs": ["Vertices", "Faces"], "outputs": ["Mesh"]},
        ],
    },
    "Transform": {
        "Affine": [
            {"name": "Move", "description": "Move geometry", "inputs": ["Geometry", "Motion"], "outputs": ["Geometry"]},
            {"name": "Rotate", "description": "Rotate geometry around axis", "inputs": ["Geometry", "Angle", "Plane"], "outputs": ["Geometry"]},
            {"name": "Rotate Axis", "description": "Rotate around specific axis", "inputs": ["Geometry", "Angle", "Axis"], "outputs": ["Geometry"]},
            {"name": "Scale", "description": "Scale geometry uniformly", "inputs": ["Geometry", "Center", "Factor"], "outputs": ["Geometry"]},
            {"name": "Scale NU", "description": "Scale non-uniformly", "inputs": ["Geometry", "Center", "X", "Y", "Z"], "outputs": ["Geometry"]},
            {"name": "Mirror", "description": "Mirror geometry across plane", "inputs": ["Geometry", "Plane"], "outputs": ["Geometry"]},
            {"name": "Orient", "description": "Orient geometry from plane to plane", "inputs": ["Geometry", "Source", "Target"], "outputs": ["Geometry"]},
        ],
        "Array": [
            {"name": "Move Away From", "description": "Move points away from point", "inputs": ["Points", "Emitter", "Factor"], "outputs": ["Points"]},
            {"name": "Linear Array", "description": "Create linear array", "inputs": ["Geometry", "Direction", "Count"], "outputs": ["Geometry"]},
            {"name": "Rectangular Array", "description": "Create rectangular array", "inputs": ["Geometry", "X", "Y", "CountX", "CountY"], "outputs": ["Geometry"]},
            {"name": "Polar Array", "description": "Create polar array", "inputs": ["Geometry", "Plane", "Count", "Angle"], "outputs": ["Geometry"]},
        ],
        "Morph": [
            {"name": "Box Morph", "description": "Morph geometry to fit box", "inputs": ["Geometry", "Reference", "Target"], "outputs": ["Geometry"]},
            {"name": "Surface Morph", "description": "Morph geometry to surface", "inputs": ["Geometry", "Reference", "Surface", "UV"], "outputs": ["Geometry"]},
        ],
    },
    "Display": {
        "Preview": [
            {"name": "Custom Preview", "description": "Preview with custom material", "inputs": ["Geometry", "Material"], "outputs": []},
            {"name": "Point Cloud", "description": "Display point cloud", "inputs": ["Points", "Colors"], "outputs": []},
        ],
        "Colour": [
            {"name": "Colour RGB", "description": "Create color from RGB", "inputs": ["Red", "Green", "Blue", "Alpha"], "outputs": ["Colour"]},
            {"name": "Colour HSL", "description": "Create color from HSL", "inputs": ["Hue", "Saturation", "Lightness", "Alpha"], "outputs": ["Colour"]},
            {"name": "Gradient", "description": "Sample gradient at parameter", "inputs": ["Gradient", "Parameter"], "outputs": ["Colour"]},
        ],
    },
    "Intersect": {
        "Physical": [
            {"name": "Solid Intersection", "description": "Boolean intersection", "inputs": ["A", "B"], "outputs": ["Result"]},
            {"name": "Solid Union", "description": "Boolean union", "inputs": ["Breps"], "outputs": ["Result"]},
            {"name": "Solid Difference", "description": "Boolean difference", "inputs": ["A", "B"], "outputs": ["Result"]},
        ],
        "Mathematical": [
            {"name": "Curve | Curve", "nickname": "CCX", "description": "Curve curve intersection", "inputs": ["A", "B"], "outputs": ["Points", "ParamsA", "ParamsB"]},
            {"name": "Curve | Plane", "nickname": "CPX", "description": "Curve plane intersection", "inputs": ["Curve", "Plane"], "outputs": ["Points", "Params"]},
            {"name": "Curve | Surface", "nickname": "CSX", "description": "Curve surface intersection", "inputs": ["Curve", "Surface"], "outputs": ["Points", "UV", "Params"]},
            {"name": "Surface | Surface", "nickname": "SSX", "description": "Surface surface intersection", "inputs": ["A", "B"], "outputs": ["Curves"]},
            {"name": "Brep | Plane", "nickname": "BPX", "description": "Brep plane intersection", "inputs": ["Brep", "Plane"], "outputs": ["Curves"]},
        ],
    },
}


def get_component_reference_text() -> str:
    """Generate a formatted text reference of all components."""
    lines = ["# Grasshopper Component Reference", ""]
    lines.append("Use exact component names when calling create_definition or add_component.")
    lines.append("Use search_components tool to find components not listed here.")
    lines.append("")

    for category, subcats in COMPONENT_REFERENCE.items():
        lines.append(f"## {category}")
        for subcat, components in subcats.items():
            lines.append(f"### {subcat}")
            for comp in components:
                name = comp["name"]
                nick = comp.get("nickname", "")
                desc = comp.get("description", "")
                special = " [SPECIAL]" if comp.get("special") else ""
                nick_str = f" ({nick})" if nick else ""
                lines.append(f"- **{name}**{nick_str}: {desc}{special}")
            lines.append("")

    return "\n".join(lines)


@mcp.resource("grasshopper://components/reference")
def component_reference_resource() -> str:
    """
    Complete reference of common Grasshopper components.
    Use this to find the exact component names for create_definition or add_component.
    """
    return get_component_reference_text()


@mcp.resource("grasshopper://components/special")
def special_components_resource() -> str:
    """
    Reference for special components that need direct instantiation.
    These components (sliders, toggles, panels) require specific handling.
    """
    return """# Special Grasshopper Components

These components are in Grasshopper.Kernel.Special namespace and require direct instantiation.

## Number Slider
- **Name**: "Number Slider"
- **Properties**: min, max, value, decimals
- **Example**:
  ```json
  {"name": "Number Slider", "nickname": "MySlider", "position": [0, 0], "min": 0, "max": 100, "value": 50, "decimals": 2}
  ```

## Boolean Toggle
- **Name**: "Boolean Toggle"
- **Properties**: value (true/false)
- **Example**:
  ```json
  {"name": "Boolean Toggle", "nickname": "MyToggle", "position": [0, 0], "value": true}
  ```

## Panel
- **Name**: "Panel"
- **Properties**: content/value (text content)
- **Example**:
  ```json
  {"name": "Panel", "nickname": "Info", "position": [0, 0], "content": "Display text"}
  ```

## Value List
- **Name**: "Value List"
- **Example**:
  ```json
  {"name": "Value List", "nickname": "Options", "position": [0, 0]}
  ```

## Colour Swatch
- **Name**: "Colour Swatch" (or "Color Swatch")
- **Example**:
  ```json
  {"name": "Colour Swatch", "nickname": "MyColor", "position": [0, 0]}
  ```

## Relay
- **Name**: "Relay"
- **Description**: Wire relay point for organizing connections

## Scribble
- **Name**: "Scribble"
- **Properties**: text
- **Description**: Text annotation on canvas

## Group
- **Name**: "Group"
- **Properties**: group_name
- **Description**: Visual grouping of components
"""


# Use-case organized guide - helps AI understand WHAT to use for specific tasks
USE_CASE_GUIDE = """
# Grasshopper Component Guide by Use Case

This guide helps you choose the right components for common tasks.
Use get_component_type_info(name="ComponentName") to check inputs before creating.

## CREATING WAVE/SINUSOIDAL PATTERNS

### Simple Approach (RECOMMENDED)
Use dedicated trig components instead of Expression:
- "Sine" - Takes angle, outputs sine value
- "Cosine" - Takes angle, outputs cosine value
- "Tangent" - Takes angle, outputs tangent value

Example workflow for a sine wave:
```
Series (0 to 2*Pi) → Sine → Construct Point (use result as Y or Z)
```

Components needed:
1. "Series" - generates values from 0 to n (inputs: Start, Step, Count)
2. "Sine" - calculates sine (input: Value in radians)
3. "Multiplication" - scale the result (inputs: A, B)
4. "Construct Point" - create points from X, Y, Z values

### DO NOT use Expression for simple trig!
Expression has DYNAMIC inputs (only x, y by default). It's complex and error-prone.

---

## CREATING GRIDS OF POINTS

### Rectangular Grid
- "Square Grid" - uniform grid (inputs: Plane, Size, ExtX, ExtY)
- "Rectangular Grid" - non-uniform (inputs: Plane, SizeX, SizeY, ExtX, ExtY)

### Custom Grid
Use nested Series:
1. "Series" for X coordinates
2. "Series" for Y coordinates
3. "Cross Reference" to combine
4. "Construct Point" from the coordinates

---

## CREATING PARAMETRIC FACADES

Typical component flow:
1. Grid of points: "Rectangular Grid" or "Square Grid"
2. Displacement: "Move" with vectors from "Sine"/"Cosine" calculations
3. Curves through points: "Interpolate" (creates smooth curve through points)
4. Surface from curves: "Loft" or "Sweep1"
5. Thickness: "Extrude" with "Unit X/Y/Z" vector

Key components:
- "Divide Surface" - get points on a surface (inputs: Surface, U count, V count)
- "Interpolate" - smooth curve through points (inputs: Vertices, Degree, Periodic)
- "Loft" - surface from multiple curves (inputs: Curves, Options)

---

## MATHEMATICAL OPERATIONS

### Basic Math (use these, not Expression!)
- "Addition" - A + B (can chain multiple inputs)
- "Subtraction" - A - B
- "Multiplication" - A * B
- "Division" - A / B
- "Power" - base^exponent
- "Modulus" - remainder of division

### Trigonometry (use these, not Expression!)
- "Sine" - sin(x) where x is in radians
- "Cosine" - cos(x)
- "Tangent" - tan(x)
- "Pi" - multiply factor by Pi

### Number Sequences
- "Series" - start, step, count → list of numbers
- "Range" - domain, steps → evenly spaced numbers
- "Random" - random numbers in domain

### Remapping Values
- "Remap Numbers" - map value from source domain to target domain
- "Construct Domain" - create domain from min/max

---

## CREATING CURVES

### Straight Lines
- "Line" - from Start point to End point
- "Line SDL" - from Start, Direction vector, Length

### Circles and Arcs
- "Circle" - from Plane and Radius (input 0: Plane, input 1: Radius)
- "Arc" - from Plane, Radius, and Angle
- "Arc 3Pt" - through three points

### Curves Through Points
- "Polyline" - straight segments through points
- "Interpolate" - smooth curve through points (NURBS)
- "Nurbs Curve" - control point curve

### Rectangles
- "Rectangle" - from Plane, X size, Y size
  IMPORTANT: X and Y inputs expect NUMBER values, not Domains!
  Input 0: Plane, Input 1: X size, Input 2: Y size

---

## CREATING SURFACES

### From Curves
- "Loft" - surface through multiple curves
- "Sweep1" - sweep section along one rail
- "Sweep2" - sweep between two rails
- "Boundary Surfaces" - fill closed planar curves

### From Points/Curves
- "Extrude" - extend curve along vector (inputs: Base, Direction)
- "Pipe" - tube along curve (inputs: Curve, Radius)
- "Revolution" - rotate curve around axis

### Primitives
- "Sphere" - from base plane and radius
- "Box" - from base plane and X, Y, Z sizes
- "Cylinder" - from base, radius, length

---

## TRANSFORMATIONS

### Move/Translate
- "Move" - geometry + translation vector
  Create vectors with: "Unit X", "Unit Y", "Unit Z", "Vector XYZ"

### Rotate
- "Rotate" - geometry + angle + plane (rotates around plane Z axis)
- "Rotate Axis" - geometry + angle + specific axis

### Scale
- "Scale" - uniform scale from center point
- "Scale NU" - non-uniform scale (different X, Y, Z factors)

### Arrays/Patterns
- "Linear Array" - repeat along direction
- "Polar Array" - repeat around center
- "Rectangular Array" - 2D grid of copies

---

## GOTCHAS AND WARNINGS

### Expression Component - AVOID for simple math!
- Only has "x" and "y" inputs by default
- Additional inputs must be added manually in GH UI
- Use dedicated math components instead (Sine, Cosine, Addition, etc.)

### Rectangle Component
- Inputs expect NUMBER values for X and Y sizes, NOT domains
- Common error: "Data conversion failed from Domain to Rectangle"
- Correct: connect Number Slider directly to X and Y inputs

### Circle Component
- Input 0 is Plane (optional, defaults to XY plane)
- Input 1 is Radius (required)

### Interpolate vs Polyline
- Interpolate creates SMOOTH curves (NURBS)
- Polyline creates STRAIGHT segments between points

### Domain vs Number
- Some components expect Domains (min/max range): "Remap Numbers"
- Most expect Numbers: "Rectangle", "Circle", etc.
- Use "Construct Domain" to create domains from numbers

---

## QUICK COMPONENT LOOKUP

Inputs: "Number Slider", "Panel", "Boolean Toggle", "Point"
Math: "Addition", "Multiplication", "Division", "Sine", "Cosine", "Series", "Range"
Points: "Construct Point", "Deconstruct Point", "Distance"
Vectors: "Unit X", "Unit Y", "Unit Z", "Vector XYZ", "Amplitude"
Curves: "Line", "Circle", "Rectangle", "Arc", "Polyline", "Interpolate"
Surfaces: "Extrude", "Loft", "Sweep1", "Pipe", "Boundary Surfaces"
Transform: "Move", "Rotate", "Scale", "Mirror"
Lists: "List Item", "Merge", "Flatten", "Graft", "Reverse List"
"""


@mcp.resource("grasshopper://components/guide")
def component_guide_resource() -> str:
    """
    Use-case organized guide for Grasshopper components.
    Helps you choose the right components for common tasks.
    Includes warnings about problematic components.
    """
    return USE_CASE_GUIDE


@mcp.resource("grasshopper://components/gotchas")
def component_gotchas_resource() -> str:
    """
    Known issues and warnings for Grasshopper components.
    Check this before using unfamiliar components.
    """
    return """# Grasshopper Component Gotchas

## Expression Component - AVOID for simple math!
**Problem**: Expression only has "x" and "y" inputs by default. You cannot add more inputs via MCP.

**Solution**: Use dedicated math components instead:
- For sin(x): Use "Sine" component
- For cos(x): Use "Cosine" component
- For x + y: Use "Addition" component
- For x * y: Use "Multiplication" component
- For x^n: Use "Power" component

**If you must use Expression**:
1. Create it with just x, y variables
2. Set formula with: set_parameter_value(nickname="Expr", value="x*sin(y)")

---

## Rectangle Component
**Problem**: "Data conversion failed from Domain to Rectangle"

**Cause**: Rectangle expects NUMBER inputs for X and Y sizes, not Domains.

**Wrong**:
```json
{"source": "DomainComponent", "target": "Rect", "target_input": 1}
```

**Correct**:
```json
{"source": "NumberSlider", "target": "Rect", "target_input": 1}
```

Input mapping:
- Input 0: Plane (optional)
- Input 1: X Size (Number)
- Input 2: Y Size (Number)
- Input 3: Radius (Number, for rounded corners)

---

## Circle Component
**Problem**: Circle not appearing or wrong position

**Cause**: Input order confusion

Input mapping:
- Input 0: Plane (defines center and orientation)
- Input 1: Radius (Number)

To place at a point, connect point to the Plane input or create plane at point.

---

## Loft Component
**Problem**: Loft creates twisted or incorrect surface

**Cause**: Curves not in correct order or orientations flipped

**Solutions**:
1. Ensure curves are ordered from bottom to top (or start to end)
2. Use "Flip Curve" if curves have inconsistent directions
3. Check "Loft Options" for alignment settings

---

## Divide Curve vs Divide Surface
**Divide Curve**: Creates points ALONG a curve
- Inputs: Curve, Count (number of segments)
- Outputs: Points, Tangents, Parameters

**Divide Surface**: Creates grid of points ON a surface
- Inputs: Surface, U count, V count
- Outputs: Points, Normals, Parameters

---

## Series vs Range
**Series**: Start + Step × n
- Series(0, 1, 5) → [0, 1, 2, 3, 4]
- Inputs: Start, Step, Count

**Range**: Evenly divide a domain
- Range(0 to 10, 5) → [0, 2.5, 5, 7.5, 10]
- Inputs: Domain, Steps

---

## Move Component
**Problem**: Geometry doesn't move or moves wrong direction

**Cause**: Motion vector not correctly defined

Input mapping:
- Input 0: Geometry
- Input 1: Motion (Vector)

Create vectors with:
- "Unit X/Y/Z" for axis-aligned motion
- "Vector XYZ" for custom direction
- Multiply vector by number for distance

---

## Script Components (C#, Python, VB)
**Problem**: Wrong number of inputs/outputs

**Cause**: Script components have CONFIGURABLE inputs/outputs that can only be set in the GH UI.

**Solution**: For complex logic, use multiple standard components chained together, or use the execute_csharp_code tool for procedural operations.

---

## Data Tree Mismatches
**Problem**: Component produces unexpected results or "1 item" when expecting many

**Cause**: Data tree structure mismatch between inputs

**Solutions**:
- "Flatten" - collapse tree to single list
- "Graft" - wrap each item in its own branch
- "Simplify" - remove redundant tree levels
- "Cross Reference" - combine lists in specific patterns
"""
