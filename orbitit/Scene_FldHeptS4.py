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

import logging
import math

from orbitit import Geom3D, geomtypes, isometry, heptagons, rgb
from orbitit.geomtypes import Rot3 as Rot
from orbitit.geomtypes import Vec3 as Vec

TITLE = 'Polyhedra with Folded Regular Heptagons and Cube Symmetry'

trisAlt = heptagons.TrisAlt()
trisAlt.baseKey = {
    trisAlt.refl_1: True,
    trisAlt.refl_2: True,
}

counter = heptagons.Tris_counter()

DYN_POS = heptagons.DYN_POS
OPEN_FILE = heptagons.OPEN_FILE
ONLY_HEPTS = heptagons.ONLY_HEPTS
ONLY_XTRA_O3S = heptagons.ONLY_XTRA_O3S
T32 = counter.pp()
T24_S6 = counter.pp()
T24_S30 = counter.pp()
T32_S24 = counter.pp()
T56_S6 = counter.pp()
S_T8_S6 = counter.pp()
ALL_EQ_TRIS = counter.pp()
NO_O3_TRIS = counter.pp()
edge_1_1_V2_1 = counter.pp()
edge_1_V2_1_1 = counter.pp()
edge_V2_1_1_1 = counter.pp()
edge_V2_1_V2_1 = counter.pp()
squares_24 = counter.pp()
edge_0_1_1_1 = counter.pp()
edge_0_1_V2_1 = counter.pp()
tris_24 = counter.pp()
edge_1_1_0_1 = counter.pp()
edge_1_0_1_1 = counter.pp()
edge_V2_1_0_1 = counter.pp()
edge_V2_1_1_0 = counter.pp()
square_12 = counter.pp()
edge_0_V2_1_1 = counter.pp()

Stringify = {
    DYN_POS:        'Enable Sliders',
    T32:        '32 Triangles',
    T24_S6:             '24 Triangles and 6 Squares',
    T24_S30:            '24 Triangles and 30 Squares',
    T32_S24:            '32 Triangles and 24 Squares',
    T56_S6:             '56 Triangles and 6 Squares',
    S_T8_S6:        'SEL: 8 Triangles and 6 Squares',
    NO_O3_TRIS:     '48 Triangles',
    ALL_EQ_TRIS:    'All 80 Triangles Equilateral',
    ONLY_XTRA_O3S:  '8 Triangles (O3)',
    edge_V2_1_0_1:  '8 Triangles and 12 Folded Squares',
    edge_0_1_V2_1:  '8 Triangles and 24 Folded Squares',
    edge_V2_1_V2_1: '8 Triangles and 36 Folded Squares',
    square_12:      '12 Folded Squares',
    tris_24:        '24 Triangles',
    squares_24:     '24 Folded Squares',
    edge_V2_1_1_0:  '24 Triangles and 12 Folded Squares',
    edge_1_1_0_1:   '32 Triangles (24 + 8) I',
    edge_1_0_1_1:   '32 Triangles (24 + 8) II',
    edge_0_V2_1_1:  '32 Triangles and 12 Folded Squares',
    edge_1_1_V2_1:  '32 Triangles and 24 Folded Squares: I',
    edge_1_V2_1_1:  '32 Triangles and 24 Folded Squares: II',
    edge_0_1_1_1:   '56 Triangles',
    edge_V2_1_1_1:  '56 Triangles and 12 Folded Squares',
    ONLY_HEPTS:     'Just Heptagons',
}

pos_angle_refl_2 = math.pi/2

def Vlen(v0, v1):
    x = v1[0] - v0[0]
    y = v1[1] - v0[1]
    z = v1[2] - v0[2]
    return (math.sqrt(x*x + y*y + z*z))

V2 = math.sqrt(2)
V3 = math.sqrt(3)
hV2 = V2/2

o4_fld_0 = geomtypes.Vec3([1, 0, 0])
o4_fld_1 = geomtypes.Vec3([0, 1, 1])
isomS4 = isometry.S4(setup = {'o4axis0': o4_fld_0, 'o4axis1': o4_fld_1})
o4fld = Rot(axis = o4_fld_1, angle = geomtypes.QUARTER_TURN)
isomO4 = isometry.C4(setup = {'axis': o4_fld_1})

o3axis = geomtypes.Vec3([1/V3, 0, V2/V3])
o3fld = Rot(axis = o3axis, angle = geomtypes.THIRD_TURN)
isomO3 = isometry.C3(setup = {'axis': o3axis})

# get the col faces array by using a similar shape here, so it is calculated
# only once
colStabilisers = [
    isometry.D2(setup = {
        'axis_n': [0.0, 0.0, 1.0],
        'axis_2': [1.0, 0.0, 0.0],
    }),
    isometry.D2(setup = {
        'axis_n': [1.0, 0.0, 0.0],
        'axis_2': [0.0, 1.0, 1.0],
    }),
    isometry.D2(setup = {
        'axis_n': [0.0, 1.0, 1.0],
        'axis_2': [1.0, -hV2, hV2],
    }),
]
colStabiliser = colStabilisers[-1]
colQuotientSet = isomS4 / colStabiliser
useRgbCols = [
    rgb.indianRed,
    rgb.mediumBlue,
    rgb.limeGreen,
    rgb.cornflowerBlue,
    rgb.mistyRose1,
    rgb.gray20,
]
heptColPerIsom = []
for isom in isomS4:
    for subSet, i in zip(colQuotientSet, list(range(len(colQuotientSet)))):
        if isom in subSet:
            heptColPerIsom.append(useRgbCols[i])
            break;

