import Rhino

import scriptcontext

import rhinocompat as compat
from rhinoscript import utility as rhutil


def __getlinetype(name_or_id):
    id = rhutil.coerceguid(name_or_id)
    if id: return scriptcontext.doc.Linetypes.FindId(id)
    return scriptcontext.doc.Linetypes.FindName(name_or_id)


def IsLinetype(name_or_id):
    """Verifies the existance of a linetype in the document
    Parameters:
      name_or_id (guid|str): The name or identifier of an existing linetype.
    Returns: 
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      name = rs.GetString("Linetype name")
      if rs.IsLinetype(name): print("The linetype exists.")
      else: print("The linetype does not exist")
    See Also:
      IsLinetypeReference
    """
    lt = __getlinetype(name_or_id)
    return lt is not None


def IsLinetypeReference(name_or_id):
    """Verifies that an existing linetype is from a reference file
    Parameters:
      name_or_id (guid|str): The name or identifier of an existing linetype.
    Returns: 
      bool: True or False
    Example:
      import rhinoscriptsyntax as rs
      name = rs.GetString("Linetype name")
      if rs.IsLinetype(name):
          if rs.IsLinetypeReference(name):
              print("The linetype is a reference linetype.")
          else:
              print("The linetype is not a reference linetype.")
      else:
          print("The linetype does not exist.")
    See Also:
      IsLinetype
    """
    lt = __getlinetype(name_or_id)
    if lt is None: raise ValueError("unable to coerce %s into linetype"%name_or_id)
    return lt.IsReference


def LinetypeCount():
    """Returns number of linetypes in the document
    Returns:
      number: the number of linetypes in the document
    Example:
      import rhinoscriptsyntax as rs
      count = rs.LinetypeCount()
      print("There are {} linetypes".format(count))
    See Also:
      LinetypeNames
    """
    return scriptcontext.doc.Linetypes.Count


def LinetypeNames(sort=False):
    """Returns names of all linetypes in the document
    Parameters:
      sort (bool, optional): return a sorted list of the linetype names
    Returns:
      list(str, ...): list of linetype names if successful
    Example:
      import rhinoscriptsyntax as rs
      names = rs.LinetypeNames()
      if names:
          for name in names: print(name)
    See Also:
      LinetypeCount
    """
    count = scriptcontext.doc.Linetypes.Count
    rc = []
    for i in compat.RANGE(count):
        linetype = scriptcontext.doc.Linetypes[i]
        if not linetype.IsDeleted: rc.append(linetype.Name)
    if sort: rc.sort()
    return rc
