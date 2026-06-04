import math

import System

import Rhino

import scriptcontext

from rhinoscript import utility as rhutil


def __viewhelper(view):
    if view is None: return scriptcontext.doc.Views.ActiveView
    allviews = scriptcontext.doc.Views.GetViewList(True, True)
    view_id = rhutil.coerceguid(view, False)
    for item in allviews:
        if view_id:
            if item.MainViewport.Id == view_id: return item
        elif item.MainViewport.Name == view:
            return item
    raise ValueError("unable to coerce %s into a view"%view)


def AddDetail(layout_id, corner1, corner2, title=None, projection=1):
    """Add new detail view to an existing layout view
    Parameters:
      layout_id (guid): identifier of an existing layout
      corner1, corner2 (point): 2d corners of the detail in the layout's unit system
      title (str, optional): title of the new detail
      projection (number, optional): type of initial view projection for the detail
          1 = parallel top view
          2 = parallel bottom view
          3 = parallel left view
          4 = parallel right view
          5 = parallel front view
          6 = parallel back view
          7 = perspective view
    Returns:
      guid: identifier of the newly created detail on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      layout = rs.AddLayout("Portrait", (8.5,11))
      if layout:
          rs.AddDetail(layout, (0.5,0.5), (8,10.5), None, 7)
    See Also:
      DeleteNamedView
      NamedViews
      RestoreNamedView
    """
    layout_id = rhutil.coerceguid(layout_id, True)
    corner1 = rhutil.coerce2dpoint(corner1, True)
    corner2 = rhutil.coerce2dpoint(corner2, True)
    if projection<1 or projection>7: raise ValueError("projection must be a value between 1-7")
    layout = scriptcontext.doc.Views.Find(layout_id)
    if not layout: raise ValueError("no layout found for given layout_id")
    projection = System.Enum.ToObject(Rhino.Display.DefinedViewportProjection, projection)
    detail = layout.AddDetailView(title, corner1, corner2, projection)
    if not detail: return scriptcontext.errorhandler()
    scriptcontext.doc.Views.Redraw()
    return detail.Id


def AddLayout(title=None, size=None):
    """Adds a new page layout view
    Parameters:
      title (str, optional): title of new layout
      size ([number, number], optional): width and height of paper for the new layout
    Returns:
      guid: id of new layout
    Example:
      import rhinoscriptsyntax as rs
      rs.AddLayout("Portrait")
    See Also:
      DeleteNamedView
      NamedViews
      RestoreNamedView
    """
    page = None
    if size is None: page = scriptcontext.doc.Views.AddPageView(title)
    else: page = scriptcontext.doc.Views.AddPageView(title, size[0], size[1])
    if page: return page.MainViewport.Id


def AddNamedCPlane(cplane_name, view=None):
    """Adds new named construction plane to the document
    Parameters:
      cplane_name (str): the name of the new named construction plane
      view (guid|str): Title or identifier of the view from which to save
               the construction plane. If omitted, the current active view is used.
    Returns:
      atr: name of the newly created construction plane if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      views = rs.ViewNames()
      if views:
          for view in views:
              name = view + "_cplane"
              rs.AddNamedCPlane( name, view )
    See Also:
      DeleteNamedCPlane
      NamedCPlane
      NamedCPlanes
      RestoreNamedCPlane
    """
    view = __viewhelper(view)
    if not cplane_name: raise ValueError("cplane_name is empty")
    plane = view.MainViewport.ConstructionPlane()
    index = scriptcontext.doc.NamedConstructionPlanes.Add(cplane_name, plane)
    if index<0: return scriptcontext.errorhandler()
    return cplane_name


def AddNamedView(name, view=None):
    """Adds a new named view to the document
    Parameters:
      name (str): the name of the new named view
      view: (guid|str): the title or identifier of the view to save. If omitted, the current
            active view is saved
    Returns:
      str: name fo the newly created named view if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      views = rs.ViewNames()
      if views:
          for view in views:
              name = view + "_view"
              rs.AddNamedView( name, view )
    See Also:
      DeleteNamedView
      NamedViews
      RestoreNamedView
    """
    view = __viewhelper(view)
    if not name: raise ValueError("name is empty")
    viewportId = view.MainViewport.Id
    index = scriptcontext.doc.NamedViews.Add(name, viewportId)
    if index<0: return scriptcontext.errorhandler()
    return name


def CurrentDetail(layout, detail=None, return_name=True):
    """Returns or changes the current detail view in a page layout view
    Parameters:
      layout (str|guid): title or identifier of an existing page layout view
      detail (str|guid, optional): title or identifier the the detail view to set
      return_name (bool, optional): return title if True, else return identifier
    Returns:
      str: if detail is not specified, the title or id of the current detail view
      str: if detail is specified, the title or id of the previous detail view
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      layout = rs.CurrentView(return_name=False)
      if rs.IsLayout(layout):
          rs.CurrentDetail( layout, layout )
    See Also:
      IsDetail
      IsLayout
    """
    layout_id = rhutil.coerceguid(layout)
    page = None
    if layout_id is None: page = scriptcontext.doc.Views.Find(layout, False)
    else: page = scriptcontext.doc.Views.Find(layout_id)
    if page is None: return scriptcontext.errorhandler()
    rc = None
    active_viewport = page.ActiveViewport
    if return_name: rc = active_viewport.Name
    else: rc = active_viewport.Id
    if detail:
        id = rhutil.coerceguid(detail)
        if( (id and id==page.MainViewport.Id) or (id is None and detail==page.MainViewport.Name) ):
            page.SetPageAsActive()
        else:
            if id: page.SetActiveDetail(id)
            else: page.SetActiveDetail(detail, False)
    scriptcontext.doc.Views.Redraw()
    return rc


