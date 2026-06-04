import math

import System

import Rhino

import scriptcontext

from rhinoscript import utility as rhutil
from rhinoscript.layer import __getlayer
from rhinoscript.view import __viewhelper


__ALLOWED_TRANSFORM_TYPES = [
    Rhino.Geometry.Point3d,
    Rhino.Geometry.Line,
    Rhino.Geometry.Rectangle3d,
    Rhino.Geometry.Circle,
    Rhino.Geometry.Ellipse,
    Rhino.Geometry.Arc,
    Rhino.Geometry.Polyline,
    Rhino.Geometry.Box,
    Rhino.Geometry.Sphere
]


def CopyObject(object_id, translation=None):
    """Copies object from one location to another, or in-place.
    Parameters:
      object_id (guid): object to copy
      translation (vector, optional): translation vector to apply
    Returns:
      guid: id for the copy if successful
      None: if not able to copy
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object to copy")
      if id:
          start = rs.GetPoint("Point to copy from")
          if start:
              end = rs.GetPoint("Point to copy to", start)
              if end:
                  translation = end-start
                  rs.CopyObject( id, translation )
    See Also:
      CopyObjects
    """
    rc = CopyObjects(object_id, translation)
    if rc: return rc[0]


def CopyObjects(object_ids, translation=None):
    """Copies one or more objects from one location to another, or in-place.
    Parameters:
      object_ids ([guid, ...])list of objects to copy
      translation (vector, optional): list of three numbers or Vector3d representing
                         translation vector to apply to copied set
    Returns:
      list(guid, ...): identifiers for the copies if successful
    Example:
      import rhinoscriptsyntax as rs
      objectIds = rs.GetObjects("Select objects to copy")
      if objectIds:
          start = rs.GetPoint("Point to copy from")
          if start:
              end = rs.GetPoint("Point to copy to", start)
              if end:
                  translation = end-start
                  rs.CopyObjects( objectIds, translation )
    See Also:
      CopyObject
    """
    if translation:
        translation = rhutil.coerce3dvector(translation, True)
        translation = Rhino.Geometry.Transform.Translation(translation)
    else:
        translation = Rhino.Geometry.Transform.Identity
    return TransformObjects(object_ids, translation, True)


def DeleteObject(object_id):
    """Deletes a single object from the document
    Parameters:
      object_id (guid): identifier of object to delete
    Returns:
      bool: True of False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object to delete")
      if id: rs.DeleteObject(id)
    See Also:
      DeleteObjects
    """
    object_id = rhutil.coerceguid(object_id, True)
    rc = scriptcontext.doc.Objects.Delete(object_id, True)
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def DeleteObjects(object_ids):
    """Deletes one or more objects from the document
    Parameters:
      object_ids ([guid, ...]): identifiers of objects to delete
    Returns:
      number: Number of objects deleted
    Example:
      import rhinoscriptsyntax as rs
      object_ids = rs.GetObjects("Select objects to delete")
      if object_ids: rs.DeleteObjects(object_ids)
    See Also:
      DeleteObject
    """
    rc = 0
    id = rhutil.coerceguid(object_ids, False)
    if id: object_ids = [id]
    for id in object_ids:
        id = rhutil.coerceguid(id, True)
        if scriptcontext.doc.Objects.Delete(id, True): rc+=1
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def FlashObject(object_ids, style=True):
    """Causes the selection state of one or more objects to change momentarily
    so the object appears to flash on the screen
    Parameters:
      object_ids ([guid, ...]) identifiers of objects to flash
      style (bool, optional): If True, flash between object color and selection color.
        If False, flash between visible and invisible
    Returns:
      None
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.ObjectsByLayer("Default")
      if objs: rs.FlashObject(objs)
    See Also:
      HideObjects
      SelectObjects
      ShowObjects
      UnselectObjects
    """
    id = rhutil.coerceguid(object_ids, False)
    if id: object_ids = [id]
    rhobjs = [rhutil.coercerhinoobject(id, True, True) for id in object_ids]
    if rhobjs: scriptcontext.doc.Views.FlashObjects(rhobjs, style)


def HideObject(object_id):
    """Hides a single object
    Parameters:
      object_id (guid): id of object to hide
    Returns:
      bool: True of False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object to hide")
      if id: rs.HideObject(id)
    See Also:
      HideObjects
      IsObjectHidden
      ShowObject
      ShowObjects
    """
    return HideObjects(object_id)==1


def HideObjects(object_ids):
    """Hides one or more objects
    Parameters:
      object_ids ([guid, ...]): identifiers of objects to hide
    Returns:
      number: Number of objects hidden
    Example:
      import rhinoscriptsyntax as rs
      ids = rs.GetObjects("Select objects to hide")
      if ids: rs.HideObjects(ids)
    See Also:
      HideObjects
      IsObjectHidden
      ShowObject
      ShowObjects
    """
    id = rhutil.coerceguid(object_ids, False)
    if id: object_ids = [id]
    rc = 0
    for id in object_ids:
        id = rhutil.coerceguid(id, True)
        if scriptcontext.doc.Objects.Hide(id, False): rc += 1
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def IsLayoutObject(object_id):
    """Verifies that an object is in either page layout space or model space
    Parameters:
      object_id (guid): id of an object to test
    Returns:
      bool: True if the object is in page layout space
      bool: False if the object is in model space
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object")
      if id:
          if rs.IsLayoutObject(id):
              print("The object is in page layout space.")
          else:
              print("The object is in model space.")
    See Also:
      IsObject
      IsObjectReference
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.Attributes.Space == Rhino.DocObjects.ActiveSpace.PageSpace


def IsObject(object_id):
    """Verifies the existence of an object
    Parameters:
      object_id (guid): an object to test
    Returns:
      bool: True if the object exists
      bool: False if the object does not exist
    Example:
      import rhinoscriptsyntax as rs
      #Do something here...
      if rs.IsObject(id):
          print("The object exists.")
      else:
          print("The object does not exist.")
    See Also:
      IsObjectHidden
      IsObjectInGroup
      IsObjectLocked
      IsObjectNormal
      IsObjectReference
      IsObjectSelectable
      IsObjectSelected
      IsObjectSolid
    """
    return rhutil.coercerhinoobject(object_id, True, False) is not None


def IsObjectHidden(object_id):
    """Verifies that an object is hidden. Hidden objects are not visible, cannot
    be snapped to, and cannot be selected
    Parameters:
      object_id (guid): The identifier of an object to test
    Returns:
      bool: True if the object is hidden
      bool: False if the object is not hidden
    Example:
      import rhinoscriptsyntax as rs
      # Do something here...
      if rs.IsObjectHidden(id):
          print("The object is hidden.")
      else:
          print("The object is not hidden.")
    See Also:
      IsObject
      IsObjectInGroup
      IsObjectLocked
      IsObjectNormal
      IsObjectReference
      IsObjectSelectable
      IsObjectSelected
      IsObjectSolid
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.IsHidden


