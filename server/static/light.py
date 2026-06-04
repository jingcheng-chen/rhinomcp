import math

import Rhino.Geometry

import scriptcontext

import rhinocompat as compat
from rhinoscript import utility as rhutil


def __coercelight(id, raise_if_missing=False):
    light = rhutil.coercegeometry(id)
    if isinstance(light, Rhino.Geometry.Light): return light
    if raise_if_missing: raise ValueError("unable to retrieve light from %s"%id)


def AddDirectionalLight(start_point, end_point):
    """Adds a new directional light object to the document
    Parameters:
      start_point(point): starting point of the light
      end_point (point): ending point and direction of the light
    Returns:
      (guid): identifier of the new object if successful
    Example:
      import rhinoscriptsyntax as rs
      end = rs.GetPoint("End of light vector direction")
      if end:
          start = rs.GetPoint("Start of light vector direction", end)
          if start: rs.AddDirectionalLight( start, end )
    See Also:
      IsDirectionalLight
    """
    start = rhutil.coerce3dpoint(start_point, True)
    end = rhutil.coerce3dpoint(end_point, True)
    light = Rhino.Geometry.Light()
    light.LightStyle = Rhino.Geometry.LightStyle.WorldDirectional
    light.Location = start
    light.Direction = end-start
    index = scriptcontext.doc.Lights.Add(light)
    if index<0: raise Exception("unable to add light to LightTable")
    rc = scriptcontext.doc.Lights[index].Id
    scriptcontext.doc.Views.Redraw()
    return rc


def AddLinearLight(start_point, end_point, width=None):
    """Adds a new linear light object to the document
    Parameters:
      start_point (point): starting point of the light
      end_point (point): ending point and direction of the light
      width (number): width of the light
    Returns:
      guid: identifier of the new object if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      start = rs.GetPoint("Light origin")
      if start:
          end = rs.GetPoint("Light length and direction", start)
          if end: rs.AddLinearLight(start, end)
    See Also:
      IsLinearLight
    """
    start = rhutil.coerce3dpoint(start_point, True)
    end = rhutil.coerce3dpoint(end_point, True)
    if width is None:
        radius=0.5
        units = scriptcontext.doc.ModelUnitSystem
        if units!=compat.ENUM_NONE(Rhino.UnitSystem):
            scale = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Inches, units)
            radius *= scale
        width = radius
    light = Rhino.Geometry.Light()
    light.LightStyle = Rhino.Geometry.LightStyle.WorldLinear
    light.Location = start
    v = end-start
    light.Direction = v
    light.Length = light.Direction
    light.Width = -light.Width
    plane = Rhino.Geometry.Plane(light.Location, light.Direction)
    xaxis = plane.XAxis
    xaxis.Unitize()
    plane.XAxis = xaxis
    light.Width = xaxis * min(width, v.Length/20)
    #light.Location = start - light.Direction
    index = scriptcontext.doc.Lights.Add(light)
    if index<0: raise Exception("unable to add light to LightTable")
    rc = scriptcontext.doc.Lights[index].Id
    scriptcontext.doc.Views.Redraw()
    return rc


def AddPointLight(point):
    """Adds a new point light object to the document
    Parameters:
      point (point): the 3d location of the point
    Returns:
      guid: identifier of the new object if successful
    Example:
      import rhinoscriptsyntax as rs
      point = rs.GetPoint("Point light location")
      if point: rs.AddPointLight(point)
    See Also:
      IsPointLight
    """
    point = rhutil.coerce3dpoint(point, True)
    light = Rhino.Geometry.Light()
    light.LightStyle = Rhino.Geometry.LightStyle.WorldPoint
    light.Location = point
    index = scriptcontext.doc.Lights.Add(light)
    if index<0: raise Exception("unable to add light to LightTable")
    rc = scriptcontext.doc.Lights[index].Id
    scriptcontext.doc.Views.Redraw()
    return rc


def AddRectangularLight(origin, width_point, height_point):
    """Adds a new rectangular light object to the document
    Parameters:
      origin (point): 3d origin point of the light
      width_point (point): 3d width and direction point of the light
      height_point (point): 3d height and direction point of the light
    Returns:
      guid: identifier of the new object if successful
    Example:
      import rhinoscriptsyntax as rs
      rect = rs.GetRectangle(2)
      if rect: rs.AddRectangularLight( rect[0], rect[1], rect[3] )
    See Also:
      IsRectangularLight
    """
    origin = rhutil.coerce3dpoint(origin, True)
    ptx = rhutil.coerce3dpoint(width_point, True)
    pty = rhutil.coerce3dpoint(height_point, True)
    length = pty-origin
    width = ptx-origin
    normal = Rhino.Geometry.Vector3d.CrossProduct(width, length)
    normal.Unitize()
    light = Rhino.Geometry.Light()
    light.LightStyle = Rhino.Geometry.LightStyle.WorldRectangular
    light.Location = origin
    light.Width = width
    light.Length = length
    light.Direction = normal
    index = scriptcontext.doc.Lights.Add(light)
    if index<0: raise Exception("unable to add light to LightTable")
    rc = scriptcontext.doc.Lights[index].Id
    scriptcontext.doc.Views.Redraw()
    return rc