def CurrentView(view=None, return_name=True):
    """Returns or sets the currently active view
    Parameters:
      view (str|guid): Title or id of the view to set current.
        If omitted, only the title or identifier of the current view is returned
      return_name (bool, optional): If True, then the name, or title, of the view is returned.
        If False, then the identifier of the view is returned
    Returns:
      str: if the title is not specified, the title or id of the current view
      str: if the title is specified, the title or id of the previous current view
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      previous = rs.CurrentView("Perspective")
      print("The previous current view was {}".format(previous))
      viewId = rs.CurrentView( return_name=False )
      print("The identifier of the current view is {}".format(viewId))
    See Also:
      IsViewCurrent
      ViewNames
    """
    rc = None
    if return_name: rc = scriptcontext.doc.Views.ActiveView.MainViewport.Name
    else: rc = scriptcontext.doc.Views.ActiveView.MainViewport.Id
    if view:
        id = rhutil.coerceguid(view)
        rhview = None
        if id: rhview = scriptcontext.doc.Views.Find(id)
        else: rhview = scriptcontext.doc.Views.Find(view, False)
        if rhview is None: return scriptcontext.errorhandler()
        scriptcontext.doc.Views.ActiveView = rhview
    return rc


def DeleteNamedCPlane(name):
    """Removes a named construction plane from the document
    Parameters:
      name (str): name of the construction plane to remove
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      cplanes = rs.NamedCplanes()
      if cplanes:
          for cplane in cplanes: rs.DeleteNamedCPlane(cplane)
    See Also:
      AddNamedCPlane
      NamedCPlane
      NamedCPlanes
      RestoreNamedCPlane
    """
    return scriptcontext.doc.NamedConstructionPlanes.Delete(name)


def DeleteNamedView(name):
    """Removes a named view from the document
    Parameters:
      name (str): name of the named view to remove
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      views = rs.NamedViews()
      if views:
          for view in views: rs.DeleteNamedView(view)
    See Also:
      AddNamedView
      NamedViews
      RestoreNamedView
    """
    return scriptcontext.doc.NamedViews.Delete(name)


def DetailLock(detail_id, lock=None):
    """Returns or modifies the projection locked state of a detail
    Parameters:
      detail_id (guid): identifier of a detail object
      lock (bool, optional) the new lock state
    Returns:
      bool: if lock==None, the current detail projection locked state
      bool: if lock is True or False, the previous detail projection locked state
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      detail = rs.GetObject("select a detail", rs.filter.detail)
      if detail: rs.DetailLock(detail,True)
    See Also:
      IsDetail
      IsLayout
    """
    detail_id = rhutil.coerceguid(detail_id, True)
    detail = scriptcontext.doc.Objects.Find(detail_id)
    if not detail: return scriptcontext.errorhandler()
    rc = detail.DetailGeometry.IsProjectionLocked
    if lock is not None and lock!=rc:
        detail.DetailGeometry.IsProjectionLocked = lock
        detail.CommitChanges()
    return rc


def DetailScale(detail_id, model_length=None, page_length=None):
    """Returns or modifies the scale of a detail object
    Parameters:
      detail_id (guid): identifier of a detail object
      model_length (number, optional): a length in the current model units
      page_length (number, optional): a length in the current page units
    Returns:
      number: current page to model scale ratio if model_length and page_length are both None
      number: previous page to model scale ratio if model_length and page_length are values
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      detail = rs.GetObject("select a detail", rs.filter.detail)
      if detail: rs.DetailScale(detail,1,1)
    See Also:
      IsDetail
      IsLayout
    """
    detail_id = rhutil.coerceguid(detail_id, True)
    detail = scriptcontext.doc.Objects.Find(detail_id)
    if detail is None: return scriptcontext.errorhandler()
    rc = detail.DetailGeometry.PageToModelRatio
    if model_length or page_length:
        if model_length is None or page_length is None:
            return scriptcontext.errorhandler()
        model_units = scriptcontext.doc.ModelUnitSystem
        page_units = scriptcontext.doc.PageUnitSystem
        if detail.DetailGeometry.SetScale(model_length, model_units, page_length, page_units):
            detail.CommitChanges()
            scriptcontext.doc.Views.Redraw()
    return rc


def IsDetail(layout, detail):
    """Verifies that a detail view exists on a page layout view
    Parameters:
      layout (str|guid): title or identifier of an existing page layout
      detail (str|guid): title or identifier of an existing detail view
    Returns:
      bool: True if detail is a detail view
      bool: False if detail is not a detail view
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      if rs.IsLayout(view):
          isdetail = rs.IsDetail(view, "Top")
          if isdetail:
              print("Top is a detail view.")
          else:
              print("Top is not a detail view.")
    See Also:
      IsLayout
      CurrentDetail
    """
    layout_id = rhutil.coerceguid(layout)
    views = scriptcontext.doc.Views.GetViewList(False, True)
    found_layout = None
    for view in views:
        if layout_id:
            if view.MainViewport.Id==layout_id:
                found_layout = view
                break
        elif view.MainViewport.Name==layout:
            found_layout = view
            break
    # if we couldn't find a layout, this is an error
    if found_layout is None: return scriptcontext.errorhandler()
    detail_id = rhutil.coerceguid(detail)
    details = view.GetDetailViews()
    if not details: return False
    for detail_view in details:
        if detail_id:
            if detail_view.Id==detail_id: return True
        else:
            if detail_view.Name==detail: return True
    return False


def IsLayout(layout):
    """Verifies that a view is a page layout view
    Parameters:
      layout (guid|str): title or identifier of an existing page layout view
    Returns:
      bool: True if layout is a page layout view
      bool: False is layout is a standard, model view
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      if rs.IsLayout(view):
          print("The current view is a page layout view.")
      else:
          print("The current view is standard, model view.")
    See Also:
      IsLayout
      CurrentDetail
    """
    layout_id = rhutil.coerceguid(layout)
    alllayouts = scriptcontext.doc.Views.GetViewList(False, True)
    for layoutview in alllayouts:
        if layout_id:
            if layoutview.MainViewport.Id==layout_id: return True
        elif layoutview.MainViewport.Name==layout: return True
    allmodelviews = scriptcontext.doc.Views.GetViewList(True, False)
    for modelview in allmodelviews:
        if layout_id:
          if modelview.MainViewport.Id==layout_id: return False
        elif modelview.MainViewport.Name==layout: return False
    return scriptcontext.errorhandler()


