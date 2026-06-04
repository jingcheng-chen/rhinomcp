import math

import System
import System.Drawing
import System.IO

import Rhino

import scriptcontext

from rhinoscript import utility as rhutil


def _SetRenderMeshAndUpdateStyle(current):
    scriptcontext.doc.SetCustomMeshingParameters(current)
    scriptcontext.doc.MeshingParameterStyle = Rhino.Geometry.MeshingParameterStyle.Custom


def CreatePreviewImage(filename, view=None, size=None, flags=0, wireframe=False):
    """Create a bitmap preview image of the current model
    Parameters:
      filename (str): name of the bitmap file to create
      view (str, optional): title of the view. If omitted, the active view is used
      size (number, optional): two integers that specify width and height of the bitmap
      flags (number, optional): Bitmap creation flags. Can be the combination of:
          1 = honor object highlighting
          2 = draw construction plane
          4 = use ghosted shading
      wireframe (bool, optional): If True then a wireframe preview image. If False,
          a rendered image will be created
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as  rs
      result = rs.CreatePreviewImage("test.jpg")
      if result:
          print( "test.jpg created successfully.")
      else:
          print( "Unable to create preview image.")
    See Also:
      ExtractPreviewImage
    """
    rhview = scriptcontext.doc.Views.ActiveView
    if view is not None:
        rhview = scriptcontext.doc.Views.Find(view, False)
        if rhview is None: return False
    rhsize = rhview.ClientRectangle.Size
    if size: rhsize = System.Drawing.Size(size[0], size[1])
    ignore_highlights = (flags&1)!=1
    drawcplane = (flags&2)==2
    useghostedshading = (flags&4)==4
    if wireframe:
        return rhview.CreateWireframePreviewImage(filename, rhsize, ignore_highlights, drawcplane)
    else:
        return rhview.CreateShadedPreviewImage(filename, rhsize, ignore_highlights, drawcplane, useghostedshading)


def DocumentModified(modified=None):
    """Returns or sets the document's modified flag. This flag indicates whether
    or not any changes to the current document have been made. NOTE: setting the
    document modified flag to False will prevent the "Do you want to save this
    file..." from displaying when you close Rhino.
    Parameters:
      modified (bool): the modified state, either True or False
    Returns:
      bool: if no modified state is specified, the current modified state
      bool: if a modified state is specified, the previous modified state
    Example:
      import rhinoscriptsyntax as rs
      modified = rs.IsDocumentModified()
      if not modified: rs.DocumentModified(True)
    See Also:
      IsDocumentModified
    """
    oldstate = scriptcontext.doc.Modified
    if modified is not None and modified!=oldstate:
        scriptcontext.doc.Modified = modified
    return oldstate


def DocumentName():
    """Returns the name of the currently loaded Rhino document (3DM file)
    Returns:
      str: the name of the currently loaded Rhino document (3DM file)
    Example:
      import rhinoscriptsyntax as rs
      name = rs.DocumentName()
      print(name)
    See Also:
      DocumentPath
    """
    return scriptcontext.doc.Name or None


def DocumentPath():
    """Returns path of the currently loaded Rhino document (3DM file)
    Returns:
      str: the path of the currently loaded Rhino document (3DM file)
    Example:
      import rhinoscriptsyntax as rs
      path = rs.DocumentPath()
      print(path)
    See Also:
      DocumentName
    """
    # GetDirectoryName throws an exception if an empty string is passed hence the 'or None'
    path = System.IO.Path.GetDirectoryName(scriptcontext.doc.Path or None)
    # add \ or / at the end to be consistent with RhinoScript
    if path and not path.endswith(str(System.IO.Path.DirectorySeparatorChar)):
      path += System.IO.Path.DirectorySeparatorChar
    return path


def EnableRedraw(enable=True):
    """Enables or disables screen redrawing
    Parameters:
      enable (bool, optional): True to enable, False to disable
    Returns: 
      bool: previous screen redrawing state
    Example:
      import rhinoscriptsyntax as rs
      redraw = rs.EnableRedraw(True)
    See Also:
      Redraw
    """
    old = scriptcontext.doc.Views.RedrawEnabled
    if old!=enable: scriptcontext.doc.Views.RedrawEnabled = enable
    return old


def ExtractPreviewImage(filename, modelname=None):
    """Extracts the bitmap preview image from the specified model (.3dm)
    Parameters:
      filename (str): name of the bitmap file to create. The extension of
         the filename controls the format of the bitmap file created.
         (.bmp, .tga, .jpg, .jpeg, .pcx, .png, .tif, .tiff)
      modelname (str, optional): The model (.3dm) from which to extract the
         preview image. If omitted, the currently loaded model is used.
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      result = rs.ExtractPreviewImage("test.jpg")
      if result:
          print("Test.jpg created successfully.")
      else:
          print("Unable to extract preview image.")
    See Also:
      CreatePreviewImage
    """
    return scriptcontext.doc.ExtractPreviewImage(filename, modelname)


