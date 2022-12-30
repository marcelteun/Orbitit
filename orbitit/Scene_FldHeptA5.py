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

TITLE = 'Polyhedra with Folded Regular Heptagons and Icosahedral Symmetry'

trisAlt = heptagons.TrisAlt()
trisAlt.base_key = {
    trisAlt.refl_1:    True,
    trisAlt.refl_2:    True,
    trisAlt.crossed_2: True
}

TA_1 = heptagons.define_tris_alt(
    'TA_1',
    [
        heptagons.TrisAltBase.refl_1,
        heptagons.TrisAltBase.refl_2,
        heptagons.TrisAltBase.crossed_2,
        (heptagons.TrisAltBase.strip_I, heptagons.TrisAltBase.strip_I),
        (heptagons.TrisAltBase.strip_I, heptagons.TrisAltBase.strip_II),
        (heptagons.TrisAltBase.strip_I, heptagons.TrisAltBase.star),
        (heptagons.TrisAltBase.strip_I, heptagons.TrisAltBase.star_1_loose),
        (heptagons.TrisAltBase.strip_I, heptagons.TrisAltBase.strip_1_loose),

        (heptagons.TrisAltBase.strip_II, heptagons.TrisAltBase.strip_I),
        (heptagons.TrisAltBase.strip_II, heptagons.TrisAltBase.strip_II),
        (heptagons.TrisAltBase.strip_II, heptagons.TrisAltBase.star),
        (heptagons.TrisAltBase.strip_II, heptagons.TrisAltBase.star_1_loose),
        (heptagons.TrisAltBase.strip_II, heptagons.TrisAltBase.strip_1_loose),

        (heptagons.TrisAltBase.star, heptagons.TrisAltBase.strip_I),
        (heptagons.TrisAltBase.star, heptagons.TrisAltBase.strip_II),
        (heptagons.TrisAltBase.star, heptagons.TrisAltBase.star),
        (heptagons.TrisAltBase.star, heptagons.TrisAltBase.star_1_loose),
        (heptagons.TrisAltBase.star, heptagons.TrisAltBase.strip_1_loose)
    ]
)
trisAlts = [
    trisAlt,
    TA_1()
]

counter = heptagons.TrisCounter()

DYN_POS = heptagons.DYN_POS
OPEN_FILE = heptagons.OPEN_FILE
ONLY_HEPTS = heptagons.ONLY_HEPTS
ALL_EQ_TRIS = counter.get_next_id()
NO_O3_TRIS = counter.get_next_id()
T20_P12 = counter.get_next_id()
T60_P12 = counter.get_next_id()
T140_P12 = counter.get_next_id()
T200 = counter.get_next_id()

