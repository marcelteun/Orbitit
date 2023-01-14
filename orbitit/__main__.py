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

import logging
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
    geom_3d,
    geomtypes,
    Scene_24Cell,
    Scene_5Cell,
    Scene_8Cell,
    Scene_EqlHeptA5xI,
    Scene_EqlHeptA5xI_GD,
    Scene_EqlHeptA5xI_GI,
    scene_eql_hept_from_kite,
    Scene_EqlHeptS4A4,
    Scene_EqlHeptS4xI,
    Scene_FldHeptA4,
    Scene_FldHeptA5,
    Scene_FldHeptS4,
    Scene_Rectified24Cell,
    Scene_Rectified8Cell,
    scene_orbit,
    Scenes3D,
    main_dlg,
    main_win,
)

SCENES = {
    '24Cell': Scene_24Cell,
    '5Cell': Scene_5Cell,
    '8Cell': Scene_8Cell,
    'eqlHeptA5xI': Scene_EqlHeptA5xI,
    'eqlHeptA5xI_GD': Scene_EqlHeptA5xI_GD,
    'eqlHeptA5xI_GI': Scene_EqlHeptA5xI_GI,
    'eqlHeptFromKite': scene_eql_hept_from_kite,
    'eqlHeptS4A4': Scene_EqlHeptS4A4,
    'eqlHeptS4xI': Scene_EqlHeptS4xI,
    'fldHeptA4': Scene_FldHeptA4,
    'fldHeptA5': Scene_FldHeptA5,
    'fldHeptS4': Scene_FldHeptS4,
    'rectified24Cell': Scene_Rectified24Cell,
    'rectified8Cell': Scene_Rectified8Cell,
    'scene_orbit': scene_orbit,
}
DEFAULT_SCENE = 'scene_orbit'

# prevent warning for not being used:
del pre_pyopengl

def is_off_model(filename):
    """Return True if the filename indicates this is an off-file."""
    return filename[-4:] == '.off'

def is_json_model(filename):
    """Return True if the filename indicates this is an JSON file."""
    return filename[-5:] == '.json'

def read_shape_file(filename):
    """Load off-file or python file and return shape"""
    shape = None
    if filename is not None:
        if is_off_model(filename):
            with open(filename, 'r') as fd:
                shape = geom_3d.read_off_file(fd)
        elif is_json_model(filename):
            shape = base.Orbitit.from_json_file(filename)
        else:
            logging.warning('unrecognised file extension, file not opened')
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
        self.shape.gl_draw()