def IsDocumentModified():
    """Verifies that the current document has been modified in some way
    Returns:
      bool: True or False. None on error
    Example:
      import rhinoscriptsyntax as rs
      modified = rs.IsDocumentModified()
      if not modified: rs.DocumentModified(True)
    See Also:
      DocumentModified
    """
    return scriptcontext.doc.Modified


def Notes(newnotes=None):
    """Returns or sets the document's notes. Notes are generally created
    using Rhino's Notes command
    Parameters:
      newnotes (str): new notes to set
    Returns:
      str: if `newnotes` is omitted, the current notes if successful
      str: if `newnotes` is specified, the previous notes if successful
    Example:
      import rhinoscriptsyntax as rs
      notes = rs.Notes()
      if notes: rs.MessageBox(notes)
    See Also:
      
    """
    old = scriptcontext.doc.Notes
    if newnotes is not None: scriptcontext.doc.Notes = newnotes
    return old


def ReadFileVersion():
    """Returns the file version of the current document. Use this function to
    determine which version of Rhino last saved the document. Note, this
    function will not return values from referenced or merged files.
    Returns:
      str: the file version of the current document
    Example:
      import rhinoscriptsyntax as rs
      print("ReadFileVersion = {}".format(rs.ReadFileVersion()))
    See Also:
      DocumentName
      DocumentPath
    """
    return scriptcontext.doc.ReadFileVersion()


def Redraw():
    """Redraws all views
    Returns:
      None 
    Example:
      import rhinoscriptsyntax as rs
      rs.Redraw()
    See Also:
      EnableRedraw
    """
    old = scriptcontext.doc.Views.RedrawEnabled
    scriptcontext.doc.Views.RedrawEnabled = True
    scriptcontext.doc.Views.Redraw()
    Rhino.RhinoApp.Wait()
    scriptcontext.doc.Views.RedrawEnabled = old


def RenderAntialias(style=None):
    """Returns or sets render antialiasing style
    Parameters:
      style (number, optional): level of antialiasing (0=none, 1=normal, 2=best)
    Returns:
      number: if style is not specified, the current antialiasing style
      number: if style is specified, the previous antialiasing style
    Example:
      import rhinoscriptsyntax as rs
      rs.RenderAntialias(1)
    See Also:
      RenderColor
      RenderResolution
      RenderSettings
    """
    rc = scriptcontext.doc.RenderSettings.AntialiasLevel
    if style==0 or style==1 or style==2:
        settings = scriptcontext.doc.RenderSettings
        settings.AntialiasLevel = style
        scriptcontext.doc.RenderSettings = settings
    return rc


def RenderColor(item, color=None):
    """Returns or sets the render ambient light or background color
    Parameters:
      item (number): 0=ambient light color, 1=background color
      color (color, optional): the new color value. If omitted, the current item color is returned
    Returns:
      color: if color is not specified, the current item color
      color: if color is specified, the previous item color
    Example:
      import rhinoscriptsyntax as rs
      render_background_color = 1
      rs.RenderColor( render_background_color, (0,0,255) )
    See Also:
      RenderAntialias
      RenderResolution
      RenderSettings
    """
    if item!=0 and item!=1: raise ValueError("item must be 0 or 1")
    if item==0: rc = scriptcontext.doc.RenderSettings.AmbientLight
    else: rc = scriptcontext.doc.RenderSettings.BackgroundColorTop
    if color is not None:
        color = rhutil.coercecolor(color, True)
        settings = scriptcontext.doc.RenderSettings
        if item==0: settings.AmbientLight = color
        else: settings.BackgroundColorTop = color
        scriptcontext.doc.RenderSettings = settings
        scriptcontext.doc.Views.Redraw()
    return rc


def RenderResolution(resolution=None):
    """Returns or sets the render resolution
    Parameters:
      resolution ([number, number], optional): width and height of render
    Returns:
      tuple(number, number): if resolution is not specified, the current resolution width,height
      tuple(number, number): if resolution is specified, the previous resolution width, height
    Example:
      import rhinoscriptsyntax as rs
      sizex, sizey = rs.Viewsize()
      resolution = sizex/2 , sizey/2
      rs.RenderResolution( resolution )
    See Also:
      RenderAntialias
      RenderColor
      RenderSettings
    """
    rc = scriptcontext.doc.RenderSettings.ImageSize
    if resolution:
        settings = scriptcontext.doc.RenderSettings
        settings.ImageSize = System.Drawing.Size(resolution[0], resolution[1])
        scriptcontext.doc.RenderSettings = settings
    return rc.Width, rc.Height


