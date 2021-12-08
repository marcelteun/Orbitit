#!/usr/bin/env python3
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

# 2021-05-05:
# work-around for PyOpenGL bug (see commit message)
if not os.environ.get("PYOPENGL_PLATFORM", ""):
    if os.environ.get("DESKTOP_SESSION", "").lower() == "i3" or\
            "wayland" in os.getenv("XDG_SESSION_TYPE", "").lower():
        os.environ['PYOPENGL_PLATFORM'] = 'egl'
from OpenGL import GL

from orbitit import Geom3D, geom_gui, geomtypes, Scenes3D, X3D
from orbitit import (
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

def on_switch_front_and_back(canvas):
    if GL.glGetIntegerv(GL.GL_FRONT_FACE) == GL.GL_CCW:
        GL.glFrontFace(GL.GL_CW)
    else:
        GL.glFrontFace(GL.GL_CCW)
    canvas.paint()

class Canvas3DScene(Scenes3D.Interactive3DCanvas):
    def __init__(self, shape, *args, **kwargs):
        self.shape = shape
        Scenes3D.Interactive3DCanvas.__init__(self, *args, **kwargs)

    def init_gl(self):
        self.set_cam_pos(15.0)
        Scenes3D.Interactive3DCanvas.init_gl(self)

        #GL.glShadeModel(GL.GL_SMOOTH)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY);
        GL.glEnableClientState(GL.GL_NORMAL_ARRAY)

        matAmbient    = [0.2, 0.2, 0.2, 0.0]
        matDiffuse    = [0.1, 0.6, 0.0, 0.0]
        #matSpecular   = [0.2, 0.2, 0.2, 1.]
        matShininess  = 0.0
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_AMBIENT, matAmbient)
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_DIFFUSE, matDiffuse)
        #GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_SPECULAR, matSpecular)
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
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self.shape.glDraw()