def IsView(view):
    """Verifies that the specified view exists
    Parameters:
      view (str|guid): title or identifier of the view
    Returns:
      bool: True of False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      title = "Perspective"
      result = rs.IsView(title)
      if result:
          print("The {} view exists.".format(title))
      else:
          print("The {} view does not exist.".format(title))
    See Also:
      ViewNames
    """
    view_id = rhutil.coerceguid(view)
    if view_id is None and view is None: return False
    allviews = scriptcontext.doc.Views.GetViewList(True, True)
    for item in allviews:
        if view_id:
            if item.MainViewport.Id==view_id: return True
        elif item.MainViewport.Name==view: return True
    return False


def IsViewCurrent(view):
    """Verifies that the specified view is the current, or active view
    Parameters:
      view (str|guid): title or identifier of the view
    Returns:
      bool: True of False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      title = "Perspective"
      result = rs.IsViewCurrent(title)
      if result:
          print("The {} view is current".format(title))
      else:
          print("The {} view is not current".format(title))
    See Also:
      CurrentView
    """
    activeview = scriptcontext.doc.Views.ActiveView
    view_id = rhutil.coerceguid(view)
    if view_id: return view_id==activeview.MainViewport.Id
    return view==activeview.MainViewport.Name


def IsViewMaximized(view=None):
    """Verifies that the specified view is maximized (enlarged so as to fill
    the entire Rhino window)
    Parameters:
      view: (str|guid): title or identifier of the view. If omitted, the current
            view is used
    Returns:
      bool: True of False
    Example:
      import rhinoscriptsyntax as rs
      title = rs.CurrentView()
      result = rs.IsViewMaximized(title)
      if result:
          print("The {} view is maximized".format(title))
      else:
          print("The {} view is not maximized".format(title))
    See Also:
      MaximizeRestoreView
    """
    view = __viewhelper(view)
    return view.Maximized


def IsViewPerspective(view):
    """Verifies that the specified view's projection is set to perspective
    Parameters:
      view (str|guid): title or identifier of the view
    Returns:
      bool: True of False
    Example:
      import rhinoscriptsyntax as rs
      title = rs.CurrentView()
      result = rs.IsViewPerspective(title)
      if result:
          print("The {} view is set to perspective projection".format(title))
      else:
          print("The {} view is set to parallel projection".format(title))
    See Also:
      ViewProjection
    """
    view = __viewhelper(view)
    return view.MainViewport.IsPerspectiveProjection


def IsViewTitleVisible(view=None):
    """Verifies that the specified view's title window is visible
    Parameters:
      view: (str|guid, optional): The title or identifier of the view. If omitted, the current
            active view is used
    Returns:
      bool: True of False
    Example:
      import rhinoscriptsyntax as rs
      title = rs.CurrentView()
      vis = rs.IsViewTitleVisible(title)
      if vis:
          print("The {} view's title is visible".format(title))
      else:
          print("The {} view's title is not visible".format(title))
    See Also:
      ShowViewTitle
    """
    view = __viewhelper(view)
    return view.MainViewport.TitleVisible


def IsWallpaper(view):
    """Verifies that the specified view contains a wallpaper image
    Parameters:
      view (str|guid): view to verify
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      filename = rs.OpenFileName()
      if filename and not rs.IsWallpaper(view):
          rs.Wallpaper(view, filename)
    See Also:
      Wallpaper
    """
    view = __viewhelper(view)
    return len(view.MainViewport.WallpaperFilename)>0


def MaximizeRestoreView(view=None):
    """Toggles a view's maximized/restore window state of the specified view
    Parameters:
      view: (str|guid, optional): the title or identifier of the view. If omitted, the current
            active view is used
    Returns:
      None
    Example:
      import rhinoscriptsyntax as rs
      title = rs.CurrentView()
      if rs.IsViewMaximized(title):
          rs.MaximizeRestoreView( title )
    See Also:
      IsViewMaximized
    """
    view = __viewhelper(view)
    view.Maximized = not view.Maximized


def NamedCPlane(name):
    """Returns the plane geometry of the specified named construction plane
    Parameters:
      name (str): the name of the construction plane
    Returns:
      plane: a plane on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      names = rs.NamedCPlanes()
      if names:
          for name in names:
              plane = rs.NamedCPlane(name)
              print("CPlane name:" + name)
              print("CPlane origin:" + plane.Origin)
              print("CPlane x-axis:" + plane.Xaxis)
              print("CPlane y-axis:" + plane.Yaxis)
              print("CPlane z-axis:" + plane.Zaxis)
    See Also:
      AddNamedCPlane
      DeleteNamedCPlane
      NamedCPlanes
      RestoreNamedCPlane
    """
    index = scriptcontext.doc.NamedConstructionPlanes.Find(name)
    if index<0: return scriptcontext.errorhandler()
    return scriptcontext.doc.NamedConstructionPlanes[index].Plane


def NamedCPlanes():
    """Returns the names of all named construction planes in the document
    Returns:
      list(str, ...): the names of all named construction planes in the document
    Example:
      import rhinoscriptsyntax as rs
      cplanes = rs.NamedCPlanes()
      if cplanes:
          for cplane in cplanes: print(cplane)
    See Also:
      AddNamedCPlane
      DeleteNamedCPlane
      NamedCPlane
      RestoreNamedCPlane
    """
    count = scriptcontext.doc.NamedConstructionPlanes.Count
    rc = [scriptcontext.doc.NamedConstructionPlanes[i].Name for i in range(count)]
    return rc


def NamedViews():
    """Returns the names of all named views in the document
    Returns:
      list(str, ...): the names of all named views in the document
    Example:
      import rhinoscriptsyntax as rs
      views = rs.NamedViews()
      if views:
          for view in views: print(view)
    See Also:
      AddNamedView
      DeleteNamedView
      RestoreNamedView
    """
    count = scriptcontext.doc.NamedViews.Count
    return [scriptcontext.doc.NamedViews[i].Name for i in range(count)]


