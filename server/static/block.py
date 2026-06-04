import math

import System

import Rhino

import scriptcontext

from rhinoscript import utility as rhutil


def __InstanceObjectFromId(id, raise_if_missing):
    rhobj = rhutil.coercerhinoobject(id, True, raise_if_missing)
    if isinstance(rhobj, Rhino.DocObjects.InstanceObject): return rhobj
    if raise_if_missing: raise ValueError("unable to find InstanceObject")


def AddBlock(object_ids, base_point, name=None, delete_input=False):
    """Adds a new block definition to the document
    Parameters:
      object_ids ([guid, ....]) objects that will be included in the block
      base_point (point): 3D base point for the block definition
      name (str, optional): name of the block definition. If omitted a name will be
        automatically generated
      delete_input (bool): if True, the object_ids will be deleted
    Returns:
      str: name of new block definition on success
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select objects to define block")
      if objs:
          point = rs.GetPoint("Block base point")
          if point:
              block = rs.AddBlock(objs, point, None, True)
              rs.InsertBlock(block, point)
    See Also:
      InsertBlock
    """
    base_point = rhutil.coerce3dpoint(base_point, True)
    if not name:
        name = scriptcontext.doc.InstanceDefinitions.GetUnusedInstanceDefinitionName()
    found = scriptcontext.doc.InstanceDefinitions.Find(name)
    objects = []
    for id in object_ids:
        obj = rhutil.coercerhinoobject(id, True)
        if obj.IsReference: return
        ot = obj.ObjectType
        if ot==Rhino.DocObjects.ObjectType.Light: return
        if ot==Rhino.DocObjects.ObjectType.Grip: return
        if ot==Rhino.DocObjects.ObjectType.Phantom: return
        if ot==Rhino.DocObjects.ObjectType.InstanceReference and found:
            uses, nesting = obj.UsesDefinition(found.Index)
            if uses: return
        objects.append(obj)
    if objects:
        geometry = [obj.Geometry for obj in objects]
        attrs = [obj.Attributes for obj in objects]
        rc = 0
        if found:
          rc = scriptcontext.doc.InstanceDefinitions.ModifyGeometry(found.Index, geometry, attrs)
        else:
          rc = scriptcontext.doc.InstanceDefinitions.Add(name, "", base_point, geometry, attrs)
        if rc>=0:
            if delete_input:
                for obj in objects: scriptcontext.doc.Objects.Delete(obj, True)
            scriptcontext.doc.Views.Redraw()
    return name


def BlockContainerCount(block_name):
    """Returns number of block definitions that contain a specified
    block definition
    Parameters:
      block_name (str): the name of an existing block definition
    Returns:
      number: the number of block definitions that contain a specified block definition
    Example:
      import rhinoscriptscriptsyntax as rs
      block = rs.GetString("Block name to query")
      if rs.IsBlock(block):
          count = rs.BlockContainerCount(block)
          print("This block is nested in {} block(s).".format(count))
    See Also:
      BlockContainers
      IsBlock
    """
    return len(BlockContainers(block_name))


