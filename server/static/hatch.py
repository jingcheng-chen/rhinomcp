import System

import Rhino

import scriptcontext

from rhinoscript import utility as rhutil


def __initHatchPatterns():
    if scriptcontext.doc.HatchPatterns.FindName(Rhino.DocObjects.HatchPattern.Defaults.Solid.Name) is None:
        scriptcontext.doc.HatchPatterns.Add(Rhino.DocObjects.HatchPattern.Defaults.Solid)

    if scriptcontext.doc.HatchPatterns.FindName(Rhino.DocObjects.HatchPattern.Defaults.Hatch1.Name) is None:
        scriptcontext.doc.HatchPatterns.Add(Rhino.DocObjects.HatchPattern.Defaults.Hatch1)

    if scriptcontext.doc.HatchPatterns.FindName(Rhino.DocObjects.HatchPattern.Defaults.Hatch2.Name) is None:
        scriptcontext.doc.HatchPatterns.Add(Rhino.DocObjects.HatchPattern.Defaults.Hatch2)

    if scriptcontext.doc.HatchPatterns.FindName(Rhino.DocObjects.HatchPattern.Defaults.Hatch3.Name) is None:
        scriptcontext.doc.HatchPatterns.Add(Rhino.DocObjects.HatchPattern.Defaults.Hatch3)

    if scriptcontext.doc.HatchPatterns.FindName(Rhino.DocObjects.HatchPattern.Defaults.Dash.Name) is None:
        scriptcontext.doc.HatchPatterns.Add(Rhino.DocObjects.HatchPattern.Defaults.Dash)

    if scriptcontext.doc.HatchPatterns.FindName(Rhino.DocObjects.HatchPattern.Defaults.Grid.Name) is None:
        scriptcontext.doc.HatchPatterns.Add(Rhino.DocObjects.HatchPattern.Defaults.Grid)

    if scriptcontext.doc.HatchPatterns.FindName(Rhino.DocObjects.HatchPattern.Defaults.Grid60.Name) is None:
        scriptcontext.doc.HatchPatterns.Add(Rhino.DocObjects.HatchPattern.Defaults.Grid60)

    if scriptcontext.doc.HatchPatterns.FindName(Rhino.DocObjects.HatchPattern.Defaults.Plus.Name) is None:
        scriptcontext.doc.HatchPatterns.Add(Rhino.DocObjects.HatchPattern.Defaults.Plus)

    if scriptcontext.doc.HatchPatterns.FindName(Rhino.DocObjects.HatchPattern.Defaults.Squares.Name) is None:
        scriptcontext.doc.HatchPatterns.Add(Rhino.DocObjects.HatchPattern.Defaults.Squares)


def AddHatch(curve_id, hatch_pattern=None, scale=1.0, rotation=0.0):
    """Creates a new hatch object from a closed planar curve object
    Parameters:
      curve_id (guid): identifier of the closed planar curve that defines the
          boundary of the hatch object
      hatch_pattern (str, optional): name of the hatch pattern to be used by the hatch
          object. If omitted, the current hatch pattern will be used
      scale (number, optional): hatch pattern scale factor
      rotation (number, optional): hatch pattern rotation angle in degrees.
    Returns:
      guid:identifier of the newly created hatch on success
      None on error
    Example:
      import rhinoscriptsyntax as rs
      circle = rs.AddCircle(rs.WorldXYPlane(), 10.0)
      if rs.IsHatchPattern("Grid"):
          rs.AddHatch( circle, "Grid" )
      else:
          rs.AddHatch( circle, rs.CurrentHatchPattern() )
    See Also:
      AddHatches
      CurrentHatchPattern
      HatchPatternNames
    """
    rc = AddHatches(curve_id, hatch_pattern, scale, rotation)
    if rc: return rc[0]
    return scriptcontext.errorhandler()