def RenameView(old_title, new_title):
    """Changes the title of the specified view
    Parameters:
      old_title (str|guid): the title or identifier of the view to rename
      new_title (str): the new title of the view
    Returns:
      str: the view's previous title if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      oldtitle = rs.CurrentView()
      rs.renameview( oldtitle, "Current" )
    See Also:
      ViewNames
    """
    if not old_title or not new_title: return scriptcontext.errorhandler()
    old_id = rhutil.coerceguid(old_title)
    foundview = None
    allviews = scriptcontext.doc.Views.GetViewList(True, True)
    for view in allviews:
        if old_id:
            if view.MainViewport.Id==old_id:
                foundview = view
                break
        elif view.MainViewport.Name==old_title:
            foundview = view
            break
    if foundview is None: return scriptcontext.errorhandler()
    old_title = foundview.MainViewport.Name
    foundview.MainViewport.Name = new_title
    return old_title


def RestoreNamedCPlane(cplane_name, view=None):
    """Restores a named construction plane to the specified view.
    Parameters:
      cplane_name (str): name of the construction plane to restore
      view: (str|guid, optional): the title or identifier of the view. If omitted, the current
            active view is used
    Returns:
      str: name of the restored named construction plane if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      cplanes = rs.NamedCplanes()
      if cplanes: rs.RestoreNamedCPlane( cplanes[0] )
    See Also:
      AddNamedCPlane
      DeleteNamedCPlane
      NamedCPlane
      NamedCPlanes
    """
    view = __viewhelper(view)
    index = scriptcontext.doc.NamedConstructionPlanes.Find(cplane_name)
    if index<0: return scriptcontext.errorhandler()
    cplane = scriptcontext.doc.NamedConstructionPlanes[index]
    view.MainViewport.PushConstructionPlane(cplane)
    view.Redraw()
    return cplane_name


def RestoreNamedView(named_view, view=None, restore_bitmap=False):
    """Restores a named view to the specified view
    Parameters:
      named_view (str): name of the named view to restore
      view (str|guid, optional):  title or id of the view to restore the named view.
           If omitted, the current active view is used
      restore_bitmap: (bool, optional): restore the named view's background bitmap
    Returns:
      str: name of the restored view if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      views = rs.NamedViews()
      if views: rs.RestoreNamedView(views[0])
    See Also:
      AddNamedView
      DeleteNamedView
      NamedViews
    """
    view = __viewhelper(view)
    index = scriptcontext.doc.NamedViews.FindByName(named_view)
    if index<0: return scriptcontext.errorhandler()
    viewinfo = scriptcontext.doc.NamedViews[index]
    if view.MainViewport.PushViewInfo(viewinfo, restore_bitmap):
        view.Redraw()
        return view.MainViewport.Name
    return scriptcontext.errorhandler()


def RotateCamera(view=None, direction=0, angle=None):
    """Rotates a perspective-projection view's camera. See the RotateCamera
    command in the Rhino help file for more details
    Parameters:
      view (str|guid, optional):  title or id of the view. If omitted, current active view is used
      direction(number, optional): the direction to rotate the camera where
        0=right
        1=left
        2=down
        3=up
      angle: (number, optional): the angle to rotate. If omitted, the angle of rotation
            is specified by the "Increment in divisions of a circle" parameter
            specified in Options command's View tab
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      rs.RotateCamera( angle=15 )
    See Also:
      RotateView
      TiltView
    """
    view = __viewhelper(view)
    viewport = view.ActiveViewport
    if angle is None:
        angle = 2.0*math.pi/Rhino.ApplicationSettings.ViewSettings.RotateCircleIncrement
    else:
        angle = Rhino.RhinoMath.ToRadians( abs(angle) )
    target_distance = (viewport.CameraLocation-viewport.CameraTarget)*viewport.CameraZ
    axis = viewport.CameraY
    if direction==0 or direction==2: angle=-angle
    if direction==0 or direction==1:
        if Rhino.ApplicationSettings.ViewSettings.RotateToView:
            axis = viewport.CameraY
        else:
            axis = Rhino.Geometry.Vector3d.ZAxis
    elif direction==2 or direction==3:
        axis = viewport.CameraX
    else:
        return False
    if Rhino.ApplicationSettings.ViewSettings.RotateReverseKeyboard: angle=-angle
    rot = Rhino.Geometry.Transform.Rotation(angle, axis, Rhino.Geometry.Point3d.Origin)
    camUp = rot * viewport.CameraY
    camDir = -(rot * viewport.CameraZ)
    target = viewport.CameraLocation + target_distance*camDir
    viewport.SetCameraLocations(target, viewport.CameraLocation)
    viewport.CameraUp = camUp
    view.Redraw()
    return True


def RotateView(view=None, direction=0, angle=None):
    """Rotates a view. See RotateView command in Rhino help for more information
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, the current active view is used
      direction (number, optional): the direction to rotate the view where
            0=right
            1=left
            2=down
            3=up
      angle (number): angle to rotate. If omitted, the angle of rotation is specified
            by the "Increment in divisions of a circle" parameter specified in
            Options command's View tab
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      rs.RotateView( angle=90.0 )
    See Also:
      RotateCamera
      TiltView
    """
    view = __viewhelper(view)
    viewport = view.ActiveViewport
    if angle is None:
        angle = 2.0*math.pi/Rhino.ApplicationSettings.ViewSettings.RotateCircleIncrement
    else:
        angle = Rhino.RhinoMath.ToRadians( abs(angle) )
    if Rhino.ApplicationSettings.ViewSettings.RotateReverseKeyboard: angle = -angle
    if direction==0: viewport.KeyboardRotate(True, angle)
    elif direction==1: viewport.KeyboardRotate(True, -angle)
    elif direction==2: viewport.KeyboardRotate(False, -angle)
    elif direction==3: viewport.KeyboardRotate(False, angle)
    else: return False
    view.Redraw()
    return True


def ShowGrid(view=None, show=None):
    """Shows or hides a view's construction plane grid
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, the current active view is used
      show (bool, optional): The grid state to set. If omitted, the current grid display state is returned
    Returns:
      bool: If show is not specified, then the grid display state if successful
      bool: If show is specified, then the previous grid display state if successful
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      if rs.ShowGrid(view)==False:
          rs.ShowGrid( view, True )
    See Also:
      ShowGridAxes
      ShowWorldAxes
    """
    view = __viewhelper(view)
    viewport = view.ActiveViewport
    rc = viewport.ConstructionGridVisible
    if show is not None and rc!=show:
        viewport.ConstructionGridVisible = show
        view.Redraw()
    return rc