def RenderMeshDensity(density=None):
    """Returns or sets the render mesh density property of the active document.
        For more information on render meshes, see the Document Properties: Mesh topic in the Rhino help file.
    Parameters:
      density (number, optional): the new render mesh density, which is a number between 0.0 and 1.0.
    Returns:
      number: if density is not specified, the current render mesh density if successful.
      number: if density is specified, the previous render mesh density if successful.
    Example:
      import rhinoscriptsyntax as  rs
      print("Quality: %s" % rs.RenderMeshQuality())
      print("Mesh density: %s" % rs.RenderMeshDensity())
      print("Maximum angle: %s" % rs.RenderMeshMaxAngle())
      print("Maximum aspect ratio: %s" % rs.RenderMeshMaxAspectRatio())
      print("Minimun edge length: %s" % rs.RenderMeshMinEdgeLength())
      print("Maximum edge length: %s" % rs.RenderMeshMaxEdgeLength())
      print("Maximum distance, edge to surface: %s" % rs.RenderMeshMaxDistEdgeToSrf())
      print("Minumum initial grid quads: %s" % rs.RenderMeshMinInitialGridQuads())
      print("Other settings: %s" % rs.RenderMeshSettings())
    See Also:
      RenderMeshDensity
      RenderMeshMaxAngle
      RenderMeshMaxAspectRatio
      RenderMeshMaxDistEdgeToSrf
      RenderMeshMaxEdgeLength
      RenderMeshMinEdgeLength
      RenderMeshMinInitialGridQuads
      RenderMeshQuality
      RenderMeshSettings
    """
    current = scriptcontext.doc.GetCurrentMeshingParameters()
    rc = current.RelativeTolerance
    if density is not None:
        if Rhino.RhinoMath.Clamp(density, 0.0, 1.0) != density: return None
        current.RelativeTolerance = density
        _SetRenderMeshAndUpdateStyle(current)
    return rc


def RenderMeshMaxAngle(angle_degrees=None):
    """Returns or sets the render mesh maximum angle property of the active document.  
      For more information on render meshes, see the Document Properties: Mesh topic in the Rhino help file.
    Parameters:
      angle_degrees (number, optional): the new maximum angle, which is a positive number in degrees.
    Returns:
      number: if angle_degrees is not specified, the current maximum angle if successful.
      number: if angle_degrees is specified, the previous maximum angle if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as  rs
      print("Quality: %s" % rs.RenderMeshQuality())
      print("Mesh density: %s" % rs.RenderMeshDensity())
      print("Maximum angle: %s" % rs.RenderMeshMaxAngle())
      print("Maximum aspect ratio: %s" % rs.RenderMeshMaxAspectRatio())
      print("Minimun edge length: %s" % rs.RenderMeshMinEdgeLength())
      print("Maximum edge length: %s" % rs.RenderMeshMaxEdgeLength())
      print("Maximum distance, edge to surface: %s" % rs.RenderMeshMaxDistEdgeToSrf())
      print("Minumum initial grid quads: %s" % rs.RenderMeshMinInitialGridQuads())
      print("Other settings: %s" % rs.RenderMeshSettings())
    See Also:
      RenderMeshDensity
      RenderMeshMaxAngle
      RenderMeshMaxAspectRatio
      RenderMeshMaxDistEdgeToSrf
      RenderMeshMaxEdgeLength
      RenderMeshMinEdgeLength
      RenderMeshMinInitialGridQuads
      RenderMeshQuality
      RenderMeshSettings
    """
    current = scriptcontext.doc.GetCurrentMeshingParameters()
    rc = math.degrees(current.RefineAngle)
    if angle_degrees is not None:
        if angle_degrees < 0: return None
        current.RefineAngle = math.radians(angle_degrees)
        _SetRenderMeshAndUpdateStyle(current)
    return rc


def RenderMeshMaxAspectRatio(ratio=None):
    """Returns or sets the render mesh maximum aspect ratio property of the active document.
      For more information on render meshes, see the Document Properties: Mesh topic in the Rhino help file.
     Parameters:
      ratio (number, optional): the render mesh maximum aspect ratio.  The suggested range, when not zero, is from 1 to 100.
    Returns:
      number: if ratio is not specified, the current render mesh maximum aspect ratio if successful.
      number: if ratio is specified, the previous render mesh maximum aspect ratio if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as  rs
      print("Quality: %s" % rs.RenderMeshQuality())
      print("Mesh density: %s" % rs.RenderMeshDensity())
      print("Maximum angle: %s" % rs.RenderMeshMaxAngle())
      print("Maximum aspect ratio: %s" % rs.RenderMeshMaxAspectRatio())
      print("Minimun edge length: %s" % rs.RenderMeshMinEdgeLength())
      print("Maximum edge length: %s" % rs.RenderMeshMaxEdgeLength())
      print("Maximum distance, edge to surface: %s" % rs.RenderMeshMaxDistEdgeToSrf())
      print("Minumum initial grid quads: %s" % rs.RenderMeshMinInitialGridQuads())
      print("Other settings: %s" % rs.RenderMeshSettings())
    See Also:
      RenderMeshDensity
      RenderMeshMaxAngle
      RenderMeshMaxAspectRatio
      RenderMeshMaxDistEdgeToSrf
      RenderMeshMaxEdgeLength
      RenderMeshMinEdgeLength
      RenderMeshMinInitialGridQuads
      RenderMeshQuality
      RenderMeshSettings
    """
    current = scriptcontext.doc.GetCurrentMeshingParameters()
    rc = current.GridAspectRatio
    if ratio is not None:
        current.GridAspectRatio = ratio
        _SetRenderMeshAndUpdateStyle(current)
    return rc


