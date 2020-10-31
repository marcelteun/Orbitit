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
#--------------------------------------------------------------------

import wx
import math
import rgb
import Heptagons
import Geom3D
import geomtypes
import Scenes3D
from OpenGL.GLU import *
from OpenGL.GL import *

TITLE = 'Equilateral Heptagons from Kite'

class Shape(Geom3D.SimpleShape):
    def __init__(this):
        Geom3D.SimpleShape.__init__(this, [], [], name = "HeptaFromKite")
        this.topMin  = 0.0
        this.topMax  = 2.0
        this.tailMin = 0.0
        this.tailMax = 10.0
        this.sideMin = 0.1
        this.sideMax = 6.0
        this.initArrs()
        this.setKite(
                this.topMax / 2,
                this.tailMax / 2,
                this.sideMax / 2
            )
        this.setViewSettings(
            addFaces      = True,
            useCylinderEs = False,
            useSphereVs   = False,
            showKite      = True,
            showHepta     = True
        )

    def glInit(this):
        lightPosition = [-5., 5., 200., 0.]
        lightAmbient  = [0.7, 0.7, 0.7, 1.]
        #lightDiffuse  = [1., 1., 1., 1.]
        #lightSpecular = [0., 0., 0., 1.]
        #materialSpec  = [0., 0., 0., 0.]
        glLightfv(GL_LIGHT0, GL_POSITION, lightPosition)
        glLightfv(GL_LIGHT0, GL_AMBIENT, lightAmbient)
        #glLightfv(GL_LIGHT0, GL_DIFFUSE, lightDiffuse)
        #glLightfv(GL_LIGHT0, GL_SPECULAR, lightSpecular)
        #glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, materialSpec)
        glEnable(GL_LIGHT0)
        #glDisable(GL_DEPTH_TEST)

    def initArrs(this):
        this.colors = [rgb.red, rgb.yellow]
        this.kiteFs = [
                [0, 2, 1], [0, 3, 2]
            ]
        this.kiteColors = [0, 0]
        this.kiteEs = [
                0, 1, 1, 2, 2, 3, 3, 0
            ]
        this.kiteVsIndices = list(range(4))
        this.heptaFs = [
                [0, 6, 1],
                [1, 6, 5],
                [1, 5, 2],
                [2, 5, 4],
                [2, 4, 3],
            ]
        this.heptaColors = [1, 1, 1, 1, 1]
        this.heptaEs  = [
                0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0
            ]
        this.heptaVsIndices = list(range(3, 10))
        this.allNs = [
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
            ]

    def setV(this):
        Vt = [0, this.top, 0]
        Vb = [0, -this.tail, 0]
        Vl = [-this.side, 0, 0]
        Vr = [ this.side, 0, 0]
        tuple = Heptagons.Kite2Hept(Vl, Vt, Vr, Vb)
        if tuple == None: return
        h0, h1, h2, h3, h4, h5, h6 = tuple[0]

                #
                #              3 0'
                #
                #
                #        6'            1'
                #
                #
                #   2           +           0
                #
                #      5'                2'
                #
                #
                #
                #          4'        3'
                #
                #
                #               1
                #
        this.kiteVs = [
                geomtypes.Vec3([Vr[0], Vr[1], Vr[2]]),
                geomtypes.Vec3([Vb[0], Vb[1], Vb[2]]),
                geomtypes.Vec3([Vl[0], Vl[1], Vl[2]]),
                geomtypes.Vec3([Vt[0], Vt[1], Vt[2]])
           ]
        d = 1e-4
        this.heptaVs = [
                geomtypes.Vec3([Vt[0], Vt[1], Vt[2] + d]),
                geomtypes.Vec3([h1[0], h1[1], h1[2] + d]),
                geomtypes.Vec3([h2[0], h2[1], h2[2] + d]),
                geomtypes.Vec3([h3[0], h3[1], h3[2] + d]),
                geomtypes.Vec3([h4[0], h4[1], h4[2] + d]),
                geomtypes.Vec3([h5[0], h5[1], h5[2] + d]),
                geomtypes.Vec3([h6[0], h6[1], h6[2] + d])
            ]
        # try to set the vertices array.
        # the failure occurs at init since showKite and showHepta don't exist
        try:
            Vs = []
            print('this.showKite', this.showKite, 'this.showHepta', this.showHepta)
            if this.showKite:
                Vs.extend(this.kiteVs)
            if this.showHepta:
                Vs.extend(this.heptaVs)
            for v in Vs: print(v)
            print('===============')
            this.setVertexProperties(Vs = Vs)
        except AttributeError: pass

    def setViewSettings(this,
            addFaces      = None,
            useCylinderEs = None,
            useSphereVs   = None,
            showKite      = None,
            showHepta     = None
        ):
        if addFaces != None:
            this.setFaceProperties(drawFaces = addFaces)
        if useCylinderEs != None:
            if useCylinderEs:
                radius = 0.05
            else:
                radius = 0.00
            this.setEdgeProperties(radius = radius, drawEdges = True)
        if useSphereVs != None:
            if useSphereVs:
                radius = 0.1
            else:
                radius = 0.00
            this.setVertexProperties(radius = radius)
        if showKite != None or showHepta != None:
            Fs = []
            Es = []
            Vs = []
            ColsI = []
            if showKite:
                Vs.extend(this.kiteVs)
                Fs.extend(this.kiteFs)
                Es.extend(this.kiteEs)
                ColsI.extend(this.kiteColors)
            if showHepta:
                if Vs != []:
                    lVs = len(Vs)
                    for face in this.heptaFs:
                        Fs.append([i + lVs for i in face])
                    Es.extend([i + lVs for i in this.heptaEs])
                    Vs.extend(this.heptaVs)
                    ColsI.extend(this.heptaColors)
                else:
                    Fs.extend(this.heptaFs)
                    Es.extend(this.heptaEs)
                    Vs.extend(this.heptaVs)
                    ColsI.extend(this.heptaColors)
            this.setVertexProperties(Vs = Vs)
            this.setEdgeProperties(Es = Es)
            this.setFaceProperties(Fs = Fs, colors = [this.colors[:], ColsI[:]])
            # save for setV:
            this.showKite  = showKite
            this.showHepta = showHepta

    def setTop(this, top):
        this.top  = top
        this.setV()

    def setTail(this, tail):
        this.tail  = tail
        this.setV()

    def setSide(this, side):
        this.side  = side
        this.setV()

    def setKite(this, top, tail, side):
        this.top  = top
        this.tail = tail
        this.side = side
        this.setV()

    def getStatusStr(this):
        floatFmt = '%02.2f'
        fmtStr   = 'Top = %s, Tail = %s, Side = %s' % (floatFmt, floatFmt, floatFmt)
        str      = fmtStr % (this.top, this.tail, this.side)
        return str

    # GUI PART

