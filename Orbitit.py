#!/usr/bin/env python
#
# Copyright (C) 2010-2019 Marcel Tunnissen
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

import glue
import math
import os
import rgb
import re
import sys
import X3D
import Scenes3D
import Geom3D
import geomtypes
import geom_gui
import pprint
import tkinter as tk

from OpenGL import GL, GLU
#from OpenGL.GLU import *
#from OpenGL.GL import *
from tkinter import messagebox

DEG2RAD = Geom3D.Deg2Rad

DefaultScene = './scene_orbit.py'

def onSwitchFrontBack(gl_scane):
    if glGetIntegerv(GL_FRONT_FACE) == GL_CCW:
        glFrontFace(GL_CW)
    else:
        glFrontFace(GL_CCW)
    gl_scane.paint()

class OglFrame(Scenes3D.OglFrame):
    def __init__(self, shape):
        super().__init__(shape)

    def initgl(self):
        super().initgl()
        self.set_cam_position(15.0)

        #glShadeModel(GL_SMOOTH)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY);
        GL.glEnableClientState(GL.GL_NORMAL_ARRAY)

        matAmbient    = [0.2, 0.2, 0.2, 0.0]
        matDiffuse    = [0.1, 0.6, 0.0, 0.0]
        #matSpecular   = [0.2, 0.2, 0.2, 1.]
        matShininess  = 0.0
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_AMBIENT, matAmbient)
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_DIFFUSE, matDiffuse)
        #GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL_SPECULAR, matSpecular)
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_SHININESS, matShininess)

        lightPosition = [10.0, -30.0, -20.0, 0.0]
        lightAmbient  = [0.3, 0.3, 0.3, 1.0]
        lightDiffuse  = [0.5, 0.5, 0.5, 1.0]
        # disable specular part:
        lightSpecular = [0., 0., 0., 1.]
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, lightPosition)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, lightAmbient)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, lightDiffuse)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, lightSpecular)
        GL.glEnable(GL.GL_LIGHT0)

        lightPosition = [-30.0, 0.0, -20.0, 0.0]
        lightAmbient  = [0.0, 0.0, 0.0, 1.]
        lightDiffuse  = [0.08, 0.08, 0.08, 1.]
        lightSpecular = [0.0, 0.0, 0.0, 1.]
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_POSITION, lightPosition)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_AMBIENT, lightAmbient)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_DIFFUSE, lightDiffuse)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_SPECULAR, lightSpecular)
        GL.glEnable(GL.GL_LIGHT1)

        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glLightModeli(GL.GL_LIGHT_MODEL_TWO_SIDE, GL.GL_TRUE)
        GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        GL.glClearColor(self.bgCol[0], self.bgCol[1], self.bgCol[2], 0)

    def setBgCol(this, bgCol):
        """rgb in value between 0 and 1"""
        this.bgCol = bgCol
        GL.glClearColor(bgCol[0], bgCol[1], bgCol[2], 0)

    def getBgCol(this):
        """rgb in value between 0 and 1"""
        return this.bgCol

    def redraw(self):
        super().redraw()
        self.shape.glDraw()


