import Rhino


def CloseToolbarCollection(name, prompt=False):
    """Closes a currently open toolbar collection
    Parameters:
      name (str): name of a currently open toolbar collection
      prompt  (bool, optional): if True, user will be prompted to save the collection file
        if it has been modified prior to closing
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      names = rs.ToolbarCollectionNames()
      if names:
          for name in names: rs.CloseToolbarCollection( name, True )
    See Also:
      IsToolbarCollection
      OpenToolbarCollection
      ToolbarCollectionCount
      ToolbarCollectionNames
      ToolbarCollectionPath
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile: return tbfile.Close(prompt)
    return False


def HideToolbar(name, toolbar_group):
    """Hides a previously visible toolbar group in an open toolbar collection
    Parameters:
      name (str): name of a currently open toolbar file
      toolbar_group (str): name of a toolbar group to hide
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      file = "C:\\SteveBaer\\AppData\\Roaming\\McNeel\\Rhinoceros\\5.0\\UI\\default.rui"
      name = rs.IsToolbarCollection(file)
      if names: rs.HideToolbar(name, "Layer")
    See Also:
      IsToolbar
      IsToolbarVisible
      ShowToolbar
      ToolbarCount
      ToolbarNames
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile:
        group = tbfile.GetGroup(toolbar_group)
        if group:
            group.Visible = False
            return True
    return False


def IsToolbar(name, toolbar, group=False):
    """Verifies a toolbar (or toolbar group) exists in an open collection file
    Parameters:
      name (str): name of a currently open toolbar file
      toolbar (str): name of a toolbar group
      group (bool, optional): if toolbar parameter is referring to a toolbar group
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      file = "C:\\SteveBaer\\AppData\\Roaming\\McNeel\\Rhinoceros\\5.0\\UI\\default.rui"
      name = rs.IsToolbarCollection(file)
      if name:
          if rs.IsToolbar(name, "Layer"):
              print("The collection contains the Layer toolbar.")
          else:
              print("The collection does not contain the Layer toolbar.")
    See Also:
      HideToolbar
      IsToolbarVisible
      ShowToolbar
      ToolbarCount
      ToolbarNames
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile:
        if group: return tbfile.GetGroup(toolbar) != None
        return tbfile.GetToolbar(toolbar) != None
    return False


def IsToolbarCollection(file):
    """Verifies that a toolbar collection is open
    Parameters:
      file (str): full path to a toolbar collection file
    Returns:
      str: Rhino-assigned name of the toolbar collection if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      file = "C:\\SteveBaer\\AppData\\Roaming\\McNeel\\Rhinoceros\\5.0\\UI\\default.rui"
      name = rs.IsToolbarCollection(file)
      if name: print("The default toolbar collection is loaded.")
      else: print("The default toolbar collection is not loaded.")
    See Also:
      CloseToolbarCollection
      OpenToolbarCollection
      ToolbarCollectionCount
      ToolbarCollectionNames
      ToolbarCollectionPath
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByPath(file)
    if tbfile: return tbfile.Name


def IsToolbarDocked(name, toolbar_group):
    """Verifies that a toolbar group in an open toolbar collection is visible
    Parameters:
      name (str): name of a currently open toolbar file
      toolbar_group (str): name of a toolbar group
    Returns:
      boolean: True or False indicating success or failure
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      rc = rs.IsToolbarDocked("Default", "Main1")
      if rc==True:
          print("The Main1 toolbar is docked.")
      elif rc==False:
          print("The Main1 toolbar is not docked.")
      else:
          print("The Main1 toolbar is not visible.")
    See Also:
      IsToolbar
      IsToolbarVisible
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile:
        group = tbfile.GetGroup(toolbar_group)
        if group: return group.IsDocked


def IsToolbarVisible(name, toolbar_group):
    """Verifies that a toolbar group in an open toolbar collection is visible
    Parameters:
      name (str): name of a currently open toolbar file
      toolbar_group (str): name of a toolbar group
    Returns:
      bool:True or False indicating success or failure
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      file = "C:\\SteveBaer\\AppData\\Roaming\\McNeel\\Rhinoceros\\5.0\\UI\\default.rui"
      name = rs.IsToolbarCollection(file)
      if name:
          if rs.IsToolbarVisible(name, "Layer"): print("The Layer toolbar is visible.")
          else: print("The Layer toolbar is not visible.")
    See Also:
      HideToolbar
      IsToolbar
      ShowToolbar
      ToolbarCount
      ToolbarNames
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile:
        group = tbfile.GetGroup(toolbar_group)
        if group: return group.Visible


