import math

import Rhino

import scriptcontext

from rhinoscript import utility as rhutil
from rhinoscript.view import __viewhelper


def IsXformIdentity(xform):
    """Verifies a matrix is the identity matrix
    Parameters:
      xform (transform): List or Rhino.Geometry.Transform.  A 4x4 transformation matrix.
    Returns:
      bool: True or False indicating success or failure.
    Example:
      import rhinoscriptsyntax as rs
      xform = rs.XformIdentity()
      print(rs.IsXformIdentity(xform))
    See Also:
      IsXformSimilarity
      IsXformZero
      XformIdentity
    """
    xform = rhutil.coercexform(xform, True)
    return xform==Rhino.Geometry.Transform.Identity


def IsXformSimilarity(xform):
    """Verifies a matrix is a similarity transformation. A similarity
    transformation can be broken into a sequence of dilations, translations,
    rotations, and reflections
    Parameters:
      xform (transform): List or Rhino.Geometry.Transform.  A 4x4 transformation matrix.
    Returns:
      bool: True if this transformation is an orientation preserving similarity, otherwise False.
    Example:
      import rhinoscriptsyntax as rs
      xform = rs.BlockInstanceXform(block)
      print(rs.IsXformSimilarity(xform))
    See Also:
      IsXformIdentity
      IsXformZero
    """
    xform = rhutil.coercexform(xform, True)
    return xform.SimilarityType!=Rhino.Geometry.TransformSimilarityType.NotSimilarity


def IsXformZero(xform):
    """verifies that a matrix is a zero transformation matrix
    Parameters:
      xform (transform): List or Rhino.Geometry.Transform.  A 4x4 transformation matrix.
    Returns:
      bool: True or False indicating success or failure.
    Example:
      import rhinoscriptsyntax as rs
      xform = rs.XformZero()
      print(rs.IsXformZero(xform))
    See Also:
      IsXformIdentity
      IsXformSimilarity
      XformZero
    """
    xform = rhutil.coercexform(xform, True)
    for i in range(4):
        for j in range(4):
            if xform[i,j]!=0: return False
    return True


def XformChangeBasis(initial_plane, final_plane):
    """Returns a change of basis transformation matrix or None on error
    Parameters:
      initial_plane (plane): the initial plane
      final_plane (plane): the final plane
    Returns:
      transform: The 4x4 transformation matrix if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      import math
      objs = rs.GetObjects("Select objects to shear")
      if objs:
          cplane = rs.ViewCPlane()
          cob = rs.XformChangeBasis(rs.WorldXYPlane(), cplane)
          shear2d = rs.XformIdentity()
          shear2d[0,2] = math.tan(math.radians(45.0))
          cob_inverse = rs.XformChangeBasis(cplane, rs.WorldXYPlane())
          temp = rs.XformMultiply(shear2d, cob)
          xform = rs.XformMultiply(cob_inverse, temp)
          rs.TransformObjects( objs, xform, True )
    See Also:
      XformCPlaneToWorld
      XformWorldToCPlane
    """
    initial_plane = rhutil.coerceplane(initial_plane, True)
    final_plane = rhutil.coerceplane(final_plane, True)
    xform = Rhino.Geometry.Transform.ChangeBasis(initial_plane, final_plane)
    if not xform.IsValid: return scriptcontext.errorhandler()
    return xform


def XformChangeBasis2(x0,y0,z0,x1,y1,z1):
    """Returns a change of basis transformation matrix of None on error
    Parameters:
      x0,y0,z0 (vector): initial basis
      x1,y1,z1 (vector): final basis
    Returns:
      transform: The 4x4 transformation matrix if successful
      None: if not successful
    Example:
    See Also:
    """
    x0 = rhutil.coerce3dvector(x0, True)
    y0 = rhutil.coerce3dvector(y0, True)
    z0 = rhutil.coerce3dvector(z0, True)
    x1 = rhutil.coerce3dvector(x1, True)
    y1 = rhutil.coerce3dvector(y1, True)
    z1 = rhutil.coerce3dvector(z1, True)
    xform = Rhino.Geometry.Transform.ChangeBasis(x0,y0,z0,x1,y1,z1)
    if not xform.IsValid: return scriptcontext.errorhandler()
    return xform


