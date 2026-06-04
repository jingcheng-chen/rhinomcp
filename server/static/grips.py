import Rhino

import scriptcontext

import rhinocompat as compat
from rhinoscript import utility as rhutil


def __neighborgrip(i, object_id, index, direction, enable):
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    grips = rhobj.GetGrips()
    if not grips or len(grips)<=index: return scriptcontext.errorhandler()
    grip = grips[index]
    next_grip=None
    if direction==0:
        next_grip = grip.NeighborGrip(i,0,0,False)
    else:
        next_grip = grip.NeighborGrip(0,i,0,False)
    if next_grip and enable:
        next_grip.Select(True)
        scriptcontext.doc.Views.Redraw()
    return next_grip


def EnableObjectGrips(object_id, enable=True):
    """Enables or disables an object's grips. For curves and surfaces, these are
    also called control points.
    Parameters:
      object_id (guid): identifier of the object
      enable (bool, optional): if True, the specified object's grips will be turned on.
        Otherwise, they will be turned off
    Returns:
      bool: True on success, False on failure
    Example:
      import rhinoscriptsyntax as  rs
      objects = rs.GetObjects("Select  objects")
      if objects: [rs.EnableObjectGrips(obj)  for obj in objs]
    See Also:
      ObjectGripCount
      ObjectGripsOn
      ObjectGripsSelected
      SelectObjectGrips
      UnselectObjectGrips
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    if enable!=rhobj.GripsOn:
        rhobj.GripsOn = enable
        scriptcontext.doc.Views.Redraw()


def GetObjectGrip(message=None, preselect=False, select=False):
    """Prompts the user to pick a single object grip
    Parameters:
      message (str, optional): prompt for picking
      preselect (bool, optional): allow for selection of pre-selected object grip.
      select (bool, optional): select the picked object grip.
    Returns:
      tuple(guid, number, point): defining a grip record.
         [0] = identifier of the object that owns the grip
         [1] = index value of the grip
         [2] = location of the grip
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select a curve", rs.filter.curve)
      if curve:
          rs.EnableObjectGrips( curve )
          grip = rs.GetObjectGrip("Select a curve grip")
          if grip: print(grip[2])
    See Also:
      GetObjectGrips
    """
    if not preselect:
        scriptcontext.doc.Objects.UnselectAll()
        scriptcontext.doc.Views.Redraw()
    rc, grip = Rhino.Input.RhinoGet.GetGrip(message)
    if rc!=Rhino.Commands.Result.Success: return scriptcontext.errorhandler()
    if select:
        grip.Select(True, True)
        scriptcontext.doc.Views.Redraw()
    return grip.OwnerId, grip.Index, grip.CurrentLocation


def GetObjectGrips(message=None, preselect=False, select=False):
    """Prompts user to pick one or more object grips from one or more objects.
    Parameters:
      message (str, optional): prompt for picking
      preselect (bool, optional): allow for selection of pre-selected object grips
      select (bool, optional) select the picked object grips
    Returns:
      list((guid, number, point), ...): containing one or more grip records. Each grip record is a tuple
        [n][0] = identifier of the object that owns the grip
        [n][1] = index value of the grip
        [n][2] = location of the grip
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      curves = rs.GetObjects("Select curves", rs.filter.curves)
      if curves:
          for curve in curves: rs.EnableObjectGrips(curve)
          grips = rs.GetObjectGrips("Select curve grips")
          if grips: for grip in grips: print(grip[0])
    See Also:
      GetObjectGrip
    """
    if not preselect:
        scriptcontext.doc.Objects.UnselectAll()
        scriptcontext.doc.Views.Redraw()
    getrc, grips = Rhino.Input.RhinoGet.GetGrips(message)
    if getrc!=Rhino.Commands.Result.Success or not grips:
        return scriptcontext.errorhandler()
    rc = []
    for grip in grips:
        id = grip.OwnerId
        index = grip.Index
        location = grip.CurrentLocation
        rc.append((id, index, location))
        if select: grip.Select(True, True)
    if select: scriptcontext.doc.Views.Redraw()
    return rc


def NextObjectGrip(object_id, index, direction=0, enable=True):
    """Returns the next grip index from a specified grip index of an object
    Parameters:
      object_id (guid): identifier of the object
      index (number): zero based grip index from which to get the next grip index
      direction ([number, number], optional): direction to get the next grip index (0=U, 1=V)
      enable (bool, optional): if True, the next grip index found will be selected
    Returns:
      number: index of the next grip on success
      None: on failure
    Example:
      import rhinoscriptsyntax as rs
      object_id = rs.GetObject("Select curve", rs.filter.curve)
      if object_id:
          rs.EnableObjectGrips( object_id )
          count = rs.ObjectGripCount( object_id )
          for i in range(0,count,2):
              rs.NextObjectGrip(object_id, i, 0, True)
    See Also:
      EnableObjectGrips
      PrevObjectGrip
    """
    return __neighborgrip(1, object_id, index, direction, enable)


def ObjectGripCount(object_id):
    """Returns number of grips owned by an object
    Parameters:
      object_id (guid): identifier of the object
    Returns:
      number: number of grips if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if rs.ObjectGripsOn(obj):
          print("Grip count ={}".format(rs.ObjectGripCount(obj)))
    See Also:
      EnableObjectGrips
      ObjectGripsOn
      ObjectGripsSelected
      SelectObjectGrips
      UnselectObjectGrips
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    grips = rhobj.GetGrips()
    if not grips: return scriptcontext.errorhandler()
    return grips.Length


