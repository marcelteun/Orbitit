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
#-------------------------------------------------------------------
#
# $Log: Scenes.py,v $
# Revision 1.5  2008/10/26 22:33:43  marcelteun
# added arcball navigation
#
# Revision 1.4  2008/10/08 19:18:21  marcelteun
# fixed regular heptagon in Scene_EqlHeptFromKite.py
#
# Revision 1.3  2008/10/04 21:13:29  marcelteun
# fix for undestroyed boxes in Ubuntu Hardy Heron
#
# Revision 1.2  2008/10/03 20:09:51  marcelteun
# Bridges2008 changes: window position
#
# Revision 1.1.1.1  2008/07/05 10:35:42  marcelteun
# Imported sources
#
# Revision 1.1  2008/06/18 05:31:54  teun
# Initial revision
#
#

import wx
import math
import Geom3D
from wx import glcanvas
from OpenGL.GLU import *
from OpenGL.GL import *
from cgkit import cgtypes

def getAxis2AxisRotation(a0, a1):
    # TODO: how to know which angle is taken (if you switch the axes, will you
    # still have to correct angle and axis?)
    vec3Type = type(cgtypes.vec3())
    altVec3Type = type(cgtypes.mat3()*cgtypes.vec3())
    assert (type(a0) == vec3Type or type(a0) == altVec3Type) and (type(a1) == vec3Type or type(a1) == altVec3Type)
    #assert (type(a0) == vec3Type) and (type(a1) == vec3Type)
    if Geom3D.Veq(a0, a1):
        # if both axis are in fact the same no roation is needed
        axis = cgtypes.vec3(0, 0, 0)
        angle = 0
    if Geom3D.Veq(a0, -a1):
        # if one axis should be rotated in its opposite axis, handle
        # separately, since the cross product will not work.
        # rotate pi around any vector that makes a straight angle with a0
        a2 = cgtypes.vec3([i+0.5 for i in a1])
        angle = math.pi
        axis = a2.cross(a0)
    else:
        a_0 = a0.normalize()
        a_1 = a1.normalize()
        n = a_0 * a_1
        # because of floats there might be some rounding problems:
        n = min(n, 1.0)
        n = max(n, -1.0)
        angle = math.acos(n)
        axis = a_0.cross(a_1)
    return {'axis': axis, 'angle': angle}

class Triangle:
    def __init__(this, v0, v1, v2):
        this.v = [
                cgtypes.vec3(v0[0], v0[1], v0[2]),
                cgtypes.vec3(v1[0], v1[1], v1[2]),
                cgtypes.vec3(v2[0], v2[1], v2[2])
            ]
        this.N = None

    def normal(this):
        if this.N == None:
            n = (this.v[1] - this.v[0]).cross(this.v[2] - this.v[0])
            this.N = [n[0], n[1], n[2]]
            return this.N
        else:
            return this.N

class P2PCylinder:
    def __init__(this, radius = 0.15, slices = 12, stacks = 1):
        this.quad = gluNewQuadric()
        this.radius = radius
        this.slices = slices
        this.stacks = stacks
	gluQuadricNormals(this.quad, GLU_SMOOTH)
	#gluQuadricTexture(this.quad, GL_TRUE)

    def draw(this, v0 = [0, 0, 0], v1 = [0, 0, 1]):
        e = [v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]]
        eLen = math.sqrt(e[0]*e[0] + e[1]*e[1] + e[2]*e[2])
        if eLen == 0: return

        #if this.slices < 3: this.slices = 10

        # Rotate such that the edge v0-v1 points in the positive z-direction,
        # Then translate the scene such that v0 ends up in the origin.
        # angle = acos( e.(0,0,1) / eLen) , with . the dot product
        #       = acos( e[2]/eLen)
        # axis = (0,0,1) x e , with x the cross product
        #      = [-e[1], e[0], 0]
        glPushMatrix();
        glTranslatef(v0[0], v0[1], v0[2]);
        glRotatef(math.acos(e[2]/eLen) * Geom3D.Rad2Deg, -e[1], e[0], 0.);
        gluCylinder(this.quad, this.radius, this.radius, eLen, this.slices, this.stacks)
        glPopMatrix();

class VSphere:
    def __init__(this, radius = 0.2, slices = 12, stacks = 12):
        this.quad = gluNewQuadric()
        this.radius = radius
        this.slices = slices
        this.stacks = stacks
	gluQuadricNormals(this.quad, GLU_SMOOTH)
	#gluQuadricTexture(this.quad, GL_TRUE)

    def draw(this, v = [0, 0, 0]):
        glPushMatrix();
        glTranslatef(v[0], v[1], v[2]);
        gluSphere(this.quad, this.radius, this.slices, this.stacks)
        glPopMatrix();

