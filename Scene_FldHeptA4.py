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

TITLE = 'Polyhedra with Folded Regular Heptagons and Tetrahedral Symmetry'

V2 = math.sqrt(2)

trisAlt = Heptagons.TrisAlt()
trisAlt.baseKey = {
    trisAlt.strip_I:           True,
    trisAlt.strip_II:          True,
    trisAlt.star:              True,
    trisAlt.strip_1_loose:     True,
    trisAlt.star_1_loose:      True,
    trisAlt.alt_strip_I:       True,
    trisAlt.alt_strip_II:      True,
    trisAlt.alt_strip_1_loose: True,
    trisAlt.twist_strip_I:     True
}

counter = Heptagons.Tris_counter()

dyn_pos         = Heptagons.dyn_pos
open_file       = Heptagons.open_file
# symmtric edge lengths: b0 == b1, c0 == c1, d0 == d1
S_T8            = Heptagons.only_xtra_o3s
S_only_hepts    = Heptagons.only_hepts
S_T16           = counter.pp()
S_T24           = counter.pp()
S_T32           = counter.pp()
S_T40           = counter.pp()
S_T48           = counter.pp()
S_T56           = counter.pp()
S_T80           = counter.pp()

# symmtric edge lengths with flat squares
S_T16_S12       = counter.pp()

# symmtric edge lengths with folded squares
S_S12           = counter.pp()
S_T8_S12        = counter.pp()
S_S24           = counter.pp()
S_T8_S24        = counter.pp()
S_T24_S12       = counter.pp()
S_T8_S36        = counter.pp()
S_T32_S12       = counter.pp()
S_T32_S24       = counter.pp()
S_T56_S12       = counter.pp()

# symmtric edge lengths with hexagon
S_T24_H4        = counter.pp()

# non-symmetryc edge lengths
T8              = counter.pp()
T16             = counter.pp()
T24             = counter.pp()
T32             = counter.pp()
T40             = counter.pp()
T64             = counter.pp()

Stringify = {
    dyn_pos:            'Enable Sliders',
    # symmtric edge lengths: b0 == b1, c0 == c1, d0 == d1
    S_only_hepts:       'Only heptagons',
    S_T8:               'Heptagons and 8 Triangles',
    S_T16:              'SEL: 16 Triangles',
    S_T24:              'SEL: 24 Triangles',
    S_T32:              'SEL: 32 Triangles',
    S_T40:              'SEL: 40 Triangles',
    S_T48:              'SEL: 48 Triangles',
    S_T56:              'SEL: 56 Triangles',
    S_T80:              'SEL: 80 Triangles Equilateral',
    # with flat squares
    S_T16_S12:          'SEL: 28 = 16 Triangles and 12 Squares',
    # with folded squares:
    S_S12:              'SEL: 12 Folded Squares',
    S_T8_S12:           'SEL: 20 = 8 Triangles + 12 Folded Squares',
    S_S24:              'SEL: 24 Folded Squares',
    S_T8_S24:           'SEL: 32 = 8 Triangles + 24 Folded Squares',
    S_T24_S12:          'SEL: 36 = 24 Triangles + 12 Folded Squares',
    S_T8_S36:           'SEL: 44 = 8 Triangles + 36 Folded Squares',
    S_T32_S12:          'SEL: 44 = 32 Triangles + 12 Folded Squares',
    S_T32_S24:          'SEL: 56 = 32 Triangles + 24 Folded Squares',
    S_T56_S12:          'SEL: 68 = 56 Triangles + 12 Folded Squares',

    # with hexagons
    S_T24_H4:           'SEL: 28 = 24 Triangles + 4 Hexagons',

    # non-symmetric edges lengths
    T8:                 ' 8 Triangles (O3)',
    T16:                '16 Triangles',
    T24:                '24 Triangles',
    T32:                '32 Triangles',
    T40:                '40 Triangles',
    T64:                '64 Triangles',
}

def Vlen(v0, v1):
    x = v1[0] - v0[0]
    y = v1[1] - v0[1]
    z = v1[2] - v0[2]
    return (math.sqrt(x*x + y*y + z*z))

# get the col faces array by using a similar shape here, so it is calculated
# only once
useIsom = isometry.A4()
egShape = Geom3D.IsometricShape(
    Vs = [
        geomtypes.Vec3([0, 0, 1]),
        geomtypes.Vec3([0, 1, 1]),
        geomtypes.Vec3([1, 1, 1])
    ],
    Fs = [[0, 1, 2]],
    directIsometries = useIsom,
    unfoldOrbit = True
)
#colStabiliser = isometry.C2(setup = {'axis': [0.0, 1.0, 0.0]})
#colStabiliser = isometry.C2(setup = {'axis': [0.0, 0.0, 1.0]})
useSimpleColours = False
colStabiliser = isometry.C2(setup = {'axis': [1.0, 0.0, 0.0]})
colQuotientSet = useIsom / colStabiliser
if useSimpleColours:
    useRgbCols = [
        rgb.gray95,
        rgb.gray80,
        rgb.gray65,
        rgb.gray50,
        rgb.gray35,
        rgb.gray20,
    ]
else:
    useRgbCols = [
        rgb.indianRed,
        rgb.mediumBlue,
        rgb.limeGreen,
        rgb.cornflowerBlue,
        rgb.mistyRose1,
        rgb.gray20,
    ]

heptColPerIsom = []
for isom in useIsom:
    for subSet, i in zip(colQuotientSet, list(range(len(colQuotientSet)))):
        if isom in subSet:
            heptColPerIsom.append(([useRgbCols[i]], []))
            break;
isomsO3 = isometry.D2()

