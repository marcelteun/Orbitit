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
# -------------------------------------------------------------------

import math

from OpenGL import GLU, GL
from pyopengltk import OpenGLFrame

import Geom3D
import geomtypes


def axis_to_axis_rotation(a0, a1):
    """Get the rotation that is needed to rotate 1 axis into the another."""
    vec3_type = geomtypes.Vec3
    assert isinstance(a0, vec3_type) and isinstance(a1, vec3_type)
    if a0 == a1:
        # if both axis are in fact the same no roation is needed
        axis = geomtypes.UZ
        angle = 0
    if a0 == -a1:
        # if one axis should be rotated in its opposite axis, handle
        # separately, since the cross product will not work.
        # rotate pi around any vector that makes a straight angle with a0
        a2 = geomtypes.Vec3([i+0.5 for i in a1])
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
    def __init__(self, v0, v1, v2):
        self.v = [geomtypes.Vec3(v0), geomtypes.Vec3(v1), geomtypes.Vec3(v2)]
        self.N = None

    def normal(self):
        if self.N == None:
            n = (self.v[1] - self.v[0]).cross(self.v[2] - self.v[0])
            self.N = [n[0], n[1], n[2]]
            return self.N
        else:
            return self.N


class P2PCylinder:
    def __init__(self, radius=0.15, slices=12, stacks=1):
        self.quad = GLU.gluNewQuadric()
        self.radius = radius
        self.slices = slices
        self.stacks = stacks
        GLU.gluQuadricNormals(self.quad, GLU.GLU_SMOOTH)
        # GLU.gluQuadricTexture(self.quad, GL.GL_TRUE)

    def draw(self, v0=[0, 0, 0], v1=[0, 0, 1]):
        e = [v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]]
        eLen = math.sqrt(e[0]*e[0] + e[1]*e[1] + e[2]*e[2])
        if eLen == 0:
            return

        # if self.slices < 3: self.slices = 10

        # Rotate such that the edge v0-v1 points in the positive z-direction,
        # Then translate the scene such that v0 ends up in the origin.
        # angle = acos( e.(0,0,1) / eLen) , with . the dot product
        #       = acos( e[2]/eLen)
        # axis = (0,0,1) x e , with x the cross product
        #      = [-e[1], e[0], 0]
        GL.glPushMatrix()
        GL.glTranslatef(v0[0], v0[1], v0[2])
        GL.glRotatef(math.acos(e[2]/eLen) * Geom3D.Rad2Deg, -e[1], e[0], 0.)
        GLU.gluCylinder(self.quad, self.radius, self.radius,
                        eLen, self.slices, self.stacks)
        GL.glPopMatrix()


class VSphere:
    def __init__(self, radius=0.2, slices=12, stacks=12):
        self.quad = GLU.gluNewQuadric()
        self.radius = radius
        self.slices = slices
        self.stacks = stacks
        GLU.gluQuadricNormals(self.quad, GLU.GLU_SMOOTH)
        # GLU.gluQuadricTexture(self.quad, GL.GL_TRUE)

    def draw(self, v=[0, 0, 0]):
        GL.glPushMatrix()
        GL.glTranslatef(v[0], v[1], v[2])
        GLU.gluSphere(self.quad, self.radius, self.slices, self.stacks)
        GL.glPopMatrix()


