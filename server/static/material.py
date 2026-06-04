import Rhino
import Rhino.DocObjects

import scriptcontext

from rhinoscript import utility as rhutil
from rhinoscript.layer import __getlayer


def AddMaterialToLayer(layer):
    """Add material to a layer and returns the new material's index. If the
    layer already has a material, then the layer's current material index is
    returned
    Parameters:
      layer (str): name of an existing layer.
    Returns:
      number: Material index of the layer if successful
      None: if not successful or on error
    Example:
      import rhinoscriptsyntax as rs
      layer = rs.CurrentLayer()
      index = rs.LayerMaterialIndex(layer)
      if index==-1: index = rs.AddMaterialToLayer(layer)
    See Also:
      LayerMaterialIndex
      IsMaterialDefault
    """
    layer = __getlayer(layer, True)
    if layer.RenderMaterialIndex>-1: return layer.RenderMaterialIndex
    material_index = scriptcontext.doc.Materials.Add()
    layer.RenderMaterialIndex = material_index
    scriptcontext.doc.Views.Redraw()
    return material_index
    #return scriptcontext.errorhandler()


def AddMaterialToObject(object_id):
    """Adds material to an object and returns the new material's index. If the
    object already has a material, the the object's current material index is
    returned.
    Parameters:
      object_id (guid): identifier of an object
    Returns:
      number: material index of the object
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject()
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index==-1: index = rs.AddMaterialToObject(obj)
    See Also:
      IsMaterialDefault
      ObjectMaterialIndex
      ObjectMaterialSource
    """
    rhino_object = rhutil.coercerhinoobject(object_id, True, True)
    attr = rhino_object.Attributes
    if attr.MaterialSource!=Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject:
        attr.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
        scriptcontext.doc.Objects.ModifyAttributes(rhino_object, attr, True)
        attr = rhino_object.Attributes
    material_index = attr.MaterialIndex
    if material_index>-1: return material_index
    material_index = scriptcontext.doc.Materials.Add()
    attr.MaterialIndex = material_index
    scriptcontext.doc.Objects.ModifyAttributes(rhino_object, attr, True)
    return material_index

    
def CopyMaterial(source_index, destination_index):
    """Copies definition of a source material to a destination material
    Parameters:
      source_index, destination_index (number): indices of materials to copy
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      src = rs.LayerMaterialIndex("Default")
      dest = rs.LayerMaterialIndex(rs.CurrentLayer())
      if src>=0 and dest>=0 and src!=dest:
          rs.CopyMaterial( src, dest )
    See Also:
      LayerMaterialIndex
      ObjectMaterialIndex
    """
    if source_index==destination_index: return False
    source = scriptcontext.doc.Materials[source_index]
    if source is None: return False
    rc = scriptcontext.doc.Materials.Modify(source, destination_index, True)
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def IsMaterialDefault(material_index):
    """Verifies a material is a copy of Rhino's built-in "default" material.
    The default material is used by objects and layers that have not been
    assigned a material.
    Parameters:
      material_index (number): the zero-based material index
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject()
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if rs.IsMaterialDefault(index):
              print("Object is assigned default material.")
          else:
              print("Object is not assigned default material.")
    See Also:
      LayerMaterialIndex
      ObjectMaterialIndex
    """
    mat = scriptcontext.doc.Materials[material_index]
    return mat and mat.IsDefaultMaterial


def IsMaterialReference(material_index):
    """Verifies a material is referenced from another file
    Parameters:
      material_index (number): the zero-based material index
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject()
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if rs.IsMaterialReference(index):
              print("The material is referenced from another file.")
          else:
              print("The material is not referenced from another file.")
    See Also:
      IsLayerReference
      IsLightReference
      IsObjectReference
    """
    mat = scriptcontext.doc.Materials[material_index]
    return mat and mat.IsReference