def AddSpotLight(origin, radius, apex_point):
    """Adds a new spot light object to the document
    Parameters:
      origin (point): 3d origin point of the light
      radius (number):  radius of the cone
      apex_point (point): 3d apex point of the light
    Returns:
      guid: identifier of the new object
    Example:
      import rhinoscriptsyntax as rs
      radius = 5.0
      origin = rs.GetPoint("Base of cone")
      if origin:
          apex = rs.GetPoint("End of cone", origin)
          if apex: rs.AddSpotLight(origin, radius, apex)
    See Also:
      IsSpotLight
      SpotLightHardness
      SpotLightShadowIntensity
    """
    origin = rhutil.coerce3dpoint(origin, True)
    apex_point = rhutil.coerce3dpoint(apex_point, True)
    if radius<0: radius=1.0
    light = Rhino.Geometry.Light()
    light.LightStyle = Rhino.Geometry.LightStyle.WorldSpot
    light.Location = apex_point
    light.Direction = origin-apex_point
    light.SpotAngleRadians = math.atan(radius / (light.Direction.Length))
    light.HotSpot = 0.50
    index = scriptcontext.doc.Lights.Add(light)
    if index<0: raise Exception("unable to add light to LightTable")
    rc = scriptcontext.doc.Lights[index].Id
    scriptcontext.doc.Views.Redraw()
    return rc


def EnableLight(object_id, enable=None):
    """Enables or disables a light object
    Parameters:
      object_id (guid): the light object's identifier
      enable (bool, optional): the light's enabled status
    Returns:
      bool: if enable is not specified, the current enabled status
      bool: if enable is specified, the previous enabled status
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select light", rs.filter.light)
      if id: rs.EnableLight( id, False )
    See Also:
      IsLight
      IsLightEnabled
      LightColor
      LightCount
      LightName
      LightObjects
    """
    light = __coercelight(object_id, True)
    rc = light.IsEnabled
    if enable is not None and enable!=rc:
        light.IsEnabled = enable
        id = rhutil.coerceguid(object_id)
        if not scriptcontext.doc.Lights.Modify(id, light):
            return scriptcontext.errorhandler()
        scriptcontext.doc.Views.Redraw()
    return rc


def IsDirectionalLight(object_id):
    """Verifies a light object is a directional light
    Parameters:
      object_id (guid): the light object's identifier
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if rs.IsDirectionalLight(id):
          print("The object is a directional light.")
      else:
          print("The object is not a directional light.")
    See Also:
      AddDirectionalLight
    """
    light = __coercelight(object_id, True)
    return light.IsDirectionalLight


def IsLight(object_id):
    """Verifies an object is a light object
    Parameters:
      object_id (guid): the light object's identifier
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light")
      if rs.IsLight(id):
          print("The object is a light.")
      else:
          print("The object is not a light.")
    See Also:
      EnableLight
      IsLightEnabled
      LightColor
      LightCount
      LightName
      LightObjects
    """
    light = __coercelight(object_id, False)
    return light is not None


def IsLightEnabled(object_id):
    """Verifies a light object is enabled
    Parameters:
      object_id (guid): the light object's identifier
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if rs.IsLightEnabled(id):
          print("The light is enabled (on).")
      else:
          print("The light is disabled (off).")
    See Also:
      EnableLight
      IsLight
      LightColor
      LightCount
      LightName
      LightObjects
    """
    light = __coercelight(object_id, True)
    return light.IsEnabled


def IsLightReference(object_id):
    """Verifies a light object is referenced from another file
    Parameters:
      object_id (guid): the light object's identifier
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if rs.IsLightReference(id):
          print("The light is a reference object.")
      else:
          print("The light is not a reference object.")
    See Also:
      IsObjectReference
    """
    light = __coercelight(object_id, True)
    return light.IsReference


def IsLinearLight(object_id):
    """Verifies a light object is a linear light
    Parameters:
      object_id (guid): the light object's identifier
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if rs.IsLinearLight(id):
          print("The object is a linear light.")
      else:
          print("The object is not a linear light.")
    See Also:
      AddLinearLight
    """
    light = __coercelight(object_id, True)
    return light.IsLinearLight


