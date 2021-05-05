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
import wx
import pprint
import wx.lib.intctrl
import wx.lib.colourselect

# work-around for PyOpenGL bug (see commit message)
if not os.environ.get("PYOPENGL_PLATFORM", ""):
    if os.environ.get("DESKTOP_SESSION", "").lower() == "i3" or\
            "wayland" in os.getenv("XDG_SESSION_TYPE", "").lower():
        os.environ['PYOPENGL_PLATFORM'] = 'egl'
from OpenGL.GLU import *
from OpenGL.GL import *

DEG2RAD = Geom3D.Deg2Rad

# TODO
# 20100405: clean up: get rid of Geom3D.IsometricShape.unfoldOrbit parameter
# introduced for legacy code. The new way by using glMultMatrix is better, since
# it takes care of the vertex normals in the correct way for opposite
# isometries. In that case the seperate opposite isometries parameter is not
# needed anymore either...
#
# 20090911:
# To fix the transparency: order the faces...: it became much better for the 24
# cell after putting the outer cell last.
# What is needed is faces per cell. This way cells can be made a little bit
# smaller so faces that are shared and have different colours can be drawn in
# the correct order.
# Then per face you keep a average/gracity point. This only need to be
#       <<< start with gravity by cell and sort on that >>
# calculated at setVertices, but it needs to be projected as well. (is this
# correct; I guess not if e.g. one of the vertices end up in the camera...)
# Anyway you prevent having to calc all these gravity points every time you
# draw. Then these gravity points are used to order the faces..
#
# 20091109: At export to PS add margin to decide whether 2 faces ly in 1 plane:
#           try exporting the 24 cell to PS with settings 40, 12, 6..

# continue with:
# 20090302:
#            find roots for Fld alternatives.
#            set normals for FLD to see the effect of folding...
#            what about more roots.... combos of 1/V2/0
#
# TODO:
# - 20090302: fix glInit and initGl confusion. Both set lights, one in canvas
#             one in shape. Be consistent.
#             20100406: setup through GUI.
# - 20090222: Shape classes in Geom3D has parameter: colors = [([], [])].
#             This should be split into 2 separate pars. Sometimes you just want
#             to change the colours, sometimes you just want to change which
#             face will get the colours that are defined already.
# - 20090215: Printing Hepta with Alt Min for dodecahedron raises an assertion:
#             File "/home/teun/prj/python/polyh/work/Geom3D.py", line 274, in getFactor
#               assert False, 'The point is not one the line;'
#             AssertionError: The point is not one the line;
# - 20090215: Printing Hepta with Pref Min for dodecahedron raises an assertion.
#             Would be nice to spec an own assertion here and catch that in
#             Geom3D.facePlane so that the loop can continue.
#               File "/home/teun/prj/python/polyh/work/Geom3D.py", line 610, in __init__
#                 assert(not P1 == P2)
#             AssertionError
# - 20090215: Fix lights for off files. Now shadow, e.g. for cube compound
#             12.S4xI.ExI.
# - 20090215: See also comment 20090211:
#             For faces that ly in the same plane all edges need to be drawn.
#             And the facets should be merged.
#             Catch this at a level that calls Geom3D.intersectWithFacet
#             Now it sometimes works, sometimes it doesn't, e.g. octa compounds
#             8.S4xI.C3Xi.mu.alt1.off.
# - 20090214: Geom3D.Line.getFactor check should not crash, but return None if
#             check failed..
#             This can be used for Line.vOnLine. And then  and
#             use getFactor for edge on Line.
# - 20090212: Got this one as well (e.g. when scaling too much (800 on a 15 octa
#             compound)
#             File "/home/teun/prj/python/polyh/work/PS.py", line 132, in appendPageStr
#             this.pagesStr[-1] = "%s%s" % (this.pagesStr[-1], str)
#             IndexError: list index out of range

# - 20090212: Add colour print somehow?
# - 20090211: Why don't I get 2 triangles in PS print for A5xI heptagons
#             positions for which 2 triangles end up in one plane? This works
#             for S4xI.
# - 20090207: Add cube compound shapes as scenes.
# - 20090207: Add centralised setting that shows up only if the shape is a
#             compound shape and that takes care of only showing the base shape.
# - 20090207: Fix transparency for Scene_EqlHeptA5xI_GI.py and
#             Scene_EqlHeptA5xI_GD.py
# - 20090204: The scenes use too many vertices.. Add to Shape that only the
#             vertices in edges are to be shown.
# - 20090203: HeptaScenes: do not triangulate the faces: breaks export->PS and
#             adds extra edges to the off file. (only partly fixed 20090211)
# - Test the gl stuf of SimpleShape: create an Interactive3DCanvas
#   the Symmetry stuff should not contain any shape stuff
# - In SimpleShape I split the setFaceProperties in functions that set separate
#   properties. Do something similar for Edges and Vertices.
# - Add class function: intersect faces: which will return a new shape for
#   which the faces do not intersect anymore. Then there should be a class
#   function for converting the faces to PS string as is.
# - remove depedency towards cgkit?
# - add transforms
# - add print pieces (cp from p3D)
# - function toPsPiecesStr finds intersection: this should be part of a separate
#   functons mapping the SimpleShape on a shape consisting of none intersecting
#   pieces. This could be a child of SimpleShape.
# - add function to filter out vertices that ly within a certain area: these
#   should be projected on the avg of all of them: use a counter for this.
# - clean up a bit: some functions return objects, other return the strings.
#   Compare e.g. toOffStr, toX3dDoc. This is mainly since there are no Off
#   objects. But if you compare toPsPiecesStr, it returns a str, but there are
#   PS objects.

# FIXED:
#
# 20090215: fixed:
# - 20090214: check Geom3D.intersectWithFacet by trying many templates. If ok
#             remove old code from this function.
# - 20090211: For min max cases A5xI I end up in an TODO assert, even if the
#             faces don't dissapear. Also for the S4A4 case with 3 in one plane.
#
# 20090214: fixed:
# - 20090212: For octa compound 4A.D4xI.C2xI.mu4.off I end up in a different
#             assert: assert len(pOnLineAtEdges) % 2 == 0, "The nr of
#             intersections should be even, are all edges unique and do they
#             form one closed face?"

DefaultScene = './scene_orbit.py'

def onSwitchFrontBack(canvas):
    if glGetIntegerv(GL_FRONT_FACE) == GL_CCW:
        glFrontFace(GL_CW)
    else:
        glFrontFace(GL_CCW)
    canvas.paint()

