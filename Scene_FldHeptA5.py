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
#

import wx
import math
import re
import rgb
import Heptagons
import isometry
import Geom3D
import Scenes3D

from glob import glob
from OpenGL.GL import *

import geomtypes
from geomtypes import Rot3 as Rot
from geomtypes import Vec3 as Vec

TITLE = 'Polyhedra with Folded Regular Heptagons and Icosahedral Symmetry'

trisAlt = Heptagons.TrisAlt()
trisAlt.baseKey = {
    trisAlt.refl_1:    True,
    trisAlt.refl_2:    True,
    trisAlt.crossed_2: True
}

TA_1 = Heptagons.Def_TrisAlt(
    'TA_1',
    [
        Heptagons.TrisAlt_base.refl_1,
        Heptagons.TrisAlt_base.refl_2,
        Heptagons.TrisAlt_base.crossed_2,
        (Heptagons.TrisAlt_base.strip_I, Heptagons.TrisAlt_base.strip_I),
        (Heptagons.TrisAlt_base.strip_I, Heptagons.TrisAlt_base.strip_II),
        (Heptagons.TrisAlt_base.strip_I, Heptagons.TrisAlt_base.star),
        (Heptagons.TrisAlt_base.strip_I, Heptagons.TrisAlt_base.star_1_loose),
        (Heptagons.TrisAlt_base.strip_I, Heptagons.TrisAlt_base.strip_1_loose),

        (Heptagons.TrisAlt_base.strip_II, Heptagons.TrisAlt_base.strip_I),
        (Heptagons.TrisAlt_base.strip_II, Heptagons.TrisAlt_base.strip_II),
        (Heptagons.TrisAlt_base.strip_II, Heptagons.TrisAlt_base.star),
        (Heptagons.TrisAlt_base.strip_II, Heptagons.TrisAlt_base.star_1_loose),
        (Heptagons.TrisAlt_base.strip_II, Heptagons.TrisAlt_base.strip_1_loose),

        (Heptagons.TrisAlt_base.star, Heptagons.TrisAlt_base.strip_I),
        (Heptagons.TrisAlt_base.star, Heptagons.TrisAlt_base.strip_II),
        (Heptagons.TrisAlt_base.star, Heptagons.TrisAlt_base.star),
        (Heptagons.TrisAlt_base.star, Heptagons.TrisAlt_base.star_1_loose),
        (Heptagons.TrisAlt_base.star, Heptagons.TrisAlt_base.strip_1_loose)
    ]
)
trisAlts = [
    trisAlt,
    TA_1()
]

counter = Heptagons.Tris_counter()

dyn_pos       =  Heptagons.dyn_pos
open_file     =  Heptagons.open_file
only_hepts    =  Heptagons.only_hepts
all_eq_tris   =  counter.pp()
no_o3_tris    =  counter.pp()
T60_P12       =  counter.pp()
T140_P12      =  counter.pp()
T200          =  counter.pp()

Stringify = {
    dyn_pos:      'Enable Sliders',
    only_hepts:   'Just Heptagons',
    all_eq_tris:  'All 80 Triangles Equilateral',
    no_o3_tris:   '48 Triangles',
    T60_P12:      '60 Triangles and 12 Pentagons',
    T140_P12:     '140 Triangles and 12 Pentagons',
    T200:         '200 Triangles',
}

def Vlen(v0, v1):
    x = v1[0] - v0[0]
    y = v1[1] - v0[1]
    z = v1[2] - v0[2]
    return (math.sqrt(x*x + y*y + z*z))

V2 = math.sqrt(2)
V3 = math.sqrt(3)
V5 = math.sqrt(5)
tau = (1.0 + V5)/2
tau2 = tau + 1
dtau = 1.0/tau

isomA5 = isometry.A5()
o5axis = geomtypes.Vec([1, 0, tau])
o5fld = Rot(axis = o5axis, angle = geomtypes.turn(1.0/5))
_o5fld = Rot(axis = o5axis, angle = geomtypes.turn(-1.0/5))
isomO5 = isometry.C5(setup = {'axis': o5axis})

o3axis = geomtypes.Vec([0, dtau, tau])
o3fld = Rot(axis = o3axis, angle = geomtypes.THIRD_TURN)
isomO3 = isometry.C3(setup = {'axis': o3axis})

# get the col faces array by using a similar shape here, so it is calculated
# only once
colStabilisers = [
    isometry.A4(setup = {
        'o2axis0': [1.0, 0.0, 0.0],
        'o2axis1': [0.0, 0.0, 1.0],
    }),
    isometry.A4(setup = {
        'o2axis0': [1.0,  tau, tau2],
        'o2axis1': [tau, -tau2, 1.0],
    }),
]
colStabiliser = colStabilisers[1]
colQuotientSet = isomA5 / colStabiliser
useRgbCols = [
    rgb.indianRed,
    rgb.mediumBlue,
    rgb.limeGreen,
    rgb.cornflowerBlue,
    rgb.mistyRose1,
    rgb.gray20,
]
heptColPerIsom = []
for isom in isomA5:
    for subSet, i in zip(colQuotientSet, list(range(len(colQuotientSet)))):
        if isom in subSet:
            heptColPerIsom.append(([useRgbCols[i]], []))
            break;

