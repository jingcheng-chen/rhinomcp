import time
import math
import string
import numbers
from operator import attrgetter

import System
import System.Drawing
import System.Windows.Forms

import Rhino

import rhinocompat as compat
import scriptcontext


def ContextIsRhino():
    """Return True if the script is being executed in the context of Rhino
    Returns:
      bool: True if the script is being executed in the context of Rhino
    Example:
      import rhinoscriptsyntax as  rs
      print(rs.ContextIsRhino())
    See Also:
      ContextIsGrasshopper
    """
    return scriptcontext.id == 1


def ContextIsGrasshopper():
    """Return True if the script is being executed in a grasshopper component
    Returns:
      bool: True if the script is being executed in a grasshopper component
    Example:
      import rhinoscriptsyntax as  rs
      print(rs.ContextIsGrasshopper())
    See Also:
      ContextIsRhino
    """
    return scriptcontext.id == 2


def Angle(point1, point2, plane=True):
    """Measures the angle between two points
    Parameters:
      point1, point2 (point): the input points
      plane (bool, optional): Boolean or Plane
        If True, angle calculation is based on the world coordinate system.
        If False, angle calculation is based on the active construction plane
        If a plane is provided, angle calculation is with respect to this plane
    Returns:
      tuple(tuple(number, number), number, number, number, number): containing the following elements if successful
        element 0 = the X,Y angle in degrees
        element 1 = the elevation
        element 2 = delta in the X direction
        element 3 = delta in the Y direction
        element 4 = delta in the Z direction
      None: if not successful
    Example:
      import rhinoscriptsyntax as  rs
      point1 = rs.GetPoint("First  point")
      if point1:
          point2  = rs.GetPoint("Second point")
          if point2:
              angle  = rs.Angle(point1, point2)
              if  angle: print("Angle: {}".format(angle[0]))
    See Also:
      Angle2
      Distance
    """
    pt1 = coerce3dpoint(point1)
    if pt1 is None:
        pt1 = coercerhinoobject(point1)
        if isinstance(pt1, Rhino.DocObjects.PointObject): pt1 = pt1.Geometry.Location
        else: pt1=None
    pt2 = coerce3dpoint(point2)
    if pt2 is None:
        pt2 = coercerhinoobject(point2)
        if isinstance(pt2, Rhino.DocObjects.PointObject): pt2 = pt2.Geometry.Location
        else: pt2=None
    point1 = pt1
    point2 = pt2
    if point1 is None or point2 is None: return scriptcontext.errorhandler()
    vector = point2 - point1
    x = vector.X
    y = vector.Y
    z = vector.Z
    if plane!=True:
        plane = coerceplane(plane)
        if plane is None:
            plane = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane()
        vfrom = point1 - plane.Origin
        vto = point2 - plane.Origin
        x = vto * plane.XAxis - vfrom * plane.XAxis
        y = vto * plane.YAxis - vfrom * plane.YAxis
        z = vto * plane.ZAxis - vfrom * plane.ZAxis
    h = math.sqrt( x * x + y * y)
    angle_xy = math.degrees( math.atan2( y, x ) )
    elevation = math.degrees( math.atan2( z, h ) )
    return angle_xy, elevation, x, y, z


def Angle2(line1, line2):
    """Measures the angle between two lines
    Parameters:
      line1 (line): List of 6 numbers or 2 Point3d.
      line2 (line): List of 6 numbers or 2 Point3d.
    Returns:
      tuple(number, number): containing the following elements if successful.
        0 The angle in degrees.
        1 The reflex angle in degrees.
      None: If not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      point1 = rs.GetPoint("Start of first line")
      point2 = rs.GetPoint("End of first line", point1)
      point3 = rs.GetPoint("Start of second line")
      point4 = rs.GetPoint("End of second line", point3)
      angle = rs.Angle2( (point1, point2), (point3, point4))
      if angle: print("Angle: {}".format(angle))
    See Also:
      Angle
      Distance
    """
    line1 = coerceline(line1, True)
    line2 = coerceline(line2, True)
    vec0 = line1.To - line1.From
    vec1 = line2.To - line2.From
    if not vec0.Unitize() or not vec1.Unitize(): return scriptcontext.errorhandler()
    dot = vec0 * vec1
    dot = clamp(-1,1,dot)
    angle = math.acos(dot)
    reflex_angle = 2.0*math.pi - angle
    angle = math.degrees(angle)
    reflex_angle = math.degrees(reflex_angle)
    return angle, reflex_angle


def ClipboardText(text=None):
    """Returns or sets a text string to the Windows clipboard
    Parameters:
      text (str, optional): text to set
    Returns:
      str: if text is not specified, the current text in the clipboard
      str: if text is specified, the previous text in the clipboard
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      txt = rs.ClipboardText("Hello Rhino!")
      if txt: rs.MessageBox(txt, 0, "Clipboard Text")
    See Also:
      
    """
    rc = None
    if System.Windows.Forms.Clipboard.ContainsText():
        rc = System.Windows.Forms.Clipboard.GetText()
    if text:
        if not isinstance(text, str): text = str(text)
        System.Windows.Forms.Clipboard.SetText(text)
    return rc


