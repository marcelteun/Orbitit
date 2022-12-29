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

TITLE = 'Equilateral Heptagons Tetrahedron'

vec = lambda x, y, z: geomtypes.Vec3([x, y, z])

V2  = math.sqrt(2)
hV2 = 1.0/V2
tV3 = 1.0/math.sqrt(3)

class Shape(heptagons.EqlHeptagonShape):
    def __init__(this):
        super().__init__(
            base_isometries=[
                    geomtypes.E,
                    geomtypes.HX,
                    geomtypes.HY,
                    geomtypes.HZ
                ],
            name='EglHeptS4A4'
        )
        this.initArrs()
        this.height = 1.0

    def set_height(self, h):
        self._angle = geom_3d.Rad2Deg * math.atan2(V2 * (1 - h), 4*h - 1)
        super().set_height(h)

    def set_angle(self, a):
        tanA = math.tan(a*geom_3d.Deg2Rad)
        self._height = (V2 + tanA) / (V2 + 4*tanA)
        super().set_angle(a)

    def set_vs(this):
        St = this.height / (4*this.height - 1)
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
            # There are vertices with more than one index, because the normals
            # will differ.
            #
            #          '-,
            #         /   '-,
            #        /       -.2
            #        |  5   -' \ 1, 11
            #       /   3.-' 0  '-
            #       |   /   4 8 __'-10
            #      / ,-'  __--""
            #     /,=---""  7
            #    6          9
            #
            # For tetrahedral position: 1, 3, and 5 are on the vertices of a
            # cube and 2, 4, 6, are on the face centres of that cube
            #
            vs = [
                vec( St, St, -St),  # 0
                vec( 0.0, 1.0, 0.0),
                vec( this.height, this.height,  this.height),
                vec( 1.0, 0.0, 0.0),  # 3

                vec( St, St, -St),  # 4
                vec( 1.0, 0.0, 0.0),
                vec( this.height, -this.height, -this.height),
                vec( 0.0, 0.0, -1.0),  # 7

                vec( St, St, -St),  # 8
                vec( 0.0, 0.0, -1.0),
                vec(-this.height, this.height, -this.height),
                vec( 0.0, 1.0, 0.0)  # 11
            ]
            # Normals are set below, after calculating the heptagons
            #this.Ns = this.NsAlt
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
            # There are vertices with more than one index, because the normals
            # will differ.
            #
            #                    6
            #              9    /
            #          '-, 7   V_
            #         /   '-,
            #        /       -.0, 4, 8
            #        | 10   -' \ 3, 5
            #       /11,1.-'    '-
            #       |   /    2  __'-
            #      / ,-'  __--""
            #     /,=---""
            #
            #
            # For tetrahedral position: 1, 3, and 5 are on the vertices of a
            # cube and 2, 4, 6, are on the face centres of that cube
            #
            vs = [
                vec(this.height, this.height, this.height),  # 0
                vec(1.0, 0.0, 0.0),
                vec(St, St, -St),
                vec(0.0, 1.0, 0.0),  # 3

                vec(this.height, this.height, this.height),  # 4
                vec(0.0, 1.0, 0.0),
                vec(-St, St, St),
                vec(0.0, 0.0, 1.0),  # 7

                vec(this.height, this.height, this.height),  # 8
                vec(0.0, 0.0, 1.0),
                vec(St, -St, St),
                vec(1.0, 0.0, 0.0)   # 11
            ]

        # add heptagons
        heptN = heptagons.kite_to_hept(vs[3], vs[2], vs[1], vs[0])
        if heptN == None:
          this.error_msg = 'No valid equilateral heptagon for this position'
          return
        else:
          this.error_msg = ''
        vs.extend(heptN[0]) # V12 - V18
        Ns = list(range(33))
        for i in range(4):
            Ns[i] = heptN[1]
        for i in range(12, 19):
            Ns[i] = heptN[1]
        heptN = heptagons.kite_to_hept(vs[7], vs[6], vs[5], vs[4])
        vs.extend(heptN[0]) # V19 - V25
        for i in range(4, 8):
            Ns[i] = heptN[1]
        for i in range(19, 26):
            Ns[i] = heptN[1]
        heptN = heptagons.kite_to_hept(vs[11], vs[10], vs[9], vs[8])
        vs.extend(heptN[0]) # V26 - V32
        for i in range(8, 12):
            Ns[i] = heptN[1]
        for i in range(26, 33):
            Ns[i] = heptN[1]

        # add equilateral triangles:
        vs.extend([vs[15], vs[22], vs[29]])         # V33 - V35
        # add isosceles triangles:
        this.xtraEs = []
        if this.tri_alt:
            vs.extend([vs[13], vs[14], vs[32]]) # V36 - V38
            vs.extend([vs[20], vs[21], vs[18]]) # V39 - V41
            vs.extend([vs[27], vs[28], vs[25]]) # V42 - V44
            if this.add_extra_edge:
                this.xtraEs = [36, 38, 39, 41, 42, 44]
        else:
            vs.extend([vs[13], vs[14], vs[14]]) # V36 - V38
            vs.extend([vs[20], vs[21], vs[21]]) # V39 - V41
            vs.extend([vs[27], vs[28], vs[28]]) # V42 - V44
            if this.alt_hept_pos:
                v = vs[38]
                vs[38] = vec(-v[0],  v[1], -v[2])    # HY * V9
                v = vs[41]
                vs[41] = vec( v[0], -v[1], -v[2])    # HX * V23
            else:
                v = vs[38]
                vs[38] = vec( v[0], -v[1], -v[2])    # HX * V9
                v = vs[41]
                vs[41] = vec(-v[0],  v[1], -v[2])    # HY * V23
            v = vs[44]
            vs[44] = vec(-v[0], -v[1],  v[2])    # HZ * V16
            if this.add_extra_edge:
                this.xtraEs = [37, 38, 40, 41, 43, 44]

        # normal of equilateral triangle
        for i in range(3):
            Ns.append(vs[0])
        # normal of isosceles triangles
        for i in range(3):
            o = 36 + 3*i
            IsoscelesTriangleN = geom_3d.Triangle(
                vs[o],
                vs[o+1],
                vs[o+2]
            ).normal()
            Ns.extend([IsoscelesTriangleN, IsoscelesTriangleN, IsoscelesTriangleN])

        this.xtraFs = [
                [33, 34, 35],
                [36, 37, 38],
                [39, 40, 41],
                [42, 43, 44]
            ]

        this.setBaseVertexProperties(vs=vs, Ns=Ns)
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
        this.setBaseEdgeProperties(es=es)
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
        this.xtraFs = [
            ]
        this.xtraColIds = [2 for i in range(4)]
        this.xtraEs = [
            ]
        #this.NsAlt = [
        #        [ tV3,  tV3, -tV3],
        #        [ tV3,  tV3,  tV3],
        #        [ 0.0,  1.0,  0.0],
        #        [-tV3,  tV3, -tV3],
        #        [ 0.0,  0.0, -1.0],
        #        [ tV3, -tV3, -tV3],
        #        [ 1.0,  0.0,  0.0]
        #    ]
        #this.NsPref = [
        #        [ tV3,  tV3,  tV3],
        #        [ tV3,  tV3, -tV3],
        #        [ 1.0,  0.0,  0.0],
        #        [ tV3, -tV3,  tV3],
        #        [ 0.0,  0.0,  1.0],
        #        [-tV3,  tV3,  tV3],
        #        [ 0.0,  1.0,  0.0]
        #    ]
        # init heptagons normal, will be set in set_vs:
        #for i in range(21):
        #    this.NsAlt.append([0, 0, 1])
        #    this.NsPref.append([0, 0, 1])
        ## set xtra normals for regular faces
        #for i in range(3):
        #    this.NsAlt.append(this.NsAlt[0])
        #    this.NsPref.append(this.NsPref[0])
        ## init xtra normals for regular faces
        #for i in range(12):
        #    this.NsAlt.append([0, 0, 1])
        #    this.NsPref.append([0, 0, 1])

    # GUI PART