class Interactive3DCanvas(glcanvas.GLCanvas):
    dbgTrace = False
    def __init__(this, parent, size = None):
        # Ensure double buffered to prevent flashing on systems where double buffering is not default.
        if this.dbgTrace:
            print 'Interactive3DCanvas.__init__(this,..):'
        glcanvas.GLCanvas.__init__(this, parent, -1,
                size = size,
                attribList = [
                    wx.glcanvas.WX_GL_RGBA,
                    wx.glcanvas.WX_GL_DOUBLEBUFFER,
                    wx.glcanvas.WX_GL_STENCIL_SIZE, 8
                ]
            )
        this.cyl = P2PCylinder(radius = 0.05)
        this.sphere = VSphere(radius = 0.1)
        this.init = False
        # initial mouse position
        this.xOrg = this.x = 0
        this.yOrg = this.y = 0
        this.zBac = this.z = 0
        this.mouseLeftIn   = False
        this.mouseRightIn  = False
        this.zScaleFactor  = 1.0/100
        this.currentScale  = 1.0
        this.rScale = 0.8
        this.modelRepos = Geom3D.E
        this.movingRepos = Geom3D.E
        this.xAxis = cgtypes.vec3([1.0, 0.0, 0.0])
        this.yAxis = cgtypes.vec3([0.0, 1.0, 0.0])
        this.angleAroundYaxis = 0
        this.angleAroundXaxis = 0
        this.bgCol = [0.097656, 0.097656, 0.437500] # midnightBlue 
        this.size = size
        this.Bind(wx.EVT_ERASE_BACKGROUND, this.onEraseBackground)
        this.Bind(wx.EVT_SIZE, this.onSize)
        this.Bind(wx.EVT_PAINT, this.OnPaint)
        this.Bind(wx.EVT_LEFT_DOWN, this.onRotateStart)
        this.Bind(wx.EVT_LEFT_UP, this.onRotateStop)
        this.Bind(wx.EVT_RIGHT_DOWN, this.onZoomStart)
        this.Bind(wx.EVT_RIGHT_UP, this.onZoomStop)
        this.Bind(wx.EVT_MOTION, this.onMouseMotion)
        this.cameraDistance = 5.0

    def setCameraPosition(this, distance):
        """
        Set the camera distance

        distance: camera distance, usually a positive nr. Note that the camera
                  is somewhere along the z-axis
        """
        if this.dbgTrace:
            print 'Interactive3DCanvas.setCameraDistance(this,..):'
        this.cameraDistance = distance

    def initGl(this):
        #if this.dbgTrace:
        if True:
            print 'Interactive3DCanvas.initGl(this,..):'
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45., 1.0, 1., 300.)

        glTranslatef(0.0, 0.0, -this.cameraDistance)
        glMatrixMode(GL_MODELVIEW)

    def onEraseBackground(this, event):
        pass # Do nothing, to avoid flashing on MSW.

    def setArcBallRadius(this, R = 0.8):
        if this.dbgTrace:
            print 'Interactive3DCanvas.setArcBallRadius(this,..):'
        this.rScale = R

    def onSize(this, event):
        if this.dbgTrace:
            print 'Interactive3DCanvas.onSize(this,..):'
        size = this.GetClientSize()
        wOrH = min(size.width, size.height)
        size.height = size.width = wOrH
        this.SetClientSize(size)
        this.size = size
        if this.GetContext():
            this.SetCurrent()
            glViewport(0, 0, this.size.width, this.size.height)
            #glViewport(0, 0, wOrH, wOrH)
        event.Skip()

    def OnPaint(this, event):
        if this.dbgTrace:
            print 'Interactive3DCanvas.OnPaint(this,..):'
        def xy2SphereV(x, y, w, h, R2):
            x, y = x - width/2, height/2 - y
            l2 = x * x + y * y
            if l2 < R2:
                spherePos = cgtypes.vec3(x, y, math.sqrt(R2 - l2))
            elif l2 > R2:
                scale = math.sqrt(R2/l2)
                spherePos = cgtypes.vec3(scale*x, scale*y, 0)
            else: # probably never happens (floats)
                spherePos = cgtypes.vec3(x, y, 0)
            return spherePos
        dc = wx.PaintDC(this)
        this.SetCurrent()
        if not this.init:
            this.initGl()
            this.init = True
            this.Moriginal = glGetDoublev(GL_MODELVIEW_MATRIX)
        glPushMatrix()
        this.onPaint()
        glPopMatrix()

        if this.xOrg != 0 or this.yOrg != 0:
            viewPort = glGetIntegerv(GL_VIEWPORT)
            height = viewPort[3] - viewPort[1]
            width  = viewPort[2] - viewPort[0]
            D = min(width, height)
            R2 = float(D*D)/4
            R2 = this.rScale*this.rScale*R2
            newSpherePos = xy2SphereV(this.x,    this.y,    width, height, R2)
            orgSphere = xy2SphereV(this.xOrg, this.yOrg, width, height, R2)
            rotAA = getAxis2AxisRotation(orgSphere, newSpherePos)
            angle = rotAA['angle']
            axis = rotAA['axis']
            this.movingRepos = cgtypes.quat(angle, axis) * this.modelRepos
            glLoadMatrixd(this.Moriginal)
            glScalef(this.currentScale, this.currentScale, this.currentScale)
            angleAxis = this.movingRepos.toAngleAxis()
            angle = Geom3D.Rad2Deg*angleAxis[0]
            axis = angleAxis[1]
            #print 'rotate', angle, axis
            glRotatef(angle, axis[0], axis[1], axis[2])
            
        if this.z != this.zBac:
            dZ = this.z - this.zBac
            # map [min, max] onto [0, 2]
            # dZ' = (2/(max-min)) dZ + 1
            #pStr = '%f ->' % dZ
            dZ = dZ*this.zScaleFactor + 1.0
            this.currentScale = dZ * this.currentScale
            #print '%s %f' % (pStr, dZ)
            glScalef(dZ, dZ, dZ)

        glFlush()
        this.SwapBuffers()

    def resetOrientation(this):
        if this.dbgTrace:
            print 'Interactive3DCanvas.resetOrientation(this,..):'
        try: # this.Moriginal might not exist at an early stage (e.g. on Windows)...
            glLoadMatrixd(this.Moriginal)
        except AttributeError:
            pass
        this.modelRepos = Geom3D.E
        this.movingRepos = Geom3D.E
        this.currentScale = 1.0
        this.paint()

    def paint(this):
        if this.dbgTrace:
            print 'Interactive3DCanvas.paint(this,..):'
        this.Refresh(False)

    def onRotateStart(this, event):
        this.CaptureMouse()
        this.mouseLeftIn = True
        this.xOrg, this.yOrg = this.x, this.y = event.GetPosition()

    def onRotateStop(this, event):
        # we need to check this, because a mouse click in a window A on top of
        # this window can cause window A to be closed and the release button
        # event is captured here, while the was no capture here.
        if this.dbgTrace:
            print 'Interactive3DCanvas.onRotateStop(this,..):'
        if this.mouseLeftIn:
            this.mouseLeftIn = False
            this.ReleaseMouse()
            this.modelRepos = this.movingRepos
        this.xOrg, this.yOrg = this.x, this.y = (0, 0)

    def onZoomStart(this, event):
        if this.dbgTrace:
            print 'Interactive3DCanvas.onZoomStart(this,..):'
        this.CaptureMouse()
        this.mouseRightIn = True
        this.z = this.zBac = event.GetPosition()[1]

    def onZoomStop(this, event):
        # we need to check this, because a mouse click in a window A on top of
        # this window can cause window A to be closed and the release button
        # event is captured here, while the was no capture here.
        if this.dbgTrace:
            print 'Interactive3DCanvas.onZoomStop(this,..):'
        if this.mouseRightIn:
            this.mouseRightIn = False
            this.ReleaseMouse()
        this.zBac = this.z = 0.0

    def onMouseMotion(this, event):
        #if this.dbgTrace:
        #    print 'Interactive3DCanvas.onMouseMotion(this,..):'
        if event.Dragging():
            if event.LeftIsDown():
                this.x, this.y = event.GetPosition()
            if event.RightIsDown():
                this.zBac = this.z
                this.z = event.GetPosition()[1]
            this.Refresh(False)