class Canvas3DScene(Scenes3D.Interactive3DCanvas):
    def __init__(this, shape, *args, **kwargs):
        this.shape = shape
        Scenes3D.Interactive3DCanvas.__init__(this, *args, **kwargs)

    def initGl(this):
        this.setCameraPosition(15.0)
        Scenes3D.Interactive3DCanvas.initGl(this)

        #glShadeModel(GL_SMOOTH)

        glEnableClientState(GL_VERTEX_ARRAY);
        glEnableClientState(GL_NORMAL_ARRAY)

        matAmbient    = [0.2, 0.2, 0.2, 0.0]
        matDiffuse    = [0.1, 0.6, 0.0, 0.0]
        #matSpecular   = [0.2, 0.2, 0.2, 1.]
        matShininess  = 0.0
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, matAmbient)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, matDiffuse)
        #glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, matSpecular)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, matShininess)

        lightPosition = [10.0, -30.0, -20.0, 0.0]
        lightAmbient  = [0.3, 0.3, 0.3, 1.0]
        lightDiffuse  = [0.5, 0.5, 0.5, 1.0]
        # disable specular part:
        lightSpecular = [0., 0., 0., 1.]
        glLightfv(GL_LIGHT0, GL_POSITION, lightPosition)
        glLightfv(GL_LIGHT0, GL_AMBIENT, lightAmbient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, lightDiffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, lightSpecular)
        glEnable(GL_LIGHT0)

        lightPosition = [-30.0, 0.0, -20.0, 0.0]
        lightAmbient  = [0.0, 0.0, 0.0, 1.]
        lightDiffuse  = [0.08, 0.08, 0.08, 1.]
        lightSpecular = [0.0, 0.0, 0.0, 1.]
        glLightfv(GL_LIGHT1, GL_POSITION, lightPosition)
        glLightfv(GL_LIGHT1, GL_AMBIENT, lightAmbient)
        glLightfv(GL_LIGHT1, GL_DIFFUSE, lightDiffuse)
        glLightfv(GL_LIGHT1, GL_SPECULAR, lightSpecular)
        glEnable(GL_LIGHT1)

        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glClearColor(this.bgCol[0], this.bgCol[1], this.bgCol[2], 0)

    def setBgCol(this, bgCol):
        """rgb in value between 0 and 1"""
        this.bgCol = bgCol
        glClearColor(bgCol[0], bgCol[1], bgCol[2], 0)

    def getBgCol(this):
        """rgb in value between 0 and 1"""
        return this.bgCol

    def onPaint(this):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        this.shape.glDraw()