def XformCompare(xform1, xform2):
    """Compares two transformation matrices
    Parameters:
      xform1, xform2 = matrices to compare
    Returns:
        number:
        -1 if xform1<xform2
         1 if xform1>xform2
         0 if xform1=xform2
    Example:
      import rhinoscriptsyntax as rs
      xform0 = rs.XformZero()
      xform1 = rs.XformIdentity()
      print(rs.XformCompare(xform0, xform1))
    See Also:
      IsXformIdentity
      IsXformSimilarity
      IsXformZero
    """
    xform1 = rhutil.coercexform(xform1, True)
    xform2 = rhutil.coercexform(xform2, True)
    return xform1.CompareTo(xform2)


def XformCPlaneToWorld(point, plane):
    """Transform point from construction plane coordinates to world coordinates
    Parameters:
      point (point): A 3D point in construction plane coordinates.
      plane (plane): The construction plane
    Returns:
      point: A 3D point in world coordinates
    Example:
      import rhinoscriptsyntax as rs
      plane = rs.ViewCPlane()
      point = rs.XFormCPlaneToWorld([0,0,0], plane)
      if point: print("World point: {}".format(point))
    See Also:
      XformWorldToCPlane
    """
    point = rhutil.coerce3dpoint(point, True)
    plane = rhutil.coerceplane(plane, True)
    return plane.Origin + point.X*plane.XAxis + point.Y*plane.YAxis + point.Z*plane.ZAxis


def XformDeterminant(xform):
    """Returns the determinant of a transformation matrix. If the determinant
    of a transformation matrix is 0, the matrix is said to be singular. Singular
    matrices do not have inverses.
    Parameters:
      xform (transform): List or Rhino.Geometry.Transform.  A 4x4 transformation matrix.
    Returns:
      number: The determinant if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      xform = rs.BlockInstanceXform(obj)
      if xform: print(rs.XformDeterminant(xform))
    See Also:
      XformInverse
    """
    xform = rhutil.coercexform(xform, True)
    return xform.Determinant


def XformDiagonal(diagonal_value):
    """Returns a diagonal transformation matrix. Diagonal matrices are 3x3 with
    the bottom row [0,0,0,1]
    Parameters:
      diagonal_value (number): the diagonal value
    Returns:
      transform: The 4x4 transformation matrix if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      def printmatrix(xform):
          for i in range(4):
              print("[{}, {}, {}, {}]".format(xform[i,0], xform[i,1], xform[i,2], xform[i,3]))
      printmatrix(rs.XformDiagonal(3))
    See Also:
      XformIdentity
      XformZero
    """
    return Rhino.Geometry.Transform(diagonal_value)


def XformIdentity():
    """returns the identity transformation matrix
    Returns:
      transform: The 4x4 transformation matrix
    Example:
      import rhinoscriptsyntax as rs
      def printmatrix(xform):
          for i in range(4):
              print("[{}, {}, {}, {}]".format(xform[i,0], xform[i,1], xform[i,2], xform[i,3]))
      printmatrix(rs.XformIdentity())
    See Also:
      XformDiagonal
      XformZero
    """
    return Rhino.Geometry.Transform.Identity


def XformInverse(xform):
    """Returns the inverse of a non-singular transformation matrix
    Parameters:
      xform (transform): List or Rhino.Geometry.Transform.  A 4x4 transformation matrix.
    Returns:
      transform: The inverted 4x4 transformation matrix if successful.
      None: if matrix is non-singular or on error.
    Example:
      import rhinoscriptsyntax as rs
      xform = rs.BlockInstanceXform(obj)
      if xform:
          rs.TransformObject( obj, rs.XformInverse(xform) )
    See Also:
      XformDeterminant
    """
    xform = rhutil.coercexform(xform, True)
    rc, inverse = xform.TryGetInverse()
    if not rc: return scriptcontext.errorhandler()
    return inverse