class Scene:
    """
    The Scene class helps implementing a scene.

    A scene class should accept at least 2 parameters:
        1. The frame of the control window.
        2. The panel of the control window.
    This allows the scene to add controls to the control window / panel.
    The ctrlFrame class is a Frame that implements a function 
      - sceneClosed, which deletes the references to this scene
      - setDefaultSize, that sets the size of the control frame
    A scene is supposed to 
      - create a sizer this.ctrlSizer during object creation. This is done by
        calling the function this.createControlsSizer(), which takes one
        parameter, which is the ctrlPanel of the control window.
      - implement a function close, which should release all GUIs in
        rmControlsSizer. The close function calls the function
        this.rmControlsSizer().
    Optionally a scene can implement
      - a function setArcBallRadius to set the relative radius of the sphere of
        the arc ball navigation. It shall except one radius parameter.
    During init the Scene creates a canvas frame which is supposed to hold the
    3D object. The window frame is created here in the Scene class, but the
    contents is supposed to be created in the class with the name SceneCanvas,
    which should be a descendent of Scenes.Interactive3DCanvas.
    To summarise, the descendent of this class should:
      - implement this.createControlsSizer(ctrlPanel)
      - implement this.rmControlsSizer()
      - call the init of this class with a class SceneCanvas, which is a
        descendent of Scenes.Interactive3DCanvas.
    """
    def __init__(this, ctrlFrame, ctrlPanel, SceneCanvas, *args, **kwargs):
        this.ctrlFrame = ctrlFrame
        this.ctrlPanel = ctrlPanel
        this.canvasFrame = wx.Frame(None, -1, *args, **kwargs)
        this.canvasFrame.Bind(wx.EVT_CLOSE, this.onCloseCanvas)
        this.canvasFrame.Bind(wx.EVT_SIZE, this.onSize)
        this.statusBar = this.canvasFrame.CreateStatusBar()
        this.canvas = SceneCanvas(this.canvasFrame)
        this.canvasFrame.Show(True)
        this.createControlsSizer(this.ctrlPanel)

    def setArcBallRadius(this, R = 0.8):
        this.canvas.setArcBallRadius(R = R)

    def onSize(this, event):
        this.canvas.onSize(event)
        print 'Canvas window size:', this.canvasFrame.GetClientSize()

    def onCloseCanvas(this, event):
        print 'onCloseCanvas'
        this.close()
        this.ctrlFrame.sceneClosed()

    def close(this):
        #try:
            this.rmControlsSizer()
            this.canvas.Destroy()
            this.canvasFrame.Destroy()
        #except wx._core.PyDeadObjectError: pass

def AllMem(aClass):
    try: mro = list(aClass.__mro__)
    except AttributeError:
        def getMro(aClass, rec):
            mro = [aClass]
            for base in aClass.__bases__: mro.extend(rec(base, rec))
            return mro
        mro = getMro(aClass, getMro)
    mro.reverse()
    members = {}
    for someClass in mro: members.update(vars(someClass))
    return members

class Symmetry:
    def __init__(this):
        this.nrOfSyms = 0
        def set(incr = 1):
            nr = this.nrOfSyms
            this.nrOfSyms += incr
            return nr
        # identity:
        this.E = set()
        # tetrahedral:
        this.A4 = set()
        this.A4xI = set()
        this.S4A4 = set()
        # octahedral:
        this.S4 = set()
        this.S4xI = set()
        # icosahedral:
        this.A5 = set()
        this.A5xI = set()
        # ExI
        this.ExI = set()
        # special usage, for which =~ C2C1 is not used:
        this.C2C1 = set()
        this.D1C1 = set()
        # cylclic and dihedral
        this.maxN = 1000
        this.baseCn = set(this.maxN)
        this.baseCnxI = set(this.maxN)
        this.baseC2nCn = set(this.maxN)
        this.baseDnCn = set(this.maxN)
        this.baseDn = set(this.maxN)
        this.baseDnxI = set(this.maxN)
        this.baseD2nDn = set(this.maxN)

    def CorD(this, base, n):
        assert n <= this.maxN, "n should be smaller than %d" % this.maxN
        assert n > 0, 'n should be at least 1'
        return base + n - 1

    def Cn(this, n):
        if n == 1:
            return this.E
        elif n == 2:
            # C2 ~= D1
            return this.Dn(1)
        else:
            return this.CorD(this.baseCn, n)

    def CnxI(this, n):
        if n == 1:
            return this.ExI
        elif n == 2:
            # C2 ~= D1
            return this.DnxI(1)
        return this.CorD(this.baseCnxI, n)

    def C2nCn(this, n):
        if n == 1:
            # C2 ~= D1
            return this.DnCn(1)
        else:
            return this.CorD(this.baseC2nCn, n)

    def DnCn(this, n):
        if n == 2:
            # C2 ~= D1
            return this.D2nDn(1)
        else:
            return this.CorD(this.baseDnCn, n)

    def Dn(this, n):
        return this.CorD(this.baseDn, n)

    def DnxI(this, n):
        return this.CorD(this.baseDnxI, n)

    def D2nDn(this, n):
        return this.CorD(this.baseD2nDn, n)

symmetry = Symmetry()

