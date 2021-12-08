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

# 2021-05-05:
# work-around for PyOpenGL bug (see commit message)
if not os.environ.get("PYOPENGL_PLATFORM", ""):
    if os.environ.get("DESKTOP_SESSION", "").lower() == "i3" or\
            "wayland" in os.getenv("XDG_SESSION_TYPE", "").lower():
        os.environ['PYOPENGL_PLATFORM'] = 'egl'
from OpenGL import GL

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

    def initGl(self):
        self.setCameraPosition(15.0)
        Scenes3D.Interactive3DCanvas.initGl(self)

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
        GL.glClearColor(self.bgCol[0], self.bgCol[1], self.bgCol[2], 0)

    def setBgCol(self, bgCol):
        """rgb in value between 0 and 1"""
        self.bgCol = bgCol
        GL.glClearColor(bgCol[0], bgCol[1], bgCol[2], 0)

    def getBgCol(self):
        """rgb in value between 0 and 1"""
        return self.bgCol

    def onPaint(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self.shape.glDraw()

class MainWindow(wx.Frame):
    wildcard = "OFF shape (*.off)|*.off| Python shape (*.py)|*.py"
    def __init__(self, TstScene, shape, p_args, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.scenes_list = list(SCENES.keys())
        self.addMenuBar()
        self.statusBar = self.CreateStatusBar()
        self.scene = None
        self.exportDirName = '.'
        self.importDirName = '.'
        self.sceneDirName = '.'
        self.viewSettingsWindow = None
        self.colourSettingsWindow = None
        self.transformSettingsWindow = None
        self.scene = None
        self.panel = MainPanel(self, TstScene, shape, wx.ID_ANY)
        if len(p_args) > 0 and (
            p_args[0][-4:] == '.off' or p_args[0][-3:] == '.py'
        ):
            self.openFile(p_args[0])
        self.Show(True)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.keySwitchFronBack = wx.NewIdRef().GetId()
        ac = [
            (wx.ACCEL_NORMAL, wx.WXK_F3, self.keySwitchFronBack)
        ]
        self.Bind(wx.EVT_MENU, self.onKeyDown, id=self.keySwitchFronBack)
        self.SetAcceleratorTable(wx.AcceleratorTable(ac))

    def addMenuBar(self):
        menuBar = wx.MenuBar()
        menuBar.Append(self.createFileMenu(), '&File')
        menuBar.Append(self.createEditMenu(), '&Edit')
        menuBar.Append(self.createViewMenu(), '&View')
        menuBar.Append(self.createToolsMenu(), '&Tools')
        self.SetMenuBar(menuBar)

    def createFileMenu(self):
        menu = wx.Menu()

        openGui = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Open\tCtrl+O"
            )
        self.Bind(wx.EVT_MENU, self.onOpen, id = openGui.GetId())
        menu.Append(openGui)

        openGui = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Reload\tCtrl+R"
            )
        self.Bind(wx.EVT_MENU, self.onReload, id = openGui.GetId())
        menu.Append(openGui)

        add = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Add\tCtrl+A"
            )
        self.Bind(wx.EVT_MENU, self.onAdd, id = add.GetId())
        menu.Append(add)
        export = wx.Menu()

        saveAsPy = wx.MenuItem(
                export,
                wx.ID_ANY,
                text = "&Python\tCtrl+Y"
            )
        self.Bind(wx.EVT_MENU, self.onSaveAsPy, id = saveAsPy.GetId())
        export.Append(saveAsPy)

        saveAsOff = wx.MenuItem(
                export,
                wx.ID_ANY,
                text = "&Off\tCtrl+E"
            )
        self.Bind(wx.EVT_MENU, self.onSaveAsOff, id = saveAsOff.GetId())
        export.Append(saveAsOff)

        saveAsPs = wx.MenuItem(
                export,
                wx.ID_ANY,
                text = "&PS\tCtrl+P"
            )
        self.Bind(wx.EVT_MENU, self.onSaveAsPs, id = saveAsPs.GetId())
        export.Append(saveAsPs)

        saveAsWrl = wx.MenuItem(
                export,
                wx.ID_ANY,
                text = "&VRML\tCtrl+V"
            )
        self.Bind(wx.EVT_MENU, self.onSaveAsWrl, id = saveAsWrl.GetId())
        export.Append(saveAsWrl)

        menu.AppendSubMenu(export, "&Export")
        menu.AppendSeparator()
        exit = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "E&xit\tCtrl+Q"
            )
        self.Bind(wx.EVT_MENU, self.onExit, id = exit.GetId())
        menu.Append(exit)
        return menu

    def createEditMenu(self):
        menu = wx.Menu()

        viewSettings = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&View Settings\tCtrl+W"
            )
        self.Bind(wx.EVT_MENU, self.onViewSettings, id = viewSettings.GetId())
        menu.Append(viewSettings)

        colourSettings = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Colours\tCtrl+C"
            )
        self.Bind(wx.EVT_MENU, self.onColourSettings, id = colourSettings.GetId())
        menu.Append(colourSettings)

        transformSettings = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Transform\tCtrl+T"
            )
        self.Bind(wx.EVT_MENU, self.onTransform, id = transformSettings.GetId())
        menu.Append(transformSettings)

        return menu

    def createToolsMenu(self):
        menu = wx.Menu()
        tool = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Dome Level 1\td"
            )
        self.Bind(wx.EVT_MENU, self.onDome, id = tool.GetId())
        menu.Append(tool)
        self.dome1 = tool
        tool = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Dome Level 2\tShift+D"
            )
        self.Bind(wx.EVT_MENU, self.onDome, id = tool.GetId())
        menu.Append(tool)
        self.dome2 = tool
        return menu

    def createViewMenu(self):
        menu = wx.Menu()
        reset = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Reset\tF5"
            )
        self.Bind(wx.EVT_MENU, self.onResetView, id = reset.GetId())
        menu.Append(reset)
        scene = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Scene..."
            )
        self.Bind(wx.EVT_MENU, self.onOpenScene, id = scene.GetId())
        menu.Append(scene)
        return menu

    def onReload(self, e):
        if self.currentFile != None:
            self.openFile(self.currentFile)
        elif self.currentScene != None:
            self.setScene(self.currentScene)

    def onOpen(self, e):
        dlg = wx.FileDialog(self, 'New: Choose a file',
                self.importDirName, '', self.wildcard, wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            if dirname != None:
                filename = os.path.join(dirname, filename)
            self.openFile(filename)
        dlg.Destroy()

    def readShapeFile(self, filename):
        isOffModel = filename[-3:] == 'off'
        print("opening file:", filename)
        fd = open(filename, 'r')
        if isOffModel:
            shape = Geom3D.readOffFile(fd, recreateEdges = True)
        else:
            assert filename[-2:] == 'py'
            shape = Geom3D.readPyFile(fd)
        self.setStatusStr("file opened")
        fd.close()
        return shape

    def openFile(self, filename):
        self.closeCurrentScene()
        dirname = os.path.dirname(filename)
        if dirname != "":
            self.importDirName = dirname
        try:
            shape = self.readShapeFile(filename)
        except AssertionError:
            self.setStatusStr("ERROR reading file")
            raise
        if isinstance(shape, Geom3D.CompoundShape):
            # convert to SimpleShape first, since adding to IsometricShape
            # will not work.
            shape = shape.simple_shape
        # Create a compound shape to be able to add shapes later.
        shape = Geom3D.CompoundShape([shape], name = filename)
        self.panel.setShape(shape)
        # overwrite the view properties, if the shape doesn't have any
        # faces and would be invisible to the user otherwise
        if len(shape.getFaceProperties()['Fs']) == 0 and (
            self.panel.getShape().getVertexProperties()['radius'] <= 0
        ):
            self.panel.getShape().setVertexProperties(radius = 0.05)
        self.SetTitle('%s' % os.path.basename(filename))
        # Save for reload:
        self.currentFile = filename
        self.currentScene = None

    def onAdd(self, e):
        dlg = wx.FileDialog(self, 'Add: Choose a file',
                self.importDirName, '', self.wildcard, wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            isOffModel = filename[-3:] == 'off'
            self.importDirName  = dlg.GetDirectory()
            print("adding file:", filename)
            fd = open(os.path.join(self.importDirName, filename), 'r')
            if isOffModel:
                shape = Geom3D.readOffFile(fd, recreateEdges = True)
            else:
                shape = Geom3D.readPyFile(fd)
            if isinstance(shape, Geom3D.CompoundShape):
                # convert to SimpleShape first, since adding a IsometricShape
                # will not work.
                shape = shape.simple_shape
            try:
                self.panel.getShape().addShape(shape)
            except AttributeError:
                print("warning: cannot 'add' a shape to this scene, use 'File->Open' instead")
            self.setStatusStr("OFF file added")
            fd.close()
            # TODO: set better title
            self.SetTitle('Added: %s' % os.path.basename(filename))
        dlg.Destroy()

    def onSaveAsPy(self, e):
        dlg = wx.FileDialog(self, 'Save as .py file',
            self.exportDirName, '', '*.py',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            filename = dlg.GetFilename()
            self.exportDirName  = filepath.rsplit('/', 1)[0]
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
            shape = self.panel.getShape()
            shape.name = filename
            shape.saveFile(fd)
            self.setStatusStr("Python file written")
        dlg.Destroy()

    def onSaveAsOff(self, e):
        dlg = ExportOffDialog(self, wx.ID_ANY, 'OFF settings')
        fileChoosen = False
        while not fileChoosen:
            if dlg.ShowModal() == wx.ID_OK:
                extraInfo = dlg.getExtraInfo()
                cleanUp = dlg.getCleanUp()
                precision = dlg.getPrecision()
                margin = dlg.getFloatMargin()
                fileDlg = wx.FileDialog(self, 'Save as .off file',
                    self.exportDirName, '', '*.off',
                    wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                )
                fileChoosen = fileDlg.ShowModal() == wx.ID_OK
                if fileChoosen:
                    filepath = fileDlg.GetPath()
                    filename = fileDlg.GetFilename()
                    self.exportDirName  = filepath.rsplit('/', 1)[0]
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
                    shape = self.panel.getShape()
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    if cleanUp:
                        shape = shape.cleanShape(margin)
                    fd.write(shape.toOffStr(precision, extraInfo))
                    print("OFF file written")
                    self.setStatusStr("OFF file written")
                    fd.close()
                else:
                    dlg.Show()
                fileDlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def onSaveAsPs(self, e):
        dlg = ExportPsDialog(self, wx.ID_ANY, 'PS settings')
        fileChoosen = False
        while not fileChoosen:
            if dlg.ShowModal() == wx.ID_OK:
                scalingFactor = dlg.getScaling()
                precision = dlg.getPrecision()
                margin = dlg.getFloatMargin()
                assert (scalingFactor >= 0 and scalingFactor != None)
                fileDlg = wx.FileDialog(self, 'Save as .ps file',
                    self.exportDirName, '', '*.ps',
                    style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                )
                fileChoosen = fileDlg.ShowModal() == wx.ID_OK
                if fileChoosen:
                    filepath = fileDlg.GetPath()
                    filename = fileDlg.GetFilename()
                    self.exportDirName  = filepath.rsplit('/', 1)[0]
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
                    shape = self.panel.getShape()
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
                        self.setStatusStr("PS file written")
                    except Geom3D.PrecisionError:
                        self.setStatusStr(
                            "Precision error, try to decrease float margin")

                    fd.close()
                else:
                    dlg.Show()
                fileDlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def onSaveAsWrl(self, e):
        dlg = wx.FileDialog(self,
            'Save as .vrml file', self.exportDirName, '', '*.wrl',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            filename = dlg.GetFilename()
            self.exportDirName  = filepath.rsplit('/', 1)[0]
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
            r = self.panel.getShape().getEdgeProperties()['radius']
            x3dObj = self.panel.getShape().toX3dDoc(edgeRadius = r)
            x3dObj.setFormat(X3D.VRML_FMT)
            fd.write(x3dObj.toStr())
            self.setStatusStr("VRML file written")
            fd.close()
        dlg.Destroy()

    def onViewSettings(self, e):
        if self.viewSettingsWindow == None:
            self.viewSettingsWindow = ViewSettingsWindow(self.panel.getCanvas(),
                None, wx.ID_ANY,
                title = 'View Settings',
                size = (394, 300)
            )
            self.viewSettingsWindow.Bind(wx.EVT_CLOSE, self.onViewSettingsClose)
        else:
            self.viewSettingsWindow.SetFocus()
            self.viewSettingsWindow.Raise()

    def onColourSettings(self, e):
        if not self.colourSettingsWindow is None:
            # Don't reuse, the colours might be wrong after loading a new model
            self.colourSettingsWindow.Destroy()
        self.colourSettingsWindow = ColourSettingsWindow(
            self.panel.getCanvas(), 5, None, wx.ID_ANY,
            title = 'Colour Settings',
        )
        self.colourSettingsWindow.Bind(wx.EVT_CLOSE, self.onColourSettingsClose)

    def onTransform(self, e):
        if self.transformSettingsWindow == None:
            self.transformSettingsWindow = TransformSettingsWindow(
                self.panel.getCanvas(), None, wx.ID_ANY,
                title = 'Transform Settings',
            )
            self.transformSettingsWindow.Bind(wx.EVT_CLOSE, self.onTransformSettingsClose)
        else:
            self.transformSettingsWindow.SetFocus()
            self.transformSettingsWindow.Raise()

    def onDome(self, event):
        if self.dome1.GetId() == event.GetId(): level = 1
        else: level = 2
        shape = self.panel.getShape().getDome(level)
        if shape != None:
            self.panel.setShape(shape)
            self.SetTitle("Dome %s" % self.GetTitle())

    def onOpenScene(self, e):
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
        self.setScene(scene)

    def setScene(self, scene):
        self.closeCurrentScene()
        print('Switch to scene "%s"' % scene['lab'])
        canvas = self.panel.getCanvas()
        self.scene = scene['class'](self, canvas)
        self.panel.setShape(self.scene.shape)
        self.SetTitle(scene['lab'])
        canvas.resetOrientation()
        try:
            self.viewSettingsWindow.reBuild()
        except AttributeError:
            pass
        # save for reload:
        self.currentScene = scene
        self.currentFile = None

    def onResetView(self, e):
        self.panel.getCanvas().resetOrientation()

    def closeCurrentScene(self):
        if self.scene != None:
            self.scene.close()
            del self.scene
            self.scene = None

    def setStatusStr(self, str):
        self.statusBar.SetStatusText(str)

    def onExit(self, e):
        dlg = wx.MessageDialog(None,
                               'Are you sure you want to quit?', 'Question',
                               wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            dlg.Destroy()
            self.Close(True)
        else:
            dlg.Destroy()

    def onViewSettingsClose(self, event):
        self.viewSettingsWindow.Destroy()
        self.viewSettingsWindow = None

    def onColourSettingsClose(self, event):
        self.colourSettingsWindow.Destroy()
        self.colourSettingsWindow = None

    def onTransformSettingsClose(self, event):
        self.transformSettingsWindow.Destroy()
        self.transformSettingsWindow = None

    def onClose(self, event):
        print('main onclose')
        if self.viewSettingsWindow != None:
            self.viewSettingsWindow.Close()
        if self.colourSettingsWindow != None:
            self.colourSettingsWindow.Close()
        if self.transformSettingsWindow != None:
            self.transformSettingsWindow.Close()
        self.Destroy()

    def onKeyDown(self, e):
        id = e.GetId()
        if id == self.keySwitchFronBack:
            on_switch_front_and_back(self.panel.getCanvas())

class MainPanel(wx.Panel):
    def __init__(self, parent, TstScene, shape, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        # Note that uncommenting this will override the default size
        # handler, which resizes the sizers that are part of the Frame.
        self.Bind(wx.EVT_SIZE, self.onSize)

        self.canvas = TstScene(shape, self)
        self.canvas.panel = self
        self.canvas.SetMinSize((300, 300))
        self.canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.canvasSizer.Add(self.canvas, 1, wx.SHAPED)

        # Ctrl Panel:
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.canvasSizer, 1, wx.SHAPED)
        self.SetSizer(mainSizer)
        self.SetAutoLayout(True)
        self.Layout()

    def getCanvas(self):
        return self.canvas

    def onSize(self, event):
        """Print the size plus an offset for y that includes the title bar.

        This function is used to set the ctrl window size in the interactively.
        Bind this function, and read and set the correct size in the scene.
        """
        s = self.GetClientSize()
        print('Window size:', (s[0]+2, s[1]+54))
        self.Layout()

    def setShape(self, shape):
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
        self.parent.setStatusStr("Shape Updated")
        del oldShape

    def getShape(self):
        """Return the current shape object
        """
        return self.canvas.shape

class ColourSettingsWindow(wx.Frame):
    def __init__(self, canvas, width, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas    = canvas
        self.col_width = width
        self.statusBar = self.CreateStatusBar()
        self.panel     = wx.Panel(self, wx.ID_ANY)
        self.cols = self.canvas.shape.getFaceProperties()['colors']
        # take a copy for reset
        self.org_cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in self.cols]
        self.addContents()

    def addContents(self):
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
                    self.panel.Bind(wx.EVT_COLOURPICKER_CHANGED, self.onColSel)
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
        self.Guis[-1].Bind(wx.EVT_BUTTON, self.onCancel)
        self.subSizer.Add(self.Guis[-1], 0, wx.EXPAND)

        self.Guis.append(wx.Button(self.panel, label='Reset'))
        self.Guis[-1].Bind(wx.EVT_BUTTON, self.onReset)
        self.subSizer.Add(self.Guis[-1], 0, wx.EXPAND)

        self.Guis.append(wx.Button(self.panel, label='Done'))
        self.Guis[-1].Bind(wx.EVT_BUTTON, self.onDone)
        self.subSizer.Add(self.Guis[-1], 0, wx.EXPAND)

        self.panel.SetSizer(self.colSizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    def onReset(self, e):
        for colgui in self.selColGuis:
             shape_idx = colgui.my_shape_idx
             col_idx = colgui.my_cols[0]
             c = self.org_cols[shape_idx][0][col_idx]
             wxcol = wx.Colour(255*c[0], 255*c[1], 255*c[2])
             colgui.SetColour(wxcol)
        self.cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in self.org_cols]
        self.updatShapeColours()

    def onCancel(self, e):
        self.cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in self.org_cols]
        self.updatShapeColours()
        self.Close()

    def onDone(self, e):
        self.Close()

    def onColSel(self, e):
        wxcol = e.GetColour().Get()
        col = (float(wxcol[0])/255, float(wxcol[1])/255, float(wxcol[2])/255)
        gui_id = e.GetId()
        for gui in self.selColGuis:
            if gui.GetId() == gui_id:
                shape_cols = self.cols[gui.my_shape_idx][0]
                for col_idx in gui.my_cols:
                    shape_cols[col_idx] = col
                self.updatShapeColours()

    def updatShapeColours(self):
        self.canvas.shape.setFaceProperties(colors=self.cols)
        self.canvas.paint()

    def close(self):
        for Gui in self.Guis:
            Gui.Destroy()

class TransformSettingsWindow(wx.Frame):
    def __init__(self, canvas, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas    = canvas
        self.statusBar = self.CreateStatusBar()
        self.panel     = wx.Panel(self, wx.ID_ANY)
        self.addContents()
        self.orgVs = self.canvas.shape.getVertexProperties()['Vs']
        self.org_orgVs = self.orgVs # for cancel
        self.set_status("")

    def addContents(self):
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.rotateSizer = geom_gui.AxisRotateSizer(
            self.panel,
            self.on_rot,
            min_angle=-180,
            max_angle=180,
            initial_angle=0
        )
        self.mainSizer.Add(self.rotateSizer)

        self.guis = []

        # TODO: Add scale to transform
        # TODO: Add reflection

        # Transform
        translate_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(translate_sizer)
        self.guis.append(geom_gui.Vector3DInput(self.panel, "Translation vector:"))
        self.translation = self.guis[-1]
        translate_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        self.guis.append(wx.Button(self.panel, label='Translate'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_translate)
        translate_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        # Invert
        invert_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(invert_sizer)
        self.guis.append(wx.Button(self.panel, label='Invert'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_invert)
        invert_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.subSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(self.subSizer)

        self.guis.append(wx.Button(self.panel, label='Apply'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.onApply)
        self.subSizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Cancel'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.onCancel)
        self.subSizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Reset'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.onReset)
        self.subSizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Done'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.onDone)
        self.subSizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.panel.SetSizer(self.mainSizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    def on_rot(self, angle, axis):
        if Geom3D.eq(axis.norm(), 0):
            self.set_status("Please define a proper axis")
            return
        transform = geomtypes.Rot3(angle=DEG2RAD*angle, axis=axis)
        # Assume compound shape
        newVs = [
            [transform * geomtypes.Vec3(v) for v in shapeVs] for shapeVs in self.orgVs]
        self.canvas.shape.setVertexProperties(Vs=newVs)
        self.canvas.paint()
        self.set_status("Use 'Apply' to define a subsequent transform")

    def on_invert(self, e=None):
        # Assume compound shape
        newVs = [
            [-geomtypes.Vec3(v) for v in shapeVs] for shapeVs in self.orgVs]
        self.canvas.shape.setVertexProperties(Vs=newVs)
        self.canvas.paint()
        self.set_status("Use 'Apply' to define a subsequent transform")

    def on_translate(self, e=None):
        # Assume compound shape
        newVs = [
            [geomtypes.Vec3(v) + self.translation.get_vertex()
             for v in shapeVs] for shapeVs in self.orgVs]
        self.canvas.shape.setVertexProperties(Vs=newVs)
        self.canvas.paint()
        self.set_status("Use 'Apply' to define a subsequent transform")

    def onApply(self, e=None):
        self.orgVs = self.canvas.shape.getVertexProperties()['Vs']
        # reset the angle
        self.rotateSizer.set_angle(0)
        self.set_status("applied, now you can define another axis")

    def onReset(self, e=None):
        self.canvas.shape.setVertexProperties(Vs=self.org_orgVs)
        self.canvas.paint()
        self.orgVs = self.org_orgVs

    def onCancel(self, e=None):
        self.onReset()
        self.Close()

    def onDone(self, e):
        self.Close()

    def close(self):
        for Gui in self.guis:
            Gui.Destroy()

    def set_status(self, str):
        self.statusBar.SetStatusText(str)

class ViewSettingsWindow(wx.Frame):
    def __init__(self, canvas, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas    = canvas
        self.statusBar = self.CreateStatusBar()
        self.panel     = wx.Panel(self, wx.ID_ANY)
        self.addContents()

    def addContents(self):
        self.ctrlSizer = ViewSettingsSizer(self, self.panel, self.canvas)
        if self.canvas.shape.dimension == 4:
            self.setDefaultSize((413, 791))
        else:
            self.setDefaultSize((380, 414))
        self.panel.SetSizer(self.ctrlSizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    # move to general class
    def setDefaultSize(self, size):
        self.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        self.SetSize(size)

    def reBuild(self):
        # Doesn't work out of the box (Guis are not destroyed...):
        #self.ctrlSizer.Destroy()
        self.ctrlSizer.close()
        self.addContents()

    def setStatusStr(self, str):
        self.statusBar.SetStatusText(str)

class ViewSettingsSizer(wx.BoxSizer):
    cull_show_none  = 'Hide'
    cull_show_both  = 'Show Front and Back Faces'
    cull_show_front = 'Show Only Front Face'
    cull_show_back  = 'Show Only Back Face'
    def __init__(self, parentWindow, parentPanel, canvas, *args, **kwargs):
        """
        Create a sizer with view settings.

        parentWindow: the parentWindow object. This is used to update de
                      status string in the status bar. The parent window is
                      supposed to contain a function setStatusStr for this
                      to work.
        parentPanel: The panel to add all control widgets to.
        canvas: An interactive 3D canvas object. This object is supposed to
                have a shape field that points to the shape object that is
                being viewed.
        """

        self.Guis = []
        self.Boxes = []
        wx.BoxSizer.__init__(self, wx.VERTICAL, *args, **kwargs)
        self.canvas       = canvas
        self.parentWindow = parentWindow
        self.parentPanel  = parentPanel
        # Show / Hide vertices
        vProps            = canvas.shape.getVertexProperties()
        self.vR           = vProps['radius']
        self.vOptionsLst  = ['hide', 'show']
        if self.vR > 0:
            default = 1 # key(1) = 'show'
        else:
            default = 0 # key(0) = 'hide'
        self.vOptionsGui  = wx.RadioBox(self.parentPanel,
            label = 'Vertex Options',
            style = wx.RA_VERTICAL,
            choices = self.vOptionsLst
        )
        self.parentPanel.Bind(wx.EVT_RADIOBOX, self.onVOption, id = self.vOptionsGui.GetId())
        self.vOptionsGui.SetSelection(default)
        # Vertex Radius
        nrOfSliderSteps   = 40
        self.vRadiusMin   = 0.01
        self.vRadiusMax   = 0.100
        self.vRadiusScale = 1.0 / self.vRadiusMin
        s = (self.vRadiusMax - self.vRadiusMin) * self.vRadiusScale
        if int(s) < nrOfSliderSteps:
            self.vRadiusScale = (self.vRadiusScale * nrOfSliderSteps) / s
        self.vRadiusGui = wx.Slider(self.parentPanel,
            value = self.vRadiusScale * self.vR,
            minValue = self.vRadiusScale * self.vRadiusMin,
            maxValue = self.vRadiusScale * self.vRadiusMax,
            style = wx.SL_HORIZONTAL
        )
        self.Guis.append(self.vRadiusGui)
        self.parentPanel.Bind(wx.EVT_SLIDER, self.onVRadius, id = self.vRadiusGui.GetId())
        self.Boxes.append(wx.StaticBox(self.parentPanel, label = 'Vertex radius'))
        vRadiusSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        # disable if vertices are hidden anyway:
        if default != 1:
            self.vRadiusGui.Disable()
        # Vertex Colour
        self.vColorGui = wx.Button(self.parentPanel, wx.ID_ANY, "Colour")
        self.Guis.append(self.vColorGui)
        self.parentPanel.Bind(wx.EVT_BUTTON, self.onVColor, id = self.vColorGui.GetId())
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
        self.eOptionsGui = wx.RadioBox(self.parentPanel,
            label = 'Edge Options',
            style = wx.RA_VERTICAL,
            choices = self.eOptionsLst
        )
        self.Guis.append(self.eOptionsGui)
        self.parentPanel.Bind(wx.EVT_RADIOBOX, self.onEOption, id = self.eOptionsGui.GetId())
        self.eOptionsGui.SetSelection(default)
        # Edge Radius
        nrOfSliderSteps   = 40
        self.eRadiusMin   = 0.008
        self.eRadiusMax   = 0.08
        self.eRadiusScale = 1.0 / self.eRadiusMin
        s = (self.eRadiusMax - self.eRadiusMin) * self.eRadiusScale
        if int(s) < nrOfSliderSteps:
            self.eRadiusScale = (self.eRadiusScale * nrOfSliderSteps) / s
        self.eRadiusGui = wx.Slider(self.parentPanel,
            value = self.eRadiusScale * self.eR,
            minValue = self.eRadiusScale * self.eRadiusMin,
            maxValue = self.eRadiusScale * self.eRadiusMax,
            style = wx.SL_HORIZONTAL
        )
        self.Guis.append(self.eRadiusGui)
        self.parentPanel.Bind(wx.EVT_SLIDER, self.onERadius, id = self.eRadiusGui.GetId())
        self.Boxes.append(wx.StaticBox(self.parentPanel, label = 'Edge radius'))
        eRadiusSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        # disable if edges are not drawn as scalable items anyway:
        if default != 1:
            self.eRadiusGui.Disable()
        # Edge Colour
        self.eColorGui = wx.Button(self.parentPanel, wx.ID_ANY, "Colour")
        self.Guis.append(self.eColorGui)
        self.parentPanel.Bind(wx.EVT_BUTTON, self.onEColor, id = self.eColorGui.GetId())
        # Show / hide face
        self.fOptionsLst = [
            self.cull_show_both,
            self.cull_show_front,
            self.cull_show_back,
            self.cull_show_none,
        ]
        self.fOptionsGui = wx.RadioBox(self.parentPanel,
            label = 'Face Options',
            style = wx.RA_VERTICAL,
            choices = self.fOptionsLst
        )
        self.Guis.append(self.fOptionsGui)
        self.parentPanel.Bind(wx.EVT_RADIOBOX, self.onFOption, id = self.fOptionsGui.GetId())
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
        self.Boxes.append(wx.StaticBox(self.parentPanel,
                                                label = 'OpenGL Settings'))
        oglSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        self.Guis.append(
            wx.CheckBox(self.parentPanel,
                                label = 'Switch Front and Back Face (F3)')
        )
        self.oglFrontFaceGui = self.Guis[-1]
        self.oglFrontFaceGui.SetValue(GL.glGetIntegerv(GL.GL_FRONT_FACE) == GL.GL_CW)
        self.parentPanel.Bind(wx.EVT_CHECKBOX, self.onOgl,
                                        id = self.oglFrontFaceGui.GetId())
        # background Colour
        colTxt = wx.StaticText(self.parentPanel, -1, "Background Colour: ")
        self.Guis.append(colTxt)
        col = self.canvas.getBgCol()
        self.bgColorGui = wx.lib.colourselect.ColourSelect(self.parentPanel,
            wx.ID_ANY, colour = (col[0]*255, col[1]*255, col[2]*255),
            size=wx.Size(40, 30))
        self.Guis.append(self.bgColorGui)
        self.parentPanel.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
            self.onBgCol)

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
        bgSizerSub.Add(self.bgColorGui, 0, wx.EXPAND)
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
            self.useTransparencyGui = wx.RadioBox(self.parentPanel,
                label = 'Use Transparency',
                style = wx.RA_VERTICAL,
                choices = ['Yes', 'No']
            )
            self.Guis.append(self.useTransparencyGui)
            self.parentPanel.Bind(wx.EVT_RADIOBOX, self.onUseTransparency, id = self.useTransparencyGui.GetId())
            self.useTransparencyGui.SetSelection(default)
            faceSizer.Add(self.useTransparencyGui, 1, wx.EXPAND)

            default = 0
            self.showUnscaledEdgesGui = wx.RadioBox(self.parentPanel,
                label = 'Unscaled Edges',
                style = wx.RA_VERTICAL,
                choices = ['Show', 'Hide']
            )
            self.Guis.append(self.showUnscaledEdgesGui)
            self.parentPanel.Bind(wx.EVT_RADIOBOX, self.onShowUnscaledEdges, id =
            self.showUnscaledEdgesGui.GetId())
            self.showUnscaledEdgesGui.SetSelection(default)
            faceSizer.Add(self.showUnscaledEdgesGui, 1, wx.EXPAND)

            min   = 0.01
            max   = 1.0
            steps = 100
            self.cellScaleFactor = float(max - min) / steps
            self.cellScaleOffset = min
            self.scaleGui = wx.Slider(
                    self.parentPanel,
                    value = 100,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.Guis.append(self.scaleGui)
            self.parentPanel.Bind(
                wx.EVT_SLIDER, self.onScale, id = self.scaleGui.GetId()
            )
            self.Boxes.append(wx.StaticBox(self.parentPanel, label = 'Scale Cells'))
            scaleSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
            scaleSizer.Add(self.scaleGui, 1, wx.EXPAND)

            # 4D -> 3D projection properties: camera and prj volume distance
            steps = 100
            min   = 0.1
            max   = 5
            self.prjVolFactor = float(max - min) / steps
            self.prjVolOffset = min
            self.prjVolGui = wx.Slider(
                    self.parentPanel,
                    value = self.Value2Slider(
                            self.prjVolFactor,
                            self.prjVolOffset,
                            self.canvas.shape.wProjVolume
                        ),
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.Guis.append(self.prjVolGui)
            self.parentPanel.Bind(
                wx.EVT_SLIDER, self.onPrjVolAdjust, id = self.prjVolGui.GetId()
            )
            self.Boxes.append(wx.StaticBox(self.parentPanel, label = 'Projection Volume W-Coordinate'))
            prjVolSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
            prjVolSizer.Add(self.prjVolGui, 1, wx.EXPAND)
            min   = 0.5
            max   = 5
            self.camDistFactor = float(max - min) / steps
            self.camDistOffset = min
            self.camDistGui = wx.Slider(
                    self.parentPanel,
                    value = self.Value2Slider(
                            self.camDistFactor,
                            self.camDistOffset,
                            self.canvas.shape.wCameraDistance
                        ),
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.Guis.append(self.camDistGui)
            self.parentPanel.Bind(
                wx.EVT_SLIDER, self.onPrjVolAdjust, id = self.camDistGui.GetId()
            )
            self.Boxes.append(wx.StaticBox(self.parentPanel, label = 'Camera Distance (from projection volume)'))
            camDistSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
            camDistSizer.Add(self.camDistGui, 1, wx.EXPAND)

            # Create a ctrl for specifying a 4D rotation
            self.Boxes.append(wx.StaticBox(parentPanel, label = 'Rotate 4D Object'))
            rotationSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
            self.Boxes.append(wx.StaticBox(parentPanel, label = 'In a Plane Spanned by'))
            planeSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
            self.v0Gui = geom_gui.Vector4DInput(
                    self.parentPanel,
                    #label = 'Vector 1',
                    rel_float_size = 4,
                    elem_labels = ['x0', 'y0', 'z0', 'w0']
                )
            self.parentPanel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, self.onV, id = self.v0Gui.GetId()
            )
            self.v1Gui = geom_gui.Vector4DInput(
                    self.parentPanel,
                    #label = 'Vector 1',
                    rel_float_size = 4,
                    elem_labels = ['x1', 'y1', 'z1', 'w1']
                )
            self.parentPanel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, self.onV, id = self.v1Gui.GetId()
            )
            # Exchange planes
            self.exchangeGui = wx.CheckBox(self.parentPanel, label = "Use Orthogonal Plane instead")
            self.exchangeGui.SetValue(False)
            self.parentPanel.Bind(wx.EVT_CHECKBOX, self.onExchangePlanes, id = self.exchangeGui.GetId())
            #self.Boxes.append?
            self.Guis.append(self.v0Gui)
            self.Guis.append(self.v1Gui)
            self.Guis.append(self.exchangeGui)
            planeSizer.Add(self.v0Gui, 12, wx.EXPAND)
            planeSizer.Add(self.v1Gui, 12, wx.EXPAND)
            planeSizer.Add(self.exchangeGui, 10, wx.EXPAND)

            min   = 0.00
            max   = math.pi
            steps = 360 # step by degree (if you change this, make at least 30 and 45 degrees possible)
            self.angleFactor = float(max - min) / steps
            self.angleOffset = min
            self.angleGui = wx.Slider(
                    self.parentPanel,
                    value = 0,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.Guis.append(self.angleGui)
            self.parentPanel.Bind(
                wx.EVT_SLIDER, self.onAngle, id = self.angleGui.GetId()
            )
            self.Boxes.append(wx.StaticBox(self.parentPanel, label = 'Using Angle'))
            angleSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
            angleSizer.Add(self.angleGui, 1, wx.EXPAND)

            min   = 0.00
            max   = 1.0
            steps = 100
            self.angleScaleFactor = float(max - min) / steps
            self.angleScaleOffset = min
            self.angleScaleGui = wx.Slider(
                    self.parentPanel,
                    value = 0,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            self.Guis.append(self.angleScaleGui)
            self.parentPanel.Bind(
                wx.EVT_SLIDER, self.onAngleScale, id = self.angleScaleGui.GetId()
            )
            self.Boxes.append(wx.StaticBox(self.parentPanel, label = 'Set Angle (by Scale) of Rotation in the Orthogonal Plane'))
            angleScaleSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
            angleScaleSizer.Add(self.angleScaleGui, 1, wx.EXPAND)

            rotationSizer.Add(planeSizer, 12, wx.EXPAND)
            rotationSizer.Add(angleSizer, 5, wx.EXPAND)
            rotationSizer.Add(angleScaleSizer, 5, wx.EXPAND)

            self.Add(scaleSizer, 3, wx.EXPAND)
            self.Add(prjVolSizer, 3, wx.EXPAND)
            self.Add(camDistSizer, 3, wx.EXPAND)
            self.Add(rotationSizer, 12, wx.EXPAND)

        self.setStatusStr()

    def close(self):
        # The 'try' is necessary, since the boxes are destroyed in some OS,
        # while this is necessary for e.g. Ubuntu Hardy Heron.
        for Box in self.Boxes:
            try:
                Box.Destroy()
            except wx._core.PyDeadObjectError: pass
        for Gui in self.Guis:
            Gui.Destroy()

    def setStatusStr(self):
        try:
            self.parentWindow.setStatusStr('V-Radius: %0.5f; E-Radius: %0.5f' % (self.vR, self.eR))
        except AttributeError:
            print("parentWindow.setStatusStr function undefined")

    def onVOption(self, e):
        #print 'onVOption'
        sel = self.vOptionsGui.GetSelection()
        selStr = self.vOptionsLst[sel]
        if selStr == 'show':
            self.vRadiusGui.Enable()
            self.canvas.shape.setVertexProperties(radius = self.vR)
        elif selStr == 'hide':
            self.vRadiusGui.Disable()
            self.canvas.shape.setVertexProperties(radius = -1.0)
        self.canvas.paint()

    def onVRadius(self, e):
        self.vR = (float(self.vRadiusGui.GetValue()) / self.vRadiusScale)
        self.canvas.shape.setVertexProperties(radius = self.vR)
        self.canvas.paint()
        self.setStatusStr()

    def onVColor(self, e):
        dlg = wx.ColourDialog(self.parentWindow)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgba = data.GetColour()
            rgb  = rgba.Get()
            self.canvas.shape.setVertexProperties(
                color = [float(i)/255 for i in rgb]
            )
            self.canvas.paint()
        dlg.Destroy()

    def onEOption(self, e):
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

    def onERadius(self, e):
        self.eR = (float(self.eRadiusGui.GetValue()) / self.eRadiusScale)
        self.canvas.shape.setEdgeProperties(radius = self.eR)
        self.canvas.paint()
        self.setStatusStr()

    def onEColor(self, e):
        dlg = wx.ColourDialog(self.parentWindow)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgba = data.GetColour()
            rgb  = rgba.Get()
            self.canvas.shape.setEdgeProperties(
                color = [float(i)/255 for i in rgb]
            )
            self.canvas.paint()
        dlg.Destroy()

    def onFOption(self, e):
        print('View Settings Window size:', self.parentWindow.GetSize())
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

    def onOgl(self, e):
        id = e.GetId()
        if id == self.oglFrontFaceGui.GetId():
            on_switch_front_and_back(self.canvas)

    def onBgCol(self, e):
        col = e.GetValue().Get()
        self.canvas.setBgCol(
            [float(col[0])/255, float(col[1])/255, float(col[2])/255]
        )
        self.canvas.paint()

    def onUseTransparency(self, event):
        self.canvas.shape.useTransparency((self.useTransparencyGui.GetSelection() == 0))
        self.canvas.paint()

    def onShowUnscaledEdges(self, event):
        self.canvas.shape.setEdgeProperties(
            showUnscaled = (self.showUnscaledEdgesGui.GetSelection() == 0)
        )
        self.canvas.paint()

    def Value2Slider(self, factor, offset, y):
        return (y - offset) / factor

    def Slider2Value(self, factor, offset, x):
        return factor * float(x) + offset

    def onScale(self, event):
        scale = self.Slider2Value(
                self.cellScaleFactor,
                self.cellScaleOffset,
                self.scaleGui.GetValue()
            )
        self.canvas.shape.setCellProperties(scale = scale)
        self.canvas.paint()

    def onPrjVolAdjust(self, event):
        #print 'size =', self.dynDlg.GetClientSize()
        cameraDistance = self.Slider2Value(
                self.camDistFactor,
                self.camDistOffset,
                self.camDistGui.GetValue()
            )
        wProjVolume = self.Slider2Value(
                self.prjVolFactor,
                self.prjVolOffset,
                self.prjVolGui.GetValue()
            )
        if (cameraDistance > 0) and (wProjVolume > 0):
            self.parentWindow.statusBar.SetStatusText(
                "projection volume w = %0.2f; camera distance: %0.3f" % (
                    wProjVolume, cameraDistance
                )
            )
        else:
            if cameraDistance > 0:
                self.parentWindow.statusBar.SetStatusText(
                    'Error: Camera distance should be > 0!'
                )
            else:
                self.parentWindow.statusBar.SetStatusText(
                    'Error: Projection volume:  w should be > 0!'
                )
        self.canvas.shape.setProjectionProperties(cameraDistance, wProjVolume, dbg = True)
        self.canvas.paint()
        event.Skip()

    def onAngle(self, event):
        self.rotate()

    def onAngleScale(self, event):
        self.rotate()

    def onExchangePlanes(self, event):
        self.rotate()

    def onV(self, event):
        self.rotate()

    def rotate(self):
        v0 = self.v0Gui.GetValue()
        v1 = self.v1Gui.GetValue()
        angle = self.Slider2Value(
                self.angleFactor,
                self.angleOffset,
                self.angleGui.GetValue()
            )
        scale = self.Slider2Value(
                self.angleScaleFactor,
                self.angleScaleOffset,
                self.angleScaleGui.GetValue()
            )
        if geomtypes.eq(angle, 0): return
        try:
            v1 = v1.make_orthogonal_to(v0)
            # if vectors are exchange, you actually specify the axial plane
            if self.exchangeGui.IsChecked():
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
            self.parentWindow.statusBar.SetStatusText(
                "Rotation angle: %f degrees (and scaling %0.2f)" % (aDeg, scale)
            )
        except ZeroDivisionError:
            # zero division means 1 of the vectors is (0, 0, 0, 0)
            self.parentWindow.statusBar.SetStatusText("Error: Don't use a zero vector")
            pass
        #except AssertionError:
        #    zV = geomtypes.Vec4([0, 0, 0, 0])
        #    if v0 == zV or v1 == zV:
        #        self.parentWindow.statusBar.SetStatusText("Error: Don't use a zero vector")
        #    else:
        #        self.parentWindow.statusBar.SetStatusText("Error: The specified vectors are (too) parallel")
        #    pass

class ExportOffDialog(wx.Dialog):
    precision = 12
    floatMargin = 10
    cleanUp = False
    extraInfo = False
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
        self.precisionGui = wx.lib.intctrl.IntCtrl(self,
                value = self.precision,
                min   = 1,
                max   = 16
            )
        self.precisionGui.Bind(wx.lib.intctrl.EVT_INT, self.onPrecision)
        hbox.Add(self.precisionGui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)

        self.extraInfoGui = wx.CheckBox(self,
                label = 'Print extra info')
        self.extraInfoGui.SetValue(self.extraInfo)
        self.extraInfoGui.Bind(wx.EVT_CHECKBOX, self.onExtraInfo)
        sizer.Add(self.extraInfoGui,
            0, wx.GROW|wx.ALL, 5)

        self.cleanUpGui = wx.CheckBox(self,
                label = 'Merge equal vertices (can take a while)')
        self.cleanUpGui.SetValue(self.cleanUp)
        self.cleanUpGui.Bind(wx.EVT_CHECKBOX, self.onCleanUp)
        sizer.Add(self.cleanUpGui,
            0, wx.GROW|wx.ALL, 5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "float margin for being equal (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.floatMarginGui = wx.lib.intctrl.IntCtrl(self,
                value = self.floatMargin,
                min   = 1,
                max   = 16
            )
        self.floatMarginGui.Bind(wx.lib.intctrl.EVT_INT, self.onFloatMargin)
        if not self.cleanUp:
            self.floatMarginGui.Disable()
        hbox.Add(self.floatMarginGui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)

        buttonSizer = wx.StdDialogButtonSizer()

        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        buttonSizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        buttonSizer.AddButton(button)
        buttonSizer.Realize()

        sizer.Add(buttonSizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def onExtraInfo(self, e):
        ExportOffDialog.extraInfo = self.extraInfoGui.GetValue()

    def getExtraInfo(self):
        return self.extraInfoGui.GetValue()

    def onCleanUp(self, e):
        ExportOffDialog.cleanUp = self.cleanUpGui.GetValue()
        if ExportOffDialog.cleanUp:
            self.floatMarginGui.Enable()
        else:
            self.floatMarginGui.Disable()

    def getCleanUp(self):
        return self.cleanUpGui.GetValue()

    def onPrecision(self, e):
        ExportOffDialog.precision = self.precisionGui.GetValue()

    def getPrecision(self):
        return self.precisionGui.GetValue()

    def onFloatMargin(self, e):
        ExportOffDialog.floatMargin = self.floatMarginGui.GetValue()

    def getFloatMargin(self):
        return self.floatMarginGui.GetValue()

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
        self.precisionGui = wx.lib.intctrl.IntCtrl(self,
                value = ExportPsDialog.precision,
                min   = 1,
                max   = 16
            )
        self.precisionGui.Bind(wx.lib.intctrl.EVT_INT, self.onPrecision)
        hbox.Add(self.precisionGui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "float margin for being equal (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.floatMarginGui = wx.lib.intctrl.IntCtrl(self,
                value = ExportPsDialog.floatMargin,
                min   = 1,
                max   = 16
            )
        self.floatMarginGui.Bind(wx.lib.intctrl.EVT_INT, self.onFloatMargin)
        hbox.Add(self.floatMarginGui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)

        buttonSizer = wx.StdDialogButtonSizer()

        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        buttonSizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        buttonSizer.AddButton(button)
        buttonSizer.Realize()

        sizer.Add(buttonSizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def onScaling(self, e):
        ExportPsDialog.scaling = self.scalingFactorGui.GetValue()

    def getScaling(self):
        return self.scalingFactorGui.GetValue()

    def onPrecision(self, e):
        ExportPsDialog.precision = self.precisionGui.GetValue()

    def getPrecision(self):
        return self.precisionGui.GetValue()

    def onFloatMargin(self, e):
        ExportPsDialog.floatMargin = self.floatMarginGui.GetValue()

    def getFloatMargin(self):
        return self.floatMarginGui.GetValue()

def readShapeFile(filename):
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
    # TODO: support for saving extraInfo?
    o_fd.write(shape.toOffStr(precision))

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
        --py=<file>  export to a python file defing a shape that can be
                     interpreted by Orbitit

        -f <file>
        --off=<file> export to a python file defing a shape that can be read by
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
        shape = readShapeFile(i_filename)
        if shape != None:
            convertToPs(shape, o_fd, scale, precision, margin)
    elif oper == Oper.toOff:
        shape = readShapeFile(i_filename)
        if shape != None:
            convertToOff(shape, o_fd, precision, margin)
    elif oper == Oper.toPy:
        shape = readShapeFile(i_filename)
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