def RenderMeshMaxDistEdgeToSrf(distance=None):
    """Returns or sets the render mesh maximum distance, edge to surface parameter of the active document.
      For more information on render meshes, see the Document Properties: Mesh topic in the Rhino help file.
    Parameters:
      distance (number, optional): the render mesh maximum distance, edge to surface.
    Returns:
      number: if distance is not specified, the current render mesh maximum distance, edge to surface if successful.
      number: if distance is specified, the previous render mesh maximum distance, edge to surface if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as  rs
      print("Quality: %s" % rs.RenderMeshQuality())
      print("Mesh density: %s" % rs.RenderMeshDensity())
      print("Maximum angle: %s" % rs.RenderMeshMaxAngle())
      print("Maximum aspect ratio: %s" % rs.RenderMeshMaxAspectRatio())
      print("Minimun edge length: %s" % rs.RenderMeshMinEdgeLength())
      print("Maximum edge length: %s" % rs.RenderMeshMaxEdgeLength())
      print("Maximum distance, edge to surface: %s" % rs.RenderMeshMaxDistEdgeToSrf())
      print("Minumum initial grid quads: %s" % rs.RenderMeshMinInitialGridQuads())
      print("Other settings: %s" % rs.RenderMeshSettings())
    See Also:
      RenderMeshDensity
      RenderMeshMaxAngle
      RenderMeshMaxAspectRatio
      RenderMeshMaxDistEdgeToSrf
      RenderMeshMaxEdgeLength
      RenderMeshMinEdgeLength
      RenderMeshMinInitialGridQuads
      RenderMeshQuality
      RenderMeshSettings
    """
    current = scriptcontext.doc.GetCurrentMeshingParameters()
    rc = current.Tolerance
    if distance is not None:
        current.Tolerance = distance
        _SetRenderMeshAndUpdateStyle(current)
    return rc


def RenderMeshMaxEdgeLength(distance=None):
    """Returns or sets the render mesh maximum edge length parameter of the active document.
      For more information on render meshes, see the Document Properties: Mesh topic in the Rhino help file.
    Parameters:
      distance (number, optional): the render mesh maximum edge length.
    Returns:
      number: if distance is not specified, the current render mesh maximum edge length if successful.
      number: if distance is specified, the previous render mesh maximum edge length if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as  rs
      print("Quality: %s" % rs.RenderMeshQuality())
      print("Mesh density: %s" % rs.RenderMeshDensity())
      print("Maximum angle: %s" % rs.RenderMeshMaxAngle())
      print("Maximum aspect ratio: %s" % rs.RenderMeshMaxAspectRatio())
      print("Minimun edge length: %s" % rs.RenderMeshMinEdgeLength())
      print("Maximum edge length: %s" % rs.RenderMeshMaxEdgeLength())
      print("Maximum distance, edge to surface: %s" % rs.RenderMeshMaxDistEdgeToSrf())
      print("Minumum initial grid quads: %s" % rs.RenderMeshMinInitialGridQuads())
      print("Other settings: %s" % rs.RenderMeshSettings())
    See Also:
      RenderMeshDensity
      RenderMeshMaxAngle
      RenderMeshMaxAspectRatio
      RenderMeshMaxDistEdgeToSrf
      RenderMeshMaxEdgeLength
      RenderMeshMinEdgeLength
      RenderMeshMinInitialGridQuads
      RenderMeshQuality
      RenderMeshSettings
    """
    current = scriptcontext.doc.GetCurrentMeshingParameters()
    rc = current.MaximumEdgeLength
    if distance is not None:
        current.MaximumEdgeLength = distance
        _SetRenderMeshAndUpdateStyle(current)
    return rc


def RenderMeshMinEdgeLength(distance=None):
    """Returns or sets the render mesh minimum edge length parameter of the active document.
      For more information on render meshes, see the Document Properties: Mesh topic in the Rhino help file.
        Parameters:
      distance (number, optional): the render mesh minimum edge length.
    Returns:
      number: if distance is not specified, the current render mesh minimum edge length if successful.
      number: if distance is specified, the previous render mesh minimum edge length if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as  rs
      print("Quality: %s" % rs.RenderMeshQuality())
      print("Mesh density: %s" % rs.RenderMeshDensity())
      print("Maximum angle: %s" % rs.RenderMeshMaxAngle())
      print("Maximum aspect ratio: %s" % rs.RenderMeshMaxAspectRatio())
      print("Minimun edge length: %s" % rs.RenderMeshMinEdgeLength())
      print("Maximum edge length: %s" % rs.RenderMeshMaxEdgeLength())
      print("Maximum distance, edge to surface: %s" % rs.RenderMeshMaxDistEdgeToSrf())
      print("Minumum initial grid quads: %s" % rs.RenderMeshMinInitialGridQuads())
      print("Other settings: %s" % rs.RenderMeshSettings())
    See Also:
      RenderMeshDensity
      RenderMeshMaxAngle
      RenderMeshMaxAspectRatio
      RenderMeshMaxDistEdgeToSrf
      RenderMeshMaxEdgeLength
      RenderMeshMinEdgeLength
      RenderMeshMinInitialGridQuads
      RenderMeshQuality
      RenderMeshSettings
    """
    current = scriptcontext.doc.GetCurrentMeshingParameters()
    rc = current.MinimumEdgeLength
    if distance is not None:
        current.MinimumEdgeLength = distance
        _SetRenderMeshAndUpdateStyle(current)
    return rc


