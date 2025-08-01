#!/usr/bin/env python
#
# Copyright (C) 2010-2024 Marcel Tunnissen
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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# -------------------------------------------------------------------

import wx
import math

from orbitit import geom_3d, geomtypes, heptagons
from orbitit.geomtypes import HalfTurn3 as HalfTurn
from orbitit.geomtypes import Rot3 as Rot

vec = lambda x, y, z: geomtypes.Vec3([x, y, z])

TITLE = 'Equilateral Heptagons from Great Icosahedron - Great Stellated Dodecahedron'

V3   = math.sqrt(3)
V5   = math.sqrt(5)
tau  = (1.0 + V5)/2
tau2 = tau + 1.0
Dtau2= (3 + V5)
dtau = 1.0/tau
w    = 1
Ca   = 1.0/V3
H0   = 2.0*Ca/tau2
Rl   = vec(1.0, -Ca, H0)

halfTurn = HalfTurn(axis=geomtypes.UX)

class Shape(heptagons.EqlHeptagonShape):
    def __init__(this, *args, **kwargs):
        t1 = Rot(angle=geomtypes.turn(0.2), axis=vec(0, -Dtau2, 1))
        t2 = Rot(angle=geomtypes.turn(0.4), axis=vec(0, -Dtau2, 1))
        t3 = Rot(angle=geomtypes.turn(0.6), axis=vec(0, -Dtau2, 1))
        t4 = Rot(angle=geomtypes.turn(0.8), axis=vec(0, -Dtau2, 1))
        h0 = HalfTurn(axis=vec(0, -1, tau2))
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
            name='EglHeptA5xI_GI'
        )
        this.initArrs()
        this.height = H0

    def set_height(this, h):
        this._angle = geom_3d.RAD2DEG * math.atan((h - H0)/Ca)
        super().set_height(h)

    def set_angle(this, a):
        this._height = Ca * math.tan(a*geom_3d.DEG2RAD) + H0
        super().set_angle(a)

    def set_vs(this):
        St = this.height / (Dtau2*V3*this.height - 3)
        #                  0
        #           __..--'-_
        #      3 -''    .    _"- 1
        #         \       _-'
        #          \   _-'
        #           \-'
        #           2
        #
        #    z    y
        #     ^ 7\
        #     |/
        #     ---> x
        #
        #
        # The kite above is a 5th of the top face of dodecahedron
        # standing on 1 face, 2 is a vertex, 1 and 3, centres of two edges
        # and 0 a face centre.
        #
        vs = [
            vec(0.0, 0.0, this.height),  # 0
            Rl,
            vec(0.0, -Dtau2*St, St),
            vec(-Rl[0],  Rl[1],  Rl[2]),  # 3
        ]

        # add heptagons
        H = HalfTurn(axis=vs[3])
        this.error_msg = ''
        if not this.alt_hept_pos:
            ns = vs
            heptN = heptagons.kite_to_hept(vs[3], vs[0], vs[1], vs[2])
            if not heptN:
              this.error_msg = 'No valid equilateral heptagon for this position'
              return
            Mr = Rot(axis = geomtypes.Vec3(vs[2]), angle = geomtypes.turn(0.2))

            # p is a corner of the pentagon inside the pentagram
            # p is rotated 1/5th turn to form a triangle
            # together with 2 corners of the pentagram:
            # 5 of these triangles will cover the pentagram.
            # this is easier than finding the centre of the pentagram.
            v3 = heptN[0][3]
            v4 = heptN[0][4]
            p = v3 + (v4 - v3)/tau
            v = Mr*p
            if this.tri_alt:
                vt = heptN[0][6]
                xtraEdgeIndex = 15
            else:
                vt = heptN[0][5]
                xtraEdgeIndex = 14
            # A part that will form the regular pentagrams (with overlaps).
            RegularTrianglePartV = [
                        heptN[0][3],
                        heptN[0][4],
                        vec(v[0], v[1], v[2]),
                    ]
            RegularTrianglePartN = vs[2]
            # vt is the vertex that will be projected by a half turn on the
            # third vertex of the isosceles triangle.
            IsoscelesTriangleV = [
                        heptN[0][5],
                        heptN[0][6],
                        vt
                    ]
        else:
            heptN = heptagons.kite_to_hept(vs[1], vs[2], vs[3], vs[0])
            if not heptN:
              this.error_msg = 'No valid equilateral heptagon for this position'
              return
            if this.tri_alt:
                vt = heptN[0][1]
                xtraEdgeIndex = 14
            else:
                vt = heptN[0][2]
                xtraEdgeIndex = 15
            # One third of regular triangle.
            RegularTrianglePartV = [
                        heptN[0][3],
                        heptN[0][4],
                        vec(0, 0, heptN[0][3][2]),
                    ]
            RegularTrianglePartN = RegularTrianglePartV[2]
            # vt is the vertex that will be projected by a half turn on the
            # third vertex of the isosceles triangle.
            IsoscelesTriangleV = [
                        heptN[0][1],
                        heptN[0][2],
                        vt
                    ]
        if not heptN:
            this.error_msg = 'No valid equilateral heptagon for this position'
            return
        else:
            this.error_msg = ''
        vt = H * vt
        # rotate vt by a half turn, IsoscelesTriangleV NOT auto updated.
        IsoscelesTriangleV[2] = vt
        vs.extend(heptN[0]) # V4 - V10, the heptagon
        vs.extend(RegularTrianglePartV) # V11 - V13
        vs.extend(IsoscelesTriangleV) # V14 - V16
        ns = [heptN[1] for i in range(11)]
        ns.extend([RegularTrianglePartN for i in range(3)])
        IsoscelesTriangleN = geom_3d.Triangle(
                IsoscelesTriangleV[0],
                IsoscelesTriangleV[1],
                IsoscelesTriangleV[2]
            ).normal
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
        # p: alternative heptagon position
        # if a field is not specified: don't care.
        this.specialSolidAngles = [
            {'a':   0.0,               's': 'None'},
            {'a':   0.0,               's': 'Great Icosahedron', 'p': False},
            {'a':  79.187683036428297, 's': 'Great Stellated Dodecahedron', 'p': True},
            {'a':  20.905157447889302, 's': 'A Stellation of the Rhombic Triacontahedron (IJ)'},
            {'a':  41.810314895778596, 's': 'A Stellation of the Icosahedron (C)'}
        ]
        this.prefHeptSpecAngles = [
            {'a':   0.0,                's': 'None'},
            {'a':  -7.362284243348462, 's': 'Minimum Angle', 't': True, 'e': True},
            {'a':  53.175309408014598, 's': 'Maximum Angle', 't': False, 'e': True},
            {'a':  14.444715180025225, 's': 'Equilateral Triangles', 't': True, 'e': True},
            {'a':  17.084786013831049, 's': 'Equilateral Triangles', 't': False, 'e': True},
            # no rhombi
        ]

        this.altHeptSpecAngles = [
            {'a':   0.0,               's': 'None'},
            {'a':   6.837020288942317, 's': 'Minimum Angle', 't': False, 'e': True},
            {'a':  82.321770249837471, 's': 'Maximum Angle', 't': True, 'e': True},
            {'a':  35.179849014382299, 's': 'Equilateral Triangles', 't': False, 'e': True},
            {'a':  61.551581272227054, 's': 'Equilateral Triangles', 't': True, 'e': True},
        ]
        this.set_kite_angle_domain(
                this.prefHeptSpecAngles[1]['a'],
                this.altHeptSpecAngles[2]['a']
            )
        kwargs['title'] = TITLE
        heptagons.EqlHeptagonCtrlWin.__init__(this,
            shape, canvas, (332, 638),
            *args, **kwargs
        )
        this.shape.update_view_opt(alt_hept_pos=True)
        this.alt_hept_pos_gui.SetValue(True)

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
            this.onSpecialSolidPos,
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

        # TODO port to new shape framework:
        #this.transparencyGui = wx.Slider(parentFrame,
        #        value = this.Opaqueness2Transparency(this.shape.opaqueness),
        #        minValue = 0,
        #        maxValue = 100,
        #        style = wx.SL_HORIZONTAL
        #    )
        #this.transparencyGui.Bind(wx.EVT_SLIDER, this.onOpaquenessAdjust)
        #this.transparencyBox = wx.StaticBox(parentFrame, label = 'Transparency of Heptagons (Experimental)')
        #this.transparencySizer = wx.StaticBoxSizer(this.transparencyBox, wx.HORIZONTAL)
        #this.transparencySizer.Add(this.transparencyGui, 1, wx.EXPAND)

        specPosSizer = wx.BoxSizer(wx.HORIZONTAL)
        specPosSizer.Add(this.prefHeptSpecPosGui, 1, wx.EXPAND)
        specPosSizer.Add(this.altHeptSpecPosGui,  1, wx.EXPAND)

        #parentSizer.Add(this.transparencySizer,  .1, wx.EXPAND)
        parentSizer.Add(this.specialSolidPosGui, 12, wx.EXPAND)
        parentSizer.Add(specPosSizer,      12, wx.EXPAND)

    def onSpecialSolidPos(this, event = None):
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
        this.add_extra_face_gui.SetValue(False)
        if 'p' in angleData:
            this.alt_hept_pos_gui.SetValue(angleData['p'])
            this.view_hept_gui.SetValue(True)
        else:
            this.view_hept_gui.SetValue(False)
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

    def Opaqueness2Transparency(this, opaqueness):
        return (1 - opaqueness) * 100

    def onOpaquenessAdjust(this, event):
        transparency = float(this.transparencyGui.GetValue())
        this.shape.update_view_opt(opaqueness=1-transparency/100)

class Scene(geom_3d.Scene):
    def __init__(this, parent, canvas):
        geom_3d.Scene.__init__(this, Shape, CtrlWin, parent, canvas)


