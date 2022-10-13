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

import logging
import wx
from OpenGL.GLU import *
from OpenGL.GL import *

from orbitit import Geom3D, geomtypes, heptagons, rgb

TITLE = 'Equilateral Heptagons from Kite'

class Shape(Geom3D.SimpleShape):
    def __init__(self):
        Geom3D.SimpleShape.__init__(self, [], [], name = "HeptaFromKite")
        self.topMin  = 0.0
        self.topMax  = 2.0
        self.tailMin = 0.0
        self.tailMax = 10.0
        self.sideMin = 0.1
        self.sideMax = 6.0
        self.initArrs()
        self.setKite(
                self.topMax / 2,
                self.tailMax / 2,
                self.sideMax / 2
            )
        self.setViewSettings(
            addFaces=True,
            useCylinderEs=False,
            useSphereVs=False,
            showKite=True,
            showHepta=True,
        )

    @staticmethod
    def glInit():
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

    def initArrs(self):
        self.colors = [rgb.red, rgb.yellow]
        self.kiteFs = [
                [0, 2, 1], [0, 3, 2]
            ]
        self.kiteColors = [0, 0]
        self.kiteEs = [
                0, 1, 1, 2, 2, 3, 3, 0
            ]
        self.kiteVsIndices = list(range(4))
        self.heptaFs = [
                [0, 6, 1],
                [1, 6, 5],
                [1, 5, 2],
                [2, 5, 4],
                [2, 4, 3],
            ]
        self.heptaColors = [1, 1, 1, 1, 1]
        self.heptaEs  = [
                0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0
            ]
        self.heptaVsIndices = list(range(3, 10))
        self.allNs = [
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

    def setV(self):
        Vt = [0, self.top, 0]
        Vb = [0, -self.tail, 0]
        Vl = [-self.side, 0, 0]
        Vr = [ self.side, 0, 0]
        tuple = heptagons.Kite2Hept(Vl, Vt, Vr, Vb)
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
        self.kiteVs = [
                geomtypes.Vec3([Vr[0], Vr[1], Vr[2]]),
                geomtypes.Vec3([Vb[0], Vb[1], Vb[2]]),
                geomtypes.Vec3([Vl[0], Vl[1], Vl[2]]),
                geomtypes.Vec3([Vt[0], Vt[1], Vt[2]])
           ]
        d = 1e-4
        self.heptaVs = [
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
            if self.showKite:
                Vs.extend(self.kiteVs)
            if self.showHepta:
                Vs.extend(self.heptaVs)
            self.setVertexProperties(Vs = Vs)
        except AttributeError: pass

    def setViewSettings(self,
            addFaces=None,
            useCylinderEs=None,
            useSphereVs=None,
            showKite=None,
            showHepta=None
        ):
        if addFaces != None:
            self.setFaceProperties(drawFaces = addFaces)
        if useCylinderEs != None:
            if useCylinderEs:
                radius = 0.05
            else:
                radius = 0.00
            self.setEdgeProperties(radius = radius, drawEdges = True)
        if useSphereVs != None:
            if useSphereVs:
                radius = 0.1
            else:
                radius = 0.00
            self.setVertexProperties(radius = radius)
        if showKite != None or showHepta != None:
            Fs = []
            Es = []
            Vs = []
            ColsI = []
            if showKite:
                Vs.extend(self.kiteVs)
                Fs.extend(self.kiteFs)
                Es.extend(self.kiteEs)
                ColsI.extend(self.kiteColors)
            if showHepta:
                if Vs != []:
                    lVs = len(Vs)
                    for face in self.heptaFs:
                        Fs.append([i + lVs for i in face])
                    Es.extend([i + lVs for i in self.heptaEs])
                    Vs.extend(self.heptaVs)
                    ColsI.extend(self.heptaColors)
                else:
                    Fs.extend(self.heptaFs)
                    Es.extend(self.heptaEs)
                    Vs.extend(self.heptaVs)
                    ColsI.extend(self.heptaColors)
            self.setVertexProperties(Vs = Vs)
            self.setEdgeProperties(Es = Es)
            self.setFaceProperties(Fs = Fs, colors = [self.colors[:], ColsI[:]])
            # save for setV:
            self.showKite  = showKite
            self.showHepta = showHepta

    def setTop(self, top):
        self.top  = top
        self.setV()

    def setTail(self, tail):
        self.tail  = tail
        self.setV()

    def setSide(self, side):
        self.side  = side
        self.setV()

    def setKite(self, top, tail, side):
        self.top  = top
        self.tail = tail
        self.side = side
        self.setV()

    def getStatusStr(self):
        floatFmt = '%02.2f'
        fmtStr   = 'Top = %s, Tail = %s, Side = %s' % (floatFmt, floatFmt, floatFmt)
        str      = fmtStr % (self.top, self.tail, self.side)
        return str

    # GUI PART

class CtrlWin(wx.Frame):
    def __init__(self, shape, canvas, *args, **kwargs):
        self.shape = shape
        self.canvas = canvas
        wx.Frame.__init__(self, *args, **kwargs)
        self.panel = wx.Panel(self, -1)
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(
                self.createControlsSizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        self.set_default_size((438, 312))
        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.mainSizer)
        self.Show(True)
        self.panel.Layout()

    def createControlsSizer(self):
        self.sideScale = 100
        self.topScale  = 100
        self.tailScale = 100

        self.shape.setViewSettings(showHepta=False, showKite=True)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # GUI for dynamic adjustment
        self.kiteSideAdjust = wx.Slider(
                self.panel,
                value = self.shape.side * self.sideScale,
                minValue = self.shape.sideMin * self.sideScale,
                maxValue = self.shape.sideMax * self.sideScale,
                style = wx.SL_HORIZONTAL
            )
        self.panel.Bind(wx.EVT_SLIDER, self.onSideAdjust, id = self.kiteSideAdjust.GetId())
        self.kiteSideBox = wx.StaticBox(self.panel, label = 'Kite Side')
        self.kiteSideSizer = wx.StaticBoxSizer(self.kiteSideBox, wx.HORIZONTAL)
        self.kiteSideSizer.Add(self.kiteSideAdjust, 1, wx.EXPAND)

        self.kiteTopAdjust = wx.Slider(
                self.panel,
                value = self.shape.top * self.sideScale,
                maxValue = self.shape.topMax * self.topScale,
                minValue = self.shape.topMin * self.topScale,
                style = wx.SL_VERTICAL
            )
        self.topRange = (self.shape.topMax - self.shape.topMin) * self.topScale
        self.panel.Bind(wx.EVT_SLIDER, self.onTopAdjust, id = self.kiteTopAdjust.GetId())
        self.kiteTopBox = wx.StaticBox(self.panel, label = 'Kite Top')
        self.kiteTopSizer = wx.StaticBoxSizer(self.kiteTopBox, wx.VERTICAL)
        self.kiteTopSizer.Add(self.kiteTopAdjust, 1, wx.EXPAND)
        self.kiteTailAdjust = wx.Slider(
                self.panel,
                value = self.shape.tail * self.sideScale,
                minValue = self.shape.tailMin * self.tailScale,
                maxValue = self.shape.tailMax * self.tailScale,
                style = wx.SL_VERTICAL
            )
        self.panel.Bind(wx.EVT_SLIDER, self.onTailAdjust, id = self.kiteTailAdjust.GetId())
        self.kiteTailBox = wx.StaticBox(self.panel, label = 'Kite Tail')
        self.kiteTailSizer = wx.StaticBoxSizer(self.kiteTailBox, wx.VERTICAL)
        self.kiteTailSizer.Add(self.kiteTailAdjust, 1, wx.EXPAND)

        # GUI for predefined positions
        self.prePosLst = [
                'None',
                'Concave I',
                'Concave II',
                'Regular'
            ]
        self.prePosSelect = wx.RadioBox(self.panel,
                label = 'Predefined Positions',
                style = wx.RA_VERTICAL,
                choices = self.prePosLst
            )
        self.setNoPrePos()
        self.panel.Bind(wx.EVT_RADIOBOX, self.onPrePos) #, id = self.prePosSelect.GetId())

        # GUI for general view settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        self.view_kite_gui = wx.CheckBox(self.panel, label = 'Show Kite')
        self.view_kite_gui.SetValue(self.shape.showKite)
        self.view_hept_gui = wx.CheckBox(self.panel, label = 'Show Heptagon')
        self.view_hept_gui.SetValue(self.shape.showHepta)
        self.panel.Bind(wx.EVT_CHECKBOX, self.on_view_settings_chk)
        self.view_opt_box = wx.StaticBox(self.panel, label = 'View Settings')
        self.view_opt_sizer = wx.StaticBoxSizer(self.view_opt_box, wx.VERTICAL)

        self.view_opt_sizer.Add(self.view_kite_gui, 1, wx.EXPAND)
        self.view_opt_sizer.Add(self.view_hept_gui, 1, wx.EXPAND)

        self.row_sizer = wx.BoxSizer(wx.VERTICAL)
        self.row_sizer.Add(self.prePosSelect, 1, wx.EXPAND)
        self.row_sizer.Add(self.view_opt_sizer, 1, wx.EXPAND)

        self.column_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.column_sizer.Add(self.kiteTopSizer, 1, wx.EXPAND)
        self.column_sizer.Add(self.kiteTailSizer, 1, wx.EXPAND)
        self.column_sizer.Add(self.row_sizer, 2, wx.EXPAND)

        mainSizer.Add(self.kiteSideSizer, 2, wx.EXPAND)
        mainSizer.Add(self.column_sizer, 10, wx.EXPAND)

        return mainSizer

    def setNoPrePos(self):
        sel = self.prePosSelect.SetSelection(0)
        self.pre_pos_selected = False

    def onSideAdjust(self, event):
        self.setNoPrePos()
        self.shape.setSide(float(self.kiteSideAdjust.GetValue()) / self.sideScale)
        self.canvas.paint()
        try:
            self.statusBar.SetStatusText(self.shape.getStatusStr())
        except AttributeError: pass
        event.Skip()

    def onTopAdjust(self, event):
        self.setNoPrePos()
        self.shape.setTop(float(self.topRange - self.kiteTopAdjust.GetValue()) / self.topScale)
        self.canvas.paint()
        try:
            self.statusBar.SetStatusText(self.shape.getStatusStr())
        except AttributeError: pass
        event.Skip()

    def onTailAdjust(self, event):
        self.setNoPrePos()
        self.shape.setTail(float(self.kiteTailAdjust.GetValue()) / self.tailScale)
        self.canvas.paint()
        try:
            self.statusBar.SetStatusText(self.shape.getStatusStr())
        except AttributeError: pass
        event.Skip()

    def onPrePos(self, event = None):
        sel = self.prePosSelect.GetSelection()
        # if switching from 'None' to a predefined position:
        if not self.pre_pos_selected and (sel != 0):
            self.topSav = self.shape.top
            self.tailSav = self.shape.tail
            self.sideSav = self.shape.side
            self.pre_pos_selected = True
        # TODO: id user selects prepos and then starts sliding, then the
        # selection should become None again.
        selStr = self.prePosLst[sel]
        if selStr == 'None':
            top  = self.topSav
            tail = self.tailSav
            side = self.sideSav
            self.pre_pos_selected = False
        elif selStr == 'Concave I':
            top  =  0.25
            tail = 10.0
            side =  1.6
        elif selStr == 'Concave II':
            top  = 2.0
            tail = 0.6
            side = 1.6
        elif selStr == 'Regular':
            top  = 2*heptagons.RhoH
            tail = top * (2 * heptagons.Rho - 1)
            side = 1 + heptagons.Sigma
        else:
            logging.info("onPrePos: oops, default case")
            top  = 0.1
            tail = 0.1
            side = 0.1
        self.shape.setKite(top, tail, side)
        self.canvas.paint()
        self.kiteTopAdjust.SetValue(self.topRange - top * self.topScale)
        self.kiteTailAdjust.SetValue(tail * self.tailScale)
        self.kiteSideAdjust.SetValue(side * self.sideScale)
        try:
            self.statusBar.SetStatusText(self.shape.getStatusStr())
        except AttributeError: pass

    def on_view_settings_chk(self, event):
        showKite = self.view_kite_gui.IsChecked()
        showHepta = self.view_hept_gui.IsChecked()
        self.shape.setViewSettings(
            showKite=showKite,
            showHepta=showHepta
        )
        self.canvas.paint()

    # move to general class
    def set_default_size(self, size):
        self.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        self.SetSize(size)

class Scene():
    def __init__(self, parent, canvas):
        self.shape = Shape()
        self.ctrlWin = CtrlWin(self.shape, canvas, parent, wx.ID_ANY, TITLE)

    def close(self):
        try:
            self.ctrlWin.Close(True)
        except RuntimeError:
            # The user probably closed the window already
            pass