def MatchMaterial(source, destination):
    """Copies the material definition from one material to one or more objects
    Parameters:
      source (number|guid): source material index -or- identifier of the source object.
        The object must have a material assigned
      destination ([guid, ...]) identifiers(s) of the destination object(s)
    Returns:
      number: number of objects that were modified if successful
      None: if not successful or on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select source object")
      if obj and rs.ObjectMaterialIndex(obj)>-1:
          objects = rs.GetObjects("Select destination objects")
          if objects: rs.MatchMaterial( obj, objects )
    See Also:
      CopyMaterial
      LayerMaterialIndex
      ObjectMaterialIndex
    """
    source_id = rhutil.coerceguid(source)
    source_mat = None
    if source_id:
        rhobj = rhutil.coercerhinoobject(source_id, True, True)
        source = rhobj.Attributes.MaterialIndex
    mat = scriptcontext.doc.Materials[source]
    if not mat: return scriptcontext.errorhandler()
    destination_id = rhutil.coerceguid(destination)
    if destination_id: destination = [destination]
    ids = [rhutil.coerceguid(d) for d in destination]
    rc = 0
    for id in ids:
        rhobj = scriptcontext.doc.Objects.Find(id)
        if rhobj:
            rhobj.Attributes.MaterialIndex = source
            rhobj.Attributes.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
            rhobj.CommitChanges()
            rc += 1
    if rc>0: scriptcontext.doc.Views.Redraw()
    return rc


def MaterialBump(material_index, filename=None):
    """Returns or modifies a material's bump bitmap filename
    Parameters:
      material_index (number): zero based material index
      filename (str, optional): the bump bitmap filename
    Returns:
      str: if filename is not specified, the current bump bitmap filename
      str: if filename is specified, the previous bump bitmap filename
      None: if not successful or on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index>-1:
              rs.MaterialBump( index, "C:\\Users\\Steve\\Desktop\\bumpimage.png" )
    See Also:
      MaterialColor
      MaterialName
      MaterialReflectiveColor
      MaterialShine
      MaterialTexture
      MaterialTransparency
    """
    mat = scriptcontext.doc.Materials[material_index]
    if mat is None: return scriptcontext.errorhandler()
    texture = mat.GetBumpTexture()
    rc = texture.FileName if texture else ""
    if filename:
        mat.SetBumpTexture(filename)
        mat.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def MaterialColor(material_index, color=None):
    """Returns or modifies a material's diffuse color.
    Parameters:
      material_index (number): zero based material index
      color (color, optional): the new color value
    Returns:
      color: if color is not specified, the current material color
      color: if color is specified, the previous material color
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index>-1:
              rs.MaterialColor( index, (127, 255, 191) )
    See Also:
      MaterialBump
      MaterialName
      MaterialReflectiveColor
      MaterialShine
      MaterialTexture
      MaterialTransparency
    """
    mat = scriptcontext.doc.Materials[material_index]
    if mat is None: return scriptcontext.errorhandler()
    rc = mat.DiffuseColor
    color = rhutil.coercecolor(color)
    if color:
        mat.DiffuseColor = color
        mat.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def MaterialEnvironmentMap(material_index, filename=None):
    """Returns or modifies a material's environment bitmap filename.
    Parameters:
      material_index (number): zero based material index
      filename (str, optional): the environment bitmap filename
    Returns:
      str: if filename is not specified, the current environment bitmap filename
      str: if filename is specified, the previous environment bitmap filename
      None: if not successful or on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index>-1:
              rs.MaterialEnvironmentMap( index, "C:\\Users\\Steve\\Desktop\\emapimage.png" )
    See Also:
      MaterialBump
      MaterialTexture
      MaterialTransparencyMap
    """
    mat = scriptcontext.doc.Materials[material_index]
    if mat is None: return scriptcontext.errorhandler()
    texture = mat.GetEnvironmentTexture()
    rc = texture.FileName if texture else ""
    if filename:
        mat.SetEnvironmentTexture(filename)
        mat.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def MaterialName(material_index, name=None):
    """Returns or modifies a material's user defined name
    Parameters:
      material_index (number): zero based material index
      name (str, optional): the new name
    Returns:
      str: if name is not specified, the current material name
      str: if name is specified, the previous material name
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index>-1:
              rs.MaterialName( index, "Fancy_Material" )
    See Also:
      MaterialBump
      MaterialColor
      MaterialReflectiveColor
      MaterialShine
      MaterialTexture
      MaterialTransparency
    """
    mat = scriptcontext.doc.Materials[material_index]
    if mat is None: return scriptcontext.errorhandler()
    rc = mat.Name
    if name:
        mat.Name = name
        mat.CommitChanges()
    return rc