def IsObjectInBox(object_id, box, test_mode=True):
    """Verifies an object's bounding box is inside of another bounding box
    Parameters:
      object_id (guid): identifier of an object to be tested
      box ([point, point, point, point, point, point, point, point]): bounding box to test for containment
      test_mode (bool, optional): If True, the object's bounding box must be contained by box
        If False, the object's bounding box must be contained by or intersect box
    Returns:
      bool: True if object is inside box
      bool: False is object is not inside box
    Example:
      import rhinoscriptsyntax as rs
      box = rs.GetBox()
      if box:
          rs.EnableRedraw(False)
          object_list = rs.AllObjects()
          for obj in object_list:
              if rs.IsObjectInBox(obj, box, False):
                  rs.SelectObject( obj )
          rs.EnableRedraw( True )
    See Also:
      BoundingBox
      GetBox
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    box = rhutil.coerceboundingbox(box, True)
    objbox = rhobj.Geometry.GetBoundingBox(True)
    if test_mode: return box.Contains(objbox)
    union = Rhino.Geometry.BoundingBox.Intersection(box, objbox)
    return union.IsValid


def IsObjectInGroup(object_id, group_name=None):
    """Verifies that an object is a member of a group
    Parameters:
      object_id (guid): The identifier of an object
      group_name (str, optional): The name of a group. If omitted, the function
        verifies that the object is a member of any group
    Returns:
      bool: True if the object is a member of the specified group. If a group_name
        was not specified, the object is a member of some group.
      bool: False if the object is not a member of the specified group. If a
        group_name was not specified, the object is not a member of any group
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object")
      if id:
          name = rs.GetString("Group name")
          if name:
              result = rs.IsObjectInGroup(id, name)
              if result:
                  print("The object belongs to the group.")
              else:
                  print("The object does not belong to the group.")
    See Also:
      IsObject
      IsObjectHidden
      IsObjectLocked
      IsObjectNormal
      IsObjectReference
      IsObjectSelectable
      IsObjectSelected
      IsObjectSolid
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    count = rhobj.GroupCount
    if count<1: return False
    if not group_name: return True
    index = scriptcontext.doc.Groups.Find(group_name)
    if index<0: raise ValueError("%s group does not exist"%group_name)
    group_ids = rhobj.GetGroupList()
    for id in group_ids:
        if id==index: return True
    return False


def IsObjectLocked(object_id):
    """Verifies that an object is locked. Locked objects are visible, and can
    be snapped to, but cannot be selected
    Parameters:
      object_id (guid): The identifier of an object to be tested
    Returns:
      bool: True if the object is locked
      bool: False if the object is not locked
    Example:
      import rhinoscriptsyntax as rs
      # Do something here...
      if rs.IsObjectLocked(object):
          print("The object is locked.")
      else:
          print("The object is not locked.")
    See Also:
      IsObject
      IsObjectHidden
      IsObjectInGroup
      IsObjectNormal
      IsObjectReference
      IsObjectSelectable
      IsObjectSelected
      IsObjectSolid
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.IsLocked


def IsObjectNormal(object_id):
    """Verifies that an object is normal. Normal objects are visible, can be
    snapped to, and can be selected
    Parameters:
      object_id (guid): The identifier of an object to be tested
    Returns:
      bool: True if the object is normal
      bool: False if the object is not normal
    Example:
      import rhinoscriptsyntax as rs
      #Do something here...
      if rs.IsObjectNormal(object):
          print("The object is normal.")
      else:
          print("The object is not normal.")
    See Also:
      IsObject
      IsObjectHidden
      IsObjectInGroup
      IsObjectLocked
      IsObjectReference
      IsObjectSelectable
      IsObjectSelected
      IsObjectSolid
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.IsNormal


def IsObjectReference(object_id):
    """Verifies that an object is a reference object. Reference objects are
    objects that are not part of the current document
    Parameters:
      object_id (guid): The identifier of an object to test
    Returns:
      bool: True if the object is a reference object
      bool: False if the object is not a reference object
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object")
      if rs.IsObjectReference(id):
          print("The object is a reference object.")
      else:
          print("The object is not a reference object.")
    See Also:
      IsObject
      IsObjectHidden
      IsObjectInGroup
      IsObjectLocked
      IsObjectNormal
      IsObjectSelectable
      IsObjectSelected
      IsObjectSolid
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.IsReference


def IsObjectSelectable(object_id):
    """Verifies that an object can be selected
    Parameters:
      object_id (guid): The identifier of an object to test
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      # Do something here...
      if rs.IsObjectSelectable(object):
      rs.SelectObject( object )
    See Also:
      IsObject
      IsObjectHidden
      IsObjectInGroup
      IsObjectLocked
      IsObjectNormal
      IsObjectReference
      IsObjectSelected
      IsObjectSolid
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.IsSelectable(True,False,False,False)


def IsObjectSelected(object_id):
    """Verifies that an object is currently selected.
    Parameters:
      object_id (guid): The identifier of an object to test
    Returns:
      int: 0, the object is not selected
      int: 1, the object is selected
      int: 2, the object is entirely persistently selected
      int: 3, one or more proper sub-objects are selected
    Example:
      import rhinoscriptsyntax as rs
      object = rs.GetObject()
      if rs.IsObjectSelected(object):
          print("The object is selected.")
      else:
          print("The object is not selected.")
    See Also:
      IsObject
      IsObjectHidden
      IsObjectInGroup
      IsObjectLocked
      IsObjectNormal
      IsObjectReference
      IsObjectSelectable
      IsObjectSolid
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.IsSelected(False)


def IsObjectSolid(object_id):
    """Determines if an object is closed, solid
    Parameters:
      object_id (guid): The identifier of an object to test
    Returns:
      bool: True if the object is solid, or a mesh is closed.
      bool: False otherwise.
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object")
      if rs.IsObjectSolid(id):
          print("The object is solid.")
      else:
          print("The object is not solid.")
    See Also:
      IsObject
      IsObjectHidden
      IsObjectInGroup
      IsObjectLocked
      IsObjectNormal
      IsObjectReference
      IsObjectSelectable
      IsObjectSelected
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.IsSolid


def IsObjectValid(object_id):
    """Verifies an object's geometry is valid and without error
    Parameters:
      object_id (guid): The identifier of an object to test
    Returns:
      bool: True if the object is valid
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object")
      if rs.IsObjectValid(id):
          print("The object is valid.")
      else:
          print("The object is not valid.")
    See Also:
      IsObject
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.IsValid


def IsVisibleInView(object_id, view=None):
    """Verifies an object is visible in a view
    Parameters:
      object_id (guid): the identifier of an object to test
      view (str, optional): he title of the view.  If omitted, the current active view is used.
    Returns:
      bool: True if the object is visible in the specified view, otherwise False.  None on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if rs.IsObject(obj):
          view = rs.CurrentView()
          if rs.IsVisibleInView(obj, view):
              print("The object is visible in {}.".format(view))
          else:
              print("The object is not visible in {}.".format(view))
    See Also:
      IsObject
      IsView
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    viewport = __viewhelper(view).MainViewport
    bbox = rhobj.Geometry.GetBoundingBox(True)
    return rhobj.Visible and viewport.IsVisible(bbox)


def LockObject(object_id):
    """Locks a single object. Locked objects are visible, and they can be
    snapped to. But, they cannot be selected.
    Parameters:
      object_id (guid): The identifier of an object
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object to lock")
      if id: rs.LockObject(id)
    See Also:
      IsObjectLocked
      LockObjects
      UnlockObject
      UnlockObjects
    """
    return LockObjects(object_id)==1