class Shape(Heptagons.FldHeptagonShape):
    def __init__(this, *args, **kwargs):
        heptagonsShape = Geom3D.IsometricShape(
            Vs = [], Fs = [], directIsometries = isomA5,
            name = 'FoldedHeptagonsA5',
            recreateEdges = False
        )
        xtraTrisShape = Geom3D.IsometricShape(
            Vs = [], Fs = [], directIsometries = isomA5,
            name = 'xtraTrisA5',
            recreateEdges = False
        )
        trisO3Shape = Geom3D.SymmetricShape(
            Vs = [], Fs = [],
            finalSym = isomA5, stabSym = isomO3,
            colors = [([rgb.cyan[:]], [])],
            name = 'o3TrisA5',
            recreateEdges = False
        )
        trisO5Shape = Geom3D.SymmetricShape(
            Vs = [], Fs = [],
            finalSym = isomA5, stabSym = isomO5,
            colors = [([rgb.cyan[:]], [])],
            name = 'o5PentasA5',
            recreateEdges = False
        )
        Heptagons.FldHeptagonShape.__init__(this,
            [heptagonsShape, xtraTrisShape, trisO3Shape, trisO5Shape],
            5, 3,
            name = 'FoldedRegHeptA5xI'
        )
        this.heptagonsShape = heptagonsShape
        this.xtraTrisShape = xtraTrisShape
        this.trisO3Shape = trisO3Shape
        this.trisO5Shape = trisO5Shape
        this.posAngleMin = -math.pi/2
        this.posAngleMax = math.pi/2
        this.height = 2.7
        this.dihedralAngle = Geom3D.Deg2Rad * 119
        this.initArrs()
        this.setTriangleFillPosition(0)
        this.setEdgeAlternative(trisAlt.strip_II, trisAlt.strip_II)
        this.setV()

    def getStatusStr(this):
        #angle = Geom3D.Rad2Deg * this.dihedralAngle
        s = Heptagons.FldHeptagonShape.getStatusStr(this)
        if this.updateShape:
            #print 'getStatusStr: forced setV'
            this.setV()
        Vs = this.baseVs
        if this.inclReflections:
            Es = this.triEs[this.edgeAlternative]
            aLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
            bLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
            cLen = '%2.2f' % Vlen(Vs[Es[4]], Vs[Es[5]])
            dLen = '%2.2f' % Vlen(Vs[Es[6]], Vs[Es[7]])
        else:
            Es = this.triEs[this.edgeAlternative]
            aLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
            bLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
            cLen = '%2.2f' % Vlen(Vs[Es[4]], Vs[Es[5]])
            Es = this.o5triEs[this.edgeAlternative]
            dLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])

        if this.inclReflections:
            s = 'T = %02.2f; |a|: %s, |b|: %s, |c|: %s, |d|: %s' % (
                    this.height, aLen, bLen, cLen, dLen
                )
        else:
            Es = this.oppTriEs[this.oppEdgeAlternative]
            opp_bLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
            opp_cLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
            Es = this.o3triEs[this.oppEdgeAlternative]
            if this.oppEdgeAlternative != trisAlt.refl_1:
                opp_dLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
            else:
                opp_dLen = '-'
            s = 'T = %02.2f; |a|: %s, |b|: %s (%s), |c|: %s (%s), |d|: %s (%s)' % (
                    this.height,
                    aLen, bLen, opp_bLen, cLen, opp_cLen, dLen, opp_dLen
                )
        return s

    @property
    def nr_of_positions(this):
        return len(this.triFs_alts)

    def setTriangleFillPosition(this, i):
        this.triangleFillPosition = i
        this.triFs     = this.triFs_alts[i]
        this.triEs     = this.triEs_alts[i]
        this.oppTriFs  = this.oppTriFs_alts[i]
        this.oppTriEs  = this.oppTriEs_alts[i]
        this.o5triEs   = this.o5triEs_alts[i]
        this.o5triFs   = this.o5triFs_alts[i]
        this.o3triEs   = this.o3triEs_alts[i]
        this.o3triFs   = this.o3triFs_alts[i]
        this.triColIds = this.triColIds_alts[i]

    def setEdgeAlternative(this, alt = None, oppositeAlt = None):
        Heptagons.FldHeptagonShape.setEdgeAlternative(this, alt, oppositeAlt)

    def setV(this):
        #
        # o3:
        #     0 -> 9 -> 10
        #     6 -> 16 -> 17
        #     5 -> 22 -> 23
        #     4 -> 28 -> 29
        #     8 -> 34 -> 35
        #
        # o5: 0 -> 11 -> 12 -> 13 -> 14         centre: 44
        #     1 -> 18 -> 19 -> 20 -> 21
        #     2 -> 24 -> 25 -> 26 -> 27
        #     3 -> 30 -> 31 -> 32 -> 33
        #     6 -> 40 -> 41 -> 42 -> 43
        #     7 -> 36 -> 37 -> 38 -> 39
        #
        #                      o3
        #
        #
        #                      0
        #
        #               6             1
        #
        #
        #
        #             5                 2
        #
        #
        #    11'=15        4   .   3        11 = 0'   o5
        #                      o2
        #
        #         2' = 8                7 = 5'

        #print '  --> triangle fill alt', this.edgeAlternative, this.oppEdgeAlternative
        #print '  --> triangle fill pos', this.triangleFillPosition
        #print '  --> fold1', this.fold1, this.oppFold1
        #print '  --> fold2', this.fold2, this.oppFold2
        #print '  --> height', this.height
        #print '  --> dihedralAngle', this.dihedralAngle
        #print '  --> posAngle', this.posAngle
        #print '------Shape.setV--------------------'

        this.posHeptagon()
        Vs = this.heptagon.Vs[:]
        Vs.append(Vec([-Vs[5][0], -Vs[5][1], Vs[5][2]]))        # Vs[7]
        Vs.append(Vec([-Vs[2][0], -Vs[2][1], Vs[2][2]]))        # Vs[8]
        Vs.append(o3fld * Vs[0])                                # Vs[9]
        Vs.append(o3fld * Vs[-1])                               # Vs[10]
        Vs.append(o5fld * Vs[0])                                # Vs[11]
        Vs.append(o5fld * Vs[-1])                               # Vs[12]
        Vs.append(o5fld * Vs[-1])                               # Vs[13]
        Vs.append(o5fld * Vs[-1])                               # Vs[14]
        Vs.append(Vec([-Vs[11][0], -Vs[11][1], Vs[11][2]]))     # Vs[15]
        Vs.append(o3fld * Vs[6])                                # Vs[16]
        Vs.append(o3fld * Vs[-1])                               # Vs[17]
        Vs.append(o5fld * Vs[1])                                # Vs[18]
        Vs.append(o5fld * Vs[-1])                               # Vs[19]
        Vs.append(o5fld * Vs[-1])                               # Vs[20]
        Vs.append(o5fld * Vs[-1])                               # Vs[21]
        Vs.append(o3fld * Vs[5])                                # Vs[22]
        Vs.append(o3fld * Vs[-1])                               # Vs[23]
        Vs.append(o5fld * Vs[2])                                # Vs[24]
        Vs.append(o5fld * Vs[-1])                               # Vs[25]
        Vs.append(o5fld * Vs[-1])                               # Vs[26]
        Vs.append(o5fld * Vs[-1])                               # Vs[27]
        Vs.append(o3fld * Vs[4])                                # Vs[28]
        Vs.append(o3fld * Vs[-1])                               # Vs[29]
        Vs.append(o5fld * Vs[3])                                # Vs[30]
        Vs.append(o5fld * Vs[-1])                               # Vs[31]
        Vs.append(o5fld * Vs[-1])                               # Vs[32]
        Vs.append(o5fld * Vs[-1])                               # Vs[33]
        Vs.append(o3fld * Vs[8])                                # Vs[34]
        Vs.append(o3fld * Vs[-1])                               # Vs[35]
        Vs.append(o5fld * Vs[7])                                # Vs[36]
        Vs.append(o5fld * Vs[-1])                               # Vs[37]
        Vs.append(o5fld * Vs[-1])                               # Vs[38]
        Vs.append(o5fld * Vs[-1])                               # Vs[39]
        Vs.append(o5fld * Vs[6])                                # Vs[40]
        Vs.append(o5fld * Vs[-1])                               # Vs[41]
        Vs.append(o5fld * Vs[-1])                               # Vs[42]
        Vs.append(o5fld * Vs[-1])                               # Vs[43]
        Vs.append((Vs[0] + Vs[11] + Vs[12] + Vs[13] + Vs[14])/5)# Vs[44]
        # TODO: if adding more Vs, rm above if or use predefined indices
        this.baseVs = Vs
        Es = []
        Fs = []
        Fs.extend(this.heptagon.Fs) # use extend to copy the list to Fs
        Es.extend(this.heptagon.Es) # use extend to copy the list to Fs
        this.heptagonsShape.setBaseVertexProperties(Vs = Vs)
        this.heptagonsShape.setBaseEdgeProperties(Es = Es)
        # TODO CHk: comment out this and nvidia driver crashes:...
        this.heptagonsShape.setBaseFaceProperties(Fs = Fs)
        this.heptagonsShape.setFaceColors(heptColPerIsom)
        theShapes = [this.heptagonsShape]
        if this.addXtraFs:
            assert this.edgeAlternative in this.o5triFs, \
                "this triangle fill isn't implemented for A5"
            Fs = this.o5triFs[this.edgeAlternative][:]
            Es = this.o5triEs[this.edgeAlternative][:]
            this.trisO5Shape.setBaseVertexProperties(Vs = Vs)
            this.trisO5Shape.setBaseEdgeProperties(Es = Es)
            this.trisO5Shape.setBaseFaceProperties(Fs = Fs)
            theShapes.append(this.trisO5Shape)
            Es = this.o3triEs[this.oppEdgeAlternative][:]
            Fs = this.o3triFs[this.oppEdgeAlternative][:]
            this.trisO3Shape.setBaseVertexProperties(Vs = Vs)
            this.trisO3Shape.setBaseEdgeProperties(Es = Es)
            this.trisO3Shape.setBaseFaceProperties(Fs = Fs)
            theShapes.append(this.trisO3Shape)
            if (not this.onlyRegFs):
                # when you use the rot alternative the rot is leading for
                # choosing the colours.
                if this.triangleFillPosition == 0:
                    if this.oppEdgeAlternative & Heptagons.rot_bit:
                        eAlt = this.oppEdgeAlternative
                    else:
                        eAlt = this.edgeAlternative
                    colIds = this.triColIds[eAlt]
                else:
                    colIds = this.triColIds[this.edgeAlternative][:3]
                    colIds.extend(this.triColIds[this.oppEdgeAlternative][3:])
                Fs = this.triFs[this.edgeAlternative][:]
                Fs.extend(this.oppTriFs[this.oppEdgeAlternative])
                Es = this.triEs[this.edgeAlternative][:]
                Es.extend(this.oppTriEs[this.oppEdgeAlternative])
                this.xtraTrisShape.setBaseVertexProperties(Vs = Vs)
                this.xtraTrisShape.setBaseEdgeProperties(Es = Es)
                this.xtraTrisShape.setBaseFaceProperties(
                    Fs = Fs,
                    colors = ([rgb.darkRed[:], rgb.yellow[:], rgb.magenta[:]],
                        colIds
                    )
                )
                theShapes.append(this.xtraTrisShape)
        for shape in theShapes:
            shape.showBaseOnly = not this.applySymmetry
        this.setShapes(theShapes)
        #rad = this.getRadii()
        #print 'min radius:', rad[0], 'max radius:', rad[1]
        this.updateShape = False
        #print 'V0 = (%.4f, %.4f, %.4f)' % (Vs[0][0], Vs[0][1], Vs[0][2])
        #print 'V1 = (%.4f, %.4f, %.4f)' % (Vs[1][0], Vs[1][1], Vs[1][2])
        #print 'V2 = (%.4f, %.4f, %.4f)' % (Vs[2][0], Vs[2][1], Vs[2][2])
        #print 'V3 = (%.4f, %.4f, %.4f)' % (Vs[3][0], Vs[3][1], Vs[3][2])
        #print 'V4 = (%.4f, %.4f, %.4f)' % (Vs[4][0], Vs[4][1], Vs[4][2])
        #print 'V5 = (%.4f, %.4f, %.4f)' % (Vs[5][0], Vs[5][1], Vs[5][2])
        #print 'V6 = (%.4f, %.4f, %.4f)' % (Vs[6][0], Vs[6][1], Vs[6][2])

    def initArrs(this):

        #
        # o3:
        #     0 -> 9 -> 10
        #     6 -> 16 -> 17
        #     5 -> 22 -> 23
        #     4 -> 28 -> 29
        #     8 -> 34 -> 35
        #
        # o5: 0 -> 11 -> 12 -> 13 -> 14
        #     1 -> 18 -> 19 -> 20 -> 21
        #     2 -> 24 -> 25 -> 26 -> 27
        #     3 -> 30 -> 31 -> 32 -> 33
        #     6 -> 40 -> 41 -> 42 -> 43
        #     7 -> 36 -> 37 -> 38 -> 39
        #
        #                      o3
        #
        #
        #                      0
        #
        #               6             1
        #
        #
        #
        #             5                 2
        #
        #
        #    11'=15        4   .   3        11 = 0'   o5
        #                      o2
        #
        #         2' = 8                7 = 5'

        # Triangles:
        # alternative fill 0:
        I_loose   = [[2, 3, 7]]
        noLoose   = [[2, 3, 11]]
        stripI    = [[2, 11, 18]]
        stripII   = [[2, 3, 18], [3, 11, 18]]
        star      = [[1, 2, 11], [1, 11, 18]]
        refl_1    = [[2, 3, 7], [1, 2, 39, 16], [0, 1, 16, 9]]
        refl_2    = [[4, 5, 8], [5, 6, 21, 34], [6, 0, 14, 21]]
        crossed_2 = [[29, 4, 5, 35], [5, 26, 35], [5, 6, 20, 26], [6, 0, 13, 20]]
        strip_1_loose = stripI[:]
        star_1_loose  = star[:]
        stripI.extend(noLoose)
        star.extend(noLoose)
        strip_1_loose.extend(I_loose)
        star_1_loose.extend(I_loose)
        this.triFs_alts = []
        triFs = {
                trisAlt.strip_1_loose:      strip_1_loose[:],
                trisAlt.strip_I:            stripI[:],
                trisAlt.strip_II:           stripII[:],
                trisAlt.star:               star[:],
                trisAlt.star_1_loose:       star_1_loose[:],
                trisAlt.alt_strip_1_loose:  strip_1_loose[:],
                trisAlt.alt_strip_I:        stripI[:],
                trisAlt.alt_strip_II:       stripII[:],
                trisAlt.refl_1:             refl_1[:],
                trisAlt.refl_2:             refl_2[:],
                trisAlt.crossed_2:          crossed_2[:],
        }
        stdO5 = [1, 2, 18]
        altO5 = [2, 18, 24]
        triFs[trisAlt.strip_1_loose].append(stdO5)
        triFs[trisAlt.strip_I].append(stdO5)
        triFs[trisAlt.strip_II].append(stdO5)
        triFs[trisAlt.alt_strip_1_loose].append(altO5)
        triFs[trisAlt.alt_strip_I].append(altO5)
        triFs[trisAlt.alt_strip_II].append(altO5)
        this.triFs_alts.append(triFs)
        strip_1_loose = [2, 7, 2, 11, 2, 18]
        stripI        = [3, 11, 2, 11, 2, 18]
        stripII       = [3, 11, 3, 18, 2, 18]
        star          = [3, 11, 2, 11, 1, 11]
        star_1_loose  = [2, 7, 2, 11, 1, 11]
        refl_1        = [2, 7, 2, 39, 1, 16, 0, 9]
        refl_2        = [5, 8, 5, 34, 6, 21, 0, 14]
        crossed_2     = [4, 28, 5, 35, 5, 26, 6, 20, 0, 13]
        this.triEs_alts = []
        this.triEs_alts.append({
                trisAlt.strip_1_loose:     strip_1_loose,
                trisAlt.strip_I:           stripI,
                trisAlt.strip_II:          stripII,
                trisAlt.star:              star,
                trisAlt.star_1_loose:      star_1_loose,
                trisAlt.alt_strip_I:       stripI,
                trisAlt.alt_strip_II:      stripII,
                trisAlt.alt_strip_1_loose: strip_1_loose,
                trisAlt.refl_1:            refl_1,
                trisAlt.refl_2:            refl_2,
                trisAlt.crossed_2:         crossed_2,
            })
        # alternative fill 1:
        stripI = [[1, 40, 11], [1, 2, 40], [0, 1, 11]] # middle, centre, o3
        stripII = [[2, 11, 1], [2, 40, 11], [0, 1, 11]]
        star = [[0, 1, 40], [1, 2, 40], [0, 40, 11]]
        triFs = {
                trisAlt.strip_I:     stripI[:],
                trisAlt.strip_II:    stripII[:],
                trisAlt.star:        star[:],
                trisAlt.refl_1:      this.triFs_alts[0][trisAlt.refl_1],
                trisAlt.refl_2:      this.triFs_alts[0][trisAlt.refl_2],
                trisAlt.crossed_2:   this.triFs_alts[0][trisAlt.crossed_2]
            }
        this.triFs_alts.append(triFs)
        stripI = [2, 40, 1, 40, 1, 11]
        stripII = [2, 40, 2, 11, 1, 11]
        star = [2, 40, 1, 40, 0, 40]
        this.triEs_alts.append({
                trisAlt.strip_I:     stripI,
                trisAlt.strip_II:    stripII,
                trisAlt.star:        star,
                trisAlt.refl_1:      this.triEs_alts[0][trisAlt.refl_1],
                trisAlt.refl_2:      this.triEs_alts[0][trisAlt.refl_2],
                trisAlt.crossed_2:   this.triEs_alts[0][trisAlt.crossed_2]
            })

        # Triangles: opposite
        # alternative fill 0:
        # TODO rot variants,.. also for roots_batch
        I_loose = [[5, 15, 8]]
        noLoose = [[3, 7, 11]]
        stripI  = [[5, 17, 15]]
        stripII = [[4, 5, 17], [4, 17, 15]]
        star    = [[5, 6, 15], [6, 17, 15]]
        rot     = [[13, 17, 14]]
        strip_1_loose = stripI[:]
        star_1_loose  = star[:]
        rot_strip     = rot[:]
        rot_star      = rot[:]
        arot_star     = rot[:]
        refl          = []
        stripI.extend(noLoose)
        star.extend(noLoose)
        strip_1_loose.extend(I_loose)
        star_1_loose.extend(I_loose)
        rot_strip.append([13, 5, 17])
        rot_star.append([13, 5, 6])
        arot_star.append([13, 17, 17]) # <----- oops cannot be right
        this.oppTriFs_alts = []
        oppTriFs = {
                trisAlt.strip_1_loose:      strip_1_loose[:],
                trisAlt.strip_I:            stripI[:],
                trisAlt.strip_II:           stripII[:],
                trisAlt.star:               star[:],
                trisAlt.star_1_loose:       star_1_loose[:],
                trisAlt.alt_strip_1_loose:  strip_1_loose[:],
                trisAlt.alt_strip_I:        stripI[:],
                trisAlt.alt_strip_II:       stripII[:],
                trisAlt.rot_strip_1_loose:  rot_strip[:],
                trisAlt.arot_strip_1_loose: rot_strip[:],
                trisAlt.rot_star_1_loose:   rot_star[:],
                trisAlt.arot_star_1_loose:  arot_star[:],
                trisAlt.refl_1:             refl[:],
                trisAlt.refl_2:             refl[:],
                trisAlt.crossed_2:          refl[:],
        }
        stdO3   = [6, 17, 5]
        stdO3_x = [6, 17, 13]
        altO3   = [5, 23, 17]
        altO3_x = [5, 17, 13]
        oppTriFs[trisAlt.strip_1_loose].append(stdO3)
        oppTriFs[trisAlt.strip_I].append(stdO3)
        oppTriFs[trisAlt.strip_II].append(stdO3)
        oppTriFs[trisAlt.alt_strip_1_loose].append(altO3)
        oppTriFs[trisAlt.alt_strip_I].append(altO3)
        oppTriFs[trisAlt.alt_strip_II].append(altO3)
        oppTriFs[trisAlt.rot_strip_1_loose].append(stdO3)
        oppTriFs[trisAlt.arot_strip_1_loose].append(altO3)
        oppTriFs[trisAlt.rot_star_1_loose].append(stdO3_x)
        oppTriFs[trisAlt.arot_star_1_loose].append(altO3_x)
        this.oppTriFs_alts.append(oppTriFs)
        strip_1_loose = [5, 15, 5, 17]
        stripI        = [5, 15, 5, 17]
        stripII       = [4, 17, 5, 17]
        star          = [5, 15, 6, 15]
        star_1_loose  = [5, 15, 6, 15]
        rot_strip     = [13, 15, 5, 15]
        rot_star      = [13, 15, 6, 13]
        arot_star     = [13, 15, 13, 17]
        refl          = []
        this.oppTriEs_alts = []
        this.oppTriEs_alts.append({
                trisAlt.strip_1_loose:      strip_1_loose,
                trisAlt.strip_I:            stripI,
                trisAlt.strip_II:           stripII,
                trisAlt.star:               star,
                trisAlt.star_1_loose:       star_1_loose,
                trisAlt.alt_strip_I:        stripI,
                trisAlt.alt_strip_II:       stripII,
                trisAlt.alt_strip_1_loose:  strip_1_loose,
                trisAlt.rot_strip_1_loose:  rot_strip,
                trisAlt.arot_strip_1_loose: rot_strip,
                trisAlt.rot_star_1_loose:   rot_star,
                trisAlt.arot_star_1_loose:  arot_star,
                trisAlt.refl_1:             refl,
                trisAlt.refl_2:             refl,
                trisAlt.crossed_2:          refl,
            })
        # alternative fill 1:
        # middle, centre, o5
        stripI        = [[4, 23, 17], [2, 3, 40], [5, 23, 4]]
        stripII       = [[8, 4, 23], [23, 17, 8], [5, 23, 4]]
        star          = [[4, 5, 17], [8, 4, 17], [5, 23, 17]]
        star_1_loose  = [[8, 5, 17], [5, 8, 4], [5, 23, 17]]
        strip_1_loose = [[8, 5, 23], [5, 8, 4], [8, 23, 17]]
        oppTriFs = {
                trisAlt.strip_I:       stripI[:],
                trisAlt.strip_II:      stripII[:],
                trisAlt.star:          star[:],
                trisAlt.star_1_loose:  star_1_loose[:],
                trisAlt.strip_1_loose: strip_1_loose[:],
                trisAlt.refl_1:        this.oppTriFs_alts[0][trisAlt.refl_1],
                trisAlt.refl_2:        this.oppTriFs_alts[0][trisAlt.refl_2],
                trisAlt.crossed_2:     this.oppTriFs_alts[0][trisAlt.crossed_2]
        }
        this.oppTriFs_alts.append(oppTriFs)
        stripI        = [4, 17, 4, 23]
        stripII       = [8, 23, 4, 23]
        star          = [4, 17, 5, 17]
        star_1_loose  = [5, 8, 5, 17]
        strip_1_loose = [5, 8, 8, 23]
        this.oppTriEs_alts.append({
                trisAlt.strip_I:       stripI,
                trisAlt.strip_II:      stripII,
                trisAlt.star:          star,
                trisAlt.star_1_loose:  star_1_loose[:],
                trisAlt.strip_1_loose: strip_1_loose[:],
                trisAlt.refl_1:        this.oppTriEs_alts[0][trisAlt.refl_1],
                trisAlt.refl_2:        this.oppTriEs_alts[0][trisAlt.refl_2],
                trisAlt.crossed_2:     this.oppTriEs_alts[0][trisAlt.crossed_2]
            })

        # Colours:
        strip      = [0, 1, 1, 1, 0, 0]
        loose      = [0, 0, 1, 0, 1, 1]
        star1loose = [0, 1, 0, 0, 1, 1]
        rot        = [1, 0, 0, 0, 1, 0]
        rot_x      = [0, 0, 1, 1, 1, 0]
        arot_x     = [1, 1, 0, 0, 1, 0]
        refl_1     = [1, 1, 0]
        refl_2     = [1, 1, 0]
        crossed_2  = [1, 0, 1, 0]
        this.triColIds_alts = []
        this.triColIds_alts.append({
                trisAlt.strip_1_loose:          loose,
                trisAlt.strip_I:                strip,
                trisAlt.strip_II:               strip,
                trisAlt.star:                   strip,
                trisAlt.star_1_loose:           star1loose,
                trisAlt.alt_strip_I:            strip,
                trisAlt.alt_strip_II:           strip,
                trisAlt.alt_strip_1_loose:      loose,
                trisAlt.rot_strip_1_loose:      rot,
                trisAlt.arot_strip_1_loose:     rot,
                trisAlt.rot_star_1_loose:       rot_x,
                trisAlt.arot_star_1_loose:      arot_x,
                trisAlt.refl_1:                 refl_1,
                trisAlt.refl_2:                 refl_2,
                trisAlt.crossed_2:              crossed_2,
            })
        # alternative fill 1:
        star1loose = [0, 1, 0, 0, 1, 1]
        this.triColIds_alts.append({
                trisAlt.strip_I:       strip,
                trisAlt.strip_II:      strip,
                trisAlt.star:          strip,
                trisAlt.star_1_loose:  star1loose,
                trisAlt.strip_1_loose: strip,
                trisAlt.refl_1:        refl_1,
                trisAlt.refl_2:        refl_2,
                trisAlt.crossed_2:     crossed_2,
            })

        # O5
        # alternative fill 0:
        std  = [1, 18, 19, 20, 21]
        alt  = [2, 24, 25, 26, 27]
        refl_1 = [2, 7, 24, 36, 25, 37, 26, 38, 27, 39]
        refl_2 = [0, 11, 12, 13, 14]
        crossed_2 = [
                [0, 12, 44], [12, 14, 44], [14, 11, 44], [11, 13, 44],
                [13, 0, 44]
        ]
        this.o5triFs_alts = []
        this.o5triFs_alts.append({
                trisAlt.strip_1_loose:          [std],
                trisAlt.strip_I:                [std],
                trisAlt.strip_II:               [std],
                trisAlt.star:                   [std],
                trisAlt.star_1_loose:           [std],
                trisAlt.alt_strip_I:            [alt],
                trisAlt.alt_strip_II:           [alt],
                trisAlt.alt_strip_1_loose:      [alt],
                trisAlt.rot_strip_1_loose:      [std],
                trisAlt.arot_strip_1_loose:     [alt],
                trisAlt.rot_star_1_loose:       [std],
                trisAlt.arot_star_1_loose:      [alt],
                trisAlt.refl_1:                 [refl_1],
                trisAlt.refl_2:                 [refl_2],
                trisAlt.crossed_2:              crossed_2,
            })
        std    = [1, 18, 18, 19, 19, 20, 20, 21, 21, 1]
        alt    = [2, 24, 24, 25, 25, 26, 26, 27, 27, 2]
        refl   = []
        this.o5triEs_alts = []
        this.o5triEs_alts.append({
                trisAlt.strip_1_loose:      std,
                trisAlt.strip_I:            std,
                trisAlt.strip_II:           std,
                trisAlt.star:               std,
                trisAlt.star_1_loose:       std,
                trisAlt.alt_strip_I:        alt,
                trisAlt.alt_strip_II:       alt,
                trisAlt.alt_strip_1_loose:  alt,
                trisAlt.rot_strip_1_loose:  std,
                trisAlt.arot_strip_1_loose: alt,
                trisAlt.rot_star_1_loose:   std,
                trisAlt.arot_star_1_loose:  alt,
                trisAlt.refl_1:             refl,
                trisAlt.refl_2:             refl,
                trisAlt.crossed_2:          refl,
            })
        # alternative fill 1:
        o5 = [0, 11, 12, 13, 14]
        this.o5triFs_alts.append({
                trisAlt.strip_I:      [o5],
                trisAlt.strip_II:     [o5],
                trisAlt.star:         [o5],
                trisAlt.refl_1:       this.o5triFs_alts[0][trisAlt.refl_1],
                trisAlt.refl_2:       this.o5triFs_alts[0][trisAlt.refl_2],
                trisAlt.crossed_2:    this.o5triFs_alts[0][trisAlt.crossed_2]
            })
        o5    = [0, 11, 11, 12, 12, 13, 13, 14, 14, 0]
        this.o5triEs_alts.append({
                trisAlt.strip_I:      o5,
                trisAlt.strip_II:     o5,
                trisAlt.star:         o5,
                trisAlt.refl_1:       this.o5triEs_alts[0][trisAlt.refl_1],
                trisAlt.refl_2:       this.o5triEs_alts[0][trisAlt.refl_2],
                trisAlt.crossed_2:    this.o5triEs_alts[0][trisAlt.crossed_2]
            })

        # O3 ( = opposite)
        # alternative fill 0:
        std    = [6, 16, 17]
        alt    = [5, 22, 23]
        refl_1 = [0, 9, 10]
        refl_2 = [5, 34, 22, 35, 23, 8]
        crossed_2 = [4, 28, 29]
        this.o3triFs_alts = []
        this.o3triFs_alts.append({
                trisAlt.strip_1_loose:          [std],
                trisAlt.strip_I:                [std],
                trisAlt.strip_II:               [std],
                trisAlt.star:                   [std],
                trisAlt.star_1_loose:           [std],
                trisAlt.alt_strip_I:            [alt],
                trisAlt.alt_strip_II:           [alt],
                trisAlt.alt_strip_1_loose:      [alt],
                # TODO
                trisAlt.rot_strip_1_loose:      [],
                trisAlt.arot_strip_1_loose:     [],
                trisAlt.rot_star_1_loose:       [],
                trisAlt.arot_star_1_loose:      [],
                trisAlt.refl_1:                 [refl_1],
                trisAlt.refl_2:                 [refl_2],
                trisAlt.crossed_2:              [crossed_2],
            })
        std  = [6, 16, 16, 17, 17, 6]
        alt  = [5, 22, 22, 23, 23, 5]
        refl = []
        this.o3triEs_alts = []
        this.o3triEs_alts.append({
                trisAlt.strip_1_loose:      std,
                trisAlt.strip_I:            std,
                trisAlt.strip_II:           std,
                trisAlt.star:               std,
                trisAlt.star_1_loose:       std,
                trisAlt.alt_strip_I:        alt,
                trisAlt.alt_strip_II:       alt,
                trisAlt.alt_strip_1_loose:  alt,
                # TODO
                trisAlt.rot_strip_1_loose:  [],
                trisAlt.arot_strip_1_loose: [],
                trisAlt.rot_star_1_loose:   [],
                trisAlt.arot_star_1_loose:  [],
                trisAlt.refl_1:             refl,
                trisAlt.refl_2:             refl,
                trisAlt.crossed_2:          refl,
            })
        # alternative fill 1:
        o3 = [5, 22, 23]
        this.o3triFs_alts.append({
                trisAlt.strip_I:       [o3],
                trisAlt.strip_II:      [o3],
                trisAlt.star:          [o3],
                trisAlt.star_1_loose:  [o3],
                trisAlt.strip_1_loose: [o3],
                trisAlt.refl_1:        this.o3triFs_alts[0][trisAlt.refl_1],
                trisAlt.refl_2:        this.o3triFs_alts[0][trisAlt.refl_2],
                trisAlt.crossed_2:     this.o3triFs_alts[0][trisAlt.crossed_2]
            })
        o3  = [5, 22, 22, 23, 23, 5]
        this.o3triEs_alts.append({
                trisAlt.strip_I:       o3,
                trisAlt.strip_II:      o3,
                trisAlt.star:          o3,
                trisAlt.star_1_loose:  o3,
                trisAlt.strip_1_loose: o3,
                trisAlt.refl_1:        this.o3triEs_alts[0][trisAlt.refl_1],
                trisAlt.refl_2:        this.o3triEs_alts[0][trisAlt.refl_2],
                trisAlt.crossed_2:     this.o3triEs_alts[0][trisAlt.crossed_2]
            })