class Isometry:
    VsOrbits = None
    sphere   = None
    cyl      = None
    addFaces = True
    dbgPrn   = True

    """
    This class contains symmetry descriptions. 

    The class can be used to describe shapes with symmetry, e.g. the cube.
    The cube can be described by one square and a object of the Isometry class.
    This object should contain 6 transformations (including the Identity).
    The colour maps then describe which colour a face of the cube should get
    after transforming the initial square.
    """
    def __init__(this,
        directIsometries, oppositeIsometry = None,
        Vs = [], Es = [], Fs = []
    ):
        """
        Set the initial isometries, vertices, edges and faces.

        directIsometries: specifies an array of direct isometries. Each isometry
                          is a cgtypes.quat.
        oppositeIsometry: specifies a cgtypes.mat3 that represents an opposite
                          isometry, e.g. the central inversion or a reflection.
                          The set of opposite isometries is defined by this
                          opposite isometry applied after each direct isometry
                          in directIsometries.
                          The parameter is optional and it will be None on
                          default, meaning there will be no opposite isometries.
        Vs: Optional array of 3D vertices if no array is specified an empty
            array will be used.
        Es: optional array of edges. It is a flat array, that is assumed to have
            an even length. where i and j in edge [ .., i, j,.. ] are indices in
            Vs. Empty on default.
        Fs: Optional array of faces, that do not need to be triangular. It is a
            hierarchical array, ie it consists of sub-array, where each
            sub-array describes one face. Each n-sided face is desribed by n
            indices. Empty on default. Using triangular faces only gives a
            better performance.
        """
        if this.dbgPrn:
            print 'Isometry.__init__:'
            print '  directIsometries = ['
            for isom in directIsometries:
                print '    ', isom
            print '  ]'
            print '  Vs = ['
            for V in Vs:
                print '    ', V
            print '  ]'
        this.setIsoOp(directIsometries, oppositeIsometry)
        this.setVertexProperties(Vs, radius = -1.)
        this.setEdgeProperties(Es, radius = -1., color = [0.1, 0.1, 0.1])
        this.setFaceProperties(Fs, colors = [[0.9, 0.9, 0.9]])

    def setVertexProperties(this, Vs = None, radius = None, color = None):
        """
        Set the vertices and how/whether vertices are drawn in OpenGL.

        For all parameters hold that they are optional and that they are not
        changed if not specified (or equal to None)
        Vs: an array of vertices.
        radius: If > 0.0 draw vertices as spheres with the specified colour. If
                no spheres are required (for preformance reasons) set the radius
                to a value <= 0.0.
        color: optianl array with 3 rgb values between 0 and 1.
        """
        if Vs != None:
            this.Vs = Vs
            this.VsRange = range(len(Vs))
            if this.VsOrbits != None:
                this.orbitVs()
            this.glUpdateVs = True
        if radius != None:
            this.addSphereVs = radius > 0.0
            if this.addSphereVs:
                if this.sphere != None: del this.sphere
                this.sphere = VSphere(radius = radius)
        if color != None:
            this.vCol = color

    def setEdgeProperties(this, Es = None, radius = None, color = None):
        """
        Specify the edges and set how they are drawn in OpenGL.

        For all parameters hold that they are optional and that they are not
        changed if not specified (or equal to None)
        Es: an array of edges, where i and j in edge [ .., i, j,.. ] are indices
            in Vs.
        radius: If > 0.0 draw vertices as cylinders with the specified colour.
                If no cylinders are required (for preformance reasons) set the
                radius to a value <= 0.0 and the edges will be drawn as lines,
                using glPolygonOffset.
        color: array with 3 rgb values between 0 and 1.
        """
        if Es != None:
            this.Es = Es
            this.EsRange = range(0, len(this.Es), 2)
        if radius != None:
            this.useCylinderEs = radius > 0.0
            if this.useCylinderEs:
                if this.cyl != None: del this.cyl
                this.cyl = P2PCylinder(radius = radius)
        if color != None:
            this.eCol = color

    def setFaceProperties(this, Fs = None, colors = None):
        """
        Define the colours of the faces and optionally the edges. 

        For all parameters hold that they are optional and that they are not
        changed if not specified (or equal to None)
        Fs: Optional array of faces, that do not need to be triangular. It is a
            hierarchical array, ie it consists of sub-array, where each
            sub-array describes one face. Each n-sided face is desribed by n
            indices. Empty on default. Using triangular faces only gives a
            better performance.
            If Fs == None, then the previous specified value will be used.
        colors: an array of rgb arrays, where each colour channel is between 0
                and 1. If the array is one colour than all faces (after applying
                the symmetry) will have the same colour. If the array has the
                same (or more) amount as the number of symmetries, than each
                face after symmetry operation i will get colour fCol[i].  If the
                amount of colours is less than the number of symmetries then
                they should be divisible and the symmetry is used to divide the
                colours of the object. E.g. a cube with symmetry S4xI, i.e. 48
                isometries can be coloured with 3 colours, each oppositing face
                having the same colour.
        """
        if Fs != None:
            this.Fs = []
            this.Ts = []
            this.TriangulatedFs =[]
            for f in Fs:
                # one could check whether f[0] == f[len(f)-1] to reduce, though
                # the function text explains that one should not so this...
                # check if the face is a triangle or not.
                if len(f) == 3:
                    this.Ts.append(f)
                # the following only makes sense if the quadrilateral is conves,
                # i.e. if it isn't an arrow... Hmm, is it always true that the
                # shortest diagonal of an arrow is inside the arrow?
                # TODO: Does the same hold for GL_QUADS...? The red book doesn't
                # state anything... (Chapter 2)
                #elif len(f) == 4:
                #    this.Ts.append(f[0], f[1], f[2])
                #    this.Ts.append(f[0], f[2], f[3])
                else:
                    this.Fs.append(f)
                    # triagulate the Fs here. The stencil buffer will be used to
                    # triangulate. Note that this method draw a pentagram specified by 5
                    # straight edges with a empty pentagon in the centre.
                    triF = []
                    for i in range(1, len(f)-1):
                        # i+1 before i, to keep clock-wise direction
                        triF.extend([f[0], f[i+1], f[i]])
                    this.TriangulatedFs.append(triF)
        if colors != None:
            nrOfColors = len(colors)
            if nrOfColors == 1:
                this.fCol = [colors[0] for i in this.isomRange]
            elif nrOfColors < this.order:
                this.divideColor(colors)
            else:
                this.fCol = colors[:this.order]

    def divideColor(this, colors):
        """
        Divide the specified colours over the isometries. 

        This function should actually be implemented by a descendent, so that
        the colours can be divided according to the symmetry. This function
        just repeats the colours until the length is long enough.
        The amount of colours should be less than the nr of isomentries.
        """
        nrOfColors = len(colors)
        div = this.order / nrOfColors
        mod = this.order % nrOfColors
        this.fCol = []
        for i in range(div):
            this.fCol.extend(colors)
        this.fCol.extend(colors[:mod])

    def setIsoOp(this, directIsometries, oppositeIsometry = None):
        """
        Set the isometry operation at initialisation.

        It is recommended to set the isometry operations at initialisation
        only, otherwise you might break other properties, like the face colours.
        directIsometries: specifies an array of direct isometries. Each isometry
                          is a cgtypes.quat.
        oppositeIsometry: specifies a cgtypes.mat3 that represents an opposite
                          isometry, e.g. the central inversion or a reflection.
                          The set of opposite isometries is defined by this
                          opposite isometry applied after each direct isometry
                          in directIsometries.
                          The parameter is optional and it will be None on
                          default, meaning there will be no opposite isometries.
        """
        this.isometryOperations = {
                'direct': directIsometries,
                'opposite': oppositeIsometry
            }
        this.order = len(directIsometries)
        assert oppositeIsometry == None or (
                type(oppositeIsometry) == type(cgtypes.mat3())
            ), 'Either oppositeIsometry should be None or it should have be of type cgtype.mat3'
        this.isomRange = range(this.order)
        if this.VsOrbits != None:
            this.orbitVs()

    def getIsoOp(this):
        """
        Get the isometry operations.
        """
        return this.isometryOperations

    def orbitVs(this):
        """
        Orbit the faces according to the specified isometries

        The result is saved in this.VsOrbits. Note that this.VsOrbits is not a
        flat array. For each isometry this arrays contains a subarray of
        vertices that contains the repositioned the repositioned vertices of
        this.Vs. When drawing with glDraw the orbited elements will be
        used. If this is not wanted anymore, use unOrbitVs.
        """
        VsOrbits = []
        #print 'in', this.Vs[0]
        for dirIsom in this.isometryOperations['direct']:
            MdirIsom = dirIsom.toMat3()
            VsOrbits.append([MdirIsom*cgtypes.vec3(v) for v in this.Vs])
        #print 'out', this.Vs[0]
        #try:
        #    print 'res', VsOrbits[0][0], VsOrbits[1][0]
        #except IndexError: print
        MoppIsom = this.isometryOperations['opposite']
        if MoppIsom != None:
            for dirIsom in this.isometryOperations['direct']:
                MdirIsom = dirIsom.toMat3()
                VsOrbits.append([MoppIsom*MdirIsom*cgtypes.vec3(v) for v in this.Vs])
        this.VsOrbits = VsOrbits

    def unOrbitVs(this):
        """
        Undo the effect of orbitVs

        See orbitVs for more info.
        """
        this.VsOrbits = None

    def glDrawBaseElement(this, Vs, fCol):
        """
        Draw the base element according to the definition of the Vs, Es, Fs and
        colour settings.

        fCol: the colour to use for the face.
        Use this.addFaces to set whether the faces should be drawn.
        Use this.useCylinderEs to set whether the edges should be drawn as
        cylinders, not as lines.
        Use this.setVertexProperties(xx) to set how the vertices are drawn.
        """
        # have this one here and not in glDraw, so that a client can call this
        # function as well (without having to think about this)
        if this.glUpdateVs:
            glVertexPointerf(Vs)
            glNormalPointerf(Vs)
            this.glUpdateVs = False
        # VERTICES
        if this.addSphereVs:
            glColor(this.vCol[0], this.vCol[1], this.vCol[2])
            for i in this.VsRange:
                this.sphere.draw(Vs[i])
        # EDGES
        glColor(this.eCol[0], this.eCol[1], this.eCol[2])
        if this.useCylinderEs:
            # draw edges as cylinders
            for i in this.EsRange:
                this.cyl.draw(
                        v0 = Vs[this.Es[i]],
                        v1 = Vs[this.Es[i+1]]
                    )
        else:
            # draw edges as lines
            glPolygonOffset(1.0, 3.)
            glDisable(GL_POLYGON_OFFSET_FILL)
            glDrawElementsui(GL_LINES, this.Es)
            glEnable(GL_POLYGON_OFFSET_FILL)

        # FACES
        if this.addFaces:
            glColor(fCol[0], fCol[1], fCol[2])
            if this.Ts != []:
                glDrawElementsui(GL_TRIANGLES, this.Ts)
            if this.Fs != []:
                # TODO: This part belongs to a GLinit:
                glClearStencil(0)
                stencilBits = glGetIntegerv(GL_STENCIL_BITS)
                assert stencilBits > 0, 'Only triangles are supported, since there is no stencil bit'
                # << TODO: end part that belongs to a GLinit
                for face in this.TriangulatedFs:
                    glClear(GL_STENCIL_BUFFER_BIT)
                    # use stecil buffer to triangulate.
                    glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
                    glDepthMask(GL_FALSE)
                    #glDepthFunc(GL_ALWAYS)
                    # Enable Stencil, always pass test
                    glEnable(GL_STENCIL_TEST)
                    # always pass stencil test
                    glStencilFunc(GL_ALWAYS, 1, 1)
                    # stencil fail: don't care, never fails
                    # z-fail: zero
                    # both pass: invert stencil values
                    glStencilOp(GL_KEEP, GL_ZERO, GL_INVERT)
                    # Create triangulated stencil:
                    glDrawElementsui(GL_TRIANGLES, face)
                    # Reset colour mask and depth settings.
                    #glDepthFunc(GL_LESS)
                    glDepthMask(GL_TRUE)
                    glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
                    # Draw only where stencil equals 1 (masked to 1)
                    # GL_INVERT was used, i.e. in case of e.g. 8 bits the value is
                    # either 0 or 0xff, but only the last bit is checked.
                    glStencilFunc(GL_EQUAL, 1, 1)
                    # make stencil read only:
                    glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
                    # Now, write according to stencil
                    glDrawElementsui(GL_TRIANGLES, face)
                    # ready, disable stencil
                    glDisable(GL_STENCIL_TEST)

    def glDraw(this):
        """
        Assumes that OpenGL is set up properly and draws the base element,
        with all isomentry operations. The matrix mode should be set to
        GL_MODELVIEW.
        """
        if this.dbgPrn and this.VsOrbits != None:
            print 'Isometry.glDraw', this.order, 'of', len(this.VsOrbits), 'orbited elements'
        for i in this.isomRange:
            if this.VsOrbits != None:
                this.glUpdateVs = True
                this.glDrawBaseElement(this.VsOrbits[i], this.fCol[i])
            else:
                op = this.isometryOperations['direct'][i]
                glPushMatrix()
                angleAxis = op.toAngleAxis()
                glRotate(
                    Geom3D.Rad2Deg*angleAxis[0],
                    angleAxis[1][0], angleAxis[1][1], angleAxis[1][2]
                )
                this.glDrawBaseElement(this.Vs, this.fCol[i])
                glPopMatrix()

