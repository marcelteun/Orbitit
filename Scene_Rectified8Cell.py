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
#-------------------------------------------------------------------

import wx
import math
import rgb
import Geom3D
import Geom4D
import Scenes3D
from OpenGL.GL import *

TITLE = 'Rectified Tesseract'

l = 2.0

Vs = [
        [l, l, l, 0],     #  0
        [l, l, -l, 0],    #  1
        [l, -l, l, 0],    #  2
        [l, -l, -l, 0],   #  3
        [-l, l, l, 0],    #  4
        [-l, l, -l, 0],   #  5
        [-l, -l, l, 0],   #  6
        [-l, -l, -l, 0],  #  7

        [l, l, 0, l],     #  8
        [l, l, 0, -l],    #  9
        [l, -l, 0, l],    # 10
        [l, -l, 0, -l],   # 11
        [-l, l, 0, l],    # 12
        [-l, l, 0, -l],   # 13
        [-l, -l, 0, l],   # 14
        [-l, -l, 0, -l],  # 15

        [l, 0, l, l],     # 16
        [l, 0, l, -l],    # 17
        [l, 0, -l, l],    # 18
        [l, 0, -l, -l],   # 19
        [-l, 0, l, l],    # 20
        [-l, 0, l, -l],   # 21
        [-l, 0, -l, l],   # 22
        [-l, 0, -l, -l],  # 23

        [0, l, l, l],     # 24
        [0, l, l, -l],    # 25
        [0, l, -l, l],    # 26
        [0, l, -l, -l],   # 27
        [0, -l, l, l],    # 28
        [0, -l, l, -l],   # 29
        [0, -l, -l, l],   # 30
        [0, -l, -l, -l],  # 31
    ]

Es = [
        24, 16, 16,  8,  8, 24,
        24,  0, 16,  0,  8,  0,
        24, 12, 12, 20, 20, 24,
        24,  4, 12,  4, 20,  4,
        20, 14, 14, 28, 28, 20,
        20,  6, 14,  6, 28,  6,
        28, 10, 10, 16, 16, 28,
        28,  2, 10,  2, 16,  2,

        26,  8,  8, 18, 18, 26,
        26,  1,  8,  1, 18,  1,
        26, 22, 22, 12, 12, 26,
        26,  5, 22,  5, 12,  5,
        22, 30, 30, 14, 14, 22,
        22,  7, 30,  7, 14,  7,
        30, 18, 18, 10, 10, 30,
        30,  3, 18,  3, 10,  3,

        25, 17, 17,  9,  9, 25,
        25,  0, 17,  0,  9,  0,
        25, 13, 13, 21, 21, 25,
        25,  4, 13,  4, 21,  4,
        21, 15, 15, 29, 29, 21,
        21,  6, 15,  6, 29,  6,
        29, 11, 11, 17, 17, 29,
        29,  2, 11,  2, 17,  2,

        27,  9,  9, 19, 19, 27,
        27,  1,  9,  1, 19,  1,
        27, 23, 23, 13, 13, 27,
        27,  5, 23,  5, 13,  5,
        23, 31, 31, 15, 15, 23,
        23,  7, 31,  7, 15,  7,
        31, 19, 19, 11, 11, 31,
        31,  3, 19,  3, 11,  3,

    ]

Tetrahedra0_Fs = [
    [
        [24, 16, 8], [24, 0, 16], [16, 0, 8], [8, 0, 24],
    ], [
        [20, 14, 28], [20, 6, 14], [14, 6, 28], [28, 6, 20],
    ], [
        [26, 22, 12], [26, 5, 22], [22, 5, 12], [12, 5, 26],
    ], [
        [30, 18, 10], [30, 3, 18], [18, 3, 10], [10, 3, 30],
    ], [
        [25, 13, 21], [25, 4, 13], [13, 4, 21], [21, 4, 25],
    ], [
        [29, 11, 17], [29, 2, 11], [11, 2, 17], [17, 2, 29],
    ], [
        [27, 9, 19], [27, 1, 9], [9, 1, 19], [19, 1, 27],
    ], [
        [23, 31, 15], [23, 7, 31], [31, 7, 15], [15, 7, 23],
    ]
]

Tetrahedra0_Cols = [
    [0, 0, 0, 0] for cell in Tetrahedra0_Fs
]

Tetrahedra1_Fs = [
    [
        [24, 12, 20], [24, 4, 12], [12, 4, 20], [20, 4, 24],
    ], [
        [28, 10, 16], [28, 2, 10], [10, 2, 16], [16, 2, 28],
    ], [
        [26, 8, 18], [26, 1, 8], [8, 1, 18], [18, 1, 26],
    ], [
        [22, 30, 14], [22, 7, 30], [30, 7, 14], [14, 7, 22],
    ], [
        [25, 17, 9], [25, 0, 17], [17, 0, 9], [9, 0, 25],
    ], [
        [21, 15, 29], [21, 6, 15], [15, 6, 29], [29, 6, 21],
    ], [
        [27, 23, 13], [27, 5, 23], [23, 5, 13], [13, 5, 27],
    ], [
        [31, 19, 11], [31, 3, 19], [19, 3, 11], [11, 3, 31],
    ]
]
Tetrahedra1_Cols = [
    [1, 1, 1, 1] for cell in Tetrahedra1_Fs
]