class CtrlWin(wx.Frame):
    def __init__(this, shape, canvas, *args, **kwargs):
        this.shape = shape
        this.canvas = canvas
        wx.Frame.__init__(this, *args, **kwargs)
        this.panel = wx.Panel(this, -1)
        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
        this.mainSizer.Add(
                this.createControlsSizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.setDefaultSize((438, 312))
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()

    def createControlsSizer(this):
        this.sideScale = 100
        this.topScale  = 100
        this.tailScale = 100

        this.shape.setViewSettings(showHepta = False, showKite  = True)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # GUI for dynamic adjustment
        this.kiteSideAdjust = wx.Slider(
                this.panel,
                value = this.shape.side * this.sideScale,
                minValue = this.shape.sideMin * this.sideScale,
                maxValue = this.shape.sideMax * this.sideScale,
                style = wx.SL_HORIZONTAL
            )
        this.panel.Bind(wx.EVT_SLIDER, this.onSideAdjust, id = this.kiteSideAdjust.GetId())
        this.kiteSideBox = wx.StaticBox(this.panel, label = 'Kite Side')
        this.kiteSideSizer = wx.StaticBoxSizer(this.kiteSideBox, wx.HORIZONTAL)
        this.kiteSideSizer.Add(this.kiteSideAdjust, 1, wx.EXPAND)

        this.kiteTopAdjust = wx.Slider(
                this.panel,
                value = this.shape.top * this.sideScale,
                maxValue = this.shape.topMax * this.topScale,
                minValue = this.shape.topMin * this.topScale,
                style = wx.SL_VERTICAL
            )
        this.topRange = (this.shape.topMax - this.shape.topMin) * this.topScale
        this.panel.Bind(wx.EVT_SLIDER, this.onTopAdjust, id = this.kiteTopAdjust.GetId())
        this.kiteTopBox = wx.StaticBox(this.panel, label = 'Kite Top')
        this.kiteTopSizer = wx.StaticBoxSizer(this.kiteTopBox, wx.VERTICAL)
        this.kiteTopSizer.Add(this.kiteTopAdjust, 1, wx.EXPAND)
        this.kiteTailAdjust = wx.Slider(
                this.panel,
                value = this.shape.tail * this.sideScale,
                minValue = this.shape.tailMin * this.tailScale,
                maxValue = this.shape.tailMax * this.tailScale,
                style = wx.SL_VERTICAL
            )
        this.panel.Bind(wx.EVT_SLIDER, this.onTailAdjust, id = this.kiteTailAdjust.GetId())
        this.kiteTailBox = wx.StaticBox(this.panel, label = 'Kite Tail')
        this.kiteTailSizer = wx.StaticBoxSizer(this.kiteTailBox, wx.VERTICAL)
        this.kiteTailSizer.Add(this.kiteTailAdjust, 1, wx.EXPAND)

        # GUI for predefined positions
        this.prePosLst = [
                'None',
                'Concave I',
                'Concave II',
                'Regular'
            ]
        this.prePosSelect = wx.RadioBox(this.panel,
                label = 'Predefined Positions',
                style = wx.RA_VERTICAL,
                choices = this.prePosLst
            )
        this.setNoPrePos()
        this.panel.Bind(wx.EVT_RADIOBOX, this.onPrePos) #, id = this.prePosSelect.GetId())

        # GUI for general view settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        this.showKiteChk = wx.CheckBox(this.panel, label = 'Show Kite')
        this.showKiteChk.SetValue(this.shape.showKite)
        this.showHeptaChk = wx.CheckBox(this.panel, label = 'Show Heptagon')
        this.showHeptaChk.SetValue(this.shape.showHepta)
        this.panel.Bind(wx.EVT_CHECKBOX, this.onViewSettingsChk)
        this.viewSettingsBox = wx.StaticBox(this.panel, label = 'View Settings')
        this.viewSettingsSizer = wx.StaticBoxSizer(this.viewSettingsBox, wx.VERTICAL)

        this.viewSettingsSizer.Add(this.showKiteChk, 1, wx.EXPAND)
        this.viewSettingsSizer.Add(this.showHeptaChk, 1, wx.EXPAND)

        this.rowSubSizer = wx.BoxSizer(wx.VERTICAL)
        this.rowSubSizer.Add(this.prePosSelect, 1, wx.EXPAND)
        this.rowSubSizer.Add(this.viewSettingsSizer, 1, wx.EXPAND)

        this.columnSubSizer = wx.BoxSizer(wx.HORIZONTAL)
        this.columnSubSizer.Add(this.kiteTopSizer, 1, wx.EXPAND)
        this.columnSubSizer.Add(this.kiteTailSizer, 1, wx.EXPAND)
        this.columnSubSizer.Add(this.rowSubSizer, 2, wx.EXPAND)

        mainSizer.Add(this.kiteSideSizer, 2, wx.EXPAND)
        mainSizer.Add(this.columnSubSizer, 10, wx.EXPAND)

        return mainSizer

    def setNoPrePos(this):
        sel = this.prePosSelect.SetSelection(0)
        this.prePosSelected = False

    def onSideAdjust(this, event):
        #print 'size =', this.dynDlg.GetClientSize()
        this.setNoPrePos()
        this.shape.setSide(float(this.kiteSideAdjust.GetValue()) / this.sideScale)
        this.canvas.paint()
        try:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        except AttributeError: pass
        event.Skip()

    def onTopAdjust(this, event):
        this.setNoPrePos()
        this.shape.setTop(float(this.topRange - this.kiteTopAdjust.GetValue()) / this.topScale)
        this.canvas.paint()
        try:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        except AttributeError: pass
        event.Skip()

    def onTailAdjust(this, event):
        this.setNoPrePos()
        this.shape.setTail(float(this.kiteTailAdjust.GetValue()) / this.tailScale)
        this.canvas.paint()
        try:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        except AttributeError: pass
        event.Skip()

    def onPrePos(this, event = None):
        #print 'onPrePos'
        sel = this.prePosSelect.GetSelection()
        # if switching from 'None' to a predefined position:
        if not this.prePosSelected and (sel != 0):
            this.topSav = this.shape.top
            this.tailSav = this.shape.tail
            this.sideSav = this.shape.side
            #print this.topSav, this.tailSav, this.sideSav
            this.prePosSelected = True
        # TODO: id user selects prepos and then starts sliding, then the
        # selection should become None again.
        selStr = this.prePosLst[sel]
        if selStr == 'None':
            top  = this.topSav
            tail = this.tailSav
            side = this.sideSav
            #print this.topSav, this.tailSav, this.sideSav
            this.prePosSelected = False
        elif selStr == 'Concave I':
            top  =  0.25
            tail = 10.0
            side =  1.6
        elif selStr == 'Concave II':
            top  = 2.0
            tail = 0.6
            side = 1.6
        elif selStr == 'Regular':
            top  = 2*Heptagons.RhoH
            tail = top * (2 * Heptagons.Rho - 1)
            side = 1 + Heptagons.Sigma
        else:
            print('onPrePos: oops, default case')
            top  = 0.1
            tail = 0.1
            side = 0.1
        this.shape.setKite(top, tail, side)
        this.canvas.paint()
        this.kiteTopAdjust.SetValue(this.topRange - top * this.topScale)
        this.kiteTailAdjust.SetValue(tail * this.tailScale)
        this.kiteSideAdjust.SetValue(side * this.sideScale)
        try:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        except AttributeError: pass

    def onViewSettingsChk(this, event):
        showKite      = this.showKiteChk.IsChecked()
        showHepta     = this.showHeptaChk.IsChecked()
        this.shape.setViewSettings(
                showKite      = showKite,
                showHepta     = showHepta
            )
        this.canvas.paint()

    # move to general class
    def setDefaultSize(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

class Scene():
    def __init__(this, parent, canvas):
        this.shape = Shape()
        this.ctrlWin = CtrlWin(this.shape, canvas, parent, wx.ID_ANY, TITLE)

    def close(this):
        try:
            this.ctrlWin.Close(True)
        except wx._core.PyDeadObjectError:
            # The user closed the window already
            pass