class MainWindow(wx.Frame):
    wildcard = "OFF shape (*.off)|*.off| Python shape (*.py)|*.py"
    def __init__(this, TstScene, shape, p_args, *args, **kwargs):
        wx.Frame.__init__(this, *args, **kwargs)
        this.addMenuBar()
        this.statusBar = this.CreateStatusBar()
        this.scene = None
        this.exportDirName = '.'
        this.importDirName = '.'
        this.sceneDirName = '.'
        this.viewSettingsWindow = None
        this.colourSettingsWindow = None
        this.transformSettingsWindow = None
        this.scene = None
        this.panel = MainPanel(this, TstScene, shape, wx.ID_ANY)
        if len(p_args) > 0 and (
            p_args[0][-4:] == '.off' or p_args[0][-3:] == '.py'
        ):
            this.openFile(p_args[0])
        this.Show(True)
        this.Bind(wx.EVT_CLOSE, this.onClose)
        this.keySwitchFronBack = wx.NewIdRef().GetId()
        ac = [
            (wx.ACCEL_NORMAL, wx.WXK_F3, this.keySwitchFronBack)
        ]
        this.Bind(wx.EVT_MENU, this.onKeyDown, id=this.keySwitchFronBack)
        this.SetAcceleratorTable(wx.AcceleratorTable(ac))

    def addMenuBar(this):
        menuBar = wx.MenuBar()
        menuBar.Append(this.createFileMenu(), '&File')
        menuBar.Append(this.createEditMenu(), '&Edit')
        menuBar.Append(this.createViewMenu(), '&View')
        menuBar.Append(this.createToolsMenu(), '&Tools')
        this.SetMenuBar(menuBar)

    def createFileMenu(this):
        menu = wx.Menu()

        openGui = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Open\tCtrl+O"
            )
        this.Bind(wx.EVT_MENU, this.onOpen, id = openGui.GetId())
        menu.Append(openGui)

        openGui = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Reload\tCtrl+R"
            )
        this.Bind(wx.EVT_MENU, this.onReload, id = openGui.GetId())
        menu.Append(openGui)

        add = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Add\tCtrl+A"
            )
        this.Bind(wx.EVT_MENU, this.onAdd, id = add.GetId())
        menu.Append(add)
        export = wx.Menu()

        saveAsPy = wx.MenuItem(
                export,
                wx.ID_ANY,
                text = "&Python\tCtrl+Y"
            )
        this.Bind(wx.EVT_MENU, this.onSaveAsPy, id = saveAsPy.GetId())
        export.Append(saveAsPy)

        saveAsOff = wx.MenuItem(
                export,
                wx.ID_ANY,
                text = "&Off\tCtrl+E"
            )
        this.Bind(wx.EVT_MENU, this.onSaveAsOff, id = saveAsOff.GetId())
        export.Append(saveAsOff)

        saveAsPs = wx.MenuItem(
                export,
                wx.ID_ANY,
                text = "&PS\tCtrl+P"
            )
        this.Bind(wx.EVT_MENU, this.onSaveAsPs, id = saveAsPs.GetId())
        export.Append(saveAsPs)

        saveAsWrl = wx.MenuItem(
                export,
                wx.ID_ANY,
                text = "&VRML\tCtrl+V"
            )
        this.Bind(wx.EVT_MENU, this.onSaveAsWrl, id = saveAsWrl.GetId())
        export.Append(saveAsWrl)

        menu.AppendSubMenu(export, "&Export")
        menu.AppendSeparator()
        exit = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "E&xit\tCtrl+Q"
            )
        this.Bind(wx.EVT_MENU, this.onExit, id = exit.GetId())
        menu.Append(exit)
        return menu

    def createEditMenu(this):
        menu = wx.Menu()

        viewSettings = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&View Settings\tCtrl+W"
            )
        this.Bind(wx.EVT_MENU, this.onViewSettings, id = viewSettings.GetId())
        menu.Append(viewSettings)

        colourSettings = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Colours\tCtrl+C"
            )
        this.Bind(wx.EVT_MENU, this.onColourSettings, id = colourSettings.GetId())
        menu.Append(colourSettings)

        transformSettings = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Transform\tCtrl+T"
            )
        this.Bind(wx.EVT_MENU, this.onTransform, id = transformSettings.GetId())
        menu.Append(transformSettings)

        return menu

    def createToolsMenu(this):
        menu = wx.Menu()
        tool = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Dome Level 1\td"
            )
        this.Bind(wx.EVT_MENU, this.onDome, id = tool.GetId())
        menu.Append(tool)
        this.dome1 = tool
        tool = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Dome Level 2\tShift+D"
            )
        this.Bind(wx.EVT_MENU, this.onDome, id = tool.GetId())
        menu.Append(tool)
        this.dome2 = tool
        return menu

    def createViewMenu(this):
        menu = wx.Menu()
        reset = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Reset\tF5"
            )
        this.Bind(wx.EVT_MENU, this.onResetView, id = reset.GetId())
        menu.Append(reset)
        scene = wx.MenuItem(
                menu,
                wx.ID_ANY,
                text = "&Scene..."
            )
        this.Bind(wx.EVT_MENU, this.onOpenScene, id = scene.GetId())
        menu.Append(scene)
        return menu

    def onReload(this, e):
        if this.currentFile != None:
            this.openFile(this.currentFile)
        elif this.currentScene != None:
            this.setScene(this.currentScene)

    def onOpen(this, e):
        dlg = wx.FileDialog(this, 'New: Choose a file',
                this.importDirName, '', this.wildcard, wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            if dirname != None:
                filename = os.path.join(dirname, filename)
            this.openFile(filename)
        dlg.Destroy()

    def readShapeFile(this, filename):
        isOffModel = filename[-3:] == 'off'
        print("opening file:", filename)
        fd = open(filename, 'r')
        if isOffModel:
            shape = Geom3D.readOffFile(fd, recreateEdges = True)
        else:
            assert filename[-2:] == 'py'
            shape = Geom3D.readPyFile(fd)
        this.setStatusStr("file opened")
        fd.close()
        return shape

    def openFile(this, filename):
        this.closeCurrentScene()
        dirname = os.path.dirname(filename)
        if dirname != "":
            this.importDirName = dirname
        try:
            shape = this.readShapeFile(filename)
        except AssertionError:
            this.setStatusStr("ERROR reading file")
            raise
        if isinstance(shape, Geom3D.CompoundShape):
            # convert to SimpleShape first, since adding to IsometricShape
            # will not work.
            shape = shape.simple_shape
        # Create a compound shape to be able to add shapes later.
        shape = Geom3D.CompoundShape([shape], name = filename)
        this.panel.setShape(shape)
        # overwrite the view properties, if the shape doesn't have any
        # faces and would be invisible to the user otherwise
        if len(shape.getFaceProperties()['Fs']) == 0 and (
            this.panel.getShape().getVertexProperties()['radius'] <= 0
        ):
            this.panel.getShape().setVertexProperties(radius = 0.05)
        this.SetTitle('%s' % os.path.basename(filename))
        # Save for reload:
        this.currentFile = filename
        this.currentScene = None

    def onAdd(this, e):
        dlg = wx.FileDialog(this, 'Add: Choose a file',
                this.importDirName, '', this.wildcard, wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            isOffModel = filename[-3:] == 'off'
            this.importDirName  = dlg.GetDirectory()
            print("adding file:", filename)
            fd = open(os.path.join(this.importDirName, filename), 'r')
            if isOffModel:
                shape = Geom3D.readOffFile(fd, recreateEdges = True)
            else:
                shape = Geom3D.readPyFile(fd)
            if isinstance(shape, Geom3D.CompoundShape):
                # convert to SimpleShape first, since adding a IsometricShape
                # will not work.
                shape = shape.simple_shape
            try:
                this.panel.getShape().addShape(shape)
            except AttributeError:
                print("warning: cannot 'add' a shape to this scene, use 'File->Open' instead")
            this.setStatusStr("OFF file added")
            fd.close()
            # TODO: set better title
            this.SetTitle('Added: %s' % os.path.basename(filename))
        dlg.Destroy()

    def onSaveAsPy(this, e):
        dlg = wx.FileDialog(this, 'Save as .py file',
            this.exportDirName, '', '*.py',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            filename = dlg.GetFilename()
            this.exportDirName  = filepath.rsplit('/', 1)[0]
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
            shape = this.panel.getShape()
            shape.name = filename
            shape.saveFile(fd)
            this.setStatusStr("Python file written")
        dlg.Destroy()

    def onSaveAsOff(this, e):
        dlg = ExportOffDialog(this, wx.ID_ANY, 'OFF settings')
        fileChoosen = False
        while not fileChoosen:
            if dlg.ShowModal() == wx.ID_OK:
                extraInfo = dlg.getExtraInfo()
                cleanUp = dlg.getCleanUp()
                precision = dlg.getPrecision()
                margin = dlg.getFloatMargin()
                fileDlg = wx.FileDialog(this, 'Save as .off file',
                    this.exportDirName, '', '*.off',
                    wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                )
                fileChoosen = fileDlg.ShowModal() == wx.ID_OK
                if fileChoosen:
                    filepath = fileDlg.GetPath()
                    filename = fileDlg.GetFilename()
                    this.exportDirName  = filepath.rsplit('/', 1)[0]
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
                    shape = this.panel.getShape()
                    try:
                        shape = shape.simple_shape
                    except AttributeError:
                        pass
                    if cleanUp:
                        shape = shape.cleanShape(margin)
                    fd.write(shape.toOffStr(precision, extraInfo))
                    print("OFF file written")
                    this.setStatusStr("OFF file written")
                    fd.close()
                else:
                    dlg.Show()
                fileDlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def onSaveAsPs(this, e):
        dlg = ExportPsDialog(this, wx.ID_ANY, 'PS settings')
        fileChoosen = False
        while not fileChoosen:
            if dlg.ShowModal() == wx.ID_OK:
                scalingFactor = dlg.getScaling()
                precision = dlg.getPrecision()
                margin = dlg.getFloatMargin()
                assert (scalingFactor >= 0 and scalingFactor != None)
                fileDlg = wx.FileDialog(this, 'Save as .ps file',
                    this.exportDirName, '', '*.ps',
                    style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
                )
                fileChoosen = fileDlg.ShowModal() == wx.ID_OK
                if fileChoosen:
                    filepath = fileDlg.GetPath()
                    filename = fileDlg.GetFilename()
                    this.exportDirName  = filepath.rsplit('/', 1)[0]
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
                    shape = this.panel.getShape()
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
                        this.setStatusStr("PS file written")
                    except Geom3D.PrecisionError:
                        this.setStatusStr(
                            "Precision error, try to decrease float margin")

                    fd.close()
                else:
                    dlg.Show()
                fileDlg.Destroy()
            else:
                break
        # done while: file choosen
        dlg.Destroy()

    def onSaveAsWrl(this, e):
        dlg = wx.FileDialog(this,
            'Save as .vrml file', this.exportDirName, '', '*.wrl',
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = fileDlg.GetPath()
            filename = dlg.GetFilename()
            this.exportDirName  = filepath.rsplit('/', 1)[0]
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
            r = this.panel.getShape().getEdgeProperties()['radius']
            x3dObj = this.panel.getShape().toX3dDoc(edgeRadius = r)
            x3dObj.setFormat(X3D.VRML_FMT)
            fd.write(x3dObj.toStr())
            this.setStatusStr("VRML file written")
            fd.close()
        dlg.Destroy()

    def onViewSettings(this, e):
        if this.viewSettingsWindow == None:
            this.viewSettingsWindow = ViewSettingsWindow(this.panel.getCanvas(),
                None, wx.ID_ANY,
                title = 'View Settings',
                size = (394, 300)
            )
            this.viewSettingsWindow.Bind(wx.EVT_CLOSE, this.onViewSettingsClose)
        else:
            this.viewSettingsWindow.SetFocus()
            this.viewSettingsWindow.Raise()

    def onColourSettings(this, e):
        if not this.colourSettingsWindow is None:
            # Don't reuse, the colours might be wrong after loading a new model
            this.colourSettingsWindow.Destroy()
        this.colourSettingsWindow = ColourSettingsWindow(
            this.panel.getCanvas(), 5, None, wx.ID_ANY,
            title = 'Colour Settings',
        )
        this.colourSettingsWindow.Bind(wx.EVT_CLOSE, this.onColourSettingsClose)

    def onTransform(this, e):
        if this.transformSettingsWindow == None:
            this.transformSettingsWindow = TransformSettingsWindow(
                this.panel.getCanvas(), None, wx.ID_ANY,
                title = 'Transform Settings',
            )
            this.transformSettingsWindow.Bind(wx.EVT_CLOSE, this.onTransformSettingsClose)
        else:
            this.transformSettingsWindow.SetFocus()
            this.transformSettingsWindow.Raise()

    def onDome(this, event):
        if this.dome1.GetId() == event.GetId(): level = 1
        else: level = 2
        shape = this.panel.getShape().getDome(level)
        if shape != None:
            this.panel.setShape(shape)
            this.SetTitle("Dome %s" % this.GetTitle())

    def onOpenScene(this, e):
        wildcard = "Scene plugin (Scene_*.py)|?cene_*.py"
        dlg = wx.FileDialog(this, 'New: Choose a Scene',
                this.sceneDirName, '', wildcard, wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            print('filepath', filepath)
            this.sceneDirName = filepath.rsplit('/', 1)[0]
            print('sceneDirName', this.sceneDirName)
            shape = this.readSceneFile(filepath)
        dlg.Destroy()

    def readSceneFile(this, filename):
        print("Starting scene", filename)
        fd = open(filename, 'r')
        ed = {}
        exec(fd.read(), ed)
        scene = {
            'lab': ed['TITLE'],
            'class': ed['Scene']
        }
        this.setScene(scene)

    def setScene(this, scene):
        this.closeCurrentScene()
        print('Switch to scene "%s"' % scene['lab'])
        canvas = this.panel.getCanvas()
        this.scene = scene['class'](this, canvas)
        this.panel.setShape(this.scene.shape)
        this.SetTitle(scene['lab'])
        canvas.resetOrientation()
        try:
            this.viewSettingsWindow.reBuild()
        except AttributeError:
            pass
        # save for reload:
        this.currentScene = scene
        this.currentFile = None

    def onResetView(this, e):
        this.panel.getCanvas().resetOrientation()

    def closeCurrentScene(this):
        if this.scene != None:
            this.scene.close()
            del this.scene
            this.scene = None

    def setStatusStr(this, str):
        this.statusBar.SetStatusText(str)

    def onExit(this, e):
        dlg = wx.MessageDialog(None,
                               'Are you sure you want to quit?', 'Question',
                               wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            dlg.Destroy()
            this.Close(True)
        else:
            dlg.Destroy()

    def onViewSettingsClose(this, event):
        this.viewSettingsWindow.Destroy()
        this.viewSettingsWindow = None

    def onColourSettingsClose(this, event):
        this.colourSettingsWindow.Destroy()
        this.colourSettingsWindow = None

    def onTransformSettingsClose(this, event):
        this.transformSettingsWindow.Destroy()
        this.transformSettingsWindow = None

    def onClose(this, event):
        print('main onclose')
        if this.viewSettingsWindow != None:
            this.viewSettingsWindow.Close()
        if this.colourSettingsWindow != None:
            this.colourSettingsWindow.Close()
        if this.transformSettingsWindow != None:
            this.transformSettingsWindow.Close()
        this.Destroy()

    def onKeyDown(this, e):
        id = e.GetId()
        if id == this.keySwitchFronBack:
            onSwitchFrontBack(this.panel.getCanvas())

class MainPanel(wx.Panel):
    def __init__(this, parent, TstScene, shape, *args, **kwargs):
        wx.Panel.__init__(this, parent, *args, **kwargs)
        this.parent = parent
        # Note that uncommenting this will override the default size
        # handler, which resizes the sizers that are part of the Frame.
        this.Bind(wx.EVT_SIZE, this.onSize)

        this.canvas = TstScene(shape, this)
        this.canvas.panel = this
        this.canvas.SetMinSize((300, 300))
        this.canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        this.canvasSizer.Add(this.canvas, 1, wx.SHAPED)

        # Ctrl Panel:
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(this.canvasSizer, 1, wx.SHAPED)
        this.SetSizer(mainSizer)
        this.SetAutoLayout(True)
        this.Layout()

    def getCanvas(this):
        return this.canvas

    def onSize(this, event):
        """Print the size plus an offset for y that includes the title bar.

        This function is used to set the ctrl window size in the interactively.
        Bind this function, and read and set the correct size in the scene.
        """
        s = this.GetClientSize()
        print('Window size:', (s[0]+2, s[1]+54))
        this.Layout()

    def setShape(this, shape):
        """Set a new shape to be shown with the current viewing settings

        shape: the new shape. This will refresh the canvas.
        """
        oldShape = this.canvas.shape
        this.canvas.shape = shape
        # Use all the vertex settings except for Vs, i.e. keep the view
        # vertex settings the same.
        oldVSettings = oldShape.getVertexProperties()
        del oldVSettings['Vs']
        del oldVSettings['Ns']
        this.canvas.shape.setVertexProperties(oldVSettings)
        # Use all the edge settings except for Es
        oldESettings = oldShape.getEdgeProperties()
        del oldESettings['Es']
        this.canvas.shape.setEdgeProperties(oldESettings)
        # Use only the 'drawFaces' setting:
        oldFSettings = {
                'drawFaces': oldShape.getFaceProperties()['drawFaces']
            }
        this.canvas.shape.setFaceProperties(oldFSettings)
        # if the shape generates the normals itself:
        # TODO: handle that this.Ns is set correctly, i.e. normalised
        if shape.generateNormals:
            glDisable(GL_NORMALIZE)
        else:
            glEnable(GL_NORMALIZE)
        this.canvas.paint()
        this.parent.setStatusStr("Shape Updated")
        del oldShape

    def getShape(this):
        """Return the current shape object
        """
        return this.canvas.shape

class ColourSettingsWindow(wx.Frame):
    def __init__(this, canvas, width, *args, **kwargs):
        wx.Frame.__init__(this, *args, **kwargs)
        this.canvas    = canvas
        this.col_width = width
        this.statusBar = this.CreateStatusBar()
        this.panel     = wx.Panel(this, wx.ID_ANY)
        this.cols = this.canvas.shape.getFaceProperties()['colors']
        # take a copy for reset
        this.org_cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in this.cols]
        this.addContents()

    def addContents(this):
        this.colSizer = wx.BoxSizer(wx.VERTICAL)

        this.selColGuis = []
        i = 0
        shape_idx = 0
        # assume compound shape
        for shape_cols in this.cols:
            # use one colour select per colour for each sub-shape
            added_cols = []
            col_idx = 0
            for col in shape_cols[0]:
                wxcol = wx.Colour(255*col[0], 255*col[1], 255*col[2])
                if not wxcol in added_cols:
                    if i % this.col_width == 0:
                        selColSizerRow = wx.BoxSizer(wx.HORIZONTAL)
                        this.colSizer.Add(selColSizerRow, 0, wx.EXPAND)
                    this.selColGuis.append(
                        wx.ColourPickerCtrl(
                            this.panel, wx.ID_ANY, wxcol))
                    this.panel.Bind(wx.EVT_COLOURPICKER_CHANGED, this.onColSel)
                    selColSizerRow.Add(this.selColGuis[-1], 0, wx.EXPAND)
                    i += 1
                    # connect GUI to shape_idx and col_idx
                    this.selColGuis[-1].my_shape_idx = shape_idx
                    this.selColGuis[-1].my_cols = [col_idx]
                    # connect wxcolour to GUI
                    wxcol.my_gui = this.selColGuis[-1]
                    added_cols.append(wxcol)
                else:
                    gui = added_cols[added_cols.index(wxcol)].my_gui
                    # must be same shape_id
                    gui.my_cols.append(col_idx)
                col_idx += 1
            shape_idx += 1

        this.noOfCols = i
        this.Guis = []

        this.subSizer = wx.BoxSizer(wx.HORIZONTAL)
        this.colSizer.Add(this.subSizer)

        this.Guis.append(wx.Button(this.panel, label='Cancel'))
        this.Guis[-1].Bind(wx.EVT_BUTTON, this.onCancel)
        this.subSizer.Add(this.Guis[-1], 0, wx.EXPAND)

        this.Guis.append(wx.Button(this.panel, label='Reset'))
        this.Guis[-1].Bind(wx.EVT_BUTTON, this.onReset)
        this.subSizer.Add(this.Guis[-1], 0, wx.EXPAND)

        this.Guis.append(wx.Button(this.panel, label='Done'))
        this.Guis[-1].Bind(wx.EVT_BUTTON, this.onDone)
        this.subSizer.Add(this.Guis[-1], 0, wx.EXPAND)

        this.panel.SetSizer(this.colSizer)
        this.panel.SetAutoLayout(True)
        this.panel.Layout()
        this.Show(True)

    def onReset(this, e):
        for colgui in this.selColGuis:
             shape_idx = colgui.my_shape_idx
             col_idx = colgui.my_cols[0]
             c = this.org_cols[shape_idx][0][col_idx]
             wxcol = wx.Colour(255*c[0], 255*c[1], 255*c[2])
             colgui.SetColour(wxcol)
        this.cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in this.org_cols]
        this.updatShapeColours()

    def onCancel(this, e):
        this.cols = [[[c for c in col_idx] for col_idx in shape_cols] for shape_cols in this.org_cols]
        this.updatShapeColours()
        this.Close()

    def onDone(this, e):
        this.Close()

    def onColSel(this, e):
        wxcol = e.GetColour().Get()
        col = (float(wxcol[0])/255, float(wxcol[1])/255, float(wxcol[2])/255)
        gui_id = e.GetId()
        for gui in this.selColGuis:
            if gui.GetId() == gui_id:
                shape_cols = this.cols[gui.my_shape_idx][0]
                for col_idx in gui.my_cols:
                    shape_cols[col_idx] = col
                this.updatShapeColours()

    def updatShapeColours(this):
        this.canvas.shape.setFaceProperties(colors=this.cols)
        this.canvas.paint()

    def close(this):
        for Gui in this.Guis:
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
    def __init__(this, canvas, *args, **kwargs):
        wx.Frame.__init__(this, *args, **kwargs)
        this.canvas    = canvas
        this.statusBar = this.CreateStatusBar()
        this.panel     = wx.Panel(this, wx.ID_ANY)
        this.addContents()

    def addContents(this):
        this.ctrlSizer = ViewSettingsSizer(this, this.panel, this.canvas)
        if this.canvas.shape.dimension == 4:
            this.setDefaultSize((413, 791))
        else:
            this.setDefaultSize((380, 414))
        this.panel.SetSizer(this.ctrlSizer)
        this.panel.SetAutoLayout(True)
        this.panel.Layout()
        this.Show(True)

    # move to general class
    def setDefaultSize(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

    def reBuild(this):
        # Doesn't work out of the box (Guis are not destroyed...):
        #this.ctrlSizer.Destroy()
        this.ctrlSizer.close()
        this.addContents()

    def setStatusStr(this, str):
        this.statusBar.SetStatusText(str)

class ViewSettingsSizer(wx.BoxSizer):
    cull_show_none  = 'Hide'
    cull_show_both  = 'Show Front and Back Faces'
    cull_show_front = 'Show Only Front Face'
    cull_show_back  = 'Show Only Back Face'
    def __init__(this, parentWindow, parentPanel, canvas, *args, **kwargs):
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

        this.Guis = []
        this.Boxes = []
        wx.BoxSizer.__init__(this, wx.VERTICAL, *args, **kwargs)
        this.canvas       = canvas
        this.parentWindow = parentWindow
        this.parentPanel  = parentPanel
        # Show / Hide vertices
        vProps            = canvas.shape.getVertexProperties()
        this.vR           = vProps['radius']
        this.vOptionsLst  = ['hide', 'show']
        if this.vR > 0:
            default = 1 # key(1) = 'show'
        else:
            default = 0 # key(0) = 'hide'
        this.vOptionsGui  = wx.RadioBox(this.parentPanel,
            label = 'Vertex Options',
            style = wx.RA_VERTICAL,
            choices = this.vOptionsLst
        )
        this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onVOption, id = this.vOptionsGui.GetId())
        this.vOptionsGui.SetSelection(default)
        # Vertex Radius
        nrOfSliderSteps   = 40
        this.vRadiusMin   = 0.01
        this.vRadiusMax   = 0.100
        this.vRadiusScale = 1.0 / this.vRadiusMin
        s = (this.vRadiusMax - this.vRadiusMin) * this.vRadiusScale
        if int(s) < nrOfSliderSteps:
            this.vRadiusScale = (this.vRadiusScale * nrOfSliderSteps) / s
        this.vRadiusGui = wx.Slider(this.parentPanel,
            value = this.vRadiusScale * this.vR,
            minValue = this.vRadiusScale * this.vRadiusMin,
            maxValue = this.vRadiusScale * this.vRadiusMax,
            style = wx.SL_HORIZONTAL
        )
        this.Guis.append(this.vRadiusGui)
        this.parentPanel.Bind(wx.EVT_SLIDER, this.onVRadius, id = this.vRadiusGui.GetId())
        this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Vertex radius'))
        vRadiusSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        # disable if vertices are hidden anyway:
        if default != 1:
            this.vRadiusGui.Disable()
        # Vertex Colour
        this.vColorGui = wx.Button(this.parentPanel, wx.ID_ANY, "Colour")
        this.Guis.append(this.vColorGui)
        this.parentPanel.Bind(wx.EVT_BUTTON, this.onVColor, id = this.vColorGui.GetId())
        # Show / hide edges
        eProps           = canvas.shape.getEdgeProperties()
        this.eR          = eProps['radius']
        this.eOptionsLst = ['hide', 'as cylinders', 'as lines']
        if eProps['drawEdges']:
            if this.vR > 0:
                default = 1 # key(1) = 'as cylinders'
            else:
                default = 2 # key(2) = 'as lines'
        else:
            default     = 0 # key(0) = 'hide'
        this.eOptionsGui = wx.RadioBox(this.parentPanel,
            label = 'Edge Options',
            style = wx.RA_VERTICAL,
            choices = this.eOptionsLst
        )
        this.Guis.append(this.eOptionsGui)
        this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onEOption, id = this.eOptionsGui.GetId())
        this.eOptionsGui.SetSelection(default)
        # Edge Radius
        nrOfSliderSteps   = 40
        this.eRadiusMin   = 0.008
        this.eRadiusMax   = 0.08
        this.eRadiusScale = 1.0 / this.eRadiusMin
        s = (this.eRadiusMax - this.eRadiusMin) * this.eRadiusScale
        if int(s) < nrOfSliderSteps:
            this.eRadiusScale = (this.eRadiusScale * nrOfSliderSteps) / s
        this.eRadiusGui = wx.Slider(this.parentPanel,
            value = this.eRadiusScale * this.eR,
            minValue = this.eRadiusScale * this.eRadiusMin,
            maxValue = this.eRadiusScale * this.eRadiusMax,
            style = wx.SL_HORIZONTAL
        )
        this.Guis.append(this.eRadiusGui)
        this.parentPanel.Bind(wx.EVT_SLIDER, this.onERadius, id = this.eRadiusGui.GetId())
        this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Edge radius'))
        eRadiusSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        # disable if edges are not drawn as scalable items anyway:
        if default != 1:
            this.eRadiusGui.Disable()
        # Edge Colour
        this.eColorGui = wx.Button(this.parentPanel, wx.ID_ANY, "Colour")
        this.Guis.append(this.eColorGui)
        this.parentPanel.Bind(wx.EVT_BUTTON, this.onEColor, id = this.eColorGui.GetId())
        # Show / hide face
        this.fOptionsLst = [
            this.cull_show_both,
            this.cull_show_front,
            this.cull_show_back,
            this.cull_show_none,
        ]
        this.fOptionsGui = wx.RadioBox(this.parentPanel,
            label = 'Face Options',
            style = wx.RA_VERTICAL,
            choices = this.fOptionsLst
        )
        this.Guis.append(this.fOptionsGui)
        this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onFOption, id = this.fOptionsGui.GetId())
        faceSizer = wx.BoxSizer(wx.HORIZONTAL)
        faceSizer.Add(this.fOptionsGui, 1, wx.EXPAND)
        if not glIsEnabled(GL_CULL_FACE):
            this.fOptionsGui.SetStringSelection(this.cull_show_both)
        else:
            # Looks like I switch front and back here, but this makes sense from
            # the GUI.
            if glGetInteger(GL_CULL_FACE_MODE) == GL_FRONT:
                this.fOptionsGui.SetStringSelection(this.cull_show_front)
            if glGetInteger(GL_CULL_FACE_MODE) == GL_BACK:
                this.fOptionsGui.SetStringSelection(this.cull_show_back)
            else: # ie GL_FRONT_AND_BACK
                this.fOptionsGui.SetStringSelection(this.cull_show_none)

        # Open GL
        this.Boxes.append(wx.StaticBox(this.parentPanel,
                                                label = 'OpenGL Settings'))
        oglSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        this.Guis.append(
            wx.CheckBox(this.parentPanel,
                                label = 'Switch Front and Back Face (F3)')
        )
        this.oglFrontFaceGui = this.Guis[-1]
        this.oglFrontFaceGui.SetValue(glGetIntegerv(GL_FRONT_FACE) == GL_CW)
        this.parentPanel.Bind(wx.EVT_CHECKBOX, this.onOgl,
                                        id = this.oglFrontFaceGui.GetId())
        # background Colour
        colTxt = wx.StaticText(this.parentPanel, -1, "Background Colour: ")
        this.Guis.append(colTxt)
        col = this.canvas.getBgCol()
        this.bgColorGui = wx.lib.colourselect.ColourSelect(this.parentPanel,
            wx.ID_ANY, colour = (col[0]*255, col[1]*255, col[2]*255),
            size=wx.Size(40, 30))
        this.Guis.append(this.bgColorGui)
        this.parentPanel.Bind(wx.lib.colourselect.EVT_COLOURSELECT,
            this.onBgCol)

        # Sizers
        vRadiusSizer.Add(this.vRadiusGui, 1, wx.EXPAND | wx.TOP    | wx.LEFT)
        vRadiusSizer.Add(this.vColorGui,  1,             wx.BOTTOM | wx.LEFT)
        eRadiusSizer.Add(this.eRadiusGui, 1, wx.EXPAND | wx.TOP    | wx.LEFT)
        eRadiusSizer.Add(this.eColorGui,  1,             wx.BOTTOM | wx.LEFT)
        #sizer = wx.BoxSizer(wx.VERTICAL)
        vSizer = wx.BoxSizer(wx.HORIZONTAL)
        vSizer.Add(this.vOptionsGui, 2, wx.EXPAND)
        vSizer.Add(vRadiusSizer, 5, wx.EXPAND)
        eSizer = wx.BoxSizer(wx.HORIZONTAL)
        eSizer.Add(this.eOptionsGui, 2, wx.EXPAND)
        eSizer.Add(eRadiusSizer, 5, wx.EXPAND)
        bgSizerSub = wx.BoxSizer(wx.HORIZONTAL)
        bgSizerSub.Add(colTxt, 0, wx.EXPAND)
        bgSizerSub.Add(this.bgColorGui, 0, wx.EXPAND)
        bgSizerSub.Add(wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND)
        oglSizer.Add(this.oglFrontFaceGui, 0, wx.EXPAND)
        oglSizer.Add(bgSizerSub, 0, wx.EXPAND)
        this.Add(vSizer, 5, wx.EXPAND)
        this.Add(eSizer, 5, wx.EXPAND)
        this.Add(faceSizer, 6, wx.EXPAND)
        this.Add(oglSizer, 0, wx.EXPAND)

        # 4D stuff
        if this.canvas.shape.dimension == 4:
            default = 0
            this.useTransparencyGui = wx.RadioBox(this.parentPanel,
                label = 'Use Transparency',
                style = wx.RA_VERTICAL,
                choices = ['Yes', 'No']
            )
            this.Guis.append(this.useTransparencyGui)
            this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onUseTransparency, id = this.useTransparencyGui.GetId())
            this.useTransparencyGui.SetSelection(default)
            faceSizer.Add(this.useTransparencyGui, 1, wx.EXPAND)

            default = 0
            this.showUnscaledEdgesGui = wx.RadioBox(this.parentPanel,
                label = 'Unscaled Edges',
                style = wx.RA_VERTICAL,
                choices = ['Show', 'Hide']
            )
            this.Guis.append(this.showUnscaledEdgesGui)
            this.parentPanel.Bind(wx.EVT_RADIOBOX, this.onShowUnscaledEdges, id =
            this.showUnscaledEdgesGui.GetId())
            this.showUnscaledEdgesGui.SetSelection(default)
            faceSizer.Add(this.showUnscaledEdgesGui, 1, wx.EXPAND)

            min   = 0.01
            max   = 1.0
            steps = 100
            this.cellScaleFactor = float(max - min) / steps
            this.cellScaleOffset = min
            this.scaleGui = wx.Slider(
                    this.parentPanel,
                    value = 100,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            this.Guis.append(this.scaleGui)
            this.parentPanel.Bind(
                wx.EVT_SLIDER, this.onScale, id = this.scaleGui.GetId()
            )
            this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Scale Cells'))
            scaleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
            scaleSizer.Add(this.scaleGui, 1, wx.EXPAND)

            # 4D -> 3D projection properties: camera and prj volume distance
            steps = 100
            min   = 0.1
            max   = 5
            this.prjVolFactor = float(max - min) / steps
            this.prjVolOffset = min
            this.prjVolGui = wx.Slider(
                    this.parentPanel,
                    value = this.Value2Slider(
                            this.prjVolFactor,
                            this.prjVolOffset,
                            this.canvas.shape.wProjVolume
                        ),
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            this.Guis.append(this.prjVolGui)
            this.parentPanel.Bind(
                wx.EVT_SLIDER, this.onPrjVolAdjust, id = this.prjVolGui.GetId()
            )
            this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Projection Volume W-Coordinate'))
            prjVolSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
            prjVolSizer.Add(this.prjVolGui, 1, wx.EXPAND)
            min   = 0.5
            max   = 5
            this.camDistFactor = float(max - min) / steps
            this.camDistOffset = min
            this.camDistGui = wx.Slider(
                    this.parentPanel,
                    value = this.Value2Slider(
                            this.camDistFactor,
                            this.camDistOffset,
                            this.canvas.shape.wCameraDistance
                        ),
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            this.Guis.append(this.camDistGui)
            this.parentPanel.Bind(
                wx.EVT_SLIDER, this.onPrjVolAdjust, id = this.camDistGui.GetId()
            )
            this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Camera Distance (from projection volume)'))
            camDistSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
            camDistSizer.Add(this.camDistGui, 1, wx.EXPAND)

            # Create a ctrl for specifying a 4D rotation
            this.Boxes.append(wx.StaticBox(parentPanel, label = 'Rotate 4D Object'))
            rotationSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
            this.Boxes.append(wx.StaticBox(parentPanel, label = 'In a Plane Spanned by'))
            planeSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
            this.v0Gui = geom_gui.Vector4DInput(
                    this.parentPanel,
                    #label = 'Vector 1',
                    relativeFloatSize = 4,
                    elem_labels = ['x0', 'y0', 'z0', 'w0']
                )
            this.parentPanel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, this.onV, id = this.v0Gui.GetId()
            )
            this.v1Gui = geom_gui.Vector4DInput(
                    this.parentPanel,
                    #label = 'Vector 1',
                    relativeFloatSize = 4,
                    elem_labels = ['x1', 'y1', 'z1', 'w1']
                )
            this.parentPanel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, this.onV, id = this.v1Gui.GetId()
            )
            # Exchange planes
            this.exchangeGui = wx.CheckBox(this.parentPanel, label = "Use Orthogonal Plane instead")
            this.exchangeGui.SetValue(False)
            this.parentPanel.Bind(wx.EVT_CHECKBOX, this.onExchangePlanes, id = this.exchangeGui.GetId())
            #this.Boxes.append?
            this.Guis.append(this.v0Gui)
            this.Guis.append(this.v1Gui)
            this.Guis.append(this.exchangeGui)
            planeSizer.Add(this.v0Gui, 12, wx.EXPAND)
            planeSizer.Add(this.v1Gui, 12, wx.EXPAND)
            planeSizer.Add(this.exchangeGui, 10, wx.EXPAND)

            min   = 0.00
            max   = math.pi
            steps = 360 # step by degree (if you change this, make at least 30 and 45 degrees possible)
            this.angleFactor = float(max - min) / steps
            this.angleOffset = min
            this.angleGui = wx.Slider(
                    this.parentPanel,
                    value = 0,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            this.Guis.append(this.angleGui)
            this.parentPanel.Bind(
                wx.EVT_SLIDER, this.onAngle, id = this.angleGui.GetId()
            )
            this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Using Angle'))
            angleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
            angleSizer.Add(this.angleGui, 1, wx.EXPAND)

            min   = 0.00
            max   = 1.0
            steps = 100
            this.angleScaleFactor = float(max - min) / steps
            this.angleScaleOffset = min
            this.angleScaleGui = wx.Slider(
                    this.parentPanel,
                    value = 0,
                    minValue = 0,
                    maxValue = steps,
                    style = wx.SL_HORIZONTAL
                )
            this.Guis.append(this.angleScaleGui)
            this.parentPanel.Bind(
                wx.EVT_SLIDER, this.onAngleScale, id = this.angleScaleGui.GetId()
            )
            this.Boxes.append(wx.StaticBox(this.parentPanel, label = 'Set Angle (by Scale) of Rotation in the Orthogonal Plane'))
            angleScaleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
            angleScaleSizer.Add(this.angleScaleGui, 1, wx.EXPAND)

            rotationSizer.Add(planeSizer, 12, wx.EXPAND)
            rotationSizer.Add(angleSizer, 5, wx.EXPAND)
            rotationSizer.Add(angleScaleSizer, 5, wx.EXPAND)

            this.Add(scaleSizer, 3, wx.EXPAND)
            this.Add(prjVolSizer, 3, wx.EXPAND)
            this.Add(camDistSizer, 3, wx.EXPAND)
            this.Add(rotationSizer, 12, wx.EXPAND)

        this.setStatusStr()

    def close(this):
        # The 'try' is necessary, since the boxes are destroyed in some OS,
        # while this is necessary for e.g. Ubuntu Hardy Heron.
        for Box in this.Boxes:
            try:
                Box.Destroy()
            except wx._core.PyDeadObjectError: pass
        for Gui in this.Guis:
            Gui.Destroy()

    def setStatusStr(this):
        try:
            this.parentWindow.setStatusStr('V-Radius: %0.5f; E-Radius: %0.5f' % (this.vR, this.eR))
        except AttributeError:
            print("parentWindow.setStatusStr function undefined")

    def onVOption(this, e):
        #print 'onVOption'
        sel = this.vOptionsGui.GetSelection()
        selStr = this.vOptionsLst[sel]
        if selStr == 'show':
            this.vRadiusGui.Enable()
            this.canvas.shape.setVertexProperties(radius = this.vR)
        elif selStr == 'hide':
            this.vRadiusGui.Disable()
            this.canvas.shape.setVertexProperties(radius = -1.0)
        this.canvas.paint()

    def onVRadius(this, e):
        this.vR = (float(this.vRadiusGui.GetValue()) / this.vRadiusScale)
        this.canvas.shape.setVertexProperties(radius = this.vR)
        this.canvas.paint()
        this.setStatusStr()

    def onVColor(this, e):
        dlg = wx.ColourDialog(this.parentWindow)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgba = data.GetColour()
            rgb  = rgba.Get()
            this.canvas.shape.setVertexProperties(
                color = [float(i)/255 for i in rgb]
            )
            this.canvas.paint()
        dlg.Destroy()

    def onEOption(this, e):
        sel = this.eOptionsGui.GetSelection()
        selStr = this.eOptionsLst[sel]
        if selStr == 'hide':
            this.eRadiusGui.Disable()
            this.canvas.shape.setEdgeProperties(drawEdges = False)
        elif selStr == 'as cylinders':
            this.eRadiusGui.Enable()
            this.canvas.shape.setEdgeProperties(drawEdges = True)
            this.canvas.shape.setEdgeProperties(radius = this.eR)
        elif selStr == 'as lines':
            this.eRadiusGui.Disable()
            this.canvas.shape.setEdgeProperties(drawEdges = True)
            this.canvas.shape.setEdgeProperties(radius = 0)
        this.canvas.paint()

    def onERadius(this, e):
        this.eR = (float(this.eRadiusGui.GetValue()) / this.eRadiusScale)
        this.canvas.shape.setEdgeProperties(radius = this.eR)
        this.canvas.paint()
        this.setStatusStr()

    def onEColor(this, e):
        dlg = wx.ColourDialog(this.parentWindow)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgba = data.GetColour()
            rgb  = rgba.Get()
            this.canvas.shape.setEdgeProperties(
                color = [float(i)/255 for i in rgb]
            )
            this.canvas.paint()
        dlg.Destroy()

    def onFOption(this, e):
        print('View Settings Window size:', this.parentWindow.GetSize())
        sel = this.fOptionsGui.GetStringSelection()
        # Looks like I switch front and back here, but this makes sense from
        # the GUI.
        this.canvas.shape.setFaceProperties(drawFaces = True)
        if sel == this.cull_show_both:
            glDisable(GL_CULL_FACE)
        elif sel == this.cull_show_none:
            # don't use culling here: doesn't work with edge radius and vertext
            # radius > 0
            this.canvas.shape.setFaceProperties(drawFaces = False)
            glDisable(GL_CULL_FACE)
        elif sel == this.cull_show_front:
            glCullFace(GL_FRONT)
            glEnable(GL_CULL_FACE)
        elif this.cull_show_back:
            glCullFace(GL_BACK)
            glEnable(GL_CULL_FACE)
        this.canvas.paint()

    def onOgl(this, e):
        id = e.GetId()
        if id == this.oglFrontFaceGui.GetId():
            onSwitchFrontBack(this.canvas)

    def onBgCol(this, e):
        col = e.GetValue().Get()
        this.canvas.setBgCol(
            [float(col[0])/255, float(col[1])/255, float(col[2])/255]
        )
        this.canvas.paint()

    def onUseTransparency(this, event):
        this.canvas.shape.useTransparency((this.useTransparencyGui.GetSelection() == 0))
        this.canvas.paint()

    def onShowUnscaledEdges(this, event):
        this.canvas.shape.setEdgeProperties(
            showUnscaled = (this.showUnscaledEdgesGui.GetSelection() == 0)
        )
        this.canvas.paint()

    def Value2Slider(this, factor, offset, y):
        return (y - offset) / factor

    def Slider2Value(this, factor, offset, x):
        return factor * float(x) + offset

    def onScale(this, event):
        scale = this.Slider2Value(
                this.cellScaleFactor,
                this.cellScaleOffset,
                this.scaleGui.GetValue()
            )
        this.canvas.shape.setCellProperties(scale = scale)
        this.canvas.paint()

    def onPrjVolAdjust(this, event):
        #print 'size =', this.dynDlg.GetClientSize()
        cameraDistance = this.Slider2Value(
                this.camDistFactor,
                this.camDistOffset,
                this.camDistGui.GetValue()
            )
        wProjVolume = this.Slider2Value(
                this.prjVolFactor,
                this.prjVolOffset,
                this.prjVolGui.GetValue()
            )
        if (cameraDistance > 0) and (wProjVolume > 0):
            this.parentWindow.statusBar.SetStatusText(
                "projection volume w = %0.2f; camera distance: %0.3f" % (
                    wProjVolume, cameraDistance
                )
            )
        else:
            if cameraDistance > 0:
                this.parentWindow.statusBar.SetStatusText(
                    'Error: Camera distance should be > 0!'
                )
            else:
                this.parentWindow.statusBar.SetStatusText(
                    'Error: Projection volume:  w should be > 0!'
                )
        this.canvas.shape.setProjectionProperties(cameraDistance, wProjVolume, dbg = True)
        this.canvas.paint()
        event.Skip()

    def onAngle(this, event):
        this.rotate()

    def onAngleScale(this, event):
        this.rotate()

    def onExchangePlanes(this, event):
        this.rotate()

    def onV(this, event):
        this.rotate()

    def rotate(this):
        v0 = this.v0Gui.GetValue()
        v1 = this.v1Gui.GetValue()
        angle = this.Slider2Value(
                this.angleFactor,
                this.angleOffset,
                this.angleGui.GetValue()
            )
        scale = this.Slider2Value(
                this.angleScaleFactor,
                this.angleScaleOffset,
                this.angleScaleGui.GetValue()
            )
        if geomtypes.eq(angle, 0): return
        try:
            v1 = v1.make_orthogonal_to(v0)
            # if vectors are exchange, you actually specify the axial plane
            if this.exchangeGui.IsChecked():
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
            this.canvas.shape.rotate(r)
            this.canvas.paint()
            aDeg = Geom3D.Rad2Deg * angle
            this.parentWindow.statusBar.SetStatusText(
                "Rotation angle: %f degrees (and scaling %0.2f)" % (aDeg, scale)
            )
        except ZeroDivisionError:
            # zero division means 1 of the vectors is (0, 0, 0, 0)
            this.parentWindow.statusBar.SetStatusText("Error: Don't use a zero vector")
            pass
        #except AssertionError:
        #    zV = geomtypes.Vec4([0, 0, 0, 0])
        #    if v0 == zV or v1 == zV:
        #        this.parentWindow.statusBar.SetStatusText("Error: Don't use a zero vector")
        #    else:
        #        this.parentWindow.statusBar.SetStatusText("Error: The specified vectors are (too) parallel")
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

    def onExtraInfo(this, e):
        ExportOffDialog.extraInfo = this.extraInfoGui.GetValue()

    def getExtraInfo(this):
        return this.extraInfoGui.GetValue()

    def onCleanUp(this, e):
        ExportOffDialog.cleanUp = this.cleanUpGui.GetValue()
        if ExportOffDialog.cleanUp:
            this.floatMarginGui.Enable()
        else:
            this.floatMarginGui.Disable()

    def getCleanUp(this):
        return this.cleanUpGui.GetValue()

    def onPrecision(this, e):
        ExportOffDialog.precision = this.precisionGui.GetValue()

    def getPrecision(this):
        return this.precisionGui.GetValue()

    def onFloatMargin(this, e):
        ExportOffDialog.floatMargin = this.floatMarginGui.GetValue()

    def getFloatMargin(this):
        return this.floatMarginGui.GetValue()

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

    def onScaling(this, e):
        ExportPsDialog.scaling = this.scalingFactorGui.GetValue()

    def getScaling(this):
        return this.scalingFactorGui.GetValue()

    def onPrecision(this, e):
        ExportPsDialog.precision = this.precisionGui.GetValue()

    def getPrecision(this):
        return this.precisionGui.GetValue()

    def onFloatMargin(this, e):
        ExportPsDialog.floatMargin = this.floatMarginGui.GetValue()

    def getFloatMargin(this):
        return this.floatMarginGui.GetValue()

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
        scene_file = DefaultScene
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
        frame.readSceneFile(scene_file)
    app.MainLoop()

sys.stderr.write("Done\n")

if o_fd != None: o_fd.close()