def XformMirror(mirror_plane_point, mirror_plane_normal):
    """Creates a mirror transformation matrix
    Parameters:
      mirror_plane_point (point): point on the mirror plane
      mirror_plane_normal (vector): a 3D vector that is normal to the mirror plane
    Returns:
      transform: mirror Transform matrix
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to mirror")
      if objs:
          plane = rs.ViewCPlane()
          xform = rs.XformMirror(plane.Origin, plane.Normal)
          rs.TransformObjects( objs, xform, True )
    See Also:
      XformPlanarProjection
      XformRotation1
      XformRotation2
      XformRotation3
      XformRotation4
      XformScale
      XformShear
      XformTranslation
    """
    point = rhutil.coerce3dpoint(mirror_plane_point, True)
    normal = rhutil.coerce3dvector(mirror_plane_normal, True)
    return Rhino.Geometry.Transform.Mirror(point, normal)


def XformMultiply(xform1, xform2):
    """Multiplies two transformation matrices, where result = xform1 * xform2
    Parameters:
      xform1 (transform): List or Rhino.Geometry.Transform.  The first 4x4 transformation matrix to multiply.
      xform2 (transform): List or Rhino.Geometry.Transform.  The second 4x4 transformation matrix to multiply.
    Returns:
      transform: result transformation on success
    Example:
      import rhinoscriptsyntax as rs
      import math
      objs = rs.GetObjects("Select objects to shear")
      if objs:
          cplane = rs.ViewCPlane()
          cob = rs.XformChangeBasis(rs.WorldXYPlane(), cplane)
          shear2d = rs.XformIdentity()
          shear2d[0,2] = math.tan(math.radians(45.0))
          cob_inv = rs.XformChangeBasis(cplane, rs.WorldXYPlane())
          temp = rs.XformMultiply(shear2d, cob)
          xform = rs.XformMultiply(cob_inv, temp)
          rs.TransformObjects( objs, xform, True )
    See Also:
      XformPlanarProjection
      XformRotation1
      XformRotation2
      XformRotation3
      XformRotation4
      XformScale
      XformShear
      XformTranslation
    """
    xform1 = rhutil.coercexform(xform1, True)
    xform2 = rhutil.coercexform(xform2, True)
    return xform1*xform2


def XformPlanarProjection(plane):
    """Returns a transformation matrix that projects to a plane.
    Parameters:
      plane (plane): The plane to project to.
    Returns:
      transform: The 4x4 transformation matrix.
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.GetObjects("Select objects to project")
      if objects:
          cplane = rs.ViewCPlane()
          xform = rs.XformPlanarProjection(cplane)
          rs.TransformObjects( objects, xform, True )
    See Also:
      XformMirror
      XformRotation1
      XformRotation2
      XformRotation3
      XformRotation4
      XformScale
      XformShear
      XformTranslation
    """
    plane = rhutil.coerceplane(plane, True)
    return Rhino.Geometry.Transform.PlanarProjection(plane)


def XformRotation1(initial_plane, final_plane):
    """Returns a rotation transformation that maps initial_plane to final_plane.
    The planes should be right hand orthonormal planes.
    Parameters:
      initial_plane (plane): plane to rotate from
      final_plane (plane): plane to rotate to
    Returns:
      transform: The 4x4 transformation matrix.
      None: on error.
    Example:
    See Also:
    """
    initial_plane = rhutil.coerceplane(initial_plane, True)
    final_plane = rhutil.coerceplane(final_plane, True)
    xform = Rhino.Geometry.Transform.PlaneToPlane(initial_plane, final_plane)
    if not xform.IsValid: return scriptcontext.errorhandler()
    return xform


def XformRotation2(angle_degrees, rotation_axis, center_point):
    """Returns a rotation transformation around an axis
    Parameters:
      angle_degrees (number): rotation angle in degrees
      rotation_axis (vector): rotation axis
      center_point (point): rotation center
    Returns:
      transform: The 4x4 transformation matrix.
      None: on error.
    Example:
    See Also:
    """
    axis = rhutil.coerce3dvector(rotation_axis, True)
    center = rhutil.coerce3dpoint(center_point, True)
    angle_rad = math.radians(angle_degrees)
    xform = Rhino.Geometry.Transform.Rotation(angle_rad, axis, center)
    if not xform.IsValid: return scriptcontext.errorhandler()
    return xform