def ColorAdjustLuma(rgb, luma, scale=False):
    """Changes the luminance of a red-green-blue value. Hue and saturation are
    not affected
    Parameters:
      rgb (color): initial rgb value
      luma (number): The luminance in units of 0.1 percent of the total range. A
          value of luma = 50 corresponds to 5 percent of the maximum luminance
      scale (bool, optional): if True, luma specifies how much to increment or decrement the
          current luminance. If False, luma specified the absolute luminance.
    Returns:
      color: modified rgb value if successful
    Example:
      import rhinoscriptsyntax as rs
      rgb = rs.ColorAdjustLuma((128, 128, 128), 50)
      print("Red = {}".format(rs.ColorRedValue(rgb)))
      print("Green = {}".format(rs.ColorGreenValue(rgb)))
      print("Blue = {}".format(rs.ColorBlueValue(rgb)))
    See Also:
      ColorHLSToRGB
      ColorRGBToHLS
    """
    rgb = coercecolor(rgb, True)
    hsl = Rhino.Display.ColorHSL(rgb)
    luma = luma / 1000.0
    if scale: luma = hsl.L + luma
    hsl.L = luma
    return hsl.ToArgbColor()


def ColorBlueValue(rgb):
    """Retrieves intensity value for the blue component of an RGB color
    Parameters:
      rgb (color): the RGB color value
    Returns:
      number: The blue component if successful, otherwise None
    Example:
      import rhinoscriptsyntax as rs
      rgb = rs.LayerColor("Default")
      print("Red = {}".format(rs.ColorRedValue(rgb)))
      print("Green = {}".format(rs.ColorGreenValue(rgb)))
      print("Blue = {}".format(rs.ColorBlueValue(rgb)))
    See Also:
      ColorGreenValue
      ColorRedValue
    """
    return coercecolor(rgb, True).B


def ColorGreenValue(rgb):
    """Retrieves intensity value for the green component of an RGB color
    Parameters:
      rgb (color): the RGB color value
    Returns:
      number: The green component if successful, otherwise None
    Example:
      import rhinoscriptsyntax as rs
      rgb = rs.LayerColor("Default")
      print("Red = {}".format(rs.ColorRedValue(rgb)))
      print("Green = {}".format(rs.ColorGreenValue(rgb)))
      print("Blue = {}".format(rs.ColorBlueValue(rgb)))
    See Also:
      ColorBlueValue
      ColorRedValue
    """
    return coercecolor(rgb, True).G


def ColorHLSToRGB(hls):
    """Converts colors from hue-lumanence-saturation to RGB
    Parameters:
      hls (color): the HLS color value
    Returns:
      color: The RGB color value if successful, otherwise False
    Example:
      import rhinoscriptsyntax as rs
      rgb = rs.ColorHLSToRGB( (160, 120, 0) )
      print("Red = {}".format(rs.ColorRedValue(rgb)))
      print("Green = {}".format(rs.ColorGreenValue(rgb)))
      print("Blue = {}".format(rs.ColorBlueValue(rgb)))
    See Also:
      ColorAdjustLuma
      ColorRGBToHLS
    """
    if len(hls)==3:
        hls = Rhino.Display.ColorHSL(hls[0]/240.0, hls[2]/240.0, hls[1]/240.0)
    elif len(hls)==4:
        hls = Rhino.Display.ColorHSL(hls[3]/240.0, hls[0]/240.0, hls[2]/240.0, hls[1]/240.0)
    return hls.ToArgbColor()


def ColorRedValue(rgb):
    """Retrieves intensity value for the red component of an RGB color
    Parameters:
      hls (color): the HLS color value
    Returns:
      color: The red color value if successful, otherwise False
    Example:
      import rhinoscriptsyntax as rs
      rgb = rs.LayerColor("Default")
      print("Red = {}".format(rs.ColorRedValue(rgb)))
      print("Green = {}".format(rs.ColorGreenValue(rgb)))
      print("Blue = {}".format(rs.ColorBlueValue(rgb)))
    See Also:
      ColorBlueValue
      ColorGreenValue
    """
    return coercecolor(rgb, True).R


def ColorRGBToHLS(rgb):
    """Convert colors from RGB to HLS
    Parameters:
      rgb (color): the RGB color value
    Returns:
      color: The HLS color value if successful, otherwise False
    Example:
      import rhinoscriptsyntax as rs
      hls = rs.ColorRGBToHLS((128, 128, 128))
      print("Hue = {}".format(hls[0]))
      print("Luminance = {}".format(hls[1]))
      print("Saturation = {}".format(hls[2]))
    See Also:
      ColorAdjustLuma
      ColorHLSToRGB
    """
    rgb = coercecolor(rgb, True)
    hsl = Rhino.Display.ColorHSL(rgb)
    return hsl.H, hsl.S, hsl.L


