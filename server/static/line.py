import Rhino

import scriptcontext

import rhinocompat as compat
from rhinoscript import utility as rhutil


def LineClosestPoint(line, testpoint):
    """Finds the point on an infinite line that is closest to a test point
    Parameters:
      line ([point, point]): List of 6 numbers or 2 Point3d.  Two 3-D points identifying the starting and ending points of the line.
      testpoint (point): List of 3 numbers or Point3d.  The test point.
    Returns:
      point: the point on the line that is closest to the test point if successful, otherwise None
    Example:
      import rhinoscriptsyntax as rs
      line = (0,0,0), (5,5,0)
      point = (15, 10, 0)
      result = rs.LineClosestPoint( line, point)
      if result: rs.AddPoint(result)
    See Also:
      LineIsFartherThan
      LineMaxDistanceTo
      LineMinDistanceTo
      LinePlane
      LineTransform
    """
    line = rhutil.coerceline(line, True)
    testpoint = rhutil.coerce3dpoint(testpoint, True)
    return line.ClosestPoint(testpoint, False)


def LineCylinderIntersection(line, cylinder_plane, cylinder_height, cylinder_radius):
    """Calculates the intersection of a line and a cylinder
    Parameters:
      line (guid|line): the line to intersect
      cylinder_plane (plane): base plane of the cylinder
      cylinder_height (number): height of the cylinder
      cylinder_radius (number): radius of the cylinder
    Returns:
      list(point, ...): list of intersection points (0, 1, or 2 points)
    Example:
      import rhinoscriptsyntax as rs
      plane = rs.WorldXYPlane()
      line = (-10,0,0), (10,0,10)
      points = rs.LineCylinderIntersection(line, plane, cylinder_height=10, cylinder_radius=5)
      if points:
          for point in points: rs.AddPoint(point)
    See Also:
      LineLineIntersection
      LinePlaneIntersection
      LineSphereIntersection
    """
    line = rhutil.coerceline(line, True)
    cylinder_plane = rhutil.coerceplane(cylinder_plane, True)
    circle = Rhino.Geometry.Circle( cylinder_plane, cylinder_radius )
    if not circle.IsValid: raise ValueError("unable to create valid circle with given plane and radius")
    cyl = Rhino.Geometry.Cylinder( circle, cylinder_height )
    if not cyl.IsValid: raise ValueError("unable to create valid cylinder with given circle and height")
    rc, pt1, pt2 = Rhino.Geometry.Intersect.Intersection.LineCylinder(line, cyl)
    if rc==compat.ENUM_NONE(Rhino.Geometry.Intersect.LineCylinderIntersection):
        return []
    if rc==Rhino.Geometry.Intersect.LineCylinderIntersection.Single:
        return [pt1]
    return [pt1, pt2]


def LineIsFartherThan(line, distance, point_or_line):
    """Determines if the shortest distance from a line to a point or another
    line is greater than a specified distance
    Parameters:
      line (line | [point, point]): List of 6 numbers, 2 Point3d, or Line.
      distance (number): the distance
      point_or_line (point|line) the test point or the test line
    Returns:
      bool: True if the shortest distance from the line to the other project is
            greater than distance, False otherwise
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      line = (0,0,0), (10,10,0)
      testPoint = (10,5,0)
      print(rs.LineIsFartherThan(line, 3, testPoint))
    See Also:
      LineClosestPoint
      LineMaxDistanceTo
      LineMinDistanceTo
      LinePlane
      LineTransform
    """
    line = rhutil.coerceline(line, True)
    test = rhutil.coerceline(point_or_line)
    if not test: test = rhutil.coerce3dpoint(point_or_line, True)
    minDist = line.MinimumDistanceTo(test)
    return minDist>distance


def LineLineIntersection(lineA, lineB):
    """Calculates the intersection of two non-parallel lines. Note, the two
    lines do not have to intersect for an intersection to be found. (see help)
    Parameters:
      lineA, lineB (line): lines to intersect
    Returns:
      tuple(point, point): containing a point on the first line and a point on the second line if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      lineA = (1,1,0), (5,0,0)
      lineB = (1,3,0), (5,5,0)
      point = rs.LineLineIntersection(lineA, lineB)
      if point:
          rs.AddPoint(point[0])
          rs.AddPoint(point[1])
    See Also:
      IntersectPlanes
      LinePlaneIntersection
      PlanePlaneIntersection
    """
    lineA = rhutil.coerceline(lineA, True)
    lineB = rhutil.coerceline(lineB, True)
    rc, a, b = Rhino.Geometry.Intersect.Intersection.LineLine(lineA, lineB)
    if not rc: return None
    return lineA.PointAt(a), lineB.PointAt(b)


def LineMaxDistanceTo(line, point_or_line):
    """Finds the longest distance between a line as a finite chord, and a point
    or another line
    Parameters:
      line (line | [point, point]): List of 6 numbers, two Point3d, or Line.
      point_or_line (point|line): the test point or test line.
    Returns:
      number: A distance (D) such that if Q is any point on the line and P is any point on the other object, then D >= Rhino.Distance(Q, P).
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      line = (0,0,0), (10,10,0)
      print(rs.LineMaxDistanceTo( line, (10,5,0) ))
    See Also:
      LineClosestPoint
      LineIsFartherThan
      LineMinDistanceTo
      LinePlane
      LineTransform
    """
    line = rhutil.coerceline(line, True)
    test = rhutil.coerceline(point_or_line)
    if test is None: test = rhutil.coerce3dpoint(point_or_line, True)
    return line.MaximumDistanceTo(test)