def BlockContainers(block_name):
    """Returns names of the block definitions that contain a specified block
    definition.
    Parameters:
      block_name (str): the name of an existing block definition
    Returns:
      list(str, ...): A list of block definition names
    Example:
      import rhinoscriptsyntax as rs
      blockname = rs.GetString("Block name to query")
      if rs.IsBlock(blockname):
          blocks = rs.BlockContainers(blockname)
          for block in blocks: print(block)
    See Also:
      BlockContainerCount
      IsBlock
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    containers = idef.GetContainers()
    rc = []
    for item in containers:
        if not item.IsDeleted: rc.append(item.Name)
    return rc


def BlockCount():
    """Returns the number of block definitions in the document
    Returns:
      number: the number of block definitions in the document
    Example:
      import rhinoscriptsyntax as rs
      count = rs.BlockCount()
      print("There are {} blocks".format(count)
    See Also:
      BlockNames
      IsBlock
    """
    return scriptcontext.doc.InstanceDefinitions.ActiveCount


def BlockDescription(block_name, description=None):
    """Returns or sets the description of a block definition
    Parameters:
      block_name (str): the name of an existing block definition
      description (str, optional): The new description.
    Returns:
      str: if description is not specified, the current description
      str: if description is specified, the previous description
    Example:
      import rhinoscriptsyntax as rs
      blockname = rs.GetString("Block name to list description")
      if rs.IsBlock(blockname):
          desc = rs.BlockDescription(blockname)
          if desc is None: print("No description")
          else: print(desc)
    See Also:
      IsBlock
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    rc = idef.Description
    if description: scriptcontext.doc.InstanceDefinitions.Modify( idef, idef.Name, description, True )
    return rc


def BlockInstanceCount(block_name,where_to_look=0):
    """Counts number of instances of the block in the document.
    Nested instances are not included in the count.
    Parameters:
      block_name (str): the name of an existing block definition
      where_to_look (number, optional):
        0 = get top level references in active document.
        1 = get top level and nested references in active document.
        2 = check for references from other instance definitions
    Returns:
      number: the number of instances of the block in the document
    Example:
      import rhinoscriptsyntax as rs
      blockname = rs.GetString("Block to count")
      if rs.IsBlock(blockname):
          count = rs.BlockInstanceCount(blockname)
          print("{} block(s) found.".format(count))
    See Also:
      BlockInstanceInsertPoint
      BlockInstances
      BlockInstanceXform
      IsBlockInstance
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    refs = idef.GetReferences(where_to_look)
    return len(refs)


def BlockInstanceInsertPoint(object_id):
    """Returns the insertion point of a block instance.
    Parameters:
      object_id (guid): The identifier of an existing block insertion object
    Returns:
      point: The insertion 3D point if successful
    Example:
      import rhinoscriptsyntax as rs
      strObject = rs.GetObject("Select block")
      if rs.IsBlockInstance(strObject):
          rs.AddPoint( rs.BlockInstanceInsertPoint(strObject) )
    See Also:
      BlockInstanceCount
      BlockInstances
      BlockInstanceXform
      IsBlockInstance
    """
    instance = __InstanceObjectFromId(object_id, True)
    xf = instance.InstanceXform
    pt = Rhino.Geometry.Point3d.Origin
    pt.Transform(xf)
    return pt


def BlockInstanceName(object_id):
    """Returns the block name of a block instance
    Parameters:
      object_id (guid): The identifier of an existing block insertion object
    Returns:
      str: the block name of a block instance
    Example:
      import rhinoscriptsyntax as rs
      strObject = rs.GetObject("Select block")
      if rs.IsBlockInstance(strObject):
          print(rs.BlockInstanceName(strObject))
    See Also:
      BlockInstanceCount
      BlockInstances
      BlockInstanceXform
      IsBlockInstance
    """
    instance = __InstanceObjectFromId(object_id, True)
    idef = instance.InstanceDefinition
    return idef.Name


def BlockInstances(block_name,where_to_look=0):
    """Returns the identifiers of the inserted instances of a block.
    Parameters:
      block_name (str): the name of an existing block definition
      where_to_look (number, optional):
        0 = get top level references in active document.
        1 = get top level and nested references in active document.
        2 = check for references from other instance definitions
    Returns:
      list(guid, ...): Ids identifying the instances of a block in the model.
    Example:
      import rhinoscriptsyntax as rs
      strBlock = rs.GetString("Block to select")
      if rs.IsBlock(strBlock):
          arrObjects = rs.BlockInstances(strBlock)
          if arrobjects:
              rs.SelectObjects(arrObjects)
    See Also:
      BlockInstanceCount
      BlockInstanceInsertPoint
      BlockInstanceXform
      IsBlockInstance
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    instances = idef.GetReferences(where_to_look)
    return [item.Id for item in instances]


def BlockInstanceXform(object_id):
    """Returns the location of a block instance relative to the world coordinate
    system origin (0,0,0). The position is returned as a 4x4 transformation
    matrix
    Parameters:
      object_id (guid): The identifier of an existing block insertion object
    Returns:
      transform: the location, as a transform matrix, of a block instance relative to the world coordinate
    system origin
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select block to query")
      if rs.IsBlockInstance(obj):
          arrMatrix = rs.BlockInstanceXform(obj)
          if arrMatrix is not None:
              pointId = rs.AddPoint([0,0,0])
              rs.TransformObject( pointId, arrMatrix)
    See Also:
      BlockInstanceCount
      BlockInstanceInsertPoint
      BlockInstances
      IsBlockInstance
    """
    instance = __InstanceObjectFromId(object_id, True)
    return instance.InstanceXform


def BlockNames( sort=False ):
    """Returns the names of all block definitions in the document
    Parameters:
      sort (bool): True to return a sorted list
    Returns:
      list(str, ...): the names of all block definitions in the document
    Example:
      import rhinoscriptsyntax as rs
      names = rs.BlockNames(True)
      if names:
          for name in names: print(name)
    See Also:
      BlockCount
      IsBlock
    """
    ideflist = scriptcontext.doc.InstanceDefinitions.GetList(True)
    rc = [item.Name for item in ideflist]
    if(sort): rc.sort()
    return rc


def BlockObjectCount(block_name):
    """Returns number of objects that make up a block definition
    Parameters:
      block_name (str): name of an existing block definition
    Returns:
      number: the number of objects that make up a block definition
    Example:
      import rhinoscriptsyntax as rs
      count = rs.BlockObjectCount()
      print("There are {} blocks".format(count))
    See Also:
      BlockNames
      BlockObjects
      IsBlock
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    return idef.ObjectCount


def BlockObjects(block_name):
    """Returns identifiers of the objects that make up a block definition
    Parameters:
      block_name (str): name of an existing block definition
    Returns:
      list(guid, ...): list of identifiers on success
    Example:
      import rhinoscriptsyntax as rs
      strBlock = rs.GetString("Block name to list identifiers")
      if rs.IsBlock(strBlock):
          objects = rs.BlockObjects(strBlock)
          if objects:
              for item in objects: print(item)
    See Also:
      BlockNames
      BlockObjectCount
      IsBlock
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    rhobjs = idef.GetObjects()
    return [obj.Id for obj in rhobjs]


def BlockPath(block_name):
    """Returns path to the source of a linked or embedded block definition.
    A linked or embedded block definition is a block definition that was
    inserted from an external file.
    Parameters:
      block_name (str): name of an existing block definition
    Returns:
      str: path to the linked block on success
    Example:
      import rhinoscriptsyntax as rs
      strBlock = rs.GetString("Block name to list path")
      if rs.IsBlockEmbedded(strBlock):
          print(rs.BlockPath(strBlock))
    See Also:
      IsBlock
      IsBlockEmbedded
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    return idef.SourceArchive


def BlockStatus(block_name):
    """Returns the status of a linked block
    Parameters:
        block_name (str): Name of an existing block
    Returns:
      number: the status of a linked block
        Value Description
        -3    Not a linked block definition.
        -2    The linked block definition's file could not be opened or could not be read.
        -1    The linked block definition's file could not be found.
         0    The linked block definition is up-to-date.
         1    The linked block definition's file is newer than definition.
         2    The linked block definition's file is older than definition.
         3    The linked block definition's file is different than definition.
    Example:
      import rhinoscriptsyntax as rs
      block = rs.GetString("Block name to list description")
      if rs.IsBlock(block):
          status = rs.BlockStatus(block)
          print("block status for {} is {}".format(block, status))
    See Also:
      IsBlock
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: return -3
    return int(idef.ArchiveFileStatus)


def DeleteBlock(block_name):
    """Deletes a block definition and all of it's inserted instances.
    Parameters:
      block_name (str): name of an existing block definition
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      strBlock = rs.GetString("Block name to delete")
      if rs.IsBlock(strBlock):
          rs.DeleteBlock(strBlock)
    See Also:
      BlockNames
      ExplodeBlockInstance
      IsBlock
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    rc = scriptcontext.doc.InstanceDefinitions.Delete(idef.Index, True, False)
    scriptcontext.doc.Views.Redraw()
    return rc


def ExplodeBlockInstance(object_id, explode_nested_instances=False):
    """Explodes a block instance into it's geometric components. The
    exploded objects are added to the document
    Parameters:
      object_id (guid): The identifier of an existing block insertion object
      explode_nested_instances (bool, optional): By default nested blocks are not exploded.
    Returns:
      list(guid, ...): identifiers for the newly exploded objects on success
    Example:
      import rhinoscriptsyntax as rs
      strObject = rs.GetObject("Select block instance to explode")
      if rs.IsBlockInstance(strObject):
          rs.ExplodeBlockInstance(strObject)
    See Also:
      DeleteBlock
      IsBlockInstance
    """
    instance = __InstanceObjectFromId(object_id, True)
    guids = scriptcontext.doc.Objects.AddExplodedInstancePieces(instance, explodeNestedInstances=explode_nested_instances, deleteInstance=True)
    if guids:
      scriptcontext.doc.Views.Redraw()
    return guids


def InsertBlock( block_name, insertion_point, scale=(1,1,1), angle_degrees=0, rotation_normal=(0,0,1) ):
    """Inserts a block whose definition already exists in the document
    Parameters:
      block_name (str): name of an existing block definition
      insertion_point (point): insertion point for the block
      scale ({number, number, number]): x,y,z scale factors
      angle_degrees (number, optional): rotation angle in degrees
      rotation_normal (vector, optional): the axis of rotation.
    Returns:
      guid: id for the block that was added to the doc
    Example:
    See Also:
    """
    insertion_point = rhutil.coerce3dpoint(insertion_point, True)
    rotation_normal = rhutil.coerce3dvector(rotation_normal, True)
    angle_radians = math.radians(angle_degrees)
    trans = Rhino.Geometry.Transform
    move = trans.Translation(insertion_point[0],insertion_point[1],insertion_point[2])
    scale = trans.Scale(Rhino.Geometry.Plane.WorldXY, scale[0], scale[1], scale[2])
    rotate = trans.Rotation(angle_radians, rotation_normal, Rhino.Geometry.Point3d.Origin)
    xform = move * scale * rotate
    return InsertBlock2( block_name, xform )


def InsertBlock2(block_name, xform):
    """Inserts a block whose definition already exists in the document
    Parameters:
      block_name (str): name of an existing block definition
      xform (transform): 4x4 transformation matrix to apply
    Returns:
      guid: id for the block that was added to the doc on success
    Example:
    See Also:
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    xform = rhutil.coercexform(xform, True)
    id = scriptcontext.doc.Objects.AddInstanceObject(idef.Index, xform )
    if id!=System.Guid.Empty:
        scriptcontext.doc.Views.Redraw()
        return id


def IsBlock(block_name):
    """Verifies the existence of a block definition in the document.
    Parameters:
      block_name (str): name of an existing block definition
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      strBlock = rs.GetString("Block name")
      if rs.IsBlock(strBlock):
          print("The block definition exists.")
      else:
          print("The block definition does not exist.")
    See Also:
      IsBlockEmbedded
      IsBlockInstance
      IsBlockInUse
      IsBlockReference
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    return (idef is not None)


def IsBlockEmbedded(block_name):
    """Verifies a block definition is embedded, or linked, from an external file.
    Parameters:
      block_name (str): name of an existing block definition
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      strBlock = rs.GetString("Block name")
      if rs.IsBlock(strBlock):
          if rs.IsBlockEmbedded(strBlock):
              print("The block definition is embedded.")
          else:
              print("The block definition is not embedded.")
      else:
          print("The block definition does not exist.")
    See Also:
      IsBlock
      IsBlockInstance
      IsBlockInUse
      IsBlockReference
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    ut = Rhino.DocObjects.InstanceDefinitionUpdateType
    return (idef.UpdateType==ut.Embedded or idef.UpdateType==ut.Static or idef.UpdateType==ut.LinkedAndEmbedded)


def IsBlockInstance(object_id):
    """Verifies an object is a block instance
    Parameters:
      object_id (guid): The identifier of an existing block insertion object
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select block instance")
      if rs.IsBlockInstance(obj):
          print("The object is a block instance.")
      else:
          print("The object is not a block instance.")
    See Also:
      IsBlock
      IsBlockEmbedded
      IsBlockInUse
      IsBlockReference
    """
    return  __InstanceObjectFromId(object_id, False) is not None


def IsBlockInUse(block_name, where_to_look=0):
    """Verifies that a block definition is being used by an inserted instance
    Parameters:
      block_name (str): name of an existing block definition
      where_to_look (number, optional): One of the following values
           0 = Check for top level references in active document
           1 = Check for top level and nested references in active document
           2 = Check for references in other instance definitions
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      strBlock = rs.GetString("Block name")
      if rs.IsBlock(strBlock):
          if rs.IsBlockInUse(strBlock):
              print("The block definition is in use.")
          else:
              print("The block definition is not in use.")
      else:
          print("The block definition does not exist.")
    See Also:
      IsBlock
      IsBlockInstance
      IsBlockEmbedded
      IsBlockReference
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    return idef.InUse(where_to_look)


def IsBlockReference(block_name):
    """Verifies that a block definition is from a reference file.
    Parameters:
      block_name (str): name of an existing block definition
    Returns:
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      strBlock = rs.GetString("Block name")
      if rs.IsBlock(strBlock):
          if rs.IsBlockReference(strBlock):
              print("The block definition is a reference definition.")
          else:
              print("The block definition is not a reference definition.")
      else:
          print("The block definition does not exist.")
    See Also:
      IsBlock
      IsBlockEmbedded
      IsBlockInUse
      IsBlockInstance
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    return idef.IsReference


def RenameBlock( block_name, new_name ):
    """Renames an existing block definition
    Parameters:
      block_name (str): name of an existing block definition
      new_name (str): name to change to
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      strOldBlock = rs.GetString("Old block name")
      if strOldBlock:
          strNewBlock = rs.GetString("New block name")
          if strNewBlock:
              rs.RenameBlock (strOldBlock, strNewBlock)
    See Also:
      BlockNames
      IsBlock
    """
    idef = scriptcontext.doc.InstanceDefinitions.Find(block_name)
    if not idef: raise ValueError("%s does not exist in InstanceDefinitionsTable"%block_name)
    description = idef.Description
    rc = scriptcontext.doc.InstanceDefinitions.Modify(idef, new_name, description, False)
    return rc
