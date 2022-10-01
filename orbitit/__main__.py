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
    base,
    Geom3D,
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
    main_dlg,
    main_win,
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

# prevent warning for not being used:
del pre_pyopengl

def is_off_model(filename):
    return filename[-4:] == '.off'

def is_json_model(filename):
    return filename[-5:] == '.json'

def read_shape_file(filename):
    """Load off-file or python file and return shape"""
    shape = None
    if filename is not None:
        if is_off_model(filename):
            with open(filename, 'r') as fd:
                shape = Geom3D.read_off_file(fd)
        elif is_json_model(filename):
            shape = base.Orbitit.from_json_file(filename)
        else:
            print('unrecognised file extension')
    return shape

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
    wildcard = "OFF shape (*.off)|*.off| JSON shape (*.json)|*.json"
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
        if filename and (is_off_model(filename) or is_json_model(filename)):
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

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&Open\tCtrl+O")
        self.Bind(wx.EVT_MENU, self.on_open, id=menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&Reload\tCtrl+R")
        self.Bind(wx.EVT_MENU, self.on_reload, id=menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&Add\tCtrl+A")
        self.Bind(wx.EVT_MENU, self.on_add, id=menu_item.GetId())
        menu.Append(menu_item)
        export = wx.Menu()

        menu_item = wx.MenuItem(export, wx.ID_ANY, text="&JSON\tCtrl+J")
        self.Bind(wx.EVT_MENU, self.on_save_json, id=menu_item.GetId())
        export.Append(menu_item)

        menu_item = wx.MenuItem(export, wx.ID_ANY, text="&Off\tCtrl+E")
        self.Bind(wx.EVT_MENU, self.on_save_off, id=menu_item.GetId())
        export.Append(menu_item)

        menu_item = wx.MenuItem(export, wx.ID_ANY, text="&PS\tCtrl+P")
        self.Bind(wx.EVT_MENU, self.on_save_ps, id=menu_item.GetId())
        export.Append(menu_item)

        menu_item = wx.MenuItem(export, wx.ID_ANY, text="&VRML\tCtrl+V")
        self.Bind(wx.EVT_MENU, self.on_save_wrl, id=menu_item.GetId())
        export.Append(menu_item)

        menu.AppendSubMenu(export, "&Export")
        menu.AppendSeparator()
        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="E&xit\tCtrl+Q")
        self.Bind(wx.EVT_MENU, self.on_exit, id=menu_item.GetId())
        menu.Append(menu_item)
        return menu

    def create_edit_menu(self):
        """Create 'Edit' menu"""
        menu = wx.Menu()

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&View Settings\tCtrl+W")
        self.Bind(wx.EVT_MENU, self.on_view_settings, id=menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&Colours\tCtrl+C")
        self.Bind(wx.EVT_MENU, self.on_col_settings, id=menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&Transform\tCtrl+T")
        self.Bind(wx.EVT_MENU, self.on_transform, id=menu_item.GetId())
        menu.Append(menu_item)

        return menu

    def create_tools_menu(self):
        """Create 'Tools' menu"""
        menu = wx.Menu()
        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&Dome Level 1\td")
        self.Bind(wx.EVT_MENU, self.on_dome, id=menu_item.GetId())
        menu.Append(menu_item)
        self.dome1 = menu_item

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&Dome Level 2\tShift+D")
        self.Bind(wx.EVT_MENU, self.on_dome, id=menu_item.GetId())
        menu.Append(menu_item)
        self.dome2 = menu_item

        return menu

    def create_view_menu(self):
        """Create 'View' menu"""
        menu = wx.Menu()
        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&Reset\tF5")
        self.Bind(wx.EVT_MENU, self.on_view_reset, id=menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&Scene...")
        self.Bind(wx.EVT_MENU, self.on_view_scene, id=menu_item.GetId())
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
        dlg = wx.FileDialog(
            self, 'New: Choose a file', self.import_dir_name, '', self.wildcard, wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            if dirname is not None:
                filename = os.path.join(dirname, filename)
            self.open_file(filename)
        dlg.Destroy()

    def open_file(self, filename):
        """Open the shape file with 'filename' and update shape"""
        self.close_current_scene()
        dirname = os.path.dirname(filename)
        if dirname != "":
            self.import_dir_name = dirname
        print(f"opening {filename}")
        shape = read_shape_file(filename)
        if shape:
            self.set_status_text("file opened")
        else:
            self.set_status_text("ERROR reading file")
            raise ValueError(f"Invalid input file {filename}")

        if isinstance(shape, Geom3D.CompoundShape):
            # convert to SimpleShape first, since adding to SymmetricShape
            # will not work.
            shape = shape.simple_shape
        # Create a compound shape to be able to add shapes later.
        shape = Geom3D.CompoundShape([shape], name=filename)
        self.panel.shape = shape
        # overwrite the view properties, if the shape doesn't have any
        # faces and would be invisible to the user otherwise
        if (
                len(shape.getFaceProperties()['Fs']) == 0
                and
                self.panel.shape.getVertexProperties()['radius'] <= 0
        ):
            self.panel.shape.setVertexProperties(radius=0.05)
        self.SetTitle(os.path.basename(filename))
        # Save for reload:
        self.current_file = filename
        self.current_scene = None

    def on_add(self, _):
        """Handle event '_' to add file to the current shape"""
        dlg = wx.FileDialog(
            self, 'Add: Choose a file', self.import_dir_name, '', self.wildcard, wx.FD_OPEN
        )
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            self.import_dir_name = dlg.GetDirectory()
            print("adding file:", filename)
            path = os.path.join(self.import_dir_name, filename)
            if is_off_model(filename):
                with open(path, 'r') as fd:
                    shape = Geom3D.read_off_file(fd)
            else:
                shape = base.Orbitit.from_json_file(path)
            if isinstance(shape, Geom3D.CompoundShape):
                # convert to SimpleShape first, since adding a SymmetricShape
                # will not work.
                shape = shape.simple_shape
            try:
                self.panel.shape.add_shape(shape)
            except AttributeError:
                print("warning: cannot 'add' a shape to this scene, use 'File->Open' instead")
            self.set_status_text("OFF file added")
            # TODO: set better title
            self.SetTitle(f'Added: {os.path.basename(filename)}')
        dlg.Destroy()

    # TODO: turn into saving a JSON file
    def on_save_json(self, _):
        """Handle event '_' to export the current shape to a JSON file"""
        dlg = wx.FileDialog(
            self,
            'Save as .json file',
            self.export_dir_name,
            '',
            '*.json',
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            filename = dlg.GetFilename()
            self.export_dir_name = filepath.rsplit('/', 1)[0]
            name_ext = filename.split('.')
            if len(name_ext) == 1:
                filename = f'{filename}.json'
            elif name_ext[-1].lower() != 'json':
                if name_ext[-1] != '':
                    filename = f'{filename}.json'
                else:
                    filename = f'{filename}json'
            print(f"writing to file {filepath}")
            # TODO add precision through setting:
            shape = self.panel.shape
            shape.name = filename
            shape.write_json_file(filepath)
            self.set_status_text("JSON file written")
        dlg.Destroy()

    def on_save_off(self, _):
        """Handle event '_' to save the current shape as off-file"""
        dlg = main_dlg.ExportOffDialog(self, wx.ID_ANY, 'OFF settings')
        file_chosen = False
        while not file_chosen:
            if dlg.ShowModal() == wx.ID_OK:
                extra_data = dlg.get_extra_data()
                clean_up = dlg.get_clean_up()
                precision = dlg.get_precision()
                margin = dlg.get_float_margin()
                file_dlg = wx.FileDialog(
                    self,
                    'Save as .off file',
                    self.export_dir_name,
                    '',
                    '*.off',
                    wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                )
                file_chosen = file_dlg.ShowModal() == wx.ID_OK
                if file_chosen:
                    filepath = file_dlg.GetPath()
                    filename = file_dlg.GetFilename()
                    self.export_dir_name = filepath.rsplit('/', 1)[0]
                    name_ext = filename.split('.')
                    if len(name_ext) == 1:
                        filename = f'{filename}.off'
                    elif name_ext[-1].lower() != 'off':
                        if name_ext[-1] != '':
                            filename = f'{filename}.off'
                        else:
                            filename = f'{filename}off'
                    print(f"writing to file {filepath}")
                    shape = self.panel.shape
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    if clean_up:
                        shape = shape.cleanShape(margin)
                    with open(filepath, 'w') as fd:
                        fd.write(shape.toOffStr(precision, extra_data))
                    self.set_status_text("OFF file written")
                else:
                    dlg.Show()
                file_dlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def on_save_ps(self, _):
        """Handle event '_' to save PostScript faces of the current shape"""
        dlg = main_dlg.ExportPsDialog(self, wx.ID_ANY, 'PS settings')
        file_chosen = False
        while not file_chosen:
            if dlg.ShowModal() == wx.ID_OK:
                scale_factor = dlg.get_scaling()
                precision = dlg.get_precision()
                margin = dlg.get_float_margin()
                assert (scale_factor >= 0 and scale_factor is not None)
                file_dlg = wx.FileDialog(
                    self,
                    'Save as .ps file',
                    self.export_dir_name,
                    '',
                    '*.ps',
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                )
                file_chosen = file_dlg.ShowModal() == wx.ID_OK
                if file_chosen:
                    filepath = file_dlg.GetPath()
                    filename = file_dlg.GetFilename()
                    self.export_dir_name = filepath.rsplit('/', 1)[0]
                    name_ext = filename.split('.')
                    if len(name_ext) == 1:
                        filename = f'{filename}.ps'
                    elif name_ext[-1].lower() != 'ps':
                        if name_ext[-1] != '':
                            filename = f'{filename}.ps'
                        else:
                            filename = f'{filename}ps'
                    # Note: if file exists is part of file dlg...
                    print(f"writing to file {filepath}")
                    shape = self.panel.shape
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    shape = shape.cleanShape(margin)
                    with open(filepath, 'w') as fd:
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
            print(f"writing to file {filepath}")
            # TODO precision through setting:
            r = self.panel.shape.getEdgeProperties()['radius']
            x3d_obj = self.panel.shape.toX3dDoc(edgeRadius = r)
            x3d_obj.setFormat(X3D.VRML_FMT)
            with open(filepath, 'w') as fd:
                fd.write(x3d_obj.toStr())
            self.set_status_text("VRML file written")
        dlg.Destroy()

    def on_view_settings(self, _):
        """Handle event '_' to load the view settings"""
        if self.view_settings_win is None:
            self.view_settings_win = main_win.ViewSettingsWindow(self.panel.canvas,
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
        self.col_settings_win = main_win.ColourWindow(
            self.panel.canvas, 5, None, wx.ID_ANY,
            title = 'Colour Settings',
        )
        self.col_settings_win.Bind(wx.EVT_CLOSE, self.on_col_win_closed)

    def on_transform(self, _):
        """Handle event '_' to transform the current shape"""
        if self.transform_settings_win is None:
            self.transform_settings_win = main_win.TransformWindow(
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
            Scenes3D.on_switch_front_and_back(self.panel.canvas)

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
    else:
        in_shape = Geom3D.SimpleShape([], [])

    if START_GUI:
        app = wx.App(False)
        frame = MainWindow(
                Canvas3DScene,
                in_shape,
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
