#!/usr/bin/env python
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

import math

from orbitit import Geom3D, geomtypes, glue, PS, rgb

from OpenGL.GLU import *
from OpenGL.GL import *

class Axis:
    X  = 1
    Y  = 1 << 1
    Z  = 1 << 2
    W  = 1 << 3

class Plane:
    XY = Axis.X | Axis.Y
    XZ = Axis.X | Axis.Z
    XW = Axis.X | Axis.W
    YZ = Axis.Y | Axis.Z
    YW = Axis.Y | Axis.W
    ZW = Axis.Z | Axis.W

class SimpleShape:
    dbgPrn = False
    dbgTrace = False
    className = "Geom4D.SimpleShape"
    def __init__(this, Vs, Cs, Es = [], Ns = [], colors = ([], []), name = "4DSimpleShape"):
        """
        Cs: and array of cells, consisting of an array of Fs.
        """
        if this.dbgTrace:
            print('%s.SimpleShape.__init__(%s,..):' % (this.__class__name))
        this.dimension = 4
        this.generateNormals = False
        this.v = Geom3D.Fields()
        this.e = Geom3D.Fields()
        this.f = Geom3D.Fields()
        this.c = Geom3D.Fields()
        # SETTINGS similar to Geom3D.SimpleShape:
        #print 'SimpleShape.Fs', Fs
        this.name = name
        if colors[0] == []:
            colors = ([rgb.gray95[:]], [])
        # if this.mapToSingeShape = False each cell is mapped to one 3D shape
        # and the edges are mapped to one shape as well. The disadvantage is
        # that for each shape glVertexPointer is set, while if
        # this.mapToSingeShape = True is set to True one vertex array is used.
        this.mapToSingeShape = True
        # if useTransparency = False opaque colours are used, even if they
        # specifically set to transparent colours.
        this.useTransparency(True)
        this.setVertexProperties(Vs = Vs, Ns = Ns, radius = -1., color = [1. , 1. , .8 ])
        this.setFaceProperties(
            colors = colors, drawFaces = True
        )
        this.glInitialised = False
        # SETTINGS 4D specific:
        this.setCellProperties(
            Cs = Cs, colors = colors, drawCells = False, scale = 1.0
        )
        # For initialisation setCellProperties needs to be called before
        # setEdgeProperties, since the latter will check the scale value
        this.setEdgeProperties(
            Es = Es, radius = -1., color = [0.1, 0.1, 0.1],
            drawEdges = True, showUnscaled = True
        )
        this.setProjectionProperties(11.0, 10.0)
        # expresses whether the 4D coordinates need to be updated:
        this.rot4 = None
        this.projectedTo3D = False
        if this.dbgPrn:
            print('%s.__init__(%s,..)' % (this.__class__, this.name))
            print('this.colorData:')
            for i in range(len(this.colorData[0])):
                print(('%d.' % i), this.colorData[0][i])
            if len(this.colorData[0]) > 1:
                assert this.colorData[0][1] != [0]
            print(this.colorData[1])

    def setVertexProperties(this, dictPar = None, **kwargs):
        """
        Set the vertices and how/whether vertices are drawn in OpenGL.

        Accepted are the optional (keyword) parameters:
        - Vs,
        - radius,
        - color.
        - Ns.
        Either these parameters are specified as part of kwargs or as key value
        pairs in the dictionary dictPar.
        If they are not specified (or equal to None) they are not changed.
        See getVertexProperties for the explanation of the keywords.
        The output of getVertexProperties can be used as the dictPar parameter.
        This can be used to copy settings from one shape to another.
        If dictPar is used and kwargs, then only the dictPar will be used.
        """
        if this.dbgTrace:
            print('%s.setVertexProperties(%s,..):' % (this.__class__, this.name))
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Vs' in dict and dict['Vs'] != None:
                this.Vs  = [ geomtypes.Vec4(v) for v in dict['Vs'] ]
            if 'Ns' in dict and dict['Ns'] != None:
                this.Ns  = [ geomtypes.Vec4(n) for n in dict['Ns'] ]
                #assert len(this.Ns) == len(this.Vs)
            if 'radius' in dict and dict['radius'] != None:
                this.v.radius = dict['radius']
            if 'color' in dict and dict['color'] != None:
                this.v.col = dict['color']
            this.projectedTo3D = False

    def getVertexProperties(this):
        """
        Return the current vertex properties as can be set by setVertexProperties.

        Returned is a dictionary with the keywords Vs, radius, color.
        Vs: an array of vertices.
        radius: If > 0.0 draw vertices as spheres with the specified colour. If
                no spheres are required (for preformance reasons) set the radius
                to a value <= 0.0.
        color: optianl array with 3 rgb values between 0 and 1.
        Ns: an array of normals (per vertex) This value might be None if the
            value is not set. If the value is set it is used by glDraw
        """
        if this.dbgTrace:
            print('%s.getVertexProperties(%s,..):' % (this.__class__, this.name))
        return {
            'Vs': this.Vs,
            'radius': this.v.radius,
            'color': this.v.col,
            'Ns': this.Ns
        }


    def setEdgeProperties(this, dictPar = None, **kwargs):
        """
        Specify the edges and set how they are drawn in OpenGL.

        Accepted are the optional (keyword) parameters:
          - Es,
          - radius,
          - color,
          - drawEdges.
        Either these parameters are specified as part of kwargs or as key value
        pairs in the dictionary dictPar.
        If they are not specified (or equel to None) they are not changed.
        See getEdgeProperties for the explanation of the keywords.
        The output of getEdgeProperties can be used as the dictPar parameter.
        This can be used drawFacesto copy settings from one shape to another.
        If dictPar is used and kwargs, then only the dictPar will be used.
        """
        if this.dbgTrace:
            print('%s.setEdgeProperties(%s,..):' % (this.__class__, this.name))
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Es' in dict and dict['Es'] != None:
                this.Es = dict['Es']
                this.projectedTo3D = False
            if 'radius' in dict and dict['radius'] != None:
                this.e.radius = dict['radius']
                this.projectedTo3D = False
            if 'color' in dict and dict['color'] != None:
                this.e.col = dict['color']
                this.projectedTo3D = False
            if 'drawEdges' in dict and dict['drawEdges'] != None:
                try:
                    currentSetting = this.e.draw
                except AttributeError:
                    currentSetting = None
                if currentSetting != dict['drawEdges']:
                    this.projectedTo3D = this.projectedTo3D and not (
                            # if all the below are true, then the edges need
                            # extra Vs, which means we need to reproject.
                            this.c.scale < 1.0
                            and
                            # .. and if the CURRENT settings is show unscaled
                            # (Though changes in this setting might mean that
                            # new projection was not needed)
                            this.e.showUnscaled
                        )
                    if this.projectedTo3D:
                        # Try is needed,
                        # not for the first time, since then this.projectedTo3D
                        # will be False
                        # but because of the this.mapToSingeShape setting.
                        try:
                            this.cell.setEdgeProperties(drawEdges = dict['drawEdges'])
                        except AttributeError:
                            pass
                this.e.draw = dict['drawEdges']
            if 'showUnscaled' in dict and dict['showUnscaled'] != None:
                this.projectedTo3D = this.projectedTo3D and not (
                        # if all the below are true, then a change in unscaled
                        # edges means a changes in Vs, since the extra edges
                        # have different Vs. This means we need to reproject.
                        this.e.draw
                        and
                        this.c.scale < 1.0
                        and
                        this.e.showUnscaled != dict['showUnscaled']
                    )
                this.e.showUnscaled = dict['showUnscaled']

    def getEdgeProperties(this):
        """
        Return the current edge properties as can be set by setEdgeProperties.

        Returned is a dictionary with the keywords Es, radius, color, drawEdges
        Es: a qD array of edges, where i and j in edge [ .., i, j,.. ] are
            indices in Vs.
        radius: If > 0.0 draw vertices as cylinders with the specified colour.
                If no cylinders are required (for preformance reasons) set the
                radius to a value <= 0.0 and the edges will be drawn as lines,
                using glPolygonOffset.
        color: array with 3 rgb values between 0 and 1.
        drawEdges: settings that expresses whether the edges should be drawn at
                   all.
        """
        if this.dbgTrace:
            print('%s.getEdgeProperties(%s,..):' % (this.__class__, this.name))
        return {'Es': this.Es,
                'radius': this.e.radius,
                'color': this.e.col,
                'drawEdges': this.e.draw
            }

    def recreateEdges(this):
        """
        Recreates the edges in the 3D object by using an adges for every side of
        a face, i.e. all faces will be surrounded by edges.

        Edges will be filtered so that shared edges between faces,
        i.e. edges that have the same vertex index, only appear once.
        The creation of edges is not optimised and can take a long time.
        """
        assert False, "Geom4D.SimpleShape.recreateEdges: TODO IMPLEMENT"

    def setFaceProperties(this, dictPar = None, **kwargs):
        """
        Define the properties of the faces.

        Accepted are the optional (keyword) parameters:
          - colors,
          - drawFaces.
        Either these parameters are specified as part of kwargs or as key value
        pairs in the dictionary dictPar.
        If they are not specified (or equal to None) they are not changed.
        See getFaceProperties for the explanation of the keywords.
        The output of getFaceProperties can be used as the dictPar parameter.
        This can be used to copy settings from one shape to another.
        If dictPar is used and kwargs, then only the dictPar will be used.
        """
        loc = '%s.setFaceProperties(%s,..): warning' % (this.__class__, this.name)
        if this.dbgTrace:
            print(loc)
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Fs' in dict and dict['Fs'] != None:
                print('%s: FS not supported, use Cs instead' % (loc))
            if 'colors' in dict and dict['colors'] != None:
                this.f.col = (dict['colors'])
            if 'drawFaces' in dict and dict['drawFaces'] != None:
                this.f.draw = dict['drawFaces']
            this.projectedTo3D = False

    def getFaceProperties(this):
        """
        Return the current face properties as can be set by setFaceProperties.

        Returned is a dictionary with the keywords colors, and drawFaces.
        colors: A tuple that defines the colour of the faces. The tuple consists
                of the following two items:
                0. colour definitions:
                   defines the colours used in the shape. It should contain at
                   least one colour definition. Each colour is a 3 dimensional
                   array containing the rgb value between 0 and 1.
                1. colour index per face:
                   An array of colour indices. It specifies for each face with
                   index 'i' in Fs which colour index from the parameter color
                   is used for this face. If empty then colors[0][0] shall be
                   used for each face.
                   It should have the same length as Fs (or the current faces if
                   Fs not specified) otherwise the parameter is ignored and the
                   face colors are set by some default algorithm.
        drawFaces: settings that expresses whether the faces should be drawn.
        NOTE: these settings can be overwritten by setCellProperties, see
        setCellProperties (or getCellProperties).
        """
        if this.dbgTrace:
            print('%s.getFaceColors(%s,..):' % (this.__class__, this.name))
        return {
                'colors': this.f.col,
                'drawFaces': this.f.draw
            }

    def setCellProperties(this, dictPar = None, **kwargs):
        """
        Define the properties of the cells.

        Accepted are the optional (keyword) parameters:
          - Cs
          - colors,
          - drawCells
          - scale: scale is the new scaling factor (i.e. it will not be
            multiplied by the current scaling factor)
        Either these parameters are specified as part of kwargs or as key value
        pairs in the dictionary dictPar.
        If they are not specified (or equal to None) they are not changed.
        See getCellProperties for the explanation of the keywords.
        The output of getCellProperties can be used as the dictPar parameter.
        This can be used to copy settings from one shape to another.
        If dictPar is used and kwargs, then onl    dbgPrn = False
    dbgTrace = False
    className = "SimpleShape"y the dictPar will be used.
        """
        if this.dbgTrace:
            print('%s.setCellProperties(%s,..):' % (this.__class__, this.name))
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'Cs' in dict and dict['Cs'] != None:
                this.Cs = dict['Cs']
            if 'colors' in dict and dict['colors'] != None:
                this.c.col = dict['colors']
            if 'drawCells' in dict and dict['drawCells'] != None:
                this.c.draw = dict['drawCells']
            if 'scale' in dict and dict['scale'] != None:
                this.c.scale = dict['scale']
            #print 'Cs:', this.Cs
            #print 'this.c.col[1]:', this.c.col[1]
            # TODO Is an assert valid here:
            #assert len(this.Cs) == len(this.c.col[1]), 'len(Cs) = %d != %d = (c.col[1])' % (len(this.Cs), len(this.c.col[1]))
            this.projectedTo3D = False

    def getCellProperties(this, Cs = None, colors = None):
        """
        Return the current face properties as can be set by setCellProperties.

        Cs: optional array of cells. Each cell consists of an array of faces,
            that do not need to be triangular. It is a hierarchical array, ie it
            consists of sub-array, where each sub-array describes one face. Each
            n-sided face is desribed by n indices. Empty on default. Using
            triangular faces only gives a better performance.
            If Cs == None, then the previous specified value will be used.
        colors: A tuple that defines the colour of the faces. The tuple consists
                of the following two items:
                0. colour definitions:
                   defines the colours used in the shape. It should contain at
                   least one colour definition. Each colour is a 3 dimensional
                   array containing the rgb value between 0 and 1.
                1. colour index per face:
                   An array of colour indices. It specifies for each cell with
                   index 'i' in Cs which colour index from the parameter color
                   is used for this face. If empty then colors[0][0] shall be
                   used for each face.
                   It should have the same length as Cs (or the current cells if
                   Cs not specified) otherwise the parameter is ignored and the
                   cell colors are set by some default algorithm.
        drawCells: settings that expresses whether the cells should be drawn. If
                   cells are drawn, then the individual faces of the cell will
                   not be drawn. I.e. it overwrites the color settings in
                   setFaceProperties
        scale: scale the cell with the specified scaling factor around its
               gravitational centre. This factor is typically <= 1.
        """
        if this.dbgTrace:
            print('%s.getCellProperties(%s,..):' % (this.__class__, this.name))
        return {
                'Cs': this.Cs,
                'colors': this.c.col,
                'drawCells': this.c.draw,
                'scale': this.c.scale
            }

    def setProjectionProperties(this, wCameraDistance, w_prj_vol, dbg = False):
        """
        wCameraDistance: should be > 0. distance in w coordinate between the
                         camera (for which x, y, z, are 0) and the projection
                         volume>
        w_prj_vol: should be >= 0. w coordinate of the near volume. This is
                   the voume in which the object is projected.
        """
        #
        #                 |
        # wCameraDistance |
        #           |     |
        #           V     |           V
        #     wC <-----> wProjV
        #                 |
        #                 |
        #                 |
        #
        assert (w_prj_vol > 0)
        assert (wCameraDistance > 0)
        this.w_prj_vol = w_prj_vol
        this.wCamera = w_prj_vol + wCameraDistance
        this.wCameraDistance = wCameraDistance
        this.projectedTo3D = False

    def rotate(this, rotation, successive = False):
        """
        Rotate the polychoron by the specified rotation.

        rotation: a rotation of type geomtypes.Rot4.
        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """
        if not successive or this.rot4 == None: this.rot4 = rotation
        else: this.rot4 = rotation * this.rot4
        this.projectedTo3D = False

    def rotateInStdPlane(this, plane, angle, successive = False):
        """
        Rotate in a plane defined by 2 coordinate axes.

        plane: one of Plane.XY, Plane.XZ, Plane.XW, Plane.YZ,
               Plane.YW, Plane.ZW
        angle: the angle in radians in counter-clockwise direction, while the
               Plane.PQ has a horizontal axis P pointing to the right and a
               vertical axis Q pointing up.
        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """
        q0 = None
        if Axis.X & plane: q0 = Vec4([1, 0, 0, 0])
        if Axis.Y & plane:
            if q0 == None:
                q0 = Vec4([0, 1, 0, 0])
            else:
                q1 = Vec4([0, 1, 0, 0])
        if Axis.Z & plane:
            if q0 == None:
                q0 = Vec4([0, 0, 1, 0])
            else:
                q1 = Vec4([0, 0, 1, 0])
        if Axis.W & plane:
            q1 = Vec4([0, 0, 0, 1])
        r = geomtypes.Rot4(axialPlane = (q0, q1), angle = angle)
        if not successive or this.rot4 == None: this.rot4 = r
        else: this.rot4 = r * this.rot4
        this.projectedTo3D = False

    def projectVsTo3D(this, Vs4D):
        """
        returns an array of 3D vertices.
        """
        #print "projectTo3D_getVs"
        Vs3D = []
        for v in Vs4D:
            wV = v[3]
            #print "mapping v:", v
            if not Geom3D.eq(this.wCamera, wV):
                scale = this.wCameraDistance / (this.wCamera - wV)
                Vs3D.append([scale * v[0], scale * v[1], scale * v[2]])
            else:
                Vs3D.append([1e256, 1e256, 1e256])
        return Vs3D

    def applyTransform(this):
        """
        Apply current transformation to the current vertices and returns the
        result.

        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """

    def useTransparency(this, use):
        this.removeTransparency = not use
        this.updateTransparency = True

    def glInit(this):
        """
        Initialise OpenGL for specific shapes

        Enables a derivative to use some specific OpenGL settings needed for
        this shape. This function is called in glDraw for the first time glDraw
        is called.
        """
        if this.dbgTrace:
            print('%s.glInit(%s,..):' % (this.__class__, this.name))
        glEnableClientState(GL_VERTEX_ARRAY);
        glEnableClientState(GL_NORMAL_ARRAY)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)

        this.glInitialised = True

    def glDraw(this):
        if not this.glInitialised:
            this.glInit()
        if this.mapToSingeShape:
            this.glDrawSingleRemoveUnscaledEdges()
            this.cell.generateNormals = this.generateNormals
            this.cell.glDraw()
        else:
            this.glDrawSplit()
            for cell in this.cells:
                cell.generateNormals = this.generateNormals
                cell.glDraw()

    def glDrawSingleRemoveUnscaledEdges(this):
        isScaledDown = not Geom3D.eq(this.c.scale, 1.0, margin = 0.001)
        if not this.projectedTo3D:
            # print 'reprojecting...'
            try:
                del this.cell
            except AttributeError:
                pass
            Ns3D = []
            if this.rot4 != None:
                Vs4D = [this.rot4*v for v in this.Vs]
            # TODO fix Ns.. if needed..
            #    if this.Ns != []:cleanUp
            #        Ns4D = [this.rot4*n for n in this.Ns]
            else:
                Vs4D = [v for v in this.Vs]
            Vs3D = this.projectVsTo3D(Vs4D)
            #for i in range(0, len(this.Es), 2):
            #    v0 = Vs4D[this.Es[i]]
            #    v1 = Vs4D[this.Es[i+1]]
            #    print 'delta v:', v0 - v1
            #    print 'Edge [%d, %d]; len:' % (this.Es[i], this.Es[i+1]), (v1-v0).length()
            #if this.Ns != []:
            #    Ns3D = this.projectVsTo3D(Ns4D)
            # Now project all to one 3D shape. 1 3D shape is chosen, instean of
            # projecting each cell to one shape because of different reasons:
            #  - when drawing transparent faces all the opaqe fae should be
            #    drawn first.
            #  - if drawing the cells per shape, the glVertexPointer should be
            #    called for each cell. (Currently SimpleShape will not call this
            #    function unless the vertices have been changed...
            shapeVs = []
            shapeEs = []
            shapeFs = []
            shapeColIndices = []
            if this.c.draw:
                shapeCols = this.c.col[0]
            else:
                shapeCols = this.f.col[0]
            if this.removeTransparency:
                shapeCols = [ c[0:3] for c in shapeCols ]
            if this.e.draw and (not isScaledDown or this.e.showUnscaled):
                shapeVs = Vs3D
                shapeEs = this.Es
            # Add a shape with faces for each cell
            for i in range(len(this.Cs)):
                # use a copy, since we will filter (v indices will change):
                cellFs = [ f[:] for f in this.Cs[i]]
                if this.c.draw:
                    shapeColIndices.extend([this.c.col[1][i] for f in cellFs])
                else:
                    shapeColIndices.extend(this.f.col[1][i])
                # Now cleanup Vs3D
                # TODO
                # if this.e.draw and (not isScaledDown or this.e.showUnscaled):
                # Then shapeVs = Vs3D already, and the code below is all
                # unecessary.
                cellVs = Vs3D[:]
                nrUsed = glue.cleanUpVsFs(cellVs, cellFs)
                # Now attaching to current Vs, will change index:
                offset = len(shapeVs)
                cellFs = [[vIndex + offset for vIndex in f] for f in cellFs]
                # Now scale from gravitation centre:
                if isScaledDown:
                    g = geomtypes.Vec3([0, 0, 0])
                    sum = 0
                    for vIndex in range(len(cellVs)):
                        g = g + nrUsed[vIndex] * geomtypes.Vec3(cellVs[vIndex])
                        sum = sum + nrUsed[vIndex]
                    if sum != 0:
                        g = g / sum
                    #print this.name, 'g:', g
                    cellVs = [this.c.scale * (geomtypes.Vec3(v) - g) + g for v in cellVs]


                shapeVs.extend(cellVs)
                shapeFs.extend(cellFs)
                # for shapeColIndices.extend() see above
            this.cell = Geom3D.SimpleShape(
                    shapeVs, shapeFs, shapeEs, [], # Vs , Fs, Es, Ns
                    (shapeCols, shapeColIndices),
                    name = '%s_projection' % (this.name)
                )
            this.cell.setVertexProperties(radius = this.v.radius, color = this.v.col)
            this.cell.setEdgeProperties(radius = this.e.radius, color = this.e.col, drawEdges = this.e.draw)
            this.cell.setFaceProperties(drawFaces = this.f.draw)
            this.cell.glInitialised = True # done as first step in this func
            this.projectedTo3D = True
            this.updateTransparency = False
            if this.e.draw and isScaledDown:
                this.cell.recreateEdges()
                # Don't use, out of performance issues:
                # cellEs = this.cell.getEdgeProperties()['Es']
                # --------------------------
                # Bad performance during scaling:
                # cellEs = this.cell.getEdgeProperties()['Es']
                # this.cell.recreateEdges()
                # cellEs.extend(this.cell.getEdgeProperties()['Es'])
                # -------end bad perf---------
                cellEs = this.cell.Es
                if this.e.showUnscaled:
                    cellEs.extend(this.Es)
                this.cell.setEdgeProperties(Es = cellEs)
        if this.updateTransparency:
            cellCols = this.cell.getFaceProperties()['colors']
            if this.removeTransparency:
                shapeCols = [ c[0:3] for c in cellCols[0] ]
            else:
                if this.c.draw:
                    shapeCols = this.c.col[0]
                else:
                    shapeCols = this.f.col[0]
            cellCols = (shapeCols, cellCols[1])
            this.cell.setFaceProperties(colors = cellCols)
            this.updateTransparency = False

    def glDrawSplit(this):
        if not this.projectedTo3D:
            try:
                del this.cells
            except AttributeError:
                pass
            Ns3D = []
            if this.rot4 != None:
                Vs4D = [this.rot4*v for v in this.Vs]
            # TODO fix Ns.. if needed..
            #    if this.Ns != []:
            #        Ns4D = [this.rot4*n for n in this.Ns]
            else:
                Vs4D = [v for v in this.Vs]
            Vs3D = this.projectVsTo3D(Vs4D)
            #if this.Ns != []:
            #    Ns3D = this.projectVsTo3D(Ns4D)
            this.cells = []
            # Add a cell for just the edges:
            if this.e.draw:
                cell = Geom3D.SimpleShape(
                        Vs3D, [], this.Es, [], # Vs , Fs, Es, Ns
                        name = '%s_Es' % (this.name)
                    )
                cell.setVertexProperties(radius = this.v.radius, color = this.v.col)
                cell.setEdgeProperties(radius = this.e.radius, color = this.e.col, drawEdges = this.e.draw)
                cell.setFaceProperties(drawFaces = False)
                cell.glInitialised = True
                this.cells.append(cell)
            # Add a shape with faces for each cell
            for i in range(len(this.Cs)):
                if this.c.draw:
                    colors = (this.c.col[0][this.c.col[1][i]], [])
                else:
                    colors = (this.f.col[0], this.f.col[1][i])
                #print colors
                cell = Geom3D.SimpleShape(
                        Vs3D, this.Cs[i], [], [], # Vs , Fs, Es, Ns
                        colors,
                        name = '%s_%d' % (this.name, i)
                    )
                # The edges and vertices are drawn through a separate shape below.
                cell.setVertexProperties(radius = -1)
                cell.setEdgeProperties(drawEdges = False)
                cell.setFaceProperties(drawFace = this.f.draw)
                cell.scale(this.c.scale)
                cell.glInitialised = True
                this.cells.append(cell)
            this.projectedTo3D = True

    def toPsPiecesStr(this,
            faceIndices = [],
            scaling = 1,
            precision = 7,
            margin = 1.0e5*Geom3D.defaultFloatMargin,
            pageSize = PS.PageSizeA4
        ):
        if this.mapToSingeShape:
            return this.cell.toPsPiecesStr(faceIndices, scaling, precision, margin, pageSize)
        else:
            assert False, 'toPsPiecesStr not supported for mapping to split draw'