def AddHatches(curve_ids, hatch_pattern=None, scale=1.0, rotation=0.0, tolerance=None):
    """Creates one or more new hatch objects a list of closed planar curves
    Parameters:
      curve_ids ([guid, ...]): identifiers of the closed planar curves that defines the
          boundary of the hatch objects
      hatch_pattern (str, optional):  name of the hatch pattern to be used by the hatch
          object. If omitted, the current hatch pattern will be used
      scale (number, optional): hatch pattern scale factor
      rotation (number, optional): hatch pattern rotation angle in degrees.
      tolerance (number, optional): tolerance for hatch fills.
    Returns:
      list(guid, ...): identifiers of the newly created hatch on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      curves = rs.GetObjects("Select closed planar curves", rs.filter.curve)
      if curves:
          if rs.IsHatchPattern("Grid"):
              rs.AddHatches( curves, "Grid" )
          else:
              rs.AddHatches( curves, rs.CurrentHatchPattern() )
    See Also:
      AddHatch
      CurrentHatchPattern
      HatchPatternNames
    """
    __initHatchPatterns()
    id = rhutil.coerceguid(curve_ids, False)
    if id: curve_ids = [id]
    index = scriptcontext.doc.HatchPatterns.CurrentHatchPatternIndex
    if hatch_pattern is None:
        hatch_pattern = CurrentHatchPattern()
    if isinstance(hatch_pattern, int) and hatch_pattern != index:
        index = hatch_pattern
    else:
        pattern_instance = scriptcontext.doc.HatchPatterns.FindName(hatch_pattern)
        index = Rhino.RhinoMath.UnsetIntIndex if pattern_instance is None else pattern_instance.Index
    if index<0: return scriptcontext.errorhandler()
    curves = [rhutil.coercecurve(id, -1, True) for id in curve_ids]
    rotation = Rhino.RhinoMath.ToRadians(rotation)
    if tolerance is None or tolerance < 0:
        tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    hatches = Rhino.Geometry.Hatch.Create(curves, index, rotation, scale, tolerance)
    if not hatches: return scriptcontext.errorhandler()
    ids = []
    for hatch in hatches:
        id = scriptcontext.doc.Objects.AddHatch(hatch)
        if id==System.Guid.Empty: continue
        ids.append(id)
    if not ids: return scriptcontext.errorhandler()
    scriptcontext.doc.Views.Redraw()
    return ids


def AddHatchPatterns(filename, replace=False):
    """Adds hatch patterns to the document by importing hatch pattern definitions
    from a pattern file.
    Parameters:
      filename (str): name of the hatch pattern file
      replace (bool, optional): If hatch pattern names already in the document match hatch
          pattern names in the pattern definition file, then the existing hatch
          patterns will be redefined
    Returns:
      list(str, ...): Names of the newly added hatch patterns if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      filename = rs.OpenFileName("Import", "Pattern Files (*.pat)|*.pat||")
      if filename:
          patterns = rs.AddHatchPatterns(filename)
          if patterns:
              for pattern in patterns: print(pattern)
    See Also:
      HatchPatternCount
      HatchPatternNames
    """
    patterns = Rhino.DocObjects.HatchPattern.ReadFromFile(filename, True)
    if not patterns: return scriptcontext.errorhandler()
    rc = []
    for pattern in patterns:
         index = scriptcontext.doc.HatchPatterns.Add(pattern)
         if index>=0:
             pattern = scriptcontext.doc.HatchPatterns[index]
             rc.append(pattern.Name)
    if not rc: return scriptcontext.errorhandler()
    return rc


def CurrentHatchPattern(hatch_pattern=None):
    """Returns or sets the current hatch pattern file
    Parameters:
      hatch_pattern(str, optional):  name of an existing hatch pattern to make current
    Returns:
      str: if hatch_pattern is not specified, the current hatch pattern
      str: if hatch_pattern is specified, the previous hatch pattern
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      if rs.IsHatchPattern("Hatch2"): rs.CurrentHatchPattern("Hatch2")
    See Also:
      HatchPatternCount
      HatchPatternNames
    """
    i = scriptcontext.doc.HatchPatterns.CurrentHatchPatternIndex
    rc = scriptcontext.doc.HatchPatterns[i].Name
    if hatch_pattern:
        __initHatchPatterns()
        pattern_instance = scriptcontext.doc.HatchPatterns.FindName(hatch_pattern)
        if pattern_instance is None: return scriptcontext.errorhandler()
        scriptcontext.doc.HatchPatterns.CurrentHatchPatternIndex = pattern_instance.Index
    return rc


def ExplodeHatch(hatch_id, delete=False):
    """Explodes a hatch object into its component objects. The exploded objects
    will be added to the document. If the hatch object uses a solid pattern,
    then planar face Brep objects will be created. Otherwise, line curve objects
    will be created
    Parameters:
      hatch_id (guid): identifier of a hatch object
      delete (bool, optional): delete the hatch object
    Returns:
      list(guid, ...): list of identifiers for the newly created objects
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object")
      if rs.IsHatch(id): rs.ExplodeHatch(id, True)
    See Also:
      IsHatch
      HatchPattern
      HatchRotation
      HatchScale
    """
    rhobj = rhutil.coercerhinoobject(hatch_id, True, True)
    pieces = rhobj.HatchGeometry.Explode()
    if not pieces: return scriptcontext.errorhandler()
    attr = rhobj.Attributes
    rc = []
    for piece in pieces:
        id = None
        if isinstance(piece, Rhino.Geometry.Curve):
            id = scriptcontext.doc.Objects.AddCurve(piece, attr)
        elif isinstance(piece, Rhino.Geometry.Brep):
            id = scriptcontext.doc.Objects.AddBrep(piece, attr)
        if id: rc.append(id)
    if delete: scriptcontext.doc.Objects.Delete(rhobj)
    return rc