class CtrlWin(Heptagons.FldHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
        Heptagons.FldHeptagonCtrlWin.__init__(this,
            shape, canvas,
            12, # maxHeigth
            [ # prePosLst
                Stringify[only_hepts],
                Stringify[dyn_pos],
                Stringify[T60_P12],
                Stringify[T140_P12],
                Stringify[T200],
            ],
            isometry.A5,
            trisAlts,
            Stringify,
            *args, **kwargs
        )

    def showOnlyHepts(this):
        return this.prePos == only_hepts and not (
                this.trisFill == None
            ) and not (
                this.trisFill == trisAlt.refl_1 or
                this.trisFill == trisAlt.refl_2 or
                this.trisFill == trisAlt.crossed_2
            )

    def showOnlyO3Tris(this):
        return this.prePos == Heptagons.only_xtra_o3s and not (
                this.trisFill == None
            ) and not (
                this.trisFill == trisAlt.refl_1 or
                this.trisFill == trisAlt.refl_2 or
                this.trisFill == trisAlt.crossed_2
            )

    rDir = 'data/Data_FldHeptA5'
    rPre = 'frh-roots'

    def printFileStrMapWarning(this, filename, funcname):
        print('%s:' % funcname)
        print('  WARNING: unable to interprete filename', filename)

    @property
    def specPosSetup(this):
        prePosId = this.prePos
        if prePosId != open_file and prePosId != dyn_pos:
            # use correct predefined special positions
            if this.shape.inclReflections:
                psp = this.predefReflSpecPos
            else:
                psp = this.predefRotSpecPos
            if this.specPosIndex >= len(psp[this.prePos]):
                this.specPosIndex = -1
            data = psp[this.prePos][this.specPosIndex]
            if 'file' in data:
                print('see file %s/%s' % (this.rDir, data['file']))
            return data

    predefReflSpecPos = {
        only_hepts: [
            {
                #'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_1-pos-0.py'
                'set': [2.59804095112, 0.07208941199, -0.07223544999, 2.53866531680],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.refl_1,
            },{
                #'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_2-pos-0.py'
                'set': [3.54099634761, 0.46203434348, -0.50537193698, 2.35569911915, 1.57079632679],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.refl_2,
            },{
                #'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_1-pos-0.py'
                'set': [2.59967616789, 0.00000000000, 0.11360610699, 2.44771371251],
                '7fold': Heptagons.foldMethod.triangle,
                'tris': trisAlt.refl_1,
            },{
                #'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_1-pos-0.py'
                'set': [2.59967616789, -0.00000000000, 2.29825889037, 0.69387894108],
                '7fold': Heptagons.foldMethod.triangle,
                'tris': trisAlt.refl_1,
            },{
                #'file': 'frh-roots-0_0_0_0-fld_w.0-refl_1-pos-0.py'
                'set': [0.78019870723, 2.64930187805, 0.54062307364, 0.00913464936],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.refl_1,
            },{
                #'file': 'frh-roots-0_0_0_0-fld_w.0-refl_1-pos-0.py'
                'set': [2.56440119971, 0.06605029302, -0.42550124895, 0.64274301662],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.refl_1,
            },{
                #'file': 'frh-roots-0_0_0_0-fld_w.0-refl_2-pos-0.py'
                'set': [3.41692468489, 0.40788151929, -0.96765917562, 0.84720346804, 1.57079632679],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.refl_2,
            },{
                #'file': 'frh-roots-0_0_0_0-fld_w.0-refl_2-pos-0.py'
                'set': [-0.78796389438, 2.77826685391, 1.16636078799, 2.12574368211, 1.57079632679],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.refl_2,
            }
        ],
        T60_P12: [
            {
                #'file': 'frh-roots-0_0_0_1-fld_w.0-refl_2-pos-0.py'
                'set': [1.596941118660, 2.593080381370, 0.403913171960, 0.449605194880, 1.5707963268
                ],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.refl_2,
            },{
                #'file': 'frh-roots-0_0_0_1-fld_shell.0-refl_2-pos-0.py'
                'set': [1.655881786380, 2.578935099880, 0.646433762790, -0.461827521280, 1.5707963268
                ],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.refl_2,
            },{
                #'file': 'frh-roots-0_0_0_1-fld_shell.0-refl_2-pos-0.py'
                'set': [1.655881786380, 2.578935099880, 0.646433762790, -2.317062680690, 1.5707963268
                ],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.refl_2,
            },{
                #'file': 'frh-roots-0_0_0_1-fld_shell.0-refl_2-pos-0.py'
                'set': [3.722764049900, -0.024061600030, 0.024067017100, 1.458692444820, 1.5707963268
                ],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.refl_2,
            }
        ],
    }
    predefRotSpecPos = {
        only_hepts: [
            {
                #'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.0-shell-opp_strip_II-pos-1.py '
                'set': [2.190643133767, 0.0, -2.750194494870, 1.320518652645, 0.080811779365, 1.327501379252, 1.320518652644],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.shell_strip_II,
                'tris-pos': 1
            },{
                #'file': frh-roots-1_0_1_0_0_1_0-fld_w.1-strip_II-opp_shell-pos-1.py
                'set': [2.2398383815253, 1.538134037316, -1.753834771439, 2.220230723671, 0.6077158322698, -1.7538347714391, -0.1073726559505],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 1
            },{
                #'file': frh-roots-1_0_1_0_0_1_0-fld_w.1-strip_II-opp_shell-pos-1.py
                'set': [2.5964060652451, 0.6303582297009, -1.7538347714387, 2.8348162453136, 0.3892552426313, -1.7538347714394, 1.4996710788234],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 1
            },{
                #'file': frh-roots-1_0_1_0_0_1_0-fld_w.1-strip_II-opp_shell-pos-1.py
                'set': [2.5964060652451, 0.6303582297009, -1.7538347714387, 2.8348162453136, 0.3892552426313, -1.7538347714394, 1.4996710788234],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 1
            },{
                #'file': frh-roots-1_0_1_0_0_1_0-fld_w.1-strip_II-opp_shell-pos-1.py
                'set': [1.5146302263609, -2.3128908096943, -1.753834771439, -1.8766503426196, -0.4739245692867, -1.753834771439, 1.9319622451753],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 1
            },{
                #'file': frh-roots-1_0_1_0_0_1_0-fld_w.1-strip_II-opp_shell-pos-1.py
                'set': [1.5146302263604, -2.3128908096942, 1.7538347714387, 1.1330038160007, -0.4739245692867, 1.7538347714397, -1.3415689033837],
                '7fold': Heptagons.foldMethod.w,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 1
            }
        ],
        T60_P12: [
            {
                #'file': 'frh-roots-0_1_0_1_1_1_0-fld_shell.0-strip_II-opp_shell-pos-1.py'
                'set': [3.567397972268, 0.577608713844, -0.805085622072, -1.564973557413, 0.802103304585, 0.794585079662, 2.557585428357
                ],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1
            }
        ],
        T200: [
            {
                #'file': 'frh-roots-1_0_1_0_1_1_1-fld_shell.0-shell-opp_strip_II-pos-1.py'
                'set': [4.142695742002, 1.124949218194, 0.821407938281, 3.141592653589, 1.570796326795, -0.566349943870, 0.910396047071
                ],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.shell_strip_II,
                'tris-pos': 1
            },{
                #'file': 'frh-roots-1_0_1_0_1_1_1-fld_shell.0-shell-opp_strip_II-pos-1.py'
                'set': [4.142695742003, 1.124949218194, -1.954107826020, 1.286357494175, 1.570796326795, -0.566349943869, -0.944839112344
                ],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.shell_strip_II,
                'tris-pos': 1
            },{
                #'file': 'frh-roots-1_0_1_0_1_1_1-fld_shell.0-shell-opp_strip_II-pos-1.py'
                'set': [2.504073272511, 1.943327879806, 2.108843675970, -1.286357494175, 1.570796326795, 0.721085793819, -0.509380996152
                ],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.shell_strip_II,
                'tris-pos': 1
            },
        ],
        T140_P12: [
            {
                #'file': 'frh-roots-0_1_0_1_1_1_1-fld_shell.0-strip_II-opp_strip_II-pos-1.py'
                'set': [4.389693800678, 1.613882084912, 0.259202620907, -0.178125410980, 1.279825824143, -0.703784937696, 1.377596588777
                ],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.strip_II_strip_II,
                'tris-pos': 1
            },{
                #'file': 'frh-roots-0_1_0_1_1_1_1-fld_shell.0-strip_II-opp_strip_II-pos-1.py'
                'set': [4.170755846609, 0.821420235107, 0.100700797086, -2.149394471077, 1.035800183137, 0.974085339636, 1.554356155170
                ],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.strip_II_strip_II,
                'tris-pos': 1
            },{
                #'file': 'frh-roots-0_1_0_1_1_1_1-fld_shell.0-strip_II-opp_strip_II-pos-1.py'
                'set': [4.005419181303, 0.470909001839, -1.360105032126, 0.426263518595, 0.786838873976, 1.479755007849, -0.977504044321
                ],
                '7fold': Heptagons.foldMethod.star,
                'tris': trisAlt.strip_II_strip_II,
                'tris-pos': 1
            }
        ],
    }

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