def LockObjects(object_ids):
    """Locks one or more objects. Locked objects are visible, and they can be
    snapped to. But, they cannot be selected.
    Parameters:
      object_ids ([guid, ...]): list of Strings or Guids. The identifiers of objects
    Returns:
      number: number of objects locked
    Example:
      import rhinoscriptsyntax as rs
      ids = rs.GetObjects("Select objects to lock")
      if ids: rs.LockObjects(ids)
    See Also:
      IsObjectLocked
      LockObject
      UnlockObject
      UnlockObjects
    """
    id = rhutil.coerceguid(object_ids, False)
    if id: object_ids = [id]
    rc = 0
    for id in object_ids:
        id = rhutil.coerceguid(id, True)
        if scriptcontext.doc.Objects.Lock(id, False): rc += 1
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def MatchObjectAttributes(target_ids, source_id=None):
    """Matches, or copies the attributes of a source object to a target object
    Parameters:
      target_ids ([guid, ...]): identifiers of objects to copy attributes to
      source_id (guid, optional): identifier of object to copy attributes from. If None,
        then the default attributes are copied to the target_ids
    Returns:
      number: number of objects modified
    Example:
      import rhinoscriptsyntax as rs
      targets = rs.GetObjects("Select objects")
      if targets:
          source = rs.GetObject("Select object to match")
          if source: rs.MatchObjectAttributes( targets, source )
    See Also:
      GetObject
      GetObjects
    """
    id = rhutil.coerceguid(target_ids, False)
    if id: target_ids = [id]
    source_attr = Rhino.DocObjects.ObjectAttributes()
    if source_id:
        source = rhutil.coercerhinoobject(source_id, True, True)
        source_attr = source.Attributes.Duplicate()
    rc = 0
    for id in target_ids:
        id = rhutil.coerceguid(id, True)
        if scriptcontext.doc.Objects.ModifyAttributes(id, source_attr, True):
            rc += 1
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def MirrorObject(object_id, start_point, end_point, copy=False):
    """Mirrors a single object
    Parameters:
      object_id (guid): The identifier of an object to mirror
      start_point (point): start of the mirror plane
      end_point (point): end of the mirror plane
      copy (bool, optional): copy the object
    Returns:
      guid: Identifier of the mirrored object if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object to mirror")
      if obj:
          start = rs.GetPoint("Start of mirror plane")
          end = rs.GetPoint("End of mirror plane")
          if start and end:
              rs.MirrorObject( obj, start, end, True )
    See Also:
      MirrorObjects
    """
    rc = MirrorObjects(object_id, start_point, end_point, copy)
    if rc: return rc[0]


def MirrorObjects(object_ids, start_point, end_point, copy=False):
    """Mirrors a list of objects
    Parameters:
      object_ids ([guid, ...]): identifiers of objects to mirror
      start_point (point): start of the mirror plane
      end_point (point): end of the mirror plane
      copy (bool, optional): copy the objects
    Returns:
      list(guid, ...): List of identifiers of the mirrored objects if successful
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to mirror")
      if objs:
          start = rs.GetPoint("Start of mirror plane")
          end = rs.GetPoint("End of mirror plane")
          if start and end:
              rs.MirrorObjects( objs, start, end, True )
    See Also:
      MirrorObject
    """
    start_point = rhutil.coerce3dpoint(start_point, True)
    end_point = rhutil.coerce3dpoint(end_point, True)
    vec = end_point-start_point
    if vec.IsTiny(0): raise Exception("start and end points are too close to each other")
    normal = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane().Normal
    vec = Rhino.Geometry.Vector3d.CrossProduct(vec, normal)
    vec.Unitize()
    xf = Rhino.Geometry.Transform.Mirror(start_point, vec)
    rc = TransformObjects(object_ids, xf, copy)
    return rc


def MoveObject(object_id, translation):
    """Moves a single object
    Parameters:
      object_id (guid): The identifier of an object to move
      translation (vector): list of 3 numbers or Vector3d
    Returns:
      guid: Identifier of the moved object if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object to move")
      if id:
          start = rs.GetPoint("Point to move from")
          if start:
              end = rs.GetPoint("Point to move to")
              if end:
                  translation = end-start
                  rs.MoveObject(id, translation)
    See Also:
      MoveObjects
    """
    rc = MoveObjects(object_id, translation)
    if rc: return rc[0]


def MoveObjects(object_ids, translation):
    """Moves one or more objects
    Parameters:
      object_ids ([guid, ...]): The identifiers objects to move
      translation (vector): list of 3 numbers or Vector3d
    Returns:
      list(guid, ...): identifiers of the moved objects if successful
    Example:
      import rhinoscriptsyntax as rs
      ids = rs.GetObjects("Select objects to move")
      if ids:
          start = rs.GetPoint("Point to move from")
          if start:
              end = rs.GetPoint("Point to move to")
              if end:
                  translation = end-start
                  rs.MoveObjects( ids, translation )
    See Also:
      MoveObject
    """
    translation = rhutil.coerce3dvector(translation, True)
    xf = Rhino.Geometry.Transform.Translation(translation)
    rc = TransformObjects(object_ids, xf)
    return rc


def ObjectColor(object_ids, color=None):
    """Returns of modifies the color of an object. Object colors are represented
    as RGB colors. An RGB color specifies the relative intensity of red, green,
    and blue to cause a specific color to be displayed
    Parameters:
        object_ids ([guid, ...]): id or ids of object(s)
        color (color, optional): the new color value. If omitted, then current object
            color is returned. If object_ids is a list, color is required
    Returns:
        color: If color value is not specified, the current color value
        color: If color value is specified, the previous color value
        number: If object_ids is a list, then the number of objects modified
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to change color")
      if objs:
          color = rs.GetColor(0)
          if color:
              for obj in objs: rs.ObjectColor( obj, color )
    See Also:
      ObjectColorSource
      ObjectsByColor
    """
    id = rhutil.coerceguid(object_ids, False)
    rhino_object = None
    rhino_objects = None
    if id:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
    else:
        rhino_objects = [rhutil.coercerhinoobject(id, True, True) for id in object_ids]
        if len(rhino_objects)==1:
            rhino_object = rhino_objects[0]
            rhino_objects = None
    if color is None:
        #get the color
        if rhino_objects: raise ValueError("color must be specified when a list of rhino objects is provided")
        return rhino_object.Attributes.DrawColor(scriptcontext.doc)
    color = rhutil.coercecolor(color, True)
    if rhino_objects is not None:
        for rh_obj in rhino_objects:
            attr = rh_obj.Attributes
            attr.ObjectColor = color
            attr.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
            scriptcontext.doc.Objects.ModifyAttributes( rh_obj, attr, True)
        scriptcontext.doc.Views.Redraw()
        return len(rhino_objects)
    rc = rhino_object.Attributes.DrawColor(scriptcontext.doc)
    attr = rhino_object.Attributes
    attr.ObjectColor = color
    attr.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
    scriptcontext.doc.Objects.ModifyAttributes( rhino_object, attr, True )
    scriptcontext.doc.Views.Redraw()
    return rc


def ObjectColorSource(object_ids, source=None):
    """Returns of modifies the color source of an object.
    Parameters:
      object_ids ([guid, ...]): single identifier of list of identifiers
      source (number, optional) = new color source
          0 = color from layer
          1 = color from object
          2 = color from material
          3 = color from parent
    Returns:
      if color source is not specified, the current color source
      is color source is specified, the previous color source
      if color_ids is a list, then the number of objects modifief
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to reset color source")
      if objs:
          for obj In objs: rs.ObjectColorSource(obj, 0)
    See Also:
      ObjectColor
    """
    id = rhutil.coerceguid(object_ids, False)
    if id:
        rhobj = rhutil.coercerhinoobject(id, True, True)
        rc = int(rhobj.Attributes.ColorSource)
        if source is not None:
            rhobj.Attributes.ColorSource = System.Enum.ToObject(Rhino.DocObjects.ObjectColorSource, source)
            rhobj.CommitChanges()
            scriptcontext.doc.Views.Redraw()
        return rc
    else:
        rc = 0
        source = System.Enum.ToObject(Rhino.DocObjects.ObjectColorSource, source)
        for id in object_ids:
            rhobj = rhutil.coercerhinoobject(id, True, True)
            rhobj.Attributes.ColorSource = source
            rhobj.CommitChanges()
            rc += 1
        if rc: scriptcontext.doc.Views.Redraw()
        return rc