def HatchPattern(hatch_id, hatch_pattern=None):
    """Returns or changes a hatch object's hatch pattern
    Parameters:
      hatch_id (guid): identifier of a hatch object
      hatch_pattern (str, optional): name of an existing hatch pattern to replace the
          current hatch pattern
    Returns:
      str: if hatch_pattern is not specified, the current hatch pattern
      str: if hatch_pattern is specified, the previous hatch pattern
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.AllObjects()
      if objects is not None:
          for obj in objects:
              if rs.IsHatch(obj) and rs.HatchPattern(obj)=="Solid":
                  rs.SelectObject(obj)
    See Also:
      AddHatch
      AddHatches
      HatchRotation
      HatchScale
      IsHatch
    """
    hatchobj = rhutil.coercerhinoobject(hatch_id, True, True)
    if not isinstance(hatchobj, Rhino.DocObjects.HatchObject):
        return scriptcontext.errorhandler()
    old_index = hatchobj.HatchGeometry.PatternIndex
    if hatch_pattern:
        __initHatchPatterns()
        new_patt = scriptcontext.doc.HatchPatterns.FindName(hatch_pattern)
        if new_patt is None: return scriptcontext.errorhandler()
        hatchobj.HatchGeometry.PatternIndex = new_patt.Index
        hatchobj.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return scriptcontext.doc.HatchPatterns[old_index].Name


def HatchPatternCount():
    """Returns the number of hatch patterns in the document
    Returns:
      number: the number of hatch patterns in the document
    Example:
      import rhinoscriptsyntax as rs
      print("There are {} hatch patterns.".format(rs.HatchPatternCount()))
    See Also:
      HatchPatternNames
    """
    __initHatchPatterns()
    return scriptcontext.doc.HatchPatterns.Count


def HatchPatternDescription(hatch_pattern):
    """Returns the description of a hatch pattern. Note, not all hatch patterns
    have descriptions
    Parameters:
      hatch_pattern (str): name of an existing hatch pattern
    Returns:
      str: description of the hatch pattern on success otherwise None
    Example:
      import rhinoscriptsyntax as rs
      patterns = rs.HatchPatternNames()
      for pattern in patterns:
          description = rs.HatchPatternDescription(pattern)
          if description: print("{} - {}".format(pattern, description))
          else: print(pattern)
    See Also:
      HatchPatternCount
      HatchPatternNames
    """
    __initHatchPatterns()
    pattern_instance = scriptcontext.doc.HatchPatterns.FindName(hatch_pattern)
    if pattern_instance is None: return scriptcontext.errorhandler()
    return pattern_instance.Description


def HatchPatternFillType(hatch_pattern):
    """Returns the fill type of a hatch pattern.
    Parameters:
      hatch_pattern (str): name of an existing hatch pattern
    Returns:
      number: hatch pattern's fill type if successful
              0 = solid, uses object color
              1 = lines, uses pattern file definition
              2 = gradient, uses fill color definition
      None: if unsuccessful
    Example:
      import rhinoscriptsyntax as rs
      patterns = rs.HatchPatternNames()
      for pattern in patterns:
          fill = rs.HatchPatternFillType(pattern)
          print("{} - {}".format(pattern, fill))
    See Also:
      HatchPatternCount
      HatchPatternNames
    """
    __initHatchPatterns()
    pattern_instance = scriptcontext.doc.HatchPatterns.FindName(hatch_pattern)
    if pattern_instance is None: return scriptcontext.errorhandler()
    return int(pattern_instance.FillType)


def HatchPatternNames():
    """Returns the names of all of the hatch patterns in the document
    Returns:
      list(str, ...): the names of all of the hatch patterns in the document
    Example:
      import rhinoscriptsyntax as rs
      patterns = rs.HatchPatternNames()
      for pattern in patterns:
          description = rs.HatchPatternDescription(pattern)
          if description: print("{} - {}".format(pattern, description))
          else: print(pattern)
    See Also:
      HatchPatternCount
    """
    __initHatchPatterns()
    rc = []
    for i in range(scriptcontext.doc.HatchPatterns.Count):
        hatchpattern = scriptcontext.doc.HatchPatterns[i]
        if hatchpattern.IsDeleted: continue
        rc.append(hatchpattern.Name)
    return rc