# Tests:
if __name__ == '__main__':
    import os

    wDir = 'tstThis'
    cwd = os.getcwd()

    if not os.path.isdir(wDir):
        os.mkdir(wDir, 0o775)
    os.chdir(wDir)

    NrOfErrorsOcurred = 0
    def printError(str):
        global NrOfErrorsOcurred
        print('***** ERROR while testing *****')
        print(' ', str)
        NrOfErrorsOcurred += 1

    v = vec(1, 1, 0, 0)
    w = vec(0, 3, 4, 0)
    z = 0.1 * w
    p = z.is_parallel(w)
    if not p:
        printError('in function is_parallel')
    t = w.make_orthogonal_to(v)
    #print 'check if [-3, 3, 8, 0] ==', w
    if not (
        Geom3D.eq(t.x, -3) and
        Geom3D.eq(t.y, 3) and
        Geom3D.eq(t.z, 8) and
        Geom3D.eq(t.w, 0)
    ):
        printError('in function make_orthogonal_to')
        print('  Expected (-3, 3, 8, 0), got', t)

    n = w.normalise()

    # TODO Move some of these tests to geomtypes, after cgtypes rm, any relevant?

    # check if n is still of type vec and not cgtypes.vec4 (which doesn't have
    # a is_parallel)
    if not n.is_parallel(w):
        printError('in function is_parallel after norm')

    def testOrthogonalVectors (R, margin = Geom3D.defaultFloatMargin):
        if not Geom3D.eq(R.e0 * R.e1, 0.0, margin):
            printError('in function _setOrthoMatrix: e0.e1 = ', R.e0*R.e1, '!= 0')
        if not Geom3D.eq(R.e0 * R.e2, 0.0, margin):
            printError('in function _setOrthoMatrix: e0.e2 = ', R.e0*R.e2, '!= 0')
        if not Geom3D.eq(R.e0 * R.e3, 0.0, margin):
            printError('in function _setOrthoMatrix: e0.e3 = ', R.e0*R.e3, '!= 0')
        if not Geom3D.eq(R.e1 * R.e2, 0.0, margin):
            printError('in function _setOrthoMatrix: e1.e2 = ', R.e1*R.e2, '!= 0')
        if not Geom3D.eq(R.e1 * R.e3, 0.0, margin):
            printError('in function _setOrthoMatrix: e1.e3 = ', R.e1*R.e3, '!= 0')
        if not Geom3D.eq(R.e2 * R.e3, 0.0, margin):
            printError('in function _setOrthoMatrix: e2.e3 = ', R.e2*R.e3, '!= 0')
        print('-----resulting matrix-----')
        print(R.getMatrix())
        print('--------------------------')

    r = Rotation(v, w, math.pi/4)
    r._setOrthoMatrix()
    testOrthogonalVectors(r, margin = 1.0e-16)

    r = Rotation(vec(0, 0, 1, 0), vec(0, 1, 0, 0), math.pi/4)
    r._setOrthoMatrix()
    testOrthogonalVectors(r, margin = 1.0e-16)

    # error in this one:
    #r = Rotation(vec(0, 1, 0, 0), vec(0, 0, 1, 0), math.pi/4)
    # ok:
    #r = Rotation(vec(1, 0, 0, 0), vec(0, 0, 1, 0), math.pi/4)
    # not ok:
    r = Rotation(vec(0, 0, 1, 0), vec(1, 0, 0, 0), math.pi/4)
    r._setOrthoMatrix()
    testOrthogonalVectors(r, margin = 1.0e-16)

    r = Rotation(vec(0, 0, 0, 1), vec(1, 0, 0, 0), math.pi/4)
    r._setOrthoMatrix()
    testOrthogonalVectors(r, margin = 1.0e-16)

    r = Rotation(vec(0, 0, 0, 1), vec(1, 0, 0, 0), math.pi/4, math.atan(0.75))
    r._setOrthoMatrix()
    testOrthogonalVectors(r, margin = 1.0e-16)

    # EOT
    if NrOfErrorsOcurred == 0:
        print('test OK')
    else:
        print('test failed with %d error(s)' % NrOfErrorsOcurred)