class MainWindow(tk.Frame):
    wildcard = "OFF shape (*.off)|*.off| Python shape (*.py)|*.py"

    def __init__(self, root, ogl_frame, shape, p_args):
        super().__init__(root)
        self.root = root
        self.context_created = False
        self.add_menu_bar()
        self.add_scene_canvas(ogl_frame, shape)
        self.add_status_bar()
        root.protocol('WM_DELETE_WINDOW', self.on_quit)
        self.export_dir = '.'
        self.import_dir = '.'
        self.scene_dir = '.'
        #self.viewSettingsWindow = None
        #self.colourSettingsWindow = None
        #self.transformSettingsWindow = None

        if len(p_args) > 0 and (p_args[0][-4:] == '.off' or
                                p_args[0][-3:] == '.py'):
            self.open_file(p_args[0])
        #self.Show(True)
        #self.Bind(wx.EVT_CLOSE, self.onClose)
        #self.keySwitchFronBack = wx.NewId()
        #ac = [
        #    (wx.ACCEL_NORMAL, wx.WXK_F3, self.keySwitchFronBack)
        #]
        #self.Bind(wx.EVT_MENU, self.onKeyDown, id=self.keySwitchFronBack)
        #self.SetAcceleratorTable(wx.AcceleratorTable(ac))

    def tkCreateContext(self):
        super().tkCreateContext()
        self.context_created = True

    def add_menu_bar(self):
        self.menu_bar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        file_menu = self.create_file_menu("File", 0)
        file_menu.grid(row=0, column=0)
        self.root.bind('<Alt_L><f>',
                       lambda e: file_menu.event_generate('<<Invoke>>'))
        edit_menu = self.create_edit_menu("Edit", 0)
        edit_menu.grid(row=0, column=1)
        self.root.bind('<Alt_L><e>',
                       lambda e: edit_menu.event_generate('<<Invoke>>'))
        view_menu = self.create_view_menu("View", 0)
        view_menu.grid(row=0, column=2)
        self.root.bind('<Alt_L><v>',
                       lambda e: view_menu.event_generate('<<Invoke>>'))
        tools_menu = self.create_tools_menu("Tools", 0)
        tools_menu.grid(row=0, column=3)
        self.root.bind('<Alt_L><t>',
                       lambda e: tools_menu.event_generate('<<Invoke>>'))

        # bind the buttons (in alphabetical order)
        self.root.bind("<Control-a>", lambda e: self.on_add(e))
        self.root.bind("<Control-c>", lambda e: self.on_colour_settings(e))
        self.root.bind("<Control-d>", lambda e: self.on_dome(1, e))
        self.root.bind("<Control-e>", lambda e: self.on_save_as_off(e))
        self.root.bind("<Control-m>", lambda e: self.on_dome(2, e))
        self.root.bind("<Control-o>", lambda e: self.on_open(e))
        self.root.bind("<Control-p>", lambda e: self.on_save_as_ps(e))
        self.root.bind("<Control-q>", lambda e: self.on_quit(e))
        self.root.bind("<Control-r>", lambda e: self.on_reload(e))
        self.root.bind("<Control-t>", lambda e: self.on_transform(e))
        self.root.bind("<Control-v>", lambda e: self.on_view_settings(e))
        self.root.bind("<Control-w>", lambda e: self.on_save_as_wrl(e))
        self.root.bind("<Control-y>", lambda e: self.on_save_as_py(e))

        self.root.bind("<F5>", lambda e: self.on_reset_view(e))

        self.menu_bar.grid(row=0, column=0, sticky=tk.W + tk.E)

    def create_file_menu(self, text, underline):
        menu_button = tk.Menubutton(self.menu_bar,
                                    text=text,
                                    underline=underline)
        menu_file = tk.Menu(menu_button, tearoff=False)
        menu_file.add_command(label="Open",
                              underline=0,
                              accelerator="Ctrl-O",
                              command=self.on_open)
        menu_file.add_command(label="Reload",
                              underline=0,
                              accelerator="Ctrl-R",
                              command=self.on_reload)
        menu_file.add_command(label="Add",
                              underline=0,
                              accelerator="Ctrl-A",
                              command=self.on_add)

        menu_export = tk.Menu(menu_file, tearoff=False)
        menu_export.add_command(label="Python",
                                underline=1,
                                accelerator="Ctrl-Y",
                                command=self.on_save_as_py)
        menu_export.add_command(label="Off",
                                underline=0,
                                accelerator="Ctrl-E",
                                command=self.on_save_as_off)
        menu_export.add_command(label="PS",
                                underline=0,
                                accelerator="Ctrl-P",
                                command=self.on_save_as_ps)
        menu_export.add_command(label="VRML",
                                underline=0,
                                accelerator="Ctrl-W",
                                command=self.on_save_as_wrl)
        menu_file.add_cascade(label='Export', menu=menu_export, underline=0)

        menu_file.add_separator()
        menu_file.add_command(label="Quit",
                              underline=0,
                              accelerator="Ctrl-Q",
                              command=self.on_quit)

        menu_button.config(menu=menu_file)
        return menu_button

    def create_edit_menu(self, text, underline):
        menu_button = tk.Menubutton(self.menu_bar,
                                    text=text,
                                    underline=underline)
        menu_edit = tk.Menu(menu_button, tearoff=False)

        menu_edit.add_command(label="View Settings",
                              underline=0,
                              accelerator="Ctrl-V",
                              command=self.on_view_settings)
        menu_edit.add_command(label="Colours",
                              underline=0,
                              accelerator="Ctrl-C",
                              command=self.on_colour_settings)
        menu_edit.add_command(label="Transform",
                              underline=0,
                              accelerator="Ctrl-T",
                              command=self.on_transform)

        menu_button.config(menu=menu_edit)
        return menu_button

    def create_view_menu(self, text, underline):
        menu_button = tk.Menubutton(self.menu_bar,
                                    text=text,
                                    underline=underline)
        menu_view = tk.Menu(menu_button, tearoff=False)

        menu_view.add_command(label="Reset",
                              underline=0,
                              accelerator="F5",
                              command=self.on_reset_view)
        menu_view.add_command(label="Scene...",
                              underline=0,
                              command=self.on_open_scene)

        menu_button.config(menu=menu_view)
        return menu_button

    def create_tools_menu(self, text, underline):
        menu_button = tk.Menubutton(self.menu_bar,
                                    text=text,
                                    underline=underline)
        menu_tools = tk.Menu(menu_button, tearoff=False)

        menu_tools.add_command(label="Dome Level 1",
                               underline=11,
                               accelerator="Ctrl-D",
                               command=lambda: self.on_dome(1))
        menu_tools.add_command(label="Dome Level 2",
                               accelerator="Ctrl-M",
                               underline=11,
                               command=lambda: self.on_dome(2))

        menu_button.config(menu=menu_tools)
        return menu_button

    def add_scene_canvas(self, ogl_frame, shape):
        self.ogl_frame = ogl_frame(shape)
        self.ogl_frame.grid(row=1, column=0, sticky=tk.N + tk.E + tk.S + tk.W)
        self.root.grid_rowconfigure(1, weight=1, minsize=300)
        self.root.grid_columnconfigure(0, weight=1, minsize=300)
        self.ogl_frame.after(100, lambda: self.ogl_frame.printContext(extns=False))

    def add_status_bar(self):
        self.status_str = tk.StringVar()
        self.status_bar = tk.Label(root, textvariable=self.status_str,
                                   bd=1, relief=tk.SUNKEN)
        self.status_bar.grid(row=2, column=0, sticky=tk.W + tk.E)

    def on_reload(self, e=None):
        print('TODO: on_reload')
        if self.currentFile != None:
            self.open_file(self.currentFile)
        elif self.currentScene != None:
            self.set_scene(self.currentScene)

    def on_open(self, e=None):
        print("TODO: on_open.")
        dlg = wx.FileDialog(self, 'New: Choose a file',
                self.import_dir, '', self.wildcard, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            if dirname != None:
                filename = os.path.join(dirname, filename)
            self.open_file(filename)
        dlg.Destroy()

    def read_shape_file(self, filename):
        isOffModel = filename[-3:] == 'off'
        print("opening file:", filename)
        fd = open(filename, 'r')
        if isOffModel:
            shape = Geom3D.read_off_file(fd, recreateEdges=True)
        else:
            assert filename[-2:] == 'py'
            shape = Geom3D.read_py_file(fd)
        self.update_status_bar("file opened")
        fd.close()
        return shape

    def open_file(self, filename):
        self.close_current_scene()
        dirname = os.path.dirname(filename)
        if dirname != "":
            self.import_dir = dirname
        try:
            shape = self.read_shape_file(filename)
        except AssertionError:
            self.update_status_bar("ERROR reading file")
            raise
        if isinstance(shape, Geom3D.CompoundShape):
            # convert to SimpleShape first, since adding to IsometricShape
            # will not work.
            shape = shape.simple_shape
        # Create a compound shape to be able to add shapes later.
        shape = Geom3D.CompoundShape([shape], name=filename)
        self.set_shape(shape)
        # overwrite the view properties, if the shape doesn't have any
        # faces and would be invisible to the user otherwise
        if len(shape.getFaceProperties()['Fs']) == 0 and (
            self.get_shape().getVertexProperties()['radius'] <= 0
        ):
            self.get_shape().setVertexProperties(radius=0.05)
        self.root.title('%s' % os.path.basename(filename))
        # Save for reload:
        self.currentFile = filename
        self.currentScene = None

    def on_add(self, e=None):
        print("TODO on_add")
        dlg = wx.FileDialog(self, 'Add: Choose a file',
                self.import_dir, '', self.wildcard, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            isOffModel = filename[-3:] == 'off'
            self.import_dir  = dlg.GetDirectory()
            print("adding file:", filename)
            fd = open(os.path.join(self.import_dir, filename), 'r')
            if isOffModel:
                shape = Geom3D.read_off_file(fd, recreateEdges = True)
            else:
                shape = Geom3D.read_py_file(fd)
            if isinstance(shape, Geom3D.CompoundShape):
                # convert to SimpleShape first, since adding a IsometricShape
                # will not work.
                shape = shape.simple_shape
            try:
                self.get_shape().addShape(shape)
            except AttributeError:
                print("warning: cannot 'add' a shape to self scene, use 'File->Open' instead")
            self.update_status_bar("OFF file added")
            fd.close()
            # TODO: set better title
            self.root.title('Added: %s' % os.path.basename(filename))
        dlg.Destroy()

    def on_save_as_py(self, e=None):
        print("TODO: on_save_as_py")
        dlg = wx.FileDialog(self, 'Save as .py file',
            self.export_dir, '', '*.py',
            style = wx.SAVE | wx.OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            filename = dlg.GetFilename()
            self.export_dir  = filepath.rsplit('/', 1)[0]
            NameExt = filename.split('.')
            if len(NameExt) == 1:
                filename = '%s.py' % filename
            elif NameExt[-1].lower() != 'py':
                if NameExt[-1] != '':
                    filename = '%s.py' % filename
                else:
                    filename = '%spy' % filename
            fd = open(filepath, 'w')
            print("writing to file %s" % filepath)
            # TODO precision through setting:
            shape = self.get_shape()
            shape.name = filename
            shape.saveFile(fd)
            self.update_status_bar("Python file written")
        dlg.Destroy()

    def on_save_as_off(self, e=None):
        print('TODO: on_save_as_off')
        dlg = ExportOffDialog(self, wx.ID_ANY, 'OFF settings')
        fileChoosen = False
        while not fileChoosen:
            if dlg.ShowModal() == wx.ID_OK:
                extraInfo = dlg.getExtraInfo()
                cleanUp = dlg.getCleanUp()
                precision = dlg.getPrecision()
                margin = dlg.getFloatMargin()
                fileDlg = wx.FileDialog(self, 'Save as .off file',
                    self.export_dir, '', '*.off',
                    wx.SAVE | wx.OVERWRITE_PROMPT
                )
                fileChoosen = fileDlg.ShowModal() == wx.ID_OK
                if fileChoosen:
                    filepath = fileDlg.GetPath()
                    filename = fileDlg.GetFilename()
                    self.export_dir  = filepath.rsplit('/', 1)[0]
                    NameExt = filename.split('.')
                    if len(NameExt) == 1:
                        filename = '%s.off' % filename
                    elif NameExt[-1].lower() != 'off':
                        if NameExt[-1] != '':
                            filename = '%s.off' % filename
                        else:
                            filename = '%soff' % filename
                    fd = open(filepath, 'w')
                    print("writing to file %s" % filepath)
                    shape = self.get_shape()
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    if cleanUp:
                        shape = shape.cleanShape(margin)
                    fd.write(shape.to_off_str(precision, extraInfo))
                    print("OFF file written")
                    self.update_status_bar("OFF file written")
                    fd.close()
                else:
                    dlg.Show()
                fileDlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def on_save_as_ps(self, e=None):
        print("TODO: on_save_as_ps")
        dlg = ExportPsDialog(self, wx.ID_ANY, 'PS settings')
        fileChoosen = False
        while not fileChoosen:
            if dlg.ShowModal() == wx.ID_OK:
                scalingFactor = dlg.getScaling()
                precision = dlg.getPrecision()
                margin = dlg.getFloatMargin()
                assert (scalingFactor >= 0 and scalingFactor != None)
                fileDlg = wx.FileDialog(self, 'Save as .ps file',
                    self.export_dir, '', '*.ps',
                    style = wx.SAVE | wx.OVERWRITE_PROMPT
                )
                fileChoosen = fileDlg.ShowModal() == wx.ID_OK
                if fileChoosen:
                    filepath = fileDlg.GetPath()
                    filename = fileDlg.GetFilename()
                    self.export_dir  = filepath.rsplit('/', 1)[0]
                    NameExt = filename.split('.')
                    if len(NameExt) == 1:
                        filename = '%s.ps' % filename
                    elif NameExt[-1].lower() != 'ps':
                        if NameExt[-1] != '':
                            filename = '%s.ps' % filename
                        else:
                            filename = '%sps' % filename
                    # Note: if file exists is part of file dlg...
                    fd = open(filepath, 'w')
                    print("writing to file %s" % filepath)
                    shape = self.get_shape()
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    shape = shape.cleanShape(margin)
                    try:
                        fd.write(shape.to_ps_pieces_str(
                            scaling=scalingFactor,
                            precision=precision,
                            margin=math.pow(10, -margin)))
                        self.update_status_bar("PS file written")
                    except Geom3D.PrecisionError:
                        self.update_status_bar(
                            "Precision error, try to decrease float margin")

                    fd.close()
                else:
                    dlg.Show()
                fileDlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def on_save_as_wrl(self, e=None):
        print("TODO: on_save_as_wrl")
        dlg = wx.FileDialog(self,
            'Save as .vrml file', self.export_dir, '', '*.wrl',
            style = wx.SAVE | wx.OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = fileDlg.GetPath()
            filename = dlg.GetFilename()
            self.export_dir  = filepath.rsplit('/', 1)[0]
            NameExt = filename.split('.')
            if len(NameExt) == 1:
                filename = '%s.wrl' % filename
            elif NameExt[-1].lower() != 'wrl':
                if NameExt[-1] != '':
                    filename = '%s.wrl' % filename
                else:
                    filename = '%swrl' % filename
            fd = open(filepath, 'w')
            print("writing to file %s" % filepath)
            # TODO precision through setting:
            r = self.get_shape().getEdgeProperties()['radius']
            x3dObj = self.get_shape().toX3dDoc(edgeRadius = r)
            x3dObj.setFormat(X3D.VRML_FMT)
            fd.write(x3dObj.toStr())
            self.update_status_bar("VRML file written")
            fd.close()
        dlg.Destroy()

    def on_view_settings(self, e=None):
        print("TODO: on_view_settings")
        if self.viewSettingsWindow == None:
            self.viewSettingsWindow = ViewSettingsWindow(self.ogl_frame,
                None, wx.ID_ANY,
                title = 'View Settings',
                size = (394, 300)
            )
            self.viewSettingsWindow.Bind(wx.EVT_CLOSE, self.onViewSettingsClose)
        else:
            self.viewSettingsWindow.SetFocus()
            self.viewSettingsWindow.Raise()

    def on_colour_settings(self, e=None):
        if not self.colourSettingsWindow is None:
            # Don't reuse, the colours might be wrong after loading a new model
            self.colourSettingsWindow.Destroy()
        self.colourSettingsWindow = ColourSettingsWindow(
            self.ogl_frame, 5, None, wx.ID_ANY,
            title = 'Colour Settings',
        )
        self.colourSettingsWindow.Bind(wx.EVT_CLOSE, self.onColourSettingsClose)

    def on_transform(self, e=None):
        if self.transformSettingsWindow == None:
            self.transformSettingsWindow = TransformSettingsWindow(
                self.ogl_frame(), None, wx.ID_ANY,
                title = 'Transform Settings',
            )
            self.transformSettingsWindow.Bind(wx.EVT_CLOSE, self.onTransformSettingsClose)
        else:
            self.transformSettingsWindow.SetFocus()
            self.transformSettingsWindow.Raise()

    def on_dome(self, level, e=None):
        print("TODO: on_dome level", level)
        shape = self.get_shape().getDome(level)
        if shape is not None:
            self.set_shape(shape)
            self.root.title("Dome %s" % self.GetTitle())

    def on_open_scene(self, e=None):
        wildcard = "Scene plugin (Scene_*.py)|?cene_*.py"
        dlg = wx.FileDialog(self, 'New: Choose a Scene',
                self.scene_dir, '', wildcard, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            print('filepath', filepath)
            self.scene_dir = filepath.rsplit('/', 1)[0]
            print('scene_dir', self.scene_dir)
            shape = self.read_scene_file(filepath)
        dlg.Destroy()

    def read_scene_file(self, filename):
        print("Starting scene", filename)
        fd = open(filename, 'r')
        ed = {}
        exec(fd.read(), ed)
        scene = { 'label': ed['TITLE'],
                 'class': ed['Scene']}
        self.set_scene(scene)

    def set_scene(self, scene):
        self.close_current_scene()
        print('Switch to scene "%s"' % scene['label'])
        self.ogl_frame = scene['class']()
        self.root.title(scene['label'])
        self.ogl_frame.reset_orientation()
        try:
            self.viewSettingsWindow.reBuild()
        except AttributeError:
            pass
        # save for reload:
        self.currentScene = scene
        self.currentFile = None

    def on_reset_view(self, e=None):
        self.ogl_frame().reset_orientation()

    def close_current_scene(self):
        print("print: TODO: only for destroying scenes control window")
        return
        if self.ogl_frame is not None:
            #self.ogl_frame.close()
            del self.ogl_frame
            self.ogl_frame = None

    def update_status_bar(self, str):
        self.status_str.set(str)

    def on_quit(self, e=None):
        if messagebox.askokcancel('Quit?', 'Are you sure you want to quit?'):
            self.master.destroy()
            sys.exit()

#
#    def onViewSettingsClose(this, event):
#        this.viewSettingsWindow.Destroy()
#        this.viewSettingsWindow = None
#
#    def onColourSettingsClose(this, event):
#        this.colourSettingsWindow.Destroy()
#        this.colourSettingsWindow = None
#
#    def onTransformSettingsClose(this, event):
#        this.transformSettingsWindow.Destroy()
#        this.transformSettingsWindow = None
#
#    def onClose(this, event):
#        print('main onclose')
#        if this.viewSettingsWindow != None:
#            this.viewSettingsWindow.Close()
#        if this.colourSettingsWindow != None:
#            this.colourSettingsWindow.Close()
#        if this.transformSettingsWindow != None:
#            this.transformSettingsWindow.Close()
#        this.Destroy()
#
#    def onKeyDown(this, e):
#        id = e.GetId()
#        if id == this.keySwitchFronBack:
#            onSwitchFrontBack(this.panel.getCanvas())

    def set_shape(self, shape):
        """Set a new shape to be shown with the current viewing settings

        shape: the new shape. This will refresh the canvas.
        """
        org_shape = self.get_shape()
        self.ogl_frame.shape = shape
        if org_shape:
            # Use all the vertex settings except for Vs, i.e. keep the view
            # vertex settings the same.
            org_vs_settings = org_shape.getVertexProperties()
            del org_vs_settings['Vs']
            del org_vs_settings['Ns']
            self.ogl_frame.shape.setVertexProperties(org_vs_settings)
            # Use all the edge settings except for Es
            org_es_settings = org_shape.getEdgeProperties()
            del org_es_settings['Es']
            self.ogl_frame.shape.setEdgeProperties(org_es_settings)
            # Use only the 'drawFaces' setting:
            org_fs_settings = {
                    'drawFaces': org_shape.getFaceProperties()['drawFaces']
                }
            self.ogl_frame.shape.setFaceProperties(org_fs_settings)
            del org_shape
        # if the shape generates the normals itself:
        # TODO: handle that self.Ns is set correctly, i.e. normalised
        if shape.generateNormals:
            GL.glDisable(GL.GL_NORMALIZE)
        else:
            GL.glEnable(GL.GL_NORMALIZE)
        if self.context_created:
            self.ogl_frame.redraw()
        self.update_status_bar("Shape Updated")

    def get_shape(self):
        """Return the current shape object"""
        return None if self.ogl_frame is not None else self.ogl_frame.shape


#class ColourSettingsWindow(wx.Frame):
#    def __init__(this, canvas, width, *args, **kwargs):
#        wx.Frame.__init__(this, *args, **kwargs)
#        this.canvas    = canvas
#        this.col_width = width
#        this.statusBar = this.CreateStatusBar()
#        this.panel     = wx.Panel(this, wx.ID_ANY)
#        this.cols = this.canvas.shape.getFaceProperties()['colors']
#        # take a copy for reset
#        this.org_cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in this.cols]
#        this.addContents()
#
#    def addContents(this):
#        this.colSizer = wx.BoxSizer(wx.VERTICAL)
#
#        this.selColGuis = []
#        i = 0
#        shape_idx = 0
#        # assume compound shape
#        for shape_cols in this.cols:
#            # use one colour select per colour for each sub-shape
#            added_cols = []
#            col_idx = 0
#            for col in shape_cols[0]:
#                wxcol = wx.Colour(256*col[0], 256*col[1], 256*col[2])
#                if not wxcol in added_cols:
#                    if i % this.col_width == 0:
#                        selColSizerRow = wx.BoxSizer(wx.HORIZONTAL)
#                        this.colSizer.Add(selColSizerRow, 0, wx.EXPAND)
#                    this.selColGuis.append(
#                        wx.ColourPickerCtrl(
#                            this.panel, wx.ID_ANY, wxcol))
#                    this.panel.Bind(wx.EVT_COLOURPICKER_CHANGED, this.onColSel)
#                    selColSizerRow.Add(this.selColGuis[-1], 0, wx.EXPAND)
#                    i += 1
#                    # connect GUI to shape_idx and col_idx
#                    this.selColGuis[-1].my_shape_idx = shape_idx
#                    this.selColGuis[-1].my_cols = [col_idx]
#                    # connect wxcolour to GUI
#                    wxcol.my_gui = this.selColGuis[-1]
#                    added_cols.append(wxcol)
#                else:
#                    gui = added_cols[added_cols.index(wxcol)].my_gui
#                    # must be same shape_id
#                    gui.my_cols.append(col_idx)
#                col_idx += 1
#            shape_idx += 1
#
#        this.noOfCols = i
#        this.Guis = []
#
#        this.subSizer = wx.BoxSizer(wx.HORIZONTAL)
#        this.colSizer.Add(this.subSizer)
#
#        this.Guis.append(wx.Button(this.panel, label='Cancel'))
#        this.Guis[-1].Bind(wx.EVT_BUTTON, this.onCancel)
#        this.subSizer.Add(this.Guis[-1], 0, wx.EXPAND)
#
#        this.Guis.append(wx.Button(this.panel, label='Reset'))
#        this.Guis[-1].Bind(wx.EVT_BUTTON, this.onReset)
#        this.subSizer.Add(this.Guis[-1], 0, wx.EXPAND)
#
#        this.Guis.append(wx.Button(this.panel, label='Done'))
#        this.Guis[-1].Bind(wx.EVT_BUTTON, this.onDone)
#        this.subSizer.Add(this.Guis[-1], 0, wx.EXPAND)
#
#        this.panel.SetSizer(this.colSizer)
#        this.panel.SetAutoLayout(True)
#        this.panel.Layout()
#        this.Show(True)
#
#    def onReset(this, e):
#        for colgui in this.selColGuis:
#             shape_idx = colgui.my_shape_idx
#             col_idx = colgui.my_cols[0]
#             c = this.org_cols[shape_idx][0][col_idx]
#             wxcol = wx.Colour(256*c[0], 256*c[1], 256*c[2])
#             colgui.SetColour(wxcol)
#        this.cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in this.org_cols]
#        this.updatShapeColours()
#
#    def onCancel(this, e):
#        this.cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in this.org_cols]
#        this.updatShapeColours()
#        this.Close()
#
#    def onDone(this, e):
#        this.Close()
#
#    def onColSel(this, e):
#        wxcol = e.GetColour().Get()
#        col = (float(wxcol[0])/256, float(wxcol[1])/256, float(wxcol[2])/256)
#        gui_id = e.GetId()
#        for gui in this.selColGuis:
#            if gui.GetId() == gui_id:
#                shape_cols = this.cols[gui.my_shape_idx][0]
#                for col_idx in gui.my_cols:
#                    shape_cols[col_idx] = col
#                this.updatShapeColours()
#
#    def updatShapeColours(this):
#        this.canvas.shape.setFaceProperties(colors=this.cols)
#        this.canvas.paint()
#
#    def close(this):
#        for Gui in this.Guis:
#            Gui.Destroy()
#
#class TransformSettingsWindow(wx.Frame):
#    def __init__(this, canvas, *args, **kwargs):
#        wx.Frame.__init__(this, *args, **kwargs)
#        this.canvas    = canvas
#        this.statusBar = this.CreateStatusBar()
#        this.panel     = wx.Panel(this, wx.ID_ANY)
#        this.addContents()
#        this.orgVs = this.canvas.shape.getVertexProperties()['Vs']
#        this.org_orgVs = this.orgVs # for cancel
#        this.set_status("")
#
#    def addContents(this):
#        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
#
#        this.rotateSizer = geom_gui.AxisRotateSizer(
#            this.panel,
#            this.on_rot,
#            min_angle=-180,
#            max_angle=180,
#            initial_angle=0
#        )
#        this.mainSizer.Add(this.rotateSizer)
#
#        # TODO: Add scale to transform
#        # TODO: Add reflection
#
#        this.Guis = []
#
#        this.subSizer = wx.BoxSizer(wx.HORIZONTAL)
#        this.mainSizer.Add(this.subSizer)
#
#        this.Guis.append(wx.Button(this.panel, label='Apply'))
#        this.Guis[-1].Bind(wx.EVT_BUTTON, this.onApply)
#        this.subSizer.Add(this.Guis[-1], 0, wx.EXPAND)
#
#        this.Guis.append(wx.Button(this.panel, label='Cancel'))
#        this.Guis[-1].Bind(wx.EVT_BUTTON, this.onCancel)
#        this.subSizer.Add(this.Guis[-1], 0, wx.EXPAND)
#
#        this.Guis.append(wx.Button(this.panel, label='Reset'))
#        this.Guis[-1].Bind(wx.EVT_BUTTON, this.onReset)
#        this.subSizer.Add(this.Guis[-1], 0, wx.EXPAND)
#
#        this.Guis.append(wx.Button(this.panel, label='Done'))
#        this.Guis[-1].Bind(wx.EVT_BUTTON, this.onDone)
#        this.subSizer.Add(this.Guis[-1], 0, wx.EXPAND)
#
#        this.panel.SetSizer(this.mainSizer)
#        this.panel.SetAutoLayout(True)
#        this.panel.Layout()
#        this.Show(True)
#
#    def on_rot(self, angle, axis):
#        if Geom3D.eq(axis.norm(), 0):
#            this.set_status("Please define a proper axis")
#            return
#        transform = geomtypes.Rot3(angle=DEG2RAD*angle, axis=axis)
#        # Assume compound shape
#        newVs = [
#            [transform * geomtypes.Vec3(v) for v in shapeVs] for shapeVs in this.orgVs]
#        this.canvas.shape.setVertexProperties(Vs=newVs)
#        this.canvas.paint()
#        this.set_status("Use 'Apply' to define a subsequent transform")
#
#    def onApply(this, e=None):
#        this.orgVs = this.canvas.shape.getVertexProperties()['Vs']
#        # reset the angle
#        this.rotateSizer.set_angle(0)
#        this.set_status("applied, now you can define another axis")
#
#    def onReset(this, e=None):
#        this.canvas.shape.setVertexProperties(Vs=this.org_orgVs)
#        this.canvas.paint()
#        this.orgVs = this.org_orgVs
#
#    def onCancel(this, e=None):
#        this.onReset()
#        this.Close()
#
#    def onDone(this, e):
#        this.Close()
#
#    def close(this):
#        for Gui in this.Guis:
#            Gui.Destroy()
#
#    def set_status(this, str):
#        this.statusBar.SetStatusText(str)
#
#class ViewSettingsWindow(wx.Frame):
#    def __init__(this, canvas, *args, **kwargs):
#        wx.Frame.__init__(this, *args, **kwargs)
#        this.canvas    = canvas
#        this.statusBar = this.CreateStatusBar()
#        this.panel     = wx.Panel(this, wx.ID_ANY)
#        this.addContents()
#
#    def addContents(this):
#        this.ctrlSizer = ViewSettingsSizer(this, this.panel, this.canvas)
#        if this.canvas.shape.dimension == 4:
#            this.setDefaultSize((413, 791))
#        else:
#            this.setDefaultSize((380, 414))
#        this.panel.SetSizer(this.ctrlSizer)
#        this.panel.SetAutoLayout(True)
#        this.panel.Layout()
#        this.Show(True)
#
#    # move to general class
#    def setDefaultSize(this, size):
#        this.SetMinSize(size)
#        # Needed for Dapper, not for Feisty:
#        # (I believe it is needed for Windows as well)
#        this.SetSize(size)
#
#    def reBuild(this):
#        # Doesn't work out of the box (Guis are not destroyed...):
#        #this.ctrlSizer.Destroy()
#        this.ctrlSizer.close()
#        this.addContents()
#
#    def update_status_bar(this, str):
#        this.statusBar.SetStatusText(str)
#
#class ViewSettingsSizer(wx.BoxSizer):
#    cull_show_none  = 'Hide'
#    cull_show_both  = 'Show Front and Back Faces'
#    cull_show_front = 'Show Only Front Face'
#    cull_show_back  = 'Show Only Back Face'
#    def __init__(this, parentWindow, parentPanel, canvas, *args, **kwargs):
#        """
#        Create a sizer with view settings.
#
#        parentWindow: the parentWindow object. This is used to update de
#                      status string in the status bar. The parent window is
#                      supposed to contain a function update_status_bar for this
#                      to work.
#        parentPanel: The panel to add all control widgets to.
#        canvas: An interactive 3D canvas object. This object is supposed to
#                have a shape field that points to the shape object that is
#                being viewed.
#        """
#
#        this.Guis = []
#        this.Boxes = []
#        wx.BoxSizer.__init__(this, wx.VERTICAL, *args, **kwargs)
#        this.canvas       = canvas
#        this.parentWindow = parentWindow
#        this.parentPanel  = parentPanel
#        # Show / Hide vertices
#        vProps            = canvas.shape.getVertexProperties()
#        this.vR           = vProps['radius']
#        this.vOptionsLst  = ['hide', 'show']
#        if this.vR > 0:
#            default = 1 # key(1) = 'show'
#        else:
#            default = 0 # key(0) = 'hide'
#        this.vOptionsGui  = wx.RadioBox(this.parentPanel,
#            label = 'Vertex Options',
#            style = wx.RA_VERTICAL,
#            choices = this.vOptionsLst
#        )
#        this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onVOption, id = this.vOptionsGui.GetId())
#        this.vOptionsGui.SetSelection(default)
#        # Vertex Radius
#        nrOfSliderSteps   = 40
#        this.vRadiusMin   = 0.01
#        this.vRadiusMax   = 0.100
#        this.vRadiusScale = 1.0 / this.vRadiusMin
#        s = (this.vRadiusMax - this.vRadiusMin) * this.vRadiusScale
#        if int(s) < nrOfSliderSteps:
#            this.vRadiusScale = (this.vRadiusScale * nrOfSliderSteps) / s
#        this.vRadiusGui = wx.Slider(this.parentPanel,
#            value = this.vRadiusScale * this.vR,
#            minValue = this.vRadiusScale * this.vRadiusMin,
#            maxValue = this.vRadiusScale * this.vRadiusMax,
#            style = wx.SL_HORIZONTAL
#        )
#        this.Guis.append(this.vRadiusGui)
#        this.parentPanel.Bind(wx.EVT_SLIDER, this.onVRadius, id = this.vRadiusGui.GetId())
#        this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Vertex radius'))
#        vRadiusSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
#        # disable if vertices are hidden anyway:
#        if default != 1:
#            this.vRadiusGui.Disable()
#        # Vertex Colour
#        this.vColorGui = wx.Button(this.parentPanel, wx.ID_ANY, "Colour")
#        this.Guis.append(this.vColorGui)
#        this.parentPanel.Bind(wx.EVT_BUTTON, this.onVColor, id = this.vColorGui.GetId())
#        # Show / hide edges
#        eProps           = canvas.shape.getEdgeProperties()
#        this.eR          = eProps['radius']
#        this.eOptionsLst = ['hide', 'as cylinders', 'as lines']
#        if eProps['drawEdges']:
#            if this.vR > 0:
#                default = 1 # key(1) = 'as cylinders'
#            else:
#                default = 2 # key(2) = 'as lines'
#        else:
#            default     = 0 # key(0) = 'hide'
#        this.eOptionsGui = wx.RadioBox(this.parentPanel,
#            label = 'Edge Options',
#            style = wx.RA_VERTICAL,
#            choices = this.eOptionsLst
#        )
#        this.Guis.append(this.eOptionsGui)
#        this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onEOption, id = this.eOptionsGui.GetId())
#        this.eOptionsGui.SetSelection(default)
#        # Edge Radius
#        nrOfSliderSteps   = 40
#        this.eRadiusMin   = 0.008
#        this.eRadiusMax   = 0.08
#        this.eRadiusScale = 1.0 / this.eRadiusMin
#        s = (this.eRadiusMax - this.eRadiusMin) * this.eRadiusScale
#        if int(s) < nrOfSliderSteps:
#            this.eRadiusScale = (this.eRadiusScale * nrOfSliderSteps) / s
#        this.eRadiusGui = wx.Slider(this.parentPanel,
#            value = this.eRadiusScale * this.eR,
#            minValue = this.eRadiusScale * this.eRadiusMin,
#            maxValue = this.eRadiusScale * this.eRadiusMax,
#            style = wx.SL_HORIZONTAL
#        )
#        this.Guis.append(this.eRadiusGui)
#        this.parentPanel.Bind(wx.EVT_SLIDER, this.onERadius, id = this.eRadiusGui.GetId())
#        this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Edge radius'))
#        eRadiusSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
#        # disable if edges are not drawn as scalable items anyway:
#        if default != 1:
#            this.eRadiusGui.Disable()
#        # Edge Colour
#        this.eColorGui = wx.Button(this.parentPanel, wx.ID_ANY, "Colour")
#        this.Guis.append(this.eColorGui)
#        this.parentPanel.Bind(wx.EVT_BUTTON, this.onEColor, id = this.eColorGui.GetId())
#        # Show / hide face
#        this.fOptionsLst = [
#            this.cull_show_both,
#            this.cull_show_front,
#            this.cull_show_back,
#            this.cull_show_none,
#        ]
#        this.fOptionsGui = wx.RadioBox(this.parentPanel,
#            label = 'Face Options',
#            style = wx.RA_VERTICAL,
#            choices = this.fOptionsLst
#        )
#        this.Guis.append(this.fOptionsGui)
#        this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onFOption, id = this.fOptionsGui.GetId())
#        faceSizer = wx.BoxSizer(wx.HORIZONTAL)
#        faceSizer.Add(this.fOptionsGui, 1, wx.EXPAND)
#        if not glIsEnabled(GL_CULL_FACE):
#            this.fOptionsGui.SetStringSelection(this.cull_show_both)
#        else:
#            # Looks like I switch front and back here, but this makes sense from
#            # the GUI.
#            if glGetInteger(GL_CULL_FACE_MODE) == GL_FRONT:
#                this.fOptionsGui.SetStringSelection(this.cull_show_front)
#            if glGetInteger(GL_CULL_FACE_MODE) == GL_BACK:
#                this.fOptionsGui.SetStringSelection(this.cull_show_back)
#            else: # ie GL_FRONT_AND_BACK
#                this.fOptionsGui.SetStringSelection(this.cull_show_none)
#
#        # Open GL
#        this.Boxes.append(wx.StaticBox(this.parentPanel,
#                                                label = 'OpenGL Settings'))
#        oglSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
#        this.Guis.append(
#            wx.CheckBox(this.parentPanel,
#                                label = 'Switch Front and Back Face (F3)')
#        )
#        this.oglFrontFaceGui = this.Guis[-1]
#        this.oglFrontFaceGui.SetValue(glGetIntegerv(GL_FRONT_FACE) == GL_CW)
#        this.parentPanel.Bind(wx.EVT_CHECKBOX, this.onOgl,
#                                        id = this.oglFrontFaceGui.GetId())
#        # background Colour
#        colTxt = wx.StaticText(this.parentPanel, -1, "Background Colour: ")
#        this.Guis.append(colTxt)
#        col = this.canvas.getBgCol()
#        this.bgColorGui = wx.lib.colourselect.ColourSelect(this.parentPanel,
#            wx.ID_ANY, colour = (col[0]*255, col[1]*255, col[2]*255),
#            size=wx.Size(40, 30))
#        this.Guis.append(this.bgColorGui)
#        this.parentPanel.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
#            this.onBgCol)
#
#        # Sizers
#        vRadiusSizer.Add(this.vRadiusGui, 1, wx.EXPAND | wx.TOP    | wx.LEFT)
#        vRadiusSizer.Add(this.vColorGui,  1,             wx.BOTTOM | wx.LEFT)
#        eRadiusSizer.Add(this.eRadiusGui, 1, wx.EXPAND | wx.TOP    | wx.LEFT)
#        eRadiusSizer.Add(this.eColorGui,  1,             wx.BOTTOM | wx.LEFT)
#        #sizer = wx.BoxSizer(wx.VERTICAL)
#        vSizer = wx.BoxSizer(wx.HORIZONTAL)
#        vSizer.Add(this.vOptionsGui, 2, wx.EXPAND)
#        vSizer.Add(vRadiusSizer, 5, wx.EXPAND)
#        eSizer = wx.BoxSizer(wx.HORIZONTAL)
#        eSizer.Add(this.eOptionsGui, 2, wx.EXPAND)
#        eSizer.Add(eRadiusSizer, 5, wx.EXPAND)
#        bgSizerSub = wx.BoxSizer(wx.HORIZONTAL)
#        bgSizerSub.Add(colTxt, 0, wx.EXPAND)
#        bgSizerSub.Add(this.bgColorGui, 0, wx.EXPAND)
#        bgSizerSub.Add(wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND)
#        oglSizer.Add(this.oglFrontFaceGui, 0, wx.EXPAND)
#        oglSizer.Add(bgSizerSub, 0, wx.EXPAND)
#        this.Add(vSizer, 5, wx.EXPAND)
#        this.Add(eSizer, 5, wx.EXPAND)
#        this.Add(faceSizer, 6, wx.EXPAND)
#        this.Add(oglSizer, 0, wx.EXPAND)
#
#        # 4D stuff
#        if this.canvas.shape.dimension == 4:
#            default = 0
#            this.useTransparencyGui = wx.RadioBox(this.parentPanel,
#                label = 'Use Transparency',
#                style = wx.RA_VERTICAL,
#                choices = ['Yes', 'No']
#            )
#            this.Guis.append(this.useTransparencyGui)
#            this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onUseTransparency, id = this.useTransparencyGui.GetId())
#            this.useTransparencyGui.SetSelection(default)
#            faceSizer.Add(this.useTransparencyGui, 1, wx.EXPAND)
#
#            default = 0
#            this.showUnscaledEdgesGui = wx.RadioBox(this.parentPanel,
#                label = 'Unscaled Edges',
#                style = wx.RA_VERTICAL,
#                choices = ['Show', 'Hide']
#            )
#            this.Guis.append(this.showUnscaledEdgesGui)
#            this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onShowUnscaledEdges, id =
#            this.showUnscaledEdgesGui.GetId())
#            this.showUnscaledEdgesGui.SetSelection(default)
#            faceSizer.Add(this.showUnscaledEdgesGui, 1, wx.EXPAND)
#
#            min   = 0.01
#            max   = 1.0
#            steps = 100
#            this.cellScaleFactor = float(max - min) / steps
#            this.cellScaleOffset = min
#            this.scaleGui = wx.Slider(
#                    this.parentPanel,
#                    value = 100,
#                    minValue = 0,
#                    maxValue = steps,
#                    style = wx.SL_HORIZONTAL
#                )
#            this.Guis.append(this.scaleGui)
#            this.parentPanel.Bind(
#                wx.EVT_SLIDER, this.onScale, id = this.scaleGui.GetId()
#            )
#            this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Scale Cells'))
#            scaleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
#            scaleSizer.Add(this.scaleGui, 1, wx.EXPAND)
#
#            # 4D -> 3D projection properties: camera and prj volume distance
#            steps = 100
#            min   = 0.1
#            max   = 5
#            this.prjVolFactor = float(max - min) / steps
#            this.prjVolOffset = min
#            this.prjVolGui = wx.Slider(
#                    this.parentPanel,
#                    value = this.Value2Slider(
#                            this.prjVolFactor,
#                            this.prjVolOffset,
#                            this.canvas.shape.wProjVolume
#                        ),
#                    minValue = 0,
#                    maxValue = steps,
#                    style = wx.SL_HORIZONTAL
#                )
#            this.Guis.append(this.prjVolGui)
#            this.parentPanel.Bind(
#                wx.EVT_SLIDER, this.onPrjVolAdjust, id = this.prjVolGui.GetId()
#            )
#            this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Projection Volume W-Coordinate'))
#            prjVolSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
#            prjVolSizer.Add(this.prjVolGui, 1, wx.EXPAND)
#            min   = 0.5
#            max   = 5
#            this.camDistFactor = float(max - min) / steps
#            this.camDistOffset = min
#            this.camDistGui = wx.Slider(
#                    this.parentPanel,
#                    value = this.Value2Slider(
#                            this.camDistFactor,
#                            this.camDistOffset,
#                            this.canvas.shape.wCameraDistance
#                        ),
#                    minValue = 0,
#                    maxValue = steps,
#                    style = wx.SL_HORIZONTAL
#                )
#            this.Guis.append(this.camDistGui)
#            this.parentPanel.Bind(
#                wx.EVT_SLIDER, this.onPrjVolAdjust, id = this.camDistGui.GetId()
#            )
#            this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Camera Distance (from projection volume)'))
#            camDistSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
#            camDistSizer.Add(this.camDistGui, 1, wx.EXPAND)
#
#            # Create a ctrl for specifying a 4D rotation
#            this.Boxes.append(wx.StaticBox(parentPanel, label = 'Rotate 4D Object'))
#            rotationSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
#            this.Boxes.append(wx.StaticBox(parentPanel, label = 'In a Plane Spanned by'))
#            planeSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
#            this.v0Gui = geom_gui.Vector4DInput(
#                    this.parentPanel,
#                    #label = 'Vector 1',
#                    relativeFloatSize = 4,
#                    elem_labels = ['x0', 'y0', 'z0', 'w0']
#                )
#            this.parentPanel.Bind(
#                geom_gui.EVT_VECTOR_UPDATED, this.onV, id = this.v0Gui.GetId()
#            )
#            this.v1Gui = geom_gui.Vector4DInput(
#                    this.parentPanel,
#                    #label = 'Vector 1',
#                    relativeFloatSize = 4,
#                    elem_labels = ['x1', 'y1', 'z1', 'w1']
#                )
#            this.parentPanel.Bind(
#                geom_gui.EVT_VECTOR_UPDATED, this.onV, id = this.v1Gui.GetId()
#            )
#            # Exchange planes
#            this.exchangeGui = wx.CheckBox(this.parentPanel, label = "Use Orthogonal Plane instead")
#            this.exchangeGui.SetValue(False)
#            this.parentPanel.Bind(wx.EVT_CHECKBOX, this.onExchangePlanes, id = this.exchangeGui.GetId())
#            #this.Boxes.append?
#            this.Guis.append(this.v0Gui)
#            this.Guis.append(this.v1Gui)
#            this.Guis.append(this.exchangeGui)
#            planeSizer.Add(this.v0Gui, 12, wx.EXPAND)
#            planeSizer.Add(this.v1Gui, 12, wx.EXPAND)
#            planeSizer.Add(this.exchangeGui, 10, wx.EXPAND)
#
#            min   = 0.00
#            max   = math.pi
#            steps = 360 # step by degree (if you change this, make at least 30 and 45 degrees possible)
#            this.angleFactor = float(max - min) / steps
#            this.angleOffset = min
#            this.angleGui = wx.Slider(
#                    this.parentPanel,
#                    value = 0,
#                    minValue = 0,
#                    maxValue = steps,
#                    style = wx.SL_HORIZONTAL
#                )
#            this.Guis.append(this.angleGui)
#            this.parentPanel.Bind(
#                wx.EVT_SLIDER, this.onAngle, id = this.angleGui.GetId()
#            )
#            this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Using Angle'))
#            angleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
#            angleSizer.Add(this.angleGui, 1, wx.EXPAND)
#
#            min   = 0.00
#            max   = 1.0
#            steps = 100
#            this.angleScaleFactor = float(max - min) / steps
#            this.angleScaleOffset = min
#            this.angleScaleGui = wx.Slider(
#                    this.parentPanel,
#                    value = 0,
#                    minValue = 0,
#                    maxValue = steps,
#                    style = wx.SL_HORIZONTAL
#                )
#            this.Guis.append(this.angleScaleGui)
#            this.parentPanel.Bind(
#                wx.EVT_SLIDER, this.onAngleScale, id = this.angleScaleGui.GetId()
#            )
#            this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Set Angle (by Scale) of Rotation in the Orthogonal Plane'))
#            angleScaleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
#            angleScaleSizer.Add(this.angleScaleGui, 1, wx.EXPAND)
#
#            rotationSizer.Add(planeSizer, 12, wx.EXPAND)
#            rotationSizer.Add(angleSizer, 5, wx.EXPAND)
#            rotationSizer.Add(angleScaleSizer, 5, wx.EXPAND)
#
#            this.Add(scaleSizer, 3, wx.EXPAND)
#            this.Add(prjVolSizer, 3, wx.EXPAND)
#            this.Add(camDistSizer, 3, wx.EXPAND)
#            this.Add(rotationSizer, 12, wx.EXPAND)
#
#        this.update_status_bar()
#
#    def close(this):
#        # The 'try' is necessary, since the boxes are destroyed in some OS,
#        # while this is necessary for e.g. Ubuntu Hardy Heron.
#        for Box in this.Boxes:
#            try:
#                Box.Destroy()
#            except wx._core.PyDeadObjectError: pass
#        for Gui in this.Guis:
#            Gui.Destroy()
#
#    def update_status_bar(this):
#        try:
#            this.parentWindow.update_status_bar('V-Radius: %0.5f; E-Radius: %0.5f' % (this.vR, this.eR))
#        except AttributeError:
#            print("parentWindow.update_status_bar function undefined")
#
#    def onVOption(this, e):
#        #print 'onVOption'
#        sel = this.vOptionsGui.GetSelection()
#        selStr = this.vOptionsLst[sel]
#        if selStr == 'show':
#            this.vRadiusGui.Enable()
#            this.canvas.shape.setVertexProperties(radius = this.vR)
#        elif selStr == 'hide':
#            this.vRadiusGui.Disable()
#            this.canvas.shape.setVertexProperties(radius = -1.0)
#        this.canvas.paint()
#
#    def onVRadius(this, e):
#        this.vR = (float(this.vRadiusGui.GetValue()) / this.vRadiusScale)
#        this.canvas.shape.setVertexProperties(radius = this.vR)
#        this.canvas.paint()
#        this.update_status_bar()
#
#    def onVColor(this, e):
#        dlg = wx.ColourDialog(this.parentWindow)
#        if dlg.ShowModal() == wx.ID_OK:
#            data = dlg.GetColourData()
#            rgba = data.GetColour()
#            rgb  = rgba.Get()
#            this.canvas.shape.setVertexProperties(
#                color = [float(i)/256 for i in rgb]
#            )
#            this.canvas.paint()
#        dlg.Destroy()
#
#    def onEOption(this, e):
#        sel = this.eOptionsGui.GetSelection()
#        selStr = this.eOptionsLst[sel]
#        if selStr == 'hide':
#            this.eRadiusGui.Disable()
#            this.canvas.shape.setEdgeProperties(drawEdges = False)
#        elif selStr == 'as cylinders':
#            this.eRadiusGui.Enable()
#            this.canvas.shape.setEdgeProperties(drawEdges = True)
#            this.canvas.shape.setEdgeProperties(radius = this.eR)
#        elif selStr == 'as lines':
#            this.eRadiusGui.Disable()
#            this.canvas.shape.setEdgeProperties(drawEdges = True)
#            this.canvas.shape.setEdgeProperties(radius = 0)
#        this.canvas.paint()
#
#    def onERadius(this, e):
#        this.eR = (float(this.eRadiusGui.GetValue()) / this.eRadiusScale)
#        this.canvas.shape.setEdgeProperties(radius = this.eR)
#        this.canvas.paint()
#        this.update_status_bar()
#
#    def onEColor(this, e):
#        dlg = wx.ColourDialog(this.parentWindow)
#        if dlg.ShowModal() == wx.ID_OK:
#            data = dlg.GetColourData()
#            rgba = data.GetColour()
#            rgb  = rgba.Get()
#            this.canvas.shape.setEdgeProperties(
#                color = [float(i)/256 for i in rgb]
#            )
#            this.canvas.paint()
#        dlg.Destroy()
#
#    def onFOption(this, e):
#        print('View Settings Window size:', this.parentWindow.GetSize())
#        sel = this.fOptionsGui.GetStringSelection()
#        # Looks like I switch front and back here, but this makes sense from
#        # the GUI.
#        this.canvas.shape.setFaceProperties(drawFaces = True)
#        if sel == this.cull_show_both:
#            glDisable(GL_CULL_FACE)
#        elif sel == this.cull_show_none:
#            # don't use culling here: doesn't work with edge radius and vertext
#            # radius > 0
#            this.canvas.shape.setFaceProperties(drawFaces = False)
#            glDisable(GL_CULL_FACE)
#        elif sel == this.cull_show_front:
#            glCullFace(GL_FRONT)
#            glEnable(GL_CULL_FACE)
#        elif this.cull_show_back:
#            glCullFace(GL_BACK)
#            glEnable(GL_CULL_FACE)
#        this.canvas.paint()
#
#    def onOgl(this, e):
#        id = e.GetId()
#        if id == this.oglFrontFaceGui.GetId():
#            onSwitchFrontBack(this.canvas)
#
#    def onBgCol(this, e):
#        col = e.GetValue().Get()
#        this.canvas.setBgCol(
#            [float(col[0])/255, float(col[1])/255, float(col[2])/255]
#        )
#        this.canvas.paint()
#
#    def onUseTransparency(this, event):
#        this.canvas.shape.useTransparency((this.useTransparencyGui.GetSelection() == 0))
#        this.canvas.paint()
#
#    def onShowUnscaledEdges(this, event):
#        this.canvas.shape.setEdgeProperties(
#            showUnscaled = (this.showUnscaledEdgesGui.GetSelection() == 0)
#        )
#        this.canvas.paint()
#
#    def Value2Slider(this, factor, offset, y):
#        return (y - offset) / factor
#
#    def Slider2Value(this, factor, offset, x):
#        return factor * float(x) + offset
#
#    def onScale(this, event):
#        scale = this.Slider2Value(
#                this.cellScaleFactor,
#                this.cellScaleOffset,
#                this.scaleGui.GetValue()
#            )
#        this.canvas.shape.setCellProperties(scale = scale)
#        this.canvas.paint()
#
#    def onPrjVolAdjust(this, event):
#        #print 'size =', this.dynDlg.GetClientSize()
#        cameraDistance = this.Slider2Value(
#                this.camDistFactor,
#                this.camDistOffset,
#                this.camDistGui.GetValue()
#            )
#        wProjVolume = this.Slider2Value(
#                this.prjVolFactor,
#                this.prjVolOffset,
#                this.prjVolGui.GetValue()
#            )
#        if (cameraDistance > 0) and (wProjVolume > 0):
#            this.parentWindow.statusBar.SetStatusText(
#                "projection volume w = %0.2f; camera distance: %0.3f" % (
#                    wProjVolume, cameraDistance
#                )
#            )
#        else:
#            if cameraDistance > 0:
#                this.parentWindow.statusBar.SetStatusText(
#                    'Error: Camera distance should be > 0!'
#                )
#            else:
#                this.parentWindow.statusBar.SetStatusText(
#                    'Error: Projection volume:  w should be > 0!'
#                )
#        this.canvas.shape.setProjectionProperties(cameraDistance, wProjVolume, dbg = True)
#        this.canvas.paint()
#        event.Skip()
#
#    def onAngle(this, event):
#        this.rotate()
#
#    def onAngleScale(this, event):
#        this.rotate()
#
#    def onExchangePlanes(this, event):
#        this.rotate()
#
#    def onV(this, event):
#        this.rotate()
#
#    def rotate(this):
#        v0 = this.v0Gui.GetValue()
#        v1 = this.v1Gui.GetValue()
#        angle = this.Slider2Value(
#                this.angleFactor,
#                this.angleOffset,
#                this.angleGui.GetValue()
#            )
#        scale = this.Slider2Value(
#                this.angleScaleFactor,
#                this.angleScaleOffset,
#                this.angleScaleGui.GetValue()
#            )
#        if geomtypes.eq(angle, 0): return
#        try:
#            v1 = v1.make_orthogonal_to(v0)
#            # if vectors are exchange, you actually specify the axial plane
#            if this.exchangeGui.IsChecked():
#                if geomtypes.eq(scale, 0):
#                    r = geomtypes.Rot4(axialPlane = (v1, v0), angle = angle)
#                else:
#                    r = geomtypes.DoubleRot4(
#                            axialPlane = (v1, v0),
#                            angle = (angle, scale*angle)
#                        )
#            else:
#                    r = geomtypes.DoubleRot4(
#                            axialPlane = (v1, v0),
#                            angle = (scale*angle, angle)
#                        )
#            #print r.getMatrix()
#            this.canvas.shape.rotate(r)
#            this.canvas.paint()
#            aDeg = Geom3D.Rad2Deg * angle
#            this.parentWindow.statusBar.SetStatusText(
#                "Rotation angle: %f degrees (and scaling %0.2f)" % (aDeg, scale)
#            )
#        except ZeroDivisionError:
#            # zero division means 1 of the vectors is (0, 0, 0, 0)
#            this.parentWindow.statusBar.SetStatusText("Error: Don't use a zero vector")
#            pass
#        #except AssertionError:
#        #    zV = geomtypes.Vec4([0, 0, 0, 0])
#        #    if v0 == zV or v1 == zV:
#        #        this.parentWindow.statusBar.SetStatusText("Error: Don't use a zero vector")
#        #    else:
#        #        this.parentWindow.statusBar.SetStatusText("Error: The specified vectors are (too) parallel")
#        #    pass
#
#class ExportOffDialog(wx.Dialog):
#    precision = 12
#    floatMargin = 10
#    cleanUp = False
#    extraInfo = False
#    """
#    Dialog for exporting a polyhedron to a PS file.
#
#    Settings like: scaling size and precision. Changing these settings will
#    reflect in the next dialog that is created.
#    Based on wxPython example dialog
#    """
#    def __init__(this,
#            parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition,
#            style=wx.DEFAULT_DIALOG_STYLE
#        ):
#
#        # Instead of calling wx.Dialog.__init__ we precreate the dialog
#        # so we can set an extra style that must be set before
#        # creation, and then we create the GUI dialog using the Create
#        # method.
#        pre = wx.PreDialog()
#        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
#        pre.Create(parent, ID, title, pos, size, style)
#
#        # This next step is the most important, it turns this Python
#        # object into the real wrapper of the dialog (instead of pre)
#        # as far as the wxPython extension is concerned.
#        this.PostCreate(pre)
#
#        # Now continue with the normal construction of the dialog
#        # contents
#        sizer = wx.BoxSizer(wx.VERTICAL)
#
#        hbox = wx.BoxSizer(wx.HORIZONTAL)
#        label = wx.StaticText(this, -1, "vertex precision (decimals):")
#        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
#        this.precisionGui = wx.lib.intctrl.IntCtrl(this,
#                value = this.precision,
#                min   = 1,
#                max   = 16
#            )
#        this.precisionGui.Bind(wx.lib.intctrl.EVT_INT, this.onPrecision)
#        hbox.Add(this.precisionGui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
#        sizer.Add(hbox, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
#
#        this.extraInfoGui = wx.CheckBox(this,
#                label = 'Print extra info')
#        this.extraInfoGui.SetValue(this.extraInfo)
#        this.extraInfoGui.Bind(wx.EVT_CHECKBOX, this.onExtraInfo)
#        sizer.Add(this.extraInfoGui,
#            0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
#
#        this.cleanUpGui = wx.CheckBox(this,
#                label = 'Merge equal vertices (can take a while)')
#        this.cleanUpGui.SetValue(this.cleanUp)
#        this.cleanUpGui.Bind(wx.EVT_CHECKBOX, this.onCleanUp)
#        sizer.Add(this.cleanUpGui,
#            0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
#
#        hbox = wx.BoxSizer(wx.HORIZONTAL)
#        label = wx.StaticText(this, -1, "float margin for being equal (decimals):")
#        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
#        this.floatMarginGui = wx.lib.intctrl.IntCtrl(this,
#                value = this.floatMargin,
#                min   = 1,
#                max   = 16
#            )
#        this.floatMarginGui.Bind(wx.lib.intctrl.EVT_INT, this.onFloatMargin)
#        if not this.cleanUp:
#            this.floatMarginGui.Disable()
#        hbox.Add(this.floatMarginGui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
#        sizer.Add(hbox, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
#
#        buttonSizer = wx.StdDialogButtonSizer()
#
#        button = wx.Button(this, wx.ID_OK)
#        button.SetDefault()
#        buttonSizer.AddButton(button)
#        button = wx.Button(this, wx.ID_CANCEL)
#        buttonSizer.AddButton(button)
#        buttonSizer.Realize()
#
#        sizer.Add(buttonSizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
#
#        this.SetSizer(sizer)
#        sizer.Fit(this)
#
#    def onExtraInfo(this, e):
#        ExportOffDialog.extraInfo = this.extraInfoGui.GetValue()
#
#    def getExtraInfo(this):
#        return this.extraInfoGui.GetValue()
#
#    def onCleanUp(this, e):
#        ExportOffDialog.cleanUp = this.cleanUpGui.GetValue()
#        if ExportOffDialog.cleanUp:
#            this.floatMarginGui.Enable()
#        else:
#            this.floatMarginGui.Disable()
#
#    def getCleanUp(this):
#        return this.cleanUpGui.GetValue()
#
#    def onPrecision(this, e):
#        ExportOffDialog.precision = this.precisionGui.GetValue()
#
#    def getPrecision(this):
#        return this.precisionGui.GetValue()
#
#    def onFloatMargin(this, e):
#        ExportOffDialog.floatMargin = this.floatMarginGui.GetValue()
#
#    def getFloatMargin(this):
#        return this.floatMarginGui.GetValue()
#
#class ExportPsDialog(wx.Dialog):
#    scaling = 50
#    precision = 12
#    floatMargin = 10
#    """
#    Dialog for exporting a polyhedron to a PS file.
#
#    Settings like: scaling size and precision. Changing these settings will
#    reflect in the next dialog that is created.
#    Based on wxPython example dialog
#    """
#    def __init__(this,
#            parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition,
#            style=wx.DEFAULT_DIALOG_STYLE
#        ):
#
#        # Instead of calling wx.Dialog.__init__ we precreate the dialog
#        # so we can set an extra style that must be set before
#        # creation, and then we create the GUI dialog using the Create
#        # method.
#        pre = wx.PreDialog()
#        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
#        pre.Create(parent, ID, title, pos, size, style)
#
#        # This next step is the most important, it turns this Python
#        # object into the real wrapper of the dialog (instead of pre)
#        # as far as the wxPython extension is concerned.
#        this.PostCreate(pre)
#
#        # Now continue with the normal construction of the dialog
#        # contents
#        sizer = wx.BoxSizer(wx.VERTICAL)
#
#        hbox = wx.BoxSizer(wx.HORIZONTAL)
#        label = wx.StaticText(this, -1, "Scaling Factor:")
#        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
#        this.scalingFactorGui = wx.lib.intctrl.IntCtrl(this,
#                value = ExportPsDialog.scaling,
#                min   = 1,
#                max   = 10000
#            )
#        this.scalingFactorGui.Bind(wx.lib.intctrl.EVT_INT, this.onScaling)
#        hbox.Add(this.scalingFactorGui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
#        sizer.Add(hbox, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
#        hbox = wx.BoxSizer(wx.HORIZONTAL)
#        label = wx.StaticText(this, -1, "vertex precision (decimals):")
#        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
#        this.precisionGui = wx.lib.intctrl.IntCtrl(this,
#                value = ExportPsDialog.precision,
#                min   = 1,
#                max   = 16
#            )
#        this.precisionGui.Bind(wx.lib.intctrl.EVT_INT, this.onPrecision)
#        hbox.Add(this.precisionGui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
#        sizer.Add(hbox, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
#        hbox = wx.BoxSizer(wx.HORIZONTAL)
#        label = wx.StaticText(this, -1, "float margin for being equal (decimals):")
#        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
#        this.floatMarginGui = wx.lib.intctrl.IntCtrl(this,
#                value = ExportPsDialog.floatMargin,
#                min   = 1,
#                max   = 16
#            )
#        this.floatMarginGui.Bind(wx.lib.intctrl.EVT_INT, this.onFloatMargin)
#        hbox.Add(this.floatMarginGui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
#        sizer.Add(hbox, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
#
#        buttonSizer = wx.StdDialogButtonSizer()
#
#        button = wx.Button(this, wx.ID_OK)
#        button.SetDefault()
#        buttonSizer.AddButton(button)
#        button = wx.Button(this, wx.ID_CANCEL)
#        buttonSizer.AddButton(button)
#        buttonSizer.Realize()
#
#        sizer.Add(buttonSizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
#
#        this.SetSizer(sizer)
#        sizer.Fit(this)
#
#    def onScaling(this, e):
#        ExportPsDialog.scaling = this.scalingFactorGui.GetValue()
#
#    def getScaling(this):
#        return this.scalingFactorGui.GetValue()
#
#    def onPrecision(this, e):
#        ExportPsDialog.precision = this.precisionGui.GetValue()
#
#    def getPrecision(this):
#        return this.precisionGui.GetValue()
#
#    def onFloatMargin(this, e):
#        ExportPsDialog.floatMargin = this.floatMarginGui.GetValue()
#
#    def getFloatMargin(this):
#        return this.floatMarginGui.GetValue()


def read_shape_file(filename):
    if filename is None:
        fd = sys.stdin
    else:
        if filename[-3:] == '.py':
            fd = open(filename, 'r')
            return Geom3D.read_py_file(fd)
        elif filename[-4:] == '.off':
            fd = open(filename, 'r')
            return Geom3D.read_off_file(fd, recreateEdges=True)
        else:
            print('unrecognised file extension')
            return None


def convert_to_ps(shape, o_fd, scale, precision, margin):
    o_fd.write(shape.to_ps_pieces_str(scaling=scale,
                                      precision=precision,
                                      margin=math.pow(10, -margin),
                                      suppressWarn=True))


def convert_to_off(shape, o_fd, precision, margin=0):
    """
    Save the shape to the o_fd file descriptor in .off format

    precision: how many decimals to write.
    margin: what margin to use to require that 2 floating numbers are equal.
            If not specified or 0, then no cleaning up is done, meaning that no
            attempt is made of merging vertices that have the same coordinate.
            Neither are faces with the same coordinates filtered out.
    """
    try:
        shape = shape.simple_shape
    except AttributeError:
        pass
    if margin != 0:
        shape = shape.cleanShape(margin)
    # TODO: support for saving extraInfo?
    o_fd.write(shape.to_off_str(precision))


def usage(exit_nr):
    print("""
usage Orbitit.py [-p | --ps] [<in_file>] [<out_file>]

Without any specified options ut starts the program in the default scene.
Options:

        --precision <int>
        -P <int>          Write the number with <int> number of decimals.

        -p
        --ps         export to PS. The input file is either a python scrypt,
                     specified by -y or an off file, specified by -f. If no
                     argument is specified, the the result is piped to stdout.
        -y <file>
        --py=<file>  export to a python fyle defing a shape that can be
                     interpreted by Orbitit

        -f <file>
        --off=<file> export to a python fyle defing a shape that can be read by
                     other programs, like Antiprism and Stella.

        -m <int>
        --margin=<int> set the margin for floating point numbers to be
                       considered equal. All numbers with a difference that is
                       smaller than 1.0e-<int> will be considered equal.

        -s <file>
        --scene=<file> Start the program with the scene as specified by the
                       file parameter.
    """)
    sys.exit(exit_nr)

class Oper:
    toPs = 1
    toOff = 2
    toPy = 3
    openScene = 4

import getopt

try:
    opts, args = getopt.getopt(sys.argv[1:],
        'fm:P:ps:y', ['off', '--margin=', 'precision=', 'ps', 'scene=', 'py'])
except getopt.GetoptError as err:
    print(str(err))
    usage(2)

# defaults:
scale = 50
margin = 10
precision = 15

oper = None
for opt, opt_arg in opts:
    if opt in ('-f', '--off'):
        oper = Oper.toOff
    elif opt in ('-m', '--margin'):
        margin = int(opt_arg)
    elif opt in ('-P', '--precision'):
        precision = int(opt_arg)
    elif opt in ('-p', '--ps'):
        oper = Oper.toPs
    elif opt in ('-s', '--scene'):
        oper = Oper.openScene
        scene_file = opt_arg
        print('DBG scene_file', scene_file)
    elif opt in ('-y', '--py'):
        oper = Oper.toPy
    else:
        print("Error: unknown option")
        usage(2)

o_fd = None
a_ind = 0
print('DBG args', args)
if oper is not None:
    if len(args) <= a_ind:
        print("reading python format from std input")
        i_filename = None
    else:
        i_filename = args[a_ind]
        a_ind += 1
    if len(args) <= a_ind:
        o_fd = sys.stdout
    else:
        o_fd = open(args[a_ind], 'w')
        a_ind += 1

if oper == Oper.toPs:
    shape = read_shape_file(i_filename)
    if shape is not None:
        convert_to_ps(shape, o_fd, scale, precision, margin)
elif oper == Oper.toOff:
    shape = read_shape_file(i_filename)
    if shape is not None:
        convert_to_off(shape, o_fd, precision, margin)
elif oper == Oper.toPy:
    shape = read_shape_file(i_filename)
    if shape is not None:
        shape.saveFile(o_fd)
else:
    if oper != Oper.openScene:
        scene_file = DefaultScene
    root = tk.Tk()
    root.title("Orbitit")
    root.geometry("430x482")
    frame = MainWindow(
        root,
        OglFrame,
        Geom3D.SimpleShape([], []),
        args)
    frame.grid(row=0, column=0)
    if (len(args) == 0):
        frame.read_scene_file(scene_file)
    root.mainloop()

sys.stderr.write("Done\n")

if o_fd != None: o_fd.close()