class CtrlWin(heptagons.EqlHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
        # a: angle
        # s: string text in GUI
        # t: triangle alternative value
        # e: add extra edge
        # if a field is not specified: don't care.
        this.specialAngles = [
            {'a':  0.0,                's': 'None'},
            {'a':  0.0,                's': 'tetrahedron 0'},
            {'a':  70.528779365509308, 's': 'tetrahedron 1'},
            {'a': -13.407749697962847, 's': 'Minimum Angle', 't': True, 'e': False},
            {'a':  57.606581098355008, 's': 'Maximum Angle', 't': True, 'e': False},
            {'a':   7.136412252550596, 's': 'Equilateral Triangles', 't': True,'e': True},
            {'a':  24.602778241392063, 's': 'Equilateral Triangles', 't': False,'e': True},
            {'a':  45.464238739313160, 's': 'Three Triangles in One Plane', 't': True,'e': True},
        ]
        this.set_kite_angle_domain(this.specialAngles[3]['a'], this.specialAngles[2]['a'])
        kwargs['title'] = TITLE
        heptagons.EqlHeptagonCtrlWin.__init__(this,
            shape, canvas, (338, 570),
            *args, **kwargs
        )

    def add_specials(this, parentFrame, parentSizer):
        labelLst = []
        for i in range(len(this.specialAngles)):
            labelLst.append(this.specialAngles[i]['s'])
        this.specialPosGui = wx.RadioBox(parentFrame,
                    label = 'Special Positions',
                    style = wx.RA_VERTICAL,
                    choices = labelLst
                )
        parentFrame.Bind(wx.EVT_RADIOBOX, this.onSpecialPos)
        this.previousIndex = 0

        parentSizer.Add(this.specialPosGui, 18, wx.EXPAND)

    def onSpecialPos(this, event = None):
        index = this.specialPosGui.GetSelection()
        angleData = this.specialAngles[index]
        angle = angleData['a']
        if index != 0 and this.previousIndex == 0:
            # save angle in None
            this.specialAngles[0]['a'] = this.get_angle_val(
                    this.kite_angle_gui.GetValue()
                )
            #TODO save other settings? Make a functions for this.
        this.previousIndex = index
        this.kite_angle_gui.SetValue(this.get_slider_val(angle))
        this.shape.angle = angle

        this.view_hept_gui.SetValue(True)
        this.alt_hept_pos_gui.SetValue(False)
        if 't' in angleData:
            this.view_kite_gui.SetValue(False)
            this.add_extra_face_gui.SetValue(True)
            this.tri_alt_gui.SetValue(angleData['t'])
        else:
            this.view_kite_gui.SetValue(True)
            this.add_extra_face_gui.SetValue(False)
        if 'e' in angleData:
            this.add_extra_edge_gui.SetValue(angleData['e'])
        this.on_view_settings_chk(this)


class Scene(geom_3d.Scene):
    def __init__(this, parent, canvas):
        geom_3d.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