class Shape(heptagons.FldHeptagonShape):
    def __init__(this, *args, **kwargs):
        heptagonsShape = Geom3D.SymmetricShape(
            Vs=[],
            Fs=[],
            isometries=isomS4,
            name='FoldedHeptagonsS4',
            regen_edges=False
        )
        xtraTrisShape = Geom3D.SymmetricShapeSplitCols(
            Vs=[],
            Fs=[],
            isometries=isomS4,
            name='xtraTrisS4',
            regen_edges=False
        )
        trisO3Shape = Geom3D.OrbitShape(
            Vs=[],
            Fs=[],
            final_sym=isomS4,
            stab_sym=isomO3,
            colors=[rgb.cyan[:]],
            name='o3TrisS4',
            regen_edges=False
        )
        trisO4Shape = Geom3D.OrbitShape(
            Vs=[],
            Fs=[],
            final_sym=isomS4,
            stab_sym=isomO4,
            colors=[rgb.cyan[:]],
            name='o4SquareS4',
            regen_edges=False
        )
        heptagons.FldHeptagonShape.__init__(this,
            [heptagonsShape, xtraTrisShape, trisO3Shape, trisO4Shape],
            4, 3,
            name='FoldedRegHeptS4xI'
        )
        this.heptagonsShape = heptagonsShape
        this.xtraTrisShape = xtraTrisShape
        this.trisO3Shape = trisO3Shape
        this.trisO4Shape = trisO4Shape
        this.pos_angle_min = -pos_angle_refl_2
        this.pos_angle_max = pos_angle_refl_2
        this.height = 3.9
        this.setEdgeAlternative(trisAlt.strip_1_loose, trisAlt.strip_1_loose)
        this.initArrs()
        this.setV()

    def getStatusStr(this):
        #angle = Geom3D.Rad2Deg * this.dihedralAngle
        s = heptagons.FldHeptagonShape.getStatusStr(this)
        if this.update_shape:
            this.setV()
        #                                  14 = 2'
        #                0
        #   13                      12 = o3 centre
        #         6             1
        #
        # 11                           9 = 1'
        #
        #       5                 2
        #
        #
        #   10       4       3        8 = 0'
        #
        #
        #                         7 = 6'
        Vs = this.baseVs
        if this.has_reflections:
            Es = this.triEs[this.edge_alt]
            aLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
            bLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
            cLen = '%2.2f' % Vlen(Vs[Es[4]], Vs[Es[5]])
            dLen = '%2.2f' % Vlen(Vs[Es[6]], Vs[Es[7]])
        else:
            Es = this.triEs[this.edge_alt]
            aLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
            bLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
            cLen = '%2.2f' % Vlen(Vs[Es[4]], Vs[Es[5]])
            Es = this.o3triEs[this.edge_alt]
            dLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])

        if this.has_reflections:
            s = 'T = %02.2f; |a|: %s, |b|: %s, |c|: %s, |d|: %s' % (
                this.height, aLen, bLen, cLen, dLen
            )
        else:
            Es = this.oppTriEs[this.opposite_edge_alt]
            opp_bLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
            opp_cLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
            Es = this.o4triEs[this.opposite_edge_alt]
            if this.opposite_edge_alt != trisAlt.refl_1:
                opp_dLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
            else:
                opp_dLen = '-'
            s = 'T = %02.2f; |a|: %s, |b|: %s (%s), |c|: %s (%s), |d|: %s (%s)' % (
                this.height,
                aLen, bLen, opp_bLen, cLen, opp_cLen, dLen, opp_dLen
            )
        return s

    def set_tri_fill_pos(this, i):
        logging.warning(f"TODO implement set_tri_fill_pos for {i}")

    def setV(this):
        #
        # o4: 5 -> 18 -> 19 -> 20
        #     0 -> 21 -> 22 -> 23
        #    12 -> 28 -> 29 -> 30
        #     6 -> 31
        #
            # 6" = 16
        #             6' = 15             12 = 2"
            #          o4          0
            #                                    10 = 1"
            #  6'" = 17     6             1   o3
            #                                            11 = 2'
            #                                    9 = 1'
            #
            #             5                 2
            #
            #
            #        14        4       3        8 = 0'
            #
            #
            #         2' = 13               7 = 5'
        #
        #               o3: 7 -> 24 -> 25
        #                   0 -> 26 -> 27
        this.posHeptagon()
        Vs = this.heptagon.Vs[:]
        Vs.append(Vec([-Vs[5][0], -Vs[5][1], Vs[5][2]]))        # Vs[7]
        Vs.append(o3fld * Vs[0])                # Vs[8]
        Vs.append(o3fld * Vs[1])                # Vs[9]
        Vs.append(o3fld * Vs[-1])               # Vs[10]
        Vs.append(o3fld * Vs[2])                # Vs[11]
        Vs.append(o3fld * Vs[-1])               # Vs[12]
        Vs.append(Vec([-Vs[2][0], -Vs[2][1], Vs[2][2]]))        # Vs[13]
        Vs.append(Vec([-Vs[8][0], -Vs[8][1], Vs[8][2]]))        # Vs[14]
        Vs.append(o4fld * Vs[6])                # Vs[15]
        Vs.append(o4fld * Vs[-1])               # Vs[16]
        Vs.append(o4fld * Vs[-1])               # Vs[17]
        Vs.append(o4fld * Vs[5])                # Vs[18]
        Vs.append(o4fld * Vs[-1])               # Vs[19]
        Vs.append(o4fld * Vs[-1])               # Vs[20]
        Vs.append(o4fld * Vs[0])                # Vs[21]
        Vs.append(o4fld * Vs[-1])               # Vs[22]
        Vs.append(o4fld * Vs[-1])               # Vs[23]
        Vs.append(o3fld * Vs[7])                # Vs[24]
        Vs.append(o3fld * Vs[-1])               # Vs[25]
        Vs.append(o3fld * Vs[0])                # Vs[26]
        Vs.append(o3fld * Vs[-1])               # Vs[27]
        Vs.append(o4fld * Vs[12])               # Vs[28]
        Vs.append(o4fld * Vs[-1])               # Vs[29]
        Vs.append(o4fld * Vs[-1])               # Vs[30]
        Vs.append(o4fld * Vs[6])                # Vs[31]
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
        # TODO rm:
        if this.addXtraFs:
            Fs = this.o3triFs[this.edge_alt][:]
            Es = this.o3triEs[this.edge_alt][:]
            this.trisO3Shape.setBaseVertexProperties(Vs = Vs)
            this.trisO3Shape.setBaseEdgeProperties(Es = Es)
            this.trisO3Shape.setBaseFaceProperties(Fs = Fs)
            theShapes.append(this.trisO3Shape)
            Es = this.o4triEs[this.opposite_edge_alt][:]
            Fs = this.o4triFs[this.opposite_edge_alt][:]
            this.trisO4Shape.setBaseVertexProperties(Vs = Vs)
            this.trisO4Shape.setBaseEdgeProperties(Es = Es)
            this.trisO4Shape.setBaseFaceProperties(Fs = Fs)
            theShapes.append(this.trisO4Shape)
            if (not this.onlyRegFs):
                # when you use the rot alternative the rot is leading for
                # choosing the colours.
                if this.opposite_edge_alt & heptagons.rot_bit:
                    eAlt = this.opposite_edge_alt
                else:
                    eAlt = this.edge_alt
                Fs = this.triFs[this.edge_alt][:]
                Fs.extend(this.oppTriFs[this.opposite_edge_alt])
                Es = this.triEs[this.edge_alt][:]
                Es.extend(this.oppTriEs[this.opposite_edge_alt])
                colIds = this.triColIds[eAlt]
                this.xtraTrisShape.setBaseVertexProperties(Vs = Vs)
                this.xtraTrisShape.setBaseEdgeProperties(Es = Es)
                this.xtraTrisShape.setBaseFaceProperties(
                    Fs = Fs,
                    colors = ([rgb.darkRed[:], rgb.yellow[:], rgb.magenta[:]],
                              colIds))
                theShapes.append(this.xtraTrisShape)
        for isom_shape in theShapes:
            isom_shape.show_base_only = not this.apply_symmetries
        this.setShapes(theShapes)
        this.update_shape = False

    def initArrs(this):
        #
        # o4: 5 -> 18 -> 19 -> 20
        #     0 -> 21 -> 22 -> 23
        #    12 -> 28 -> 29 -> 30
        #     6 -> 31
        #
            # 6" = 16
        #             6' = 15             12 = 2"
            #          o4          0
            #                                    10 = 1"
            #  6'" = 17     6             1   o3
            #                                            11 = 2'
            #                                    9 = 1'
            #
            #             5                 2
            #
            #
            #        14        4       3        8 = 0'
            #
            #
            #         2' = 13               7 = 5'
        #
        #               o3: 7 -> 24 -> 25
        #                   0 -> 26 -> 27
        I_loose = [[2, 3, 7]]
        noLoose = [[2, 3, 8]]
        stripI  = [[2, 8, 9]]
        stripII = [[2, 3, 9], [3, 8, 9]]
        star    = [[1, 2, 8], [1, 8, 9]]
        refl_1  = [[2, 3, 7], [1, 2, 25, 31], [0, 1, 31, 21]]
        refl_2  = [[4, 5, 30], [5, 6, 10, 12], [0, 27, 10, 6]]
        strip_1_loose = stripI[:]
        star_1_loose  = star[:]
        stripI.extend(noLoose)
        star.extend(noLoose)
        strip_1_loose.extend(I_loose)
        star_1_loose.extend(I_loose)
        this.triFs = {
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
        stripI  = [[5, 17, 14]]
        stripII = [[4, 5, 17], [4, 17, 14]]
        star    = [[5, 6, 14], [6, 17, 14]]
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
        arot_star.append([5, 20, 17])
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
            trisAlt.refl_1:             refl[:],
            trisAlt.refl_2:             refl[:],
        }
        stdO3   = [6, 17, 5]
        stdO3_x = [6, 17, 13]
        altO3   = [5, 20, 17]
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

        strip      = [0, 1, 1, 1, 0, 0]
        loose      = [0, 0, 1, 0, 1, 1]
        star1loose = [0, 1, 0, 0, 1, 1]
        rot        = [1, 0, 0, 0, 1, 0]
        rot_x      = [0, 0, 1, 1, 1, 0]
        arot_x     = [1, 1, 0, 0, 1, 0]
        refl_1     = [1, 1, 0]
        refl_2     = [1, 1, 0]

        this.triColIds = {
            trisAlt.strip_1_loose:      loose,
            trisAlt.strip_I:        strip,
            trisAlt.strip_II:       strip,
            trisAlt.star:           strip,
            trisAlt.star_1_loose:       star1loose,
            trisAlt.alt_strip_I:        strip,
            trisAlt.alt_strip_II:       strip,
            trisAlt.alt_strip_1_loose:  loose,
            trisAlt.rot_strip_1_loose:  rot,
            trisAlt.arot_strip_1_loose: rot,
            trisAlt.rot_star_1_loose:   rot_x,
            trisAlt.arot_star_1_loose:  arot_x,
            trisAlt.refl_1:             refl_1,
            trisAlt.refl_2:             refl_2,
        }

        std    = [1, 9, 10]
        alt    = [2, 11, 12]
        refl_1 = [2, 7, 11, 24, 12, 25]
        refl_2 = [0, 26, 27]
        this.o3triFs = {
            trisAlt.strip_1_loose:      [std],
            trisAlt.strip_I:        [std],
            trisAlt.strip_II:       [std],
            trisAlt.star:           [std],
            trisAlt.star_1_loose:       [std],
            trisAlt.alt_strip_I:        [alt],
            trisAlt.alt_strip_II:       [alt],
            trisAlt.alt_strip_1_loose:  [alt],
            trisAlt.refl_1:             [refl_1],
            trisAlt.refl_2:             [refl_2],
        }

        std  = [6, 15, 16, 17]
        alt  = [5, 18, 19, 20]
        refl_1 = [0, 21, 22, 23]
        refl_2 = [5, 12, 18, 28, 19, 29, 20, 30]
        this.o4triFs = {
            trisAlt.strip_1_loose:      [std],
            trisAlt.strip_I:        [std],
            trisAlt.strip_II:       [std],
            trisAlt.star:           [std],
            trisAlt.star_1_loose:       [std],
            trisAlt.alt_strip_I:        [alt],
            trisAlt.alt_strip_II:       [alt],
            trisAlt.alt_strip_1_loose:  [alt],
            trisAlt.rot_strip_1_loose:  [std],
            trisAlt.arot_strip_1_loose: [alt],
            trisAlt.rot_star_1_loose:   [std],
            trisAlt.arot_star_1_loose:  [alt],
            trisAlt.refl_1:             [refl_1],
            trisAlt.refl_2:             [refl_2],
        }

        strip_1_loose = [2, 7, 2, 8, 2, 9]
        stripI        = [3, 8, 2, 8, 2, 9]
        stripII       = [3, 8, 3, 9, 2, 9]
        star          = [3, 8, 2, 8, 1, 8]
        star_1_loose  = [2, 7, 2, 8, 1, 8]
        refl_1        = [2, 7, 2, 25, 1, 31, 0, 21]
        refl_2        = [30, 5, 5, 12, 6, 10, 0, 26]
        this.triEs = {
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
        }

        strip_1_loose = [5, 14, 5, 17]
        stripI        = [5, 14, 5, 17]
        stripII       = [4, 17, 5, 17]
        star          = [5, 14, 6, 14]
        star_1_loose  = [5, 14, 6, 14]
        rot_strip     = [13, 17, 5, 17]
        rot_star      = [13, 17, 6, 13]
        arot_star     = [13, 17, 5, 17]
        refl          = []
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
            trisAlt.refl_1:             refl,
            trisAlt.refl_2:             refl,
        }

        std  = [1, 9, 9, 10, 10, 1]
        alt  = [2, 11, 11, 12, 12, 2]
        refl = []
        this.o3triEs = {
            trisAlt.strip_1_loose:      std,
            trisAlt.strip_I:        std,
            trisAlt.strip_II:       std,
            trisAlt.star:           std,
            trisAlt.star_1_loose:       std,
            trisAlt.alt_strip_I:        alt,
            trisAlt.alt_strip_II:       alt,
            trisAlt.alt_strip_1_loose:  alt,
            trisAlt.refl_1:         refl,
            trisAlt.refl_2:         refl,
        }

        std    = [6, 15, 15, 16, 16, 17, 17, 6]
        alt    = [5, 18, 18, 19, 19, 20, 20, 5]
        refl   = []
        this.o4triEs = {
            trisAlt.strip_1_loose:      std,
            trisAlt.strip_I:        std,
            trisAlt.strip_II:       std,
            trisAlt.star:           std,
            trisAlt.star_1_loose:       std,
            trisAlt.alt_strip_I:        alt,
            trisAlt.alt_strip_II:       alt,
            trisAlt.alt_strip_1_loose:  alt,
            trisAlt.rot_strip_1_loose:  std,
            trisAlt.arot_strip_1_loose: alt,
            trisAlt.rot_star_1_loose:   std,
            trisAlt.arot_star_1_loose:  alt,
            trisAlt.refl_1:         refl,
            trisAlt.refl_2:         refl,
        }