class Shape(Heptagons.FldHeptagonShape):
    def __init__(this, *args, **kwargs):
        heptagonsShape = Geom3D.IsometricShape(
            Vs = [], Fs = [], directIsometries = isometry.A4(),
            name = 'FoldedHeptagonsA4'
        )
        xtraTrisShape = Geom3D.IsometricShape(
            Vs = [], Fs = [], directIsometries = isometry.A4(),
            name = 'xtraTrisA4'
        )
        trisO3Shape = Geom3D.IsometricShape(
            Vs = [], Fs = [], directIsometries = isomsO3,
            colors = [([rgb.cyan[:]], [])],
            name = 'o3TrisA4'
        )
        Heptagons.FldHeptagonShape.__init__(this,
            [heptagonsShape, xtraTrisShape, trisO3Shape],
            3, 3,
            name = 'FoldedRegHeptA4'
        )
        this.heptagonsShape = heptagonsShape
        this.xtraTrisShape = xtraTrisShape
        this.trisO3Shape = trisO3Shape
        this.posAngleMin = -math.pi
        this.posAngleMax = math.pi
        this.posAngle = 0
        this.setEdgeAlternative(trisAlt.strip_1_loose, trisAlt.strip_1_loose)
        this.initArrs()
        this.setV()

    def getStatusStr(this):
        if this.updateShape:
            #print 'getStatusStr: forced setV'
            this.setV()
        Vs = this.baseVs
        Es = this.triEs[this.edgeAlternative]
        aLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
        bLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
        cLen = '%2.2f' % Vlen(Vs[Es[4]], Vs[Es[5]])
        Es = this.o3triEs[this.edgeAlternative]
        dLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
        if this.inclReflections:
            s = 'T = %02.2f; |a|: %s, |b|: %s, |c|: %s, |d|: %s' % (
                    this.height, aLen, bLen, cLen, dLen
                )
        else:
            if this.edgeAlternative == trisAlt.twist_strip_I:
                Es = this.oppTriEs[this.oppEdgeAlternative][
                    this.inclReflections]
            else:
                Es = this.oppTriEs[this.oppEdgeAlternative]
            opp_bLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
            opp_cLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
            Es = this.oppO3triEs[this.oppEdgeAlternative]
            if this.oppEdgeAlternative != trisAlt.twist_strip_I:
                opp_dLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
            else:
                opp_dLen = '-'
            s = 'T = %02.2f; |a|: %s, |b|: %s (%s), |c|: %s (%s), |d|: %s (%s)' % (
                    this.height,
                    aLen, bLen, opp_bLen, cLen, opp_cLen, dLen, opp_dLen
                )
        return s

    def correctEdgeAlternative(this):
        # TODO
        if (this.edgeAlternative == trisAlt.star or
                this.edgeAlternative == trisAlt.star_1_loose):
            this.altMFoldFace = False
            this.altNFoldFace = False
        else:
            if this.altNFoldFace:
                this.edgeAlternative = this.edgeAlternative | alt1_bit
            else:
                this.edgeAlternative = this.edgeAlternative & ~alt1_bit
            if this.altMFoldFace:
                this.edgeAlternative = this.edgeAlternative | alt2_bit
            else:
                this.edgeAlternative = this.edgeAlternative & ~alt2_bit

    def setTriangleFillPosition(this, i):
        print("TODO implement setTriangleFillPosition for", i)

    def setEdgeAlternative(this, alt = None, oppositeAlt = None):
        Heptagons.FldHeptagonShape.setEdgeAlternative(this, alt, oppositeAlt)
        # TODO
        #this.correctEdgeAlternative()

    def setV(this):
        this.posHeptagon()
        Vs = this.heptagon.Vs[:]

        #            5" = 18                 12 = 2"
        #    6" = 16                                 10 = 1"
        #                           0
        # 5' = 17     o3                         o3      11 = 2'
        #                    6             1
        #
        #       6' = 15                           9 = 1'
        #
        #                  5                 2
        #
        #
        #              14       4       3        8 = 0'
        #
        #
        #             2' = 13                7 = 5'

        Rr = Rot(axis = Vec([ 1, 1, 1]), angle = geomtypes.THIRD_TURN)
        Rl = Rot(axis = Vec([-1, 1, 1]), angle = -geomtypes.THIRD_TURN)
        Vs.append(Vec([-Vs[5][0], -Vs[5][1], Vs[5][2]]))       # Vs[7]
        Vs.append(Rr * Vs[0])                                  # Vs[8]
        Vs.append(Rr * Vs[1])                                  # Vs[9]
        Vs.append(Rr * Vs[9])                                  # Vs[10]
        Vs.append(Rr * Vs[2])                                  # Vs[11]
        Vs.append(Rr * Vs[11])                                 # Vs[12]
        Vs.append(Vec([-Vs[2][0], -Vs[2][1], Vs[2][2]]))       # Vs[13]
        Vs.append(Rl * Vs[0])                                  # Vs[14]
        Vs.append(Rl * Vs[6])                                  # Vs[15]
        Vs.append(Rl * Vs[-1])                                 # Vs[16]
        Vs.append(Rl * Vs[5])                                  # Vs[17]
        Vs.append(Rl * Vs[-1])                                 # Vs[18]
        Vs.append(Rr * Vs[8])                                  # Vs[19] = V0"
        Vs.append(Rr * Vs[6])                                  # Vs[20] = V6'"
        Vs.append(Rr * Vs[5])                                  # Vs[21] = V5'"

        Vs.append(Rl * Vs[13])                                 # Vs[22] = V13'
        Vs.append(Rl * Vs[-1])                                 # Vs[23] = V13"
        this.baseVs = Vs
        #for i in range(len(Vs)):
        #    print 'Vs[%d]:' % i, Vs[i]
        Es = []
        Fs = []
        Fs.extend(this.heptagon.Fs) # use extend to copy the list to Fs
        Es.extend(this.heptagon.Es) # use extend to copy the list to Fs
        this.heptagonsShape.setBaseVertexProperties(Vs = Vs)
        this.heptagonsShape.setBaseEdgeProperties(Es = Es)
        # comment out this and nvidia driver crashes:...
        this.heptagonsShape.setBaseFaceProperties(Fs = Fs)
        this.heptagonsShape.setFaceColors(heptColPerIsom)
        theShapes = [this.heptagonsShape]
        if this.addXtraFs:
            Es      = this.o3triEs[this.edgeAlternative][:]
            Fs      = this.o3triFs[this.edgeAlternative][:]
            Es.extend(this.oppO3triEs[this.oppEdgeAlternative])
            Fs.extend(this.oppO3triFs[this.oppEdgeAlternative])
            this.trisO3Shape.setBaseVertexProperties(Vs = Vs)
            this.trisO3Shape.setBaseEdgeProperties(Es = Es)
            this.trisO3Shape.setBaseFaceProperties(Fs = Fs)
            theShapes.append(this.trisO3Shape)
            if (not this.onlyRegFs):
                # when you use the rot alternative the rot is leading for
                # choosing the colours.
                if this.oppEdgeAlternative & Heptagons.rot_bit:
                    eAlt = this.oppEdgeAlternative
                else:
                    eAlt = this.edgeAlternative
                Es      = this.triEs[this.edgeAlternative][:]
                if this.edgeAlternative == trisAlt.twist_strip_I:
                    Fs = this.triFs[this.edgeAlternative][
                        this.inclReflections][:]
                    Fs.extend(
                        this.oppTriFs[this.oppEdgeAlternative][
                            this.inclReflections
                        ]
                    )
                    Es.extend(
                        this.oppTriEs[this.oppEdgeAlternative][
                            this.inclReflections
                        ]
                    )
                    # only draw the folds of the hexagon for the twisted variant
                    # if the hexagon isn't flat.
                    if (not Geom3D.eq(abs(this.posAngle) % (math.pi/2), math.pi/4)):
                        Es.extend(this.twistedEs_A4)
                    colIds = this.triColIds[eAlt][this.inclReflections]
                else:
                    Fs = this.triFs[this.edgeAlternative][:]
                    Fs.extend(this.oppTriFs[this.oppEdgeAlternative])
                    Es.extend(this.oppTriEs[this.oppEdgeAlternative])
                    colIds = this.triColIds[eAlt]
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
        this.updateShape = False
        # print 'V0 = (%.4f, %.4f, %.4f)' % (Vs[0][1], Vs[0][0], Vs[0][2])
        # print 'V1 = (%.4f, %.4f, %.4f)' % (Vs[1][1], Vs[1][0], Vs[1][2])
        # print 'V2 = (%.4f, %.4f, %.4f)' % (Vs[2][1], Vs[2][0], Vs[2][2])
        # print 'V3 = (%.4f, %.4f, %.4f)' % (Vs[3][1], Vs[3][0], Vs[3][2])
        # print 'V4 = (%.4f, %.4f, %.4f)' % (Vs[4][1], Vs[4][0], Vs[4][2])
        # print 'V5 = (%.4f, %.4f, %.4f)' % (Vs[5][1], Vs[5][0], Vs[5][2])
        # print 'V6 = (%.4f, %.4f, %.4f)' % (Vs[6][1], Vs[6][0], Vs[6][2])

    def getReflPosAngle(this):
        if this.edgeAlternative & Heptagons.twist_bit == Heptagons.twist_bit:
            return math.pi/4
        else:
            return 0

    def initArrs(this):
        print(this.name, "initArrs")

        #            5" = 18                 12 = 2"
        #    6" = 16                                 10 = 1"
        #                           0
        # 5' = 17     o3                         o3      11 = 2'
        #                    6             1
        #
        #       6' = 15                           9 = 1'
        #
        #                  5                 2
        #
        #
        #              14       4       3        8 = 0'
        #
        #
        #             2' = 13                7 = 5'

        I_loose = [[2, 3, 7]]
        noLoose = [[2, 3, 8]]
        stripI  = [[2, 8, 9]]
        stripII = [[2, 3, 9], [3, 8, 9]]
        star    = [[1, 2, 8], [1, 8, 9]]
        strip_1_loose = stripI[:]
        star_1_loose  = star[:]
        stripI.extend(noLoose)
        star.extend(noLoose)
        strip_1_loose.extend(I_loose)
        star_1_loose.extend(I_loose)
        twist_strip = { # reflections included:
            False: [[2, 3, 7], [1, 2, 20], [0, 1, 8]],
            True:  [[2, 3, 7], [1, 2, 21, 20], [0, 1, 20, 8]]
        }
        this.triFs = {
                trisAlt.strip_1_loose:      strip_1_loose[:],
                trisAlt.strip_I:            stripI[:],
                trisAlt.strip_II:           stripII[:],
                trisAlt.star:               star[:],
                trisAlt.star_1_loose:       star_1_loose[:],
                trisAlt.alt_strip_1_loose:  strip_1_loose[:],
                trisAlt.alt_strip_I:        stripI[:],
                trisAlt.alt_strip_II:       stripII[:],
                trisAlt.twist_strip_I:      twist_strip,
        }
        stdO3   = [1, 2, 9]
        altO3   = [2, 9, 11]
        this.triFs[trisAlt.strip_1_loose].append(stdO3)
        this.triFs[trisAlt.strip_I].append(stdO3)
        this.triFs[trisAlt.strip_II].append(stdO3)
        this.triFs[trisAlt.alt_strip_1_loose].append(altO3)
        this.triFs[trisAlt.alt_strip_I].append(altO3)
        this.triFs[trisAlt.alt_strip_II].append(altO3)
        I_loose = [[5, 14, 13]]
        noLoose = [[3, 7, 8]]
        stripI  = [[5, 15, 14]]
        stripII = [[4, 5, 15], [4, 15, 14]]
        star    = [[5, 6, 14], [6, 15, 14]]
        strip_1_loose = stripI[:]
        star_1_loose  = star[:]
        stripI.extend(noLoose)
        star.extend(noLoose)
        strip_1_loose.extend(I_loose)
        star_1_loose.extend(I_loose)
        rot_strip = [[13, 15, 14], [13, 5, 15]]
        rot_star = [[13, 15, 14], [13, 5, 6]]
        arot_star = [[13, 15, 14], [13, 17, 15]]
        twist_strip = { # reflections included:
            False: [[1, 20, 8], [2, 21, 20]],
            True:  []
        }
        this.oppTriFs = {
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
                trisAlt.twist_strip_I:      twist_strip,
        }
        stdO3   = [6, 15, 5]
        stdO3_x = [6, 15, 13]
        altO3   = [5, 17, 15]
        altO3_x = [5, 17, 13]
        this.oppTriFs[trisAlt.strip_1_loose].append(stdO3)
        this.oppTriFs[trisAlt.strip_I].append(stdO3)
        this.oppTriFs[trisAlt.strip_II].append(stdO3)
        this.oppTriFs[trisAlt.alt_strip_1_loose].append(altO3)
        this.oppTriFs[trisAlt.alt_strip_I].append(altO3)
        this.oppTriFs[trisAlt.alt_strip_II].append(altO3)
        this.oppTriFs[trisAlt.rot_strip_1_loose].append(stdO3)
        this.oppTriFs[trisAlt.arot_strip_1_loose].append(altO3)
        this.oppTriFs[trisAlt.rot_star_1_loose].append(stdO3_x)
        this.oppTriFs[trisAlt.arot_star_1_loose].append(altO3_x)

        strip = [0, 1, 1, 1, 0, 0]
        loose = [0, 0, 1, 0, 1, 1]
        star1loose = [0, 1, 0, 0, 1, 1]
        rot = [1, 0, 0, 0, 1, 0]
        rot_x = [0, 0, 1, 1, 1, 0]
        arot_x = [1, 1, 0, 0, 1, 0]
        twist = { # reflections included:
            False: [1, 1, 0, 0, 1],
            True:  [1, 1, 0]
        }
        this.triColIds = {
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
                trisAlt.twist_strip_I:          twist,
            }

        #            5" = 18                 12 = 2"
        #    6" = 16                                 10 = 1"
        #                           0
        # 5' = 17     o3                         o3      11 = 2'
        #                    6             1
        #
        #       6' = 15                           9 = 1'
        #
        #                  5                 2
        #
        #
        #              14       4       3        8 = 0'
        #
        #
        #             2' = 13                7 = 5'

        std   = [1, 9, 10]
        alt   = [2, 11, 12]
        twist = [0, 8, 19]
        this.o3triFs = {
                trisAlt.strip_1_loose:          [std],
                trisAlt.strip_I:                [std],
                trisAlt.strip_II:               [std],
                trisAlt.star:                   [std],
                trisAlt.star_1_loose:           [std],
                trisAlt.alt_strip_I:            [alt],
                trisAlt.alt_strip_II:           [alt],
                trisAlt.alt_strip_1_loose:      [alt],
                trisAlt.twist_strip_I:          [twist],
            }
        std   = [6, 16, 15]
        alt   = [5, 18, 17]
        # Twisted leads to a hexagon, however only for +/- 45 degrees (mod 90)
        # Otherise the hexagon isn't flat: then it is a folded one. Therefore
        # draw the hexagon by the 4 triangles that are folded. Save the folds as
        # separate edges in this.twistedEs_A4 that are only drawn if the hexagon
        # isn't flat.
        twist = [[23, 22, 13], [5, 23, 13], [18, 22, 23], [17, 13, 22]]
        this.twistedEs_A4 = [23, 22, 22, 13, 13, 23]
        this.oppO3triFs = {
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
                trisAlt.twist_strip_I:          twist,
            }

        #            5" = 18                 12 = 2"
        #    6" = 16                                 10 = 1"
        #                           0
        # 5' = 17     o3                         o3      11 = 2'
        #                    6             1
        #
        #       6' = 15                           9 = 1'
        #
        #                  5                 2
        #
        #
        #              14       4       3        8 = 0'
        #
        #
        #             2' = 13                7 = 5'
        strip_1_loose = [2, 7, 2, 8, 2, 9]
        stripI        = [3, 8, 2, 8, 2, 9]
        stripII       = [3, 8, 3, 9, 2, 9]
        star          = [3, 8, 2, 8, 1, 8]
        star_1_loose  = [2, 7, 2, 8, 1, 8]
        twist_stripI  = [2, 7, 2, 21, 1, 20]
        this.triEs = {
                trisAlt.strip_1_loose:     strip_1_loose,
                trisAlt.strip_I:           stripI,
                trisAlt.strip_II:          stripII,
                trisAlt.star:              star,
                trisAlt.star_1_loose:      star_1_loose,
                trisAlt.alt_strip_I:       stripI,
                trisAlt.alt_strip_II:      stripII,
                trisAlt.alt_strip_1_loose: strip_1_loose,
                trisAlt.twist_strip_I:     twist_stripI,
            }
        strip_1_loose = [5, 14, 5, 15]
        stripI        = [5, 14, 5, 15]
        stripII       = [4, 15, 5, 15]
        star          = [5, 14, 6, 14]
        star_1_loose  = [5, 14, 6, 14]
        rot_strip     = [13, 15, 5, 15]
        rot_star      = [13, 15, 6, 13]
        arot_star     = [13, 15, 13, 17]
        twist_stripI  = { # reflections included:
            False: [1, 8, 2, 20],
            True:  []
        }
        this.oppTriEs = {
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
                trisAlt.twist_strip_I:      twist_stripI,
            }

        std   = [1, 9, 9, 10, 10, 1]
        alt   = [2, 11, 11, 12, 12, 2]
        twist = [0, 8, 8, 19, 19, 0]
        this.o3triEs = {
                trisAlt.strip_1_loose:          std,
                trisAlt.strip_I:                std,
                trisAlt.strip_II:               std,
                trisAlt.star:                   std,
                trisAlt.star_1_loose:           std,
                trisAlt.alt_strip_I:            alt,
                trisAlt.alt_strip_II:           alt,
                trisAlt.alt_strip_1_loose:      alt,
                trisAlt.twist_strip_I:          twist,
            }
        std   = [6, 16, 16, 15, 15, 6]
        alt   = [5, 18, 18, 17, 17, 5]
        twist = []
        this.oppO3triEs = {
                trisAlt.strip_1_loose:          std,
                trisAlt.strip_I:                std,
                trisAlt.strip_II:               std,
                trisAlt.star:                   std,
                trisAlt.star_1_loose:           std,
                trisAlt.alt_strip_I:            alt,
                trisAlt.alt_strip_II:           alt,
                trisAlt.alt_strip_1_loose:      alt,
                trisAlt.rot_strip_1_loose:      std,
                trisAlt.arot_strip_1_loose:     alt,
                trisAlt.rot_star_1_loose:       std,
                trisAlt.arot_star_1_loose:      alt,
                trisAlt.twist_strip_I:          twist,
            }

    def printTrisAngles(this):
        # TODO: fix this function. Which angles to take (ie which faces) depends
        # on the triangle alternative.
        tris = this.triFs[this.edgeAlternative]
        # for non 1 loose
        # for i in range(0, len(tris) - 2, 2):
        d = 2
        # for 1 loose:
        d = 1
        for i in range(2):
            norm0 = Geom3D.Triangle(
                this.baseShape.Vs[tris[i][0]],
                this.baseShape.Vs[tris[i][1]],
                this.baseShape.Vs[tris[i][2]],
            ).normal(True)
            print('norm0 %d: ', norm0)
            norm1 = Geom3D.Triangle(
                this.baseShape.Vs[tris[i+d][0]],
                this.baseShape.Vs[tris[i+d][1]],
                this.baseShape.Vs[tris[i+d][2]],
            ).normal(True)
            print('norm1 %d: ', norm1)
            inprod = norm0 * norm1
            print('Tris angle %d: %.6f degrees' % (i, math.acos(inprod) * Geom3D.Rad2Deg))
        print('------------') # TODO move out

