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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#--------------------------------------------------------------------

import wx
import math

from orbitit import Geom3D, geomtypes, Heptagons
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

class Shape(Heptagons.EqlHeptagonShape):
    def __init__(this, *args, **kwargs):
        t1 = Rot(angle = geomtypes.turn(0.2), axis = vec(0, -Dtau2, 1))
        t2 = Rot(angle = geomtypes.turn(0.4), axis = vec(0, -Dtau2, 1))
        t3 = Rot(angle = geomtypes.turn(0.6), axis = vec(0, -Dtau2, 1))
        t4 = Rot(angle = geomtypes.turn(0.8), axis = vec(0, -Dtau2, 1))
        h0 = HalfTurn(axis=vec(0, -1, tau2))
        Heptagons.EqlHeptagonShape.__init__(this,
            directIsometries = [
                    geomtypes.E, t1, t2, t3, t4,
                    h0, h0*t1, h0*t2, h0*t3, h0*t4,
                    t1*h0, t1*h0*t1, t1*h0*t2, t1*h0*t3, t1*h0*t4,
                    t2*h0, t2*h0*t1, t2*h0*t2, t2*h0*t3, t2*h0*t4,
                    t3*h0, t3*h0*t1, t3*h0*t2, t3*h0*t3, t3*h0*t4,
                    t4*h0, t4*h0*t1, t4*h0*t2, t4*h0*t3, t4*h0*t4
                ],
            # abuse the opposite isometry (even though this is not an opposite
            # isometry really) But for historical reasons I used a half turn
            # here to prevent edges to be drawn twice.
            #oppositeIsometry = geomtypes.I,
            oppositeIsometry = halfTurn,
            name = 'EglHeptA5xI_GI'
        )
        this.initArrs()
        this.setH(H0)

    def setH(this, h):
        this.angle = Geom3D.Rad2Deg * math.atan((h - H0)/Ca)
        Heptagons.EqlHeptagonShape.setH(this, h)

    def setAngle(this, a):
        this.h     = Ca * math.tan(a*Geom3D.Deg2Rad) + H0
        Heptagons.EqlHeptagonShape.setAngle(this, a)

    def setV(this):
        # input this.h
        St = this.h / (Dtau2*V3*this.h - 3)
        #print 's', St
        #
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
        Vs = [
                vec(0.0,      0.0,      this.h),   # 0
                Rl,
                vec(0.0,     -Dtau2*St, St),
                vec(-Rl[0],   Rl[1],    Rl[2])     # 3
            ]

        # add heptagons
        H = HalfTurn(axis=Vs[3])
        this.errorStr = ''
        if not this.heptPosAlt:
            Ns = Vs
            heptN = Heptagons.Kite2Hept(Vs[3], Vs[0], Vs[1], Vs[2])
            if heptN == None:
              this.errorStr = 'No valid equilateral heptagon for this position'
              return
            Mr = Rot(axis = geomtypes.Vec3(Vs[2]), angle = geomtypes.turn(0.2))

            # p is a corner of the pentagon inside the pentagram
            # p is rotated 1/5th turn to form a triangle
            # together with 2 corners of the pentagram:
            # 5 of these triangles will cover the pentagram.
            # this is easier than finding the centre of the pentagram.
            v3 = heptN[0][3]
            v4 = heptN[0][4]
            p = v3 + (v4 - v3)/tau
            v = Mr*p
            if this.triangleAlt:
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
            RegularTrianglePartN = Vs[2]
            # vt is the vertex that will be projected by a half turn on the
            # third vertex of the isosceles triangle.
            IsoscelesTriangleV = [
                        heptN[0][5],
                        heptN[0][6],
                        vt
                    ]
        else:
            heptN = Heptagons.Kite2Hept(Vs[1], Vs[2], Vs[3], Vs[0])
            if heptN == None:
              this.errorStr = 'No valid equilateral heptagon for this position'
              return
            if this.triangleAlt:
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
        if heptN == None:
            this.errorStr = 'No valid equilateral heptagon for this position'
            return
        else:
            this.errorStr = ''
        vt = H * vt
        # rotate vt by a half turn, IsoscelesTriangleV NOT auto updated.
        IsoscelesTriangleV[2] = vt
        Vs.extend(heptN[0]) # V4 - V10, the heptagon
        Vs.extend(RegularTrianglePartV) # V11 - V13
        Vs.extend(IsoscelesTriangleV) # V14 - V16
        #for V in Vs: print V
        #h = heptN[1]
        #Ns = [[-h[0], -h[1], -h[2]] for i in range(11)]
        Ns = [heptN[1] for i in range(11)]
        Ns.extend([RegularTrianglePartN for i in range(3)])
        IsoscelesTriangleN = Geom3D.Triangle(
                IsoscelesTriangleV[0],
                IsoscelesTriangleV[1],
                IsoscelesTriangleV[2]
            ).normal()
        Ns.extend([IsoscelesTriangleN for i in range(3)])
        this.xtraEs = []
        if this.addXtraEdge:
            this.xtraEs = [xtraEdgeIndex, 16]

        #this.showBaseOnly = True
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
        this.setVs(Vs)

    def toPsPiecesStr(this,
            faceIndices = [],
            scaling = 1,
            precision = 7,
            margin = 1.0e-10
        ):
        if faceIndices == []:
            offset = 0
            #for f in range(len(this.Fs)):
            #    print 'F[', f, '] =', this.Fs[f]
            if this.showKite:
                faceIndices.append(offset)
                offset += len(this.kiteFs)
            if this.showHepta:
                faceIndices.append(offset)
                offset += len(this.heptFs)
            if this.showXtra:
                faceIndices.append(offset)
                faceIndices.append(offset+1)
        #print 'faceIndices', faceIndices
        return Heptagons.EqlHeptagonShape.toPsPiecesStr(this,
            faceIndices, scaling, precision, margin
        )

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
        stdStr = Heptagons.EqlHeptagonShape.getStatusStr(this)
        if this.showXtra and this.addXtraEdge and len(this.xtraEs) == 2:
            if this.updateV:
                this.setV()
            # reference vector, a side of the heptagon:
            vs = this.Vs[0]
            r0 = vs[4]
            r1 = vs[5]
            r = r0 - r1
            # the extra edge
            v0 = vs[this.xtraEs[0]]
            v1 = vs[this.xtraEs[1]]
            v = v0 - v1
            #print r.norm(), v.norm()
            return '%s, extra edge length: %02.2f' % (stdStr, v.norm()/r.norm())
        # TODO: if not addXtraEdge: print diff in norms (or both edge lengths)
        else:
            return stdStr
    # GUI PART

