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

TITLE = 'Equilateral Heptagons from Dodecahedron - Icosahedron'

V5   = math.sqrt(5)
tau  = (1.0 + V5)/2
tau2 = tau + 1.0
w    = math.sqrt(tau2 + 1.0)/2

atanH0d2 = geom_3d.Rad2Deg * math.atan(tau2/2)
halfTurn = HalfTurn(axis=geomtypes.UY)

class Shape(heptagons.EqlHeptagonShape):
    def __init__(this, *args, **kwargs):
        t1 = Rot(angle=geomtypes.turn(0.2), axis=geomtypes.UZ)
        t2 = Rot(angle=geomtypes.turn(0.4), axis=geomtypes.UZ)
        t3 = Rot(angle=geomtypes.turn(0.6), axis=geomtypes.UZ)
        t4 = Rot(angle=geomtypes.turn(0.8), axis=geomtypes.UZ)
        h0 = HalfTurn(axis=vec(1, 0, tau))
        super().__init__(
            base_isometries=[
                    geomtypes.E, t1, t2, t3, t4,
                    h0, h0*t1, h0*t2, h0*t3, h0*t4,
                    t1*h0, t1*h0*t1, t1*h0*t2, t1*h0*t3, t1*h0*t4,
                    t2*h0, t2*h0*t1, t2*h0*t2, t2*h0*t3, t2*h0*t4,
                    t3*h0, t3*h0*t1, t3*h0*t2, t3*h0*t3, t3*h0*t4,
                    t4*h0, t4*h0*t1, t4*h0*t2, t4*h0*t3, t4*h0*t4
                ],
            # Use a half turn here to prevent edges to be drawn twice.
            extra_isometry=halfTurn,
            name='EglHeptA5xI'
        )
        this.initArrs()
        this.height = 2.618

    def set_height(this, h):
        this._angle = geom_3d.Rad2Deg * math.atan((h - tau2)/w) #+ atanH0d2
        super().set_height(h)

    def set_angle(self, a):
        self._height = w * math.tan(a*geom_3d.Deg2Rad) + tau2
        super().set_angle(a)

    def set_vs(this):
        St = this.height / (4 - tau2 - (4 * this.height / tau2))
        #    z
        #     ^
        #     |
        #     ---> y
        #    /
        #   V_
        #  x
        #                  2
        #           __..--'-_
        #      1 -''    .    _"- 3
        #         \       _-'
        #          \   _-'
        #           \-'
        #           0
        #
        # The kite above is a 5th of the top face of dodecahedron
        # standing on 1 face, 2 is a vertex, 1 and 3, centres of two edges
        # and 0 a face centre.
        #
        vs = [
            vec(0.0, 0.0, this.height),  # 0
            vec(-tau2/2, -w, tau2),
            vec(2.0*St, 0.0, -tau2*St),
            vec(-tau2/2, w, tau2),  # 3
        ]

        # add heptagons
        ns = vs
        if this.alt_hept_pos:
            heptN = heptagons.kite_to_hept(vs[3], vs[0], vs[1], vs[2])
            if heptN == None: return
            Mr = Rot(angle = geomtypes.THIRD_TURN, axis = vs[2])

            v = Mr*heptN[0][4]
            if this.tri_alt:
                vt = heptN[0][6]
                xtraEdgeIndex = 15
            else:
                vt = heptN[0][5]
                xtraEdgeIndex = 14
            # One third of regular triangle.
            RegularTrianglePartV = [
                        heptN[0][3],
                        heptN[0][4],
                        vec(v[0], v[1], v[2]),
                    ]
            # vt is the vertex that will be projected by a half turn on the
            # third vertex of the isosceles triangle.
            IsoscelesTriangleV = [
                        heptN[0][5],
                        heptN[0][6],
                        vt
                    ]
        else:
            heptN = heptagons.kite_to_hept(vs[1], vs[2], vs[3], vs[0])
            if heptN == None: return
            if this.tri_alt:
                vt = heptN[0][1]
                xtraEdgeIndex = 14
            else:
                vt = heptN[0][2]
                xtraEdgeIndex = 15
            # One third of regular pentagon.
            RegularTrianglePartV = [
                        heptN[0][3],
                        heptN[0][4],
                        vec(0, 0, heptN[0][3][2]),
                    ]
            # vt is the vertex that will be projected by a half turn on the
            # third vertex of the isosceles triangle.
            IsoscelesTriangleV = [
                        heptN[0][1],
                        heptN[0][2],
                        vt
                    ]
        if heptN == None:
            this.error_msg = 'No valid equilateral heptagon for this position'
            return
        else:
            this.error_msg = ''
        h = HalfTurn(axis=vs[3])
        vt = h * vt
        IsoscelesTriangleV[2] = vt
        vs.extend(heptN[0]) # V4 - V10
        vs.extend(RegularTrianglePartV) # V11 - V13
        vs.extend(IsoscelesTriangleV) # V14 - V16
        ns = [heptN[1] for i in range(11)]
        RegularTrianglePartN = RegularTrianglePartV[2]
        ns.extend([RegularTrianglePartN for i in range(3)])
        IsoscelesTriangleN = geom_3d.Triangle(
                IsoscelesTriangleV[0],
                IsoscelesTriangleV[1],
                IsoscelesTriangleV[2]
            ).normal()
        ns.extend([IsoscelesTriangleN for i in range(3)])
        this.xtraEs = []
        if this.add_extra_edge:
            this.xtraEs = [xtraEdgeIndex, 16]

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
            fs.extend(this.xtraFs)
            es.extend(this.xtraEs)
            colIds.extend(this.xtraColIds)
        this.base_shape.es = es
        this.base_fs_props = {'fs': fs, 'colors': (this.face_col, colIds)}
        this.base_vs = vs

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
                face_indices.append(offset+1)
        return super().to_postscript(face_indices, scaling, precision, margin)

    def initArrs(this):
        this.kiteFs = [[3, 2, 1, 0]]
        this.kiteColIds = [0 for i in range(1)]
        # TODO probably only half is needed, e.g. only right (left) edges
        this.kiteEs = [0, 1, 1, 2, 2, 3, 3, 0]
        this.heptFs = [[10, 9, 8, 7, 6, 5, 4]]
        this.heptColIds = [1 for i in range(1)]
        this.heptEs = [
                4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 4
            ]
        this.xtraFs = [[11, 12, 13], [14, 15, 16]]
        this.xtraColIds = [2 for i in range(2)]
        this.xtraEs = []

    def getStatusStr(this):
        stdStr = super().getStatusStr()
        if this.show_extra and this.add_extra_edge and len(this.xtraEs) == 2:
            if this.update_vs:
                this.set_vs()
            # reference vector, a side of the heptagon:
            vs = this.vs[0]
            r0 = vs[4]
            r1 = vs[5]
            #r2 = vs[6]
            r = r0 - r1
            # the extra edge
            v0 = vs[this.xtraEs[0]]
            v1 = vs[this.xtraEs[1]]
            v = v0 - v1
            return '%s, extra edge length: %02.2f' % (stdStr, v.norm()/r.norm())
        # TODO: if not add_extra_edge: print diff in norms (or both edge lengths)
        else:
            return stdStr
    # GUI PART

