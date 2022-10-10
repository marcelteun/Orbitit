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

from orbitit import Geom3D, geomtypes, heptagons
from orbitit.geomtypes import HalfTurn3 as HalfTurn
from orbitit.geomtypes import Rot3 as Rot

vec = lambda x, y, z: geomtypes.Vec3([x, y, z])

TITLE = 'Equilateral Heptagons from Cube - Octahedron'

V2  = math.sqrt(2)
hV2 = 1.0/V2
tV3 = 1.0/math.sqrt(3)

halfTurn = HalfTurn(axis=geomtypes.UX)

class Shape(heptagons.EqlHeptagonShape):
    def __init__(this, *args, **kwargs):
        this.atanHV2 = Geom3D.Rad2Deg * math.atan(1/V2)
        super().__init__(
            base_isometries=[
                    geomtypes.E,
                    Rot(angle=geomtypes.turn(0.25), axis=geomtypes.UZ),
                    Rot(angle=geomtypes.turn(0.50), axis=geomtypes.UZ),
                    Rot(angle=geomtypes.turn(0.75), axis=geomtypes.UZ)
                ],
            # Use a half turn here to prevent edges to be drawn twice.
            extra_isometry=halfTurn,
            name='EglHeptS4xI'
        )
        this.initArrs()
        this.setH(1.0)
        this.setViewSettings(edgeR = 0.02, vertexR = 0.04)

    def setH(this, h):
        # TODO: use consistent angles, Dodecahedron uses without const atanHV2
        # such that dodecahedron angle == 0
        # check this with tetrahedron angle....
        this.angle = Geom3D.Rad2Deg * math.atan(V2 * (h - 1.0)) + this.atanHV2
        super().setH(h)

    def setAngle(this, a):
        # TODO: use consistent angles, Dodecahedron uses without const atanHV2
        # such that dodecahedron angle == 0
        # check this with tetrahedron angle....
        alpha = a - this.atanHV2
        this.h = hV2 * math.tan(alpha*Geom3D.Deg2Rad) + 1.0
        super().setAngle(alpha)

    def setV(this):
        # input this.h
        St = this.h / (2*this.h - 1)
        if this.heptPosAlt:
            #
            #    z
            #     ^
            #     |
            #     ---> y
            #    /
            #   V_
            #  x
            #
            #         .------------.
            #       ,'   2 _____1,'|
            #     ,'     ,'    ,'11|
            #    .-----3.----0'  | |
            #    |     5|    4|8 | |
            #    |      |     | ,' |
            #    |      +-----+' 10-
            #    |     6     7|9 ,'
            #    |            |,'
            #    '------------'
            #
            Vs = [
                    vec(St,     St,      St),    # 0
                    vec(0.0,    1.0,    1.0),
                    vec(0.0,    0.0,    this.h),
                    vec(1.0,    0.0,    1.0),    # 3

                    vec(St,     St,      St),    # 4
                    vec(1.0,    0.0,    1.0),
                    vec(this.h, 0.0,    0.0),
                    vec(1.0,    1.0,    0.0),    # 7

                    vec(St,     St,      St),    # 8
                    vec(1.0,    1.0,    0.0),
                    vec(0.0,    this.h, 0.0),
                    vec(0.0,    1.0,    1.0)     # 11
                ]
        else:
            #
            #    z
            #     ^
            #     |
            #     ---> y
            #    /
            #   V_
            #  x
            #
            #         .------------.
            #       ,'   0 _____3,'|
            #     ,'     ,'    ,'|9|
            #    .-----1.----2'  | |
            #    |     7|    6|10| |
            #    |      |     | ,' |
            #    |      +-----+' 8 -
            #    |     4     5|11,'
            #    |            |,'
            #    '------------'
            #
            Vs = [
                    vec(0.0,    0.0,    this.h), # 0
                    vec(1.0,    0.0,    1.0),
                    vec(St,     St,      St),
                    vec(0.0,    1.0,    1.0),    # 3

                    vec(this.h, 0.0,    0.0),    # 4
                    vec(1.0,    1.0,    0.0),
                    vec(St,     St,      St),
                    vec(1.0,    0.0,    1.0),    # 7

                    vec(0.0,    this.h, 0.0),    # 8
                    vec(0.0,    1.0,    1.0),
                    vec(St,     St,      St),
                    vec(1.0,    1.0,    0.0),    # 11
                ]

        # add heptagons
        heptN = heptagons.Kite2Hept(Vs[3], Vs[2], Vs[1], Vs[0])
        if heptN == None:
          this.errorStr = 'No valid equilateral heptagon for this position'
          return
        else:
          this.errorStr = ''
        Vs.extend(heptN[0]) # V12 - V18
        Ns = list(range(33))
        for i in range(4):
            Ns[i] = heptN[1]
        for i in range(12, 19):
            Ns[i] = heptN[1]
        heptN = heptagons.Kite2Hept(Vs[7], Vs[6], Vs[5], Vs[4])
        Vs.extend(heptN[0]) # V19 - V25
        for i in range(4, 8):
            Ns[i] = heptN[1]
        for i in range(19, 26):
            Ns[i] = heptN[1]
        heptN = heptagons.Kite2Hept(Vs[11], Vs[10], Vs[9], Vs[8])
        Vs.extend(heptN[0]) # V26 - V32
        for i in range(8, 12):
            Ns[i] = heptN[1]
        for i in range(26, 33):
            Ns[i] = heptN[1]

        xtraEs = []
        # add extra faces:
        if this.heptPosAlt:
            # Eql triangle
            Vs.extend([Vs[15], Vs[22], Vs[29]])         # V33 - V35
            # Isosceles triangles
            if this.triangleAlt:
                Vs.extend([Vs[13], Vs[14], Vs[32]]) # V36 - V38
                Vs.extend([Vs[20], Vs[21], Vs[18]]) # V39 - V41
                Vs.extend([Vs[27], Vs[28], Vs[25]]) # V42 - V44
            else:
                v = Vs[14]
                Vs.extend([Vs[13], Vs[14], vec(-v[0],  v[1],  v[2])]) # V36 - V38
                v = Vs[21]
                Vs.extend([Vs[20], Vs[21], vec( v[0], -v[1],  v[2])]) # V39 - V41
                v = Vs[28]
                Vs.extend([Vs[27], Vs[28], vec( v[0],  v[1], -v[2])]) # V42 - V44

            for i in range(3):
                Ns.append(Vs[0]) # N33 - N35
            # normals for the isosceles triangles:
            # N36 - N38, N39 - N41 and N42 - N44
            for i in range(3):
                o = 36 + 3*i
                IsoscelesTriangleN = Geom3D.Triangle(
                    Vs[o],
                    Vs[o+1],
                    Vs[o+2]
                ).normal()
                Ns.extend([IsoscelesTriangleN, IsoscelesTriangleN, IsoscelesTriangleN])

            xtraFs = [
                    # Eql triangle
                    [33, 34, 35],
                    # Isosceles triangles
                    [36, 37, 38],
                    [39, 40, 41],
                    [42, 43, 44],
                ]
            this.xtraColIds = [2 for i in range(4)]
            if this.addXtraEdge:
                if this.triangleAlt:
                    xtraEs = [36, 38, 39, 41, 42, 44]
                else:
                    xtraEs = [37, 38, 40, 41, 43, 44]
        else:
            # The Squares, divided into rectangular isosceles triangles,
            # because of the sym-op
            Vs.extend([Vs[15], Vs[16], vec(0, 0, Vs[15][2])]) # V33 - V35
            Vs.extend([Vs[22], Vs[23], vec(Vs[22][0], 0, 0)]) # V36 - V38
            Vs.extend([Vs[29], Vs[30], vec(0, Vs[29][1], 0)]) # V39 - V41
            # add isosceles triangles:
            if this.triangleAlt:
                v = Vs[13]
                Vs.extend([Vs[13], Vs[14], vec(v[0], -v[1], v[2])]) # V42 - V44
                v = Vs[20]
                Vs.extend([Vs[20], Vs[21], vec(v[0], v[1], -v[2])]) # V45 - V47
                v = Vs[27]
                Vs.extend([Vs[27], Vs[28], vec(-v[0], v[1], v[2])]) # V48 - V50
            else:
                Vs.extend([Vs[13], Vs[14], Vs[24]]) # V42 - V44
                Vs.extend([Vs[20], Vs[21], Vs[31]]) # V45 - V47
                Vs.extend([Vs[27], Vs[28], Vs[17]]) # V48 - V50

            # normals for the equilateral triangles:
            for i in range(3):
                Ns.append(Vs[0])  # N33 - N35
            for i in range(3):
                Ns.append(Vs[4])  # N36 - N38
            for i in range(3):
                Ns.append(Vs[8]) # N39 - N41
            # normals for the isosceles triangles:
            # N42 - N44, N45 - N47 and N48 - N50
            for i in range(3):
                o = 42 + 3*i
                IsoscelesTriangleN = Geom3D.Triangle(
                    Vs[o],
                    Vs[o+1],
                    Vs[o+2]
                ).normal()
                Ns.extend([IsoscelesTriangleN, IsoscelesTriangleN, IsoscelesTriangleN])

            xtraFs = [
                    # square parts:
                    [33, 34, 35],
                    [36, 37, 38],
                    [39, 40, 41],
                    # isosceles triangles:
                    [42, 43, 44],
                    [45, 46, 47],
                    [48, 49, 50]
                ]
            this.xtraColIds = [2 for i in range(6)]
            if this.addXtraEdge:
                if this.triangleAlt:
                    xtraEs = [42, 44, 45, 47, 48, 50]
                else:
                    xtraEs = [43, 44, 46, 47, 49, 50]

        this.setBaseVertexProperties(Vs = Vs, Ns = Ns)
        Fs = []
        Es = []
        colIds = []
        if this.showKite:
            Fs.extend(this.kiteFs)
            Es.extend(this.kiteEs)
            colIds.extend(this.kiteColIds)
        if this.showHepta:
            Fs.extend(this.heptFs)
            Es.extend(this.heptEs)
            colIds.extend(this.heptColIds)
        if this.showXtra:
            Fs.extend(xtraFs)
            Es.extend(xtraEs)
            colIds.extend(this.xtraColIds)
        this.setBaseEdgeProperties(Es=Es)
        this.setBaseFaceProperties(Fs=Fs, colors=(this.theColors, colIds))

    def toPsPiecesStr(this,
            faceIndices=[],
            scaling=1,
            precision=7,
            margin=1.0e-10,
        ):
        if faceIndices == []:
            offset = 0
            if this.showKite:
                faceIndices.append(offset)
                offset += len(this.kiteFs)
            if this.showHepta:
                faceIndices.append(offset)
                offset += len(this.heptFs)
            if this.showXtra:
                faceIndices.append(offset)
                if this.heptPosAlt:
                    faceIndices.append(offset+1)
                else:
                    faceIndices.append(offset+3)
        return super().toPsPiecesStr(faceIndices, scaling, precision, margin)

    def initArrs(this):
        this.kiteFs = [
                [0, 1, 2, 3],
                [4, 5, 6, 7],
                [8, 9, 10, 11]
            ]
        this.kiteColIds = [0 for i in range(3)]
        this.kiteEs = [
                0, 1, 1, 2, 2, 3,
                4, 5, 5, 6, 6, 7,
                8, 9, 9, 10, 10, 11
            ]
        this.heptFs = [
                [18, 17, 16, 15, 14, 13, 12],
                [25, 24, 23, 22, 21, 20, 19],
                [32, 31, 30, 29, 28, 27, 26]
            ]
        this.heptColIds = [1 for i in range(3)]
        this.heptEs = [
                12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 12,
                19, 20, 20, 21, 21, 22, 22, 23, 23, 24, 24, 25, 25, 19,
                26, 27, 27, 28, 28, 29, 29, 30, 30, 31, 31, 32, 32, 26
            ]
        this.xtraEs = []

    # GUI PART

