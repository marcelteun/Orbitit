#!/usr/bin/env python
#
# Copyright (C) 2008 Marcel Tunnissen
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
#-----------------------------------------------------------------
# $Log$
#
import wx
import math
import re
from OpenGL.GL import glColor, glEnable, glDisable, glBlendFunc
from OpenGL.GL import GL_CULL_FACE, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA

from orbitit import Geom3D, geomtypes, rgb
from orbitit.geomtypes import Rot3 as Rot
from orbitit.geomtypes import Vec3 as Vec

V3 = math.sqrt(3)

h         = math.sin(  math.pi / 7)
RhoH      = math.sin(2*math.pi / 7)
SigmaH    = math.sin(3*math.pi / 7)
Rho       = RhoH / h
Sigma     = SigmaH / h
R         = 0.5 / h
H         = (1 + Sigma + Rho)*h

only_hepts      = -1
dyn_pos         = -2
open_file       = -3
only_xtra_o3s   = -4
all_eq_tris     = -5
no_o3_tris      = -6

tris_fill_base  = 0

alt_bit = 8
loose_bit = 16
rot_bit   = 32
twist_bit = 64
tris_offset = 128

class Tris_counter():
    def __init__(this):
        this.reset(tris_offset)

    def reset(this, v):
        this.counter = v;

    def pp(this):
        i = this.counter
        this.counter += 1
        return i

class TrisAlt_base(object):
    # Note nrs should be different from below
    refl_1             = 0
    strip_I            = 1
    strip_II           = 2
    star               = 3
    refl_2             = 4
    crossed_2          = 5
    strip_1_loose      = strip_I  | loose_bit
    star_1_loose       = star     | loose_bit
    alt_strip_I        = strip_I              | alt_bit
    alt_strip_II       = strip_II             | alt_bit
    alt_strip_1_loose  = strip_I  | loose_bit | alt_bit
    rot_strip_1_loose  = strip_I  | loose_bit           | rot_bit
    arot_strip_1_loose = strip_I  | loose_bit | alt_bit | rot_bit
    rot_star_1_loose   = star     | loose_bit           | rot_bit
    arot_star_1_loose  = star     | loose_bit | alt_bit | rot_bit
    rot_strip_I        = strip_I  |                       rot_bit
    rot_star           = star     |                       rot_bit
    arot_strip_I       = strip_I              | alt_bit | rot_bit
    arot_star          = star                 | alt_bit | rot_bit
    # TODO: this is a new position really
    # TODO: rename to refl2 for S4A4
    # TODO: rename to some 1 - loose variant for A4
    twist_strip_I      = strip_I                                  | twist_bit

    stringify = {
        refl_1:                 'refl 1',
        refl_2:                 'refl 2',
        crossed_2:              'crossed',
        strip_1_loose:          'strip 1 Loose',
        strip_I:                'strip I',
        strip_II:               'strip II',
        star:                   'shell',
        star_1_loose:           'shell 1 loose',
        alt_strip_I:            'alt. strip I',
        alt_strip_II:           'alt. strip II',
        alt_strip_1_loose:      'alt. strip 1 loose',

        twist_strip_I:          'twisted',

        rot_strip_1_loose:      'rot. strip 1 loose',
        rot_star_1_loose:       'rot. shell 1 loose',
        arot_strip_1_loose:     'alt. rot. strip 1 loose',
        arot_star_1_loose:      'alt. rot. shell 1 loose',
        rot_strip_I:            'rot. strip I',
        rot_star:               'rot. shell',
        arot_strip_I:           'alt. rot. strip I',
        arot_star:              'alt. rot. shell',
    }

    class_key = {
        'refl_1':            refl_1,
        'refl_2':            refl_2,
        'crossed_2':         crossed_2,
        'strip_I':           strip_I,
        'strip_II':          strip_II,
        'star':              star,
        'strip_1_loose':     strip_1_loose,
        'star_1_loose':      star_1_loose,
        'alt_strip_I':       alt_strip_I,
        'alt_strip_II':      alt_strip_II,
        'alt_strip_1_loose': alt_strip_1_loose,

        'twist_strip_I':     twist_strip_I,

        'rot_strip_1_loose':  rot_strip_1_loose,
        'rot_star_1_loose':   rot_star_1_loose,
        'arot_strip_1_loose': arot_strip_1_loose,
        'arot_star_1_loose':  arot_star_1_loose,
        'rot_strip_I':        rot_strip_I,
        'rot_star':           rot_star,
        'arot_strip_I':       arot_strip_I,
        'arot_star':          arot_star
    }

    key = {
        stringify[refl_1]:            refl_1,
        stringify[refl_2]:            refl_2,
        stringify[crossed_2]:         crossed_2,
        stringify[strip_I]:           strip_I,
        stringify[strip_II]:          strip_II,
        stringify[star]:              star,
        stringify[strip_1_loose]:     strip_1_loose,
        stringify[star_1_loose]:      star_1_loose,
        stringify[alt_strip_I]:       alt_strip_I,
        stringify[alt_strip_II]:      alt_strip_II,
        stringify[alt_strip_1_loose]: alt_strip_1_loose,

        stringify[twist_strip_I]:     twist_strip_I,

        stringify[rot_strip_1_loose]:  rot_strip_1_loose,
        stringify[rot_star_1_loose]:   rot_star_1_loose,
        stringify[arot_strip_1_loose]: arot_strip_1_loose,
        stringify[arot_star_1_loose]:  arot_star_1_loose,
        stringify[rot_strip_I]:        rot_strip_I,
        stringify[rot_star]:           rot_star,
        stringify[arot_strip_I]:       arot_strip_I,
        stringify[arot_star]:          arot_star,
    }

    def isBaseKey(this, k):
        try:
            return this.baseKey[k]
        except KeyError:
            return False

    def toFileStr(this, tId = None, tStr = None):
        assert(tId is not None or tStr is not None)
        if (tId is None):
            tId = this.key[tStr]
        if not isinstance(tId, int):
            tStr0 = this.stringify[tId[0]]
            tStr1 = this.stringify[tId[1]]
            tStr = "%s-opp_%s" % (tStr0, tStr1)
        elif tStr is None:
            tStr = this.stringify[tId]

        t = '_'.join(tStr.split()).lower().replace('ernative', '')
        t = t.replace('_ii', '_II')
        t = t.replace('_i', '_I')
        t = t.replace('alt.', 'alt')
        t = t.replace('rot.', 'rot')
        #print 'DBP map(%s) ==> %s' % (this.stringify[trisFillId], t)
        return t

    baseKey = {}
    def __init__(this):
        # TODO? Note that only s that aren't primitives (isinstance(x, int))
        # should be added here.
        this.choiceList = [s for s in this.stringify.values()]
        this.mapKeyOnFileStr = {}
        this.mapStrOnFileStr = {}
        this.mapFileStrOnStr = {}
        this.mapFileStrOnKey = {}
        for (tStr, tId) in this.key.items():
            fileStr = this.toFileStr(tStr = tStr)
            this.mapKeyOnFileStr[tId]     = fileStr
            this.mapStrOnFileStr[tStr]    = fileStr
            this.mapFileStrOnStr[fileStr] = tStr
            this.mapFileStrOnKey[fileStr] = tId

def toTrisAltKeyStr(tId = None, tStr = None):
    assert(tId is not None or tStr is not None)
    if (tId is None):
        tId = TrisAlt_base.key[tStr]
    if not isinstance(tId, int):
        if tId[0] & loose_bit and tId[1] & loose_bit:
            tStr = '%s_1loose_%s' % (
                        TrisAlt_base.stringify[tId[0] & ~loose_bit],
                        TrisAlt_base.stringify[tId[1] & ~loose_bit])
        elif tId[0] & loose_bit:
            tStr = '%s__%s' % (
                        TrisAlt_base.stringify[tId[0]],
                        TrisAlt_base.stringify[tId[1]])
        # TODO: remove share under new position
        elif (tId[0] == TrisAlt_base.twist_strip_I and
            tId[1] == TrisAlt_base.twist_strip_I
        ):
            tStr = 'twist_strip_I_strip_I'
        else:
            tStr = '%s_%s' % (
                        TrisAlt_base.stringify[tId[0]],
                        TrisAlt_base.stringify[tId[1]])
    elif tStr is None:
        tStr = TrisAlt_base.stringify[tId]
    t = "_".join(tStr.split())
    t = t.replace('_ii', '_II')
    t = t.replace('_i', '_I')
    t = t.replace('alt._rot.', 'arot')
    t = t.replace('rot.', 'rot')
    t = t.replace('alt.', 'alt')
    return t

class Meta_TrisAlt(type):
    def __init__(this, classname, bases, classdict):
        type.__init__(this, classname, bases, classdict)

def Def_TrisAlt(name, tris_keys):
    class_dict = {
        'mixed':     False,
        'stringify': {},
        'key':       {},
        'baseKey':   {}
    }
    # Always add all primitives:
    for (k, s) in TrisAlt_base.stringify.items():
        class_dict['stringify'][k] = s
        class_dict['key'][s] = k
        class_dict[toTrisAltKeyStr(k)] = k
    for k in tris_keys:
        if isinstance(k, int):
            class_dict['baseKey'][k] = True
        else:
            # must be a tuple of 2
            assert len(k) == 2, 'Exptected 2 tuple, got: %s.' % k
            if k[0] & loose_bit and k[1] & loose_bit:
                s = '%s - 1 loose - %s' % (
                            TrisAlt_base.stringify[k[0] & ~loose_bit],
                            TrisAlt_base.stringify[k[1] & ~loose_bit])
            elif (k[0] == TrisAlt_base.twist_strip_I and
                k[1] == TrisAlt_base.twist_strip_I
            ):
                s = 'strip I - twisted - strip I'
            else:
                s = '%s - %s' % (
                            TrisAlt_base.stringify[k[0]],
                            TrisAlt_base.stringify[k[1]])
            class_dict['stringify'][k] = s
            class_dict['key'][s] = k
            class_dict[toTrisAltKeyStr(k)] = k
    return Meta_TrisAlt(name, (TrisAlt_base,), class_dict)

TrisAlt = Def_TrisAlt('TrisAlt', [
            TrisAlt_base.refl_1,
            TrisAlt_base.refl_2,
            TrisAlt_base.crossed_2,
            TrisAlt_base.strip_1_loose,
            TrisAlt_base.strip_I,
            TrisAlt_base.strip_II,
            TrisAlt_base.star,
            TrisAlt_base.star_1_loose,
            TrisAlt_base.alt_strip_I,
            TrisAlt_base.alt_strip_II,
            TrisAlt_base.alt_strip_1_loose,

            TrisAlt_base.twist_strip_I,

            TrisAlt_base.rot_strip_1_loose,
            TrisAlt_base.rot_star_1_loose,
            TrisAlt_base.arot_strip_1_loose,
            TrisAlt_base.arot_star_1_loose,

            (TrisAlt_base.strip_I, TrisAlt_base.strip_I),
            (TrisAlt_base.strip_I, TrisAlt_base.strip_II),
            (TrisAlt_base.strip_I, TrisAlt_base.star),
            (TrisAlt_base.strip_I, TrisAlt_base.alt_strip_I),
            (TrisAlt_base.strip_I, TrisAlt_base.alt_strip_II),

            (TrisAlt_base.strip_II, TrisAlt_base.strip_I),
            (TrisAlt_base.strip_II, TrisAlt_base.strip_II),
            (TrisAlt_base.strip_II, TrisAlt_base.star),
            (TrisAlt_base.strip_II, TrisAlt_base.alt_strip_I),
            (TrisAlt_base.strip_II, TrisAlt_base.alt_strip_II),

            (TrisAlt_base.star, TrisAlt_base.strip_I),
            (TrisAlt_base.star, TrisAlt_base.strip_II),
            (TrisAlt_base.star, TrisAlt_base.star),
            (TrisAlt_base.star, TrisAlt_base.alt_strip_I),
            (TrisAlt_base.star, TrisAlt_base.alt_strip_II),

            (TrisAlt_base.alt_strip_I, TrisAlt_base.strip_I),
            (TrisAlt_base.alt_strip_I, TrisAlt_base.strip_II),
            (TrisAlt_base.alt_strip_I, TrisAlt_base.star),
            (TrisAlt_base.alt_strip_I, TrisAlt_base.alt_strip_I),
            (TrisAlt_base.alt_strip_I, TrisAlt_base.alt_strip_II),

            (TrisAlt_base.twist_strip_I, TrisAlt_base.twist_strip_I),

            (TrisAlt_base.alt_strip_II, TrisAlt_base.strip_I),
            (TrisAlt_base.alt_strip_II, TrisAlt_base.strip_II),
            (TrisAlt_base.alt_strip_II, TrisAlt_base.star),
            (TrisAlt_base.alt_strip_II, TrisAlt_base.alt_strip_I),
            (TrisAlt_base.alt_strip_II, TrisAlt_base.alt_strip_II),

            (TrisAlt_base.strip_1_loose, TrisAlt_base.strip_1_loose),
            (TrisAlt_base.strip_1_loose, TrisAlt_base.star_1_loose),
            (TrisAlt_base.strip_1_loose, TrisAlt_base.alt_strip_1_loose),

            (TrisAlt_base.star_1_loose, TrisAlt_base.strip_1_loose),
            (TrisAlt_base.star_1_loose, TrisAlt_base.star_1_loose),
            (TrisAlt_base.star_1_loose, TrisAlt_base.alt_strip_1_loose),

            (TrisAlt_base.alt_strip_1_loose, TrisAlt_base.strip_1_loose),
            (TrisAlt_base.alt_strip_1_loose, TrisAlt_base.star_1_loose),
            (TrisAlt_base.alt_strip_1_loose, TrisAlt_base.alt_strip_1_loose),

            (TrisAlt_base.star_1_loose, TrisAlt_base.rot_strip_1_loose),
            (TrisAlt_base.strip_1_loose, TrisAlt_base.rot_strip_1_loose),
            (TrisAlt_base.alt_strip_1_loose, TrisAlt_base.rot_strip_1_loose),

            (TrisAlt_base.star_1_loose, TrisAlt_base.arot_strip_1_loose),
            (TrisAlt_base.strip_1_loose, TrisAlt_base.arot_strip_1_loose),
            (TrisAlt_base.alt_strip_1_loose, TrisAlt_base.arot_strip_1_loose),

            (TrisAlt_base.star_1_loose, TrisAlt_base.rot_star_1_loose),
            (TrisAlt_base.strip_1_loose, TrisAlt_base.rot_star_1_loose),
            (TrisAlt_base.alt_strip_1_loose, TrisAlt_base.rot_star_1_loose),

            (TrisAlt_base.star_1_loose, TrisAlt_base.arot_star_1_loose),
            (TrisAlt_base.strip_1_loose, TrisAlt_base.arot_star_1_loose),
            (TrisAlt_base.alt_strip_1_loose, TrisAlt_base.arot_star_1_loose),
        ]
    )

class FoldMethod:
    parallel  = 0
    trapezium = 1
    w         = 2
    triangle  = 3
    star      = 4

    def get(this, s):
        for k,v in FoldName.items():
            if v == s:
                return k
        s = str.capitalize(s)
        for k,v in FoldName.items():
            if v == s:
                return k
        return None

FoldName = {
        FoldMethod.parallel: 'Parallel',
        FoldMethod.trapezium: 'Trapezium',
        FoldMethod.w: 'W',
        FoldMethod.triangle: 'Triangle',
        FoldMethod.star: 'Shell',
    }