class OglFrame(OpenGLFrame):
    def __init__(self, shape, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shape = shape
        self.cam_position = 5.0
        self.bgCol = [0.097656, 0.097656, 0.437500]  # midnightBlue
        self.cyl = P2PCylinder(radius=0.05)
        self.sphere = VSphere(radius=0.1)
        self.init = False
        self.first_frame = True
        # initial mouse position
        self.x_org = self.x = 0
        self.y_org = self.y = 0
        self.z_bac = self.z = 0
        self.mouse_left_pressed = False
        self.mouse_right_pressed = False
        self.z_scale = 1.0/100
        self.current_scale = 1.0
        self.r_scale = 0.8

        # these orientations are used internally and are related to the
        # rotation caused by the mouse
        # - model_orientation is used when calculating a new orientation. It
        #   expresses the rotation caused by the mouse, before calculating the
        #   new one.
        # - moving_orientation is the newly calculated rotation after a mouse
        #   indicated rotation is finished.
        self.model_orientation = geomtypes.E
        self.moving_orientation = geomtypes.E

        self.bind("<ButtonPress-1>", lambda e: self.on_rotate_start(e))
        self.bind("<ButtonRelease-1>", lambda e: self.on_rotate_stop(e))
        self.bind("<ButtonPress-3>", lambda e: self.on_zoom_start(e))
        self.bind("<ButtonRelease-3>", lambda e: self.on_zoom_stop(e))
        self.bind("<B3-Motion>", lambda e: self.on_mouse_move(e))
        self.bind("<B1-Motion>", lambda e: self.on_mouse_move(e))
        self.bind("<Configure>", lambda e: self.on_size(e))

    def initgl(self):
        width, height = self.winfo_width(), self.winfo_height()
        size = min(width, height)

        GL.glViewport(0, 0, size, size)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GLU.gluPerspective(45., 1.0, 1., 300.)

        GL.glTranslatef(0.0, 0.0, -self.cam_position)
        GL.glMatrixMode(GL.GL_MODELVIEW)

        self.model_mat_org = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
        self.init = True
        self.shape.glInit()

    def redraw(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        def xy_to_sphere_pos(x, y, w, h, r2):
            x, y = x - w/2, h/2 - y
            l2 = x * x + y * y
            if l2 < r2:
                sphere_pos = geomtypes.Vec3([x, y, math.sqrt(r2 - l2)])
            elif l2 > r2:
                scale = math.sqrt(r2/l2)
                sphere_pos = geomtypes.Vec3([scale*x, scale*y, 0])
            else:  # probably never happens (floats)
                sphere_pos = geomtypes.Vec3([x, y, 0])
            return sphere_pos

        if not self.init:
            self.initgl()
            self.init = True
        GL.glPushMatrix()
        self.shape.glDraw()
        GL.glPopMatrix()

        if self.x_org != 0 or self.y_org != 0:
            width, height = self.winfo_width(), self.winfo_height()
            edge_size = min(width, height)
            if height > width:
                x0 = self.x
                y0 = self.y - (height - edge_size)
                x1 = self.x_org
                y1 = self.y_org - (height - edge_size)
            else:
                x0 = self.x - (width - edge_size)
                y0 = self.y
                x1 = self.x_org - (width - edge_size)
                y1 = self.y_org
            r2 = float(edge_size * edge_size) / 4
            r2 = self.r_scale * self.r_scale * r2
            sphere_pos_1 = xy_to_sphere_pos(x0, y0, edge_size, edge_size, r2)
            sphere_pos_0 = xy_to_sphere_pos(x1, y1, edge_size, edge_size, r2)
            axis, angle = axis_to_axis_rotation(sphere_pos_0, sphere_pos_1)
            self.moving_orientation = geomtypes.Rot3(
                axis=axis, angle=angle) * self.model_orientation
            GL.glLoadMatrixd(self.model_mat_org)
            GL.glScalef(self.current_scale,
                        self.current_scale,
                        self.current_scale)
            geomtypes.set_eq_float_margin(1.0e-14)
            angle = Geom3D.Rad2Deg*self.moving_orientation.angle()
            axis = self.moving_orientation.axis()
            geomtypes.reset_eq_float_margin()
            GL.glRotatef(angle, axis[0], axis[1], axis[2])

        if self.z != self.z_bac:
            dZ = self.z - self.z_bac
            # map [min, max] onto [0, 2]
            # dZ' = (2/(max-min)) dZ + 1
            dZ = dZ*self.z_scale + 1.0
            self.current_scale = dZ * self.current_scale
            GL.glScalef(dZ, dZ, dZ)

        GL.glFlush()
        if not self.first_frame:
            self.tkSwapBuffers()
            return
        self.first_frame = False

    def reset_orientation(self):
        try:  # self.model_mat_org might not exist at an early stage
            GL.glLoadMatrixd(self.model_mat_org)
        except AttributeError:
            pass
        self.model_orientation = geomtypes.E
        self.moving_orientation = geomtypes.E
        self.current_scale = 1.0
        self.paint()

    def paint(self):
        self.redraw()

    def set_cam_position(self, distance):
        """
        Set the camera distance

        distance: camera distance, usually a positive nr. Note that the camera
                  is somewhere along the z-axis
        """
        self.cam_position = distance

    def on_zoom_start(self, event):
        self.mouse_right_pressed = True
        self.z = self.z_bac = event.y
        return "break"

    def on_zoom_stop(self, event):
        # we need to check self, because a mouse click in a window A on top of
        # self window can cause window A to be closed and the release button
        # event is captured here, while the was no capture here.
        if self.mouse_right_pressed:
            self.mouse_right_pressed = False
        self.z_bac = self.z = 0.0
        return "break"

    def on_rotate_start(self, event):
        self.mouse_left_pressed = True
        self.x_org, self.y_org = self.x, self.y = event.x, event.y
        return "break"

    def on_rotate_stop(self, event):
        # we need to check self, because a mouse click in a window A on top of
        # self window can cause window A to be closed and the release button
        # event is captured here, while the was no capture here.
        if self.mouse_left_pressed:
            self.mouse_left_pressed = False
            self.model_orientation = self.moving_orientation
        self.x_org, self.y_org = self.x, self.y = (0, 0)
        return "break"

    def on_mouse_move(self, event):
        if self.mouse_left_pressed:
            self.x, self.y = event.x, event.y
            self.paint()
        if self.mouse_right_pressed:
            self.z_bac = self.z
            self.z = event.y
            self.paint()
        return "break"

    def on_size(self, event):
        width, height = event.width, event.height
        size = min(width, height)
        GL.glViewport(0, 0, size, size)
        self.paint()

    def set_arc_ball_radius(self, r=0.8):
        self.r_scale = r


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
      - a function set_arc_ball_radius to set the relative radius of the sphere
        of the arc ball navigation. It shall except one radius parameter.
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

    def set_arc_ball_radius(this, R=0.8):
        this.canvas.set_arc_ball_radius(R=R)

    def onSize(this, event):
        this.canvas.onSize(event)
        print('Canvas window size:', this.canvasFrame.GetClientSize())

    def onCloseCanvas(this, event):
        print('onCloseCanvas')
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