def CullDuplicateNumbers(numbers, tolerance=None):
    """Removes duplicates from an array of numbers.
    Parameters:
      numbers ([number, ...]): list or tuple
      tolerance (number, optional): The minimum distance between numbers.  Numbers that fall within this tolerance will be discarded.  If omitted, Rhino's internal zero tolerance is used.
    Returns:
      list(number, ...): numbers with duplicates removed if successful.
    Example:
      import rhinoscriptsyntax as rs
      arr = [1,1,2,2,3,3,4,4,5,5]
      arr = rs.CullDuplicateNumbers(arr)
      for n in arr: print(n)
    See Also:
      CullDuplicatePoints
    """
    count = len(numbers)
    if count < 2: return numbers
    if tolerance is None: tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    numbers = sorted(numbers)
    d = numbers[0]
    index = 1
    for step in range(1,count):
        test_value = numbers[index]
        if math.fabs(d-test_value)<=tolerance:
            numbers.pop(index)
        else:
            d = test_value
            index += 1
    return numbers


def CullDuplicatePoints(points, tolerance=-1):
    """Removes duplicates from a list of 3D points.
    Parameters:
      points ([point, ...]): A list of 3D points.
      tolerance (number): Minimum distance between points. Points within this
        tolerance will be discarded. If omitted, Rhino's internal zero tolerance
        is used.
    Returns:
      list(point, ...): of 3D points with duplicates removed if successful.
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints(,,"First point", "Next point")
      if points:
          points= rs.CullDuplicatePoints(points)
          for p in points: print(p)
    See Also:
      CullDuplicateNumbers
    """
    points = coerce3dpointlist(points, True)
    if tolerance is None or tolerance < 0:
        tolerance = Rhino.RhinoMath.ZeroTolerance
    return list(Rhino.Geometry.Point3d.CullDuplicates(points, tolerance))


def Distance(point1, point2):
    """Measures distance between two 3D points, or between a 3D point and
    an array of 3D points.
    Parameters:
      point1 (point): The first 3D point.
      point2 (point): The second 3D point or list of 3-D points.
    Returns:
      point: If point2 is a 3D point then the distance if successful.
      point: If point2 is a list of points, then an list of distances if successful.
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      point1 = rs.GetPoint("First point")
      if point1:
          point2 = rs.GetPoint("Second point")
          if point2:
              print("Distance: {}".format(rs.Distance(point1, point2)))
    See Also:
      Angle
      Angle2
    """
    from_pt = coerce3dpoint(point1, True)
    to_pt = coerce3dpoint(point2)
    if to_pt: return (to_pt - from_pt).Length
    # check if we have a list of points
    to_pt = coerce3dpointlist(point2, True)
    distances = [(point - from_pt).Length for point in to_pt]
    if distances: return distances


def GetSettings(filename, section=None, entry=None):
    """Returns string from a specified section in a initialization file.
    Parameters:
      filename (str): name of the initialization file
      section (str, optional): section containing the entry
      entry (str, optional): entry whose associated string is to be returned
    Returns:
      list(str, ...): If section is not specified, a list containing all section names
      list:(str, ...): If entry is not specified, a list containing all entry names for a given section
      str: If section and entry are specified, a value for entry
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      filename = rs.OpenFileName("Open", "Initialization Files (*.ini)|*.ini||")
      if filename:
          sections = rs.GetSettings(filename)
          if sections:
              section = rs.ListBox(sections, "Select a section", filename)
              if section:
                  entries = rs.GetSettings(filename, section)
                  if entries:
                      entry = rs.ListBox(entries, "Select an entry", section)
                      if entry:
                          value = rs.GetSettings(filename, section, entry)
                          if value: rs.MessageBox( value, 0, entry )
    See Also:
      
    """
    CP = compat.GET_IMPORT_CONFIG_PARSER()
    try:
        cp = CP.ConfigParser()
        cp.read(filename)
        if not section: return cp.sections()
        section = string.lower(section)
        if not entry: return cp.options(section)
        entry = string.lower(entry)
        return cp.get(section, entry)
    except IOError:
        return scriptcontext.errorhander()
    return scriptcontext.errorhandler()


def Polar(point, angle_degrees, distance, plane=None):
    """Returns 3D point that is a specified angle and distance from a 3D point
    Parameters:
      point (point): the point to transform
      plane (plane, optional): plane to base the transformation. If omitted, the world
        x-y plane is used
    Returns:
      point: resulting point is successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      point = (1.0, 1.0, 0.0)
      result = rs.Polar(point, 45.0, 1.414214)
      print(result)
    See Also:
      PointAdd
      PointCompare
      PointDivide
      PointScale
      PointSubtract
    """
    point = coerce3dpoint(point, True)
    angle = math.radians(angle_degrees)
    if plane: plane = coerceplane(plane)
    else: plane = Rhino.Geometry.Plane.WorldXY
    offset = plane.XAxis
    offset.Unitize()
    offset *= distance
    rc = point+offset
    xform = Rhino.Geometry.Transform.Rotation(angle, plane.ZAxis, point)
    rc.Transform(xform)
    return rc