Stringify = {
    DYN_POS: 'Enable Sliders',
    ONLY_HEPTS: 'Just Heptagons',
    ALL_EQ_TRIS: 'All 80 Triangles Equilateral',
    NO_O3_TRIS: '48 Triangles',
    T20_P12: '20 Triangles and 12 Pentagons',
    T60_P12: '60 Triangles and 12 Pentagons',
    T140_P12: '140 Triangles and 12 Pentagons',
    T200: '200 Triangles',
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
            heptColPerIsom.append(useRgbCols[i])
            break;

class Shape(heptagons.FldHeptagonShape):
    def __init__(this, *args, **kwargs):
        heptagonsShape = geom_3d.SymmetricShape(
            vs=[],
            fs=[],
            isometries=isomA5,
            name='FoldedHeptagonsA5',
            regen_edges=False
        )
        xtraTrisShape = geom_3d.SymmetricShapeSplitCols(
            vs=[],
            fs=[],
            isometries=isomA5,
            name='xtraTrisA5',
            regen_edges=False
        )
        trisO3Shape = geom_3d.OrbitShape(
            vs=[],
            fs=[],
            final_sym=isomA5,
            stab_sym=isomO3,
            colors=[rgb.cyan[:]],
            name='o3TrisA5',
            regen_edges=False
        )
        trisO5Shape = geom_3d.OrbitShape(
            vs=[],
            fs=[],
            final_sym=isomA5,
            stab_sym=isomO5,
            colors=[rgb.cyan[:]],
            name='o5PentasA5',
            regen_edges=False
        )
        heptagons.FldHeptagonShape.__init__(this,
            [heptagonsShape, xtraTrisShape, trisO3Shape, trisO5Shape],
            name='FoldedRegHeptA5xI'
        )
        this.heptagonsShape = heptagonsShape
        this.xtraTrisShape = xtraTrisShape
        this.trisO3Shape = trisO3Shape
        this.trisO5Shape = trisO5Shape
        this.pos_angle_min = -math.pi/2
        this.pos_angle_max = math.pi/2
        this.height = 2.7
        this.dihedral_angle = geom_3d.Deg2Rad * 119
        this.initArrs()
        this.set_tri_fill_pos(0)
        this.set_edge_alt(trisAlt.strip_II, trisAlt.strip_II)
        this.set_vertices()

    def get_status_str(this):
        s = heptagons.FldHeptagonShape.get_status_str(this)
        if this.update_shape:
            this.set_vertices()
        vs = this.baseVs
        if this.has_reflections:
            es = this.triEs[this.edge_alt]
            aLen = '%2.2f' % Vlen(vs[es[0]], vs[es[1]])
            bLen = '%2.2f' % Vlen(vs[es[2]], vs[es[3]])
            cLen = '%2.2f' % Vlen(vs[es[4]], vs[es[5]])
            dLen = '%2.2f' % Vlen(vs[es[6]], vs[es[7]])
        else:
            es = this.triEs[this.edge_alt]
            aLen = '%2.2f' % Vlen(vs[es[0]], vs[es[1]])
            bLen = '%2.2f' % Vlen(vs[es[2]], vs[es[3]])
            cLen = '%2.2f' % Vlen(vs[es[4]], vs[es[5]])
            es = this.o5triEs[this.edge_alt]
            dLen = '%2.2f' % Vlen(vs[es[0]], vs[es[1]])

        if this.has_reflections:
            s = 'T = %02.2f; |a|: %s, |b|: %s, |c|: %s, |d|: %s' % (
                    this.height, aLen, bLen, cLen, dLen
                )
        else:
            es = this.oppTriEs[this.opposite_edge_alt]
            opp_bLen = '%2.2f' % Vlen(vs[es[0]], vs[es[1]])
            opp_cLen = '%2.2f' % Vlen(vs[es[2]], vs[es[3]])
            es = this.o3triEs[this.opposite_edge_alt]
            if this.opposite_edge_alt != trisAlt.refl_1:
                opp_dLen = '%2.2f' % Vlen(vs[es[0]], vs[es[1]])
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

    def set_tri_fill_pos(this, i):
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

    def set_edge_alt(this, alt = None, oppositeAlt = None):
        heptagons.FldHeptagonShape.set_edge_alt(this, alt, oppositeAlt)

    def set_vertices(this):
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

        this.position_heptagon()
        vs = this.heptagon.vs[:]
        vs.append(Vec([-vs[5][0], -vs[5][1], vs[5][2]]))        # vs[7]
        vs.append(Vec([-vs[2][0], -vs[2][1], vs[2][2]]))        # vs[8]
        vs.append(o3fld * vs[0])                                # vs[9]
        vs.append(o3fld * vs[-1])                               # vs[10]
        vs.append(o5fld * vs[0])                                # vs[11]
        vs.append(o5fld * vs[-1])                               # vs[12]
        vs.append(o5fld * vs[-1])                               # vs[13]
        vs.append(o5fld * vs[-1])                               # vs[14]
        vs.append(Vec([-vs[11][0], -vs[11][1], vs[11][2]]))     # vs[15]
        vs.append(o3fld * vs[6])                                # vs[16]
        vs.append(o3fld * vs[-1])                               # vs[17]
        vs.append(o5fld * vs[1])                                # vs[18]
        vs.append(o5fld * vs[-1])                               # vs[19]
        vs.append(o5fld * vs[-1])                               # vs[20]
        vs.append(o5fld * vs[-1])                               # vs[21]
        vs.append(o3fld * vs[5])                                # vs[22]
        vs.append(o3fld * vs[-1])                               # vs[23]
        vs.append(o5fld * vs[2])                                # vs[24]
        vs.append(o5fld * vs[-1])                               # vs[25]
        vs.append(o5fld * vs[-1])                               # vs[26]
        vs.append(o5fld * vs[-1])                               # vs[27]
        vs.append(o3fld * vs[4])                                # vs[28]
        vs.append(o3fld * vs[-1])                               # vs[29]
        vs.append(o5fld * vs[3])                                # vs[30]
        vs.append(o5fld * vs[-1])                               # vs[31]
        vs.append(o5fld * vs[-1])                               # vs[32]
        vs.append(o5fld * vs[-1])                               # vs[33]
        vs.append(o3fld * vs[8])                                # vs[34]
        vs.append(o3fld * vs[-1])                               # vs[35]
        vs.append(o5fld * vs[7])                                # vs[36]
        vs.append(o5fld * vs[-1])                               # vs[37]
        vs.append(o5fld * vs[-1])                               # vs[38]
        vs.append(o5fld * vs[-1])                               # vs[39]
        vs.append(o5fld * vs[6])                                # vs[40]
        vs.append(o5fld * vs[-1])                               # vs[41]
        vs.append(o5fld * vs[-1])                               # vs[42]
        vs.append(o5fld * vs[-1])                               # vs[43]
        vs.append((vs[0] + vs[11] + vs[12] + vs[13] + vs[14])/5)# vs[44]
        # TODO: if adding more vs, rm above if or use predefined indices
        this.baseVs = vs
        es = []
        fs = []
        fs.extend(this.heptagon.fs) # use extend to copy the list to fs
        es.extend(this.heptagon.es) # use extend to copy the list to fs
        this.heptagonsShape.base_shape.vertex_props = {'vs': vs}
        this.heptagonsShape.base_shape.es = es
        # TODO CHk: comment out this and nvidia driver crashes:...
        this.heptagonsShape.base_fs_props = {'fs': fs}
        this.heptagonsShape.shape_colors = heptColPerIsom
        theShapes = [this.heptagonsShape]
        if this.add_extra_faces:
            assert this.edge_alt in this.o5triFs, \
                "this triangle fill isn't implemented for A5"
            fs = this.o5triFs[this.edge_alt][:]
            es = this.o5triEs[this.edge_alt][:]
            this.trisO5Shape.base_shape.vertex_props = {'vs': vs}
            this.trisO5Shape.base_shape.es = es
            this.trisO5Shape.base_fs_props = {'fs': fs}
            theShapes.append(this.trisO5Shape)
            es = this.o3triEs[this.opposite_edge_alt][:]
            fs = this.o3triFs[this.opposite_edge_alt][:]
            this.trisO3Shape.base_shape.vertex_props = {'vs': vs}
            this.trisO3Shape.base_shape.es = es
            this.trisO3Shape.base_fs_props = {'fs': fs}
            theShapes.append(this.trisO3Shape)
            if (not this.all_regular_faces):
                # when you use the rot alternative the rot is leading for
                # choosing the colours.
                if this.triangleFillPosition == 0:
                    if this.opposite_edge_alt & heptagons.ROT_BIT:
                        eAlt = this.opposite_edge_alt
                    else:
                        eAlt = this.edge_alt
                    colIds = this.triColIds[eAlt]
                else:
                    colIds = this.triColIds[this.edge_alt][:3]
                    colIds.extend(this.triColIds[this.opposite_edge_alt][3:])
                fs = this.triFs[this.edge_alt][:]
                fs.extend(this.oppTriFs[this.opposite_edge_alt])
                es = this.triEs[this.edge_alt][:]
                es.extend(this.oppTriEs[this.opposite_edge_alt])
                this.xtraTrisShape.base_shape.vertex_props = {'vs': vs}
                this.xtraTrisShape.base_shape.es = es
                this.xtraTrisShape.base_fs_props = {
                    'fs': fs,
                    'colors': ([rgb.darkRed[:], rgb.yellow[:], rgb.magenta[:]], colIds),
                }
                theShapes.append(this.xtraTrisShape)
        for isom_shape in theShapes:
            isom_shape.show_base_only = not this.apply_symmetries
        this.setShapes(theShapes)
        #rad = this.getRadii()
        this.update_shape = False

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

class CtrlWin(heptagons.FldHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
        heptagons.FldHeptagonCtrlWin.__init__(this,
            shape, canvas,
            12, # maxHeigth
            [ # prePosLst
                Stringify[ONLY_HEPTS],
                Stringify[DYN_POS],
                Stringify[T20_P12],
                Stringify[T60_P12],
                Stringify[T140_P12],
                Stringify[T200],
            ],
            trisAlts,
            Stringify,
            *args, **kwargs
        )

    def has_only_hepts(self):
        return self.pre_pos_enum == ONLY_HEPTS and not (
                self.tris_fill is None
            ) and not (
                self.tris_fill == trisAlt.refl_1 or
                self.tris_fill == trisAlt.refl_2 or
                self.tris_fill == trisAlt.crossed_2
            )

    def has_only_o3_triangles(self):
        return self.pre_pos_enum == heptagons.ONLY_XTRA_O3S and not (
                self.tris_fill is None
            ) and not (
                self.tris_fill == trisAlt.refl_1 or
                self.tris_fill == trisAlt.refl_2 or
                self.tris_fill == trisAlt.crossed_2
            )

    rDir = 'data/Data_FldHeptA5'
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
            data = psp[self.pre_pos_enum][self.special_pos_idx]
            if 'file' in data:
                logging.info(f"see file {self.rDir}/{data['file']}")
            return data

    predefReflSpecPos = {
        ONLY_HEPTS: [
            {
                'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_1-pos-0.json',
                'set': [2.59804095112, 0.07208941199, -0.07223544999, 2.53866531680],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.refl_1,
            },{
                'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_2-pos-0.json',
                'set': [3.54099634761, 0.46203434348, -0.50537193698, 2.35569911915, 1.57079632679],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.refl_2,
            },{
                'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_1-pos-0.json',
                'set': [2.59967616789, 0.00000000000, 0.11360610699, 2.44771371251],
                '7fold': heptagons.FoldMethod.TRIANGLE,
                'tris': trisAlt.refl_1,
            },{
                'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_1-pos-0.json',
                'set': [2.59967616789, -0.00000000000, 2.29825889037, 0.69387894108],
                '7fold': heptagons.FoldMethod.TRIANGLE,
                'tris': trisAlt.refl_1,
            },{
                'file': 'frh-roots-0_0_0_0-fld_w.0-refl_1-pos-0.json',
                'set': [0.78019870723, 2.64930187805, 0.54062307364, 0.00913464936],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.refl_1,
            },{
                'file': 'frh-roots-0_0_0_0-fld_w.0-refl_1-pos-0.json',
                'set': [2.56440119971, 0.06605029302, -0.42550124895, 0.64274301662],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.refl_1,
            },{
                'file': 'frh-roots-0_0_0_0-fld_w.0-refl_2-pos-0.json',
                'set': [3.41692468489, 0.40788151929, -0.96765917562, 0.84720346804, 1.57079632679],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.refl_2,
            },{
                'file': 'frh-roots-0_0_0_0-fld_w.0-refl_2-pos-0.json',
                'set': [-0.78796389438, 2.77826685391, 1.16636078799, 2.12574368211, 1.57079632679],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.refl_2,
            }
        ],
        T60_P12: [
            {
                'file': 'frh-roots-0_0_0_1-fld_w.0-refl_2-pos-0.json',
                'set': [1.596941118660, 2.593080381370, 0.403913171960, 0.449605194880, 1.5707963268
                ],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.refl_2,
            },{
                'file': 'frh-roots-0_0_0_1-fld_shell.0-refl_2-pos-0.json',
                'set': [1.655881786380, 2.578935099880, 0.646433762790, -0.461827521280, 1.5707963268
                ],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.refl_2,
            },{
                'file': 'frh-roots-0_0_0_1-fld_shell.0-refl_2-pos-0.json',
                'set': [1.655881786380, 2.578935099880, 0.646433762790, -2.317062680690, 1.5707963268
                ],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.refl_2,
            },{
                'file': 'frh-roots-0_0_0_1-fld_shell.0-refl_2-pos-0.json',
                'set': [3.722764049900, -0.024061600030, 0.024067017100, 1.458692444820, 1.5707963268
                ],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.refl_2,
            }
        ],
    }
    predefRotSpecPos = {
        ONLY_HEPTS: [
            {
                'file': 'frh-roots-1_0_1_0_0_1_0-fld_w.0-shell-opp_strip_II-pos-1.json',
                'set': [2.190643133767, 0.0, -2.750194494870, 1.320518652645, 0.080811779365, 1.327501379252, 1.320518652644],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.shell_strip_II,
                'tris-pos': 1
            },{
                'file': "frh-roots-1_0_1_0_0_1_0-fld_w.1-strip_II-opp_shell-pos-1.json",
                'set': [2.2398383815253, 1.538134037316, -1.753834771439, 2.220230723671, 0.6077158322698, -1.7538347714391, -0.1073726559505],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 1
            },{
                'file': "frh-roots-1_0_1_0_0_1_0-fld_w.1-strip_II-opp_shell-pos-1.json",
                'set': [2.5964060652451, 0.6303582297009, -1.7538347714387, 2.8348162453136, 0.3892552426313, -1.7538347714394, 1.4996710788234],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 1
            },{
                'file': "frh-roots-1_0_1_0_0_1_0-fld_w.1-strip_II-opp_shell-pos-1.json",
                'set': [2.5964060652451, 0.6303582297009, -1.7538347714387, 2.8348162453136, 0.3892552426313, -1.7538347714394, 1.4996710788234],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 1
            },{
                'file': "frh-roots-1_0_1_0_0_1_0-fld_w.1-strip_II-opp_shell-pos-1.json",
                'set': [1.5146302263609, -2.3128908096943, -1.753834771439, -1.8766503426196, -0.4739245692867, -1.753834771439, 1.9319622451753],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 1
            },{
                'file': "frh-roots-1_0_1_0_0_1_0-fld_w.1-strip_II-opp_shell-pos-1.json",
                'set': [1.5146302263604, -2.3128908096942, 1.7538347714387, 1.1330038160007, -0.4739245692867, 1.7538347714397, -1.3415689033837],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 1
            }
        ],
        T20_P12: [
            {
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_w.0-strip_II-opp_shell-pos-1.json',
                'set': [3.9285156166, 0.4481183997, -1.1824397375, -0.6742498494, 0.7406212166, 1.0271943946, -2.9154857351],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 0
            }, {
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_w.0-strip_II-opp_shell-pos-1.json',
                'set': [3.7946099505, 0.4342295954, -1.3000303091, -0.6713165943, 0.6792547664, 1.1292221703, -3.1339879423],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 0
            }, {
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_w.0-strip_II-opp_shell-pos-1.json',
                'set': [3.2135654837, -0.4036768949, 1.6871643575, 0.8066757021, -2.7177042329, -1.8939034612, -2.3546442874],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 0
            }, {
                'file': 'frh-roots-0_1_0_1_1_0_1-fld_w.0-strip_II-opp_shell-pos-1.json',
                'set': [2.7907235251, -0.3606585776, 1.2610787379, 0.2334086784, -3.0920488367, -1.8938496708, 2.5205702708],
                '7fold': heptagons.FoldMethod.W,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1,
                'fold-rot': 0
            }
        ],
        T60_P12: [
            {
                'file': 'frh-roots-0_1_0_1_1_1_0-fld_shell.0-strip_II-opp_shell-pos-1.json',
                'set': [3.567397972268, 0.577608713844, -0.805085622072, -1.564973557413, 0.802103304585, 0.794585079662, 2.557585428357
                ],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.strip_II_shell,
                'tris-pos': 1
            }
        ],
        T200: [
            {
                'file': 'frh-roots-1_0_1_0_1_1_1-fld_shell.0-shell-opp_strip_II-pos-1.json',
                'set': [4.142695742002, 1.124949218194, 0.821407938281, 3.141592653589, 1.570796326795, -0.566349943870, 0.910396047071
                ],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.shell_strip_II,
                'tris-pos': 1
            },{
                'file': 'frh-roots-1_0_1_0_1_1_1-fld_shell.0-shell-opp_strip_II-pos-1.json',
                'set': [4.142695742003, 1.124949218194, -1.954107826020, 1.286357494175, 1.570796326795, -0.566349943869, -0.944839112344
                ],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.shell_strip_II,
                'tris-pos': 1
            },{
                'file': 'frh-roots-1_0_1_0_1_1_1-fld_shell.0-shell-opp_strip_II-pos-1.json',
                'set': [2.504073272511, 1.943327879806, 2.108843675970, -1.286357494175, 1.570796326795, 0.721085793819, -0.509380996152
                ],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.shell_strip_II,
                'tris-pos': 1
            },
        ],
        T140_P12: [
            {
                'file': 'frh-roots-0_1_0_1_1_1_1-fld_shell.0-strip_II-opp_strip_II-pos-1.json',
                'set': [4.389693800678, 1.613882084912, 0.259202620907, -0.178125410980, 1.279825824143, -0.703784937696, 1.377596588777
                ],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.strip_II_strip_II,
                'tris-pos': 1
            },{
                'file': 'frh-roots-0_1_0_1_1_1_1-fld_shell.0-strip_II-opp_strip_II-pos-1.json',
                'set': [4.170755846609, 0.821420235107, 0.100700797086, -2.149394471077, 1.035800183137, 0.974085339636, 1.554356155170
                ],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.strip_II_strip_II,
                'tris-pos': 1
            },{
                'file': 'frh-roots-0_1_0_1_1_1_1-fld_shell.0-strip_II-opp_strip_II-pos-1.json',
                'set': [4.005419181303, 0.470909001839, -1.360105032126, 0.426263518595, 0.786838873976, 1.479755007849, -0.977504044321
                ],
                '7fold': heptagons.FoldMethod.SHELL,
                'tris': trisAlt.strip_II_strip_II,
                'tris-pos': 1
            }
        ],
    }

class Scene(geom_3d.Scene):
    def __init__(self, parent, canvas):
        geom_3d.Scene.__init__(self, Shape, CtrlWin, parent, canvas)
