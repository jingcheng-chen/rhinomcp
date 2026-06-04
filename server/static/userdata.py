import scriptcontext

from rhinoscript import utility as rhutil


def DeleteDocumentData(section=None, entry=None):
    """Removes user data strings from the current document
    Parameters:
      section (str, optional): section name. If omitted, all sections and their corresponding
        entries are removed
      entry (str, optional): entry name. If omitted, all entries for section are removed
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      rs.DeleteDocumentData( "MySection1", "MyEntry1" )
      rs.DeleteDocumentData( "MySection1", "MyEntry2" )
      rs.DeleteDocumentData( "MySection2", "MyEntry1" )
    See Also:
      DocumentDataCount
      GetDocumentData
      IsDocumentData
      SetDocumentData
    """
    return scriptcontext.doc.Strings.Delete(section, entry)


def DocumentDataCount():
    """Returns the number of user data strings in the current document
    Returns:
      number: the number of user data strings in the current document
    Example:
      import rhinoscriptsyntax as rs
      count = rs.DocumentDataCount()
      print("RhinoScript document user data count: {}".format(count))
    See Also:
      DeleteDocumentData
      GetDocumentData
      IsDocumentData
      SetDocumentData
    """
    return scriptcontext.doc.Strings.DocumentDataCount


def DocumentUserTextCount():
    """Returns the number of user text strings in the current document
    Returns:
      number: the number of user text strings in the current document
    Example:
      
    See Also:
      GetDocumentUserText
      IsDocumentUserText
      SetDocumentUserText
    """
    return scriptcontext.doc.Strings.DocumentUserTextCount


def GetDocumentData(section=None, entry=None):
    """Returns a user data item from the current document
    Parameters:
      section (str, optional): section name. If omitted, all section names are returned
      entry (str, optional): entry name. If omitted, all entry names for section are returned
    Returns:
      list(str, ...): of all section names if section name is omitted
      list(str, ...) of all entry names for a section if entry is omitted
      str: value of the entry if both section and entry are specified
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      value = rs.GetDocumentData("MySection1", "MyEntry1")
      print(value)
      value = rs.GetDocumentData("MySection1", "MyEntry2")
      print(value)
      value = rs.GetDocumentData("MySection2", "MyEntry1")
      print(value)
    See Also:
      DeleteDocumentData
      DocumentDataCount
      IsDocumentData
      SetDocumentData
    """
    if section is None:
        rc = scriptcontext.doc.Strings.GetSectionNames()
        return list(rc) if rc else None
    if entry is None:
        rc = scriptcontext.doc.Strings.GetEntryNames(section)
        return list(rc) if rc else None
    val = scriptcontext.doc.Strings.GetValue(section, entry)
    return val if val else None


def GetDocumentUserText(key=None):
    """Returns user text stored in the document
    Parameters:
      key (str, optional): key to use for retrieving user text. If empty, all keys are returned
    Returns:
      str: If key is specified, then the associated value if successful.
      list(str, ...):If key is not specified, then a list of key names if successful.
      None: If not successful, or on error.
    Example:
      import rhinoscriptsyntax as rs
      print(rs.GetDocumentUserText("Designer"))
      print(rs.GetDocumentUserText("Notes"))
    See Also:
      SetDocumentUserText
    """
    if key: 
      val =  scriptcontext.doc.Strings.GetValue(key)
      return val if val else None
    #todo: leaky abstraction: "\\" logic should be inside doc.Strings implementation
    keys = [scriptcontext.doc.Strings.GetKey(i) for i in range(scriptcontext.doc.Strings.Count) if not "\\" in scriptcontext.doc.Strings.GetKey(i)]
    return keys if keys else None


def GetUserText(object_id, key=None, attached_to_geometry=False):
    """Returns user text stored on an object.
    Parameters:
      object_id (guid): the object's identifies
      key (str, optional): the key name. If omitted all key names for an object are returned
      attached_to_geometry (bool, optional): location on the object to retrieve the user text
    Returns:
      str: if key is specified, the associated value if successful
      list(str, ...): if key is not specified, a list of key names if successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          print(rs.GetUserText(obj, "PartNo"))
          print(rs.GetUserText(obj, "Price"))
    See Also:
      IsUserText
      SetUserText
    """
    obj = rhutil.coercerhinoobject(object_id, True, True)
    source = None
    if attached_to_geometry: source = obj.Geometry
    else: source = obj.Attributes
    rc = None
    if key: return source.GetUserString(key)
    userstrings = source.GetUserStrings()
    return [userstrings.GetKey(i) for i in range(userstrings.Count)]