def RenderMeshMinInitialGridQuads(quads=None):
    """Returns or sets the render mesh minimum initial grid quads parameter of the active document.
      For more information on render meshes, see the Document Properties: Mesh topic in the Rhino help file.
    Parameters:
      quads (number, optional): the render mesh minimum initial grid quads. The suggested range is from 0 to 10000.
    Returns:
      number: if quads is not specified, the current render mesh minimum initial grid quads if successful.
      number: if quads is specified, the previous render mesh minimum initial grid quads if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as  rs
      print("Quality: %s" % rs.RenderMeshQuality())
      print("Mesh density: %s" % rs.RenderMeshDensity())
      print("Maximum angle: %s" % rs.RenderMeshMaxAngle())
      print("Maximum aspect ratio: %s" % rs.RenderMeshMaxAspectRatio())
      print("Minimun edge length: %s" % rs.RenderMeshMinEdgeLength())
      print("Maximum edge length: %s" % rs.RenderMeshMaxEdgeLength())
      print("Maximum distance, edge to surface: %s" % rs.RenderMeshMaxDistEdgeToSrf())
      print("Minumum initial grid quads: %s" % rs.RenderMeshMinInitialGridQuads())
      print("Other settings: %s" % rs.RenderMeshSettings())
    See Also:
      RenderMeshDensity
      RenderMeshMaxAngle
      RenderMeshMaxAspectRatio
      RenderMeshMaxDistEdgeToSrf
      RenderMeshMaxEdgeLength
      RenderMeshMinEdgeLength
      RenderMeshMinInitialGridQuads
      RenderMeshQuality
      RenderMeshSettings
    """
    current = scriptcontext.doc.GetCurrentMeshingParameters()
    rc = current.GridMinCount
    if quads is not None:
        current.GridMinCount = quads
        _SetRenderMeshAndUpdateStyle(current)
    return rc


def RenderMeshQuality(quality=None):
    """Returns or sets the render mesh quality of the active document.
        For more information on render meshes, see the Document Properties: Mesh topic in the Rhino help file.
      Parameters:
      quality (number, optional): the render mesh quality, either:
        0: Jagged and faster.  Objects may look jagged, but they should shade and render relatively quickly.
        1: Smooth and slower.  Objects should look smooth, but they may take a very long time to shade and render.
        2: Custom.
    Returns:
      number: if quality is not specified, the current render mesh quality if successful.
      number: if quality is specified, the previous render mesh quality if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as  rs
      print("Quality: %s" % rs.RenderMeshQuality())
      print("Mesh density: %s" % rs.RenderMeshDensity())
      print("Maximum angle: %s" % rs.RenderMeshMaxAngle())
      print("Maximum aspect ratio: %s" % rs.RenderMeshMaxAspectRatio())
      print("Minimun edge length: %s" % rs.RenderMeshMinEdgeLength())
      print("Maximum edge length: %s" % rs.RenderMeshMaxEdgeLength())
      print("Maximum distance, edge to surface: %s" % rs.RenderMeshMaxDistEdgeToSrf())
      print("Minumum initial grid quads: %s" % rs.RenderMeshMinInitialGridQuads())
      print("Other settings: %s" % rs.RenderMeshSettings())
    See Also:
      RenderMeshDensity
      RenderMeshMaxAngle
      RenderMeshMaxAspectRatio
      RenderMeshMaxDistEdgeToSrf
      RenderMeshMaxEdgeLength
      RenderMeshMinEdgeLength
      RenderMeshMinInitialGridQuads
      RenderMeshQuality
      RenderMeshSettings
    """
    current = scriptcontext.doc.MeshingParameterStyle
    if current == Rhino.Geometry.MeshingParameterStyle.Fast:
        rc = 0
    elif current == Rhino.Geometry.MeshingParameterStyle.Quality:
        rc = 1
    elif current == Rhino.Geometry.MeshingParameterStyle.Custom:
        rc = 2
    else:
        rc = None
    if quality is not None:
        if quality == 0:
            new_value = Rhino.Geometry.MeshingParameterStyle.Fast
        elif quality == 1:
            new_value = Rhino.Geometry.MeshingParameterStyle.Quality
        elif quality == 2:
            new_value = Rhino.Geometry.MeshingParameterStyle.Custom
        else:
            return None
        scriptcontext.doc.MeshingParameterStyle = new_value
    return rc


