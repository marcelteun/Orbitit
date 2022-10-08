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
from OpenGL.GL import glBlendFunc, glEnable, GL_SRC_ALPHA, GL_BLEND, GL_ONE_MINUS_SRC_ALPHA

from orbitit import Geom3D, Geom4D, rgb

TITLE = 'Tesseract'

l = 2.0

Vs = [
        [ l,  l,  l,  l],     #  0
        [-l,  l,  l,  l],     #  1
        [ l, -l,  l,  l],     #  2
        [-l, -l,  l,  l],     #  3

        [ l,  l, -l,  l],     #  4
        [-l,  l, -l,  l],     #  5
        [ l, -l, -l,  l],     #  6
        [-l, -l, -l,  l],     #  7

        [ l,  l,  l, -l],     #  8
        [-l,  l,  l, -l],     #  9
        [ l, -l,  l, -l],     # 10
        [-l, -l,  l, -l],     # 11

        [ l,  l, -l, -l],     # 12
        [-l,  l, -l, -l],     # 13
        [ l, -l, -l, -l],     # 14
        [-l, -l, -l, -l],     # 15

    ]

Es = [
        0, 1, 1, 3, 3, 2, 2, 0,
        0, 4, 1, 5, 3, 7, 2, 6,
        4, 5, 5, 7, 7, 6, 6, 4,
        0+8, 1+8, 1+8, 3+8, 3+8, 2+8, 2+8, 0+8,
        0+8, 4+8, 1+8, 5+8, 3+8, 7+8, 2+8, 6+8,
        4+8, 5+8, 5+8, 7+8, 7+8, 6+8, 6+8, 4+8,
        1, 1+8, 5, 5+8, 0, 0+8, 4, 4+8,
	2, 10, 3, 11, 6, 14, 7, 15,
    ]

Fs_0 = [
    [
        [0, 1, 3, 2], [4, 5, 7, 6],
        [0, 1, 5, 4], [3, 2, 6, 7],
        [1, 3, 7, 5], [2, 0, 4, 6]
    ], [
        [0+8, 1+8, 3+8, 2+8], [4+8, 5+8, 7+8, 6+8],
        [0+8, 1+8, 5+8, 4+8], [3+8, 2+8, 6+8, 7+8],
        [1+8, 3+8, 7+8, 5+8], [2+8, 0+8, 4+8, 6+8]
    ]
]
Cols_0 = [
    [0, 0, 1, 1, 2, 2] for cell in Fs_0
]

Fs_1 = [
    [
        [0, 1, 1+8, 0+8], [4, 5, 5+8, 4+8],
        [0, 1, 5, 4], [0+8, 1+8, 5+8, 4+8],
        [1, 1+8, 5+8, 5], [0+8, 0, 4, 4+8],
    ], [
        [3, 2, 2+8, 3+8], [7, 6, 6+8, 7+8],
        [3, 2, 6, 7], [2+8, 3+8, 7+8, 6+8],
        [2, 2+8, 6+8, 6], [3+8, 3, 7, 7+8]
    ]
]
Cols_1 = [
    [3, 3, 1, 1, 4, 4] for cell in Fs_1
]

Fs_2 = [
    [
        [1, 3, 3+8, 1+8], [5, 7, 7+8, 5+8],
        [1, 3, 7, 5], [3+8, 1+8, 5+8, 7+8],
        [3, 3+8, 7+8, 7], [1+8, 1, 5, 5+8]
    ], [
        [2, 0, 0+8, 2+8], [6, 4, 4+8, 6+8],
        [2, 0, 4, 6], [0+8, 2+8, 6+8, 4+8],
        [0, 0+8, 4+8, 4], [2+8, 2, 6, 6+8]
    ]
]
Cols_2 = [
    [5, 5, 2, 2, 4, 4] for cell in Fs_2
]

Fs_3 = [
    [
        [0, 1, 3, 2], [0+8, 1+8, 3+8, 2+8],
        [0, 1, 1+8, 0+8], [3, 2, 2+8, 3+8],
        [1, 3, 3+8, 1+8], [2, 0, 0+8, 2+8]
    ], [
        [4, 5, 7, 6], [4+8, 5+8, 7+8, 6+8],
        [4, 5, 5+8, 4+8], [7, 6, 6+8, 7+8],
        [5, 7, 7+8, 5+8], [6, 4, 4+8, 6+8]
    ]
]
Cols_3 = [
    [0, 0, 3, 3, 5, 5] for cell in Fs_2
]

Cells = [Fs_0, Fs_1, Fs_2, Fs_3]
CellGroups = ['Cube Pair 0', 'Cube Pair 1', 'Cube Pair 2', 'Cube Pair 3']
ColGroups  = [Cols_0, Cols_1, Cols_2, Cols_3]

Col_0    = rgb.green[:]
Col_0.append(0.2)
Col_1    = rgb.orange[:]
Col_1.append(0.2)
Col_2   = rgb.red[:]
Col_2.append(0.2)
Col_3   = Col_2[:]
Col_3.append(0.2)
Col_4   = Col_0[:]
Col_4.append(0.2)
Col_5   = Col_1[:]
Cols     = [Col_0, Col_1, Col_2, Col_3, Col_4, Col_5]

class Shape(Geom4D.SimpleShape):
    def __init__(this):
        Cs = []
        cols = []
        assert len(Cells) == len(ColGroups)
        for i in range(len(Cells)):
            Cs.extend(Cells[i])
            cols.extend(ColGroups[i])
        Geom4D.SimpleShape.__init__(this,
            Vs, Cs = Cs, Es = Es, Ns = [],
            colors = (Cols, cols),
            name = TITLE
        )
        this.showGroup = [True for i in range(len(Cells))]
        this.showWhichCells = []
        for i in range(len(Cells)):
            this.showWhichCells.append([True for j in range(len(Cells[i]))])
        # On default, don't draw the outer cell:
        this.showWhichCells[0][0] = False
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
        this.setFaceProperties(colors = (Cols, colIds))

    def glInit(this):
        Geom4D.SimpleShape.glInit(this)
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
                this.createControlsSizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.set_default_size((237, 590))
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()

    def createControlsSizer(this):
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

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
