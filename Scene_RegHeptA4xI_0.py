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
#-------------------------------------------------------------------
#
# $Log: Scene_RegHeptS4A4Eg.py,v $
# Revision 1.4  2008/10/04 21:38:16  marcelteun
# fix canvas position of regular heptagons
#
# Revision 1.3  2008/10/04 21:13:29  marcelteun
# fix for undestroyed boxes in Ubuntu Hardy Heron
#
# Revision 1.2  2008/10/03 20:09:51  marcelteun
# Bridges2008 changes: window position
#
# Revision 1.1.1.1  2008/07/05 10:35:43  marcelteun
# Imported sources
#
# Revision 1.1  2008/06/18 05:31:54  teun
# Initial revision
#
#

import wx
import math
import rgb
import Heptagons
import Geom3D
import Scenes3D
from cgkit import cgtypes
from OpenGL.GL import *

Title = 'Polyhedra with Folded Regular Heptagons A4xI'

def Vlen(v0, v1):
    x = v1[0] - v0[0]
    y = v1[1] - v0[1]
    z = v1[2] - v0[2]
    return (math.sqrt(x*x + y*y + z*z))

class Shape(Geom3D.SymmetricShape):
    def __init__(this, *args, **kwargs):
        Geom3D.SymmetricShape.__init__(this,
            Vs = [], Fs = [],
            directIsometries = [
                    Geom3D.E,
                    cgtypes.quat(Geom3D.R1_3, cgtypes.vec3( 1,  1, 1)),
                    cgtypes.quat(Geom3D.R2_3, cgtypes.vec3( 1,  1, 1)),
                ],
            oppositeIsometry = Geom3D.I,
            name = 'FoldedRegHeptA4xI'
        )
        #this.dbgPrn = True
        this.theColors     = [
                rgb.oliveDrab[:],
                rgb.brown[:],
                rgb.yellow[:],
                rgb.cyan[:]
            ]
        this.angle = 1.2
        this.fold1 = 0.0
        this.fold2 = 0.0
        this.translation = 4.0
        this.applySymmetry = True
        this.addTriangles = True
        this.useCulling = False
        this.edgeAlternative = 0
        # There are 4 different edges to separate the triangles:
        # a (V2-V9), b (V2-V12), c (V2-V14), and d (V14-V1)
        # the first three have opposite alternatives:
        # a' (V3-V12), b' (V3-V14) and c' (V1-V12)
        # This leads to 2^3 possible combinations,
        # however the edge configuration a b' does not occur
        # neither does b' c'
        # This leaves 5 possible edge configurations:
        this.nrOfEdgeAlternatives = 5
        this.T_STRIP_1_LOOSE = 0
        this.T_STRIP_I       = 1
        this.T_STRIP_II      = 2
        this.T_STAR          = 3
        this.T_STAR_1_LOOSE  = 4
        this.edgeChoices = [
                'Triangle Strip, 1 Loose ',
                'Triangle Strip I',
                'Triangle Strip II',
                'Triangle Star',
                'Triangle Star, 1 Loose'
            ]

        this.lightPosition = [-50., 50., 200., 0.]
        this.lightAmbient  = [0.25, 0.25, 0.25, 1.]
        this.lightDiffuse  = [1., 1., 1., 1.]
        this.materialSpec  = [0., 0., 0., 0.]
        #this.showBaseOnly  = True
        this.initArrs()
        this.setV()

    def glDraw(this):
        if this.updateShape: this.setV()
        Geom3D.SymmetricShape.glDraw(this)

    def setEdgeAlternative(this, alt):
        this.edgeAlternative = alt % this.nrOfEdgeAlternatives
        this.updateShape = True

    def setAngle(this, angle):
        this.angle = angle
        this.updateShape = True

    def setFold1(this, angle):
        this.fold1 = angle
        this.updateShape = True

    def setFold2(this, angle):
        this.fold2 = angle
        this.updateShape = True

    def setHeight(this, height):
        this.translation = height
        this.updateShape = True

    def edgeColor(this):
        glColor(0.5, 0.5, 0.5)

    def vertColor(this):
        glColor(0.7, 0.5, 0.5)

    def getStatusStr(this):
        #angle = Geom3D.Rad2Deg * this.angle
        str = 'Angle = %01.2f rad, fold1 = %01.2f rad, fold2 = %01.2f rad, T = %02.2f' % (
                this.angle,
                this.fold1,
                this.fold2,
                this.translation
            )
        if this.updateShape:
            this.setV()
        if this.edgeAlternative == this.T_STRIP_1_LOOSE:
            aLen = Vlen(this.Vs[5], this.Vs[10])
            bLen = Vlen(this.Vs[5], this.Vs[13])
            cLen = Vlen(this.Vs[5], this.Vs[15])
            dLen = Vlen(this.Vs[6], this.Vs[15])
        elif this.edgeAlternative == this.T_STRIP_I:
            aLen = Vlen(this.Vs[4], this.Vs[13])
            bLen = Vlen(this.Vs[5], this.Vs[13])
            cLen = Vlen(this.Vs[5], this.Vs[15])
            dLen = Vlen(this.Vs[6], this.Vs[15])
        elif this.edgeAlternative == this.T_STRIP_II:
            aLen = Vlen(this.Vs[4], this.Vs[13])
            bLen = Vlen(this.Vs[4], this.Vs[15])
            cLen = Vlen(this.Vs[5], this.Vs[15])
            dLen = Vlen(this.Vs[6], this.Vs[15])
        elif this.edgeAlternative == this.T_STAR:
            aLen = Vlen(this.Vs[4], this.Vs[13])
            bLen = Vlen(this.Vs[5], this.Vs[13])
            cLen = Vlen(this.Vs[6], this.Vs[13])
            dLen = Vlen(this.Vs[6], this.Vs[15])
        elif this.edgeAlternative == this.T_STAR_1_LOOSE:
            aLen = Vlen(this.Vs[5], this.Vs[10])
            bLen = Vlen(this.Vs[5], this.Vs[13])
            cLen = Vlen(this.Vs[6], this.Vs[13])
            dLen = Vlen(this.Vs[6], this.Vs[15])
        #tst:
        #aLen = Vlen(this.Vs[0], [(this.Vs[6][i] + this.Vs[1][i]) / 2 for i in range(3)])
        #bLen = Vlen([(this.Vs[5][i] + this.Vs[2][i]) / 2 for i in range(3)], [(this.Vs[6][i] + this.Vs[1][i]) / 2 for i in range(3)])
        str = '%s, |a|: %02.2f, |b|: %02.2f, |c|: %02.2f, |d|: %02.2f' % (
                str, aLen, bLen, cLen, dLen
            )

        return str

    def setV(this):
        print this.name, "setV"
        sina = math.sin(this.angle)
        cosa = math.cos(this.angle)

        sinb = math.sin(this.fold1)
        cosb = math.cos(this.fold1)

        sing = math.sin(this.fold2)
        cosg = math.cos(this.fold2)

        # note the role of sin and cos are exchanged compared to my sketch, 
        # because the angle is measured differently: thisAngle = 90 deg - sketchAngle
        x0__ = cosg * (Heptagons.H) + Heptagons.SigmaH + Heptagons.RhoH
        z0__ = sing * (Heptagons.H)

        x0_ = cosb * (x0__ - Heptagons.RhoH) - sinb * (z0__                 ) + Heptagons.RhoH
        z0_ = cosb * (z0__                 ) + sinb * (x0__ - Heptagons.RhoH)

        x1_  = cosb * (Heptagons.SigmaH) + Heptagons.RhoH
        z1_  = sinb * (Heptagons.SigmaH)

        x0  = sina * x0_ - cosa * z0_
        x1  = sina * x1_ - cosa * z1_
        x2  = sina * (         Heptagons.RhoH)
        x3  =                 0.0
        x4  =                 0.0
        x5  = x2
        x6  = x1

        y0  =  0.0
        y1  =  Heptagons.Rho / 2
        y2  =  Heptagons.Sigma / 2
        y3  =  0.5
        y4  = -y3
        y5  = -y2
        y6  = -y1

        z0  = this.translation - (sina * z0_ + cosa * x0_)
        z1  = this.translation - (sina * z1_ + cosa * x1_)
        z2  = this.translation - cosa * (         Heptagons.RhoH)
        z3  = this.translation
        z4  = this.translation
        z5  = z2
        z6  = z1

        Vs = [
                cgtypes.vec3([ x0,    y0,    z0]),
                cgtypes.vec3([ x1,    y1,    z1]),
                cgtypes.vec3([ x2,    y2,    z2]),
                cgtypes.vec3([ x3,    y3,    z3]),
                cgtypes.vec3([ x4,    y4,    z4]),
                cgtypes.vec3([ x5,    y5,    z5]),
                cgtypes.vec3([ x6,    y6,    z6]),
 
                cgtypes.vec3([-x0,    y0,    z0]),        # V0' = V7
                cgtypes.vec3([-x1,    y1,    z1]),        # V1' = V8
                cgtypes.vec3([-x2,    y2,    z2]),        # V2' = V9
                cgtypes.vec3([-x5,    y5,    z5]),       # V5' = V10
                cgtypes.vec3([-x6,    y6,    z6]),       # V6' = V11

                cgtypes.vec3([ y0,    z0,    x0]),        # V12
                cgtypes.vec3([-y0,   -z0,    x0]),        # V13
                cgtypes.vec3([ y1,    z1,    x1]),        # V14
                cgtypes.vec3([ y1,   -z1,    x1]),        # V15
                cgtypes.vec3([ y6,    z6,    x6]),       # V16
                cgtypes.vec3([ y6,   -z6,    x6]),       # V17

                # 
                #             16                14
                #                      12
                #                      
                #               9             2
                #      8                               1
                #                       
                #                      3
                #                       
                #   7                  |<-RH->|<--SH--><H>0
                #                       
                #                      4
                #                       
                #     11                               6
                #              10             5
                #                      
                #                      13
                #             17                15
                #/

                # now add the vertices of the triangles on order 3 axes,
                # some are double but that is easier to understand / maintain the faces array
                # even reflections (including indentity)
                [x1, y1, z1],             # V18
                [y1, z1, x1],             # V19
                [z1, x1, y1],             # V20

                [-x1, y1, z1],            # V21
                [-y1, z1, x1],            # V22
                [-z1, x1, y1],            # V23
            ]

        # there are more vertices in the array, but this is the amount of Vs
        # that will generate all Vs once after applying the group symmetry
        this.setBaseVertexProperties(Vs = Vs)
        Es = []
        Fs = []
        Fs.extend(this.heptaF) # use extend to copy heptaF to Fs
        colIds = [0, 0, 0, 0, 0, 0]
        if this.addTriangles:
            Fs.extend(this.triFs[this.edgeAlternative])
            colIds.extend(this.triColIds[this.edgeAlternative])
            # TODO: the following array contains all faces already, i.e. each
            # symmetry operation will map the set on itself
            Fs.extend(this.triO3F)
            colIds.extend([3 for i in range(len(this.triO3F))])
            Es.extend(this.heptaEs[this.edgeAlternative])
        this.setBaseEdgeProperties(Es = Es)
        this.setBaseFaceProperties(Fs = Fs, colors = (this.theColors, colIds))
        this.showBaseOnly = not this.applySymmetry
        this.updateShape = False

    def initArrs(this):
        print this.name, "initArrs"

        this.heptaF = [
                [0, 1, 6],
                [1, 2, 5, 6],
                [2, 3, 4, 5],
                [8, 7, 11],
                [9, 8, 11, 10],
                [4, 3, 9, 10]
            ]
        this.triFs = [
                [
                    [3, 2, 9], [5, 4, 10],
                    [9, 2, 12], [5, 10, 13],
                    [2, 14, 12], [5, 13, 15],
                    [9, 12, 16], [17, 13, 10],
                    [2, 1, 14], [6, 5, 15],
                    [8, 9, 16], [10, 11, 17],
                ],
                [
                    [8, 9, 16], [9, 12, 16],
                    [3, 12, 9], [3, 2, 12],
                    [2, 14, 12], [2, 1, 14],
                    [10, 11, 17], [17, 13, 10],
                    [4, 10, 13], [4, 13, 5],
                    [5, 13, 15], [6, 5, 15],
                ],

        # 
        #             16                14
        #                      12
        #                      
        #               9             2
        #      8                               1
        #                       
        #                      3
        #                       
        #   7                  |<-RH->|<--SH--><H>0
        #                       
        #                      4
        #                       
        #     11                               6
        #              10             5
        #                      
        #                      13
        #             17                15
        #/
                [
                    [8, 9, 16], [3, 16, 9],
                    [3, 12, 16], [3, 14, 12],
                    [3, 2, 14], [2, 1, 14],
                    [10, 11, 17], [4, 10, 17],
                    [17, 13, 4], [4, 13, 15],
                    [4, 15, 5], [6, 5, 15],
                ],
                [
                    [8, 12, 16], [9, 12, 8],
                    [3, 12, 9], [3, 2, 12],
                    [2, 1, 12], [12, 1, 14],
                    [17, 13, 11], [10, 11, 13],
                    [4, 10, 13], [4, 13, 5],
                    [5, 13, 6], [6, 13, 15],
                ],
                [
                    [3, 2, 9], [9, 2, 12],
                    [9, 12, 8], [2, 1, 12],
                    [8, 12, 16], [12, 1, 14],
                    [5, 4, 10], [5, 10, 13],
                    [10, 11, 13], [5, 13, 6],
                    [17, 13, 11], [6, 13, 15],
                ]
            ]
        this.triColIds = [
                [1, 1, 2, 2, 1, 1, 1, 1, 2, 2, 2, 2],
                [1, 2, 1, 2, 1, 2, 2, 1, 2, 1, 2, 1],
                [1, 2, 1, 2, 1, 2, 2, 1, 2, 1, 2, 1],
                [1, 2, 1, 2, 1, 2, 2, 1, 2, 1, 2, 1],
                [1, 2, 1, 1, 2, 2, 1, 2, 1, 1, 2, 2],
            ]
        this.triO3F = [
                [18, 20, 19], [21, 23, 22],
            ]
        this.heptaEs = [
                [
                    0, 1, 1, 2, 2, 3,
                    3, 4, 4, 5, 5, 6,
                    6, 0, 7, 8, 8, 9,
                    9, 3, 4, 10, 10, 11,
                    11, 7, 10, 5, 2, 9,
                    12, 9, 12, 2, 13, 5,
                    13, 10, 14, 2, 14, 12,
                    15, 5, 15, 13, 16, 9,
                    16, 12, 17, 10, 17, 13,
                    14, 1, 15, 6, 16, 8, 
                    17, 11,
                ],
                [
                    0, 1, 1, 2, 2, 3,
                    3, 4, 4, 5, 5, 6,
                    6, 0, 7, 8, 8, 9,
                    9, 3, 4, 10, 10, 11,
                    11, 7, 12, 3, 4, 13,
                    12, 9, 12, 2, 13, 5,
                    13, 10, 14, 2, 14, 12,
                    15, 5, 15, 13, 16, 9,
                    16, 12, 17, 10, 17, 13,
                    14, 1, 15, 6, 16, 8, 
                    17, 11,
                ],
                [
                    0, 1, 1, 2, 2, 3,
                    3, 4, 4, 5, 5, 6,
                    6, 0, 7, 8, 8, 9,
                    9, 3, 4, 10, 10, 11,
                    11, 7, 12, 3, 4, 13,
                    16, 3, 14, 3, 15, 4,
                    17, 4, 14, 2, 14, 12,
                    15, 5, 15, 13, 16, 9,
                    16, 12, 17, 10, 17, 13,
                    14, 1, 15, 6, 16, 8, 
                    17, 11,
                ],
                [
                    0, 1, 1, 2, 2, 3,
                    3, 4, 4, 5, 5, 6,
                    6, 0, 7, 8, 8, 9,
                    9, 3, 4, 10, 10, 11,
                    11, 7, 12, 3, 4, 13,
                    12, 9, 12, 2, 13, 5,
                    13, 10, 12, 1, 14, 12,
                    13, 6, 15, 13, 12, 8,
                    16, 12, 13, 11, 17, 13,
                    14, 1, 15, 6, 16, 8, 
                    17, 11,
                ],
                [
                    0, 1, 1, 2, 2, 3,
                    3, 4, 4, 5, 5, 6,
                    6, 0, 7, 8, 8, 9,
                    9, 3, 4, 10, 10, 11,
                    11, 7, 10, 5, 2, 9,
                    12, 9, 12, 2, 13, 5,
                    13, 10, 12, 1, 14, 12,
                    13, 6, 15, 13, 12, 8,
                    16, 12, 13, 11, 17, 13,
                    14, 1, 15, 6, 16, 8, 
                    17, 11
                ]
            ]