class CtrlWin(Heptagons.FldHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
        Heptagons.FldHeptagonCtrlWin.__init__(this,
            shape, canvas,
            3, # maxHeigth
            [ # prePosLst
                Stringify[S_only_hepts],
                Stringify[S_T8],
                Stringify[S_T16],
                Stringify[S_T24],

                Stringify[S_T24_H4],

                Stringify[S_T32],
                Stringify[S_T40],
                Stringify[S_T48],
                Stringify[S_T56],
                Stringify[S_T80],

                Stringify[S_T16_S12],

                Stringify[S_S12],
                Stringify[S_T8_S12],
                Stringify[S_S24],
                Stringify[S_T8_S24],
                Stringify[S_T24_S12],
                Stringify[S_T8_S36],
                Stringify[S_T32_S12],
                Stringify[S_T32_S24],
                Stringify[S_T56_S12],

                Stringify[T8],
                Stringify[T16],
                Stringify[T24],
                Stringify[T40],
                Stringify[T64],
                Stringify[dyn_pos],
            ],
            isometry.A4,
            [trisAlt],
            Stringify,
            *args, **kwargs
        )

    def showOnlyHepts(this):
        return this.prePos == S_only_hepts and not (
                this.trisFill == None
            ) and not (
                this.trisFill & Heptagons.twist_bit == Heptagons.twist_bit)

    def showOnlyO3Tris(this):
        return this.prePos == Heptagons.only_xtra_o3s and not (
                this.trisFill == None
            ) and not (
                this.trisFill & Heptagons.twist_bit == Heptagons.twist_bit)

    rDir = 'data/Data_FldHeptA4'
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
            in_data = psp[this.prePos][this.specPosIndex]
            fold_method_str = this.fileStrMapFoldMethodStr(in_data['file'])
            assert fold_method_str != None
            tris_str = this.fileStrMapTrisStr(in_data['file'])
            assert tris_str != None
            tris_str = trisAlt.key[tris_str]
            data = {
                    'set': in_data['set'],
                    '7fold': Heptagons.foldMethod.get(fold_method_str),
                    'tris': tris_str,
                    'fold-rot': this.fileStrMapFoldPos(in_data['file'])
            }
            print('see file %s/%s' % (this.rDir, in_data['file']))
            return data

    predefReflSpecPos = {
        S_only_hepts: [
            {
                'file': 'frh-roots-1_0_1_0-fld_w.0-strip_I.py',
                'set': [2.380384930680, 0.693073733187, -0.568746300899, -0.882436236397],
            },{
                'file': 'frh-roots-1_0_1_0-fld_w.0-strip_I.py',
                'set': [-1.886848679993, -2.675843213538, -3.128320557422, 1.954454451606],
            },{
                'file': 'frh-roots-1_0_1_0-fld_w.0-strip_I.py',
                'set': [-1.322333216810, -2.967180003002, -1.183250747277, 1.668301536282],
            },{
                'file': 'frh-roots-1_0_1_0-fld_shell.0-alt_strip_II.py',
                'set': [1.384557049344, 1.446970234245, -1.316197505877, -0.865444046055],
            },{
                'file': 'frh-roots-1_0_1_0-fld_shell.0-alt_strip_II.py',
                'set': [-0.893811200268, -2.124009132680, -2.221957533639, 0.797991253652],
            },{
                'file': 'frh-roots-1_0_1_0-fld_shell.0-alt_strip_II.py',
                'set': [-0.556102494513, -2.609660225894, -1.565821769393, -2.603286338808],
            },{
                'file': 'frh-roots-1_0_1_0-fld_shell.0-alt_strip_II.py',
                'set': [-0.621710474737, -2.385085606668, 2.979725519925, 2.212236586768],
            },{
                'file': 'frh-roots-1_0_1_0-fld_shell.0-alt_strip_II.py',
                'set': [-0.744610213721, -2.981881518271, 2.772201116514, -1.626936107939],
           },{
               'file': 'frh-roots-1_0_1_0-fld_parallel.0-shell.py',
               'set': [2.05527791079771, 0.0, 1.17877572036290, 0.93053176681969, 0.],
           },{
               'file': 'frh-roots-0_0_0_0-fld_triangle.0-twisted.py',
               'set': [1.57625873995627, 0.0, 1.70780610035987, 0.69387894107559, 0.78539816339745],
           },{
               'file': 'frh-roots-0_0_0_0-fld_w.0-twisted.py',
               'set': [-0.55652539638413, 2.39522124261844, 0.72665170889609, 0.82988500709760, 0.78539816339745],
           },{
               'file': 'frh-roots-0_0_0_0-fld_w.0-twisted.py',
               'set': [-0.75211335117600, 2.47041152939265, 0.78109340649621, 1.45595139993016, 0.78539816339745],
           },{
               'file': 'frh-roots-0_0_0_0-fld_shell.0-twisted.py',
               'set': [1.57829332274746, -0.32640923840694, 0.34074243237606, 2.04797705220462, 0.78539816339745],
            }
        ],
        S_T8: [
            {
                'file': 'frh-roots-0_1_0_1-fld_triangle.0-strip_I.py',
                'set': [1.668804061427, 1.471660709431, -0.787124235167, 0.879575685317],
            },{
                'file': 'frh-roots-0_1_0_1-fld_shell.0-strip_I.py',
                'set': [1.778711440973, 0.947499660437, -1.726110141329, 0.0],
            },{
                'file': 'frh-roots-0_1_0_1-fld_shell.0-strip_I.py',
                'set': [1.778711440973, 0.947499660437, 0.458542642050, 0.0],
            },{
                'file': 'frh-roots-0_1_0_1-fld_trapezium.0-strip_I.py',
                'set': [1.603988045241, 1.179161796661, -1.224721468276, 0.987593630632],
            },{
                'file': 'frh-roots-0_1_0_1-fld_w.0-shell_1_loose.py',
                'set': [2.596914957747, 0.371800292039, -0.991598446991, 0.954998112111],
            },{
                'file': 'frh-roots-0_1_0_1-fld_w.0-shell_1_loose.py',
                'set': [-2.396628548671, -2.760441424536, -2.289627248660, 2.151908864169],
            },{
                'file': 'frh-roots-0_1_0_1-fld_w.0-shell_1_loose.py',
                'set': [-2.396628548671, -2.760441424536, -2.289627248660, -0.989683789421],
            }
        ],
        S_T16_S12: [
            {
                'file': 'frh-roots-0_1_1_0-fld_shell.0-twisted.py',
                'set': [2.28349922775437, 0.06277160667564, -0.06286795681704, 2.75487753324911, 0.78539816339745],
            },{
                'file': 'frh-roots-0_1_1_0-fld_triangle.0-twisted.py',
                'set': [2.28336552114282, 0.0, 1.13059660075713, 1.75383477143902, 0.78539816339745],
            },{
                'file': 'frh-roots-0_1_1_0-fld_triangle.0-twisted.py',
                'set': [2.28336552114282, 0.0, 1.13059660075713, -2.67411537632553, 0.78539816339745],
            },{
                'file': 'frh-roots-0_1_1_0-fld_triangle.0-twisted.py',
                'set': [2.28336552114282, 0.0, 0.10036281658365, 2.67411537632553, 0.78539816339745],
            },{
                'file': 'frh-roots-0_0_1_1-fld_triangle.0-twisted.py',
                'set': [1.57625873995627, 0.0, 2.13564659960344, 1.09359107312669, 0.78539816339745],
            }
        ],
        S_T16: [
            {
                'file': 'frh-roots-1_0_0_0-fld_w.0-twisted.py',
                'set': [0.38625024358001, 2.04181085346543, 0.53307481297736, -0.02371984670375, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_0-fld_shell.0-twisted.py',
                'set': [0.38635143295225, 2.04177274103915, 0.51985442041897, 0.02379038049852, 0.78539816339745],
            },{
                'file': 'frh-roots-0_1_0_0-fld_shell.0-twisted.py',
                'set': [2.28349922775437, 0.06277160667564, -0.06286795681704, 1.46852003907435, 0.78539816339745],
            },{
                'file': 'frh-roots-0_0_0_1-fld_parallel.0-twisted.py',
                'set': [1.57625873995627, 0.0, 2.05411520911343, 0.26432165270370, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_0-fld_triangle.0-twisted.py',
                'set': [1.74903011940493, 0.69387894107539, 1.01392715928449, 0.69387894107539, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_0-fld_triangle.0-twisted.py',
                'set': [0.54693117675810, 2.44771371251441, -0.73990761215453, 0.69387894107539, 0.78539816339745],
            },{
                'file': 'frh-roots-0_1_0_0-fld_triangle.0-twisted.py',
                'set': [2.28336552114282, 0.0, 1.13059660075713, 0.46747727726426, 0.78539816339745],
            },{
                'file': 'frh-roots-0_1_0_0-fld_triangle.0-twisted.py',
                'set': [2.28336552114282, -0.0, 1.13059660075713, -1.38775788215078, 0.78539816339745],
            },{
                'file': 'frh-roots-0_1_0_0-fld_triangle.0-twisted.py',
                'set': [2.28336552114282, 0.0, 0.10036281658365, 1.38775788215077, 0.78539816339745],
            },{
                'file': 'frh-roots-0_0_0_1-fld_triangle.0-twisted.py',
                'set': [1.57625873995627, 0.0, 2.13564659960344, -0.19276642104807, 0.78539816339745],
            },{
                'file': 'frh-roots-0_0_0_1-fld_triangle.0-twisted.py',
                'set': [1.57625873995627, 0.0, 2.13564659960344, -2.04800158046311, 0.78539816339745],
            },{
                'file': 'frh-roots-0_0_0_1-fld_triangle.0-twisted.py',
                'set': [1.57625873995627, 0.0, 1.13059660075713, 1.75383477143902, 0.78539816339745],
            }
        ],
        S_T24: [
            {
                'file': 'frh-roots-1_1_0_0-fld_w.0-twisted.py',
                'set': [1.76492506022939, -0.23739205643944, -0.34895078545162, -0.15519364844989, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_w.0-twisted.py',
                'set': [-0.79173444161549, 2.48583128085619, -2.97499620550543, 0.36291871955997, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_shell.0-twisted.py',
                'set': [1.76465226082310, -0.23752704781790, -0.43444382937558, 0.15892519348001, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_shell.0-twisted.py',
                'set': [-0.18835951730218, 2.25653920053309, 0.20791586793685, 0.83498494726983, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_shell.0-twisted.py',
                'set': [1.76465226082310, -0.23752704781790, -0.43444382937558, 2.01416035289505, 0.78539816339745],
            }
        ],
        S_T24_H4: [
            {
                'file': 'frh-roots-1_1_0_0-fld_w.0-twisted.py',
                'set': [2.45721938357382, 1.02864406950856, -1.27167415256983, 1.13471006522803, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_w.0-twisted.py',
                'set': [2.45628709627969, 0.20145076069264, 1.27330784422036, -1.34814068537132, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_w.0-twisted.py',
                'set': [-1.74055595544021, 2.89220370313053, 1.27640556999649, 0.99923157377633, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_triangle.0-twisted.py',
                'set': [1.25403795794465, 2.44771371251441, -1.31711711175728, -1.38775788215077, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_triangle.0-twisted.py',
                'set': [2.45613690059148, 0.69387894107539, 0.43671765968174, -1.38775788215077, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_triangle.0-twisted.py',
                'set': [2.45613690059148, 0.69387894107539, -0.59351612449174, 1.38775788215078, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_triangle.0-twisted.py',
                'set': [1.25403795794465, 2.44771371251441, -2.34735089593076, -0.46747727726426, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_shell.0-twisted.py',
                'set': [2.46960924618761, 1.01698736209970, -0.38433974199343, 0.86045704157206, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_shell.0-twisted.py',
                'set': [2.47252905514248, 0.21676593171114, 0.45516655939558, 0.93763273086315, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_shell.0-twisted.py',
                'set': [2.47252905514248, 0.21676593171114, 0.45516655939558, -0.91760242855189, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_shell.0-twisted.py',
                'set': [0.83956069972121, 1.86800900646576, 0.91933083158157, -2.73340822015620, 0.78539816339745],
            },{
                'file': 'frh-roots-1_1_0_0-fld_shell.0-twisted.py',
                'set': [0.83956069972121, 1.86800900646576, 0.91933083158157, -0.87817306074117, 0.78539816339745],
            }
        ],
        S_T32: [
            {
                'file': 'frh-roots-1_0_0_1-fld_trapezium.0-twisted.py',
                'set': [0.48568807039262, 2.25669785825937, 0.06173900355777, 0.41753524083101, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_shell.0-twisted.py',
                'set': [0.51874726388437, 2.25653920053309, 0.20791586793685, -0.45137254690493, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_shell.0-twisted.py',
                'set': [0.51874726388437, 2.25653920053309, 0.20791586793685, -2.30660770631996, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_parallel.0-twisted.py',
                'set': [0.54693117675810, 2.44771371251441, -0.39359850340097, 0.26432165270381, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_parallel.0-twisted.py',
                'set': [1.74903011940493, 0.69387894107539, 1.36023626803805, 0.26432165270370, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_triangle.0-twisted.py',
                'set': [0.54693117675810, 2.44771371251441, -0.31206711291096, -0.19276642104807, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_triangle.0-twisted.py',
                'set': [1.74903011940493, 0.69387894107539, 1.44176765852806, -0.19276642104807, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_triangle.0-twisted.py',
                'set': [1.74903011940493, 0.69387894107539, 1.44176765852806, -2.04800158046311, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_triangle.0-twisted.py',
                'set': [0.54693117675810, 2.44771371251441, -0.31206711291096, -2.04800158046311, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_triangle.0-twisted.py',
                'set': [0.54693117675810, 2.44771371251441, -1.31711711175728, 1.75383477143902, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_triangle.0-twisted.py',
                'set': [1.74903011940493, 0.69387894107539, 0.43671765968174, 1.75383477143902, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_0_1-fld_w.0-twisted.py',
                'set': [0.48540719864890, 2.26900223672547, -0.02757800836859, 0.44535720008269, 0.78539816339745],
            },{
                'file': 'frh-roots-0_1_0_1-fld_parallel.0-twisted.py',
                'set': [2.28336552114282, 0.0, 1.37672964253502, 0.94170721928212, 0.78539816339745],
            },{
                'file': 'frh-roots-0_1_0_1-fld_parallel.0-twisted.py',
                'set': [2.28336552114282, 0.0, 1.37672964253501, -2.46420708701138, 0.78539816339745],
            },{
                'file': 'frh-roots-0_1_0_1-fld_shell.0-twisted.py',
                'set': [1.84775911011892, 0.92575452409419, -1.72327793624487, 2.57828590634453, 0.78539816339745],
            }
        ],
        S_T40: [
            {
                'file': 'frh-roots-1_0_1_0-fld_w.0-twisted.py',
                'set': [0.01810673840905, 2.17952724009918, -0.07870584086126, 1.61757544772923, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_1_0-fld_w.0-twisted.py',
                'set': [-0.16303030453660, 2.24707815221230, -0.03993084437920, 2.11938494155470, 0.78539816339745],
            },{
                'file': 'frh-roots-1_0_1_0-fld_w.0-twisted.py',
                'set': [0.17474539602927, 2.12109878921778, 1.27980043291040, -1.16062859887813, 0.78539816339745],
            }
        ],
        S_S12: [
            {
                'file': 'frh-roots-0_V2_1_0-fld_w.0-shell_1_loose.py',
                'set': [2.33699202331, 0.07199688787, 0.78873100385, -1.72648574722]
            }
        ]
    }

    predefRotSpecPos = {
        S_only_hepts: [
            {
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.1-alt_strip_I-opp_alt_strip_II-pos-0.py',
                'set': [0.7496252273681, 1.8388723684393, -1.7538347714391, 1.4526321889049, -0.1943741858469, -1.753834771439, -0.3966660749159],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.1-alt_strip_I-opp_alt_strip_II-pos-0.py',
                'set': [1.0536253361613, 1.4583087103255, -1.7538347714389, 1.5121382011463, -0.1804014766055, -1.7538347714391, 0.6519255476389],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.1-shell-opp_alt_strip_II-pos-0.py',
                'set': [1.274286108189, 2.1023807514558, -1.0623578815823, -0.866370345885, 0.2114548278112, 1.729065266832, -0.8663703458851],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.1-shell-opp_alt_strip_II-pos-0.py',
                'set': [-0.8597451588333, -1.0617299797456, -2.236200847328, -0.4041945853315, 1.2986267346582, 0.8759573026118, -0.4041945853315],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_shell.0-alt_strip_II-opp_alt_strip_II-pos-0.py',
                'set': [-0.584447329706, -2.485288015235, 2.540930460981, 2.593087704091, 0.385739827710, -1.373557246626, -2.412102564927],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_shell.0-alt_strip_II-opp_alt_strip_II.py',
                'set': [-0.801847203711, -2.608143090127, -2.668837734722, -1.252388597181, -1.021040545614, 1.744176845223, -2.460124162981],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_shell.0-alt_strip_II-opp_alt_strip_II.py',
                'set': [-0.866025403784, -2.222676713307, -2.064570332814, -0.827255867832, -0.884416238250, -2.064570332813, 1.904278188607],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.0-shell-opp_shell.py',
                'set': [1.731178674695, -0.460140302443, 1.753834771439, -0.784585557814, 2.512070703819, 1.753834771439, -2.488945590745],
            },
        ],
        S_T8: [
            {
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_shell.0-strip_II-opp_strip_II.py',
                'set': [1.778711440973, 0.947499660437, -1.726110141329, 0.0, 0.0, 0.458542642050, 0.0],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_shell.0-strip_1_loose-opp_strip_1_loose.py',
                'set': [1.230780883271, -0.833487854345, 1.222093745524, 1.087041924921, 1.964018074389, 1.222093745524, 1.087041924921],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_shell.0-strip_1_loose-opp_strip_1_loose.py',
                'set': [0.997749181426, -0.792857842956, 1.100626985898, 2.388598519690, 1.598141634206, 1.100626985898, 2.388598519690],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_w.0-strip_1_loose-opp_alt_strip_1_loose.py',
                'set': [1.322002234160, -0.777358422835, 1.753834771439, -0.835355509883, 2.211531833297, 1.753834771439, -0.835355509883],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_w.0-strip_1_loose-opp_alt_strip_1_loose.py',
                'set': [1.601135681483, 0.889170493616, -1.753834771439, -0.498916362774, 0.0, -1.753834771439, -0.498916362774],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_shell.0-shell_1_loose-opp_shell_1_loose.py',
                'set': [1.901507063757, -0.303461611612, 0.314885093380, 0.854512058189, -1.863748016803, 0.314885093380, 0.854512058189],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_w.0-shell_1_loose-opp_strip_1_loose.py',
                'set': [-1.876023780285, 2.806553402452, 2.764486274075, -2.283625185913, -2.226783359690, 0.308178247636, 2.459602201102],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_w.0-shell_1_loose-opp_shell_1_loose.py',
                'set': [2.596914957747, 0.371800292039, -0.991598446991, 0.0, 0.0, -0.991598446991, 1.909996224222],
            },
        ]
    }

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