class CtrlWin(heptagons.EqlHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
        # a: angle
        # s: string text in GUI
        # t: triangle alternative value
        # e: add extra edge
        # if a field is not specified: don't care.
        this.specialSolidAngles = [
            {'a':   0.0,               's': 'None'},
            {'a':   0.0,               's': 'Dodecahedron'},
            {'a':  46.436999400426913, 's': 'Icosahedron'},
            {'a': -40.2163996884,      's': 'Rhombic Hexecontahedron'},
            {'a':  67.1317327636,      's': 'Medial Rhombic Triacontahedron'},
            {'a':  82.26,              's': 'Medial Triambic Icosahedron'}
        ]
        this.prefHeptSpecAngles = [
            {'a':   0.0,                's': 'None'},
            {'a': -41.290922668655959, 's': 'Minimum Angle', 't': False, 'e': False},
            {'a':  81.327488000488543, 's': 'Maximum Angle', 't': True, 'e': False},
            {'a':  53.089011204927090, 's': 'Equilateral Triangles', 't': True, 'e': True},
            {'a':  -2.544267522629735, 's': 'Equilateral Triangles', 't': False, 'e': True},
            {'a':  30.063178288003261, 's': 'Rhombi', 't': True, 'e': False},
        ]

        this.altHeptSpecAngles = [
            {'a':   0.0,               's': 'None'},
            {'a': -60.96845,           's': 'Minimum Angle', 't': True, 'e': True},
            {'a': -36.984797756909167, 's': 'Maximum Angle', 't': True, 'e': False},
            {'a': -41.536138658834069, 's': 'Equilateral Triangles', 't': True, 'e': True},
            #{'a':  14.020488654174214, 's': 'Equilateral Triangles', 't': False, 'e': True},
        ]
        this.set_kite_angle_domain(-60.96845, 82.26)
        kwargs['title'] = TITLE
        heptagons.EqlHeptagonCtrlWin.__init__(this,
            shape, canvas, (332, 650),
            *args, **kwargs
        )

    def add_specials(this, parentFrame, parentSizer):
        labelLst = []
        for i in range(len(this.specialSolidAngles)):
            labelLst.append(this.specialSolidAngles[i]['s'])
        this.specialSolidPosGui = wx.RadioBox(parentFrame,
                    label = 'Special Solids Positions',
                    style = wx.RA_VERTICAL,
                    choices = labelLst
                )
        parentFrame.Bind(
            wx.EVT_RADIOBOX,
            this.onSpecialSolidsPos,
            id = this.specialSolidPosGui.GetId()
        )
        this.specialSolidPreviousIndex = 0

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
                    # 20080614: the spaces fixes an outline error on Dapper
                    label = 'Alternative Heptagon     ',
                    style = wx.RA_VERTICAL,
                    choices = labelLst
                )
        parentFrame.Bind(wx.EVT_RADIOBOX, this.onAltHeptSpecPos, id = this.altHeptSpecPosGui.GetId())
        this.altHeptSpecPreviousIndex = 0

        specPosSizer = wx.BoxSizer(wx.HORIZONTAL)
        specPosSizer.Add(this.prefHeptSpecPosGui, 1, wx.EXPAND)
        specPosSizer.Add(this.altHeptSpecPosGui,  1, wx.EXPAND)

        parentSizer.Add(this.specialSolidPosGui, 14, wx.EXPAND)
        parentSizer.Add(specPosSizer,            14, wx.EXPAND)

    def onSpecialSolidsPos(this, event = None):
        index = this.specialSolidPosGui.GetSelection()
        angleData = this.specialSolidAngles[index]
        angle = angleData['a']
        if index != 0 and this.specialSolidPreviousIndex == 0:
            # save angle in None
            this.specialSolidAngles[0]['a'] = this.get_angle_val(
                    this.kite_angle_gui.GetValue()
                )
            #TODO save other settings? Make a functions for this.
        this.specialSolidPreviousIndex = index
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
            if this.specialSolidPosGui.GetSelection() != 0:
                this.specialSolidPosGui.SetSelection(0)
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
            if this.specialSolidPosGui.GetSelection() != 0:
                this.specialSolidPosGui.SetSelection(0)
            if this.prefHeptSpecPosGui.GetSelection() != 0:
                this.prefHeptSpecPosGui.SetSelection(0)

class Scene(geom_3d.Scene):
    def __init__(this, parent, canvas):
        geom_3d.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