def SimplifyArray(points):
    """Flattens an array of 3-D points into a one-dimensional list of real numbers. For example, if you had an array containing three 3-D points, this method would return a one-dimensional array containing nine real numbers.
    Parameters:
      points ([point, ...]): Points to flatten
    Returns:
      list(number, ...): A one-dimensional list containing real numbers, if successful, otherwise None
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints()
      if points:
          numbers = rs.SimplifyArray(points)
          for n in numbers: print(n)
    See Also:
      
    """
    rc = []
    for point in points:
        point = coerce3dpoint(point, True)
        rc.append(point.X)
        rc.append(point.Y)
        rc.append(point.Z)
    return rc


def Sleep(milliseconds):
    """Suspends execution of a running script for the specified interval
    Parameters:
      milliseconds (number): thousands of a second
    Returns:
      None
    Example:
      import rhinoscriptsyntax as rs
      print("This")
      rs.Sleep(2000)
      print("is")
      rs.Sleep(2000)
      print("a")
      rs.Sleep(2000)
      print("slow")
      rs.Sleep(2000)
      print("message!")
    See Also:
      
    """
    time.sleep( milliseconds / 1000.0 )
    Rhino.RhinoApp.Wait() #keep the message pump alive

def SortPointList(points, tolerance=None):
    """Sorts list of points so they will be connected in a "reasonable" polyline order
    Parameters:
      points ({point, ...])the points to sort
      tolerance (number, optional): minimum distance between points. Points that fall within this tolerance
        will be discarded. If omitted, Rhino's internal zero tolerance is used.
    Returns:
      list(point, ...): of sorted 3D points if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPointCoordinates()
      if points:
          sorted = rs.SortPointList(points)
          rs.AddPolyline(sorted)
    See Also:
      SortPoints
    """
    points = coerce3dpointlist(points, True)
    if tolerance is None: tolerance = Rhino.RhinoMath.ZeroTolerance
    return list(Rhino.Geometry.Point3d.SortAndCullPointList(points, tolerance))


def SortPoints(points, ascending=True, order=0):
    """Sorts the components of an array of 3D points
    Parameters:
      points ([point, ...]): points to sort
      ascending (bool, optional: ascending if omitted (True) or True, descending if False.
      order (number, optional): the component sort order
        Value       Component Sort Order
        0 (default) X, Y, Z
        1           X, Z, Y
        2           Y, X, Z
        3           Y, Z, X
        4           Z, X, Y
        5           Z, Y, X
    Returns:
      list(point, ...): sorted 3-D points if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints()
      if points:
          points = rs.SortPoints(points)
          for p in points: print(p)
    See Also:
      
    """
    __attrXYZ = attrgetter('X', 'Y', 'Z')
    __attrXZY = attrgetter('X', 'Z', 'Y')
    __attrYXZ = attrgetter('Y', 'X', 'Z')
    __attrYZX = attrgetter('Y', 'Z', 'X')
    __attrZXY = attrgetter('Z', 'X', 'Y')
    __attrZYX = attrgetter('Z', 'Y', 'X')
    __attrgetter = (__attrXYZ, __attrXZY, __attrYXZ, __attrYZX, __attrZXY, __attrZYX)[order]
    return sorted(points, key=__attrgetter, reverse=not ascending)


def Str2Pt(point):
    """convert a formatted string value into a 3D point value
    Parameters:
      point (str): A string that contains a delimited point like "1,2,3".
    Returns:
      point: Point structure from the input string.
      None: error on invalid format
    Example:
      import rhinoscriptsyntax as rs
      point = rs.Str2Pt("1,2,3")
      if point: rs.AddPoint( point )
    See Also:
      
    """
    return coerce3dpoint(point, True)


def clamp(lowvalue, highvalue, value):
    if lowvalue>=highvalue: raise Exception("lowvalue must be less than highvalue")
    if value<lowvalue: return lowvalue
    if value>highvalue: return highvalue
    return value


def fxrange(start, stop, step):
    "float version of the xrange function"
    if step==0: raise ValueError("step must not equal 0")
    x = start
    if start<stop:
        if step<0: raise ValueError("step must be greater than 0")
        while x<=stop:
            yield x
            x+=step
    else:
        if step>0: raise ValueError("step must be less than 0")
        while x>=stop:
            yield x
            x+=step


def frange(start, stop, step):
    "float version of the range function"
    return [x for x in fxrange(start, stop, step)]


