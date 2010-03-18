#!/usr/bin/python
#
# Copyright (C) 2010 Marcel Tunnissen
#
# License: GNU Public License version 2
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not,
# check at http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# or write to the Free Software Foundation,
#
#------------------------------------------------------------------
#
# I am not sure where to put these functions. These convert objects from A to
# B. Should they be in A or in B?

import math
import X3D
import PS
import Geom3D

X3D_DEFAULT_V_NAME     = 'coords'
X3D_DEFAULT_PROTO_NAME = 'proto'
X3D_DEFAULT_TRANS_NAME = 'transform'
X3D_DEFAULT_SHAPE_NAME = 'shape'

def ConvertVec3ToX3d(vertices, precision):
    Vs = []
    for v in vertices:
        Vs.append(X3D.FloatVec(v, precision))
        #print v, X3D.FloatVec(v).vec, X3D.FloatVec(v).toVrmlStr() 
    return Vs

def ConvertIndicesToX3d(indexVecs):
    result = []
    for indexV in indexVecs:
        result.append(X3D.Index(indexV))
    return result

def VerticesToX3d(vertices = [], vName = X3D_DEFAULT_V_NAME, precision = 5):
    """gets X3D node for vertices

    vertices: if not empty, then a full vertex node is returned.
              if empty, then a node with the USE construction is returned
              and vName is used as the name.
    vName: name for the coordinates if vertices == [].
    """
    if vertices == []:
        return X3D.Node('Coordinate', USE = vName)
    elif vName == '':
        return X3D.Node('Coordinate', point = ConvertVec3ToX3d(vertices, precision))
    else:
        return X3D.Node(
                'Coordinate',
                DEF = vName,
                point = ConvertVec3ToX3d(vertices, precision)
            )

def edgesToX3d(
        edges,
        vertices = [],
        vName = X3D_DEFAULT_V_NAME,
        precision = 5
    ):
    """returns the X3D shapes for the edges (which are black)

    edges: the edges array
    vertices: if not empty, then the edges refer to these vertices.
              if empty, then the USE construction is used and the vName
              should refer to the vertices.
    vName: name for the coordinates.
           If vertices is empty then the USE construction is use with
           vName as reference.
           If vertices is not empty, then the DEF construction is used
           with vName as reference name.
    """
    return X3D.Node('Shape',
        appearance = X3D.Node('Appearance',
            material = X3D.Node('Material',
                diffuseColor = X3D.FloatVec([0, 0, 0], 1)
            )
        ),
        geometry = X3D.Node('IndexedLineSet',
            coord = VerticesToX3d(vertices, vName),
            coordIndex = ConvertIndicesToX3d(edges),
        )
    )

def cylinderEdgeToX3d(
        v0, v1,
        radius = 0.1,
        precision = 5
    ):
    vz = Geom3D.vec(0, 1, 0)
    dv = v1 - v0
    l = dv.length()
    if l == 0:
        print 'warning, edge length 0'
        return
    angle = math.acos((dv*vz)/l)
    axis = vz.cross(dv)
    return X3D.Node('Group',
            children = [
                X3D.Node('Transform',
                    translation = X3D.FloatVec((v1+v0)/2, precision),
                    rotation = X3D.FloatVec(
                        [axis[0], axis[1], axis[2], angle],
                        precision
                    ),
                    children = [
                        X3D.Node('Shape',
                            appearance = X3D.Node('Appearance',
                                material = X3D.Node('Material',
                                    diffuseColor = X3D.FloatVec([0, 0, 0], 1)
                                )
                            ),
                            geometry = X3D.Node('Cylinder',
                                radius = radius,
                                height = dv.length(),
                                bottom = False,
                                top = False
                            )
                        )
                    ]
                ),
                X3D.Node('Transform',
                    translation = X3D.FloatVec(v0, precision),
                    children = [ X3D.Node('Sphere', radius = radius) ]
                ),
                X3D.Node('Transform',
                    translation = X3D.FloatVec(v1, precision),
                    children = [ X3D.Node('Sphere', radius = radius) ]
                ),
            ]
        )


# TODO cylinderEdgesToX3d shoudl accept a flat array...
def cylinderEdgesToX3d(
        edges,
        vertices,
        radius = 0.1,
        precision = 5
    ):
    """returns the X3D shapes for the edges (which are black)

    edges: the edges array
    vertices: if not empty, then the edges refer to these vertices.
              if empty, then the USE construction is used and the vName
              should refer to the vertices.
    vName: name for the coordinates.
           If vertices is empty then the USE construction is use with
           vName as reference.
           If vertices is not empty, then the DEF construction is used
           with vName as reference name.
    """
    Es = []
    for e in edges:
        l = len(e)
        for i in range(l):
            Es.append(
                cylinderEdgeToX3d(
                    vertices[e[i]],
                    vertices[e[(i+1) % l]],
                    radius = radius,
                    precision = precision
                )
            )
    return X3D.Node('Group', children = Es)