def ShowGridAxes(view=None, show=None):
    """Shows or hides a view's construction plane grid axes.
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, the current active view is used
      show (bool, optional): The state to set. If omitted, the current grid axes display state is returned
    Returns:
      bool: If show is not specified, then the grid axes display state
      bool: If show is specified, then the previous grid axes display state
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      if rs.ShowGridAxes(view)==False:
          rs.ShowGridAxes( view, True )
    See Also:
      ShowGrid
      ShowWorldAxes
    """
    view = __viewhelper(view)
    viewport = view.ActiveViewport
    rc = viewport.ConstructionAxesVisible
    if show is not None and rc!=show:
        viewport.ConstructionAxesVisible = show
        view.Redraw()
    return rc


def ShowViewTitle(view=None, show=True):
    """Shows or hides the title window of a view
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, the current active view is used
      show (bool, optional): The state to set.
    Returns:
      None
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      if rs.IsViewTitleVisible(view)==False:
          rs.ShowViewTitle( view, True )
    See Also:
      IsViewTitleVisible
    """
    view = __viewhelper(view)
    if view is None: return scriptcontext.errorhandler()
    view.TitleVisible = show


def ShowWorldAxes(view=None, show=None):
    """Shows or hides a view's world axis icon
    Parameters:
      view (str|guid, optional):  title or id of the view. If omitted, the current active view is used
      show: (bool, optional): The state to set.
    Returns:
      bool: If show is not specified, then the world axes display state
      bool: If show is specified, then the previous world axes display state
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      if rs.ShowWorldAxes(view)==False:
          rs.ShowWorldAxes( view, True )
    See Also:
      ShowGrid
      ShowGridAxes
    """
    view = __viewhelper(view)
    viewport = view.ActiveViewport
    rc = viewport.WorldAxesVisible
    if show is not None and rc!=show:
        viewport.WorldAxesVisible = show
        view.Redraw()
    return rc


def TiltView(view=None, direction=0, angle=None):
    """Tilts a view by rotating the camera up vector. See the TiltView command in
    the Rhino help file for more details.
    Parameters:
      view (str|guid, optional):  title or id of the view. If omitted, the current active view is used
      direction (number, optional): the direction to rotate the view where
        0=right
        1=left
      angle (number, optional): the angle to rotate. If omitted, the angle of rotation is
        specified by the "Increment in divisions of a circle" parameter specified
        in Options command's View tab
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      rs.TiltView( angle=15 )
    See Also:
      RotateCamera
    """
    view = __viewhelper(view)
    viewport = view.ActiveViewport
    if angle is None:
        angle = 2.0*math.pi/Rhino.ApplicationSettings.ViewSettings.RotateCircleIncrement
    else:
        angle = Rhino.RhinoMath.ToRadians( abs(angle) )
    
    if Rhino.ApplicationSettings.ViewSettings.RotateReverseKeyboard: angle = -angle
    axis = viewport.CameraLocation - viewport.CameraTarget
    if direction==0: viewport.Rotate(angle, axis, viewport.CameraLocation)
    elif direction==1: viewport.Rotate(-angle, axis, viewport.CameraLocation)
    else: return False
    view.Redraw()
    return True


def ViewCamera(view=None, camera_location=None):
    """Returns or sets the camera location of the specified view
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, the current active view is used
      camera_location (point, optional): a 3D point identifying the new camera location.
        If omitted, the current camera location is returned
    Returns:
      point: If camera_location is not specified, the current camera location
      point: If camera_location is specified, the previous camera location
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      camera = rs.GetPoint("Select new camera location")
      if camera: rs.ViewCamera(view,camera)
    See Also:
      ViewCameraTarget
      ViewTarget
    """
    view = __viewhelper(view)
    rc = view.ActiveViewport.CameraLocation
    if camera_location is None: return rc
    camera_location = rhutil.coerce3dpoint(camera_location)
    if camera_location is None: return scriptcontext.errorhandler()
    view.ActiveViewport.SetCameraLocation(camera_location, True)
    view.Redraw()
    return rc


def ViewCameraLens(view=None, length=None):
    """Returns or sets the 35mm camera lens length of the specified perspective
    projection view.
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, the current active view is used
      length (number, optional): the new 35mm camera lens length. If omitted, the previous
        35mm camera lens length is returned
    Returns:
      number: If lens length is not specified, the current lens length
      number: If lens length is specified, the previous lens length
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      if rs.IsViewPerspective(view):
          length = rs.ViewCameraLens(view, 100)
    See Also:
      ViewCameraTarget
      ViewCPlane
      ViewDisplayModes
      ViewProjection
      ViewSize
    """
    view = __viewhelper(view)
    rc = view.ActiveViewport.Camera35mmLensLength
    if not length: return rc
    view.ActiveViewport.Camera35mmLensLength = length
    view.Redraw()
    return rc


def ViewCameraPlane(view=None):
    """Returns the orientation of a view's camera.
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, the current active view is used
    Returns:
      plane: the view's camera plane if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      target = rs.ViewTarget(view)
      camplane = rs.ViewCameraPlane(view)
      plane = rs.MovePlane(camplane, target)
      rs.ViewCPlane( view, plane )
    See Also:
      ViewCamera
      ViewTarget
    """
    view = __viewhelper(view)
    rc, frame = view.ActiveViewport.GetCameraFrame()
    if not rc: return scriptcontext.errorhandler()
    return frame