def coerce3dpoint(point, raise_on_error=False):
    """Converts input into a Rhino.Geometry.Point3d if possible.
    Parameters:
      point = Point3d, Vector3d, Point3f, Vector3f, str, uuid
      raise_on_error [opt] = True or False
    Returns:
      a Rhino.Geometry.Point3d
    Example:
    See Also:
    """
    if type(point) is Rhino.Geometry.Point3d: return point
    enumerable = compat.GET_HOST().Coerce3dPointFromEnumerables(point)
    if enumerable is not None: return enumerable
    if type(point) is System.Guid:
        found, pt = scriptcontext.doc.Objects.TryFindPoint(point)
        if found: return pt
    if hasattr(point, "__len__") and len(point)==3 and hasattr(point, "__getitem__"):
        try:
            return Rhino.Geometry.Point3d(float(point[0]), float(point[1]), float(point[2]))
        except:
            if raise_on_error: raise
    if type(point) is Rhino.Geometry.Vector3d or type(point) is Rhino.Geometry.Point3f or type(point) is Rhino.Geometry.Vector3f:
        return Rhino.Geometry.Point3d(point.X, point.Y, point.Z)
    if type(point) is str:
        point = point.split(',')
        return Rhino.Geometry.Point3d( float(point[0]), float(point[1]), float(point[2]) )
    if hasattr(point, "__len__") and len(point)==2 and hasattr(point, "__getitem__"):
        try:
            return Rhino.Geometry.Point3d(float(point[0]), float(point[1]), 0.0)
        except:
            if raise_on_error: raise
    if raise_on_error: raise ValueError("Could not convert %s to a Point3d" % point)


def CreatePoint(point, y=None, z=None):
    """Converts 'point' into a Rhino.Geometry.Point3d if possible.
    If the provided object is already a point, it value is copied.
    In case the conversion fails, an error is raised.
    Alternatively, you can also pass two coordinates singularly for a
    point on the XY plane, or three for a 3D point.
    Parameters:
      point (Point3d|Vector3d|Point3f|Vector3f|str|guid|[number, number, number])
    Returns:
      point: a Rhino.Geometry.Point3d. This can be seen as an object with three indices:
        [0]  X coordinate
        [1]  Y coordinate
        [2]  Z coordinate.
    Example:
    See Also:
    """
    if y is not None: return Rhino.Geometry.Point3d(float(point), float(y), float(z or 0.0))
    if type(point) is System.Drawing.Color: return Rhino.Geometry.Point3d(point)
    return coerce3dpoint(point, True)


def coerce2dpoint(point, raise_on_error=False):
    """Convert input into a Rhino.Geometry.Point2d if possible.
    Parameters:
      point = Point2d, list, tuple, Vector3d, Point3d, str
      raise_on_error [opt] = True or False
    Returns:
      a Rhino.Geometry.Point2d
    Example:
    See Also:
    """
    if type(point) is Rhino.Geometry.Point2d: return point
    if type(point) is list or type(point) is tuple:
        length = len(point)
        if length==2 and type(point[0]) is not list and type(point[0]) is not Rhino.Geometry.Point2d:
            return Rhino.Geometry.Point2d(point[0], point[1])
    if type(point) is Rhino.Geometry.Vector3d or type(point) is Rhino.Geometry.Point3d:
        return Rhino.Geometry.Point2d(point.X, point.Y)
    if type(point) is str:
        point = point.split(',')
        return Rhino.Geometry.Point2d( float(point[0]), float(point[1]) )
    if raise_on_error: raise ValueError("Could not convert %s to a Point2d" % point)


def coerce3dvector(vector, raise_on_error=False):
    """Convert input into a Rhino.Geometry.Vector3d if possible.
    Parameters:
      vector = Vector3d, Point3d, list, Point3f, Vector3f, str, uuid
      raise_on_error [opt] = True or False
    Returns:
      a Rhino.Geometry.Vector3d
    Example:
    See Also:
    """
    if type(vector) is Rhino.Geometry.Vector3d: return vector
    point = coerce3dpoint(vector, False)
    if point: return Rhino.Geometry.Vector3d(point.X, point.Y, point.Z)
    if raise_on_error: raise ValueError("Could not convert %s to a Vector3d" % vector)


def CreateVector(vector, y=None, z=None):
    """Converts 'vector' into a Rhino.Geometry.Vector3d if possible.
    If the provided object is already a vector, it value is copied.
    If the conversion fails, an error is raised.
    Alternatively, you can also pass two coordinates singularly for a
    vector on the XY plane, or three for a 3D vector.
    Parameters:
      vector (Vector3d|Point3d|Point3f|Vector3f\str|guid|[number, number, number])
      raise_on_error (bool, optionals): True or False
    Returns:
      a Rhino.Geometry.Vector3d. This can be seen as an object with three indices:
      result[0]: X component, result[1]: Y component, and result[2] Z component.
    Example:
    See Also:
    """
    if y is not None: return Rhino.Geometry.Vector3d(float(vector), float(y), float(z or 0.0))
    if type(vector) is Rhino.Geometry.Vector3d: return Rhino.Geometry.Vector3d(vector)
    return coerce3dvector(vector, True)


