import System

import Rhino

import scriptcontext

from rhinoscript import utility as rhutil
from rhinoscript.view import __viewhelper, ViewCPlane


def __coerceannotation(object_id):
    annotation_object = rhutil.coercerhinoobject(object_id, True)
    if not isinstance(annotation_object, Rhino.DocObjects.AnnotationObjectBase):
        raise ValueError("object_id does not refer to an Annotation")
    return annotation_object


def AddAlignedDimension(start_point, end_point, point_on_dimension_line, style=None):
    """Adds an aligned dimension object to the document. An aligned dimension
    is a linear dimension lined up with two points
    Parameters:
      start_point (point): first point of dimension
      end_point (point): second point of dimension
      point_on_dimension_line (point): location point of dimension line
      style (str, optional): name of dimension style
    Returns:
      guid: identifier of new dimension on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      origin = 1, 1, 0
      offset = 11, 5, 0
      point = 1, 3, 0
      rs.AddAlignedDimension( origin, offset, point )
    See Also:
      IsAlignedDimension
    """
    start = rhutil.coerce3dpoint(start_point, True)
    end = rhutil.coerce3dpoint(end_point, True)
    onpoint = rhutil.coerce3dpoint(point_on_dimension_line, True)
    plane = Rhino.Geometry.Plane(start, end, onpoint)
    if not plane.IsValid:
      # usually when points passed to ctor are colinear
      plane = ViewCPlane()
    success, s, t = plane.ClosestParameter(start)
    start = Rhino.Geometry.Point2d(s,t)
    success, s, t = plane.ClosestParameter(end)
    end = Rhino.Geometry.Point2d(s,t)
    success, s, t = plane.ClosestParameter(onpoint)
    onpoint = Rhino.Geometry.Point2d(s,t)
    ldim = Rhino.Geometry.LinearDimension(plane, start, end, onpoint)
    if not ldim: return scriptcontext.errorhandler()
    ldim.Aligned = True
    if style:
        ds = scriptcontext.doc.DimStyles.FindName(style)
        if ds is None: return scriptcontext.errorhandler()
        ldim.DimensionStyleId = ds.Id
    rc = scriptcontext.doc.Objects.AddLinearDimension(ldim)
    if rc==System.Guid.Empty: raise Exception("unable to add dimension to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddDimStyle(dimstyle_name=None):
    """Adds a new dimension style to the document. The new dimension style will
    be initialized with the current default dimension style properties.
    Parameters:
      dimstyle_name (str, optional): name of the new dimension style. If omitted, Rhino automatically generates the dimension style name
    Returns:
      str: name of the new dimension style on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      print("New dimension style: {}".format(rs.AddDimStyle()))
      print("New dimension style: {}".format(rs.AddDimStyle("MyDimStyle")))
    See Also:
      CurrentDimStyle
      DeleteDimStyle
      IsDimStyle
      RenameDimStyle
    """
    index = scriptcontext.doc.DimStyles.Add(dimstyle_name)
    if index<0: return scriptcontext.errorhandler()
    ds = scriptcontext.doc.DimStyles[index]
    return ds.Name


def AddLeader(points, view_or_plane=None, text=None):
    """Adds a leader to the document. Leader objects are planar.
    The 3D points passed to this function should be co-planar
    Parameters:
      points ([point, point, ....])list of (at least 2) 3D points
      view_or_plane (str, optional): If a view name is specified, points will be constrained
        to the view's construction plane. If a view is not specified, points
        will be constrained to a plane fit through the list of points
      text (str, optional): leader's text string
    Returns:
      guid: identifier of the new leader on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints(True, False, "Select leader points")
      if points: rs.AddLeader( points )
    See Also:
      IsLeader
      LeaderText
    """
    points = rhutil.coerce3dpointlist(points)
    if points is None or len(points)<2: raise ValueError("points must have at least two items")
    rc = System.Guid.Empty
    view = None
    if text and not isinstance(text, str): 
        text = str(text)

    if not view_or_plane:
        if len(points) == 2:
            plane = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane()
            rc = scriptcontext.doc.Objects.AddLeader(text, plane, [Rhino.Geometry.Point2d(p.X, p.Y) for p in points])
        else:
            rc = scriptcontext.doc.Objects.AddLeader(text, points)
    else:
        plane = rhutil.coerceplane(view_or_plane)
        if not plane:
            view = __viewhelper(view_or_plane)
            plane = view.ActiveViewport.ConstructionPlane()
        points2d = []
        for point in points:
            cprc, s, t = plane.ClosestParameter( point )
            if not cprc: return scriptcontext.errorhandler()
            points2d.append( Rhino.Geometry.Point2d(s,t) )
        if text is None:
            rc = scriptcontext.doc.Objects.AddLeader(plane, points2d)
        else:
            if not isinstance(text, str): text = str(text)
            rc = scriptcontext.doc.Objects.AddLeader(text, plane, points2d)
    if rc==System.Guid.Empty: return scriptcontext.errorhandler()
    scriptcontext.doc.Views.Redraw()
    return rc


def AddLinearDimension(plane, start_point, end_point, point_on_dimension_line):
    """Adds a linear dimension to the document
    Parameters:
      plane (plane): The plane on which the dimension will lie.
      start_point (point): The origin, or first point of the dimension.
      end_point (point): The offset, or second point of the dimension.
      point_on_dimension_line (point): A point that lies on the dimension line.
    Returns:
      guid: identifier of the new object on success
      None: on error
    Example:
      import rhinoscriptsyntax as  rs
      points = rs.GetPoints(True,  False, "Select 3 dimension points")
      if points and len(points)>2:
          rs.AddLinearDimension(rs.WorldXYPlane(),  points[0], points[1], points[2] )
    See Also:
      IsLeader
      LeaderText
    """
    if not plane: 
      plane = ViewCPlane()
    else:
      plane = rhutil.coerceplane(plane, True)
    start = rhutil.coerce3dpoint(start_point, True)
    plane.Origin = start
    end = rhutil.coerce3dpoint(end_point, True)
    onpoint = rhutil.coerce3dpoint(point_on_dimension_line, True)
    # Calculate 2d dimension points
    success, s, t = plane.ClosestParameter(start)
    start = Rhino.Geometry.Point2d(s,t)
    success, s, t = plane.ClosestParameter(end)
    end = Rhino.Geometry.Point2d(s,t)
    success, s, t = plane.ClosestParameter(onpoint)
    onpoint = Rhino.Geometry.Point2d(s,t)    
    # Add the dimension
    ldim = Rhino.Geometry.LinearDimension(plane, start, end, onpoint)
    if not ldim: return scriptcontext.errorhandler()
    rc = scriptcontext.doc.Objects.AddLinearDimension(ldim)
    if rc==System.Guid.Empty: raise Exception("unable to add dimension to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def CurrentDimStyle(dimstyle_name=None):
    """Returns or changes the current default dimension style
    Parameters:
      dimstyle_name (str, optional): name of an existing dimension style to make current
    Returns:
      str: if dimstyle_name is not specified, name of the current dimension style
      str: if dimstyle_name is specified, name of the previous dimension style
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      rs.AddDimStyle("MyDimStyle")
      rs.CurrentDimStyle("MyDimStyle")
    See Also:
      AddDimStyle
      DeleteDimStyle
      IsDimStyle
      RenameDimStyle
    """
    rc = scriptcontext.doc.DimStyles.Current.Name
    if dimstyle_name:
        ds = scriptcontext.doc.DimStyles.FindName(dimstyle_name)
        if ds is None: return scriptcontext.errorhandler()
        scriptcontext.doc.DimStyles.SetCurrent(ds.Index, False)
    return rc


def DeleteDimStyle(dimstyle_name):
    """Removes an existing dimension style from the document. The dimension style
    to be removed cannot be referenced by any dimension objects.
    Parameters:
      dimstyle_name (str): the name of an unreferenced dimension style
    Returns:
      str: The name of the deleted dimension style if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.GetString("Dimension style to remove")
      if dimstyle: rs.DeleteDimStyle(dimstyle)
    See Also:
      AddDimStyle
      CurrentDimStyle
      IsDimStyle
      RenameDimStyle
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle_name)
    if ds and scriptcontext.doc.DimStyles.DeleteDimensionStyle(ds.Index, True):
        return dimstyle_name
    return scriptcontext.errorhandler()


def DimensionStyle(object_id, dimstyle_name=None):
    """Returns or modifies the dimension style of a dimension object
    Parameters:
      object_id (guid): identifier of the object
      dimstyle_name (str, optional): the name of an existing dimension style
    Returns:
      str: if dimstyle_name is not specified, the object's current dimension style name
      str: if dimstyle_name is specified, the object's previous dimension style name
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsDimension(obj): rs.DimensionStyle(obj, "Default")
    See Also:
      DimStyleNames
      IsDimStyle
    """
    annotation_object = __coerceannotation(object_id)
    ds = annotation_object.AnnotationGeometry.ParentDimensionStyle
    rc = ds.Name
    if dimstyle_name:
        ds = scriptcontext.doc.DimStyles.FindName(dimstyle_name)
        if not ds: return scriptcontext.errorhandler()
        annotation = annotation_object.Geometry
        annotation.DimensionStyleId = ds.Id
        annotation_object.CommitChanges()
    return rc


def DimensionText(object_id):
    """Returns the text displayed by a dimension object
    Parameters:
      object_id (guid): identifier of the object
    Returns:
      str: the text displayed by a dimension object
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsDimension(obj):
          print(rs.DimensionText(obj))
    See Also:
      DimensionUserText
      DimensionValue
      IsDimension
    """
    annotation_object = __coerceannotation(object_id)
    return annotation_object.DisplayText


def DimensionUserText(object_id, usertext=None):
    """Returns of modifies the user text string of a dimension object. The user
    text is the string that gets printed when the dimension is defined
    Parameters:
      object_id (guid): identifier of the object
      usertext (str, optional): the new user text string value
    Returns:
      str: if usertext is not specified, the current usertext string
      str: if usertext is specified, the previous usertext string
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsDimension(obj):
          usertext = "!= " + chr(177) + str(rs.UnitAbsoluteTolerance())
          rs.DimensionUserText( obj, usertext )
    See Also:
      DimensionText
      DimensionValue
      IsDimension
    """
    annotation_object = __coerceannotation(object_id)
    rc = annotation_object.Geometry.Text
    if usertext is not None:
        annotation_object.Geometry.Text = usertext
        annotation_object.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def DimensionValue(object_id):
    """Returns the value of a dimension object
    Parameters:
      object_id (guid): identifier of the object
    Returns:
      number: numeric value of the dimension if successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsDimension(obj):
          print(rs.DimensionValue(obj))
    See Also:
      DimensionText
      DimensionUserText
      IsDimension
    """
    annotation_object = __coerceannotation(object_id)
    return annotation_object.Geometry.NumericValue


def DimStyleAnglePrecision(dimstyle, precision=None):
    """Returns or changes the angle display precision of a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      precision (number, optional): the new angle precision value. If omitted, the current angle
        precision is returned
    Returns:
      number: If a precision is not specified, the current angle precision
      number: If a precision is specified, the previous angle precision
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      precision = rs.DimStyleAnglePrecision(dimstyle)
      if precision>2:
          rs.DimStyleAnglePrecision( dimstyle, 2 )
    See Also:
      DimStyleArrowSize
      DimStyleExtension
      DimStyleFont
      DimStyleLinearPrecision
      DimStyleNumberFormat
      DimStyleOffset
      DimStyleTextAlignment
      DimStyleTextHeight
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.AngleResolution
    if precision is not None:
        ds.AngleResolution = precision
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleArrowSize(dimstyle, size=None):
    """Returns or changes the arrow size of a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      size (number, optional): the new arrow size. If omitted, the current arrow size is returned
    Returns:
      number: If size is not specified, the current arrow size
      number: If size is specified, the previous arrow size
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      size = rs.DimStyleArrowSize(dimstyle)
      if size>1.0: rs.DimStyleArrowSize( dimstyle, 1.0 )
    See Also:
      DimStyleAnglePrecision
      DimStyleExtension
      DimStyleFont
      DimStyleLinearPrecision
      DimStyleNumberFormat
      DimStyleOffset
      DimStyleTextAlignment
      DimStyleTextHeight
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.ArrowLength
    if size is not None:
        ds.ArrowLength = size
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleCount():
    """Returns the number of dimension styles in the document
    Returns:
      number: the number of dimension styles in the document
    Example:
      import rhinoscriptsyntax as rs
      count = rs.DimStyleCount()
      print("There are", count, "dimension styles.")
    See Also:
      DimStyleNames
      IsDimStyle
    """
    return scriptcontext.doc.DimStyles.Count


def DimStyleExtension(dimstyle, extension=None):
    """Returns or changes the extension line extension of a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      extension (number, optional): the new extension line extension
    Returns:
      number: if extension is not specified, the current extension line extension
      number: if extension is specified, the previous extension line extension
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      extension = rs.DimStyleExtension(dimstyle)
      if extension>0.5: rs.DimStyleExtension( dimstyle, 0.5 )
    See Also:
      DimStyleAnglePrecision
      DimStyleArrowSize
      DimStyleFont
      DimStyleLinearPrecision
      DimStyleNumberFormat
      DimStyleOffset
      DimStyleTextAlignment
      DimStyleTextHeight
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.ExtensionLineExtension
    if extension is not None:
        ds.ExtensionLineExtension = extension
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleFont(dimstyle, font=None):
    """Returns or changes the font used by a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      font (str, optional): the new font face name
    Returns:
      str: if font is not specified, the current font if successful
      str: if font is specified, the previous font if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      font = rs.DimStyleFont(dimstyle)
      if font!="Arial": rs.DimStyleFont( dimstyle, "Arial" )
    See Also:
      DimStyleAnglePrecision
      DimStyleArrowSize
      DimStyleExtension
      DimStyleLinearPrecision
      DimStyleNumberFormat
      DimStyleOffset
      DimStyleTextAlignment
      DimStyleTextHeight
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.Font.FaceName
    if font:
        newindex = scriptcontext.doc.Fonts.FindOrCreate(font, False, False)
        ds.Font = scriptcontext.doc.Fonts[newindex]
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleLeaderArrowSize(dimstyle, size=None):
    """Returns or changes the leader arrow size of a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      size (number, optional) the new leader arrow size
    Returns:
      number: if size is not specified, the current leader arrow size
      number: if size is specified, the previous leader arrow size
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      size = rs.DimStyleLeaderArrowSize(dimstyle)
      if size>1.0: rs.DimStyleLeaderArrowSize( dimstyle, 1.0 )
    See Also:
      DimStyleAnglePrecision
      DimStyleArrowSize
      DimStyleExtension
      DimStyleFont
      DimStyleLinearPrecision
      DimStyleNumberFormat
      DimStyleOffset
      DimStyleTextAlignment
      DimStyleTextHeight
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.LeaderArrowLength
    if size is not None:
        ds.LeaderArrowLength = size
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleLengthFactor(dimstyle, factor=None):
    """Returns or changes the length factor of a dimension style. Length factor
    is the conversion between Rhino units and dimension units
    Parameters:
      dimstyle (str): the name of an existing dimension style
      factor (number, optional): the new length factor
    Returns:
      number: if factor is not defined, the current length factor
      number: if factor is defined, the previous length factor
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      factor = rs.DimStyleLengthFactor(dimstyle)
      if factor>1.0: rs.DimStyleLengthFactor( dimstyle, 1.0 )
    See Also:
      DimStylePrefix
      DimStyleSuffix
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.LengthFactor
    if factor is not None:
        ds.LengthFactor = factor
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleLinearPrecision(dimstyle, precision=None):
    """Returns or changes the linear display precision of a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      precision (number, optional): the new linear precision value
    Returns:
      number: if precision is not specified, the current linear precision value
      number: if precision is specified, the previous linear precision value
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      precision = rs.DimStyleLinearPrecision(dimstyle)
      if precision>2: rs.DimStyleLinearPrecision( dimstyle, 2 )
    See Also:
      DimStyleAnglePrecision
      DimStyleArrowSize
      DimStyleExtension
      DimStyleFont
      DimStyleNumberFormat
      DimStyleOffset
      DimStyleTextAlignment
      DimStyleTextHeight
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.LengthResolution
    if precision is not None:
        ds.LengthResolution = precision
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleNames(sort=False):
    """Returns the names of all dimension styles in the document
    Parameters:
      sort (bool): sort the list if True, not sorting is the default (False)
    Returns:
      list(str, ...): the names of all dimension styles in the document
    Example:
      import rhinoscriptsyntax as rs
      dimstyles = rs.DimStyleNames()
      if dimstyles:
          for dimstyle in dimstyles: print(dimstyle)
    See Also:
      DimStyleCount
      IsDimStyle
    """
    rc = [ds.Name for ds in scriptcontext.doc.DimStyles]
    if sort: rc.sort()
    return rc


def DimStyleNumberFormat(dimstyle, format=None):
    """Returns or changes the number display format of a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      format (number, optional) the new number format
         0 = Decimal
         1 = Fractional
         2 = Feet and inches
    Returns:
      number: if format is not specified, the current display format
      number: if format is specified, the previous display format
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      format = rs.DimStyleNumberFormat(dimstyle)
      if format>0: rs.DimStyleNumberFormat( dimstyle, 0 )
    See Also:
      DimStyleAnglePrecision
      DimStyleArrowSize
      DimStyleExtension
      DimStyleFont
      DimStyleLinearPrecision
      DimStyleOffset
      DimStyleTextAlignment
      DimStyleTextHeight
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = int(ds.LengthFormat)
    if format is not None:
        if format==0: ds.LengthFormat = Rhino.DocObjects.DistanceDisplayMode.Decimal
        if format==1: ds.LengthFormat = Rhino.DocObjects.DistanceDisplayMode.Feet
        if format==2: ds.LengthFormat = Rhino.DocObjects.DistanceDisplayMode.FeetAndInches
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleOffset(dimstyle, offset=None):
    """Returns or changes the extension line offset of a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      offset (number, optional): the new extension line offset
    Returns:
      number: if offset is not specified, the current extension line offset
      number: if offset is specified, the previous extension line offset
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      offset = rs.DimStyleOffset(dimstyle)
      if offset>0.5: rs.DimStyleOffset( dimstyle, 0.5 )
    See Also:
      DimStyleAnglePrecision
      DimStyleArrowSize
      DimStyleExtension
      DimStyleFont
      DimStyleLinearPrecision
      DimStyleNumberFormat
      DimStyleTextAlignment
      DimStyleTextHeight
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.ExtensionLineOffset
    if offset is not None:
        ds.ExtensionLineOffset = offset
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStylePrefix(dimstyle, prefix=None):
    """Returns or changes the prefix of a dimension style - the text to
    prefix to the dimension text.
    Parameters:
      dimstyle (str): the name of an existing dimstyle
      prefix (str, optional): the new prefix
    Returns:
      str: if prefix is not specified, the current prefix
      str: if prefix is specified, the previous prefix
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      rs.DimStylePrefix( dimstyle, "[" )
    See Also:
      DimStyleLengthFactor
      DimStyleSuffix
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.Prefix
    if prefix is not None:
        ds.Prefix = prefix
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleScale(dimstyle, scale=None):
    """Returns or modifies the scale of a dimension style.
    Parameters:
      dimstyle (str): the name of an existing dimstyle
      scale (number, optional): the new scale value
    Returns:
      number: if scale is not specified, the current scale
      number: if scale is specified, the previous scale
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      from scriptcontext import doc
      dimstyle = doc.DimStyles.Current
      scale = rs.DimStyleScale(dimstyle)
      rs.DimStyleScale(dimstyle, scale*2.0)
    See Also:
      DimStyleTextHeight
      DimStyleOffset
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.DimensionScale
    if scale is not None:
        ds.DimensionScale = scale
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleSuffix(dimstyle, suffix=None):
    """Returns or changes the suffix of a dimension style - the text to
    append to the dimension text.
    Parameters:
      dimstyle (str): the name of an existing dimstyle
      suffix (str, optional): the new suffix
    Returns:
      str: if suffix is not specified, the current suffix
      str: if suffix is specified, the previous suffix
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      rs.DimStyleSuffix( dimstyle, "}" )
    See Also:
      DimStyleLengthFactor
      DimStylePrefix
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.Suffix
    if suffix is not None:
        ds.Suffix = suffix
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleTextAlignment(dimstyle, alignment=None):
    """Returns or changes the text alignment mode of a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      alignment (number, optional): the new text alignment
          0 = Normal (same as 2)
          1 = Horizontal to view
          2 = Above the dimension line
          3 = In the dimension line
    Returns:
      number: if alignment is not specified, the current text alignment
      number: if alignment is specified, the previous text alignment
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      alignment = rs.DimStyleTextAlignment(dimstyle)
      if alignment!=2: rs.DimStyleTextAlignment( dimstyle, 2 )
    See Also:
      DimStyleAnglePrecision
      DimStyleArrowSize
      DimStyleExtension
      DimStyleFont
      DimStyleLinearPrecision
      DimStyleNumberFormat
      DimStyleOffset
      DimStyleTextHeight
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    # NOTE:
    # this function is about text alignment so return alignment value
    rc = int(ds.DimTextLocation)
    if alignment is not None:
        # NOTE:
        # for backward compatibility, lets set the "horizontal to view" if
        # alignment value is '1' - eirannejad 2025-03-17 (RH-86539)
        if alignment==1: ds.DimTextOrientation = Rhino.DocObjects.TextOrientation.InView

        # set dim text location
        if alignment==3: ds.DimTextLocation = Rhino.DocObjects.DimensionStyle.TextLocation.InDimLine
        if alignment==0 or alignment==2:
          ds.DimTextLocation = Rhino.DocObjects.DimensionStyle.TextLocation.AboveDimLine  # default

        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleTextGap(dimstyle, gap=None):
    """Returns or changes the text gap used by a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      gap (number, optional): the new text gap
    Returns:
      number: if gap is not specified, the current text gap
      number: if gap is specified, the previous text gap
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      gap = rs.DimStyleTextGap(dimstyle)
      if gap>0.25: rs.DimStyleTextGap( dimstyle, 0.25 )
    See Also:
      DimStyleAnglePrecision
      DimStyleArrowSize
      DimStyleExtension
      DimStyleFont
      DimStyleLinearPrecision
      DimStyleNumberFormat
      DimStyleOffset
      DimStyleTextAlignment
      DimStyleTextHeight
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.TextGap
    if gap is not None:
        ds.TextGap = gap
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def DimStyleTextHeight(dimstyle, height=None):
    """Returns or changes the text height used by a dimension style
    Parameters:
      dimstyle (str): the name of an existing dimension style
      height (number, optional): the new text height
    Returns:
      number: if height is not specified, the current text height
      number: if height is specified, the previous text height
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.CurrentDimStyle()
      height = rs.DimStyleTextHeight(dimstyle)
      if offset>1.0: rs.DimStyleTextHeight( dimstyle, 1.0 )
    See Also:
      DimStyleAnglePrecision
      DimStyleArrowSize
      DimStyleExtension
      DimStyleFont
      DimStyleLinearPrecision
      DimStyleNumberFormat
      DimStyleOffset
      DimStyleTextAlignment
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    rc = ds.TextHeight
    if height:
        ds.TextHeight = height
        scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False)
        scriptcontext.doc.Views.Redraw()
    return rc


def IsAlignedDimension(object_id):
    """Verifies an object is an aligned dimension object
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True or False.  None on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsAlignedDimension(obj):
          print("The object is an aligned dimension.")
      else:
          print("The object is not an aligned dimension.")
    See Also:
      IsAngularDimension
      IsDiameterDimension
      IsDimension
      IsLinearDimension
      IsOrdinateDimension
      IsRadialDimension
    """
    annotation_object = __coerceannotation(object_id)
    id = rhutil.coerceguid(object_id, True)
    annotation_object = scriptcontext.doc.Objects.Find(id)
    geom = annotation_object.Geometry
    if isinstance(geom, Rhino.Geometry.LinearDimension): return geom.Aligned
    return False


def IsAngularDimension(object_id):
    """Verifies an object is an angular dimension object
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True or False.
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsAngularDimension(obj):
          print("The object is an angular dimension.")
      else:
          print("The object is not an angular dimension.")
    See Also:
      IsAlignedDimension
      IsDiameterDimension
      IsDimension
      IsLinearDimension
      IsOrdinateDimension
      IsRadialDimension
    """
    id = rhutil.coerceguid(object_id, True)
    annotation_object = scriptcontext.doc.Objects.Find(id)
    geom = annotation_object.Geometry
    return isinstance(geom, Rhino.Geometry.AngularDimension)


def IsDiameterDimension(object_id):
    """Verifies an object is a diameter dimension object
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True or False.
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsDiameterDimension(obj):
          print("The object is a diameter dimension.")
      else:
          print("The object is not a diameter dimension.")
    See Also:
      IsAlignedDimension
      IsAngularDimension
      IsDimension
      IsLinearDimension
      IsOrdinateDimension
      IsRadialDimension
    """
    id = rhutil.coerceguid(object_id, True)
    annotation_object = scriptcontext.doc.Objects.Find(id)
    geom = annotation_object.Geometry
    if isinstance(geom, Rhino.Geometry.RadialDimension):
        return geom.IsDiameterDimension
    return False


def IsDimension(object_id):
    """Verifies an object is a dimension object
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True or False.
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsDimension(obj):
          print("The object is a dimension.")
      else:
          print("The object is not a dimension.")
    See Also:
      IsAlignedDimension
      IsAngularDimension
      IsDiameterDimension
      IsLinearDimension
      IsOrdinateDimension
      IsRadialDimension
    """
    id = rhutil.coerceguid(object_id, True)
    annotation_object = scriptcontext.doc.Objects.Find(id)
    geom = annotation_object.Geometry
    return isinstance(geom, Rhino.Geometry.AnnotationBase)


def IsDimStyle(dimstyle):
    """Verifies the existance of a dimension style in the document
    Parameters:
      dimstyle (str): the name of a dimstyle to test for
    Returns:
      bool: True or False.
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.GetString("Dimension style to test")
      if rs.IsDimStyle(dimstyle):
          if rs.IsDimStyleReference(dimstyle):
              print("The dimension style is from a reference file.")
          else:
              print("The dimension style is not from a reference file.")
      else:
          print("The dimension style does not exist.")
    See Also:
      IsDimStyleReference
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    return ds is not None


def IsDimStyleReference(dimstyle):
    """Verifies that an existing dimension style is from a reference file
    Parameters:
      dimstyle (str): the name of an existing dimension style
    Returns:
      bool: True or False.
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      dimstyle = rs.GetString("Dimension style to test")
      if rs.IsDimStyle(dimstyle):
          if rs.IsDimStyleReference(dimstyle):
              print("The dimension style is from a reference file.")
          else:
              print("The dimension style is not from a reference file.")
      else:
          print("The dimension style does not exist.")
    See Also:
      IsDimStyle
    """
    ds = scriptcontext.doc.DimStyles.FindName(dimstyle)
    if ds is None: return scriptcontext.errorhandler()
    return ds.IsReference


def IsLeader(object_id):
    """Verifies an object is a dimension leader object
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True or False.
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a leader")
      if rs.IsLeader(obj):
          print("The object is a leader.")
      else:
          print("The object is not a leader.")
    See Also:
      AddLeader
      LeaderText
    """
    id = rhutil.coerceguid(object_id, True)
    annotation_object = scriptcontext.doc.Objects.Find(id)
    geom = annotation_object.Geometry
    return isinstance(geom, Rhino.Geometry.Leader)


def IsLinearDimension(object_id):
    """Verifies an object is a linear dimension object
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True or False.
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsLinearDimension(obj):
          print("The object is a linear dimension.")
      else:
          print("The object is not a linear dimension.")
    See Also:
      IsAlignedDimension
      IsAngularDimension
      IsDiameterDimension
      IsDimension
      IsOrdinateDimension
      IsRadialDimension
    """
    id = rhutil.coerceguid(object_id, True)
    annotation_object = scriptcontext.doc.Objects.Find(id)
    geom = annotation_object.Geometry
    return isinstance(geom, Rhino.Geometry.LinearDimension)


def IsOrdinateDimension(object_id):
    """Verifies an object is an ordinate dimension object
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True or False.
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsOrdinateDimension(obj):
          print("The object is an ordinate dimension.")
      else:
          print("The object is not an ordinate dimension.")
    See Also:
      IsAlignedDimension
      IsAngularDimension
      IsDiameterDimension
      IsDimension
      IsLinearDimension
      IsRadialDimension
    """
    id = rhutil.coerceguid(object_id, True)
    annotation_object = scriptcontext.doc.Objects.Find(id)
    geom = annotation_object.Geometry
    return isinstance(geom, Rhino.Geometry.OrdinateDimension)


def IsRadialDimension(object_id):
    """Verifies an object is a radial dimension object
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True or False.
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a dimension")
      if rs.IsRadialDimension(obj):
          print("The object is a radial dimension.")
      else:
          print("The object is not a radial dimension.")
    See Also:
      IsAlignedDimension
      IsAngularDimension
      IsDiameterDimension
      IsDimension
      IsLinearDimension
      IsOrdinateDimension
    """
    id = rhutil.coerceguid(object_id, True)
    annotation_object = scriptcontext.doc.Objects.Find(id)
    geom = annotation_object.Geometry
    return isinstance(geom, Rhino.Geometry.RadialDimension)


def LeaderText(object_id, text=None):
    """Returns or modifies the text string of a dimension leader object
    Parameters:
      object_id (guid): the object's identifier
      text (string, optional): the new text string
    Returns:
      str: if text is not specified, the current text string
      str: if text is specified, the previous text string
      None on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a leader")
      if rs.IsLeader(obj): print(rs.LeaderText(obj))
    See Also:
      AddLeader
      IsLeader
    """
    id = rhutil.coerceguid(object_id, True)
    annotation_object = scriptcontext.doc.Objects.Find(id)
    geom = annotation_object.Geometry
    if not isinstance(geom, Rhino.Geometry.Leader):
        return scriptcontext.errorhandler()
    rc = annotation_object.DisplayText
    if text is not None:
        geom.RichText = text
        annotation_object.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def RenameDimStyle(oldstyle, newstyle):
    """Renames an existing dimension style
    Parameters:
      oldstyle (str): the name of an existing dimension style
      newstyle (str): the new dimension style name
    Returns:
      str: the new dimension style name if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      oldstyle = rs.GetString("Old dimension style name")
      if oldstyle:
          newstyle = rs.GetString("New dimension style name")
          if newstyle: rs.RenameDimStyle( oldstyle, newstyle )
    See Also:
      AddDimStyle
      CurrentDimStyle
      DeleteDimStyle
      IsDimStyle
    """
    ds = scriptcontext.doc.DimStyles.FindName(oldstyle)
    if not ds: return scriptcontext.errorhandler()
    ds.Name = newstyle
    if scriptcontext.doc.DimStyles.Modify(ds, ds.Id, False): return newstyle
    return None