def ObjectGripLocation(object_id, index, point=None):
    """Returns or modifies the location of an object's grip
    Parameters:
      object_id (guid) identifier of the object
      index (number): index of the grip to either query or modify
      point (point, optional): 3D point defining new location of the grip
    Returns:
      point: if point is not specified, the current location of the grip referenced by index
      point: if point is specified, the previous location of the grip referenced by index
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select curve", rs.filter.curve)
      if obj:
          rs.EnableObjectGrips(obj)
          point = rs.ObjectGripLocation(obj, 0)
          point[0] = point[0] + 1.0
          point[1] = point[1] + 1.0
          point[2] = point[2] + 1.0
          rs.ObjectGripLocation(obj, 0, point)
          rs.EnableObjectGrips(obj, False)
    See Also:
      EnableObjectGrips
      ObjectGripLocations
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    if not rhobj.GripsOn: return scriptcontext.errorhandler()
    grips = rhobj.GetGrips()
    if not grips or index<0 or index>=grips.Length:
        return scriptcontext.errorhandler()
    grip = grips[index]
    rc = grip.CurrentLocation
    if point:
        grip.CurrentLocation = rhutil.coerce3dpoint(point, True)
        scriptcontext.doc.Objects.GripUpdate(rhobj, True)
        scriptcontext.doc.Views.Redraw()
    return rc


def ObjectGripLocations(object_id, points=None):
    """Returns or modifies the location of all grips owned by an object. The
    locations of the grips are returned in a list of Point3d with each position
    in the list corresponding to that grip's index. To modify the locations of
    the grips, you must provide a list of points that contain the same number
    of points at grips
    Parameters:
      object_id (guid): identifier of the object
      points ([point, ...], optional) list of 3D points identifying the new grip locations
    Returns:
      list(point, ...): if points is not specified, the current location of all grips
      list(point, ...): if points is specified, the previous location of all grips
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select curve", rs.filter.curve)
      if obj:
          rs.EnableObjectGrips( obj )
          points = rs.ObjectGripLocations(obj)
          for point in points:  print(point)
    See Also:
      EnableObjectGrips
      ObjectGripCount
      ObjectGripLocation
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    if not rhobj.GripsOn: return scriptcontext.errorhandler()
    grips = rhobj.GetGrips()
    if grips is None: return scriptcontext.errorhandler()
    rc = [grip.CurrentLocation for grip in grips]
    if points and len(points)==len(grips):
        points = rhutil.coerce3dpointlist(points, True)
        for i, grip in enumerate(grips):
            point = points[i]
            grip.CurrentLocation = point
        scriptcontext.doc.Objects.GripUpdate(rhobj, True)
        scriptcontext.doc.Views.Redraw()
    return rc


def ObjectGripsOn(object_id):
    """Verifies that an object's grips are turned on
    Parameters:
      object_id (guid): identifier of the object
    Returns:
      bool: True or False indicating Grips state
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if rs.ObjectGripsOn(obj):
          print("Grip count = {}".format(rs.ObjectGripCount(obj)))
    See Also:
      EnableObjectGrips
      ObjectGripCount
      ObjectGripsSelected
      SelectObjectGrips
      UnselectObjectGrips
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.GripsOn


def ObjectGripsSelected(object_id):
    """Verifies that an object's grips are turned on and at least one grip
    is selected
    Parameters:
      object_id (guid): identifier of the object
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if rs.ObjectGripsSelected(obj):
          rs.UnselectObjectGrips( obj )
    See Also:
      EnableObjectGrips
      ObjectGripCount
      ObjectGripsOn
      SelectObjectGrips
      UnselectObjectGrips
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    if not rhobj.GripsOn: return False
    grips = rhobj.GetGrips()
    if grips is None: return False
    for grip in grips:
        if grip.IsSelected(False): return True
    return False