def coerce3dpointlist(points, raise_on_error=False):
    if isinstance(points, System.Array[Rhino.Geometry.Point3d]):
        return list(points)
    if isinstance(points, Rhino.Collections.Point3dList): return list(points)
    if type(points) is list or type(points) is tuple:
        count = len(points)
        if count>10 and type(points[0]) is Rhino.Geometry.Point3d: return points
        if count>0 and (coerce3dpoint(points[0]) is not None):
            return [coerce3dpoint(points[i], raise_on_error) for i in compat.RANGE(count)]
        elif count>2 and type(points[0]) is not list:
            point_count = count/3
            rc = []
            for i in compat.RANGE(point_count):
                pt = Rhino.Geometry.Point3d(points[i*3], points[i*3+1], points[i*3+2])
                rc.append(pt)
            return rc
    if hasattr(points, '__iter__'):
        return [coerce3dpoint(pt, raise_on_error) for pt in points]
    if raise_on_error: raise ValueError("Could not convert %s to a list of points" % points)


def coerce2dpointlist(points):
    if points is None or isinstance(points, System.Array[Rhino.Geometry.Point2d]):
        return points
    if type(points) is list or type(points) is tuple:
        count = len(points)
        if count>0 and type(points[0]) is Rhino.Geometry.Point2d:
            rc = System.Array.CreateInstance(Rhino.Geometry.Point2d, count)
            for i in compat.RANGE(count): rc[i] = points[i]
            return rc
        elif count>1 and type(points[0]) is not list:
            point_count = count/2
            rc = System.Array.CreateInstance(Rhino.Geometry.Point2d,point_count)
            for i in compat.RANGE(point_count):
                rc[i] = Rhino.Geometry.Point2d(points[i*2], points[i*2+1])
            return rc
        elif count>0 and type(points[0]) is list:
            point_count = count
            rc = System.Array.CreateInstance(Rhino.Geometry.Point2d,point_count)
            for i in compat.RANGE(point_count):
                pt = points[i]
                rc[i] = Rhino.Geometry.Point2d(pt[0],pt[1])
            return rc
        return None
    return None


def coerceplane(plane, raise_on_bad_input=False):
    """Convert input into a Rhino.Geometry.Plane if possible.
    Parameters:
      plane = Plane, list, tuple
    Returns:
      a Rhino.Geometry.Plane
    Example:
    See Also:
    """
    if type(plane) is Rhino.Geometry.Plane: return plane
    if type(plane) is list or type(plane) is tuple:
        length = len(plane)
        if length == 1:
            point = coerce3dpoint(plane, False)
            if point: plane = point; length = 3
            elif plane[0] is list or plane[0] is tuple: return coerceplane(plane[0])
        if length==3 and type(plane[0]) is not list:
            rc = Rhino.Geometry.Plane.WorldXY
            rc.Origin = Rhino.Geometry.Point3d(plane[0],plane[1],plane[2])
            return rc
        if length==9 and type(plane[0]) is not list:
            origin = Rhino.Geometry.Point3d(plane[0],plane[1],plane[2])
            xpoint = Rhino.Geometry.Point3d(plane[3],plane[4],plane[5])
            ypoint = Rhino.Geometry.Point3d(plane[6],plane[7],plane[8])
            rc     = Rhino.Geometry.Plane(origin, xpoint, ypoint)
            return rc
        if (length==3 or length==4) and (type(plane[0]) is list or type(plane[0]) is tuple):
            origin = Rhino.Geometry.Point3d(plane[0][0],plane[0][1],plane[0][2])
            xpoint = Rhino.Geometry.Point3d(plane[1][0],plane[1][1],plane[1][2])
            ypoint = Rhino.Geometry.Point3d(plane[2][0],plane[2][1],plane[2][2])
            rc     = Rhino.Geometry.Plane(origin, xpoint, ypoint)
            return rc
    if raise_on_bad_input: raise TypeError("%s can not be converted to a Plane"%plane)


def CreatePlane(plane_or_origin, x_axis=None, y_axis=None, ignored=None):
    """Converts input into a Rhino.Geometry.Plane object if possible.
    If the provided object is already a plane, its value is copied.
    The returned data is accessible by indexing[origin, X axis, Y axis, Z axis], and that is the suggested method to interact with the type.
    The Z axis is in any case computed from the X and Y axes, so providing it is possible but not required.
    If the conversion fails, an error is raised.
    Parameters:
      plane (plane|point|point, vector, vector|[point, vector, vector])
    Returns:
      plane: A Rhino.Geometry.plane.
    Example:
    See Also:
    """
    if type(plane_or_origin) is Rhino.Geometry.Plane: return plane_or_origin.Clone()
    if x_axis != None:
        if y_axis == None: raise Exception("A value for the Y axis is expected if the X axis is specified.")
        origin = coerce3dpoint(plane_or_origin, True)
        x_axis = coerce3dvector(x_axis, True)
        y_axis = coerce3dvector(y_axis, True)
        return Rhino.Geometry.Plane(origin, x_axis, y_axis)
    return coerceplane(plane_or_origin, True)


def coercexform(xform, raise_on_bad_input=False):
    """Convert input into a Rhino.Transform if possible.
    Parameters:
      xform = the xform
      raise_on_bad_input [opt] = True or False
    Example:
    See Also:
    """
    t = type(xform)
    if t is Rhino.Geometry.Transform: return xform
    if( (t is list or t is tuple) and len(xform)==4 and len(xform[0])==4):
        xf = Rhino.Geometry.Transform()
        for i in range(4):
            for j in range(4):
                xf[i,j] = xform[i][j]
        return xf
    if raise_on_bad_input: raise TypeError("%s can not be converted to a Transform"%xform)


