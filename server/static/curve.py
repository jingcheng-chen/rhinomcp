import math

import System

import Rhino

import scriptcontext

import rhinocompat as compat
from rhinoscript import utility as rhutil


def AddArc(plane, radius, angle_degrees):
    """Adds an arc curve to the document
    Parameters:
      plane (str): plane on which the arc will lie. The origin of the plane will be
        the center point of the arc. x-axis of the plane defines the 0 angle
        direction.
      radius(number): radius of the arc
      angle_degrees (number): interval of arc in degrees
    Returns:
      guid: id of the new curve object
    Example:
      import rhinoscriptsyntax as  rs
      plane = rs.WorldXYPlane()
      plane = rs.RotatePlane(plane,  45.0, [0,0,1])
      rs.AddArc( plane, 5.0, 45.0  )
    See Also:
      AddArc3Pt
      ArcAngle
      ArcCenterPoint
      ArcMidPoint
      ArcRadius
      IsArc
    """
    plane = rhutil.coerceplane(plane, True)
    radians = math.radians(angle_degrees)
    arc = Rhino.Geometry.Arc(plane, radius, radians)
    rc = scriptcontext.doc.Objects.AddArc(arc)
    if rc==System.Guid.Empty: raise Exception("Unable to add arc to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddArc3Pt(start, end, point_on_arc):
    """Adds a 3-point arc curve to the document
    Parameters:
      start, end (point|guid): endpoints of the arc
      point_on_arc (point|guid): a point on the arc
    Returns:
      guid: id of the new curve object
    Example:
      import rhinoscriptsyntax as rs
      start = rs.GetPoint("Start of arc")
      if start is not None:
          end = rs.GetPoint("End of arc")
          if end is not None:
              pton = rs.GetPoint("Point on arc")
              if pton is not None:
                  rs.AddArc3Pt(start, end, pton)
    See Also:
      AddArc
      ArcAngle
      ArcCenterPoint
      ArcMidPoint
      ArcRadius
      IsArc
    """
    start = rhutil.coerce3dpoint(start, True)
    end = rhutil.coerce3dpoint(end, True)
    pton = rhutil.coerce3dpoint(point_on_arc, True)
    arc = Rhino.Geometry.Arc(start, pton, end)
    rc = scriptcontext.doc.Objects.AddArc(arc)
    if rc==System.Guid.Empty: raise Exception("Unable to add arc to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddArcPtTanPt(start, direction, end):
    """Adds an arc curve, created from a start point, a start direction, and an
    end point, to the document
    Parameters:
      start (point): the starting point of the arc
      direction (vector): the arc direction at start
      end (point): the ending point of the arc
    Returns:
      guid: id of the new curve object
    Example:
      import rhinoscriptsyntax as rs
      pick = rs.GetCurveObject("Select curve to extend")
      point = rs.GetPoint("End of extension")
      domain = rs.CurveDomain(pick[0])
      if abs(pick[4]-domain[0]) < abs(pick[4]-domain[1]):
          origin = rs.CurveStartPoint(pick[0])
          tangent = rs.VectorReverse(rs.CurveTangent(pick[0], domain[0]))
      else:
          origin = rs.CurveEndPoint(pick[0])
          tangent = rs.CurveTangent(pick[0], domain[1])
      rs.AddArcPtTanPt(origin, tangent, point)
    See Also:
      AddArc
      AddArc3Pt
      IsArc
    """
    start = rhutil.coerce3dpoint(start, True)
    direction = rhutil.coerce3dvector(direction, True)
    end = rhutil.coerce3dpoint(end, True)
    arc = Rhino.Geometry.Arc(start, direction, end)
    rc = scriptcontext.doc.Objects.AddArc(arc)
    if rc==System.Guid.Empty: raise Exception("Unable to add arc to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddBlendCurve(curves, parameters, reverses, continuities):
    """Makes a curve blend between two curves
    Parameters:
      curves ([guid|curve, guid|curve]): list of two curves
      parameters ([number, number]): list of two curve parameters defining the blend end points
      reverses ([bool, bool]): list of two boolean values specifying to use the natural or opposite direction of the curve
      continuities ([number, number]): list of two numbers specifying continuity at end points
                                            0 = position
                                            1 = tangency
                                            2 = curvature
    Returns:
      guid: identifier of new curve on success
    Example:
        import rhinoscriptsyntax as rs
        curve0 = rs.AddLine((0,0,0), (0,9,0))
        curve1 = rs.AddLine((1,10,0), (10,10,0))
        curves = curve0, curve1
        domain_crv0 = rs.CurveDomain(curve0)
        domain_crv1 = rs.CurveDomain(curve1)
        params = domain_crv0[1], domain_crv1[0]
        revs = False, True
        cont = 2,2
        rs.AddBlendCurve( curves, params, revs, cont )
    See Also:
      AddFilletCurve
    """
    crv0 = rhutil.coercecurve(curves[0], -1, True)
    crv1 = rhutil.coercecurve(curves[1], -1, True)
    c0 = System.Enum.ToObject(Rhino.Geometry.BlendContinuity, continuities[0])
    c1 = System.Enum.ToObject(Rhino.Geometry.BlendContinuity, continuities[1])
    curve = Rhino.Geometry.Curve.CreateBlendCurve(crv0, parameters[0], reverses[0], c0, crv1, parameters[1], reverses[1], c1)
    rc = scriptcontext.doc.Objects.AddCurve(curve)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddCircle(plane_or_center, radius):
    """Adds a circle curve to the document
    Parameters:
      plane_or_center (point|plane): plane on which the circle will lie. If a point is
        passed, this will be the center of the circle on the active
        construction plane
      radius (number): the radius of the circle
    Returns:
      guid: id of the new curve object
    Example:
      import rhinoscriptsyntax as rs
      plane = rs.WorldXYPlane()
      rs.AddCircle( plane, 5.0 )
    See Also:
      AddCircle3Pt
      CircleCenterPoint
      CircleCircumference
      CircleRadius
      IsCircle
    """
    rc = None
    plane = rhutil.coerceplane(plane_or_center, False)
    if plane:
        circle = Rhino.Geometry.Circle(plane, radius)
        rc = scriptcontext.doc.Objects.AddCircle(circle)
    else:
        center = rhutil.coerce3dpoint(plane_or_center, True)
        view = scriptcontext.doc.Views.ActiveView
        plane = view.ActiveViewport.ConstructionPlane()
        plane.Origin = center
        circle = Rhino.Geometry.Circle(plane, radius)
        rc = scriptcontext.doc.Objects.AddCircle(circle)
    if rc==System.Guid.Empty: raise Exception("Unable to add circle to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddCircle3Pt(first, second, third):
    """Adds a 3-point circle curve to the document
    Parameters:
      first, second, third (point|guid): points on the circle
    Returns:
      guid: id of the new curve object
    Example:
      import rhinoscriptsyntax as rs
      point1 = rs.GetPoint("First point on circle")
      if point1:
          point2 = rs.GetPoint("Second point on circle")
          if point2:
              point3 = rs.GetPoint("Third point on circle")
              if point3:
                  rs.AddCircle3Pt(point1, point2, point3)
    See Also:
      AddCircle
      CircleCenterPoint
      CircleCircumference
      CircleRadius
      IsCircle
    """
    start = rhutil.coerce3dpoint(first, True)
    end = rhutil.coerce3dpoint(second, True)
    third = rhutil.coerce3dpoint(third, True)
    circle = Rhino.Geometry.Circle(start, end, third)
    rc = scriptcontext.doc.Objects.AddCircle(circle)
    if rc==System.Guid.Empty: raise Exception("Unable to add circle to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddCurve(points, degree=3):
    """Adds a control points curve object to the document
    Parameters:
      points ([point|guid, ...]) a list of points
      degree (number): degree of the curve
    Returns:
      guid: id of the new curve object
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints(True, message1="Pick curve point")
      if points: rs.AddCurve(points)
    See Also:
      AddInterpCurve
      IsCurve
    """
    points = rhutil.coerce3dpointlist(points, True)
    curve = Rhino.Geometry.Curve.CreateControlPointCurve(points, degree)
    if not curve: raise Exception("unable to create control point curve from given points")
    rc = scriptcontext.doc.Objects.AddCurve(curve)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddEllipse(plane, radiusX, radiusY):
    """Adds an elliptical curve to the document
    Parameters:
      plane (plane) the plane on which the ellipse will lie. The origin of
              the plane will be the center of the ellipse
      radiusX, radiusY (number): radius in the X and Y axis directions
    Returns:
      guid: id of the new curve object if successful
    Example:
      import rhinoscriptsyntax as rs
      plane = rs.WorldXYPlane()
      rs.AddEllipse( plane, 5.0, 10.0 )
    See Also:
      AddEllipse3Pt
      IsEllipse
      EllipseCenterPoint
      EllipseQuadPoints
    """
    plane = rhutil.coerceplane(plane, True)
    ellipse = Rhino.Geometry.Ellipse(plane, radiusX, radiusY)
    rc = scriptcontext.doc.Objects.AddEllipse(ellipse)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddEllipse3Pt(center, second, third):
    """Adds a 3-point elliptical curve to the document
    Parameters:
      center (point|guid): center point of the ellipse
      second (point|guid): end point of the x axis
      third  (point|guid): end point of the y axis
    Returns:
      guid: id of the new curve object if successful
    Example:
      import rhinoscriptsyntax as rs
      center = (0,0,0)
      second = (5,0,0)
      third = (0,10,0)
      rs.AddEllipse3Pt( center, second, third )
    See Also:
      AddEllipse
      IsEllipse
      EllipseCenterPoint
      EllipseQuadPoints
    """
    center = rhutil.coerce3dpoint(center, True)
    second = rhutil.coerce3dpoint(second, True)
    third = rhutil.coerce3dpoint(third, True)
    ellipse = Rhino.Geometry.Ellipse(center, second, third)
    rc = scriptcontext.doc.Objects.AddEllipse(ellipse)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddFilletCurve(curve0id, curve1id, radius=1.0, base_point0=None, base_point1=None):
    """Adds a fillet curve between two curve objects
    Parameters:
      curve0id (guid): identifier of the first curve object
      curve1id (guid): identifier of the second curve object
      radius (number, optional): fillet radius
      base_point0 (point|guid, optional): base point of the first curve. If omitted,
                          starting point of the curve is used
      base_point1 (point|guid, optional): base point of the second curve. If omitted,
                          starting point of the curve is used
    Returns:
      guid: id of the new curve object if successful
    Example:
      import rhinoscriptsyntax as rs
      curve0 = rs.AddLine([0,0,0], [5,1,0])
      curve1 = rs.AddLine([0,0,0], [1,5,0])
      rs.AddFilletCurve( curve0, curve1 )
    See Also:
      CurveFilletPoints
    """
    if base_point0: base_point0 = rhutil.coerce3dpoint(base_point0, True)
    else: base_point0 = Rhino.Geometry.Point3d.Unset
    if base_point1: base_point1 = rhutil.coerce3dpoint(base_point1, True)
    else: base_point1 = Rhino.Geometry.Point3d.Unset
    curve0 = rhutil.coercecurve(curve0id, -1, True)
    curve1 = rhutil.coercecurve(curve1id, -1, True)
    crv0_t = 0.0
    if base_point0==Rhino.Geometry.Point3d.Unset:
        crv0_t = curve0.Domain.Min
    else:
        rc, t = curve0.ClosestPoint(base_point0, 0.0)
        if not rc: raise Exception("ClosestPoint failed")
        crv0_t = t
    crv1_t = 0.0
    if base_point1==Rhino.Geometry.Point3d.Unset:
        crv1_t = curve1.Domain.Min
    else:
        rc, t = curve1.ClosestPoint(base_point1, 0.0)
        if not rc: raise Exception("ClosestPoint failed")
        crv1_t = t
    arc = Rhino.Geometry.Curve.CreateFillet(curve0, curve1, radius, crv0_t, crv1_t)
    rc = scriptcontext.doc.Objects.AddArc(arc)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddInterpCrvOnSrf(surface_id, points):
    """Adds an interpolated curve object that lies on a specified
    surface.  Note, this function will not create periodic curves,
    but it will create closed curves.
    Parameters:
      surface_id (guid): identifier of the surface to create the curve on
      points ([point|guid, point|guid, ...])list of 3D points that lie on the specified surface.
               The list must contain at least 2 points
    Returns:
      guid: id of the new curve object if successful
    Example:
      import rhinoscriptsyntax as rs
      surface_id = rs.GetObject("Select surface to draw curve on", rs.filter.surface)
      if surface_id:
          point1 = rs.GetPointOnSurface( surface_id, "First point on surface")
          if point1:
              point2 = rs.GetPointOnSurface( surface_id, "Second point on surface")
              if point2:
                  rs.AddInterpCrvOnSrf( surface_id, [point1, point2])
    See Also:
      AddCurve
      AddInterpCurve
      AddInterpCrvOnSrfUV
    """
    surface = rhutil.coercesurface(surface_id, True)
    points = rhutil.coerce3dpointlist(points, True)
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    curve = surface.InterpolatedCurveOnSurface(points, tolerance)
    if not curve: raise Exception("unable to create InterpolatedCurveOnSurface")
    rc = scriptcontext.doc.Objects.AddCurve(curve)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddInterpCrvOnSrfUV(surface_id, points):
    """Adds an interpolated curve object based on surface parameters,
    that lies on a specified surface. Note, this function will not
    create periodic curves, but it will create closed curves.
    Parameters:
      surface_id (guid): identifier of the surface to create the curve on
      points ([[number, number}, [number,number], ...]): a list of 2D surface parameters. The list must contain
                                                         at least 2 sets of parameters
    Returns:
      guid: id of the new curve object if successful
    Example:
      import rhinoscriptsyntax as rs
      surface_id = rs.GetObject("Select surface to draw curve on", rs.filter.surface)
      if surface_id:
          domainU = rs.SurfaceDomain( surface_id, 0)
          u0 = domainU[0]/2
          u1 = domainU[1]/2
          domainV = rs.SurfaceDomain( surface_id, 1)
          v0 = domainV[0]/2
          v1 = domainV[1]/2
          rs.AddInterpCrvOnSrfUV( surface_id, [[u0,v0],[u1,v1]])
    See Also:
      AddCurve
      AddInterpCurve
      AddInterpCrvOnSrf
    """
    surface = rhutil.coercesurface(surface_id, True)
    points = rhutil.coerce2dpointlist(points)
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    curve = surface.InterpolatedCurveOnSurfaceUV(points, tolerance)
    if not curve: raise Exception("unable to create InterpolatedCurveOnSurfaceUV")
    rc = scriptcontext.doc.Objects.AddCurve(curve)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddInterpCurve(points, degree=3, knotstyle=0, start_tangent=None, end_tangent=None):
    """Adds an interpolated curve object to the document. Options exist to make
    a periodic curve or to specify the tangent at the endpoints. The resulting
    curve is a non-rational NURBS curve of the specified degree.
    Parameters:
      points (point|guid, point|guid, ...]): a list containing 3D points to interpolate. For periodic curves,
          if the final point is a duplicate of the initial point, it is
          ignored. The number of control points must be >= (degree+1).
      degree (number, optional): The degree of the curve (must be >=1).
          Periodic curves must have a degree >= 2. For knotstyle = 1 or 2,
          the degree must be 3. For knotstyle = 4 or 5, the degree must be odd
      knotstyle(opt):
          0 Uniform knots.  Parameter spacing between consecutive knots is 1.0.
          1 Chord length spacing.  Requires degree = 3 with arrCV1 and arrCVn1 specified.
          2 Sqrt (chord length).  Requires degree = 3 with arrCV1 and arrCVn1 specified.
          3 Periodic with uniform spacing.
          4 Periodic with chord length spacing.  Requires an odd degree value.
          5 Periodic with sqrt (chord length) spacing.  Requires an odd degree value.
      start_tangent (vector, optional): a vector that specifies a tangency condition at the
          beginning of the curve. If the curve is periodic, this argument must be omitted.
      end_tangent (vector, optional): 3d vector that specifies a tangency condition at the
          end of the curve. If the curve is periodic, this argument must be omitted.
    Returns:
      guid: id of the new curve object if successful
    Example:
      import rhinoscriptsyntax as rs
      points = (0,0,0), (1,1,0), (2,0,0), (3,1,0), (4,0,0), (5,1,0)
      rs.AddInterpCurve(points)
    See Also:
      AddCurve
      CurvePointCount
      IsCurve
    """
    points = rhutil.coerce3dpointlist(points, True)
    if not start_tangent: start_tangent = Rhino.Geometry.Vector3d.Unset
    start_tangent = rhutil.coerce3dvector(start_tangent, True)
    if not end_tangent: end_tangent = Rhino.Geometry.Vector3d.Unset
    end_tangent = rhutil.coerce3dvector(end_tangent, True)
    knotstyle = System.Enum.ToObject(Rhino.Geometry.CurveKnotStyle, knotstyle)
    curve = Rhino.Geometry.Curve.CreateInterpolatedCurve(points, degree, knotstyle, start_tangent, end_tangent)
    if not curve: raise Exception("unable to CreateInterpolatedCurve")
    rc = scriptcontext.doc.Objects.AddCurve(curve)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddLine(start, end):
    """Adds a line curve to the current model.
    Parameters:
      start, end (point|guid) end points of the line
    Returns:
      guid: id of the new curve object
    Example:
      import rhinoscriptsyntax as rs
      start = rs.GetPoint("Start of line")
      if start:
          end = rs.GetPoint("End of line")
          if end: rs.AddLine(start, end)
    See Also:
      CurveEndPoint
      CurveStartPoint
      IsLine
    """
    start = rhutil.coerce3dpoint(start, True)
    end = rhutil.coerce3dpoint(end, True)
    rc = scriptcontext.doc.Objects.AddLine(start, end)
    if rc==System.Guid.Empty: raise Exception("Unable to add line to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddNurbsCurve(points, knots, degree, weights=None):
    """Adds a NURBS curve object to the document
    Parameters:
      points ([guid|point, guid|point, ...]): a list containing 3D control points
      knots ([number, number, ...]): Knot values for the curve. The number of elements in knots must
          equal the number of elements in points plus degree minus 1
      degree (number): degree of the curve. must be greater than of equal to 1
      weights([number, number, ...], optional) weight values for the curve. Number of elements should
          equal the number of elements in points. Values must be greater than 0
    Returns:
      guid: the identifier of the new object if successful, otherwise None
    Example:
      import rhinoscriptsyntax as rs
      curve_id = rs.GetObject("Pick a curve", rs.filter.curve)
      if curve_id:
          points = rs.CurvePoints(curve_id)
          knots = rs.CurveKnots(curve_id)
          degree = rs.CurveDegree(curve_id)
          newcurve = rs.AddNurbsCurve( points, knots, degree)
          if newcurve: rs.SelectObject(newcurve)
    See Also:
      CurveDegree
      CurveKnots
      CurvePoints
    """
    points = rhutil.coerce3dpointlist(points, True)
    cvcount = len(points)
    knotcount = cvcount + degree - 1
    if len(knots)!=knotcount:
        raise Exception("Number of elements in knots must equal the number of elements in points plus degree minus 1")
    if weights and len(weights)!=cvcount:
        raise Exception("Number of elements in weights should equal the number of elements in points")
    rational = (weights!=None)
    
    nc = Rhino.Geometry.NurbsCurve(3,rational,degree+1,cvcount)
    if rational: 
        for i in compat.RANGE(cvcount):
            nc.Points.SetPoint(i, points[i], weights[i])
    else:
        for i in compat.RANGE(cvcount):
            nc.Points.SetPoint(i, points[i])
    for i in compat.RANGE(knotcount): nc.Knots[i] = knots[i]
    rc = scriptcontext.doc.Objects.AddCurve(nc)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddPolyline(points, replace_id=None):
    """Adds a polyline curve to the current model
    Parameters:
      points ([guid|point, guid|point, ...]): list of 3D points. Duplicate, consecutive points will be
               removed. The list must contain at least two points. If the
               list contains less than four points, then the first point and
               last point must be different.
      replace_id (guid, optional): If set to the id of an existing object, the object
               will be replaced by this polyline
    Returns:
      guid: id of the new curve object if successful
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints(True)
      if points: rs.AddPolyline(points)
    See Also:
      IsPolyline
    """
    points = rhutil.coerce3dpointlist(points, True)
    if replace_id: replace_id = rhutil.coerceguid(replace_id, True)
    rc = System.Guid.Empty
    pl = Rhino.Geometry.Polyline(points)
    pl.DeleteShortSegments(scriptcontext.doc.ModelAbsoluteTolerance)
    if replace_id:
        if scriptcontext.doc.Objects.Replace(replace_id, pl):
            rc = replace_id
    else:
        rc = scriptcontext.doc.Objects.AddPolyline(pl)
    if rc==System.Guid.Empty: raise Exception("Unable to add polyline to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddRectangle(plane, width, height):
    """Add a rectangular curve to the document
    Parameters:
      plane (plane) plane on which the rectangle will lie
      width, height (number): width and height of rectangle as measured along the plane's
        x and y axes
    Returns:
      guid: id of new rectangle
    Example:
      import rhinoscriptsyntax as rs
      plane = rs.WorldXYPlane()
      plane = rs.RotatePlane(plane, 45.0, [0,0,1])
      rs.AddRectangle( plane, 5.0, 15.0 )
    See Also:
      
    """
    plane = rhutil.coerceplane(plane, True)
    rect = Rhino.Geometry.Rectangle3d(plane, width, height)
    poly = rect.ToPolyline()
    rc = scriptcontext.doc.Objects.AddPolyline(poly)
    if rc==System.Guid.Empty: raise Exception("Unable to add polyline to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddSpiral(point0, point1, pitch, turns, radius0, radius1=None):
    """Adds a spiral or helical curve to the document
    Parameters:
      point0 (point|guid): helix axis start point or center of spiral
      point1 (point|guid): helix axis end point or point normal on spiral plane
      pitch (number): distance between turns. If 0, then a spiral. If > 0 then the
              distance between helix "threads"
      turns (number): number of turns
      radius0 (number): starting radius of spiral
      radius1 (number, optional): ending radius of spiral. If omitted, the starting radius is used for the complete spiral.
    Returns:
      guid: id of new curve on success
    Example:
      import rhinoscriptsyntax as rs
      point0 = (0,0,0)
      point1 = (0,0,10)
      pitch = 1
      turns = 10
      radius0 = 5.0
      radius1 = 8.0
      rs.AddSpiral(point0, point1, pitch, turns, radius0, radius1)
    See Also:
      
    """
    if radius1 is None: radius1 = radius0
    point0 = rhutil.coerce3dpoint(point0, True)
    point1 = rhutil.coerce3dpoint(point1, True)
    dir = point1 - point0
    plane = Rhino.Geometry.Plane(point0, dir)
    point2 = point0 + plane.XAxis
    curve = Rhino.Geometry.NurbsCurve.CreateSpiral(point0, dir, point2, pitch, turns, radius0, radius1)
    rc = scriptcontext.doc.Objects.AddCurve(curve)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddSubCrv(curve_id, param0, param1):
    """Add a curve object based on a portion, or interval of an existing curve
    object. Similar in operation to Rhino's SubCrv command
    Parameters:
      curve_id (guid): identifier of a closed planar curve object
      param0, param1 (number): first and second parameters on the source curve
    Returns:
      guid: id of the new curve object if successful
    Example:
      import rhinoscriptsyntax as rs
      getresult = rs.GetCurveObject()
      if getresult:
          curve_id = getresult[0]
          point0 = rs.GetPointOnCurve( curve_id )
          if point0:
              point1 = rs.GetPointOnCurve( curve_id )
              if point1:
                  t0 = rs.CurveClosestPoint( curve_id, point0)
                  t1 = rs.CurveClosestPoint( curve_id, point1)
                  rs.AddSubCrv( curve_id, t0, t1 )
    See Also:
      CurveClosestPoint
      GetCurveObject
      GetPointOnCurve
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    trimcurve = curve.Trim(param0, param1)
    if not trimcurve: raise Exception("unable to trim curve")
    rc = scriptcontext.doc.Objects.AddCurve(trimcurve)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def ArcAngle(curve_id, segment_index=-1):
    """Returns the angle of an arc curve object.
    Parameters:
      curve_id (guid): identifier of a curve object
      segment_index (number, optional): identifies the curve segment if
      curve_id (guid): identifies a polycurve
    Returns:
      number: The angle in degrees if successful.
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select arc")
      if rs.IsArc(id):
          angle = rs.ArcAngle(id)
          print("Arc angle: {}".format(angle))
    See Also:
      AddArc3Pt
      ArcCenterPoint
      ArcMidPoint
      ArcRadius
      IsArc
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc, arc = curve.TryGetArc( Rhino.RhinoMath.ZeroTolerance )
    if not rc: raise Exception("curve is not arc")
    return arc.AngleDegrees


def ArcCenterPoint(curve_id, segment_index=-1):
    """Returns the center point of an arc curve object
    Parameters:
      curve_id (guid): identifier of a curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      point: The 3D center point of the arc if successful.
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select arc")
      if rs.IsArc(id):
      point = rs.ArcCenterPoint(id)
      rs.AddPoint(point)
    See Also:
      AddArc3Pt
      ArcAngle
      ArcMidPoint
      ArcRadius
      IsArc
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc, arc = curve.TryGetArc( Rhino.RhinoMath.ZeroTolerance )
    if not rc: raise Exception("curve is not arc")
    return arc.Center


def ArcMidPoint(curve_id, segment_index=-1):
    """Returns the mid point of an arc curve object
    Parameters:
      curve_id (guid): identifier of a curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      point: The 3D mid point of the arc if successful.
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select arc")
      if rs.IsArc(id):
          point = rs.ArcMidPoint(id)
          rs.AddPoint(point)
    See Also:
      AddArc3Pt
      ArcAngle
      ArcCenterPoint
      ArcRadius
      IsArc
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc, arc = curve.TryGetArc( Rhino.RhinoMath.ZeroTolerance )
    if not rc: raise Exception("curve is not arc")
    return arc.MidPoint


def ArcRadius(curve_id, segment_index=-1):
    """Returns the radius of an arc curve object
    Parameters:
      curve_id (guid): identifier of a curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      number: The radius of the arc if successful.
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select arc")
      if rs.IsArc(id):
          radius = rs.ArcRadius(id)
          print("Arc radius: {}".format(radius))
    See Also:
      AddArc3Pt
      ArcAngle
      ArcCenterPoint
      ArcMidPoint
      IsArc
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc, arc = curve.TryGetArc( Rhino.RhinoMath.ZeroTolerance )
    if not rc: raise Exception("curve is not arc")
    return arc.Radius


def CircleCenterPoint(curve_id, segment_index=-1, return_plane=False):
    """Returns the center point of a circle curve object
    Parameters:
      curve_id (guid): identifier of a curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
      return_plane (bool, optional): if True, the circle's plane is returned. If omitted the plane is not returned.
    Returns:
      point: The 3D center point of the circle if successful.
      plane: The plane of the circle if return_plane is True
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select circle")
      if rs.IsCircle(id):
          point = rs.CircleCenterPoint(id)
          rs.AddPoint( point )
    See Also:
      AddCircle
      AddCircle3Pt
      CircleCircumference
      CircleRadius
      IsCircle
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc, circle = curve.TryGetCircle(Rhino.RhinoMath.ZeroTolerance)
    if not rc: raise Exception("curve is not circle")
    if return_plane: return circle.Plane
    return circle.Center


def CircleCircumference(curve_id, segment_index=-1):
    """Returns the circumference of a circle curve object
    Parameters:
      curve_id (guid): identifier of a curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      number: The circumference of the circle if successful.
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select circle")
      if rs.IsCircle(id):
          circumference = rs.CircleCircumference(id)
          print("Circle circumference: {}".format(circumference))
    See Also:
      AddCircle
      AddCircle3Pt
      CircleCenterPoint
      CircleRadius
      IsCircle
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc, circle = curve.TryGetCircle( Rhino.RhinoMath.ZeroTolerance )
    if not rc: raise Exception("curve is not circle")
    return circle.Circumference


def CircleRadius(curve_id, segment_index=-1):
    """Returns the radius of a circle curve object
    Parameters:
      curve_id (guid): identifier of a curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      number: The radius of the circle if successful.
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select circle")
      if rs.IsCircle(id):
          radius = rs.CircleRadius(id)
          print("Circle radius: {}".format(radius))
    See Also:
      AddCircle
      AddCircle3Pt
      CircleCenterPoint
      CircleCircumference
      IsCircle
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc, circle = curve.TryGetCircle( Rhino.RhinoMath.ZeroTolerance )
    if not rc: raise Exception("curve is not circle")
    return circle.Radius


def CloseCurve(curve_id, tolerance=-1.0):
    """Closes an open curve object by making adjustments to the end points so
    they meet at a point
    Parameters:
      curve_id (guid): identifier of a curve object
      tolerance (number, optional): maximum allowable distance between start and end
                                    point. If omitted, the current absolute tolerance is used
    Returns:
      guid: id of the new curve object if successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select curve", rs.filter.curve)
      if not rs.IsCurveClosed(obj) and rs.IsCurveClosable(obj):
          rs.CloseCurve( obj )
    See Also:
      IsCurveClosable
      IsCurveClosed
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if curve.IsClosed: return curve_id
    if tolerance<0.0: tolerance = Rhino.RhinoMath.ZeroTolerance
    if not curve.MakeClosed(tolerance): return scriptcontext.errorhandler()
    rc = scriptcontext.doc.Objects.AddCurve(curve)
    if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def ClosedCurveOrientation(curve_id, direction=(0,0,1)):
    """Determine the orientation (counter-clockwise or clockwise) of a closed,
    planar curve
    Parameters:
      curve_id (guid): identifier of a curve object
      direction (vector, optional): 3d vector that identifies up, or Z axs, direction of
                                    the plane to test against
    Returns:
      number: 1 if the curve's orientation is counter-clockwise
             -1 if the curve's orientation is clockwise
              0 if unable to compute the curve's orientation
    Example:
    See Also:
    """
    curve = rhutil.coercecurve(curve_id, -1 ,True)
    direction = rhutil.coerce3dvector(direction, True)
    if not curve.IsClosed: return 0
    orientation = curve.ClosedCurveOrientation(direction)
    return int(orientation)


def ConvertCurveToPolyline(curve_id, angle_tolerance=5.0, tolerance=0.01, delete_input=False, min_edge_length=0, max_edge_length=0):
    """Convert curve to a polyline curve
    Parameters:
      curve_id (guid): identifier of a curve object
      angle_tolerance (number, optional): The maximum angle between curve tangents at line endpoints.
                                          If omitted, the angle tolerance is set to 5.0.
      tolerance(number, optional): The distance tolerance at segment midpoints. If omitted, the tolerance is set to 0.01.
      delete_input(bool, optional): Delete the curve object specified by curve_id. If omitted, curve_id will not be deleted.
      min_edge_length (number, optional): Minimum segment length
      max_edge_length (number, optonal): Maximum segment length
    Returns:
      guid: The new curve if successful.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          polyline = rs.ConvertCurveToPolyline(obj)
          if polyline: rs.SelectObject(polyline)
    See Also:
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if angle_tolerance<=0: angle_tolerance = 5.0
    angle_tolerance = Rhino.RhinoMath.ToRadians(angle_tolerance)
    if tolerance<=0.0: tolerance = 0.01;
    polyline_curve = curve.ToPolyline( 0, 0, angle_tolerance, 0.0, 0.0, tolerance, min_edge_length, max_edge_length, True)
    if not polyline_curve: return scriptcontext.errorhandler()
    id = System.Guid.Empty
    if delete_input:
        if scriptcontext.doc.Objects.Replace( curve_id, polyline_curve): id = curve_id
    else:
        id = scriptcontext.doc.Objects.AddCurve( polyline_curve )
    if System.Guid.Empty==id: return scriptcontext.errorhandler()
    return id

  
def CurveArcLengthPoint(curve_id, length, from_start=True):
    """Returns the point on the curve that is a specified arc length
    from the start of the curve.
    Parameters:
      curve_id (guid): identifier of a curve object
      length (number): The arc length from the start of the curve to evaluate.
      from_start (bool, optional): If not specified or True, then the arc length point is
          calculated from the start of the curve. If False, the arc length
          point is calculated from the end of the curve.
    Returns:
      point: on curve if successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          length = rs.CurveLength(obj)
          point = rs.CurveArcLengthPoint(obj, length/3.0)
          rs.AddPoint( point )
    See Also:
      CurveEndPoint
      CurveMidPoint
      CurveStartPoint
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    curve_length = curve.GetLength()
    if curve_length>=length:
        s = 0.0
        if length==0.0: s = 0.0
        elif length==curve_length: s = 1.0
        else: s = length / curve_length
        dupe = curve.Duplicate()
        if dupe:
            if from_start==False: dupe.Reverse()
            rc, t = dupe.NormalizedLengthParameter(s)
            if rc: return dupe.PointAt(t)
            dupe.Dispose()


def CurveArea(curve_id):
    """Returns area of closed planar curves. The results are based on the
    current drawing units.
    Parameters:
      curve_id (guid): The identifier of a closed, planar curve object.
    Returns:
      list[number, number]: List of area information. The list will contain the following information:
        Element  Description
        [0]      The area. If more than one curve was specified, the
                   value will be the cumulative area.
        [1]      The absolute (+/-) error bound for the area.
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a curve", rs.filter.curve)
      if id:
          props = rs.CurveArea(id)
          if props:
              print("The curve area is: {}".format(props[0]))
    See Also:
      IsCurve
      IsCurveClosed
      IsCurvePlanar
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    tol = scriptcontext.doc.ModelAbsoluteTolerance
    mp = Rhino.Geometry.AreaMassProperties.Compute(curve, tol)
    if mp == None: return None
    return mp.Area, mp.AreaError


def CurveAreaCentroid(curve_id):
    """Returns area centroid of closed, planar curves. The results are based
    on the current drawing units.
    Parameters:
      curve_id (guid)The identifier of a closed, planar curve object.
    Returns:
      tuple(point, vector): of area centroid information containing the following information:
        Element  Description
        [0]        The 3d centroid point. If more than one curve was specified,
                 the value will be the cumulative area.
        [1]        A 3d vector with the absolute (+/-) error bound for the area
                 centroid.
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a curve", rs.filter.curve)
      if id:
          props = rs.CurveAreaCentroid(id)
          if props:
              print("The curve area centroid is: {}".format(props[0]))
    See Also:
      IsCurve
      IsCurveClosed
      IsCurvePlanar
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    tol = scriptcontext.doc.ModelAbsoluteTolerance
    mp = Rhino.Geometry.AreaMassProperties.Compute(curve, tol)
    if mp == None: return None
    return mp.Centroid, mp.CentroidError


def CurveArrows(curve_id, arrow_style=None):
    """Enables or disables a curve object's annotation arrows
    Parameters:
      curve_id (guid): identifier of a curve
      arrow_style (number, optional): the style of annotation arrow to be displayed. If omitted the current type is returned.
        0 = no arrows
        1 = display arrow at start of curve
        2 = display arrow at end of curve
        3 = display arrow at both start and end of curve
      Returns:
        number: if arrow_style is not specified, the current annotation arrow style
        number: if arrow_style is specified, the previous arrow style
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve", rs.filter.curve)
      if rs.CurveArrows(obj)!=3: rs.CurveArrows(obj, 3)
    See Also:
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    rhobj = rhutil.coercerhinoobject(curve_id, True, True)
    attr = rhobj.Attributes
    rc = attr.ObjectDecoration
    none_obj_decor = compat.ENUM_NONE(Rhino.DocObjects.ObjectDecoration)
    if arrow_style is not None:
        if arrow_style==0:
            attr.ObjectDecoration = none_obj_decor
        elif arrow_style==1:
            attr.ObjectDecoration = Rhino.DocObjects.ObjectDecoration.StartArrowhead
        elif arrow_style==2:
            attr.ObjectDecoration = Rhino.DocObjects.ObjectDecoration.EndArrowhead
        elif arrow_style==3:
            attr.ObjectDecoration = Rhino.DocObjects.ObjectDecoration.BothArrowhead
        id = rhutil.coerceguid(curve_id, True)
        scriptcontext.doc.Objects.ModifyAttributes(id, attr, True)
        scriptcontext.doc.Views.Redraw()
    if rc==none_obj_decor: return 0
    if rc==Rhino.DocObjects.ObjectDecoration.StartArrowhead: return 1
    if rc==Rhino.DocObjects.ObjectDecoration.EndArrowhead: return 2
    if rc==Rhino.DocObjects.ObjectDecoration.BothArrowhead: return 3


def CurveBooleanDifference(curve_id_0, curve_id_1, tolerance=None):
    """Calculates the difference between two closed, planar curves and
    adds the results to the document. Note, curves must be coplanar.
    Parameters:
      curve_id_0 (guid): identifier of the first curve object.
      curve_id_1 (guid): identifier of the second curve object.
      tolerance (float, optional): a positive tolerance value, or None for the doc default.
    Returns:
      list(guid, ...): The identifiers of the new objects if successful, None on error.
    Example:
      import rhinoscriptsyntax as rs
      curveA = rs.GetObject("Select first curve", rs.filter.curve)
      curveB = rs.GetObject("Select second curve", rs.filter.curve)
      arrResult = rs.CurveBooleanDifference(curveA, curveB)
      if arrResult:
          rs.DeleteObject( curveA )
          rs.DeleteObject( curveB )
    See Also:
      CurveBooleanIntersection
      CurveBooleanUnion
    """
    curve0 = rhutil.coercecurve(curve_id_0, -1, True)
    curve1 = rhutil.coercecurve(curve_id_1, -1, True)
    if tolerance is None or tolerance<0:
        tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    out_curves = Rhino.Geometry.Curve.CreateBooleanDifference(curve0, curve1, tolerance)
    curves = []
    if out_curves:
        for curve in out_curves:
            if curve and curve.IsValid:
                rc = scriptcontext.doc.Objects.AddCurve(curve)
                curve.Dispose()
                if rc==System.Guid.Empty: raise Exception("unable to add curve to document")
                curves.append(rc)
    scriptcontext.doc.Views.Redraw()
    return curves


def CurveBooleanIntersection(curve_id_0, curve_id_1, tolerance=None):
    """Calculates the intersection of two closed, planar curves and adds
    the results to the document. Note, curves must be coplanar.
    Parameters:
      curve_id_0 (guid): identifier of the first curve object.
      curve_id_1 (guid): identifier of the second curve object.
      tolerance (float, optional): a positive tolerance value, or None for the doc default.
    Returns:
      list(guid, ...): The identifiers of the new objects.
    Example:
      import rhinoscriptsyntax as rs
      curveA = rs.GetObject("Select first curve", rs.filter.curve)
      curveB = rs.GetObject("Select second curve", rs.filter.curve)
      result = rs.CurveBooleanIntersection(curveA, curveB)
      if result:
          rs.DeleteObject( curveA )
          rs.DeleteObject( curveB )
    See Also:
      CurveBooleanDifference
      CurveBooleanUnion
    """
    curve0 = rhutil.coercecurve(curve_id_0, -1, True)
    curve1 = rhutil.coercecurve(curve_id_1, -1, True)
    if tolerance is None or tolerance<0:
        tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    out_curves = Rhino.Geometry.Curve.CreateBooleanIntersection(curve0, curve1, tolerance)
    curves = []
    if out_curves:
        for curve in out_curves:
            if curve and curve.IsValid:
                rc = scriptcontext.doc.Objects.AddCurve(curve)
                curve.Dispose()
                if rc==System.Guid.Empty: raise Exception("unable to add curve to document")
                curves.append(rc)
    scriptcontext.doc.Views.Redraw()
    return curves


def CurveBooleanUnion(curve_id, tolerance=None):
    """Calculate the union of two or more closed, planar curves and
    add the results to the document. Note, curves must be coplanar.
    Parameters:
      curve_id ([guid, guid, ...])list of two or more close planar curves identifiers
      tolerance (float, optional): a positive tolerance value, or None for the doc default.
    Returns:
      list(guid, ...): The identifiers of the new objects.
    Example:
      import rhinoscriptsyntax as rs
      curve_ids = rs.GetObjects("Select curves to union", rs.filter.curve)
      if curve_ids and len(curve_ids)>1:
          result = rs.CurveBooleanUnion(curve_ids)
          if result: rs.DeleteObjects(curve_ids)
    See Also:
      CurveBooleanDifference
      CurveBooleanIntersection
    """
    in_curves = [rhutil.coercecurve(id,-1,True) for id in curve_id]
    if len(in_curves)<2: raise ValueException("curve_id must have at least 2 curves")
    if tolerance is None or tolerance<0:
        tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    out_curves = Rhino.Geometry.Curve.CreateBooleanUnion(in_curves, tolerance)
    curves = []
    if out_curves:
        for curve in out_curves:
            if curve and curve.IsValid:
                rc = scriptcontext.doc.Objects.AddCurve(curve)
                curve.Dispose()
                if rc==System.Guid.Empty: raise Exception("unable to add curve to document")
                curves.append(rc)
        scriptcontext.doc.Views.Redraw()
    return curves


def CurveBrepIntersect(curve_id, brep_id, tolerance=None):
    """Intersects a curve object with a brep object. Note, unlike the
    CurveSurfaceIntersection function, this function works on trimmed surfaces.
    Parameters:
      curve_id (guid): identifier of a curve object
      brep_id (guid): identifier of a brep object
      tolerance (number, optional): distance tolerance at segment midpoints.
                        If omitted, the current absolute tolerance is used.
    Returns:
      list(guid, ...): identifiers for the newly created intersection objects if successful.
      None: on error.
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a curve", rs.filter.curve)
      if curve:
          brep = rs.GetObject("Select a brep", rs.filter.surface + rs.filter.polysurface)
          if brep: rs.CurveBrepIntersect( curve, brep )
    See Also:
      CurveSurfaceIntersection
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    brep = rhutil.coercebrep(brep_id, True)
    if tolerance is None or tolerance<0:
        tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    rc, out_curves, out_points = Rhino.Geometry.Intersect.Intersection.CurveBrep(curve, brep, tolerance)
    if not rc: return scriptcontext.errorhandler()
    
    curves = []
    points = []
    for curve in out_curves:
        if curve and curve.IsValid:
            rc = scriptcontext.doc.Objects.AddCurve(curve)
            curve.Dispose()
            if rc==System.Guid.Empty: raise Exception("unable to add curve to document")
            curves.append(rc)
    for point in out_points:
        if point and point.IsValid:
            rc = scriptcontext.doc.Objects.AddPoint(point)
            points.append(rc)
    if not curves and not points: return None
    scriptcontext.doc.Views.Redraw()
    return curves, points


def CurveClosestObject(curve_id, object_ids):
    """Returns the 3D point locations on two objects where they are closest to
    each other. Note, this function provides similar functionality to that of
    Rhino's ClosestPt command.
    Parameters:
      curve_id (guid):identifier of the curve object to test
      object_ids ([guid, ...]) list of identifiers of point cloud, curve, surface, or
        polysurface to test against
    Returns:
      tuple[guid, point, point]: containing the results of the closest point calculation.
      The elements are as follows:
        [0]    The identifier of the closest object.
        [1]    The 3-D point that is closest to the closest object.
        [2]    The 3-D point that is closest to the test curve.
    Example:
      import rhinoscriptsyntax as rs
      filter = rs.filter.curve | rs.filter.pointcloud | rs.filter.surface | rs.filter.polysurface
      objects = rs.GetObjects("Select target objects for closest point", filter)
      if objects:
          curve = rs.GetObject("Select curve")
          if curve:
              results = rs.CurveClosestObject(curve, objects)
              if results:
                  print("Curve id: {}".format(results[0]))
                  rs.AddPoint( results[1] )
                  rs.AddPoint( results[2] )
    See Also:
      CurveClosestPoint
      EvaluateCurve
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id,-1,True)
    geometry = []
    id = rhutil.coerceguid(object_ids, False)
    if id: object_ids = [id]
    for object_id in object_ids:
        rhobj = rhutil.coercerhinoobject(object_id, True, True)
        geometry.append( rhobj.Geometry )
    if not geometry: raise ValueError("object_ids must contain at least one item")
    success, curve_point, geom_point, which_geom = curve.ClosestPoints(geometry, 0.0)
    if success: return object_ids[which_geom], geom_point, curve_point

    
def CurveClosestPoint(curve_id, test_point, segment_index=-1 ):
    """Returns parameter of the point on a curve that is closest to a test point.
    Parameters:
      curve_id (guid): identifier of a curve object
      point (point): sampling point
      segment_index (number, optional): curve segment index if `curve_id` identifies a polycurve
    Returns:
      number: The parameter of the closest point on the curve
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a curve")
      if id:
          point = rs.GetPointOnCurve(id, "Pick a test point")
          if point:
              param = rs.CurveClosestPoint(id, point)
              print("Curve parameter: {}".format(param))
    See Also:
      EvaluateCurve
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    point = rhutil.coerce3dpoint(test_point, True)
    rc, t = curve.ClosestPoint(point, 0.0)
    if not rc: raise Exception("ClosestPoint failed")
    return t


def CurveContourPoints(curve_id, start_point, end_point, interval=None):
    """Returns the 3D point locations calculated by contouring a curve object.
    Parameters:
      curve_id (guid): identifier of a curve object.
      start_point (point): 3D starting point of a center line.
      end_point (point): 3D ending point of a center line.
      interval (number, optional): The distance between contour curves. If omitted,
      the interval will be equal to the diagonal distance of the object's
      bounding box divided by 50.
    Returns:
      list(point, ....): A list of 3D points, one for each contour
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select curve", rs.filter.curve)
      start_point = rs.GetPoint("Base point of center line")
      end_point = rs.GetPoint("Endpoint of center line", start_point)
      contour = rs.CurveContourPoints(obj, start_point, end_point)
      if contour: rs.AddPoints(contour)
    See Also:
      AddSrfContourCrvs
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    start_point = rhutil.coerce3dpoint(start_point, True)
    end_point = rhutil.coerce3dpoint(end_point, True)
    if start_point.DistanceTo(end_point)<Rhino.RhinoMath.ZeroTolerance:
        raise Exception("start and end point are too close to define a line")
    if not interval:
        bbox = curve.GetBoundingBox(True)
        diagonal = bbox.Max - bbox.Min
        interval = diagonal.Length / 50.0
    rc = curve.DivideAsContour( start_point, end_point, interval )
    return list(rc)


def CurveCurvature(curve_id, parameter):
    """Returns the curvature of a curve at a parameter. See the Rhino help for
    details on curve curvature
    Parameters:
      curve_id (guid): identifier of the curve
      parameter (number): parameter to evaluate
    Returns:
      tuple[point, vector, point, number, vector]: of curvature information on success
        [0] = point at specified parameter
        [1] = tangent vector
        [2] = center of radius of curvature
        [3] = radius of curvature
        [4] = curvature vector
      None: on failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          point = rs.GetPointOnCurve(obj, "Pick a test point")
          if point:
              param = rs.CurveClosestPoint(obj, point)
              if param:
                  data = rs.CurveCurvature(obj, param)
                  if data:
                      print("Curve curvature evaluation at parameter {}".format(param, ":"))
                      print(" 3-D Point: {}".format(data[0]))
                      print(" 3-D Tangent: {}".format(data[1]))
                      print(" Center of radius of curvature: {}".format(data[2]))
                      print(" Radius of curvature: {}".format(data[3]))
                      print(" 3-D Curvature: {}".format(data[4]))
    See Also:
      SurfaceCurvature
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    point = curve.PointAt(parameter)
    tangent = curve.TangentAt(parameter)
    if tangent.IsTiny(0): return scriptcontext.errorhandler()
    cv = curve.CurvatureAt(parameter)
    k = cv.Length
    if k<Rhino.RhinoMath.SqrtEpsilon: return scriptcontext.errorhandler()
    rv = cv / (k*k)
    circle = Rhino.Geometry.Circle(point, tangent, point + 2.0*rv)
    center = point + rv
    radius = circle.Radius
    return point, tangent, center, radius, cv


def CurveCurveIntersection(curveA, curveB=None, tolerance=-1):
    """Calculates intersection of two curve objects.
    Parameters:
      curveA (guid): identifier of the first curve object.
      curveB  (guid, optional): identifier of the second curve object. If omitted, then a
               self-intersection test will be performed on curveA.
      tolerance (number, optional): absolute tolerance in drawing units. If omitted,
                        the document's current absolute tolerance is used.
    Returns:
      list of tuples: containing intersection information if successful.
      The list will contain one or more of the following elements:
        Element Type     Description
        [n][0]  Number   The intersection event type, either Point (1) or Overlap (2).
        [n][1]  Point3d  If the event type is Point (1), then the intersection point 
                         on the first curve. If the event type is Overlap (2), then
                         intersection start point on the first curve.
        [n][2]  Point3d  If the event type is Point (1), then the intersection point
                         on the first curve. If the event type is Overlap (2), then
                         intersection end point on the first curve.
        [n][3]  Point3d  If the event type is Point (1), then the intersection point 
                         on the second curve. If the event type is Overlap (2), then
                         intersection start point on the second curve.
        [n][4]  Point3d  If the event type is Point (1), then the intersection point
                         on the second curve. If the event type is Overlap (2), then
                         intersection end point on the second curve.
        [n][5]  Number   If the event type is Point (1), then the first curve parameter.
                         If the event type is Overlap (2), then the start value of the
                         first curve parameter range.
        [n][6]  Number   If the event type is Point (1), then the first curve parameter.
                         If the event type is Overlap (2), then the end value of the
                         first curve parameter range.
        [n][7]  Number   If the event type is Point (1), then the second curve parameter.
                         If the event type is Overlap (2), then the start value of the
                         second curve parameter range.
        [n][8]  Number   If the event type is Point (1), then the second curve parameter.
                         If the event type is Overlap (2), then the end value of the 
                         second curve parameter range.
    Example:
      import rhinoscriptsyntax as rs
      def ccx():
          curve1 = rs.GetObject("Select first curve", rs.filter.curve)
          if curve1 is None: return
          curve2 = rs.GetObject("Select second curve", rs.filter.curve)
          if curve2 is None: return
          intersection_list = rs.CurveCurveIntersection(curve1, curve2)
          if intersection_list is None:
              print("Selected curves do not intersect.")
              return
          for intersection in intersection_list:
              if intersection[0] == 1:
                  print("Point")
                  print("Intersection point on first curve:  {}".format(intersection[1]))
                  print("Intersection point on second curve:  {}".format(intersection[3]))
                  print("First curve parameter:  {}".format(intersection[5]))
                  print("Second curve parameter:  {}".format(intersection[7]))
              else:
                  print("Overlap")
                  print("Intersection start point on first curve: {}".format(intersection[1]))
                  print("Intersection end point on first curve: {}".format(intersection[2]))
                  print("Intersection start point on second curve: {}".format(intersection[3]))
                  print("Intersection end point on second curve: {}".format(intersection[4]))
                  print("First curve parameter range: {} to {}".format(intersection[5], intersection[6]))
                  print("Second curve parameter range: {} to {}".format(intersection[7], intersection[8]))
      ccx()
    See Also:
      CurveSurfaceIntersection
    """
    curveA = rhutil.coercecurve(curveA, -1, True)
    if curveB: curveB = rhutil.coercecurve(curveB, -1, True)
    if tolerance is None or tolerance<0.0:
        tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    if curveB:
        rc = Rhino.Geometry.Intersect.Intersection.CurveCurve(curveA, curveB, tolerance, 0.0)
    else:
        rc = Rhino.Geometry.Intersect.Intersection.CurveSelf(curveA, tolerance)
    if rc:
        events = []
        for i in compat.RANGE(rc.Count):
            event_type = 1
            if( rc[i].IsOverlap ): event_type = 2
            oa = rc[i].OverlapA
            ob = rc[i].OverlapB
            element = (event_type, rc[i].PointA, rc[i].PointA2, rc[i].PointB, rc[i].PointB2, oa[0], oa[1], ob[0], ob[1])
            events.append(element)
        return events


def CurveDegree(curve_id, segment_index=-1):
    """Returns the degree of a curve object.
    Parameters:
      curve_id (guid): identifier of a curve object.
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve.
    Returns:
      number: The degree of the curve if successful.
      None: on error.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          degree = rs.CurveDegree(obj)
          print("Curve degree:{}".format(degree))
    See Also:
      CurveDomain
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    return curve.Degree


def CurveDeviation(curve_a, curve_b):
    """Returns the minimum and maximum deviation between two curve objects
    Parameters:
      curve_a, curve_b (guid): identifiers of two curves
    Returns:
      tuple[number, number, number, number, number, number]: of deviation information on success
        [0] = curve_a parameter at maximum overlap distance point
        [1] = curve_b parameter at maximum overlap distance point
        [2] = maximum overlap distance
        [3] = curve_a parameter at minimum overlap distance point
        [4] = curve_b parameter at minimum overlap distance point
        [5] = minimum distance between curves
      None on error
    Example:
      import rhinoscriptsyntax as rs
      curveA = rs.GetObject("Select first curve to test", rs.filter.curve)
      curveB = rs.GetObject("Select second curve to test", rs.filter.curve)
      deviation = rs.CurveDeviation(curveA, curveB)
      if deviation:
          print("Minimum deviation = {}".format(deviation[5]))
          print("Maximum deviation = {}".format(deviation[2]))
    See Also:
      CurveArea
      CurveAreaCentroid
    """
    curve_a = rhutil.coercecurve(curve_a, -1, True)
    curve_b = rhutil.coercecurve(curve_b, -1, True)
    tol = scriptcontext.doc.ModelAbsoluteTolerance
    rc = Rhino.Geometry.Curve.GetDistancesBetweenCurves(curve_a, curve_b, tol)
    if not rc[0]: return scriptcontext.errorhandler()
    maxa = rc[2]
    maxb = rc[3]
    maxd = rc[1]
    mina = rc[5]
    minb = rc[6]
    mind = rc[4]
    return maxa, maxb, maxd, mina, minb, mind


def CurveDim(curve_id, segment_index=-1):
    """Returns the dimension of a curve object
    Parameters:
      curve_id (guid): identifier of a curve object.
      segment_index (number, optional): the curve segment if `curve_id` identifies a polycurve.
    Returns:
      number: The dimension of the curve if successful. None on error.
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a curve")
      if rs.IsCurve(curve):
          print("Curve dimension = {}".format(rs.CurveDim(curve)))
    See Also:
      CurveDegree
      CurveDomain
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    return curve.Dimension


def CurveDirectionsMatch(curve_id_0, curve_id_1):
    """Tests if two curve objects are generally in the same direction or if they
    would be more in the same direction if one of them were flipped. When testing
    curve directions, both curves must be either open or closed - you cannot test
    one open curve and one closed curve.
    Parameters:
      curve_id_0 (guid): identifier of first curve object
      curve_id_1 (guid): identifier of second curve object
    Returns:
      bool: True if the curve directions match, otherwise False.
    Example:
      import rhinoscriptsyntax as rs
      curve1 = rs.GetObject("Select first curve to compare", rs.filter.curve)
      curve2 = rs.GetObject("Select second curve to compare", rs.filter.curve)
      if rs.CurveDirectionsMatch(curve1, curve2):
          print("Curves are in the same direction")
      else:
          print("Curve are not in the same direction")
    See Also:
      ReverseCurve
    """
    curve0 = rhutil.coercecurve(curve_id_0, -1, True)
    curve1 = rhutil.coercecurve(curve_id_1, -1, True)
    return Rhino.Geometry.Curve.DoDirectionsMatch(curve0, curve1)


def CurveDiscontinuity(curve_id, style):   
    """Search for a derivatitive, tangent, or curvature discontinuity in
    a curve object.
    Parameters:
      curve_id (guid): identifier of curve object
      style (number): The type of continuity to test for. The types of
          continuity are as follows:
          Value    Description
          1        C0 - Continuous function
          2        C1 - Continuous first derivative
          3        C2 - Continuous first and second derivative
          4        G1 - Continuous unit tangent
          5        G2 - Continuous unit tangent and curvature
    Returns:
      list(point, ...): 3D points where the curve is discontinuous
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a curve", rs.filter.curve)
      if rs.IsCurve(curve):
          points = rs.CurveDiscontinuity(curve, 2)
          if points: rs.AddPoints( points )
    See Also:
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    dom = curve.Domain
    t0 = dom.Min
    t1 = dom.Max
    points = []
    get_next = True
    while get_next:
        get_next, t = curve.GetNextDiscontinuity(System.Enum.ToObject(Rhino.Geometry.Continuity, style), t0, t1)
        if get_next:
            points.append(curve.PointAt(t))
            t0 = t # Advance to the next parameter
    return points


def CurveDomain(curve_id, segment_index=-1):
    """Returns the domain of a curve object
    as an indexable object with two elements.
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve.
    Returns:
      list(number, number): the domain of the curve if successful.
         [0] Domain minimum
         [1] Domain maximum
      None: on error

    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          domain = rs.CurveDomain(obj)
          print("Curve domain: {} to {}".format(domain[0], domain[1]))
    See Also:
      CurveDegree
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    return curve.Domain


def CurveEditPoints(curve_id, return_parameters=False, segment_index=-1):
    """Returns the edit, or Greville, points of a curve object. 
    For each curve control point, there is a corresponding edit point.
    Parameters:
      curve_id (guid): identifier of the curve object
      return_parameters (bool, optional): if True, return as a list of curve parameters.
                                          If False, return as a list of 3d points
      segment_index (number, optional): the curve segment index is `curve_id` identifies a polycurve
    Returns:
      list(point, ....): curve edit points on success
      None on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          points = rs.CurveEditPoints(obj)
          if points: rs.AddPointCloud( points )
    See Also:
      IsCurve
      CurvePointCount
      CurvePoints
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    nc = curve.ToNurbsCurve()
    if not nc: return scriptcontext.errorhandler()
    if return_parameters: return nc.GrevilleParameters()
    return list(nc.GrevillePoints())


def CurveEndPoint(curve_id, segment_index=-1):
    """Returns the end point of a curve object
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      point: The 3d endpoint of the curve if successful.
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      object = rs.GetObject("Select a curve")
      if rs.IsCurve(object):
          point = rs.CurveEndPoint(object)
          rs.AddPoint(point)
    See Also:
      CurveMidPoint
      CurveStartPoint
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    return curve.PointAtEnd


def CurveFilletPoints(curve_id_0, curve_id_1, radius=1.0, base_point_0=None, base_point_1=None, return_points=True):
    """Find points at which to cut a pair of curves so that a fillet of a
    specified radius fits. A fillet point is a pair of points (point0, point1)
    such that there is a circle of radius tangent to curve curve0 at point0 and
    tangent to curve curve1 at point1. Of all possible fillet points, this
    function returns the one which is the closest to the base point base_point_0,
    base_point_1. Distance from the base point is measured by the sum of arc
    lengths along the two curves. 
    Parameters:
      curve_id_0 (guid): identifier of the first curve object.
      curve_id_1 (guid): identifier of the second curve object.
      radius (number, optional): The fillet radius. If omitted, a radius
                     of 1.0 is specified.
      base_point_0 (point, optional): The base point on the first curve.
                     If omitted, the starting point of the curve is used.
      base_point_1 (point, optional): The base point on the second curve. If omitted,
                     the starting point of the curve is used.
      return_points (bool, optional): If True (Default), then fillet points are
                     returned. Otherwise, a fillet curve is created and
                     it's identifier is returned.
    Returns:
      list(point, point, point, vector, vector, vector): If return_points is True, then a list of point and vector values
      if successful. The list elements are as follows:
          [0]    A point on the first curve at which to cut (point).
          [1]    A point on the second curve at which to cut (point).
          [2]    The fillet plane's origin (point). This point is also
                   the center point of the fillet
          [3]    The fillet plane's X axis (vector).
          [4]    The fillet plane's Y axis (vector).
          [5]    The fillet plane's Z axis (vector).
      
      guid: If return_points is False, then the identifier of the fillet curve
            if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      curve0 = rs.AddLine([0,0,0], [5,1,0])
      curve1 = rs.AddLine([0,0,0], [1,5,0])
      fillet = rs.CurveFilletPoints(curve0, curve1)
      if fillet:
          rs.AddPoint( fillet[0] )
          rs.AddPoint( fillet[1] )
          rs.AddPoint( fillet[2] )
    See Also:
      AddFilletCurve
    """
    curve0 = rhutil.coercecurve(curve_id_0, -1, True)
    curve1 = rhutil.coercecurve(curve_id_1, -1, True)
    t0_base = curve0.Domain.Min
    
    if base_point_0:
        rc = curve0.ClosestPoint(base_point_0, t0_base)
        if not rc[0]: return scriptcontext.errorhandler()
    
    t1_base = curve1.Domain.Min
    if base_point_1:
        rc = curve1.ClosestPoint(base_point_1, t1_base)
        if not rc[0]: return scriptcontext.errorhandler()

    r = radius if (radius and radius>0) else 1.0
    rc = Rhino.Geometry.Curve.GetFilletPoints(curve0, curve1, r, t0_base, t1_base)
    if rc[0]:
        point_0 = curve0.PointAt(rc[1])
        point_1 = curve1.PointAt(rc[2])
        return point_0, point_1, rc[3].Origin, rc[3].XAxis, rc[3].YAxis, rc[3].ZAxis
    return scriptcontext.errorhandler()


def CurveFrame(curve_id, parameter, segment_index=-1):
    """Returns the plane at a parameter of a curve. The plane is based on the
    tangent and curvature vectors at a parameter.
    Parameters:
      curve_id (guid): identifier of the curve object.
      parameter (number): parameter to evaluate.
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      plane: The plane at the specified parameter if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetCurveObject("Select a curve")
      if curve:
          plane = rs.CurveFrame(curve[0], curve[4])
          rs.AddPlaneSurface(plane, 5.0, 3.0)
    See Also:
      CurvePerpFrame
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    domain = curve.Domain
    if not domain.IncludesParameter(parameter):
        tol = scriptcontext.doc.ModelAbsoluteTolerance
        if parameter>domain.Max and (parameter-domain.Max)<=tol:
            parameter = domain.Max
        elif parameter<domain.Min and (domain.Min-parameter)<=tol:
            parameter = domain.Min
        else:
            return scriptcontext.errorhandler()
    rc, frame = curve.FrameAt(parameter)
    if rc and frame.IsValid: return frame
    return scriptcontext.errorhandler()


def CurveKnotCount(curve_id, segment_index=-1):
    """Returns the knot count of a curve object.
    Parameters:
      curve_id (guid): identifier of the curve object.
      segment_index (number, optional): the curve segment if `curve_id` identifies a polycurve.
    Returns:
      number: The number of knots if successful.
      None: if not successful or on error.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          count = rs.CurveKnotCount(obj)
          print("Curve knot count:{}".format(count))
    See Also:
      DivideCurve
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    nc = curve.ToNurbsCurve()
    if not nc: return scriptcontext.errorhandler()
    return nc.Knots.Count


def CurveKnots(curve_id, segment_index=-1):
    """Returns the knots, or knot vector, of a curve object
    Parameters:
      curve_id (guid): identifier of the curve object.
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve.
    Returns:
      list(number, ....): knot values if successful.
      None: if not successful or on error.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          knots = rs.CurveKnots(obj)
          if knots:
              for knot in knots: print("Curve knot value:{}".format(knot))
    See Also:
      CurveKnotCount
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    nc = curve.ToNurbsCurve()
    if not nc: return scriptcontext.errorhandler()
    rc = [nc.Knots[i] for i in range(nc.Knots.Count)]
    return rc


def CurveLength(curve_id, segment_index=-1, sub_domain=None):
    """Returns the length of a curve object.
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
      sub_domain ([number, number], optional): list of two numbers identifying the sub-domain of the
          curve on which the calculation will be performed. The two parameters
          (sub-domain) must be non-decreasing. If omitted, the length of the
          entire curve is returned.
    Returns:
      number: The length of the curve if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      object = rs.GetObject("Select a curve")
      if rs.IsCurve(object):
          length = rs.CurveLength(object)
          print("Curve length:{}".format(length))
    See Also:
      CurveDomain
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    if sub_domain:
        if len(sub_domain)==2:
            dom = Rhino.Geometry.Interval(sub_domain[0], sub_domain[1])
            return curve.GetLength(dom)
        return scriptcontext.errorhandler()
    return curve.GetLength()


def CurveMidPoint(curve_id, segment_index=-1):
    """Returns the mid point of a curve object.
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      point: The 3D midpoint of the curve if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      object = rs.GetObject("Select a curve")
      if rs.IsCurve(object):
          point = rs.CurveMidPoint(pbject)
          rs.AddPoint( point )
    See Also:
      CurveEndPoint
      CurveStartPoint
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc, t = curve.NormalizedLengthParameter(0.5)
    if rc: return curve.PointAt(t)
    return scriptcontext.errorhandler()


def CurveNormal(curve_id, segment_index=-1):
    """Returns the normal direction of the plane in which a planar curve object lies.
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment if curve_id identifies a polycurve
    Returns:
      vector: The 3D normal vector if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      object = rs.GetObject("Select a planar curve")
      if rs.IsCurve(object) and rs.IsCurvePlanar(object):
          normal = rs.CurveNormal(object)
          if normal: print("Curve Normal:{}".format(normal))
    See Also:
      IsCurve
      IsCurvePlanar
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    tol = scriptcontext.doc.ModelAbsoluteTolerance
    rc, plane = curve.TryGetPlane(tol)
    if rc: return plane.Normal
    return scriptcontext.errorhandler()


def CurveNormalizedParameter(curve_id, parameter):
    """Converts a curve parameter to a normalized curve parameter;
    one that ranges between 0-1
    Parameters:
      curve_id (guid): identifier of the curve object
      parameter (number): the curve parameter to convert
    Returns:
      number: normalized curve parameter
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select curve")
      if rs.IsCurve(obj):
          domain = rs.CurveDomain(obj)
          parameter = (domain[0]+domain[1])/2.0
          print("Curve parameter:{}".format(parameter))
          normalized = rs.CurveNormalizedParameter(obj, parameter)
          print("Normalized parameter:{}".format(normalized))
    See Also:
      CurveDomain
      CurveParameter
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    return curve.Domain.NormalizedParameterAt(parameter)


def CurveParameter(curve_id, parameter):
    """Converts a normalized curve parameter to a curve parameter;
    one within the curve's domain
    Parameters:
      curve_id (guid): identifier of the curve object
      parameter (number): the normalized curve parameter to convert
    Returns:
      number: curve parameter
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select curve")
      if rs.IsCurve(obj):
          normalized = 0.5
          print("Normalized parameter:{}".format(normalized))
          parameter = rs.CurveParameter(obj, normalized)
          print("Curve parameter:{}".format(parameter))
    See Also:
      CurveDomain
      CurveNormalizedParameter
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    return curve.Domain.ParameterAt(parameter)


def CurvePerpFrame(curve_id, parameter):
    """Returns the perpendicular plane at a parameter of a curve. The result
    is relatively parallel (zero-twisting) plane
    Parameters:
      curve_id (guid): identifier of the curve object
      parameter (number): parameter to evaluate
    Returns:
      plane: Plane on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      crv = rs.GetCurveObject("Select a curve")
      if crv:
          plane = rs.CurvePerpFrame(crv[0], crv[4])
          rs.AddPlaneSurface( plane, 1, 1 )
    See Also:
      CurveFrame
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    parameter = float(parameter)
    rc, plane = curve.PerpendicularFrameAt(parameter)
    if rc: return plane


def CurvePlane(curve_id, segment_index=-1):
    """Returns the plane in which a planar curve lies. Note, this function works
    only on planar curves.
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      plane: The plane in which the curve lies if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a curve", rs.filter.curve)
      if rs.IsCurvePlanar(curve):
          plane = rs.CurvePlane(curve)
          rs.ViewCPlane(None, plane)
    See Also:
      IsCurve
      IsCurvePlanar
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    tol = scriptcontext.doc.ModelAbsoluteTolerance
    rc, plane = curve.TryGetPlane(tol)
    if rc: return plane
    return scriptcontext.errorhandler()


def CurvePointCount(curve_id, segment_index=-1):
    """Returns the control points count of a curve object.
    Parameters:
      curve_id (guid) identifier of the curve object
      segment_index (number, optional): the curve segment if `curve_id` identifies a polycurve
    Returns:
      number: Number of control points if successful.
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          count = rs.CurvePointCount(obj)
          print("Curve point count:{}".format(count))
    See Also:
      DivideCurve
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    nc = curve.ToNurbsCurve()
    if nc: return nc.Points.Count
    return scriptcontext.errorhandler()


def CurvePoints(curve_id, segment_index=-1):
    """Returns the control points, or control vertices, of a curve object.
    If the curve is a rational NURBS curve, the euclidean control vertices
    are returned.
    Parameters:
      curve_id (guid): the object's identifier
      segment_index (number, optional): the curve segment if `curve_id` identifies a polycurve
    Returns:
      list(point, ...): the control points, or control vertices, of a curve object
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          points = rs.CurvePoints(obj)
          if points: [rs.AddPoint(pt) for pt in points]
    See Also:
      CurvePointCount
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    nc = curve.ToNurbsCurve()
    if nc is None: return scriptcontext.errorhandler()
    points = [nc.Points[i].Location for i in compat.RANGE(nc.Points.Count)]
    return points


def CurveRadius(curve_id, test_point, segment_index=-1):
    """Returns the radius of curvature at a point on a curve.
    Parameters:
      curve_id (guid): identifier of the curve object
      test_point (point): sampling point
      segment_index (number, optional): the curve segment if curve_id identifies a polycurve
    Returns:
      number: The radius of curvature at the point on the curve if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          point = rs.GetPointOnCurve(obj, "Pick a test point")
          if point:
              radius = rs.CurveRadius(obj, point)
              print("Radius of curvature:{}".format(radius))
    See Also:
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    point = rhutil.coerce3dpoint(test_point, True)
    rc, t = curve.ClosestPoint(point, 0.0)
    if not rc: return scriptcontext.errorhandler()
    v = curve.CurvatureAt( t )
    k = v.Length
    if k>Rhino.RhinoMath.ZeroTolerance: return 1/k
    return scriptcontext.errorhandler()


def CurveSeam(curve_id, parameter):
    """Adjusts the seam, or start/end, point of a closed curve.
    Parameters:
      curve_id (guid): identifier of the curve object
      parameter (number): The parameter of the new start/end point.
                  Note, if successful, the resulting curve's
                  domain will start at `parameter`.
    Returns:
      bool: True or False indicating success or failure.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select closed curve", rs.filter.curve)
      if rs.IsCurveClosed(obj):
          domain = rs.CurveDomain(obj)
          parameter = (domain[0] + domain[1])/2.0
          rs.CurveSeam( obj, parameter )
    See Also:
      IsCurve
      IsCurveClosed
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if (not curve.IsClosed or not curve.Domain.IncludesParameter(parameter)):
        return False
    dupe = curve.Duplicate()
    if dupe:
        dupe.ChangeClosedCurveSeam(parameter)
        curve_id = rhutil.coerceguid(curve_id)
        dupe_obj = scriptcontext.doc.Objects.Replace(curve_id, dupe)
        return dupe_obj is not None
    return False


def CurveStartPoint(curve_id, segment_index=-1, point=None):
    """Returns the start point of a curve object
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
      point (point, optional): new start point
    Returns:
      point: The 3D starting point of the curve if successful.
    Example:
      import rhinoscriptsyntax as rs
      object = rs.GetObject("Select a curve")
      if rs.IsCurve(object):
          point = rs.CurveStartPoint(object)
          rs.AddPoint(point)
    See Also:
      CurveEndPoint
      CurveMidPoint
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc = curve.PointAtStart
    if point:
        point = rhutil.coerce3dpoint(point, True)
        if point and curve.SetStartPoint(point):
            curve_id = rhutil.coerceguid(curve_id, True)
            scriptcontext.doc.Objects.Replace(curve_id, curve)
            scriptcontext.doc.Views.Redraw()
    return rc


def CurveSurfaceIntersection(curve_id, surface_id, tolerance=-1, angle_tolerance=-1):
    """Calculates intersection of a curve object with a surface object.
    Note, this function works on the untrimmed portion of the surface.
    Parameters:
      curve_id (guid): The identifier of the first curve object.
      surface_id (guid): The identifier of the second curve object. If omitted,
          the a self-intersection test will be performed on curve.
      tolerance (number, optional): The absolute tolerance in drawing units. If omitted,
          the document's current absolute tolerance is used.
      angle_tolerance (number, optional) angle tolerance in degrees. The angle
          tolerance is used to determine when the curve is tangent to the
          surface. If omitted, the document's current angle tolerance is used.
    Returns:
      list(list(point, point, point, point, number, number, number, number, number, number), ...): of intersection information if successful.
      The list will contain one or more of the following elements:
        Element Type     Description
        [n][0]  Number   The intersection event type, either Point(1) or Overlap(2).
        [n][1]  Point3d  If the event type is Point(1), then the intersection point
                         on the first curve. If the event type is Overlap(2), then
                         intersection start point on the first curve.
        [n][2]  Point3d  If the event type is Point(1), then the intersection point
                         on the first curve. If the event type is Overlap(2), then
                         intersection end point on the first curve.
        [n][3]  Point3d  If the event type is Point(1), then the intersection point
                         on the second curve. If the event type is Overlap(2), then
                         intersection start point on the surface.
        [n][4]  Point3d  If the event type is Point(1), then the intersection point
                         on the second curve. If the event type is Overlap(2), then
                         intersection end point on the surface.
        [n][5]  Number   If the event type is Point(1), then the first curve parameter.
                         If the event type is Overlap(2), then the start value of the
                         first curve parameter range.
        [n][6]  Number   If the event type is Point(1), then the first curve parameter.
                         If the event type is Overlap(2), then the end value of the
                         curve parameter range.
        [n][7]  Number   If the event type is Point(1), then the U surface parameter.
                         If the event type is Overlap(2), then the U surface parameter
                         for curve at (n, 5).
        [n][8]  Number   If the event type is Point(1), then the V surface parameter.
                         If the event type is Overlap(2), then the V surface parameter
                         for curve at (n, 5).
        [n][9]  Number   If the event type is Point(1), then the U surface parameter.
                         If the event type is Overlap(2), then the U surface parameter
                         for curve at (n, 6).
        [n][10] Number   If the event type is Point(1), then the V surface parameter.
                         If the event type is Overlap(2), then the V surface parameter
                         for curve at (n, 6).
    Example:
      import rhinoscriptsyntax as rs
      def csx():
          curve = rs.GetObject("Select curve", rs.filter.curve)
          if curve is None: return
          surface = rs.GetObject("Select surface", rs.filter.surface)
          if surface is None: return
          intersection_list = rs.CurveSurfaceIntersection(curve, surface)
          if intersection_list is None:
              print("Curve and surface do not intersect.")
              return
          for intersection in intersection_list:
              if intersection[0]==1:
                  print("Point")
                  print("Intersection point on curve:{}".format(intersection[1]))
                  print("Intersection point on surface:{}".format(intersection[3]))
                  print("Curve parameter:{}".format(intersection[5]))
                  print("Surface parameter: {}, {}".format(intersection[7], intersection[8]))
              else:
                  print("Overlap")
                  print("Intersection start point on curve:{}".format(intersection[1]))
                  print("Intersection end point on curve:{}".format(intersection[2]))
                  print("Intersection start point on surface:{}".format(intersection[3]))
                  print("Intersection end point on surface:{}".format(intersection[4]))
                  print("Curve parameter range: {} to {}".format(intersection[5], intersection[6]))
                  print("Surface parameter range: {}, {} to {}, {}".format(intersection[7] intersection[8], intersection[9], intersection[10]))
      csx()
    See Also:
      CurveCurveIntersection
      CurveBrepIntersect
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    surface = rhutil.coercesurface(surface_id, True)
    if tolerance is None or tolerance<0:
        tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    if angle_tolerance is None or angle_tolerance<0:
        angle_tolerance = scriptcontext.doc.ModelAngleToleranceRadians
    else:
        angle_tolerance = math.radians(angle_tolerance)
    rc = Rhino.Geometry.Intersect.Intersection.CurveSurface(curve, surface, tolerance, angle_tolerance)
    if rc:
        events = []
        for i in compat.RANGE(rc.Count):
            event_type = 2 if rc[i].IsOverlap else 1
            item = rc[i]
            oa = item.OverlapA
            u,v = item.SurfaceOverlapParameter()
            e = (event_type, item.PointA, item.PointA2, item.PointB, item.PointB2, oa[0], oa[1], u[0], u[1], v[0], v[1])
            events.append(e)
        return events


def CurveTangent(curve_id, parameter, segment_index=-1):
    """Returns a 3D vector that is the tangent to a curve at a parameter.
    Parameters:
      curve_id (guid): identifier of the curve object
      parameter (number) parameter to evaluate
      segment_index (number, optional) the curve segment index if `curve_id` identifies a polycurve
    Returns:
      vector: A 3D vector if successful.
      None: on error.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve", rs.filter.curve)
      if obj:
          point = rs.GetPointOnCurve(obj)
          if point:
              param = rs.CurveClosestPoint(obj, point)
              normal = rs.CurveTangent(obj, param)
              print(normal)
    See Also:
      CurveClosestPoint
      CurveDomain
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc = Rhino.Geometry.Point3d.Unset
    if curve.Domain.IncludesParameter(parameter):
        return curve.TangentAt(parameter)
    return scriptcontext.errorhandler()


def CurveWeights(curve_id, segment_index=-1):
    """Returns list of weights that are assigned to the control points of a curve
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      number: The weight values of the curve if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          weights = rs.CurveWeights(obj)
          if weights:
              for weight in weights:
                  print("Curve control point weight value:{}".format(weight))
    See Also:
      CurveKnots
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    nc = curve
    if type(curve) is not Rhino.Geometry.NurbsCurve:
        nc = curve.ToNurbsCurve()
    if nc is None: return scriptcontext.errorhandler()
    return [pt.Weight for pt in nc.Points]


def DivideCurve(curve_id, segments, create_points=False, return_points=True):
    """Divides a curve object into a specified number of segments.
    Parameters:
      curve_id (guid):identifier of the curve object
      segments (number): The number of segments.
      create_points (bool, optional): Create the division points. If omitted or False,
          points are not created.
      return_points (bool, optional): If omitted or True, points are returned.
          If False, then a list of curve parameters are returned.
    Returns:
      list(point|number, ...): If `return_points` is not specified or True, then a list containing 3D division points.
      list(point|number, ...): If `return_points` is False, then an array containing division curve parameters.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if obj:
          points = rs.DivideCurve(obj, 4)
          for point in points: rs.AddPoint(point)
    See Also:
      DivideCurveEquidistant
      DivideCurveLength
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    rc = curve.DivideByCount(segments, True)
    if not rc: return scriptcontext.errorhandler()
    if return_points or create_points:
        outputpoints = [curve.PointAt(t) for t in rc]
        if return_points: rc = outputpoints
        if create_points:
            for point in outputpoints:
                if point.IsValid: scriptcontext.doc.Objects.AddPoint(point)
            scriptcontext.doc.Views.Redraw()
    return rc


def DivideCurveEquidistant(curve_id, distance, create_points=False, return_points=True):
    """Divides a curve such that the linear distance between the points is equal.
    Parameters:
      curve_id (guid): the object's identifier
      distance (number): linear distance between division points
      create_points (bool, optional): create the division points if True.
      return_points (bool, optional): If True, return a list of points.
                                      If False, return a list of curve parameters
    Returns:
      list(point|number, ...): points or curve parameters based on the value of return_points
      none on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve", rs.filter.curve)
      if obj:
          points = rs.DivideCurveEquidistant(obj, 4, True)
    See Also:
      DivideCurve
      DivideCurveLength
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    points = curve.DivideEquidistant(distance)
    if not points: return scriptcontext.errorhandler()
    if create_points:
        for point in points: scriptcontext.doc.Objects.AddPoint(point)
        scriptcontext.doc.Views.Redraw()
    if return_points: return points
    tvals = []
    for point in points:
        rc, t = curve.ClosestPoint(point)
        tvals.append(t)
    return tvals


def DivideCurveLength(curve_id, length, create_points=False, return_points=True):
    """Divides a curve object into segments of a specified length.
    Parameters:
      curve_id (guid): identifier of the curve object
      length (number): The length of each segment.
      create_points (bool, optional): Create the division points. If omitted or False,
          points are not created.
      return_points (bool, optional): If omitted or True, points are returned.
          If False, then a list of curve parameters are returned.
    Returns:
      list(point, ...): If return_points is not specified or True, then a list containing division points.
      list(number, ...): If return_points is False, then an array containing division curve parameters.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          length = rs.CurveLength(obj) / 4
          points = rs.DivideCurveLength(obj, length)
          for point in points: rs.AddPoint(point)
    See Also:
      DivideCurve
      DivideCurveEquidistant
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    rc = curve.DivideByLength(length, True)
    if not rc: return scriptcontext.errorhandler()
    if return_points or create_points:
        outputpoints = [curve.PointAt(t) for t in rc]
        if create_points:
            for point in outputpoints:
                if (point.IsValid): scriptcontext.doc.Objects.AddPoint(point)
        if return_points: rc = outputpoints
    return rc


def EllipseCenterPoint(curve_id):
    """Returns the center point of an elliptical-shaped curve object.
    Parameters:
      curve_id (guid): identifier of the curve object.
    Returns:
      point: The 3D center point of the ellipse if successful.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select ellipse")
      if rs.IsEllipse(obj):
          point = rs.EllipseCenterPoint(obj)
          rs.AddPoint( point )
    See Also:
      IsEllipse
      EllipseQuadPoints
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    rc, ellipse = curve.TryGetEllipse()
    if not rc: raise ValueError("curve is not an ellipse")
    return ellipse.Plane.Origin


def EllipseQuadPoints(curve_id):
    """Returns the quadrant points of an elliptical-shaped curve object.
    Parameters:
      curve_id (guid): identifier of the curve object.
    Returns:
      list(point, point, point, point): Four points identifying the quadrants of the ellipse
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select ellipse")
      if rs.IsEllipse(obj):
          rs.AddPoints( rs.EllipseQuadPoints(obj) )
    See Also:
      IsEllipse
      EllipseCenterPoint
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    rc, ellipse = curve.TryGetEllipse()
    if not rc: raise ValueError("curve is not an ellipse")
    origin = ellipse.Plane.Origin;
    xaxis = ellipse.Radius1 * ellipse.Plane.XAxis;
    yaxis = ellipse.Radius2 * ellipse.Plane.YAxis;
    return (origin-xaxis, origin+xaxis, origin-yaxis, origin+yaxis)


def EvaluateCurve(curve_id, t, segment_index=-1):
    """Evaluates a curve at a parameter and returns a 3D point
    Parameters:
      curve_id (guid): identifier of the curve object
      t (number): the parameter to evaluate
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      point: a 3-D point if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          domain = rs.CurveDomain(obj)
          t = domain[1]/2.0
          point = rs.EvaluateCurve(obj, t)
          rs.AddPoint( point )
    See Also:
      CurveClosestPoint
      IsCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    return curve.PointAt(t)


def ExplodeCurves(curve_ids, delete_input=False):
    """Explodes, or un-joins, one curves. Polycurves will be exploded into curve
    segments. Polylines will be exploded into line segments. ExplodeCurves will
    return the curves in topological order. 
    Parameters:
      curve_ids (guid): the curve object(s) to explode.
      delete_input (bool, optional): Delete input objects after exploding if True.
    Returns:
      list(guid, ...): identifying the newly created curve objects
    Example:
      import rhinoscriptsyntax as rs
      crv = rs.GetObject("Select curve to explode", rs.filter.curve)
      if rs.IsCurve(crv): rs.ExplodeCurves(crv)
    See Also:
      IsCurve
      IsPolyCurve
      IsPolyline
      JoinCurves
    """
    if( type(curve_ids) is list or type(curve_ids) is tuple ): pass
    else: curve_ids = [curve_ids]
    rc = []
    for id in curve_ids:
        curve = rhutil.coercecurve(id, -1, True)
        pieces = curve.DuplicateSegments()
        if pieces:
            for piece in pieces:
                rc.append(scriptcontext.doc.Objects.AddCurve(piece))
            if delete_input:
                id = rhutil.coerceguid(id, True)
                scriptcontext.doc.Objects.Delete(id, True)
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def ExtendCurve(curve_id, extension_type, side, boundary_object_ids):
    """Extends a non-closed curve object by a line, arc, or smooth extension
    until it intersects a collection of objects.
    Parameters:
      curve_id (guid): identifier of curve to extend
      extension_type (number):
        0 = line
        1 = arc
        2 = smooth
      side (number):
        0=extend from the start of the curve
        1=extend from the end of the curve
        2=extend from both the start and the end of the curve
      boundary_object_ids (guid): curve, surface, and polysurface objects to extend to
    Returns:
      guid: The identifier of the new object if successful.
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      filter = rs.filter.curve | rs.filter.surface | rs.filter.polysurface
      objects = rs.GetObjects("Select boundary objects", filter)
      if objects:
          curve = rs.GetObject("Select curve to extend", rs.filter.curve)
          if curve: rs.ExtendCurve( curve, 2, 1, objects )
    See Also:
      ExtendCurveLength
      ExtendCurvePoint
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if extension_type==0: extension_type = Rhino.Geometry.CurveExtensionStyle.Line
    elif extension_type==1: extension_type = Rhino.Geometry.CurveExtensionStyle.Arc
    elif extension_type==2: extension_type = Rhino.Geometry.CurveExtensionStyle.Smooth
    else: raise ValueError("extension_type must be 0, 1, or 2")
    
    if side==0: side = Rhino.Geometry.CurveEnd.Start
    elif side==1: side = Rhino.Geometry.CurveEnd.End
    elif side==2: side = Rhino.Geometry.CurveEnd.Both
    else: raise ValueError("side must be 0, 1, or 2")
    
    rhobjs = [rhutil.coercerhinoobject(id) for id in boundary_object_ids]
    if not rhobjs: raise ValueError("boundary_object_ids must contain at least one item")
    geometry = [obj.Geometry for obj in rhobjs]
    newcurve = curve.Extend(side, extension_type, geometry)
    if newcurve and newcurve.IsValid:
        curve_id = rhutil.coerceguid(curve_id, True)
        if scriptcontext.doc.Objects.Replace(curve_id, newcurve):
            scriptcontext.doc.Views.Redraw()
            return curve_id
    return scriptcontext.errorhandler()


def ExtendCurveLength(curve_id, extension_type, side, length):
    """Extends a non-closed curve by a line, arc, or smooth extension for a
    specified distance
    Parameters:
      curve_id (guid): curve to extend
      extension_type (number):
        0 = line
        1 = arc
        2 = smooth
      side (number):
        0=extend from start of the curve
        1=extend from end of the curve
        2=Extend from both ends
      length (number): distance to extend
    Returns:
      guid: The identifier of the new object
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select curve to extend", rs.filter.curve)
      if curve:
          length = rs.GetReal("Length to extend", 3.0)
          if length: rs.ExtendCurveLength( curve, 2, 2, length )
    See Also:
      ExtendCurve
      ExtendCurvePoint
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if extension_type==0: extension_type = Rhino.Geometry.CurveExtensionStyle.Line
    elif extension_type==1: extension_type = Rhino.Geometry.CurveExtensionStyle.Arc
    elif extension_type==2: extension_type = Rhino.Geometry.CurveExtensionStyle.Smooth
    else: raise ValueError("extension_type must be 0, 1, or 2")
    
    if side==0: side = Rhino.Geometry.CurveEnd.Start
    elif side==1: side = Rhino.Geometry.CurveEnd.End
    elif side==2: side = Rhino.Geometry.CurveEnd.Both
    else: raise ValueError("side must be 0, 1, or 2")
    newcurve = None
    if length<0: newcurve = curve.Trim(side, -length)
    else: newcurve = curve.Extend(side, length, extension_type)
    if newcurve and newcurve.IsValid:
        curve_id = rhutil.coerceguid(curve_id, True)
        if scriptcontext.doc.Objects.Replace(curve_id, newcurve):
            scriptcontext.doc.Views.Redraw()
            return curve_id
    return scriptcontext.errorhandler()


def ExtendCurvePoint(curve_id, side, point, extension_type=2):
    """Extends a non-closed curve by smooth extension to a point
    Parameters:
      curve_id (guid): curve to extend
      side (number):
        0=extend from start of the curve
        1=extend from end of the curve
      point (guid|point): point to extend to
      extension_type (number, optional): type of extension
        0 = Line
        1 = Arc
        2 = Smooth
    Returns:
      guid: The identifier of the new object if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select curve to extend", rs.filter.curve)
      if curve:
          point = rs.GetPoint("Point to extend to")
          if point: rs.ExtendCurvePoint(curve, 1, point)
    See Also:
      ExtendCurve
      ExtendCurveLength
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    point = rhutil.coerce3dpoint(point, True)
    
    if side==0: side = Rhino.Geometry.CurveEnd.Start
    elif side==1: side = Rhino.Geometry.CurveEnd.End
    elif side==2: side = Rhino.Geometry.CurveEnd.Both
    else: raise ValueError("side must be 0, 1, or 2")
    
    if extension_type==0: extension_type = Rhino.Geometry.CurveExtensionStyle.Line
    elif extension_type==1: extension_type = Rhino.Geometry.CurveExtensionStyle.Arc
    elif extension_type==2: extension_type = Rhino.Geometry.CurveExtensionStyle.Smooth
    else: raise ValueError("extension_type must be 0, 1, or 2")
    
    newcurve = curve.Extend(side, extension_type, point)
    if newcurve and newcurve.IsValid:
        curve_id = rhutil.coerceguid(curve_id, True)
        if scriptcontext.doc.Objects.Replace( curve_id, newcurve ):
            scriptcontext.doc.Views.Redraw()
            return curve_id
    return scriptcontext.errorhandler()


def FairCurve(curve_id, tolerance=1.0):
    """Fairs a curve. Fair works best on degree 3 (cubic) curves. Fair attempts
    to remove large curvature variations while limiting the geometry changes to
    be no more than the specified tolerance. Sometimes several applications of
    this method are necessary to remove nasty curvature problems.
    Parameters:
      curve_id (guid): curve to fair
      tolerance (number, optional): fairing tolerance
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      curves = rs.GetObjects("Select curves to fair", rs.filter.curve)
      if curves:
          [rs.FairCurve(curve) for curve in curves]
    See Also:
      
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    angle_tol = 0.0
    clamp = 0
    if curve.IsPeriodic:
        curve = curve.ToNurbsCurve()
        clamp = 1
    newcurve = curve.Fair(tolerance, angle_tol, clamp, clamp, 100)
    if not newcurve: return False
    curve_id = rhutil.coerceguid(curve_id, True)
    if scriptcontext.doc.Objects.Replace(curve_id, newcurve):
        scriptcontext.doc.Views.Redraw()
        return True
    return False


def FitCurve(curve_id, degree=3, distance_tolerance=-1, angle_tolerance=-1):
    """Reduces number of curve control points while maintaining the curve's same
    general shape. Use this function for replacing curves with many control
    points. For more information, see the Rhino help for the FitCrv command.
    Parameters:
      curve_id (guid): Identifier of the curve object
      degree (number, optional): The curve degree, which must be greater than 1.
                     The default is 3.
      distance_tolerance (number, optional): The fitting tolerance. If distance_tolerance
          is not specified or <= 0.0, the document absolute tolerance is used.
      angle_tolerance (number, optional): The kink smoothing tolerance in degrees. If
          angle_tolerance is 0.0, all kinks are smoothed. If angle_tolerance
          is > 0.0, kinks smaller than angle_tolerance are smoothed. If
          angle_tolerance is not specified or < 0.0, the document angle
          tolerance is used for the kink smoothing.
    Returns:
      guid: The identifier of the new object
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      oldCurve = rs.GetObject("Select curve to fit", rs.filter.curve)
      if oldCurve:
          newCurve = rs.FitCurve(oldCurve)
          if newCurve: rs.DeleteObject(oldCurve)
    See Also:
      
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if distance_tolerance is None or distance_tolerance<0:
        distance_tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    if angle_tolerance is None or angle_tolerance<0:
        angle_tolerance = scriptcontext.doc.ModelAngleToleranceRadians
    nc = curve.Fit(degree, distance_tolerance, angle_tolerance)
    if nc:
        rhobj = rhutil.coercerhinoobject(curve_id)
        rc = None
        if rhobj:
            rc = scriptcontext.doc.Objects.AddCurve(nc, rhobj.Attributes)
        else:
            rc = scriptcontext.doc.Objects.AddCurve(nc)
        if rc==System.Guid.Empty: raise Exception("Unable to add curve to document")
        scriptcontext.doc.Views.Redraw()
        return rc
    return scriptcontext.errorhandler()


def InsertCurveKnot(curve_id, parameter, symmetrical=False ):
    """Inserts a knot into a curve object
    Parameters:
      curve_id (guid): identifier of the curve object
      parameter (number): parameter on the curve
      symmetrical (bool, optional): if True, then knots are added on both sides of
          the center of the curve
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select curve for knot insertion", rs.filter.curve)
      if obj:
          point = rs.GetPointOnCurve(obj, "Point on curve to add knot")
          if point:
              parameter = rs.CurveClosestPoint(obj, point)
              rs.InsertCurveKnot( obj, parameter )
    See Also:
      CurveKnotCount
      CurveKnots
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if not curve.Domain.IncludesParameter(parameter): return False
    nc = curve.ToNurbsCurve()
    if not nc: return False
    rc, t = curve.GetNurbsFormParameterFromCurveParameter(parameter)
    if rc:
        rc = nc.Knots.InsertKnot(t,1)
        if rc and symmetrical:
            domain = nc.Domain
            t_sym = domain.T1 - t + domain.T0
            if abs(t_sym)>Rhino.RhinoMath.SqrtEpsilon:
                rc = nc.Knots.InsertKnot(t_sym,1)
        if rc:
            curve_id = rhutil.coerceguid(curve_id)
            rc = scriptcontext.doc.Objects.Replace(curve_id, nc)
            if rc: scriptcontext.doc.Views.Redraw()
    return rc


def IsArc(curve_id, segment_index=-1):
    """Verifies an object is an open arc curve
    Parameters:
      curve_id (guid): Identifier of the curve object
      segment_index (number): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select an arc")
      if rs.IsArc(obj):
          print("The object is an arc.")
      else:
          print("The object is not an arc.")
    See Also:
      AddArc3Pt
      ArcAngle
      ArcCenterPoint
      ArcMidPoint
      ArcRadius
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    return curve.IsArc() and not curve.IsClosed


def IsCircle(curve_id, tolerance=None):
    """Verifies an object is a circle curve
    Parameters:
      curve_id (guid): Identifier of the curve object
      tolerance (number, optional) If the curve is not a circle, then the tolerance used
        to determine whether or not the NURBS form of the curve has the
        properties of a circle. If omitted, Rhino's internal zero tolerance is used
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a circle")
      if rs.IsCircle(obj):
          print("The object is a circle.")
      else:
          print("The object is not a circle.")
    See Also:
      AddCircle
      AddCircle3Pt
      CircleCenterPoint
      CircleCircumference
      CircleRadius
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if tolerance is None or tolerance < 0:
        tolerance = Rhino.RhinoMath.ZeroTolerance
    return curve.IsCircle(tolerance)


def IsCurve(object_id):
    """Verifies an object is a curve
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      object = rs.GetObject("Select a curve")
      if rs.IsCurve(object):
          print("The object is a curve.")
      else:
          print("The object is not a curve.")
    See Also:
      IsCurveClosed
      IsCurveLinear
      IsCurvePeriodic
      IsCurvePlanar
    """
    curve = rhutil.coercecurve(object_id)
    return curve is not None


def IsCurveClosable(curve_id, tolerance=None):
    """Decide if it makes sense to close off the curve by moving the end point
    to the start point based on start-end gap size and length of curve as
    approximated by chord defined by 6 points
    Parameters:
      curve_id (guid): identifier of the curve object
      tolerance[opt] = maximum allowable distance between start point and end
        point. If omitted, the document's current absolute tolerance is used
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      crv = rs.GetObject("Select curve", rs.filter.curve)
      if not rs.IsCurveClosed(crv) and rs.IsCurveClosable(crv):
          rs.CloseCurve( crv, 0.1 )
    See Also:
      CloseCurve
      IsCurveClosed
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if tolerance is None: tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    return curve.IsClosable(tolerance)


def IsCurveClosed(object_id):
    """Verifies an object is a closed curve object
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True if successful otherwise False.  None on error
    Example:
      import rhinoscriptsyntax as rs
      object = rs.GetObject("Select a curve")
      if rs.IsCurve(object):
          if rs.IsCurveClosed(oObject):
              print("The object is a closed curve.")
          else:
              print("The object is not a closed curve.")
      else:
          print("The object is not a curve.")
    See Also:
      IsCurve
      IsCurveLinear
      IsCurvePeriodic
      IsCurvePlanar
    """
    curve = rhutil.coercecurve(object_id)
    return None if not curve else curve.IsClosed


def IsCurveInPlane(object_id, plane=None):
    """Test a curve to see if it lies in a specific plane
    Parameters:
      object_id (guid): the object's identifier
      plane (plane, optional): plane to test. If omitted, the active construction plane is used
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj) and rs.IsCurvePlanar(obj):
          if rs.IsCurveInPlane(obj):
              print("The curve lies in the current cplane.")
          else:
              print("The curve does not lie in the current cplane.")
      else:
          print("The object is not a planar curve.")
    See Also:
      IsCurve
      IsCurvePlanar
    """
    curve = rhutil.coercecurve(object_id, -1, True)
    if not plane:
        plane = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane()
    else:
        plane = rhutil.coerceplane(plane, True)
    return curve.IsInPlane(plane, scriptcontext.doc.ModelAbsoluteTolerance)


def IsCurveLinear(object_id, segment_index=-1):
    """Verifies an object is a linear curve
    Parameters:
      curve_id (guid):identifier of the curve object
      segment_index (number): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a curve")
      if rs.IsCurve(id):
          if rs.IsCurveLinear(id):
              print("The object is a linear curve.")
          else:
              print("The object is not a linear curve.")
      else:
          print("The object is not a curve.")
    See Also:
      IsCurve
      IsCurveClosed
      IsCurvePeriodic
      IsCurvePlanar
    """
    curve = rhutil.coercecurve(object_id, segment_index, True)
    return curve.IsLinear()


def IsCurvePeriodic(curve_id, segment_index=-1):
    """Verifies an object is a periodic curve object
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          if rs.IsCurvePeriodic(obj):
              print("The object is a periodic curve.")
          else:
              print("The object is not a periodic curve.")
      else:
          print("The object is not a curve.")
    See Also:
      IsCurve
      IsCurveClosed
      IsCurveLinear
      IsCurvePlanar
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    return curve.IsPeriodic


def IsCurvePlanar(curve_id, segment_index=-1):
    """Verifies an object is a planar curve
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          if rs.IsCurvePlanar(obj):
              print("The object is a planar curve.")
          else:
              print("The object is not a planar curve.")
      else:
          print("The object is not a curve.")
    See Also:
      IsCurve
      IsCurveClosed
      IsCurveLinear
      IsCurvePeriodic
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    tol = scriptcontext.doc.ModelAbsoluteTolerance
    return curve.IsPlanar(tol)


def IsCurveRational(curve_id, segment_index=-1):
    """Verifies an object is a rational NURBS curve
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          if rs.IsCurveRational(obj):
              print("The object is a rational NURBS curve.")
          else:
              print("The object is not a rational NURBS curve.")
      else:
          print("The object is not a curve.")
    See Also:
      IsCurve
      IsCurveClosed
      IsCurveLinear
      IsCurvePeriodic
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    if isinstance(curve, Rhino.Geometry.NurbsCurve): return curve.IsRational
    return False


def IsEllipse(object_id, segment_index=-1):
    """Verifies an object is an elliptical-shaped curve
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select an ellipse")
      if rs.IsEllipse(obj):
          print("The object is an ellipse.")
      else:
          print("The object is not an ellipse.")
    See Also:
      EllipseCenterPoint
      EllipseQuadPoints
    """
    curve = rhutil.coercecurve(object_id, segment_index, True)
    return curve.IsEllipse()


def IsLine(object_id, segment_index=-1):
    """Verifies an object is a line curve
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a line")
      if rs.IsLine(obj):
          print("The object is a line.")
      else:
          print("The object is not a line.")
    See Also:
      AddLine
    """
    curve = rhutil.coercecurve(object_id, segment_index, True)
    if isinstance(curve, Rhino.Geometry.LineCurve): return True
    rc, polyline = curve.TryGetPolyline()
    if rc and polyline.Count==2: return True
    return False


def IsPointOnCurve(object_id, point, segment_index=-1):
    """Verifies that a point is on a curve
    Parameters:
      curve_id (guid): identifier of the curve object
      point (point): the test point
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve")
      if rs.IsCurve(obj):
          point = rs.GetPoint("Pick a test point")
          if point:
              if rs.IsPointOnCurve(obj, point):
                  print("The point is on the curve")
              else:
                  print("The point is not on the curve")
    See Also:
      IsCurve
    """
    curve = rhutil.coercecurve(object_id, segment_index, True)
    point = rhutil.coerce3dpoint(point, True)
    rc, t = curve.ClosestPoint(point, Rhino.RhinoMath.SqrtEpsilon)
    return rc


def IsPolyCurve(object_id, segment_index=-1):
    """Verifies an object is a PolyCurve curve
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional) the curve segment index if `curve_id` identifies a polycurve
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a polycurve")
      if rs.IsPolyCurve(obj):
          print("The object is a polycurve.")
      else:
          print("The object is not a polycurve.")
    See Also:
      PolyCurveCount
    """
    curve = rhutil.coercecurve(object_id, segment_index, True)
    return isinstance(curve, Rhino.Geometry.PolyCurve)


def IsPolyline( object_id, segment_index=-1 ):
    """Verifies an object is a Polyline curve object
    Parameters:
      curve_id (guid): identifier of the curve object
      segment_index (number, optional): the curve segment index if `curve_id` identifies a polycurve
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a polyline")
      if rs.IsPolyline(obj):
          print("The object is a polyline.")
      else:
          print("The object is not a polyline.")
    See Also:
      IsPolyline
      PolylineVertices
    """
    curve = rhutil.coercecurve(object_id, segment_index, True)
    return isinstance(curve, Rhino.Geometry.PolylineCurve)


def JoinCurves(object_ids, delete_input=False, tolerance=None):
    """Joins multiple curves together to form one or more curves or polycurves
    Parameters:
      object_ids (guid): list of multiple curves
      delete_input (bool, optional): delete input objects after joining
      tolerance (number, optional): join tolerance. If omitted, 2.1 * document absolute
          tolerance is used
    Returns:
      list(guid, ...): Object id representing the new curves
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select curves to join", rs.filter.curve)
      if objs: rs.JoinCurves(objs)
    See Also:
      ExplodeCurves
      IsCurve
      IsCurveClosed
    """
    if len(object_ids)<2: raise ValueError("object_ids must contain at least 2 items")
    curves = [rhutil.coercecurve(id, -1, True) for id in object_ids]
    if tolerance is None:
        tolerance = 2.1 * scriptcontext.doc.ModelAbsoluteTolerance
    newcurves = Rhino.Geometry.Curve.JoinCurves(curves, tolerance)
    rc = []
    if newcurves:
        rc = [scriptcontext.doc.Objects.AddCurve(crv) for crv in newcurves]
    if rc and delete_input:
        for id in object_ids:
            id = rhutil.coerceguid(id, True)
            scriptcontext.doc.Objects.Delete(id, False)
    scriptcontext.doc.Views.Redraw()
    return rc


def LineFitFromPoints(points):
    """Returns a line that was fit through an array of 3D points
    Parameters:
      points ([point, point, ...]): a list of at least two 3D points
    Returns:
      line: line on success
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints()
      if points and len(points)>1:
          line=rs.LineFitFromPoints(points)
          if line: rs.AddLine(line.From, line.To)
    See Also:
      AddLine
      CurveEndPoint
      CurveStartPoint
    """
    points = rhutil.coerce3dpointlist(points, True)
    rc, line = Rhino.Geometry.Line.TryFitLineToPoints(points)
    if rc: return line
    return scriptcontext.errorhandler()


def MakeCurveNonPeriodic(curve_id, delete_input=False):
    """Makes a periodic curve non-periodic. Non-periodic curves can develop
    kinks when deformed
    Parameters:
      curve_id (guid): identifier of the curve object
      delete_input (bool): delete the input curve. If omitted, the input curve will not be deleted.
    Returns:
      guid: id of the new or modified curve if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a curve", rs.filter.curve)
      if rs.IsCurvePeriodic(curve): rs.MakeCurveNonPeriodic( curve )
    See Also:
      IsCurvePeriodic
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if not curve.IsPeriodic: return scriptcontext.errorhandler()
    nc = curve.ToNurbsCurve()
    if nc is None: return scriptcontext.errorhandler()
    nc.Knots.ClampEnd( Rhino.Geometry.CurveEnd.Both )
    rc = None
    if delete_input:
        if type(curve_id) is Rhino.DocObjects.ObjRef: pass
        else: curve_id = rhutil.coerceguid(curve_id)
        if curve_id:
            rc = scriptcontext.doc.Objects.Replace(curve_id, nc)
            if not rc: return scriptcontext.errorhandler()
            rc = rhutil.coerceguid(curve_id)
    else:
        attrs = None
        if type(scriptcontext.doc) is Rhino.RhinoDoc:
            rhobj = rhutil.coercerhinoobject(curve_id)
            if rhobj: attrs = rhobj.Attributes
        rc = scriptcontext.doc.Objects.AddCurve(nc, attrs)
        if rc==System.Guid.Empty: return scriptcontext.errorhandler()
    scriptcontext.doc.Views.Redraw()
    return rc


def MeanCurve(curve0, curve1, tolerance=None):
    """Creates an average curve from two curves
    Parameters:
      curve0, curve1 (guid): identifiers of two curves
      tolerance (number, optional): angle tolerance used to match kinks between curves
    Returns:
      guid: id of the new or modified curve if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      curve0 = rs.GetObject("Select the first curve", rs.filter.curve)
      curve1 = rs.GetObject("Select the second curve", rs.filter.curve)
      rs.MeanCurve( curve0, curve1 )
    See Also:
      UnitAngleTolerance
    """
    curve0 = rhutil.coercecurve(curve0, -1, True)
    curve1 = rhutil.coercecurve(curve1, -1, True)
    if tolerance is None: tolerance=Rhino.RhinoMath.UnsetValue
    crv = Rhino.Geometry.Curve.CreateMeanCurve(curve0,curve1,tolerance)
    if crv:
        rc = scriptcontext.doc.Objects.AddCurve(crv)
        scriptcontext.doc.Views.Redraw()
        return rc


def MeshPolyline(polyline_id):
    """Creates a polygon mesh object based on a closed polyline curve object.
    The created mesh object is added to the document
    Parameters:
      polyline_id (guid): identifier of the polyline curve object
    Returns:
      guid: identifier of the new mesh object
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      polyline = rs.GetObject("Select a polyline", rs.filter.curve)
      if polyline:
          if rs.IsPolyline(polyline) and rs.IsCurveClosed(polyline):
              rs.MeshPolyline( polyline )
    See Also:
      IsCurveClosed
      IsPolyline
    """
    curve = rhutil.coercecurve(polyline_id, -1, True)
    ispolyline, polyline = curve.TryGetPolyline()
    if not ispolyline: return scriptcontext.errorhandler()
    mesh = Rhino.Geometry.Mesh.CreateFromClosedPolyline(polyline)
    if not mesh: return scriptcontext.errorhandler()
    rc = scriptcontext.doc.Objects.AddMesh(mesh)
    scriptcontext.doc.Views.Redraw()
    return rc


def OffsetCurve(object_id, direction, distance, normal=None, style=1):
    """Offsets a curve by a distance. The offset curve will be added to Rhino
    Parameters:
      object_id (guid): identifier of a curve object
      direction (point): point describing direction of the offset
      distance (number): distance of the offset
      normal (vector, optional): normal of the plane in which the offset will occur.
          If omitted, the normal of the active construction plane will be used
      style (number, optional): the corner style. If omitted, the style is sharp.
                                0 = None
                                1 = Sharp
                                2 = Round
                                3 = Smooth
                                4 = Chamfer
    Returns:
      list(guid, ...): list of ids for the new curves on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a curve", rs.filter.curve)
      if rs.IsCurve(obj):
          rs.OffsetCurve( obj, [0,0,0], 1.0 )
    See Also:
      OffsetCurveOnSurface
      OffsetSurface
    """
    curve = rhutil.coercecurve(object_id, -1, True)
    direction = rhutil.coerce3dpoint(direction, True)
    if normal:
        normal = rhutil.coerce3dvector(normal, True)
    else:
        normal = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane().Normal
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    style = System.Enum.ToObject(Rhino.Geometry.CurveOffsetCornerStyle, style)
    curves = curve.Offset(direction, normal, distance, tolerance, style)
    if curves is None: return scriptcontext.errorhandler()
    rc = [scriptcontext.doc.Objects.AddCurve(curve) for curve in curves]
    scriptcontext.doc.Views.Redraw()
    return rc


def OffsetCurveOnSurface(curve_id, surface_id, distance_or_parameter):
    """Offset a curve on a surface. The source curve must lie on the surface.
    The offset curve or curves will be added to Rhino
    Parameters:
      curve_id, surface_id (guid): curve and surface identifiers
      distance_or_parameter (number|tuple(number, number)): If a single number is passed, then this is the
        distance of the offset. Based on the curve's direction, a positive value
        will offset to the left and a negative value will offset to the right.
        If a tuple of two values is passed, this is interpreted as the surface
        U,V parameter that the curve will be offset through
    Returns:
      list(guid, ...): identifiers of the new curves if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      def TestOffset():
          curve = rs.GetObject("Select curve on a surface", rs.filter.curve)
          if curve is None: return False
          surface = rs.GetObject("Select base surface", rs.filter.surface)
          if surface is None: return False
          point = rs.GetPointOnSurface( surface, "Through point" )
          if point is None: return False
          parameter = rs.SurfaceClosestPoint(surface, point)
          rc = rs.OffsetCurveOnSurface( curve, surface, parameter )
          return rc is not None
       
      TestOffset()
    See Also:
      OffsetCurve
      OffsetSurface
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    surface = rhutil.coercesurface(surface_id, True)
    x = None
    if type(distance_or_parameter) is list or type(distance_or_parameter) is tuple:
        x = Rhino.Geometry.Point2d( distance_or_parameter[0], distance_or_parameter[1] )
    else:
        x = float(distance_or_parameter)
    tol = scriptcontext.doc.ModelAbsoluteTolerance
    curves = curve.OffsetOnSurface(surface, x, tol)
    if curves is None: return scriptcontext.errorhandler()
    curves = [curve.ExtendOnSurface(Rhino.Geometry.CurveEnd.Both, surface) for curve in curves]
    rc = [scriptcontext.doc.Objects.AddCurve(curve) for curve in curves]
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def PlanarClosedCurveContainment(curve_a, curve_b, plane=None, tolerance=None):
    """Determines the relationship between the regions bounded by two coplanar
    simple closed curves
    Parameters:
      curve_a, curve_b (guid): identifiers of two planar, closed curves
      plane (plane, optional): test plane. If omitted, the currently active construction
        plane is used
      tolerance (number, optional): if omitted, the document absolute tolerance is used
    Returns:
      number: a number identifying the relationship if successful
        0 = the regions bounded by the curves are disjoint
        1 = the two curves intersect
        2 = the region bounded by curve_a is inside of curve_b
        3 = the region bounded by curve_b is inside of curve_a
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      curve1 = rs.GetObject("Select first curve", rs.filter.curve )
      curve2 = rs.GetObject("Select second curve", rs.filter.curve )
      if rs.IsCurvePlanar(curve1) and rs.IsCurvePlanar(curve2):
          if rs.IsCurveClosed(curve1) and rs.IsCurveClosed(curve2):
              if rs.IsCurveInPlane(curve1) and rs.IsCurveInPlane(curve2):
                  result = rs.PlanarClosedCurveContainment(curve1, curve2)
                  if result==0: print("The regions bounded by the curves are disjoint.")
                  elif result==1: print("The two curves intersect..")
                  elif result==2: print("The region bounded by Curve1 is inside of Curve2.")
                  else: print("The region bounded by Curve2 is inside of Curve1.")
    See Also:
      PlanarCurveCollision
      PointInPlanarClosedCurve
    """
    curve_a = rhutil.coercecurve(curve_a, -1, True)
    curve_b = rhutil.coercecurve(curve_b, -1, True)
    if tolerance is None or tolerance<=0:
        tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    if plane:
        plane = rhutil.coerceplane(plane)
    else:
        plane = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane()
    rc = Rhino.Geometry.Curve.PlanarClosedCurveRelationship(curve_a, curve_b, plane, tolerance)
    return int(rc)


def PlanarCurveCollision(curve_a, curve_b, plane=None, tolerance=None):
    """Determines if two coplanar curves intersect
    Parameters:
      curve_a, curve_b (guid): identifiers of two planar curves
      plane (plane, optional): test plane. If omitted, the currently active construction
        plane is used
      tolerance (number, optional): if omitted, the document absolute tolerance is used
    Returns:
      bool: True if the curves intersect; otherwise False
    Example:
      import rhinoscriptsyntax as rs
      curve1 = rs.GetObject("Select first curve")
      curve2 = rs.GetObject("Select second curve")
      if( rs.IsCurvePlanar(curve1) and rs.IsCurvePlanar(curve2) and rs.IsCurveInPlane(curve1) and rs.IsCurveInPlane(curve2) ):
          if rs.PlanarCurveCollision(curve1, curve2):
              print("The coplanar curves intersect.")
          else:
              print("The coplanar curves do not intersect.")
    See Also:
      CurveCurveIntersection
      PlanarClosedCurveContainment
      PointInPlanarClosedCurve
    """
    curve_a = rhutil.coercecurve(curve_a, -1, True)
    curve_b = rhutil.coercecurve(curve_b, -1, True)
    if tolerance is None or tolerance<=0:
        tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    if plane:
        plane = rhutil.coerceplane(plane)
    else:
        plane = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane()
    return Rhino.Geometry.Curve.PlanarCurveCollision(curve_a, curve_b, plane, tolerance)


def PointInPlanarClosedCurve(point, curve, plane=None, tolerance=None):
    """Determines if a point is inside of a closed curve, on a closed curve, or
    outside of a closed curve
    Parameters:
      point (point|guid): text point
      curve (guid): identifier of a curve object
      plane (plane, optional): plane containing the closed curve and point. If omitted,
          the currently active construction plane is used
      tolerance (number, optional) it omitted, the document abosulte tolerance is used
    Returns:
      number: number identifying the result if successful
              0 = point is outside of the curve
              1 = point is inside of the curve
              2 = point in on the curve
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a planar, closed curve", rs.filter.curve)
      if rs.IsCurveClosed(curve) and rs.IsCurvePlanar(curve):
          point = rs.GetPoint("Pick a point")
          if point:
              result = rs.PointInPlanarClosedCurve(point, curve)
              if result==0: print("The point is outside of the closed curve.")
              elif result==1: print("The point is inside of the closed curve.")
              else: print("The point is on the closed curve.")
    See Also:
      PlanarClosedCurveContainment
      PlanarCurveCollision
    """
    point = rhutil.coerce3dpoint(point, True)
    curve = rhutil.coercecurve(curve, -1, True)
    if tolerance is None or tolerance<=0:
        tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    if plane:
        plane = rhutil.coerceplane(plane)
    else:
        plane = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane()
    rc = curve.Contains(point, plane, tolerance)
    if rc==Rhino.Geometry.PointContainment.Unset: raise Exception("Curve.Contains returned Unset")
    if rc==Rhino.Geometry.PointContainment.Outside: return 0
    if rc==Rhino.Geometry.PointContainment.Inside: return 1
    return 2


def PolyCurveCount(curve_id, segment_index=-1):
    """Returns the number of curve segments that make up a polycurve
    Parameters:
      curve_id (guid): the object's identifier
      segment_index (number, optional): if `curve_id` identifies a polycurve object, then `segment_index` identifies the curve segment of the polycurve to query.
    Returns:
      number: the number of curve segments in a polycurve if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a polycurve")
      if rs.IsPolyCurve(obj):
          count = rs.PolyCurveCount(obj)
          if count: print("The polycurve contains {} curves".format(count))
    See Also:
      IsPolyCurve
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    if isinstance(curve, Rhino.Geometry.PolyCurve): return curve.SegmentCount
    raise ValueError("curve_id does not reference a polycurve")


def PolylineVertices(curve_id, segment_index=-1):
    """Returns the vertices of a polyline curve on success
    Parameters:
      curve_id (guid): the object's identifier
      segment_index (number, optional): if curve_id identifies a polycurve object, then segment_index identifies the curve segment of the polycurve to query.
    Returns:
      list(point, ...): an list of Point3d vertex points if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a polyline")
      if rs.IsPolyline(obj):
          points = rs.PolylineVertices(obj)
          if points:
              for point in points: rs.AddPoint(point)
    See Also:
      AddPolyline
      IsPolyline
    """
    curve = rhutil.coercecurve(curve_id, segment_index, True)
    rc, polyline = curve.TryGetPolyline()
    if rc: return [pt for pt in polyline]
    raise ValueError("curve_id does not reference a polyline")


def ProjectCurveToMesh(curve_ids, mesh_ids, direction):
    """Projects one or more curves onto one or more surfaces or meshes
    Parameters:
      curve_ids ([guid, ...]): identifiers of curves to project
      mesh_ids ([guid, ...]): identifiers of meshes to project onto
      direction (vector): projection direction
    Returns:
      list(guid, ...): list of identifiers for the resulting curves.
    Example:
      import rhinoscriptsyntax as rs
      mesh = rs.GetObject("Select mesh to project onto", rs.filter.mesh)
      curve= rs.GetObject("Select curve to project", rs.filter.curve)
      #Project down...
      results = rs.ProjectCurveToMesh(curve, mesh, (0,0,-1))
    See Also:
      ProjectCurveToSurface
      ProjectPointToMesh
      ProjectPointToSurface
    """
    curve_ids = rhutil.coerceguidlist(curve_ids)
    mesh_ids = rhutil.coerceguidlist(mesh_ids)
    direction = rhutil.coerce3dvector(direction, True)
    curves = [rhutil.coercecurve(id, -1, True) for id in curve_ids]
    meshes = [rhutil.coercemesh(id, True) for id in mesh_ids]
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    newcurves = Rhino.Geometry.Curve.ProjectToMesh(curves, meshes, direction, tolerance)
    ids = [scriptcontext.doc.Objects.AddCurve(curve) for curve in newcurves]
    if ids: scriptcontext.doc.Views.Redraw()
    return ids


def ProjectCurveToSurface(curve_ids, surface_ids, direction):
    """Projects one or more curves onto one or more surfaces or polysurfaces
    Parameters:
      curve_ids ([guid, ...]): identifiers of curves to project
      surface_ids ([guid, ...]): identifiers of surfaces to project onto
      direction (vector): projection direction
    Returns:
      list(guid, ...): list of identifiers
    Example:
      import rhinoscriptsyntax as rs
      surface = rs.GetObject("Select surface to project onto", rs.filter.surface)
      curve = rs.GetObject("Select curve to project", rs.filter.curve)
      # Project down...
      results = rs.ProjectCurveToSurface(curve, surface, (0,0,-1))
    See Also:
      ProjectCurveToMesh
      ProjectPointToMesh
      ProjectPointToSurface
    """
    curve_ids = rhutil.coerceguidlist(curve_ids)
    surface_ids = rhutil.coerceguidlist(surface_ids)
    direction = rhutil.coerce3dvector(direction, True)
    curves = [rhutil.coercecurve(id, -1, True) for id in curve_ids]
    breps = [rhutil.coercebrep(id, True) for id in surface_ids]
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    newcurves = Rhino.Geometry.Curve.ProjectToBrep(curves, breps, direction, tolerance)
    ids = [scriptcontext.doc.Objects.AddCurve(curve) for curve in newcurves]
    if ids: scriptcontext.doc.Views.Redraw()
    return ids


def RebuildCurve(curve_id, degree=3, point_count=10):
    """Rebuilds a curve to a given degree and control point count. For more
    information, see the Rhino help for the Rebuild command.
    Parameters:
      curve_id (guid): identifier of the curve object
      degree (number, optional): new degree (must be greater than 0)
      point_count (number, optional) new point count, which must be bigger than degree.
    Returns:
      bool: True of False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select curve to rebuild", rs.filter.curve)
      if curve: rs.RebuildCurve(curve, 3, 10)
    See Also:
      RebuildSurface
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if degree<1: raise ValueError("degree must be greater than 0")
    newcurve = curve.Rebuild(point_count, degree, False)
    if not newcurve: return False
    scriptcontext.doc.Objects.Replace(curve_id, newcurve)
    scriptcontext.doc.Views.Redraw()
    return True


def RemoveCurveKnot(curve, parameter):
    """Deletes a knot from a curve object.
    Parameters:
      curve (guid): The reference of the source object
      parameter (number): The parameter on the curve. Note, if the parameter is not equal to one
                      of the existing knots, then the knot closest to the specified parameter
                      will be removed.
    Returns:
      bool: True of False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs

      crv_info = rs.GetCurveObject("Select curve near knot to be removed")
      if crv_info:
          crv_id = crv_info[0]
          crv_param = crv_info[4]
          rs.RemoveCurveKnot(crv_id, crv_param)
    See Also:
      RemoveSurfaceKnot
    """
    curve_inst = rhutil.coercecurve(curve, -1, True)
    success, n_param = curve_inst.GetCurveParameterFromNurbsFormParameter(parameter)
    if not success: return False
    n_curve = curve_inst.ToNurbsCurve()
    if not n_curve: return False
    success = n_curve.Knots.RemoveKnotAt(n_param)
    if not success: return False
    scriptcontext.doc.Objects.Replace(curve, n_curve)
    scriptcontext.doc.Views.Redraw()
    return True


def ReverseCurve(curve_id):
    """Reverses the direction of a curve object. Same as Rhino's Dir command
    Parameters:
      curve_id (guid): identifier of the curve object
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a curve to reverse")
      if rs.IsCurve(curve): rs.ReverseCurve(curve)
    See Also:
      CurveDirectionsMatch
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if curve.Reverse():
        curve_id = rhutil.coerceguid(curve_id, True)
        scriptcontext.doc.Objects.Replace(curve_id, curve)
        return True
    return False


def SimplifyCurve(curve_id, flags=0):
    """Replace a curve with a geometrically equivalent polycurve.
    
    The polycurve will have the following properties:
     - All the polycurve segments are lines, polylines, arcs, or NURBS curves.
     - The NURBS curves segments do not have fully multiple interior knots.
     - Rational NURBS curves do not have constant weights.
     - Any segment for which IsCurveLinear or IsArc is True is a line, polyline segment, or an arc.
     - Adjacent co-linear or co-circular segments are combined.
     - Segments that meet with G1-continuity have there ends tuned up so that they meet with G1-continuity to within machine precision.
     - If the polycurve is a polyline, a polyline will be created


    Parameters:
      curve_id (guid): the object's identifier
      flags (number, optional): the simplification methods to use. By default, all methods are used (flags = 0)
        Value Description
        0     Use all methods.
        1     Do not split NURBS curves at fully multiple knots.
        2     Do not replace segments with IsCurveLinear = True with line curves.
        4     Do not replace segments with IsArc = True with arc curves.
        8     Do not replace rational NURBS curves with constant denominator with an equivalent non-rational NURBS curve.
        16    Do not adjust curves at G1-joins.
        32    Do not merge adjacent co-linear lines or co-circular arcs or combine consecutive line segments into a polyline.

    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a curve to simplify", rs.filter.curve)
      if curve: rs.SimplifyCurve(curve)
    See Also:
      IsArc
      IsCurveLinear
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    _flags = Rhino.Geometry.CurveSimplifyOptions.All
    if( flags&1 ==1 ): _flags &= (~Rhino.Geometry.CurveSimplifyOptions.SplitAtFullyMultipleKnots)
    if( flags&2 ==2 ): _flags &= (~Rhino.Geometry.CurveSimplifyOptions.RebuildLines)
    if( flags&4 ==4 ): _flags &= (~Rhino.Geometry.CurveSimplifyOptions.RebuildArcs)
    if( flags&8 ==8 ): _flags &= (~Rhino.Geometry.CurveSimplifyOptions.RebuildRationals)
    if( flags&16==16 ): _flags &= (~Rhino.Geometry.CurveSimplifyOptions.AdjustG1)
    if( flags&32==32 ): _flags &= (~Rhino.Geometry.CurveSimplifyOptions.Merge)
    tol = scriptcontext.doc.ModelAbsoluteTolerance
    ang_tol = scriptcontext.doc.ModelAngleToleranceRadians
    newcurve = curve.Simplify(_flags, tol, ang_tol)
    if newcurve:
        curve_id = rhutil.coerceguid(curve_id, True)
        scriptcontext.doc.Objects.Replace(curve_id, newcurve)
        scriptcontext.doc.Views.Redraw()
        return True
    return False


def SplitCurve(curve_id, parameter, delete_input=True):
    """Splits, or divides, a curve at a specified parameter. The parameter must
    be in the interior of the curve's domain
    Parameters:
      curve_id (guid): the curve to split
      parameter ({number, ...]) one or more parameters to split the curve at
      delete_input (bool, optional): delete the input curve
    Returns:
      list(guid, ....): list of new curves on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a curve to split", rs.filter.curve)
      if rs.IsCurve(curve):
          domain = rs.CurveDomain(curve)
          parameter = domain[1] / 2.0
          rs.SplitCurve( curve, parameter )
    See Also:
      TrimCurve
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    newcurves = curve.Split(parameter)
    if newcurves is None: return scriptcontext.errorhandler()
    att = None
    rhobj = rhutil.coercerhinoobject(curve_id)
    if rhobj: att = rhobj.Attributes
    rc = [scriptcontext.doc.Objects.AddCurve(crv, att) for crv in newcurves]
    if rc and delete_input:
        id = rhutil.coerceguid(curve_id, True)
        scriptcontext.doc.Objects.Delete(id, True)
    scriptcontext.doc.Views.Redraw()
    return rc


def TrimCurve(curve_id, interval, delete_input=True):
    """Trims a curve by removing portions of the curve outside a specified interval
    Parameters:
      curve_id (guid):the curve to trim
      interval ([number, number]): two numbers identifying the interval to keep. Portions of
        the curve before domain[0] and after domain[1] will be removed. If the
        input curve is open, the interval must be increasing. If the input
        curve is closed and the interval is decreasing, then the portion of
        the curve across the start and end of the curve is returned
      delete_input (bool): delete the input curve. If omitted the input curve is deleted.
    Returns:
      list(guid, ...): identifier of the new curve on success
      None: on failure
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a curve to trim", rs.filter.curve)
      if rs.IsCurve(curve):
          domain = rs.CurveDomain(curve)
          domain[1] /= 2.0
          rs.TrimCurve( curve, domain )
    See Also:
      SplitCurve
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    if interval[0]==interval[1]: raise ValueError("interval values are equal")
    newcurve = curve.Trim(interval[0], interval[1])
    if not newcurve: return scriptcontext.errorhandler()
    att = None
    rhobj = rhutil.coercerhinoobject(curve_id)
    if rhobj: att = rhobj.Attributes
    rc = scriptcontext.doc.Objects.AddCurve(newcurve, att)
    if delete_input:
        id = rhutil.coerceguid(curve_id, True)
        scriptcontext.doc.Objects.Delete(id, True)
    scriptcontext.doc.Views.Redraw()
    return rc


def ChangeCurveDegree(object_id, degree):
    """Changes the degree of a curve object. For more information see the Rhino help file for the ChangeDegree command.
      Parameters:
        object_id (guid): the object's identifier.
        degree (number): the new degree.
      Returns:
        bool: True of False indicating success or failure.
        None: on failure
      Example:
    
      See Also:
        IsCurve
        CurveDegree
    """ 
    curve = rhutil.coercerhinoobject(object_id)
    if not curve: return None
    if not isinstance(curve, Rhino.DocObjects.CurveObject): return None

    curve = curve.CurveGeometry
    if not isinstance(curve, Rhino.Geometry.NurbsCurve):
        curve = curve.ToNurbsCurve()

    max_nurbs_degree = 11
    if degree < 1 or degree > max_nurbs_degree or curve.Degree == degree:
        return None

    r = False
    if curve.IncreaseDegree(degree):
        r = scriptcontext.doc.Objects.Replace(object_id, curve)
    return r


def AddTweenCurves(from_curve_id, to_curve_id, number_of_curves = 1, method = 0, sample_number = 10):
    """Creates curves between two open or closed input curves.
    Parameters:
      from_curve_id (guid): identifier of the first curve object.
      to_curve_id (guid): identifier of the second curve object.
      number_of_curves (number): The number of curves to create. The default is 1.
      method (number): The method for refining the output curves, where:
        0: (Default) Uses the control points of the curves for matching. So the first control point of first curve is matched to first control point of the second curve.
        1: Refits the output curves like using the FitCurve method.  Both the input curve and the output curve will have the same structure. The resulting curves are usually more complex than input unless input curves are compatible.
        2: Input curves are divided to the specified number of points on the curve, corresponding points define new points that output curves go through. If you are making one tween curve, the method essentially does the following: divides the two curves into an equal number of points, finds the midpoint between the corresponding points on the curves, and interpolates the tween curve through those points.
      sample_number (number): The number of samples points to use if method is 2. The default is 10.
    Returns:
      list(guid, ...): The identifiers of the new tween objects if successful, None on error.
    Example:
      import rhinoscriptsyntax as rs
      curveA = rs.GetObject("Select first curve", rs.filter.curve)
      curveB = rs.GetObject("Select second curve", rs.filter.curve)
      arrResult = rs.AddTweenCurves(curveA, curveB, 6, 2, 30)
    """
    curve0 = rhutil.coercecurve(from_curve_id, -1, True)
    curve1 = rhutil.coercecurve(to_curve_id, -1, True)
    out_curves = 0
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    if method == 0:
        out_curves = Rhino.Geometry.Curve.CreateTweenCurves(curve0, curve1, number_of_curves, tolerance)
    elif method == 1:
        out_curves = Rhino.Geometry.Curve.CreateTweenCurvesWithMatching(curve0, curve1, number_of_curves, tolerance)
    elif method == 2:
        out_curves = Rhino.Geometry.Curve.CreateTweenCurvesWithSampling(curve0, curve1, number_of_curves, sample_number, tolerance)
    else: raise ValueError("method must be 0, 1, or 2")
    curves = None
    if out_curves:
        curves = []
        for curve in out_curves:
            if curve and curve.IsValid:
                rc = scriptcontext.doc.Objects.AddCurve(curve)
            curve.Dispose()
            if rc==System.Guid.Empty: raise Exception("unable to add curve to document")
            curves.append(rc)
        scriptcontext.doc.Views.Redraw()
    return curves