class Iso_A4(Isometry):
    def __init__(this, *args, **kwargs):
        """
        This is the isometry consisting of all the direct isometries of a
        tetrahedron.

        The tetrahedron is positioned in such a way that the x-. y- and z-axis
        are the 2-fold symmetry axes.
        For explanation of the parameters, see Isometry. All parameters except
        for the isometries can be specified here.
        """
        # A4 consists of
        # - E
        # - 1/3 and 2/3 (of a circle) rotations around axes 1, 2, 3, 4: T1.1,
        #   T1.2, T2.1, T2.2, T3.1, T3.2, T4.1, and T4.2.
        # - 1/2 rotations around axes 5, 6, 7: H5, H6, H7
        # Now a subgroup of A4 is D2: { E, H5, H6, H7 }
        # Its cosets are:
        # T1.1 o D2 = { T4.1, T3.1, T2.1, T1.1 }
        # T1.2 o D2 = { T4.2, T3.2, T2.2, T1.2 }
        # This means that A4 can be generated by whatever generates D2 and T1.1.
        # Now all elements of D2 are needed to generate D2.
        E    = Geom3D.E
        T1_1 = cgtypes.quat(Geom3D.R1_3,   cgtypes.vec3(1., 1., 1.))
        T1_2 = cgtypes.quat(2*Geom3D.R1_3, cgtypes.vec3(1., 1., 1.))
        H5   = cgtypes.quat(Geom3D.R1_2,   cgtypes.vec3(1., 0., 0.))
        H6   = cgtypes.quat(Geom3D.R1_2,   cgtypes.vec3(0., 1., 0.))
        H7   = cgtypes.quat(Geom3D.R1_2,   cgtypes.vec3(0., 0., 1.))
        Isometry.__init__(this,
            [
                E,  T1_1     , T1_2,            # E , T1.1, T1.2
                H5, T1_1 * H5, T1_2 * H5,       # H5, T4.1, T2.2
                H6, T1_1 * H6, T1_2 * H6,       # H6, T3.1, T4.2
                H7, T1_1 * H7, T1_2 * H7,       # H7, T2.1, T3.2
            ],
            None,
            *args, **kwargs
        )

    def divideColor(this, c):
        """
        Divide the colours c according to the symmetry.

        Accepted amount of colours are 3, 4, or 6, otherwise
        Isometry.divideColor is used.
        see Isometry.divideColor.
        """
        nrOfColors = len(c)
        if nrOfColors == 3:
            # divide according to the 3 cosets:
            #  {E, H5, H6, H7}
            #  {T1.1, T2.1, T3.1, T4.1}
            #  {T1.2, T2.2, T3.2, T4.2}
            this.fCol = c
            this.fCol.extend(c)
            this.fCol.extend(c)
            this.fCol.extend(c)
        elif nrOfColors == 4:
            # divide according to the 4 cosets:
            #  {E , T1.1, T1.2}
            #  {H5, T2.1, T4.2}
            #  {H6, T4.1, T3.2}
            #  {H7, T3.1, T2.2}
            this.fCol = [
                    c[0], c[0], c[0],
                    c[1], c[2], c[3],
                    c[2], c[3], c[1],
                    c[3], c[1], c[2]
                ]
        elif nrOfColors == 6:
            # divide according to the 6 cosets:
            # {E   , H5  }, {H6  , H7  },
            # {T1.1, T4.1}, {T1.2, T2.2},
            # {T2.1, T3.1}, {T3.2, T4.2}
            this.fCol = [
                    c[0], c[2], c[3],
                    c[0], c[2], c[3],
                    c[1], c[4], c[5],
                    c[1], c[4], c[5]
                ]
        elif nrOfColors == 2:
            # There is no subgroup of order 6
            # but we can divide the colours in such a way that for a certain
            # starting element the element around a pair of 3 axes have the same
            # colour:
            # { E, T1_1, T1_2, H5, T2_1, T4_2 }
            this.fCol = [
                    c[0], c[0], c[0],
                    c[0], c[1], c[1],
                    c[1], c[1], c[0],
                    c[1], c[0], c[1]
                ]
        else:
            Isometry.divideColor(this, c)