class CtrlWin(heptagons.EqlHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
        # a: angle
        # s: string text in GUI
        # t: triangle alternative value
        # e: add extra edge
        # if a field is not specified: don't care.
        this.minMaxAngles = [
            {'a':   0.0,               's': 'None'},
            {'a':  35.264389682754654, 's': 'Cube'},
            {'a':  90.0,               's': 'Octahedron'}
        ]
        this.prefHeptSpecAngles = [
            {'a':   0.0,                's': 'None'},
            {'a':  25.737159975962488, 's': 'Minimum Angle', 't': False, 'e': False},
            {'a': 115.241668099768972, 's': 'Maximum Angle', 't': True, 'e': False},
            {'a':  89.956421271960977, 's': 'Equilateral Triangles', 't': True, 'e': True},
            {'a':  56.997093533919418, 's': 'Equilateral Triangles', 't': False, 'e': True},
            {'a':  58.020015841718553, 's': 'Rhombi', 't': True, 'e': False},
        ]

        this.altHeptSpecAngles = [
            {'a':   0.0,               's': 'None'},
            {'a':   2.372909245253462, 's': 'Minimum Angle', 't': True, 'e': False},
            {'a':  61.462528254690412, 's': 'Maximum Angle', 't': True, 'e': False},
            {'a':  23.204016748550931, 's': 'Equilateral Triangles', 't': True, 'e': True},
            {'a':  14.020488654174214, 's': 'Equilateral Triangles', 't': False, 'e': True},
        ]
        this.setKiteAngleExtremes(2.4, 115.24)
        kwargs['title'] = TITLE
        heptagons.EqlHeptagonCtrlWin.__init__(this,
            shape, canvas, (340, 570),
            *args, **kwargs
        )

    def add_specials(this, parentFrame, parentSizer):
        labelLst = []
        for i in range(len(this.minMaxAngles)):
            labelLst.append(this.minMaxAngles[i]['s'])
        this.minMaxPosGui = wx.RadioBox(parentFrame,
                    label = 'Platonic Solids Positions',
                    style = wx.RA_VERTICAL,
                    choices = labelLst
                )
        parentFrame.Bind(wx.EVT_RADIOBOX, this.onMinMaxPos, id = this.minMaxPosGui.GetId())
        this.minMaxPreviousIndex = 0

        labelLst = []
        for i in range(len(this.prefHeptSpecAngles)):
            labelLst.append(this.prefHeptSpecAngles[i]['s'])
        this.prefHeptSpecPosGui = wx.RadioBox(parentFrame,
                    label = 'Prefered Heptagon',
                    style = wx.RA_VERTICAL,
                    choices = labelLst
                )
        parentFrame.Bind(wx.EVT_RADIOBOX, this.onPrefHeptSpecPos, id = this.prefHeptSpecPosGui.GetId())
        this.prefHeptSpecPreviousIndex = 0

        labelLst = []
        for i in range(len(this.altHeptSpecAngles)):
            labelLst.append(this.altHeptSpecAngles[i]['s'])
        this.altHeptSpecPosGui = wx.RadioBox(parentFrame,
                    label = 'Alternative Heptagon      ',
                    style = wx.RA_VERTICAL,
                    choices = labelLst
                )
        parentFrame.Bind(wx.EVT_RADIOBOX, this.onAltHeptSpecPos, id = this.altHeptSpecPosGui.GetId())
        this.altHeptSpecPreviousIndex = 0

        specPosSizer = wx.BoxSizer(wx.HORIZONTAL)
        specPosSizer.Add(this.prefHeptSpecPosGui, 1, wx.EXPAND)
        specPosSizer.Add(this.altHeptSpecPosGui,  1, wx.EXPAND)

        parentSizer.Add(this.minMaxPosGui,  8, wx.EXPAND)
        parentSizer.Add(specPosSizer,      15, wx.EXPAND)

    def onMinMaxPos(this, event = None):
        index = this.minMaxPosGui.GetSelection()
        angleData = this.minMaxAngles[index]
        angle = angleData['a']
        if index != 0 and this.minMaxPreviousIndex == 0:
            # save angle in None
            this.minMaxAngles[0]['a'] = this.Slider2Angle(
                    this.kiteAngleGui.GetValue()
                )
            #TODO save other settings? Make a functions for this.
        this.minMaxPreviousIndex = index
        this.kiteAngleGui.SetValue(this.Angle2Slider(angle))
        this.shape.setAngle(angle)

        this.showKiteChk.SetValue(True)
        this.showHeptaChk.SetValue(True)
        this.showXtraChk.SetValue(False)
        this.altHeptPosChk.SetValue(False)
        this.on_view_settings_chk(this)
        if index != 0:
            if this.prefHeptSpecPosGui.GetSelection() != 0:
                this.prefHeptSpecPosGui.SetSelection(0)
            if this.altHeptSpecPosGui.GetSelection() != 0:
                this.altHeptSpecPosGui.SetSelection(0)

    def onPrefHeptSpecPos(this, event = None):
        index = this.prefHeptSpecPosGui.GetSelection()
        angleData = this.prefHeptSpecAngles[index]
        angle = angleData['a']
        if index != 0 and this.prefHeptSpecPreviousIndex == 0:
            # save angle in None
            this.prefHeptSpecAngles[0]['a'] = this.Slider2Angle(
                    this.kiteAngleGui.GetValue()
                )
            #TODO save other settings? Make a functions for this.
        this.prefHeptSpecPreviousIndex = index
        this.kiteAngleGui.SetValue(this.Angle2Slider(angle))
        this.shape.setAngle(angle)

        this.showHeptaChk.SetValue(True)
        this.altHeptPosChk.SetValue(False)
        if 't' in angleData:
            this.showKiteChk.SetValue(False)
            this.showXtraChk.SetValue(True)
            this.triangleAltChk.SetValue(angleData['t'])
        if 'e' in angleData:
            this.addXtraEdgeChk.SetValue(angleData['e'])
        this.on_view_settings_chk(this)
        if index != 0:
            if this.minMaxPosGui.GetSelection() != 0:
                this.minMaxPosGui.SetSelection(0)
            if this.altHeptSpecPosGui.GetSelection() != 0:
                this.altHeptSpecPosGui.SetSelection(0)

    def onAltHeptSpecPos(this, event = None):
        index = this.altHeptSpecPosGui.GetSelection()
        angleData = this.altHeptSpecAngles[index]
        angle = angleData['a']
        if index != 0 and this.altHeptSpecPreviousIndex == 0:
            # save angle in None
            this.altHeptSpecAngles[0]['a'] = this.Slider2Angle(
                    this.kiteAngleGui.GetValue()
                )
            #TODO save other settings? Make a functions for this.
        this.altHeptSpecPreviousIndex = index
        this.kiteAngleGui.SetValue(this.Angle2Slider(angle))
        this.shape.setAngle(angle)

        this.showHeptaChk.SetValue(True)
        this.altHeptPosChk.SetValue(True)
        if 't' in angleData:
            this.showKiteChk.SetValue(False)
            this.showXtraChk.SetValue(True)
            this.triangleAltChk.SetValue(angleData['t'])
        if 'e' in angleData:
            this.addXtraEdgeChk.SetValue(angleData['e'])
        this.on_view_settings_chk(this)
        if index != 0:
            if this.minMaxPosGui.GetSelection() != 0:
                this.minMaxPosGui.SetSelection(0)
            if this.prefHeptSpecPosGui.GetSelection() != 0:
                this.prefHeptSpecPosGui.SetSelection(0)

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