def RenderMeshSettings(settings=None):
    """Returns or sets the render mesh settings of the active document.
      For more information on render meshes, see the Document Properties: Mesh topic in the Rhino help file.
    Parameters:
      settings (number, optional): the render mesh settings, which is a bit-coded number that allows or disallows certain features.
      The bits can be added together in any combination to form a value between 0 and 7.  The bit values are as follows:
        0: No settings enabled.
        1: Refine mesh enabled.
        2: Jagged seams enabled.
        4: Simple planes enabled.
        8: Texture is packed, scaled and normalized; otherwise unpacked, unscaled and normalized.
    Returns:
      number: if settings is not specified, the current render mesh settings if successful.
      number: if settings is specified, the previous render mesh settings if successful.
      None: if not successful, or on error.
    Example:
      import rhinoscriptsyntax as  rs
      print("Quality: %s" % rs.RenderMeshQuality())
      print("Mesh density: %s" % rs.RenderMeshDensity())
      print("Maximum angle: %s" % rs.RenderMeshMaxAngle())
      print("Maximum aspect ratio: %s" % rs.RenderMeshMaxAspectRatio())
      print("Minimun edge length: %s" % rs.RenderMeshMinEdgeLength())
      print("Maximum edge length: %s" % rs.RenderMeshMaxEdgeLength())
      print("Maximum distance, edge to surface: %s" % rs.RenderMeshMaxDistEdgeToSrf())
      print("Minumum initial grid quads: %s" % rs.RenderMeshMinInitialGridQuads())
      print("Other settings: %s" % rs.RenderMeshSettings())
    See Also:
      RenderMeshDensity
      RenderMeshMaxAngle
      RenderMeshMaxAspectRatio
      RenderMeshMaxDistEdgeToSrf
      RenderMeshMaxEdgeLength
      RenderMeshMinEdgeLength
      RenderMeshMinInitialGridQuads
      RenderMeshQuality
      RenderMeshSettings
    """
    current = scriptcontext.doc.GetCurrentMeshingParameters()
    rc = 0
    if current.RefineGrid: rc += 1
    if current.JaggedSeams: rc += 2
    if current.SimplePlanes: rc += 4
    if current.TextureRange == Rhino.Geometry.MeshingParameterTextureRange.PackedScaledNormalized: rc += 8
    if settings is not None:
        current.RefineGrid = (settings & 1)
        current.JaggedSeams = (settings & 2)
        current.SimplePlanes = (settings & 4)
        current.TextureRange = Rhino.Geometry.MeshingParameterTextureRange.PackedScaledNormalized if (settings & 8) else Rhino.Geometry.MeshingParameterTextureRange.UnpackedUnscaledNormalized
        _SetRenderMeshAndUpdateStyle(current)
    return rc


def RenderSettings(settings=None):
    """Returns or sets render settings
    Parameters:
      settings (number, optional): bit-coded flags of render settings to modify.
        0=none,
        1=create shadows,
        2=use lights on layers that are off,
        4=render curves and isocurves,
        8=render dimensions and text
    Returns:
      number: if settings are not specified, the current render settings in bit-coded flags
      number: if settings are specified, the previous render settings in bit-coded flags
    Example:
      import rhinoscriptsyntax as rs
      render_annotations = 8
      settings = rs.RenderSettings()
      if settings & render_annotations:
          settings = settings - render_annotations
          rs.RenderSettings( settings )
    See Also:
      RenderAntialias
      RenderColor
      RenderResolution
    """
    rc = 0
    rendersettings = scriptcontext.doc.RenderSettings
    if rendersettings.ShadowmapLevel: rc+=1
    if rendersettings.UseHiddenLights: rc+=2
    if rendersettings.RenderCurves: rc+=4
    if rendersettings.RenderAnnotations: rc+=8
    if settings is not None:
        rendersettings.ShadowmapLevel = (settings & 1)
        rendersettings.UseHiddenLights = (settings & 2)==2
        rendersettings.RenderCurves = (settings & 4)==4
        rendersettings.RenderAnnotations = (settings & 8)==8
        scriptcontext.doc.RenderSettings = rendersettings
    return rc


def UnitAbsoluteTolerance(tolerance=None, in_model_units=True):
    """Resturns or sets the document's absolute tolerance. Absolute tolerance
    is measured in drawing units. See Rhino's document properties command
    (Units and Page Units Window) for details
    Parameters:
      tolerance (number, optional): the absolute tolerance to set
      in_model_units (bool, optional): Return or modify the document's model units (True)
                            or the document's page units (False)
    Returns:
      number: if tolerance is not specified, the current absolute tolerance
      number: if tolerance is specified, the previous absolute tolerance
    Example:
      import rhinoscriptsyntax as rs
      tol = rs.UnitAbsoluteTolerance()
      if tol<0.01:
          rs.UnitAbsoluteTolerance( 0.01 )
    See Also:
      UnitAngleTolerance
      UnitDistanceDisplayPrecision
      UnitRelativeTolerance
      UnitSystem
    """
    if in_model_units:
        rc = scriptcontext.doc.ModelAbsoluteTolerance
        if tolerance is not None:
            scriptcontext.doc.ModelAbsoluteTolerance = tolerance
    else:
        rc = scriptcontext.doc.PageAbsoluteTolerance
        if tolerance is not None:
            scriptcontext.doc.PageAbsoluteTolerance = tolerance
    return rc