def MaterialReflectiveColor(material_index, color=None):
    """Returns or modifies a material's reflective color.
    Parameters:
      material_index (number): zero based material index
      color (color, optional): the new color value
    Returns:
      color: if color is not specified, the current material reflective color
      color: if color is specified, the previous material reflective color
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index>-1:
              rs.MaterialReflectiveColor( index, (191, 191, 255) )
    See Also:
      MaterialBump
      MaterialColor
      MaterialName
      MaterialShine
      MaterialTexture
      MaterialTransparency
    """
    mat = scriptcontext.doc.Materials[material_index]
    if mat is None: return scriptcontext.errorhandler()
    rc = mat.ReflectionColor
    color = rhutil.coercecolor(color)
    if color:
        mat.ReflectionColor = color
        mat.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def MaterialShine(material_index, shine=None):
    """Returns or modifies a material's shine value
    Parameters:
      material_index (number): zero based material index
      shine (number, optional): the new shine value. A material's shine value ranges from 0.0 to 255.0, with
        0.0 being matte and 255.0 being glossy
    Returns:
      number: if shine is not specified, the current material shine value
      number: if shine is specified, the previous material shine value
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      MAX_SHINE = 255.0
      obj = rs.GetObject("Select object")
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index>-1:
              rs.MaterialShine( index, MAX_SHINE/2 )
    See Also:
      MaterialBump
      MaterialColor
      MaterialName
      MaterialReflectiveColor
      MaterialTexture
      MaterialTransparency
    """
    mat = scriptcontext.doc.Materials[material_index]
    if mat is None: return scriptcontext.errorhandler()
    rc = mat.Shine
    if shine:
        mat.Shine = shine
        mat.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def MaterialTexture(material_index, filename=None):
    """Returns or modifies a material's texture bitmap filename
    Parameters:
      material_index (number): zero based material index
      filename (str, optional): the texture bitmap filename
    Returns:
      str: if filename is not specified, the current texture bitmap filename
      str: if filename is specified, the previous texture bitmap filename
      None: if not successful or on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index>-1:
              rs.MaterialTexture( index, "C:\\Users\\Steve\\Desktop\\textureimage.png" )
    See Also:
      MaterialBump
      MaterialColor
      MaterialName
      MaterialReflectiveColor
      MaterialShine
      MaterialTransparency
    """
    mat = scriptcontext.doc.Materials[material_index]
    if mat is None: return scriptcontext.errorhandler()
    texture = mat.GetBitmapTexture()
    rc = texture.FileName if texture else ""
    if filename:
        mat.SetBitmapTexture(filename)
        mat.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def MaterialTransparency(material_index, transparency=None):
    """Returns or modifies a material's transparency value
    Parameters:
      material_index (number): zero based material index
      transparency (number, optional): the new transparency value. A material's transparency value ranges from 0.0 to 1.0, with
        0.0 being opaque and 1.0 being transparent
    Returns:
      number: if transparency is not specified, the current material transparency value
      number: if transparency is specified, the previous material transparency value
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index>-1:
              rs.MaterialTransparency( index, 0.50 )
    See Also:
      MaterialBump
      MaterialColor
      MaterialName
      MaterialReflectiveColor
      MaterialShine
      MaterialTexture
    """
    mat = scriptcontext.doc.Materials[material_index]
    if mat is None: return scriptcontext.errorhandler()
    rc = mat.Transparency
    if transparency:
        mat.Transparency = transparency
        mat.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def MaterialTransparencyMap(material_index, filename=None):
    """Returns or modifies a material's transparency bitmap filename
    Parameters:
      material_index (number): zero based material index
      filename (str, optional): the transparency bitmap filename
    Returns:
      str: if filename is not specified, the current transparency bitmap filename
      str: if filename is specified, the previous transparency bitmap filename
      None: if not successful or on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index>-1:
              rs.MaterialTransparencyMap( index, "C:\\Users\\Steve\\Desktop\\texture.png" )
    See Also:
      MaterialBump
      MaterialEnvironmentMap
      MaterialTexture
    """
    mat = scriptcontext.doc.Materials[material_index]
    if mat is None: return scriptcontext.errorhandler()
    texture = mat.GetTransparencyTexture()
    rc = texture.FileName if texture else ""
    if filename:
        mat.SetTransparencyTexture(filename)
        mat.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def ResetMaterial(material_index):
    """Resets a material to Rhino's default material
    Parameters:
      material_index (number) zero based material index
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          index = rs.ObjectMaterialIndex(obj)
          if index>-1: rs.ResetMaterial(index)
    See Also:
      LayerMaterialIndex
      ObjectMaterialIndex
    """
    mat = scriptcontext.doc.Materials[material_index]
    if mat is None: return False
    rc = scriptcontext.doc.Materials.ResetMaterial(material_index)
    scriptcontext.doc.Views.Redraw()
    return rc
