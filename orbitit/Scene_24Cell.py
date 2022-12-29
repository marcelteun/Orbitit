#!/usr/bin/python
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

from orbitit import geom_3d, Geom4D, rgb

TITLE = '24-Cell'

l = 2.3

vs = [

        [ 0,  0,  l,  l],  #  0
        [ 0,  0, -l,  l],  #  1
        [ 0,  l,  0,  l],  #  2
        [ 0, -l,  0,  l],  #  3
        [ l,  0,  0,  l],  #  4
        [-l,  0,  0,  l],  #  5

        [ 0,  0,  l, -l],  #  6
        [ 0,  0, -l, -l],  #  7
        [ 0,  l,  0, -l],  #  8
        [ 0, -l,  0, -l],  #  9
        [ l,  0,  0, -l],  # 10
        [-l,  0,  0, -l],  # 11

        # vertices between 2 parallel octrahedra edges:
        #TODO reorder logically
        #                          between
        [ 0,  l,  l,  0],  # 12    (6, 8) and (0, 2)
        [ l,  l,  0,  0],  # 13    (8, 10) and (2, 4)
        [ 0,  l, -l,  0],  # 14    (7, 8) and (1, 2)
        [-l,  l,  0,  0],  # 15    (8, 11) and (2, 5)

        [ l,  0,  l,  0],  # 16    (6, 10) and (0, 4)
        [ l,  0, -l,  0],  # 17    (7, 10) and (1, 4)
        [-l,  0, -l,  0],  # 18    (7, 11) and (1, 5)
        [-l,  0,  l,  0],  # 19    (6, 11) and (0, 5)

        [ 0, -l,  l,  0],  # 20    (6, 9) and (0, 3)
        [ l, -l,  0,  0],  # 21    (9, 10) and (3, 4)
        [ 0, -l, -l,  0],  # 22    (7, 9) and (1, 3)
        [-l, -l,  0,  0],  # 23    (9, 11) and (3, 5)
    ]

# Inner octahedron: 8
#                   |
#                   |,7
#             11----|---10
#                 6'|
#                   |
#                   9
#
#

FsOpaq = [  # opaque faces
        # 6, 8, 10:
        [
            [6, 8, 10], [6, 12, 8], [8, 13, 10], [10, 16, 6],
            [6, 16, 12], [8, 12, 13], [10, 13, 16], [12, 16, 13],
        ],
        # 6, 9, 11:
        [
            [6, 9, 11], [11, 19, 6], [6, 20, 9], [9, 23, 11],
            [19, 20, 6], [20, 23, 9], [23, 19, 11], [19, 23, 20],
        ],
        # 7, 9, 10:
        [
            [7, 9, 10], [7, 22, 9], [9, 21, 10], [10, 17, 7],
            [22, 7, 17], [17, 10, 21], [21, 9, 22], [17, 21, 22],
        ],
        # 7, 8, 11:
        [
            [7, 8, 11],  [7, 14, 8], [8, 15, 11], [11, 18, 7],
            [14, 7, 18], [18, 11, 15],  [15, 8, 14], [14, 18, 15],
        ],
        # outer 0, (-20-), 3, (-21-) 4 (-16-) (above 6, 9, 10)
        [
            [0, 3, 4], [0, 20, 3], [3, 21, 4], [4, 16, 0],
            [20, 0, 16], [16, 4, 21], [21, 3, 20], [20, 16, 21],
        ],
        # outer 1, (-14-), 2, (-13-) 4 (-17-) (above 7, 8, 10)
        [
            [1, 2, 4], [1, 14, 2], [2, 13, 4], [4, 17, 1],
            [14, 1, 17], [17, 4, 13], [13, 2, 14], [14, 17, 13],
        ],
        # outer 0, (-12-), 2, (-15-) 5 (-19-) (above 6, 8, 11)
        [
            [0, 2, 5], [0, 12, 2], [2, 15, 5], [5, 19, 0],
            [12, 0, 19], [19, 5, 15], [15, 2, 12], [12, 19, 15],
        ],
        # outer 1, (-22-), 3, (-23-) 5 (-18-) (above 7, 9, 11)
        [
            [1, 3, 5], [1, 22, 3], [3, 23, 5], [5, 18, 1],
            [22, 1, 18], [18, 5, 23], [23, 3, 22], [22, 18, 23],
        ],
    ]