class MainWindow(wx.Frame):
    wildcard = "OFF shape (*.off)|*.off| Python shape (*.py)|*.py"
    def __init__(self, TstScene, shape, p_args, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.scenes_list = list(SCENES.keys())
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
        if len(p_args) > 0 and (
            p_args[0][-4:] == '.off' or p_args[0][-3:] == '.py'
        ):
            self.open_file(p_args[0])
        self.Show(True)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.key_switch_front_back = wx.NewIdRef().GetId()
        ac = [
            (wx.ACCEL_NORMAL, wx.WXK_F3, self.key_switch_front_back)
        ]
        self.Bind(wx.EVT_MENU, self.on_key_down, id=self.key_switch_front_back)
        self.SetAcceleratorTable(wx.AcceleratorTable(ac))

    def add_menu_bar(self):
        menuBar = wx.MenuBar()
        menuBar.Append(self.create_file_menu(), '&File')
        menuBar.Append(self.create_edit_menu(), '&Edit')
        menuBar.Append(self.create_view_menu(), '&View')
        menuBar.Append(self.create_tools_menu(), '&Tools')
        self.SetMenuBar(menuBar)

    def create_file_menu(self):
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
        menu = wx.Menu()
        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Reset\tF5")
        self.Bind(wx.EVT_MENU, self.on_view_reset, id = menu_item.GetId())
        menu.Append(menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, text = "&Scene...")
        self.Bind(wx.EVT_MENU, self.on_view_scene, id = menu_item.GetId())
        menu.Append(menu_item)
        return menu

    def on_reload(self, e):
        if self.current_file != None:
            self.open_file(self.current_file)
        elif self.current_scene != None:
            self.set_scene(self.current_scene)

    def on_open(self, e):
        dlg = wx.FileDialog(self, 'New: Choose a file',
                self.import_dir_name, '', self.wildcard, wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            if dirname != None:
                filename = os.path.join(dirname, filename)
            self.open_file(filename)
        dlg.Destroy()

    def read_shape_file(self, filename):
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
        self.panel.set_shape(shape)
        # overwrite the view properties, if the shape doesn't have any
        # faces and would be invisible to the user otherwise
        if len(shape.getFaceProperties()['Fs']) == 0 and (
            self.panel.get_shape().getVertexProperties()['radius'] <= 0
        ):
            self.panel.get_shape().setVertexProperties(radius = 0.05)
        self.SetTitle('%s' % os.path.basename(filename))
        # Save for reload:
        self.current_file = filename
        self.current_scene = None

    def on_add(self, e):
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
                self.panel.get_shape().addShape(shape)
            except AttributeError:
                print("warning: cannot 'add' a shape to this scene, use 'File->Open' instead")
            self.set_status_text("OFF file added")
            fd.close()
            # TODO: set better title
            self.SetTitle('Added: %s' % os.path.basename(filename))
        dlg.Destroy()

    def on_save_py(self, e):
        dlg = wx.FileDialog(self, 'Save as .py file',
            self.export_dir_name, '', '*.py',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            filename = dlg.GetFilename()
            self.export_dir_name  = filepath.rsplit('/', 1)[0]
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
            shape = self.panel.get_shape()
            shape.name = filename
            shape.saveFile(fd)
            self.set_status_text("Python file written")
        dlg.Destroy()

    def on_save_off(self, e):
        dlg = ExportOffDialog(self, wx.ID_ANY, 'OFF settings')
        file_chosen = False
        while not file_chosen:
            if dlg.ShowModal() == wx.ID_OK:
                extra_data = dlg.get_extra_data()
                cleanUp = dlg.get_clean_up()
                precision = dlg.get_precision()
                margin = dlg.get_float_margin()
                fileDlg = wx.FileDialog(self, 'Save as .off file',
                    self.export_dir_name, '', '*.off',
                    wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                )
                file_chosen = fileDlg.ShowModal() == wx.ID_OK
                if file_chosen:
                    filepath = fileDlg.GetPath()
                    filename = fileDlg.GetFilename()
                    self.export_dir_name  = filepath.rsplit('/', 1)[0]
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
                    shape = self.panel.get_shape()
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    if cleanUp:
                        shape = shape.cleanShape(margin)
                    fd.write(shape.toOffStr(precision, extra_data))
                    print("OFF file written")
                    self.set_status_text("OFF file written")
                    fd.close()
                else:
                    dlg.Show()
                fileDlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def on_save_ps(self, e):
        dlg = ExportPsDialog(self, wx.ID_ANY, 'PS settings')
        file_chosen = False
        while not file_chosen:
            if dlg.ShowModal() == wx.ID_OK:
                scalingFactor = dlg.getScaling()
                precision = dlg.get_precision()
                margin = dlg.get_float_margin()
                assert (scalingFactor >= 0 and scalingFactor != None)
                fileDlg = wx.FileDialog(self, 'Save as .ps file',
                    self.export_dir_name, '', '*.ps',
                    style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                )
                file_chosen = fileDlg.ShowModal() == wx.ID_OK
                if file_chosen:
                    filepath = fileDlg.GetPath()
                    filename = fileDlg.GetFilename()
                    self.export_dir_name  = filepath.rsplit('/', 1)[0]
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
                    shape = self.panel.get_shape()
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    shape = shape.cleanShape(margin)
                    try:
                        fd.write(
                            shape.toPsPiecesStr(
                                scaling = scalingFactor,
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
                fileDlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def on_save_wrl(self, e):
        dlg = wx.FileDialog(self,
            'Save as .vrml file', self.export_dir_name, '', '*.wrl',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            filename = dlg.GetFilename()
            self.export_dir_name  = filepath.rsplit('/', 1)[0]
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
            r = self.panel.get_shape().getEdgeProperties()['radius']
            x3dObj = self.panel.get_shape().toX3dDoc(edgeRadius = r)
            x3dObj.setFormat(X3D.VRML_FMT)
            fd.write(x3dObj.toStr())
            self.set_status_text("VRML file written")
            fd.close()
        dlg.Destroy()

    def on_view_settings(self, e):
        if self.view_settings_win == None:
            self.view_settings_win = ViewSettingsWindow(self.panel.get_canvas(),
                None, wx.ID_ANY,
                title = 'View Settings',
                size = (394, 300)
            )
            self.view_settings_win.Bind(wx.EVT_CLOSE, self.on_view_win_closed)
        else:
            self.view_settings_win.SetFocus()
            self.view_settings_win.Raise()

    def on_col_settings(self, e):
        if not self.col_settings_win is None:
            # Don't reuse, the colours might be wrong after loading a new model
            self.col_settings_win.Destroy()
        self.col_settings_win = ColourSettingsWindow(
            self.panel.get_canvas(), 5, None, wx.ID_ANY,
            title = 'Colour Settings',
        )
        self.col_settings_win.Bind(wx.EVT_CLOSE, self.on_col_win_closed)

    def on_transform(self, e):
        if self.transform_settings_win == None:
            self.transform_settings_win = TransformSettingsWindow(
                self.panel.get_canvas(), None, wx.ID_ANY,
                title = 'Transform Settings',
            )
            self.transform_settings_win.Bind(wx.EVT_CLOSE, self.on_transform_win_closed)
        else:
            self.transform_settings_win.SetFocus()
            self.transform_settings_win.Raise()

    def on_dome(self, event):
        if self.dome1.GetId() == event.GetId(): level = 1
        else: level = 2
        shape = self.panel.get_shape().getDome(level)
        if shape != None:
            self.panel.set_shape(shape)
            self.SetTitle("Dome %s" % self.GetTitle())

    def on_view_scene(self, e):
        dlg = wx.SingleChoiceDialog(self,'Choose a Scene', '', self.scenes_list)
        if dlg.ShowModal() == wx.ID_OK:
            scene_index = dlg.GetSelection()
            frame.load_scene(SCENES[self.scenes_list[scene_index]])
        dlg.Destroy()

    def load_scene(self, scene):
        print("Starting scene", scene)
        scene = {
            'lab': scene.TITLE,
            'class': scene.Scene,
        }
        self.set_scene(scene)

    def set_scene(self, scene):
        self.close_current_scene()
        print('Switch to scene "%s"' % scene['lab'])
        canvas = self.panel.get_canvas()
        self.scene = scene['class'](self, canvas)
        self.panel.set_shape(self.scene.shape)
        self.SetTitle(scene['lab'])
        canvas.resetOrientation()
        try:
            self.view_settings_win.rebuild()
        except AttributeError:
            pass
        # save for reload:
        self.current_scene = scene
        self.current_file = None

    def on_view_reset(self, e):
        self.panel.get_canvas().resetOrientation()

    def close_current_scene(self):
        if self.scene != None:
            self.scene.close()
            del self.scene
            self.scene = None

    def set_status_text(self, str):
        self.status_bar.SetStatusText(str)

    def on_exit(self, e):
        dlg = wx.MessageDialog(None,
                               'Are you sure you want to quit?', 'Question',
                               wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            dlg.Destroy()
            self.Close(True)
        else:
            dlg.Destroy()

    def on_view_win_closed(self, event):
        self.view_settings_win.Destroy()
        self.view_settings_win = None

    def on_col_win_closed(self, event):
        self.col_settings_win.Destroy()
        self.col_settings_win = None

    def on_transform_win_closed(self, event):
        self.transform_settings_win.Destroy()
        self.transform_settings_win = None

    def on_close(self, event):
        print('main onclose')
        if self.view_settings_win != None:
            self.view_settings_win.Close()
        if self.col_settings_win != None:
            self.col_settings_win.Close()
        if self.transform_settings_win != None:
            self.transform_settings_win.Close()
        self.Destroy()

    def on_key_down(self, e):
        id = e.GetId()
        if id == self.key_switch_front_back:
            on_switch_front_and_back(self.panel.get_canvas())

class MainPanel(wx.Panel):
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

    def get_canvas(self):
        return self.canvas

    def on_size(self, event):
        """Print the size plus an offset for y that includes the title bar.

        This function is used to set the ctrl window size in the interactively.
        Bind this function, and read and set the correct size in the scene.
        """
        s = self.GetClientSize()
        print('Window size:', (s[0]+2, s[1]+54))
        self.Layout()

    def set_shape(self, shape):
        """Set a new shape to be shown with the current viewing settings

        shape: the new shape. This will refresh the canvas.
        """
        oldShape = self.canvas.shape
        self.canvas.shape = shape
        # Use all the vertex settings except for Vs, i.e. keep the view
        # vertex settings the same.
        oldVSettings = oldShape.getVertexProperties()
        del oldVSettings['Vs']
        del oldVSettings['Ns']
        self.canvas.shape.setVertexProperties(oldVSettings)
        # Use all the edge settings except for Es
        oldESettings = oldShape.getEdgeProperties()
        del oldESettings['Es']
        self.canvas.shape.setEdgeProperties(oldESettings)
        # Use only the 'drawFaces' setting:
        oldFSettings = {
                'drawFaces': oldShape.getFaceProperties()['drawFaces']
            }
        self.canvas.shape.setFaceProperties(oldFSettings)
        # if the shape generates the normals itself:
        # TODO: handle that this.Ns is set correctly, i.e. normalised
        if shape.generateNormals:
            GL.glDisable(GL.GL_NORMALIZE)
        else:
            GL.glEnable(GL.GL_NORMALIZE)
        self.canvas.paint()
        self.parent.set_status_text("Shape Updated")
        del oldShape

    def get_shape(self):
        """Return the current shape object
        """
        return self.canvas.shape

class ColourSettingsWindow(wx.Frame):
    def __init__(self, canvas, width, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas = canvas
        self.col_width = width
        self.status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.cols = self.canvas.shape.getFaceProperties()['colors']
        # take a copy for reset
        self.org_cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in self.cols]
        self.add_content()

    def add_content(self):
        self.colSizer = wx.BoxSizer(wx.VERTICAL)

        self.selColGuis = []
        i = 0
        shape_idx = 0
        # assume compound shape
        for shape_cols in self.cols:
            # use one colour select per colour for each sub-shape
            added_cols = []
            col_idx = 0
            for col in shape_cols[0]:
                wxcol = wx.Colour(255*col[0], 255*col[1], 255*col[2])
                if not wxcol in added_cols:
                    if i % self.col_width == 0:
                        selColSizerRow = wx.BoxSizer(wx.HORIZONTAL)
                        self.colSizer.Add(selColSizerRow, 0, wx.EXPAND)
                    self.selColGuis.append(
                        wx.ColourPickerCtrl(
                            self.panel, wx.ID_ANY, wxcol))
                    self.panel.Bind(wx.EVT_COLOURPICKER_CHANGED, self.on_col_select)
                    selColSizerRow.Add(self.selColGuis[-1], 0, wx.EXPAND)
                    i += 1
                    # connect GUI to shape_idx and col_idx
                    self.selColGuis[-1].my_shape_idx = shape_idx
                    self.selColGuis[-1].my_cols = [col_idx]
                    # connect wxcolour to GUI
                    wxcol.my_gui = self.selColGuis[-1]
                    added_cols.append(wxcol)
                else:
                    gui = added_cols[added_cols.index(wxcol)].my_gui
                    # must be same shape_id
                    gui.my_cols.append(col_idx)
                col_idx += 1
            shape_idx += 1

        self.noOfCols = i
        self.Guis = []

        self.subSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.colSizer.Add(self.subSizer)

        self.Guis.append(wx.Button(self.panel, label='Cancel'))
        self.Guis[-1].Bind(wx.EVT_BUTTON, self.on_cancel)
        self.subSizer.Add(self.Guis[-1], 0, wx.EXPAND)

        self.Guis.append(wx.Button(self.panel, label='Reset'))
        self.Guis[-1].Bind(wx.EVT_BUTTON, self.on_reset)
        self.subSizer.Add(self.Guis[-1], 0, wx.EXPAND)

        self.Guis.append(wx.Button(self.panel, label='Done'))
        self.Guis[-1].Bind(wx.EVT_BUTTON, self.on_done)
        self.subSizer.Add(self.Guis[-1], 0, wx.EXPAND)

        self.panel.SetSizer(self.colSizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    def on_reset(self, e):
        for colgui in self.selColGuis:
             shape_idx = colgui.my_shape_idx
             col_idx = colgui.my_cols[0]
             c = self.org_cols[shape_idx][0][col_idx]
             wxcol = wx.Colour(255*c[0], 255*c[1], 255*c[2])
             colgui.SetColour(wxcol)
        self.cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in self.org_cols]
        self.update_shape_cols()

    def on_cancel(self, e):
        self.cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in self.org_cols]
        self.update_shape_cols()
        self.Close()

    def on_done(self, e):
        self.Close()

    def on_col_select(self, e):
        wxcol = e.GetColour().Get()
        col = (float(wxcol[0])/255, float(wxcol[1])/255, float(wxcol[2])/255)
        gui_id = e.GetId()
        for gui in self.selColGuis:
            if gui.GetId() == gui_id:
                shape_cols = self.cols[gui.my_shape_idx][0]
                for col_idx in gui.my_cols:
                    shape_cols[col_idx] = col
                self.update_shape_cols()

    def update_shape_cols(self):
        self.canvas.shape.setFaceProperties(colors=self.cols)
        self.canvas.paint()

    def close(self):
        for Gui in self.Guis:
            Gui.Destroy()

class TransformSettingsWindow(wx.Frame):
    def __init__(self, canvas, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas = canvas
        self.status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.add_content()
        self.orgVs = self.canvas.shape.getVertexProperties()['Vs']
        self.org_orgVs = self.orgVs # for cancel
        self.set_status_text("")

    def add_content(self):
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.rotateSizer = geom_gui.AxisRotateSizer(
            self.panel,
            self.on_rot,
            min_angle=-180,
            max_angle=180,
            initial_angle=0
        )
        self.main_sizer.Add(self.rotateSizer)

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

        self.subSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(self.subSizer)

        self.guis.append(wx.Button(self.panel, label='Apply'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_apply)
        self.subSizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Cancel'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_cancel)
        self.subSizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Reset'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_reset)
        self.subSizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Done'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_done)
        self.subSizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.panel.SetSizer(self.main_sizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    def on_rot(self, angle, axis):
        if Geom3D.eq(axis.norm(), 0):
            self.set_status_text("Please define a proper axis")
            return
        transform = geomtypes.Rot3(angle=DEG2RAD*angle, axis=axis)
        # Assume compound shape
        newVs = [
            [transform * geomtypes.Vec3(v) for v in shapeVs] for shapeVs in self.orgVs]
        self.canvas.shape.setVertexProperties(Vs=newVs)
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_invert(self, e=None):
        # Assume compound shape
        newVs = [
            [-geomtypes.Vec3(v) for v in shapeVs] for shapeVs in self.orgVs]
        self.canvas.shape.setVertexProperties(Vs=newVs)
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_translate(self, e=None):
        # Assume compound shape
        newVs = [
            [geomtypes.Vec3(v) + self.translation.get_vertex()
             for v in shapeVs] for shapeVs in self.orgVs]
        self.canvas.shape.setVertexProperties(Vs=newVs)
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_apply(self, e=None):
        self.orgVs = self.canvas.shape.getVertexProperties()['Vs']
        # reset the angle
        self.rotateSizer.set_angle(0)
        self.set_status_text("applied, now you can define another axis")

    def on_reset(self, e=None):
        self.canvas.shape.setVertexProperties(Vs=self.org_orgVs)
        self.canvas.paint()
        self.orgVs = self.org_orgVs

    def on_cancel(self, e=None):
        self.on_reset()
        self.Close()

    def on_done(self, e):
        self.Close()

    def close(self):
        for Gui in self.guis:
            Gui.Destroy()

    def set_status_text(self, str):
        self.status_bar.SetStatusText(str)

class ViewSettingsWindow(wx.Frame):
    def __init__(self, canvas, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas    = canvas
        self.status_bar = self.CreateStatusBar()
        self.panel     = wx.Panel(self, wx.ID_ANY)
        self.add_contents()

    def add_contents(self):
        self.ctrlSizer = ViewSettingsSizer(self, self.panel, self.canvas)
        if self.canvas.shape.dimension == 4:
            self.set_default_size((413, 791))
        else:
            self.set_default_size((380, 414))
        self.panel.SetSizer(self.ctrlSizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    # move to general class
    def set_default_size(self, size):
        self.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        self.SetSize(size)

    def rebuild(self):
        # Doesn't work out of the box (Guis are not destroyed...):
        #self.ctrlSizer.Destroy()
        self.ctrlSizer.close()
        self.add_contents()

    def set_status_text(self, str):
        self.status_bar.SetStatusText(str)

class ViewSettingsSizer(wx.BoxSizer):
    cull_show_none  = 'Hide'
    cull_show_both  = 'Show Front and Back Faces'
    cull_show_front = 'Show Only Front Face'
    cull_show_back  = 'Show Only Back Face'
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

        self.Guis = []
        self.Boxes = []
        wx.BoxSizer.__init__(self, wx.VERTICAL, *args, **kwargs)
        self.canvas = canvas
        self.parent_win = parent_win
        self.parent_panel = parent_panel
        # Show / Hide vertices
        vProps = canvas.shape.getVertexProperties()
        self.vR = vProps['radius']
        self.vOptionsLst = ['hide', 'show']
        if self.vR > 0:
            default = 1 # key(1) = 'show'
        else:
            default = 0 # key(0) = 'hide'
        self.vOptionsGui  = wx.RadioBox(self.parent_panel,
            label = 'Vertex Options',
            style = wx.RA_VERTICAL,
            choices = self.vOptionsLst
        )
        self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_v_option, id = self.vOptionsGui.GetId())
        self.vOptionsGui.SetSelection(default)
        # Vertex Radius
        nrOfSliderSteps   = 40
        self.vRadiusMin   = 0.01
        self.vRadiusMax   = 0.100
        self.vRadiusScale = 1.0 / self.vRadiusMin
        s = (self.vRadiusMax - self.vRadiusMin) * self.vRadiusScale
        if int(s) < nrOfSliderSteps:
            self.vRadiusScale = (self.vRadiusScale * nrOfSliderSteps) / s
        self.vRadiusGui = wx.Slider(self.parent_panel,
            value = self.vRadiusScale * self.vR,
            minValue = self.vRadiusScale * self.vRadiusMin,
            maxValue = self.vRadiusScale * self.vRadiusMax,
            style = wx.SL_HORIZONTAL
        )
        self.Guis.append(self.vRadiusGui)
        self.parent_panel.Bind(wx.EVT_SLIDER, self.on_v_radius, id = self.vRadiusGui.GetId())
        self.Boxes.append(wx.StaticBox(self.parent_panel, label = 'Vertex radius'))
        vRadiusSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        # disable if vertices are hidden anyway:
        if default != 1:
            self.vRadiusGui.Disable()
        # Vertex Colour
        self.vColorGui = wx.Button(self.parent_panel, wx.ID_ANY, "Colour")
        self.Guis.append(self.vColorGui)
        self.parent_panel.Bind(wx.EVT_BUTTON, self.on_v_col, id = self.vColorGui.GetId())
        # Show / hide edges
        eProps           = canvas.shape.getEdgeProperties()
        self.eR          = eProps['radius']
        self.eOptionsLst = ['hide', 'as cylinders', 'as lines']
        if eProps['drawEdges']:
            if self.vR > 0:
                default = 1 # key(1) = 'as cylinders'
            else:
                default = 2 # key(2) = 'as lines'
        else:
            default     = 0 # key(0) = 'hide'
        self.eOptionsGui = wx.RadioBox(self.parent_panel,
            label = 'Edge Options',
            style = wx.RA_VERTICAL,
            choices = self.eOptionsLst
        )
        self.Guis.append(self.eOptionsGui)
        self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_e_option, id = self.eOptionsGui.GetId())
        self.eOptionsGui.SetSelection(default)
        # Edge Radius
        nrOfSliderSteps   = 40
        self.eRadiusMin   = 0.008
        self.eRadiusMax   = 0.08
        self.eRadiusScale = 1.0 / self.eRadiusMin
        s = (self.eRadiusMax - self.eRadiusMin) * self.eRadiusScale
        if int(s) < nrOfSliderSteps:
            self.eRadiusScale = (self.eRadiusScale * nrOfSliderSteps) / s
        self.eRadiusGui = wx.Slider(self.parent_panel,
            value = self.eRadiusScale * self.eR,
            minValue = self.eRadiusScale * self.eRadiusMin,
            maxValue = self.eRadiusScale * self.eRadiusMax,
            style = wx.SL_HORIZONTAL
        )
        self.Guis.append(self.eRadiusGui)
        self.parent_panel.Bind(wx.EVT_SLIDER, self.on_e_radius, id = self.eRadiusGui.GetId())
        self.Boxes.append(wx.StaticBox(self.parent_panel, label = 'Edge radius'))
        eRadiusSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        # disable if edges are not drawn as scalable items anyway:
        if default != 1:
            self.eRadiusGui.Disable()
        # Edge Colour
        self.eColorGui = wx.Button(self.parent_panel, wx.ID_ANY, "Colour")
        self.Guis.append(self.eColorGui)
        self.parent_panel.Bind(wx.EVT_BUTTON, self.on_e_col, id = self.eColorGui.GetId())
        # Show / hide face
        self.fOptionsLst = [
            self.cull_show_both,
            self.cull_show_front,
            self.cull_show_back,
            self.cull_show_none,
        ]
        self.fOptionsGui = wx.RadioBox(self.parent_panel,
            label = 'Face Options',
            style = wx.RA_VERTICAL,
            choices = self.fOptionsLst
        )
        self.Guis.append(self.fOptionsGui)
        self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_f_option, id = self.fOptionsGui.GetId())
        faceSizer = wx.BoxSizer(wx.HORIZONTAL)
        faceSizer.Add(self.fOptionsGui, 1, wx.EXPAND)
        if not GL.glIsEnabled(GL.GL_CULL_FACE):
            self.fOptionsGui.SetStringSelection(self.cull_show_both)
        else:
            # Looks like I switch front and back here, but this makes sense from
            # the GUI.
            if GL.glGetInteger(GL.GL_CULL_FACE_MODE) == GL.GL_FRONT:
                self.fOptionsGui.SetStringSelection(self.cull_show_front)
            if GL.glGetInteger(GL.GL_CULL_FACE_MODE) == GL.GL_BACK:
                self.fOptionsGui.SetStringSelection(self.cull_show_back)
            else: # ie GL.GL_FRONT_AND_BACK
                self.fOptionsGui.SetStringSelection(self.cull_show_none)

        # Open GL
        self.Boxes.append(wx.StaticBox(self.parent_panel,
                                                label = 'OpenGL Settings'))
        oglSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        self.Guis.append(
            wx.CheckBox(self.parent_panel,
                                label = 'Switch Front and Back Face (F3)')
        )
        self.oglFrontFaceGui = self.Guis[-1]
        self.oglFrontFaceGui.SetValue(GL.glGetIntegerv(GL.GL_FRONT_FACE) == GL.GL_CW)
        self.parent_panel.Bind(wx.EVT_CHECKBOX, self.on_front_back,
                                        id = self.oglFrontFaceGui.GetId())
        # background Colour
        colTxt = wx.StaticText(self.parent_panel, -1, "Background Colour: ")
        self.Guis.append(colTxt)
        col = self.canvas.bg_col
        self.bg_col_gui = wx.lib.colourselect.ColourSelect(self.parent_panel,
            wx.ID_ANY, colour = (col[0]*255, col[1]*255, col[2]*255),
            size=wx.Size(40, 30))
        self.Guis.append(self.bg_col_gui)
        self.parent_panel.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
            self.on_bg_col)

        # Sizers
        vRadiusSizer.Add(self.vRadiusGui, 1, wx.EXPAND | wx.TOP    | wx.LEFT)
        vRadiusSizer.Add(self.vColorGui,  1,             wx.BOTTOM | wx.LEFT)
        eRadiusSizer.Add(self.eRadiusGui, 1, wx.EXPAND | wx.TOP    | wx.LEFT)
        eRadiusSizer.Add(self.eColorGui,  1,             wx.BOTTOM | wx.LEFT)
        #sizer = wx.BoxSizer(wx.VERTICAL)
        vSizer = wx.BoxSizer(wx.HORIZONTAL)
        vSizer.Add(self.vOptionsGui, 2, wx.EXPAND)
        vSizer.Add(vRadiusSizer, 5, wx.EXPAND)
        eSizer = wx.BoxSizer(wx.HORIZONTAL)
        eSizer.Add(self.eOptionsGui, 2, wx.EXPAND)
        eSizer.Add(eRadiusSizer, 5, wx.EXPAND)
        bgSizerSub = wx.BoxSizer(wx.HORIZONTAL)
        bgSizerSub.Add(colTxt, 0, wx.EXPAND)
        bgSizerSub.Add(self.bg_col_gui, 0, wx.EXPAND)
        bgSizerSub.Add(wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND)
        oglSizer.Add(self.oglFrontFaceGui, 0, wx.EXPAND)
        oglSizer.Add(bgSizerSub, 0, wx.EXPAND)
        self.Add(vSizer, 5, wx.EXPAND)
        self.Add(eSizer, 5, wx.EXPAND)
        self.Add(faceSizer, 6, wx.EXPAND)
        self.Add(oglSizer, 0, wx.EXPAND)

        # 4D stuff
        if self.canvas.shape.dimension == 4:
            default = 0
            self.useTransparencyGui = wx.RadioBox(self.parent_panel,
                label = 'Use Transparency',
                style = wx.RA_VERTICAL,
                choices = ['Yes', 'No']
            )
            self.Guis.append(self.useTransparencyGui)
            self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_use_transparent, id = self.useTransparencyGui.GetId())
            self.useTransparencyGui.SetSelection(default)
            faceSizer.Add(self.useTransparencyGui, 1, wx.EXPAND)

            default = 0
            self.showUnscaledEdgesGui = wx.RadioBox(self.parent_panel,
                label = 'Unscaled Edges',
                style = wx.RA_VERTICAL,
                choices = ['Show', 'Hide']
            )
            self.Guis.append(self.showUnscaledEdgesGui)
            self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_show_unscaled_es, id =
            self.showUnscaledEdgesGui.GetId())
            self.showUnscaledEdgesGui.SetSelection(default)
            faceSizer.Add(self.showUnscaledEdgesGui, 1, wx.EXPAND)

            min   = 0.01
            max   = 1.0
            steps = 100
            self.cellScaleFactor = float(max - min) / steps
            self.cellScaleOffset = min
            self.scaleGui = wx.Slider(
                    self.parent_panel,
                    value = 100,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.Guis.append(self.scaleGui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_scale, id = self.scaleGui.GetId()
            )
            self.Boxes.append(wx.StaticBox(self.parent_panel, label = 'Scale Cells'))
            scale_sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
            scale_sizer.Add(self.scaleGui, 1, wx.EXPAND)

            # 4D -> 3D projection properties: camera and prj volume distance
            steps = 100
            min   = 0.1
            max   = 5
            self.prjVolFactor = float(max - min) / steps
            self.prjVolOffset = min
            self.prjVolGui = wx.Slider(
                    self.parent_panel,
                    value = self.val_2_slider(
                            self.prjVolFactor,
                            self.prjVolOffset,
                            self.canvas.shape.w_prj_vol
                        ),
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.Guis.append(self.prjVolGui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_prj_vol_adjust, id = self.prjVolGui.GetId()
            )
            self.Boxes.append(wx.StaticBox(self.parent_panel, label = 'Projection Volume W-Coordinate'))
            prj_vol_sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
            prj_vol_sizer.Add(self.prjVolGui, 1, wx.EXPAND)
            min   = 0.5
            max   = 5
            self.camDistFactor = float(max - min) / steps
            self.camDistOffset = min
            self.camDistGui = wx.Slider(
                    self.parent_panel,
                    value = self.val_2_slider(
                            self.camDistFactor,
                            self.camDistOffset,
                            self.canvas.shape.wCameraDistance
                        ),
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.Guis.append(self.camDistGui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_prj_vol_adjust, id = self.camDistGui.GetId()
            )
            self.Boxes.append(wx.StaticBox(self.parent_panel, label = 'Camera Distance (from projection volume)'))
            cam_dist_sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
            cam_dist_sizer.Add(self.camDistGui, 1, wx.EXPAND)

            # Create a ctrl for specifying a 4D rotation
            self.Boxes.append(wx.StaticBox(parent_panel, label = 'Rotate 4D Object'))
            rotation_sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
            self.Boxes.append(wx.StaticBox(parent_panel, label = 'In a Plane Spanned by'))
            planeSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
            self.v0Gui = geom_gui.Vector4DInput(
                    self.parent_panel,
                    #label = 'Vector 1',
                    rel_float_size = 4,
                    elem_labels = ['x0', 'y0', 'z0', 'w0']
                )
            self.parent_panel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, self.on_rot_axes, id = self.v0Gui.GetId()
            )
            self.v1Gui = geom_gui.Vector4DInput(
                    self.parent_panel,
                    #label = 'Vector 1',
                    rel_float_size = 4,
                    elem_labels = ['x1', 'y1', 'z1', 'w1']
                )
            self.parent_panel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, self.on_rot_axes, id = self.v1Gui.GetId()
            )
            # Exchange planes
            self.switch_planes_gui = wx.CheckBox(self.parent_panel, label = "Use Orthogonal Plane instead")
            self.switch_planes_gui.SetValue(False)
            self.parent_panel.Bind(wx.EVT_CHECKBOX, self.on_switch_planes, id = self.switch_planes_gui.GetId())
            #self.Boxes.append?
            self.Guis.append(self.v0Gui)
            self.Guis.append(self.v1Gui)
            self.Guis.append(self.switch_planes_gui)
            planeSizer.Add(self.v0Gui, 12, wx.EXPAND)
            planeSizer.Add(self.v1Gui, 12, wx.EXPAND)
            planeSizer.Add(self.switch_planes_gui, 10, wx.EXPAND)

            min   = 0.00
            max   = math.pi
            steps = 360 # step by degree (if you change this, make at least 30 and 45 degrees possible)
            self.angle_factor = float(max - min) / steps
            self.angle_offset = min
            self.angle_gui = wx.Slider(
                    self.parent_panel,
                    value = 0,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.Guis.append(self.angle_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_angle, id = self.angle_gui.GetId()
            )
            self.Boxes.append(wx.StaticBox(self.parent_panel, label = 'Using Angle'))
            angleSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
            angleSizer.Add(self.angle_gui, 1, wx.EXPAND)

            min   = 0.00
            max   = 1.0
            steps = 100
            self.angle_scale_factor = float(max - min) / steps
            self.angle_scale_offset = min
            self.angle_scale_gui = wx.Slider(
                    self.parent_panel,
                    value = 0,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.Guis.append(self.angle_scale_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_angle_scale, id = self.angle_scale_gui.GetId()
            )
            self.Boxes.append(wx.StaticBox(self.parent_panel, label = 'Set Angle (by Scale) of Rotation in the Orthogonal Plane'))
            angle_scale_sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
            angle_scale_sizer.Add(self.angle_scale_gui, 1, wx.EXPAND)

            rotation_sizer.Add(planeSizer, 12, wx.EXPAND)
            rotation_sizer.Add(angleSizer, 5, wx.EXPAND)
            rotation_sizer.Add(angle_scale_sizer, 5, wx.EXPAND)

            self.Add(scale_sizer, 3, wx.EXPAND)
            self.Add(prj_vol_sizer, 3, wx.EXPAND)
            self.Add(cam_dist_sizer, 3, wx.EXPAND)
            self.Add(rotation_sizer, 12, wx.EXPAND)

        self.set_status_text()

    def close(self):
        # The 'try' is necessary, since the boxes are destroyed in some OS,
        # while this is necessary for e.g. Ubuntu Hardy Heron.
        for Box in self.Boxes:
            try:
                Box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass
        for Gui in self.Guis:
            Gui.Destroy()

    def set_status_text(self):
        try:
            self.parent_win.set_status_text('V-Radius: %0.5f; E-Radius: %0.5f' % (self.vR, self.eR))
        except AttributeError:
            print("parent_win.set_status_text function undefined")

    def on_v_option(self, e):
        sel = self.vOptionsGui.GetSelection()
        selStr = self.vOptionsLst[sel]
        if selStr == 'show':
            self.vRadiusGui.Enable()
            self.canvas.shape.setVertexProperties(radius = self.vR)
        elif selStr == 'hide':
            self.vRadiusGui.Disable()
            self.canvas.shape.setVertexProperties(radius = -1.0)
        self.canvas.paint()

    def on_v_radius(self, e):
        self.vR = (float(self.vRadiusGui.GetValue()) / self.vRadiusScale)
        self.canvas.shape.setVertexProperties(radius = self.vR)
        self.canvas.paint()
        self.set_status_text()

    def on_v_col(self, e):
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

    def on_e_option(self, e):
        sel = self.eOptionsGui.GetSelection()
        selStr = self.eOptionsLst[sel]
        if selStr == 'hide':
            self.eRadiusGui.Disable()
            self.canvas.shape.setEdgeProperties(drawEdges = False)
        elif selStr == 'as cylinders':
            self.eRadiusGui.Enable()
            self.canvas.shape.setEdgeProperties(drawEdges = True)
            self.canvas.shape.setEdgeProperties(radius = self.eR)
        elif selStr == 'as lines':
            self.eRadiusGui.Disable()
            self.canvas.shape.setEdgeProperties(drawEdges = True)
            self.canvas.shape.setEdgeProperties(radius = 0)
        self.canvas.paint()

    def on_e_radius(self, e):
        self.eR = (float(self.eRadiusGui.GetValue()) / self.eRadiusScale)
        self.canvas.shape.setEdgeProperties(radius = self.eR)
        self.canvas.paint()
        self.set_status_text()

    def on_e_col(self, e):
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

    def on_f_option(self, e):
        print('View Settings Window size:', self.parent_win.GetSize())
        sel = self.fOptionsGui.GetStringSelection()
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
        id = e.GetId()
        if id == self.oglFrontFaceGui.GetId():
            on_switch_front_and_back(self.canvas)

    def on_bg_col(self, e):
        col = e.GetValue().Get()
        self.canvas.bg_col = [float(col[0])/255, float(col[1])/255, float(col[2])/255]
        self.canvas.paint()

    def on_use_transparent(self, event):
        self.canvas.shape.useTransparency((self.useTransparencyGui.GetSelection() == 0))
        self.canvas.paint()

    def on_show_unscaled_es(self, event):
        self.canvas.shape.setEdgeProperties(
            showUnscaled = (self.showUnscaledEdgesGui.GetSelection() == 0)
        )
        self.canvas.paint()

    def val_2_slider(self, factor, offset, y):
        return (y - offset) / factor

    def slider_to_val(self, factor, offset, x):
        return factor * float(x) + offset

    def on_scale(self, event):
        scale = self.slider_to_val(
                self.cellScaleFactor,
                self.cellScaleOffset,
                self.scaleGui.GetValue()
            )
        self.canvas.shape.setCellProperties(scale = scale)
        self.canvas.paint()

    def on_prj_vol_adjust(self, event):
        #print 'size =', self.dynDlg.GetClientSize()
        cam_dist = self.slider_to_val(
                self.camDistFactor,
                self.camDistOffset,
                self.camDistGui.GetValue()
            )
        w_prj_vol = self.slider_to_val(
                self.prjVolFactor,
                self.prjVolOffset,
                self.prjVolGui.GetValue()
            )
        if (cam_dist > 0) and (w_prj_vol > 0):
            self.parent_win.set_status_text(
                "projection volume w = %0.2f; camera distance: %0.3f" % (
                    w_prj_vol, cam_dist
                )
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
        event.Skip()

    def on_angle(self, event):
        self.rotate()

    def on_angle_scale(self, event):
        self.rotate()

    def on_switch_planes(self, event):
        self.rotate()

    def on_rot_axes(self, event):
        self.rotate()

    def rotate(self):
        v0 = self.v0Gui.GetValue()
        v1 = self.v1Gui.GetValue()
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
        if geomtypes.eq(angle, 0): return
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
                            angle = (scale*angle, angle)
                        )
            #print r.getMatrix()
            self.canvas.shape.rotate(r)
            self.canvas.paint()
            aDeg = Geom3D.Rad2Deg * angle
            self.parent_win.set_status_text(
                "Rotation angle: %f degrees (and scaling %0.2f)" % (aDeg, scale)
            )
        except ZeroDivisionError:
            # zero division means 1 of the vectors is (0, 0, 0, 0)
            self.parent_win.set_status_text("Error: Don't use a zero vector")
            pass
        #except AssertionError:
        #    zV = geomtypes.Vec4([0, 0, 0, 0])
        #    if v0 == zV or v1 == zV:
        #        self.parent_win.set_status_text("Error: Don't use a zero vector")
        #    else:
        #        self.parent_win.set_status_text("Error: The specified vectors are (too) parallel")
        #    pass

class ExportOffDialog(wx.Dialog):
    precision = 12
    floatMargin = 10
    cleanUp = False
    extra_data = False
    """
    Dialog for exporting a polyhedron to a PS file.

    Settings like: scaling size and precision. Changing these settings will
    reflect in the next dialog that is created.
    Based on wxPython example dialog
    """
    def __init__(self,
            parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition,
            style=wx.DEFAULT_DIALOG_STYLE
        ):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        wx.Dialog.__init__(self)
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        self.Create(parent, ID, title, pos, size, style)

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "vertex precision (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.precision_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.precision,
                min   = 1,
                max   = 16
            )
        self.precision_gui.Bind(wx.lib.intctrl.EVT_INT, self.on_precision)
        hbox.Add(self.precision_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)

        self.extra_data_gui = wx.CheckBox(self,
                label = 'Print extra info')
        self.extra_data_gui.SetValue(self.extra_data)
        self.extra_data_gui.Bind(wx.EVT_CHECKBOX, self.on_extra_data)
        sizer.Add(self.extra_data_gui,
            0, wx.GROW|wx.ALL, 5)

        self.clean_up_gui = wx.CheckBox(self,
                label = 'Merge equal vertices (can take a while)')
        self.clean_up_gui.SetValue(self.cleanUp)
        self.clean_up_gui.Bind(wx.EVT_CHECKBOX, self.on_clean_up)
        sizer.Add(self.clean_up_gui,
            0, wx.GROW|wx.ALL, 5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "float margin for being equal (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.float_margin_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.floatMargin,
                min   = 1,
                max   = 16
            )
        self.float_margin_gui.Bind(wx.lib.intctrl.EVT_INT, self.on_float_margin)
        if not self.cleanUp:
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

    def on_extra_data(self, e):
        ExportOffDialog.extra_data = self.extra_data_gui.GetValue()

    def get_extra_data(self):
        return self.extra_data_gui.GetValue()

    def on_clean_up(self, e):
        ExportOffDialog.cleanUp = self.clean_up_gui.GetValue()
        if ExportOffDialog.cleanUp:
            self.float_margin_gui.Enable()
        else:
            self.float_margin_gui.Disable()

    def get_clean_up(self):
        return self.clean_up_gui.GetValue()

    def on_precision(self, e):
        ExportOffDialog.precision = self.precision_gui.GetValue()

    def get_precision(self):
        return self.precision_gui.GetValue()

    def on_float_margin(self, e):
        ExportOffDialog.floatMargin = self.float_margin_gui.GetValue()

    def get_float_margin(self):
        return self.float_margin_gui.GetValue()

class ExportPsDialog(wx.Dialog):
    scaling = 50
    precision = 12
    floatMargin = 10
    """
    Dialog for exporting a polyhedron to a PS file.

    Settings like: scaling size and precision. Changing these settings will
    reflect in the next dialog that is created.
    Based on wxPython example dialog
    """
    def __init__(self,
            parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition,
            style=wx.DEFAULT_DIALOG_STYLE
        ):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        wx.Dialog.__init__(self)
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        self.Create(parent, ID, title, pos, size, style)

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Scaling Factor:")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.scalingFactorGui = wx.lib.intctrl.IntCtrl(self,
                value = ExportPsDialog.scaling,
                min   = 1,
                max   = 10000
            )
        self.scalingFactorGui.Bind(wx.lib.intctrl.EVT_INT, self.onScaling)
        hbox.Add(self.scalingFactorGui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "vertex precision (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.precision_gui = wx.lib.intctrl.IntCtrl(self,
                value = ExportPsDialog.precision,
                min   = 1,
                max   = 16
            )
        self.precision_gui.Bind(wx.lib.intctrl.EVT_INT, self.on_precision)
        hbox.Add(self.precision_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "float margin for being equal (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.float_margin_gui = wx.lib.intctrl.IntCtrl(self,
                value = ExportPsDialog.floatMargin,
                min   = 1,
                max   = 16
            )
        self.float_margin_gui.Bind(wx.lib.intctrl.EVT_INT, self.on_float_margin)
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

    def onScaling(self, e):
        ExportPsDialog.scaling = self.scalingFactorGui.GetValue()

    def getScaling(self):
        return self.scalingFactorGui.GetValue()

    def on_precision(self, e):
        ExportPsDialog.precision = self.precision_gui.GetValue()

    def get_precision(self):
        return self.precision_gui.GetValue()

    def on_float_margin(self, e):
        ExportPsDialog.floatMargin = self.float_margin_gui.GetValue()

    def get_float_margin(self):
        return self.float_margin_gui.GetValue()

def read_shape_file(filename):
    if filename == None:
        fd = sys.stdin
    else:
        if filename[-3:] == '.py':
            fd = open(filename, 'r')
            return Geom3D.readPyFile(fd)
        elif filename[-4:] == '.off':
            fd = open(filename, 'r')
            return Geom3D.readOffFile(fd, recreateEdges = True)
        else:
            print('unrecognised file extension')
            return None

def convertToPs(shape, o_fd, scale, precision, margin):
    o_fd.write(
        shape.toPsPiecesStr(
            scaling = scale,
            precision = precision,
            margin = math.pow(10, -margin),
            suppressWarn = True
        )
    )

def convertToOff(shape, o_fd, precision, margin = 0):
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
    # TODO: support for saving extra_data?
    o_fd.write(shape.toOffStr(precision))

def usage(exit_nr):
    print("""
usage Orbitit.py [-p | --ps] [<in_file>] [<out_file>]

Without any specified options it starts the program in the default scene.
Options:

        --precision <int>
        -P <int>          Write the number with <int> number of decimals.

        -p
        --ps         export to PS. The input file is either a python scrypt,
                     specified by -y or an off file, specified by -f. If no
                     argument is specified, the the result is piped to stdout.
        -y <file>
        --py=<file>  export to a python file defing a shape that can be
                     interpreted by Orbitit

        -f <file>
        --off=<file> export to a off-file defing a shape that can be read by
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
    if oper != None:
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
        if shape != None:
            convertToPs(shape, o_fd, scale, precision, margin)
    elif oper == Oper.toOff:
        shape = read_shape_file(i_filename)
        if shape != None:
            convertToOff(shape, o_fd, precision, margin)
    elif oper == Oper.toPy:
        shape = read_shape_file(i_filename)
        if shape != None:
            shape.saveFile(o_fd)
    else:
        if oper != Oper.openScene:
            scene_name = DEFAULT_SCENE
        app = wx.App(False)
        frame = MainWindow(
                Canvas3DScene,
                Geom3D.SimpleShape([], []),
                args,
                None,
                wx.ID_ANY, "test",
                size = (430, 482),
                pos = wx.Point(980, 0)
            )
        if (len(args) == 0):
            frame.load_scene(SCENES[scene_name])
        app.MainLoop()

    sys.stderr.write("Done\n")

    if o_fd != None: o_fd.close()