def facesToX3d(
        faces,
        color,
        vertices = [],
        vName = X3D_DEFAULT_V_NAME,
        precision = 5
    ):
    """returns the X3D shapes for the faces (all having the same colour)

    faces: the faces array
    color: the rbg color used for these faces.
    vertices: if not empty, then the faces refer to these vertices.
              if empty, then the USE construction is used and the vName
              should refer to the vertices.
    vName: name for the coordinates.
           If vertices is empty then the USE construction is use with
           vName as reference.
           If vertices is not empty, then the DEF construction is used
           with vName as reference name.
    """
    return X3D.Node('Shape',
        appearance = X3D.Node('Appearance',
            material = X3D.Node('Material',
                diffuseColor = X3D.FloatVec(color, precision)
            )
        ),
        geometry = X3D.Node('IndexedFaceSet',
            coord = VerticesToX3d(vertices, vName),
            coordIndex = ConvertIndicesToX3d(faces),
            normalPerVertex = False,
            ccw             = False,
            solid           = False,
            creaseAngle     = 0.5
        )
    )

def getVUsageIn1D(Vs, Es, vUsage = None):
    if vUsage == None:
        vUsage = [0 for v in Vs]
    for vIndex in Es:
        vUsage[vIndex] = vUsage[vIndex] + 1
    return vUsage

def getVUsageIn2D(Vs, Fs, vUsage = None):
    if vUsage == None:
        vUsage = [0 for v in Vs]
    for f in Fs:
        for vIndex in f:
            vUsage[vIndex] = vUsage[vIndex] + 1
    return vUsage

def cleanUpVsFs(Vs, Fs):
    """cleanup Vs and update Fs by removing unused vertices.

    Note that the arrays themselves are updated. If this is not wanted, send in
    copies.
    It returns an array with tuples expressing which vertices are deleted. This
    array can be used as input to filterEs
    """
    # The clean up is done as follows: 
    # first construct an array of unused vertex indices 
    # remove all unused indices from Vs and subtract the approproate amount
    # from the indices in Fs that are bigger 
    # vUsage contains for each vertex a tuple that expresses:
    # - how ofter the vertex is used:
    # After the unused vertices are deleted, vReoved will contain:
    # - how many vertices that come before this (vertex) index are deleted.
    #
    #print 'cleanUpVsFs(Vs, Fs):'
    vUsage = getVUsageIn2D(Vs, Fs)
    vRemoved = [0 for x in vUsage]
    notUsed = 0 # counts the amount of vertices that are not used until vertex i
    for i in range(len(vUsage)):
        # If the vertex is not used
        if vUsage[i - notUsed] == 0:
            del Vs[i - notUsed]
            del vUsage[i - notUsed]
            #print i, ', new Vs:', Vs
            notUsed += 1
        # change the value of vUsage to the amount of vertices that are (not
        # used and from now on) deleted until vertex i
        vRemoved[i] = notUsed
    for f in Fs:
        for faceIndex in range(len(f)):
            f[faceIndex] = f[faceIndex] - vRemoved[f[faceIndex]]
    return vUsage

def cleanUp(Vs, Fs):
    """cleanup Vs and update Fs by removing unused vertices.

    Note that the arrays themselves are updated. If this is not wanted, send in
    copies.
    It returns an array with tuples expressing which vertices are deleted. This
    array can be used as input to filterEs
    """
    # The clean up is done as follows: 
    # first construct an array of unused vertex indices 
    # remove all unused indices from Vs and subtract the approproate amount
    # from the indices  in Fs that are bigger 
    # isUsed contains for each vertex a tuple that expresses:
    # 1. whether the vertex is used:
    # 2. how many vertices before this vertex are deleted.
    #
    # tested on
    # a = range(10)
    # b = [[0, 1, 4], [4, 1, 8]]
    #print 'cleanUp(Vs, Fs):'
    isUsed = [[False, 0] for i in range(len(Vs))]
    for f in Fs:
        for i in f:
            isUsed[i][0] = True
    notUsed = 0
    #print 'not used:'
    for i in range(len(isUsed)):
        vData = isUsed[i]
        vData[1] = notUsed
        if vData[0] == False:
            del Vs[i - notUsed]
            #print i, ', new Vs:', Vs
            notUsed += 1
    #print 'new index mapping:'
    #for i in range(len(isUsed)):
    #    print i, ' ->', i, '-', isUsed[i][1], '=', i - isUsed[i][1]
    #print notUsed, 'vertices not used'
    for f in Fs:
        for i in range(len(f)):
            f[i] = f[i] - isUsed[f[i]][1]
    return isUsed

def filterIsUsed(isUsed, flatArray):
    for i in range(len(flatArray)):
        flatArray[i] = flatArray[i] - isUsed[flatArray[i]][1]
