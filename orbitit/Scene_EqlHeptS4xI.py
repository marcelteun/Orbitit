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

from orbitit import geom_3d, geomtypes, heptagons
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
        this.atanHV2 = geom_3d.Rad2Deg * math.atan(1/V2)
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
        this.height = 1.0

    def set_height(this, h):
        # TODO: use consistent angles, Dodecahedron uses without const atanHV2
        # such that dodecahedron angle == 0
        # check this with tetrahedron angle....
        this._angle = geom_3d.Rad2Deg * math.atan(V2 * (h - 1.0)) + this.atanHV2
        super().set_height(h)

    def set_angle(self, a):
        # TODO: use consistent angles, Dodecahedron uses without const atanHV2
        # such that dodecahedron angle == 0
        # check this with tetrahedron angle....
        alpha = a - self.atanHV2
        self._height = hV2 * math.tan(alpha*geom_3d.Deg2Rad) + 1.0
        super().set_angle(alpha)

    def set_vs(this):
        St = this.height / (2*this.height - 1)
        if this.alt_hept_pos:
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
            vs = [
                vec(St, St, St),  # 0
                vec(0.0, 1.0, 1.0),
                vec(0.0, 0.0, this.height),
                vec(1.0, 0.0, 1.0),  # 3

                vec(St, St, St),  # 4
                vec(1.0, 0.0, 1.0),
                vec(this.height, 0.0, 0.0),
                vec(1.0, 1.0, 0.0),  # 7

                vec(St, St, St),  # 8
                vec(1.0, 1.0, 0.0),
                vec(0.0, this.height, 0.0),
                vec(0.0, 1.0, 1.0)  # 11
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
            vs = [
                vec(0.0, 0.0, this.height),  # 0
                vec(1.0, 0.0, 1.0),
                vec(St, St, St),
                vec(0.0, 1.0, 1.0),  # 3

                vec(this.height, 0.0, 0.0),  # 4
                vec(1.0, 1.0, 0.0),
                vec(St, St, St),
                vec(1.0, 0.0, 1.0),  # 7

                vec(0.0, this.height, 0.0),  # 8
                vec(0.0, 1.0, 1.0),
                vec(St, St, St),
                vec(1.0, 1.0, 0.0),  # 11
            ]

        # add heptagons
        heptN = heptagons.kite_to_hept(vs[3], vs[2], vs[1], vs[0])
        if heptN == None:
          this.error_msg = 'No valid equilateral heptagon for this position'
          return
        else:
          this.error_msg = ''
        vs.extend(heptN[0]) # V12 - V18
        ns = list(range(33))
        for i in range(4):
            ns[i] = heptN[1]
        for i in range(12, 19):
            ns[i] = heptN[1]
        heptN = heptagons.kite_to_hept(vs[7], vs[6], vs[5], vs[4])
        vs.extend(heptN[0]) # V19 - V25
        for i in range(4, 8):
            ns[i] = heptN[1]
        for i in range(19, 26):
            ns[i] = heptN[1]
        heptN = heptagons.kite_to_hept(vs[11], vs[10], vs[9], vs[8])
        vs.extend(heptN[0]) # V26 - V32
        for i in range(8, 12):
            ns[i] = heptN[1]
        for i in range(26, 33):
            ns[i] = heptN[1]

        xtraEs = []
        # add extra faces:
        if this.alt_hept_pos:
            # Eql triangle
            vs.extend([vs[15], vs[22], vs[29]])         # V33 - V35
            # Isosceles triangles
            if this.tri_alt:
                vs.extend([vs[13], vs[14], vs[32]]) # V36 - V38
                vs.extend([vs[20], vs[21], vs[18]]) # V39 - V41
                vs.extend([vs[27], vs[28], vs[25]]) # V42 - V44
            else:
                v = vs[14]
                vs.extend([vs[13], vs[14], vec(-v[0],  v[1],  v[2])]) # V36 - V38
                v = vs[21]
                vs.extend([vs[20], vs[21], vec( v[0], -v[1],  v[2])]) # V39 - V41
                v = vs[28]
                vs.extend([vs[27], vs[28], vec( v[0],  v[1], -v[2])]) # V42 - V44

            for i in range(3):
                ns.append(vs[0]) # N33 - N35
            # normals for the isosceles triangles:
            # N36 - N38, N39 - N41 and N42 - N44
            for i in range(3):
                o = 36 + 3*i
                IsoscelesTriangleN = geom_3d.Triangle(
                    vs[o],
                    vs[o+1],
                    vs[o+2]
                ).normal()
                ns.extend([IsoscelesTriangleN, IsoscelesTriangleN, IsoscelesTriangleN])

            xtraFs = [
                    # Eql triangle
                    [33, 34, 35],
                    # Isosceles triangles
                    [36, 37, 38],
                    [39, 40, 41],
                    [42, 43, 44],
                ]
            this.xtraColIds = [2 for i in range(4)]
            if this.add_extra_edge:
                if this.tri_alt:
                    xtraEs = [36, 38, 39, 41, 42, 44]
                else:
                    xtraEs = [37, 38, 40, 41, 43, 44]
        else:
            # The Squares, divided into rectangular isosceles triangles,
            # because of the sym-op
            vs.extend([vs[15], vs[16], vec(0, 0, vs[15][2])]) # V33 - V35
            vs.extend([vs[22], vs[23], vec(vs[22][0], 0, 0)]) # V36 - V38
            vs.extend([vs[29], vs[30], vec(0, vs[29][1], 0)]) # V39 - V41
            # add isosceles triangles:
            if this.tri_alt:
                v = vs[13]
                vs.extend([vs[13], vs[14], vec(v[0], -v[1], v[2])]) # V42 - V44
                v = vs[20]
                vs.extend([vs[20], vs[21], vec(v[0], v[1], -v[2])]) # V45 - V47
                v = vs[27]
                vs.extend([vs[27], vs[28], vec(-v[0], v[1], v[2])]) # V48 - V50
            else:
                vs.extend([vs[13], vs[14], vs[24]]) # V42 - V44
                vs.extend([vs[20], vs[21], vs[31]]) # V45 - V47
                vs.extend([vs[27], vs[28], vs[17]]) # V48 - V50

            # normals for the equilateral triangles:
            for i in range(3):
                ns.append(vs[0])  # N33 - N35
            for i in range(3):
                ns.append(vs[4])  # N36 - N38
            for i in range(3):
                ns.append(vs[8]) # N39 - N41
            # normals for the isosceles triangles:
            # N42 - N44, N45 - N47 and N48 - N50
            for i in range(3):
                o = 42 + 3*i
                IsoscelesTriangleN = geom_3d.Triangle(
                    vs[o],
                    vs[o+1],
                    vs[o+2]
                ).normal()
                ns.extend([IsoscelesTriangleN, IsoscelesTriangleN, IsoscelesTriangleN])

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
            if this.add_extra_edge:
                if this.tri_alt:
                    xtraEs = [42, 44, 45, 47, 48, 50]
                else:
                    xtraEs = [43, 44, 46, 47, 49, 50]

        this.base_shape.vertex_props = {'vs': vs, 'ns': ns}
        fs = []
        es = []
        colIds = []
        if this.show_kite:
            fs.extend(this.kiteFs)
            es.extend(this.kiteEs)
            colIds.extend(this.kiteColIds)
        if this.show_hepta:
            fs.extend(this.heptFs)
            es.extend(this.heptEs)
            colIds.extend(this.heptColIds)
        if this.show_extra:
            fs.extend(xtraFs)
            es.extend(xtraEs)
            colIds.extend(this.xtraColIds)
        this.base_shape.es = es
        this.setBaseFaceProperties(fs=fs, colors=(this.face_col, colIds))

    def to_postscript(this,
            face_indices=[],
            scaling=1,
            precision=7,
            margin=1.0e-10,
        ):
        if face_indices == []:
            offset = 0
            if this.show_kite:
                face_indices.append(offset)
                offset += len(this.kiteFs)
            if this.show_hepta:
                face_indices.append(offset)
                offset += len(this.heptFs)
            if this.show_extra:
                face_indices.append(offset)
                if this.alt_hept_pos:
                    face_indices.append(offset+1)
                else:
                    face_indices.append(offset+3)
        return super().to_postscript(face_indices, scaling, precision, margin)

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
        this.set_kite_angle_domain(2.4, 115.24)
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
            this.minMaxAngles[0]['a'] = this.get_angle_val(
                    this.kite_angle_gui.GetValue()
                )
            #TODO save other settings? Make a functions for this.
        this.minMaxPreviousIndex = index
        this.kite_angle_gui.SetValue(this.get_slider_val(angle))
        this.shape.angle = angle

        this.view_kite_gui.SetValue(True)
        this.view_hept_gui.SetValue(True)
        this.add_extra_face_gui.SetValue(False)
        this.alt_hept_pos_gui.SetValue(False)
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
            this.prefHeptSpecAngles[0]['a'] = this.get_angle_val(
                    this.kite_angle_gui.GetValue()
                )
            #TODO save other settings? Make a functions for this.
        this.prefHeptSpecPreviousIndex = index
        this.kite_angle_gui.SetValue(this.get_slider_val(angle))
        this.shape.angle = angle

        this.view_hept_gui.SetValue(True)
        this.alt_hept_pos_gui.SetValue(False)
        if 't' in angleData:
            this.view_kite_gui.SetValue(False)
            this.add_extra_face_gui.SetValue(True)
            this.tri_alt_gui.SetValue(angleData['t'])
        if 'e' in angleData:
            this.add_extra_edge_gui.SetValue(angleData['e'])
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
            this.altHeptSpecAngles[0]['a'] = this.get_angle_val(
                    this.kite_angle_gui.GetValue()
                )
            #TODO save other settings? Make a functions for this.
        this.altHeptSpecPreviousIndex = index
        this.kite_angle_gui.SetValue(this.get_slider_val(angle))
        this.shape.angle = angle

        this.view_hept_gui.SetValue(True)
        this.alt_hept_pos_gui.SetValue(True)
        if 't' in angleData:
            this.view_kite_gui.SetValue(False)
            this.add_extra_face_gui.SetValue(True)
            this.tri_alt_gui.SetValue(angleData['t'])
        if 'e' in angleData:
            this.add_extra_edge_gui.SetValue(angleData['e'])
        this.on_view_settings_chk(this)
        if index != 0:
            if this.minMaxPosGui.GetSelection() != 0:
                this.minMaxPosGui.SetSelection(0)
            if this.prefHeptSpecPosGui.GetSelection() != 0:
                this.prefHeptSpecPosGui.SetSelection(0)

class Scene(geom_3d.Scene):
    def __init__(this, parent, canvas):
        geom_3d.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