class MainWindow(wx.Frame):  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """Main window holding the shape for the orbitit program"""
    wildcard = "OFF shape (*.off)|*.off| JSON shape (*.json)|*.json"
    def __init__(self, TstScene, shape, filename, export_dir, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.current_scene = None
        self.current_file = None
        self.dome1 = None
        self.dome2 = None
        self.id_to_scene = {}
        self.add_menu_bar()
        self.status_bar = self.CreateStatusBar()
        self.scene = None
        self.export_dir_name = export_dir if export_dir else os.getcwd()
        self.import_dir_name = os.environ.get("ORBITIT_LIB", os.getcwd())
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

        menu.AppendSubMenu(self.create_scenes_main_menu(), "&Scene")
        return menu

    def create_scenes_main_menu(self):
        """Return the main menu for loading new scenes."""
        menu = wx.Menu()

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text="&Orbit")
        menu_id = menu_item.GetId()
        self.id_to_scene[menu_id] = scene_orbit
        self.Bind(wx.EVT_MENU, self.on_select_scene, id=menu_id)
        menu.Append(menu_item)

        menu.AppendSubMenu(self.create_hept_scenes_menu(), "&Heptagons")
        menu.AppendSubMenu(self.create_polychora_menu(), "&Polychora")

        return menu

    def create_hept_scenes_menu(self):
        """Return the menu for loading heptagon scenes."""
        menu = wx.Menu()

        sub_menu = wx.Menu()
        scene_items = [  # menu_title, scene
            ("&Tetrahedral", Scene_FldHeptA4),
            ("&Octahedral", Scene_FldHeptS4),
            ("&Dodecahedral", Scene_FldHeptA5),
        ]
        for title, scene in scene_items:
            sub_menu_item = wx.MenuItem(menu, wx.ID_ANY, text=title)
            sub_menu_id = sub_menu_item.GetId()
            self.id_to_scene[sub_menu_id] = scene
            self.Bind(wx.EVT_MENU, self.on_select_scene, id=sub_menu_id)
            sub_menu.Append(sub_menu_item)
        menu.AppendSubMenu(sub_menu, "&Folded")

        sub_menu = wx.Menu()
        scene_items = [  # menu_title, scene
            ("One &Kite", scene_eql_hept_from_kite),
            ("&Dodecadron", Scene_EqlHeptA5xI),
            ("&Great Dodecahedron", Scene_EqlHeptA5xI_GD),
            ("Great &Icosahedron", Scene_EqlHeptA5xI_GI),
            ("&Tetrahedron", Scene_EqlHeptS4A4),
            ("&Cube", Scene_EqlHeptS4xI),
        ]
        for title, scene in scene_items:
            sub_menu_item = wx.MenuItem(menu, wx.ID_ANY, text=title)
            sub_menu_id = sub_menu_item.GetId()
            self.id_to_scene[sub_menu_id] = scene
            self.Bind(wx.EVT_MENU, self.on_select_scene, id=sub_menu_id)
            sub_menu.Append(sub_menu_item)
        menu.AppendSubMenu(sub_menu, "&Equilateral based on")

        return menu

    def create_polychora_menu(self):
        """Return the menu for loading 4D models."""
        menu = wx.Menu()

        scene_items = [  # menu_title, scene
            ("5 Cell", Scene_5Cell),
            ("Tesseract", Scene_8Cell),
            ("Rectified Tesseract", Scene_Rectified8Cell),
            ("24 Cell", Scene_24Cell),
            ("Rectified 24 Cell", Scene_Rectified24Cell),
        ]
        for title, scene in scene_items:
            menu_item = wx.MenuItem(menu, wx.ID_ANY, text=title)
            menu_id = menu_item.GetId()
            self.id_to_scene[menu_id] = scene
            self.Bind(wx.EVT_MENU, self.on_select_scene, id=menu_id)
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
            self, 'Open an file', self.import_dir_name, '', self.wildcard, wx.FD_OPEN)
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
        logging.info("opening %s", filename)
        shape = read_shape_file(filename)
        if shape:
            self.set_status_text("file opened")
        else:
            self.set_status_text("ERROR reading file")
            raise ValueError(f"Invalid input file {filename}")

        if isinstance(shape, geom_3d.CompoundShape):
            # convert to SimpleShape first, since adding to SymmetricShape
            # will not work.
            shape = shape.simple_shape
        # Create a compound shape to be able to add shapes later.
        shape = geom_3d.CompoundShape([shape], name=filename)
        self.panel.shape = shape
        # overwrite the view properties, if the shape doesn't have any
        # faces and would be invisible to the user otherwise
        if (
                len(shape.face_props['fs']) == 0
                and
                self.panel.shape.vertex_props['radius'] <= 0
        ):
            self.panel.shape.vertex_props = {'radius': 0.05}
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
            logging.info("adding file: %s", filename)
            path = os.path.join(self.import_dir_name, filename)
            if is_off_model(filename):
                with open(path, 'r') as fd:
                    shape = geom_3d.read_off_file(fd)
            else:
                shape = base.Orbitit.from_json_file(path)
            if isinstance(shape, geom_3d.CompoundShape):
                # convert to SimpleShape first, since adding a SymmetricShape
                # will not work.
                shape = shape.simple_shape
            try:
                self.panel.shape.add_shape(shape)
            except AttributeError:
                logging.warning("Cannot 'add' a shape to this scene, use 'File->Open' instead")
            self.set_status_text("OFF file added")
            # TODO: set better title
            self.SetTitle(f'Added: {os.path.basename(filename)}')
        dlg.Destroy()

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
            logging.info("writing to file %s", filepath)
            shape = self.panel.shape
            shape.name = filename
            # TODO add precision through setting:
            precision = geomtypes.FLOAT_OUT_PRECISION
            org_precision, geomtypes.float_out_precision = (
                geomtypes.float_out_precision, precision
            )
            shape.write_json_file(filepath)
            geomtypes.float_out_precision = org_precision
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
                    logging.info("writing to file %s", filepath)
                    shape = self.panel.shape
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    if clean_up:
                        shape = shape.clean_shape(margin)
                    with open(filepath, 'w') as fd:
                        fd.write(shape.to_off(precision, extra_data))
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
                    logging.info("writing to file %s", filepath)
                    shape = self.panel.shape
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    shape = shape.clean_shape(margin)
                    with open(filepath, 'w') as fd:
                        try:
                            with geomtypes.FloatHandler(margin):
                                fd.write(
                                    shape.to_postscript(scaling=scale_factor, precision=precision)
                                )
                                self.set_status_text("PS file written")
                        except ValueError:
                            self.set_status_text(
                                "Precision error, try to decrease float margin")
                else:
                    dlg.Show()
                file_dlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def on_view_settings(self, _):
        """Handle event '_' to load the view settings"""
        if self.view_settings_win is None:
            self.view_settings_win = main_win.ViewSettingsWindow(
                self.panel.canvas,
                None, wx.ID_ANY,
                title='View Settings',
                size=(394, 300)
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
            title='Colour Settings',
        )
        self.col_settings_win.Bind(wx.EVT_CLOSE, self.on_col_win_closed)

    def on_transform(self, _):
        """Handle event '_' to transform the current shape"""
        if self.transform_settings_win is None:
            self.transform_settings_win = main_win.TransformWindow(
                self.panel.canvas, None, wx.ID_ANY,
                title='Transform Settings',
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
        shape = self.panel.shape.get_dome(level)
        if shape is not None:
            self.panel.shape = shape
            self.SetTitle(f"Dome({self.GetTitle()})")

    def on_select_scene(self, evt):
        """Handle event '_' change to scene connected to some menu ID"""
        self.load_scene(self.id_to_scene[evt.GetId()])

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
        logging.info('Switching to scene: "%s".', scene['lab'])
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
        logging.info('main onclose')
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
        logging.info("Window size: [%d, %d]", s[0]+2, s[1]+54)
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
        # Use all the vertex settings except for vs, i.e. keep the view
        # vertex settings the same.
        old_v_settings = old_shape.vertex_props
        del old_v_settings['vs']
        del old_v_settings['ns']
        self.canvas.shape.vertex_props = old_v_settings
        # Use all the edge settings except for es
        old_e_settings = old_shape.edge_props
        del old_e_settings['es']
        self.canvas.shape.edge_props = old_e_settings
        # Use only the 'draw_faces' setting:
        old_f_settings = {'draw_faces': old_shape.face_props['draw_faces']}
        self.canvas.shape.face_props = old_f_settings
        # if the shape generates the normals itself:
        # TODO: handle that this.ns is set correctly, i.e. normalised
        if shape.generate_normals:
            GL.glDisable(GL.GL_NORMALIZE)
        else:
            GL.glEnable(GL.GL_NORMALIZE)
        self.canvas.paint()
        self.parent.set_status_text("Shape Updated")
        del old_shape

def convert_to_ps(shape, fd, scale, precision, margin):
    """Convert shape to PostScript and save to file descriptor fd"""
    fd.write(
        shape.to_postscript(
            scaling=scale,
            precision=precision,
            margin=math.pow(10, -margin),
        )
    )

def convert_to_off(shape, fd, precision, margin=0):
    """
    Save the shape to the fd file descriptor in .off format

    precision: how many decimals to write.
    margin: what margin to use to require that 2 floating numbers are equal. It is specified in the
        number of decimals. If not specified or 0, then no cleaning up is done, meaning that no
        attempt is made of merging vertices that have the same coordinate. Neither are faces with
        the same coordinates filtered out.
    """
    try:
        shape = shape.simple_shape
    except AttributeError:
        pass
    if margin != 0:
        shape = shape.clean_shape(margin)
    # TODO: support for saving extra_data?
    fd.write(shape.to_off(precision))

if __name__ == "__main__":
    import argparse

    DESCR = """Utility for handling polyhedra.

    The enviroment variable ORBITIT_LIB can be used to specifiy the default location for importing
    files (unless you use the filename parameter).
    """

    PARSER = argparse.ArgumentParser(description=DESCR)
    PARSER.add_argument(
        "inputfile",
        metavar='filename',
        nargs="?",
        help="Input files can either be a python file in a certain format or an off file. "
        "If this is specified then the setting for ORBITIT_LIB is overwritten to the path "
        "of this files.",
    )
    PARSER.add_argument(
        "-d", "--debug",
        action='store_true',
        help="Enable logs for debugging.",
    )
    PARSER.add_argument(
        "-e", "--export-dir",
        metavar="path",
        help="Export to this directory when exporting files. If nothing is specified, then "
        "the current working dir is used.",
    )
    PARSER.add_argument(
        "-m", "--margin",
        type=int,
        metavar='i',
        default=10,
        help="Set the margin for floating point numbers to be considered equal. All numbers with a"
        "difference that is smaller than 1.0e-<i> will be considered equal.",
    )
    PARSER.add_argument(
        "-o", "--off",
        metavar='filename',
        help="Export an input file to an off-file. Specify full path. Any --export-dir is ignored.",
    )
    PARSER.add_argument(
        "-P", "--precision",
        type=int,
        metavar='i',
        default=15,
        help="Write floating point numbers with <i> number of decimals.",
    )
    PARSER.add_argument(
        "-p", "--ps",
        metavar='filename',
        help="Export an input file to post-script. Specify full path. Any --export-dir is ignored.",
    )
    PARSER.add_argument(
        "-y", "--py",
        metavar='filename',
        help="Export an input file to python. Specify full path. Any --export-dir is ignored.",
    )
    PARSER.add_argument(
        "-s", "--scene",
        metavar='scene-name',
        default=DEFAULT_SCENE,
        help="Start the user interface with the specified scene name. This parameter is ignored if "
        f"the '-i' option is used. Valid scene names are: {list(SCENES.keys())}",
    )
    PARSER.add_argument(
        "-x", "--scale",
        metavar='n',
        default=50,
        help="When saving to PostScript, then use the specified scale factor",
    )

    PROG_ARGS = PARSER.parse_args()

    logging.basicConfig(
        format="%(levelname)s@<%(filename)s:%(lineno)d> %(message)s",
        level=logging.DEBUG if PROG_ARGS.debug else logging.INFO,
    )
    START_GUI = True
    if PROG_ARGS.inputfile:
        IN_SHAPE = read_shape_file(PROG_ARGS.inputfile)
        if not IN_SHAPE:
            logging.error("Couldn't read shape file %s", PROG_ARGS.inputfile)
            sys.exit(-1)
        if PROG_ARGS.off:
            START_GUI = False
            with open(PROG_ARGS.off, 'w') as o_fd:
                convert_to_off(IN_SHAPE, o_fd, PROG_ARGS.precision, PROG_ARGS.margin)
        elif PROG_ARGS.py:
            START_GUI = False
            with open(PROG_ARGS.py, 'w') as o_fd:
                IN_SHAPE.save_file(o_fd)
        elif PROG_ARGS.ps:
            START_GUI = False
            with open(PROG_ARGS.ps, 'w') as o_fd:
                convert_to_ps(
                    IN_SHAPE, o_fd, PROG_ARGS.scale, PROG_ARGS.precision, PROG_ARGS.margin
                )
    else:
        IN_SHAPE = geom_3d.SimpleShape([], [])

    if START_GUI:
        APP = wx.App(False)
        FRAME = MainWindow(
            Canvas3DScene,
            IN_SHAPE,
            PROG_ARGS.inputfile,
            PROG_ARGS.export_dir,
            None,
            wx.ID_ANY, "test",
            size=(430, 482),
            pos=wx.Point(980, 0)
        )
        if not PROG_ARGS.inputfile:
            FRAME.load_scene(SCENES[PROG_ARGS.scene])
        APP.MainLoop()

    sys.stderr.write("Done\n")
