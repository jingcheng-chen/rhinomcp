import math

import System
import System.Drawing
import System.Windows.Forms

import Eto.Forms

import Rhino
import Rhino.UI

import scriptcontext

import rhinocompat as compat
from rhinoscript import utility as rhutil
from rhinoscript.view import __viewhelper


def BrowseForFolder(folder=None, message=None, title=None):
    """Display browse-for-folder dialog allowing the user to select a folder
    Parameters:
      folder (str, optional): a default folder
      message (str, optional): a prompt or message
      title (str, optional): a dialog box title
    Returns:
      str: selected folder
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      folder = rs.BrowseForFolder("C:\\Program Files\\" )
      if folder: print(folder)
    See Also:
      OpenFileName
      SaveFileName
    """
    dlg = Eto.Forms.SelectFolderDialog()
    if folder:
        if not isinstance(folder, str): folder = str(folder)
        dlg.Directory = folder
    if message:
        if not isinstance(message, str): message = str(message)
        dlg.Title = message
    if title:
        if not isinstance(title, str): title = str(title)
        dlg.Title = title
    if message and title:
        if not isinstance(message, str): message = str(message)
        if not isinstance(title, str): title = str(title)
        dlg.Title = title + ": " + message
    if dlg.ShowDialog(None)==Eto.Forms.DialogResult.Ok:
        return dlg.Directory


def CheckListBox(items, message=None, title=None):
    """Displays a list of items in a checkable-style list dialog box
    Parameters:
      items ([[str, bool], ...]): a list of tuples containing a string and a boolean check state
      message (str, optional):  a prompt or message
      title (str, optional):  a dialog box title
    Returns:
      list((str, bool), ...): of tuples containing the input string in items along with their new boolean check value
      None: on error
    Example:
      import rhinoscriptsyntax as  rs
      layers = rs.LayerNames()
      if layers:
          items  = [(layer, rs.IsLayerOn(layer)) for layer in layers]
          results  = rs.CheckListBox(items, "Turn layers on/off", "Layers")
          if results:
              for  layer, state in results: rs.LayerVisible(layer, state)
    See Also:
      ComboListBox
      ListBox
      MultiListBox
      PropertyListBox
    """
    checkstates = [item[1] for item in items]
    itemstrs = [str(item[0]) for item in items]
    newcheckstates = Rhino.UI.Dialogs.ShowCheckListBox(title, message, itemstrs, checkstates)
    if newcheckstates:
        rc = compat.ITERATOR2LIST(zip(itemstrs, newcheckstates))
        return rc
    return scriptcontext.errorhandler()


def ComboListBox(items, message=None, title=None):
    """Displays a list of items in a combo-style list box dialog.
    Parameters:
      items ([str, ...]): a list of string
      message (str, optional):  a prompt of message
      title (str, optional):  a dialog box title
    Returns:
      str: The selected item if successful
      None: if not successful or on error
    Example:
      import rhinoscriptsyntax as rs
      layers = rs.LayerNames()
      if layers:
          layer = rs.ComboListBox(layers, "Select current layer")
          if layer: rs.CurrentLayer(layer)
    See Also:
      CheckListBox
      ListBox
      MultiListBox
      PropertyListBox
    """
    return Rhino.UI.Dialogs.ShowComboListBox(title, message, items)


def EditBox(default_string=None, message=None, title=None):
    """Display dialog prompting the user to enter a string. The
    string value may span multiple lines
    Parameters:
      default_string  (str, optional):  a default string value.
      message (str, optional): a prompt message.
      title (str, optional): a dialog box title.
    Returns:
      str: Multiple lines that are separated by carriage return-linefeed combinations if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      text = rs.EditBox(message="Enter some text")
      print(text)
    See Also:
      GetString
      StringBox
    """
    rc, text = Rhino.UI.Dialogs.ShowEditBox(title, message, default_string, True)
    return text

def GetAngle(point=None, reference_point=None, default_angle_degrees=0, message=None):
    """Pause for user input of an angle
    Parameters:
      point (point): starting, or base point
      reference_point (point, optional): if specified, the reference angle is calculated
        from it and the base point
      default_angle_degrees (number, optional): a default angle value specified
      message (str, optional): a prompt to display
    Returns:
      number: angle in degree if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      point = rs.GetPoint("Base point")
      if point:
          reference = rs.GetPoint("Reference point", point)
          if reference:
              angle = rs.GetAngle(point, reference)
              if angle!=None: print("Angle:{}".format(angle))
    See Also:
      GetDistance
    """
    point = rhutil.coerce3dpoint(point)
    if not point: point = Rhino.Geometry.Point3d.Unset
    reference_point = rhutil.coerce3dpoint(reference_point)
    if not reference_point: reference_point = Rhino.Geometry.Point3d.Unset
    default_angle = math.radians(default_angle_degrees)
    rc, angle = Rhino.Input.RhinoGet.GetAngle(message, point, reference_point, default_angle)
    if rc==Rhino.Commands.Result.Success: return math.degrees(angle)


def GetBoolean(message, items, defaults):
    """Pauses for user input of one or more boolean values. Boolean values are
    displayed as click-able command line option toggles
    Parameters:
      message (str): a prompt
      items ([str, str, str], ...): list or tuple of options. Each option is a tuple of three strings
        [n][1]    description of the boolean value. Must only consist of letters
                  and numbers. (no characters like space, period, or dash
        [n][2]    string identifying the false value
        [n][3]    string identifying the true value
      defaults ([bool, ...]): list of boolean values used as default or starting values
    Returns:
      list(bool, ...): a list of values that represent the boolean values if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      items = ("Lights", "Off", "On"), ("Cameras", "Disabled", "Enabled"), ("Action", "False", "True")
      results = rs.GetBoolean("Boolean options", items, (True, True, True) )
      if results:
          for val in results: print(val)
    See Also:
      GetString
    """
    go = Rhino.Input.Custom.GetOption()
    go.AcceptNothing(True)
    go.SetCommandPrompt( message )
    if type(defaults) is list or type(defaults) is tuple: pass
    else: defaults = [defaults]
    # special case for single list. Wrap items into a list
    if len(items)==3 and len(defaults)==1: items = [items]
    count = len(items)
    if count<1 or count!=len(defaults): return scriptcontext.errorhandler()
    toggles = []
    for i in compat.RANGE(count):
        initial = defaults[i]
        item = items[i]
        offVal = item[1]
        t = Rhino.Input.Custom.OptionToggle( initial, item[1], item[2] )
        toggles.append(t)
        go.AddOptionToggle(item[0], t)
    while True:
        getrc = go.Get()
        if getrc==Rhino.Input.GetResult.Option: continue
        if getrc!=Rhino.Input.GetResult.Nothing: return None
        break
    return [t.CurrentValue for t in toggles]