def ViewCameraTarget(view=None, camera=None, target=None):
    """Returns or sets the camera and target positions of the specified view
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, current active view is used
      camera (point): 3d point identifying the new camera location. If camera and
         target are not specified, current camera and target locations are returned
      target (point): 3d point identifying the new target location. If camera and
         target are not specified, current camera and target locations are returned
    Returns:
      list(point, point): if both camera and target are not specified, then the 3d points containing
        the current camera and target locations is returned
      point: if either camera or target are specified, then the 3d points containing the
        previous camera and target locations is returned
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      camera = rs.GetPoint("Select new camera location")
      target = rs.GetPoint("Select new target location")
      if camera and target:
          rs.ViewCameraTarget( view, camera, target )
    See Also:
      ViewCamera
      ViewTarget
    """
    view = __viewhelper(view)
    rc = view.ActiveViewport.CameraLocation, view.ActiveViewport.CameraTarget
    if not camera and not target: return rc
    if camera: camera = rhutil.coerce3dpoint(camera, True)
    if target: target = rhutil.coerce3dpoint(target, True)
    if camera and target: view.ActiveViewport.SetCameraLocations(target, camera)
    elif camera is None: view.ActiveViewport.SetCameraTarget(target, True)
    else: view.ActiveViewport.SetCameraLocation(camera, True)
    view.Redraw()
    return rc


def ViewCameraUp(view=None, up_vector=None):
    """Returns or sets the camera up direction of a specified
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, the current active view is used
      up_vector (vector): 3D vector identifying the new camera up direction
    Returns:
      vector: if up_vector is not specified, then the current camera up direction
      vector: if up_vector is specified, then the previous camera up direction
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      upVector = rs.ViewCameraUp(view)
      print(up_vector)
    See Also:
      ViewCamera
      ViewTarget
    """
    view = __viewhelper(view)
    rc = view.ActiveViewport.CameraUp
    if up_vector:
        view.ActiveViewport.CameraUp = rhutil.coerce3dvector(up_vector, True)
        view.Redraw()
    return rc


def ViewCPlane(view=None, plane=None):
    """Return or set a view's construction plane
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, current active view is used.
      plane (plane): the new construction plane if setting
    Returns:
      plane: If a construction plane is not specified, the current construction plane
      plane: If a construction plane is specified, the previous construction plane
    Example:
      import rhinoscriptsyntax as rs
      origin = rs.GetPoint("CPlane origin")
      if origin:
          plane = rs.ViewCPlane()
          plane = rs.MovePlane(plane,origin)
          rs.ViewCPlane(None, plane)
    See Also:
      ViewCameraLens
      ViewCameraTarget
      ViewDisplayModes
      ViewProjection
      ViewSize
    """
    view = __viewhelper(view)
    cplane = view.ActiveViewport.ConstructionPlane()
    if plane:
        plane = rhutil.coerceplane(plane, True)
        view.ActiveViewport.SetConstructionPlane(plane)
        view.Redraw()
    return cplane


def ViewDisplayMode(view=None, mode=None, return_name=True):
    """Return or set a view display mode
    Parameters:
      view (str|guid, optional): Title or id of a view. If omitted, active view is used
      mode (str|guid, optional): Name or id of a display mode
      return_name (bool, optional): If true, return display mode name. If False, display mode id
    Returns:
      str: If mode is specified, the previous mode
      str: If mode is not specified, the current mode
    Example:
      import rhinoscriptsyntax as rs
      views = rs.ViewNames()
      for view in views:
          rs.ViewDisplayMode(view, 'Ghosted')
    See Also:
      CurrentView
      ViewNames
    """
    view = __viewhelper(view)
    current = view.ActiveViewport.DisplayMode
    if return_name: rc = current.EnglishName
    else: rc = current.Id
    if mode:
        mode_id = rhutil.coerceguid(mode)
        if mode_id:
            desc = Rhino.Display.DisplayModeDescription.GetDisplayMode(mode_id)
        else:
            desc = Rhino.Display.DisplayModeDescription.FindByName(mode)
        if desc: view.ActiveViewport.DisplayMode = desc
        scriptcontext.doc.Views.Redraw()
    return rc


def ViewDisplayModeId(name):
    """Return id of a display mode given it's name
    Parameters:
      name (str): name of the display mode
    Returns:
      guid: The id of the display mode if successful, otherwise None
    Example:
      import rhinoscriptsyntax as rs
      modes = rs.ViewDisplayModes(True)
      for mode in modes: print("{} = {}".format(mode, rs.ViewDisplayModeId(mode)))
    See Also:
      ViewDisplayMode
      ViewDisplayModes
    """
    desc = Rhino.Display.DisplayModeDescription.FindByName(name)
    if desc: return desc.Id


def ViewDisplayModeName(mode_id):
    """Return name of a display mode given it's id
    Parameters:
      mode_id (guid): The identifier of the display mode obtained from the ViewDisplayModes method.
    Returns:
      str: The name of the display mode if successful, otherwise None
    Example:
      import rhinoscriptsyntax as rs
      modes = rs.ViewDisplayModes(False)
      for mode in modes: print("{} = {}".format(mode, rs.ViewDisplayModeName(mode)))
    See Also:
      ViewDisplayMode
      ViewDisplayModes
    """
    mode_id = rhutil.coerceguid(mode_id, True)
    desc = Rhino.Display.DisplayModeDescription.GetDisplayMode(mode_id)
    if desc: return desc.EnglishName


def ViewDisplayModes(return_names=True):
    """Return list of display modes
    Parameters:
      return_name (bool, otpional): If True, return mode names. If False, return ids
    Returns:
      list(str|guid, ...): strings identifying the display mode names or identifiers if successful
    Example:
      import rhinoscriptsyntax as rs
      modes = rs.ViewDisplayModes(False)
      for mode in modes: print("{} = {}".format(mode, rs.ViewDisplayModeName(mode)))
    See Also:
      ViewDisplayMode
      ViewDisplayModeName
    """
    modes = Rhino.Display.DisplayModeDescription.GetDisplayModes()
    if return_names:
        return [mode.EnglishName for mode in modes]
    return [mode.Id for mode in modes]


def ViewNames(return_names=True, view_type=0):
    """Return the names, titles, or identifiers of all views in the document
    Parameters:
      return_names (bool, optional): if True then the names of the views are returned.
        If False, then the identifiers of the views are returned
      view_type: (number, optional): the type of view to return
                       0 = standard model views
                       1 = page layout views
                       2 = both standard and page layout views
    Returns:
      list(str|guid, ...): of the view names or identifiers on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      # Print view names
      views = rs.ViewNames()
      if views:
          for view in views: print(view)
      # Print view identifiers
      view_ids = rs.ViewNames(False)
      if view_ids:
          for id in view_ids:
              print("{} = {}".format(id, rs.ViewTitle(id)))
    See Also:
      IsView
      ViewTitle
    """
    views = scriptcontext.doc.Views.GetViewList(view_type!=1, view_type>0)
    if views is None: return scriptcontext.errorhandler()
    if return_names: return [view.MainViewport.Name for view in views]
    return [view.MainViewport.Id for view in views]