def CreateXform(xform):
    """Converts input into a Rhino.Geometry.Transform object if possible.
    If the provided object is already a transform, its value is copied.
    The returned data is accessible by indexing[row, column], and that is the suggested method to interact with the type.
    If the conversion fails, an error is raised.
    Parameters:
      xform (list): the transform. This can be seen as a 4x4 matrix, given as nested lists or tuples.
    Returns:
      transform: A Rhino.Geometry.Transform. result[0,3] gives access to the first row, last column.
    Example:
    See Also:
    """
    if type(xform) is Rhino.Geometry.Transform: return xform.Clone()
    return coercexform(xform, True)


def coerceguid(id, raise_exception=False):
    if type(id) is System.Guid: return id
    if type(id) is str and len(id)>30:
        try:
            id = System.Guid(id)
            return id
        except:
            pass
    if (type(id) is list or type(id) is tuple) and len(id)==1:
        return coerceguid(id[0], raise_exception)
    if type(id) is Rhino.DocObjects.ObjRef: return id.ObjectId
    if isinstance(id,Rhino.DocObjects.RhinoObject): return id.Id
    if raise_exception: raise TypeError("Parameter must be a Guid or string representing a Guid")


def coerceguidlist(ids):
    if ids is None: return None
    rc = []
    if( type(ids) is list or type(ids) is tuple ): pass
    else: ids = [ids]
    for id in ids:
        id = coerceguid(id)
        if id: rc.append(id)
    if rc: return rc


def coerceboundingbox(bbox, raise_on_bad_input=False):
    if type(bbox) is Rhino.Geometry.BoundingBox: return bbox
    points = coerce3dpointlist(bbox)
    if points: return Rhino.Geometry.BoundingBox(points)
    if raise_on_bad_input: raise TypeError("%s can not be converted to a BoundingBox"%bbox)


def coercecolor(c, raise_if_bad_input=False):
    if type(c) is System.Drawing.Color: return c
    if type(c) is list or type(c) is tuple:
        if len(c)==3: return System.Drawing.Color.FromArgb(c[0], c[1], c[2])
        elif len(c)==4: return System.Drawing.Color.FromArgb(c[3], c[0], c[1], c[2])
    if type(c)==type(1): return System.Drawing.Color.FromArgb(c)
    if raise_if_bad_input: raise TypeError("%s can not be converted to a Color"%c)


def CreateColor(color, g=None, b=None, a=None):
    """Converts 'color' into a native color object if possible.
    The returned data is accessible by indexing, and that is the suggested method to interact with the type.
    Red index is [0], Green index is [1], Blue index is [2] and Alpha index is [3].
    If the provided object is already a color, its value is copied.
    Alternatively, you can also pass three coordinates singularly for an RGB color, or four
    for an RGBA color point.
    Parameters:
      color ([number, number, number]): list or 3 or 4 items. Also, a single int can be passed and it will be bitwise-parsed.
    Returns:
      color: An object that can be indexed for red, green, blu, alpha. Item[0] is red.
    Example:
    See Also:
    """
    if g is not None and b is not None: return System.Drawing.Color.FromArgb(int(a or 255), int(color), int(g), int(b))
    if type(color) is System.Drawing.Color: return System.Drawing.Color.FromArgb(color.A, color.R, color.G, color.B)
    return coercecolor(color, True)


def coerceline(line, raise_if_bad_input=False):
    if type(line) is Rhino.Geometry.Line: return line
    guid = coerceguid(line, False)
    if guid: line = scriptcontext.doc.Objects.Find(guid).Geometry
    if isinstance(line, Rhino.Geometry.Curve) and line.IsLinear:
        return Rhino.Geometry.Line(line.PointAtStart, line.PointAtEnd)
    points = coerce3dpointlist(line, raise_if_bad_input)
    if points and len(points)>1: return Rhino.Geometry.Line(points[0], points[1])
    if raise_if_bad_input: raise TypeError("%s can not be converted to a Line"%line)


def coercegeometry(id, raise_if_missing=False):
    """attempt to get GeometryBase class from given input
    Parameters:
      id = geometry identifier
      raise_if_missing [opt] = True or False
    Example:
    See Also:
    """
    if isinstance(id, Rhino.Geometry.GeometryBase): return id
    if type(id) is Rhino.DocObjects.ObjRef: return id.Geometry()
    if isinstance(id, Rhino.DocObjects.RhinoObject): return id.Geometry
    id = coerceguid(id, raise_if_missing)
    if id:
        rhobj = scriptcontext.doc.Objects.Find(id)
        if rhobj: return rhobj.Geometry
    if raise_if_missing: raise ValueError("unable to convert %s into geometry"%id)