def GetBox(mode=0, base_point=None, prompt1=None, prompt2=None, prompt3=None):
    """Pauses for user input of a box
    Parameters:
      mode (number): The box selection mode.
         0 = All modes
         1 = Corner. The base rectangle is created by picking two corner points
         2 = 3-Point. The base rectangle is created by picking three points
         3 = Vertical. The base vertical rectangle is created by picking three points.
         4 = Center. The base rectangle is created by picking a center point and a corner point
      base_point (point, optional): optional 3D base point
      prompt1, prompt2, prompt3 (str, optional): optional prompts to set
    Returns:
      list(point, ...): list of eight Point3d that define the corners of the box on success
      None: is not successful, or on error
    Example:
      import rhinoscriptsyntax as rs
      box = rs.GetBox()
      if box:
          for i, pt in enumerate(box): rs.AddTextDot( i, pt )
    See Also:
      GetRectangle
    """
    base_point = rhutil.coerce3dpoint(base_point)
    if base_point is None: base_point = Rhino.Geometry.Point3d.Unset
    def intToEnum(m):
      if m not in compat.RANGE(1,5):
        m = 0
      return {
        0 : Rhino.Input.GetBoxMode.All,
        1 : Rhino.Input.GetBoxMode.Corner,
        2 : Rhino.Input.GetBoxMode.ThreePoint,
        3 : Rhino.Input.GetBoxMode.Vertical,
        4 : Rhino.Input.GetBoxMode.Center
      }[m]
    rc, box = Rhino.Input.RhinoGet.GetBox(intToEnum(mode), base_point, prompt1, prompt2, prompt3)
    if rc==Rhino.Commands.Result.Success: return tuple(box.GetCorners())


def GetColor(color=[0,0,0]):
    """Display the Rhino color picker dialog allowing the user to select an RGB color
    Parameters:
      color (color, optional): default RGB value. If omitted, the default color is black
    Returns:
      color: RGB tuple of three numbers on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      color = rs.LayerColor("Default")
      rgb = rs.GetColor(color)
      if rgb: rs.LayerColor("Default", rgb)
    See Also:
      
    """
    color = rhutil.coercecolor(color)
    if color is None: color = System.Drawing.Color.Black
    rc, color = Rhino.UI.Dialogs.ShowColorDialog(color)
    if rc: return color.R, color.G, color.B
    return scriptcontext.errorhandler()


def GetCursorPos():
    """Retrieves the cursor's position
    Returns:
      tuple(point, point, guid, point) containing the following information
        [0]  cursor position in world coordinates
        [1]  cursor position in screen coordinates
        [2]  id of the active viewport
        [3]  cursor position in client coordinates
    Example:
      import rhinoscriptsyntax as  rs
      world, screen, view, client  = rs.GetCursorPos()
    See Also:
      XformScreenToWorld
      XformWorldToScreen
    """
    view = scriptcontext.doc.Views.ActiveView
    screen_pt = Rhino.UI.MouseCursor.Location
    client_pt = view.ScreenToClient(screen_pt)
    viewport = view.ActiveViewport
    xf = viewport.GetTransform(Rhino.DocObjects.CoordinateSystem.Screen, Rhino.DocObjects.CoordinateSystem.World)
    world_pt = Rhino.Geometry.Point3d(client_pt.X, client_pt.Y, 0)
    world_pt.Transform(xf)
    return world_pt, screen_pt, viewport.Id, client_pt


def GetDistance(first_pt=None, distance=None, first_pt_msg='First distance point', second_pt_msg='Second distance point'):
    """Pauses for user input of a distance.
    Parameters:
      first_pt (point, optional): First distance point
      distance (number, optional): Default distance
      first_pt_msg (str, optional): Prompt for the first distance point
      second_pt_msg (str, optional): Prompt for the second distance point
    Returns:
      number: The distance between the two points if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as  rs
      dist = rs.GetDistance()
      if dist:
          print( dist)
    See Also:
      GetAngle
    """
    if distance is not None and first_pt is None: 
        raise Exception("The 'first_pt' parameter needs a value if 'distance' is not None.")
    if distance is not None and not (isinstance(distance, int) or isinstance(distance, float)): return None
    if first_pt_msg is None or not isinstance(first_pt_msg, str): return None
    if second_pt_msg is None or not isinstance(second_pt_msg, str): return None

    if first_pt is not None:
      if first_pt == 0: first_pt = (0,0,0)
      first_pt = rhutil.coerce3dpoint(first_pt)
      if first_pt is None: return None

    if first_pt is None:
      first_pt = GetPoint(first_pt_msg)
      if first_pt is None: return None

    # cannot use GetPoint for 2nd point because of the need do differentiate 
    # between the user accepting none vs cancelling to exactly mimic RhinoScript
    gp = Rhino.Input.Custom.GetPoint()
    if distance is not None:
      gp.AcceptNothing(True)
      second_pt_msg = "{0}<{1}>".format(second_pt_msg, distance)
    gp.SetCommandPrompt(second_pt_msg)
    gp.DrawLineFromPoint(first_pt,True)
    gp.EnableDrawLineFromPoint(True)
    r = gp.Get()
    if r not in [Rhino.Input.GetResult.Cancel, Rhino.Input.GetResult.Point,
      Rhino.Input.GetResult.Nothing]: return scriptcontext.errorHandler()
    if r == Rhino.Input.GetResult.Cancel: return None
    if r == Rhino.Input.GetResult.Point:
      second_pt = gp.Point()
      distance = second_pt.DistanceTo(first_pt)
    gp.Dispose()

    return distance