def ObjectDescription(object_id):
    """Returns a short text description of an object
    Parameters:
      object_id = identifier of an object
    Returns:
      A short text description of the object if successful.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          description = rs.ObjectDescription(obj)
          print("Object description:"{} .format(description))
    See Also:
      ObjectType
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    return rhobj.ShortDescription(False)


def ObjectGroups(object_id):
    """Returns all of the group names that an object is assigned to
    Parameters:
      object_id ([guid, ...]): identifier of an object(s)
    Returns:
      list(str, ...): list of group names on success
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          groups = rs.ObjectGroups(obj)
          if groups:
              for group in groups: print("Object group: {}".format(group))
          else:
              print("No groups.")
    See Also:
      ObjectsByGroup
    """
    rhino_object = rhutil.coercerhinoobject(object_id, True, True)
    if rhino_object.GroupCount<1: return []
    group_indices = rhino_object.GetGroupList()
    rc = [scriptcontext.doc.Groups.GroupName(index) for index in group_indices]
    return rc


def ObjectLayer(object_id, layer=None):
    """Returns or modifies the layer of an object
    Parameters:
      object_id ([guid, ...]) the identifier of the object(s)
      layer (str, optional):  name of an existing layer
    Returns:
      str: If a layer is not specified, the object's current layer
      str: If a layer is specified, the object's previous layer
      number: If object_id is a list or tuple, the number of objects modified
    Example:
      import rhinoscriptsyntax as rs
      id = rs.GetObject("Select object")
      if id: rs.ObjectLayer(id, "Default")
    See Also:
      ObjectsByLayer
    """
    if type(object_id) is not str and hasattr(object_id, "__len__"):
        layer = __getlayer(layer, True)
        index = layer.LayerIndex
        for id in object_id:
            obj = rhutil.coercerhinoobject(id, True, True)
            obj.Attributes.LayerIndex = index
            obj.CommitChanges()
        scriptcontext.doc.Views.Redraw()
        return len(object_id)
    obj = rhutil.coercerhinoobject(object_id, True, True)
    if obj is None: return scriptcontext.errorhandler()
    index = obj.Attributes.LayerIndex
    rc = scriptcontext.doc.Layers[index].FullPath
    if layer:
        layer = __getlayer(layer, True)
        index = layer.LayerIndex
        obj.Attributes.LayerIndex = index
        obj.CommitChanges()
        scriptcontext.doc.Views.Redraw()
    return rc


def ObjectLayout(object_id, layout=None, return_name=True):
    """Returns or changes the layout or model space of an object
    Parameters:
      object_id (guid): identifier of the object
      layout (str|guid, optional): to change, or move, an object from model space to page
        layout space, or from one page layout to another, then specify the
        title or identifier of an existing page layout view. To move an object
        from page layout space to model space, just specify None
      return_name[opt] = If True, the name, or title, of the page layout view
        is returned. If False, the identifier of the page layout view is returned
    Returns:
      str: if layout is not specified, the object's current page layout view
      str: if layout is specified, the object's previous page layout view
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj: rs.ObjectLayout(obj, "Page 1")
    See Also:
      IsLayoutObject
      IsLayout
      ViewNames
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    rc = None
    if rhobj.Attributes.Space==Rhino.DocObjects.ActiveSpace.PageSpace:
        page_id = rhobj.Attributes.ViewportId
        pageview = scriptcontext.doc.Views.Find(page_id)
        if return_name: rc = pageview.MainViewport.Name
        else: rc = pageview.MainViewport.Id
        if layout is None: #move to model space
            rhobj.Attributes.Space = Rhino.DocObjects.ActiveSpace.ModelSpace
            rhobj.Attributes.ViewportId = System.Guid.Empty
            rhobj.CommitChanges()
            scriptcontext.doc.Views.Redraw()
    else:
        if layout:
            layout = scriptcontext.doc.Views.Find(layout, False)
            if layout is not None and isinstance(layout, Rhino.Display.RhinoPageView):
                rhobj.Attributes.ViewportId = layout.MainViewport.Id
                rhobj.Attributes.Space = Rhino.DocObjects.ActiveSpace.PageSpace
                rhobj.CommitChanges()
                scriptcontext.doc.Views.Redraw()
    return rc


def ObjectLinetype(object_ids, linetype=None):
    """Returns of modifies the linetype of an object
    Parameters:
      object_ids ({guid, ...]): identifiers of object(s)
      linetype (str, optional): name of an existing linetype. If omitted, the current
        linetype is returned. If object_ids is a list of identifiers, this parameter
        is required
    Returns:
      str: If a linetype is not specified, the object's current linetype
      str: If linetype is specified, the object's previous linetype
      number: If object_ids is a list, the number of objects modified
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj: rs.ObjectLinetype(obj, "Continuous")
    See Also:
      ObjectLinetypeSource
    """
    id = rhutil.coerceguid(object_ids, False)
    if id:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        oldindex = scriptcontext.doc.Linetypes.LinetypeIndexForObject(rhino_object)
        if linetype:
            newindex = scriptcontext.doc.Linetypes.Find(linetype)
            rhino_object.Attributes.LinetypeSource = Rhino.DocObjects.ObjectLinetypeSource.LinetypeFromObject
            rhino_object.Attributes.LinetypeIndex = newindex
            rhino_object.CommitChanges()
            scriptcontext.doc.Views.Redraw()
        return scriptcontext.doc.Linetypes[oldindex].Name

    newindex = scriptcontext.doc.Linetypes.Find(linetype)
    if newindex<0: raise Exception("%s does not exist in LineTypes table"%linetype)
    for id in object_ids:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rhino_object.Attributes.LinetypeSource = Rhino.DocObjects.ObjectLinetypeSource.LinetypeFromObject
        rhino_object.Attributes.LinetypeIndex = newindex
        rhino_object.CommitChanges()
    scriptcontext.doc.Views.Redraw()
    return len(object_ids)


def ObjectLinetypeSource(object_ids, source=None):
    """Returns of modifies the linetype source of an object
    Parameters:
      object_ids ([guid, ...]): identifiers of object(s)
      source (number, optional): new linetype source. If omitted, the current source is returned.
        If object_ids is a list of identifiers, this parameter is required
          0 = By Layer
          1 = By Object
          3 = By Parent
    Returns:
      number: If a source is not specified, the object's current linetype source
      number: If source is specified, the object's previous linetype source
      number: If object_ids is a list, the number of objects modified
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.GetObjects("Select objects to reset linetype source")
      if objects:
          for obj in objects: rs.ObjectLinetypeSource( obj, 0 )
    See Also:
      ObjectLinetype
    """
    id = rhutil.coerceguid(object_ids, False)
    if id:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        oldsource = rhino_object.Attributes.LinetypeSource
        if source is not None:
            source = System.Enum.ToObject(Rhino.DocObjects.ObjectLinetypeSource, source)
            rhino_object.Attributes.LinetypeSource = source
            rhino_object.CommitChanges()
            scriptcontext.doc.Views.Redraw()
        return int(oldsource)
    source = System.Enum.ToObject(Rhino.DocObjects.ObjectLinetypeSource, source)
    for id in object_ids:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rhino_object.Attributes.LinetypeSource = source
        rhino_object.CommitChanges()
    scriptcontext.doc.Views.Redraw()
    return len(object_ids)