def PrevObjectGrip(object_id, index, direction=0, enable=True):
    """Returns the previous grip index from a specified grip index of an object
    Parameters:
      object_id (guid): identifier of the object
      index (number): zero based grip index from which to get the previous grip index
      direction ([number, number], optional): direction to get the next grip index (0=U, 1=V)
      enable (bool, optional): if True, the next grip index found will be selected
    Returns:
      number: index of the next grip on success
      None: on failure
    Example:
      import rhinoscriptsyntax as rs
      object_id = rs.GetObject("Select curve", rs.filter.curve)
      if object_id:
          rs.EnableObjectGrips(object_id)
          count = rs.ObjectGripCount(object_id)
          for i in range(count-1, 0, -2):
              rs.PrevObjectGrip(object_id, i, 0, True)
    See Also:
      EnableObjectGrips
      NextObjectGrip
    """
    return __neighborgrip(-1, object_id, index, direction, enable)


def SelectedObjectGrips(object_id):
    """Returns a list of grip indices indentifying an object's selected grips
    Parameters:
      object_id (guid): identifier of the object
    Returns:
      list(number): list of indices on success
      None: on failure or if no grips are selected
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select curve", rs.filter.curve)
      if obj:
          rs.EnableObjectGrips( obj )
          count = rs.ObjectGripCount( obj )
          for i in range(0,count,2):
              rs.SelectObjectGrip( obj, i )
          grips = rs.SelectedObjectGrips(obj)
          if grips: print(len(grips{}).format("grips selected"))
    See Also:
      EnableObjectGrips
      SelectObjectGrip
      SelectObjectGrips
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    if not rhobj.GripsOn: return None
    grips = rhobj.GetGrips()
    rc = []
    if grips:
        for i in compat.RANGE(grips.Length):
            if grips[i].IsSelected(False): rc.append(i)
    return rc


def SelectObjectGrip(object_id, index):
    """Selects a single grip owned by an object. If the object's grips are
    not turned on, the grips will not be selected
    Parameters:
      object_id (guid) identifier of the object
      index (number): index of the grip to select
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select curve", rs.filter.curve)
      if obj:
          rs.EnableObjectGrips( obj )
          count = rs.ObjectGripCount( obj )
          for i in range(0,count,2): rs.SelectObjectGrip(obj,i)
    See Also:
      EnableObjectGrips
      ObjectGripCount
      SelectObjectGrips
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    if not rhobj.GripsOn: return False
    grips = rhobj.GetGrips()
    if grips is None: return False
    if index<0 or index>=grips.Length: return False
    grip = grips[index]
    if grip.Select(True,True)>0:
        scriptcontext.doc.Views.Redraw()
        return True
    return False


def SelectObjectGrips(object_id):
    """Selects an object's grips. If the object's grips are not turned on,
    they will not be selected
    Parameters:
      object_id (guid): identifier of the object
    Returns:
      number: Number of grips selected on success
      None: on failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if rs.ObjectGripsSelected(obj)==False:
          rs.SelectObjectGrips( obj )
    See Also:
      EnableObjectGrips
      ObjectGripCount
      SelectObjectGrip
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    if not rhobj.GripsOn: return scriptcontext.errorhandler()
    grips = rhobj.GetGrips()
    if grips is None: return scriptcontext.errorhandler()
    count = 0
    for grip in grips:
        if grip.Select(True,True)>0: count+=1
    if count>0:
        scriptcontext.doc.Views.Redraw()
        return count
    return scriptcontext.errorhandler()


def UnselectObjectGrip(object_id, index):
    """Unselects a single grip owned by an object. If the object's grips are
    not turned on, the grips will not be unselected
    Parameters:
      object_id (guid): identifier of the object
      index (number): index of the grip to unselect
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select curve", rs.filter.curve)
      if obj:
          rs.EnableObjectGrips( obj )
          count = rs.ObjectGripCount(obj)
          for i in range(0,count,2):
              rs.UnselectObjectGrip( obj, i )
    See Also:
      EnableObjectGrips
      ObjectGripCount
      UnselectObjectGrips
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    if not rhobj.GripsOn: return False
    grips = rhobj.GetGrips()
    if grips is None: return False
    if index<0 or index>=grips.Length: return False
    grip = grips[index]
    if grip.Select(False)==0:
        scriptcontext.doc.Views.Redraw()
        return True
    return False


def UnselectObjectGrips(object_id):
    """Unselects an object's grips. Note, the grips will not be turned off.
    Parameters:
      object_id (guid): identifier of the object
    Returns:
      number: Number of grips unselected on success
      None: on failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if rs.ObjectGripsSelected(obj): rs.UnselectObjectGrips(obj)
    See Also:
      EnableObjectGrips
      ObjectGripCount
      UnselectObjectGrip
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    if not rhobj.GripsOn: return scriptcontext.errorhandler()
    grips = rhobj.GetGrips()
    if grips is None: return scriptcontext.errorhandler()
    count = 0
    for grip in grips:
        if grip.Select(False)==0: count += 1
    if count>0:
        scriptcontext.doc.Views.Redraw()
        return count
    return scriptcontext.errorhandler()