def GetEdgeCurves(message=None, min_count=1, max_count=0, select=False):
    """Prompt the user to pick one or more surface or polysurface edge curves
    Parameters:
      message  (str, optional):  A prompt or message.
      min_count (number, optional): minimum number of edges to select.
      max_count (number, optional): maximum number of edges to select.
      select (bool, optional): Select the duplicated edge curves.
    Returns:
      list(tuple[guid, point, point], ...): of selection prompts (curve id, parent id, selection point)
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      edges = rs.GetEdgeCurves()
      if edges:
          for edgeinfo in edges:
              print("Curve Id ={}".format(edgeinfo[0]))
              print("Parent Id ={}".format(edgeinfo[1]))
              print("Pick point ={}".format(edgeinfo[2]))
    See Also:
      DuplicateEdgeCurves
    """
    if min_count<0 or (max_count>0 and min_count>max_count): return
    if not message: message = "Select Edges"
    go = Rhino.Input.Custom.GetObject()
    go.SetCommandPrompt(message)
    go.GeometryFilter = Rhino.DocObjects.ObjectType.Curve
    go.GeometryAttributeFilter = Rhino.Input.Custom.GeometryAttributeFilter.EdgeCurve
    go.EnablePreSelect(False, True)
    rc = go.GetMultiple(min_count, max_count)
    if rc!=Rhino.Input.GetResult.Object: return
    rc = []
    for i in compat.RANGE(go.ObjectCount):
        edge = go.Object(i).Edge()
        if not edge: continue
        edge = edge.Duplicate()
        curve_id = scriptcontext.doc.Objects.AddCurve(edge)
        parent_id = go.Object(i).ObjectId
        pt = go.Object(i).SelectionPoint()
        rc.append( (curve_id, parent_id, pt) )
    if select:
        for item in rc:
            rhobj = scriptcontext.doc.Objects.Find(item[0])
            rhobj.Select(True)
        scriptcontext.doc.Views.Redraw()
    return rc        


def GetInteger(message=None, number=None, minimum=None, maximum=None):
    """Pauses for user input of a whole number.
    Parameters:
      message (str, optional): A prompt or message.
      number (number, optional): A default whole number value.
      minimum (number, optional): A minimum allowable value.
      maximum (number, optional): A maximum allowable value.
    Returns:
       number: The whole number input by the user if successful.
       None: if not successful, or on error
    Example:
      import rhinoscriptsyntax as rs
      color = rs.LayerColor("Default")
      color = rs.GetInteger("Enter an RGB color value", color.ToArgb(), 0)
      if color: rs.LayerColor("Default", color)
    See Also:
      
    """
    gi = Rhino.Input.Custom.GetInteger()
    if message: gi.SetCommandPrompt(message)
    if number is not None: gi.SetDefaultInteger(number)
    if minimum is not None: gi.SetLowerLimit(minimum, False)
    if maximum is not None: gi.SetUpperLimit(maximum, False)
    if gi.Get()!=Rhino.Input.GetResult.Number: return scriptcontext.errorhandler()
    rc = gi.Number()
    gi.Dispose()
    return rc


def GetLayer(title="Select Layer", layer=None, show_new_button=False, show_set_current=False):
    """Displays dialog box prompting the user to select a layer
    Parameters:
      title (str, optional): dialog box title
      layer (str, optional): name of a layer to preselect. If omitted, the current layer will be preselected
      show_new_button, show_set_current (bool, optional): Optional buttons to show on the dialog
    Returns:
      str: name of selected layer if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          layer = rs.GetLayer("Select Layer", rs.ObjectLayer(obj), True, True)
          if layer: rs.ObjectLayer( obj, layer )
    See Also:
      
    """
    layer_index = scriptcontext.doc.Layers.CurrentLayerIndex
    if layer:
        if "::" in layer:
            idx = scriptcontext.doc.Layers.FindByFullPath(layer,-1)
            if idx != -1: 
                layer_index = idx
            else:
                # layer name could have embedded '::'
                layer_instance = scriptcontext.doc.Layers.FindName(layer)
                if layer_instance is not None: layer_index = layer_instance.Index
        else:
            layer_instance = scriptcontext.doc.Layers.FindName(layer)
            if layer_instance is not None: layer_index = layer_instance.Index
    rc = Rhino.UI.Dialogs.ShowSelectLayerDialog(layer_index, title, show_new_button, show_set_current, True)
    if rc[0]!=True: return None
    layer = scriptcontext.doc.Layers[rc[1]]
    return layer.FullPath


def GetLayers(title="Select Layers", show_new_button=False):
    """Displays a dialog box prompting the user to select one or more layers
    Parameters:
      title (str, optional):  dialog box title
      show_new_button (bool, optional): Optional button to show on the dialog
    Returns:
      str: The names of selected layers if successful
    Example:
      import rhinoscriptsyntax as rs
      layers = rs.GetLayers("Select Layers")
      if layers:
          for layer in layers: print(layer)
    See Also:
      GetLayer
    """
    rc, layer_indices = Rhino.UI.Dialogs.ShowSelectMultipleLayersDialog(None, title, show_new_button)
    if rc:
        return [scriptcontext.doc.Layers[index].FullPath for index in layer_indices]


def GetLine(mode=0, point=None, message1=None, message2=None, message3=None):
    """Prompts the user to pick points that define a line
    Parameters:
      mode (number, optional): line definition mode.
        0  Default - Show all modes, start in two-point mode
        1  Two-point - Defines a line from two points.
        2  Normal - Defines a line normal to a location on a surface.
        3  Angled - Defines a line at a specified angle from a reference line.
        4  Vertical - Defines a line vertical to the construction plane.
        5  Four-point - Defines a line using two points to establish direction and two points to establish length.
        6  Bisector - Defines a line that bisects a specified angle.
        7  Perpendicular - Defines a line perpendicular to or from a curve
        8  Tangent - Defines a line tangent from a curve.
        9  Extension - Defines a line that extends from a curve.
      point (point, optional): optional starting point
      message1, message2, message3 (str, optional): optional prompts
    Returns:
      line: Tuple of two points on success
      None: on error
    Example:
      import rhinoscriptsyntax as  rs
      line = rs.GetLine()
      if line: rs.AddLine( line[0],  line[1] )
    See Also:
      GetBox
      GetPoint
      GetPolyline
      GetRectangle
    """
    gl = Rhino.Input.Custom.GetLine()
    if mode==0: gl.EnableAllVariations(True)
    else: gl.GetLineMode = System.Enum.ToObject( Rhino.Input.Custom.GetLineMode, mode-1 )
    if point:
        point = rhutil.coerce3dpoint(point)
        gl.SetFirstPoint(point)
    if message1: gl.FirstPointPrompt = message1
    if message2: gl.MidPointPrompt = message2
    if message3: gl.SecondPointPrompt = message3
    rc, line = gl.Get()
    if rc==Rhino.Commands.Result.Success: return line.From, line.To