def ViewNearCorners(view=None):
    """Return 3d corners of a view's near clipping plane rectangle. Useful
    in determining the "real world" size of a parallel-projected view
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, current active view is used
    Returns:
      list(point, point, point, point): Four Point3d that define the corners of the rectangle (counter-clockwise order)
    Example:
      import rhinoscriptsyntax as rs
      rect = rs.ViewNearCorners()
      if rect:
          for i in range(4): rs.AddTextDot( i, rect[i] )
    See Also:
      CurrentView
    """
    view = __viewhelper(view)
    rc = view.ActiveViewport.GetNearRect()
    return rc[0], rc[1], rc[3], rc[2]


def ViewProjection(view=None, mode=None):
    """Return or set a view's projection mode.
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, current active view is used
      mode (number, optional): the projection mode
        1 = parallel
        2 = perspective
        3 = two point perspective
    Returns:
      number: if mode is not specified, the current projection mode for the specified view
      number: if mode is specified, the previous projection mode for the specified view
    Example:
      import rhinoscriptsyntax as rs
      views = rs.ViewNames()
      if views:
          for view in views: rs.ViewProjection(view,1)
    See Also:
      IsViewPerspective
    """
    view = __viewhelper(view)
    viewport = view.ActiveViewport
    rc = 2
    if viewport.IsParallelProjection: rc = 1
    elif viewport.IsTwoPointPerspectiveProjection: rc = 3
    if mode is None or mode==rc: return rc
    if mode==1: viewport.ChangeToParallelProjection(True)
    elif mode==2: viewport.ChangeToPerspectiveProjection(True, 50)
    elif mode==3: viewport.ChangeToTwoPointPerspectiveProjection(50)
    else: return
    view.Redraw()
    return rc


def ViewRadius(view=None, radius=None, mode=False):
    """Returns or sets the radius of a parallel-projected view. Useful
    when you need an absolute zoom factor for a parallel-projected view
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, current active view is used
      radius (number): the view radius
      mode (bool, optional): perform a "dolly" magnification by moving the camera
        towards/away from the target so that the amount of the screen 
        subtended by an object changes.  true = perform a "zoom" 
        magnification by adjusting the "lens" angle
    Returns:
      number: if radius is not specified, the current view radius for the specified view
      number: if radius is specified, the previous view radius for the specified view
    Example:
      import rhinoscriptsyntax as rs
      rhParallelView = 1
      views = rs.ViewNames()
      if views:
          for view in views:
              if rs.ViewProjection(view)==rhParallelView:
                  rs.ViewRadius(view, 10.0)
    See Also:
      IsViewPerspective
      ViewProjection
    """
    view = __viewhelper(view)
    viewport = view.ActiveViewport
    if not viewport.IsParallelProjection: return scriptcontext.errorhandler()
    fr = viewport.GetFrustum()
    frus_right = fr[2]
    frus_top = fr[4]
    old_radius = min(frus_top, frus_right)
    if radius is None: return old_radius
    magnification_factor = radius / old_radius
    d = 1.0 / magnification_factor
    viewport.Magnify(d, mode)
    view.Redraw()
    return old_radius


def ViewSize(view=None):
    """Returns the width and height in pixels of the specified view
    Parameters:
      view (str|guid): title or id of the view. If omitted, current active view is used
    Returns:
      tuple(number, number): of two numbers identifying width and height
    Example:
      import rhinoscriptsyntax as rs
      size = rs.ViewSize()
      if size:
          print("Width: {} pixels".format(size[0]))
          print("Height: {} pixels".format(size[1]))
    See Also:
      ViewCameraLens
      ViewCameraTarget
      ViewCPlane
      ViewDisplayModes
      ViewProjection
    """
    view = __viewhelper(view)
    cr = view.ClientRectangle
    return cr.Width, cr.Height


def ViewSpeedTest(view=None, frames=100, freeze=True, direction=0, angle_degrees=5):
    """Test's Rhino's display performance
    Parameters:
      view (str|guid, optional): The title or identifier of the view.  If omitted, the current active view is used
      frames (number, optional): The number of frames, or times to regenerate the view. If omitted, the view will be regenerated 100 times.
      freeze (bool, optional): If True (Default), then Rhino's display list will not be updated with every frame redraw. If False, then Rhino's display list will be updated with every frame redraw.
      direction (number, optional): The direction to rotate the view. The default direction is Right (0). Modes:
        0 = Right
        1 = Left
        2 = Down
        3 = Up.
      angle_degrees (number, optional): The angle to rotate. If omitted, the rotation angle of 5.0 degrees will be used.
    Returns:
      number: The number of seconds it took to regenerate the view frames number of times, if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      view = "Perspective"
      seconds = rs.ViewSpeedTest(view, 100)
      if seconds:
          print("Time to regen viewport 100 times = {} secords".format(seconds))
    See Also:
      
    """
    view = __viewhelper(view)
    angle_radians = math.radians(angle_degrees)
    return view.SpeedTest(frames, freeze, direction, angle_radians)


def ViewTarget(view=None, target=None):
    """Returns or sets the target location of the specified view
    Parameters:
      view (str|guid, optional): title or id of the view. If omitted, current active view is used
      target (point, optional): 3d point identifying the new target location. If omitted,
        the current target location is returned
    Returns:
      point: is target is not specified, then the current target location
      point: is target is specified, then the previous target location
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      target = rs.GetPoint("Select new target location")
      if target: rs.ViewTarget( view, target )
    See Also:
      ViewCamera
      ViewCameraTarget
    """
    view = __viewhelper(view)
    viewport = view.ActiveViewport
    old_target = viewport.CameraTarget
    if target is None: return old_target
    target = rhutil.coerce3dpoint(target)
    if target is None: return scriptcontext.errorhandler()
    viewport.SetCameraTarget(target, True)
    view.Redraw()
    return old_target