def OpenToolbarCollection(file):
    """Opens a toolbar collection file
    Parameters:
      file (str): full path to the collection file
    Returns:
      str: Rhino-assigned name of the toolbar collection if successful
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      file = "C:\\SteveBaer\\AppData\\Roaming\\McNeel\\Rhinoceros\\5.0\\UI\\default.rui"
      name = rs.IsToolbarCollection(file)
      if name is None: rs.OpenToolbarCollection(file)
    See Also:
      CloseToolbarCollection
      IsToolbarCollection
      ToolbarCollectionCount
      ToolbarCollectionNames
      ToolbarCollectionPath
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.Open(file)
    if tbfile: return tbfile.Name


def SaveToolbarCollection(name):
    """Saves an open toolbar collection to disk
    Parameters:
      name (str): name of a currently open toolbar file
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      name = "Default"
      rs.SaveToolbarCollection(name)
    See Also:
      SaveToolbarCollectionAs
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile: return tbfile.Save()
    return False


def SaveToolbarCollectionAs(name, file):
    """Saves an open toolbar collection to a different disk file
    Parameters:
      name (str): name of a currently open toolbar file
      file (str): full path to file name to save to
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      name = "Default"
      file = "D:\\NewDefault.rui"
      rs.SaveToolbarCollectionAs(name,file)
    See Also:
      SaveToolbarCollection
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile: return tbfile.SaveAs(file)
    return False


def ShowToolbar(name, toolbar_group):
    """Shows a previously hidden toolbar group in an open toolbar collection
    Parameters:
      name (str): name of a currently open toolbar file
      toolbar_group (str): name of a toolbar group to show
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      file = "C:\\SteveBaer\\AppData\\Roaming\\McNeel\\Rhinoceros\\5.0\\UI\\default.rui"
      name = rs.IsToolbarCollection(file)
      if name: rs.ShowToolbar(name, "Layer")
    See Also:
      HideToolbar
      IsToolbar
      IsToolbarVisible
      ToolbarCount
      ToolbarNames
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile:
        group = tbfile.GetGroup(toolbar_group)
        if group:
            group.Visible = True
            return True
    return False


def ToolbarCollectionCount():
    """Returns number of currently open toolbar collections
    Returns:
      number: the number of currently open toolbar collections
    Example:
      import rhinoscriptsyntax as rs
      count = rs.ToolbarCollectionCount()
      print("There are {} toolbar(s) collections loaded".format(count))
    See Also:
      CloseToolbarCollection
      IsToolbarCollection
      OpenToolbarCollection
      ToolbarCollectionNames
      ToolbarCollectionPath
    """
    return Rhino.RhinoApp.ToolbarFiles.Count


def ToolbarCollectionNames():
    """Returns names of all currently open toolbar collections
    Returns:
      list(str, ...): the names of all currently open toolbar collections
    Example:
      import rhinoscriptsyntax as rs
      names = rs.ToolbarCollectionNames()
      if names:
          for name in names: print(name)
    See Also:
      CloseToolbarCollection
      IsToolbarCollection
      OpenToolbarCollection
      ToolbarCollectionCount
      ToolbarCollectionPath
    """
    return [tbfile.Name for tbfile in Rhino.RhinoApp.ToolbarFiles]


def ToolbarCollectionPath(name):
    """Returns full path to a currently open toolbar collection file
    Parameters:
      name (str): name of currently open toolbar collection
    Returns:
      str: full path on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      names = rs.ToolbarCollectionNames()
      if names:
          for name in names: print(rs.ToolbarCollectionPath(name))
    See Also:
      CloseToolbarCollection
      IsToolbarCollection
      OpenToolbarCollection
      ToolbarCollectionCount
      ToolbarCollectionNames
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile: return tbfile.Path


def ToolbarCount(name, groups=False):
    """Returns the number of toolbars or groups in a currently open toolbar file
    Parameters:
      name (str): name of currently open toolbar collection
      groups (bool, optional): If true, return the number of toolbar groups in the file
    Returns:
      number: number of toolbars on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      names = rs.ToolbarCollectionNames()
      if names:
          count = rs.ToolbarCount(names[0])
          print("The {} collection contains {} toolbars.".format(names[0], count))
    See Also:
      HideToolbar
      IsToolbar
      IsToolbarVisible
      ShowToolbar
      ToolbarNames
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile:
        if groups: return tbfile.GroupCount
        return tbfile.ToolbarCount


def ToolbarNames(name, groups=False):
    """Returns the names of all toolbars (or toolbar groups) found in a
    currently open toolbar file
    Parameters:
      name (str): name of currently open toolbar collection
      groups (bool, optional): If true, return the names of toolbar groups in the file
    Returns:
      list(str, ...): names of all toolbars (or toolbar groups) on success
      None: on error
    Example:
      import rhinoscriptsytax as rs
      names = rs.ToolbarCollectionNames()
      if names:
          toolbars = rs.ToolbarNames(names[0])
          if toolbars:
              for toolbar in toolbars: print(toolbar)
    See Also:
      HideToolbar
      IsToolbar
      IsToolbarVisible
      ShowToolbar
      ToolbarCount
    """
    tbfile = Rhino.RhinoApp.ToolbarFiles.FindByName(name, True)
    if tbfile:
        rc = []
        if groups:
            for i in range(tbfile.GroupCount): rc.append(tbfile.GetGroup(i).Name)
        else:
            for i in range(tbfile.ToolbarCount): rc.append(tbfile.GetToolbar(i).Name)
        return rc;