def GetLinetype(default_linetype=None, show_by_layer=False):
    """Displays a dialog box prompting the user to select one linetype
    Parameters:
      default_linetype (str, optional):  Optional. The name of the linetype to select. If omitted, the current linetype will be selected.
      show_by_layer (bool, optional): If True, the "by Layer" linetype will show. Defaults to False.
    Returns:
      str: The names of selected linetype if successful
    Example:
      import rhinoscriptsyntax as rs
      linetype = rs.GetLinetype()
      if linetype: print(linetype)
    See Also:
      GetLayer
    """
    lt_instance = scriptcontext.doc.Linetypes.CurrentLinetype
    if default_linetype:
        lt_new = scriptcontext.doc.Linetypes.FindName(default_linetype)
        if lt_new is not None: lt_instance = lt_new
    id = Rhino.UI.Dialogs.ShowLineTypes("Select Linetype", "", scriptcontext.doc)
    if id == System.Guid.Empty: return None
    linetype = scriptcontext.doc.Linetypes.FindId(id)
    return linetype.Name

def GetMeshFaces(object_id, message="", min_count=1, max_count=0):
    """Prompts the user to pick one or more mesh faces
    Parameters:
      object_id (guid): the mesh object's identifier
      message (str, optional): a prompt of message
      min_count (number, optional): the minimum number of faces to select
      max_count (number, optional): the maximum number of faces to select.
        If 0, the user must press enter to finish selection.
        If -1, selection stops as soon as there are at least min_count faces selected.
    Returns:
      list(number, ...): of mesh face indices on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      mesh = rs.GetObject("Select mesh", rs.filter.mesh)
      if mesh:
          indices = rs.GetMeshFaces(mesh)
          if indices:
              for index in indices: print(index)
    See Also:
      GetMeshVertices
      MeshFaces
      MeshFaceVertices
      MeshVertices
    """
    scriptcontext.doc.Objects.UnselectAll()
    scriptcontext.doc.Views.Redraw()
    object_id = rhutil.coerceguid(object_id, True)
    def FilterById( rhino_object, geometry, component_index ):
        return object_id == rhino_object.Id
    go = Rhino.Input.Custom.GetObject()
    go.SetCustomGeometryFilter(FilterById)
    if message: go.SetCommandPrompt(message)
    go.GeometryFilter = Rhino.DocObjects.ObjectType.MeshFace
    go.AcceptNothing(True)
    if go.GetMultiple(min_count,max_count)!=Rhino.Input.GetResult.Object: return None
    objrefs = go.Objects()
    rc = [item.GeometryComponentIndex.Index for item in objrefs]
    go.Dispose()
    return rc


def GetMeshVertices(object_id, message="", min_count=1, max_count=0):
    """Prompts the user to pick one or more mesh vertices
    Parameters:
      object_id (guid): the mesh object's identifier
      message (str, optional): a prompt of message
      min_count (number, optional): the minimum number of vertices to select
      max_count (number, optional): the maximum number of vertices to select. If 0, the user must
        press enter to finish selection. If -1, selection stops as soon as there
        are at least min_count vertices selected.
    Returns:
      list(number, ...): of mesh vertex indices on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      mesh = rs.GetObject("Select mesh", rs.filter.mesh)
      if mesh:
          indices = rs.GetMeshVertices(mesh)
          if indices:
              for index in indices: print(index)
    See Also:
      GetMeshFaces
      MeshFaces
      MeshFaceVertices
      MeshVertices
    """
    scriptcontext.doc.Objects.UnselectAll()
    scriptcontext.doc.Views.Redraw()
    object_id = rhutil.coerceguid(object_id, True)
    class CustomGetObject(Rhino.Input.Custom.GetObject):
        def CustomGeometryFilter( self, rhino_object, geometry, component_index ):
            return object_id == rhino_object.Id
    go = CustomGetObject()
    if message: go.SetCommandPrompt(message)
    go.GeometryFilter = Rhino.DocObjects.ObjectType.MeshVertex
    go.AcceptNothing(True)
    if go.GetMultiple(min_count,max_count)!=Rhino.Input.GetResult.Object: return None
    objrefs = go.Objects()
    rc = [item.GeometryComponentIndex.Index for item in objrefs]
    go.Dispose()
    return rc


def GetPoint(message=None, base_point=None, distance=None, in_plane=False):
    """Pauses for user input of a point.
    Parameters:
      message (str, optional): A prompt or message.
      base_point (point, optional): list of 3 numbers or Point3d identifying a starting, or base point
      distance  (number, optional): constraining distance. If distance is specified, basePoint must also be specified.
      in_plane (bool, optional): constrains the point selections to the active construction plane.
    Returns:
      point: point on success
      None: if no point picked or user canceled
    Example:
      import rhinoscriptsyntax as rs
      point1 = rs.GetPoint("Pick first point")
      if point1:
          rs.AddPoint(point1)
          point2 = rs.GetPoint("Pick second point", point1)
          if point2:
              rs.AddPoint(point2)
              distance = (point1-point2).Length
              point3 = rs.GetPoint("Pick third point", point2, distance)
              if point3: rs.AddPoint(point3)
    See Also:
      GetPointOnCurve
      GetPointOnSurface
      GetPoints
      GetRectangle
    """
    gp = Rhino.Input.Custom.GetPoint()
    if message: gp.SetCommandPrompt(message)
    base_point = rhutil.coerce3dpoint(base_point)
    if base_point:
        gp.DrawLineFromPoint(base_point,True)
        gp.EnableDrawLineFromPoint(True)
        if distance: gp.ConstrainDistanceFromBasePoint(distance)
    if in_plane: gp.ConstrainToConstructionPlane(True)
    gp.Get()
    if gp.CommandResult()!=Rhino.Commands.Result.Success:
        return scriptcontext.errorhandler()
    pt = gp.Point()
    gp.Dispose()
    return pt