def HatchRotation(hatch_id, rotation=None):
    """Returns or modifies the rotation applied to the hatch pattern when
    it is mapped to the hatch's plane
    Parameters:
      hatch_id (guid): identifier of a hatch object
      rotation (number, optional): rotation angle in degrees
    Returns:
      number: if rotation is not defined, the current rotation angle
      number: if rotation is specified, the previous rotation angle
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.AllObjects()
      if objects:
          for obj in objects:
              if rs.IsHatch(obj) and rs.HatchRotation(obj)>0:
                  rs.HatchRotation(obj,0)
    See Also:
      AddHatch
      AddHatches
      HatchPattern
      HatchScale
      IsHatch
    """
    hatchobj = rhutil.coercerhinoobject(hatch_id, True, True)
    if not isinstance(hatchobj, Rhino.DocObjects.HatchObject):
        return scriptcontext.errorhandler()
    rc = hatchobj.HatchGeometry.PatternRotation
    rc = Rhino.RhinoMath.ToDegrees(rc)
    if rotation is not None and rotation!=rc:
        rotation = Rhino.RhinoMath.ToRadians(rotation)
        hatchobj.HatchGeometry.PatternRotation = rotation
        hatchobj.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def HatchScale(hatch_id, scale=None):
    """Returns or modifies the scale applied to the hatch pattern when it is
    mapped to the hatch's plane
    Parameters:
      hatch_id (guid): identifier of a hatch object
      scale (number, optional):  scale factor
    Returns:
      number: if scale is not defined, the current scale factor
      number: if scale is defined, the previous scale factor
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.NormalObjects()
      if objects:
          for obj in objects:
              if rs.IsHatch(obj) and rs.HatchScale(obj)>1.0:
                  rs.HatchScale(obj, 1.0)
    See Also:
      HatchPattern
      HatchRotation
      IsHatch
    """
    hatchobj = rhutil.coercerhinoobject(hatch_id)
    if not isinstance(hatchobj, Rhino.DocObjects.HatchObject):
        return scriptcontext.errorhandler()
    rc = hatchobj.HatchGeometry.PatternScale
    if scale and scale!=rc:
        hatchobj.HatchGeometry.PatternScale = scale
        hatchobj.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def IsHatch(object_id):
    """Verifies the existence of a hatch object in the document
    Parameters:
      object_id (guid): identifier of an object
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if rs.IsHatch(obj): print("Object is a hatch")
      else: print("Object is not a hatch")
    See Also:
      HatchPattern
      HatchRotation
      HatchScale
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, False)
    return isinstance(rhobj, Rhino.DocObjects.HatchObject)


def IsHatchPattern(name):
    """Verifies the existence of a hatch pattern in the document
    Parameters:
      name (str): the name of a hatch pattern
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      hatch = rs.GetString("Hatch pattern name")
      if rs.IsHatchPattern(hatch): print("The hatch pattern exists.")
      else: print("The hatch pattern does not exist.")
    See Also:
      IsHatchPatternCurrent
      IsHatchPatternReference
    """
    __initHatchPatterns()
    return scriptcontext.doc.HatchPatterns.FindName(name) is not None


def IsHatchPatternCurrent(hatch_pattern):
    """Verifies that a hatch pattern is the current hatch pattern
    Parameters:
      hatch_pattern (str): name of an existing hatch pattern
    Returns:
      bool: True or False
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      hatch = rs.GetString("Hatch pattern name")
      if rs.IsHatchPattern(hatch):
          if rs.IsHatchPatternCurrent(hatch):
              print("The hatch pattern is current.")
          else:
              print("The hatch pattern is not current.")
      else: print("The hatch pattern does not exist.")
    See Also:
      IsHatchPattern
      IsHatchPatternReference
    """
    __initHatchPatterns()
    pattern_instance = scriptcontext.doc.HatchPatterns.FindName(hatch_pattern)
    if pattern_instance is None: return scriptcontext.errorhandler()
    return pattern_instance.Index==scriptcontext.doc.HatchPatterns.CurrentHatchPatternIndex


def IsHatchPatternReference(hatch_pattern):
    """Verifies that a hatch pattern is from a reference file
    Parameters:
      hatch_pattern (str): name of an existing hatch pattern
    Returns:
      bool: True or False
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      hatch = rs.GetString("Hatch pattern name")
      if rs.IsHatchPattern(hatch):
          if rs.IsHatchPatternReference(hatch):
              print("The hatch pattern is reference.")
          else:
              print("The hatch pattern is not reference.")
      else:
          print("The hatch pattern does not exist.")
    See Also:
      IsHatchPattern
      IsHatchPatternCurrent
    """
    __initHatchPatterns()
    pattern_instance = scriptcontext.doc.HatchPatterns.FindName(hatch_pattern)
    if pattern_instance is None: return scriptcontext.errorhandler()
    return pattern_instance.IsReference