class CtrlWin(Heptagons.EqlHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
        # a: angle
        # s: string text in GUI
        # t: triangle alternative value
        # e: add extra edge
        # h: alternative heptagon position
        # if a field is not specified: don't care.
        this.specialSolidAngles = [
            {'a':   0.0,               's': 'None'},
            {'a':   0.0,               's': 'Great Icosahedron', 'h': False},
            {'a':  79.187683036428297, 's': 'Great Stellated Dodecahedron', 'h': True},
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
        this.setKiteAngleExtremes(
                this.prefHeptSpecAngles[1]['a'],
                this.altHeptSpecAngles[2]['a']
            )
        kwargs['title'] = TITLE
        Heptagons.EqlHeptagonCtrlWin.__init__(this,
            shape, canvas, (332, 638),
            *args, **kwargs
        )
        this.shape.setViewSettings(heptPosAlt=True)
        this.altHeptPosChk.SetValue(True)

    def addSpecialPositions(this, parentFrame, parentSizer):
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
            this.specialSolidAngles[0]['a'] = this.Slider2Angle(
                    this.kiteAngleGui.GetValue()
                )
            #TODO save other settings? Make a functions for this.
        this.specialSolidPreviousIndex = index
        this.kiteAngleGui.SetValue(this.Angle2Slider(angle))
        this.shape.setAngle(angle)

        this.showKiteChk.SetValue(True)
        this.showXtraChk.SetValue(False)
        if 'h' in angleData:
            this.altHeptPosChk.SetValue(angleData['h'])
            this.showHeptaChk.SetValue(True)
        else:
            this.showHeptaChk.SetValue(False)
            this.altHeptPosChk.SetValue(False)
        this.onViewSettingsChk(this)
        if index != 0:
            if this.prefHeptSpecPosGui.GetSelection() != 0:
                this.prefHeptSpecPosGui.SetSelection(0)
            if this.altHeptSpecPosGui.GetSelection() != 0:
                this.altHeptSpecPosGui.SetSelection(0)

    def onPrefHeptSpecPos(this, event = None):
        #print 'onPrefHeptSpecPos'
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
        this.onViewSettingsChk(this)
        if index != 0:
            if this.specialSolidPosGui.GetSelection() != 0:
                this.specialSolidPosGui.SetSelection(0)
            if this.altHeptSpecPosGui.GetSelection() != 0:
                this.altHeptSpecPosGui.SetSelection(0)

    def onAltHeptSpecPos(this, event = None):
        #print 'onAltHeptSpecPos'
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
        this.onViewSettingsChk(this)
        if index != 0:
            if this.specialSolidPosGui.GetSelection() != 0:
                this.specialSolidPosGui.SetSelection(0)
            if this.prefHeptSpecPosGui.GetSelection() != 0:
                this.prefHeptSpecPosGui.SetSelection(0)

    def Opaqueness2Transparency(this, opaqueness):
        return (1 - opaqueness) * 100

    def onOpaquenessAdjust(this, event):
        transparency = float(this.transparencyGui.GetValue())
        this.shape.setViewSettings(opaqueness = 1 - transparency/100)

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)