def coercebrep(id, raise_if_missing=False):
    """attempt to get polysurface geometry from the document with a given id
    Parameters:
      id = id to be coerced into a brep
      raise_if_missing [opt] = True or False
    Returns:
      a Rhino.Geometry.Brep
    Example:
    See Also:
    """
    geom = coercegeometry(id, False)
    if isinstance(geom, Rhino.Geometry.Brep): return geom
    if isinstance(geom, Rhino.Geometry.Extrusion): return geom.ToBrep(True)
    if raise_if_missing: raise ValueError("unable to convert %s into Brep geometry"%id)


def coercecurve(id, segment_index=-1, raise_if_missing=False):
    """attempt to get curve geometry from the document with a given id
    Parameters:
      id = id to be coerced into a curve
      segment_index [opt] = index of segment to retrieve
      raise_if_missing [opt] = True or False
    Example:
    See Also:
    """
    if isinstance(id, Rhino.Geometry.Curve): return id
    if type(id) is Rhino.DocObjects.ObjRef: return id.Curve()
    id = coerceguid(id, True)
    crvObj = scriptcontext.doc.Objects.Find(id)
    if crvObj:
        curve = crvObj.Geometry
        if curve and segment_index>=0 and type(curve) is Rhino.Geometry.PolyCurve:
            curve = curve.SegmentCurve(segment_index)
        if isinstance(curve, Rhino.Geometry.Curve): return curve
    if raise_if_missing: raise ValueError("unable to convert %s into Curve geometry"%id)


def coercesurface(object_id, raise_if_missing=False):
    """attempt to get surface geometry from the document with a given id
    Parameters:
      object_id = the object's identifier
      raise_if_missing [opt] = True or False
    Returns:
      a Rhino.Geometry.Surface
    Example:
    See Also:
    """
    if isinstance(object_id, Rhino.Geometry.Surface): return object_id
    if isinstance(object_id, Rhino.Geometry.Brep) and object_id.Faces.Count==1: return object_id.Faces[0]
    if type(object_id) is Rhino.DocObjects.ObjRef: return object_id.Face()
    object_id = coerceguid(object_id, True)
    srfObj = scriptcontext.doc.Objects.Find(object_id)
    if srfObj:
        srf = srfObj.Geometry
        if isinstance(srf, Rhino.Geometry.Surface): return srf
        #single face breps are considered surfaces in the context of scripts
        if isinstance(srf, Rhino.Geometry.Brep) and srf.Faces.Count==1:
            return srf.Faces[0]
    if raise_if_missing: raise ValueError("unable to convert %s into Surface geometry"%object_id)


def coercemesh(object_id, raise_if_missing=False):
    """attempt to get mesh geometry from the document with a given id
    Parameters:
      object_id = object identifier
      raise_if_missing [opt] = True or False
    Returns:
      a Rhino.Geometry.Mesh
    Example:
    See Also:
    """
    if type(object_id) is Rhino.DocObjects.ObjRef: return object_id.Mesh()
    if isinstance(object_id, Rhino.Geometry.Mesh): return object_id
    object_id = coerceguid(object_id, raise_if_missing)
    if object_id: 
        meshObj = scriptcontext.doc.Objects.Find(object_id)
        if meshObj:
            mesh = meshObj.Geometry
            if isinstance(mesh, Rhino.Geometry.Mesh): return mesh
    if raise_if_missing: raise ValueError("unable to convert %s into Mesh geometry"%object_id)


def coercerhinoobject(object_id, raise_if_bad_input=False, raise_if_missing=False):
    """attempt to get RhinoObject from the document with a given id
    Parameters:
        object_id = object's identifier
        raise_if_bad_input [opt] = True or False
        raise_if_missing [opt] = True or False
    Returns:
      a RhinoObject
    Example:
    See Also:
    """
    if isinstance(object_id, Rhino.DocObjects.RhinoObject): return object_id
    object_id = coerceguid(object_id, raise_if_bad_input)
    if object_id is None: return None
    rc = scriptcontext.doc.Objects.Find(object_id)
    if not rc and raise_if_missing: raise ValueError("%s does not exist in ObjectTable" % object_id)
    return rc

def CreateInterval(interval, y=None):
    """Converts 'interval' into a Rhino.Geometry.Interval.
    If the provided object is already an interval, its value is copied.
    In case the conversion fails, an error is raised.
    In case a single number is provided, it will be translated to an increasing interval that includes
    the provided input and 0. If two values are provided, they will be used instead.
    Parameters:
      interval ([number, number]): or any item that can be accessed at index 0 and 1; an Interval
    Returns:
      interval: a Rhino.Geometry.Interval. This can be seen as an object made of two items:
        [0] start of interval
        [1] end of interval
    Example:
    See Also:
    """
    if y is not None: return Rhino.Geometry.Interval(float(interval), float(y))
    if isinstance(interval, numbers.Number):
        return Rhino.Geometry.Interval(interval if interval < 0 else 0, interval if interval > 0 else 0)
    try:
        return Rhino.Geometry.Interval(interval[0], interval[1])
    except:
        raise ValueError("unable to convert %s into an Interval: it cannot be indexed."%interval)