def UnitAngleTolerance(angle_tolerance_degrees=None, in_model_units=True):
    """Return or set the document's angle tolerance. Angle tolerance is
    measured in degrees. See Rhino's DocumentProperties command
    (Units and Page Units Window) for details
    Parameters:
      angle_tolerance_degrees (number, optional): the angle tolerance to set
      in_model_units (number, optional): Return or modify the document's model units (True)
                             or the document's page units (False)
    Returns:
      number: if angle_tolerance_degrees is not specified, the current angle tolerance
      number: if angle_tolerance_degrees is specified, the previous angle tolerance
    Example:
      import rhinoscriptsyntax as rs
      tol = rs.UnitAngleTolerance()
      if tol<3.0:
          rs.UnitAngleTolerance(3.0)
    See Also:
      UnitAbsoluteTolerance
      UnitDistanceDisplayPrecision
      UnitRelativeTolerance
      UnitSystem
    """
    if in_model_units:
        rc = scriptcontext.doc.ModelAngleToleranceDegrees
        if angle_tolerance_degrees is not None:
            scriptcontext.doc.ModelAngleToleranceDegrees = angle_tolerance_degrees
    else:
        rc = scriptcontext.doc.PageAngleToleranceDegrees
        if angle_tolerance_degrees is not None:
            scriptcontext.doc.PageAngleToleranceDegrees = angle_tolerance_degrees
    return rc


def UnitDistanceDisplayPrecision(precision=None, model_units=True):
    """Return or set the document's distance display precision
    Parameters:
      precision (number, optional): The distance display precision.  If the current distance display mode is Decimal, then precision is the number of decimal places.
                                    If the current distance display mode is Fractional (including Feet and Inches), then the denominator = (1/2)^precision.
                                    Use UnitDistanceDisplayMode to get the current distance display mode.
      model_units (bool, optional): Return or modify the document's model units (True) or the document's page units (False). The default is True.
    Returns:
     number: If precision is not specified, the current distance display precision if successful. If precision is specified, the previous distance display precision if successful. If not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      precision = 3
      rs.UnitDistanceDisplayPrecision( precision )
    See Also:
      UnitAbsoluteTolerance
      UnitAngleTolerance
      UnitRelativeTolerance
      UnitSystem
    """
    if model_units:
        rc = scriptcontext.doc.ModelDistanceDisplayPrecision
        if precision: scriptcontext.doc.ModelDistanceDisplayPrecision = precision
        return rc
    rc = scriptcontext.doc.PageDistanceDisplayPrecision
    if precision: scriptcontext.doc.PageDistanceDisplayPrecision = precision
    return rc


def UnitRelativeTolerance(relative_tolerance=None, in_model_units=True):
    """Return or set the document's relative tolerance. Relative tolerance
    is measured in percent. See Rhino's DocumentProperties command
    (Units and Page Units Window) for details
    Parameters:
      relative_tolerance (number, optional) the relative tolerance in percent
      in_model_units (bool, optional): Return or modify the document's model units (True)
                             or the document's page units (False)
    Returns:
      number: if relative_tolerance is not specified, the current tolerance in percent
      number: if relative_tolerance is specified, the previous tolerance in percent
    Example:
      import rhinoscriptsyntax as rs
      tol = rs.UnitRelativeTolerance()
      if tol<1.0:
          rs.UnitRelativeTolerance(1.0)
    See Also:
      UnitAbsoluteTolerance
      UnitAngleTolerance
      UnitDistanceDisplayPrecision
      UnitSystem
    """
    if in_model_units:
        rc = scriptcontext.doc.ModelRelativeTolerance
        if relative_tolerance is not None:
            scriptcontext.doc.ModelRelativeTolerance = relative_tolerance
    else:
        rc = scriptcontext.doc.PageRelativeTolerance
        if relative_tolerance is not None:
            scriptcontext.doc.PageRelativeTolerance = relative_tolerance
    return rc


def UnitScale(to_system, from_system=None):
  """Return the scale factor for changing between unit systems.
  Parameters:
    to_system (number): The unit system to convert to. The unit systems are are:
       0 - No unit system
       1 - Microns (1.0e-6 meters)
       2 - Millimeters (1.0e-3 meters)
       3 - Centimeters (1.0e-2 meters)
       4 - Meters
       5 - Kilometers (1.0e+3 meters)
       6 - Microinches (2.54e-8 meters, 1.0e-6 inches)
       7 - Mils (2.54e-5 meters, 0.001 inches)
       8 - Inches (0.0254 meters)
       9 - Feet (0.3408 meters, 12 inches)
      10 - Miles (1609.344 meters, 5280 feet)
      11 - *Reserved for custom Unit System*
      12 - Angstroms (1.0e-10 meters)
      13 - Nanometers (1.0e-9 meters)
      14 - Decimeters (1.0e-1 meters)
      15 - Dekameters (1.0e+1 meters)
      16 - Hectometers (1.0e+2 meters)
      17 - Megameters (1.0e+6 meters)
      18 - Gigameters (1.0e+9 meters)
      19 - Yards (0.9144  meters, 36 inches)
      20 - Printer point (1/72 inches, computer points)
      21 - Printer pica (1/6 inches, (computer picas)
      22 - Nautical mile (1852 meters)
      23 - Astronomical (1.4959787e+11)
      24 - Lightyears (9.46073e+15 meters)
      25 - Parsecs (3.08567758e+16)
    from_system (number, optional): the unit system to convert from (see above). If omitted,
        the document's current unit system is used
  Returns:
    number: scale factor for changing between unit systems
  Example:
      import rhinoscriptsyntax as rs
      print(rs.UnitScale(3, 4)) # 100.0
      print(rs.UnitScale(3, 8)) # 2.54
      print(rs.UnitScale(8, 9)) # 12.0
    See Also:
    UnitSystem
    UnitSystemName
  """
  if from_system is None:
      from_system = scriptcontext.doc.ModelUnitSystem
  if type(from_system) is int:
      from_system = System.Enum.ToObject(Rhino.UnitSystem, from_system)
  if type(to_system) is int:
      to_system = System.Enum.ToObject(Rhino.UnitSystem, to_system)
  return Rhino.RhinoMath.UnitScale(from_system, to_system)