def IsDocumentData():
    """Verifies the current document contains user data
    Returns:
      bool: True or False indicating the presence of Script user data
    Example:
      import rhinoscriptsyntax as rs
      result = rs.IsDocumentData()
      if result:
          print("This document contains Script document user data")
      else:
          print("This document contains no Script document user data")
    See Also:
      DeleteDocumentData
      DocumentDataCount
      GetDocumentData
      SetDocumentData
    """
    return scriptcontext.doc.Strings.DocumentDataCount > 0


def IsDocumentUserText():
    """Verifies the current document contains user text
    Returns:
      bool: True or False indicating the presence of Script user text
    Example:
      
    See Also:
      GetDocumentUserText
      SetDocumentUserText
    """
    return scriptcontext.doc.Strings.DocumentUserTextCount > 0


def IsUserText(object_id):
    """Verifies that an object contains user text
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      number: result of test:
        0 = no user text
        1 = attribute user text
        2 = geometry user text
        3 = both attribute and geometry user text
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")  
      if obj:
          usertext_type = rs.IsUserText(obj)
          if usertext_type==0: print("Object has no user text")
          elif usertext_type==1: print("Object has attribute user text")
          elif usertext_type==2: print("Object has geometry user text")
          elif usertext_type==3: print("Object has attribute and geometry user text")
          else: print("Object does not exist")
    See Also:
      GetUserText
      SetUserText
    """
    obj = rhutil.coercerhinoobject(object_id, True, True)
    rc = 0
    if obj.Attributes.UserStringCount: rc = rc|1
    if obj.Geometry.UserStringCount: rc = rc|2
    return rc


def SetDocumentData(section, entry, value):
    """Adds or sets a user data string to the current document
    Parameters:
      section (str): the section name
      entry (str): the entry name
      value (str): the string value
    Returns:
      str: The previous value
    Example:
      import rhinoscriptsyntax as rs
      rs.SetDocumentData( "MySection1", "MyEntry1", "MyValue1" )
      rs.SetDocumentData( "MySection1", "MyEntry2", "MyValue2" )
      rs.SetDocumentData( "MySection2", "MyEntry1", "MyValue1" )
    See Also:
      DeleteDocumentData
      DocumentDataCount
      GetDocumentData
      IsDocumentData
    """
    val = scriptcontext.doc.Strings.SetString(section, entry, value)
    return val if val else None


def SetDocumentUserText(key, value=None):
    """Sets or removes user text stored in the document
    Parameters:
      key (str): key name to set
      value (str): The string value to set. If omitted the key/value pair
        specified by key will be deleted
    Returns:
      bool: True or False indicating success
    Example:
      import rhinoscriptsyntax as rs
      rs.SetDocumentUserText("Designer", "Steve Baer")
      rs.SetDocumentUserText("Notes", "Added some layer and updated some geometry")
    See Also:
      GetDocumentUserText
    """
    if value: scriptcontext.doc.Strings.SetString(key,value)
    else: scriptcontext.doc.Strings.Delete(key)
    return True


def SetUserText(object_id, key, value=None, attach_to_geometry=False):
    """Sets or removes user text stored on an object.
    Parameters:
      object_id (str): the object's identifier
      key (str): the key name to set
      value (str, optional) the string value to set. If omitted, the key/value pair
          specified by key will be deleted
      attach_to_geometry (bool, optional): location on the object to store the user text
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select object")
      if obj:
          rs.SetUserText( obj, "PartNo", "KM40-4960" )
          rs.SetUserText( obj, "Price", "1.25" )
    See Also:
      GetUserText
      IsUserText
    """
    obj = rhutil.coercerhinoobject(object_id, True, True)
    if type(key) is not str: key = str(key)
    if value and type(value) is not str: value = str(value)
    if attach_to_geometry: return obj.Geometry.SetUserString(key, value)
    return obj.Attributes.SetUserString(key, value)