def IsPointLight(object_id):
    """Verifies a light object is a point light
    Parameters:
      object_id (guid): the light object's identifier
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if rs.IsPointLight(id):
          print("The object is a point light.")
      else:
          print("The object is not a point light.")
    See Also:
      AddPointLight
    """
    light = __coercelight(object_id, True)
    return light.IsPointLight


def IsRectangularLight(object_id):
    """Verifies a light object is a rectangular light
    Parameters:
      object_id (guid): the light object's identifier
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if rs.IsRectangularLight(id):
          print("The object is a rectangular light.")
      else:
          print("The object is not a rectangular light.")
    See Also:
      AddRectangularLight
    """
    light = __coercelight(object_id, True)
    return light.IsRectangularLight


def IsSpotLight(object_id):
    """Verifies a light object is a spot light
    Parameters:
      object_id (guid): the light object's identifier
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if rs.IsSpotLight(id):
          print("The object is a spot light.")
      else:
          print("The object is not a spot light.")
    See Also:
      AddSpotLight
      SpotLightHardness
      SpotLightShadowIntensity
    """
    light = __coercelight(object_id, True)
    return light.IsSpotLight


def LightColor(object_id, color=None):
    """Returns or changes the color of a light
    Parameters:
      object_id (guid): the light object's identifier
      color (color, optional): the light's new color
    Returns:
      color: if color is not specified, the current color
      color: if color is specified, the previous color
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if id: rs.LightColor( id, (0,255,255) )
    See Also:
      EnableLight
      IsLight
      IsLightEnabled
      LightCount
      LightName
      LightObjects
    """
    light = __coercelight(object_id, True)
    rc = light.Diffuse
    if color:
        color = rhutil.coercecolor(color, True)
        if color!=rc:
            light.Diffuse = color
            id = rhutil.coerceguid(object_id, True)
            if not scriptcontext.doc.Lights.Modify(id, light):
                return scriptcontext.errorhandler()
            scriptcontext.doc.Views.Redraw()
    return rc


def LightCount():
    """Returns the number of light objects in the document
    Returns:
      number: the number of light objects in the document
    Example:
      import rhinoscriptsyntax as rs
      print("There are {} lights".format(rs.LightCount()))
    See Also:
      EnableLight
      IsLight
      IsLightEnabled
      LightColor
      LightName
      LightObjects
    """
    return scriptcontext.doc.Lights.Count


def LightDirection(object_id, direction=None):
    """Returns or changes the direction of a light object
    Parameters:
      object_id (guid): the light object's identifier
      direction (vector, optional): the light's new direction
    Returns:
      vector: if direction is not specified, the current direction
      vector: if direction is specified, the previous direction
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if id: print( rs.LightDirection(id) )
    See Also:
      IsLight
      LightLocation
    """
    light = __coercelight(object_id, True)
    rc = light.Direction
    if direction:
        direction = rhutil.coerce3dvector(direction, True)
        if direction!=rc:
            light.Direction = direction
            id = rhutil.coerceguid(object_id, True)
            if not scriptcontext.doc.Lights.Modify(id, light):
                return scriptcontext.errorhandler()
            scriptcontext.doc.Views.Redraw()
    return rc


def LightLocation(object_id, location=None):
    """Returns or changes the location of a light object
    Parameters:
      object_id (guid): the light object's identifier
      location (point, optional): the light's new location
    Returns:
      point: if location is not specified, the current location
      point: if location is specified, the previous location
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if id: rs.AddPoint( rs.LightLocation(id) )
    See Also:
      IsLight
      LightDirection
    """
    light = __coercelight(object_id, True)
    rc = light.Location
    if location:
        location = rhutil.coerce3dpoint(location, True)
        if location!=rc:
            light.Location = location
            id = rhutil.coerceguid(object_id, True)
            if not scriptcontext.doc.Lights.Modify(id, light):
                return scriptcontext.errorhandler()
            scriptcontext.doc.Views.Redraw()
    return rc


def LightName(object_id, name=None):
    """Returns or changes the name of a light object
    Parameters:
      object_id (guid): the light object's identifier
      name (str, optional): the light's new name
    Returns:
      str: if name is not specified, the current name
      str: if name is specified, the previous name
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if id:
          name = rs.GetString("New light name")
          if name: rs.LightName(id, name)
    See Also:
      EnableLight
      IsLight
      IsLightEnabled
      LightColor
      LightCount
      LightObjects
    """
    light = __coercelight(object_id, True)
    rc = light.Name
    if name and name!=rc:
        light.Name = name
        id = rhutil.coerceguid(object_id, True)
        if not scriptcontext.doc.Lights.Modify(id, light):
            return scriptcontext.errorhandler()
        scriptcontext.doc.Views.Redraw()
    return rc