def UnitSystem(unit_system=None, scale=False, in_model_units=True):
    """Return or set the document's unit system. See Rhino's DocumentProperties
    command (Units and Page Units Window) for details
    Parameters:
      unit_system (number, optional): The unit system to set the document to. The unit systems are:
         0 - No unit system
         1 - Microns (1.0e-6 meters)
         2 - Millimeters (1.0e-3 meters)
         3 - Centimeters (1.0e-2 meters)
         4 - Meters
         5 - Kilometers (1.0e+3 meters)
         6 - Microinches (2.54e-8 meters, 1.0e-6 inches)
         7 - Mils (2.54e-5 meters, 0.001 inches)
         8 - Inches (0.0254 meters)
         9 - Feet (0.3048 meters, 12 inches)
        10 - Miles (1609.344 meters, 5280 feet)
        11 - *Reserved for custom Unit System*
        12 - Angstroms (1.0e-10 meters)
        13 - Nanometers (1.0e-9 meters)
        14 - Decimeters (1.0e-1 meters)
        15 - Dekameters (1.0e+1 meters)
        16 - Hectometers (1.0e+2 meters)
        17 - Megameters (1.0e+6 meters)
        18 - Gigameters (1.0e+9 meters)
        19 - Yards (0.9144  meters, 36 inches)
        20 - Printer point (1/72 inches, computer points)
        21 - Printer pica (1/6 inches, (computer picas)
        22 - Nautical mile (1852 meters)
        23 - Astronomical (1.4959787e+11)
        24 - Lightyears (9.46073e+15 meters)
        25 - Parsecs (3.08567758e+16)
      scale (bool, optional): Scale existing geometry based on the new unit system.
          If not specified, any existing geometry is not scaled (False)
      in_model_units (number, optional): Return or modify the document's model units (True)
          or the document's page units (False). The default is True.
    Returns:
      number: if unit_system is not specified, the current unit system
      number: if unit_system is specified, the previous unit system
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      rhUnitMillimeters = 2
      rhUnitInches = 8
      current_system = rs.UnitSystem()
      if current_system==rhUnitMillimeters:
          rs.UnitSystem(rhUnitInches, True)
    See Also:
      UnitAbsoluteTolerance
      UnitAngleTolerance
      UnitDistanceDisplayPrecision
      UnitRelativeTolerance
    """
    if (unit_system is not None and (unit_system<1 or unit_system>25)):
        raise ValueError("unit_system value of %s is not valid"%unit_system)
    if in_model_units:
        rc = int(scriptcontext.doc.ModelUnitSystem)
        if unit_system is not None:
            unit_system = System.Enum.ToObject(Rhino.UnitSystem, unit_system)
            scriptcontext.doc.AdjustModelUnitSystem(unit_system, scale)
    else:
        rc = int(scriptcontext.doc.PageUnitSystem)
        if unit_system is not None:
            unit_system = System.Enum.ToObject(Rhino.UnitSystem, unit_system)
            scriptcontext.doc.AdjustPageUnitSystem(unit_system, scale)
    return rc


def UnitSystemName(capitalize=False, singular=True, abbreviate=False, model_units=True):
    """Returns the name of the current unit system
    Parameters:
      capitalize (bool, optional): Capitalize the first character of the units system name (e.g. return "Millimeter" instead of "millimeter"). The default is not to capitalize the first character (false).
      singular (bool, optional): Return the singular form of the units system name (e.g. "millimeter" instead of "millimeters"). The default is to return the singular form of the name (true).
      abbreviate (bool, optional): Abbreviate the name of the units system (e.g. return "mm" instead of "millimeter"). The default is not to abbreviate the name (false).
      model_units (bool, optional): Return the document's model units (True) or the document's page units (False). The default is True.
    Returns:
      str: The name of the current units system if successful.
    Example:
      import rhinoscriptsyntax as rs
      system = rs.UnitSystemName(False, False, False)
      print("The units system is set to{}".format(system))
    See Also:
      UnitSystem
    """
    return scriptcontext.doc.GetUnitSystemName(model_units, capitalize, singular, abbreviate)