def GetPointOnCurve(curve_id, message=None):
    """Pauses for user input of a point constrainted to a curve object
    Parameters:
      curve_id (guid): identifier of the curve to get a point on
      message (str, optional): a prompt of message
    Returns:
      point: 3d point if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Pick a curve")
      if rs.IsCurve(obj):
          point = rs.GetPointOnCurve(obj, "Point on curve")
          if point: rs.AddPoint(point)
    See Also:
      GetPoint
      GetPointOnMesh
      GetPointOnSurface
      GetPoints
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    gp = Rhino.Input.Custom.GetPoint()
    if message: gp.SetCommandPrompt(message)
    gp.Constrain(curve, False)
    gp.Get()
    if gp.CommandResult()!=Rhino.Commands.Result.Success:
        return scriptcontext.errorhandler()
    pt = gp.Point()
    gp.Dispose()
    return pt


def GetPointOnMesh(mesh_id, message=None):
    """Pauses for user input of a point constrained to a mesh object
    Parameters:
      mesh_id (guid): identifier of the mesh to get a point on
      message (str, optional): a prompt or message
    Returns:
      point: 3d point if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      mesh = rs.GetObject("Pick a mesh", rs.filter.mesh)
      if mesh:
          point = rs.GetPointOnMesh(mesh, "Point on mesh")
          if point: rs.AddPoint( point )
    See Also:
      GetPoint
      GetPointOnCurve
      GetPointOnSurface
      GetPoints
    """
    mesh_id = rhutil.coerceguid(mesh_id, True)
    if not message: message = "Point"
    cmdrc, point = Rhino.Input.RhinoGet.GetPointOnMesh(mesh_id, message, False)
    if cmdrc==Rhino.Commands.Result.Success: return point


def GetPointOnSurface(surface_id, message=None):
    """Pauses for user input of a point constrained to a surface or polysurface
    object
    Parameters:
      surface_id (guid): identifier of the surface to get a point on
      message (str, optional): a prompt or message
    Returns:
      point: 3d point if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      surface = rs.GetObject("Pick a surface")
      if surface:
          point = rs.GetPointOnSurface(surface, "Point on surface")
          if point: rs.AddPoint(point)
    See Also:
      GetPoint
      GetPointOnCurve
      GetPointOnMesh
      GetPoints
    """
    surfOrBrep = rhutil.coercesurface(surface_id)
    if not surfOrBrep:
        surfOrBrep = rhutil.coercebrep(surface_id, True)
    gp = Rhino.Input.Custom.GetPoint()
    if message: gp.SetCommandPrompt(message)
    if isinstance(surfOrBrep,Rhino.Geometry.Surface):
        gp.Constrain(surfOrBrep,False)
    else:
        gp.Constrain(surfOrBrep, -1, -1, False)
    gp.Get()
    if gp.CommandResult()!=Rhino.Commands.Result.Success:
        return scriptcontext.errorhandler()
    pt = gp.Point()
    gp.Dispose()
    return pt


def GetPoints(draw_lines=False, in_plane=False, message1=None, message2=None, max_points=None, base_point=None):
    """Pauses for user input of one or more points
    Parameters:
      draw_lines (bool, optional): Draw lines between points
      in_plane (bool, optional): Constrain point selection to the active construction plane
      message1 (str, optional): A prompt or message for the first point
      message2 (str, optional): A prompt or message for the next points
      max_points (number, optional): maximum number of points to pick. If not specified, an
                        unlimited number of points can be picked.
      base_point (point, optional): a starting or base point
    Returns:
      list(point, ...): of 3d points if successful
      None: if not successful or on error
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints(True)
      if points: rs.AddPointCloud(points)
    See Also:
      GetPoint
      GetPointOnCurve
      GetPointOnSurface
      GetRectangle
    """
    gp = Rhino.Input.Custom.GetPoint()
    if message1: gp.SetCommandPrompt(message1)
    gp.EnableDrawLineFromPoint( draw_lines )
    if in_plane:
        gp.ConstrainToConstructionPlane(True)
        plane = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane()
        gp.Constrain(plane, False)
    getres = gp.Get()
    if gp.CommandResult()!=Rhino.Commands.Result.Success: return None
    prevPoint = gp.Point()
    rc = [prevPoint]
    if max_points is None or max_points>1:
        current_point = 1
        if message2: gp.SetCommandPrompt(message2)
        def GetPointDynamicDrawFunc( sender, args ):
            if len(rc)>1:
                c = Rhino.ApplicationSettings.AppearanceSettings.FeedbackColor
                args.Display.DrawPolyline(rc, c)
        if draw_lines: gp.DynamicDraw += GetPointDynamicDrawFunc
        while True:
            if max_points and current_point>=max_points: break
            if draw_lines: gp.DrawLineFromPoint(prevPoint, True)
            gp.SetBasePoint(prevPoint, True)
            current_point += 1
            getres = gp.Get()
            if getres==Rhino.Input.GetResult.Cancel: break
            if gp.CommandResult()!=Rhino.Commands.Result.Success: return None
            prevPoint = gp.Point()
            rc.append(prevPoint)
    return rc

def GetPolyline(flags=3, message1=None, message2=None, message3=None, message4=None, min=2, max=0):
  """Prompts the user to pick points that define a polyline.
  Parameters:
    flags (number, optional) The options are bit coded flags. Values can be added together to specify more than one option. The default is 3.
      value description
      1     Permit close option. If specified, then after 3 points have been picked, the user can type "Close" and a closed polyline will be returned.
      2     Permit close snap. If specified, then after 3 points have been picked, the user can pick near the start point and a closed polyline will be returned.
      4     Force close. If specified, then the returned polyline is always closed. If specified, then intMax must be 0 or >= 4.
      Note: the default is 3, or "Permit close option = True", "Permit close snap = True", and "Force close = False".
    message1 (str, optional): A prompt or message for the first point.
    message2 (str, optional): A prompt or message for the second point.
    message3 (str, optional): A prompt or message for the third point.
    message4 (str, optional): A prompt or message for the 'next' point.
    min (number, optional): The minimum number of points to require. The default is 2.
    max (number, optional): The maximum number of points to require; 0 for no limit.  The default is 0.
  Returns:
    list(point, ...): A list of 3-D points that define the polyline if successful.
    None: if not successful or on error
  Example:
    import rhinoscriptsyntax as rs
    from scriptcontext import doc
    arr = rs.GetPolyline()
    if arr is not None:
        doc.AddPolyline(arr)
  See Also:
    GetBox
    GetLine
    GetRectangle
  """
  gpl = Rhino.Input.Custom.GetPolyline()
  if message1: gpl.FirstPointPrompt = message1
  if message2: gpl.SecondPointPrompt = message2
  if message3: gpl.ThirdPointPrompt = message3
  if message4: gpl.FourthPointPrompt = message4
  if min: gpl.MinPointCount = min
  if max: gpl.MaxPointCount = max
  rc, polyline = gpl.Get()
  scriptcontext.doc.Views.Redraw()
  if rc==Rhino.Commands.Result.Success: return polyline
  return None

def GetReal(message="Number", number=None, minimum=None, maximum=None):
    """Pauses for user input of a number.
    Parameters:
      message (str, optional): A prompt or message.
      number (number, optional): A default number value.
      minimum (number, optional): A minimum allowable value.
      maximum (number, optional): A maximum allowable value.
    Returns:
      number: The number input by the user if successful.
      None: if not successful, or on error
    Example:
      import rhinoscriptsyntax as rs
      radius = rs.GetReal("Radius of new circle", 3.14, 1.0)
      if radius: rs.AddCircle( (0,0,0), radius )
    See Also:
      RealBox
    """
    gn = Rhino.Input.Custom.GetNumber()
    if message: gn.SetCommandPrompt(message)
    if number is not None: gn.SetDefaultNumber(number)
    if minimum is not None: gn.SetLowerLimit(minimum, False)
    if maximum is not None: gn.SetUpperLimit(maximum, False)
    if gn.Get()!=Rhino.Input.GetResult.Number: return None
    rc = gn.Number()
    gn.Dispose()
    return rc


def GetRectangle(mode=0, base_point=None, prompt1=None, prompt2=None, prompt3=None):
    """Pauses for user input of a rectangle
    Parameters:
      mode (number, optional): The rectangle selection mode. The modes are as follows
          0 = All modes
          1 = Corner - a rectangle is created by picking two corner points
          2 = 3Point - a rectangle is created by picking three points
          3 = Vertical - a vertical rectangle is created by picking three points
          4 = Center - a rectangle is created by picking a center point and a corner point
      base_point (point, optional): a 3d base point
      prompt1, prompt2, prompt3 (str, optional): optional prompts
    Returns:
      tuple(point, point, point, point): four 3d points that define the corners of the rectangle
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      rect = rs.GetRectangle()
      if rect:
          for i, corner in enumerate(rect):
              rs.AddTextDot( i, corner )
    See Also:
      GetPoint
      GetPoints
    """
    mode = System.Enum.ToObject( Rhino.Input.GetBoxMode, mode )
    base_point = rhutil.coerce3dpoint(base_point)
    if( base_point==None ): base_point = Rhino.Geometry.Point3d.Unset
    prompts = ["", "", ""]
    if prompt1: prompts[0] = prompt1
    if prompt2: prompts[1] = prompt2
    if prompt3: prompts[2] = prompt3
    rc, corners = Rhino.Input.RhinoGet.GetRectangle(mode, base_point, prompts)
    if rc==Rhino.Commands.Result.Success: return corners
    return None


def GetString(message=None, defaultString=None, strings=None):
    """Pauses for user input of a string value
    Parameters:
      message (str, optional): a prompt or message
      defaultString (str, optional): a default value
      strings ([str, ...], optional): list of strings to be displayed as a click-able command options.
                                      Note, strings cannot begin with a numeric character
    Returns:
      str: The string either input or selected by the user if successful.
           If the user presses the Enter key without typing in a string, an empty string "" is returned.
      None: if not successful, on error, or if the user pressed cancel.
    Example:
      import rhinoscriptsyntax as rs
      layer = rs.CurrentLayer()
      layer = rs.GetString("Layer to set current", layer)
      if layer: rs.CurrentLayer(layer)
    See Also:
      GetBoolean
      StringBox
    """
    gs = Rhino.Input.Custom.GetString()
    gs.AcceptNothing(True)
    if message: gs.SetCommandPrompt(message)
    if defaultString: gs.SetDefaultString(defaultString)
    if strings:
        for s in strings: gs.AddOption(s)
    result = gs.Get()
    if result==Rhino.Input.GetResult.Cancel: return None
    if( result == Rhino.Input.GetResult.Option ):
        return gs.Option().EnglishName
    return gs.StringResult()


def ListBox(items, message=None, title=None, default=None):
    """Display a list of items in a list box dialog.
    Parameters:
      items ([str, ...]): a list of values to select
      message (str, optional): a prompt of message
      title (str, optional): a dialog box title
      default (str, optional): selected item in the list
    Returns:
      str: he selected item if successful
      None: if not successful or on error
    Example:
      import rhinoscriptsyntax as rs
      layers = rs.LayerNames()
      if layers:
          result = rs.ListBox(layers, "Layer to set current")
          if result: rs.CurrentLayer( result )
    See Also:
      CheckListBox
      ComboListBox
      MultiListBox
      PropertyListBox
    """
    return Rhino.UI.Dialogs.ShowListBox(title, message, items, default)


def MessageBox(message, buttons=0, title=""):
    """Displays a message box. A message box contains a message and
    title, plus any combination of predefined icons and push buttons.
    Parameters:
      message (str): A prompt or message.
      buttons (number, optional): buttons and icon to display as a bit coded flag. Can be a combination of the
        following flags. If omitted, an OK button and no icon is displayed
        0      Display OK button only.
        1      Display OK and Cancel buttons.
        2      Display Abort, Retry, and Ignore buttons.
        3      Display Yes, No, and Cancel buttons.
        4      Display Yes and No buttons.
        5      Display Retry and Cancel buttons.
        16     Display Critical Message icon.
        32     Display Warning Query icon.
        48     Display Warning Message icon.
        64     Display Information Message icon.
        0      First button is the default.
        256    Second button is the default.
        512    Third button is the default.
        768    Fourth button is the default.
        0      Application modal. The user must respond to the message box
               before continuing work in the current application.
        4096   System modal. The user must respond to the message box
               before continuing work in any application.
      title(str, optional): the dialog box title
    Returns:
      number: indicating which button was clicked:
        1      OK button was clicked.
        2      Cancel button was clicked.
        3      Abort button was clicked.
        4      Retry button was clicked.
        5      Ignore button was clicked.
        6      Yes button was clicked.
        7      No button was clicked.
    Example:
      import rhinoscriptsyntax as rs
      rs.MessageBox("Hello Rhino!")
      rs.MessageBox("Hello Rhino!", 4 | 32)
      rs.MessageBox("Hello Rhino!", 2 | 48)
    See Also:
      
    """
    buttontype = buttons & 0x00000007 #111 in binary
    btn = Rhino.UI.ShowMessageButton.OK
    if buttontype==1: btn = Rhino.UI.ShowMessageButton.OKCancel
    elif buttontype==2: btn = Rhino.UI.ShowMessageButton.AbortRetryIgnore
    elif buttontype==3: btn = Rhino.UI.ShowMessageButton.YesNoCancel
    elif buttontype==4: btn = Rhino.UI.ShowMessageButton.YesNo
    elif buttontype==5: btn = Rhino.UI.ShowMessageButton.RetryCancel
    
    icontype = buttons & 0x00000070
    icon = compat.ENUM_NONE(Rhino.UI.ShowMessageIcon)
    if icontype==16: icon = Rhino.UI.ShowMessageIcon.Error
    elif icontype==32: icon = Rhino.UI.ShowMessageIcon.Question
    elif icontype==48: icon = Rhino.UI.ShowMessageIcon.Warning
    elif icontype==64: icon = Rhino.UI.ShowMessageIcon.Information
    
    ### 15 Sep 2014 Alain - default button not supported in new version of RC 
    ### that isn't tied to Windows.Forms but it probably will so I'm commenting 
    ### the old code instead of deleting it.
    #defbtntype = buttons & 0x00000300
    #defbtn = System.Windows.Forms.MessageDefaultButton.Button1
    #if defbtntype==256:
    #    defbtn = System.Windows.Forms.MessageDefaultButton.Button2
    #elif defbtntype==512:
    #    defbtn = System.Windows.Forms.MessageDefaultButton.Button3

    if not isinstance(message, str): message = str(message)
    dlg_result = Rhino.UI.Dialogs.ShowMessage(message, title, btn, icon)
    if dlg_result==Rhino.UI.ShowMessageResult.OK:     return 1
    if dlg_result==Rhino.UI.ShowMessageResult.Cancel: return 2
    if dlg_result==Rhino.UI.ShowMessageResult.Abort:  return 3
    if dlg_result==Rhino.UI.ShowMessageResult.Retry:  return 4
    if dlg_result==Rhino.UI.ShowMessageResult.Ignore: return 5
    if dlg_result==Rhino.UI.ShowMessageResult.Yes:    return 6
    if dlg_result==Rhino.UI.ShowMessageResult.No:     return 7


def PropertyListBox(items, values, message=None, title=None):
    """Displays list of items and their values in a property-style list box dialog
    Parameters:
      items, values ([str, ...]): list of string items and their corresponding values
      message (str, optional): a prompt or message
      title (str, optional): a dialog box title
    Returns:
      list(str, ..): of new values on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select Objects")
      if objs:
          names = []
          for obj in objs:
              name = rs.ObjectName(obj)
              if name is None: name=""
              names.append(name)
          results = rs.PropertyListBox(objs, names, "Modify object name(s)")
          if results:
              for i in compat.RANGE(len(objs)):
                  rs.ObjectName( objs[i], results[i] )
    See Also:
      CheckListBox
      ComboListBox
      ListBox
      MultiListBox
    """
    values = [str(v) for v in values]
    return Rhino.UI.Dialogs.ShowPropertyListBox(title, message, items, values)


def MultiListBox(items, message=None, title=None, defaults=None):
    """Displays a list of items in a multiple-selection list box dialog
    Parameters:
      items ([str, ...]) a zero-based list of string items
      message (str, optional): a prompt or message
      title (str, optional): a dialog box title
      defaults (str|[str,...], optional): either a string representing the pre-selected item in the list
                                          or a list if multiple items are pre-selected
    Returns:
      list(str, ...): containing the selected items if successful
      None: on error
    Example:
      import rhinoscriptsyntax as  rs
      layers = rs.LayerNames()
      if layers:
          layers  = rs.MultiListBox(layers, "Layers to lock")
      if layers:
          for  layer in layers:
              rs.LayerLocked(layer,  True)
    See Also:
      CheckListBox
      ComboListBox
      ListBox
      PropertyListBox
    """
    if isinstance(defaults, str):
      defaults = [defaults]  
    return Rhino.UI.Dialogs.ShowMultiListBox(title, message, items, defaults)


def OpenFileName(title=None, filter=None, folder=None, filename=None, extension=None):
    """Displays file open dialog box allowing the user to enter a file name.
    Note, this function does not open the file.
    Parameters:
      title (str, optional): A dialog box title.
      filter (str, optional): A filter string. The filter must be in the following form:
        "Description1|Filter1|Description2|Filter2||", where "||" terminates filter string.
        If omitted, the filter (*.*) is used.
      folder (str, optional): A default folder.
      filename (str, optional): a default file name
      extension (str, optional): a default file extension
    Returns:
      str: file name is successful
      None: if not successful, or on error
    Example:
      import rhinoscriptsyntax as rs
      filename = rs.OpenFileName()
      if filename: rs.MessageBox(filename)
      filename = rs.OpenFileName("Open", "Text Files (*.txt)|*.txt||")
      if filename: rs.MessageBox(filename)
      filename = rs.OpenFileName("Open", "Text Files (*.txt)|*.txt|All Files (*.*)|*.*||")
      if filename: rs.MessageBox(filename)
    See Also:
      BrowseForFolder
      OpenFileNames
      SaveFileName
    """
    fd = Rhino.UI.OpenFileDialog()
    if title: fd.Title = title
    if filter: fd.Filter = filter
    if folder: fd.InitialDirectory = folder
    if filename: fd.FileName = filename
    if extension: fd.DefaultExt = extension
    if fd.ShowOpenDialog(): return fd.FileName


def OpenFileNames(title=None, filter=None, folder=None, filename=None, extension=None):
    """Displays file open dialog box allowing the user to select one or more file names.
    Note, this function does not open the file.
    Parameters:
      title (str, optional): A dialog box title.
      filter (str, optional): A filter string. The filter must be in the following form:
        "Description1|Filter1|Description2|Filter2||", where "||" terminates filter string.
        If omitted, the filter (*.*) is used.
      folder (str, optional): A default folder.
      filename (str, optional): a default file name
      extension (str, optional): a default file extension
    Returns:
      list(str, ...): of selected file names
    Example:
      import rhinoscriptsyntax as rs
      filenames = rs.OpenFileNames("Open", "Text Files (*.txt)|*.txt|All Files (*.*)|*.*||")
      for filename in filenames: print(filename)
    See Also:
      BrowseForFolder
      OpenFileName
      SaveFileName
    """
    fd = Rhino.UI.OpenFileDialog()
    if title: fd.Title = title
    if filter: fd.Filter = filter
    if folder: fd.InitialDirectory = folder
    if filename: fd.FileName = filename
    if extension: fd.DefaultExt = extension
    fd.MultiSelect = True
    if fd.ShowOpenDialog(): return fd.FileNames
    return []


def PopupMenu(items, modes=None, point=None, view=None):
    """Display a context-style popup menu. The popup menu can appear almost
    anywhere, and can be dismissed by clicking the left or right mouse buttons
    Parameters:
      items ([str, ...]): list of strings representing the menu items. An empty string or None
        will create a separator
      modes ([number, ...]): List of numbers identifying the display modes. If omitted, all
        modes are enabled.
          0 = menu item is enabled
          1 = menu item is disabled
          2 = menu item is checked
          3 = menu item is disabled and checked
      point (point, optional): a 3D point where the menu item will appear. If omitted, the menu
        will appear at the current cursor position
      view (str, optional): if point is specified, the view in which the point is computed.
        If omitted, the active view is used
    Returns:
      number: index of the menu item picked or -1 if no menu item was picked
    Example:
      import rhinoscriptsyntax as rs
      items = "Line", "", "Circle", "Arc"
      modes = 2,0,0,0
      result = rs.PopupMenu(items, modes)
      if result>=0: rs.MessageBox(items[result])
    See Also:
      
    """
    screen_point = System.Windows.Forms.Cursor.Position
    if point:
        point = rhutil.coerce3dpoint(point)
        view = __viewhelper(view)
        viewport = view.ActiveViewport
        point2d = viewport.WorldToClient(point)
        screen_point = viewport.ClientToScreen(point2d)
    return Rhino.UI.Dialogs.ShowContextMenu(items, screen_point, modes);


def RealBox(message="", default_number=None, title="", minimum=None, maximum=None):
    """Display a dialog box prompting the user to enter a number
    Parameters:
      message (str, optional): a prompt message.
      default_number (number, optional):  a default number.
      title (str, optional):  a dialog box title.
      minimum (number, optional):  a minimum allowable value.
      maximum (number, optional):  a maximum allowable value.
    Returns:
      number: The newly entered number on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      radius = rs.RealBox("Enter a radius value", 5.0 )
      if radius:
          point = (0,0,0)
          rs.AddCircle( point, radius )
    See Also:
      GetReal
    """
    if default_number is None: default_number = Rhino.RhinoMath.UnsetValue
    if minimum is None: minimum = Rhino.RhinoMath.UnsetValue
    if maximum is None: maximum = Rhino.RhinoMath.UnsetValue
    rc, number = Rhino.UI.Dialogs.ShowNumberBox(title, message, default_number, minimum, maximum)
    if rc: return number


def SaveFileName(title=None, filter=None, folder=None, filename=None, extension=None):
    """Display a save dialog box allowing the user to enter a file name.
    Note, this function does not save the file.
    Parameters:
      title (str, optional): A dialog box title.
      filter(str, optional): A filter string. The filter must be in the following form:
        "Description1|Filter1|Description2|Filter2||", where "||" terminates filter string.
        If omitted, the filter (*.*) is used.
      folder (str, optional): A default folder.
      filename (str, optional): a default file name
      extension (str, optional):  a default file extension
    Returns:
      str: the file name is successful
      None: if not successful, or on error
    Example:
      import rhinoscriptsyntax as rs
      filename = rs.SaveFileName()
      if filename: rs.MessageBox(filename)
      filename = rs.SaveFileName ("Save", "Text Files (*.txt)|*.txt||")
      if filename: rs.MessageBox(filename)
      filename = rrshui.SaveFileName ("Save", "Text Files (*.txt)|*.txt|All Files (*.*)|*.*||")
      if filename: rs.MessageBox(filename)
    See Also:
      BrowseForFolder
      OpenFileName
    """
    fd = Rhino.UI.SaveFileDialog()
    if title: fd.Title = title
    if filter: fd.Filter = filter
    if folder: fd.InitialDirectory = folder
    if filename: fd.FileName = filename
    if extension: fd.DefaultExt = extension
    if fd.ShowSaveDialog(): return fd.FileName


def StringBox(message=None, default_value=None, title=None):
    """Display a dialog box prompting the user to enter a string value.
    Parameters:
      message (str, optional): a prompt message
      default_value (str, optional): a default string value
      title (str, optional): a dialog box title
    Returns:
      str: the newly entered string value if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      layer = rs.StringBox("New layer name" )
      if layer: rs.AddLayer( layer )
    See Also:
      GetString
    """
    rc, text = Rhino.UI.Dialogs.ShowEditBox(title, message, default_value, False)
    if rc: return text


def TextOut(message=None, title=None):
    """Display a text dialog box similar to the one used by the _What command.
    Parameters:
      message (str): a message
      title (str, optional): the message title
    Returns:
      None: in any case
    Example:
      import rhinoscriptsyntax as rs
      rs.TextOut("This is a long string..." )
    See Also:
      MessagBox
    """
    Rhino.UI.Dialogs.ShowTextDialog(message, title)