def XformRotation3( start_direction, end_direction, center_point ):
    """Calculate the minimal transformation that rotates start_direction to
    end_direction while fixing center_point
    Parameters:
      start_direction, end_direction (vector): 3d vectors
      center_point (point): the rotation center
    Returns:
      transform: The 4x4 transformation matrix.
      None: on error.
    Example:
    See Also:
    """
    start = rhutil.coerce3dvector(start_direction, True)
    end = rhutil.coerce3dvector(end_direction, True)
    center = rhutil.coerce3dpoint(center_point, True)
    xform = Rhino.Geometry.Transform.Rotation(start, end, center)
    if not xform.IsValid: return scriptcontext.errorhandler()
    return xform


def XformRotation4(x0, y0, z0, x1, y1, z1):
    """Returns a rotation transformation.
    Parameters:
      x0,y0,z0 (vector): Vectors defining the initial orthonormal frame
      x1,y1,z1 (vector): Vectors defining the final orthonormal frame
    Returns:
      transform: The 4x4 transformation matrix.
      None: on error.
    Example:
    See Also:
    """
    x0 = rhutil.coerce3dvector(x0, True)
    y0 = rhutil.coerce3dvector(y0, True)
    z0 = rhutil.coerce3dvector(z0, True)
    x1 = rhutil.coerce3dvector(x1, True)
    y1 = rhutil.coerce3dvector(y1, True)
    z1 = rhutil.coerce3dvector(z1, True)
    xform = Rhino.Geometry.Transform.Rotation(x0,y0,z0,x1,y1,z1)
    if not xform.IsValid: return scriptcontext.errorhandler()
    return xform


def XformScale(scale, point=None):
    """Creates a scale transformation
    Parameters:
      scale (number|point|vector|[number, number, number]): single number, list of 3 numbers, Point3d, or Vector3d
      point (point, optional): center of scale. If omitted, world origin is used
    Returns:
      transform: The 4x4 transformation matrix on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to scale")
      if objs:
          xform = rs.XformScale( (3.0,1.0,1.0) )
          rs.TransformObjects( objs, xform, True)
    See Also:
      XformMirror
      XformPlanarProjection
      XformRotation1
      XformRotation2
      XformRotation3
      XformRotation4
      XformShear
      XformTranslation
    """
    factor = rhutil.coerce3dpoint(scale)
    if factor is None:
        if type(scale) is int or type(scale) is float:
            factor = (scale,scale,scale)
        if factor is None: return scriptcontext.errorhandler()
    if point: point = rhutil.coerce3dpoint(point, True)
    else: point = Rhino.Geometry.Point3d.Origin
    plane = Rhino.Geometry.Plane(point, Rhino.Geometry.Vector3d.ZAxis);
    xf = Rhino.Geometry.Transform.Scale(plane, factor[0], factor[1], factor[2])
    return xf


def XformScreenToWorld(point, view=None, screen_coordinates=False):
    """Transforms a point from either client-area coordinates of the specified view
    or screen coordinates to world coordinates. The resulting coordinates are represented
    as a 3-D point
    Parameters:
      point (point): 2D point
      view (str, optional): title or identifier of a view. If omitted, the active view is used
      screen_coordinates (bool, optional): if False, point is in client-area coordinates. If True,
      point is in screen-area coordinates
    Returns:
      point: on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      point2d = 200,100
      view = rs.CurrentView()
      point = rs.XformScreenToWorld(point2d, view)
      print(point)
    See Also:
      XformWorldToScreen
    """
    point = rhutil.coerce2dpoint(point, True)
    view = __viewhelper(view)
    viewport = view.MainViewport
    xform = viewport.GetTransform(Rhino.DocObjects.CoordinateSystem.Screen, Rhino.DocObjects.CoordinateSystem.World)
    point3d = Rhino.Geometry.Point3d(point.X, point.Y, 0)
    if screen_coordinates:
        screen = view.ScreenRectangle
        point3d.X = point.X - screen.Left
        point3d.Y = point.Y - screen.Top
    point3d = xform * point3d
    return point3d


