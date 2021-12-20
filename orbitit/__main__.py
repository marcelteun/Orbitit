#!/usr/bin/env python3
"""Utility for handling polyhedra"""
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

import math
import os
import sys
import wx
import wx.lib.intctrl
import wx.lib.colourselect

# pre-load a fix that can set environment variable PYOPENGL_PLATFORM
from orbitit import pre_pyopengl  # pylint: disable=wrong-import-order
from OpenGL import GL

from orbitit import (  # pylint: disable=ungrouped-imports
    Geom3D,
    geom_gui,
    geomtypes,
    Scene_24Cell,
    Scene_5Cell,
    Scene_8Cell,
    Scene_EqlHeptA5xI,
    Scene_EqlHeptA5xI_GD,
    Scene_EqlHeptA5xI_GI,
    Scene_EqlHeptFromKite,
    Scene_EqlHeptS4A4,
    Scene_EqlHeptS4xI,
    Scene_FldHeptA4,
    Scene_FldHeptA5,
    Scene_FldHeptS4,
    Scene_Rectified24Cell,
    Scene_Rectified8Cell,
    scene_orbit,
    Scenes3D,
    X3D,
)
DEFAULT_SCENE = 'scene_orbit'

SCENES = {
    'Scene_24Cell': Scene_24Cell,
    'Scene_5Cell': Scene_5Cell,
    'Scene_8Cell': Scene_8Cell,
    'Scene_EqlHeptA5xI': Scene_EqlHeptA5xI,
    'Scene_EqlHeptA5xI_GD': Scene_EqlHeptA5xI_GD,
    'Scene_EqlHeptA5xI_GI': Scene_EqlHeptA5xI_GI,
    'Scene_EqlHeptFromKite': Scene_EqlHeptFromKite,
    'Scene_EqlHeptS4A4': Scene_EqlHeptS4A4,
    'Scene_EqlHeptS4xI': Scene_EqlHeptS4xI,
    'Scene_FldHeptA4': Scene_FldHeptA4,
    'Scene_FldHeptA5': Scene_FldHeptA5,
    'Scene_FldHeptS4': Scene_FldHeptS4,
    'Scene_Rectified24Cell': Scene_Rectified24Cell,
    'Scene_Rectified8Cell': Scene_Rectified8Cell,
    'scene_orbit': scene_orbit,
}

DEG2RAD = Geom3D.Deg2Rad

# prevent warning for not being used:
del pre_pyopengl

def on_switch_front_and_back(canvas):
    """In OpenGL switch definition of what is front and back of a face"""
    if GL.glGetIntegerv(GL.GL_FRONT_FACE) == GL.GL_CCW:
        GL.glFrontFace(GL.GL_CW)
    else:
        GL.glFrontFace(GL.GL_CCW)
    canvas.paint()

class Canvas3DScene(Scenes3D.Interactive3DCanvas):
    """OpenGL canvas where the 3D shape is painted"""
    def __init__(self, shape, *args, **kwargs):
        self.shape = shape
        Scenes3D.Interactive3DCanvas.__init__(self, *args, **kwargs)

    def init_gl(self):
        """Initialise OpenGL settings"""
        self.set_cam_pos(15.0)
        Scenes3D.Interactive3DCanvas.init_gl(self)

        #GL.glShadeModel(GL.GL_SMOOTH)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_NORMAL_ARRAY)

        mat_ambient = [0.2, 0.2, 0.2, 0.0]
        mat_diffuse = [0.1, 0.6, 0.0, 0.0]
        #mat_specular = [0.2, 0.2, 0.2, 1.]
        mat_shininess = 0.0
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_AMBIENT, mat_ambient)
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_DIFFUSE, mat_diffuse)
        #GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_SPECULAR, mat_specular)
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_SHININESS, mat_shininess)

        light_pos = [10.0, -30.0, -20.0, 0.0]
        light_ambient = [0.3, 0.3, 0.3, 1.0]
        light_diffuse = [0.5, 0.5, 0.5, 1.0]
        # disable specular part:
        light_specular = [0., 0., 0., 1.]
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, light_pos)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, light_ambient)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, light_diffuse)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, light_specular)
        GL.glEnable(GL.GL_LIGHT0)

        light_pos = [-30.0, 0.0, -20.0, 0.0]
        light_ambient = [0.0, 0.0, 0.0, 1.]
        light_diffuse = [0.08, 0.08, 0.08, 1.]
        light_specular = [0.0, 0.0, 0.0, 1.]
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_POSITION, light_pos)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_AMBIENT, light_ambient)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_DIFFUSE, light_diffuse)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_SPECULAR, light_specular)
        GL.glEnable(GL.GL_LIGHT1)

        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glLightModeli(GL.GL_LIGHT_MODEL_TWO_SIDE, GL.GL_TRUE)
        GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        GL.glClearColor(self.bg_col[0], self.bg_col[1], self.bg_col[2], 0)

    @property
    def bg_col(self):
        """rgb in value between 0 and 1"""
        return self._bg_col

    @bg_col.setter
    def bg_col(self, bg_col):
        """rgb in value between 0 and 1"""
        self._bg_col = bg_col
        GL.glClearColor(bg_col[0], bg_col[1], bg_col[2], 0)

    def on_paint(self):
        """Redraw the shape on the OpenGL canvas"""
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self.shape.glDraw()

