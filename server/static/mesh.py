import System
import System.Drawing

import Rhino

import scriptcontext

import rhinocompat as compat
from rhinoscript import utility as rhutil
from rhinoscript.view import __viewhelper


def AddMesh(vertices, face_vertices, vertex_normals=None, texture_coordinates=None, vertex_colors=None):
    """Add a mesh object to the document
    Parameters:
      vertices ([point, ...]) list of 3D points defining the vertices of the mesh
      face_vertices ([[number, number, number], [number, number, number, number], ...]) list containing lists of 3 or 4 numbers that define the
                    vertex indices for each face of the mesh. If the third a fourth vertex
                     indices of a face are identical, a triangular face will be created.
      vertex_normals ([vector, ...], optional) list of 3D vectors defining the vertex normals of
        the mesh. Note, for every vertex, there must be a corresponding vertex
        normal
      texture_coordinates ([[number, number], [number, number], [number, number]], ...], optional): list of 2D texture coordinates. For every
        vertex, there must be a corresponding texture coordinate
      vertex_colors ([color, ...]) a list of color values. For every vertex,
        there must be a corresponding vertex color
    Returns:
      guid: Identifier of the new object if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      vertices = []
      vertices.append((0.0,0.0,0.0))
      vertices.append((5.0, 0.0, 0.0))
      vertices.append((10.0, 0.0, 0.0))
      vertices.append((0.0, 5.0, 0.0))
      vertices.append((5.0, 5.0, 0.0))
      vertices.append((10.0, 5.0, 0.0))
      vertices.append((0.0, 10.0, 0.0))
      vertices.append((5.0, 10.0, 0.0))
      vertices.append((10.0, 10.0, 0.0))
      faceVertices = []
      faceVertices.append((0,1,4,4))
      faceVertices.append((2,4,1,1))
      faceVertices.append((0,4,3,3))
      faceVertices.append((2,5,4,4))
      faceVertices.append((3,4,6,6))
      faceVertices.append((5,8,4,4))
      faceVertices.append((6,4,7,7))
      faceVertices.append((8,7,4,4))
      rs.AddMesh( vertices, faceVertices )
    See Also:
      MeshFaces
      MeshFaceVertices
      MeshVertexNormals
      MeshVertices
    """
    mesh = Rhino.Geometry.Mesh()
    for a, b, c in vertices: mesh.Vertices.Add(a, b, c)
    for face in face_vertices:
        if len(face)<4:
            mesh.Faces.AddFace(face[0], face[1], face[2])
        else:
            mesh.Faces.AddFace(face[0], face[1], face[2], face[3])
    if vertex_normals:
        count = len(vertex_normals)
        normals = System.Array.CreateInstance(Rhino.Geometry.Vector3f, count)
        for i, normal in enumerate(vertex_normals):
            normals[i] = Rhino.Geometry.Vector3f(normal[0], normal[1], normal[2])
        mesh.Normals.SetNormals(normals)
    if texture_coordinates:
        count = len(texture_coordinates)
        tcs = System.Array.CreateInstance(Rhino.Geometry.Point2f, count)
        for i, tc in enumerate(texture_coordinates):
            tcs[i] = Rhino.Geometry.Point2f(tc[0], tc[1])
        mesh.TextureCoordinates.SetTextureCoordinates(tcs)
    if vertex_colors:
        count = len(vertex_colors)
        colors = System.Array.CreateInstance(System.Drawing.Color, count)
        for i, color in enumerate(vertex_colors):
            colors[i] = rhutil.coercecolor(color)
        mesh.VertexColors.SetColors(colors)
    rc = scriptcontext.doc.Objects.AddMesh(mesh)
    if rc==System.Guid.Empty: raise Exception("unable to add mesh to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddPlanarMesh(object_id, delete_input=False):
    """Creates a planar mesh from a closed, planar curve
    Parameters:
      object_id (guid): identifier of a closed, planar curve
      delete_input (bool, optional) if True, delete the input curve defined by object_id
    Returns:
      guid: id of the new mesh on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select planar curves to build mesh", rs.filter.curve)
      if obj: rs.AddPlanarMesh(obj)
    See Also:
      IsCurveClosed
      IsCurvePlanar
    """
    curve = rhutil.coercecurve(object_id, -1, True)
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    mesh = Rhino.Geometry.Mesh.CreateFromPlanarBoundary(curve, Rhino.Geometry.MeshingParameters.Default, tolerance)
    if not mesh: return scriptcontext.errorhandler()
    if delete_input:
        id = rhutil.coerceguid(object_id, True)
        rc = scriptcontext.doc.Objects.Replace(id, mesh)
    else:
        rc = scriptcontext.doc.Objects.AddMesh(mesh)
    if rc==System.Guid.Empty: raise Exception("unable to add mesh to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def CurveMeshIntersection(curve_id, mesh_id, return_faces=False):
    """Calculates the intersection of a curve object and a mesh object
    Parameters:
      curve_id (guid): identifier of a curve object
      mesh_id (guid): identifier or a mesh object
      return_faces (bool, optional): return both intersection points and face indices.
        If False, then just the intersection points are returned
    Returns:
      list(point, ...): if return_false is omitted or False, then a list of intersection points
      list([point, number], ...): if return_false is True, the a one-dimensional list containing information
        about each intersection. Each element contains the following two elements
          [0] = point of intersection
          [1] = mesh face index where intersection lies
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      curve = rs.GetObject("Select curve to intersect", rs.filter.curve)
      if curve:
          mesh = rs.GetObject("Select mesh to intersect", rs.filter.mesh)
          if mesh:
              cmx = rs.CurveMeshIntersection(curve, mesh, True)
              if cmx:
                  for element in cmx:
                      print("{}, Face index = {}".format(element[0], element[1]))
                      rs.AddPoint(element[0])
    See Also:
      MeshClosestPoint
      MeshMeshIntersection
    """
    curve = rhutil.coercecurve(curve_id, -1, True)
    mesh = rhutil.coercemesh(mesh_id, True)
    tolerance = scriptcontext.doc.ModelAbsoluteTolerance
    polylinecurve = curve.ToPolyline(0,0,0,0,0.0,tolerance,0.0,0.0,True)
    pts, faceids = Rhino.Geometry.Intersect.Intersection.MeshPolyline(mesh, polylinecurve)
    if not pts: return scriptcontext.errorhandler()
    pts = list(pts)
    if return_faces:
        faceids = list(faceids)
        return compat.ITERATOR2LIST(zip(pts, faceids))
    return pts


def DisjointMeshCount(object_id):
    """Returns number of meshes that could be created by calling SplitDisjointMesh
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      number: The number of meshes that could be created
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      if rs.DisjointMeshCount(obj)>1: rs.SplitDisjointMesh(obj)
    See Also:
      IsMesh
      SplitDisjointMesh
    """
    mesh = rhutil.coercemesh(object_id, True)
    return mesh.DisjointMeshCount


def DuplicateMeshBorder(mesh_id):
    """Creates curves that duplicates a mesh border
    Parameters:
      mesh_id (guid): identifier of a mesh object
    Returns:
      list(guid, ...): list of curve ids on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      if obj: rs.DuplicateMeshBorder(obj)
    See Also:
      DuplicateEdgeCurves
      DuplicateSurfaceBorder
    """
    mesh = rhutil.coercemesh(mesh_id, True)
    polylines = mesh.GetNakedEdges()
    rc = []
    if polylines:
        for polyline in polylines:
            id = scriptcontext.doc.Objects.AddPolyline(polyline)
            if id!=System.Guid.Empty: rc.append(id)
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def ExplodeMeshes(mesh_ids, delete=False):
    """Explodes a mesh object, or mesh objects int submeshes. A submesh is a
    collection of mesh faces that are contained within a closed loop of
    unwelded mesh edges. Unwelded mesh edges are where the mesh faces that
    share the edge have unique mesh vertices (not mesh topology vertices)
    at both ends of the edge
    Parameters:
      mesh_ids ([guid, ...]): list of mesh identifiers
      delete (bool, optional): delete the input meshes
    Returns:
      list(guid, ...): List of resulting objects after explode.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh to explode", rs.filter.mesh)
      if rs.IsMesh(obj): rs.ExplodeMeshes(obj)
    See Also:
      IsMesh
    """
    id = rhutil.coerceguid(mesh_ids)
    if id: mesh_ids = [mesh_ids]
    rc = []
    for mesh_id in mesh_ids:
        mesh = rhutil.coercemesh(mesh_id, True)
        if mesh:
            submeshes = mesh.ExplodeAtUnweldedEdges()
            if submeshes:
                for submesh in submeshes:
                    id = scriptcontext.doc.Objects.AddMesh(submesh)
                    if id!=System.Guid.Empty: rc.append(id)
            if delete:
                scriptcontext.doc.Objects.Delete(mesh_id, True)
                
    if rc: scriptcontext.doc.Views.Redraw()
    return rc


def IsMesh(object_id):
    """Verifies if an object is a mesh
    Parameters:
      object_id (guid): the object's identifier
    Returns:
      bool: True if successful, otherwise False
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a mesh")
      if rs.IsMesh(obj):
          print("The object is a mesh.")
      else:
          print("The object is not a mesh.")
    See Also:
      IsMeshClosed
      MeshFaceCount
      MeshFaces
      MeshVertexCount
      MeshVertices
    """
    mesh = rhutil.coercemesh(object_id)
    return mesh is not None


def IsMeshClosed(object_id):
    """Verifies a mesh object is closed
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      bool: True if successful, otherwise False.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a mesh", rs.filter.mesh)
      if rs.IsMeshClosed(obj):
          print("The mesh is closed.")
      else:
          print("The mesh is not closed.")
    See Also:
      IsMesh
    """
    mesh = rhutil.coercemesh(object_id, True)
    return mesh.IsClosed


def IsMeshManifold(object_id):
    """Verifies a mesh object is manifold. A mesh for which every edge is shared
    by at most two faces is called manifold. If a mesh has at least one edge
    that is shared by more than two faces, then that mesh is called non-manifold
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      bool: True if successful, otherwise False.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a mesh", rs.filter.mesh)
      if rs.IsMeshClosed(obj):
          print("The mesh is manifold.")
      else:
          print("The mesh is non-manifold.")
    See Also:
      IsMesh
      IsMeshClosed
    """
    mesh = rhutil.coercemesh(object_id, True)
    rc = mesh.IsManifold(True)
    return rc[0]


def IsPointOnMesh(object_id, point):
    """Verifies a point is on a mesh
    Parameters:
      object_id (guid): identifier of a mesh object
      point (point): test point
    Returns:
      bool: True if successful, otherwise False.
      None: on error.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a mesh")
      if rs.IsMesh(obj):
          point = rs.GetPointOnMesh(strObject, "Pick a test point")
          if point:
              if rs.IsPointOnMesh(obj, point):
                  print("The point is on the mesh")
              else:
                  print("The point is not on the mesh")
    See Also:
      IsMesh
      MeshClosestPoint
    """
    mesh = rhutil.coercemesh(object_id, True)
    point = rhutil.coerce3dpoint(point, True)
    max_distance = Rhino.RhinoMath.SqrtEpsilon
    face, pt = mesh.ClosestPoint(point, max_distance)
    return face>=0


def JoinMeshes(object_ids, delete_input=False):
    """Joins two or or more mesh objects together
    Parameters:
      object_ids ([guid, ...]): identifiers of two or more mesh objects
      delete_input (bool, optional): delete input after joining
    Returns:
      guid: identifier of newly created mesh on success
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select meshes to join", rs.filter.mesh)
      if objs and len(objs)>1: rs.JoinMeshes(objs, True)
    See Also:
      JoinCurves
      JoinSurfaces
    """
    meshes = [rhutil.coercemesh(id,True) for id in object_ids]
    joined_mesh = Rhino.Geometry.Mesh()
    joined_mesh.Append(meshes)
    rc = scriptcontext.doc.Objects.AddMesh(joined_mesh)
    if delete_input:
        for id in object_ids:
            guid = rhutil.coerceguid(id)
            scriptcontext.doc.Objects.Delete(guid,True)
    scriptcontext.doc.Views.Redraw()
    return rc


def MeshArea(object_ids):
    """Returns approximate area of one or more mesh objects
    Parameters:
      object_ids ([guid, ...]): identifiers of one or more mesh objects
    Returns:
      list(number, number, number): if successful where
        [0] = number of meshes used in calculation
        [1] = total area of all meshes
        [2] = the error estimate
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh )
      if obj:
          area_rc = rs.MeshArea(obj)
          if area_rc: print("Mesh area:{}".format(area_rc[1]))
    See Also:
      MeshVolume
    """
    id = rhutil.coerceguid(object_ids)
    if id: object_ids = [object_ids]
    meshes_used = 0
    total_area = 0.0
    error_estimate = 0.0
    for id in object_ids:
        mesh = rhutil.coercemesh(id, True)
        if mesh:
            mp = Rhino.Geometry.AreaMassProperties.Compute(mesh)
            if mp:
                meshes_used += 1
                total_area += mp.Area
                error_estimate += mp.AreaError
    if meshes_used==0: return scriptcontext.errorhandler()
    return meshes_used, total_area, error_estimate


def MeshAreaCentroid(object_id):
    """Calculates the area centroid of a mesh object
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      point: representing the area centroid if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh )
      rs.AddPoint( rs.MeshAreaCentroid(obj) )
    See Also:
      IsMesh
      MeshArea
      MeshVolume
      MeshVolumeCentroid
    """
    mesh = rhutil.coercemesh(object_id, True)
    mp = Rhino.Geometry.AreaMassProperties.Compute(mesh)
    if mp is None: return scriptcontext.errorhandler()
    return mp.Centroid


def MeshBooleanDifference(input0, input1, delete_input=True, tolerance=None):
    """Performs boolean difference operation on two sets of input meshes
    Parameters:
      input0, input1 (guid): identifiers of meshes
      delete_input (bool, optional): delete the input meshes
      tolerance (float, optional): this value is ignored. 
          The parameter is only there to keep the function signature the same, 
          The build in tolerenace always is used.
    Returns:
      list(guid, ...): identifiers of newly created meshes
    Example:
      import rhinoscriptsyntax as rs
      input0 = rs.GetObjects("Select first set of meshes", rs.filter.mesh)
      if input0:
          input1 = rs.GetObjects("Select second set of meshes", rs.filter.mesh)
          if input1: rs.MeshBooleanDifference(input0, input1)
    See Also:
      MeshBooleanIntersection
      MeshBooleanSplit
      MeshBooleanUnion
    """
    id = rhutil.coerceguid(input0)
    if id: input0 = [id]
    id = rhutil.coerceguid(input1)
    if id: input1 = [id]
    meshes0 = [rhutil.coercemesh(id, True) for id in input0]
    meshes1 = [rhutil.coercemesh(id, True) for id in input1]
    if not meshes0 or not meshes1: raise ValueError("no meshes to work with")
    newmeshes = Rhino.Geometry.Mesh.CreateBooleanDifference(meshes0, meshes1)
    rc = []
    for mesh in newmeshes:
        id = scriptcontext.doc.Objects.AddMesh(mesh)
        if id!=System.Guid.Empty: rc.append(id)
    if rc and delete_input:
        input = input0 + input1
        for id in input:
            id = rhutil.coerceguid(id, True)
            scriptcontext.doc.Objects.Delete(id, True)
    scriptcontext.doc.Views.Redraw()
    return rc


def MeshBooleanIntersection(input0, input1, delete_input=True):
    """Performs boolean intersection operation on two sets of input meshes
    Parameters:
      input0, input1 (guid): identifiers of meshes
      delete_input (bool, optional): delete the input meshes
    Returns:
      list(guid, ...): identifiers of new meshes on success
    Example:
      import rhinoscriptsyntax as rs
      input0 = rs.GetObjects("Select first set of meshes", rs.filter.mesh)
      if input0:
          input1 = rs.GetObjects("Select second set of meshes", rs.filter.mesh)
          if input1: rs.MeshBooleanIntersection(input0, input1)
    See Also:
      MeshBooleanDifference
      MeshBooleanSplit
      MeshBooleanUnion
    """
    id = rhutil.coerceguid(input0)
    if id: input0 = [id]
    id = rhutil.coerceguid(input1)
    if id: input1 = [id]
    meshes0 = [rhutil.coercemesh(id, True) for id in input0]
    meshes1 = [rhutil.coercemesh(id, True) for id in input1]
    if not meshes0 or not meshes1: raise ValueError("no meshes to work with")
    newmeshes = Rhino.Geometry.Mesh.CreateBooleanIntersection(meshes0, meshes1)
    rc = []
    for mesh in newmeshes:
        id = scriptcontext.doc.Objects.AddMesh(mesh)
        if id!=System.Guid.Empty: rc.append(id)
    if rc and delete_input:
        input = input0 + input1
        for id in input:
            id = rhutil.coerceguid(id, True)
            scriptcontext.doc.Objects.Delete(id, True)
    scriptcontext.doc.Views.Redraw()
    return rc


def MeshBooleanSplit(input0, input1, delete_input=True):
    """Performs boolean split operation on two sets of input meshes
    Parameters:
      input0, input1 (guid): identifiers of meshes
      delete_input (bool, optional): delete the input meshes
    Returns:
      list(guid, ...): identifiers of new meshes on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      input0 = rs.GetObjects("Select first set of meshes", rs.filter.mesh)
      if input0:
          input1 = rs.GetObjects("Select second set of meshes", rs.filter.mesh)
          if input1: rs.MeshBooleanSplit(input0, input1)
    See Also:
      MeshBooleanDifference
      MeshBooleanIntersection
      MeshBooleanUnion
    """
    id = rhutil.coerceguid(input0)
    if id: input0 = [id]
    id = rhutil.coerceguid(input1)
    if id: input1 = [id]
    meshes0 = [rhutil.coercemesh(id, True) for id in input0]
    meshes1 = [rhutil.coercemesh(id, True) for id in input1]
    if not meshes0 or not meshes1: raise ValueError("no meshes to work with")
    newmeshes = Rhino.Geometry.Mesh.CreateBooleanSplit(meshes0, meshes1)
    rc = []
    for mesh in newmeshes:
        id = scriptcontext.doc.Objects.AddMesh(mesh)
        if id!=System.Guid.Empty: rc.append(id)
    if rc and delete_input:
        input = input0 + input1
        for id in input:
            id = rhutil.coerceguid(id, True)
            scriptcontext.doc.Objects.Delete(id, True)
    scriptcontext.doc.Views.Redraw()
    return rc


def MeshBooleanUnion(mesh_ids, delete_input=True):
    """Performs boolean union operation on a set of input meshes
    Parameters:
      mesh_ids ([guid, ...]): identifiers of meshes
      delete_input (bool, optional): delete the input meshes
    Returns:
      list(guid, ...): identifiers of new meshes
    Example:
      import rhinoscriptsyntax as rs
      input = rs.GetObjects("Select meshes to union", rs.filter.mesh)
      if input: rs.MeshBooleanUnion(input)
    See Also:
      MeshBooleanDifference
      MeshBooleanIntersection
      MeshBooleanSplit
    """
    if len(mesh_ids)<2: raise ValueError("mesh_ids must contain at least 2 meshes")
    meshes = [rhutil.coercemesh(id, True) for id in mesh_ids]
    newmeshes = Rhino.Geometry.Mesh.CreateBooleanUnion(meshes)
    rc = []
    for mesh in newmeshes:
        id = scriptcontext.doc.Objects.AddMesh(mesh)
        if id!=System.Guid.Empty: rc.append(id)
    if rc and delete_input:
        for id in mesh_ids:
            id = rhutil.coerceguid(id, True)
            scriptcontext.doc.Objects.Delete(id, True)
    scriptcontext.doc.Views.Redraw()
    return rc


def MeshClosestPoint(object_id, point, maximum_distance=None):
    """Returns the point on a mesh that is closest to a test point
    Parameters:
      object_id (guid): identifier of a mesh object
      point (point): point to test
      maximum_distance (number, optional): upper bound used for closest point calculation.
        If you are only interested in finding a point Q on the mesh when
        point.DistanceTo(Q) < maximum_distance, then set maximum_distance to
        that value
    Returns:
      tuple(point, number): containing the results of the calculation where
                            [0] = the 3-D point on the mesh
                            [1] = the index of the mesh face on which the 3-D point lies
      None: on error
    Example:
      import rhinocriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      point = rs.GetPoint("Pick test point")
      intersect = rs.MeshClosestPoint(obj, point)
      if intersect: rs.AddPoint(intersect)
    See Also:
      MeshFaceCount
      MeshFaces
    """
    mesh = rhutil.coercemesh(object_id, True)
    point = rhutil.coerce3dpoint(point, True)
    tolerance=maximum_distance if maximum_distance else 0.0
    face, closest_point = mesh.ClosestPoint(point, tolerance)
    if face<0: return scriptcontext.errorhandler()
    return closest_point, face


def MeshFaceCenters(mesh_id):
    """Returns the center of each face of the mesh object
    Parameters:
      mesh_id (guid): identifier of a mesh object
    Returns:
      list(point, ...): points defining the center of each face
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      centers = rs.MeshFaceCenters(obj)
      if centers:
          for point in centers: rs.AddPoint(point)
    See Also:
      IsMesh
      MeshFaceCount
      MeshFaces
    """
    mesh = rhutil.coercemesh(mesh_id, True)
    return [mesh.Faces.GetFaceCenter(i) for i in range(mesh.Faces.Count)]


def MeshFaceCount(object_id):
    """Returns total face count of a mesh object
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      number: the number of mesh faces if successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh )
      print("Quad faces:{}".format(rs.MeshQuadCount(obj)))
      print("Triangle faces:{}".format(rs.MeshTriangleCount(obj)))
      print("Total faces:{}".format(rs.MeshFaceCount(obj)))
    See Also:
      IsMesh
      MeshFaces
      MeshVertexCount
      MeshVertices
    """
    mesh = rhutil.coercemesh(object_id, True)
    return mesh.Faces.Count


def MeshFaceNormals(mesh_id):
    """Returns the face unit normal for each face of a mesh object
    Parameters:
      mesh_id (guid): identifier of a mesh object
    Returns:
      list(vector, ...): 3D vectors that define the face unit normals of the mesh
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      normals = rs.MeshFaceNormals(obj)
      if normals:
          for vector in normals: print(vector)
    See Also:
      MeshHasFaceNormals
      MeshFaceCount
      MeshFaces
    """
    mesh = rhutil.coercemesh(mesh_id, True)
    if mesh.FaceNormals.Count != mesh.Faces.Count:
        mesh.FaceNormals.ComputeFaceNormals()
    rc = []
    for i in compat.RANGE(mesh.FaceNormals.Count):
        normal = mesh.FaceNormals[i]
        rc.append(Rhino.Geometry.Vector3d(normal))
    return rc


def MeshFaces(object_id, face_type=True):
    """Returns face vertices of a mesh
    Parameters:
      object_id (guid): identifier of a mesh object
      face_type (bool, optional): The face type to be returned. True = both triangles
        and quads. False = only triangles
    Returns:
      list([point, point, point, point], ...): 3D points that define the face vertices of the mesh. If
      face_type is True, then faces are returned as both quads and triangles
      (4 3D points). For triangles, the third and fourth vertex will be
      identical. If face_type is False, then faces are returned as only
      triangles(3 3D points). Quads will be converted to triangles.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      faces = rs.MeshFaces(obj, False)
      if faces:
          rs.EnableRedraw(False)
          i = 0
          while( i<=len(faces) ):
              face = faces[i], faces[i+1], faces[i+2], faces[i]
              rs.AddPolyline( face )
              i += 3
      rs.EnableRedraw(True)
    See Also:
      IsMesh
      MeshFaceCount
      MeshVertexCount
      MeshVertices
    """
    mesh = rhutil.coercemesh(object_id, True)
    rc = []
    for i in compat.RANGE(mesh.Faces.Count):
        getrc, p0, p1, p2, p3 = mesh.Faces.GetFaceVertices(i)
        p0 = Rhino.Geometry.Point3d(p0)
        p1 = Rhino.Geometry.Point3d(p1)
        p2 = Rhino.Geometry.Point3d(p2)
        p3 = Rhino.Geometry.Point3d(p3)
        rc.append( p0 )
        rc.append( p1 )
        rc.append( p2 )
        if face_type:
            rc.append(p3)
        else:
            if p2!=p3:
                rc.append( p2 )
                rc.append( p3 )
                rc.append( p0 )
    return rc


def MeshFaceVertices(object_id):
    """Returns the vertex indices of all faces of a mesh object
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      list((number, number, number, number), ...): containing tuples of 4 numbers that define the vertex indices for
      each face of the mesh. Both quad and triangle faces are returned. If the
      third and fourth vertex indices are identical, the face is a triangle.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      faceVerts = rs.MeshFaceVertices( obj )
      if faceVerts:
          for count, face in enumerate(faceVerts):
              print("face({}) = ({}, {}, {}, {})".format(count, face[0], face[1], face[2], face[3]))
    See Also:
      IsMesh
      MeshFaceCount
      MeshFaces
    """
    mesh = rhutil.coercemesh(object_id, True)
    rc = []
    for i in compat.RANGE(mesh.Faces.Count):
        face = mesh.Faces.GetFace(i)
        rc.append( (face.A, face.B, face.C, face.D) )
    return rc


def MeshHasFaceNormals(object_id):
    """Verifies a mesh object has face normals
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      bool: True if successful, otherwise False.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a mesh", rs.filter.mesh)
      if rs.MeshHasFaceNormals(obj):
          print("The mesh has face normal.")
      else:
          print("The mesh does not have face normals.")
    See Also:
      MeshFaceNormals
    """
    mesh = rhutil.coercemesh(object_id, True)
    return mesh.FaceNormals.Count>0


def MeshHasTextureCoordinates(object_id):
    """Verifies a mesh object has texture coordinates
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      bool: True if successful, otherwise False.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a mesh", rs.filter.mesh)
      if rs.MeshHasTextureCoordinates(obj):
          print("The mesh has texture coordinates.")
      else:
          print("The mesh does not have texture coordinates.")
    See Also:
      
    """
    mesh = rhutil.coercemesh(object_id, True)
    return mesh.TextureCoordinates.Count>0


def MeshHasVertexColors(object_id):
    """Verifies a mesh object has vertex colors
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      bool: True if successful, otherwise False.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a mesh", rs.filter.mesh)
      if rs.mesh.MeshHasVertexColors(obj):
          print("The mesh has vertex colors.")
      else:
          print("The mesh does not have vertex colors.")
    See Also:
      MeshVertexColors
    """
    mesh = rhutil.coercemesh(object_id, True)
    return mesh.VertexColors.Count>0


def MeshHasVertexNormals(object_id):
    """Verifies a mesh object has vertex normals
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      bool: True if successful, otherwise False.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select a mesh", rs.filter.mesh)
      if rs.MeshHasVertexNormals(obj):
          print("The mesh has vertex normals.")
      else:
          print("The mesh does not have vertex normals.")
    See Also:
      MeshVertexNormals
    """
    mesh = rhutil.coercemesh(object_id, True)
    return mesh.Normals.Count>0


def MeshMeshIntersection(mesh1, mesh2, tolerance=None):
    """Calculates the intersections of a mesh object with another mesh object
    Parameters:
      mesh1, mesh2 (guid): identifiers of meshes
      tolerance (number, optional): the intersection tolerance. Defaults to ModelAbsoluteTolerance * MeshIntersectionsTolerancesCoefficient
    Returns:
      list(point, ...): of points that define the vertices of the intersection curves
    Example:
      import rhinoscriptsyntax as rs
      mesh1 = rs.GetObject("Select first mesh to intersect", rs.filter.mesh)
      mesh2 = rs.GetObject("Select second mesh to intersect", rs.filter.mesh)
      results = rs.MeshMeshIntersection(mesh1, mesh2)
      if results:
          for points in results: rs.AddPolyline(points)
    See Also:
      CurveMeshIntersection
      MeshClosestPoint
    """
    mesh1 = rhutil.coercemesh(mesh1, True)
    mesh2 = rhutil.coercemesh(mesh2, True)
    if tolerance is None:
      tolerance = scriptcontext.doc.ModelAbsoluteTolerance * Rhino.Geometry.Intersect.Intersection.MeshIntersectionsTolerancesCoefficient
    polylines = Rhino.Geometry.Intersect.Intersection.MeshMeshAccurate(mesh1, mesh2, tolerance)
    if polylines: return list(polylines)


def MeshNakedEdgePoints(object_id):
    """Identifies the naked edge points of a mesh object. This function shows
    where mesh vertices are not completely surrounded by faces. Joined
    meshes, such as are made by MeshBox, have naked mesh edge points where
    the sub-meshes are joined
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      list(bool, ...): of boolean values that represent whether or not a mesh vertex is
      naked or not. The number of elements in the list will be equal to
      the value returned by MeshVertexCount. In which case, the list will
      identify the naked status for each vertex returned by MeshVertices
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      vertices = rs.MeshVertices( obj )
      naked = rs.MeshNakedEdgePoints( obj )
      for i, vertex in enumerate(vertices):
          if naked[i]: rs.AddPoint(vertex)
    See Also:
      IsMesh
      MeshVertexCount
      MeshVertices
    """
    mesh = rhutil.coercemesh(object_id, True)
    rc = mesh.GetNakedEdgePointStatus()
    return rc


def MeshOffset(mesh_id, distance):
    """Makes a new mesh with vertices offset at a distance in the opposite
    direction of the existing vertex normals
    Parameters:
      mesh_id (guid): identifier of a mesh object
      distance (number, optional): the distance to offset
    Returns:
      guid: identifier of the new mesh object if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      mesh = rs.GetObject("Select mesh to offset", rs.filter.mesh)
      rs.MeshOffset( mesh, 10.0 )
    See Also:
      IsMesh
    """
    mesh = rhutil.coercemesh(mesh_id, True)
    offsetmesh = mesh.Offset(distance)
    if offsetmesh is None: return scriptcontext.errorhandler()
    rc = scriptcontext.doc.Objects.AddMesh(offsetmesh)
    if rc==System.Guid.Empty: raise Exception("unable to add mesh to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def MeshOutline(object_ids, view=None):
    """Creates polyline curve outlines of mesh objects
    Parameters:
      objects_ids ([guid, ...]): identifiers of meshes to outline
      view (str, optional): view to use for outline direction
    Returns:
      list(guid, ...): polyline curve identifiers on success
    Example:
      import rhinoscriptsyntax as rs
      objs = rs.GetObjects("Select mesh objects to outline", rs.filter.mesh)
      if objs: rs.MeshOutline(objs)
    See Also:
      IsMesh
    """
    viewport = __viewhelper(view).MainViewport
    meshes = []
    mesh = rhutil.coercemesh(object_ids, False)
    if mesh: meshes.append(mesh)
    else: meshes = [rhutil.coercemesh(id,True) for id in object_ids]
    rc = []
    for mesh in meshes:
        polylines = mesh.GetOutlines(viewport)
        if not polylines: continue
        for polyline in polylines:
            id = scriptcontext.doc.Objects.AddPolyline(polyline)
            rc.append(id)
    scriptcontext.doc.Views.Redraw()
    return rc


def MeshQuadCount(object_id):
    """Returns the number of quad faces of a mesh object
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      number: the number of quad mesh faces if successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh )
      print("Quad faces:{}".format(rs.MeshQuadCount(obj)))
      print("Triangle faces:{}".format(rs.MeshTriangleCount(obj)))
      print("Total faces:{}".format(rs.MeshFaceCount(obj)))
    See Also:
      MeshQuadCount
    """
    mesh = rhutil.coercemesh(object_id, True)
    return mesh.Faces.QuadCount


def MeshQuadsToTriangles(object_id):
    """Converts a mesh object's quad faces to triangles
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      bool: True or False indicating success or failure
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh )
      if rs.MeshQuadCount(obj)>0:
          rs.MeshQuadsToTriangles(obj)
    See Also:
      
    """
    mesh = rhutil.coercemesh(object_id, True)
    rc = True
    if mesh.Faces.QuadCount>0:
        rc = mesh.Faces.ConvertQuadsToTriangles()
        if rc:
            id = rhutil.coerceguid(object_id, True)
            scriptcontext.doc.Objects.Replace(id, mesh)
            scriptcontext.doc.Views.Redraw()
    return rc


def MeshToNurb(object_id, trimmed_triangles=True, delete_input=False):
    """Duplicates each polygon in a mesh with a NURBS surface. The resulting
    surfaces are then joined into a polysurface and added to the document
    Parameters:
      object_id (guid): identifier of a mesh object
      trimmed_triangles (bool, optional): if True, triangles in the mesh will be
        represented by a trimmed plane
      delete_input (bool, optional): delete input object
    Returns:
      list(guid, ...): identifiers for the new breps on success
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      if obj: rs.MeshToNurb(obj)
    See Also:
      IsMesh
      MeshFaces
      MeshVertices
    """
    mesh = rhutil.coercemesh(object_id, True)
    pieces = mesh.SplitDisjointPieces()
    breps = [Rhino.Geometry.Brep.CreateFromMesh(piece,trimmed_triangles) for piece in pieces]
    rhobj = rhutil.coercerhinoobject(object_id, True, True)
    attr = rhobj.Attributes
    ids = [scriptcontext.doc.Objects.AddBrep(brep, attr) for brep in breps]
    if delete_input: scriptcontext.doc.Objects.Delete(rhobj, True)
    scriptcontext.doc.Views.Redraw()
    return ids


def MeshTriangleCount(object_id):
    """Returns number of triangular faces of a mesh
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      number: The number of triangular mesh faces if successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh )
      print("Quad faces:{}".format(rs.MeshQuadCount(obj)))
      print("Triangle faces:{}".format(rs.MeshTriangleCount(obj)))
      print("Total faces:{}".format(rs.MeshFaceCount(obj)))
    See Also:
      IsMesh
    """
    mesh = rhutil.coercemesh(object_id, True)
    return mesh.Faces.TriangleCount


def MeshVertexColors(mesh_id, colors=0):
    """Returns of modifies vertex colors of a mesh
    Parameters:
      mesh_id (guid): identifier of a mesh object
      colors 9{color, ...], optional) A list of color values. Note, for each vertex, there must
        be a corresponding vertex color. If the value is None, then any
        existing vertex colors will be removed from the mesh
    Returns:
      color: if colors is not specified, the current vertex colors
      color: if colors is specified, the previous vertex colors
    Example:
      import rhinoscriptsyntax as rs
      import random
       
      def randomcolor():
          r = random.randint(0,255)
          g = random.randint(0,255)
          b = random.randint(0,255)
          return r,g,b
       
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      if obj:
          colors = []
          for i in range(rs.MeshVertexCount(obj)): colors.append( randomcolor() )
          rs.MeshVertexColors( obj, colors )
    See Also:
      MeshHasVertexColors
      MeshVertexCount
      MeshVertices
    """
    mesh = rhutil.coercemesh(mesh_id, True)
    rc = [mesh.VertexColors[i] for i in range(mesh.VertexColors.Count)]
    if colors==0: return rc
    if colors is None:
        mesh.VertexColors.Clear()
    else:
        color_count = len(colors)
        if color_count!=mesh.Vertices.Count:
            raise ValueError("length of colors must match vertex count")
        colors = [rhutil.coercecolor(c) for c in colors]
        mesh.VertexColors.Clear()
        for c in colors: mesh.VertexColors.Add(c)
    id = rhutil.coerceguid(mesh_id, True)
    scriptcontext.doc.Objects.Replace(id, mesh)
    scriptcontext.doc.Views.Redraw()
    return rc


def MeshVertexCount(object_id):
    """Returns the vertex count of a mesh
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      number: The number of mesh vertices if successful.
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh )
      print("Vertex count: {}".format(rs.MeshVertexCount(obj)))
    See Also:
      IsMesh
      MeshFaceCount
      MeshFaces
      MeshVertices
    """
    mesh = rhutil.coercemesh(object_id, True)
    return mesh.Vertices.Count


def MeshVertexFaces(mesh_id, vertex_index):
    """Returns the mesh faces that share a specified mesh vertex
    Parameters:
      mesh_id (guid): identifier of a mesh object
      vertex_index (number): index of the mesh vertex to find faces for
    Returns:
      list(number, ...): face indices on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      import random
      def TestMeshVertexFaces():
          mesh = rs.GetObject("Select mesh", rs.filter.mesh)
          vertices = rs.MeshVertices(mesh)
          meshfaces = rs.MeshFaceVertices(mesh)
          vertex = random.randint(0, len(vertices)-1) #some random vertex
          vertex_faces = rs.MeshVertexFaces(mesh, vertex )
          if vertex_faces:
              rs.AddPoint( vertices[vertex] )
              for face_index in vertex_faces:
                  face = meshfaces[face_index]
                  polyline = []
                  polyline.append( vertices[face[0]] )
                  polyline.append( vertices[face[1]] )
                  polyline.append( vertices[face[2]] )
                  if face[2]!=face[3]:
                      polyline.append( vertices[face[3]] )
                  polyline.append( polyline[0] )
                  rs.AddPolyline(polyline)
       
      TestMeshVertexFaces()
    See Also:
      MeshFaces
      MeshFaceVertices
      MeshVertices
    """
    mesh = rhutil.coercemesh(mesh_id, True)
    return mesh.Vertices.GetVertexFaces(vertex_index)


def MeshVertexNormals(mesh_id):
    """Returns the vertex unit normal for each vertex of a mesh
    Parameters:
      mesh_id (guid): identifier of a mesh object
    Returns:
      list(vector, ...): of vertex normals, (empty list if no normals exist)
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      normals = rs.MeshVertexNormals(obj)
      if normals:
          for normal in normals: print(normal)
    See Also:
      MeshHasVertexNormals
      MeshVertexCount
      MeshVertices
    """
    mesh = rhutil.coercemesh(mesh_id, True)
    count = mesh.Normals.Count
    if count<1: return []
    return [Rhino.Geometry.Vector3d(mesh.Normals[i]) for i in compat.RANGE(count)]


def MeshVertices(object_id):
    """Returns the vertices of a mesh
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      list(point, ...): vertex points in the mesh
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      vertices = rs.MeshVertices(obj)
      if vertices: rs.AddPointCloud(vertices)
    See Also:
      IsMesh
      MeshFaceCount
      MeshFaces
      MeshVertexCount
    """
    mesh = rhutil.coercemesh(object_id, True)
    count = mesh.Vertices.Count
    rc = []
    for i in compat.RANGE(count):
        vertex = mesh.Vertices.Point3dAt(i)
        rc.append(vertex)
    return rc


def MeshVolume(object_ids):
    """Returns the approximate volume of one or more closed meshes
    Parameters:
      object_ids ([guid, ...]): identifiers of one or more mesh objects
    Returns:
      tuple(number, number, number): containing 3 velues if successful where
           [0] = number of meshes used in volume calculation
           [1] = total volume of all meshes
           [2] = the error estimate
      None: if not successful
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh )
      if obj and rs.IsMeshClosed(obj):
          volume = rs.MeshVolume(obj)
          if volume: print("Mesh volume:{}".format(volume[1]))
    See Also:
      IsMeshClosed
      MeshArea
    """
    id = rhutil.coerceguid(object_ids)
    if id: object_ids = [id]
    meshes_used = 0
    total_volume = 0.0
    error_estimate = 0.0
    for id in object_ids:
        mesh = rhutil.coercemesh(id, True)
        mp = Rhino.Geometry.VolumeMassProperties.Compute(mesh)
        if mp:
            meshes_used += 1
            total_volume += mp.Volume
            error_estimate += mp.VolumeError
    if meshes_used==0: return scriptcontext.errorhandler()
    return meshes_used, total_volume, error_estimate


def MeshVolumeCentroid(object_id):
    """Calculates the volume centroid of a mesh
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      point: Point3d representing the volume centroid
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh )
      centroid = rs.MeshVolumeCentroid(obj)
      rs.AddPoint( centroid )
    See Also:
      IsMesh
      MeshArea
      MeshAreaCentroid
      MeshVolume
    """
    mesh = rhutil.coercemesh(object_id, True)
    mp = Rhino.Geometry.VolumeMassProperties.Compute(mesh)
    if mp: return mp.Centroid
    return scriptcontext.errorhandler()


def PullCurveToMesh(mesh_id, curve_id):
    """Pulls a curve to a mesh. The function makes a polyline approximation of
    the input curve and gets the closest point on the mesh for each point on
    the polyline. Then it "connects the points" to create a polyline on the mesh
    Parameters:
      mesh_id (guid): identifier of mesh that pulls
      curve_id (guid): identifier of curve to pull
    Returns:
      guid: identifier new curve on success
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      mesh = rs.GetObject("Select mesh that pulls", rs.filter.mesh)
      curve = rs.GetObject("Select curve to pull", rs.filter.curve)
      rs.PullCurveToMesh( mesh, curve )
    See Also:
      IsMesh
    """
    mesh = rhutil.coercemesh(mesh_id, True)
    curve = rhutil.coercecurve(curve_id, -1, True)
    tol = scriptcontext.doc.ModelAbsoluteTolerance
    polyline = curve.PullToMesh(mesh, tol)
    if not polyline: return scriptcontext.errorhandler()
    rc = scriptcontext.doc.Objects.AddCurve(polyline)
    if rc==System.Guid.Empty: raise Exception("unable to add polyline to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def SplitDisjointMesh(object_id, delete_input=False):
    """Splits up a mesh into its unconnected pieces
    Parameters:
      object_id (guid): identifier of a mesh object
      delete_input (bool, optional): delete the input object
    Returns:
      list(guid, ...): identifiers for the new meshes
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      if rs.DisjointMeshCount(obj)>0: rs.SplitDisjointMesh(obj)
    See Also:
      IsMesh
      DisjointMeshCount
    """
    mesh = rhutil.coercemesh(object_id, True)
    pieces = mesh.SplitDisjointPieces()
    rc = [scriptcontext.doc.Objects.AddMesh(piece) for piece in pieces]
    if rc and delete_input:
        id = rhutil.coerceguid(object_id, True)
        scriptcontext.doc.Objects.Delete(id, True)
    scriptcontext.doc.Views.Redraw()
    return rc


def UnifyMeshNormals(object_id):
    """Fixes inconsistencies in the directions of faces of a mesh
    Parameters:
      object_id (guid): identifier of a mesh object
    Returns:
      number: the number of faces that were modified
    Example:
      import rhinoscriptsyntax as rs
      obj = rs.GetObject("Select mesh", rs.filter.mesh)
      if rs.IsMesh(obj): rs.UnifyMeshNormals(obj)
    See Also:
      IsMesh
    """
    mesh = rhutil.coercemesh(object_id, True)
    rc = mesh.UnifyNormals()
    if rc>0:
        id = rhutil.coerceguid(object_id, True)
        scriptcontext.doc.Objects.Replace(id, mesh)
        scriptcontext.doc.Views.Redraw()
    return rc