class CtrlWin(heptagons.FldHeptagonCtrlWin):
    def __init__(self, shape, canvas, *args, **kwargs):
        heptagons.FldHeptagonCtrlWin.__init__(self,
            shape, canvas,
            8, # maxHeigth
            [ # prePosLst
                Stringify[ONLY_HEPTS],
                Stringify[DYN_POS],
                Stringify[T32],
                Stringify[T24_S6],
                Stringify[T24_S30],
                Stringify[T32_S24],
                Stringify[T56_S6],
                Stringify[S_T8_S6],
            ],
            [trisAlt],
            Stringify,
            *args, **kwargs
        )

    def has_only_hepts(self):
        return self.pre_pos_enum == ONLY_HEPTS and not (
            self.tris_fill is None) and not (
            self.tris_fill == trisAlt.refl_1 or
            self.tris_fill == trisAlt.refl_2)

    def has_only_o3_triangles(self):
        return self.pre_pos_enum == ONLY_XTRA_O3S and not (
            self.tris_fill is None) and not (
            self.tris_fill == trisAlt.refl_1 or
            self.tris_fill == trisAlt.refl_2)

    rDir = 'data/Data_FldHeptS4'
    rPre = 'frh-roots'

    def printFileStrMapWarning(self, filename, funcname):
        logging.warning(f"unable to interprete filename {filename}")

    @property
    def special_pos_setup(self):
        prePosId = self.pre_pos_enum
        if prePosId != OPEN_FILE and prePosId != DYN_POS:
            # use correct predefined special positions
            if self.shape.has_reflections:
                psp = self.predefReflSpecPos
            else:
                psp = self.predefRotSpecPos
            if self.special_pos_idx >= len(psp[self.pre_pos_enum]):
                self.special_pos_idx = -1
            in_data = psp[self.pre_pos_enum][self.special_pos_idx]
            fold_method_str = self.filename_map_fold_method(in_data['file'])
            assert fold_method_str is not None
            tris_str = self.filename_map_tris_fill(in_data['file'])
            assert tris_str is not None
            tris_alt = trisAlt.key[tris_str]
            data = {
                'set': in_data['set'],
                '7fold': heptagons.FoldMethod.get(fold_method_str),
                'tris': tris_alt,
                'fold-rot': self.filename_map_fold_pos(in_data['file'])
            }
            logging.info(f"see file {self.rDir}/{in_data['file']}")
            return data

    predefReflSpecPos = {
        ONLY_HEPTS: [
            {
                'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_2.json',
                'set': [0.0194846506, 2.5209776869, 0.7387578325, -0.2490014706, 1.5707963268],
            },{
                'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_2.json',
                'set': [1.9046884810, -0.0895860579, 0.0898667459, -0.8043880107, 1.5707963268],
            },{
                'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_1.json',
                'set': [2.3689660916, 0.0851258971, -0.0853666149, 2.1212284837],
            },{
                'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_2.json',
                'set': [0.1801294042, -0.5679882382, 2.7691714565, -0.1647931959, 1.5707963268],
            },{
                'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_1.json',
                'set': [0.1985558264, -0.7212633593, 2.5993674146, -0.2638659586],
            },{
                'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_1.json',
                'set': [2.3706859974, -0., 1.4330985471, 1.1300265566],
            },{
                'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_2.json',
                'set': [1.9053212843, 0.0000000000, 2.0476430098, 0.6938789411, 1.5707963268],
            },{
                'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_1.json',
                'set': [2.3706859974, 0., 0.1376977796, 2.0115660970],
            },{
                'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_2.json',
                'set': [1.9053212843, 0.0000000000, -0.1370097736, -0.6938789411, 1.5707963268],
            },{
                'file': 'frh-roots-0_0_0_0-fld_w.0-refl_1.json',
                'set': [0.2144969422, -0.7161063284, 2.4479090034, 0.2591004995],
            },{
                'file': 'frh-roots-0_0_0_0-fld_w.0-refl_1.json',
                'set': [1.82916035932, -0.15381215148, -0.73341848407, 2.31852723230],
            },{
                'file': 'frh-roots-0_0_0_0-fld_w.0-refl_2.json',
                'set': [1.8797513382, -0.0971685207, -0.3990474779, 0.9416509246, 1.5707963268],
            },{
                'file': 'frh-roots-0_0_0_0-fld_w.0-refl_2.json',
                'set': [0.0078461298, 2.5240450735, 0.6010013359, 0.2588481477, 1.5707963268],
            },{
                'file': 'frh-roots-0_0_0_0-fld_w.0-refl_2.json',
                'set': [1.4801185612, -0.2147509348, -0.4352845433, 2.4498730531, 1.5707963268],
            }],
        T32: [
            {
                'file': 'frh-roots-0_1_0_0-fld_shell.0-refl_1.json',
                'set': [3.093153915430, 0.729243464900, -0.945924630830, -0.096403292160],
            },{
                'file': 'frh-roots-0_1_0_0-fld_shell.0-refl_1.json',
                'set': [-0.332872892420, -0.893052366940, 2.214241531650, 0.687772958620],
            },{
                'file': 'frh-roots-0_1_0_0-fld_shell.0-refl_1.json',
                'set': [0.421896888630, 2.219588015690, 1.676036388580, -1.494259152020],
            },{
                'file': 'frh-roots-0_1_0_0-fld_w.0-refl_1.json',
                'set': [3.092923453320, 0.727933307540, -0.999726774000, 0.098142305430]
            },{
                'file': 'frh-roots-0_0_0_1-fld_parallel.0-refl_2.json',
                'set': [1.905321284300, 0., 2.393952118600, 0.264321652700, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_0_0_1-fld_parallel.0-refl_2.json',
                'set': [1.905321284300, 0., 2.393952118600, -3.141592653600, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_0_0_1-fld_shell.0-refl_2.json',
                'set': [0.2179969435, 2.7336997789, 0.436861266, -0.7278977049, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_0_0_1-fld_shell.0-refl_2.json',
                'set': [0.2179969436, 2.7336997789, 0.436861266, -2.5831328643, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_0_0_1-fld_trapezium.0-refl_2.json',
                'set': [0.1349389146, 2.780603028, -0.1223292567, 0.7819930312, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_0_0_1-fld_triangle.0-refl_2.json',
                'set': [1.9053212843, 0., 2.4754835091, -2.0480015805, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_0_0_1-fld_triangle.0-refl_2.json',
                'set': [1.9053212843, 0., 2.4754835091, -0.192766421, pos_angle_refl_2]
            },{
                # This can be investigated more, 4 triangles could be replaced
                # by one; could this be a new triangle fill alternative.
                # By increasing the translation to ~2.88 you get 3 triangles
                # that can be replaced by an hexagon: interesting,..
                'file': 'frh-roots-0_0_0_1-fld_triangle.0-refl_2.json',
                'set': [1.9053212843, 0., 1.4704335102, 1.7538347714, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_0_0_1-fld_w.0-refl_2.json',
                'set': [0.1338474664, 2.7564205113, 0.0542587182, 0.7283276276, pos_angle_refl_2]
            }],
        T24_S6: [
            {
                'file': 'frh-roots-0_1_0_0-fld_shell.0-refl_2.json',
                'set': [2.8994205035, 0.2542437305, -0.2608593723, -0.1061100151, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_1_0_0-fld_shell.0-refl_2.json',
                'set': [-0.6034905409, -0.7752097191, 2.5167648076, 0.6538549688, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_1_0_0-fld_shell.0-refl_2.json',
                'set': [0.7058724522, 2.3389880983, 1.1277333437, -1.1550885309, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_1_0_0-fld_shell.0-refl_2.json',
                'set': [0.7058724522, 2.3389880983, 1.1277333437, -3.0103236904, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_1_0_0-fld_shell.0-refl_2.json',
                'set': [2.8994205035, 0.2542437305, -0.2608593723, 1.7491251444, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_1_0_0-fld_w.0-refl_2.json',
                'set': [2.899122714800, 0.254122067300, -0.321373808900, 0.108230610700, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_1_0_0-fld_triangle.0-refl_2.json',
                'set': [2.905321284300, 0., 1.470433510200, 0.467477277300, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_1_0_0-fld_triangle.0-refl_2.json',
                'set': [2.905321284300, 0., 1.470433510200, -1.387757882200, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_1_0_0-fld_triangle.0-refl_2.json',
                'set': [2.905321284300, 0., 0.440199726000, -0.467477277300, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_1_0_0-fld_triangle.0-refl_2.json',
                'set': [2.905321284300, 0., 0.440199726000, 1.387757882200, pos_angle_refl_2]
            },{
                'file': 'frh-roots-0_0_0_1-fld_parallel.0-refl_1.json',
                'set': [2.37068599744, 0., 2.12592133774, -0.23291939219]
            },{
                'file': 'frh-roots-0_0_0_1-fld_parallel.0-refl_1.json',
                'set': [2.37068599744, 0., 2.12592133774, -2.44812695649]
            },{
                'file': 'frh-roots-0_0_0_1-fld_shell.0-refl_1.json',
                'set': [0.43294725225, 2.54026836305, 0.70692391148, -2.57893149341]
            },{
                'file': 'frh-roots-0_0_0_1-fld_trapezium.0-refl_1.json',
                'set': [0.3906376173, 2.71977645634, -0.82677451079, 1.02947405206]
            },{
                'file': 'frh-roots-0_0_0_1-fld_trapezium.0-refl_1.json',
                'set': [0.3906376173, 2.71977645634, -3.0419820751, 1.02947405206]
            },{
                'file': 'frh-roots-0_0_0_1-fld_triangle.0-refl_1.json',
                'set': [2.37068599744, 0., 2.05615681203, -1.70740415397]
            },{
                'file': 'frh-roots-0_0_0_1-fld_triangle.0-refl_1.json',
                'set': [2.37068599744, 0., 2.05615681203, 0.14783100544]
            }],
        T24_S30: [
            {
                'file': 'frh-roots-0_0_1_1-fld_triangle.0-refl_1.json',
                'set': [2.370685997440, 0., 2.056156812030, 1.434188499620]
            },{
                'file': 'frh-roots-0_0_1_1-fld_w.0-refl_1.json',
                'set': [0.381107235470, 2.557316971200, 1.008389980790, -0.521296594410]
            }],
        T32_S24: [
            {
                'file': 'frh-roots-0_0_1_1-fld_shell.0-refl_2.json',
                'set': [0.2179969435, 2.7336997789, 0.436861266, 0.5584597893, pos_angle_refl_2]
            }, {
                'file': 'frh-roots-0_0_1_1-fld_triangle.0-refl_2.json',
                'set': [1.9053212843, 0., 2.4754835091, 1.0935910731, pos_angle_refl_2]
            }, {
                'file': 'frh-roots-0_0_1_1-fld_w.0-refl_2.json',
                'set': [0.1742788711, 2.7454895051, 0.7338481676, -0.5214493418, pos_angle_refl_2]
            }],
        T56_S6: [
            {
                'file': 'frh-roots-0_1_0_1-fld_trapezium.0-refl_1.json',
                'set': [3.350523864960, 0.204096577780, 1.688905367760, -0.385851963150]
            },{
                'file': 'frh-roots-0_1_0_1-fld_trapezium.0-refl_1.json',
                'set': [3.350523864960, 0.204096577780, -0.526302196540, -0.385851963150]
            },{
                'file': 'frh-roots-0_1_0_1-fld_w.0-refl_1.json',
                'set': [3.321209142030, 0.061533063700, 0.400357498920, -0.860656783220]
            },{
                'file': 'frh-roots-0_1_0_1-fld_parallel.0-refl_1.json',
                'set': [3.370685997440, 0., 1.091435866210, 0.801566079340]
            },{
                'file': 'frh-roots-0_1_0_1-fld_parallel.0-refl_1.json',
                'set': [3.370685997440, 0., 1.091435866210, -1.413641484960]
            },{
                'file': 'frh-roots-0_1_0_1-fld_parallel.0-refl_1.json',
                'set': [3.370685997440, 0., 0.479360460590, -0.801566079340]
            },{
                'file': 'frh-roots-0_1_0_1-fld_parallel.0-refl_1.json',
                'set': [3.370685997440, 0., 0.479360460590, 1.413641484960]
            },{
                'file': 'frh-roots-0_1_0_1-fld_parallel.0-refl_2.json',
                'set': [2.90532128432676, 0, 1.71656655198914, -2.46420708701138, 1.5707963267949]
            },{
                'file': 'frh-roots-0_1_0_1-fld_parallel.0-refl_2.json',
                'set': [2.90532128432676, 0, 1.71656655198914, 0.94170721928212, 1.5707963267949]
            },{
                'file': 'frh-roots-0_1_0_1-fld_parallel.0-refl_2.json',
                'set': [2.90532128432676, 0, 0.19406668425988, 2.46420708701137, 1.5707963267949]
            },{
                'file': 'frh-roots-0_1_0_1-fld_parallel.0-refl_2.json',
                'set': [2.90532128432676, 0, 0.19406668425988, -0.94170721928212, 1.5707963267949]
            }],
    }
    predefRotSpecPos = {
        ONLY_HEPTS: [
            {
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.6-alt_strip_II-opp_alt_strip_I-pos-0.json',
                'set': [1.660304510396, 1.131428067207, -1.753834771439, 1.028812965054, 1.008752965352, -1.753834771439, 2.089397910429],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.6-alt_strip_II-opp_alt_strip_I-pos-0.json',
                'set': [1.318214671651, 1.634330675629, -1.753834771439, -0.123550494574, 0.963776965686, -1.753834771439, 1.890882378455],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.1-alt_strip_I-opp_alt_strip_II-pos-0.json',
                'set': [1.2275167604097, 2.3455801863989, -1.7538347714396, 0.6905325364774, 0.4614593061065, -1.753834771439, -0.041379464264],
            },{
                # also frh-roots-1_0_1_0_0_1_0-fld_w.6-alt_strip_II-opp_strip_I-pos-0.json
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.6-alt_strip_II-opp_shell-pos-0.json',
                'set': [1.887187237412, 2.167011989158, 1.926283193814, -1.058983114165, 0.621290661281, -0.664678942700, -1.058983114165],
            },{
                'file': 'frh-roots-0_0_1_0_0_1_0-fld_w.0-shell_1_loose-opp_shell_1_loose.json',
                'set': [2.134874485396, -0.583925900536, 2.114788565317, -0.848112522958, -2.338772404203, 2.787521022442, -2.374081458163],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_shell.0-alt_strip_II-opp_alt_strip_II.json',
                'set': [1.642456721956, 1.402279094735, -1.646522348731, -1.956656738624, 0.982920989544, -0.249747722020, -2.643294872695],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.5-strip_I-opp_strip_I-pos-0.json',
                'set': [2.196514118977, -0.000000481824, -1.542208052853, 2.649117969767, 0.782964553769, 1.974397692900, 0.000000772786],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.5-strip_I-opp_strip_I-pos-0.json',
                'set': [1.922929227843, -0.000000713874, -0.599929623618, 2.938198764507, 0.724623498417, 2.183451588501, 0.000001144966],
            },{
                # also frh-roots-1_0_1_0_0_1_0-fld_w.2-shell-opp_strip_I-pos-0.json
                # frh-roots-1_0_1_0_0_1_0-fld_w.2-strip_I-opp_shell-pos-0.json
                # frh-roots-1_0_1_0_0_1_0-fld_w.2-strip_I-opp_strip_I-pos-0.json
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.2-shell-opp_shell-pos-0.json',
                'set': [1.006674583155, 3.141592199367, -2.245363652103, 0.000000728517, 0.869161398311, 0.798074515457, 1.091453351858],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_shell.0-alt_strip_II-opp_alt_strip_II.json',
                'set': [1.582941969693, 1.309072560855, -1.650557370807, -2.447899234189, 0.891424433510, -1.350012782042, -2.738031681676],
            },{
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_shell.0-alt_strip_II-opp_alt_strip_II.json',
                'set': [-0.866025403784, -2.222676713307, -2.064570332814, -1.619344079087, 0.555984796217, -2.064570332814, 2.696366399863],
            }],
        S_T8_S6: [
            {
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_w.0-alt_strip_1_loose-opp_shell_1_loose.json',
                'set': [-2.679365251097, 2.796908311439, -1.850193700211, 2.489978770549, -2.001506476747, 1.648055108390, -0.522175830402],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_w.0-shell_1_loose-opp_alt_strip_1_loose.json',
                'set': [-2.543235013907, 2.814916149801, 1.655501423218, -0.688804482734, -2.526543126431, -1.698340172877, 2.389039768812],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_shell.0-alt_strip_II-opp_alt_strip_I.json',
                'set': [2.590217278372, 1.158363623026, -1.475190229349, 0.0, 0.888168913304, -1.245429246161, 0.0],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_shell.0-alt_strip_II-opp_alt_strip_I.json',
                'set': [2.590217278372, 1.158363623026, -1.475190229349, 0.0, 0.888168913304, 0.049971521322, 0.0]
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_shell.0-alt_strip_II-opp_alt_strip_I.json',
                'set': [2.590217278372, 1.158363623026, 0.709462554030, 0.000000000001, 0.888168913304, 0.049971521322, 0.000000000001],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_shell.0-alt_strip_II-opp_alt_strip_I.json',
                'set': [2.590217278372, 1.158363623026, 0.709462554030, 0.0, 0.888168913304, -1.245429246161, 0.0],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_shell.0-alt_strip_II-opp_alt_strip_I.json',
                'set': [2.590217278372, 1.158363623026, 0.70946255403, 0., 0.888168913304, -1.245429246161, 0.],
            },{
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_shell.0-alt_strip_1_loose-opp_strip_1_loose.json',
                'set': [-2.197000068047, 2.340848600228, 1.122472237655, 2.412926451764, -2.352510087024, 1.122472237655, 2.412926451765],
            }],
        T24_S6: [
            {
                'file': 'frh-roots-1_0_1_0_1_0_1-fld_shell.0-alt_strip_II-opp_alt_strip_I.json',
                'set': [-1.141029056551, -1.851205580480, -2.576549545626, 0.784198356242, 0.858393440458, 2.473883778277, 1.113105954025]
            }, {
                'file': 'frh-roots-1_0_1_0_1_0_1-fld_shell.0-alt_strip_II-opp_alt_strip_I.json',
                'set': [1.921997262443, 1.218559157083, -1.248804430587, 2.148304506456, 0.546329691525, 0.582189155668, 1.762965029632]
            }, {
                'file': 'frh-roots-1_0_1_0_1_0_1-fld_shell.0-alt_strip_II-opp_alt_strip_I.json',
                'set': [-2.051616116564, 1.500996115912, 1.177736425250, 0.936877691418, -2.305372874457, -0.247208002545, 1.086337936590]
            }, {
                'file': 'frh-roots-1_0_1_0_0_1_1-fld_shell.0-alt_strip_II-opp_alt_strip_II.json',
                'set': [2.090101676534, 1.637528980885, -1.095970217463, -0.879737866894, 0.800996136431, -1.882616118320, -0.138920603584]
            }, {
                'file': 'frh-roots-1_0_1_0_0_1_1-fld_shell.0-alt_strip_II-opp_alt_strip_II.json',
                'set': [1.910535022139, 1.444658548384, 0.153302501729, -2.027442812402, 0.615784119053, -2.174746648230, -0.843855915796]
            }, {
                'file': 'frh-roots-1_0_1_0_0_1_1-fld_shell.0-alt_strip_II-opp_shell.json',
                'set': [2.185434158696, 1.514092033328, -0.393265132210, -1.035923121424, 0.613632866194, 1.030378124732, -0.526044852380]
            }, {
                'file': 'frh-roots-1_0_1_0_0_1_1-fld_shell.0-alt_strip_II-opp_shell.json',
                'set': [2.185434158696, 1.514092033328, -0.393265132210, -1.035923121424, 0.613632866194, 1.030378124732, -2.741252416682]
            }, {
                'file': 'frh-roots-1_0_1_0_0_1_1-fld_shell.0-alt_strip_II-opp_shell.json',
                'set': [1.863979769045, 1.428464818300, 0.222069333254, -2.176752860496, 0.623239886239, 1.617590079465, 3.031354018117]
            }, {
                'file': 'frh-roots-1_0_1_0_0_1_1-fld_shell.0-alt_strip_II-opp_shell.json',
                'set': [1.863979769045, 1.428464818300, 0.222069333255, -2.176752860497, 0.623239886239, 1.617590079466, -1.036623724762]
            }, {
                'file': 'frh-roots-1_0_1_0_1_0_1-fld_w.0-shell_1_loose-opp_alt_strip_1_loose.json',
                'set': [2.735496407311, 0.711235714044, -1.124119809269, -1.079360570440, 0.864049311950, 0.718239976290, -1.119743102961]
            }, {
                'file': 'frh-roots-1_0_1_0_0_1_1-fld_w.0-shell-opp_shell.json',
                'set': [3.120450605047, 0.786914013717, -0.752642683093, -0.826668531662, 0.875700086111, -1.468188723031, 0.413534192558]
            }],
        T56_S6: [
            {
                'file': 'frh-roots-0_0_1_1_0_1_1-fld_shell.0-shell_1_loose-opp_shell_1_loose.json',
                'set': [3.183333507667, 0.80795231397, -1.143096876451, 2.558896234707, 0.854052155544, -1.143096876452, -0.44297383909]
            }, {
                'file': 'frh-roots-0_0_1_1_0_1_1-fld_shell.0-shell_1_loose-opp_shell_1_loose.json',
                'set': [3.183333507667, 0.807952313970, -1.143096876452, -0.847018071586, 0.854052155544, -1.143096876451, -0.442973839090]
            }, {
                'file': 'frh-roots-0_0_1_1_0_1_1-fld_shell.0-shell_1_loose-opp_shell_1_loose.json',
                'set': [3.183333507667, 0.807952313970, -1.143096876452, -0.847018071586, 0.854052155544, -1.143096876452, 1.772233725212]
            }, {
                'file': 'frh-roots-0_0_1_1_0_1_1-fld_shell.0-shell_1_loose-opp_shell_1_loose.json',
                'set': [3.183333507667, 0.8079523139697, -1.1430968764522, 2.5588962347075, 0.8540521555439, -1.1430968764523, 1.7722337252118]
            }, {
                'file': 'frh-roots-0_0_1_1_0_1_1-fld_w.0-shell_1_loose-opp_shell_1_loose.json',
                'set': [3.112096816216, 0.78432621749, -1.707364893904, 0.903431422151, 0.881057789442, -1.473905662151, 0.3936303937]
            }],
    }

class Scene(Geom3D.Scene):
    def __init__(self, parent, canvas):
        Geom3D.Scene.__init__(self, Shape, CtrlWin, parent, canvas)