class MainWindow(wx.Frame):  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """Main window holding the shape for the orbitit program"""
    wildcard = "OFF shape (*.off)|*.off| Python shape (*.py)|*.py"
    def __init__(self, TstScene, shape, filename, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.scenes_list = list(SCENES.keys())
        self.current_scene = None
        self.current_file = None
        self.dome1 = None
        self.dome2 = None
        self.add_menu_bar()
        self.status_bar = self.CreateStatusBar()
        self.scene = None
        self.export_dir_name = '.'
        self.import_dir_name = '.'
        self.view_settings_win = None
        self.col_settings_win = None
        self.transform_settings_win = None
        self.scene = None
        self.panel = MainPanel(self, TstScene, shape, wx.ID_ANY)
        if filename and (
            filename[-4:] == '.off' or filename[-3:] == '.py'
        ):
            self.open_file(filename)
        self.Show(True)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.key_switch_front_back = wx.NewIdRef().GetId()
        ac = [
            (wx.ACCEL_NORMAL, wx.WXK_F3, self.key_switch_front_back)
        ]
        self.Bind(wx.EVT_MENU, self.on_key_down, id=self.key_switch_front_back)
        self.SetAcceleratorTable(wx.AcceleratorTable(ac))

    def add_menu_bar(self):
        """Create and add a complete menu-bar"""
        menu_bar = wx.MenuBar()
        menu_bar.Append(self.create_file_menu(), '&File')
        menu_bar.Append(self.create_edit_menu(), '&Edit')
        menu_bar.Append(self.create_view_menu(), '&View')
        menu_bar.Append(self.create_tools_menu(), '&Tools')
        self.SetMenuBar(menu_bar)

    def create_file_menu(self):
        """Create 'File' menu"""
        menu = wx.Menu()

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Open\tCtrl+O")
        self.Bind(wx.EVT_MENU, self.on_open, id = menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Reload\tCtrl+R")
        self.Bind(wx.EVT_MENU, self.on_reload, id = menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Add\tCtrl+A")
        self.Bind(wx.EVT_MENU, self.on_add, id = menu_item.GetId())
        menu.Append(menu_item)
        export = wx.Menu()

        menu_item = wx.MenuItem(export, wx.ID_ANY, text = "&Python\tCtrl+Y")
        self.Bind(wx.EVT_MENU, self.on_save_py, id = menu_item.GetId())
        export.Append(menu_item)

        menu_item = wx.MenuItem(export, wx.ID_ANY, text = "&Off\tCtrl+E")
        self.Bind(wx.EVT_MENU, self.on_save_off, id = menu_item.GetId())
        export.Append(menu_item)

        menu_item = wx.MenuItem(export, wx.ID_ANY, text = "&PS\tCtrl+P")
        self.Bind(wx.EVT_MENU, self.on_save_ps, id = menu_item.GetId())
        export.Append(menu_item)

        menu_item = wx.MenuItem(export, wx.ID_ANY, text = "&VRML\tCtrl+V")
        self.Bind(wx.EVT_MENU, self.on_save_wrl, id = menu_item.GetId())
        export.Append(menu_item)

        menu.AppendSubMenu(export, "&Export")
        menu.AppendSeparator()
        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "E&xit\tCtrl+Q")
        self.Bind(wx.EVT_MENU, self.on_exit, id = menu_item.GetId())
        menu.Append(menu_item)
        return menu

    def create_edit_menu(self):
        """Create 'Edit' menu"""
        menu = wx.Menu()

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&View Settings\tCtrl+W")
        self.Bind(wx.EVT_MENU, self.on_view_settings, id = menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Colours\tCtrl+C")
        self.Bind(wx.EVT_MENU, self.on_col_settings, id = menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Transform\tCtrl+T")
        self.Bind(wx.EVT_MENU, self.on_transform, id = menu_item.GetId())
        menu.Append(menu_item)

        return menu

    def create_tools_menu(self):
        """Create 'Tools' menu"""
        menu = wx.Menu()
        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Dome Level 1\td")
        self.Bind(wx.EVT_MENU, self.on_dome, id = menu_item.GetId())
        menu.Append(menu_item)
        self.dome1 = menu_item

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Dome Level 2\tShift+D")
        self.Bind(wx.EVT_MENU, self.on_dome, id = menu_item.GetId())
        menu.Append(menu_item)
        self.dome2 = menu_item

        return menu

    def create_view_menu(self):
        """Create 'View' menu"""
        menu = wx.Menu()
        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Reset\tF5")
        self.Bind(wx.EVT_MENU, self.on_view_reset, id = menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Scene...")
        self.Bind(wx.EVT_MENU, self.on_view_scene, id = menu_item.GetId())
        menu.Append(menu_item)
        return menu

    def on_reload(self, _):
        """Handle event '_' to reset current scene or file"""
        if self.current_file is not None:
            self.open_file(self.current_file)
        elif self.current_scene is not None:
            self.set_scene(self.current_scene)

    def on_open(self, _):
        """Handle event '_' to open file"""
        dlg = wx.FileDialog(self, 'New: Choose a file',
                self.import_dir_name, '', self.wildcard, wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            if dirname is not None:
                filename = os.path.join(dirname, filename)
            self.open_file(filename)
        dlg.Destroy()

    def read_shape_file(self, filename):
        """Return shape defined in file with 'filename'"""
        is_off_model = filename[-3:] == 'off'
        print("opening file:", filename)
        fd = open(filename, 'r')
        if is_off_model:
            shape = Geom3D.readOffFile(fd, recreateEdges = True)
        else:
            assert filename[-2:] == 'py'
            shape = Geom3D.readPyFile(fd)
        self.set_status_text("file opened")
        fd.close()
        return shape

    def open_file(self, filename):
        """Open the shape file with 'filename' and update shape"""
        self.close_current_scene()
        dirname = os.path.dirname(filename)
        if dirname != "":
            self.import_dir_name = dirname
        try:
            shape = self.read_shape_file(filename)
        except AssertionError:
            self.set_status_text("ERROR reading file")
            raise
        if isinstance(shape, Geom3D.CompoundShape):
            # convert to SimpleShape first, since adding to IsometricShape
            # will not work.
            shape = shape.simple_shape
        # Create a compound shape to be able to add shapes later.
        shape = Geom3D.CompoundShape([shape], name = filename)
        self.panel.shape = shape
        # overwrite the view properties, if the shape doesn't have any
        # faces and would be invisible to the user otherwise
        if len(shape.getFaceProperties()['Fs']) == 0 and (
            self.panel.shape.getVertexProperties()['radius'] <= 0
        ):
            self.panel.shape.setVertexProperties(radius = 0.05)
        self.SetTitle(os.path.basename(filename))
        # Save for reload:
        self.current_file = filename
        self.current_scene = None

    def on_add(self, _):
        """Handle event '_' to add file to the current shape"""
        dlg = wx.FileDialog(self, 'Add: Choose a file',
                self.import_dir_name, '', self.wildcard, wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            is_off_model = filename[-3:] == 'off'
            self.import_dir_name  = dlg.GetDirectory()
            print("adding file:", filename)
            fd = open(os.path.join(self.import_dir_name, filename), 'r')
            if is_off_model:
                shape = Geom3D.readOffFile(fd, recreateEdges = True)
            else:
                shape = Geom3D.readPyFile(fd)
            if isinstance(shape, Geom3D.CompoundShape):
                # convert to SimpleShape first, since adding a IsometricShape
                # will not work.
                shape = shape.simple_shape
            try:
                self.panel.shape.addShape(shape)
            except AttributeError:
                print("warning: cannot 'add' a shape to this scene, use 'File->Open' instead")
            self.set_status_text("OFF file added")
            fd.close()
            # TODO: set better title
            self.SetTitle(f'Added: {os.path.basename(filename)}')
        dlg.Destroy()

    def on_save_py(self, _):
        """Handle event '_' to export the current shape to python file"""
        dlg = wx.FileDialog(self, 'Save as .py file',
            self.export_dir_name, '', '*.py',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            filename = dlg.GetFilename()
            self.export_dir_name  = filepath.rsplit('/', 1)[0]
            name_ext = filename.split('.')
            if len(name_ext) == 1:
                filename = f'{filename}.py'
            elif name_ext[-1].lower() != 'py':
                if name_ext[-1] != '':
                    filename = f'{filename}.py'
                else:
                    filename = f'{filename}py'
            fd = open(filepath, 'w')
            print(f"writing to file {filepath}")
            # TODO precision through setting:
            shape = self.panel.shape
            shape.name = filename
            shape.saveFile(fd)
            self.set_status_text("Python file written")
        dlg.Destroy()

    def on_save_off(self, _):
        """Handle event '_' to save the current shape as off-file"""
        dlg = ExportOffDialog(self, wx.ID_ANY, 'OFF settings')
        file_chosen = False
        while not file_chosen:
            if dlg.ShowModal() == wx.ID_OK:
                extra_data = dlg.get_extra_data()
                clean_up = dlg.get_clean_up()
                precision = dlg.get_precision()
                margin = dlg.get_float_margin()
                file_dlg = wx.FileDialog(self, 'Save as .off file',
                    self.export_dir_name, '', '*.off',
                    wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                )
                file_chosen = file_dlg.ShowModal() == wx.ID_OK
                if file_chosen:
                    filepath = file_dlg.GetPath()
                    filename = file_dlg.GetFilename()
                    self.export_dir_name  = filepath.rsplit('/', 1)[0]
                    name_ext = filename.split('.')
                    if len(name_ext) == 1:
                        filename = f'{filename}.off'
                    elif name_ext[-1].lower() != 'off':
                        if name_ext[-1] != '':
                            filename = f'{filename}.off'
                        else:
                            filename = f'{filename}off'
                    fd = open(filepath, 'w')
                    print(f"writing to file {filepath}")
                    shape = self.panel.shape
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    if clean_up:
                        shape = shape.cleanShape(margin)
                    fd.write(shape.toOffStr(precision, extra_data))
                    self.set_status_text("OFF file written")
                    fd.close()
                else:
                    dlg.Show()
                file_dlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def on_save_ps(self, _):
        """Handle event '_' to save PostScript faces of the current shape"""
        dlg = ExportPsDialog(self, wx.ID_ANY, 'PS settings')
        file_chosen = False
        while not file_chosen:
            if dlg.ShowModal() == wx.ID_OK:
                scale_factor = dlg.get_scaling()
                precision = dlg.get_precision()
                margin = dlg.get_float_margin()
                assert (scale_factor >= 0 and scale_factor is not None)
                file_dlg = wx.FileDialog(self, 'Save as .ps file',
                    self.export_dir_name, '', '*.ps',
                    style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                )
                file_chosen = file_dlg.ShowModal() == wx.ID_OK
                if file_chosen:
                    filepath = file_dlg.GetPath()
                    filename = file_dlg.GetFilename()
                    self.export_dir_name  = filepath.rsplit('/', 1)[0]
                    name_ext = filename.split('.')
                    if len(name_ext) == 1:
                        filename = f'{filename}.ps'
                    elif name_ext[-1].lower() != 'ps':
                        if name_ext[-1] != '':
                            filename = f'{filename}.ps'
                        else:
                            filename = f'{filename}ps'
                    # Note: if file exists is part of file dlg...
                    fd = open(filepath, 'w')
                    print(f"writing to file {filepath}")
                    shape = self.panel.shape
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    shape = shape.cleanShape(margin)
                    try:
                        fd.write(
                            shape.toPsPiecesStr(
                                scaling = scale_factor,
                                precision = precision,
                                margin = math.pow(10, -margin)
                            )
                        )
                        self.set_status_text("PS file written")
                    except Geom3D.PrecisionError:
                        self.set_status_text(
                            "Precision error, try to decrease float margin")

                    fd.close()
                else:
                    dlg.Show()
                file_dlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def on_save_wrl(self, _):
        """Handle event '_' to export the current shape to VRML format"""
        dlg = wx.FileDialog(self,
            'Save as .vrml file', self.export_dir_name, '', '*.wrl',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            filename = dlg.GetFilename()
            self.export_dir_name  = filepath.rsplit('/', 1)[0]
            name_ext = filename.split('.')
            if len(name_ext) == 1:
                filename = f'{filename}.wrl'
            elif name_ext[-1].lower() != 'wrl':
                if name_ext[-1] != '':
                    filename = f'{filename}.wrl'
                else:
                    filename = f'{filename}wrl'
            fd = open(filepath, 'w')
            print(f"writing to file {filepath}")
            # TODO precision through setting:
            r = self.panel.shape.getEdgeProperties()['radius']
            x3d_obj = self.panel.shape.toX3dDoc(edgeRadius = r)
            x3d_obj.setFormat(X3D.VRML_FMT)
            fd.write(x3d_obj.toStr())
            self.set_status_text("VRML file written")
            fd.close()
        dlg.Destroy()

    def on_view_settings(self, _):
        """Handle event '_' to load the view settings"""
        if self.view_settings_win is None:
            self.view_settings_win = ViewSettingsWindow(self.panel.canvas,
                None, wx.ID_ANY,
                title = 'View Settings',
                size = (394, 300)
            )
            self.view_settings_win.Bind(wx.EVT_CLOSE, self.on_view_win_closed)
        else:
            self.view_settings_win.SetFocus()
            self.view_settings_win.Raise()

    def on_col_settings(self, _):
        """Handle event '_' to change the colours of the current shape"""
        if not self.col_settings_win is None:
            # Don't reuse, the colours might be wrong after loading a new model
            self.col_settings_win.Destroy()
        self.col_settings_win = ColourWindow(
            self.panel.canvas, 5, None, wx.ID_ANY,
            title = 'Colour Settings',
        )
        self.col_settings_win.Bind(wx.EVT_CLOSE, self.on_col_win_closed)

    def on_transform(self, _):
        """Handle event '_' to transform the current shape"""
        if self.transform_settings_win is None:
            self.transform_settings_win = TransformWindow(
                self.panel.canvas, None, wx.ID_ANY,
                title = 'Transform Settings',
            )
            self.transform_settings_win.Bind(wx.EVT_CLOSE, self.on_transform_win_closed)
        else:
            self.transform_settings_win.SetFocus()
            self.transform_settings_win.Raise()

    def on_dome(self, event):
        """Handle event '_' to apply dome effect"""
        if self.dome1.GetId() == event.GetId():
            level = 1
        else:
            level = 2
        shape = self.panel.shape.getDome(level)
        if shape is not None:
            self.panel.shape = shape
            self.SetTitle(f"Dome({self.GetTitle()})")

    def on_view_scene(self, _):
        """Handle event '_' change the current scene"""
        dlg = wx.SingleChoiceDialog(self,'Choose a Scene', '', self.scenes_list)
        if dlg.ShowModal() == wx.ID_OK:
            scene_index = dlg.GetSelection()
            frame.load_scene(SCENES[self.scenes_list[scene_index]])
        dlg.Destroy()

    def load_scene(self, scene):
        """ Set the current scene to the scene with the specified name"""
        scene = {
            'lab': scene.TITLE,
            'class': scene.Scene,
        }
        self.set_scene(scene)

    def set_scene(self, scene):
        """
        Set the current scene to scene dictionary 'scene'

        scene: a dictionary with key 'lab' and 'class', where 'lab' is the class name (string) and
            'class' is the python class.
        """
        self.close_current_scene()
        print(f"Switch to scene: \"{scene['lab']}\".")
        canvas = self.panel.canvas
        self.scene = scene['class'](self, canvas)
        self.panel.shape = self.scene.shape
        self.SetTitle(scene['lab'])
        canvas.resetOrientation()
        try:
            self.view_settings_win.rebuild()
        except AttributeError:
            pass
        # save for reload:
        self.current_scene = scene
        self.current_file = None

    def on_view_reset(self, _):
        """Handle event '_' to reset shape orientation to the default"""
        self.panel.canvas.resetOrientation()

    def close_current_scene(self):
        """Close the current scene"""
        if self.scene is not None:
            self.scene.close()
            del self.scene
            self.scene = None

    def set_status_text(self, s):
        """Set window status bar to string 's'"""
        self.status_bar.SetStatusText(s)

    def on_exit(self, _):
        """Handle event '_' to quite application"""
        dlg = wx.MessageDialog(None,
                               'Are you sure you want to quit?', 'Question',
                               wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            dlg.Destroy()
            self.Close(True)
        else:
            dlg.Destroy()

    def on_view_win_closed(self, _):
        """Handle event '_' that destroys view settings window"""
        self.view_settings_win.Destroy()
        self.view_settings_win = None

    def on_col_win_closed(self, _):
        """Handle event '_' that destroys colour settings window"""
        self.col_settings_win.Destroy()
        self.col_settings_win = None

    def on_transform_win_closed(self, _):
        """Handle event '_' that destroys transform window"""
        self.transform_settings_win.Destroy()
        self.transform_settings_win = None

    def on_close(self, _):
        """Handle event '_' to close the main window"""
        print('main onclose')
        if self.view_settings_win is not None:
            self.view_settings_win.Close()
        if self.col_settings_win is not None:
            self.col_settings_win.Close()
        if self.transform_settings_win is not None:
            self.transform_settings_win.Close()
        self.Destroy()

    def on_key_down(self, e):
        """Handle event 'e' when a key is pressed"""
        if e.GetId() == self.key_switch_front_back:
            on_switch_front_and_back(self.panel.canvas)

class MainPanel(wx.Panel):
    """Main orbitit window holding showing a shape in 3 dimensions"""
    def __init__(self, parent, TstScene, shape, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        # Note that uncommenting this will override the default size
        # handler, which resizes the sizers that are part of the Frame.
        self.Bind(wx.EVT_SIZE, self.on_size)

        self.canvas = TstScene(shape, self)
        self.canvas.panel = self
        self.canvas.SetMinSize((300, 300))
        self.canvas_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.canvas_sizer.Add(self.canvas, 1, wx.SHAPED)

        # Ctrl Panel:
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.canvas_sizer, 1, wx.SHAPED)
        self.SetSizer(main_sizer)
        self.SetAutoLayout(True)
        self.Layout()

    def on_size(self, _):
        """Handle event '_' generated when the window size is changed

        This function is used to set the ctrl window size in the interactively.
        Bind this function, and read and set the correct size in the scene.
        """
        s = self.GetClientSize()
        print('Window size:', (s[0]+2, s[1]+54))
        self.Layout()

    @property
    def shape(self):
        """Return the current shape object"""
        return self.canvas.shape

    @shape.setter
    def shape(self, shape):
        """Set a new shape to be shown with the current viewing settings

        shape: the new shape. This will refresh the canvas.
        """
        old_shape = self.canvas.shape
        self.canvas.shape = shape
        # Use all the vertex settings except for Vs, i.e. keep the view
        # vertex settings the same.
        old_v_settings = old_shape.getVertexProperties()
        del old_v_settings['Vs']
        del old_v_settings['Ns']
        self.canvas.shape.setVertexProperties(old_v_settings)
        # Use all the edge settings except for Es
        old_e_settings = old_shape.getEdgeProperties()
        del old_e_settings['Es']
        self.canvas.shape.setEdgeProperties(old_e_settings)
        # Use only the 'drawFaces' setting:
        old_f_settings = {
                'drawFaces': old_shape.getFaceProperties()['drawFaces']
            }
        self.canvas.shape.setFaceProperties(old_f_settings)
        # if the shape generates the normals itself:
        # TODO: handle that this.Ns is set correctly, i.e. normalised
        if shape.generateNormals:
            GL.glDisable(GL.GL_NORMALIZE)
        else:
            GL.glEnable(GL.GL_NORMALIZE)
        self.canvas.paint()
        self.parent.set_status_text("Shape Updated")
        del old_shape

class ColourWindow(wx.Frame):  # pylint: disable=too-many-instance-attributes
    """Window enabling the user to change the face colours of a shape"""
    def __init__(self, canvas, width, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas = canvas
        self.col_width = width
        self.status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.cols = self.canvas.shape.getFaceProperties()['colors']
        # take a copy for reset
        self.org_cols = [[list(col_idx) for col_idx in shape_cols] for shape_cols in self.cols]
        self.add_content()

    def add_content(self):
        """Add all widgets to the window for updating the shape colours"""
        self.col_sizer = wx.BoxSizer(wx.VERTICAL)

        self.select_col_guis = []
        i = 0
        shape_idx = 0
        # assume compound shape
        for shape_cols in self.cols:
            # use one colour select per colour for each sub-shape
            added_cols = []
            col_idx = 0
            for col in shape_cols[0]:
                wx_col = wx.Colour(255*col[0], 255*col[1], 255*col[2])
                if wx_col not in added_cols:
                    if i % self.col_width == 0:
                        col_sizer_row = wx.BoxSizer(wx.HORIZONTAL)
                        self.col_sizer.Add(col_sizer_row, 0, wx.EXPAND)
                    self.select_col_guis.append(
                        wx.ColourPickerCtrl(
                            self.panel, wx.ID_ANY, wx_col))
                    self.panel.Bind(wx.EVT_COLOURPICKER_CHANGED, self.on_col_select)
                    col_sizer_row.Add(self.select_col_guis[-1], 0, wx.EXPAND)
                    i += 1
                    # connect GUI to shape_idx and col_idx
                    self.select_col_guis[-1].my_shape_idx = shape_idx
                    self.select_col_guis[-1].my_cols = [col_idx]
                    # connect wx_col to GUI
                    wx_col.my_gui = self.select_col_guis[-1]
                    added_cols.append(wx_col)
                else:
                    gui = added_cols[added_cols.index(wx_col)].my_gui
                    # must be same shape_id
                    gui.my_cols.append(col_idx)
                col_idx += 1
            shape_idx += 1

        self.guis = []

        self.sub_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.col_sizer.Add(self.sub_sizer)

        self.guis.append(wx.Button(self.panel, label='Cancel'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_cancel)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Reset'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_reset)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Done'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_done)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.panel.SetSizer(self.col_sizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    def on_reset(self, _):
        """Handle event '_' to recover original widget and shape colours"""
        for col_gui in self.select_col_guis:
            shape_idx = col_gui.my_shape_idx
            col_idx = col_gui.my_cols[0]
            c = self.org_cols[shape_idx][0][col_idx]
            wx_col = wx.Colour(255*c[0], 255*c[1], 255*c[2])
            col_gui.SetColour(wx_col)
        self.cols = [[list(col_idx) for col_idx in shape_cols] for shape_cols in self.org_cols]
        self.update_shape_cols()

    def on_cancel(self, _):
        """Handle event '_' to recover original shape colours and close window"""
        self.cols = [[list(col_idx) for col_idx in shape_cols] for shape_cols in self.org_cols]
        self.update_shape_cols()
        self.Close()

    def on_done(self, _):
        """Handle event '_' to confirms all colours"""
        self.Close()

    def on_col_select(self, e):
        """Handle event 'e' that is generated when a colour was updated"""
        wx_col = e.GetColour().Get()
        col = (float(wx_col[0])/255, float(wx_col[1])/255, float(wx_col[2])/255)
        gui_id = e.GetId()
        for gui in self.select_col_guis:
            if gui.GetId() == gui_id:
                shape_cols = self.cols[gui.my_shape_idx][0]
                for col_idx in gui.my_cols:
                    shape_cols[col_idx] = col
                self.update_shape_cols()

    def update_shape_cols(self):
        """Update the face colours of the current shape"""
        self.canvas.shape.setFaceProperties(colors=self.cols)
        self.canvas.paint()

    def close(self):
        """Destroy all widgets of the face colour window"""
        for gui in self.guis:
            gui.Destroy()

class TransformWindow(wx.Frame):  # pylint: disable=too-many-instance-attributes
    """Window with controls for transforming current shape

    The transform is applied dynamically (i.e. while window is still open), but can be canceled.
    """
    def __init__(self, canvas, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas = canvas
        self.status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.add_content()
        self.org_vs = self.canvas.shape.getVertexProperties()['Vs']
        self.org_org_vs = self.org_vs # for cancel
        self.set_status_text("")

    def add_content(self):
        """Create all wdigets for the transform window"""
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.rot_sizer = geom_gui.AxisRotateSizer(
            self.panel,
            self.on_rot,
            min_angle=-180,
            max_angle=180,
            initial_angle=0
        )
        self.main_sizer.Add(self.rot_sizer)

        self.guis = []

        # TODO: Add scale to transform
        # TODO: Add reflection

        # Transform
        translate_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(translate_sizer)
        self.guis.append(geom_gui.Vector3DInput(self.panel, "Translation vector:"))
        self.translation = self.guis[-1]
        translate_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        self.guis.append(wx.Button(self.panel, label='Translate'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_translate)
        translate_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        # Invert
        invert_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(invert_sizer)
        self.guis.append(wx.Button(self.panel, label='Invert'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_invert)
        invert_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.sub_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(self.sub_sizer)

        self.guis.append(wx.Button(self.panel, label='Apply'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_apply)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Cancel'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_cancel)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Reset'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_reset)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Done'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_done)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.panel.SetSizer(self.main_sizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    def on_rot(self, angle, axis):
        """Rotate shape"""
        if Geom3D.eq(axis.norm(), 0):
            self.set_status_text("Please define a proper axis")
            return
        transform = geomtypes.Rot3(angle=DEG2RAD*angle, axis=axis)
        # Assume compound shape
        new_vs = [
            [transform * geomtypes.Vec3(v) for v in shape_vs] for shape_vs in self.org_vs]
        self.canvas.shape.setVertexProperties(Vs=new_vs)
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_invert(self, _=None):
        """Handle event '_' to invert shape"""
        # Assume compound shape
        new_vs = [
            [-geomtypes.Vec3(v) for v in shape_vs] for shape_vs in self.org_vs]
        self.canvas.shape.setVertexProperties(Vs=new_vs)
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_translate(self, _=None):
        """Handle event '_' to translate shape"""
        # Assume compound shape
        new_vs = [
            [geomtypes.Vec3(v) + self.translation.get_vertex()
             for v in shape_vs] for shape_vs in self.org_vs]
        self.canvas.shape.setVertexProperties(Vs=new_vs)
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_apply(self, _=None):
        """Handle event '_' to confirm transform and prepare for a next one"""
        self.org_vs = self.canvas.shape.getVertexProperties()['Vs']
        # reset the angle
        self.rot_sizer.set_angle(0)
        self.set_status_text("applied, now you can define another axis")

    def on_reset(self, _=None):
        """Handle event '_' to undo all transforms"""
        self.canvas.shape.setVertexProperties(Vs=self.org_org_vs)
        self.canvas.paint()
        self.org_vs = self.org_org_vs

    def on_cancel(self, _=None):
        """Handle event '_' to cancel the current transform"""
        self.on_reset()
        self.Close()

    def on_done(self, _):
        """Handle event '_' to confirm all transforms are done"""
        self.Close()

    def close(self):
        """Destroy all gius for this window"""
        for gui in self.guis:
            gui.Destroy()

    def set_status_text(self, s):
        """Set text of the status bar for this window"""
        self.status_bar.SetStatusText(s)

class ViewSettingsWindow(wx.Frame):
    """Class for window with all view settings"""
    def __init__(self, canvas, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas    = canvas
        self.status_bar = self.CreateStatusBar()
        self.panel     = wx.Panel(self, wx.ID_ANY)
        self.add_contents()

    def add_contents(self):
        """Fill window with all widgets"""
        self.ctrl_sizer = ViewSettingsSizer(self, self.panel, self.canvas)
        if self.canvas.shape.dimension == 4:
            self.set_default_size((413, 791))
        else:
            self.set_default_size((380, 414))
        self.panel.SetSizer(self.ctrl_sizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    # move to general class
    def set_default_size(self, size):
        """Set dedault window size"""
        self.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        self.SetSize(size)

    def rebuild(self):
        """Detroy and re-build the content of this windown"""
        # Doesn't work out of the box (Guis are not destroyed...):
        #self.ctrl_sizer.Destroy()
        self.ctrl_sizer.close()
        self.add_contents()

    def set_status_text(self, s):
        """Set text of the status bar for this window"""
        self.status_bar.SetStatusText(s)

class ViewSettingsSizer(wx.BoxSizer):  # pylint: disable=too-many-instance-attributes
    """A sizer with all view settings for the view settings window"""

    cull_show_none  = 'Hide'
    cull_show_both  = 'Show Front and Back Faces'
    cull_show_front = 'Show Only Front Face'
    cull_show_back  = 'Show Only Back Face'

    # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    def __init__(self, parent_win, parent_panel, canvas, *args, **kwargs):
        """
        Create a sizer with view settings.

        parent_win: the parent_win object. This is used to update de status string in the status
                    bar. The parent window is supposed to contain a function set_status_text for
                    this to work.
        parent_panel: The panel to add all control widgets to.
        canvas: An interactive 3D canvas object. This object is supposed to have a shape field that
                points to the shape object that is being viewed.
        """

        self.guis = []
        self.boxes = []
        wx.BoxSizer.__init__(self, wx.VERTICAL, *args, **kwargs)
        self.canvas = canvas
        self.parent_win = parent_win
        self.parent_panel = parent_panel
        # Show / Hide vertices
        v_props = canvas.shape.getVertexProperties()
        self.v_r = v_props['radius']
        self.v_opts_lst = ['hide', 'show']
        if self.v_r > 0:
            default = 1 # key(1) = 'show'
        else:
            default = 0 # key(0) = 'hide'
        self.v_opts_gui  = wx.RadioBox(self.parent_panel,
            label = 'Vertex Options',
            style = wx.RA_VERTICAL,
            choices = self.v_opts_lst
        )
        self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_v_option, id = self.v_opts_gui.GetId())
        self.v_opts_gui.SetSelection(default)
        # Vertex Radius
        no_of_slider_steps = 40
        self.v_r_min = 0.01
        self.v_r_max = 0.100
        self.v_r_scale = 1.0 / self.v_r_min
        s = (self.v_r_max - self.v_r_min) * self.v_r_scale
        if int(s) < no_of_slider_steps:
            self.v_r_scale = (self.v_r_scale * no_of_slider_steps) / s
        self.v_r_gui = wx.Slider(self.parent_panel,
            value = self.v_r_scale * self.v_r,
            minValue = self.v_r_scale * self.v_r_min,
            maxValue = self.v_r_scale * self.v_r_max,
            style = wx.SL_HORIZONTAL
        )
        self.guis.append(self.v_r_gui)
        self.parent_panel.Bind(wx.EVT_SLIDER, self.on_v_radius, id = self.v_r_gui.GetId())
        self.boxes.append(wx.StaticBox(self.parent_panel, label = 'Vertex radius'))
        v_r_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        # disable if vertices are hidden anyway:
        if default != 1:
            self.v_r_gui.Disable()
        # Vertex Colour
        self.v_col_gui = wx.Button(self.parent_panel, wx.ID_ANY, "Colour")
        self.guis.append(self.v_col_gui)
        self.parent_panel.Bind(wx.EVT_BUTTON, self.on_v_col, id = self.v_col_gui.GetId())
        # Show / hide edges
        e_props = canvas.shape.getEdgeProperties()
        self.e_r = e_props['radius']
        self.e_opts_lst = ['hide', 'as cylinders', 'as lines']
        if e_props['drawEdges']:
            if self.v_r > 0:
                default = 1 # key(1) = 'as cylinders'
            else:
                default = 2 # key(2) = 'as lines'
        else:
            default     = 0 # key(0) = 'hide'
        self.e_opts_gui = wx.RadioBox(self.parent_panel,
            label = 'Edge Options',
            style = wx.RA_VERTICAL,
            choices = self.e_opts_lst
        )
        self.guis.append(self.e_opts_gui)
        self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_e_option, id = self.e_opts_gui.GetId())
        self.e_opts_gui.SetSelection(default)
        # Edge Radius
        no_of_slider_steps = 40
        self.e_r_min = 0.008
        self.e_r_max = 0.08
        self.e_r_scale = 1.0 / self.e_r_min
        s = (self.e_r_max - self.e_r_min) * self.e_r_scale
        if int(s) < no_of_slider_steps:
            self.e_r_scale = (self.e_r_scale * no_of_slider_steps) / s
        self.e_r_gui = wx.Slider(self.parent_panel,
            value = self.e_r_scale * self.e_r,
            minValue = self.e_r_scale * self.e_r_min,
            maxValue = self.e_r_scale * self.e_r_max,
            style = wx.SL_HORIZONTAL
        )
        self.guis.append(self.e_r_gui)
        self.parent_panel.Bind(wx.EVT_SLIDER, self.on_e_radius, id = self.e_r_gui.GetId())
        self.boxes.append(wx.StaticBox(self.parent_panel, label = 'Edge radius'))
        e_r_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        # disable if edges are not drawn as scalable items anyway:
        if default != 1:
            self.e_r_gui.Disable()
        # Edge Colour
        self.e_col_gui = wx.Button(self.parent_panel, wx.ID_ANY, "Colour")
        self.guis.append(self.e_col_gui)
        self.parent_panel.Bind(wx.EVT_BUTTON, self.on_e_col, id = self.e_col_gui.GetId())
        # Show / hide face
        self.f_opts_lst = [
            self.cull_show_both,
            self.cull_show_front,
            self.cull_show_back,
            self.cull_show_none,
        ]
        self.f_opts_gui = wx.RadioBox(self.parent_panel,
            label = 'Face Options',
            style = wx.RA_VERTICAL,
            choices = self.f_opts_lst
        )
        self.guis.append(self.f_opts_gui)
        self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_f_option, id = self.f_opts_gui.GetId())
        f_sizer = wx.BoxSizer(wx.HORIZONTAL)
        f_sizer.Add(self.f_opts_gui, 1, wx.EXPAND)
        if not GL.glIsEnabled(GL.GL_CULL_FACE):
            self.f_opts_gui.SetStringSelection(self.cull_show_both)
        else:
            # Looks like I switch front and back here, but this makes sense from
            # the GUI.
            if GL.glGetInteger(GL.GL_CULL_FACE_MODE) == GL.GL_FRONT:
                self.f_opts_gui.SetStringSelection(self.cull_show_front)
            if GL.glGetInteger(GL.GL_CULL_FACE_MODE) == GL.GL_BACK:
                self.f_opts_gui.SetStringSelection(self.cull_show_back)
            else: # ie GL.GL_FRONT_AND_BACK
                self.f_opts_gui.SetStringSelection(self.cull_show_none)

        # Open GL
        self.boxes.append(wx.StaticBox(self.parent_panel,
                                                label = 'OpenGL Settings'))
        back_front_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        self.guis.append(
            wx.CheckBox(self.parent_panel,
                                label = 'Switch Front and Back Face (F3)')
        )
        self.front_back_gui = self.guis[-1]
        self.front_back_gui.SetValue(GL.glGetIntegerv(GL.GL_FRONT_FACE) == GL.GL_CW)
        self.parent_panel.Bind(wx.EVT_CHECKBOX, self.on_front_back,
                                        id = self.front_back_gui.GetId())
        # background Colour
        col_txt = wx.StaticText(self.parent_panel, -1, "Background Colour: ")
        self.guis.append(col_txt)
        col = self.canvas.bg_col
        self.bg_col_gui = wx.lib.colourselect.ColourSelect(self.parent_panel,
            wx.ID_ANY, colour = (col[0]*255, col[1]*255, col[2]*255),
            size=wx.Size(40, 30))
        self.guis.append(self.bg_col_gui)
        self.parent_panel.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
            self.on_bg_col)

        # Sizers
        v_r_sizer.Add(self.v_r_gui, 1, wx.EXPAND | wx.TOP | wx.LEFT)
        v_r_sizer.Add(self.v_col_gui, 1, wx.BOTTOM | wx.LEFT)
        e_r_sizer.Add(self.e_r_gui, 1, wx.EXPAND | wx.TOP | wx.LEFT)
        e_r_sizer.Add(self.e_col_gui, 1, wx.BOTTOM | wx.LEFT)
        #sizer = wx.BoxSizer(wx.VERTICAL)
        v_sizer = wx.BoxSizer(wx.HORIZONTAL)
        v_sizer.Add(self.v_opts_gui, 2, wx.EXPAND)
        v_sizer.Add(v_r_sizer, 5, wx.EXPAND)
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)
        e_sizer.Add(self.e_opts_gui, 2, wx.EXPAND)
        e_sizer.Add(e_r_sizer, 5, wx.EXPAND)
        bg_sizer_sub = wx.BoxSizer(wx.HORIZONTAL)
        bg_sizer_sub.Add(col_txt, 0, wx.EXPAND)
        bg_sizer_sub.Add(self.bg_col_gui, 0, wx.EXPAND)
        bg_sizer_sub.Add(wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND)
        back_front_sizer.Add(self.front_back_gui, 0, wx.EXPAND)
        back_front_sizer.Add(bg_sizer_sub, 0, wx.EXPAND)
        self.Add(v_sizer, 5, wx.EXPAND)
        self.Add(e_sizer, 5, wx.EXPAND)
        self.Add(f_sizer, 6, wx.EXPAND)
        self.Add(back_front_sizer, 0, wx.EXPAND)

        # 4D stuff
        if self.canvas.shape.dimension == 4:
            default = 0
            self.use_transparency_gui = wx.RadioBox(
                self.parent_panel,
                label = 'Use Transparency',
                style = wx.RA_VERTICAL,
                choices = ['Yes', 'No']
            )
            self.guis.append(self.use_transparency_gui)
            self.parent_panel.Bind(
                wx.EVT_RADIOBOX,
                self.on_use_transparent,
                id = self.use_transparency_gui.GetId(),
            )
            self.use_transparency_gui.SetSelection(default)
            f_sizer.Add(self.use_transparency_gui, 1, wx.EXPAND)

            default = 0
            self.show_es_unscaled_gui = wx.RadioBox(self.parent_panel,
                label = 'Unscaled Edges',
                style = wx.RA_VERTICAL,
                choices = ['Show', 'Hide']
            )
            self.guis.append(self.show_es_unscaled_gui)
            self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_show_unscaled_es, id =
            self.show_es_unscaled_gui.GetId())
            self.show_es_unscaled_gui.SetSelection(default)
            f_sizer.Add(self.show_es_unscaled_gui, 1, wx.EXPAND)

            min_val = 0.01
            max_val = 1.0
            steps = 100
            self.cell_scale_factor = float(max_val - min_val) / steps
            self.cell_scale_offset = min_val
            self.scale_gui = wx.Slider(
                self.parent_panel,
                value = 100,
                minValue = 0,
                maxValue = steps,
                style = wx.SL_HORIZONTAL,
            )
            self.guis.append(self.scale_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_scale, id = self.scale_gui.GetId()
            )
            self.boxes.append(wx.StaticBox(self.parent_panel, label = 'Scale Cells'))
            scale_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            scale_sizer.Add(self.scale_gui, 1, wx.EXPAND)

            # 4D -> 3D projection properties: camera and prj volume distance
            steps = 100
            min_val = 0.1
            max_val = 5
            self.prj_vol_factor = float(max_val - min_val) / steps
            self.prj_vol_offset = min_val
            self.prj_vol_gui = wx.Slider(
                    self.parent_panel,
                    value = self.val_2_slider(
                            self.prj_vol_factor,
                            self.prj_vol_offset,
                            self.canvas.shape.w_prj_vol
                        ),
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.guis.append(self.prj_vol_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_prj_vol_adjust, id = self.prj_vol_gui.GetId()
            )
            self.boxes.append(
                wx.StaticBox(self.parent_panel, label = 'Projection Volume W-Coordinate')
            )
            prj_vol_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            prj_vol_sizer.Add(self.prj_vol_gui, 1, wx.EXPAND)
            min_val = 0.5
            max_val = 5
            self.cam_dist_factor = float(max_val - min_val) / steps
            self.cam_dist_offset = min_val
            self.cam_dist_gui = wx.Slider(
                self.parent_panel,
                value = self.val_2_slider(
                    self.cam_dist_factor,
                    self.cam_dist_offset,
                    self.canvas.shape.wCameraDistance,
                ),
                minValue = 0,
                maxValue = steps,
                style = wx.SL_HORIZONTAL,
            )
            self.guis.append(self.cam_dist_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_prj_vol_adjust, id = self.cam_dist_gui.GetId()
            )
            self.boxes.append(
                wx.StaticBox(self.parent_panel, label = 'Camera Distance (from projection volume)')
            )
            cam_dist_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            cam_dist_sizer.Add(self.cam_dist_gui, 1, wx.EXPAND)

            # Create a ctrl for specifying a 4D rotation
            self.boxes.append(wx.StaticBox(parent_panel, label = 'Rotate 4D Object'))
            rotation_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
            self.boxes.append(wx.StaticBox(parent_panel, label = 'In a Plane Spanned by'))
            plane_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
            self.v0_gui = geom_gui.Vector4DInput(
                    self.parent_panel,
                    #label = 'Vector 1',
                    rel_float_size = 4,
                    elem_labels = ['x0', 'y0', 'z0', 'w0']
                )
            self.parent_panel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, self.rotate, id = self.v0_gui.GetId()
            )
            self.v1_gui = geom_gui.Vector4DInput(
                    self.parent_panel,
                    #label = 'Vector 1',
                    rel_float_size = 4,
                    elem_labels = ['x1', 'y1', 'z1', 'w1']
                )
            self.parent_panel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, self.rotate, id = self.v1_gui.GetId()
            )
            # Exchange planes
            self.switch_planes_gui = wx.CheckBox(
                self.parent_panel,
                label = "Use Orthogonal Plane instead",
            )
            self.switch_planes_gui.SetValue(False)
            self.parent_panel.Bind(
                wx.EVT_CHECKBOX,
                self.rotate,
                id = self.switch_planes_gui.GetId(),
            )
            #self.boxes.append?
            self.guis.append(self.v0_gui)
            self.guis.append(self.v1_gui)
            self.guis.append(self.switch_planes_gui)
            plane_sizer.Add(self.v0_gui, 12, wx.EXPAND)
            plane_sizer.Add(self.v1_gui, 12, wx.EXPAND)
            plane_sizer.Add(self.switch_planes_gui, 10, wx.EXPAND)

            min_val = 0.00
            max_val = math.pi
            # step by degree (if you change this, make at least 30 and 45 degrees possible)
            steps = 360
            self.angle_factor = float(max_val - min_val) / steps
            self.angle_offset = min_val
            self.angle_gui = wx.Slider(
                    self.parent_panel,
                    value = 0,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.guis.append(self.angle_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.rotate, id = self.angle_gui.GetId()
            )
            self.boxes.append(wx.StaticBox(self.parent_panel, label = 'Using Angle'))
            angle_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            angle_sizer.Add(self.angle_gui, 1, wx.EXPAND)

            min_val = 0.00
            max_val = 1.0
            steps = 100
            self.angle_scale_factor = float(max_val - min_val) / steps
            self.angle_scale_offset = min_val
            self.angle_scale_gui = wx.Slider(
                    self.parent_panel,
                    value = 0,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.guis.append(self.angle_scale_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.rotate, id = self.angle_scale_gui.GetId()
            )
            self.boxes.append(
                wx.StaticBox(
                    self.parent_panel,
                    label = 'Set Angle (by Scale) of Rotation in the Orthogonal Plane',
                )
            )
            angle_scale_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            angle_scale_sizer.Add(self.angle_scale_gui, 1, wx.EXPAND)

            rotation_sizer.Add(plane_sizer, 12, wx.EXPAND)
            rotation_sizer.Add(angle_sizer, 5, wx.EXPAND)
            rotation_sizer.Add(angle_scale_sizer, 5, wx.EXPAND)

            self.Add(scale_sizer, 3, wx.EXPAND)
            self.Add(prj_vol_sizer, 3, wx.EXPAND)
            self.Add(cam_dist_sizer, 3, wx.EXPAND)
            self.Add(rotation_sizer, 12, wx.EXPAND)

        self.set_status_text()

    def close(self):
        """Close down view settings window"""
        # The 'try' is necessary, since the boxes are destroyed in some OS,
        # while this is necessary for e.g. Ubuntu Hardy Heron.
        for box in self.boxes:
            try:
                box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass
        for gui in self.guis:
            gui.Destroy()

    def set_status_text(self):
        """Set status text of view settings window"""
        try:
            self.parent_win.set_status_text(
                f"V-Radius: {self.v_r:0.5}; E-Radius: {self.e_r:0.5}"
            )
        except AttributeError:
            print("parent_win.set_status_text function undefined")

    def on_v_option(self, _):
        """Handle event '_' to show or hide vertex"""
        sel = self.v_opts_gui.GetSelection()
        sel_str = self.v_opts_lst[sel]
        if sel_str == 'show':
            self.v_r_gui.Enable()
            self.canvas.shape.setVertexProperties(radius = self.v_r)
        elif sel_str == 'hide':
            self.v_r_gui.Disable()
            self.canvas.shape.setVertexProperties(radius = -1.0)
        self.canvas.paint()

    def on_v_radius(self, _):
        """Handle event '_' to set vertex radius as according to settings"""
        self.v_r = (float(self.v_r_gui.GetValue()) / self.v_r_scale)
        self.canvas.shape.setVertexProperties(radius = self.v_r)
        self.canvas.paint()
        self.set_status_text()

    def on_v_col(self, _):
        """Handle event '_' to set vertex colour as according to settings"""
        dlg = wx.ColourDialog(self.parent_win)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgba = data.GetColour()
            rgb  = rgba.Get()
            self.canvas.shape.setVertexProperties(
                color = [float(i)/255 for i in rgb]
            )
            self.canvas.paint()
        dlg.Destroy()

    def on_e_option(self, _):
        """Handle event '_' to hide or show and edge either as a line or a cylinder"""
        sel = self.e_opts_gui.GetSelection()
        sel_str = self.e_opts_lst[sel]
        if sel_str == 'hide':
            self.e_r_gui.Disable()
            self.canvas.shape.setEdgeProperties(drawEdges = False)
        elif sel_str == 'as cylinders':
            self.e_r_gui.Enable()
            self.canvas.shape.setEdgeProperties(drawEdges = True)
            self.canvas.shape.setEdgeProperties(radius = self.e_r)
        elif sel_str == 'as lines':
            self.e_r_gui.Disable()
            self.canvas.shape.setEdgeProperties(drawEdges = True)
            self.canvas.shape.setEdgeProperties(radius = 0)
        self.canvas.paint()

    def on_e_radius(self, _):
        """Handle event '_' to set edge radius as according to settings"""
        self.e_r = (float(self.e_r_gui.GetValue()) / self.e_r_scale)
        self.canvas.shape.setEdgeProperties(radius = self.e_r)
        self.canvas.paint()
        self.set_status_text()

    def on_e_col(self, _):
        """Handle event '_' to set edge colour as according to settings"""
        dlg = wx.ColourDialog(self.parent_win)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgba = data.GetColour()
            rgb  = rgba.Get()
            self.canvas.shape.setEdgeProperties(
                color = [float(i)/255 for i in rgb]
            )
            self.canvas.paint()
        dlg.Destroy()

    def on_f_option(self, _):
        """Handle event '_' to show or hide faces as according to view settings"""
        print('View Settings Window size:', self.parent_win.GetSize())
        sel = self.f_opts_gui.GetStringSelection()
        # Looks like I switch front and back here, but this makes sense from
        # the GUI.
        self.canvas.shape.setFaceProperties(drawFaces = True)
        if sel == self.cull_show_both:
            GL.glDisable(GL.GL_CULL_FACE)
        elif sel == self.cull_show_none:
            # don't use culling here: doesn't work with edge radius and vertext
            # radius > 0
            self.canvas.shape.setFaceProperties(drawFaces = False)
            GL.glDisable(GL.GL_CULL_FACE)
        elif sel == self.cull_show_front:
            GL.glCullFace(GL.GL_FRONT)
            GL.glEnable(GL.GL_CULL_FACE)
        elif self.cull_show_back:
            GL.glCullFace(GL.GL_BACK)
            GL.glEnable(GL.GL_CULL_FACE)
        self.canvas.paint()

    def on_front_back(self, e):
        """Handle event 'e' to switch definition of what is front and back of a face"""
        if e.GetId() == self.front_back_gui.GetId():
            on_switch_front_and_back(self.canvas)

    def on_bg_col(self, e):
        """Handle event '_' to set background colour of shape canvas"""
        col = e.GetValue().Get()
        self.canvas.bg_col = [float(col[0])/255, float(col[1])/255, float(col[2])/255]
        self.canvas.paint()

    def on_use_transparent(self, _):
        """Handle event '_' to (re)set transparency for certain predefined polychoron faces"""
        self.canvas.shape.useTransparency((self.use_transparency_gui.GetSelection() == 0))
        self.canvas.paint()

    def on_show_unscaled_es(self, _):
        """Handle event '_' to show or hide unscaled edges of polychoron"""
        self.canvas.shape.setEdgeProperties(
            showUnscaled = (self.show_es_unscaled_gui.GetSelection() == 0)
        )
        self.canvas.paint()

    @staticmethod
    def val_2_slider(factor, offset, y):
        """Convert value a slider represents to slider value"""
        return (y - offset) / factor

    @staticmethod
    def slider_to_val(factor, offset, x):
        """Convert slider value to value it represents"""
        return factor * float(x) + offset

    def on_scale(self, _):
        """Handle event '_' to scale cells in polychoron from their centre"""
        scale = self.slider_to_val(
                self.cell_scale_factor,
                self.cell_scale_offset,
                self.scale_gui.GetValue()
            )
        self.canvas.shape.setCellProperties(scale = scale)
        self.canvas.paint()

    def on_prj_vol_adjust(self, e):
        """Handle event 'e' to adjust projection of polychoron to 3D according to settings"""
        cam_dist = self.slider_to_val(
                self.cam_dist_factor,
                self.cam_dist_offset,
                self.cam_dist_gui.GetValue()
            )
        w_prj_vol = self.slider_to_val(
                self.prj_vol_factor,
                self.prj_vol_offset,
                self.prj_vol_gui.GetValue()
            )
        if (cam_dist > 0) and (w_prj_vol > 0):
            self.parent_win.set_status_text(
                f"projection volume w = {w_prj_vol:0.2}; camera distance: {cam_dist:0.3}"
            )
        else:
            if cam_dist > 0:
                self.parent_win.set_status_text(
                    'Error: Camera distance should be > 0!'
                )
            else:
                self.parent_win.set_status_text(
                    'Error: Projection volume:  w should be > 0!'
                )
        self.canvas.shape.setProjectionProperties(cam_dist, w_prj_vol, dbg = True)
        self.canvas.paint()
        e.Skip()

    def rotate(self, _):
        """Rotate polychoron object according to settings"""
        v0 = self.v0_gui.GetValue()
        v1 = self.v1_gui.GetValue()
        if v0 == geomtypes.Vec([0, 0, 0, 0]) or v1 == geomtypes.Vec([0, 0, 0, 0]) or v0 == v1:
            self.parent_win.set_status_text("Please define two vectors spanning a plane")
            return
        angle = self.slider_to_val(
                self.angle_factor,
                self.angle_offset,
                self.angle_gui.GetValue()
            )
        scale = self.slider_to_val(
                self.angle_scale_factor,
                self.angle_scale_offset,
                self.angle_scale_gui.GetValue()
            )
        if geomtypes.eq(angle, 0):
            return
        try:
            v1 = v1.make_orthogonal_to(v0)
            # if vectors are exchange, you actually specify the axial plane
            if self.switch_planes_gui.IsChecked():
                if geomtypes.eq(scale, 0):
                    r = geomtypes.Rot4(axialPlane = (v1, v0), angle = angle)
                else:
                    r = geomtypes.DoubleRot4(
                            axialPlane = (v1, v0),
                            angle = (angle, scale*angle)
                        )
            else:
                r = geomtypes.DoubleRot4(
                    axialPlane = (v1, v0),
                    angle = (scale*angle, angle),
                )
            #print r.getMatrix()
            self.canvas.shape.rotate(r)
            self.canvas.paint()
            deg = Geom3D.Rad2Deg * angle
            self.parent_win.set_status_text(
                f"Rotation angle: {deg} degrees (and angle scale {scale:0.2})"
            )
        except ZeroDivisionError:
            # zero division means 1 of the vectors is (0, 0, 0, 0)
            self.parent_win.set_status_text("Error: Don't use a zero vector")

        #except AssertionError:
        #    z_v = geomtypes.Vec4([0, 0, 0, 0])
        #    if v0 == z_v or v1 == z_v:
        #        self.parent_win.set_status_text("Error: Don't use a zero vector")
        #    else:
        #        self.parent_win.set_status_text("Error: The specified vectors are (too) parallel")
        #    pass

class ExportOffDialog(wx.Dialog):
    """
    Dialog for exporting a polyhedron to a PS file.

    Settings like: scaling size and precision. Changing these settings will
    reflect in the next dialog that is created.
    Based on wxPython example dialog
    """

    precision = 12
    float_margin = 10
    clean_up = False
    extra_data = False

    def __init__(self, parent, ID, title):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        wx.Dialog.__init__(self)
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        self.Create(parent, ID, title)

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "vertex precision (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.precision_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.precision,
                min = 1,
                max = 16
            )
        hbox.Add(self.precision_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)

        self.extra_data_gui = wx.CheckBox(self,
                label = 'Print extra info')
        self.extra_data_gui.SetValue(self.extra_data)
        sizer.Add(self.extra_data_gui,
            0, wx.GROW|wx.ALL, 5)

        self.clean_up_gui = wx.CheckBox(self,
                label = 'Merge equal vertices (can take a while)')
        self.clean_up_gui.SetValue(self.clean_up)
        self.clean_up_gui.Bind(wx.EVT_CHECKBOX, self.on_clean_up)
        sizer.Add(self.clean_up_gui,
            0, wx.GROW|wx.ALL, 5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "float margin for being equal (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.float_margin_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.float_margin,
                min = 1,
                max = 16
            )
        if not self.clean_up:
            self.float_margin_gui.Disable()
        hbox.Add(self.float_margin_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)

        button_sizer = wx.StdDialogButtonSizer()

        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        button_sizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(button)
        button_sizer.Realize()

        sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def get_extra_data(self):
        """Retrieve check-box value stating whether to save extra data"""
        value = self.extra_data_gui.GetValue()
        self.__class__.extra_data = value
        return value

    def on_clean_up(self, _):
        """Handle event '_' to adjust GUI after (un)checking clean-up check box"""
        self.__class__.clean_up = self.clean_up_gui.GetValue()
        if ExportOffDialog.clean_up:
            self.float_margin_gui.Enable()
        else:
            self.float_margin_gui.Disable()

    def get_clean_up(self):
        """Retrieve check-box value whether to clean-up shape"""
        return self.clean_up_gui.GetValue()

    def get_precision(self):
        """Retrieve value of the field holding the precision"""
        value = self.precision_gui.GetValue()
        self.__class__.precision = value
        return value

    def get_float_margin(self):
        """Retrieve value of the field holding the float margin"""
        value = self.float_margin_gui.GetValue()
        self.__class__.float_margin = value
        return value

class ExportPsDialog(wx.Dialog):
    """
    Dialog for exporting a polyhedron to a PS file.

    Settings like: scaling size and precision. Changing these settings will
    reflect in the next dialog that is created.
    Based on wxPython example dialog
    """

    scaling = 50
    precision = 12
    float_margin = 10

    def __init__(self, parent, ID, title):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        wx.Dialog.__init__(self)
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        self.Create(parent, ID, title)

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Scaling Factor:")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.scale_factor_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.__class__.scaling,
                min = 1,
                max = 10000
            )
        hbox.Add(self.scale_factor_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "vertex precision (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.precision_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.__class__.precision,
                min = 1,
                max = 16
            )
        hbox.Add(self.precision_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "float margin for being equal (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.float_margin_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.__class__.float_margin,
                min = 1,
                max = 16
            )
        hbox.Add(self.float_margin_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)

        button_sizer = wx.StdDialogButtonSizer()

        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        button_sizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(button)
        button_sizer.Realize()

        sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def get_scaling(self):
        """Retrieve value of the field holding the scaling"""
        value = self.scale_factor_gui.GetValue()
        self.__class__.scaling = value
        return value

    def get_precision(self):
        """Retrieve value of the field holding the precision"""
        value = self.precision_gui.GetValue()
        self.__class__.precision = value
        return value

    def get_float_margin(self):
        """Retrieve value of the field holding the float margin"""
        value = self.float_margin_gui.GetValue()
        self.__class__.float_margin = value
        return value

def read_shape_file(filename):
    """Load off-file or python file and return shape"""
    shape = None
    if filename is not None:
        if filename[-3:] == '.py':
            with open(filename, 'r') as fd:
                shape = Geom3D.readPyFile(fd)
        elif filename[-4:] == '.off':
            with open(filename, 'r') as fd:
                shape = Geom3D.readOffFile(fd, recreateEdges = True)
        else:
            print('unrecognised file extension')
    return shape

def convert_to_ps(shape, fd, scale, precision, margin):
    """Convert shape to PostScript and save to file descriptor fd"""
    fd.write(
        shape.toPsPiecesStr(
            scaling = scale,
            precision = precision,
            margin = math.pow(10, -margin),
            suppressWarn = True
        )
    )

def convert_to_off(shape, fd, precision, margin = 0):
    """
    Save the shape to the fd file descriptor in .off format

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
    # TODO: support for saving extra_data?
    fd.write(shape.toOffStr(precision))

if __name__ == "__main__":
    import argparse

    DESCR = """Utility for handling polyhedra."""

    parser = argparse.ArgumentParser(description=DESCR)
    parser.add_argument(
        "inputfile",
        metavar='filename',
        nargs="?",
        help="Input files can either be a python file in a certain format or an off file.",
    )
    parser.add_argument(
        "-P", "--precision",
        type=int,
        metavar='i',
        default=15,
        help="Write floating point numbers with <i> number of decimals.",
    )
    parser.add_argument(
        "-o", "--off",
        metavar='filename',
        help="Export an input file to an off-file",
    )
    parser.add_argument(
        "-p", "--ps",
        metavar='filename',
        help="Export an input file to post-script",
    )
    parser.add_argument(
        "-y", "--py",
        metavar='filename',
        help="Export an input file to python",
    )
    parser.add_argument(
        "-m", "--margin",
        type=int,
        metavar='i',
        default=10,
        help="Set the margin for floating point numbers to be considered equal. All numbers with a"
            "difference that is smaller than 1.0e-<i> will be considered equal.",
    )
    parser.add_argument(
        "-s", "--scene",
        metavar='scene-name',
        default=DEFAULT_SCENE,
        help="Start the user interface with the specified scene name. This parameter is ignored if "
            f"the '-i' option is used. Valid scene names are: {list(SCENES.keys())}",
    )
    parser.add_argument(
        "-x", "--scale",
        metavar='n',
        default=50,
        help="When saving to PostScript, then use the specified scale factor",
    )

    prog_args = parser.parse_args()

    START_GUI = True
    if prog_args.inputfile:
        in_shape = read_shape_file(prog_args.inputfile)
        if not in_shape:
            print(f"Couldn't read shape file {prog_args.inputfile}")
            sys.exit(-1)
        if prog_args.off:
            START_GUI = False
            with open(prog_args.off, 'w') as o_fd:
                convert_to_off(in_shape, o_fd, prog_args.precision, prog_args.margin)
        elif prog_args.py:
            START_GUI = False
            with open(prog_args.py, 'w') as o_fd:
                in_shape.saveFile(o_fd)
        elif prog_args.ps:
            START_GUI = False
            with open(prog_args.ps, 'w') as o_fd:
                convert_to_ps(
                    in_shape, o_fd, prog_args.scale, prog_args.precision, prog_args.margin
                )

    if START_GUI:
        app = wx.App(False)
        frame = MainWindow(
                Canvas3DScene,
                Geom3D.SimpleShape([], []),
                prog_args.inputfile,
                None,
                wx.ID_ANY, "test",
                size = (430, 482),
                pos = wx.Point(980, 0)
            )
        if not prog_args.inputfile:
            frame.load_scene(SCENES[prog_args.scene])
        app.MainLoop()

    sys.stderr.write("Done\n")