def ObjectMaterialIndex(object_id, material_index=None):
    """Returns or changes the material index of an object. Rendering materials are stored in
    Rhino's rendering material table. The table is conceptually an array. Render
    materials associated with objects and layers are specified by zero based
    indices into this array.
    Parameters:
      object_id (guid): identifier of an object
      index (number, optional): the new material index
    Returns:
      number: If the return value of ObjectMaterialSource is "material by object", then
          the return value of this function is the index of the object's rendering
          material. A material index of -1 indicates no material has been assigned,
          and that Rhino's internal default material has been assigned to the object.
      None: on failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          source = rs.ObjectMaterialSource(obj)
          if source==0:
              print("The material source is by layer")
          else:
              print("The material source is by object")
              index = rs.ObjectMaterialIndex(obj)
              if index==-1: print("The material is default.")
              else: print("The material is custom.")
    See Also:
      ObjectMaterialSource
    """
    rhino_object = rhutil.coercerhinoobject(object_id, True, True)
    if material_index is not None and material_index < scriptcontext.doc.Materials.Count:
      attrs = rhino_object.Attributes
      attrs.MaterialIndex = material_index
      scriptcontext.doc.Objects.ModifyAttributes(rhino_object, attrs, True)
    return rhino_object.Attributes.MaterialIndex


def ObjectMaterialSource(object_ids, source=None):
    """Returns or modifies the rendering material source of an object.
    Parameters:
      object_ids ([guid, ...]): one or more object identifiers
      source (number, optional): The new rendering material source. If omitted and a single
        object is provided in object_ids, then the current material source is
        returned. This parameter is required if multiple objects are passed in
        object_ids
        0 = Material from layer
        1 = Material from object
        3 = Material from parent
    Returns:
      number: If source is not specified, the current rendering material source
      number: If source is specified, the previous rendering material source
      number: If object_ids refers to multiple objects, the number of objects modified
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.GetObjects("Select objects to reset rendering material source")
      if objects:
          [rs.ObjectMaterialSource(obj, 0) for obj in objects]
    See Also:
      ObjectMaterialIndex
    """
    id = rhutil.coerceguid(object_ids, False)
    if id: # working with single object
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rc = int(rhino_object.Attributes.MaterialSource)
        if source is not None:
            rhino_object.Attributes.MaterialSource = System.Enum.ToObject(Rhino.DocObjects.ObjectMaterialSource, source)
            rhino_object.CommitChanges()
        return rc
    # else working with multiple objects
    if source is None: raise Exception("source is required when object_ids represents multiple objects")
    source = System.Enum.ToObject(Rhino.DocObjects.ObjectMaterialSource, source)
    for id in object_ids:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rhino_object.Attributes.MaterialSource = source
        rhino_object.CommitChanges()
    return len(object_ids)


def ObjectName(object_id, name=None):
    """Returns or modifies the name of an object
    Parameters:
      object_id ([guid, ...]): id or ids of object(s)
      name (str, optional): the new object name. If omitted, the current name is returned
    Returns:
      str: If name is not specified, the current object name
      str: If name is specified, the previous object name
      number: If object_id is a list, the number of objects changed
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints(message1="Pick some points")
      if points:
          count = 0
          for point in points:
              obj = rs.AddPoint(point)
              if obj:
                  rs.ObjectName( obj, "Point"+str(count) )
                  count += 1
    See Also:
      ObjectsByName
    """
    id = rhutil.coerceguid(object_id, False)
    rhino_object = None
    rhino_objects = None
    if id:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
    else:
        rhino_objects = [rhutil.coercerhinoobject(id, True, True) for id in object_id]
        if not rhino_objects: return 0
        if len(rhino_objects)==1:
            rhino_object = rhino_objects[0]
            rhino_objects = None
    if name is None: #get the name
        if rhino_objects: raise Exception("name required when object_id represents multiple objects")
        return rhino_object.Name
    if rhino_objects:
        for rh_obj in rhino_objects:
            attr = rh_obj.Attributes
            attr.Name = name
            scriptcontext.doc.Objects.ModifyAttributes(rh_obj, attr, True)
        return len(rhino_objects)
    rc = rhino_object.Name
    if not type(name) is str: name = str(name)
    rhino_object.Attributes.Name = name
    rhino_object.CommitChanges()
    return rc


def ObjectPrintColor(object_ids, color=None):
    """Returns or modifies the print color of an object
    Parameters:
      object_ids ([guid, ...]): identifiers of object(s)
      color (color, optional): new print color. If omitted, the current color is returned.
    Returns:
      color: If color is not specified, the object's current print color
      color: If color is specified, the object's previous print color
      number: If object_ids is a list or tuple, the number of objects modified
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.GetObjects("Select objects to change print color")
      if objects:
          color = rs.GetColor()
          if color:
              for object in objects: rs.ObjectPrintColor(object, color)
    See Also:
      ObjectPrintColorSource
    """
    id = rhutil.coerceguid(object_ids, False)
    if id:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rc = rhino_object.Attributes.PlotColor
        if color:
            rhino_object.Attributes.PlotColorSource = Rhino.DocObjects.ObjectPlotColorSource.PlotColorFromObject
            rhino_object.Attributes.PlotColor = rhutil.coercecolor(color, True)
            rhino_object.CommitChanges()
            scriptcontext.doc.Views.Redraw()
        return rc
    for id in object_ids:
        color = rhutil.coercecolor(color, True)
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rhino_object.Attributes.PlotColorSource = Rhino.DocObjects.ObjectPlotColorSource.PlotColorFromObject
        rhino_object.Attributes.PlotColor = color
        rhino_object.CommitChanges()
    scriptcontext.doc.Views.Redraw()
    return len(object_ids)


def ObjectPrintColorSource(object_ids, source=None):
    """Returns or modifies the print color source of an object
    Parameters:
      object_ids ([guid, ...]): identifiers of object(s)
      source (number, optional): new print color source
        0 = print color by layer
        1 = print color by object
        3 = print color by parent
    Returns:
      number: If source is not specified, the object's current print color source
      number: If source is specified, the object's previous print color source
      number: If object_ids is a list or tuple, the number of objects modified
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.GetObjects("Select objects to reset print color source")
      if objects:
          for object in objects: rs.ObjectPrintColorSource(object, 0)
    See Also:
      ObjectPrintColor
    """
    id = rhutil.coerceguid(object_ids, False)
    if id:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rc = int(rhino_object.Attributes.PlotColorSource)
        if source is not None:
            rhino_object.Attributes.PlotColorSource = System.Enum.ToObject(Rhino.DocObjects.ObjectPlotColorSource, source)
            rhino_object.CommitChanges()
            scriptcontext.doc.Views.Redraw()
        return rc
    for id in object_ids:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rhino_object.Attributes.PlotColorSource = System.Enum.ToObject(Rhino.DocObjects.ObjectPlotColorSource, source)
        rhino_object.CommitChanges()
    scriptcontext.doc.Views.Redraw()
    return len(object_ids)


