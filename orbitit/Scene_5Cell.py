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
#

import wx
import math
from OpenGL.GL import glBlendFunc, glEnable, GL_SRC_ALPHA, GL_BLEND, GL_ONE_MINUS_SRC_ALPHA

from orbitit import geom_3d, Geom4D, rgb

TITLE = '5-Cell'

l = 2.0
V2 = math.sqrt(2)
V3 = math.sqrt(3)
V5 = math.sqrt(5)
V6 = V2*V3
V10= V2*V5

vs = [

#        [ -l, -l/V3,   -l/V6, -l/V10 ],  #  0
#        [  l, -l/V3,   -l/V6, -l/V10 ],  #  1
#        [  0,  2*l/V3, -l/V6, -l/V10 ],  #  2
#        [  0,  0,     3*l/V6, -l/V10 ],  #  3
#        [  0,  0,       0,   4*l/V10 ]   #  4
        [ l,  l,  l,  0],
        [-l, -l,  l,  0],
        [-l,  l, -l,  0],
        [ l, -l, -l,  0],
        [ 0,  0,  0, 2*l*V2],
#        [ l,  l,  l,  l],
#        [-l, -l, -l,  l],
#        [-l, -l,  l, -l],
#        [-l,  l, -l, -l],
#        [ l, -l, -l, -l]
    ]

Fs_0 = [  #
        [
            [0, 1, 2], [0, 1, 3], [1, 2, 3], [2, 0, 3]
        ],
        [
            [0, 1, 2], [0, 1, 4],  [1, 2, 4],  [2, 0, 4]
        ],
        [
            [0, 1, 3], [0, 1, 4], [1, 3, 4], [3, 0, 4]
        ],
        [
            [1, 2, 3], [1, 2, 4], [2, 3, 4], [3, 1, 4]
        ],
        [
            [2, 0, 3], [2, 0, 4], [0, 3, 4], [3, 2, 4]
        ],
    ]

Cols_0 = [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
]

Col0  = rgb.orange[:]
Col0.append(0.2)
Col2  = rgb.springGreen[:]
Col2.append(0.2)
Col1  = rgb.sienna[:]
Col1.append(0.4)

Cols     = [Col0, Col1, Col2]

ES = [
        0, 1, 0, 2, 0, 3, 0, 4,
        1, 2, 1, 3, 1, 4,
        2, 3, 2, 4,
        3, 4
    ]

Cells = [Fs_0]
CellGroups = ['Cells']
ColGroups  = [Cols_0]

class Shape(Geom4D.SimpleShape):
    def __init__(this):
        Cs = []
        cols = []
        assert len(Cells) == len(ColGroups)
        for i in range(len(Cells)):
            Cs.extend(Cells[i])
            cols.extend(ColGroups[i])
        Geom4D.SimpleShape.__init__(this,
            vs, Cs=Cs, es=ES, ns=[],
            colors=(Cols, cols),
            name=TITLE
        )
        this.showGroup = [True for i in range(len(Cells))]
        this.showWhichCells = []
        for i in range(len(Cells)):
            this.showWhichCells.append([True for j in range(len(Cells[i]))])
        # On default, don't draw the outer cell:
        this.showWhichCells[-1][0] = False
        this.showFs()
        this.setProjectionProperties(wCameraDistance = 3.76, w_prj_vol = 0.25)

    def setShowGroup(this, groupId, show = True):
        this.showGroup[groupId] = show
        this.showFs()

    def setShowCellsOfGroup(this, groupId, cellList):
        this.showWhichCells[groupId] = cellList
        if this.showGroup[groupId]:
            this.showFs()

    def showFs(this):
        Cs = []
        colIds = []
        for i in range(len(Cells)):
            if this.showGroup[i]:
                for j in range(len(this.showWhichCells[i])):
                    if this.showWhichCells[i][j]:
                        Cs.append(Cells[i][j])
                        colIds.append(ColGroups[i][j])
                    else:
                        Cs.append([])
                        colIds.append([])
        this.setCellProperties(Cs = Cs)
        this.set_face_props(colors = (Cols, colIds))

    def gl_init(self):
        super().gl_init()
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

class CtrlWin(wx.Frame):
    def __init__(this, shape, canvas, *args, **kwargs):
        this.shape = shape
        this.canvas = canvas
        kwargs['title'] = TITLE
        wx.Frame.__init__(this, *args, **kwargs)
        this.panel = wx.Panel(this, -1)
        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
        this.mainSizer.Add(
                this.create_control_sizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.set_default_size((237, 590))
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()

    def create_control_sizer(this):
        ctrlSizer = wx.BoxSizer(wx.VERTICAL)

        str = 'cell %d'
        lenR = len(str) + 2
        lenL = 0
        for cellGroup in CellGroups:
            lenL = max(lenL, len(cellGroup))
        this.showGui = []
        showFacesSizer = wx.StaticBoxSizer(
            wx.StaticBox(this.panel, label = 'View Settings'),
            wx.VERTICAL
        )
        L = 0
        for i in range(len(Cells)):
            showWhich = this.shape.showWhichCells[i]
            l = len(showWhich)
            cellList = [ str % j for j in range(l)]
            this.showGui.append(wx.CheckBox(this.panel, label = CellGroups[i]))
            this.showGui[-1].SetValue(this.shape.showGroup[i])
            this.showGui[-1].Bind(wx.EVT_CHECKBOX,
                this.onShowGroup,
                id = this.showGui[-1].GetId()
            )
            this.showGui.append(wx.CheckListBox(this.panel, choices = cellList))
            this.showGui[-1].Bind(wx.EVT_CHECKLISTBOX,
                this.onShowCells,
                id = this.showGui[-1].GetId()
            )
            for j in range(l):
                this.showGui[-1].Check(j ,showWhich[j])
            showCellsSizer = wx.BoxSizer(wx.HORIZONTAL)
            showCellsSizer.Add(this.showGui[-2], lenL, wx.EXPAND)
            showCellsSizer.Add(this.showGui[-1], lenR, wx.EXPAND)
            showFacesSizer.Add(showCellsSizer, l, wx.EXPAND)
            L += l

        ctrlSizer.Add(showFacesSizer, L, wx.EXPAND)
        return ctrlSizer

    def onShowGroup(this, event):
        for i in range(0, len(this.showGui), 2):
            if this.showGui[i].GetId() == event.GetId():
                this.shape.setShowGroup(i//2, this.showGui[i].IsChecked())
        this.canvas.paint()

    def onShowCells(this, event):
        for i in range(1, len(this.showGui), 2):
            if this.showGui[i].GetId() == event.GetId():
                this.showGui[i].SetSelection(event.GetSelection())
                groupId = i//2 # actually it should be (i-1)/2 but rounding fixes this
                list = [ this.showGui[i].IsChecked(j) for j in range(len(Cells[groupId])) ]
                this.shape.setShowCellsOfGroup(groupId, list)
        this.canvas.paint()

    # move to general class
    def set_default_size(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

class Scene(geom_3d.Scene):
    def __init__(this, parent, canvas):
        geom_3d.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