class Iso_A4_C3(Iso_A4):
    def __init__(this, *args, **kwargs):
        """
        This is the isometry consisting of all the direct isometries of a
        tetrahedron needed for a stabiliser with symmetry C3.

        The tetrahedron is positioned in such a way that the x-. y- and z-axis
        are the 2-fold symmetry axes.
        For explanation of the parameters, see Isometry. All parameters except
        for the isometries can be specified here.
        """
        Iso_A4.__init__(this, *args, **kwargs)
        # Only keep the half turns of Iso_A4, see Iso_A4
        # see Iso_A4 which indices these have.
        ops = this.getIsoOp()['direct']
        this.setIsoOp([ops[i] for i in range(0, 12, 3)])

    def divideColor(this, c):
        """
        Divide the colours c according to the symmetry.

        Since the order is 4, the only valid amount less than the order would be
        2. For 2 it doesn't really matter how you divide.
        see Isometry.divideColor.
        """
        Isometry.divideColor(this, c)

class Iso_A4_C2(Iso_A4):
    def __init__(this, *args, **kwargs):
        """
        This is the isometry consisting of all the direct isometries of a
        tetrahedron needed for a stabiliser with symmetry C2.

        The tetrahedron is positioned in such a way that the x-. y- and z-axis
        are the 2-fold symmetry axes.
        For explanation of the other parameters, see Isometry. All parameters
        except for the isometries can be specified here.
        """
        #track = 0
        #if 'track' in kwargs:
        #    track = kwargs['alt']
        #    del kwargs['track']
        Iso_A4.__init__(this, *args, **kwargs)
        this.setOrbit(0)

    def setOrbit(this, track):
        """
        Set the way of reproducing the whole polyhedron from the stabiliser.

        track: Since A4 doesn't have a subgroup of order 6, there is no unique
               way of reproducing A4 from any C2 pair. One way covers 4 of the
               six possible pairs, i.e. with two alternatives we can reproduce
               A4.  With the track argument you can steer which alternative is
               used.  Choices are 0 or non-zero.
        """
        tmp = Iso_A4([])
        o = tmp.getIsoOp()['direct']
        del tmp
        if track == 0:
            # { E, T1_1, T1_2, T3_1, T4_2, H6 }
            this.setIsoOp([o[0], o[1], o[2], o[6], o[7], o[8]])
        else:
            # { E, T1_1, T1_2, T2_1, T3_2, H7 }
            this.setIsoOp([o[0], o[1], o[2], o[9], o[10], o[11]])

    def divideColor(this, c):
        """
        Divide the colours c according to the symmetry.

        Since A4 doesn't have a subgroup of order 6, we cannot use any subgroups
        for this subgroup either. Common sense is to be used.
        Note that the order of the orbit that generates the complete model
        equals to 6. So the only colour combinations that make sense are 2 and 3
        colours.
        """
        nrOfColors = len(c)
        if nrOfColors == 3:
            this.fCol = [
                    c[0], c[1], c[2],
                    c[0], c[1], c[2],
                ]
        elif nrOfColors == 2:
            this.fCol = [
                    c[0], c[0], c[0],
                    c[1], c[1], c[1],
                ]
        else:
            Isometry.divideColor(this, c)

def isometryClass(
    group,
    stabilizer = symmetry.E,
    zOrder = 0,
    Gn = 0,
    Sn = 0
    #alt = 0
):
    """
    Returns the Isometry class that should be used for a polyhedron that
    belangs to the symmetry group 'group' and for which some element (in this
    module a face) has the stabiliser 'stabilizer'

    The function returned result can be called to create an object of the
    needed Isometry class.
    group: symmetry group of the polyhedron
    stabilizer: the stabiliser of the faces.
    zOrder: if the z-axis shared by a rotation axis it specifies the order of
            the rotion axis. 1 means it is not shared, 0 means that the default
            is used.
    Gn: in case a cyclic or dihedral group is specified, Gn specifies the order.
    Sn: in case a cyclic or dihedral stabiliser is specified, Sn specifies the order.
    """
