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

from copy import deepcopy
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
from tkinter import colorchooser
from tkinter import filedialog

from OpenGL import GL, GLU
#from OpenGL.GLU import *
#from OpenGL.GL import *
from tkinter import messagebox

DEG2RAD = Geom3D.Deg2Rad

DefaultScene = './scene_orbit.py'


def shape_col_to_tk(col):
    return "#{:02X}{:02X}{:02X}".format(int(0xff * col[0]),
                                        int(0xff * col[1]),
                                        int(0xff * col[2]))


def tk_to_shape_col(col):
    return (int(col[1:3], 16) / 0xff,
            int(col[3:5], 16) / 0xff,
            int(col[5:7], 16) / 0xff)


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
    off_files = (("Off shape", "*.off"),
                 ("Off shape", "*.OFF"))
    ps_files = (("Postscript", "*.ps"),
                ("Postscipt", "*.PS"))
    python_files = (("Python shape", "*.py"),
                    ("Python shape", "*.PY"))
    vrml_files = (("VRML shape", "*.wrl"),
                  ("VRML shape", "*.WRL"))
    shape_files = (("Off shape", "*.off"),
                   ("Off shape", "*.OFF"),
                   ("Python shape", "*.py"),
                   ("Python shape", "*.PY"))
    current_scene = None
    current_file = None

    def __init__(self, root, ogl_frame, shape, p_args):
        super().__init__(root)
        self.root = root
        self.context_created = False
        self.add_menu_bar()
        self.add_scene_canvas(ogl_frame, shape)
        self.add_status_bar()
        self.export_dir = '.'
        self.import_dir = '.'
        self.scene_dir = '.'
        self.off_vals = OffFields()
        self.ps_vals = PsFields()
        #self.viewSettingsWindow = None
        self.export_off_win = None
        self.export_ps_win = None
        self.col_settings_window = None
        self.transform_settings_window = None
        root.protocol('WM_DELETE_WINDOW', self.on_quit)

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
        self.root.rowconfigure(1, weight=1, minsize=300)
        self.root.columnconfigure(0, weight=1, minsize=300)

    def add_status_bar(self):
        self.status_str = tk.StringVar()
        self.status_bar = tk.Label(root, textvariable=self.status_str,
                                   bd=1, relief=tk.SUNKEN)
        self.status_bar.grid(row=2, column=0, sticky=tk.W + tk.E)

    def update_status_bar(self, str):
        self.status_str.set(str)

    def on_reload(self, e=None):
        print('TODO: on_reload')
        if self.current_file != None:
            self.open_file(self.current_file)
        elif self.current_scene != None:
            self.set_scene(self.current_scene)

    def on_open(self, e=None):
        filename = filedialog.askopenfilename(
            initialdir=self.import_dir,
            title="Choose a File",
            filetypes=self.shape_files)
        if filename:
            self.open_file(filename)
            self.import_dir = os.path.split(filename)[0]

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
        self.current_file = filename
        self.current_scene = None

    def on_add(self, e=None):
        filename = filedialog.askopenfilename(
            initialdir=self.import_dir,
            title="Choose a File",
            filetypes=self.shape_files)
        if filename:
            self.import_dir = os.path.split(filename)[0]
            is_off_model = filename[-3:] == 'off'
            print("adding file:", filename)
            fd = open(os.path.join(self.import_dir, filename), 'r')
            if is_off_model:
                shape = Geom3D.read_off_file(fd, recreateEdges=True)
            else:
                shape = Geom3D.read_py_file(fd)
            if isinstance(shape, Geom3D.CompoundShape):
                # convert to SimpleShape first, since adding a IsometricShape
                # will not work.
                shape = shape.simple_shape
            try:
                self.get_shape().addShape(shape)
            except AttributeError:
                print("warning: cannot 'add' a shape to self scene, "
                      "use 'File->Open' instead")
            self.update_status_bar("OFF file added")
            fd.close()
            # TODO: set better title
            self.root.title('Added: %s' % os.path.basename(filename))

    def _fix_file_ext(self, filename, ext):
        name_ext = filename.split('.')
        # The case below is the only case the file dialog will cover when
        # checking whether an existing file is being overwritten.
        if len(name_ext) == 1:
            filename = '{}.{}'.format(filename, ext.lower())
        return filename

    def to_top(self, window):
        window.focus_force()

    def on_save_as_py(self, e=None):
        filename = filedialog.asksaveasfilename(
            initialdir=self.export_dir,
            title="Save as Python File",
            filetypes=self.python_files)
        if filename:
            self.export_dir = os.path.split(filename)[0]
            filename = self._fix_file_ext(filename, 'py')
            # TODO precision through setting:
            shape = self.get_shape()
            shape.name = filename
            with open(filename, 'w') as fd:
                print("writing to file %s" % filename)
                shape.saveFile(fd)
            self.update_status_bar("{} file written".format(filename))

    def on_save_as_off(self, e=None):
        if self.export_off_win is not None:
            self.to_top(self.export_off_win)
            return
        self.export_off_win = ExportOffDialog(self,
                                              'OFF settings',
                                              self.off_vals)
        if self.export_off_win.show() is not None:
            filename = filedialog.asksaveasfilename(
                initialdir=self.export_dir,
                title="Save as OFF File",
                filetypes=self.off_files)
            if filename != '':
                self.export_dir = os.path.split(filename)[0]
                filename = self._fix_file_ext(filename, 'off')
                shape = self.get_shape()
                try:
                    shape = shape.simple_shape
                except AttributeError:
                    pass
                if self.off_vals.merge_vs:
                    shape = shape.clean_shape(self.off_vals.float_margin)
                with open(filename, 'w') as fd:
                    print("writing to file %s" % filename)
                    fd.write(shape.to_off_str(self.off_vals.precision,
                                              self.off_vals.extra_info))
                status_txt = "{} written".format(filename)
                print(status_txt)
                self.update_status_bar(status_txt)
        self.export_off_win = None

    def on_save_as_ps(self, e=None):
        if self.export_ps_win is not None:
            self.to_top(self.export_ps_win)
            return
        self.export_ps_win = ExportPsDialog(self,
                                            'PS settings',
                                            self.ps_vals)
        if self.export_ps_win.show() is not None:
            filename = filedialog.asksaveasfilename(
                initialdir=self.export_dir,
                title="Save as Postscript File",
                filetypes=self.ps_files)
            if filename != '':
                self.export_dir = os.path.split(filename)[0]
                filename = self._fix_file_ext(filename, 'ps')
                shape = self.get_shape()
                shape = shape.clean_shape(self.ps_vals.float_margin)
                try:
                    shape = shape.simple_shape
                except AttributeError:
                    pass
                with open(filename, 'w') as fd:
                    print("writing to file {}".format(filename))
                    try:
                        fd.write(shape.to_ps_pieces_str(
                            scaling=self.ps_vals.scaling,
                            precision=self.ps_vals.precision,
                            margin=math.pow(10,
                                            -self.ps_vals.float_margin)))
                        self.update_status_bar("{} written".format(
                            filename))
                    except Geom3D.PrecisionError as e:
                        self.update_status_bar("Margin error, " + str(e))
                        raise
        self.export_ps_win = None

    def on_save_as_wrl(self, e=None):
        filename = filedialog.asksaveasfilename(
            initialdir=self.export_dir,
            title="Save as .wrl file",
            filetypes=self.vrml_files)
        if filename != '':
            self.export_dir = os.path.split(filename)[0]
            filename = self._fix_file_ext(filename, 'wrl')
            # TODO precision through setting:
            r = self.get_shape().getEdgeProperties()['radius']
            x3dObj = self.get_shape().toX3dDoc(edgeRadius=r)
            x3dObj.setFormat(X3D.VRML_FMT)
            with open(filename, 'w') as fd:
                print(f"writing {filename}")
                fd.write(x3dObj.toStr())
            self.update_status_bar("{} written".format(filename))

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

    def make_col_map(self, all_shapes_cols):
        """From shape colours create a list of tkinter colours and create map.

        A map is create as self.idx_to_shape_cols which is a list of
        dictionaries. For the dictionaries the key is a shape index and the
        values are the face indices to which a colour should be applied. The
        colour that should be applied is in the returned flat list with the
        same index as the dictionary.

        all_shapes_cols: see face colour properties of Geom3D.SimpleShape
        return: flast list with unique colours as "#{:02X}{:02X}{:02X}"
        """
        flat_list_of_cols = []
        idx_to_shape_cols = []
        for shape_idx, shape_cols in enumerate(all_shapes_cols):
            for col_idx, col in enumerate(shape_cols[0]):
                tk_col = shape_col_to_tk(col)
                if tk_col not in flat_list_of_cols:
                    flat_list_of_cols.append(tk_col)
                    idx_to_shape_cols.append({shape_idx: [col_idx]})
                else:
                    common_idx = flat_list_of_cols.index(tk_col)
                    col_dict = idx_to_shape_cols[common_idx]
                    if shape_idx in col_dict:
                        col_dict[shape_idx].append(col_idx)
                    else:
                        col_dict[shape_idx] = [col_idx]
        self.idx_to_shape_cols = idx_to_shape_cols
        return flat_list_of_cols

    def on_colour_settings(self, e=None):
        if self.col_settings_window is not None:
            # Don't reuse, the colours might be wrong after loading a new model
            self.col_settings_window.destroy()
        cols = self.make_col_map(
            self.ogl_frame.shape.getFaceProperties()['colors'])
        self.col_settings_window = ColourSettingsWindow(
            self, 'Colour Settings',
            cols, 6,
            lambda c, i=None: self.on_update_shape_cols(c, i))
        self.col_settings_window.show()
        self.col_settings_window = None

    def on_update_shape_cols(self, tk_cols, col_idx=None):
        shape_cols = self.ogl_frame.shape.getFaceProperties()['colors']

        def update_col_dict(col_dict, tk_col):
            shape_col = tk_to_shape_col(tk_col)
            for shape_idx, col_indices in col_dict.items():
                for col_idx in col_indices:
                    shape_cols[shape_idx][0][col_idx] = shape_col

        if col_idx is not None:
            col_dict = self.idx_to_shape_cols[col_idx]
            update_col_dict(col_dict, tk_cols[col_idx])
        else:
            for col_idx, tk_col in enumerate(tk_cols):
                col_dict = self.idx_to_shape_cols[col_idx]
                update_col_dict(col_dict, tk_col)

        self.ogl_frame.shape.setFaceProperties(colors=shape_cols)
        self.ogl_frame.paint()

    def on_transform(self, e=None):
        if self.transform_settings_window is not None:
            self.to_top(self.transform_settings_window)
            return
        self.rotation = geomtypes.Rot3(axis=geomtypes.Vec3([1, 0, 0]))
        self.transform_settings_window = ContiniousRotationUpdateWindow(
            self, 'Transform Settings',
            rotation=self.rotation)
        self.transform_settings_window.show()
        self.transform_settings_window = None

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
        scene = {'label': ed['TITLE'],
                 'class': ed['Scene']}
        self.set_scene(scene)

    def set_scene(self, scene):
        print("TODO: set scene: class replaced by OglCanvas? Where Ctrl Frame")
        return
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
        self.current_scene = scene
        self.current_file = None

    def on_reset_view(self, e=None):
        self.ogl_frame.reset_orientation()

    def close_current_scene(self):
        print("print: TODO: only for destroying scenes control window")
        return
        if self.ogl_frame is not None:
            #self.ogl_frame.close()
            del self.ogl_frame
            self.ogl_frame = None

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
#
#    def onClose(this, event):
#        print('main onclose')
#        if this.viewSettingsWindow != None:
#            this.viewSettingsWindow.Close()
#        if this.colourSettingsWindow != None:
#            this.colourSettingsWindow.Close()
#        if this.transform_settings_window != None:
#            this.transform_settings_window.Close()
#        this.Destroy()
#
#    def onKeyDown(this, e):
#        id = e.GetId()
#        if id == this.keySwitchFronBack:
#            onSwitchFrontBack(this.panel.getCanvas())

    def set_shape(self, shape):
        """Set a new shape to be shown with the current viewing settings

        shape: the new shape. This will refresh the ogl_frame.
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
        self.update_status_bar("Shape Updated")
        self.update()

    def get_shape(self):
        """Return the current shape object"""
        return None if self.ogl_frame is None else self.ogl_frame.shape


# TODO: move to library, since this is a generic floating window now
class ColourSettingsWindow(tk.Toplevel):
    """Dialog window for updating the shape colours."""
    def __init__(self, parent, title, cols, no_of_cols_per_row, command):
        """Initialise object

        parent: parent widget
        title: title to use for new dialog
        cols: the OpenGL canvas holding the shape object
        no_of_cold_per_row: the number of colour buttons per dialog row.
        command: a function accepting one parameter in the same format as the
                 cols parameter. It also has an keyword parameter idx, that is
                 used when only one index is updated.
        """
        super().__init__(parent)
        self.attributes('-type', 'dialog')
        self.title(title)
        self.cols = cols
        self.update_cols = command
        # take a copy for reset
        self.org_cols = deepcopy(self.cols)
        self.protocol('WM_DELETE_WINDOW', self.on_cancel)

        self.columnconfigure(0, weight=1)

        colours = tk.Frame(self)
        colours.grid(row=0, column=0, sticky=tk.W + tk.E)
        for i in range(no_of_cols_per_row):
            colours.columnconfigure(i, weight=1)

        row = 0
        column = 0
        self.col_buttons = []
        for col in cols:
            button = tk.Button(colours, bg=col)
            button.configure(command=lambda b=button: self.on_col(b))
            button.bind("<Enter>", self.on_button_over)
            button['activebackground'] = button["background"]
            self.col_buttons.append(button)
            if column >= no_of_cols_per_row:
                column = 0
                row += 1
            button.grid(row=row, column=column, sticky=tk.W + tk.E)
            column += 1

        buttons = tk.Frame(self)
        buttons.grid(row=1, column=0, sticky=tk.W + tk.E)
        # To split at reset button if window has bigger width
        buttons.columnconfigure(1, weight=1)
        self.cancel = tk.Button(buttons, text="Cancel", command=self.on_cancel)
        self.cancel.grid(row=row, column=0, sticky=tk.W)
        self.ok = tk.Button(buttons, text="Reset", command=self.on_reset)
        self.ok.grid(row=row, column=1, sticky=tk.W)
        self.ok = tk.Button(buttons, text="OK", command=self.on_ok)
        self.ok.grid(row=row, column=2, sticky=tk.E)

        self.bind("<Escape>", lambda e: self.on_cancel(e))

    def on_button_over(self, event):
        col_button = event.widget
        col_button.focus_force()

    def on_col(self, button):
        old_col = button["background"]
        rgb_col, tk_col = colorchooser.askcolor(color=old_col)
        if rgb_col is not None:
            col_idx = self.col_buttons.index(button)
            button['background'] = tk_col
            button['activebackground'] = button["background"]
            self.cols[col_idx] = tk_col
            self.update_cols(self.cols, col_idx)

    def on_cancel(self, event=None):
        self.on_reset()
        self.destroy()

    def on_reset(self, event=None):
        # update button colours:
        for org_col, col_button in zip(self.org_cols, self.col_buttons):
            col_button.configure(bg=org_col)
            col_button['activebackground'] = col_button["background"]
        self.cols = deepcopy(self.org_cols)
        self.update_cols(self.cols)

    def on_ok(self, event=None):
        self.destroy()

    def show(self):
        """Show the dialog en return when it is closed."""
        self.wm_deiconify()
        self.wait_window()


class FloatEntry(tk.Entry):
    """Entry for only floating point numbers."""
    def __init__(self, parent, *args,
                 extra_validate=None,
                 **kwargs):
        """Initialise entry that only allows floating point numbers.

        extra_validate: an extra validation step. This is a function that takes
                        one parameters: the requested new value. Return True is
                        valid, False otherwise.
        """
        self.extra_validate = extra_validate

        float_vcmd = (parent.register(self.validate_if_float), '%P')

        super().__init__(parent,
                         *args,
                         validate='key',
                         validatecommand=float_vcmd,
                         **kwargs)

    def validate_if_float(self, new_value):
        allow = True
        try:
            value = float(new_value)
            if self.extra_validate is not None:
                allow = self.extra_validate(value)
        except ValueError:
            allow = False
        return allow


class ContiniousRotationWidget(tk.Frame):
    """A widget for continious updates of an angle."""
    def __init__(self, parent,
                 title,
                 rotation, command,
                 *args,
                 angle_domain=[-180, 180],
                 angle_digits=5,
                 angle_init_step=0.1,
                 float_width=10,
                 **kwargs):
        """Initialise object

        parent: parent widget
        rotation: a geomtypes.Rot3 object with the initial rotation
        command: the command to call every time the roation object is updated.
                 the command isn't called with any parameters. Just keep a
                 reference to the rotation object (input parameter)
        angle_domain: minimum and maximum angle (in degrees)
        angle_digits: total amount of digits to show on angle slidebar (for
                      min/max value.
        angle_init_step: initial step (in degrees) for + and - buttons
        float_width: width of all float entries that are used.
        """
        super().__init__(parent, *args, **kwargs)
        self.rotation = rotation
        self.command = command

        def on_rotate(*args):
            self.on_rotate()
            return True

        axis = rotation.axis()
        angle = rotation.angle() / DEG2RAD

        row = 0
        # Row with axis and angle entries
        tk.Label(self, text=title).grid(row=row, column=0, sticky=tk.W)
        rot_ctrl = tk.Frame(self)
        row += 1
        rot_ctrl.grid(row=row, column=0, sticky=tk.W)
        sub_row = 0
        column = 0
        tk.Button(rot_ctrl,
                  text="Axis:",
                  command=on_rotate).grid(row=sub_row, column=column)
        self.axis_var = []
        for i in range(3):
            column += 1
            # It doesn't seem that variables are required, but I got problems
            # with updating the entries (e.g. with the reset)
            self.axis_var.append(tk.DoubleVar())
            self.axis_var[-1].set(axis[i])
            axis_entry = FloatEntry(
                rot_ctrl,
                textvariable=self.axis_var[-1],
                extra_validate=lambda v, n=i: self.check_zero_axis(v, n),
                width=float_width)
            axis_entry.grid(row=sub_row, column=column)
            axis_entry.bind("<Tab>", on_rotate)
        axis_entry.bind("<Return>", on_rotate)
        column += 1
        tk.Button(rot_ctrl,
                  text="Angle:",
                  command=on_rotate).grid(row=sub_row,
                                          column=column, sticky=tk.W)
        column += 1
        self.var_angle = tk.DoubleVar()
        self.var_angle.set(angle)
        entry_angle = FloatEntry(rot_ctrl,
                                 textvariable=self.var_angle,
                                 width=float_width)
        entry_angle.grid(row=sub_row, column=column, sticky=tk.E)
        entry_angle.bind("<Return>", on_rotate)
        entry_angle.bind("<Tab>", on_rotate)

        sub_row += 1
        # Row + / - angle entry
        column = 0
        step_down = tk.Button(rot_ctrl, text="-",
                              command=lambda: self.on_step(False))
        step_down.grid(row=sub_row, column=column, sticky=tk.W)
        column += 2
        tk.Label(rot_ctrl, text="step").grid(row=sub_row, column=column,
                                             sticky=tk.E)
        column += 1
        self.angle_step = FloatEntry(rot_ctrl, width=float_width)
        self.angle_step.insert(0, angle_init_step)
        self.angle_step.grid(row=sub_row, column=column, sticky=tk.W)
        column += 2
        step_up = tk.Button(rot_ctrl, text="+",
                            command=lambda: self.on_step(True))
        step_up.grid(row=sub_row, column=column, sticky=tk.E)

        # Row with slidebar
        row += 1
        # min / max from parameter
        slidebar = tk.Scale(self, from_=angle_domain[0], to=angle_domain[1],
                            variable=self.var_angle,
                            resolution=-1,  # no rounding
                            digits=angle_digits,
                            command=on_rotate,
                            orient=tk.HORIZONTAL)
        slidebar.grid(row=row, sticky=tk.W + tk.E)

    def check_zero_axis(self, val, index):
        allow = not geomtypes.eq(val, 0)
        if not allow:
            for i, axis_entry in enumerate(self.axis_var):
                if i != index:
                    allow = allow or not geomtypes.eq(axis_entry.get(), 0)

        # TODO: add status bar with string var if not allowed (needs reset)
        return allow

    def on_rotate(self):
        self.command(geomtypes.Rot3(
            axis=geomtypes.Vec3([axis.get() for axis in self.axis_var]),
            angle=DEG2RAD * self.var_angle.get()))

    def reset(self):
        angle = self.rotation.angle()
        self.var_angle.set(angle)
        for axis_entry, ord_val in zip(self.axis_var, self.rotation.axis()):
            axis_entry.set(ord_val)

    def on_step(self, up):
        step = float(self.angle_step.get())
        if not up:
            step = -step
        self.var_angle.set(float(self.var_angle.get()) + step)
        self.on_rotate()

    def set_angle(self, angle):
        self.var_angle.set(angle)


class ContiniousRotationUpdateWindow(tk.Toplevel):
    """Dialog window for updating rotation continiously.

    Then dialog will buttons to confirm or reset the rotation
    """
    def __init__(self, parent, title, rotation, *args, **kwargs):
        """Initialise object

        parent: parent widget. This parent is supposed to have a status bar and
                an OglFrame with a CompoundShape
        title: title to use for new dialog
        rotation: a geomtypes.Rot3 object with the initial rotation
        """
        super().__init__(parent, *args, **kwargs)
        self.attributes('-type', 'dialog')
        self.parent = parent
        self.title(title)
        self.rotation = rotation

        self.org_vs = parent.ogl_frame.shape.getVertexProperties()['Vs']
        row = -1

        row += 1
        self.rotation_gui = ContiniousRotationWidget(
            self, "Rotate shape:", rotation,
            lambda rot: self.on_rotation(rot))
        self.rotation_gui.grid(row=row, column=0)

        # Add Apply, Cancel, Reset, OK
        row += 1
        final = tk.Frame(self)
        final.columnconfigure(2, weight=1)
        final.grid(row=row, column=0, sticky=tk.W + tk.E)
        column = 0
        self.cancel = tk.Button(final, text="Cancel", command=self.on_quit)
        self.cancel.grid(row=0, column=column, sticky=tk.W)
        column += 1
        self.reset = tk.Button(final, text="Reset", command=self.on_reset)
        self.reset.grid(row=0, column=column, sticky=tk.W)
        column += 1
        self.next_text = "Apply and Next"
        self.apply_it = tk.Button(final, text=self.next_text,
                                  command=self.on_apply)
        self.apply_it.grid(row=0, column=column, sticky=tk.E)
        column += 1
        self.ok = tk.Button(final, text="OK", command=self.on_ok)
        self.ok.grid(row=0, column=column, sticky=tk.E)

        self.bind("<Escape>", lambda e: self.on_quit())
        self.bind("+", lambda e: self.rotation_gui.on_step(True))
        self.bind("-", lambda e: self.rotation_gui.on_step(False))
        self.bind("<KP_Add>", lambda e: self.rotation_gui.on_step(True))
        self.bind("<KP_Subtract>", lambda e: self.rotation_gui.on_step(False))

    def on_rotation(self, rotation):
        # Assume compound shape
        newVs = [
            [rotation * geomtypes.Vec3(v) for v in shapeVs]
            for shapeVs in self.org_vs]
        self.parent.ogl_frame.shape.setVertexProperties(Vs=newVs)
        self.parent.ogl_frame.paint()
        self.parent.update_status_bar(
            f"Use '{self.next_text}' to define a subsequent transform")

    def on_apply(self):
        self.org_vs = self.parent.ogl_frame.shape.getVertexProperties()['Vs']
        self.rotation_gui.set_angle(0)
        self.parent.update_status_bar("Appyling next rotation")
        pass

    def on_quit(self):
        self.on_reset()
        self.destroy()

    def on_reset(self):
        self.rotation_gui.reset()
        self.on_rotation(self.rotation)
        self.parent.update_status_bar("Latest rotation reset")

    def on_ok(self):
        self.parent.update_status_bar("Rotation applied")
        self.destroy()

    def show(self):
        """Show the dialog en return when it is closed."""
        self.wm_deiconify()
        self.wait_window()


#class ViewSettingsWindow(wx.Frame):
#    def __init__(this, ogl_frame, *args, **kwargs):
#        wx.Frame.__init__(this, *args, **kwargs)
#        this.ogl_frame    = ogl_frame
#        this.statusBar = this.CreateStatusBar()
#        this.panel     = wx.Panel(this, wx.ID_ANY)
#        this.addContents()
#
#    def addContents(this):
#        this.ctrlSizer = ViewSettingsSizer(this, this.panel, this.ogl_frame)
#        if this.ogl_frame.shape.dimension == 4:
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
#    def __init__(this, parentWindow, parentPanel, ogl_frame, *args, **kwargs):
#        """
#        Create a sizer with view settings.
#
#        parentWindow: the parentWindow object. This is used to update de
#                      status string in the status bar. The parent window is
#                      supposed to contain a function update_status_bar for this
#                      to work.
#        parentPanel: The panel to add all control widgets to.
#        ogl_frame: An interactive 3D ogl_frame object. This object is supposed to
#                have a shape field that points to the shape object that is
#                being viewed.
#        """
#
#        this.Guis = []
#        this.Boxes = []
#        wx.BoxSizer.__init__(this, wx.VERTICAL, *args, **kwargs)
#        this.ogl_frame       = ogl_frame
#        this.parentWindow = parentWindow
#        this.parentPanel  = parentPanel
#        # Show / Hide vertices
#        vProps            = ogl_frame.shape.getVertexProperties()
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
#        eProps           = ogl_frame.shape.getEdgeProperties()
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
#        col = this.ogl_frame.getBgCol()
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
#        if this.ogl_frame.shape.dimension == 4:
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
#                            this.ogl_frame.shape.wProjVolume
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
#                            this.ogl_frame.shape.wCameraDistance
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
#            this.ogl_frame.shape.setVertexProperties(radius = this.vR)
#        elif selStr == 'hide':
#            this.vRadiusGui.Disable()
#            this.ogl_frame.shape.setVertexProperties(radius = -1.0)
#        this.ogl_frame.paint()
#
#    def onVRadius(this, e):
#        this.vR = (float(this.vRadiusGui.GetValue()) / this.vRadiusScale)
#        this.ogl_frame.shape.setVertexProperties(radius = this.vR)
#        this.ogl_frame.paint()
#        this.update_status_bar()
#
#    def onVColor(this, e):
#        dlg = wx.ColourDialog(this.parentWindow)
#        if dlg.ShowModal() == wx.ID_OK:
#            data = dlg.GetColourData()
#            rgba = data.GetColour()
#            rgb  = rgba.Get()
#            this.ogl_frame.shape.setVertexProperties(
#                color = [float(i)/256 for i in rgb]
#            )
#            this.ogl_frame.paint()
#        dlg.Destroy()
#
#    def onEOption(this, e):
#        sel = this.eOptionsGui.GetSelection()
#        selStr = this.eOptionsLst[sel]
#        if selStr == 'hide':
#            this.eRadiusGui.Disable()
#            this.ogl_frame.shape.setEdgeProperties(drawEdges = False)
#        elif selStr == 'as cylinders':
#            this.eRadiusGui.Enable()
#            this.ogl_frame.shape.setEdgeProperties(drawEdges = True)
#            this.ogl_frame.shape.setEdgeProperties(radius = this.eR)
#        elif selStr == 'as lines':
#            this.eRadiusGui.Disable()
#            this.ogl_frame.shape.setEdgeProperties(drawEdges = True)
#            this.ogl_frame.shape.setEdgeProperties(radius = 0)
#        this.ogl_frame.paint()
#
#    def onERadius(this, e):
#        this.eR = (float(this.eRadiusGui.GetValue()) / this.eRadiusScale)
#        this.ogl_frame.shape.setEdgeProperties(radius = this.eR)
#        this.ogl_frame.paint()
#        this.update_status_bar()
#
#    def onEColor(this, e):
#        dlg = wx.ColourDialog(this.parentWindow)
#        if dlg.ShowModal() == wx.ID_OK:
#            data = dlg.GetColourData()
#            rgba = data.GetColour()
#            rgb  = rgba.Get()
#            this.ogl_frame.shape.setEdgeProperties(
#                color = [float(i)/256 for i in rgb]
#            )
#            this.ogl_frame.paint()
#        dlg.Destroy()
#
#    def onFOption(this, e):
#        print('View Settings Window size:', this.parentWindow.GetSize())
#        sel = this.fOptionsGui.GetStringSelection()
#        # Looks like I switch front and back here, but this makes sense from
#        # the GUI.
#        this.ogl_frame.shape.setFaceProperties(drawFaces = True)
#        if sel == this.cull_show_both:
#            glDisable(GL_CULL_FACE)
#        elif sel == this.cull_show_none:
#            # don't use culling here: doesn't work with edge radius and vertext
#            # radius > 0
#            this.ogl_frame.shape.setFaceProperties(drawFaces = False)
#            glDisable(GL_CULL_FACE)
#        elif sel == this.cull_show_front:
#            glCullFace(GL_FRONT)
#            glEnable(GL_CULL_FACE)
#        elif this.cull_show_back:
#            glCullFace(GL_BACK)
#            glEnable(GL_CULL_FACE)
#        this.ogl_frame.paint()
#
#    def onOgl(this, e):
#        id = e.GetId()
#        if id == this.oglFrontFaceGui.GetId():
#            onSwitchFrontBack(this.ogl_frame)
#
#    def onBgCol(this, e):
#        col = e.GetValue().Get()
#        this.ogl_frame.setBgCol(
#            [float(col[0])/255, float(col[1])/255, float(col[2])/255]
#        )
#        this.ogl_frame.paint()
#
#    def onUseTransparency(this, event):
#        this.ogl_frame.shape.useTransparency((this.useTransparencyGui.GetSelection() == 0))
#        this.ogl_frame.paint()
#
#    def onShowUnscaledEdges(this, event):
#        this.ogl_frame.shape.setEdgeProperties(
#            showUnscaled = (this.showUnscaledEdgesGui.GetSelection() == 0)
#        )
#        this.ogl_frame.paint()
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
#        this.ogl_frame.shape.setCellProperties(scale = scale)
#        this.ogl_frame.paint()
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
#        this.ogl_frame.shape.setProjectionProperties(cameraDistance, wProjVolume, dbg = True)
#        this.ogl_frame.paint()
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
#            this.ogl_frame.shape.rotate(r)
#            this.ogl_frame.paint()
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


class FieldsDialog(tk.Toplevel):
    """Base class for making floating dialog windows with some fields"""
    def __init__(self, parent, title, fields):
        """Initialise object

        parent: parent widget
        title: title to use for new dialog
        fields: an object with the following initial fields:
        """
        super().__init__(parent)
        self.attributes('-type', 'dialog')
        self.title(title)
        self.fields = fields
        self.canceled = False
        self.protocol('WM_DELETE_WINDOW', self.on_quit)

    def on_quit(self, event=None):
        self.canceled = True
        self.destroy()

    def on_ok(self, event=None):
        self.destroy()

    def show(self, focus, select=True):
        """
        Show the dialog en return the values when it is close

        focus: the widget to focus on
        select: select content on 'focus'
        return: None if the dialog is canceled (e.g. by pressing ESC) otherwise
                it will return the object "fields" from __init__ (not updated)
                It is up to the inheritant to update.
        """
        self.wm_deiconify()
        focus.focus_force()
        focus.selection_range(0, tk.END)
        self.wait_window()
        if self.canceled:
            return None
        else:
            return self.fields


class OffFields(object):
    extra_info = False
    merge_vs = False

    def __init__(self, precision=12, float_margin=10):
        self.precision = precision
        self.float_margin = float_margin


class ExportOffDialog(FieldsDialog):
    min_precision = 1
    max_precision = 16
    """
    Floating dialog for exporting a polyhedron to an OFF file.

    The settings are:
        precision: how many deimals to use for floating point number.
        extra_info: whether to add extra info in comments
        merge_vs: whether to merge vertices that are "equal" to one vertex.
        float_margin: the amount of decimals to use when deciding whether
                      vertices are equals
    """
    def __init__(self, parent, title, fields):
        """Initialise object

        parent: parent widget
        title: title to use for new dialog
        fields: an OffFields object with the following initial fields:
                precision, extra_info, merge_vs and float_margin
                This object is updated with the new values.
                This is the object that will be updated with the new values
        """
        super().__init__(parent, title, fields)

        # TODO remove extra parameters
        int_vcmd = (self.register(self.validate_if_int),
                    # the parameters in elf.validate_if_int:
                    '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        row = 0
        self.precision = tk.StringVar()
        self.precision.set(fields.precision)
        self.precision_txt = tk.Label(
            self, text="vertex precision (decimals [{}, {}])".format(
                self.min_precision, self.max_precision))
        self.precision_txt.grid(row=row, column=0, sticky=tk.W)
        self.precision_in = tk.Entry(self,
                                     textvariable=self.precision,
                                     validate='key',
                                     validatecommand=int_vcmd)
        self.precision_in.grid(row=row, column=1)

        row += 1
        self.extra_info = tk.BooleanVar()
        self.extra_info.set(fields.extra_info)
        self.extra_info_chk = tk.Checkbutton(self,
                                             text="Add extra info",
                                             variable=self.extra_info,
                                             onvalue=True,
                                             offvalue=False)
        self.extra_info_chk.grid(row=row, column=0, sticky=tk.W)

        row += 1
        self.merge_vs = tk.BooleanVar()
        self.merge_vs.set(fields.merge_vs)
        self.merge_vs_chk = tk.Checkbutton(
            self,
            text="Merge equal vertices (can take time)",
            variable=self.merge_vs,
            onvalue=True,
            offvalue=False,
            command=self.on_chk_merge)
        self.merge_vs_chk.grid(row=row, column=0, sticky=tk.W)

        row += 1
        self.float_margin = tk.StringVar()
        self.float_margin.set(fields.float_margin)
        self.float_margin_txt = tk.Label(
            self, text="vertex precision (decimals [{}, {}])".format(
                self.min_precision, self.max_precision))
        self.float_margin_txt.grid(row=row, column=0, sticky=tk.W)
        self.float_margin_in = tk.Entry(self,
                                        textvariable=self.float_margin,
                                        validate='key',
                                        validatecommand=int_vcmd)
        self.float_margin_in.grid(row=row, column=1)
        if not self.fields.merge_vs:
            self.float_margin_txt.configure(state='disabled')
            self.float_margin_in.configure(state='disabled')

        row += 1
        self.cancel = tk.Button(self, text="Cancel", command=self.on_quit)
        self.cancel.grid(row=row, column=0, sticky=tk.W)
        self.ok = tk.Button(self, text="OK", command=self.on_ok)
        self.ok.grid(row=row, column=1, sticky=tk.E)

        self.bind("<Escape>", lambda e: self.on_quit(e))

    def validate_if_int(self, action, index, value_if_allowed, prior_value,
                        text, validation_type, trigger_type, widget_name):
        allow = True
        if value_if_allowed:
            try:
                i = int(value_if_allowed)
                allow = i >= self.min_precision and i <= self.max_precision
            except ValueError:
                allow = False
        return allow

    def on_chk_merge(self):
        if self.merge_vs.get():
            self.float_margin_txt.configure(state='normal')
            self.float_margin_in.configure(state='normal')
        else:
            self.float_margin_txt.configure(state='disabled')
            self.float_margin_in.configure(state='disabled')

    def show(self):
        """
        Show the dialog en return the values when it is close

        return: None if the dialog is canceled (e.g. by pressing ESC) otherwise
                it will return the updated obeject "fields" from __init__
        """
        if super().show(self.precision_in) is None:
            return None
        else:
            self.fields.precision = int(self.precision.get())
            self.fields.extra_info = self.extra_info.get()
            self.fields.merge_vs = self.merge_vs.get()
            self.fields.float_margin = int(self.float_margin.get())
            return self.fields


class PsFields(object):
    def __init__(self, scaling=50, precision=12, float_margin=10):
        self.scaling = scaling
        self.precision = precision
        self.float_margin = float_margin


class ExportPsDialog(FieldsDialog):
    min_precision = 1
    max_precision = 16
    """
    Dialog for exporting a polyhedron to a PS file.

    Settings like: scaling size and precision. Changing these settings will
    reflect in the next dialog that is created.
    Based on wxPython example dialog
    """
    def __init__(self, parent, title, fields):
        """Initialise object

        parent: parent widget
        title: title to use for new dialog
        fields: an object with the following initial fields:
                scaling, precision and float_margin
                This object is updated with the new values.
                This is the object that will be updated with the new values
        """
        super().__init__(parent, title, fields)

        # TODO use the FloatEntry
        float_vcmd = (self.register(self.validate_if_float),
                      # the parameters in self.validate_if_float:
                      '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        # TODO: remove extra parameters
        int_vcmd = (self.register(self.validate_if_int),
                    # the parameters in self.validate_if_int:
                    '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        row = 0
        self.scaling = tk.StringVar()
        self.scaling.set(self.fields.scaling)
        self.scaling_txt = tk.Label(self, text="Scaling factor")
        self.scaling_txt.grid(row=row, column=0, sticky=tk.W)
        self.scaling_in = tk.Entry(self,
                                   textvariable=self.scaling,
                                   validate='key',
                                   validatecommand=float_vcmd)
        self.scaling_in.grid(row=row, column=1)

        row += 1
        self.precision = tk.StringVar()
        self.precision.set(self.fields.precision)
        self.precision_txt = tk.Label(
            self, text="vertex precision (decimals [{}, {}])".format(
                self.min_precision, self.max_precision))
        self.precision_txt.grid(row=row, column=0, sticky=tk.W)
        self.precision_in = tk.Entry(self,
                                     textvariable=self.precision,
                                     validate='key',
                                     validatecommand=int_vcmd)
        self.precision_in.grid(row=row, column=1)

        row += 1
        self.float_margin = tk.StringVar()
        self.float_margin.set(self.fields.float_margin)
        self.float_margin_txt = tk.Label(
            self,
            text="float margin for being equal (decimals [{}, {}])".format(
                self.min_precision, self.max_precision))
        self.float_margin_txt.grid(row=row, column=0, sticky=tk.W)
        self.float_margin_in = tk.Entry(self,
                                        textvariable=self.float_margin,
                                        validate='key',
                                        validatecommand=int_vcmd)
        self.float_margin_in.grid(row=row, column=1)

        row += 1
        self.cancel = tk.Button(self, text="Cancel", command=self.on_quit)
        self.cancel.grid(row=row, column=0, sticky=tk.W)
        self.ok = tk.Button(self, text="OK", command=self.on_ok)
        self.ok.grid(row=row, column=1, sticky=tk.E)

        self.bind("<Escape>", lambda e: self.on_quit(e))

    def validate_if_float(self, action, index, value_if_allowed, prior_value,
                          text, validation_type, trigger_type, widget_name):
        allow = True
        if value_if_allowed:
            try:
                float(value_if_allowed)
            except ValueError:
                allow = False
        return allow

    def validate_if_int(self, action, index, value_if_allowed, prior_value,
                        text, validation_type, trigger_type, widget_name):
        allow = True
        if value_if_allowed:
            try:
                i = int(value_if_allowed)
                allow = i >= self.min_precision and i <= self.max_precision
            except ValueError:
                allow = False
        return allow

    def show(self):
        """
        Show the dialog en return the values when it is close

        return: None if the dialog is canceled (e.g. by pressing ESC) otherwise
                it will return the updated obeject "fields" from __init__
        """
        if super().show(self.scaling_in) is None:
            return None
        else:
            self.fields.scaling = int(self.scaling.get())
            self.fields.precision = int(self.precision.get())
            self.fields.float_margin = int(self.float_margin.get())
            return self.fields


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
        shape = shape.clean_shape(margin)
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


if __name__ == "__main__":
    import getopt

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            'fm:P:ps:y',
            ['off', '--margin=', 'precision=', 'ps', 'scene=', 'py'])
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

    if o_fd is not None:
        o_fd.close()