def ObjectPrintWidth(object_ids, width=None):
    """Returns or modifies the print width of an object
    Parameters:
      object_ids ([guid, ...]): identifiers of object(s)
      width (number, optional): new print width value in millimeters, where width=0 means use
        the default width, and width<0 means do not print (visible for screen display,
        but does not show on print). If omitted, the current width is returned.
    Returns:
      number: If width is not specified, the object's current print width
      number: If width is specified, the object's previous print width
      number: If object_ids is a list or tuple, the number of objects modified
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to change print width")
      if objs:
          for obj in objs: rs.ObjectPrintWidth(obj,0.5)
    See Also:
      ObjectPrintWidthSource
    """
    id = rhutil.coerceguid(object_ids, False)
    if id:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rc = rhino_object.Attributes.PlotWeight
        if width is not None:
            rhino_object.Attributes.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromObject
            rhino_object.Attributes.PlotWeight = width
            rhino_object.CommitChanges()
            scriptcontext.doc.Views.Redraw()
        return rc
    for id in object_ids:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rhino_object.Attributes.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromObject
        rhino_object.Attributes.PlotWeight = width
        rhino_object.CommitChanges()
    scriptcontext.doc.Views.Redraw()
    return len(object_ids)


def ObjectPrintWidthSource(object_ids, source=None):
    """Returns or modifies the print width source of an object
    Parameters:
      object_ids ([guid, ...]): identifiers of object(s)
      source (number, optional): new print width source
        0 = print width by layer
        1 = print width by object
        3 = print width by parent
    Returns:
      number: If source is not specified, the object's current print width source
      number: If source is specified, the object's previous print width source
      number: If object_ids is a list or tuple, the number of objects modified
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.GetObjects("Select objects to reset print width source")
      if objects:
          for obj in objects: rs.ObjectPrintWidthSource(obj,0)
    See Also:
      ObjectPrintColor
    """
    id = rhutil.coerceguid(object_ids, False)
    if id:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rc = int(rhino_object.Attributes.PlotWeightSource)
        if source is not None:
            rhino_object.Attributes.PlotWeightSource = System.Enum.ToObject(Rhino.DocObjects.ObjectPlotWeightSource, source)
            rhino_object.CommitChanges()
            scriptcontext.doc.Views.Redraw()
        return rc
    for id in object_ids:
        rhino_object = rhutil.coercerhinoobject(id, True, True)
        rhino_object.Attributes.PlotWeightSource = System.Enum.ToObject(Rhino.DocObjects.ObjectPlotWeightSource, source)
        rhino_object.CommitChanges()
    scriptcontext.doc.Views.Redraw()
    return len(object_ids)