Cubos_Fs = [
        [
            # Inner cubo
            [25, 21, 29, 17], [27, 19, 31, 23],
            [11, 19, 9, 17], [21, 13, 23, 15],
            [25, 9, 27, 13], [29, 15, 31, 11],
            [29, 11, 17], [25, 17, 9], [25, 13, 21], [21, 15, 29],
            [27, 9, 19], [27, 23, 13], [23, 31, 15], [31, 19, 11],
        ], [
            [24, 20, 28, 16], [25, 21, 29, 17],
            [24, 0, 25, 4], [28, 6, 29, 2],
            [16, 2, 17, 0], [20, 4, 21, 6],
            [24, 0, 16], [20, 4, 24], [28, 6, 20], [16, 2, 28],
            [17, 2, 29], [25, 0, 17], [21, 4, 25], [29, 6, 21],
        ], [
            [10, 18, 8, 16], [11, 19, 9, 17],
            [10, 2, 11, 3], [8, 0, 9, 1],
            [16, 2, 17, 0], [18, 3, 19, 1],
            [16, 0, 8], [8, 1, 18], [18, 3, 10], [10, 2, 16],
            [11, 2, 17], [17, 0, 9], [9, 1, 19], [19, 3, 11],
        ], [
            [24, 8, 26, 12], [25, 9, 27, 13],
            [24, 0, 25, 4], [26, 1, 27, 5],
            [8, 0, 9, 1], [12, 4, 13, 5],
            [8, 0, 24], [24, 4, 12], [12, 5, 26], [26, 1, 8],
            [25, 4, 13], [13, 5, 27], [27, 1, 9], [9, 0, 25],
        ], [
            [20, 12, 22, 14], [21, 13, 23, 15],
            [20, 4, 21, 6], [22, 5, 23, 7],
            [14, 6, 15, 7], [12, 4, 13, 5],
            [20, 6, 14], [14, 7, 22], [22, 5, 12], [12, 4, 20],
            [13, 4, 21], [21, 6, 15], [15, 7, 23], [23, 5, 13],
        ], [
            [28, 14, 30, 10], [29, 15, 31, 11],
            [28, 6, 29, 2], [30, 7, 31, 3],
            [14, 6, 15, 7], [10, 2, 11, 3],
            [14, 6, 28], [28, 2, 10], [10, 3, 30], [30, 7, 14],
            [29, 2, 11], [11, 3, 31], [31, 7, 15], [15, 6, 29]
        ], [
            [26, 18, 30, 22], [27, 19, 31, 23],
            [26, 1, 27, 5], [30, 7, 31, 3],
            [18, 3, 19, 1], [22, 5, 23, 7],
            [26, 5, 22], [22, 7, 30], [30, 3, 18], [18, 1, 26],
            [19, 1, 27], [27, 5, 23], [23, 7, 31], [31, 3, 19],
        ], [
            # Outer cubo
            [24, 20, 28, 16], [26, 18, 30, 22],
            [10, 18, 8, 16], [20, 12, 22, 14],
            [24, 8, 26, 12], [28, 14, 30, 10],
            [24, 16, 8], [24, 12, 20], [20, 14, 28], [28, 10, 16],
            [30, 18, 10], [26, 8, 18], [26, 22, 12], [22, 30, 14],
        ],
    ]

Cubos_Cols = [
    [2, 2, 2, 2, 2, 2, 0, 1, 0, 1, 0, 1, 0, 1] for cell in Cubos_Fs
]

Cells = [Tetrahedra0_Fs, Tetrahedra1_Fs, Cubos_Fs]
CellGroups = ['Tetrahedra group 0', 'Tetrahedra group 1', 'Cuboctahedra']
ColGroups  = [Tetrahedra0_Cols, Tetrahedra1_Cols, Cubos_Cols]

Col_0    = rgb.green[:]
Col_1    = rgb.orange[:]
Col_T2   = rgb.red[:]
Col_T2.append(0.2)
Cols     = [Col_0, Col_1, Col_T2]

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
        this.showWhichCells[-1][-1] = False
        this.showFs()
        this.setProjectionProperties(wCameraDistance = 3.76, wProjVolume = 0.25)

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
        this.setDefaultSize((237, 590))
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
                this.shape.setShowGroup(i/2, this.showGui[i].IsChecked())
        #print 'Ctrl Window size:', (this.GetClientSize()[0], this.GetClientSize()[1])
        this.canvas.paint()

    def onShowCells(this, event):
        for i in range(1, len(this.showGui), 2):
            if this.showGui[i].GetId() == event.GetId():
                this.showGui[i].SetSelection(event.GetSelection())
                groupId = i/2 # actually it should be (i-1)/2 but rounding fixes this
                list = [ this.showGui[i].IsChecked(j) for j in range(len(Cells[groupId])) ]
                this.shape.setShowCellsOfGroup(groupId, list)
        this.canvas.paint()

    # move to general class
    def setDefaultSize(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