def LineMinDistanceTo(line, point_or_line):
    """Finds the shortest distance between a line as a finite chord, and a point
    or another line
    Parameters:
      line (line | [point, point]): List of 6 numbers, two Point3d, or Line.
      point_or_line (point|line): the test point or test line.
    Returns:
      number: A distance (D) such that if Q is any point on the line and P is any point on the other object, then D <= Rhino.Distance(Q, P).
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      line = (0,0,0), (10,10,0)
      print(rs.LineMinDistanceTo(line, (10,5,0)))
    See Also:
      LineClosestPoint
      LineIsFartherThan
      LineMaxDistanceTo
      LinePlane
      LineTransform
    """
    line = rhutil.coerceline(line, True)
    test = rhutil.coerceline(point_or_line)
    if test is None: test = rhutil.coerce3dpoint(point_or_line, True)
    return line.MinimumDistanceTo(test)


def LinePlane(line):
    """Returns a plane that contains the line. The origin of the plane is at the start of
    the line. If possible, a plane parallel to the world XY, YZ, or ZX plane is returned
    Parameters:
      line (line | [point, point]):  List of 6 numbers, two Point3d, or Line.
    Returns:
      plane: the plane if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      lineFrom = (0,0,0)
      lineTo = (10,10,0)
      distance = rs.Distance(lineFrom, lineTo)
      plane = rs.LinePlane([lineFrom, lineTo])
      rs.AddPlaneSurface( plane, distance, distance )
    See Also:
      LineClosestPoint
      LineIsFartherThan
      LineMaxDistanceTo
      LineMinDistanceTo
      LineTransform
    """
    line = rhutil.coerceline(line, True)
    rc, plane = line.TryGetPlane()
    if not rc: return scriptcontext.errorhandler()
    return plane


def LinePlaneIntersection(line, plane):
    """Calculates the intersection of a line and a plane.
    Parameters:
      line ([point, point]): Two 3D points identifying the starting and ending points of the line to intersect.
      plane (plane): The plane to intersect.
    Returns:
      point: The 3D point of intersection is successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      plane = rs.WorldXYPlane()
      line = (2, 11, 13), (20, 4, -10)
      point = rs.LinePlaneIntersection(line, plane)
      if( point!=None ): rs.AddPoint(point)
    See Also:
      LineLineIntersection
      PlanePlaneIntersection
    """
    plane = rhutil.coerceplane(plane, True)
    line_points = rhutil.coerce3dpointlist(line, True)
    line = Rhino.Geometry.Line(line_points[0], line_points[1])
    rc, t = Rhino.Geometry.Intersect.Intersection.LinePlane(line, plane) 
    if  not rc: return scriptcontext.errorhandler()
    return line.PointAt(t)


def LineSphereIntersection(line, sphere_center, sphere_radius):
    """Calculates the intersection of a line and a sphere
    Parameters:
      line (line | [point, point]): the line
      sphere_center (point): the center point of the sphere
      sphere_radius (number): the radius of the sphere
    Returns:
      list(point, ...): list of intersection points if successful, otherwise None
    Example:
      import rhinoscriptsyntax as rs
      radius = 10
      line = (-10,0,0), (10,0,10)
      points = rs.LineSphereIntersection(line, (0,0,0), radius)
      if points:
          for point in points: rs.AddPoint(point)
    See Also:
      LineCylinderIntersection
      LineLineIntersection
      LinePlaneIntersection
    """
    line = rhutil.coerceline(line, True)
    sphere_center = rhutil.coerce3dpoint(sphere_center, True)
    sphere = Rhino.Geometry.Sphere(sphere_center, sphere_radius)
    rc, pt1, pt2 = Rhino.Geometry.Intersect.Intersection.LineSphere(line, sphere)
    if rc==compat.ENUM_NONE(Rhino.Geometry.Intersect.LineSphereIntersection): return []
    if rc==Rhino.Geometry.Intersect.LineSphereIntersection.Single: return [pt1]
    return [pt1, pt2]


def LineTransform(line, xform):
    """Transforms a line
    Parameters:
      line (guid): the line to transform
      xform (transform): the transformation to apply
    Returns:
      guid: transformed line
    Example:
      import rhinoscriptsyntax as rs
      line = (0,0,0), (10,10,0)
      rs.AddLine( line[0], line[1] )
      plane = rs.WorldXYPlane()
      xform = rs.XformRotation(30, plane.Zaxis, plane.Origin)
      line = rs.LineTransform(line, xform)
      rs.AddLine( line.From, line.To )
    See Also:
      LineClosestPoint
      LineIsFartherThan
      LineMaxDistanceTo
      LineMinDistanceTo
      LinePlane
    """
    line = rhutil.coerceline(line, True)
    xform = rhutil.coercexform(xform, True)
    success = line.Transform(xform)
    if not success: raise Exception("unable to transform line")
    return line
