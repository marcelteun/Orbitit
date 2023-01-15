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

from orbitit import geom_3d, geomtypes, glue, PS, rgb

from OpenGL import GL

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
    def __init__(self, vs, Cs, es=[], ns=[], colors=([], []), name="4DSimpleShape"):
        """
        Cs: and array of cells, consisting of an array of fs.
        """
        self.dimension = 4
        self.generate_normals = False
        self.v = geom_3d.Fields()
        self.e = geom_3d.Fields()
        self.f = geom_3d.Fields()
        self.c = geom_3d.Fields()
        # SETTINGS similar to geom_3d.SimpleShape:
        self.name = name
        if colors[0] == []:
            colors = ([rgb.gray95[:]], [])
        # if self.mapToSingeShape = False each cell is mapped to one 3D shape
        # and the edges are mapped to one shape as well. The disadvantage is
        # that for each shape glVertexPointer is set, while if
        # self.mapToSingeShape = True is set to True one vertex array is used.
        self.mapToSingeShape = True
        # if useTransparency = False opaque colours are used, even if they
        # specifically set to transparent colours.
        self.useTransparency(True)
        self.vertex_props = {'vs': vs, 'ns': ns, 'radius': -1., 'color': [1. , 1. , .8]}
        self.face_props = {'colors': colors, 'draw_faces': True}
        self.gl_initialised = False
        # SETTINGS 4D specific:
        self.setCellProperties(
            Cs = Cs, colors = colors, drawCells = False, scale = 1.0
        )
        # For initialisation setCellProperties needs to be called before
        # edge_props, since the latter will check the scale value
        self.edge_props = {
            'es': es,
            'radius': -1.,
            'color': [0.1, 0.1, 0.1],
            'draw_edges': True,
            'showUnscaled': True,
        }
        self.setProjectionProperties(11.0, 10.0)
        # expresses whether the 4D coordinates need to be updated:
        self.rot4 = None
        self.projectedTo3D = False

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

    @property
    def edge_props(self):
        """
        Return the current edge properties.

        Returned is a dictionary with the keywords es, radius, color, draw_edges
        es: a qD array of edges, where i and j in edge [ .., i, j,.. ] are
            indices in vs.
        radius: If > 0.0 draw vertices as cylinders with the specified colour.
                If no cylinders are required (for preformance reasons) set the
                radius to a value <= 0.0 and the edges will be drawn as lines,
                using glPolygonOffset.
        color: array with 3 rgb values between 0 and 1.
        draw_edges: settings that expresses whether the edges should be drawn at
                   all.
        """
        return {
            'es': self.es,
            'radius': self.e.radius,
            'color': self.e.col,
            'draw_edges': self.e.draw
        }

    @edge_props.setter
    def edge_props(self, props):
        """
        Specify the edges and set how they are drawn in OpenGL.

        Accepted are the optional (keyword) parameters:
          - es,
          - radius,
          - color,
          - draw_edges.
        Either these parameters are specified as part of kwargs or as key value
        pairs in the dictionary dictPar.
        If they are not specified (or equel to None) they are not changed.
        See setter for the explanation of the keys.
        """
        if props:
            if 'es' in props and props['es'] != None:
                self.es = props['es']
                self.projectedTo3D = False
            if 'radius' in props and props['radius'] != None:
                self.e.radius = props['radius']
                self.projectedTo3D = False
            if 'color' in props and props['color'] != None:
                self.e.col = props['color']
                self.projectedTo3D = False
            if 'draw_edges' in props and props['draw_edges'] != None:
                try:
                    currentSetting = self.e.draw
                except AttributeError:
                    currentSetting = None
                if currentSetting != props['draw_edges']:
                    self.projectedTo3D = self.projectedTo3D and not (
                            # if all the below are true, then the edges need
                            # extra vs, which means we need to reproject.
                            self.c.scale < 1.0
                            and
                            # .. and if the CURRENT settings is show unscaled
                            # (Though changes in this setting might mean that
                            # new projection was not needed)
                            self.e.showUnscaled
                        )
                    if self.projectedTo3D:
                        # Try is needed,
                        # not for the first time, since then self.projectedTo3D
                        # will be False
                        # but because of the self.mapToSingeShape setting.
                        try:
                            self.cell.edge_props = {'draw_edges': props['draw_edges']}
                        except AttributeError:
                            pass
                self.e.draw = props['draw_edges']
            if 'showUnscaled' in props and props['showUnscaled'] != None:
                self.projectedTo3D = self.projectedTo3D and not (
                        # if all the below are true, then a change in unscaled
                        # edges means a changes in vs, since the extra edges
                        # have different vs. This means we need to reproject.
                        self.e.draw
                        and
                        self.c.scale < 1.0
                        and
                        self.e.showUnscaled != props['showUnscaled']
                    )
                self.e.showUnscaled = props['showUnscaled']

    def regen_edges(self):
        """
        Recreates the edges in the 3D object by using an adges for every side of
        a face, i.e. all faces will be surrounded by edges.

        Edges will be filtered so that shared edges between faces,
        i.e. edges that have the same vertex index, only appear once.
        The creation of edges is not optimised and can take a long time.
        """
        assert False, "Geom4D.SimpleShape.regen_edges: TODO IMPLEMENT"

    @property
    def face_props(self):
        """
        Return the current face properties.

        Returned is a dictionary with the keywords colors, and draw_faces.
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
        draw_faces: settings that expresses whether the faces should be drawn.
        NOTE: these settings can be overwritten by setCellProperties, see
        setCellProperties (or getCellProperties).
        """
        return {
            'colors': self.f.col,
            'draw_faces': self.f.draw
        }

    @face_props.setter
    def face_props(self, props):
        """
        Define the properties of the faces.

        Accepted is a dictionary with the following keys:
          - colors,
          - draw_faces.
        See setter for more explanation of these.
        """
        if props:
            if 'colors' in props and props['colors'] != None:
                self.f.col = (props['colors'])
            if 'draw_faces' in props and props['draw_faces'] != None:
                self.f.draw = props['draw_faces']
            self.projectedTo3D = False

    def setCellProperties(self, dictPar = None, **kwargs):
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
                self.Cs = dict['Cs']
            if 'colors' in dict and dict['colors'] != None:
                self.c.col = dict['colors']
            if 'drawCells' in dict and dict['drawCells'] != None:
                self.c.draw = dict['drawCells']
            if 'scale' in dict and dict['scale'] != None:
                self.c.scale = dict['scale']
            self.projectedTo3D = False

    def getCellProperties(self, Cs = None, colors = None):
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
                   face_props
        scale: scale the cell with the specified scaling factor around its
               gravitational centre. This factor is typically <= 1.
        """
        return {
                'Cs': self.Cs,
                'colors': self.c.col,
                'drawCells': self.c.draw,
                'scale': self.c.scale
            }

    def setProjectionProperties(self, wCameraDistance, w_prj_vol, dbg = False):
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
        self.w_prj_vol = w_prj_vol
        self.wCamera = w_prj_vol + wCameraDistance
        self.wCameraDistance = wCameraDistance
        self.projectedTo3D = False

    def rotate(self, rotation, successive = False):
        """
        Rotate the polychoron by the specified rotation.

        rotation: a rotation of type geomtypes.Rot4.
        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """
        if not successive or self.rot4 == None: self.rot4 = rotation
        else: self.rot4 = rotation * self.rot4
        self.projectedTo3D = False

    def rotateInStdPlane(self, plane, angle, successive = False):
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
        if Axis.X & plane: q0 = geomtypes.Vec4([1, 0, 0, 0])
        if Axis.Y & plane:
            if q0 == None:
                q0 = geomtypes.Vec4([0, 1, 0, 0])
            else:
                q1 = geomtypes.Vec4([0, 1, 0, 0])
        if Axis.Z & plane:
            if q0 == None:
                q0 = geomtypes.Vec4([0, 0, 1, 0])
            else:
                q1 = geomtypes.Vec4([0, 0, 1, 0])
        if Axis.W & plane:
            q1 = geomtypes.Vec4([0, 0, 0, 1])
        r = geomtypes.Rot4(axialPlane = (q0, q1), angle = angle)
        if not successive or self.rot4 == None: self.rot4 = r
        else: self.rot4 = r * self.rot4
        self.projectedTo3D = False

    def projectVsTo3D(self, Vs4D):
        """
        returns an array of 3D vertices.
        """
        Vs3D = []
        for v in Vs4D:
            wV = v[3]
            if not geomtypes.FloatHandler.eq(self.wCamera, wV):
                scale = self.wCameraDistance / (self.wCamera - wV)
                Vs3D.append([scale * v[0], scale * v[1], scale * v[2]])
            else:
                Vs3D.append([1e256, 1e256, 1e256])
        return Vs3D

    def applyTransform(self):
        """
        Apply current transformation to the current vertices and returns the
        result.

        successive: specify if this is applied on any previous transform, i.e.
                    if this is not a new transforma.
        """

    def useTransparency(self, use):
        self.removeTransparency = not use
        self.updateTransparency = True

    def gl_init(self):
        """
        Initialise OpenGL for specific shapes

        Enables a derivative to use some specific OpenGL settings needed for
        this shape. This function is called in gl_draw for the first time gl_draw
        is called.
        """
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY);
        GL.glEnableClientState(GL.GL_NORMAL_ARRAY)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_NORMALIZE)
        GL.glDisable(GL.GL_CULL_FACE)

        self.gl_initialised = True

    def gl_draw(self):
        if not self.gl_initialised:
            self.gl_init()
        if self.mapToSingeShape:
            self.glDrawSingleRemoveUnscaledEdges()
            self.cell.generate_normals = self.generate_normals
            self.cell.gl_draw()
        else:
            self.glDrawSplit()
            for cell in self.cells:
                cell.generate_normals = self.generate_normals
                cell.gl_draw()

    def glDrawSingleRemoveUnscaledEdges(self):
        with geomtypes.FloatHandler(3) as fh:
            isScaledDown = not fh.eq(self.c.scale, 1.0)
        if not self.projectedTo3D:
            try:
                del self.cell
            except AttributeError:
                pass
            Ns3D = []
            if self.rot4 != None:
                Vs4D = [self.rot4*v for v in self.vs]
            # TODO fix ns.. if needed..
            #    if self.ns != []:cleanUp
            #        Ns4D = [self.rot4*n for n in self.ns]
            else:
                Vs4D = [v for v in self.vs]
            Vs3D = self.projectVsTo3D(Vs4D)
            #for i in range(0, len(self.es), 2):
            #    v0 = Vs4D[self.es[i]]
            #    v1 = Vs4D[self.es[i+1]]
            #if self.ns != []:
            #    Ns3D = self.projectVsTo3D(Ns4D)
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
            if self.c.draw:
                shapeCols = self.c.col[0]
            else:
                shapeCols = self.f.col[0]
            if self.removeTransparency:
                shapeCols = [ c[0:3] for c in shapeCols ]
            if self.e.draw and (not isScaledDown or self.e.showUnscaled):
                shapeVs = Vs3D
                shapeEs = self.es
            # Add a shape with faces for each cell
            for i in range(len(self.Cs)):
                # use a copy, since we will filter (v indices will change):
                cellFs = [ f[:] for f in self.Cs[i]]
                if self.c.draw:
                    shapeColIndices.extend([self.c.col[1][i] for f in cellFs])
                else:
                    shapeColIndices.extend(self.f.col[1][i])
                # Now cleanup Vs3D
                # TODO
                # if self.e.draw and (not isScaledDown or self.e.showUnscaled):
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
                    cellVs = [self.c.scale * (geomtypes.Vec3(v) - g) + g for v in cellVs]


                shapeVs.extend(cellVs)
                shapeFs.extend(cellFs)
                # for shapeColIndices.extend() see above
            self.cell = geom_3d.SimpleShape(
                    shapeVs, shapeFs, shapeEs, [], # vs , fs, es, ns
                    (shapeCols, shapeColIndices),
                    name = '%s_projection' % (self.name)
                )
            self.cell.vertex_props = {'radius': self.v.radius, 'color': self.v.col}
            self.cell.edge_props = {
                'radius': self.e.radius,
                'color': self.e.col,
                'draw_edges': self.e.draw,
            }
            self.cell.face_props = {'draw_faces': self.f.draw}
            self.cell.gl_initialised = True # done as first step in self func
            self.projectedTo3D = True
            self.updateTransparency = False
            if self.e.draw and isScaledDown:
                self.cell.regen_edges()
                # Don't use, out of performance issues:
                # cellEs = self.cell.edges_props['es']
                # --------------------------
                # Bad performance during scaling:
                # cellEs = self.cell.edges_props['es']
                # self.cell.regen_edges()
                # cellEs.extend(self.cell.edges_props['es'])
                # -------end bad perf---------
                cellEs = self.cell.es
                if self.e.showUnscaled:
                    cellEs.extend(self.es)
                self.cell.es = cellEs
        if self.updateTransparency:
            cellCols = self.cell.face_props['colors']
            if self.removeTransparency:
                shapeCols = [ c[0:3] for c in cellCols[0] ]
            else:
                if self.c.draw:
                    shapeCols = self.c.col[0]
                else:
                    shapeCols = self.f.col[0]
            cellCols = (shapeCols, cellCols[1])
            self.cell.face_props = {'colors': cellCols}
            self.updateTransparency = False

    def glDrawSplit(self):
        if not self.projectedTo3D:
            try:
                del self.cells
            except AttributeError:
                pass
            Ns3D = []
            if self.rot4 != None:
                Vs4D = [self.rot4*v for v in self.vs]
            # TODO fix ns.. if needed..
            #    if self.ns != []:
            #        Ns4D = [self.rot4*n for n in self.ns]
            else:
                Vs4D = [v for v in self.vs]
            Vs3D = self.projectVsTo3D(Vs4D)
            #if self.ns != []:
            #    Ns3D = self.projectVsTo3D(Ns4D)
            self.cells = []
            # Add a cell for just the edges:
            if self.e.draw:
                cell = geom_3d.SimpleShape(
                        Vs3D, [], self.es, [], # vs , fs, es, ns
                        name = '%s_Es' % (self.name)
                    )
                cell.vertex_props = {'radius': self.v.radius, 'color': self.v.col}
                cell.edge_props = {
                    'radius': self.e.radius,
                    'color': self.e.col,
                    'draw_edges': self.e.draw,
                }
                cell.face_props = {'draw_faces': False}
                cell.gl_initialised = True
                self.cells.append(cell)
            # Add a shape with faces for each cell
            for i in range(len(self.Cs)):
                if self.c.draw:
                    colors = (self.c.col[0][self.c.col[1][i]], [])
                else:
                    colors = (self.f.col[0], self.f.col[1][i])
                cell = geom_3d.SimpleShape(
                        Vs3D, self.Cs[i], [], [], # vs , fs, es, ns
                        colors,
                        name = '%s_%d' % (self.name, i)
                    )
                # The edges and vertices are drawn through a separate shape below.
                cell.vertex_props = {'radius': -1}
                cell.edge_props = {'draw_edges': False}
                cell.face_props = {'draw_faces': self.f.draw}
                cell.zoom(self.c.scale)
                cell.gl_initialised = True
                self.cells.append(cell)
            self.projectedTo3D = True

    def to_postscript(self,
            face_indices=[],
            scaling=1,
            precision=7,
            pageSize=PS.PageSizeA4,
        ):
        if self.mapToSingeShape:
            return self.cell.to_postscript(face_indices, scaling, precision, pageSize)
        else:
            assert False, 'to_postscript not supported for mapping to split draw'