FsTransp_0 = [
        # inner cell:
        [
            [6, 8, 10], [6, 10, 9], [6, 9, 11], [6, 11, 8],
            [7, 8, 10], [7, 9, 10], [7, 9, 11], [7, 8, 11],
        ],
        # 12, 16, 20, 19:
        [
            [6, 16, 12], [6, 20, 16], [6, 19, 20], [6, 12, 19],
            [0, 12, 16], [0, 16, 20], [0, 20, 19], [0, 19, 12],
        ],
        # 14, 18, 22, 17:
        [
            [7, 18, 14], [7, 22, 18], [7, 17, 22], [7, 14, 17],
            [1, 14, 18], [1, 18, 22], [1, 22, 17], [1, 17, 14],
        ],
        # 14, 13, 12, 15:
        [
            [8, 12, 13], [8, 13, 14], [8, 14, 15], [8, 15, 12],
            [2, 13, 12], [2, 14, 13], [2, 15, 14], [2, 12, 15],
        ],
        # 20, 21, 22, 23:
        [
            [9, 22, 21], [9, 21, 20], [9, 20, 23], [9, 23, 22],
            [3, 21, 22], [3, 20, 21], [3, 23, 20], [3, 22, 23],
        ],
        # 16, 13, 17, 21:
        [
            [10, 13, 16], [10, 17, 13], [10, 21, 17], [10, 16, 21],
            [4, 16, 13], [4, 13, 17], [4, 17, 21], [4, 21, 16],
        ],
        # 15, 19, 23, 18:
        [
            [11, 23, 19], [11, 19, 15], [11, 15, 18], [11, 18, 23],
            [5, 19, 23], [5, 15, 19], [5, 18, 15], [5, 23, 18],
        ],
        # outer cell:
        [
            [0, 4, 3], [0, 2, 4], [0, 5, 2], [0, 3, 5],
            [1, 4, 3], [1, 2, 4], [1, 5, 2], [1, 3, 5],
        ],
] # Transparent Octahedra group 0

FsTransp_1 = [
        # 6, 10, 9:
        [
            [6, 10, 9], [6, 16, 10], [10, 21, 9], [9, 20, 6],
            [16, 6, 20], [20, 9, 21], [21, 10, 16], [16, 20, 21],
        ],
        # 8, 6, 11:
        [
            [8, 6, 11], [8, 12, 6], [6, 19, 11], [11, 15, 8],
            [12, 8, 15], [15, 11, 19], [19, 6, 12], [12, 15, 19],
        ],
        # 8, 7, 10:
        [
            [8, 7, 10], [8, 14, 7], [7, 17, 10], [10, 13, 8],
            [14, 8, 13], [13, 10, 17], [17, 7, 14], [14, 13, 17],
        ],
        # 9, 7, 11:
        [
            [9, 7, 11], [9, 22, 7], [7, 18, 11], [11, 23, 9],
            [22, 9, 23], [23, 11, 18], [18, 7, 22], [22, 23, 18],
        ],
        # outer 0, (-16-), 4, (-13-) 2 (-12-) (above 6, 10, 8)
        [
            [0, 4, 2], [0, 16, 4], [4, 13, 2], [2, 12, 0],
            [16, 0, 12], [12, 2, 13], [13, 4, 16], [16, 12, 13],
        ],
        # outer 1, (-17-), 4, (-21-) 3 (-22-) (above 7, 10, 9)
        [
            [1, 4, 3], [1, 17, 4], [4, 21, 3], [3, 22, 1],
            [17, 1, 22], [22, 3, 21], [21, 4, 17], [17, 22, 21],
        ],
        # outer 0, (-19-), 5, (-23-) 3 (-20-) (above 6, 11, 9)
        [
            [0, 5, 3],  [0, 19, 5], [5, 23, 3], [3, 20, 0],
            [19, 0, 20], [20, 3, 23], [23, 5, 19], [19, 20, 23],
        ],
        # outer 1, (-18-), 5, (-15-) 2 (-14-) (above 7, 11, 8)
        [
            [1, 5, 2], [1, 18, 5], [5, 15, 2], [2, 14, 1],
            [18, 1, 14], [14, 2, 15], [15, 5, 18], [18, 14, 15],
        ],
] # Transparent Octahedra group 1