def ViewTitle(view_id):
    """Returns the name, or title, of a given view's identifier
    Parameters:
      view_id (str|guid): The identifier of the view
    Returns:
      str: name or title of the view on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      view_ids = rs.ViewNames(False)
      for id in view_ids:
          print(id + " = " + rs.ViewTitle(id))
    See Also:
      CurrentView
      ViewNames
    """
    view_id = rhutil.coerceguid(view_id)
    if view_id is None: return scriptcontext.errorhandler()
    view = scriptcontext.doc.Views.Find(view_id)
    if view is None: return scriptcontext.errorhandler()
    return view.MainViewport.Name


def Wallpaper(view=None, filename=None):
    """Returns or sets the wallpaper bitmap of the specified view. To remove a
    wallpaper bitmap, pass an empty string ""
    Parameters:
      view (str|guid, optional): The identifier of the view. If omitted, the
        active view is used
      filename (str): Name of the bitmap file to set as wallpaper
    Returns:
      str: If filename is not specified, the current wallpaper bitmap filename
      str: If filename is specified, the previous wallpaper bitmap filename
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      filename = rs.OpenFileName()
      if filename and not rs.IsWallpaper(view):
          rs.Wallpaper(view, filename)
    See Also:
      IsWallpaper
      WallpaperGrayScale
      WallpaperHidden
    """
    view = __viewhelper(view)
    rc = view.ActiveViewport.WallpaperFilename
    if filename is not None and filename!=rc:
        view.ActiveViewport.SetWallpaper(filename, False)
        view.Redraw()
    return rc


def WallpaperGrayScale(view=None, grayscale=None):
    """Returns or sets the grayscale display option of the wallpaper bitmap in a
    specified view
    Parameters:
      view (str|guid, optional):  The identifier of the view. If omitted, the
        active view is used
      grayscale (bool, optional): Display the wallpaper in gray(True) or color (False)
    Returns:
      bool: If grayscale is not specified, the current grayscale display option
      bool: If grayscale is specified, the previous grayscale display option
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      if rs.WallpaperGrayScale(view)==False: rs.WallpaperGrayScale(view, True)
    See Also:
      Wallpaper
      WallpaperHidden
    """
    view = __viewhelper(view)
    rc = view.ActiveViewport.WallpaperGrayscale
    if grayscale is not None and grayscale!=rc:
        filename = view.ActiveViewport.WallpaperFilename
        view.ActiveViewport.SetWallpaper(filename, grayscale)
        view.Redraw()
    return rc


def WallpaperHidden(view=None, hidden=None):
    """Returns or sets the visibility of the wallpaper bitmap in a specified view
    Parameters:
      view (str|guid, optional): The identifier of the view. If omitted, the
        active view is used
      hidden (bool, optional): Show or hide the wallpaper
    Returns:
      bool: If hidden is not specified, the current hidden state
      bool: If hidden is specified, the previous hidden state
    Example:
      import rhinoscriptsyntax as rs
      view = rs.CurrentView()
      if rs.WallpaperHidden(view) == False: rs.WallpaperHidden(view, True)
    See Also:
      Wallpaper
      WallpaperGrayScale
    """
    view = __viewhelper(view)
    rc = not view.ActiveViewport.WallpaperVisible
    if hidden is not None and hidden!=rc:
        filename = view.ActiveViewport.WallpaperFilename
        gray = view.ActiveViewport.WallpaperGrayscale
        view.ActiveViewport.SetWallpaper(filename, gray, not hidden)
        view.Redraw()
    return rc


def ZoomBoundingBox(bounding_box, view=None, all=False):
    """Zooms to the extents of a specified bounding box in the specified view
    Parameters:
      bounding_box ([point, point, point ,point, point, point, point, point]): eight points that define the corners
        of a bounding box or a BoundingBox class instance
      view  (str|guid, optional): title or id of the view. If omitted, current active view is used
      all (bool, optional): zoom extents in all views
    Returns:
      None
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject()
      if obj:
          bbox = rs.BoundingBox(obj)
          rs.ZoomBoundingBox( bbox )
    See Also:
      ZoomExtents
      ZoomSelected
    """
    bbox = rhutil.coerceboundingbox(bounding_box)
    if bbox:
      if all:
          views = scriptcontext.doc.Views.GetViewList(True, True)
          for view in views: view.ActiveViewport.ZoomBoundingBox(bbox)
      else:
          view = __viewhelper(view)
          view.ActiveViewport.ZoomBoundingBox(bbox)
      scriptcontext.doc.Views.Redraw()


def ZoomExtents(view=None, all=False):
    """Zooms to extents of visible objects in the specified view
    Parameters:
      view  (str|guid, optional): title or id of the view. If omitted, current active view is used
      all (bool, optional): zoom extents in all views
    Returns:
      None
    Example:
      import rhinoscriptsyntax as rs
      rs.ZoomExtents()
    See Also:
      ZoomBoundingBox
      ZoomSelected
    """
    if all:
        views = scriptcontext.doc.Views.GetViewList(True, True)
        for view in views: view.ActiveViewport.ZoomExtents()
    else:
        view = __viewhelper(view)
        view.ActiveViewport.ZoomExtents()
    scriptcontext.doc.Views.Redraw()


def ZoomSelected(view=None, all=False):
    """Zoom to extents of selected objects in a view
    Parameters:
      view  (str|guid, optional): title or id of the view. If omitted, active view is used
      all (bool, optional): zoom extents in all views
    Returns:
      None
    Example:
      import rhinocriptsyntax as rs
      obj = rs.GetObject("Select object", select=True)
      if obj: rs.ZoomSelected()
    See Also:
      ZoomBoundingBox
      ZoomExtents
    """
    if all:
        views = scriptcontext.doc.Views.GetViewList(True, True)
        for view in views: view.ActiveViewport.ZoomExtentsSelected()
    else:
        view = __viewhelper(view)
        view.ActiveViewport.ZoomExtentsSelected()
    scriptcontext.doc.Views.Redraw()