foldMethod = FoldMethod()

class RegularHeptagon:
    def __init__(this):
        # V0 in origin
        #             0 = (0, 0)
        #
        #      6             1
        #
        #
        #
        #    5                 2
        #
        #
        #         4       3
        #
        #
        # The fold functions below assume that for the original position holds:
        #  - parallel to the XOY-plane.
        #  - a mirror axis parallel to the Y-axis
        #  - V0 = (0, 0, 0)
        this.VsOrg = [
                Vec([     0.0,            0.0, 0.0]),
                Vec([   Rho/2,             -h, 0.0]),
                Vec([ Sigma/2, -(1 + Sigma)*h, 0.0]),
                Vec([     0.5,             -H, 0.0]),
                Vec([    -0.5,             -H, 0.0]),
                Vec([-Sigma/2, -(1 + Sigma)*h, 0.0]),
                Vec([  -Rho/2,             -h, 0.0])
            ]
        this.Vs = this.VsOrg[:]     # the vertex aray to use.
        this.Fs = [[6, 5, 4, 3, 2, 1, 0]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0]

    def fold(this, a0, b0, a1 = None, b1 = None, keepV0 = True,
                                                fold = FoldMethod.parallel,
                                                rotate = 0
    ):
        if fold == FoldMethod.parallel:
            this.foldParallel(a0, b0, keepV0, rotate)
        elif fold == FoldMethod.trapezium:
            this.foldTrapezium(a0, b0, b1, keepV0, rotate)
        elif fold == FoldMethod.w:
            this.fold_W(a0, b0, a1, b1, keepV0, rotate)
        elif fold == FoldMethod.triangle:
            this.foldTriangle(a0, b0, b1, keepV0, rotate)
        elif fold == FoldMethod.star:
            this.fold_star(a0, b0, a1, b1, keepV0, rotate)
        else:
            raise TypeError('Unknown fold')

    def foldParallel(this, a, b, keepV0 = True, rotate = 0):
        if rotate == 0:
            this.foldParallel_0(a, b, keepV0)
        else:
            this.foldParallel_1(a, b, keepV0)

    def foldParallel_0(this, a, b, keepV0 = True):
        """
        Fold around the 2 parallel diagonals V1-V6 and V2-V5.

        The fold angle a refers the the axis V2-V5 and
        the fold angle b refers the the axis V1-V6.
        If keepV0 = True then the triangle V0, V1, V6 is kept invariant during
        folding, otherwise the trapezium V2-V3-V4-V5 is kept invariant.
        It assumes that the heptagon is in the original position.
        """
        #
        #             0
        #
        #      6 ----------- 1    axis b
        #
        #
        #
        #    5 --------------- 2  axis a
        #
        #
        #         4       3
        #
        #
        this.Fs = [[0, 6, 1], [1, 6, 5, 2], [2, 5, 4, 3]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                1, 6, 2, 5,
            ]
        cosa = math.cos(a)
        sina = math.sin(a)
        cosb = math.cos(b)
        sinb = math.sin(b)
        if (keepV0):
            # for x-coord set to 0:
            # V2 - V[1] = fold_a(V[2] - V[1]) = (cosa, sina)*(V[2] - V[1])
            # => V2 = V[1] + (cosa, sina)*(V[2] - V[1])
            #
            #                             V3
            #                            /
            #                           / b _
            #                       V2 /_.-'  V3_
            #                       _.-'
            #                   _.-'  a
            #   (0, 0) .-------.-------.------.
            #   this. V[0]   V[1]    V[2]    V[3]
            dV2 = [
                    this.VsOrg[2][1] - this.VsOrg[1][1],
                    this.VsOrg[2][2] - this.VsOrg[1][2]
                ]
            V2 = Vec([
                    this.VsOrg[2][0],
                    this.VsOrg[1][1] + cosa * dV2[0] - sina * dV2[1],
                    this.VsOrg[1][2] + cosa * dV2[1] + sina * dV2[0]
                ])
            # Similarly:
            dV3_ = [
                    this.VsOrg[3][1] - this.VsOrg[1][1],
                    this.VsOrg[3][2] - this.VsOrg[1][2]
                ]
            V3_ = [
                    this.VsOrg[1][1] + cosa * dV3_[0] - sina * dV3_[1],
                    this.VsOrg[1][2] + cosa * dV3_[1] + sina * dV3_[0]
                ]
            # now rotate beta:
            dV3 = [
                    V3_[0] - V2[1],
                    V3_[1] - V2[2]
                ]
            V3 = Vec([
                    this.VsOrg[3][0],
                    V2[1] + cosb * dV3[0] - sinb * dV3[1],
                    V2[2] + cosb * dV3[1] + sinb * dV3[0]
                ])
            this.Vs = [
                    this.VsOrg[0],
                    this.VsOrg[1],
                    V2,
                    V3,
                    Vec([-V3[0], V3[1], V3[2]]),
                    Vec([-V2[0], V2[1], V2[2]]),
                    this.VsOrg[6]
                ]
        else:
            # similar to before, except the roles of the vertices are switched
            # i.e. keep V[3] constant...
            dV1 = [
                    this.VsOrg[1][1] - this.VsOrg[2][1],
                    this.VsOrg[1][2] - this.VsOrg[2][2]
                ]
            V1 = Vec([
                    this.VsOrg[1][0],
                    this.VsOrg[2][1] + cosa * dV1[0] - sina * dV1[1],
                    this.VsOrg[2][2] + cosa * dV1[1] + sina * dV1[0]
                ])
            # Similarly:
            dV0_ = [
                    this.VsOrg[0][1] - this.VsOrg[2][1],
                    this.VsOrg[0][2] - this.VsOrg[2][2]
                ]
            V0_ = [
                    this.VsOrg[2][1] + cosa * dV0_[0] - sina * dV0_[1],
                    this.VsOrg[2][2] + cosa * dV0_[1] + sina * dV0_[0]
                ]
            # now rotate beta:
            dV0 = [
                    V0_[0] - V1[1],
                    V0_[1] - V1[2]
                ]
            V0 = Vec([
                    this.VsOrg[0][0],
                    V1[1] + cosb * dV0[0] - sinb * dV0[1],
                    V1[2] + cosb * dV0[1] + sinb * dV0[0]
                ])
            this.Vs = [
                    V0,
                    V1,
                    this.VsOrg[2],
                    this.VsOrg[3],
                    this.VsOrg[4],
                    this.VsOrg[5],
                    Vec([-V1[0], V1[1], V1[2]])
                ]

    def foldParallel_1(this, a, b, keepV0 = True):
        """
        Fold around the 2 parallel diagonals parallel to the edge opposite of
        vertex 1

        The fold angle a refers the the axis V3-V6 and
        the fold angle b refers the the axis V2-V0.
        If keepV0 = True then the vertex V0, and V2 are kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #             1
        #
        #      0 ----------- 2    axis b
        #
        #
        #
        #    6 --------------- 3  axis a
        #
        #
        #         5       4
        #
        this.Fs = [[1, 0, 2], [2, 0, 6, 3], [3, 6, 5, 4]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                2, 0, 3, 6,
            ]
        if (keepV0):
            assert False, "TODO"
        else:
            V3V6 = (this.VsOrg[3] + this.VsOrg[6])/2
            V3V6axis = Vec(this.VsOrg[3] - this.VsOrg[6])
            V0V2 = (this.VsOrg[0] + this.VsOrg[2])/2
            rot_a = Rot(axis = V3V6axis, angle = a)
            V0V2_ = V3V6 + rot_a * (V0V2 - V3V6)
            V0 = V0V2_ + (this.VsOrg[0] - V0V2)
            V2 = V0V2_ + (this.VsOrg[2] - V0V2)
            V1_ = V3V6 + rot_a * (this.VsOrg[1] - V3V6)

            V0V2axis = Vec(V2 - V0)
            rot_b = Rot(axis = V0V2axis, angle = b)
            V1 = V0V2 + rot_b * (V1_ - V0V2)
            this.Vs = [
                    V0,
                    V1,
                    V2,
                    this.VsOrg[3],
                    this.VsOrg[4],
                    this.VsOrg[5],
                    this.VsOrg[6],
                ]

    def foldTrapezium(this, a, b0, b1 = None, keepV0 = True, rotate = 0):
        """
        Fold around 4 diagonals in the shape of a trapezium (trapezoid)

        The fold angle a refers the the axis V1-V6 and
        The fold angle b refers the the axes V1-V3 and V6-V4 and
        If keepV0 = True then the triangle V0, V1, V6 is kept invariant during
        folding, otherwise the edge V3-V4 is kept invariant.
        It assumes that the heptagon is in the original position.
        """
        #
        #              0
        #
        #       6 ----------- 1    axis a
        #       .             .
        #        \           /
        # axis b0 \         / axis b1
        #     5   |         |   2
        #         \        /
        #          "       "
        #          4       3
        #
        #
        this.Fs = [[0, 6, 1], [1, 3, 2], [1, 6, 4, 3], [4, 6, 5]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                4, 6, 6, 1, 1, 3,
            ]
        cosa = math.cos(a)
        sina = math.sin(a)
        if (keepV0):
            # see foldParallel
            dV2_ = [
                    this.VsOrg[2][1] - this.VsOrg[1][1],
                    this.VsOrg[2][2] - this.VsOrg[1][2]
                ]
            V2_ = Vec([
                    this.VsOrg[2][0],
                    this.VsOrg[1][1] + cosa * dV2_[0] - sina * dV2_[1],
                    this.VsOrg[1][2] + cosa * dV2_[1] + sina * dV2_[0]
                ])
            dV3 = [
                    this.VsOrg[3][1] - this.VsOrg[1][1],
                    this.VsOrg[3][2] - this.VsOrg[1][2]
                ]
            V3 = Vec([
                    this.VsOrg[3][0],
                    this.VsOrg[1][1] + cosa * dV3[0] - sina * dV3[1],
                    this.VsOrg[1][2] + cosa * dV3[1] + sina * dV3[0]
                ])
            V4 = Vec([-V3[0], V3[1], V3[2]])
            V1V3 = (this.VsOrg[1] + V3)/2
            V1V3axis = Vec(V3 - this.VsOrg[1])
            r = Rot(axis = V1V3axis, angle = b0)
            V2 = V1V3 + r * (V2_ - V1V3)
            if not Geom3D.eq(b0, b1):
                V5 = Vec([-V2[0], V2[1], V2[2]])
            else:
                V4V6 = (V4 + this.VsOrg[6])/2
                V4V6axis = Vec(this.VsOrg[6] - V4)
                r = Rot(axis = V4V6axis, angle = b1)
                V5_ = Vec([-V2_[0], V2_[1], V2_[2]])
                V5 = V4V6 + r * (V5_ - V4V6)
            this.Vs = [
                    this.VsOrg[0],
                    this.VsOrg[1],
                    V2,
                    V3,
                    V4,
                    V5,
                    this.VsOrg[6]
                ]
        else:
            dV0 = [
                    this.VsOrg[0][1] - this.VsOrg[1][1],
                    this.VsOrg[0][2] - this.VsOrg[1][2]
                ]
            V0 = Vec([
                    this.VsOrg[0][0],
                    this.VsOrg[1][1] + cosa * dV0[0] - sina * dV0[1],
                    this.VsOrg[1][2] + cosa * dV0[1] + sina * dV0[0]
                ])
            V1V3 = (this.VsOrg[1] + this.VsOrg[3])/2
            V1V3axis = Vec(this.VsOrg[3] - this.VsOrg[1])
            r = Rot(axis = V1V3axis, angle = b0)
            V2 = V1V3 + r * (this.VsOrg[2] - V1V3)
            if Geom3D.eq(b0, b1):
                V5 = Vec([-V2[0], V2[1], V2[2]])
            else:
                V4V6 = (this.VsOrg[4] + this.VsOrg[6])/2
                V4V6axis = Vec(this.VsOrg[6] - this.VsOrg[4])
                r = Rot(axis = V4V6axis, angle = b1)
                V5 = V4V6 + r * (this.VsOrg[5] - V4V6)
            this.Vs = [
                    V0,
                    this.VsOrg[1],
                    V2,
                    this.VsOrg[3],
                    this.VsOrg[4],
                    V5,
                    this.VsOrg[6]
                ]

    def foldTriangle(this, a, b0, b1, keepV0 = True, rotate = 0):
        """
        Fold around 3 triangular diagonals from V0.

        The fold angle a refers the the axes V0-V2 and V0-V5 and
        the fold angle b refers the the axis V2-V5.
        If keepV0 = True then the triangle V0, V1, V6 is kept invariant during
        folding, otherwise the trapezium V2-V3-V4-V5 is kept invariant.
        """
        #
        #                0
        #               _^_
        #         6   _/   \_   1
        #           _/       \_
        # axis b0 _/           \_ axis b1
        #        /               \
        #       5 --------------- 2  axis a
        #
        #
        #            4       3
        #
        this.Fs = [[0, 2, 1], [0, 5, 2], [0, 6, 5], [2, 5, 4, 3]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                0, 2, 2, 5, 5, 0
            ]
        Rot0_2 = Rot(axis = this.VsOrg[2] - this.VsOrg[0], angle = b0)
        V1 = Rot0_2 * this.VsOrg[1]
        if (Geom3D.eq(b0, b1)):
            V6 = Vec([-V1[0], V1[1], V1[2]])
        else:
            Rot5_0 = Rot(axis = this.VsOrg[0] - this.VsOrg[5], angle = b1)
            V6 = Rot5_0 * this.VsOrg[6]
        V2 = this.VsOrg[2]
        if keepV0:
            Rot5_2 = Rot(axis = this.VsOrg[5] - this.VsOrg[2], angle = a)
            V3 = Rot5_2 * (this.VsOrg[3] - V2) + V2
            this.Vs = [
                    this.VsOrg[0],
                    V1,
                    this.VsOrg[2],
                    V3,
                    Vec([-V3[0], V3[1], V3[2]]),
                    this.VsOrg[5],
                    V6,
                ]
        else:
            Rot2_5 = Rot(axis = this.VsOrg[2] - this.VsOrg[5], angle = a)
            V0 = Rot2_5 * (this.VsOrg[0] - V2) + V2
            V1 = Rot2_5 * (V1 - V2) + V2
            V6 = Rot2_5 * (V6 - V2) + V2
            this.Vs = [
                    V0,
                    V1,
                    this.VsOrg[2],
                    this.VsOrg[3],
                    this.VsOrg[4],
                    this.VsOrg[5],
                    V6,
                ]

    def fold_star(self, a0, b0, a1, b1, keepV0=True, rotate=0):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a refers the the axes V0-V2 and V0-V5 and
        the fold angle b0 refers the the axes V0-V3 and V0-V4.
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #               Vi
        #               .^.
        #       i+6   _/| |\_   i+1
        #           _/ /   \ \_
        # axis b1 _/  |     |  \_ axis b0
        #        /    |     |    \
        #     i+5    /       \    i+2
        #   axis a1 |         | axis a0
        #           "         "
        #         i+4         i+3
        #

        prj = {
            0: self.fold_star_0,
            1: self.fold_star_1,
            2: self.fold_star_2,
            3: self.fold_star_3,
            4: self.fold_star_4,
            5: self.fold_star_5,
            6: self.fold_star_6
        }
        prj[rotate](a0, b0, a1, b1, keepV0)

    def fold_star_0(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a refers the the axes V0-V2 and V0-V5 and
        the fold angle b0 refers the the axes V0-V3 and V0-V4.
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #                0
        #               .^.
        #         6   _/| |\_   1
        #           _/ /   \ \_
        # axis b1 _/  |     |  \_ axis b0
        #        /    |     |    \
        #       5    /       \    2
        #   axis a1 |         | axis a0
        #           "         "
        #           4         3
        #
        if (keepV0):
            assert False, "TODO"
        else:
            Rot0_3 = Rot(axis=self.VsOrg[3] - self.VsOrg[0], angle=a0)
            V0 = self.VsOrg[0]
            V1_ = Rot0_3 * self.VsOrg[1]
            V2 = Rot0_3 * self.VsOrg[2]
            Rot0_2 = Rot(axis=V2 - V0, angle=b0)
            V1 = Rot0_2 * V1_
            if (Geom3D.eq(a0, a1)):
                V5 = Vec([-V2[0], V2[1], V2[2]])
                if (Geom3D.eq(b0, b1)):
                    V6 = Vec([-V1[0], V1[1], V1[2]])
                else:
                    V6 = Vec([-V1_[0], V1_[1], V1_[2]])
                    Rot5_0 = Rot(axis=V0 - V5, angle=b1)
                    V6 = Rot5_0 * (V6 - V0) + V0
            else:
                Rot4_0 = Rot(axis=V0 - self.VsOrg[4], angle=a1)
                V6 = Rot4_0 * self.VsOrg[6]
                V5 = Rot4_0 * self.VsOrg[5]
                Rot5_0 = Rot(axis=V0 - V5, angle=b1)
                V6 = Rot5_0 * (V6 - V0) + V0
            self.Vs = [V0, V1, V2, self.VsOrg[3], self.VsOrg[4], V5, V6]
            self.fold_star_es_fs(0)

    def fold_star_es_fs(self, no):
        """
        Set self.Es and self.FS for shell fold and specified position.

        no: number to shift up
        """
        i = [(i + no) % 7 for i in range(7)]
        self.Fs = [
            [i[0], i[2], i[1]],
            [i[0], i[3], i[2]],
            [i[0], i[4], i[3]],
            [i[0], i[5], i[4]],
            [i[0], i[6], i[5]],
        ]
        self.Es = [
            i[0], i[1], i[1], i[2], i[2], i[3], i[3], i[4], i[4], i[5], i[5], i[6], i[6], i[0],
            i[0], i[2], i[0], i[3], i[0], i[4], i[0], i[5]
        ]

    def fold_star_1(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'shell'.

        the fold angle a0 refers to the axes V1-V4,
        The fold angle b0 refers to the axes V1-V3,
        the fold angle a1 refers to the axes V1-V5,
        The fold angle b1 refers to the axes V1-V6 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #                1
        #               .^.
        #         0   _/| |\_   2
        #           _/ /   \ \_
        # axis b1 _/  |     |  \_ axis b0
        #        /    |     |    \
        #       6    /       \    3
        #   axis a1 |         | axis a0
        #           "         "
        #           5         4
        #
        self.fold_star_es_fs(1)
        self.fold_star_1_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_star_1_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_star_1, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        if (keepV0):
            assert False, "TODO"
        else:
            # rot b0
            V1V3 = (Vs[1] + Vs[3]) / 2
            V1V3axis = Vec(Vs[1] - Vs[3])
            # negative angle since left side rotates
            rot_b0 = Rot(axis=V1V3axis, angle=-b0)
            V2 = V1V3 + rot_b0 * (Vs[2] - V1V3)
            # rot a0
            V1V4 = (Vs[1] + Vs[4]) / 2
            V1V4axis = Vec(Vs[1] - Vs[4])
            rot_a0 = Rot(axis=V1V4axis, angle=a0)
            # middle of V0-V5 which is // to V1V4 axis
            V0V5  = (Vs[0] + Vs[5]) / 2
            V0V5_ = V1V4 + rot_a0 * (V0V5 - V1V4)
            V0_ = V0V5_ + (Vs[0] - V0V5)
            V5  = V0V5_ + (Vs[5] - V0V5)
            V6_ = V1V4 + rot_a0 * (Vs[6] - V1V4)
            # rot a1
            V1V5 = (Vs[1] + V5) / 2
            V1V5axis = Vec(Vs[1] - V5)
            rot_a1 = Rot(axis=V1V5axis, angle=a1)
            V0V6  = (V0_ + V6_) / 2
            V0V6_ = V1V5 + rot_a1 * (V0V6 - V1V5)
            V0_ = V0V6_ + (V0_ - V0V6)
            V6  = V0V6_ + (V6_ - V0V6)
            # rot b1
            V1V6 = (Vs[1] + V6) / 2
            V1V6axis = Vec(Vs[1] - V6)
            rot_b1 = Rot(axis=V1V6axis, angle=b1)
            V0 = V1V6 + rot_b1 * (V0_ - V1V6)
            self.Vs = [V0, Vs[1], V2, Vs[3], Vs[4], V5, V6]

    def fold_star_2(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'shell'.

        the fold angle a0 refers to the axes V2-V5,
        The fold angle b0 refers to the axes V2-V4,
        the fold angle a1 refers to the axes V2-V6,
        The fold angle b1 refers to the axes V2-V0 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #                2
        #               .^.
        #         1   _/| |\_   3
        #           _/ /   \ \_
        # axis b1 _/  |     |  \_ axis b0
        #        /    |     |    \
        #       0    /       \    4
        #   axis a1 |         | axis a0
        #           "         "
        #           6         5
        #
        self.fold_star_es_fs(2)
        self.fold_star_2_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_star_2_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_star_2, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        if (keepV0):
            assert False, "TODO"
        else:
            # rot b0
            V2V4 = (Vs[2] + Vs[4]) / 2
            V2V4axis = Vec(Vs[2] - Vs[4])
            rot_b0 = Rot(axis=V2V4axis, angle=b0)
            # middle of V1-V5 which is // to V2V4 axis
            V1V5  = (Vs[1] + Vs[5]) / 2
            V1V5_ = V2V4 + rot_b0 * (V1V5 - V2V4)
            V1_ = V1V5_ + (Vs[1] - V1V5)
            V5 = V1V5_ + (Vs[5] - V1V5)
            # middle of V0-V6 which is // to V2V4 axis
            V0V6  = (Vs[0] + Vs[6]) / 2
            V0V6_ = V2V4 + rot_b0 * (V0V6 - V2V4)
            V0_ = V0V6_ + (Vs[0] - V0V6)
            V6_ = V0V6_ + (Vs[6] - V0V6)

            # rot a0
            V2V5 = (Vs[2] + V5) / 2
            V2V5axis = Vec(Vs[2] - V5)
            rot_a0 = Rot(axis=V2V5axis, angle=a0)
            # middle of V1-V6 which is // to V2V5 axis
            V1V6  = (V1_ + V6_) / 2
            V1V6_ = V2V5 + rot_a0 * (V1V6 - V2V5)
            V1_ = V1V6_ + (V1_ - V1V6)
            V6 = V1V6_ + (V6_ - V1V6)
            V0_ = V2V5 + rot_a0 * (V0_ - V2V5)

            # rot a1
            V2V6 = (Vs[2] + V6) / 2
            V2V6axis = Vec(Vs[2] - V6)
            rot_a1 = Rot(axis=V2V6axis, angle=a1)
            # middle of V0-V1 which is // to V2V6 axis
            V0V1  = (V0_ + V1_)/2
            V0V1_ = V2V6 + rot_a1 * (V0V1 - V2V6)
            V0 = V0V1_ + (V0_ - V0V1)
            V1_ = V0V1_ + (V1_ - V0V1)

            # rot b1
            V2V0 = (Vs[2] + V0) / 2
            V2V0axis = Vec(Vs[2] - V0)
            rot_b1 = Rot(axis=V2V0axis, angle=b1)
            V1 = V2V0 + rot_b1 * (V1_ - V2V0)

            self.Vs = [V0, V1, Vs[2], Vs[3], Vs[4], V5, V6]

    def fold_star_3(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'shell'.

        the fold angle a0 refers to the axes V3-V6,
        The fold angle b0 refers to the axes V3-V5,
        the fold angle a1 refers to the axes V3-V0,
        The fold angle b1 refers to the axes V3-V1 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #                3
        #               .^.
        #         2   _/| |\_   4
        #           _/ /   \ \_
        # axis b1 _/  |     |  \_ axis b0
        #        /    |     |    \
        #       1    /       \    5
        #   axis a1 |         | axis a0
        #           "         "
        #           0         6
        #
        self.fold_star_es_fs(3)
        self.fold_star_3_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_star_3_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_star_3, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        if (keepV0):
            assert False, "TODO"
        else:
            # rot b0
            V3V5 = (Vs[3] + Vs[5]) / 2
            V3V5axis = Vec(Vs[3] - Vs[5])
            rot_b0 = Rot(axis=V3V5axis, angle=b0)
            # middle of V2-V6 which is // to V3V5 axis
            V2V6  = (Vs[2] + Vs[6]) / 2
            V2V6_ = V3V5 + rot_b0 * (V2V6 - V3V5)
            V2_ = V2V6_ + (Vs[2] - V2V6)
            V6 = V2V6_ + (Vs[6] - V2V6)
            # middle of V1-V0 which is // to V3V5 axis
            V1V0  = (Vs[1] + Vs[0]) / 2
            V1V0_ = V3V5 + rot_b0 * (V1V0 - V3V5)
            V1_ = V1V0_ + (Vs[1] - V1V0)
            V0_ = V1V0_ + (Vs[0] - V1V0)

            # rot a0
            V3V6 = (Vs[3] + V6) / 2
            V3V6axis = Vec(Vs[3] - V6)
            rot_a0 = Rot(axis=V3V6axis, angle=a0)
            # middle of V2-V0 which is // to V3V6 axis
            V2V0  = (V2_ + V0_) / 2
            V2V0_ = V3V6 + rot_a0 * (V2V0 - V3V6)
            V2_ = V2V0_ + (V2_ - V2V0)
            V0 = V2V0_ + (V0_ - V2V0)
            V1_ = V3V6 + rot_a0 * (V1_ - V3V6)

            # rot a1
            V3V0 = (Vs[3] + V0) / 2
            V3V0axis = Vec(Vs[3] - V0)
            rot_a1 = Rot(axis=V3V0axis, angle=a1)
            # middle of V1-V2 which is // to V3V0 axis
            V1V2  = (V1_ + V2_) / 2
            V1V2_ = V3V0 + rot_a1 * (V1V2 - V3V0)
            V1 = V1V2_ + (V1_ - V1V2)
            V2_ = V1V2_ + (V2_ - V1V2)

            # rot b1
            V3V1 = (Vs[3] + V1) / 2
            V3V1axis = Vec(Vs[3] - V1)
            rot_b1 = Rot(axis=V3V1axis, angle=b1)
            V2 = V3V1 + rot_b1 * (V2_ - V3V1)

            self.Vs = [V0, V1, V2, Vs[3], Vs[4], Vs[5], V6]

    def fold_star_4(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'shell'.

        the fold angle a0 refers to the axes V4-V0,
        The fold angle b0 refers to the axes V4-V6,
        the fold angle a1 refers to the axes V4-V1,
        The fold angle b1 refers to the axes V4-V2 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #                4
        #               .^.
        #         3   _/| |\_   5
        #           _/ /   \ \_
        # axis b1 _/  |     |  \_ axis b0
        #        /    |     |    \
        #       2    /       \    6
        #   axis a1 |         | axis a0
        #           "         "
        #           1         0
        #
        self.fold_star_es_fs(4)
        self.fold_star_4_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_star_4_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_star_3, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        if (keepV0):
            assert False, "TODO"
        else:
            # rot b1
            V4V2 = (Vs[4] + Vs[2]) / 2
            V4V2axis = Vec(Vs[4] - Vs[2])
            rot_b1 = Rot(axis=V4V2axis, angle=-b1)
            # middle of V5-V1 which is // to V4V2 axis
            V5V1  = (Vs[5] + Vs[1]) / 2
            V5V1_ = V4V2 + rot_b1 * (V5V1 - V4V2)
            V5_ = V5V1_ + (Vs[5] - V5V1)
            V1 = V5V1_ + (Vs[1] - V5V1)
            # middle of V6-V0 which is // to V4V2 axis
            V6V0  = (Vs[6] + Vs[0]) / 2
            V6V0_ = V4V2 + rot_b1 * (V6V0 - V4V2)
            V6_ = V6V0_ + (Vs[6] - V6V0)
            V0_ = V6V0_ + (Vs[0] - V6V0)

            # rot a1
            V4V1 = (Vs[4] + V1) / 2
            V4V1axis = Vec(Vs[4] - V1)
            rot_a1 = Rot(axis=V4V1axis, angle=-a1)
            # middle of V5-V0 which is // to V4V1 axis
            V5V0  = (V5_ + V0_) / 2
            V5V0_ = V4V1 + rot_a1 * (V5V0 - V4V1)
            V5_ = V5V0_ + (V5_ - V5V0)
            V0 = V5V0_ + (V0_ - V5V0)
            V6_ = V4V1 + rot_a1 * (V6_ - V4V1)

            # rot a0
            V4V0 = (Vs[4] + V0) / 2
            V4V0axis = Vec(Vs[4] - V0)
            rot_a0 = Rot(axis=V4V0axis, angle=-a0)
            # middle of V5-V6 which is // to V4V0 axis
            V5V6  = (V5_ + V6_) / 2
            V5V6_ = V4V0 + rot_a0 * (V5V6 - V4V0)
            V5_ = V5V6_ + (V5_ - V5V6)
            V6 = V5V6_ + (V6_ - V5V6)

            # rot b0
            V4V6 = (Vs[4] + V6) / 2
            V4V6axis = Vec(Vs[4] - V6)
            rot_b0 = Rot(axis=V4V6axis, angle=-b0)
            V5 = V4V6 + rot_b0 * (V5_ - V4V6)

            self.Vs = [V0, V1, Vs[2], Vs[3], Vs[4], V5, V6]

    def fold_star_5(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'shell'.

        the fold angle a0 refers to the axes V5-V1,
        The fold angle b0 refers to the axes V5-V0,
        the fold angle a1 refers to the axes V5-V2,
        The fold angle b1 refers to the axes V5-V3 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #                5
        #               .^.
        #         4   _/| |\_   6
        #           _/ /   \ \_
        # axis b1 _/  |     |  \_ axis b0
        #        /    |     |    \
        #       3    /       \    0
        #   axis a1 |         | axis a0
        #           "         "
        #           2         1
        #
        self.fold_star_es_fs(5)
        self.fold_star_5_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_star_5_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_star_3, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        if (keepV0):
            assert False, "TODO"
        else:
            # rot b1
            V5V3 = (Vs[5] + Vs[3]) / 2
            V5V3axis = Vec(Vs[5] - Vs[3])
            rot_b1 = Rot(axis=V5V3axis, angle=-b1)
            # middle of V6-V2 which is // to V5V3 axis
            V6V2  = (Vs[6] + Vs[2]) / 2
            V6V2_ = V5V3 + rot_b1 * (V6V2 - V5V3)
            V6_ = V6V2_ + (Vs[6] - V6V2)
            V2 = V6V2_ + (Vs[2] - V6V2)
            # middle of V0-V1 which is // to V5V3 axis
            V0V1  = (Vs[0] + Vs[1]) / 2
            V0V1_ = V5V3 + rot_b1 * (V0V1 - V5V3)
            V0_ = V0V1_ + (Vs[0] - V0V1)
            V1_ = V0V1_ + (Vs[1] - V0V1)

            # rot a1
            V5V2 = (Vs[5] + V2) / 2
            V5V2axis = Vec(Vs[5] - V2)
            rot_a1 = Rot(axis=V5V2axis, angle=-a1)
            # middle of V6-V1 which is // to V5V2 axis
            V6V1  = (V6_ + V1_) / 2
            V6V1_ = V5V2 + rot_a1 * (V6V1 - V5V2)
            V6_ = V6V1_ + (V6_ - V6V1)
            V1 = V6V1_ + (V1_ - V6V1)
            V0_ = V5V2 + rot_a1 * (V0_ - V5V2)

            # rot a0
            V5V1 = (Vs[5] + V1) / 2
            V5V1axis = Vec(Vs[5] - V1)
            rot_a0 = Rot(axis=V5V1axis, angle=-a0)
            # middle of V6-V0 which is // to V5V1 axis
            V6V0  = (V6_ + V0_) / 2
            V6V0_ = V5V1 + rot_a0 * (V6V0 - V5V1)
            V6_ = V6V0_ + (V6_ - V6V0)
            V0 = V6V0_ + (V0_ - V6V0)

            # rot b0
            V5V0 = (Vs[5] + V0) / 2
            V5V0axis = Vec(Vs[5] - V0)
            rot_b0 = Rot(axis=V5V0axis, angle=-b0)
            V6 = V5V0 + rot_b0 * (V6_ - V5V0)

            self.Vs = [V0, V1, V2, Vs[3], Vs[4], Vs[5], V6]

    def fold_star_6(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'shell'.

        the fold angle a0 refers to the axes V1-V4,
        The fold angle b0 refers to the axes V1-V3,
        the fold angle a1 refers to the axes V1-V5,
        The fold angle b1 refers to the axes V1-V6 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #                6
        #               .^.
        #         5   _/| |\_   0
        #           _/ /   \ \_
        # axis b1 _/  |     |  \_ axis b0
        #        /    |     |    \
        #       4    /       \    1
        #   axis a1 |         | axis a0
        #           "         "
        #           3         2
        #
        self.Fs = [[6, 1, 0], [6, 2, 1], [6, 3, 2], [6, 4, 3], [6, 5, 4]]
        self.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                6, 1, 6, 2, 6, 3, 6, 4
            ]
        # opposite angle, because of opposite isometry
        Vs = self.fold_W1_help(-a1, -b1, -a0, -b0, keepV0,
            [
                self.VsOrg[0],
                self.VsOrg[6],
                self.VsOrg[5],
                self.VsOrg[4],
                self.VsOrg[3],
                self.VsOrg[2],
                self.VsOrg[1]
            ]
        )
        self.Vs = [
            Vs[0],
            Vs[6],
            Vs[5],
            Vs[4],
            Vs[3],
            Vs[2],
            Vs[1]
        ]

    def fold_W(this, a0, b0, a1, b1, keepV0 = True, rotate = 0):
        prj = {
            0: this.fold_W0,
            1: this.fold_W1,
            2: this.fold_W2,
            3: this.fold_W3,
            4: this.fold_W4,
            5: this.fold_W5,
            6: this.fold_W6
        }
        prj[rotate](a0, b0, a1, b1, keepV0)

    def fold_W0(this, a0, b0, a1, b1, keepV0 = True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axes V0-V3,
        the fold angle a1 refers to the axes V0-V4,
        The fold angle b0 refers to the axes V1-V3,
        The fold angle b1 refers to the axes V6-V4 and
        The vertex V0 is kept invariant during folding
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #               0
        #               ^
        #        6     | |     1
        #        .    /   \    .
        # axis b1 \  |     |  / axis b0
        #          " |     | "
        #      5   |/       \|   2
        #          V axes  a V
        #          "         "
        #          4         3
        #
        Rot0_3 = Rot(axis = this.VsOrg[3] - this.VsOrg[0], angle = a0)
        V1 = Rot0_3 * this.VsOrg[1]
        V2_ = Rot0_3 * this.VsOrg[2]
        Rot1_3 = Rot(axis = this.VsOrg[3] - V1, angle = b0)
        V2 = Rot1_3 * (V2_ - V1) + V1
        if (Geom3D.eq(a0, a1)):
            V6 = Vec([-V1[0], V1[1], V1[2]])
            if (Geom3D.eq(b0, b1)):
                V5 = Vec([-V2[0], V2[1], V2[2]])
            else:
                V5 = Vec([-V2_[0], V2_[1], V2_[2]])
                Rot4_6 = Rot(axis = V6 - this.VsOrg[4], angle = b1)
                V5 = Rot4_6 * (V5 - V6) + V6
        else:
            Rot4_0 = Rot(axis = this.VsOrg[0] - this.VsOrg[4], angle = a1)
            V6 = Rot4_0 * this.VsOrg[6]
            V5 = Rot4_0 * this.VsOrg[5]
            Rot4_6 = Rot(axis = V6 - this.VsOrg[4], angle = b1)
            V5 = Rot4_6 * (V5 - V6) + V6
        this.Vs = [
                this.VsOrg[0],
                V1,
                V2,
                this.VsOrg[3],
                this.VsOrg[4],
                V5,
                V6,
            ]
        this.Fs = [[1, 3, 2], [1, 0, 3], [0, 4, 3], [0, 6, 4], [6, 5, 4]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                1, 3, 3, 0, 0, 4, 4, 6
            ]

    def fold_W1_help(this, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_W1, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        if (keepV0):
            assert False, "TODO"
        else:
            # rot b0
            V2V4 = (Vs[2] + Vs[4])/2
            V2V4axis = Vec(Vs[2] - Vs[4])
            rot_b0 = Rot(axis = V2V4axis, angle = b0)
            V1V5  = (Vs[1] + Vs[5])/2
            V1V5_ = V2V4 + rot_b0 * (V1V5 - V2V4)
            V1  = V1V5_ + (Vs[1] - V1V5)
            V5_ = V1V5_ + (Vs[5] - V1V5)
            V0V6 = (Vs[0] + Vs[6])/2
            V0V6_ = V2V4 + rot_b0 * (V0V6 - V2V4)
            V0_ = V0V6_ + (Vs[0] - V0V6)
            V6_ = V0V6_ + (Vs[6] - V0V6)
            # rot a0
            V1V4 = (V1 + Vs[4])/2
            V1V4axis = Vec(V1 - Vs[4])
            rot_a0 = Rot(axis = V1V4axis, angle = a0)
            V0V5  = (V0_ + V5_)/2
            V0V5_ = V1V4 + rot_a0 * (V0V5 - V1V4)
            V0_ = V0V5_ + (V0_ - V0V5)
            V5  = V0V5_ + (V5_ - V0V5)
            V6_ = V1V4 + rot_a0 * (V6_ - V1V4)
            # rot a1
            V1V5 = (V1 + V5)/2
            V1V5axis = Vec(V1 - V5)
            rot_a1 = Rot(axis = V1V5axis, angle = a1)
            V0V6  = (V0_ + V6_)/2
            V0V6_ = V1V5 + rot_a1 * (V0V6 - V1V5)
            V0  = V0V6_ + (V0_ - V0V6)
            V6_ = V0V6_ + (V6_ - V0V6)
            # rot b1
            V0V5 = (V0 + V5)/2
            V0V5axis = Vec(V0 - V5)
            rot_b1 = Rot(axis = V0V5axis, angle = b1)
            V6 = V0V5 + rot_b1 * (V6_ - V0V5)
            return [
                    V0,
                    V1,
                    Vs[2],
                    Vs[3],
                    Vs[4],
                    V5,
                    V6,
                ]

    def fold_W3_help(this, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_W3, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        if (keepV0):
            assert False, "TODO"
        else:
            #
            #               3
            #               ^
            #        2     | |     4
            #        .    /   \    .
            # axis b1 \  |     |  / axis b0
            #          " |     | "
            #      1   |/       \|   5
            #          V axes  a V
            #          "         "
            #          0         6
            #
            # rot a0
            V3V6 = (Vs[3] + Vs[6])/2
            V3V6axis = Vec(Vs[3] - Vs[6])
            rot_a0 = Rot(axis = V3V6axis, angle = a0)
            V0V2  = (Vs[0] + Vs[2])/2
            V0V2_ = V3V6 + rot_a0 * (V0V2 - V3V6)
            V0  = V0V2_ + (Vs[0] - V0V2)
            V2_ = V0V2_ + (Vs[2] - V0V2)
            V1_ = V3V6 + rot_a0 * (Vs[1] - V3V6)
            # rot a1
            V3V0 = (Vs[3] + V0)/2
            V3V0axis = Vec(Vs[3] - V0)
            rot_a1 = Rot(axis = V3V0axis, angle = a1)
            V1V2  = (V1_ + V2_)/2
            V1V2_ = V3V0 + rot_a1 * (V1V2 - V3V0)
            V1_ = V1V2_ + (V1_ - V1V2)
            V2  = V1V2_ + (V2_ - V1V2)
            # rot b1
            V2V0 = (V2 + V0)/2
            V2V0axis = Vec(V2 - V0)
            rot_b1 = Rot(axis = V2V0axis, angle = b1)
            V1 = V2V0 + rot_b1 * (V1_ - V2V0)
            # rot b0
            V6V4 = (Vs[6] + Vs[4])/2
            V6V4axis = Vec(Vs[6] - Vs[4])
            rot_b0 = Rot(axis = V6V4axis, angle = b0)
            V5 = V6V4 + rot_b0 * (Vs[5] - V6V4)
            return [
                    V0,
                    V1,
                    V2,
                    Vs[3],
                    Vs[4],
                    V5,
                    Vs[6],
                ]

    def fold_W1(this, a0, b0, a1, b1, keepV0 = True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axes V1-V4,
        the fold angle a1 refers to the axes V1-V5,
        The fold angle b0 refers to the axes V2-V4,
        The fold angle b1 refers to the axes V0-V5 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #               1
        #               ^
        #        0     | |     2
        #        .    /   \    .
        # axis b1 \  |     |  / axis b0
        #          " |     | "
        #      6   |/       \|   3
        #          V axes  a V
        #          "         "
        #          5         4
        #
        this.Fs = [[2, 4, 3], [2, 1, 4], [1, 5, 4], [1, 0, 5], [0, 6, 5]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                2, 4, 4, 1, 1, 5, 5, 0
            ]
        this.Vs = this.fold_W1_help(a0, b0, a1, b1, keepV0, this.VsOrg)

    def fold_W2(this, a0, b0, a1, b1, keepV0 = True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axes V2-V5,
        the fold angle a1 refers to the axes V2-V6,
        The fold angle b0 refers to the axes V3-V5,
        The fold angle b1 refers to the axes V1-V6 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #               2
        #               ^
        #        1     | |     3
        #        .    /   \    .
        # axis b1 \  |     |  / axis b0
        #          " |     | "
        #      0   |/       \|   4
        #          V axes  a V
        #          "         "
        #          6         5
        #
        this.Fs = [[3, 5, 4], [3, 2, 5], [2, 6, 5], [2, 1, 6], [1, 0, 6]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                3, 5, 5, 2, 2, 6, 6, 1
            ]
        Vs = this.fold_W1_help(a0, b0, a1, b1, keepV0,
            [
                this.VsOrg[1],
                this.VsOrg[2],
                this.VsOrg[3],
                this.VsOrg[4],
                this.VsOrg[5],
                this.VsOrg[6],
                this.VsOrg[0]
            ]
        )
        this.Vs = [
            Vs[6],
            Vs[0],
            Vs[1],
            Vs[2],
            Vs[3],
            Vs[4],
            Vs[5]
        ]

    def fold_W3(this, a0, b0, a1, b1, keepV0 = True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axes V3-V6,
        the fold angle a1 refers to the axes V3-V0,
        The fold angle b0 refers to the axes V4-V6,
        The fold angle b1 refers to the axes V2-V0 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #               3
        #               ^
        #        2     | |     4
        #        .    /   \    .
        # axis b1 \  |     |  / axis b0
        #          " |     | "
        #      1   |/       \|   5
        #          V axes  a V
        #          "         "
        #          0         6
        #
        this.Fs = [[4, 6, 5], [4, 3, 6], [3, 0, 6], [3, 2, 0], [2, 1, 0]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                4, 6, 6, 3, 3, 0, 0, 2
            ]
        this.Vs = this.fold_W3_help(a0, b0, a1, b1, keepV0, this.VsOrg)

    def fold_W4(this, a0, b0, a1, b1, keepV0 = True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axes V3-V6,
        the fold angle a1 refers to the axes V3-V0,
        The fold angle b0 refers to the axes V4-V6,
        The fold angle b1 refers to the axes V2-V0 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #               4
        #               ^
        #        3     | |     5
        #        .    /   \    .
        # axis b1 \  |     |  / axis b0
        #          " |     | "
        #      2   |/       \|   6
        #          V axes  a V
        #          "         "
        #          1         0
        #
        this.Fs = [[5, 0, 6], [5, 4, 0], [4, 1, 0], [4, 3, 1], [3, 2, 1]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                5, 0, 0, 4, 4, 1, 1, 3
            ]
        Vs = this.fold_W3_help(-a1, -b1, -a0, -b0, keepV0,
            [
                this.VsOrg[0],
                this.VsOrg[6],
                this.VsOrg[5],
                this.VsOrg[4],
                this.VsOrg[3],
                this.VsOrg[2],
                this.VsOrg[1]
            ]
        )
        this.Vs = [
            Vs[0],
            Vs[6],
            Vs[5],
            Vs[4],
            Vs[3],
            Vs[2],
            Vs[1]
        ]

    def fold_W5(this, a0, b0, a1, b1, keepV0 = True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axes V1-V4,
        the fold angle a1 refers to the axes V1-V5,
        The fold angle b0 refers to the axes V2-V4,
        The fold angle b1 refers to the axes V0-V5 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #               5
        #               ^
        #        4     | |     6
        #        .    /   \    .
        # axis b1 \  |     |  / axis b0
        #          " |     | "
        #      3   |/       \|   0
        #          V axes  a V
        #          "         "
        #          2         1
        #
        this.Fs = [[0, 6, 1], [6, 5, 1], [5, 2, 1], [5, 4, 2], [4, 3, 2]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                6, 1, 1, 5, 5, 2, 2, 4
            ]
        Vs = this.fold_W1_help(-a1, -b1, -a0, -b0, keepV0,
            [
                this.VsOrg[6],
                this.VsOrg[5],
                this.VsOrg[4],
                this.VsOrg[3],
                this.VsOrg[2],
                this.VsOrg[1],
                this.VsOrg[0]
            ]
        )
        this.Vs = [
            Vs[6],
            Vs[5],
            Vs[4],
            Vs[3],
            Vs[2],
            Vs[1],
            Vs[0]
        ]

    def fold_W6(this, a0, b0, a1, b1, keepV0 = True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axes V6-V2,
        the fold angle a1 refers to the axes V6-V3,
        The fold angle b0 refers to the axes V2-V0 and
        The fold angle b1 refers to the axes V3-V5,
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        #
        #               6
        #               ^
        #        5     | |     0
        #        .    /   \    .
        # axis b1 \  |     |  / axis b0
        #          " |     | "
        #      4   |/       \|   1
        #          V axes  a V
        #          "         "
        #          3         2
        #
        this.Fs = [[1, 0, 2], [2, 0, 6], [2, 6, 3], [3, 6, 5], [3, 5, 4]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
                0, 2, 2, 6, 6, 3, 3, 5
            ]
        # opposite angle, because of opposite isometry
        Vs = this.fold_W1_help(-a1, -b1, -a0, -b0, keepV0,
            [
                this.VsOrg[0],
                this.VsOrg[6],
                this.VsOrg[5],
                this.VsOrg[4],
                this.VsOrg[3],
                this.VsOrg[2],
                this.VsOrg[1]
            ]
        )
        this.Vs = [
            Vs[0],
            Vs[6],
            Vs[5],
            Vs[4],
            Vs[3],
            Vs[2],
            Vs[1]
        ]

    def translate(this, T):
        for i in range(len(this.Vs)):
            this.Vs[i] = T + this.Vs[i]

    def rotate(this, axis, angle):
        this.transform(Rot(axis = axis, angle = angle))

    def transform(this, T):
        for i in range(len(this.Vs)):
            this.Vs[i] = T * this.Vs[i]

def Kite2Hept(Left, Top, Right, Bottom, heptPosAlt = False):
    """Return the a tuple with vertices and the normal of an equilateral
    heptagon for a kite, Vl, Vt, Vr, Vb; the tuple has the following structure:
    ([h0, h1, h2, h3, h4, h5, h6], normal), with h0 = Top.

    Left: left coordinate
    Top: top coordinate
    Right: right coordinate
    Bottom: bottom coordinate
    heptPosAlt: 2 possible orientations for the heptagons exists. If false then
                the preferred position is returned, otherwise the heptagon will
                be 'upside down'.
    """
    #print 'heptPosAlt', heptPosAlt
    if not heptPosAlt:
        Vl = Vec(Left)
        Vt = Vec(Top)
        Vr = Vec(Right)
        Vb = Vec(Bottom)
    else:
        Vl = Vec(Right)
        Vt = Vec(Bottom)
        Vr = Vec(Left)
        Vb = Vec(Top)
    Vo = (Vl + Vr) /2
    Dr = Vo - Vr
    Du = Vo - Vt
    w = Dr.norm()
    f = Du.norm()
    g = (Vo - Vb).norm()
    #print 'f', f, 'g', g

    if f == 0:
        print('Kite2Hept: warning f == 0')
        return
    if w == 0:
        print('Kite2Hept: warning w == 0')
        return
    #if f > g:
    #    f, g = g, f

    V = lambda x: math.sqrt(x)

    r = f / w
    q = g / w
    n = V(1.0 + q*q) / 2
    m = V(1.0 + r*r) / 2
    k = m*(1.0 + 1.0/n)

    qkpr = q * k + r
    root = (k*(2 - k) + r * r)

    #assert(root>=0)
    if root < 0:
        print('kite2Hept: negative sqrt requested')
        return

    nom   = (f + g)
    denom = qkpr + V(root)

    if denom == 0:
        print('kite2Hept: error denom == 0')
        return

    w1    =  nom / denom

    w1Rel = w1 / w
    #print 'c', w1Rel
    w2Rel = k * w1Rel
    w3Rel = m * w1Rel

    relPos = lambda v0, v1, rat: rat*(v1 - v0) + v0
    #h0 = Vt
    h1 = relPos(Vt, Vr, w1Rel)
    h2 = relPos(Vb, Vr, w2Rel)
    h3 = relPos(Vb, Vr, w3Rel)
    h4 = relPos(Vb, Vl, w3Rel)
    h5 = relPos(Vb, Vl, w2Rel)
    h6 = relPos(Vt, Vl, w1Rel)

    N = Dr.cross(Du).normalize()

    #C = (Vt + h1 + h2 + h3 + h4 + h5 + h6) / 7
    #return ([Vt, h1, h2, h3, h4, h5, h6], N)
    # Don't return Vector types, since I had problems with this on a MS. Windows
    # OS.
    return (
            [
                Vec([Vt[0], Vt[1], Vt[2]]),
                Vec([h1[0], h1[1], h1[2]]),
                Vec([h2[0], h2[1], h2[2]]),
                Vec([h3[0], h3[1], h3[2]]),
                Vec([h4[0], h4[1], h4[2]]),
                Vec([h5[0], h5[1], h5[2]]),
                Vec([h6[0], h6[1], h6[2]])
            ],
            Vec(N)
        )

class FldHeptagonShape(Geom3D.CompoundShape):
    def __init__(this, shapes, nFold = 3, mFold = 3,
            name = 'Folded Regular Heptagons'
    ):
        this.nFold = nFold
        this.mFold = mFold
        this.altNFoldFace = False
        this.altMFoldFace = False
        Geom3D.CompoundShape.__init__(this, shapes, name = name)
        this.heptagon = RegularHeptagon()
        this.dihedralAngle = 1.2
        this.posAngleMin = 0
        this.posAngleMax = math.pi/2
        this.posAngle = 0
        this.inclReflections = True
        this.rotateFold = 0
        this.fold1 = 0.0
        this.fold2 = 0.0
        this.oppFold1 = 0.0
        this.oppFold2 = 0.0
        this.foldHeptagon = foldMethod.parallel
        this.height = 2.3
        this.applySymmetry = True
        this.addXtraFs = True
        this.onlyRegFs = False
        this.useCulling = False
        this.updateShape = True

    def __repr__(this):
        #s = '%s(\n  ' % findModuleClassName(this.__class__, __name__)
        s = 'FldHeptagonShape(\n  '
        s = '%sshapes = [\n' % (s)
        for shape in this.shapeElements:
            s = '%s    %s,\n' % (s, repr(shape))
        s = '%s  ],\n  ' % s
        s = '%snFold = "%s",\n' % (s, this.nFold)
        s = '%smFold = "%s",\n' % (s, this.mFold)
        s = '%sname = "%s"\n' % (s, this.mFold)
        s = '%s)\n' % (s)
        if __name__ != '__main__':
            s = '%s.%s' % (__name__, s)
        return s

    def glDraw(this):
        if this.updateShape:
            this.setV()
        Geom3D.CompoundShape.glDraw(this)

    def setEdgeAlternative(this, alt = None, oppositeAlt = None):
        if alt is not None:
            this.edgeAlternative = alt
        if oppositeAlt is not None:
            this.oppEdgeAlternative = oppositeAlt
        this.updateShape = True

    def setFoldMethod(this, method):
        this.foldHeptagon = method
        this.updateShape = True

    def setRotateFold(this, step):
        this.rotateFold = step
        this.updateShape = True

    def setDihedralAngle(this, angle):
        this.dihedralAngle = angle
        this.updateShape = True

    def setPosAngle(this, angle):
        this.posAngle = angle
        this.updateShape = True

    def setTriangleFillPosition(this, position):
        print("WARNING: implement in derived class")

    def setFold1(this, angle = None, oppositeAngle = None):
        if angle is not None:
            this.fold1 = angle
        if oppositeAngle is not None:
            this.oppFold1 = oppositeAngle
        this.updateShape = True

    def setFold2(this, angle = None, oppositeAngle = None):
        if angle is not None:
            this.fold2 = angle
        if oppositeAngle is not None:
            this.oppFold2 = oppositeAngle
        this.updateShape = True

    def setHeight(this, height):
        this.height = height
        this.updateShape = True

    def edgeColor(this):
        glColor(0.5, 0.5, 0.5)

    def vertColor(this):
        glColor(0.7, 0.5, 0.5)

    def getStatusStr(this):
        return 'T = %02.2f, Angle = %01.2f rad, fold1 = %01.2f (%01.2f) rad, fold2 = %01.2f (%01.2f) rad' % (
                this.height,
                this.dihedralAngle,
                this.fold1, this.oppFold1,
                this.fold2, this.oppFold2
            )

    def getReflPosAngle(this):
        # meant to be implemented by child
        if this.edgeAlternative == TrisAlt.refl_1:
            return 0
        else:
            return this.posAngleMax

    def posHeptagon(this):
        this.heptagon.fold(this.fold1, this.fold2, this.oppFold1, this.oppFold2,
            keepV0 = False, fold = this.foldHeptagon, rotate = this.rotateFold)
        this.heptagon.translate(H * geomtypes.UY)
        # Note: the rotation angle != the dihedral angle
        this.heptagon.rotate(
            -geomtypes.UX, geomtypes.QUARTER_TURN - this.dihedralAngle)
        this.heptagon.translate(this.height*geomtypes.UZ)
        if this.posAngle != 0:
            this.heptagon.rotate(-geomtypes.UZ, this.posAngle)

    def setV(this):
        this.posHeptagon()

class FldHeptagonCtrlWin(wx.Frame):
    refl_min_size = (525, 425)
    rot_min_size = (545, 600)
    def __init__(this,
            shape, canvas,
            maxHeight,
            prePosStrLst,
            symmetryBase,
            trisAlts,
            stringify,
            parent,
            *args, **kwargs
    ):
        """Create a control window for the scene that folds heptagons

        shape: the Geom3D shape object that is shown
        canvas: wx canvas to be used
        maxHeight: max translation height to be used for the heptagon
        prePosStrLst: string list that expresses which special positions can be
                      found, e.g. where all holes disappear.
        trisAlts: an array consisting of TrisAlt_base derived objects. Each
                  element in the array expresses which triangle fills are valid
                  for the position with the same index as the element.
        stringify: hash table that maps enums on strings.
        *args: standard wx Frame *args
        **kwargs: standard wx Frame **kwargs
        """
        # TODO assert (type(shape) == type(RegHeptagonShape()))
        wx.Frame.__init__(this, parent, *args, **kwargs)
        this.parent = parent
        this.shape = shape
        this.trisAlts = trisAlts
        this.nr_of_positions = len(trisAlts)
        this.setTriangleFillPosition(0)
        this.canvas = canvas
        this.maxHeight = maxHeight
        this.prePosStrLst = prePosStrLst
        this.symBase = symmetryBase
        this.stringify = stringify
        if not open_file in stringify:
                this.stringify[open_file] = "From File"
        this.panel = wx.Panel(this, -1)
        this.statusBar = this.CreateStatusBar()
        this.foldMethod = foldMethod.triangle
        this.restoreTris = False
        this.restoreO3s = False
        this.shape.foldHeptagon = this.foldMethod
        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
        this.specPosIndex = 0

        this.mainSizer.Add(
                this.createControlsSizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.set_default_size(this.refl_min_size)
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()
        this.prevTrisFill    = -1
        this.prevOppTrisFill = -1

    def createControlsSizer(this):
        this.heightF = 40 # slider step factor, or: 1 / slider step

        this.Guis = []

        # static adjustments
        this.trisFillGui = wx.Choice(this.panel,
                style = wx.RA_VERTICAL,
                choices = []
            )
        this.Guis.append(this.trisFillGui)
        this.trisFillGui.Bind(wx.EVT_CHOICE, this.onTriangleFill)
        this.setEnableTrisFillItems()

        this.trisPosGui = wx.Choice(this.panel,
                style = wx.RA_VERTICAL,
                choices = [
                    'Position {}'.format(i + 1)
                    for i in range(this.nr_of_positions)])
        this.Guis.append(this.trisPosGui)
        this.trisPosGui.Bind(wx.EVT_CHOICE, this.onTrisPosition)
        this.setEnableTrisFillItems()

        this.reflGui = wx.CheckBox(this.panel, label = 'Reflections Required')
        this.Guis.append(this.reflGui)
        this.reflGui.SetValue(this.shape.inclReflections)
        this.reflGui.Bind(wx.EVT_CHECKBOX, this.onRefl)

        this.rotateFldGui = wx.Button(this.panel, label = 'Rotate Fold 1/7')
        this.rotateFld = 0
        this.Guis.append(this.rotateFldGui)
        this.rotateFldGui.Bind(wx.EVT_BUTTON, this.onRotateFld)

        # View Settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        this.applySymGui = wx.CheckBox(this.panel, label = 'Apply Symmetry')
        this.Guis.append(this.applySymGui)
        this.applySymGui.SetValue(this.shape.applySymmetry)
        this.applySymGui.Bind(wx.EVT_CHECKBOX, this.onApplySym)
        this.addTrisGui = wx.CheckBox(this.panel, label = 'Show Triangles')
        this.Guis.append(this.addTrisGui)
        this.addTrisGui.SetValue(this.shape.addXtraFs)
        this.addTrisGui.Bind(wx.EVT_CHECKBOX, this.onAddTriangles)

        # static adjustments
        l = this.foldMethodList = [
            FoldName[foldMethod.parallel],
            FoldName[foldMethod.triangle],
            FoldName[foldMethod.star],
            FoldName[foldMethod.w],
            FoldName[foldMethod.trapezium],
        ]
        this.foldMethodListItems = [
            foldMethod.get(l[i]) for i in range(len(l))
        ]
        this.foldMethodGui = wx.RadioBox(this.panel,
                label = 'Heptagon Fold Method',
                style = wx.RA_VERTICAL,
                choices = this.foldMethodList
            )
        for i in range(len(this.foldMethodList)):
            if (this.foldMethodList[i] == FoldName[this.foldMethod]):
                this.foldMethodGui.SetSelection(i)
        this.Guis.append(this.foldMethodGui)
        this.foldMethodGui.Bind(wx.EVT_RADIOBOX, this.onFoldMethod)

        # predefined positions
        this.prePosGui = wx.Choice(this.panel,
                #label = 'Only Regular Faces with:',
                style = wx.RA_VERTICAL,
                choices = this.prePosStrLst
            )
        # Don't hardcode which index is dyn_pos, I might reorder the item list
        # one time, and will probably forget to update the default selection..
        for i in range(len(this.prePosStrLst)):
            if (this.prePosStrLst[i] == this.stringify[dyn_pos]):
                this.prePosGui.SetStringSelection(this.stringify[dyn_pos])
                break
        this.setEnablePrePosItems()
        this.Guis.append(this.prePosGui)
        this.prePosGui.Bind(wx.EVT_CHOICE, this.onPrePos)

        this.openFileButton = wx.Button(this.panel, label = 'Open File')
        this.firstButton    = wx.Button(this.panel, label = 'First')
        this.nextButton     = wx.Button(this.panel, label = 'Next')
        this.nrTxt          = wx.Button(this.panel, label = '---',  style=wx.NO_BORDER)
        this.prevButton     = wx.Button(this.panel, label = 'Prev')
        this.lastButton     = wx.Button(this.panel, label = 'Last')
        this.Guis.append(this.openFileButton)
        this.Guis.append(this.firstButton)
        this.Guis.append(this.nextButton)
        this.Guis.append(this.nrTxt)
        this.Guis.append(this.prevButton)
        this.Guis.append(this.lastButton)
        this.openFileButton.Bind(wx.EVT_BUTTON, this.onOpenFile)
        this.firstButton.Bind(wx.EVT_BUTTON, this.onFirst)
        this.nextButton.Bind(wx.EVT_BUTTON, this.onNext)
        this.prevButton.Bind(wx.EVT_BUTTON, this.onPrev)
        this.lastButton.Bind(wx.EVT_BUTTON, this.onLast)

        # dynamic adjustments
        this.posAngleGui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.posAngle,
                minValue = Geom3D.Rad2Deg * this.shape.posAngleMin,
                maxValue = Geom3D.Rad2Deg * this.shape.posAngleMax,
                style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.posAngleGui)
        this.posAngleGui.Bind(wx.EVT_SLIDER, this.onPosAngle)
        this.minFoldAngle = -180
        this.maxFoldAngle =  180
        this.dihedralAngleGui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.dihedralAngle,
                minValue = this.minFoldAngle,
                maxValue = this.maxFoldAngle,
                style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.dihedralAngleGui)
        this.dihedralAngleGui.Bind(wx.EVT_SLIDER, this.onDihedralAngle)
        this.fold1Gui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.fold1,
                minValue = this.minFoldAngle,
                maxValue = this.maxFoldAngle,
                style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.fold1Gui)
        this.fold1Gui.Bind(wx.EVT_SLIDER, this.onFold1)
        this.fold2Gui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.fold2,
                minValue = this.minFoldAngle,
                maxValue = this.maxFoldAngle,
                style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.fold2Gui)
        this.fold2Gui.Bind(wx.EVT_SLIDER, this.onFold2)
        this.fold1OppGui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.oppFold1,
                minValue = this.minFoldAngle,
                maxValue = this.maxFoldAngle,
                style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.fold1OppGui)
        this.fold1OppGui.Bind(wx.EVT_SLIDER, this.onFold1Opp)
        this.fold2OppGui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.oppFold2,
                minValue = this.minFoldAngle,
                maxValue = this.maxFoldAngle,
                style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.fold2OppGui)
        this.fold2OppGui.Bind(wx.EVT_SLIDER, this.onFold2Opp)
        this.heightGui = wx.Slider(
                this.panel,
                value = this.maxHeight - this.shape.height*this.heightF,
                minValue = -this.maxHeight * this.heightF,
                maxValue = this.maxHeight * this.heightF,
                style = wx.SL_VERTICAL
            )
        this.Guis.append(this.heightGui)
        this.heightGui.Bind(wx.EVT_SLIDER, this.onHeight)
        this.__guisNoReflEnabled = True
        if this.shape.inclReflections:
            this.disableGuisNoRefl()

        this.setOrientGui = wx.TextCtrl(
                this.panel
            )
        this.Guis.append(this.setOrientGui)
        this.setOrientButton  = wx.Button(this.panel, label = 'Apply')
        this.Guis.append(this.setOrientButton)
        this.setOrientButton.Bind(wx.EVT_BUTTON, this.onSetOrient)
        this.cleanOrientButton  = wx.Button(this.panel, label = 'Clean')
        this.Guis.append(this.cleanOrientButton)
        this.cleanOrientButton.Bind(wx.EVT_BUTTON, this.onCleanOrient)

        # Sizers
        this.Boxes = []

        # sizer with view settings
        this.Boxes.append(wx.StaticBox(this.panel, label = 'View Settings'))
        settingsSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        settingsSizer.Add(this.applySymGui, 0, wx.EXPAND)
        settingsSizer.Add(this.addTrisGui, 0, wx.EXPAND)
        settingsSizer.Add(this.reflGui, 0, wx.EXPAND)
        settingsSizer.Add(this.rotateFldGui, 0, wx.EXPAND)
        settingsSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        # The sizers holding the special positions
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Special Positions'))
        posSizerSubV = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        posSizerSubH = wx.BoxSizer(wx.HORIZONTAL)
        posSizerSubH.Add(this.openFileButton, 0, wx.EXPAND)
        posSizerSubH.Add(this.prePosGui, 0, wx.EXPAND)
        posSizerSubV.Add(posSizerSubH, 0, wx.EXPAND)
        posSizerSubH = wx.BoxSizer(wx.HORIZONTAL)
        posSizerSubH.Add(this.firstButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.prevButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.nrTxt, 1, wx.EXPAND)
        posSizerSubH.Add(this.nextButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.lastButton, 1, wx.EXPAND)
        posSizerSubV.Add(posSizerSubH, 0, wx.EXPAND)
        posSizerSubV.Add(wx.BoxSizer(), 1, wx.EXPAND)
        prePosSizerH = wx.BoxSizer(wx.HORIZONTAL)
        prePosSizerH.Add(posSizerSubV, 0, wx.EXPAND)
        prePosSizerH.Add(wx.BoxSizer(), 1, wx.EXPAND)

        # Alternatives of filling with triangles
        this.Boxes.append(wx.StaticBox(this.panel,
                                        label = 'Triangle Fill Alternative'))
        fillSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        fillSizer.Add(this.trisFillGui, 0, wx.EXPAND)
        fillSizer.Add(this.trisPosGui, 0, wx.EXPAND)

        statSizer = wx.BoxSizer(wx.HORIZONTAL)
        statSizer.Add(this.foldMethodGui, 0, wx.EXPAND)
        statSizer.Add(fillSizer, 0, wx.EXPAND)
        statSizer.Add(settingsSizer, 0, wx.EXPAND)
        statSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        posSizerH = wx.BoxSizer(wx.HORIZONTAL)
        # sizer holding the dynamic adjustments
        specPosDynamic = wx.BoxSizer(wx.VERTICAL)
        this.Boxes.append(wx.StaticBox(this.panel,
                                            label = 'Dihedral Angle (Degrees)'))
        angleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        angleSizer.Add(this.dihedralAngleGui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel,
                                            label = 'Fold 1 Angle (Degrees)'))
        fold1Sizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        fold1Sizer.Add(this.fold1Gui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel,
                                            label = 'Fold 2 Angle (Degrees)'))
        fold2Sizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        fold2Sizer.Add(this.fold2Gui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel,
                                        label = 'Positional Angle (Degrees)'))
        posAngleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        posAngleSizer.Add(this.posAngleGui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel,
                                    label = 'Opposite Fold 1 Angle (Degrees)'))
        oppFold1Sizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        oppFold1Sizer.Add(this.fold1OppGui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel,
                                    label = 'Opposite Fold 2 Angle (Degrees)'))
        oppFold2Sizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        oppFold2Sizer.Add(this.fold2OppGui, 1, wx.EXPAND)

        this.Boxes.append(wx.StaticBox(this.panel, label = 'Offset T'))
        heightSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        heightSizer.Add(this.heightGui, 1, wx.EXPAND)
        specPosDynamic.Add(angleSizer, 0, wx.EXPAND)
        specPosDynamic.Add(fold1Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(fold2Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(posAngleSizer, 0, wx.EXPAND)
        specPosDynamic.Add(oppFold1Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(oppFold2Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(wx.BoxSizer(), 1, wx.EXPAND)
        posSizerH.Add(specPosDynamic, 3, wx.EXPAND)
        posSizerH.Add(heightSizer, 1, wx.EXPAND)

        this.Boxes.append(wx.StaticBox(this.panel,
            label = 'Set Orientation Directly (specify array)'))
        setOrientSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        setOrientSizer.Add(this.setOrientGui, 1, wx.EXPAND)
        setOrientSizer.Add(this.setOrientButton, 0, wx.EXPAND)
        setOrientSizer.Add(this.cleanOrientButton, 0, wx.EXPAND)

        # MAIN sizer
        mainVSizer = wx.BoxSizer(wx.VERTICAL)
        mainVSizer.Add(statSizer, 0, wx.EXPAND)
        mainVSizer.Add(prePosSizerH, 0, wx.EXPAND)
        mainVSizer.Add(posSizerH, 0, wx.EXPAND)
        mainVSizer.Add(setOrientSizer, 0, wx.EXPAND)
        mainVSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(mainVSizer, 6, wx.EXPAND)

        this.errorStr = {
                'PosEdgeCfg': "ERROR: Impossible combination of position and edge configuration!"
            }

        return mainSizer

    def isPrePosValid(this, prePosId):
        if this.shape.inclReflections:
            psp = this.predefReflSpecPos
        else:
            psp = this.predefRotSpecPos
        return prePosId in psp

    def fileStrMapFoldMethodStr(this, filename):
        res = re.search("-fld_([^.]*)\.", filename)
        if res:
            return res.groups()[0]
        else:
            this.printFileStrMapWarning(filename, 'fileStrMapFoldMethodStr')

    def fileStrMapFoldPosStr(this, filename):
        res = re.search("-fld_[^.]*\.([0-6])-.*", filename)
        if res:
            return res.groups()[0]
        else:
            this.printFileStrMapWarning(filename, 'fileStrMapFoldPosStr')

    def fileStrMapHasReflections(this, filename):
        res = re.search(".*frh-roots-(.*)-fld_.*", filename)
        if res:
            pos_vals = res.groups()[0].split('_')
            nr_pos = len(pos_vals)
            return (nr_pos == 4) or (nr_pos == 5 and pos_vals[4] == '0')
        else:
            this.printFileStrMapWarning(filename, 'fileStrMapHasReflections')

    def fileStrMapTrisStr(this, filename):
        # New format: incl -pos:
        res = re.search("-fld_[^.]*\.[0-7]-([^.]*)\-pos-.*.py", filename)
        if res is None:
            # try old method:
            res = re.search("-fld_[^.]*\.[0-7]-([^.]*)\.py", filename)
        if res:
            tris_str = res.groups()[0]
            return this.trisAlt.mapFileStrOnStr[tris_str]
        else:
            this.printFileStrMapWarning(filename, 'fileStrMapTrisStr')

    def fileStrMapTrisPos(this, filename):
        res = re.search("-fld_[^.]*\.[0-7]-[^.]*-pos-([0-9]*)\.py", filename)
        if res:
            tris_pos = res.groups()[0]
            return int(tris_pos)
        else:
            # try old syntax:
            res = re.search("-fld_[^.]*\.[0-7]-([^.]*)\.py", filename)
            if res:
                return 0
            else:
                this.printFileStrMapWarning(filename, 'fileStrMapTrisPos')
                assert(False)

    def fileStrMapFoldPos(this, filename):
        res = re.search("-fld_[^.]*\.([0-7])-.*\.py", filename)
        if res:
            tris_pos = res.groups()[0]
            return int(tris_pos)
        else:
            return 0

    def setEnablePrePosItems(this):
        currentPrePos = this.prePos
        this.prePosGui.Clear()
        prePosStillValid = False
        for prePosStr in this.prePosStrLst:
            prePosId = this.mapPrePosStr(prePosStr)
            if this.isPrePosValid(prePosId):
                this.prePosGui.Append(prePosStr)
                if currentPrePos == prePosId:
                    prePosStillValid = True
            else:
                if prePosStr == this.stringify[dyn_pos]:
                    this.prePosGui.Append(prePosStr)
        if prePosStillValid:
            this.prePosGui.SetStringSelection(this.stringify[currentPrePos])
        else:
            this.prePosGui.SetStringSelection(this.stringify[dyn_pos])

    def rmControlsSizer(this):
        #print "rmControlsSizer"
        # The 'try' is necessary, since the boxes are destroyed in some OS,
        # while this is necessary for Ubuntu Hardy Heron.
        for Box in this.Boxes:
            try:
                Box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass
        for Gui in this.Guis:
            Gui.Destroy()

    def set_default_size(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

    def onPosAngle(this, event):
        this.shape.setPosAngle(Geom3D.Deg2Rad * this.posAngleGui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.updateShape()
        event.Skip()

    def onDihedralAngle(this, event):
        #print this.GetSize()
        this.shape.setDihedralAngle(
            Geom3D.Deg2Rad * this.dihedralAngleGui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.updateShape()
        event.Skip()

    def onFold1(this, event):
        val = this.fold1Gui.GetValue()
        s_val = Geom3D.Deg2Rad * val
        if this.shape.inclReflections:
            this.shape.setFold1(s_val, s_val)
        else:
            this.shape.setFold1(s_val)
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.updateShape()
        event.Skip()

    def onFold2(this, event):
        val = this.fold2Gui.GetValue()
        s_val = Geom3D.Deg2Rad * val
        if this.shape.inclReflections:
            this.shape.setFold2(s_val, s_val)
        else:
            this.shape.setFold2(s_val)
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.updateShape()
        event.Skip()

    def onFold1Opp(this, event):
        this.shape.setFold1(
            oppositeAngle = Geom3D.Deg2Rad * this.fold1OppGui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.updateShape()
        event.Skip()

    def onFold2Opp(this, event):
        this.shape.setFold2(
            oppositeAngle = Geom3D.Deg2Rad * this.fold2OppGui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.updateShape()
        event.Skip()

    def onHeight(this, event):
        this.shape.setHeight(float(this.maxHeight - this.heightGui.GetValue())/this.heightF)
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.updateShape()
        event.Skip()

    def onCleanOrient(this, event):
        this.setOrientGui.SetValue('')

    def onSetOrient(this, event):
        inputStr = 'ar = %s' % this.setOrientGui.GetValue()
        ed = {'__name__': 'inputStr'}
        try:
                exec(inputStr, ed)
        except SyntaxError:
                this.statusBar.SetStatusText('Syntax error in input string');
                raise
        tVal = ed['ar'][0]
        aVal = ed['ar'][1]
        fld1 = ed['ar'][2]
        fld2 = ed['ar'][3]
        this.heightGui.SetValue(this.maxHeight - this.heightF * tVal)
        this.dihedralAngleGui.SetValue(Geom3D.Rad2Deg * aVal)
        this.fold1Gui.SetValue(Geom3D.Rad2Deg * fld1)
        this.fold2Gui.SetValue(Geom3D.Rad2Deg * fld2)
        inclRefl = len(ed['ar']) <= 5
        this.shape.inclReflections = inclRefl
        this.reflGui.SetValue(inclRefl)
        if not inclRefl:
            this.enableGuisNoRefl()
            posVal = ed['ar'][4]
            oppFld1 = ed['ar'][5]
            oppFld2 = ed['ar'][6]
            this.fold1OppGui.SetValue(Geom3D.Rad2Deg * oppFld1)
            this.fold2OppGui.SetValue(Geom3D.Rad2Deg * oppFld2)
            this.posAngleGui.SetValue(Geom3D.Rad2Deg * posVal)
            this.shape.setPosAngle(posVal)
        else:
            this.disableGuisNoRefl()
            this.setReflPosAngle()
            oppFld1 = fld1
            oppFld2 = fld2
        this.shape.setDihedralAngle(aVal)
        this.shape.setHeight(tVal)
        this.shape.setFold1(fld1, oppFld1)
        this.shape.setFold2(fld2, oppFld2)
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.updateShape()
        event.Skip()

    def onApplySym(this, event):
        this.shape.applySymmetry = this.applySymGui.IsChecked()
        this.shape.updateShape = True
        this.updateShape()

    def onAddTriangles(this, event):
        this.shape.addXtraFs = this.addTrisGui.IsChecked()
        this.shape.updateShape = True
        this.updateShape()

    def allignFoldSlideBarsWithFoldMethod(this):
        if not this.shape.inclReflections:
            if this.foldMethod == FoldMethod.parallel:
                this.fold1OppGui.Disable()
                this.fold2OppGui.Disable()
            elif (this.foldMethod == FoldMethod.w or
                this.foldMethod == FoldMethod.star
            ):
                this.fold1OppGui.Enable()
                this.fold2OppGui.Enable()
            elif (this.foldMethod == FoldMethod.trapezium or
                this.foldMethod == FoldMethod.triangle
            ):
                this.fold1OppGui.Disable()
                this.fold2OppGui.Enable()

    def setReflPosAngle(this):
        posAngle = this.shape.getReflPosAngle()
        this.shape.setPosAngle(posAngle)
        this.posAngleGui.SetValue(Geom3D.Rad2Deg * posAngle)

    def disableSlidersNoRefl(this):
        this.fold1OppGui.Disable()
        this.fold2OppGui.Disable()
        this.posAngleGui.Disable()
        # the code below is added to be able to check and uncheck "Has
        # Reflections" in a "undo" kind of way.
        this.__sav_oppFld1 = this.shape.oppFold1
        this.__sav_oppFld2 = this.shape.oppFold2
        this.__sav_posAngle = this.shape.posAngle
        this.shape.setFold1(oppositeAngle = this.shape.fold1)
        this.shape.setFold2(oppositeAngle = this.shape.fold2)
        this.setReflPosAngle()
        this.fold1OppGui.SetValue(this.minFoldAngle)
        this.fold2OppGui.SetValue(this.minFoldAngle)

    def enableSlidersNoRefl(this, restore = True):
        this.allignFoldSlideBarsWithFoldMethod()
        this.posAngleGui.Enable()
        # the code below is added to be able to check and uncheck "Has
        # Reflections" in a "undo" kind of way.
        if restore:
            this.shape.setFold1(oppositeAngle = this.__sav_oppFld1)
            this.shape.setFold2(oppositeAngle = this.__sav_oppFld2)
            this.shape.setPosAngle(this.__sav_posAngle)
            this.fold1OppGui.SetValue(Geom3D.Rad2Deg * this.__sav_oppFld1)
            this.fold2OppGui.SetValue(Geom3D.Rad2Deg * this.__sav_oppFld2)
            this.posAngleGui.SetValue(Geom3D.Rad2Deg * this.__sav_posAngle)

    def disableGuisNoRefl(this):
        if this.__guisNoReflEnabled:
            this.setEnableTrisFillItems()
            this.trisPosGui.Disable()
            this.rotateFldGui.Disable()
            this.shape.setRotateFold(0)
            this.disableSlidersNoRefl()
            this.__guisNoReflEnabled = False

    def enableGuisNoRefl(this, restore = True):
        if not this.__guisNoReflEnabled:
            this.setEnableTrisFillItems()
            this.trisPosGui.Enable()
            this.rotateFldGui.Enable()
            this.shape.setRotateFold(this.rotateFld)
            this.enableSlidersNoRefl(restore)
            this.__guisNoReflEnabled = True

    def disableTrisFillGuis(this):
        this.addTrisGui.Disable()
        this.trisFillGui.Disable()

    def enableTrisFillGuis(this):
        this.addTrisGui.Enable()
        this.trisFillGui.Enable()

    def onRefl(this, event=None):
        this.shape.inclReflections = this.reflGui.IsChecked()
        this.shape.updateShape = True
        this.setEnablePrePosItems()
        if this.shape.inclReflections:
            this.set_default_size(this.refl_min_size)
        else:
            this.set_default_size(this.rot_min_size)
        if event is not None:
            if this.isPrePos():
                this.prePosGui.SetStringSelection(this.stringify[dyn_pos])
                if not this.shape.inclReflections:
                    this.__sav_oppFld1 = this.shape.fold1
                    this.__sav_oppFld2 = this.shape.fold2
                this.onPrePos(event)
            else:
                if this.shape.inclReflections:
                    this.savTrisNoRefl = this.trisFillGui.GetStringSelection()
                    this.disableGuisNoRefl()
                else:
                    this.savTrisRefl = this.trisFillGui.GetStringSelection()
                    this.enableGuisNoRefl()
                this.statusBar.SetStatusText(this.shape.getStatusStr())
                this.updateShape()

    def setRotateFld(this, rotateFld):
        this.rotateFld = int(rotateFld) % 7
        this.shape.setRotateFold(this.rotateFld)
        this.rotateFldGui.SetLabel('Rotate Fold %d/7' % (this.rotateFld + 1))
        this.updateShape()

    def onRotateFld(this, event):
        this.setRotateFld(this.rotateFld + 1)

    def isPrePos(this):
        # TODO: move to offspring
        # FIXME TODO the string 'Enable Sliders' should be a constant and be
        # imported and used in the Scenes.. (or move to offspring..)
        return this.prePosGui.GetStringSelection() != 'Enable Sliders'

    def saveTrisFillItem(this):
        currentChoice = this.trisAlt.key[this.trisFillGui.GetStringSelection()]
        if this.trisAlt.isBaseKey(currentChoice):
            this.__sav_reflTrisFill = currentChoice
        else:
            this.__sav_rotTrisFill = currentChoice

    def setTriangleFillPosition(this, position):
        """Sets which triangle fills are valid for the current settings

        Note that you have to call setEnableTrisFillItems to apply these
        settings to the GUI.

        position: an index in this.trisAlts
        """
        if position < 0:
            position = 0
        if position >= this.nr_of_positions:
            position = this.nr_of_positions - 1
        this.position = position
        this.trisAlt = this.trisAlts[this.position]
        this.shape.setTriangleFillPosition(position)

    def setEnableTrisFillItems(this, itemList = None):
        # first time fails
        try:
            currentChoice = this.trisAlt.key[this.trisFillGui.GetStringSelection()]
        except KeyError:
            currentChoice = this.trisAlt.strip_I
        if itemList is None:
            itemList = this.trisAlt.choiceList
            if this.shape.inclReflections:
                isValid = lambda c: this.trisAlt.isBaseKey(this.trisAlt.key[c])
                if not this.trisAlt.isBaseKey(currentChoice):
                    try:
                        currentChoice = this.trisAlt.key[this.savTrisRefl]
                    except AttributeError:
                        # TODO: use the first one that is valid
                        currentChoice = this.trisAlt.strip_I
            else:
                def isValid (c):
                    c_key = this.trisAlt.key[c]
                    if this.trisAlt.isBaseKey(c_key) or isinstance(c_key, int):
                        return False
                    else:
                        return True
                if not isValid(this.trisAlt.stringify[currentChoice]):
                    try:
                        currentChoice = this.trisAlt.key[this.savTrisNoRefl]
                    except AttributeError:
                        # TODO: use the first one that is valid
                        currentChoice = this.trisAlt.strip_I_strip_I
        else:
            isValid = lambda c: True
        this.trisFillGui.Clear()
        currentStillValid = False
        for choice in itemList:
            if isValid(choice):
                this.trisFillGui.Append(choice)
                if currentChoice == this.trisAlt.key[choice]:
                    currentStillValid = True
                lastValid = choice

        if currentStillValid:
            this.trisFillGui.SetStringSelection(this.trisAlt.stringify[currentChoice])
        else:
            try:
                this.trisFillGui.SetStringSelection(lastValid)
            except UnboundLocalError:
                # None are valid...
                return
        this.shape.setEdgeAlternative(this.trisFill, this.oppTrisFill)

    @property
    def trisFill(this):
        s = this.trisFillGui.GetStringSelection()
        if s == '':
            return None
        t = this.trisAlt.key[s]
        if this.shape.inclReflections:
            return t
        else:
            return t[0]

    @property
    def oppTrisFill(this):
        t = this.trisAlt.key[this.trisFillGui.GetStringSelection()]
        if this.shape.inclReflections:
            return t
        else:
            return t[1]

    def nvidea_workaround_0(this):
        this.prevTrisFill    = this.shape.edgeAlternative
        this.prevOppTrisFill = this.shape.oppEdgeAlternative

    def nvidea_workaround(this):
        restoreMyShape = (
            this.prevTrisFill == this.trisAlt.twist_strip_I and
            this.prevOppTrisFill == this.trisAlt.twist_strip_I and
            this.trisFill != this.trisAlt.twist_strip_I and
            this.oppTrisFill != this.trisAlt.twist_strip_I
        )
        changeMyShape = (
            this.trisFill == this.trisAlt.twist_strip_I and
            this.oppTrisFill == this.trisAlt.twist_strip_I
        )
        if changeMyShape:
            if (
                this.prevTrisFill != this.trisAlt.twist_strip_I and
                this.prevOppTrisFill != this.trisAlt.twist_strip_I
            ):
                print('---------nvidia-seg-fault-work-around-----------')
                this.nvidea_workaround_0()
                this.restoreShape = this.canvas.shape
            this.shape.setV() # make sure the shape is updated
            shape =  FldHeptagonShape(this.shape.shapes,
                this.shape.nFold, this.shape.mFold,
                name = this.shape.name
            )
            shape.altNFoldFace = this.shape.altNFoldFace
            shape.altMFoldFace = this.shape.altMFoldFace
            shape.heptagon = this.shape.heptagon
            shape.dihedralAngle = this.shape.dihedralAngle
            shape.posAngleMin = this.shape.posAngleMin
            shape.posAngleMax = this.shape.posAngleMax
            shape.posAngle = this.shape.posAngle
            shape.inclReflections = this.shape.inclReflections
            shape.rotateFold = this.shape.rotateFold
            shape.fold1 = this.shape.fold1
            shape.fold2 = this.shape.fold2
            shape.oppFold1 = this.shape.oppFold1
            shape.oppFold2 = this.shape.oppFold2
            shape.foldHeptagon = this.shape.foldHeptagon
            shape.height = this.shape.height
            shape.applySymmetry = this.shape.applySymmetry
            shape.addXtraFs = this.shape.addXtraFs
            shape.onlyRegFs = this.shape.onlyRegFs
            shape.useCulling = this.shape.useCulling
            shape.edgeAlternative = this.trisFill
            shape.oppEdgeAlternative = this.oppTrisFill
            shape.updateShape = True
            this.canvas.shape = shape
        elif restoreMyShape:
            this.parent.panel.shape = this.shape

    def updateShape(this):
        this.nvidea_workaround()
        this.canvas.paint()

    def onTriangleFill(this, event = None):
        this.nvidea_workaround_0()
        this.shape.setEdgeAlternative(this.trisFill, this.oppTrisFill)
        if event is not None:
            if this.isPrePos():
                this.onPrePos(event)
            else:
                if this.shape.inclReflections:
                    this.setReflPosAngle()
                this.statusBar.SetStatusText(this.shape.getStatusStr())
            this.updateShape()

    @property
    def tris_position(this):
        # Note these are called "Position <int>"
        selected = this.trisPosGui.GetSelection()
        # If nothing selected (after changing from having reflections)
        if selected < 0:
            selected = 0
        return selected

    @tris_position.setter
    def tris_position(this, value):
        this.trisPosGui.SetSelection(value)
        this.onTrisPosition()

    def onTrisPosition(this, event=None):
        this.setTriangleFillPosition(this.tris_position)
        this.setEnableTrisFillItems()
        this.updateShape()

    def onFoldMethod(this, event = None):
        this.foldMethod = this.foldMethodListItems[
                this.foldMethodGui.GetSelection()
            ]
        this.shape.setFoldMethod(this.foldMethod)
        this.allignFoldSlideBarsWithFoldMethod()
        if event is not None:
            if this.isPrePos():
                this.onPrePos(event)
            else:
                this.statusBar.SetStatusText(this.shape.getStatusStr())
            this.updateShape()

    def onFirst(this, event = None):
        this.specPosIndex = 0
        this.onPrePos()

    def onLast(this, event = None):
        this.specPosIndex = -1
        this.onPrePos()

    def mapPrePosStr(this, s):
        try:
            return this.__prePosStr2Key[s]
        except AttributeError:
            this.__prePosStr2Key = {}
            for k, v in this.stringify.items():
                this.__prePosStr2Key[v] = k
            return this.__prePosStr2Key[s]
        except KeyError:
            # Happens when switching from Open File to Only Hepts e.g.
            return -1

    @property
    def prePos(this):
        return this.mapPrePosStr(this.prePosGui.GetStringSelection())

    def openPrePosFile(this, filename):
        try:
            print('DBG open', filename)
            fd = open(filename, 'r')
        except IOError:
            print('DBG file not found:\n %s' % filename)
            return []
        ed = {'__name__': 'readPyFile'}
        exec(fd.read(), ed)
        fd.close()
        return ed['results']

    def noPrePosFound(this):
        s = 'Note: no valid positions found'
        print(s)
        this.statusBar.SetStatusText(s)

    @property
    def stdPrePos(this):
        try:
            return this.sav_stdPrePos
        except AttributeError:
            prePosId = this.prePos
            assert prePosId != dyn_pos
            if prePosId == open_file:
                filename = this.prePosFileName
                if filename is None:
                    return []
                this.sav_stdPrePos = this.openPrePosFile(filename)
                return this.sav_stdPrePos
            else:
                # use correct predefined special positions
                if this.shape.inclReflections:
                    psp = this.predefReflSpecPos
                else:
                    psp = this.predefRotSpecPos
                # Oops not good for performance:
                # TODO only return correct one en add length func
                this.sav_stdPrePos = [sp['set'] for sp in psp[this.prePos]]
                return this.sav_stdPrePos

    def onPrev(this, event = None):
        if this.stdPrePos != []:
            if this.specPosIndex > 0:
                this.specPosIndex -= 1
            elif this.specPosIndex == -1:
                this.specPosIndex = len(this.stdPrePos) - 2
            # else prePosId == 0 : first one selected don't scroll around
            this.onPrePos()
        else:
            this.noPrePosFound()

    def onNext(this, event = None):
        if this.stdPrePos != []:
            try:
                maxI = len(this.stdPrePos) - 1
                if this.specPosIndex >= 0:
                    if this.specPosIndex < maxI - 1:
                        this.specPosIndex += 1
                    else:
                        this.specPosIndex = -1 # select last
            except KeyError:
                pass
            this.onPrePos()
        else:
            this.noPrePosFound()

    def showOnlyHepts(this):
        return this.prePos == only_hepts

    def showOnlyO3Tris(this):
        return this.prePos == only_xtra_o3s

    def chooseOpenFile(this):
        filename = None
        dlg = wx.FileDialog(this, 'New: Choose a file',
                this.rDir, '', '*.py', wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
        dlg.Destroy()
        return filename

    def onOpenFile(this, e):
        filename = this.chooseOpenFile()
        if filename is None:
            return
        this.prePosFileName = filename
        this.foldMethodGui.SetStringSelection(
            this.fileStrMapFoldMethodStr(this.prePosFileName))
        this.onFoldMethod()
        this.setRotateFld(this.fileStrMapFoldPosStr(this.prePosFileName))
        # Note: Reflections need to be set before triangle fill, otherwise the
        # right triangle fills are not available
        has_reflections = this.fileStrMapHasReflections(this.prePosFileName)
        this.reflGui.SetValue(has_reflections)
        this.onRefl()
        # not needed: this.shape.updateShape = True
        this.setEnableTrisFillItems()
        this.trisFillGui.SetStringSelection(
            this.fileStrMapTrisStr(this.prePosFileName))
        this.onTriangleFill()
        this.tris_position = this.fileStrMapTrisPos(this.prePosFileName)
        # it's essential that prePosGui is set to dynamic be4 stdPrePos is read
        # otherwise something else than dynamic might be read...
        openFileStr = this.stringify[open_file]
        if not openFileStr in this.prePosGui.GetItems():
                this.prePosGui.Append(openFileStr)
        this.prePosGui.SetStringSelection(openFileStr)
        this.resetStdPrePos()
        this.onPrePos()

    def updateShapeSettings(this, setting):
        if setting == []:
            return
        else:
            if this.specPosIndex >= len(setting):
                this.specPosIndex = len(setting) - 1
            tVal = setting[this.specPosIndex][0]
            aVal = setting[this.specPosIndex][1]
            fld1 = setting[this.specPosIndex][2]
            fld2 = setting[this.specPosIndex][3]
            vStr = '[tVal, aVal, fld1, fld2'
            dbgStr = '  [%.12f, %.12f, %.12f, %.12f' % (
                                                tVal, aVal, fld1, fld2)
            if len(setting[this.specPosIndex]) > 4:
                posVal = setting[this.specPosIndex][4]
            else:
                posVal = 0
            if len(setting[this.specPosIndex]) > 5:
                oppFld1 = setting[this.specPosIndex][5]
                oppFld2 = setting[this.specPosIndex][6]
                vStr = '%s, posVal, oppFld1, oppFld2] =' % vStr
                dbgStr = '%s, %.12f, %.12f, %.12f]' % (
                                    dbgStr, posVal, oppFld1, oppFld2)
            else:
                oppFld1 = fld1
                oppFld2 = fld2
                vStr = '%s] =' % vStr
                dbgStr = '%s]' % dbgStr
            print(vStr)
            print(dbgStr)
            print('----------------------------------------------------')
            # Ensure this.specPosIndex in range:
        nrPos = len(setting)
        maxI = nrPos - 1
        if (this.specPosIndex > maxI):
            this.specPosIndex = maxI
        # keep -1 (last) so switching triangle alternative will keep
        # last selection.
        elif (this.specPosIndex < -1):
            this.specPosIndex = maxI - 1
        this.shape.setDihedralAngle(aVal)
        this.shape.setHeight(tVal)
        this.shape.setFold1(fld1, oppFld1)
        this.shape.setFold2(fld2, oppFld2)
        this.shape.setPosAngle(posVal)
        # For the user: start counting with '1' instead of '0'
        if this.specPosIndex == -1:
            nr = nrPos # last position
        else:
            nr = this.specPosIndex + 1
        # set nr of possible positions
        this.nrTxt.SetLabel('%d/%d' % (nr, nrPos))
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        #this.shape.printTrisAngles()

    def resetStdPrePos(this):
        try:
            del this.sav_stdPrePos
        except AttributeError:
            pass

    tNone = 1.0
    aNone = 0.0
    fld1None = 0.0
    fld2None = 0.0
    def onPrePos(this, event = None):
        c = this.shape
        # remove the "From File" from the pull down list as soon as it is
        # deselected
        if event is not None and this.prePos != open_file:
            openFileStr = this.stringify[open_file]
            n = this.prePosGui.FindString(openFileStr)
            if n >= 0:
                # deleting will reset the selection, so save and reselect:
                selStr = this.prePosGui.GetSelection()
                this.prePosGui.Delete(this.prePosGui.FindString(openFileStr))
                this.prePosGui.SetSelection(selStr)
        if this.prePos == dyn_pos:
            if event is not None:
                this.prePosFileName = None
            if (this.restoreTris):
                this.restoreTris = False
                this.shape.addXtraFs = this.addTrisGui.IsChecked()
                this.shape.updateShape = True
            if (this.restoreO3s):
                this.restoreO3s = False
                this.shape.onlyRegFs = False
                this.shape.updateShape = True
            this.nrTxt.SetLabel('---')
        elif this.prePos != open_file:
            # this block is run for predefined spec pos only:
            if (this.showOnlyHepts()):
                this.shape.addXtraFs = False
                this.restoreTris = True
            elif (this.restoreTris):
                this.restoreTris = False
                this.shape.addXtraFs = this.addTrisGui.IsChecked()
            if (this.showOnlyO3Tris()):
                this.shape.onlyRegFs = True
                this.restoreO3s = True
            elif (this.restoreO3s):
                this.restoreO3s = False
                this.shape.onlyRegFs = False
#           try:
#           except AttributeError:
#               print 'DBG key eror for trisFill: "%s"' % this.trisFillGui.GetStringSelection()
#               pass

            # get fold, tris alt
            sps = this.specPosSetup
            this.foldMethodGui.SetStringSelection(FoldName[sps['7fold']])
            this.trisFillGui.SetStringSelection(this.trisAlt.stringify[sps['tris']])
            try:
                this.tris_position = sps['tris-pos']
            except KeyError:
                this.tris_position = 0
            try:
                rotateFold = sps['fold-rot']
            except KeyError:
                rotateFold = 0
            this.setRotateFld(rotateFold)

            this.onFoldMethod()
            this.onTriangleFill()

            for gui in [
                this.dihedralAngleGui, this.posAngleGui,
                this.heightGui,
                this.fold1Gui, this.fold2Gui,
                this.fold1OppGui, this.fold2OppGui
            ]:
                gui.SetValue(0)
                gui.Disable()
            if not this.shape.inclReflections:
                this.enableGuisNoRefl()
            else:
                this.disableGuisNoRefl()
        if this.prePos != dyn_pos:
            if event is not None:
                this.resetStdPrePos()
            setting = this.stdPrePos
            if setting == []:
                this.noPrePosFound()
                return
            # Note if the setting array uses a none symmetric setting, then the
            # shape will not be symmetric. This is not supposed to be handled
            # here: don't overdo it!
            this.updateShapeSettings(setting)
        # for open_file it is important that updateShapeSettins is done before
        # updating the sliders...
        if this.prePos == dyn_pos or this.prePos == open_file:
            for gui in [
                this.dihedralAngleGui, this.posAngleGui,
                this.heightGui,
                this.fold1Gui, this.fold2Gui,
                this.fold1OppGui, this.fold2OppGui
            ]:
                gui.Enable()
            this.dihedralAngleGui.SetValue(Geom3D.Rad2Deg * c.dihedralAngle)
            this.posAngleGui.SetValue(Geom3D.Rad2Deg * c.posAngle)
            val1 = Geom3D.Rad2Deg * c.fold1
            val2 = Geom3D.Rad2Deg * c.fold2
            this.fold1Gui.SetValue(val1)
            this.fold2Gui.SetValue(val2)
            val1 = Geom3D.Rad2Deg * c.oppFold1
            val2 = Geom3D.Rad2Deg * c.oppFold2
            this.fold1OppGui.SetValue(val1)
            this.fold2OppGui.SetValue(val2)
            if not this.shape.inclReflections:
                this.enableGuisNoRefl(restore = False)
            this.heightGui.SetValue(
                this.maxHeight - this.heightF * c.height)
            this.setEnableTrisFillItems()
        this.updateShape()

class EqlHeptagonShape(Geom3D.IsometricShape):
    def __init__(this,
        directIsometries = [geomtypes.E],
        oppositeIsometry = None,
        name = 'EqlHeptagonShape'
    ):
        Geom3D.IsometricShape.__init__(this,
            Vs = [],
            Fs = [],
            #Es = [],
            #colors = [()]
            directIsometries = directIsometries,
            oppositeIsometry = oppositeIsometry,
            unfoldOrbit = True,
            name = name)
        this.showKite      = True
        this.showHepta     = False
        this.addFaces      = True
        this.heptPosAlt    = False
        this.cullingOn     = False
        this.showXtra      = False
        this.triangleAlt   = True
        this.addXtraEdge   = True
        this.errorStr      = ''
        this.opaqueness    = 1.0

        kiteColor          = rgb.oliveDrab[:]
        heptColor          = rgb.oliveDrab[:]
        xtraColor          = rgb.brown[:]
        this.theColors     = [heptColor, kiteColor, xtraColor]

    def setV(this):
        """
        Set the vertex array, implemented by derivative
        """
        pass

    def setH(this, h):
        this.h = h
        this.setV()

    def setAngle(this, a):
        this.angle = a
        this.setV()

    def setViewSettings(this,
            addFaces      = None,
            showKite      = None,
            showHepta     = None,
            showXtra      = None,
            triangleAlt   = None,
            addXtraEdge   = None,
            heptPosAlt    = None,
            cullingOn     = None,
            edgeR         = None,
            vertexR       = None,
            opaqueness    = None
        ):
        if addFaces is not None:
            this.setFaceProperties(drawFaces = addFaces)
        if showKite is not None:
            this.showKite = showKite
        if showHepta is not None:
            this.showHepta = showHepta
        if showXtra is not None:
            this.showXtra = showXtra
        if heptPosAlt is not None:
            this.heptPosAlt = heptPosAlt
        if triangleAlt is not None:
            this.triangleAlt = triangleAlt
            this.updateV = True
        if addXtraEdge is not None:
            this.addXtraEdge = addXtraEdge
        if cullingOn is not None:
            if cullingOn:
                glEnable(GL_CULL_FACE)
            else:
                glDisable(GL_CULL_FACE)
        if edgeR is not None:
            this.setEdgeProperties(radius = edgeR, drawEdges = True)
        if vertexR is not None:
            this.setVertexProperties(radius = vertexR)
        if opaqueness is not None:
            # TODO...
            this.opaqueness = opaqueness
        if (
            showKite is not None  # not so efficient perhaps, but works..
            or
            showHepta is not None  # not so efficient perhaps, but works..
            or
            showXtra is not None  # not so efficient perhaps, but works..
            or
            heptPosAlt is not None
            or
            addXtraEdge is not None
        ):
            this.setV()


    def glInit(this):
        Geom3D.IsometricShape.glInit(this)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def getStatusStr(this):
        if this.errorStr == '':
          floatFmt = '%02.2f'
          fmtStr   = 'H = %s, Angle = %s degrees' % (floatFmt, floatFmt)
          s        = fmtStr % (this.h, this.angle)
          return s
        else:
          return this.errorStr

class EqlHeptagonCtrlWin(wx.Frame):
    def __init__(this, shape, canvas, size, *args, **kwargs):
        assert isinstance(shape, EqlHeptagonShape)
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
        this.set_default_size(size)
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()

    def setKiteAngleExtremes(this, min, max, steps = 100):
        # Linear mapping of [0, this.kiteAngleSteps] ->
        #                   [min, max]
        #
        # min: minimal angle in degrees
        # max: maximum angle in degrees
        # steps: the amount of steps in the slider.
        # y = x * (max - min)/this.kiteAngleSteps + min
        this.kiteAngleSteps = steps
        this.kiteAngleFactor = (max - min) / steps
        this.kiteAngleOffset = min
        # inverse:
        # x = ( y - min ) /  this.kiteAngleFactor

    def Slider2Angle(this, x):
        # angle in degrees
        return this.kiteAngleFactor * float(x) + this.kiteAngleOffset

    def Angle2Slider(this, y):
        # angle in degrees
        return (y - this.kiteAngleOffset) / this.kiteAngleFactor

    def createControlsSizer(this):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # GUI for dynamic adjustment
        this.kiteAngleGui = wx.Slider(
                this.panel,
                value = this.Angle2Slider(this.shape.angle),
                minValue = 0,
                maxValue = this.kiteAngleSteps,
                style = wx.SL_HORIZONTAL
            )
        this.panel.Bind(
            wx.EVT_SLIDER, this.onKiteAngleAdjust, id = this.kiteAngleGui.GetId()
        )
        this.kiteAngleBox = wx.StaticBox(this.panel, label = 'Kite Angle')
        this.kiteAngleSizer = wx.StaticBoxSizer(this.kiteAngleBox, wx.HORIZONTAL)
        this.kiteAngleSizer.Add(this.kiteAngleGui, 1, wx.EXPAND)
        this.statusBar.SetStatusText(this.shape.getStatusStr())

        # GUI for general view settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        this.showKiteChk = wx.CheckBox(this.panel, label = 'Show Kite')
        this.showKiteChk.SetValue(this.shape.showKite)
        this.showHeptaChk = wx.CheckBox(this.panel, label = 'Show Heptagon')
        this.showHeptaChk.SetValue(this.shape.showHepta)
        this.showXtraChk = wx.CheckBox(this.panel, label = 'Show Extra Faces')
        this.showXtraChk.SetValue(this.shape.showXtra)
        this.altHeptPosChk = wx.CheckBox(this.panel, label = 'Use Alternative Heptagon Position')
        this.altHeptPosChk.SetValue(this.shape.heptPosAlt)
        this.triangleAltChk = wx.CheckBox(this.panel, label = 'Triangle Alternative')
        this.triangleAltChk.SetValue(this.shape.triangleAlt)
        this.addXtraEdgeChk = wx.CheckBox(this.panel, label = 'Add Extra Edge')
        this.addXtraEdgeChk.SetValue(this.shape.addXtraEdge)
        this.cullingChk = wx.CheckBox(this.panel, label = 'Draw one sided polygon')
        this.cullingChk.SetValue(this.shape.cullingOn)
        this.panel.Bind(wx.EVT_CHECKBOX, this.onViewSettingsChk)
        this.viewSettingsBox = wx.StaticBox(this.panel, label = 'View Settings')
        this.viewSettingsSizer = wx.StaticBoxSizer(this.viewSettingsBox, wx.VERTICAL)

        this.viewSettingsSizer.Add(this.showKiteChk, 1, wx.EXPAND)
        this.viewSettingsSizer.Add(this.showHeptaChk, 1, wx.EXPAND)
        this.viewSettingsSizer.Add(this.showXtraChk, 1, wx.EXPAND)
        this.viewSettingsSizer.Add(this.altHeptPosChk, 1, wx.EXPAND)
        this.viewSettingsSizer.Add(this.triangleAltChk, 1, wx.EXPAND)
        this.viewSettingsSizer.Add(this.addXtraEdgeChk, 1, wx.EXPAND)
        this.viewSettingsSizer.Add(this.cullingChk, 1, wx.EXPAND)

        this.rowSubSizer = wx.BoxSizer(wx.VERTICAL)
        this.rowSubSizer.Add(this.viewSettingsSizer, 1, wx.EXPAND)

        this.columnSubSizer = wx.BoxSizer(wx.HORIZONTAL)
        this.columnSubSizer.Add(this.rowSubSizer, 2, wx.EXPAND)

        mainSizer.Add(this.kiteAngleSizer, 4, wx.EXPAND)
        mainSizer.Add(this.columnSubSizer, 20, wx.EXPAND)
        try:
            this.addSpecialPositions(this.panel, mainSizer)
        except AttributeError: pass

        return mainSizer

    def setNoPrePos(this):
        #sel = this.prePosSelect.SetSelection(0)
        this.prePosSelected = False

    def onKiteAngleAdjust(this, event):
        #print 'size =', this.dynDlg.GetClientSize()
        this.setNoPrePos()
        this.shape.setAngle(this.Slider2Angle(this.kiteAngleGui.GetValue()))
        this.canvas.paint()
        try:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        except AttributeError: pass
        event.Skip()

    def onViewSettingsChk(this, event = None):
        showKite      = this.showKiteChk.IsChecked()
        showHepta     = this.showHeptaChk.IsChecked()
        showXtra      = this.showXtraChk.IsChecked()
        altHeptPos    = this.altHeptPosChk.IsChecked()
        triangleAlt   = this.triangleAltChk.IsChecked()
        addXtraEdge   = this.addXtraEdgeChk.IsChecked()
        cullingOn     = this.cullingChk.IsChecked()
        this.shape.setViewSettings(
                showKite      = showKite,
                showHepta     = showHepta,
                showXtra      = showXtra,
                heptPosAlt    = altHeptPos,
                triangleAlt   = triangleAlt,
                addXtraEdge   = addXtraEdge,
                cullingOn     = cullingOn
            )
        this.canvas.paint()
        try:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        except AttributeError: pass

    # move to general class
    def set_default_size(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)