Col0  = rgb.orange[:]
Col2  = rgb.springGreen[:]
Col2.append(0.2)
Col1  = rgb.sienna[:]
Col1.append(0.4)

Cols     = [Col0, Col1, Col2]
ColIdsOpaq = [
    0, 0, 0, 0, 0, 0, 0, 0,
]
ColIdsTransp_0 = [
    1, 1, 1, 1, 1, 1, 1, 1,
]
ColIdsTransp_1 = [
    2, 2, 2, 2, 2, 2, 2, 2,
]

ColIds_Alt1_0 = [
    1, 0, 0, 0, 1, 1, 1, 0,
]
ColIds_Alt1_1 = [
    2, 0, 0, 0, 2, 2, 2, 0,
]
ColIds_Alt1_2 = [
    1, 2, 1, 2, 2, 1, 2, 1,
]

Es_0 = [
        0, 2, 0, 3, 0, 4, 0, 5,
        2, 4, 4, 3, 3, 5, 5, 2,
        1, 2, 1, 3, 1, 4, 1, 5,
    ]
offsetIndexWith = lambda i: lambda x: x+i
ES = []
ES.extend(list(map(offsetIndexWith(0), Es_0)))
ES.extend(list(map(offsetIndexWith(6), Es_0)))
ES.extend(
    [
        6, 12, 6, 16, 8, 12, 8, 13, 10, 13, 10, 16, 12, 16, 16, 13, 13, 12,
        11, 19, 19, 6, 6, 20, 20, 9, 9, 23, 23, 11, 19, 23, 23, 20, 20, 19,
        7, 22, 22, 9, 9, 21, 21, 10, 10, 17, 17, 7, 17, 21, 21, 22, 22, 17,
        8, 14, 14, 7, 7, 18, 18, 11, 11, 15, 15, 8, 14, 18, 18, 15, 15, 14,
        16, 20, 20, 21, 21, 16, 12, 15, 15, 19, 19, 12,
        14, 13, 13, 17, 17, 14, 22, 23, 23, 18, 18, 22,
        0, 12, 0, 16, 0, 20, 0, 19,
        1, 14, 1, 18, 1, 22, 1, 17,
        2, 14, 2, 13, 2, 12, 2, 15,
        3, 20, 3, 21, 3, 22, 3, 23,
        4, 16, 4, 13, 4, 17, 4, 21,
        5, 15, 5, 19, 5, 23, 5, 18,
    ]
)

