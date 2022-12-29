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

from orbitit import geom_3d, geomtypes, isometry, heptagons, rgb
from orbitit.geomtypes import Rot3 as Rot
from orbitit.geomtypes import Vec3 as Vec

TITLE = "Polyhedra with Folded Regular Heptagons and Tetrahedral Symmetry"

V2 = math.sqrt(2)

trisAlt = heptagons.TrisAlt()
trisAlt.base_key = {
    trisAlt.strip_I: True,
    trisAlt.strip_II: True,
    trisAlt.star: True,
    trisAlt.strip_1_loose: True,
    trisAlt.star_1_loose: True,
    trisAlt.alt_strip_I: True,
    trisAlt.alt_strip_II: True,
    trisAlt.alt_strip_1_loose: True,
    trisAlt.twist_strip_I: True,
}

counter = heptagons.TrisCounter()

DYN_POS = heptagons.DYN_POS
OPEN_FILE = heptagons.OPEN_FILE
# symmtric edge lengths: b0 == b1, c0 == c1, d0 == d1
S_T8 = heptagons.ONLY_XTRA_O3S
S_ONLY_HEPTS = heptagons.ONLY_HEPTS
S_T16 = counter.get_next_id()
S_T24 = counter.get_next_id()
S_T32 = counter.get_next_id()
S_T40 = counter.get_next_id()
S_T48 = counter.get_next_id()
S_T56 = counter.get_next_id()
S_T80 = counter.get_next_id()

# symmtric edge lengths with flat squares
S_T16_S12 = counter.get_next_id()

# symmtric edge lengths with folded squares
S_S12 = counter.get_next_id()
S_T8_S12 = counter.get_next_id()
S_S24 = counter.get_next_id()
S_T8_S24 = counter.get_next_id()
S_T24_S12 = counter.get_next_id()
S_T8_S36 = counter.get_next_id()
S_T32_S12 = counter.get_next_id()
S_T32_S24 = counter.get_next_id()
S_T56_S12 = counter.get_next_id()

# symmtric edge lengths with hexagon
S_T24_H4 = counter.get_next_id()

# non-symmetryc edge lengths
T8 = counter.get_next_id()
T16 = counter.get_next_id()
T24 = counter.get_next_id()
T32 = counter.get_next_id()
T40 = counter.get_next_id()
T64 = counter.get_next_id()

Stringify = {
    DYN_POS: "Enable Sliders",
    # symmtric edge lengths: b0 == b1, c0 == c1, d0 == d1
    S_ONLY_HEPTS: "Only heptagons",
    S_T8: "Heptagons and 8 Triangles",
    S_T16: "SEL: 16 Triangles",
    S_T24: "SEL: 24 Triangles",
    S_T32: "SEL: 32 Triangles",
    S_T40: "SEL: 40 Triangles",
    S_T48: "SEL: 48 Triangles",
    S_T56: "SEL: 56 Triangles",
    S_T80: "SEL: 80 Triangles Equilateral",
    # with flat squares
    S_T16_S12: "SEL: 28 = 16 Triangles and 12 Squares",
    # with folded squares:
    S_S12: "SEL: 12 Folded Squares",
    S_T8_S12: "SEL: 20 = 8 Triangles + 12 Folded Squares",
    S_S24: "SEL: 24 Folded Squares",
    S_T8_S24: "SEL: 32 = 8 Triangles + 24 Folded Squares",
    S_T24_S12: "SEL: 36 = 24 Triangles + 12 Folded Squares",
    S_T8_S36: "SEL: 44 = 8 Triangles + 36 Folded Squares",
    S_T32_S12: "SEL: 44 = 32 Triangles + 12 Folded Squares",
    S_T32_S24: "SEL: 56 = 32 Triangles + 24 Folded Squares",
    S_T56_S12: "SEL: 68 = 56 Triangles + 12 Folded Squares",
    # with hexagons
    S_T24_H4: "SEL: 28 = 24 Triangles + 4 Hexagons",
    # non-symmetric edges lengths
    T8: " 8 Triangles (O3)",
    T16: "16 Triangles",
    T24: "24 Triangles",
    T32: "32 Triangles",
    T40: "40 Triangles",
    T64: "64 Triangles",
}


def Vlen(v0, v1):
    x = v1[0] - v0[0]
    y = v1[1] - v0[1]
    z = v1[2] - v0[2]
    return math.sqrt(x * x + y * y + z * z)


# get the col faces array by using a similar shape here, so it is calculated
# only once
use_isom = isometry.A4()
use_black_and_white = False
col_stabiliser = isometry.C2(setup={"axis": [1.0, 0.0, 0.0]})
col_stabiliser = isometry.C2(setup={"axis": [0.0, 0.0, 1.0]})
col_stabiliser = isometry.C2(setup={"axis": [0.0, 1.0, 0.0]})
# col_stabiliser = isometry.C3(setup={'axis': [1.0, 1.0, 1.0]})
# col_stabiliser = isometry.C3(setup={'axis': [1.0, -1.0, 1.0]})
colQuotientSet = use_isom / col_stabiliser
if use_black_and_white:
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
        rgb.cornflowerBlue,
        rgb.limeGreen,
        rgb.mistyRose1,
        rgb.mediumBlue,
        rgb.gray20,
    ]

heptColPerIsom = []
for isom in use_isom:
    for subSet, i in zip(colQuotientSet, list(range(len(colQuotientSet)))):
        if isom in subSet:
            heptColPerIsom.append(useRgbCols[i])
            break
isomsO3 = isometry.D2()