def XformShear(plane, x, y, z):
    """Returns a shear transformation matrix
    Parameters:
      plane (plane): plane[0] is the fixed point
      x,y,z (number): each axis scale factor
    Returns:
      transform: The 4x4 transformation matrix on success
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.GetObjects("Select objects to shear")
      if objects:
          cplane = rs.ViewCPlane()
          xform = rs.XformShear(cplane, (1,1,0), (-1,1,0), (0,0,1))
          rs.TransformObjects(objects, xform, True)
    See Also:
      XformMirror
      XformPlanarProjection
      XformRotation1
      XformRotation2
      XformRotation3
      XformRotation4
      XformScale
      XformTranslation
    """
    plane = rhutil.coerceplane(plane, True)
    x = rhutil.coerce3dvector(x, True)
    y = rhutil.coerce3dvector(y, True)
    z = rhutil.coerce3dvector(z, True)
    return Rhino.Geometry.Transform.Shear(plane,x,y,z)


def XformTranslation(vector):
    """Creates a translation transformation matrix
    Parameters:
      vector (vector): List of 3 numbers, Point3d, or Vector3d.  A 3-D translation vector.
    Returns:
      transform: The 4x4 transformation matrix is successful, otherwise None
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to copy")
      if objs:
          xform = rs.XformTranslation([1,0,0])
          rs.TransformObjects( objs, xform, True )
    See Also:
      XformMirror
      XformPlanarProjection
      XformRotation1
      XformRotation2
      XformRotation3
      XformRotation4
      XformScale
      XformShear
    """
    vector = rhutil.coerce3dvector(vector, True)
    return Rhino.Geometry.Transform.Translation(vector)


def XformWorldToCPlane(point, plane):
    """Transforms a point from world coordinates to construction plane coordinates.
    Parameters:
      point (point): A 3D point in world coordinates.
      plane (plane): The construction plane
    Returns:
      (point): 3D point in construction plane coordinates
    Example:
      import rhinoscriptsyntax as rs
      plane = rs.ViewCPlane()
      point = rs.XformWorldToCPlane([0,0,0], plane)
      if point: print("CPlane point:{}".format(point))
    See Also:
      XformCPlaneToWorld
    """
    point = rhutil.coerce3dpoint(point, True)
    plane = rhutil.coerceplane(plane, True)
    v = point - plane.Origin;
    return Rhino.Geometry.Point3d(v*plane.XAxis, v*plane.YAxis, v*plane.ZAxis)


def XformWorldToScreen(point, view=None, screen_coordinates=False):
    """Transforms a point from world coordinates to either client-area coordinates of
    the specified view or screen coordinates. The resulting coordinates are represented
    as a 2D point
    Parameters:
      point (point): 3D point in world coordinates
      view (str, optional): title or identifier of a view. If omitted, the active view is used
      screen_coordinates (bool, optional): if False, the function returns the results as
        client-area coordinates. If True, the result is in screen-area coordinates
    Returns:
      (point): 2D point on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      point = (0.0, 0.0, 0.0)
      view = rs.CurrentView()
      point2d = rs.XformWorldToScreen(point, view)
      print(point2d)
    See Also:
      XformScreenToWorld
    """
    point = rhutil.coerce3dpoint(point, True)
    view = __viewhelper(view)
    viewport = view.MainViewport
    xform = viewport.GetTransform(Rhino.DocObjects.CoordinateSystem.World, Rhino.DocObjects.CoordinateSystem.Screen)
    point = xform * point
    point = Rhino.Geometry.Point2d(point.X, point.Y)
    if screen_coordinates:
        screen = view.ScreenRectangle
        point.X = point.X + screen.Left
        point.Y = point.Y + screen.Top
    return point


def XformZero():
    """Returns a zero transformation matrix
    Returns:
      transform: a zero transformation matrix
    Example:
      import rhinoscriptsyntax as rs
      def printmatrix(xform):
          for i in range(4):
              print("[{}, {}, {}, {}]".format(xform[i,0], xform[i,1], xform[i,2], xform[i,3]))
      printmatrix( rs.XformZero() )
    See Also:
      XformDiagonal
      XformIdentity
    """
    return Rhino.Geometry.Transform()