class Shape(Geom4D.SimpleShape):
    def __init__(this):
        Geom4D.SimpleShape.__init__(this,
            vs, Cs=[], es=ES, ns=[],
            colors=(Cols, ColIdsOpaq),
            name=TITLE
        )
        this.showSolids = True
        this.showTranspI = True
        this.showTranspII = True
        this.showWichSolids = [ True for i in range(8) ]
        this.showWichTranspI = [ True for i in range(8) ]
        this.showWichTranspII = [ True for i in range(8) ]
        this.colAlternative = 0
        this.setProjectionProperties(2.3, 1.0)

    def setShowSolids(this, show = True):
        this.showFs(show, this.showTranspI, this.showTranspII)

    def setShowTranspI(this, show = True):
        this.showFs(this.showSolids, show, this.showTranspII)

    def setShowTranspII(this, show = True):
        this.showFs(this.showSolids, this.showTranspI, show)

    def setShowWhichSolids(this, list):
        this.showWichSolids = list
        if this.showSolids:
            this.showFs(this.showSolids, this.showTranspI, this.showTranspII)

    def setShowWhichTranspI(this, list):
        this.showWichTranspI = list
        if this.showTranspI:
            this.showFs(this.showSolids, this.showTranspI, this.showTranspII)

    def setShowWhichTranspII(this, list):
        this.showWichTranspII = list
        if this.showTranspII:
            this.showFs(this.showSolids, this.showTranspI, this.showTranspII)

    def showFs(this, showSolids = True, showTranspI = True, showTranspII = True):
        Cs = []
        this.showSolids = showSolids
        this.showTranspI = showTranspI
        this.showTranspII = showTranspII
        colIds = []
        # Note the order is important for the transparency.
        if showSolids:
            for i in range(8):
                if this.showWichSolids[i]:
                    Cs.append(FsOpaq[i])
                    #Cs.extend(FsTransp_0[i])
                    if this.colAlternative == 0:
                        colIds.append(ColIds_Alt1_0)
                    else:
                        colIds.append(ColIdsOpaq)
                else:
                    Cs.append([])
                    colIds.append([])
        if showTranspII:
            for i in range(8):
                if this.showWichTranspII[i]:
                    Cs.append(FsTransp_1[i])
                    if this.colAlternative == 0:
                        colIds.append(ColIds_Alt1_1)
                    else:
                        colIds.append(ColIdsTransp_1)
                else:
                    Cs.append([])
                    colIds.append([])
        if showTranspI:
            for i in range(8):
                if this.showWichTranspI[i]:
                    Cs.append(FsTransp_0[i])
                    #Cs.extend(FsOpaq[i])
                    if this.colAlternative == 0:
                        colIds.append(ColIds_Alt1_2)
                    else:
                        colIds.append(ColIdsTransp_0)
                else:
                    Cs.append([])
                    colIds.append([])
        this.setCellProperties(Cs = Cs)
        this.set_face_props(colors = (Cols, colIds))

    def setColAlternative(this, index):
        colIds = []
        this.colAlternative = index
        if this.showSolids:
            for i in range(8):
                if this.showWichSolids[i]:
                    if index == 0:
                        colIds.append(ColIds_Alt1_0)
                    else:
                        colIds.append(ColIdsOpaq)
                else:
                    colIds.append([])
        if this.showTranspII:
            for i in range(8):
                if this.showWichTranspII[i]:
                    if index == 0:
                        colIds.append(ColIds_Alt1_1)
                    else:
                        colIds.append(ColIdsTransp_1)
                else:
                    colIds.append([])
        if this.showTranspI:
            for i in range(8):
                if this.showWichTranspI[i]:
                    if index == 0:
                        colIds.append(ColIds_Alt1_2)
                    else:
                        colIds.append(ColIdsTransp_0)
                else:
                    colIds.append([])
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
        this.set_default_size((505, 594))
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()

    def create_control_sizer(this):
        ctrlSizer = wx.BoxSizer(wx.VERTICAL)

        str = 'Octahedron %d'
        cellList = [ str % i for i in range(8)]

        this.showSolidsGui = wx.CheckBox(this.panel, label = 'Show Solid Octahedra')
        this.showSolidsGui.SetValue(this.shape.showSolids)
        this.showSolidsGui.Bind(wx.EVT_CHECKBOX, this.onShowSolids)
        this.showSolidsListGui = wx.CheckListBox(this.panel, choices = cellList)
        this.showSolidsListGui.Bind(wx.EVT_CHECKLISTBOX, this.onShowSolidsList)
        for i in range(4): this.showSolidsListGui.Check(i)
        list = [ this.showSolidsListGui.IsChecked(i) for i in range(8) ]
        this.shape.setShowWhichSolids(list)
        showSolidsSizer = wx.BoxSizer(wx.HORIZONTAL)
        showSolidsSizer.Add(this.showSolidsGui, 1, wx.EXPAND)
        showSolidsSizer.Add(this.showSolidsListGui, 1, wx.EXPAND)

        this.showTranspIGui = wx.CheckBox(this.panel, label = 'Show Transparent Octahedra (I)')
        this.showTranspIGui.SetValue(this.shape.showTranspI)
        this.showTranspIGui.Bind(wx.EVT_CHECKBOX, this.onShowTranspI)
        this.showTranspIListGui = wx.CheckListBox(this.panel, choices = cellList)
        this.showTranspIListGui.Bind(wx.EVT_CHECKLISTBOX, this.onShowTranspIList)
        for i in range(7): this.showTranspIListGui.Check(i)
        list = [ this.showTranspIListGui.IsChecked(i) for i in range(8) ]
        this.shape.setShowWhichTranspI(list)
        showTranspISizer = wx.BoxSizer(wx.HORIZONTAL)
        showTranspISizer.Add(this.showTranspIGui, 1, wx.EXPAND)
        showTranspISizer.Add(this.showTranspIListGui, 1, wx.EXPAND)

        this.showTranspIIGui = wx.CheckBox(this.panel, label = 'Show Transparent Octahedra (II)')
        this.showTranspIIGui.SetValue(this.shape.showTranspII)
        this.showTranspIIGui.Bind(wx.EVT_CHECKBOX, this.onShowTranspII)
        this.showTranspIIListGui = wx.CheckListBox(this.panel, choices = cellList)
        this.showTranspIIListGui.Bind(wx.EVT_CHECKLISTBOX, this.onShowTranspIIList)
        for i in range(8): this.showTranspIIListGui.Check(i)
        list = [ this.showTranspIIListGui.IsChecked(i) for i in range(8) ]
        this.shape.setShowWhichTranspII(list)
        showTranspIISizer = wx.BoxSizer(wx.HORIZONTAL)
        showTranspIISizer.Add(this.showTranspIIGui, 1, wx.EXPAND)
        showTranspIISizer.Add(this.showTranspIIListGui, 1, wx.EXPAND)

        this.colAltGui  = wx.RadioBox(this.panel,
            label = 'Colour Alternative',
            style = wx.RA_HORIZONTAL,
            choices = ['a', 'b']
        )
        this.panel.Bind(wx.EVT_RADIOBOX, this.onColAlt, id = this.colAltGui.GetId())
        #this.colAltGu.SetSelection(0)
        colAltSizer = wx.BoxSizer(wx.HORIZONTAL)
        colAltSizer.Add(this.colAltGui, 1, wx.EXPAND)

        showFacesSizer = wx.StaticBoxSizer(
            wx.StaticBox(this.panel, label = 'View Settings'),
            wx.VERTICAL
        )
        showFacesSizer.Add(showSolidsSizer, 1, wx.EXPAND)
        showFacesSizer.Add(showTranspISizer, 1, wx.EXPAND)
        showFacesSizer.Add(showTranspIISizer, 1, wx.EXPAND)

        ctrlSizer.Add(showFacesSizer, 20, wx.EXPAND)
        ctrlSizer.Add(colAltSizer, 2, wx.EXPAND)

        return ctrlSizer

    def onShowSolids(this, event):
        this.shape.setShowSolids(this.showSolidsGui.IsChecked())
        this.canvas.paint()

    def onShowTranspI(this, event):
        this.shape.setShowTranspI(this.showTranspIGui.IsChecked())
        this.canvas.paint()

    def onShowTranspII(this, event):
        this.shape.setShowTranspII(this.showTranspIIGui.IsChecked())
        this.canvas.paint()

    def onShowSolidsList(this, event):
        this.showSolidsListGui.SetSelection(event.GetSelection())
        list = [ this.showSolidsListGui.IsChecked(i) for i in range(8) ]
        this.shape.setShowWhichSolids(list)
        this.canvas.paint()

    def onShowTranspIList(this, event):
        this.showTranspIListGui.SetSelection(event.GetSelection())
        list = [ this.showTranspIListGui.IsChecked(i) for i in range(8) ]
        this.shape.setShowWhichTranspI(list)
        this.canvas.paint()

    def onShowTranspIIList(this, event):
        this.showTranspIIListGui.SetSelection(event.GetSelection())
        list = [ this.showTranspIIListGui.IsChecked(i) for i in range(8) ]
        this.shape.setShowWhichTranspII(list)
        this.canvas.paint()

    def onColAlt(this, event):
        this.shape.setColAlternative(this.colAltGui.GetSelection())
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