class Shape(heptagons.FldHeptagonShape):
    def __init__(this, *args, **kwargs):
        heptagonsShape = geom_3d.SymmetricShape(
            vs=[], fs=[], isometries=isometry.A4(), name="FoldedHeptagonsA4"
        )
        xtraTrisShape = geom_3d.SymmetricShapeSplitCols(
            vs=[], fs=[], isometries=isometry.A4(), name="xtraTrisA4"
        )
        trisO3Shape = geom_3d.SymmetricShape(
            vs=[], fs=[], isometries=isomsO3, colors=[rgb.cyan[:]], name="o3TrisA4"
        )
        heptagons.FldHeptagonShape.__init__(
            this, [heptagonsShape, xtraTrisShape, trisO3Shape], name="FoldedRegHeptA4"
        )
        this.heptagonsShape = heptagonsShape
        this.xtraTrisShape = xtraTrisShape
        this.trisO3Shape = trisO3Shape
        this.pos_angle_min = -math.pi
        this.pos_angle_max = math.pi
        this.pos_angle = 0
        this.set_edge_alt(trisAlt.strip_1_loose, trisAlt.strip_1_loose)
        this.initArrs()
        this.set_vertices()

    def get_status_str(this):
        if this.update_shape:
            this.set_vertices()
        vs = this.baseVs
        es = this.triEs[this.edge_alt]
        a_len = f"{Vlen(vs[es[0]], vs[es[1]]):.2f}"
        b_len = f"{Vlen(vs[es[2]], vs[es[3]]):.2f}"
        c_len = f"{Vlen(vs[es[4]], vs[es[5]]):.2f}"
        es = this.o3triEs[this.edge_alt]
        d_len = f"{Vlen(vs[es[0]], vs[es[1]]):.2f}"
        if this.has_reflections:
            s = f"T = {this.height:.2f}; |a|: {a_len}, |b|: {b_len}, |c|: {c_len}, |d|: {d_len}"
        else:
            if this.edge_alt == trisAlt.twist_strip_I:
                es = this.oppTriEs[this.opposite_edge_alt][this.has_reflections]
            else:
                es = this.oppTriEs[this.opposite_edge_alt]
            opp_b_len = f"{Vlen(vs[es[0]], vs[es[1]]):.2f}"
            opp_c_len = f"{Vlen(vs[es[2]], vs[es[3]]):.2f}"
            es = this.oppO3triEs[this.opposite_edge_alt]
            if this.opposite_edge_alt != trisAlt.twist_strip_I:
                opp_d_len = f"{Vlen(vs[es[0]], vs[es[1]]):.2f}"
            else:
                opp_d_len = "-"
            s = "T = {:.2f}; |a|: {}, |b|: {} ({}), |c|: {} ({}), |d|: {} ({})".format(
                this.height, a_len, b_len, opp_b_len, c_len, opp_c_len, d_len, opp_d_len
            )
        return s

    def set_tri_fill_pos(this, i):
        logging.warning(f"TODO implement set_tri_fill_pos for {i}")

    def set_edge_alt(this, alt=None, oppositeAlt=None):
        heptagons.FldHeptagonShape.set_edge_alt(this, alt, oppositeAlt)
        # TODO correct edge alternative?

    def set_vertices(this):
        this.position_heptagon()
        vs = this.heptagon.vs[:]

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

        Rr = Rot(axis=Vec([1, 1, 1]), angle=geomtypes.THIRD_TURN)
        Rl = Rot(axis=Vec([-1, 1, 1]), angle=-geomtypes.THIRD_TURN)
        vs.append(Vec([-vs[5][0], -vs[5][1], vs[5][2]]))  # vs[7]
        vs.append(Rr * vs[0])  # vs[8]
        vs.append(Rr * vs[1])  # vs[9]
        vs.append(Rr * vs[9])  # vs[10]
        vs.append(Rr * vs[2])  # vs[11]
        vs.append(Rr * vs[11])  # vs[12]
        vs.append(Vec([-vs[2][0], -vs[2][1], vs[2][2]]))  # vs[13]
        vs.append(Rl * vs[0])  # vs[14]
        vs.append(Rl * vs[6])  # vs[15]
        vs.append(Rl * vs[-1])  # vs[16]
        vs.append(Rl * vs[5])  # vs[17]
        vs.append(Rl * vs[-1])  # vs[18]
        vs.append(Rr * vs[8])  # vs[19] = V0"
        vs.append(Rr * vs[6])  # vs[20] = V6'"
        vs.append(Rr * vs[5])  # vs[21] = V5'"

        vs.append(Rl * vs[13])  # vs[22] = V13'
        vs.append(Rl * vs[-1])  # vs[23] = V13"
        this.baseVs = vs
        es = []
        fs = []
        fs.extend(this.heptagon.fs)  # use extend to copy the list to fs
        es.extend(this.heptagon.es)  # use extend to copy the list to fs
        this.heptagonsShape.setBaseVertexProperties(vs=vs)
        this.heptagonsShape.setBaseEdgeProperties(es=es)
        # comment out this and nvidia driver crashes:...
        this.heptagonsShape.setBaseFaceProperties(fs=fs)
        this.heptagonsShape.setFaceColors(heptColPerIsom)
        theShapes = [this.heptagonsShape]
        if this.add_extra_faces:
            es = this.o3triEs[this.edge_alt][:]
            fs = this.o3triFs[this.edge_alt][:]
            es.extend(this.oppO3triEs[this.opposite_edge_alt])
            fs.extend(this.oppO3triFs[this.opposite_edge_alt])
            this.trisO3Shape.setBaseVertexProperties(vs=vs)
            this.trisO3Shape.setBaseEdgeProperties(es=es)
            this.trisO3Shape.setBaseFaceProperties(fs=fs)
            theShapes.append(this.trisO3Shape)
            if not this.all_regular_faces:
                # when you use the rot alternative the rot is leading for
                # choosing the colours.
                if this.opposite_edge_alt & heptagons.ROT_BIT:
                    eAlt = this.opposite_edge_alt
                else:
                    eAlt = this.edge_alt
                es = this.triEs[this.edge_alt][:]
                if this.edge_alt == trisAlt.twist_strip_I:
                    fs = this.triFs[this.edge_alt][this.has_reflections][:]
                    fs.extend(
                        this.oppTriFs[this.opposite_edge_alt][this.has_reflections]
                    )
                    es.extend(
                        this.oppTriEs[this.opposite_edge_alt][this.has_reflections]
                    )
                    # only draw the folds of the hexagon for the twisted variant
                    # if the hexagon isn't flat.
                    if not geom_3d.eq(abs(this.pos_angle) % (math.pi / 2), math.pi / 4):
                        es.extend(this.twistedEs_A4)
                    colIds = this.triColIds[eAlt][this.has_reflections]
                else:
                    fs = this.triFs[this.edge_alt][:]
                    fs.extend(this.oppTriFs[this.opposite_edge_alt])
                    es.extend(this.oppTriEs[this.opposite_edge_alt])
                    colIds = this.triColIds[eAlt]
                this.xtraTrisShape.setBaseVertexProperties(vs=vs)
                this.xtraTrisShape.setBaseEdgeProperties(es=es)
                this.xtraTrisShape.setBaseFaceProperties(
                    fs=fs,
                    colors=([rgb.darkRed[:], rgb.yellow[:], rgb.magenta[:]], colIds),
                )
                theShapes.append(this.xtraTrisShape)
        for isom_shape in theShapes:
            isom_shape.show_base_only = not this.apply_symmetries
        this.setShapes(theShapes)
        this.update_shape = False

    @property
    def refl_pos_angle(this):
        """Return the pos angle for a polyhedron with reflections."""
        if this.edge_alt & heptagons.TWIST_BIT == heptagons.TWIST_BIT:
            return math.pi / 4
        else:
            return 0

    def initArrs(this):
        logging.info(f"{this.name} initArrs")

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
        stripI = [[2, 8, 9]]
        stripII = [[2, 3, 9], [3, 8, 9]]
        star = [[1, 2, 8], [1, 8, 9]]
        strip_1_loose = stripI[:]
        star_1_loose = star[:]
        stripI.extend(noLoose)
        star.extend(noLoose)
        strip_1_loose.extend(I_loose)
        star_1_loose.extend(I_loose)
        twist_strip = {  # reflections included:
            False: [[2, 3, 7], [1, 2, 20], [0, 1, 8]],
            True: [[2, 3, 7], [1, 2, 21, 20], [0, 1, 20, 8]],
        }
        this.triFs = {
            trisAlt.strip_1_loose: strip_1_loose[:],
            trisAlt.strip_I: stripI[:],
            trisAlt.strip_II: stripII[:],
            trisAlt.star: star[:],
            trisAlt.star_1_loose: star_1_loose[:],
            trisAlt.alt_strip_1_loose: strip_1_loose[:],
            trisAlt.alt_strip_I: stripI[:],
            trisAlt.alt_strip_II: stripII[:],
            trisAlt.twist_strip_I: twist_strip,
        }
        stdO3 = [1, 2, 9]
        altO3 = [2, 9, 11]
        this.triFs[trisAlt.strip_1_loose].append(stdO3)
        this.triFs[trisAlt.strip_I].append(stdO3)
        this.triFs[trisAlt.strip_II].append(stdO3)
        this.triFs[trisAlt.alt_strip_1_loose].append(altO3)
        this.triFs[trisAlt.alt_strip_I].append(altO3)
        this.triFs[trisAlt.alt_strip_II].append(altO3)
        I_loose = [[5, 14, 13]]
        noLoose = [[3, 7, 8]]
        stripI = [[5, 15, 14]]
        stripII = [[4, 5, 15], [4, 15, 14]]
        star = [[5, 6, 14], [6, 15, 14]]
        strip_1_loose = stripI[:]
        star_1_loose = star[:]
        stripI.extend(noLoose)
        star.extend(noLoose)
        strip_1_loose.extend(I_loose)
        star_1_loose.extend(I_loose)
        rot_strip = [[13, 15, 14], [13, 5, 15]]
        rot_star = [[13, 15, 14], [13, 5, 6]]
        arot_star = [[13, 15, 14], [13, 17, 15]]
        twist_strip = {  # reflections included:
            False: [[1, 20, 8], [2, 21, 20]],
            True: [],
        }
        this.oppTriFs = {
            trisAlt.strip_1_loose: strip_1_loose[:],
            trisAlt.strip_I: stripI[:],
            trisAlt.strip_II: stripII[:],
            trisAlt.star: star[:],
            trisAlt.star_1_loose: star_1_loose[:],
            trisAlt.alt_strip_1_loose: strip_1_loose[:],
            trisAlt.alt_strip_I: stripI[:],
            trisAlt.alt_strip_II: stripII[:],
            trisAlt.rot_strip_1_loose: rot_strip[:],
            trisAlt.arot_strip_1_loose: rot_strip[:],
            trisAlt.rot_star_1_loose: rot_star[:],
            trisAlt.arot_star_1_loose: arot_star[:],
            trisAlt.twist_strip_I: twist_strip,
        }
        stdO3 = [6, 15, 5]
        stdO3_x = [6, 15, 13]
        altO3 = [5, 17, 15]
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
        twist = {False: [1, 1, 0, 0, 1], True: [1, 1, 0]}  # reflections included:
        this.triColIds = {
            trisAlt.strip_1_loose: loose,
            trisAlt.strip_I: strip,
            trisAlt.strip_II: strip,
            trisAlt.star: strip,
            trisAlt.star_1_loose: star1loose,
            trisAlt.alt_strip_I: strip,
            trisAlt.alt_strip_II: strip,
            trisAlt.alt_strip_1_loose: loose,
            trisAlt.rot_strip_1_loose: rot,
            trisAlt.arot_strip_1_loose: rot,
            trisAlt.rot_star_1_loose: rot_x,
            trisAlt.arot_star_1_loose: arot_x,
            trisAlt.twist_strip_I: twist,
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

        std = [1, 9, 10]
        alt = [2, 11, 12]
        twist = [0, 8, 19]
        this.o3triFs = {
            trisAlt.strip_1_loose: [std],
            trisAlt.strip_I: [std],
            trisAlt.strip_II: [std],
            trisAlt.star: [std],
            trisAlt.star_1_loose: [std],
            trisAlt.alt_strip_I: [alt],
            trisAlt.alt_strip_II: [alt],
            trisAlt.alt_strip_1_loose: [alt],
            trisAlt.twist_strip_I: [twist],
        }
        std = [6, 16, 15]
        alt = [5, 18, 17]
        # Twisted leads to a hexagon, however only for +/- 45 degrees (mod 90)
        # Otherise the hexagon isn't flat: then it is a folded one. Therefore
        # draw the hexagon by the 4 triangles that are folded. Save the folds as
        # separate edges in this.twistedEs_A4 that are only drawn if the hexagon
        # isn't flat.
        twist = [[23, 22, 13], [5, 23, 13], [18, 22, 23], [17, 13, 22]]
        this.twistedEs_A4 = [23, 22, 22, 13, 13, 23]
        this.oppO3triFs = {
            trisAlt.strip_1_loose: [std],
            trisAlt.strip_I: [std],
            trisAlt.strip_II: [std],
            trisAlt.star: [std],
            trisAlt.star_1_loose: [std],
            trisAlt.alt_strip_I: [alt],
            trisAlt.alt_strip_II: [alt],
            trisAlt.alt_strip_1_loose: [alt],
            trisAlt.rot_strip_1_loose: [std],
            trisAlt.arot_strip_1_loose: [alt],
            trisAlt.rot_star_1_loose: [std],
            trisAlt.arot_star_1_loose: [alt],
            trisAlt.twist_strip_I: twist,
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
        stripI = [3, 8, 2, 8, 2, 9]
        stripII = [3, 8, 3, 9, 2, 9]
        star = [3, 8, 2, 8, 1, 8]
        star_1_loose = [2, 7, 2, 8, 1, 8]
        twist_stripI = [2, 7, 2, 21, 1, 20]
        this.triEs = {
            trisAlt.strip_1_loose: strip_1_loose,
            trisAlt.strip_I: stripI,
            trisAlt.strip_II: stripII,
            trisAlt.star: star,
            trisAlt.star_1_loose: star_1_loose,
            trisAlt.alt_strip_I: stripI,
            trisAlt.alt_strip_II: stripII,
            trisAlt.alt_strip_1_loose: strip_1_loose,
            trisAlt.twist_strip_I: twist_stripI,
        }
        strip_1_loose = [5, 14, 5, 15]
        stripI = [5, 14, 5, 15]
        stripII = [4, 15, 5, 15]
        star = [5, 14, 6, 14]
        star_1_loose = [5, 14, 6, 14]
        rot_strip = [13, 15, 5, 15]
        rot_star = [13, 15, 6, 13]
        arot_star = [13, 15, 13, 17]
        twist_stripI = {False: [1, 8, 2, 20], True: []}  # reflections included:
        this.oppTriEs = {
            trisAlt.strip_1_loose: strip_1_loose,
            trisAlt.strip_I: stripI,
            trisAlt.strip_II: stripII,
            trisAlt.star: star,
            trisAlt.star_1_loose: star_1_loose,
            trisAlt.alt_strip_I: stripI,
            trisAlt.alt_strip_II: stripII,
            trisAlt.alt_strip_1_loose: strip_1_loose,
            trisAlt.rot_strip_1_loose: rot_strip,
            trisAlt.arot_strip_1_loose: rot_strip,
            trisAlt.rot_star_1_loose: rot_star,
            trisAlt.arot_star_1_loose: arot_star,
            trisAlt.twist_strip_I: twist_stripI,
        }

        std = [1, 9, 9, 10, 10, 1]
        alt = [2, 11, 11, 12, 12, 2]
        twist = [0, 8, 8, 19, 19, 0]
        this.o3triEs = {
            trisAlt.strip_1_loose: std,
            trisAlt.strip_I: std,
            trisAlt.strip_II: std,
            trisAlt.star: std,
            trisAlt.star_1_loose: std,
            trisAlt.alt_strip_I: alt,
            trisAlt.alt_strip_II: alt,
            trisAlt.alt_strip_1_loose: alt,
            trisAlt.twist_strip_I: twist,
        }
        std = [6, 16, 16, 15, 15, 6]
        alt = [5, 18, 18, 17, 17, 5]
        twist = []
        this.oppO3triEs = {
            trisAlt.strip_1_loose: std,
            trisAlt.strip_I: std,
            trisAlt.strip_II: std,
            trisAlt.star: std,
            trisAlt.star_1_loose: std,
            trisAlt.alt_strip_I: alt,
            trisAlt.alt_strip_II: alt,
            trisAlt.alt_strip_1_loose: alt,
            trisAlt.rot_strip_1_loose: std,
            trisAlt.arot_strip_1_loose: alt,
            trisAlt.rot_star_1_loose: std,
            trisAlt.arot_star_1_loose: alt,
            trisAlt.twist_strip_I: twist,
        }

    def printTrisAngles(this):
        # TODO: fix this function. Which angles to take (ie which faces) depends
        # on the triangle alternative.
        tris = this.triFs[this.edge_alt]
        # for non 1 loose
        # for i in range(0, len(tris) - 2, 2):
        d = 2
        # for 1 loose:
        d = 1
        for i in range(2):
            norm0 = geom_3d.Triangle(
                this.base_shape.vs[tris[i][0]],
                this.base_shape.vs[tris[i][1]],
                this.base_shape.vs[tris[i][2]],
            ).normal(True)
            logging.info("norm0: {norm0}")
            norm1 = geom_3d.Triangle(
                this.base_shape.vs[tris[i + d][0]],
                this.base_shape.vs[tris[i + d][1]],
                this.base_shape.vs[tris[i + d][2]],
            ).normal(True)
            logging.info("norm1: {norm1}")
            inprod = norm0 * norm1
            logging.info(
                f"Tris angle {i}: {math.acos(inprod) * geom_3d.Rad2Deg:.6f} degrees"
            )
        logging.info("------------")


class CtrlWin(heptagons.FldHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
        heptagons.FldHeptagonCtrlWin.__init__(
            this,
            shape,
            canvas,
            3,  # maxHeigth
            [  # prePosLst
                Stringify[S_ONLY_HEPTS],
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
                Stringify[DYN_POS],
            ],
            [trisAlt],
            Stringify,
            *args,
            **kwargs,
        )

    def has_only_hepts(this):
        return (
            this.pre_pos_enum == S_ONLY_HEPTS
            and not (this.tris_fill is None)
            and not (this.tris_fill & heptagons.TWIST_BIT == heptagons.TWIST_BIT)
        )

    def has_only_o3_triangles(this):
        return (
            this.pre_pos_enum == heptagons.ONLY_XTRA_O3S
            and not (this.tris_fill is None)
            and not (this.tris_fill & heptagons.TWIST_BIT == heptagons.TWIST_BIT)
        )

    rDir = "data/Data_FldHeptA4"
    rPre = "frh-roots"

    def printFileStrMapWarning(this, filename, funcname):
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
            fold_method_str = self.filename_map_fold_method(in_data["file"])
            assert fold_method_str is not None
            tris_str = self.filename_map_tris_fill(in_data["file"])
            assert tris_str is not None
            tris_str = trisAlt.key[tris_str]
            data = {
                "set": in_data["set"],
                "7fold": heptagons.FoldMethod.get(fold_method_str),
                "tris": tris_str,
                "fold-rot": self.filename_map_fold_pos(in_data["file"]),
            }
            logging.info(f"see file {self.rDir}/{in_data['file']}")
            return data

    predefReflSpecPos = {
        S_ONLY_HEPTS: [
            {
                "file": "frh-roots-1_0_1_0-fld_w.0-strip_I.json",
                "set": [
                    2.380384930680,
                    0.693073733187,
                    -0.568746300899,
                    -0.882436236397,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0-fld_w.0-strip_I.json",
                "set": [
                    -1.886848679993,
                    -2.675843213538,
                    -3.128320557422,
                    1.954454451606,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0-fld_w.0-strip_I.json",
                "set": [
                    -1.322333216810,
                    -2.967180003002,
                    -1.183250747277,
                    1.668301536282,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0-fld_shell.0-alt_strip_II.json",
                "set": [
                    1.384557049344,
                    1.446970234245,
                    -1.316197505877,
                    -0.865444046055,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0-fld_shell.0-alt_strip_II.json",
                "set": [
                    -0.893811200268,
                    -2.124009132680,
                    -2.221957533639,
                    0.797991253652,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0-fld_shell.0-alt_strip_II.json",
                "set": [
                    -0.556102494513,
                    -2.609660225894,
                    -1.565821769393,
                    -2.603286338808,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0-fld_shell.0-alt_strip_II.json",
                "set": [
                    -0.621710474737,
                    -2.385085606668,
                    2.979725519925,
                    2.212236586768,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0-fld_shell.0-alt_strip_II.json",
                "set": [
                    -0.744610213721,
                    -2.981881518271,
                    2.772201116514,
                    -1.626936107939,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0-fld_parallel.0-shell.json",
                "set": [2.05527791079771, 0.0, 1.17877572036290, 0.93053176681969, 0.0],
            },
            {
                "file": "frh-roots-0_0_0_0-fld_triangle.0-twisted.json",
                "set": [
                    1.57625873995627,
                    0.0,
                    1.70780610035987,
                    0.69387894107559,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_0_0_0-fld_w.0-twisted.json",
                "set": [
                    -0.55652539638413,
                    2.39522124261844,
                    0.72665170889609,
                    0.82988500709760,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_0_0_0-fld_w.0-twisted.json",
                "set": [
                    -0.75211335117600,
                    2.47041152939265,
                    0.78109340649621,
                    1.45595139993016,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_0_0_0-fld_shell.0-twisted.json",
                "set": [
                    1.57829332274746,
                    -0.32640923840694,
                    0.34074243237606,
                    2.04797705220462,
                    0.78539816339745,
                ],
            },
        ],
        S_T8: [
            {
                "file": "frh-roots-0_1_0_1-fld_triangle.0-strip_I.json",
                "set": [
                    1.668804061427,
                    1.471660709431,
                    -0.787124235167,
                    0.879575685317,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1-fld_shell.0-strip_I.json",
                "set": [1.778711440973, 0.947499660437, -1.726110141329, 0.0],
            },
            {
                "file": "frh-roots-0_1_0_1-fld_shell.0-strip_I.json",
                "set": [1.778711440973, 0.947499660437, 0.458542642050, 0.0],
            },
            {
                "file": "frh-roots-0_1_0_1-fld_trapezium.0-strip_I.json",
                "set": [
                    1.603988045241,
                    1.179161796661,
                    -1.224721468276,
                    0.987593630632,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1-fld_w.0-shell_1_loose.json",
                "set": [
                    2.596914957747,
                    0.371800292039,
                    -0.991598446991,
                    0.954998112111,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1-fld_w.0-shell_1_loose.json",
                "set": [
                    -2.396628548671,
                    -2.760441424536,
                    -2.289627248660,
                    2.151908864169,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1-fld_w.0-shell_1_loose.json",
                "set": [
                    -2.396628548671,
                    -2.760441424536,
                    -2.289627248660,
                    -0.989683789421,
                ],
            },
        ],
        S_T16_S12: [
            {
                "file": "frh-roots-0_1_1_0-fld_shell.0-twisted.json",
                "set": [
                    2.28349922775437,
                    0.06277160667564,
                    -0.06286795681704,
                    2.75487753324911,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_1_1_0-fld_triangle.0-twisted.json",
                "set": [
                    2.28336552114282,
                    0.0,
                    1.13059660075713,
                    1.75383477143902,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_1_1_0-fld_triangle.0-twisted.json",
                "set": [
                    2.28336552114282,
                    0.0,
                    1.13059660075713,
                    -2.67411537632553,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_1_1_0-fld_triangle.0-twisted.json",
                "set": [
                    2.28336552114282,
                    0.0,
                    0.10036281658365,
                    2.67411537632553,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_0_1_1-fld_triangle.0-twisted.json",
                "set": [
                    1.57625873995627,
                    0.0,
                    2.13564659960344,
                    1.09359107312669,
                    0.78539816339745,
                ],
            },
        ],
        S_T16: [
            {
                "file": "frh-roots-1_0_0_0-fld_w.0-twisted.json",
                "set": [
                    0.38625024358001,
                    2.04181085346543,
                    0.53307481297736,
                    -0.02371984670375,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_0-fld_shell.0-twisted.json",
                "set": [
                    0.38635143295225,
                    2.04177274103915,
                    0.51985442041897,
                    0.02379038049852,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_1_0_0-fld_shell.0-twisted.json",
                "set": [
                    2.28349922775437,
                    0.06277160667564,
                    -0.06286795681704,
                    1.46852003907435,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_0_0_1-fld_parallel.0-twisted.json",
                "set": [
                    1.57625873995627,
                    0.0,
                    2.05411520911343,
                    0.26432165270370,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_0-fld_triangle.0-twisted.json",
                "set": [
                    1.74903011940493,
                    0.69387894107539,
                    1.01392715928449,
                    0.69387894107539,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_0-fld_triangle.0-twisted.json",
                "set": [
                    0.54693117675810,
                    2.44771371251441,
                    -0.73990761215453,
                    0.69387894107539,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_1_0_0-fld_triangle.0-twisted.json",
                "set": [
                    2.28336552114282,
                    0.0,
                    1.13059660075713,
                    0.46747727726426,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_1_0_0-fld_triangle.0-twisted.json",
                "set": [
                    2.28336552114282,
                    -0.0,
                    1.13059660075713,
                    -1.38775788215078,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_1_0_0-fld_triangle.0-twisted.json",
                "set": [
                    2.28336552114282,
                    0.0,
                    0.10036281658365,
                    1.38775788215077,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_0_0_1-fld_triangle.0-twisted.json",
                "set": [
                    1.57625873995627,
                    0.0,
                    2.13564659960344,
                    -0.19276642104807,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_0_0_1-fld_triangle.0-twisted.json",
                "set": [
                    1.57625873995627,
                    0.0,
                    2.13564659960344,
                    -2.04800158046311,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_0_0_1-fld_triangle.0-twisted.json",
                "set": [
                    1.57625873995627,
                    0.0,
                    1.13059660075713,
                    1.75383477143902,
                    0.78539816339745,
                ],
            },
        ],
        S_T24: [
            {
                "file": "frh-roots-1_1_0_0-fld_w.0-twisted.json",
                "set": [
                    1.76492506022939,
                    -0.23739205643944,
                    -0.34895078545162,
                    -0.15519364844989,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_w.0-twisted.json",
                "set": [
                    -0.79173444161549,
                    2.48583128085619,
                    -2.97499620550543,
                    0.36291871955997,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_shell.0-twisted.json",
                "set": [
                    1.76465226082310,
                    -0.23752704781790,
                    -0.43444382937558,
                    0.15892519348001,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_shell.0-twisted.json",
                "set": [
                    -0.18835951730218,
                    2.25653920053309,
                    0.20791586793685,
                    0.83498494726983,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_shell.0-twisted.json",
                "set": [
                    1.76465226082310,
                    -0.23752704781790,
                    -0.43444382937558,
                    2.01416035289505,
                    0.78539816339745,
                ],
            },
        ],
        S_T24_H4: [
            {
                "file": "frh-roots-1_1_0_0-fld_w.0-twisted.json",
                "set": [
                    2.45721938357382,
                    1.02864406950856,
                    -1.27167415256983,
                    1.13471006522803,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_w.0-twisted.json",
                "set": [
                    2.45628709627969,
                    0.20145076069264,
                    1.27330784422036,
                    -1.34814068537132,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_w.0-twisted.json",
                "set": [
                    -1.74055595544021,
                    2.89220370313053,
                    1.27640556999649,
                    0.99923157377633,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_triangle.0-twisted.json",
                "set": [
                    1.25403795794465,
                    2.44771371251441,
                    -1.31711711175728,
                    -1.38775788215077,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_triangle.0-twisted.json",
                "set": [
                    2.45613690059148,
                    0.69387894107539,
                    0.43671765968174,
                    -1.38775788215077,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_triangle.0-twisted.json",
                "set": [
                    2.45613690059148,
                    0.69387894107539,
                    -0.59351612449174,
                    1.38775788215078,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_triangle.0-twisted.json",
                "set": [
                    1.25403795794465,
                    2.44771371251441,
                    -2.34735089593076,
                    -0.46747727726426,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_shell.0-twisted.json",
                "set": [
                    2.46960924618761,
                    1.01698736209970,
                    -0.38433974199343,
                    0.86045704157206,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_shell.0-twisted.json",
                "set": [
                    2.47252905514248,
                    0.21676593171114,
                    0.45516655939558,
                    0.93763273086315,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_shell.0-twisted.json",
                "set": [
                    2.47252905514248,
                    0.21676593171114,
                    0.45516655939558,
                    -0.91760242855189,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_shell.0-twisted.json",
                "set": [
                    0.83956069972121,
                    1.86800900646576,
                    0.91933083158157,
                    -2.73340822015620,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_1_0_0-fld_shell.0-twisted.json",
                "set": [
                    0.83956069972121,
                    1.86800900646576,
                    0.91933083158157,
                    -0.87817306074117,
                    0.78539816339745,
                ],
            },
        ],
        S_T32: [
            {
                "file": "frh-roots-1_0_0_1-fld_trapezium.0-twisted.json",
                "set": [
                    0.48568807039262,
                    2.25669785825937,
                    0.06173900355777,
                    0.41753524083101,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_shell.0-twisted.json",
                "set": [
                    0.51874726388437,
                    2.25653920053309,
                    0.20791586793685,
                    -0.45137254690493,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_shell.0-twisted.json",
                "set": [
                    0.51874726388437,
                    2.25653920053309,
                    0.20791586793685,
                    -2.30660770631996,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_parallel.0-twisted.json",
                "set": [
                    0.54693117675810,
                    2.44771371251441,
                    -0.39359850340097,
                    0.26432165270381,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_parallel.0-twisted.json",
                "set": [
                    1.74903011940493,
                    0.69387894107539,
                    1.36023626803805,
                    0.26432165270370,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_triangle.0-twisted.json",
                "set": [
                    0.54693117675810,
                    2.44771371251441,
                    -0.31206711291096,
                    -0.19276642104807,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_triangle.0-twisted.json",
                "set": [
                    1.74903011940493,
                    0.69387894107539,
                    1.44176765852806,
                    -0.19276642104807,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_triangle.0-twisted.json",
                "set": [
                    1.74903011940493,
                    0.69387894107539,
                    1.44176765852806,
                    -2.04800158046311,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_triangle.0-twisted.json",
                "set": [
                    0.54693117675810,
                    2.44771371251441,
                    -0.31206711291096,
                    -2.04800158046311,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_triangle.0-twisted.json",
                "set": [
                    0.54693117675810,
                    2.44771371251441,
                    -1.31711711175728,
                    1.75383477143902,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_triangle.0-twisted.json",
                "set": [
                    1.74903011940493,
                    0.69387894107539,
                    0.43671765968174,
                    1.75383477143902,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_0_1-fld_w.0-twisted.json",
                "set": [
                    0.48540719864890,
                    2.26900223672547,
                    -0.02757800836859,
                    0.44535720008269,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1-fld_parallel.0-twisted.json",
                "set": [
                    2.28336552114282,
                    0.0,
                    1.37672964253502,
                    0.94170721928212,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1-fld_parallel.0-twisted.json",
                "set": [
                    2.28336552114282,
                    0.0,
                    1.37672964253501,
                    -2.46420708701138,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1-fld_shell.0-twisted.json",
                "set": [
                    1.84775911011892,
                    0.92575452409419,
                    -1.72327793624487,
                    2.57828590634453,
                    0.78539816339745,
                ],
            },
        ],
        S_T40: [
            {
                "file": "frh-roots-1_0_1_0-fld_w.0-twisted.json",
                "set": [
                    0.01810673840905,
                    2.17952724009918,
                    -0.07870584086126,
                    1.61757544772923,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0-fld_w.0-twisted.json",
                "set": [
                    -0.16303030453660,
                    2.24707815221230,
                    -0.03993084437920,
                    2.11938494155470,
                    0.78539816339745,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0-fld_w.0-twisted.json",
                "set": [
                    0.17474539602927,
                    2.12109878921778,
                    1.27980043291040,
                    -1.16062859887813,
                    0.78539816339745,
                ],
            },
        ],
        S_S12: [
            {
                "file": "frh-roots-0_V2_1_0-fld_w.0-shell_1_loose.json",
                "set": [2.33699202331, 0.07199688787, 0.78873100385, -1.72648574722],
            }
        ],
    }

    predefRotSpecPos = {
        S_ONLY_HEPTS: [
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_w.1-alt_strip_I-opp_alt_strip_II-pos-0.json",
                "set": [
                    0.7496252273681,
                    1.8388723684393,
                    -1.7538347714391,
                    1.4526321889049,
                    -0.1943741858469,
                    -1.753834771439,
                    -0.3966660749159,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_shell.1-alt_strip_I-opp_alt_strip_II-pos-0.json",
                "set": [
                    0.737081365300,
                    2.135543171300,
                    -0.240151262100,
                    -1.612173881200,
                    0.175482033600,
                    -2.354694778700,
                    -0.134157564200,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_mixed.1-alt_strip_I-opp_alt_strip_II-pos-0.json",
                "set": [
                    0.7465565929,
                    2.1277333577,
                    -0.2431598718,
                    -1.6050771083,
                    0.1735568552,
                    -2.4279720848,
                    0.1613334404,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_mixed.1-alt_strip_I-opp_alt_strip_II-pos-0.json",
                "set": [
                    1.0574795488,
                    1.8028664458,
                    -0.2935844284,
                    -1.5708247705,
                    0.152367402,
                    -2.3994054877,
                    1.2294173767,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_w.1-alt_strip_I-opp_alt_strip_II-pos-0.json",
                "set": [
                    1.0536253361613,
                    1.4583087103255,
                    -1.7538347714389,
                    1.5121382011463,
                    -0.1804014766055,
                    -1.7538347714391,
                    0.6519255476389,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_mixed.3-alt_strip_II-opp_strip_I-pos-0.json",
                "set": [
                    1.3302316311,
                    2.4586844387,
                    0.6982103019,
                    -1.711877148,
                    0.0606160433,
                    -0.5402910692,
                    -1.0498059828,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_w.1-shell-opp_alt_strip_II-pos-0.json",
                "set": [
                    1.274286108189,
                    2.1023807514558,
                    -1.0623578815823,
                    -0.866370345885,
                    0.2114548278112,
                    1.729065266832,
                    -0.8663703458851,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_w.1-shell-opp_alt_strip_II-pos-0.json",
                "set": [
                    -0.8597451588333,
                    -1.0617299797456,
                    -2.236200847328,
                    -0.4041945853315,
                    1.2986267346582,
                    0.8759573026118,
                    -0.4041945853315,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_shell.0-alt_strip_II-opp_alt_strip_II-pos-0.json",
                "set": [
                    -0.584447329706,
                    -2.485288015235,
                    2.540930460981,
                    2.593087704091,
                    0.385739827710,
                    -1.373557246626,
                    -2.412102564927,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_shell.0-alt_strip_II-opp_alt_strip_II.json",
                "set": [
                    -0.801847203711,
                    -2.608143090127,
                    -2.668837734722,
                    -1.252388597181,
                    -1.021040545614,
                    1.744176845223,
                    -2.460124162981,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_shell.0-alt_strip_II-opp_alt_strip_II.json",
                "set": [
                    -0.866025403784,
                    -2.222676713307,
                    -2.064570332814,
                    -0.827255867832,
                    -0.884416238250,
                    -2.064570332813,
                    1.904278188607,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_w.0-shell-opp_shell.json",
                "set": [
                    1.731178674695,
                    -0.460140302443,
                    1.753834771439,
                    -0.784585557814,
                    2.512070703819,
                    1.753834771439,
                    -2.488945590745,
                ],
            },
            {
                "file": "frh-roots-1_0_1_0_0_1_0-fld_shell.1-alt_strip_I-opp_alt_strip_II-pos-0.json",
                "set": [
                    0.327010675100,
                    1.585778378200,
                    0.563818962300,
                    1.799974476600,
                    0.190867351500,
                    2.913259018300,
                    -1.276141172400,
                ],
            },
        ],
        S_T8: [
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_shell.0-strip_II-opp_strip_II.json",
                "set": [
                    1.778711440973,
                    0.947499660437,
                    -1.726110141329,
                    0.0,
                    0.0,
                    0.458542642050,
                    0.0,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_shell.0-strip_1_loose-opp_strip_1_loose.json",
                "set": [
                    1.230780883271,
                    -0.833487854345,
                    1.222093745524,
                    1.087041924921,
                    1.964018074389,
                    1.222093745524,
                    1.087041924921,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_shell.0-strip_1_loose-opp_strip_1_loose.json",
                "set": [
                    0.997749181426,
                    -0.792857842956,
                    1.100626985898,
                    2.388598519690,
                    1.598141634206,
                    1.100626985898,
                    2.388598519690,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_w.0-strip_1_loose-opp_alt_strip_1_loose.json",
                "set": [
                    1.322002234160,
                    -0.777358422835,
                    1.753834771439,
                    -0.835355509883,
                    2.211531833297,
                    1.753834771439,
                    -0.835355509883,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_w.0-strip_1_loose-opp_alt_strip_1_loose.json",
                "set": [
                    1.601135681483,
                    0.889170493616,
                    -1.753834771439,
                    -0.498916362774,
                    0.0,
                    -1.753834771439,
                    -0.498916362774,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_shell.0-shell_1_loose-opp_shell_1_loose.json",
                "set": [
                    1.901507063757,
                    -0.303461611612,
                    0.314885093380,
                    0.854512058189,
                    -1.863748016803,
                    0.314885093380,
                    0.854512058189,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_w.0-shell_1_loose-opp_strip_1_loose.json",
                "set": [
                    1.8760237803,
                    0.3350392511,
                    -0.3081782476,
                    -2.4596022011,
                    -0.9148092939,
                    -2.7644862741,
                    2.2836251856,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_w.0-shell_1_loose-opp_strip_1_loose.json",
                "set": [
                    1.8856022075,
                    -0.3312813885,
                    0.1967117215,
                    2.9033277173,
                    -1.7112567738,
                    0.6941604482,
                    1.8113290139,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_w.0-shell_1_loose-opp_shell_1_loose.json",
                "set": [
                    2.596914957747,
                    0.371800292039,
                    -0.991598446991,
                    0.0,
                    0.0,
                    -0.991598446991,
                    1.909996224222,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_shell.1-alt_strip_II-opp_alt_strip_II-pos-0.json",
                "set": [
                    1.5500873208,
                    1.144029234,
                    0.4447621435,
                    1.3269914523,
                    0.0215214401,
                    -0.5457871759,
                    -1.066936577,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_shell.1-alt_strip_II-opp_alt_strip_II-pos-0.json",
                "set": [
                    1.728727324,
                    0.590129541,
                    0.7371091452,
                    2.5131975524,
                    -0.116839474,
                    0.0628633939,
                    0.1549096005,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_w.1-strip_I-opp_strip_I-pos-0.json",
                "set": [
                    1.621041509300,
                    1.609345876500,
                    0.604784142600,
                    -0.695028787700,
                    -0.080524980800,
                    -1.029260922700,
                    1.337815569200,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_w.1-strip_I-opp_strip_I-pos-0.json",
                "set": [
                    1.551230551100,
                    1.702711045100,
                    -1.197490012000,
                    -0.813025509500,
                    -0.095839633800,
                    1.277914181300,
                    -1.866148811200,
                ],
            },
            {
                "file": "frh-roots-0_1_0_1_1_0_1-fld_w.2-shell-opp_strip_I-pos-0.json",
                "set": [
                    0.762030869100,
                    2.474787916100,
                    -1.753834771600,
                    0.561331842500,
                    0.078085062900,
                    -1.753834771300,
                    0.561331841900,
                ],
            },
        ],
    }


class Scene(geom_3d.Scene):
    def __init__(this, parent, canvas):
        geom_3d.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