def LightObjects():
    """Returns list of identifiers of light objects in the document
    Returns:
      list(guid, ...): the list of identifiers of light objects in the document
    Example:
      import rhinoscriptsyntax as rs
      lights = rs.LightObjects()
      if lights:
          rs.AddLayer( "Lights" )
          for light in lights: rs.ObjectLayer( light, "Lights" )
    See Also:
      EnableLight
      IsLight
      IsLightEnabled
      LightColor
      LightCount
      LightName
    """
    count = scriptcontext.doc.Lights.Count
    rc = []
    for i in range(count):
        rhlight = scriptcontext.doc.Lights[i]
        if not rhlight.IsDeleted: rc.append(rhlight.Id)
    return rc


def RectangularLightPlane(object_id):
    """Returns the plane of a rectangular light object
    Parameters:
      object_id (guid): the light object's identifier
    Returns:
      plane: the plane if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a rectangular light", rs.filter.light)
      if id:
          rc = rs.RectangularLightPlane(id)
          if rc:
              plane, extents = rc
              rs.AddPlaneSurface( plane, extents[0], extents[1] )
    See Also:
      IsRectangularLight
    """
    light = __coercelight(object_id, True)
    if light.LightStyle!=Rhino.Geometry.LightStyle.WorldRectangular:
        return scriptcontext.errorhandler()
    location = light.Location
    length = light.Length
    width = light.Width
    direction = light.Direction
    plane = Rhino.Geometry.Plane(location, length, width)
    return plane, (length.Length, width.Length)


def SpotLightHardness(object_id, hardness=None):
    """Returns or changes the hardness of a spot light. Spotlight hardness
    controls the fully illuminated region.
    Parameters:
      object_id (guid): the light object's identifier
      hardness (number, optional): the light's new hardness
    Returns:
      number: if hardness is not specified, the current hardness
      number: if hardness is specified, the previous hardness
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if id: rs.SpotLightHardness(id, 0.75)
    See Also:
      AddSpotLight
      IsSpotLight
      SpotLightRadius
      SpotLightShadowIntensity
    """
    light = __coercelight(object_id, True)
    if light.LightStyle!=Rhino.Geometry.LightStyle.WorldSpot:
        return scriptcontext.errorhandler()
    rc = light.HotSpot
    if hardness and hardness!=rc:
        light.HotSpot = hardness
        id = rhutil.coerceguid(object_id, True)
        if not scriptcontext.doc.Lights.Modify(id, light):
            return scriptcontext.errorhandler()
        scriptcontext.doc.Views.Redraw()
    return rc


def SpotLightRadius(object_id, radius=None):
    """Returns or changes the radius of a spot light.
    Parameters:
      object_id (guid): the light object's identifier
      radius (number, optional): the light's new radius
    Returns:
      number: if radius is not specified, the current radius
      number: if radius is specified, the previous radius
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if id: rs.SpotLightRadius(id, 5.0)
    See Also:
      AddSpotLight
      IsSpotLight
      SpotLightHardness
      SpotLightShadowIntensity
    """
    light = __coercelight(object_id, True)
    if light.LightStyle!=Rhino.Geometry.LightStyle.WorldSpot:
        return scriptcontext.errorhandler()
    radians = light.SpotAngleRadians
    rc = light.Direction.Length * math.tan(radians)
    if radius and radius!=rc:
        radians = math.atan(radius/light.Direction.Length)
        light.SpotAngleRadians = radians
        id = rhutil.coerceguid(object_id, True)
        if not scriptcontext.doc.Lights.Modify(id, light):
            return scriptcontext.errorhandler()
        scriptcontext.doc.Views.Redraw()
    return rc


def SpotLightShadowIntensity(object_id, intensity=None):
    """Returns or changes the shadow intensity of a spot light.
    Parameters:
      object_id (guid): the light object's identifier
      intensity (number, optional): the light's new intensity
    Returns:
      number: if intensity is not specified, the current intensity
      number: if intensity is specified, the previous intensity
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select a light", rs.filter.light)
      if id: rs.SpotLightShadowIntensity(id, 0.75)
    See Also:
      AddSpotLight
      IsSpotLight
      SpotLightHardness
      SpotLightRadius
    """
    light = __coercelight(object_id, True)
    if light.LightStyle!=Rhino.Geometry.LightStyle.WorldSpot:
        return scriptcontext.errorhandler()
    rc = light.SpotLightShadowIntensity
    if intensity and intensity!=rc:
        light.SpotLightShadowIntensity = intensity
        id = rhutil.coerceguid(object_id, True)
        if not scriptcontext.doc.Lights.Modify(id, light):
            return scriptcontext.errorhandler()
        scriptcontext.doc.Views.Redraw()
    return rc
