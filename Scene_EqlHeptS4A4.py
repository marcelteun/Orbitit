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
import Heptagons
import geomtypes
import Geom3D

TITLE = 'Equilateral Heptagons Tetrahedron'

vec = lambda x, y, z: geomtypes.Vec3([x, y, z])

V2  = math.sqrt(2)
hV2 = 1.0/V2
tV3 = 1.0/math.sqrt(3)

class Shape(Heptagons.EqlHeptagonShape):
    def __init__(this):
        Heptagons.EqlHeptagonShape.__init__(this,
            directIsometries = [
                    geomtypes.E,
                    geomtypes.HX,
                    geomtypes.HY,
                    geomtypes.HZ
                ],
            name = 'EglHeptS4A4'
        )
        this.initArrs()
        this.setH(1.0)
        this.setViewSettings(edgeR = 0.02, vertexR = 0.04)

    def setH(this, h):
        this.angle = Geom3D.Rad2Deg * math.atan2(V2 * (1 - h), 4*h - 1)
        Heptagons.EqlHeptagonShape.setH(this, h)

    def setAngle(this, a):
        tanA     = math.tan(a*Geom3D.Deg2Rad)
        this.h     = (V2 + tanA) / (V2 + 4*tanA)
        this.setH(this.h)
        Heptagons.EqlHeptagonShape.setAngle(this, a)

    def setV(this):
        # input this.h
        St = this.h / (4*this.h - 1)
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
            Vs = [
                    vec( St,      St,     -St),        # 0
                    vec( 0.0,     1.0,     0.0),
                    vec( this.h,  this.h,  this.h),
                    vec( 1.0,     0.0,     0.0),       # 3

                    vec( St,      St,     -St),        # 4
                    vec( 1.0,     0.0,     0.0),
                    vec( this.h, -this.h, -this.h),
                    vec( 0.0,     0.0,    -1.0),       # 7

                    vec( St,      St,     -St),        # 8
                    vec( 0.0,     0.0,    -1.0),
                    vec(-this.h,  this.h, -this.h),
                    vec( 0.0,     1.0,     0.0)        # 11
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
            Vs = [
                    vec( this.h,  this.h,  this.h),    # 0
                    vec( 1.0,     0.0,     0.0),
                    vec( St,      St,     -St),
                    vec( 0.0,     1.0,     0.0),       # 3

                    vec( this.h,  this.h,  this.h),    # 4
                    vec( 0.0,     1.0,     0.0),
                    vec(-St,      St,      St),
                    vec( 0.0,     0.0,     1.0),       # 7

                    vec( this.h,  this.h,  this.h),    # 8
                    vec( 0.0,     0.0,     1.0),
                    vec( St,     -St,      St),
                    vec( 1.0,     0.0,     0.0)        # 11
                ]
            # Normals are set below, after calculating the heptagons
            #this.Ns = this.NsPref

        # add heptagons
        heptN = Heptagons.Kite2Hept(Vs[3], Vs[2], Vs[1], Vs[0])
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
        heptN = Heptagons.Kite2Hept(Vs[7], Vs[6], Vs[5], Vs[4])
        Vs.extend(heptN[0]) # V19 - V25
        for i in range(4, 8):
            Ns[i] = heptN[1]
        for i in range(19, 26):
            Ns[i] = heptN[1]
        heptN = Heptagons.Kite2Hept(Vs[11], Vs[10], Vs[9], Vs[8])
        Vs.extend(heptN[0]) # V26 - V32
        for i in range(8, 12):
            Ns[i] = heptN[1]
        for i in range(26, 33):
            Ns[i] = heptN[1]

        # add equilateral triangles:
        Vs.extend([Vs[15], Vs[22], Vs[29]])         # V33 - V35
        # add isosceles triangles:
        this.xtraEs = []
        if this.triangleAlt:
            Vs.extend([Vs[13], Vs[14], Vs[32]]) # V36 - V38
            Vs.extend([Vs[20], Vs[21], Vs[18]]) # V39 - V41
            Vs.extend([Vs[27], Vs[28], Vs[25]]) # V42 - V44
            if this.addXtraEdge:
                this.xtraEs = [36, 38, 39, 41, 42, 44]
        else:
            Vs.extend([Vs[13], Vs[14], Vs[14]]) # V36 - V38
            Vs.extend([Vs[20], Vs[21], Vs[21]]) # V39 - V41
            Vs.extend([Vs[27], Vs[28], Vs[28]]) # V42 - V44
            if this.heptPosAlt:
                v = Vs[38]
                Vs[38] = vec(-v[0],  v[1], -v[2])    # HY * V9
                v = Vs[41]
                Vs[41] = vec( v[0], -v[1], -v[2])    # HX * V23
            else:
                v = Vs[38]
                Vs[38] = vec( v[0], -v[1], -v[2])    # HX * V9
                v = Vs[41]
                Vs[41] = vec(-v[0],  v[1], -v[2])    # HY * V23
            v = Vs[44]
            Vs[44] = vec(-v[0], -v[1],  v[2])    # HZ * V16
            if this.addXtraEdge:
                this.xtraEs = [37, 38, 40, 41, 43, 44]

        # normal of equilateral triangle
        for i in range(3):
            Ns.append(Vs[0])
        # normal of isosceles triangles
        for i in range(3):
            o = 36 + 3*i
            IsoscelesTriangleN = Geom3D.Triangle(
                Vs[o],
                Vs[o+1],
                Vs[o+2]
            ).normal()
            Ns.extend([IsoscelesTriangleN, IsoscelesTriangleN, IsoscelesTriangleN])

        this.xtraFs = [
                [33, 34, 35],
                [36, 37, 38],
                [39, 40, 41],
                [42, 43, 44]
            ]

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
            Fs.extend(this.xtraFs)
            Es.extend(this.xtraEs)
            colIds.extend(this.xtraColIds)
        this.setBaseEdgeProperties(Es = Es)
        this.setBaseFaceProperties(Fs = Fs, colors = (this.theColors, colIds))

    def toPsPiecesStr(this,
            faceIndices = [],
            scaling = 1,
            precision = 7,
            margin = 1.0e-10
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
                faceIndices.append(offset+3)
        #print faceIndices
        return Heptagons.EqlHeptagonShape.toPsPiecesStr(this,
            faceIndices, scaling, precision, margin
        )

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
        # init heptagons normal, will be set in setV:
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

class CtrlWin(Heptagons.EqlHeptagonCtrlWin):
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
        this.setKiteAngleExtremes(this.specialAngles[3]['a'], this.specialAngles[2]['a'], 168)
        kwargs['title'] = TITLE
        Heptagons.EqlHeptagonCtrlWin.__init__(this,
            shape, canvas, (338, 570),
            *args, **kwargs
        )

    def addSpecialPositions(this, parentFrame, parentSizer):
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
        #print 'onSpecialPos'
        index = this.specialPosGui.GetSelection()
        angleData = this.specialAngles[index]
        angle = angleData['a']
        if index != 0 and this.previousIndex == 0:
            # save angle in None
            this.specialAngles[0]['a'] = this.Slider2Angle(
                    this.kiteAngleGui.GetValue()
                )
            #TODO save other settings? Make a functions for this.
        this.previousIndex = index
        this.kiteAngleGui.SetValue(this.Angle2Slider(angle))
        this.shape.setAngle(angle)

        this.showHeptaChk.SetValue(True)
        this.altHeptPosChk.SetValue(False)
        if 't' in angleData:
            this.showKiteChk.SetValue(False)
            this.showXtraChk.SetValue(True)
            this.triangleAltChk.SetValue(angleData['t'])
        else:
            this.showKiteChk.SetValue(True)
            this.showXtraChk.SetValue(False)
        if 'e' in angleData:
            this.addXtraEdgeChk.SetValue(angleData['e'])
        this.onViewSettingsChk(this)
        # onViewSettingsChk(this) contains:
        #this.canvas.paint()
        #try:
        #    this.statusBar.SetStatusText(this.shape.getStatusStr())
        #except AttributeError: pass


class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
