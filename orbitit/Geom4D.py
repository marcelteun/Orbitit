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

import logging
import math

from orbitit import geom_3d, geomtypes, glue, PS, rgb

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
    className = "Geom4D.SimpleShape"
    def __init__(this, vs, Cs, es=[], ns=[], colors=([], []), name="4DSimpleShape"):
        """
        Cs: and array of cells, consisting of an array of fs.
        """
        this.dimension = 4
        this.generateNormals = False
        this.v = geom_3d.Fields()
        this.e = geom_3d.Fields()
        this.f = geom_3d.Fields()
        this.c = geom_3d.Fields()
        # SETTINGS similar to geom_3d.SimpleShape:
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
        this.vertex_props = {'vs': vs, 'ns': ns, 'radius': -1., 'color': [1. , 1. , .8]}
        this.set_face_props(
            colors = colors, drawFaces = True
        )
        this.gl_initialised = False
        # SETTINGS 4D specific:
        this.setCellProperties(
            Cs = Cs, colors = colors, drawCells = False, scale = 1.0
        )
        # For initialisation setCellProperties needs to be called before
        # set_edge_props, since the latter will check the scale value
        this.set_edge_props(
            es = es, radius = -1., color = [0.1, 0.1, 0.1],
            drawEdges = True, showUnscaled = True
        )
        this.setProjectionProperties(11.0, 10.0)
        # expresses whether the 4D coordinates need to be updated:
        this.rot4 = None
        this.projectedTo3D = False

    @property
    def vertex_props(self):
        """
        Return the current vertex properties

        Returned is a dictionary with the keywords vs, radius, color.
        vs: an array of vertices.
        radius: If > 0.0 draw vertices as spheres with the specified colour. If
                no spheres are required (for preformance reasons) set the radius
                to a value <= 0.0.
        color: optianl array with 3 rgb values between 0 and 1.
        ns: an array of normals (per vertex) This value might be None if the
            value is not set. If the value is set it is used by gl_draw
        """
        return {
            'vs': self.vs,
            'radius': self.v.radius,
            'color': self.v.col,
            'ns': self.ns
        }

    @vertex_props.setter
    def vertex_props(self, props):
        """
        Set the vertices and how/whether vertices are drawn in OpenGL.

        Accepted are the optional (keys) parameters:
        - vs,
        - radius,
        - color.
        - ns.
        See setter for the explanation of the keys.
        """
        if props:
            if 'vs' in props and props['vs'] != None:
                self.vs  = [ geomtypes.Vec4(v) for v in props['vs'] ]
            if 'ns' in props and props['ns'] != None:
                self.ns  = [ geomtypes.Vec4(n) for n in props['ns'] ]
                #assert len(self.ns) == len(self.vs)
            if 'radius' in props and props['radius'] != None:
                self.v.radius = props['radius']
            if 'color' in props and props['color'] != None:
                self.v.col = props['color']
            self.projectedTo3D = False

    def set_edge_props(this, dictPar = None, **kwargs):
        """
        Specify the edges and set how they are drawn in OpenGL.

        Accepted are the optional (keyword) parameters:
          - es,
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
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'es' in dict and dict['es'] != None:
                this.es = dict['es']
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
                            # extra vs, which means we need to reproject.
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
                            this.cell.set_edge_props(drawEdges = dict['drawEdges'])
                        except AttributeError:
                            pass
                this.e.draw = dict['drawEdges']
            if 'showUnscaled' in dict and dict['showUnscaled'] != None:
                this.projectedTo3D = this.projectedTo3D and not (
                        # if all the below are true, then a change in unscaled
                        # edges means a changes in vs, since the extra edges
                        # have different vs. This means we need to reproject.
                        this.e.draw
                        and
                        this.c.scale < 1.0
                        and
                        this.e.showUnscaled != dict['showUnscaled']
                    )
                this.e.showUnscaled = dict['showUnscaled']

    def getEdgeProperties(this):
        """
        Return the current edge properties as can be set by set_edge_props.

        Returned is a dictionary with the keywords es, radius, color, drawEdges
        es: a qD array of edges, where i and j in edge [ .., i, j,.. ] are
            indices in vs.
        radius: If > 0.0 draw vertices as cylinders with the specified colour.
                If no cylinders are required (for preformance reasons) set the
                radius to a value <= 0.0 and the edges will be drawn as lines,
                using glPolygonOffset.
        color: array with 3 rgb values between 0 and 1.
        drawEdges: settings that expresses whether the edges should be drawn at
                   all.
        """
        return {'es': this.es,
                'radius': this.e.radius,
                'color': this.e.col,
                'drawEdges': this.e.draw
            }

    def regen_edges(this):
        """
        Recreates the edges in the 3D object by using an adges for every side of
        a face, i.e. all faces will be surrounded by edges.

        Edges will be filtered so that shared edges between faces,
        i.e. edges that have the same vertex index, only appear once.
        The creation of edges is not optimised and can take a long time.
        """
        assert False, "Geom4D.SimpleShape.regen_edges: TODO IMPLEMENT"

    def set_face_props(this, dictPar = None, **kwargs):
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
        if dictPar != None or kwargs != {}:
            if dictPar != None:
                dict = dictPar
            else:
                dict = kwargs
            if 'fs' in dict and dict['fs'] != None:
                logging.info("FS not supported, use Cs instead")
            if 'colors' in dict and dict['colors'] != None:
                this.f.col = (dict['colors'])
            if 'drawFaces' in dict and dict['drawFaces'] != None:
                this.f.draw = dict['drawFaces']
            this.projectedTo3D = False

    def getFaceProperties(this):
        """
        Return the current face properties as can be set by set_face_props.

        Returned is a dictionary with the keywords colors, and drawFaces.
        colors: A tuple that defines the colour of the faces. The tuple consists
                of the following two items:
                0. colour definitions:
                   defines the colours used in the shape. It should contain at
                   least one colour definition. Each colour is a 3 dimensional
                   array containing the rgb value between 0 and 1.
                1. colour index per face:
                   An array of colour indices. It specifies for each face with
                   index 'i' in fs which colour index from the parameter color
                   is used for this face. If empty then colors[0][0] shall be
                   used for each face.
                   It should have the same length as fs (or the current faces if
                   fs not specified) otherwise the parameter is ignored and the
                   face colors are set by some default algorithm.
        drawFaces: settings that expresses whether the faces should be drawn.
        NOTE: these settings can be overwritten by setCellProperties, see
        setCellProperties (or getCellProperties).
        """
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
        If dictPar is used and kwargs, then only the dictPar will be used.
        """
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
                   set_face_props
        scale: scale the cell with the specified scaling factor around its
               gravitational centre. This factor is typically <= 1.
        """
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
        Vs3D = []
        for v in Vs4D:
            wV = v[3]
            if not geom_3d.eq(this.wCamera, wV):
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

    def gl_init(self):
        """
        Initialise OpenGL for specific shapes

        Enables a derivative to use some specific OpenGL settings needed for
        this shape. This function is called in gl_draw for the first time gl_draw
        is called.
        """
        glEnableClientState(GL_VERTEX_ARRAY);
        glEnableClientState(GL_NORMAL_ARRAY)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)

        self.gl_initialised = True

    def gl_draw(this):
        if not this.gl_initialised:
            this.gl_init()
        if this.mapToSingeShape:
            this.glDrawSingleRemoveUnscaledEdges()
            this.cell.generateNormals = this.generateNormals
            this.cell.gl_draw()
        else:
            this.glDrawSplit()
            for cell in this.cells:
                cell.generateNormals = this.generateNormals
                cell.gl_draw()

    def glDrawSingleRemoveUnscaledEdges(this):
        isScaledDown = not geom_3d.eq(this.c.scale, 1.0, margin = 0.001)
        if not this.projectedTo3D:
            try:
                del this.cell
            except AttributeError:
                pass
            Ns3D = []
            if this.rot4 != None:
                Vs4D = [this.rot4*v for v in this.vs]
            # TODO fix ns.. if needed..
            #    if this.ns != []:cleanUp
            #        Ns4D = [this.rot4*n for n in this.ns]
            else:
                Vs4D = [v for v in this.vs]
            Vs3D = this.projectVsTo3D(Vs4D)
            #for i in range(0, len(this.es), 2):
            #    v0 = Vs4D[this.es[i]]
            #    v1 = Vs4D[this.es[i+1]]
            #if this.ns != []:
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
                shapeEs = this.es
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
                # Now attaching to current vs, will change index:
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
                    cellVs = [this.c.scale * (geomtypes.Vec3(v) - g) + g for v in cellVs]


                shapeVs.extend(cellVs)
                shapeFs.extend(cellFs)
                # for shapeColIndices.extend() see above
            this.cell = geom_3d.SimpleShape(
                    shapeVs, shapeFs, shapeEs, [], # vs , fs, es, ns
                    (shapeCols, shapeColIndices),
                    name = '%s_projection' % (this.name)
                )
            this.cell.vertex_props = {'radius': this.v.radius, 'color': this.v.col}
            this.cell.set_edge_props(radius = this.e.radius, color = this.e.col, drawEdges = this.e.draw)
            this.cell.set_face_props(drawFaces = this.f.draw)
            this.cell.gl_initialised = True # done as first step in this func
            this.projectedTo3D = True
            this.updateTransparency = False
            if this.e.draw and isScaledDown:
                this.cell.regen_edges()
                # Don't use, out of performance issues:
                # cellEs = this.cell.getEdgeProperties()['es']
                # --------------------------
                # Bad performance during scaling:
                # cellEs = this.cell.getEdgeProperties()['es']
                # this.cell.regen_edges()
                # cellEs.extend(this.cell.getEdgeProperties()['es'])
                # -------end bad perf---------
                cellEs = this.cell.es
                if this.e.showUnscaled:
                    cellEs.extend(this.es)
                this.cell.set_edge_props(es = cellEs)
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
            this.cell.set_face_props(colors = cellCols)
            this.updateTransparency = False

    def glDrawSplit(this):
        if not this.projectedTo3D:
            try:
                del this.cells
            except AttributeError:
                pass
            Ns3D = []
            if this.rot4 != None:
                Vs4D = [this.rot4*v for v in this.vs]
            # TODO fix ns.. if needed..
            #    if this.ns != []:
            #        Ns4D = [this.rot4*n for n in this.ns]
            else:
                Vs4D = [v for v in this.vs]
            Vs3D = this.projectVsTo3D(Vs4D)
            #if this.ns != []:
            #    Ns3D = this.projectVsTo3D(Ns4D)
            this.cells = []
            # Add a cell for just the edges:
            if this.e.draw:
                cell = geom_3d.SimpleShape(
                        Vs3D, [], this.es, [], # vs , fs, es, ns
                        name = '%s_Es' % (this.name)
                    )
                cell.vertex_props = {'radius': this.v.radius, 'color': this.v.col}
                cell.set_edge_props(radius = this.e.radius, color = this.e.col, drawEdges = this.e.draw)
                cell.set_face_props(drawFaces = False)
                cell.gl_initialised = True
                this.cells.append(cell)
            # Add a shape with faces for each cell
            for i in range(len(this.Cs)):
                if this.c.draw:
                    colors = (this.c.col[0][this.c.col[1][i]], [])
                else:
                    colors = (this.f.col[0], this.f.col[1][i])
                cell = geom_3d.SimpleShape(
                        Vs3D, this.Cs[i], [], [], # vs , fs, es, ns
                        colors,
                        name = '%s_%d' % (this.name, i)
                    )
                # The edges and vertices are drawn through a separate shape below.
                cell.vertex_props = {'radius': -1}
                cell.set_edge_props(drawEdges = False)
                cell.set_face_props(drawFace = this.f.draw)
                cell.zoom(this.c.scale)
                cell.gl_initialised = True
                this.cells.append(cell)
            this.projectedTo3D = True

    def to_postscript(this,
            face_indices=[],
            scaling=1,
            precision=7,
            margin=1.0e5*geom_3d.default_float_margin,
            pageSize=PS.PageSizeA4,
        ):
        if this.mapToSingeShape:
            return this.cell.to_postscript(face_indices, scaling, precision, margin, pageSize)
        else:
            assert False, 'to_postscript not supported for mapping to split draw'