class CtrlWin(wx.Frame):
    def __init__(this, shape, canvas, *args, **kwargs):
        size = (440, 880)
        # TODO assert (type(shape) == type(RegHeptagonShape()))
        this.shape = shape
        this.canvas = canvas
        wx.Frame.__init__(this, *args, **kwargs)
        this.panel = wx.Panel(this, -1)
        this.statusBar = this.CreateStatusBar()
        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
        this.mainSizer.Add(
                this.createControlsSizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.setDefaultSize(size)
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()

        this.specPosIndex = 0
        this.specPos = [
                [], # None
                [ # 1, 1, 1, 1
                    [ # index T_STRIP_1_LOOSE
                        [0.12225322067129163, 0.69387894107538739, -2.8805347296708912, -1.4528097830759066],
                        [0.12225322067129135, 0.69387894107538739, -2.8805347296708907, 0.97566810142912352],
                        [-1.0798457219755391, 2.4477137125144059, -1.1266999582318729, -1.4528097830759075],
                        [-1.0798457219755393, 2.4477137125144059, -1.1266999582318729, 0.97566810142912264],
                        [0.48335670145489734, 2.4477137125144059, 1.9718085849819014, -1.3005095003723568],
                        [0.48335670145489718, 2.4477137125144059, 1.9718085849819014, 2.5541979223021967],
                        [0.069502909920064734, 2.4477137125144059, 0.86221483369683438, -1.4133895408640926],
                        [0.069502909920064929, 2.4477137125144059, 0.86221483369683449, 2.4413178818104626],
                        [1.271601852566896, 0.69387894107538739, -0.89161993774218384, -1.4133895408640926],
                        [1.2716018525668957, 0.69387894107538739, -0.89161993774218473, 2.4413178818104613],
                        [1.6854556441017283, 0.69387894107538739, 0.21797381354288348, -1.3005095003723577],
                        [1.6854556441017283, 0.6938789410753875, 0.21797381354288348, 2.5541979223021971],
                        [1.4967584913927861, 2.4477137125144059, 1.2849159913648354, 1.5024366351232004],
                        [1.4967584913927861, 2.4477137125144059, 1.2849159913648354, -0.92604124938183041],
                        [2.698857434039617, 0.69387894107538739, -0.46891878007418342, -0.92604124938183041],
                        [2.6988574340396174, 0.69387894107538739, -0.46891878007418253, 1.5024366351231997],
                    ],
                    [ # index T_STRIP_I
                        [-1.156637817378058, 2.7544847680954581, -0.60432651389549186, -2.1952192586001704] ,
                        [-0.80659177867111587, 2.0380849613850587, -1.7484826657781838, 0.75631842380774827] ,
                        [0.42167356237852688, 2.5217075314325132, 1.9601130634313986, -1.1682581061100761] ,
                        [0.045985361816704901, 2.6195862264538823, 1.2488853709117418, 2.2391071949708214] ,
                        [1.6127089750792163, 0.8960600601261185, 0.59474532287192872, 2.7202541745041593] ,
                        [1.632164823313732, 0.45148184556249021, -0.4345281024844514, 2.2408843223541539] ,
                        [0.2700664528450854, 2.0991609559786299, 0.26487872604964213, 2.8244875350830063] ,
                        [0.65532847315761944, 1.6099414020433973, -0.36585112032953671, -2.2559584645024433] ,
                        [1.046029937161403, 2.7705999979927567, 1.2607488678219125, 2.5274815882531603] ,
                        [2.3225481937956785, 1.5804869294071295, 0.74234494088217806, 0.28406772970135918] ,
                    ],
                    [],  # index T_STRIP_II
                    [ # index T_STAR
                       [-0.68958505376778345, -2.7696838629629861, 1.8676782736688526, -2.8833852670220774] ,
                       [-0.19704139133793197, -2.4699975062528203, 2.5847963085157168, -0.94597526034129231] ,
                       [-1.0845032151713569, -2.7900809377096936, 0.72626261351302934, -2.9760746154612101] ,
                       [-1.0931182092639629, 2.7314368575690051, -0.64021128226658242, -2.3596477091653614] ,
                       [-1.2277270226021526, -2.7907417508085364, 0.7276977195917137, -2.5022421464560081] ,
                       [-1.2382185407715089, 2.7319533145320043, -0.64071803589591614, -1.8835010126493845] ,
                       [0.63325519828989496, -1.3781269897190276, 2.9949754009094858, -2.0258812783756817] ,
                       [1.0822514530522973, -0.98200247015339048, -2.9335495968145002, 2.3457373536690409] ,
                       [1.1898603046161322, -0.3136159062298125, -1.5302505921582226, 2.9405127532309492] ,
                       [0.52091537040053171, -2.0394160644242385, 2.5154785652852962, -1.4681786794801743] ,
                       [1.6788412682906029, -0.30530724663815345, -0.89030309765033433, -1.1053291855067311] ,
                       [1.5927868724261478, 0.90443394452585701, 0.69420736165576036, 2.8069802147078304] ,
                       [1.742300860519741, 0.5429616709670313, 0.57909026065007829, -1.9874363203388654] ,
                       [0.90745910529245521, 1.0979361913340906, -1.9819560030787446, 1.656761037113343] ,
                       [0.61445205337854325, 1.5406078029015788, -1.5599598916192576, 2.1201871496572462] ,
                       [1.3155499020279271, -3.0834911230708753, 2.2752628509264001, -0.60007527499206059] ,
                    ],
                    [ # index T_STAR_1_LOOSE
                       [0.28592011827864433, -0.69387894107538717, 3.0914363610021587, -2.7118862151736765] ,
                       [0.18803380976514264, 0.69387894107538739, -2.887492084887687, -1.6205232315712745] ,
                       [0.45405009105009386, -0.69387894107538717, 3.1070403302585325, 3.0489972727344448] ,
                       [0.34459144908216149, 0.69387894107538739, -2.8717533536288018, -2.1505358163794623] ,
                       [-0.7480488515967384, -2.4477137125144059, 1.3532055588195133, 3.0489972727344492] ,
                       [-0.85750749356466915, 2.4477137125144059, -1.1179185821897839, -2.1505358163794632] ,
                       [-0.91617882436818654, -2.4477137125144059, 1.3376015895631408, -2.7118862151736765] ,
                       [-1.0140651328816883, 2.4477137125144059, -1.1336573134486683, -1.6205232315712736] ,
                       [0.46052924938527157, 2.4477137125144059, 2.5454679368948545, -2.1792035409732051] ,
                       [0.47708107305485198, 2.4477137125144059, 2.1074649520189057, 2.690505533394651] ,
                       [0.63369573819626746, -2.4477137125144059, 2.2084094046000917, 1.7744881136624304] ,
                       [1.6626281920321024, 0.6938789410753875, 0.79163316545583573, -2.179203540973206] ,
                       [1.6791800157016832, 0.69387894107538739, 0.35363018057988738, 2.690505533394651] ,
                       [0.85196300238033951, -2.4477137125144059, 2.4495268503566252, -1.0637165671611601] ,
                       [1.8357946808430985, -0.69387894107538717, -2.3209411311404757, 1.7744881136624304] ,
                       [2.0540619450271707, -0.69387894107538717, -2.0798236853839418, -1.0637165671611601] ,
                    ]

                ],
                [ # 1, 1, 1, 0
                    [ # index T_STRIP_1_LOOSE
                       [0.61336294993015139, 0.69387894107538739, -2.0238552489037858, -2.9635369142286225],
                       [-0.5887359927166792, 2.4477137125144059, -0.27002047746476787, -2.9635369142286265],
                       [-0.58873599271667931, 2.4477137125144055, -0.27002047746476787, -0.53505902972359287],
                       [0.61336294993015172, 0.6938789410753875, -2.0238552489037858, -0.5350590297235911],
                       [1.1885747858746869, 2.4477137125144059, 2.0238552489037858, -0.17805573936116925],
                       [1.1885747858746867, 2.4477137125144059, 2.0238552489037858, -2.6065336238662007],
                       [2.3906737285215178, 0.69387894107538739, 0.27002047746476765, -2.6065336238662007],
                       [2.3906737285215178, 0.69387894107538739, 0.27002047746476748, -0.17805573936117014],
                    ],
                    [ # index T_STRIP_I
                       [-0.44916112192145952, 2.1122756168847681, -0.79012198328513161, -2.3865538712183882],
                       [-0.17280305940844223, 1.708197033320781, -1.3032695012730287, -1.0165778617602852],
                       [1.9747407952132807, 1.4333956202690126, 1.3032695012730287, -2.125014791829507],
                       [2.2510988577262974, 1.0293170367050262, 0.79012198328513306, -0.75503878237140576],
                    ],
                    [],  # index T_STRIP_II
                    [ # index T_STAR, same as T_STRIP_I, since d==0
                       [-0.44916112192145868, 2.1122756168847676, -0.7901219832851325, -2.38655387121839],
                       [-0.17280305940844282, 1.7081970333207814, -1.3032695012730278, -1.0165778617602879],
                       [1.9747407952132801, 1.433395620269013, 1.3032695012730293, -2.1250147918295088],
                       [2.2510988577262974, 1.0293170367050257, 0.7901219832851325, -0.75503878237140576],
                    ],
                    [ # index T_STAR_1_LOOSE same as T_STRIP_1_LOOSE, since d == 0
                       [0.61336294993015139, 0.69387894107538739, -2.0238552489037858, -2.9635369142286225],
                       [-0.5887359927166792, 2.4477137125144059, -0.27002047746476787, -2.9635369142286265],
                       [-0.58873599271667931, 2.4477137125144055, -0.27002047746476787, -0.53505902972359287],
                       [0.61336294993015172, 0.6938789410753875, -2.0238552489037858, -0.5350590297235911],
                       [1.1885747858746869, 2.4477137125144059, 2.0238552489037858, -0.17805573936116925],
                       [1.1885747858746867, 2.4477137125144059, 2.0238552489037858, -2.6065336238662007],
                       [2.3906737285215178, 0.69387894107538739, 0.27002047746476765, -2.6065336238662007],
                       [2.3906737285215178, 0.69387894107538739, 0.27002047746476748, -0.17805573936117014],
                    ],
                ],
                [ # 1, V2, 1, 0
                    [ # index T_STRIP_1_LOOSE
                    ],
                    [ # index T_STRIP_I
                    ],
                    [ # index T_STRIP_II
                       [-0.11267755272150123, -3.0831450050562297, 1.3877578821507743, 1.8449713169461077],
                       [-0.11267755272150136, -3.0831450050562297, 1.3877578821507746, -2.1153635908403672],
                       [-0.11267755272150137, 1.6299156253637703, -1.3877578821507743, -0.9099725032984054],
                       [-0.11267755272150125, 1.6299156253637701, -1.3877578821507743, 3.0503624044880708],
                       [1.9146152885263397, -0.058447648533563878, -1.3877578821507743, 1.2966213366436845],
                       [1.9146152885263397, -0.058447648533563878, -1.3877578821507743, -1.0262290627494259],
                       [1.9146152885263397, 1.511677028226023, 1.3877578821507743, -2.2316201502913877],
                       [1.9146152885263394, 1.5116770282260232, 1.3877578821507748, 0.091230249101723615],
                    ],
                    [ # index T_STAR
                       [-0.08705843892515136, 1.5969418702542431, -1.421867197734886, 2.9924491746224842] ,
                       [0.49431990960006078, 0.84938187722147296, -1.9643841934177342, 0.66547727260192069] ,
                       [1.3076178262047773, 2.2922107763683206, 1.9643841934177342, 2.4761153809878742] ,
                       [1.8889961747299897, 1.5446507833355498, 1.4218671977348862, 0.14914347896730806] ,
                    ],
                    [ # index T_STAR_1_LOOSE
                    ],
                ],
                [ # 1, 1, V2, 1
                    [ # index T_STRIP_1_LOOSE
                    ],
                    [ # index T_STRIP_I
                       [-0.7567470429582589, -2.5576199555507575, 1.1795454244237868, 2.3059857893662681] ,
                       [-1.1678661078471526, -2.8121029764287098, 0.68295574950813442, -2.7139655274915295] ,
                       [-0.41297524742965674, -3.1174972074287144, 1.7516400761892816, 2.79576640194874] ,
                       [0.077508458941164482, -3.1132425768136569, 2.5081433873465593, -1.0130287751739537] ,
                       [1.3083497604815739, -0.1140786213581082, -1.285439266528412, 2.7129193530365638] ,
                       [0.25783404055203479, -2.5546307363274132, 1.7636722787631758, -2.2647077563220268] ,
                       [1.7906535720932244, 0.18641414197294012, -0.10475933583315822, -1.4181438292384954] ,
                       [1.7043186392248841, 2.5563292347776989, 1.7243790607070171, -0.22076373594903842] ,
                    ],
                    [ # index T_STRIP_II
                    ],
                    [ # index T_STAR
                       [0.16424126714814655, 2.9498362993661056, 2.3874240497328016, -1.1058248893059073],
                       [-0.19882278292562994, 2.9032159671887756, 1.5610799938533146, 2.4783868428030944],
                       [0.25790649607642102, -2.5549946510779682, 1.7632951187038364, -2.2653071966369556],
                       [0.93204577472517836, 1.5477756634948827, -0.99061381559026351, 2.1311786323813067],
                       [1.4034311724568889, 0.99681726039765606, -1.4331975048281924, 1.4674950784683738],
                       [1.8605312748771268, 2.3066435603055355, 1.4909152805218127, -0.17100514406483569],
                    ],
                    [ # index T_STAR_1_LOOSE
                       [0.47092324271706787, 2.4477137125144059, 2.202048646419386, -1.6406340012575686] ,
                       [0.46605546632809519, 2.4477137125144055, 1.6180811587323642, 2.1466265883588198] ,
                       [-0.023098085998088189, 2.4477137125144059, -0.43468821406451319, 0.094928336006570621] ,
                       [1.1790008566487422, 0.6938789410753875, -2.188522985503532, 0.094928336006570094] ,
                       [1.6730221853638987, 0.6938789410753875, 0.44821387498036724, -1.6406340012575686] ,
                       [1.6681544089749261, 0.6938789410753875, -0.13575361270665454, 2.1466265883588189] ,
                       [0.35276606332980004, 2.4477137125144059, 0.013198617843297455, 0.76713308744683972] ,
                       [1.5548650059766309, 0.69387894107538739, -1.7406361535957213, 0.76713308744683828] ,
                       [1.6426004818639248, 2.4477137125144059, 1.4471492405143849, 0.831403385559082] ,
                       [1.7634098860459992, 2.4477137125144059, 1.6101771888421501, -0.48553086554936442] ,
                       [2.8446994245107557, 0.69387894107538739, -0.30668553092463391, 0.83140338555908322] ,
                       [2.9655088286928302, 0.69387894107538739, -0.14365758259686778, -0.48553086554936353] ,
                    ],
                ],
            ]

    def createControlsSizer(this):
        this.heightF = 10
        this.maxHeight = 18

        this.Guis = []

        # static adjustments
        this.trisAltGui = wx.RadioBox(this.panel,
                label = 'Triangle Fill Alternative',
                style = wx.RA_VERTICAL,
                choices = this.shape.edgeChoices
            )
        this.Guis.append(this.trisAltGui)
        this.trisAltGui.Bind(wx.EVT_RADIOBOX, this.onTriangleAlt)
        this.prePosLst = [
                'None',
                '|a|=1 & |b|=1 & |c|=1 & |d|=1',
                '|a|=1 & |b|=1 & |c|=1 & |d|=0',
                '|a|=1 & |b|=V2 & |c|=1 & |d|=0',
                '|a|=1 & |b|=1 & |c|=V2 & |d|=1',
                'Triangle Star, 1 Loose: a=V2 & b=1 & c=V2 & d=1',
            ]
        this.prePosGui = wx.RadioBox(this.panel,
                label = 'Set Edge Lengths',
                style = wx.RA_VERTICAL,
                choices = this.prePosLst
            )
        this.Guis.append(this.prePosGui)
        this.prePosGui.Bind(wx.EVT_RADIOBOX, this.onPrePos)
        #wxPoint& pos = wxDefaultPosition, const wxSize& size = wxDefaultSize, int n = 0, const wxString choices[] = NULL, long style = 0, const wxValidator& validator = wxDefaultValidator, const wxString& name = "listBox")

        this.firstButton = wx.Button(this.panel, label = 'First')
        this.nextButton  = wx.Button(this.panel, label = 'Next')
        this.prevButton  = wx.Button(this.panel, label = 'Prev')
        this.lastButton  = wx.Button(this.panel, label = 'Last')
        this.Guis.append(this.firstButton)
        this.Guis.append(this.nextButton)
        this.Guis.append(this.prevButton)
        this.Guis.append(this.lastButton)
        this.firstButton.Bind(wx.EVT_BUTTON, this.onFirst)
        this.nextButton.Bind(wx.EVT_BUTTON, this.onNext)
        this.prevButton.Bind(wx.EVT_BUTTON, this.onPrev)
        this.lastButton.Bind(wx.EVT_BUTTON, this.onLast)

        # View Settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        this.applySymGui = wx.CheckBox(this.panel, label = 'Apply Symmetry')
        this.Guis.append(this.applySymGui)
        this.applySymGui.SetValue(this.shape.applySymmetry)
        this.applySymGui.Bind(wx.EVT_CHECKBOX, this.onApplySym)
        this.addTrisGui = wx.CheckBox(this.panel, label = 'Show Triangles')
        this.Guis.append(this.addTrisGui)
        this.addTrisGui.SetValue(this.shape.addTriangles)
        this.addTrisGui.Bind(wx.EVT_CHECKBOX, this.onAddTriangles)

        # dynamic adjustments
        this.angleGui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.angle,
                minValue = 0,
                maxValue = 180,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.angleGui)
        this.angleGui.Bind(wx.EVT_SLIDER, this.onAngle)
        this.fold1Gui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.fold1,
                minValue = -180,
                maxValue =  180,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.fold1Gui)
        this.fold1Gui.Bind(wx.EVT_SLIDER, this.onFold1)
        this.fold2Gui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.fold2,
                minValue = -180,
                maxValue =  180,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.fold2Gui)
        this.fold2Gui.Bind(wx.EVT_SLIDER, this.onFold2)
        this.heightGui = wx.Slider(
                this.panel,
                value = this.maxHeight - this.shape.translation*this.heightF,
                minValue = -this.maxHeight * this.heightF,
                maxValue = this.maxHeight * this.heightF,
		style = wx.SL_VERTICAL
            )
        this.Guis.append(this.heightGui)
        this.heightGui.Bind(wx.EVT_SLIDER, this.onHeight)


        # Sizers
        # static adjustments
        statSizer = wx.BoxSizer(wx.HORIZONTAL)
        statSizer.Add(this.trisAltGui, 1, wx.EXPAND)

        this.Boxes = []

        # view settings
        this.Boxes.append(wx.StaticBox(this.panel, label = 'View Settings'))
        settingsSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        settingsSizer.Add(this.applySymGui, 1, wx.EXPAND)
        settingsSizer.Add(this.addTrisGui, 1, wx.EXPAND)

        statSizer.Add(settingsSizer, 1, wx.EXPAND)

        this.Boxes.append(wx.StaticBox(this.panel, label = 'Special Positions'))
        this.specPosSizerV = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        this.specPosSizerH = wx.BoxSizer(wx.HORIZONTAL)
        this.specPosSizerH.Add(this.firstButton, 1, wx.EXPAND)
        this.specPosSizerH.Add(this.prevButton, 1, wx.EXPAND)
        this.specPosSizerH.Add(this.nextButton, 1, wx.EXPAND)
        this.specPosSizerH.Add(this.lastButton, 1, wx.EXPAND)
        this.specPosSizerV.Add(this.prePosGui, 10, wx.EXPAND)
        this.specPosSizerV.Add(this.specPosSizerH, 1, wx.EXPAND)

        # dynamic adjustments
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Dihedral Angle (Degrees)'))
        this.angleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        this.angleSizer.Add(this.angleGui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Fold 1 Angle (Degrees)'))
        this.fold1Sizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        this.fold1Sizer.Add(this.fold1Gui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Fold 2 Angle (Degrees)'))
        this.fold2Sizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        this.fold2Sizer.Add(this.fold2Gui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Offset T'))
        heightSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        heightSizer.Add(this.heightGui, 1, wx.EXPAND)

        mainVSizer = wx.BoxSizer(wx.VERTICAL)
        mainVSizer.Add(statSizer, 4, wx.EXPAND)
        mainVSizer.Add(this.specPosSizerV, 6, wx.EXPAND)
        mainVSizer.Add(this.angleSizer, 2, wx.EXPAND)
        mainVSizer.Add(this.fold1Sizer, 2, wx.EXPAND)
        mainVSizer.Add(this.fold2Sizer, 2, wx.EXPAND)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(mainVSizer, 6, wx.EXPAND)
        mainSizer.Add(heightSizer, 1, wx.EXPAND)

        this.errorStr = {
                'PosEdgeCfg': "ERROR: Impossible combination of position and edge configuration!"
            }

        return mainSizer

    def rmControlsSizer(this):
        #print "rmControlsSizer"
        # The 'try' is necessary, since the boxes are destroyed in some OS,
        # while this is necessary for Ubuntu Hardy Heron.
        for Box in this.Boxes:
            try:
                Box.Destroy()
            except wx._core.PyDeadObjectError: pass
        for Gui in this.Guis:
            Gui.Destroy()

    # move to general class
    def setDefaultSize(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

    def onAngle(this, event):
        this.shape.setAngle(Geom3D.Deg2Rad * this.angleGui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onFold1(this, event):
        this.shape.setFold1(Geom3D.Deg2Rad * this.fold1Gui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onFold2(this, event):
        this.shape.setFold2(Geom3D.Deg2Rad * this.fold2Gui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onHeight(this, event):
        this.shape.setHeight(float(this.maxHeight - this.heightGui.GetValue())/this.heightF)
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onApplySym(this, event):
        this.shape.applySymmetry = this.applySymGui.IsChecked()
        this.shape.updateShape = True
        this.canvas.paint()

    def onAddTriangles(this, event):
        this.shape.addTriangles  = this.addTrisGui.IsChecked()
        this.shape.updateShape = True
        this.canvas.paint()

    def onTriangleAlt(this, event):
        this.shape.setEdgeAlternative(this.trisAltGui.GetSelection())
        if this.prePosGui.GetSelection() != 0:
            this.onPrePos()
        else:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()

    def onFirst(this, event = None):
        print 'onFirst'
        this.specPosIndex = 0
        this.onPrePos()

    def onLast(this, event = None):
        this.specPosIndex = 0xefffffff
        print 'onLast'
        this.onPrePos()

    def onPrev(this, event = None):
        triangleAlt = this.trisAltGui.GetSelection()
        prePosIndex = this.prePosGui.GetSelection()
        if prePosIndex != 0:
            if this.specPosIndex > 0:
                this.specPosIndex -= 1
            #else:
            #    this.specPosIndex = len(this.specPos[prePosIndex][triangleAlt]) - 1
            this.onPrePos()

    def onNext(this, event = None):
        triangleAlt = this.trisAltGui.GetSelection()
        prePosIndex = this.prePosGui.GetSelection()
        if prePosIndex != 0:
            if this.specPosIndex < len(this.specPos[prePosIndex][triangleAlt]) - 1:
                this.specPosIndex += 1
            #else:
            #    this.specPosIndex = 0
            this.onPrePos()

    def onPrePos(this, event = None):
        sel = this.prePosGui.GetSelection()
        aVal = 0.0
        tVal = 1.0
        if sel != 0:
            selStr = this.prePosLst[sel]
            triangleAlt = this.trisAltGui.GetSelection()
            c = this.shape
            fld1 = 0.0
            fld2 = 0.0
            def EnsureInRange():
                # if this.specPosIndex not in range
                if (this.specPosIndex >= len(this.specPos[i][triangleAlt])):
                    this.specPosIndex = len(this.specPos[i][triangleAlt]) - 1
                elif (this.specPosIndex <  0):
                    this.specPosIndex = 0
            i = 1
            if selStr == this.prePosLst[i]:
                # 1, 1, 1, 1
                EnsureInRange()
                if triangleAlt <= c.T_STRIP_I or triangleAlt >= c.T_STAR :
                    tVal = this.specPos[i][triangleAlt][this.specPosIndex][0]
                    aVal = this.specPos[i][triangleAlt][this.specPosIndex][1]
                    fld1 = this.specPos[i][triangleAlt][this.specPosIndex][2]
                    fld2 = this.specPos[i][triangleAlt][this.specPosIndex][3]
                else:
                    pass
            i += 1
            if selStr == this.prePosLst[i]:
                # 1, 1, 1, 0
                EnsureInRange()
                if triangleAlt <= c.T_STRIP_I or triangleAlt >= c.T_STAR :
                    tVal = this.specPos[i][triangleAlt][this.specPosIndex][0]
                    aVal = this.specPos[i][triangleAlt][this.specPosIndex][1]
                    fld1 = this.specPos[i][triangleAlt][this.specPosIndex][2]
                    fld2 = this.specPos[i][triangleAlt][this.specPosIndex][3]
                else:
                    pass
            i += 1
            if selStr == this.prePosLst[i]:
                # 1, V2, 1, 0
                EnsureInRange()
                if triangleAlt == c.T_STRIP_II or triangleAlt == c.T_STAR :
                    tVal = this.specPos[i][triangleAlt][this.specPosIndex][0]
                    aVal = this.specPos[i][triangleAlt][this.specPosIndex][1]
                    fld1 = this.specPos[i][triangleAlt][this.specPosIndex][2]
                    fld2 = this.specPos[i][triangleAlt][this.specPosIndex][3]
            i += 1
            if selStr == this.prePosLst[i]:
                # 1, 1, V2, 1
                EnsureInRange()
                if not (triangleAlt == c.T_STRIP_II or triangleAlt == c.T_STRIP_1_LOOSE):
                    tVal = this.specPos[i][triangleAlt][this.specPosIndex][0]
                    aVal = this.specPos[i][triangleAlt][this.specPosIndex][1]
                    fld1 = this.specPos[i][triangleAlt][this.specPosIndex][2]
                    fld2 = this.specPos[i][triangleAlt][this.specPosIndex][3]
                else:
                    pass
            i += 1
            if selStr == this.prePosLst[i]:
                # 1, V2, 1, V2
                triangleAlt = c.T_STAR_1_LOOSE
                tVal = 1.293171427015779
                aVal = 1.130026556616254
                fld1 = -1.331025049020099
                fld2 = 1.724221601685890
                # triangleAlt = c.T_STAR_1_LOOSE
                # tVal = 1.389530133306510
                # aVal = 1.130026556616254
                # fld1 = 1.264497840465881
                # fld2 = -2.775882363308309

                # # 1, 1, V2, 1
                # triangleAlt = c.T_STAR
                # tVal =  -0.198822782925630
                # aVal = 2.903215967188777
                # fld1 = 1.561079993853316
                # fld2 = 2.478386842803094

            this.trisAltGui.SetSelection(triangleAlt)
            this.shape.setEdgeAlternative(triangleAlt)
            this.shape.setAngle(aVal)
            this.shape.setHeight(tVal)
            this.shape.setFold1(fld1)
            this.shape.setFold2(fld2)
            if (
                    selStr == '|a|=1 & |b|=1 & |c|=1 & |d|=0' and triangleAlt == c.T_STRIP_II
                    or
                    selStr == '|a|=1 & |b|=1 & |c|=1 & |d|=1' and triangleAlt == c.T_STRIP_II
                    or
                    selStr == '|a|=1 & |b|=1 & |c|=V2 & |d|=1' and (
                        triangleAlt == c.T_STRIP_II or triangleAlt == c.T_STRIP_1_LOOSE
                    )
                ):
                this.statusBar.SetStatusText('No solution for this triangle alternative')
            elif (
                    selStr == '|a|=1 & |b|=V2 & |c|=1 & |d|=0'
                    and
                    not (triangleAlt == c.T_STRIP_II or triangleAlt == c.T_STAR)
                    #or
                ):
                this.statusBar.SetStatusText('Doesnot mean anything special for this triangle alternative')
            else:
                this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)