def ObjectType(object_id):
    """Returns the object type
    Parameters:
      object_id (guid): identifier of an object
    Returns:
      number: The object type if successful.
        The valid object types are as follows:
        Value   Description
          0           Unknown object
          1           Point
          2           Point cloud
          4           Curve
          8           Surface or single-face brep
          16          Polysurface or multiple-face
          32          Mesh
          256         Light
          512         Annotation
          4096        Instance or block reference
          8192        Text dot object
          16384       Grip object
          32768       Detail
          65536       Hatch
          131072      Morph control
          262144      SubD
          134217728   Cage
          268435456   Phantom
          536870912   Clipping plane
          1073741824  Extrusion
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          objtype = rs.ObjectType(obj)
          print("Object type:{}".format(objtype))
    See Also:
      ObjectsByType
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    geom = rhobj.Geometry
    if isinstance(geom, Rhino.Geometry.Brep) and geom.Faces.Count==1:
        return 8 #surface
    return int(geom.ObjectType)


def OrientObject(object_id, reference, target, flags=0):
    """Orients a single object based on input points.  

    If two 3-D points are specified, then this method will function similar to Rhino's Orient command.  If more than two 3-D points are specified, then the function will orient similar to Rhino's Orient3Pt command.

    The orient flags values can be added together to specify multiple options.
        Value   Description
        1       Copy object.  The default is not to copy the object.
        2       Scale object.  The default is not to scale the object.  Note, the scale option only applies if both reference and target contain only two 3-D points.

    Parameters:
        object_id (guid): The identifier of an object
        reference ([point, point, ...]): list of 3-D reference points.
        target  ([point, point, ...]): list of 3-D target points
        flags (number):  1 = copy object
                         2 = scale object
                         3 = copy and scale
    Returns:
      guid: The identifier of the oriented object if successful.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object to orient")
      if obj:
          reference = rs.GetPoints(message1="First reference point")
          if reference and len(reference)>0:
              target = rs.GetPoints(message1="First target point")
              if target and len(target)>0:
                  rs.OrientObject( obj, reference, target )
    See Also:
      
    """
    object_id = rhutil.coerceguid(object_id, True)
    from_array = rhutil.coerce3dpointlist(reference)
    to_array = rhutil.coerce3dpointlist(target)
    if from_array is None or to_array is None:
        raise ValueError("Could not convert reference or target to point list")
    from_count = len(from_array)
    to_count = len(to_array)
    if from_count<2 or to_count<2: raise Exception("point lists must have at least 2 values")

    copy = ((flags & 1) == 1)
    scale = ((flags & 2) == 2)
    xform_final = None
    if from_count>2 and to_count>2:
        #Orient3Pt
        from_plane = Rhino.Geometry.Plane(from_array[0], from_array[1], from_array[2])
        to_plane = Rhino.Geometry.Plane(to_array[0], to_array[1], to_array[2])
        if not from_plane.IsValid or not to_plane.IsValid:
            raise Exception("unable to create valid planes from point lists")
        xform_final = Rhino.Geometry.Transform.PlaneToPlane(from_plane, to_plane)
    else:
        #Orient2Pt
        xform_move = Rhino.Geometry.Transform.Translation( to_array[0]-from_array[0] )
        xform_scale = Rhino.Geometry.Transform.Identity
        v0 = from_array[1] - from_array[0]
        v1 = to_array[1] - to_array[0]
        if scale:
            len0 = v0.Length
            len1 = v1.Length
            if len0<0.000001 or len1<0.000001: raise Exception("vector lengths too short")
            scale = len1 / len0
            if abs(1.0-scale)>=0.000001:
                plane = Rhino.Geometry.Plane(from_array[0], v0)
                xform_scale = Rhino.Geometry.Transform.Scale(plane, scale, scale, scale)
        v0.Unitize()
        v1.Unitize()
        xform_rotate = Rhino.Geometry.Transform.Rotation(v0, v1, from_array[0])
        xform_final = xform_move * xform_scale * xform_rotate
    rc = scriptcontext.doc.Objects.Transform(object_id, xform_final, not copy)
    if rc==System.Guid.Empty: return scriptcontext.errorhandler()
    scriptcontext.doc.Views.Redraw()
    return rc


def RotateObject(object_id, center_point, rotation_angle, axis=None, copy=False):
    """Rotates a single object
    Parameters:
      object_id (guid): The identifier of an object to rotate
      center_point (point): the center of rotation
      rotation_angle (number): in degrees
      axis (plane, optional): axis of rotation, If omitted, the Z axis of the active
        construction plane is used as the rotation axis
      copy (bool, optional): copy the object
    Returns:
      guid: Identifier of the rotated object if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object to rotate")
      if obj:
          point = rs.GetPoint("Center point of rotation")
          if point: rs.RotateObject(obj, point, 45.0, None, copy=True)
    See Also:
      RotateObjects
    """
    rc = RotateObjects(object_id, center_point, rotation_angle, axis, copy)
    if rc: return rc[0]
    return scriptcontext.errorhandler()


def RotateObjects( object_ids, center_point, rotation_angle, axis=None, copy=False):
    """Rotates multiple objects
    Parameters:
      object_ids ([guid, ...]): Identifiers of objects to rotate
      center_point (point): the center of rotation
      rotation_angle (number): in degrees
      axis (plane, optional): axis of rotation, If omitted, the Z axis of the active
        construction plane is used as the rotation axis
      copy (bool, optional): copy the object
    Returns:
      list(guid, ...): identifiers of the rotated objects if successful
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to rotate")
      if objs:
          point = rs.GetPoint("Center point of rotation")
          if point:
              rs.RotateObjects( objs, point, 45.0, None, True )
    See Also:
      RotateObject
    """
    center_point = rhutil.coerce3dpoint(center_point, True)
    if not axis:
        viewTable = scriptcontext.doc.Views
        activeView = None
        if viewTable is not None:
            activeView = viewTable.ActiveView
        if activeView is not None:
            axis = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane().Normal
        else:
            axis = Rhino.Geometry.Vector3d(0,0,1)
    axis = rhutil.coerce3dvector(axis, True)
    rotation_angle = Rhino.RhinoMath.ToRadians(rotation_angle)
    xf = Rhino.Geometry.Transform.Rotation(rotation_angle, axis, center_point)
    rc = TransformObjects(object_ids, xf, copy)
    return rc


def ScaleObject(object_id, origin, scale, copy=False):
    """Scales a single object. Can be used to perform a uniform or non-uniform
    scale transformation. Scaling is based on the active construction plane.
    Parameters:
      object_id (guid): The identifier of an object
      origin (point): the origin of the scale transformation
      scale ([number, number, number]): three numbers that identify the X, Y, and Z axis scale factors to apply
      copy (bool, optional): copy the object
    Returns:
      guid: Identifier of the scaled object if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object to scale")
      if obj:
          origin = rs.GetPoint("Origin point")
          if origin:
              rs.ScaleObject( obj, origin, (1,2,3), True )
    See Also:
      ScaleObjects
    """
    rc = ScaleObjects(object_id, origin, scale, copy )
    if rc: return rc[0]
    return scriptcontext.errorhandler()


def ScaleObjects(object_ids, origin, scale, copy=False):
    """Scales one or more objects. Can be used to perform a uniform or non-
    uniform scale transformation. Scaling is based on the active construction plane.
    Parameters:
      object_ids ([guid, ...]): Identifiers of objects to scale
      origin (point): the origin of the scale transformation
      scale ([number, number, number]): three numbers that identify the X, Y, and Z axis scale factors to apply
      copy (bool, optional): copy the objects
    Returns:
      list(guid, ...): identifiers of the scaled objects if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to scale")
      if objs:
          origin = rs.GetPoint("Origin point")
          if origin:
              rs.ScaleObjects( objs, origin, (2,2,2), True )
    See Also:
      ScaleObject
    """
    origin = rhutil.coerce3dpoint(origin, True)
    scale = rhutil.coerce3dpoint(scale, True)
    plane = scriptcontext.doc.Views.ActiveView.ActiveViewport.ConstructionPlane()
    plane.Origin = origin
    xf = Rhino.Geometry.Transform.Scale(plane, scale.X, scale.Y, scale.Z)
    rc = TransformObjects(object_ids, xf, copy)
    return rc


def SelectObject(object_id, redraw=True):
    """Selects a single object
    Parameters:
      object_id (guid): the identifier of the object to select
    Returns:
      bool: True on success
    Example:
      import rhinoscriptsyntax as rs
      rs.Command( "Line 0,0,0 5,5,0" )
      id = rs.FirstObject()
      if id: rs.SelectObject(id)
      # Do something here...
      rs.UnselectObject(id)
    See Also:
      IsObjectSelectable
      IsObjectSelected
      SelectObjects
      UnselectObject
      UnselectObjects
    """
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    rhobj.Select(True)
    if redraw: scriptcontext.doc.Views.Redraw()
    return True


def SelectObjects( object_ids):
    """Selects one or more objects
    Parameters:
      object_ids ([guid, ...]): identifiers of the objects to select
    Returns:
      number: number of selected objects
    Example:
      import rhinoscriptsyntax as rs
      ids = rs.GetObjects("Select object to copy in-place")
      if ids:
          rs.UnselectObjects(ids)
          copies = rs.CopyObjects(ids)
          if copies: rs.SelectObjects(copies)
    See Also:
      IsObjectSelectable
      IsObjectSelected
      SelectObject
      UnselectObject
      UnselectObjects
    """
    id = rhutil.coerceguid(object_ids, False)
    if id: object_ids = [id]
    rc = 0
    for id in object_ids:
        if SelectObject(id, False)==True: rc += 1
    if rc > 0: scriptcontext.doc.Views.Redraw()
    return rc


def ShearObject(object_id, origin, reference_point, angle_degrees, copy=False):
    """Perform a shear transformation on a single object
    Parameters:
      object_id (guid, ...): The identifier of an object
      origin, reference_point (point) origin/reference point of the shear transformation
      copy (bool, optional): copy the objects
    Returns:
      guid: Identifier of the sheared object if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object to shear")
      if obj:
          origin = rs.GetPoint("Origin point")
          refpt = rs.GetPoint("Reference point")
          if origin and refpt:
              rs.ShearObject(obj, origin, refpt, 45.0, True)
    See Also:
      ShearObjects
    """
    rc = ShearObjects(object_id, origin, reference_point, angle_degrees, copy)
    if rc: return rc[0]


def ShearObjects(object_ids, origin, reference_point, angle_degrees, copy=False):
    """Shears one or more objects
    Parameters:
      object_ids ([guid, ...]): The identifiers objects to shear
      origin, reference_point (point): origin/reference point of the shear transformation
      copy (bool, optional): copy the objects
    Returns:
      list(guid, ...]): identifiers of the sheared objects if successful
    Example:
      import rhinoscriptsyntax as rs
      object_ids = rs.GetObjects("Select objects to shear")
      if object_ids:
          origin = rs.GetPoint("Origin point")
          refpt = rs.GetPoint("Reference point")
          if origin and refpt:
              rs.ShearObjects( object_ids, origin, refpt, 45.0, True )
    See Also:
      ShearObject
    """
    origin = rhutil.coerce3dpoint(origin, True)
    reference_point = rhutil.coerce3dpoint(reference_point, True)
    if (origin-reference_point).IsTiny(): return None
    plane = scriptcontext.doc.Views.ActiveView.MainViewport.ConstructionPlane()
    frame = Rhino.Geometry.Plane(plane)
    frame.Origin = origin
    frame.ZAxis = plane.Normal
    yaxis = reference_point-origin
    yaxis.Unitize()
    frame.YAxis = yaxis
    xaxis = Rhino.Geometry.Vector3d.CrossProduct(frame.ZAxis, frame.YAxis)
    xaxis.Unitize()
    frame.XAxis = xaxis

    world_plane = Rhino.Geometry.Plane.WorldXY
    cob = Rhino.Geometry.Transform.ChangeBasis(world_plane, frame)
    shear2d = Rhino.Geometry.Transform.Identity
    shear2d[0,1] = math.tan(math.radians(angle_degrees))
    cobinv = Rhino.Geometry.Transform.ChangeBasis(frame, world_plane)
    xf = cobinv * shear2d * cob
    rc = TransformObjects(object_ids, xf, copy)
    return rc


def ShowObject(object_id):
    """Shows a previously hidden object. Hidden objects are not visible, cannot
    be snapped to and cannot be selected
    Parameters:
      object_id (guid): representing id of object to show
    Returns:
      bool: True of False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object to hide")
      if obj: rs.HideObject(obj)
      # Do something here...
      rs.ShowObject( obj )
    See Also:
      HideObject
      HideObjects
      IsObjectHidden
      ShowObjects
    """
    return ShowObjects(object_id)==1


def ShowObjects(object_ids):
    """Shows one or more objects. Hidden objects are not visible, cannot be
    snapped to and cannot be selected
    Parameters:
      object_ids ([guid, ...]): ids of objects to show
    Returns:
      number: Number of objects shown
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to hide")
      if objs: rs.HideObjects(objs)
      #Do something here...
      rs.ShowObjects( objs )
    See Also:
      HideObject
      HideObjects
      IsObjectHidden
      ShowObject
    """
    id = rhutil.coerceguid(object_ids, False)
    if id: object_ids = [id]
    rc = 0
    for id in object_ids:
        id = rhutil.coerceguid(id, True)
        if scriptcontext.doc.Objects.Show(id, False): rc += 1
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def TransformObject(object_id, matrix, copy=False):
    """Moves, scales, or rotates an object given a 4x4 transformation matrix.
    The matrix acts on the left.
    Parameters:
      object (guid): The identifier of the object.
      matrix (transform): The transformation matrix (4x4 array of numbers).
      copy (bool, optional): Copy the object.
    Returns:
      (guid): The identifier of the transformed object
      None: if not successful, or on error
    Example:
      # Rotate an object by theta degrees about the world Z axis
      import math
      import rhinoscriptsyntax as rs
      degrees = 90.0 # Some angle
      radians = math.radians(degrees)
      c = math.cos(radians)
      s = math.sin(radians)
      matrix = []
      matrix.append( [c,-s, 0, 0] )
      matrix.append( [s, c, 0, 0] )
      matrix.append( [0, 0, 1, 0] )
      matrix.append( [0, 0, 0, 1] )
      obj = rs.GetObject("Select object to rotate")
      if obj: rs.TransformObject( obj, matrix )
    See Also:
      TransformObjects
    """
    rc = TransformObjects(object_id, matrix, copy)
    if rc: return rc[0]
    return scriptcontext.errorhandler()


# this is also called by Copy, Scale, Mirror, Move, and Rotate functions defined above
def TransformObjects(object_ids, matrix, copy=False):
    """Moves, scales, or rotates a list of objects given a 4x4 transformation
    matrix. The matrix acts on the left.
    Parameters:
      object_ids [(guid, ...}): List of object identifiers.
      matrix (transform): The transformation matrix (4x4 array of numbers).
      copy (bool, optional): Copy the objects
    Returns:
      list(guid, ...): ids identifying the newly transformed objects
    Example:
      import rhinoscriptsyntax as rs
      # Translate (move) objects by (10,10,0)
      xform = rs.XformTranslation([10,10,0])
      objs = rs.GetObjects("Select objects to translate")
      if objs: rs.TransformObjects(objs, xform)
    See Also:
      TransformObject
    """
    xform = rhutil.coercexform(matrix, True)
    id = rhutil.coerceguid(object_ids, False)
    if id: object_ids = [id]
    elif isinstance(object_ids, Rhino.Geometry.GeometryBase): object_ids = [object_ids]
    elif type(object_ids) in __ALLOWED_TRANSFORM_TYPES: object_ids = [object_ids]
    rc = []
    for object_id in object_ids:
        id = System.Guid.Empty
        old_id = rhutil.coerceguid(object_id, False)
        if old_id:
            id = scriptcontext.doc.Objects.Transform(old_id, xform, not copy)
        elif isinstance(object_id, Rhino.Geometry.GeometryBase):
            if copy: object_id = object_id.Duplicate()
            if not object_id.Transform(xform): raise Exception("Cannot apply transform to geometry.")
            id = scriptcontext.doc.Objects.Add(object_id)
        else:
            type_of_id = type(object_id)
            if type_of_id in __ALLOWED_TRANSFORM_TYPES:
                if copy: object_id = System.ICloneable.Clone(object_id)
                if object_id.Transform(xform) == False: #some of the Transform methods return bools, others have no return
                    raise Exception("Cannot apply transform to geometry.")
                ot = scriptcontext.doc.Objects
                fs = [ot.AddPoint,ot.AddLine,ot.AddRectangle,ot.AddCircle,ot.AddEllipse,ot.AddArc,ot.AddPolyline,ot.AddBox,ot.AddSphere]
                t_index = __ALLOWED_TRANSFORM_TYPES.index(type_of_id)
                id = fs[t_index](object_id)
            else:
                raise Exception("The {0} cannot be tranformed. A Guid or geometry types are expected.".format(type_of_id))
        if id!=System.Guid.Empty: rc.append(id)
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def UnlockObject(object_id):
    """Unlocks an object. Locked objects are visible, and can be snapped to,
    but they cannot be selected.
    Parameters:
      object_id (guid): The identifier of an object
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object to lock")
      if obj: rs.LockObject(obj)
      #Do something here...
      rs.UnlockObject( obj )
    See Also:
      IsObjectLocked
      LockObject
      LockObjects
      UnlockObjects
    """
    return UnlockObjects(object_id)==1


def UnlockObjects(object_ids):
    """Unlocks one or more objects. Locked objects are visible, and can be
    snapped to, but they cannot be selected.
    Parameters:
      object_ids ([guid, ...]): The identifiers of objects
    Returns:
      number: number of objects unlocked
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to lock")
      if objs: rs.LockObjects(objs)
      #Do something here...
      rs.UnlockObjects( objs )
    See Also:
      IsObjectLocked
      LockObject
      LockObjects
      UnlockObject
    """
    id = rhutil.coerceguid(object_ids, False)
    if id: object_ids = [id]
    rc = 0
    for id in object_ids:
        id = rhutil.coerceguid(id, True)
        if scriptcontext.doc.Objects.Unlock(id, False): rc += 1
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def UnselectObject(object_id):
    """Unselects a single selected object
    Parameters:
      object_id: (guid): id of object to unselect
    Returns:
      bool: True of False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      rs.Command("Line 0,0,0 5,5,0")
      obj = rs.FirstObject()
      if obj: rs.SelectObject(obj)
      #Do something here...
      rs.UnselectObject( obj )
    See Also:
      IsObjectSelected
      SelectObject
      SelectObjects
      UnselectObjects
    """
    return UnselectObjects(object_id)==1


def UnselectObjects(object_ids):
    """Unselects one or more selected objects.
    Parameters:
      object_ids ([guid, ...]): identifiers of the objects to unselect.
    Returns:
      number: The number of objects unselected
    Example:
      import rhinoscriptsyntax as rs
      objects = rs.GetObjects("Select object to copy in-place")
      if objects:
          rs.UnselectObjects(objects)
          copies= rs.CopyObjects(objects)
          if copies: rs.SelectObjects(copies)
    See Also:
      IsObjectSelected
      SelectObject
      SelectObjects
      UnselectObject
    """
    id = rhutil.coerceguid(object_ids, False)
    if id: object_ids = [id]
    count = len(object_ids)
    for id in object_ids:
        obj = rhutil.coercerhinoobject(id, True, True)
        obj.Select(False)
    if count: scriptcontext.doc.Views.Redraw()
    return count
