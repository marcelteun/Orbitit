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

import wx
import math
import Geom3D
import GeomTypes
from wx import glcanvas
from OpenGL.GLU import *
from OpenGL.GL import *

def getAxis2AxisRotation(a0, a1):
    """Given 2 vectors return the rotation that is needed to transfer 1 into the other.
    """
    # TODO: how to know which angle is taken (if you switch the axes, will you
    # still have to correct angle and axis?)
    vec3Type = type(GeomTypes.Vec3([0, 0, 0]))
    assert (type(a0) == vec3Type) and (type(a1) == vec3Type)
    if a0 == a1:
        # if both axis are in fact the same no roation is needed
        axis = GeomTypes.uz
        angle = 0
    if a0 == -a1:
        # if one axis should be rotated in its opposite axis, handle
        # separately, since the cross product will not work.
        # rotate pi around any vector that makes a straight angle with a0
        a2 = GeomTypes.Vec3([i+0.5 for i in a1])
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
    return axis, angle

class Triangle:
    def __init__(this, v0, v1, v2):
        this.v = [GeomTypes.Vec3(v0), GeomTypes.Vec3(v1), GeomTypes.Vec3(v2)]
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
        this.parent = parent
        glcanvas.GLCanvas.__init__(this, parent, -1,
                size = size,
                attribList = [
                    wx.glcanvas.WX_GL_RGBA,
                    wx.glcanvas.WX_GL_DOUBLEBUFFER,
                    wx.glcanvas.WX_GL_STENCIL_SIZE, 8
                ]
            )
        this.context = glcanvas.GLContext(this)
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
        # these repos are used internally and are related to the rotation
        # caused by the mouse
        # - modelRepos is used when calculating a new orientation. It expresses
        #   the rotation caused by the mouse, before calculating the new one.
        # - movingRepos is the newly calculated rotation after a mouse indicated
        #   rotation is finished.
        this.modelRepos = GeomTypes.E
        this.movingRepos = GeomTypes.E
        this.xAxis = GeomTypes.ux
        this.yAxis = GeomTypes.uy
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
        try:
            this.SetCurrent(this.context)
        except wx._core.PyAssertionError:
            pass
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
                spherePos = GeomTypes.Vec3([x, y, math.sqrt(R2 - l2)])
            elif l2 > R2:
                scale = math.sqrt(R2/l2)
                spherePos = GeomTypes.Vec3([scale*x, scale*y, 0])
            else: # probably never happens (floats)
                spherePos = GeomTypes.Vec3([x, y, 0])
            return spherePos
        dc = wx.PaintDC(this)
        this.SetCurrent(this.context)
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
            newSpherePos = xy2SphereV(this.x, this.y,    width, height, R2)
            orgSphere = xy2SphereV(this.xOrg, this.yOrg, width, height, R2)
            ax, an = getAxis2AxisRotation(orgSphere, newSpherePos)
            this.movingRepos = GeomTypes.Rot3(axis = ax, angle = an
                ) * this.modelRepos
            glLoadMatrixd(this.Moriginal)
            glScalef(this.currentScale, this.currentScale, this.currentScale)
            save, GeomTypes.eqFloatMargin = GeomTypes.eqFloatMargin, 1.0e-14
            angle = Geom3D.Rad2Deg*this.movingRepos.angle()
            axis  = this.movingRepos.axis()
            GeomTypes.eqFloatMargin = save
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
        this.modelRepos = GeomTypes.E
        this.movingRepos = GeomTypes.E
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

#if __name__ == '__main__':
#    app = wx.PySimpleApp()
#    app.MainLoop()