#    alt: gives specifies which alternative is use. E.g. for group S4 and
#         stabiliser C2, the 2-fold axis of C2 may be on a 4-fold axis or a
#         2-fold axis of S4. The convention is to count the alternatives in
#         increasing order. For the previous example this means that alternative
#         0 refers to the sitution that the C2 2-fold s shared by the S4 2-fold
#         axis and alternative 1 to the situation where the C2 2-axis is shared
#         by the S4 4-fold axis.
    if group == symmetry.A4:
        if zOrder == 0 or zOrder == 2:
            if stabilizer == symmetry.E:
                return None# IsoA4_zO2
            elif stabilizer == symmetry.Cn(2):
                print 'Note A4/C2 is actually promoted to S4A4/C4C2'
                return None# IsoA4_zO2_6
            elif stabilizer == symmetry.Cn(3):
                return None# IsoA4_zO2_4
            elif stabilizer == symmetry.Dn(2):
                assert False, "Not yet supported, TODO IsoA4_zO2_3"
            else:
                assert False, "Not supported, are you sure the stabilizer is a subgroup of A4?"
        else:
            assert False, "%d fold z-axis not supported, for A4 symmetry" % zOrder

    elif group == symmetry.A4xI:
        if zOrder == 0 or zOrder == 2:
            if stabilizer == symmetry.E:
                return None# IsoA4xI_zO2
            elif stabilizer == symmetry.ExI:
                return None# IsoA4_zO2
            elif stabilizer == symmetry.Cn(2):
                return None# IsoA4xI_zO2_12
            elif stabilizer == symmetry.C2nCn(1):
                return None# IsoA4xI_zO2_12
            elif stabilizer == symmetry.Cn(3):
                return None# IsoA4xI_zO2_8
            elif stabilizer == symmetry.CnxI(3):
                return None# IsoA4_zO2_4
            else:
                assert False, "Stabilizer for IsoA4xI not supported (yet)"
        else:
            assert False, "Position for IsoA4xI not supported (yet)"

    elif group == symmetry.S4A4:
        if zOrder == 0 or zOrder == 2:
            if stabilizer == symmetry.E:
                return None# IsoS4A4_zO2
            elif stabilizer == symmetry.Cn(2):
                print 'Note S4A4/C2 is actually promoted to S4A4/C4C2'
                return None# IsoA4_zO2_6
            elif stabilizer == symmetry.Cn(3):
                return None# IsoS4A4_zO2_8
            elif stabilizer == symmetry.C2nCn(1):
                # C2C1 equals to E and a reflection, ie remove the reflection
                # from S4A4.
                return None# IsoA4_zO2
            elif stabilizer == symmetry.C2nCn(2):
                return None# IsoA4_zO2_6
            elif stabilizer == symmetry.DnCn(3):
                return None# IsoA4_zO2_4
            elif stabilizer == symmetry.S4A4:
                return None# IsoE
            else:
                assert False, "Stabilizer for IsoS4A4 not supported (yet)"
        else:
            assert False, "Position for IsoS4A4 not supported (yet)"

    elif group == symmetry.S4:
        if zOrder == 0 or zOrder == 4:
            if stabilizer == symmetry.E:
                return None# IsoS4_zO4
            elif stabilizer == symmetry.Cn(2): # ~= D1
                return None# IsoS4_zO4_12
            elif stabilizer == symmetry.Cn(3):
                return None# IsoS4_zO4_8
            elif stabilizer == symmetry.Cn(4):
                return None# IsoS4_zO4_6
            elif stabilizer == symmetry.Dn(2):
                # TODO why does Verheyen[2] Diagram 6 contains 2 D2's?
                assert False, "Not yet supported, TODO IsoS4_zO2_6_alt"
            elif stabilizer == symmetry.Dn(3):
                assert False, "Not yet supported, TODO IsoS4_zO2_4"
            elif stabilizer == symmetry.Dn(4):
                assert False, "Not yet supported, TODO IsoS4_zO2_3"
            elif stabilizer == symmetry.A4:
                assert False, "Not yet supported, TODO IsoS4_zO2_2"
            elif stabilizer == symmetry.Dn(2):
                assert False, "Not yet supported, TODO IsoA4_zO2_3"
            else:
                assert False, "Not supported, are you sure the stabilizer is a subgroup of S4?"
        else:
            assert False, "%d fold z-axis not supported, for S4 symmetry" % zOrder

    elif group == symmetry.S4xI:
        if zOrder == 0 or zOrder == 4:
            if stabilizer == symmetry.E:
                return None# IsoS4xI_zO4
            elif stabilizer == symmetry.ExI:
                return None# IsoS4_zO4
            elif stabilizer == symmetry.Cn(2):
                return None# IsoS4xI_zO4_24
            elif stabilizer == symmetry.Cn(3):
                return None# IsoS4xI_zO4_16
            elif stabilizer == symmetry.C2nCn(1) or stabilizer == symmetry.C2C1 or stabilizer == symmetry.D1C1:
                return None# IsoS4_zO4
            elif stabilizer == symmetry.C2nCn(2): # ~= C4D1
                return None# IsoS4xI_zO4_12
            elif stabilizer == symmetry.DnCn(2):
                return None# IsoS4_zO4_12
            elif stabilizer == symmetry.DnCn(3):
                return None# IsoS4_zO4_8
            elif stabilizer == symmetry.D2nDn(2):
                return None# IsoS4_zO4_6
            elif stabilizer == symmetry.CnxI(3):
                return None# IsoS4_zO4_8
            elif stabilizer == symmetry.CnxI(4):
                return None# IsoS4_zO4_6
            elif stabilizer == symmetry.DnxI(1):
                return None# IsoS4_D1_zO4_12
            elif stabilizer == symmetry.DnxI(2):
                return None# IsoS4_zO4_6
            elif stabilizer == symmetry.DnxI(4):
                return None# IsoS4_zO4_3
            elif stabilizer == symmetry.S4A4:
                return None# IsoS4_zO4_2
            else:
                assert False, "Stabilizer for IsoS4xI not supported (yet)"
        else:
            assert False, "Position for IsoS4xI not supported (yet)"

    elif group == symmetry.A5:
        if zOrder == 0 or zOrder == 3:
            if stabilizer == symmetry.E:
                return None# IsoA5_zO3
            elif stabilizer == symmetry.Cn(5):
                return None# IsoA5_zO3_12
            elif stabilizer == symmetry.Cn(3):
                return None# IsoA5_zO3_20
            elif stabilizer == symmetry.Cn(2):
                return None# IsoA5_zO3_30
            elif stabilizer == symmetry.A4:
                return None# IsoA5_zO3_5
            elif stabilizer == symmetry.Dn(5):
                assert False, "Not yet supported, TODO IsoA5_zO3_6"
                return None# IsoA5_zO3_6
            elif stabilizer == symmetry.Dn(3):
                assert False, "Not yet supported, TODO IsoA5_zO3_10"
                return None# IsoA5_zO3_10
            elif stabilizer == symmetry.Dn(2):
                assert False, "Not yet supported, TODO IsoA5_zO3_15"
                return None# IsoA5_zO3_15
            else:
                assert False, "Not supported, are you sure the stabilizer is a subgroup of A45"
        elif zOrder == 5:
            if stabilizer == symmetry.E:
                return None# IsoA5_zO5
            elif stabilizer == symmetry.Cn(5):
                return None# IsoA5_zO5_12
            elif stabilizer == symmetry.Cn(3):
                return None# IsoA5_zO5_20
            elif stabilizer == symmetry.Cn(2):
                return None# IsoA5_zO5_30
            elif stabilizer == symmetry.A4:
                assert False, "Not yet supported, TODO IsoA5_zO5_5"
                return None# IsoA5_zO5_5
            elif stabilizer == symmetry.Dn(5):
                assert False, "Not yet supported, TODO IsoA5_zO5_6"
                return None# IsoA5_zO5_6
            elif stabilizer == symmetry.Dn(3):
                assert False, "Not yet supported, TODO IsoA5_zO5_10"
                return None# IsoA5_zO5_10
            elif stabilizer == symmetry.Dn(2):
                assert False, "Not yet supported, TODO IsoA5_zO5_15"
                return None# IsoA5_zO5_15
            else:
                assert False, "Not supported, are you sure the stabilizer is a subgroup of A45"
        else:
            assert False, "%d fold z-axis not supported, for A5 symmetry" % zOrder

    elif group == symmetry.A5xI:
        if zOrder == 0 or zOrder == 3:
            if stabilizer == symmetry.E:
                return None# IsoA5xI_zO3
            elif stabilizer == symmetry.ExI:
                return None# IsoA5_zO3
            elif stabilizer == symmetry.Cn(3):
                return None# IsoA5xI_zO3_40
            elif stabilizer == symmetry.Cn(2):
                return None# IsoA5xI_zO3_60
            elif stabilizer == symmetry.A4:
                return None# IsoA5xI_zO3_10
            elif stabilizer == symmetry.C2nCn(1) or stabilizer == symmetry.C2C1 or stabilizer == symmetry.D1C1:
                return None# IsoA5_zO3
            elif stabilizer == symmetry.DnCn(2): # ~= D2D1
                return None# IsoA5_zO3_30
            elif stabilizer == symmetry.DnCn(3):
                return None# IsoA5_zO3_20
            else:
                assert False, "Stabilizer for IsoA5xI not supported (yet)"
        else:
            assert False, "Position for IsoA5xI not supported (yet)"

    #if group >= symmetry.baseCn and group < symmetry.baseCn + symmetry.maxN:
    elif group == symmetry.Cn:
        if stabilizer == symmetry.E:
            return None# IsoCn
        else:
            assert False, "Stabilizer for Cn not supported (yet)"

    elif group == symmetry.C2nCn:
        if stabilizer == symmetry.E:
            return None# IsoC2nCn
        else:
            assert False, "Stabilizer for C2nCn not supported (yet)"

    elif group == symmetry.CnxI:
        if stabilizer == symmetry.E:
            return None# IsoCnxI
        else:
            assert False, "Stabilizer for CnxI not supported (yet)"

    elif group == symmetry.DnCn:
        if stabilizer == symmetry.E:
            return None# IsoDnCn
        elif stabilizer == symmetry.C2nCn(1):
            return None# IsoCn
        elif stabilizer == symmetry.Cn:
            # if group symmetry = DmnCmn,
            # and stabilizer symmetry = Cm
            return None# IsoDmnCmn_2n
        elif stabilizer == symmetry.DnCn:
            # if group symmetry = DmnCmn,
            # and stabilizer symmetry = DmCm
            return None# IsoCmn_n
        else:
            assert False, "Stabilizer for DnCn not supported (yet)"

    elif group == symmetry.Dn:
        if stabilizer == symmetry.E:
            return None# IsoDn
        elif stabilizer == symmetry.Cn(2):
            return None# IsoCn
        elif stabilizer == symmetry.Cn:
            # if group symmetry = Dmn,
            # and stabilizer symmetry = Cm
            return None# IsoDmn_2n
        else:
            assert False, "Stabilizer for Dn not supported (yet)"

    elif group == symmetry.D2nDn:
        if stabilizer == symmetry.E:
            return None# IsoD2nDn
        elif stabilizer == symmetry.Cn(2):
            return None# IsoD2nDn_C2
        elif stabilizer == symmetry.Cn:
            # if group symmetry = D2mnDmn,
            # and stabilizer symmetry = Cm
            return None# IsoD2mnDmn_4n
        elif stabilizer == symmetry.C2nCn(1) or stabilizer == symmetry.C2C1:
            return None# IsoD2nDn_C2C1
        elif stabilizer == symmetry.C2nCn(2):
            # note that the caller should realise that the group symmetry
            # is D4nD2n (n odd)
            return None# IsoD4nD2n_C4C2
        elif stabilizer == symmetry.D1C1:
            return None# IsoD2nDn_D1C1 # n odd
        elif stabilizer == symmetry.DnCn(2):
            # with n odd
            return None# IsoD2nDn_D2C2
        elif stabilizer == symmetry.DnCn:
            # if group symmetry = D2mnDmn,
            # and stabilizer symmetry = DmCm
            return None# IsoD2mnDmn_DmCm
        elif stabilizer == symmetry.D2nDn:
            # if group symmetry = D2mnDmn,
            # and stabilizer symmetry = D2mDm
            return None# IsoD2mDmn_D2mDm
        else:
            assert False, "Stabilizer for D2nDn not supported (yet)"

    elif group == symmetry.DnxI:
        if stabilizer == symmetry.E:
            return None# IsoDnxI
        elif stabilizer == symmetry.Cn(2):
            return None# IsoDnxI_C2
        elif stabilizer == symmetry.Cn:
            # if group symmetry = DmnxI,
            # and stabilizer symmetry = Cm
            return None# IsoDmnxI_4n
        elif stabilizer == symmetry.C2nCn(1) or stabilizer == symmetry.C2C1:
            return None# IsoDnxI_C2C1
        elif stabilizer == symmetry.C2nCn(2):
            # note that the caller should realise that the group symmetry
            # is D4nxI
            return None# IsoD4nxI_C4C2
        elif stabilizer == symmetry.D1C1:
            # I could use IsoD2nxI_D1C1 to ensure DnxI to be even, but such a
            # trick is not possible for D2nDn / D1C1. Keep the interface
            # consisitent instead.
            return None# IsoDnxI_D1C1 # n even
        elif stabilizer == symmetry.DnCn(2):
            # with n even
            return None# IsoDnxI_D2C2
        elif stabilizer == symmetry.DnCn:
            # if group symmetry = DmnxI,
            # and stabilizer symmetry = DmCm
            return None# IsoDmnxI_DmCm
        elif stabilizer == symmetry.D2nDn:
            # if group symmetry = DmnxI,
            # and stabilizer symmetry = D2mDm
            return None# IsoDmnxI_D2mDm
        else:
            assert False, "Stabilizer for DnxI not supported (yet)"

    else:
        return None# IsoE


#if __name__ == '__main__':
#    app = wx.PySimpleApp()
#    app.MainLoop()
