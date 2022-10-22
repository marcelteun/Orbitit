#!/usr/bin/python3
"""Module with widgets and shapes to support defining polyhedra consisting of heptagons.

E.g. equilateral heptagons derived from kites or folded regular heptagons.
"""
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
# -----------------------------------------------------------------
# Old sins:
# pylint: disable=too-many-lines,too-many-arguments,too-many-locals
# pylint: disable=too-many-instance-attributes,too-many-branches
# pylint: disable=too-many-statements,too-many-public-methods

from enum import Enum
import json
import logging
import math
import re
import wx

from OpenGL.GL import glColor, glBlendFunc
from OpenGL.GL import GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA

from orbitit import Geom3D, geomtypes, rgb
from orbitit.geomtypes import Rot3 as Rot
from orbitit.geomtypes import Vec3 as Vec

V3 = math.sqrt(3)

HEPT_DENOM = math.sin(math.pi / 7)
HEPT_RHO_NUM = math.sin(2 * math.pi / 7)
HEPT_SIGMA_NUM = math.sin(3 * math.pi / 7)
HEPT_RHO = HEPT_RHO_NUM / HEPT_DENOM
HEPT_SIGMA = HEPT_SIGMA_NUM / HEPT_DENOM
HEPT_HEIGHT = (1 + HEPT_SIGMA + HEPT_RHO) * HEPT_DENOM

ONLY_HEPTS = -1
DYN_POS = -2
OPEN_FILE = -3
ONLY_XTRA_O3S = -4
ALL_EQ_TRIS = -5
NO_O3_TRIS = -6

tris_fill_base = 0

alt_bit = 8
loose_bit = 16
rot_bit = 32
twist_bit = 64
TRIS_OFFSET = 128


class Tris_counter:
    def __init__(self):
        self.reset(TRIS_OFFSET)

    def reset(self, v):
        self.counter = v

    def pp(self):
        i = self.counter
        self.counter += 1
        return i


class TrisAlt_base(object):
    # Note nrs should be different from below
    refl_1 = 0
    strip_I = 1
    strip_II = 2
    star = 3
    refl_2 = 4
    crossed_2 = 5
    strip_1_loose = strip_I | loose_bit
    star_1_loose = star | loose_bit
    alt_strip_I = strip_I | alt_bit
    alt_strip_II = strip_II | alt_bit
    alt_strip_1_loose = strip_I | loose_bit | alt_bit
    rot_strip_1_loose = strip_I | loose_bit | rot_bit
    arot_strip_1_loose = strip_I | loose_bit | alt_bit | rot_bit
    rot_star_1_loose = star | loose_bit | rot_bit
    arot_star_1_loose = star | loose_bit | alt_bit | rot_bit
    rot_strip_I = strip_I | rot_bit
    rot_star = star | rot_bit
    arot_strip_I = strip_I | alt_bit | rot_bit
    arot_star = star | alt_bit | rot_bit
    # TODO: this is a new position really
    # TODO: rename to refl2 for S4A4
    # TODO: rename to some 1 - loose variant for A4
    twist_strip_I = strip_I | twist_bit

    stringify = {
        refl_1: "refl 1",
        refl_2: "refl 2",
        crossed_2: "crossed",
        strip_1_loose: "strip 1 Loose",
        strip_I: "strip I",
        strip_II: "strip II",
        star: "shell",
        star_1_loose: "shell 1 loose",
        alt_strip_I: "alt. strip I",
        alt_strip_II: "alt. strip II",
        alt_strip_1_loose: "alt. strip 1 loose",
        twist_strip_I: "twisted",
        rot_strip_1_loose: "rot. strip 1 loose",
        rot_star_1_loose: "rot. shell 1 loose",
        arot_strip_1_loose: "alt. rot. strip 1 loose",
        arot_star_1_loose: "alt. rot. shell 1 loose",
        rot_strip_I: "rot. strip I",
        rot_star: "rot. shell",
        arot_strip_I: "alt. rot. strip I",
        arot_star: "alt. rot. shell",
    }

    class_key = {
        "refl_1": refl_1,
        "refl_2": refl_2,
        "crossed_2": crossed_2,
        "strip_I": strip_I,
        "strip_II": strip_II,
        "star": star,
        "strip_1_loose": strip_1_loose,
        "star_1_loose": star_1_loose,
        "alt_strip_I": alt_strip_I,
        "alt_strip_II": alt_strip_II,
        "alt_strip_1_loose": alt_strip_1_loose,
        "twist_strip_I": twist_strip_I,
        "rot_strip_1_loose": rot_strip_1_loose,
        "rot_star_1_loose": rot_star_1_loose,
        "arot_strip_1_loose": arot_strip_1_loose,
        "arot_star_1_loose": arot_star_1_loose,
        "rot_strip_I": rot_strip_I,
        "rot_star": rot_star,
        "arot_strip_I": arot_strip_I,
        "arot_star": arot_star,
    }

    key = {
        stringify[refl_1]: refl_1,
        stringify[refl_2]: refl_2,
        stringify[crossed_2]: crossed_2,
        stringify[strip_I]: strip_I,
        stringify[strip_II]: strip_II,
        stringify[star]: star,
        stringify[strip_1_loose]: strip_1_loose,
        stringify[star_1_loose]: star_1_loose,
        stringify[alt_strip_I]: alt_strip_I,
        stringify[alt_strip_II]: alt_strip_II,
        stringify[alt_strip_1_loose]: alt_strip_1_loose,
        stringify[twist_strip_I]: twist_strip_I,
        stringify[rot_strip_1_loose]: rot_strip_1_loose,
        stringify[rot_star_1_loose]: rot_star_1_loose,
        stringify[arot_strip_1_loose]: arot_strip_1_loose,
        stringify[arot_star_1_loose]: arot_star_1_loose,
        stringify[rot_strip_I]: rot_strip_I,
        stringify[rot_star]: rot_star,
        stringify[arot_strip_I]: arot_strip_I,
        stringify[arot_star]: arot_star,
    }

    def isBaseKey(self, k):
        try:
            return self.baseKey[k]
        except KeyError:
            return False

    def toFileStr(self, tId=None, tStr=None):
        assert tId is not None or tStr is not None
        if tId is None:
            tId = self.key[tStr]
        if not isinstance(tId, int):
            tStr0 = self.stringify[tId[0]]
            tStr1 = self.stringify[tId[1]]
            tStr = "%s-opp_%s" % (tStr0, tStr1)
        elif tStr is None:
            tStr = self.stringify[tId]

        t = "_".join(tStr.split()).lower().replace("ernative", "")
        t = t.replace("_ii", "_II")
        t = t.replace("_i", "_I")
        t = t.replace("alt.", "alt")
        t = t.replace("rot.", "rot")
        return t

    baseKey = {}

    def __init__(self):
        # TODO? Note that only s that aren't primitives (isinstance(x, int))
        # should be added here.
        self.choiceList = [s for s in self.stringify.values()]
        self.mapKeyOnFileStr = {}
        self.mapStrOnFileStr = {}
        self.mapFileStrOnStr = {}
        self.mapFileStrOnKey = {}
        for (tStr, tId) in self.key.items():
            fileStr = self.toFileStr(tStr=tStr)
            self.mapKeyOnFileStr[tId] = fileStr
            self.mapStrOnFileStr[tStr] = fileStr
            self.mapFileStrOnStr[fileStr] = tStr
            self.mapFileStrOnKey[fileStr] = tId


def toTrisAltKeyStr(tId=None, tStr=None):
    assert tId is not None or tStr is not None
    if tId is None:
        tId = TrisAlt_base.key[tStr]
    if not isinstance(tId, int):
        if tId[0] & loose_bit and tId[1] & loose_bit:
            tStr = "{}_1loose_{}".format(
                TrisAlt_base.stringify[tId[0] & ~loose_bit],
                TrisAlt_base.stringify[tId[1] & ~loose_bit],
            )
        elif tId[0] & loose_bit:
            tStr = "{}__{}".format(
                TrisAlt_base.stringify[tId[0]],
                TrisAlt_base.stringify[tId[1]],
            )
        # TODO: remove share under new position
        elif (
                tId[0] == TrisAlt_base.twist_strip_I
                and tId[1] == TrisAlt_base.twist_strip_I
        ):
            tStr = "twist_strip_I_strip_I"
        else:
            tStr = "%s_%s" % (
                TrisAlt_base.stringify[tId[0]],
                TrisAlt_base.stringify[tId[1]],
            )
    elif tStr is None:
        tStr = TrisAlt_base.stringify[tId]
    t = "_".join(tStr.split())
    t = t.replace("_ii", "_II")
    t = t.replace("_i", "_I")
    t = t.replace("alt._rot.", "arot")
    t = t.replace("rot.", "rot")
    t = t.replace("alt.", "alt")
    return t


class Meta_TrisAlt(type):
    def __init__(cls, classname, bases, classdict):
        type.__init__(cls, classname, bases, classdict)


def define_tris_alt(name, tris_keys):
    """Define a class containing a set of triangle fill alternatives."""
    class_dict = {"mixed": False, "stringify": {}, "key": {}, "baseKey": {}}
    # Always add all primitives:
    for (k, s) in TrisAlt_base.stringify.items():
        class_dict["stringify"][k] = s
        class_dict["key"][s] = k
        class_dict[toTrisAltKeyStr(k)] = k
    for k in tris_keys:
        if isinstance(k, int):
            class_dict["baseKey"][k] = True
        else:
            # must be a tuple of 2
            assert len(k) == 2, "Exptected 2 tuple, got: %s." % k
            if k[0] & loose_bit and k[1] & loose_bit:
                s = "%s - 1 loose - %s" % (
                    TrisAlt_base.stringify[k[0] & ~loose_bit],
                    TrisAlt_base.stringify[k[1] & ~loose_bit],
                )
            elif (
                    k[0] == TrisAlt_base.twist_strip_I
                    and k[1] == TrisAlt_base.twist_strip_I
            ):
                s = "strip I - twisted - strip I"
            else:
                s = "%s - %s" % (
                    TrisAlt_base.stringify[k[0]],
                    TrisAlt_base.stringify[k[1]],
                )
            class_dict["stringify"][k] = s
            class_dict["key"][s] = k
            class_dict[toTrisAltKeyStr(k)] = k
    return Meta_TrisAlt(name, (TrisAlt_base,), class_dict)


TrisAlt = define_tris_alt(
    "TrisAlt",
    [
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
    ],
)


class FoldMethod(Enum):
    """
    Enum class to distinguish the different heptagon folds

    Note: The folds only use a capital in the beginning, since the string representation is used in
    the GUI and this way there is no need to convert the strings back and forth.

    Attributes:
        PARALLEL: a fold with one reflection symmetry with two parallel diagonals
        TRAPEZIUM: a fold with one reflection symmetry with 3 folds using three shortes diagonals
        W: a fold with one reflection symmetry with in a W shape using 2 shortest and 2 longest
           diagonals.
        TRIANGLE: a fold with one reflection symmetry using two shortest and one longest diagonal
            where the diagonals form a triangle
        SHELL: a fold with one reflection symmetry using two shortest and two longest diagonals all
            from one vertex.
        G: a non-symmetric 4-fold with two short and two long diagonals. It is a triangle fold with
            one fold over a short edge added.
        MIXED: a non-symmetric 4-fold with two short and two long diagonals, which is a combination
            of a W and a Shell fold. It can be obtained from either by switching a fold over a short
            diagonal
    """

    PARALLEL = 0
    TRAPEZIUM = 1
    W = 2
    TRIANGLE = 3
    SHELL = 4
    G = 5
    MIXED = 6

    @classmethod
    def get(cls, s):
        """Get the enum value for a fold name."""
        for v in cls:
            if v.name == s:
                return v
        s = str.upper(s)
        for v in cls:
            if v.name == s:
                return v
        return None


class RegularHeptagon:
    def __init__(self):
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
        self.VsOrg = [
            Vec([0.0, 0.0, 0.0]),
            Vec([HEPT_RHO / 2, -HEPT_DENOM, 0.0]),
            Vec([HEPT_SIGMA / 2, -(1 + HEPT_SIGMA) * HEPT_DENOM, 0.0]),
            Vec([0.5, -HEPT_HEIGHT, 0.0]),
            Vec([-0.5, -HEPT_HEIGHT, 0.0]),
            Vec([-HEPT_SIGMA / 2, -(1 + HEPT_SIGMA) * HEPT_DENOM, 0.0]),
            Vec([-HEPT_RHO / 2, -HEPT_DENOM, 0.0]),
        ]
        self.Vs = self.VsOrg[:]  # the vertex aray to use.
        self.Fs = [[6, 5, 4, 3, 2, 1, 0]]
        self.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0]

    def fold(
            self,
            a0,
            b0,
            a1=None,
            b1=None,
            keepV0=True,
            fold=FoldMethod.PARALLEL,
            rotate=0,
    ):
        method = {
            FoldMethod.PARALLEL: self.fold_parallel,
            FoldMethod.TRAPEZIUM: self.fold_trapezium,
            FoldMethod.W: self.fold_w,
            FoldMethod.TRIANGLE: self.fold_triangle,
            FoldMethod.SHELL: self.fold_shell,
            FoldMethod.MIXED: self.fold_mixed,
            FoldMethod.G: self.fold_g,
        }
        method[fold](a0, b0, a1, b1, keepV0, rotate)

    def fold_parallel(self, a, b, _=None, __=None, keepV0=True, rotate=0):
        if rotate == 0:
            self.fold_parallel_0(a, b, keepV0)
        else:
            self.fold_parallel_1(a, b, keepV0)

    def fold_parallel_0(self, a, b, keepV0=True):
        """
        Fold around the 2 parallel diagonals V1-V6 and V2-V5.

        The fold angle a refers the axis V2-V5 and
        the fold angle b refers the axis V1-V6.
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
        self.Fs = [[0, 6, 1], [1, 6, 5, 2], [2, 5, 4, 3]]
        self.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0, 1, 6, 2, 5]
        cosa = math.cos(a)
        sina = math.sin(a)
        cosb = math.cos(b)
        sinb = math.sin(b)
        if keepV0:
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
            #   self. V[0]   V[1]    V[2]    V[3]
            dV2 = [
                self.VsOrg[2][1] - self.VsOrg[1][1],
                self.VsOrg[2][2] - self.VsOrg[1][2],
            ]
            V2 = Vec(
                [
                    self.VsOrg[2][0],
                    self.VsOrg[1][1] + cosa * dV2[0] - sina * dV2[1],
                    self.VsOrg[1][2] + cosa * dV2[1] + sina * dV2[0],
                ]
            )
            # Similarly:
            dV3_ = [
                self.VsOrg[3][1] - self.VsOrg[1][1],
                self.VsOrg[3][2] - self.VsOrg[1][2],
            ]
            V3_ = [
                self.VsOrg[1][1] + cosa * dV3_[0] - sina * dV3_[1],
                self.VsOrg[1][2] + cosa * dV3_[1] + sina * dV3_[0],
            ]
            # now rotate beta:
            dV3 = [V3_[0] - V2[1], V3_[1] - V2[2]]
            V3 = Vec(
                [
                    self.VsOrg[3][0],
                    V2[1] + cosb * dV3[0] - sinb * dV3[1],
                    V2[2] + cosb * dV3[1] + sinb * dV3[0],
                ]
            )
            self.Vs = [
                self.VsOrg[0],
                self.VsOrg[1],
                V2,
                V3,
                Vec([-V3[0], V3[1], V3[2]]),
                Vec([-V2[0], V2[1], V2[2]]),
                self.VsOrg[6],
            ]
        else:
            # similar to before, except the roles of the vertices are switched
            # i.e. keep V[3] constant...
            dV1 = [
                self.VsOrg[1][1] - self.VsOrg[2][1],
                self.VsOrg[1][2] - self.VsOrg[2][2],
            ]
            V1 = Vec(
                [
                    self.VsOrg[1][0],
                    self.VsOrg[2][1] + cosa * dV1[0] - sina * dV1[1],
                    self.VsOrg[2][2] + cosa * dV1[1] + sina * dV1[0],
                ]
            )
            # Similarly:
            dV0_ = [
                self.VsOrg[0][1] - self.VsOrg[2][1],
                self.VsOrg[0][2] - self.VsOrg[2][2],
            ]
            V0_ = [
                self.VsOrg[2][1] + cosa * dV0_[0] - sina * dV0_[1],
                self.VsOrg[2][2] + cosa * dV0_[1] + sina * dV0_[0],
            ]
            # now rotate beta:
            dV0 = [V0_[0] - V1[1], V0_[1] - V1[2]]
            V0 = Vec(
                [
                    self.VsOrg[0][0],
                    V1[1] + cosb * dV0[0] - sinb * dV0[1],
                    V1[2] + cosb * dV0[1] + sinb * dV0[0],
                ]
            )
            self.Vs = [
                V0,
                V1,
                self.VsOrg[2],
                self.VsOrg[3],
                self.VsOrg[4],
                self.VsOrg[5],
                Vec([-V1[0], V1[1], V1[2]]),
            ]

    def fold_parallel_1(self, a, b, keepV0=True):
        """
        Fold around the 2 parallel diagonals parallel to the edge opposite of
        vertex 1

        The fold angle a refers the axis V3-V6 and
        the fold angle b refers the axis V2-V0.
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
        self.Fs = [[1, 0, 2], [2, 0, 6, 3], [3, 6, 5, 4]]
        self.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0, 2, 0, 3, 6]
        if keepV0:
            assert False, "TODO"
        else:
            v3v6 = (self.VsOrg[3] + self.VsOrg[6]) / 2
            v3v6_axis = Vec(self.VsOrg[3] - self.VsOrg[6])
            v0v2 = (self.VsOrg[0] + self.VsOrg[2]) / 2
            rot_a = Rot(axis=v3v6_axis, angle=a)
            v0v2_ = v3v6 + rot_a * (v0v2 - v3v6)
            V0 = v0v2_ + (self.VsOrg[0] - v0v2)
            V2 = v0v2_ + (self.VsOrg[2] - v0v2)
            V1_ = v3v6 + rot_a * (self.VsOrg[1] - v3v6)

            v0v2_axis = Vec(V2 - V0)
            rot_b = Rot(axis=v0v2_axis, angle=b)
            V1 = v0v2 + rot_b * (V1_ - v0v2)
            self.Vs = [
                V0,
                V1,
                V2,
                self.VsOrg[3],
                self.VsOrg[4],
                self.VsOrg[5],
                self.VsOrg[6],
            ]

    def fold_trapezium(self, a, b0, _=None, b1=None, keepV0=True, rotate=0):
        """
        Fold around 4 diagonals in the shape of a trapezium (trapezoid)

        The fold angle a refers the axis V1-V6 and
        The fold angle b refers the axes V1-V3 and V6-V4 and
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
        self.Fs = [[0, 6, 1], [1, 3, 2], [1, 6, 4, 3], [4, 6, 5]]
        self.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0, 4, 6, 6, 1, 1, 3]
        cosa = math.cos(a)
        sina = math.sin(a)
        if keepV0:
            # see fold_parallel
            dV2_ = [
                self.VsOrg[2][1] - self.VsOrg[1][1],
                self.VsOrg[2][2] - self.VsOrg[1][2],
            ]
            V2_ = Vec(
                [
                    self.VsOrg[2][0],
                    self.VsOrg[1][1] + cosa * dV2_[0] - sina * dV2_[1],
                    self.VsOrg[1][2] + cosa * dV2_[1] + sina * dV2_[0],
                ]
            )
            dV3 = [
                self.VsOrg[3][1] - self.VsOrg[1][1],
                self.VsOrg[3][2] - self.VsOrg[1][2],
            ]
            V3 = Vec(
                [
                    self.VsOrg[3][0],
                    self.VsOrg[1][1] + cosa * dV3[0] - sina * dV3[1],
                    self.VsOrg[1][2] + cosa * dV3[1] + sina * dV3[0],
                ]
            )
            V4 = Vec([-V3[0], V3[1], V3[2]])
            v1v3 = (self.VsOrg[1] + V3) / 2
            v1v3_axis = Vec(V3 - self.VsOrg[1])
            r = Rot(axis=v1v3_axis, angle=b0)
            V2 = v1v3 + r * (V2_ - v1v3)
            if not Geom3D.eq(b0, b1):
                V5 = Vec([-V2[0], V2[1], V2[2]])
            else:
                v4v6 = (V4 + self.VsOrg[6]) / 2
                v4v6_axis = Vec(self.VsOrg[6] - V4)
                r = Rot(axis=v4v6_axis, angle=b1)
                V5_ = Vec([-V2_[0], V2_[1], V2_[2]])
                V5 = v4v6 + r * (V5_ - v4v6)
            self.Vs = [self.VsOrg[0], self.VsOrg[1], V2, V3, V4, V5, self.VsOrg[6]]
        else:
            dV0 = [
                self.VsOrg[0][1] - self.VsOrg[1][1],
                self.VsOrg[0][2] - self.VsOrg[1][2],
            ]
            V0 = Vec(
                [
                    self.VsOrg[0][0],
                    self.VsOrg[1][1] + cosa * dV0[0] - sina * dV0[1],
                    self.VsOrg[1][2] + cosa * dV0[1] + sina * dV0[0],
                ]
            )
            v1v3 = (self.VsOrg[1] + self.VsOrg[3]) / 2
            v1v3_axis = Vec(self.VsOrg[3] - self.VsOrg[1])
            r = Rot(axis=v1v3_axis, angle=b0)
            V2 = v1v3 + r * (self.VsOrg[2] - v1v3)
            if Geom3D.eq(b0, b1):
                V5 = Vec([-V2[0], V2[1], V2[2]])
            else:
                v4v6 = (self.VsOrg[4] + self.VsOrg[6]) / 2
                v4v6_axis = Vec(self.VsOrg[6] - self.VsOrg[4])
                r = Rot(axis=v4v6_axis, angle=b1)
                V5 = v4v6 + r * (self.VsOrg[5] - v4v6)
            self.Vs = [
                V0,
                self.VsOrg[1],
                V2,
                self.VsOrg[3],
                self.VsOrg[4],
                V5,
                self.VsOrg[6],
            ]

    def fold_triangle(self, a, b0, _=None, b1=None, keepV0=True, rotate=0):
        """
        Fold around 3 triangular diagonals from V0.

        The fold angle a refers the axes V0-V2 and V0-V5 and
        the fold angle b refers the axis V2-V5.
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
        self.Fs = [[0, 2, 1], [0, 5, 2], [0, 6, 5], [2, 5, 4, 3]]
        self.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0, 0, 2, 2, 5, 5, 0]
        Rot0_2 = Rot(axis=self.VsOrg[2] - self.VsOrg[0], angle=b0)
        V1 = Rot0_2 * self.VsOrg[1]
        if Geom3D.eq(b0, b1):
            V6 = Vec([-V1[0], V1[1], V1[2]])
        else:
            Rot5_0 = Rot(axis=self.VsOrg[0] - self.VsOrg[5], angle=b1)
            V6 = Rot5_0 * self.VsOrg[6]
        V2 = self.VsOrg[2]
        if keepV0:
            Rot5_2 = Rot(axis=self.VsOrg[5] - self.VsOrg[2], angle=a)
            V3 = Rot5_2 * (self.VsOrg[3] - V2) + V2
            self.Vs = [
                self.VsOrg[0],
                V1,
                self.VsOrg[2],
                V3,
                Vec([-V3[0], V3[1], V3[2]]),
                self.VsOrg[5],
                V6,
            ]
        else:
            Rot2_5 = Rot(axis=self.VsOrg[2] - self.VsOrg[5], angle=a)
            V0 = Rot2_5 * (self.VsOrg[0] - V2) + V2
            V1 = Rot2_5 * (V1 - V2) + V2
            V6 = Rot2_5 * (V6 - V2) + V2
            self.Vs = [
                V0,
                V1,
                self.VsOrg[2],
                self.VsOrg[3],
                self.VsOrg[4],
                self.VsOrg[5],
                V6,
            ]

    def fold_shell(self, a0, b0, a1, b1, keepV0=True, rotate=0):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a refers the axes V0-V2 and V0-V5 and
        the fold angle b0 refers the axes V0-V3 and V0-V4.
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

        prj = [
            self.fold_shell_0,
            self.fold_shell_1,
            self.fold_shell_2,
            self.fold_shell_3,
            self.fold_shell_4,
            self.fold_shell_5,
            self.fold_shell_6,
        ]
        prj[rotate](a0, b0, a1, b1, keepV0)

    def fold_shell_es_fs(self, no):
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
            i[0],
            i[1],
            i[1],
            i[2],
            i[2],
            i[3],
            i[3],
            i[4],
            i[4],
            i[5],
            i[5],
            i[6],
            i[6],
            i[0],
            i[0],
            i[2],
            i[0],
            i[3],
            i[0],
            i[4],
            i[0],
            i[5],
        ]

    def fold_shell_0(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a refers the axes V0-V2 and V0-V5 and
        the fold angle b0 refers the axes V0-V3 and V0-V4.
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
        self.fold_shell_es_fs(0)
        self.fold_shell_0_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_shell_0_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_shell_0, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot a0
            v0v3 = (v[0] + v[3]) / 2
            v0v3_axis = Vec(v[0] - v[3])
            rot_a0 = Rot(axis=v0v3_axis, angle=-a0)
            # middle of V1-V2 which is // to v0v3 axis
            v1v2 = (v[1] + v[2]) / 2
            v1v2_ = v0v3 + rot_a0 * (v1v2 - v0v3)
            v[1] = v1v2_ + (v[1] - v1v2)
            v[2] = v1v2_ + (v[2] - v1v2)

            # rot b0
            v0v2 = (v[0] + v[2]) / 2
            v0v2_axis = Vec(v[0] - v[2])
            rot_b0 = Rot(axis=v0v2_axis, angle=-b0)
            v[1] = v0v2 + rot_b0 * (v[1] - v0v2)

            # rot a1
            v0v4 = (v[0] + v[4]) / 2
            v0v4_axis = Vec(v[0] - v[4])
            rot_a1 = Rot(axis=v0v4_axis, angle=a1)
            # middle of V6-V5 which is // to v1v4 axis
            v6v5 = (v[6] + v[5]) / 2
            v6v5_ = v0v4 + rot_a1 * (v6v5 - v0v4)
            v[6] = v6v5_ + (v[6] - v6v5)
            v[5] = v6v5_ + (v[5] - v6v5)

            # rot b1
            v0v5 = (v[0] + v[5]) / 2
            v0v5_axis = Vec(v[0] - v[5])
            rot_b1 = Rot(axis=v0v5_axis, angle=b1)
            v[6] = v0v5 + rot_b1 * (v[6] - v0v5)

        self.Vs = v

    def fold_shell_1(self, a0, b0, a1, b1, keepV0=True):
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
        self.fold_shell_es_fs(1)
        self.fold_shell_1_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_shell_1_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_shell_1, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b0
            v1v3 = (v[1] + v[3]) / 2
            v1v3_axis = Vec(v[1] - v[3])
            # negative angle since left side rotates
            rot_b0 = Rot(axis=v1v3_axis, angle=-b0)
            v[2] = v1v3 + rot_b0 * (v[2] - v1v3)

            # rot a0
            v1v4 = (v[1] + v[4]) / 2
            v1v4_axis = Vec(v[1] - v[4])
            rot_a0 = Rot(axis=v1v4_axis, angle=a0)
            # middle of V0-V5 which is // to v1v4 axis
            v0v5 = (v[0] + v[5]) / 2
            v0v5_ = v1v4 + rot_a0 * (v0v5 - v1v4)
            v[0] = v0v5_ + (v[0] - v0v5)
            v[5] = v0v5_ + (v[5] - v0v5)
            v[6] = v1v4 + rot_a0 * (v[6] - v1v4)

            # rot a1
            v1v5 = (v[1] + v[5]) / 2
            v1v5_axis = Vec(v[1] - v[5])
            rot_a1 = Rot(axis=v1v5_axis, angle=a1)
            # middle of V0-V6 which is // to v1v4 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_ = v1v5 + rot_a1 * (v0v6 - v1v5)
            v[0] = v0v6_ + (v[0] - v0v6)
            v[6] = v0v6_ + (v[6] - v0v6)

            # rot b1
            v1v6 = (v[1] + v[6]) / 2
            v1v6_axis = Vec(v[1] - v[6])
            rot_b1 = Rot(axis=v1v6_axis, angle=b1)
            v[0] = v1v6 + rot_b1 * (v[0] - v1v6)

        self.Vs = v

    def fold_shell_2(self, a0, b0, a1, b1, keepV0=True):
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
        self.fold_shell_es_fs(2)
        self.fold_shell_2_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_shell_2_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_shell_2, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b0
            v2v4 = (v[2] + v[4]) / 2
            v2v4_axis = Vec(v[2] - v[4])
            rot_b0 = Rot(axis=v2v4_axis, angle=b0)
            # middle of V1-V5 which is // to v2v4 axis
            v1v5 = (v[1] + v[5]) / 2
            v1v5_ = v2v4 + rot_b0 * (v1v5 - v2v4)
            v[1] = v1v5_ + (v[1] - v1v5)
            v[5] = v1v5_ + (v[5] - v1v5)
            # middle of V0-V6 which is // to v2v4 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_ = v2v4 + rot_b0 * (v0v6 - v2v4)
            v[0] = v0v6_ + (v[0] - v0v6)
            v[6] = v0v6_ + (v[6] - v0v6)

            # rot a0
            v2v5 = (v[2] + v[5]) / 2
            v2v5_axis = Vec(v[2] - v[5])
            rot_a0 = Rot(axis=v2v5_axis, angle=a0)
            # middle of V1-V6 which is // to v2v5 axis
            v1v6 = (v[1] + v[6]) / 2
            v1v6_ = v2v5 + rot_a0 * (v1v6 - v2v5)
            v[1] = v1v6_ + (v[1] - v1v6)
            v[6] = v1v6_ + (v[6] - v1v6)
            v[0] = v2v5 + rot_a0 * (v[0] - v2v5)

            # rot a1
            v2v6 = (v[2] + v[6]) / 2
            v2v6_axis = Vec(v[2] - v[6])
            rot_a1 = Rot(axis=v2v6_axis, angle=a1)
            # middle of V0-V1 which is // to v2v6 axis
            v0v1 = (v[0] + v[1]) / 2
            v0v1_ = v2v6 + rot_a1 * (v0v1 - v2v6)
            v[0] = v0v1_ + (v[0] - v0v1)
            v[1] = v0v1_ + (v[1] - v0v1)

            # rot b1
            v2v0 = (v[2] + v[0]) / 2
            v2v0_axis = Vec(v[2] - v[0])
            rot_b1 = Rot(axis=v2v0_axis, angle=b1)
            v[1] = v2v0 + rot_b1 * (v[1] - v2v0)

        self.Vs = v

    def fold_shell_3(self, a0, b0, a1, b1, keepV0=True):
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
        self.fold_shell_es_fs(3)
        self.fold_shell_3_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_shell_3_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_shell_3, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b0
            v3v5 = (v[3] + v[5]) / 2
            v3v5_axis = Vec(v[3] - v[5])
            rot_b0 = Rot(axis=v3v5_axis, angle=b0)
            # middle of V2-V6 which is // to v3v5 axis
            v2v6 = (v[2] + v[6]) / 2
            v2v6_ = v3v5 + rot_b0 * (v2v6 - v3v5)
            v[2] = v2v6_ + (v[2] - v2v6)
            v[6] = v2v6_ + (v[6] - v2v6)
            # middle of V1-V0 which is // to v3v5 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_ = v3v5 + rot_b0 * (v1v0 - v3v5)
            v[1] = v1v0_ + (v[1] - v1v0)
            v[0] = v1v0_ + (v[0] - v1v0)

            # rot a0
            v3v6 = (v[3] + v[6]) / 2
            v3v6_axis = Vec(v[3] - v[6])
            rot_a0 = Rot(axis=v3v6_axis, angle=a0)
            # middle of V2-V0 which is // to v3v6 axis
            v2v0 = (v[2] + v[0]) / 2
            v2v0_ = v3v6 + rot_a0 * (v2v0 - v3v6)
            v[2] = v2v0_ + (v[2] - v2v0)
            v[0] = v2v0_ + (v[0] - v2v0)
            v[1] = v3v6 + rot_a0 * (v[1] - v3v6)

            # rot a1
            v3v0 = (v[3] + v[0]) / 2
            v3v0_axis = Vec(v[3] - v[0])
            rot_a1 = Rot(axis=v3v0_axis, angle=a1)
            # middle of V1-V2 which is // to v3v0 axis
            v1v2 = (v[1] + v[2]) / 2
            v1v2_ = v3v0 + rot_a1 * (v1v2 - v3v0)
            v[1] = v1v2_ + (v[1] - v1v2)
            v[2] = v1v2_ + (v[2] - v1v2)

            # rot b1
            v3v1 = (v[3] + v[1]) / 2
            v3v1_axis = Vec(v[3] - v[1])
            rot_b1 = Rot(axis=v3v1_axis, angle=b1)
            v[2] = v3v1 + rot_b1 * (v[2] - v3v1)

        self.Vs = v

    def fold_shell_4(self, a0, b0, a1, b1, keepV0=True):
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
        self.fold_shell_es_fs(4)
        self.fold_shell_4_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_shell_4_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_shell_3, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b1
            v4v2 = (v[4] + v[2]) / 2
            v4v2_axis = Vec(v[4] - v[2])
            rot_b1 = Rot(axis=v4v2_axis, angle=-b1)
            # middle of V5-V1 which is // to v4v2 axis
            v5v1 = (v[5] + v[1]) / 2
            v5v1_ = v4v2 + rot_b1 * (v5v1 - v4v2)
            v[5] = v5v1_ + (v[5] - v5v1)
            v[1] = v5v1_ + (v[1] - v5v1)
            # middle of V6-V0 which is // to v4v2 axis
            v6v0 = (v[6] + v[0]) / 2
            v6v0_ = v4v2 + rot_b1 * (v6v0 - v4v2)
            v[6] = v6v0_ + (v[6] - v6v0)
            v[0] = v6v0_ + (v[0] - v6v0)

            # rot a1
            v4v1 = (v[4] + v[1]) / 2
            v4v1_axis = Vec(v[4] - v[1])
            rot_a1 = Rot(axis=v4v1_axis, angle=-a1)
            # middle of V5-V0 which is // to v4v1 axis
            v5v0 = (v[5] + v[0]) / 2
            v5v0_ = v4v1 + rot_a1 * (v5v0 - v4v1)
            v[5] = v5v0_ + (v[5] - v5v0)
            v[0] = v5v0_ + (v[0] - v5v0)
            v[6] = v4v1 + rot_a1 * (v[6] - v4v1)

            # rot a0
            v4v0 = (v[4] + v[0]) / 2
            v4v0_axis = Vec(v[4] - v[0])
            rot_a0 = Rot(axis=v4v0_axis, angle=-a0)
            # middle of V5-V6 which is // to v4v0 axis
            v5v6 = (v[5] + v[6]) / 2
            v5v6_ = v4v0 + rot_a0 * (v5v6 - v4v0)
            v[5] = v5v6_ + (v[5] - v5v6)
            v[6] = v5v6_ + (v[6] - v5v6)

            # rot b0
            v4v6 = (v[4] + v[6]) / 2
            v4v6_axis = Vec(v[4] - v[6])
            rot_b0 = Rot(axis=v4v6_axis, angle=-b0)
            v[5] = v4v6 + rot_b0 * (v[5] - v4v6)

        self.Vs = v

    def fold_shell_5(self, a0, b0, a1, b1, keepV0=True):
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
        self.fold_shell_es_fs(5)
        self.fold_shell_5_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_shell_5_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_shell_3, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b1
            v5v3 = (v[5] + v[3]) / 2
            v5v3_axis = Vec(v[5] - v[3])
            rot_b1 = Rot(axis=v5v3_axis, angle=-b1)
            # middle of V6-V2 which is // to v5v3 axis
            v6v2 = (v[6] + v[2]) / 2
            v6v2_ = v5v3 + rot_b1 * (v6v2 - v5v3)
            v[6] = v6v2_ + (v[6] - v6v2)
            v[2] = v6v2_ + (v[2] - v6v2)
            # middle of V0-V1 which is // to v5v3 axis
            v0v1 = (v[0] + v[1]) / 2
            v0v1_ = v5v3 + rot_b1 * (v0v1 - v5v3)
            v[0] = v0v1_ + (v[0] - v0v1)
            v[1] = v0v1_ + (v[1] - v0v1)

            # rot a1
            v5v2 = (v[5] + v[2]) / 2
            v5v2_axis = Vec(v[5] - v[2])
            rot_a1 = Rot(axis=v5v2_axis, angle=-a1)
            # middle of V6-V1 which is // to v5v2 axis
            v6v1 = (v[6] + v[1]) / 2
            v6v1_ = v5v2 + rot_a1 * (v6v1 - v5v2)
            v[6] = v6v1_ + (v[6] - v6v1)
            v[1] = v6v1_ + (v[1] - v6v1)
            v[0] = v5v2 + rot_a1 * (v[0] - v5v2)

            # rot a0
            v5v1 = (v[5] + v[1]) / 2
            v5v1_axis = Vec(v[5] - v[1])
            rot_a0 = Rot(axis=v5v1_axis, angle=-a0)
            # middle of V6-V0 which is // to v5v1 axis
            v6v0 = (v[6] + v[0]) / 2
            v6v0_ = v5v1 + rot_a0 * (v6v0 - v5v1)
            v[6] = v6v0_ + (v[6] - v6v0)
            v[0] = v6v0_ + (v[0] - v6v0)

            # rot b0
            v5v0 = (v[5] + v[0]) / 2
            v5v0_axis = Vec(v[5] - v[0])
            rot_b0 = Rot(axis=v5v0_axis, angle=-b0)
            v[6] = v5v0 + rot_b0 * (v[6] - v5v0)

        self.Vs = v

    def fold_shell_6(self, a0, b0, a1, b1, keepV0=True):
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
        self.fold_shell_es_fs(6)
        # opposite angle, because of opposite isometry
        self.fold_shell_1_vs(
            -a1,
            -b1,
            -a0,
            -b0,
            keepV0,
            [
                self.VsOrg[0],
                self.VsOrg[6],
                self.VsOrg[5],
                self.VsOrg[4],
                self.VsOrg[3],
                self.VsOrg[2],
                self.VsOrg[1],
            ],
        )
        self.Vs = [
            self.Vs[0],
            self.Vs[6],
            self.Vs[5],
            self.Vs[4],
            self.Vs[3],
            self.Vs[2],
            self.Vs[1],
        ]

    def fold_w(self, a0, b0, a1, b1, keepV0=True, rotate=0):
        prj = [
            self.fold_w0,
            self.fold_w1,
            self.fold_w2,
            self.fold_w3,
            self.fold_w4,
            self.fold_w5,
            self.fold_w6,
        ]
        prj[rotate](a0, b0, a1, b1, keepV0)

    def fold_w_es_fs(self, no):
        """
        Set self.Es and self.FS for shell fold and specified position.

        no: number to shift up
        """
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
        i = [(i + no) % 7 for i in range(7)]
        self.Fs = [
            [i[1], i[3], i[2]],
            [i[1], i[0], i[3]],
            [i[0], i[4], i[3]],
            [i[0], i[6], i[4]],
            [i[6], i[5], i[4]],
        ]
        self.Es = [
            i[0],
            i[1],
            i[1],
            i[2],
            i[2],
            i[3],
            i[3],
            i[4],
            i[4],
            i[5],
            i[5],
            i[6],
            i[6],
            i[0],
            i[6],
            i[4],
            i[4],
            i[0],
            i[0],
            i[3],
            i[3],
            i[1],
        ]

    def fold_w0(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V0-V3,
        the fold angle a1 refers to the axis V0-V4,
        The fold angle b0 refers to the axis V1-V3,
        The fold angle b1 refers to the axis V6-V4 and
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
        Rot0_3 = Rot(axis=self.VsOrg[3] - self.VsOrg[0], angle=a0)
        V1 = Rot0_3 * self.VsOrg[1]
        V2_ = Rot0_3 * self.VsOrg[2]
        Rot1_3 = Rot(axis=self.VsOrg[3] - V1, angle=b0)
        V2 = Rot1_3 * (V2_ - V1) + V1
        if Geom3D.eq(a0, a1):
            V6 = Vec([-V1[0], V1[1], V1[2]])
            if Geom3D.eq(b0, b1):
                V5 = Vec([-V2[0], V2[1], V2[2]])
            else:
                V5 = Vec([-V2_[0], V2_[1], V2_[2]])
                Rot4_6 = Rot(axis=V6 - self.VsOrg[4], angle=b1)
                V5 = Rot4_6 * (V5 - V6) + V6
        else:
            Rot4_0 = Rot(axis=self.VsOrg[0] - self.VsOrg[4], angle=a1)
            V6 = Rot4_0 * self.VsOrg[6]
            V5 = Rot4_0 * self.VsOrg[5]
            Rot4_6 = Rot(axis=V6 - self.VsOrg[4], angle=b1)
            V5 = Rot4_6 * (V5 - V6) + V6
        self.Vs = [
            self.VsOrg[0],
            V1,
            V2,
            self.VsOrg[3],
            self.VsOrg[4],
            V5,
            V6,
        ]
        self.fold_w_es_fs(0)

    def fold_w1_help(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_w1, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        v = [v for v in Vs]
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
        if keepV0:
            assert False, "TODO"
        else:
            # rot b0
            v2v4 = (v[2] + v[4]) / 2
            v2v4_axis = Vec(v[2] - v[4])
            rot_b0 = Rot(axis=v2v4_axis, angle=b0)
            v1v5 = (v[1] + v[5]) / 2
            v1v5_ = v2v4 + rot_b0 * (v1v5 - v2v4)
            v[1] = v1v5_ + (v[1] - v1v5)
            v5_ = v1v5_ + (v[5] - v1v5)
            v0v6 = (v[0] + v[6]) / 2
            v0v6_ = v2v4 + rot_b0 * (v0v6 - v2v4)
            v0_ = v0v6_ + (v[0] - v0v6)
            v6_ = v0v6_ + (v[6] - v0v6)

            # rot a0
            v1v4 = (v[1] + v[4]) / 2
            v1v4_axis = Vec(v[1] - v[4])
            rot_a0 = Rot(axis=v1v4_axis, angle=a0)
            v0v5 = (v0_ + v5_) / 2
            v0v5_ = v1v4 + rot_a0 * (v0v5 - v1v4)
            v0_ = v0v5_ + (v0_ - v0v5)
            v[5] = v0v5_ + (v5_ - v0v5)
            v6_ = v1v4 + rot_a0 * (v6_ - v1v4)

            # rot a1
            v1v5 = (v[1] + v[5]) / 2
            v1v5_axis = Vec(v[1] - v[5])
            rot_a1 = Rot(axis=v1v5_axis, angle=a1)
            v0v6 = (v0_ + v6_) / 2
            v0v6_ = v1v5 + rot_a1 * (v0v6 - v1v5)
            v[0] = v0v6_ + (v0_ - v0v6)
            v6_ = v0v6_ + (v6_ - v0v6)

            # rot b1
            v0v5 = (v[0] + v[5]) / 2
            v0v5_axis = Vec(v[0] - v[5])
            rot_b1 = Rot(axis=v0v5_axis, angle=b1)
            v[6] = v0v5 + rot_b1 * (v6_ - v0v5)

            return v

    def fold_w2_help(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_w1, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
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
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b0
            v3v5 = (v[3] + v[5]) / 2
            v3v5_axis = Vec(v[3] - v[5])
            rot_b0 = Rot(axis=v3v5_axis, angle=b0)
            v2v6 = (v[2] + v[6]) / 2
            v2v6_ = v3v5 + rot_b0 * (v2v6 - v3v5)
            v[2] = v2v6_ + (v[2] - v2v6)
            v6_ = v2v6_ + (v[6] - v2v6)
            v1v0 = (v[1] + v[0]) / 2
            v1v0_ = v3v5 + rot_b0 * (v1v0 - v3v5)
            v1_ = v1v0_ + (v[1] - v1v0)
            v0_ = v1v0_ + (v[0] - v1v0)

            # rot a0
            v2v5 = (v[2] + v[5]) / 2
            v2v5_axis = Vec(v[2] - v[5])
            rot_a0 = Rot(axis=v2v5_axis, angle=a0)
            v1v6 = (v1_ + v6_) / 2
            v1v6_ = v2v5 + rot_a0 * (v1v6 - v2v5)
            v1_ = v1v6_ + (v1_ - v1v6)
            v[6] = v1v6_ + (v6_ - v1v6)
            v0_ = v2v5 + rot_a0 * (v0_ - v2v5)

            # rot a1
            v2v6 = (v[2] + v[6]) / 2
            v2v6_axis = Vec(v[2] - v[6])
            rot_a1 = Rot(axis=v2v6_axis, angle=a1)
            v1v0 = (v1_ + v0_) / 2
            v1v0_ = v2v6 + rot_a1 * (v1v0 - v2v6)
            v[1] = v1v0_ + (v1_ - v1v0)
            v0_ = v1v0_ + (v0_ - v1v0)

            # rot b1
            v1v6 = (v[1] + v[6]) / 2
            v1v6_axis = Vec(v[1] - v[6])
            rot_b1 = Rot(axis=v1v6_axis, angle=b1)
            v[0] = v1v6 + rot_b1 * (v0_ - v1v6)

        return v

    def fold_w3_help(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_w3, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
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
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot a0
            v3v6 = (v[3] + v[6]) / 2
            v3v6_axis = Vec(v[3] - v[6])
            rot_a0 = Rot(axis=v3v6_axis, angle=a0)
            v0v2 = (v[0] + v[2]) / 2
            v0v2_ = v3v6 + rot_a0 * (v0v2 - v3v6)
            v[0] = v0v2_ + (v[0] - v0v2)
            v2_ = v0v2_ + (v[2] - v0v2)
            v1_ = v3v6 + rot_a0 * (v[1] - v3v6)

            # rot a1
            v3v0 = (v[3] + v[0]) / 2
            v3v0_axis = Vec(v[3] - v[0])
            rot_a1 = Rot(axis=v3v0_axis, angle=a1)
            v1v2 = (v1_ + v2_) / 2
            v1v2_ = v3v0 + rot_a1 * (v1v2 - v3v0)
            v1_ = v1v2_ + (v1_ - v1v2)
            v[2] = v1v2_ + (v2_ - v1v2)

            # rot b1
            v2v0 = (v[2] + v[0]) / 2
            v2v0_axis = Vec(v[2] - v[0])
            rot_b1 = Rot(axis=v2v0_axis, angle=b1)
            v[1] = v2v0 + rot_b1 * (v1_ - v2v0)

            # rot b0
            v6v4 = (v[6] + v[4]) / 2
            v6v4_axis = Vec(v[6] - v[4])
            rot_b0 = Rot(axis=v6v4_axis, angle=b0)
            v[5] = v6v4 + rot_b0 * (v[5] - v6v4)
            return v

    def fold_w4_help(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_w3, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
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
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot a1
            v4v1 = (v[4] + v[1]) / 2
            v4v1_axis = Vec(v[4] - v[1])
            rot_a1 = Rot(axis=v4v1_axis, angle=-a1)
            # 0 2 -> 4 ,6 or 6, 4?
            v0v5 = (v[0] + v[5]) / 2
            v0v5_ = v4v1 + rot_a1 * (v0v5 - v4v1)
            v[0] = v0v5_ + (v[0] - v0v5)
            v5_ = v0v5_ + (v[5] - v0v5)
            v6_ = v4v1 + rot_a1 * (v[6] - v4v1)

            # rot a0
            v4v0 = (v[4] + v[0]) / 2
            v4v0_axis = Vec(v[4] - v[0])
            rot_a0 = Rot(axis=v4v0_axis, angle=-a0)
            v6v5 = (v6_ + v5_) / 2
            v6v5_ = v4v0 + rot_a0 * (v6v5 - v4v0)
            v6_ = v6v5_ + (v6_ - v6v5)
            v[5] = v6v5_ + (v5_ - v6v5)

            # rot b0
            v5v0 = (v[5] + v[0]) / 2
            v5v0_axis = Vec(v[5] - v[0])
            rot_b0 = Rot(axis=v5v0_axis, angle=-b0)
            v[6] = v5v0 + rot_b0 * (v6_ - v5v0)

            # rot b1
            v1v3 = (v[1] + v[3]) / 2
            v1v3_axis = Vec(v[1] - v[3])
            rot_b1 = Rot(axis=v1v3_axis, angle=-b1)
            v[2] = v1v3 + rot_b1 * (v[2] - v1v3)
            return v

    def fold_w5_help(self, a0, b0, a1, b1, keepV0, Vs):
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
        v = self.fold_w2_help(
            -a1,
            -b1,
            -a0,
            -b0,
            keepV0,
            [Vs[0], Vs[6], Vs[5], Vs[4], Vs[3], Vs[2], Vs[1]],
        )
        return [v[0], v[6], v[5], v[4], v[3], v[2], v[1]]

    def fold_w6_help(self, a0, b0, a1, b1, keepV0, Vs):
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
        v = self.fold_w1_help(
            -a1,
            -b1,
            -a0,
            -b0,
            keepV0,
            [Vs[0], Vs[6], Vs[5], Vs[4], Vs[3], Vs[2], Vs[1]],
        )
        return [v[0], v[6], v[5], v[4], v[3], v[2], v[1]]

    def fold_w1(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V1-V4,
        the fold angle a1 refers to the axis V1-V5,
        The fold angle b0 refers to the axis V2-V4,
        The fold angle b1 refers to the axis V0-V5 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(1)
        self.Vs = self.fold_w1_help(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_w2(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V2-V5,
        the fold angle a1 refers to the axis V2-V6,
        The fold angle b0 refers to the axis V3-V5,
        The fold angle b1 refers to the axis V1-V6 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(2)
        self.Vs = self.fold_w2_help(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_w3(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V3-V6,
        the fold angle a1 refers to the axis V3-V0,
        The fold angle b0 refers to the axis V4-V6,
        The fold angle b1 refers to the axis V2-V0 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(3)
        self.Vs = self.fold_w3_help(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_w4(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V3-V6,
        the fold angle a1 refers to the axis V3-V0,
        The fold angle b0 refers to the axis V4-V6,
        The fold angle b1 refers to the axis V2-V0 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(4)
        self.Vs = self.fold_w4_help(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_w5(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V1-V4,
        the fold angle a1 refers to the axis V1-V5,
        The fold angle b0 refers to the axis V2-V4,
        The fold angle b1 refers to the axis V0-V5 and
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(5)
        self.Vs = self.fold_w5_help(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_w6(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V6-V2,
        the fold angle a1 refers to the axis V6-V3,
        The fold angle b0 refers to the axis V2-V0 and
        The fold angle b1 refers to the axis V3-V5,
        If keepV0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(6)
        self.Vs = self.fold_w6_help(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_mixed(self, a0, b0, a1, b1, keepV0=True, rotate=0):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        For rotate == 0:
        The fold angle a0 refers the axis V0-V3
        the fold angle b0 refers the axes V0-V2
        The fold angle a1 refers the axis V0-V4
        the fold angle b1 refers the axes V6-V4
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #               Vi
        #               .^.
        #       i+6     | |\_   i+1
        #        |     /   \ \_
        # axis b1 \   |a    |  \_ axis b0
        #         |   |x    |    \
        #     i+5 |  / i     \    i+2
        #          \|  s      | axis a0
        #           "         "
        #         i+4  a1     i+3
        #

        prj = {
            0: self.fold_mixed_0,
            1: self.fold_mixed_1,
            2: self.fold_mixed_2,
            3: self.fold_mixed_3,
            4: self.fold_mixed_4,
            5: self.fold_mixed_5,
            6: self.fold_mixed_6,
        }
        prj[rotate](a0, b0, a1, b1, keepV0)

    def fold_mixed_es_fs(self, no):
        """
        Set self.Es and self.FS for shell fold and specified position.

        no: number to shift up
        """
        i = [(i + no) % 7 for i in range(7)]
        self.Fs = [
            [i[0], i[2], i[1]],
            [i[0], i[3], i[2]],
            [i[0], i[4], i[3]],
            [i[0], i[6], i[4]],
            [i[6], i[5], i[4]],
        ]
        self.Es = [
            i[0],
            i[1],
            i[1],
            i[2],
            i[2],
            i[3],
            i[3],
            i[4],
            i[4],
            i[5],
            i[5],
            i[6],
            i[6],
            i[0],
            i[0],
            i[2],
            i[0],
            i[3],
            i[0],
            i[4],
            i[6],
            i[4],
        ]

    def fold_mixed_0(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a0 refers the axis V0-V3
        the fold angle b0 refers the axis V0-V2
        the fold angle a1 refers the axis V0-V4
        the fold angle b1 refers the axis V6-V4
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #                0
        #               .^.
        #        6      | |\_   1
        #        |     /   \ \_
        # axis b1 \   |a    |  \_ axis b0
        #         |   |x    |    \
        #       5 |  / i     \    2
        #          \|  s      | axis a0
        #           "         "
        #           4  a1     3
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(0)
            self.fold_mixed_0_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_mixed_0_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_shell_1, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot a0
            v0v3 = (v[0] + v[3]) / 2
            v0v3_axis = Vec(v[0] - v[3])
            # Note: negative angle
            rot_a0 = Rot(axis=v0v3_axis, angle=-a0)
            # middle of V1-V2 which is // to v0v3 axis
            v1v2 = (v[1] + v[2]) / 2
            v1v2_ = v0v3 + rot_a0 * (v1v2 - v0v3)
            v[1] = v1v2_ + (v[1] - v1v2)
            v[2] = v1v2_ + (v[2] - v1v2)

            # rot b0
            v0v2 = (v[0] + v[2]) / 2
            v0v2_axis = Vec(v[0] - v[2])
            # Note: negative angle
            rot_b0 = Rot(axis=v0v2_axis, angle=-b0)
            v[1] = v0v2 + rot_b0 * (v[1] - v0v2)

            # rot a1
            v0v4 = (v[0] + v[4]) / 2
            v0v4_axis = Vec(v[0] - v[4])
            rot_a1 = Rot(axis=v0v4_axis, angle=a1)
            # middle of V6-V5 which is // to v0v4 axis
            v6v5 = (v[6] + v[5]) / 2
            v6v5_ = v0v4 + rot_a1 * (v6v5 - v0v4)
            v[6] = v6v5_ + (v[6] - v6v5)
            v[5] = v6v5_ + (v[5] - v6v5)

            # rot b1
            v6v4 = (v[6] + v[4]) / 2
            v6v4_axis = Vec(v[6] - v[4])
            rot_b1 = Rot(axis=v6v4_axis, angle=b1)
            v[5] = v6v4 + rot_b1 * (v[5] - v6v4)

        self.Vs = v

    def fold_mixed_1(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a0 refers the axis V1-V4
        the fold angle b0 refers the axis V1-V3
        the fold angle a1 refers the axis V1-V5
        the fold angle b1 refers the axis V0-V5
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #                1
        #               .^.
        #        0      | |\_   2
        #        |     /   \ \_
        # axis b1 \   |a    |  \_ axis b0
        #         |   |x    |    \
        #       6 |  / i     \    3
        #          \|  s      | axis a0
        #           "         "
        #           5  a1     4
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(1)
            self.fold_mixed_1_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_mixed_1_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot a0
            v1v4 = (v[1] + v[4]) / 2
            v1v4_axis = Vec(v[1] - v[4])
            rot_a0 = Rot(axis=v1v4_axis, angle=a0)
            # middle of V0-V5 which is // to v1v4 axis
            v0v5 = (v[0] + v[5]) / 2
            v0v5_ = v1v4 + rot_a0 * (v0v5 - v1v4)
            v[0] = v0v5_ + (v[0] - v0v5)
            v[5] = v0v5_ + (v[5] - v0v5)
            v[6] = v1v4 + rot_a0 * (v[6] - v1v4)

            # rot b0
            v1v3 = (v[1] + v[3]) / 2
            v1v3_axis = Vec(v[1] - v[3])
            # Note: negative angle
            rot_b0 = Rot(axis=v1v3_axis, angle=-b0)
            v[2] = v1v3 + rot_b0 * (v[2] - v1v3)

            # rot a1
            v1v5 = (v[1] + v[5]) / 2
            v1v5_axis = Vec(v[1] - v[5])
            rot_a1 = Rot(axis=v1v5_axis, angle=a1)
            # middle of V0-V6 which is // to v1v5 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_ = v1v5 + rot_a1 * (v0v6 - v1v5)
            v[0] = v0v6_ + (v[0] - v0v6)
            v[6] = v0v6_ + (v[6] - v0v6)

            # rot b1
            v0v5 = (v[0] + v[5]) / 2
            v0v5_axis = Vec(v[0] - v[5])
            rot_b1 = Rot(axis=v0v5_axis, angle=b1)
            v[6] = v0v5 + rot_b1 * (v[6] - v0v5)

        self.Vs = v

    def fold_mixed_2(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a0 refers the axis V2-V5
        the fold angle b0 refers the axis V2-V4
        the fold angle a1 refers the axis V2-V6
        the fold angle b1 refers the axis V1-V6
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #                2
        #               .^.
        #        1      | |\_   3
        #        |     /   \ \_
        # axis b1 \   |a    |  \_ axis b0
        #         |   |x    |    \
        #       0 |  / i     \    4
        #          \|  s      | axis a0
        #           "         "
        #           6  a1     5
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(2)
            self.fold_mixed_2_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_mixed_2_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b0
            v2v4 = (v[2] + v[4]) / 2
            v2v4_axis = Vec(v[2] - v[4])
            rot_b0 = Rot(axis=v2v4_axis, angle=b0)
            # middle of V1-V5 which is // to v2v4 axis
            v1v5 = (v[1] + v[5]) / 2
            v1v5_ = v2v4 + rot_b0 * (v1v5 - v2v4)
            v[1] = v1v5_ + (v[1] - v1v5)
            v[5] = v1v5_ + (v[5] - v1v5)
            # middle of V0-V6 which is // to v2v4 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_ = v2v4 + rot_b0 * (v0v6 - v2v4)
            v[0] = v0v6_ + (v[0] - v0v6)
            v[6] = v0v6_ + (v[6] - v0v6)

            # rot a0
            v2v5 = (v[2] + v[5]) / 2
            v2v5_axis = Vec(v[2] - v[5])
            rot_a0 = Rot(axis=v2v5_axis, angle=a0)
            # middle of V1-V6 which is // to v2v5 axis
            v1v6 = (v[1] + v[6]) / 2
            v1v6_ = v2v5 + rot_a0 * (v1v6 - v2v5)
            v[1] = v1v6_ + (v[1] - v1v6)
            v[6] = v1v6_ + (v[6] - v1v6)
            v[0] = v2v5 + rot_a0 * (v[0] - v2v5)

            # rot a1
            v2v6 = (v[2] + v[6]) / 2
            v2v6_axis = Vec(v[2] - v[6])
            rot_a1 = Rot(axis=v2v6_axis, angle=a1)
            # middle of V1-V0 which is // to v2v6 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_ = v2v6 + rot_a1 * (v1v0 - v2v6)
            v[1] = v1v0_ + (v[1] - v1v0)
            v[0] = v1v0_ + (v[0] - v1v0)

            # rot b1
            v1v6 = (v[1] + v[6]) / 2
            v1v6_axis = Vec(v[1] - v[6])
            rot_b1 = Rot(axis=v1v6_axis, angle=b1)
            v[0] = v1v6 + rot_b1 * (v[0] - v1v6)

        self.Vs = v

    def fold_mixed_3(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a0 refers the axis V3-V6
        the fold angle b0 refers the axis V3-V5
        the fold angle a1 refers the axis V3-V0
        the fold angle b1 refers the axis V2-V0
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #                3
        #               .^.
        #        2      | |\_   4
        #        |     /   \ \_
        # axis b1 \   |a    |  \_ axis b0
        #         |   |x    |    \
        #       1 |  / i     \    5
        #          \|  s      | axis a0
        #           "         "
        #           0  a1     6
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(3)
            self.fold_mixed_3_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_mixed_3_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b0
            v3v5 = (v[3] + v[5]) / 2
            v3v5_axis = Vec(v[3] - v[5])
            rot_b0 = Rot(axis=v3v5_axis, angle=b0)
            # middle of V2-V6 which is // to v3v5 axis
            v2v6 = (v[2] + v[6]) / 2
            v2v6_ = v3v5 + rot_b0 * (v2v6 - v3v5)
            v[2] = v2v6_ + (v[2] - v2v6)
            v[6] = v2v6_ + (v[6] - v2v6)
            # middle of V1-V0 which is // to v3v5 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_ = v3v5 + rot_b0 * (v1v0 - v3v5)
            v[1] = v1v0_ + (v[1] - v1v0)
            v[0] = v1v0_ + (v[0] - v1v0)

            # rot a0
            v3v6 = (v[3] + v[6]) / 2
            v3v6_axis = Vec(v[3] - v[6])
            rot_a0 = Rot(axis=v3v6_axis, angle=a0)
            # middle of V2-V0 which is // to v3v6 axis
            v2v0 = (v[2] + v[0]) / 2
            v2v0_ = v3v6 + rot_a0 * (v2v0 - v3v6)
            v[2] = v2v0_ + (v[2] - v2v0)
            v[0] = v2v0_ + (v[0] - v2v0)
            v[1] = v3v6 + rot_a0 * (v[1] - v3v6)

            # rot a1
            v3v0 = (v[3] + v[0]) / 2
            v3v0_axis = Vec(v[3] - v[0])
            rot_a1 = Rot(axis=v3v0_axis, angle=a1)
            # middle of V2-V1 which is // to v3v0 axis
            v2v1 = (v[2] + v[1]) / 2
            v2v1_ = v3v0 + rot_a1 * (v2v1 - v3v0)
            v[2] = v2v1_ + (v[2] - v2v1)
            v[1] = v2v1_ + (v[1] - v2v1)

            # rot b1
            v2v0 = (v[2] + v[0]) / 2
            v2v0_axis = Vec(v[2] - v[0])
            rot_b1 = Rot(axis=v2v0_axis, angle=b1)
            v[1] = v2v0 + rot_b1 * (v[1] - v2v0)

        self.Vs = v

    def fold_mixed_4(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a0 refers the axis V4-V0
        the fold angle b0 refers the axis V4-V6
        the fold angle a1 refers the axis V4-V1
        the fold angle b1 refers the axis V3-V1
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #                4
        #               .^.
        #        3      | |\_   5
        #        |     /   \ \_
        # axis b1 \   |a    |  \_ axis b0
        #         |   |x    |    \
        #       2 |  / i     \    6
        #          \|  s      | axis a0
        #           "         "
        #           1  a1     0
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(4)
            self.fold_mixed_4_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_mixed_4_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot a1
            v4v1 = (v[4] + v[1]) / 2
            v4v1_axis = Vec(v[4] - v[1])
            # Note: negative angle
            rot_a1 = Rot(axis=v4v1_axis, angle=-a1)
            # middle of V5-V0 which is // to v4v1 axis
            v5v0 = (v[5] + v[0]) / 2
            v5v0_ = v4v1 + rot_a1 * (v5v0 - v4v1)
            v[5] = v5v0_ + (v[5] - v5v0)
            v[0] = v5v0_ + (v[0] - v5v0)
            v[6] = v4v1 + rot_a1 * (v[6] - v4v1)

            # rot a0
            v4v0 = (v[4] + v[0]) / 2
            v4v0_axis = Vec(v[4] - v[0])
            # Note: negative angle
            rot_a0 = Rot(axis=v4v0_axis, angle=-a0)
            # middle of V5-V6 which is // to v4v0 axis
            v5v6 = (v[5] + v[6]) / 2
            v5v6_ = v4v0 + rot_a0 * (v5v6 - v4v0)
            v[5] = v5v6_ + (v[5] - v5v6)
            v[6] = v5v6_ + (v[6] - v5v6)

            # rot b0
            v4v6 = (v[4] + v[6]) / 2
            v4v6_axis = Vec(v[4] - v[6])
            # Note: negative angle
            rot_b0 = Rot(axis=v4v6_axis, angle=-b0)
            # middle of V2-V1 which is // to v4v6 axis
            v[5] = v4v6 + rot_b0 * (v[5] - v4v6)

            # rot b1
            v3v1 = (v[3] + v[1]) / 2
            v3v1_axis = Vec(v[3] - v[1])
            rot_b1 = Rot(axis=v3v1_axis, angle=b1)
            v[2] = v3v1 + rot_b1 * (v[2] - v3v1)

        self.Vs = v

    def fold_mixed_5(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a0 refers the axis V5-V1
        the fold angle b0 refers the axis V5-V0
        the fold angle a1 refers the axis V5-V2
        the fold angle b1 refers the axis V4-V2
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #                5
        #               .^.
        #        4      | |\_   6
        #        |     /   \ \_
        # axis b1 \   |a    |  \_ axis b0
        #         |   |x    |    \
        #       3 |  / i     \    0
        #          \|  s      | axis a0
        #           "         "
        #           2  a1     1
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(5)
            self.fold_mixed_5_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_mixed_5_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b1
            v4v2 = (v[4] + v[2]) / 2
            v4v2_axis = Vec(v[4] - v[2])
            # Note: negative angle
            rot_b1 = Rot(axis=v4v2_axis, angle=-b1)
            # middle of V5-V1 which is // to v4v2 axis
            v5v1 = (v[5] + v[1]) / 2
            v5v1_ = v4v2 + rot_b1 * (v5v1 - v4v2)
            v[5] = v5v1_ + (v[5] - v5v1)
            v[1] = v5v1_ + (v[1] - v5v1)
            # middle of V6-V0 which is // to v4v2 axis
            v6v0 = (v[6] + v[0]) / 2
            v6v0_ = v4v2 + rot_b1 * (v6v0 - v4v2)
            v[6] = v6v0_ + (v[6] - v6v0)
            v[0] = v6v0_ + (v[0] - v6v0)

            # rot a1
            v5v2 = (v[5] + v[2]) / 2
            v5v2_axis = Vec(v[5] - v[2])
            # Note: negative angle
            rot_a1 = Rot(axis=v5v2_axis, angle=-a1)
            # middle of V6-V1 which is // to v5v2 axis
            v6v1 = (v[6] + v[1]) / 2
            v6v1_ = v5v2 + rot_a1 * (v6v1 - v5v2)
            v[6] = v6v1_ + (v[6] - v6v1)
            v[1] = v6v1_ + (v[1] - v6v1)
            v[0] = v5v2 + rot_a1 * (v[0] - v5v2)

            # rot a0
            v5v1 = (v[5] + v[1]) / 2
            v5v1_axis = Vec(v[5] - v[1])
            # Note: negative angle
            rot_a0 = Rot(axis=v5v1_axis, angle=-a0)
            # middle of V6-V0 which is // to v5v1 axis
            v6v0 = (v[6] + v[0]) / 2
            v6v0_ = v5v1 + rot_a0 * (v6v0 - v5v1)
            v[6] = v6v0_ + (v[6] - v6v0)
            v[0] = v6v0_ + (v[0] - v6v0)

            # rot b0
            v5v0 = (v[5] + v[0]) / 2
            v5v0_axis = Vec(v[5] - v[0])
            # Note: negative angle
            rot_b0 = Rot(axis=v5v0_axis, angle=-b0)
            v[6] = v5v0 + rot_b0 * (v[6] - v5v0)

        self.Vs = v

    def fold_mixed_6(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a0 refers the axis V6-V2
        the fold angle b0 refers the axis V6-V1
        the fold angle a1 refers the axis V6-V3
        the fold angle b1 refers the axis V5-V3
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #
        #                6
        #               .^.
        #        5      | |\_   0
        #        |     /   \ \_
        # axis b1 \   |a    |  \_ axis b0
        #         |   |x    |    \
        #       4 |  / i     \    1
        #          \|  s      | axis a0
        #           "         "
        #           3  a1     2
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(6)
            self.fold_mixed_6_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_mixed_6_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b1
            v5v3 = (v[5] + v[3]) / 2
            v5v3_axis = Vec(v[5] - v[3])
            # Note: negative angle
            rot_b1 = Rot(axis=v5v3_axis, angle=-b1)
            # middle of V6-V2 which is // to v5v3 axis
            v6v2 = (v[6] + v[2]) / 2
            v6v2_ = v5v3 + rot_b1 * (v6v2 - v5v3)
            v[6] = v6v2_ + (v[6] - v6v2)
            v[2] = v6v2_ + (v[2] - v6v2)
            # middle of V0-V1 which is // to v5v3 axis
            v0v1 = (v[0] + v[1]) / 2
            v0v1_ = v5v3 + rot_b1 * (v0v1 - v5v3)
            v[0] = v0v1_ + (v[0] - v0v1)
            v[1] = v0v1_ + (v[1] - v0v1)

            # rot a1
            v6v3 = (v[6] + v[3]) / 2
            v6v3_axis = Vec(v[6] - v[3])
            # Note: negative angle
            rot_a1 = Rot(axis=v6v3_axis, angle=-a1)
            # middle of V0-V2 which is // to v6v3 axis
            v0v2 = (v[0] + v[2]) / 2
            v0v2_ = v6v3 + rot_a1 * (v0v2 - v6v3)
            v[0] = v0v2_ + (v[0] - v0v2)
            v[2] = v0v2_ + (v[2] - v0v2)
            v[1] = v6v3 + rot_a1 * (v[1] - v6v3)

            # rot a0
            v6v2 = (v[6] + v[2]) / 2
            v6v2_axis = Vec(v[6] - v[2])
            # Note: negative angle
            rot_a0 = Rot(axis=v6v2_axis, angle=-a0)
            # middle of V0-V1 which is // to v6v2 axis
            v0v1 = (v[0] + v[1]) / 2
            v0v1_ = v6v2 + rot_a0 * (v0v1 - v6v2)
            v[0] = v0v1_ + (v[0] - v0v1)
            v[1] = v0v1_ + (v[1] - v0v1)

            # rot b0
            v6v1 = (v[6] + v[1]) / 2
            v6v1_axis = Vec(v[6] - v[1])
            # Note: negative angle
            rot_b0 = Rot(axis=v6v1_axis, angle=-b0)
            v[0] = v6v1 + rot_b0 * (v[0] - v6v1)

        self.Vs = v

    def fold_g(self, a0, b0, a1, b1, keepV0=True, rotate=0):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        For rotate == 0:
        The fold angle a0 refers the axis V0-V2
        the fold angle b0 refers the axes V0-V3 and V0-V4.
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #             Vi
        #            /\
        #   Vi+6    /  '.    Vi+1
        #         .'     '.
        # axis a1/         \ axis b1
        #       /  axis a0  \
        # Vi+5 -------------.- Vi+2
        #      axis b0__--''
        #          _-'
        #       Vi+4     Vi+3
        #

        prj = {
            0: self.fold_g_0,
            1: self.fold_g_1,
            2: self.fold_g_2,
            3: self.fold_g_3,
            4: self.fold_g_4,
            5: self.fold_g_5,
            6: self.fold_g_6,
        }
        prj[rotate](a0, b0, a1, b1, keepV0)

    def fold_g_es_fs(self, no):
        """
        Set self.Es and self.FS for shell fold and specified position.

        no: number to shift up
        """
        i = [(i + no) % 7 for i in range(7)]
        self.Fs = [
            [i[0], i[2], i[1]],
            [i[0], i[5], i[2]],
            [i[0], i[6], i[5]],
            [i[2], i[5], i[4]],
            [i[2], i[4], i[3]],
        ]
        self.Es = [
            i[0],
            i[1],
            i[1],
            i[2],
            i[2],
            i[3],
            i[3],
            i[4],
            i[4],
            i[5],
            i[5],
            i[6],
            i[6],
            i[0],
            i[4],
            i[2],
            i[2],
            i[0],
            i[0],
            i[5],
            i[5],
            i[2],
        ]

    def fold_g_0(self, a0, b0, a1, b1, keepV0=True):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a0 refers the axis V0-V3
        the fold angle b0 refers the axis V0-V2
        the fold angle a1 refers the axis V0-V4
        the fold angle b1 refers the axis V6-V4
        The keepV0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        """
        #             V0
        #            /\
        #     V6    /  '.    V1
        #         .'     '.
        # axis a1/         \ axis b1
        #       /  axis a0  \
        #   V5 =------------.- V2
        #      axis b0__--''
        #          _-'
        #        V4       V3
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(0)
            self.fold_g_0_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_g_0_vs(self, a0, b0, a1, b1, keepV0, Vs):
        """Helper function for fold_shell_1, see that one for more info

        Vs: the array with vertex numbers.
        returns a new array.
        """
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b0
            v2v4 = (v[2] + v[4]) / 2
            v2v4_axis = Vec(v[2] - v[4])
            rot_b0 = Rot(axis=v2v4_axis, angle=b0)
            # middle of V1-V5 which is // to v2v4 axis
            v1v5 = (v[1] + v[5]) / 2
            v1v5_ = v2v4 + rot_b0 * (v1v5 - v2v4)
            v[1] = v1v5_ + (v[1] - v1v5)
            v[5] = v1v5_ + (v[5] - v1v5)
            # middle of V0-V6 which is // to v2v4 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_ = v2v4 + rot_b0 * (v0v6 - v2v4)
            v[0] = v0v6_ + (v[0] - v0v6)
            v[6] = v0v6_ + (v[6] - v0v6)

            # rot a0
            v2v5 = (v[2] + v[5]) / 2
            v2v5_axis = Vec(v[2] - v[5])
            rot_a0 = Rot(axis=v2v5_axis, angle=a0)
            # middle of V1-V6 which is // to v2v5 axis
            v1v6 = (v[1] + v[6]) / 2
            v1v6_ = v2v5 + rot_a0 * (v1v6 - v2v5)
            v[1] = v1v6_ + (v[1] - v1v6)
            v[6] = v1v6_ + (v[6] - v1v6)
            v[0] = v2v5 + rot_a0 * (v[0] - v2v5)

            # rot a1
            v0v5 = (v[0] + v[5]) / 2
            v0v5_axis = Vec(v[0] - v[5])
            rot_a1 = Rot(axis=v0v5_axis, angle=a1)
            v[6] = v0v5 + rot_a1 * (v[6] - v0v5)

            # rot b1
            v0v2 = (v[0] + v[2]) / 2
            v0v2_axis = Vec(v[0] - v[2])
            rot_b1 = Rot(axis=v0v2_axis, angle=-b1)
            v[1] = v0v2 + rot_b1 * (v[1] - v0v2)

        self.Vs = v

    def fold_g_1(self, a0, b0, a1, b1, keepV0=True):
        #            V1
        #            /\
        #     V0    /  '.    V2
        #         .'     '.
        # axis a1/         \ axis b1
        #       /  axis a0  \
        #   V6 =------------.- V3
        #      axis b0__--''
        #          _-'
        #        V5       V4
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(1)
            self.fold_g_1_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_g_1_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b0
            v3v5 = (v[3] + v[5]) / 2
            v3v5_axis = Vec(v[3] - v[5])
            rot_b0 = Rot(axis=v3v5_axis, angle=b0)
            # middle of V2-V6 which is // to v3v5 axis
            v2v6 = (v[2] + v[6]) / 2
            v2v6_ = v3v5 + rot_b0 * (v2v6 - v3v5)
            v[2] = v2v6_ + (v[2] - v2v6)
            v[6] = v2v6_ + (v[6] - v2v6)
            # middle of V1-V0 which is // to v3v5 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_ = v3v5 + rot_b0 * (v1v0 - v3v5)
            v[1] = v1v0_ + (v[1] - v1v0)
            v[0] = v1v0_ + (v[0] - v1v0)

            # rot a0
            v3v6 = (v[3] + v[6]) / 2
            v3v6_axis = Vec(v[3] - v[6])
            rot_a0 = Rot(axis=v3v6_axis, angle=a0)
            # middle of V2-V0 which is // to v3v6 axis
            v2v0 = (v[2] + v[0]) / 2
            v2v0_ = v3v6 + rot_a0 * (v2v0 - v3v6)
            v[2] = v2v0_ + (v[2] - v2v0)
            v[0] = v2v0_ + (v[0] - v2v0)
            v[1] = v3v6 + rot_a0 * (v[1] - v3v6)

            # rot a1
            v1v6 = (v[1] + v[6]) / 2
            v1v6_axis = Vec(v[1] - v[6])
            rot_a1 = Rot(axis=v1v6_axis, angle=a1)
            v[0] = v1v6 + rot_a1 * (v[0] - v1v6)

            # rot b1
            v1v3 = (v[1] + v[3]) / 2
            v1v3_axis = Vec(v[1] - v[3])
            rot_b1 = Rot(axis=v1v3_axis, angle=-b1)
            v[2] = v1v3 + rot_b1 * (v[2] - v1v3)

        self.Vs = v

    def fold_g_2(self, a0, b0, a1, b1, keepV0=True):
        #            V2
        #            /\
        #     V1    /  '.    V3
        #         .'     '.
        # axis a1/         \ axis b1
        #       /  axis a0  \
        #   V0 =------------.- V4
        #      axis b0__--''
        #          _-'
        #        V6       V5
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(2)
            self.fold_g_2_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_g_2_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b1
            v2v4 = (v[2] + v[4]) / 2
            v2v4_axis = Vec(v[2] - v[4])
            rot_b1 = Rot(axis=v2v4_axis, angle=b1)
            # middle of V1-V5 which is // to v2v4 axis
            v1v5 = (v[1] + v[5]) / 2
            v1v5_ = v2v4 + rot_b1 * (v1v5 - v2v4)
            v[1] = v1v5_ + (v[1] - v1v5)
            v[5] = v1v5_ + (v[5] - v1v5)
            # middle of V0-V6 which is // to v2v4 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_ = v2v4 + rot_b1 * (v0v6 - v2v4)
            v[0] = v0v6_ + (v[0] - v0v6)
            v[6] = v0v6_ + (v[6] - v0v6)

            # rot a0
            v0v4 = (v[0] + v[4]) / 2
            v0v4_axis = Vec(v[0] - v[4])
            rot_a0 = Rot(axis=v0v4_axis, angle=a0)
            # middle of V5-V6 which is // to v0v4 axis
            v5v6 = (v[5] + v[6]) / 2
            v5v6_ = v0v4 + rot_a0 * (v5v6 - v0v4)
            v[5] = v5v6_ + (v[5] - v5v6)
            v[6] = v5v6_ + (v[6] - v5v6)

            # rot a1
            v0v2 = (v[0] + v[2]) / 2
            v0v2_axis = Vec(v[0] - v[2])
            rot_a1 = Rot(axis=v0v2_axis, angle=-a1)
            v[1] = v0v2 + rot_a1 * (v[1] - v0v2)

            # rot b0
            v4v6 = (v[4] + v[6]) / 2
            v4v6_axis = Vec(v[4] - v[6])
            rot_b0 = Rot(axis=v4v6_axis, angle=-b0)
            v[5] = v4v6 + rot_b0 * (v[5] - v4v6)

        self.Vs = v

    def fold_g_3(self, a0, b0, a1, b1, keepV0=True):
        #            V3
        #            /\
        #     V2    /  '.    V4
        #         .'     '.
        # axis a1/         \ axis b1
        #       /  axis a0  \
        #   V1 =------------.- V5
        #      axis b0__--''
        #          _-'
        #        V0       V6
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(3)
            self.fold_g_3_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_g_3_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot b1
            v3v5 = (v[3] + v[5]) / 2
            v3v5_axis = Vec(v[3] - v[5])
            rot_b1 = Rot(axis=v3v5_axis, angle=b1)
            # middle of V2-V6 which is // to v3v5 axis
            v2v6 = (v[2] + v[6]) / 2
            v2v6_ = v3v5 + rot_b1 * (v2v6 - v3v5)
            v[2] = v2v6_ + (v[2] - v2v6)
            v[6] = v2v6_ + (v[6] - v2v6)
            # middle of V1-V0 which is // to v3v5 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_ = v3v5 + rot_b1 * (v1v0 - v3v5)
            v[1] = v1v0_ + (v[1] - v1v0)
            v[0] = v1v0_ + (v[0] - v1v0)

            # rot a0
            v1v5 = (v[1] + v[5]) / 2
            v1v5_axis = Vec(v[1] - v[5])
            rot_a0 = Rot(axis=v1v5_axis, angle=a0)
            # middle of V6-V0 which is // to v1v5 axis
            v6v0 = (v[6] + v[0]) / 2
            v6v0_ = v1v5 + rot_a0 * (v6v0 - v1v5)
            v[6] = v6v0_ + (v[6] - v6v0)
            v[0] = v6v0_ + (v[0] - v6v0)

            # rot a1
            v1v3 = (v[1] + v[3]) / 2
            v1v3_axis = Vec(v[1] - v[3])
            rot_a1 = Rot(axis=v1v3_axis, angle=-a1)
            v[2] = v1v3 + rot_a1 * (v[2] - v1v3)

            # rot b0
            v5v0 = (v[5] + v[0]) / 2
            v5v0_axis = Vec(v[5] - v[0])
            rot_b0 = Rot(axis=v5v0_axis, angle=-b0)
            v[6] = v5v0 + rot_b0 * (v[6] - v5v0)

        self.Vs = v

    def fold_g_4(self, a0, b0, a1, b1, keepV0=True):
        #            V4
        #            /\
        #     V3    /  '.    V5
        #         .'     '.
        # axis a1/         \ axis b1
        #       /  axis a0  \
        #   V2 =------------.- V6
        #      axis b0__--''
        #          _-'
        #        V1       V0
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(4)
            self.fold_g_4_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_g_4_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot a1
            v4v2 = (v[4] + v[2]) / 2
            v4v2_axis = Vec(v[4] - v[2])
            rot_a1 = Rot(axis=v4v2_axis, angle=-a1)
            # middle of V1-V5 which is // to v4v2 axis
            v1v5 = (v[1] + v[5]) / 2
            v1v5_ = v4v2 + rot_a1 * (v1v5 - v4v2)
            v[1] = v1v5_ + (v[1] - v1v5)
            v[5] = v1v5_ + (v[5] - v1v5)
            # middle of V0-V6 which is // to v4v2 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_ = v4v2 + rot_a1 * (v0v6 - v4v2)
            v[0] = v0v6_ + (v[0] - v0v6)
            v[6] = v0v6_ + (v[6] - v0v6)

            # rot a0
            v2v6 = (v[2] + v[6]) / 2
            v2v6_axis = Vec(v[2] - v[6])
            rot_a0 = Rot(axis=v2v6_axis, angle=a0)
            # middle of V0-V1 which is // to v2v6 axis
            v0v1 = (v[0] + v[1]) / 2
            v0v1_ = v2v6 + rot_a0 * (v0v1 - v2v6)
            v[0] = v0v1_ + (v[0] - v0v1)
            v[1] = v0v1_ + (v[1] - v0v1)

            # rot b1
            v6v4 = (v[6] + v[4]) / 2
            v6v4_axis = Vec(v[6] - v[4])
            rot_b1 = Rot(axis=v6v4_axis, angle=-b1)
            v[5] = v6v4 + rot_b1 * (v[5] - v6v4)

            # rot b0
            v6v1 = (v[6] + v[1]) / 2
            v6v1_axis = Vec(v[6] - v[1])
            rot_b0 = Rot(axis=v6v1_axis, angle=-b0)
            v[0] = v6v1 + rot_b0 * (v[0] - v6v1)

        self.Vs = v

    def fold_g_5(self, a0, b0, a1, b1, keepV0=True):
        #            V5
        #            /\
        #     V4    /  '.    V6
        #         .'     '.
        # axis a1/         \ axis b1
        #       /  axis a0  \
        #   V3 =------------.- V0
        #      axis b0__--''
        #          _-'
        #        V2       V1
        #
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(5)
            self.fold_g_5_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_g_5_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot a1
            v5v3 = (v[5] + v[3]) / 2
            v5v3_axis = Vec(v[5] - v[3])
            rot_a1 = Rot(axis=v5v3_axis, angle=-a1)
            # middle of V2-V6 which is // to v5v3 axis
            v2v6 = (v[2] + v[6]) / 2
            v2v6_ = v5v3 + rot_a1 * (v2v6 - v5v3)
            v[2] = v2v6_ + (v[2] - v2v6)
            v[6] = v2v6_ + (v[6] - v2v6)
            # middle of V0-V6 which is // to v5v3 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_ = v5v3 + rot_a1 * (v1v0 - v5v3)
            v[1] = v1v0_ + (v[1] - v1v0)
            v[0] = v1v0_ + (v[0] - v1v0)

            # rot a0
            v3v0 = (v[3] + v[0]) / 2
            v3v0_axis = Vec(v[3] - v[0])
            rot_a0 = Rot(axis=v3v0_axis, angle=a0)
            # middle of V1-V2 which is // to v3v0 axis
            v1v2 = (v[1] + v[2]) / 2
            v1v2_ = v3v0 + rot_a0 * (v1v2 - v3v0)
            v[1] = v1v2_ + (v[1] - v1v2)
            v[2] = v1v2_ + (v[2] - v1v2)

            # rot b1
            v0v5 = (v[0] + v[5]) / 2
            v0v5_axis = Vec(v[0] - v[5])
            rot_b1 = Rot(axis=v0v5_axis, angle=-b1)
            v[6] = v0v5 + rot_b1 * (v[6] - v0v5)

            # rot b0
            v0v2 = (v[0] + v[2]) / 2
            v0v2_axis = Vec(v[0] - v[2])
            rot_b0 = Rot(axis=v0v2_axis, angle=b0)
            v[1] = v0v2 + rot_b0 * (v[1] - v0v2)

        self.Vs = v

    def fold_g_6(self, a0, b0, a1, b1, keepV0=True):
        #            V6
        #            /\
        #     V5    /  '.    V0
        #         .'     '.
        # axis a1/         \ axis b1
        #       /  axis a0  \
        #   V4 =------------.- V1
        #      axis b0__--''
        #          _-'
        #        V3       V2
        #
        #
        if keepV0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(6)
            self.fold_g_6_vs(a0, b0, a1, b1, keepV0, self.VsOrg)

    def fold_g_6_vs(self, a0, b0, a1, b1, keepV0, Vs):
        v = [v for v in Vs]
        if keepV0:
            assert False, "TODO"
        else:
            # rot a0
            v4v1 = (v[4] + v[1]) / 2
            v4v1_axis = Vec(v[4] - v[1])
            rot_a0 = Rot(axis=v4v1_axis, angle=-a0)
            # middle of V5-V0 which is // to v4v1 axis
            v5v0 = (v[5] + v[0]) / 2
            v5v0_ = v4v1 + rot_a0 * (v5v0 - v4v1)
            v[5] = v5v0_ + (v[5] - v5v0)
            v[0] = v5v0_ + (v[0] - v5v0)
            v[6] = v4v1 + rot_a0 * (v[6] - v4v1)

            # rot a1
            v4v6 = (v[4] + v[6]) / 2
            v4v6_axis = Vec(v[4] - v[6])
            rot_a1 = Rot(axis=v4v6_axis, angle=-a1)
            v[5] = v4v6 + rot_a1 * (v[5] - v4v6)

            # rot b1
            v1v6 = (v[1] + v[6]) / 2
            v1v6_axis = Vec(v[1] - v[6])
            rot_b1 = Rot(axis=v1v6_axis, angle=b1)
            v[0] = v1v6 + rot_b1 * (v[0] - v1v6)

            # rot b0
            v1v3 = (v[1] + v[3]) / 2
            v1v3_axis = Vec(v[1] - v[3])
            rot_b0 = Rot(axis=v1v3_axis, angle=-b0)
            v[2] = v1v3 + rot_b0 * (v[2] - v1v3)

        self.Vs = v

    def translate(self, T):
        for i in range(len(self.Vs)):
            self.Vs[i] = T + self.Vs[i]

    def rotate(self, axis, angle):
        self.transform(Rot(axis=axis, angle=angle))

    def transform(self, T):
        for i in range(len(self.Vs)):
            self.Vs[i] = T * self.Vs[i]


def Kite2Hept(Left, Top, Right, Bottom, alt_hept_pos=False):
    """Return the a tuple with vertices and the normal of an equilateral
    heptagon for a kite, Vl, Vt, Vr, Vb; the tuple has the following structure:
    ([h0, h1, h2, h3, h4, h5, h6], normal), with h0 = Top.

    Left: left coordinate
    Top: top coordinate
    Right: right coordinate
    Bottom: bottom coordinate
    alt_hept_pos: 2 possible orientations for the heptagons exists. If false then the preferred
        position is returned, otherwise the heptagon will be 'upside down'.
    """
    if not alt_hept_pos:
        Vl = Vec(Left)
        Vt = Vec(Top)
        Vr = Vec(Right)
        Vb = Vec(Bottom)
    else:
        Vl = Vec(Right)
        Vt = Vec(Bottom)
        Vr = Vec(Left)
        Vb = Vec(Top)
    Vo = (Vl + Vr) / 2
    Dr = Vo - Vr
    Du = Vo - Vt
    w = Dr.norm()
    f = Du.norm()
    g = (Vo - Vb).norm()

    if f == 0:
        logging.warning("Kite2Hept: f == 0")
        return
    if w == 0:
        logging.warning("Kite2Hept: warning w == 0")
        return
    # if f > g:
    #    f, g = g, f

    V = lambda x: math.sqrt(x)

    r = f / w
    q = g / w
    n = V(1.0 + q * q) / 2
    m = V(1.0 + r * r) / 2
    k = m * (1.0 + 1.0 / n)

    qkpr = q * k + r
    root = k * (2 - k) + r * r

    # assert(root>=0)
    if root < 0:
        logging.warning("kite2Hept: negative sqrt requested")
        return

    nom = f + g
    denom = qkpr + V(root)

    if denom == 0:
        logging.warning("kite2Hept: denom == 0")
        return

    w1 = nom / denom

    w1Rel = w1 / w
    w2Rel = k * w1Rel
    w3Rel = m * w1Rel

    relPos = lambda v0, v1, rat: rat * (v1 - v0) + v0
    # h0 = Vt
    h1 = relPos(Vt, Vr, w1Rel)
    h2 = relPos(Vb, Vr, w2Rel)
    h3 = relPos(Vb, Vr, w3Rel)
    h4 = relPos(Vb, Vl, w3Rel)
    h5 = relPos(Vb, Vl, w2Rel)
    h6 = relPos(Vt, Vl, w1Rel)

    N = Dr.cross(Du).normalize()

    # C = (Vt + h1 + h2 + h3 + h4 + h5 + h6) / 7
    # return ([Vt, h1, h2, h3, h4, h5, h6], N)
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
            Vec([h6[0], h6[1], h6[2]]),
        ],
        Vec(N),
    )


class FldHeptagonShape(Geom3D.CompoundShape):
    def __init__(self, shapes, nFold=3, mFold=3, name="Folded Regular Heptagons"):
        self.nFold = nFold
        self.mFold = mFold
        self.altNFoldFace = False
        self.altMFoldFace = False
        Geom3D.CompoundShape.__init__(self, shapes, name=name)
        self.heptagon = RegularHeptagon()
        self.dihedralAngle = 1.2
        self.posAngleMin = 0
        self.posAngleMax = math.pi / 2
        self.posAngle = 0
        self.has_reflections = True
        self.rotate_fold = 0
        self.fold1 = 0.0
        self.fold2 = 0.0
        self.oppFold1 = 0.0
        self.oppFold2 = 0.0
        self.fold_heptagon = FoldMethod.PARALLEL
        self.height = 2.3
        self.apply_symmetries = True
        self.addXtraFs = True
        self.onlyRegFs = False
        self.useCulling = False
        self.updateShape = True

    def __repr__(self):
        # s = '%s(\n  ' % findModuleClassName(self.__class__, __name__)
        s = "FldHeptagonShape(\n  "
        s = "%sshapes = [\n" % (s)
        for shape in self.shapeElements:
            s = "%s    %s,\n" % (s, repr(shape))
        s = "%s  ],\n  " % s
        s = '%snFold = "%s",\n' % (s, self.nFold)
        s = '%smFold = "%s",\n' % (s, self.mFold)
        s = '%sname = "%s"\n' % (s, self.mFold)
        s = "%s)\n" % (s)
        if __name__ != "__main__":
            s = "%s.%s" % (__name__, s)
        return s

    def gl_draw(self):
        if self.updateShape:
            self.setV()
        Geom3D.CompoundShape.gl_draw(self)

    def setEdgeAlternative(self, alt=None, oppositeAlt=None):
        if alt is not None:
            self.edgeAlternative = alt
        if oppositeAlt is not None:
            self.oppEdgeAlternative = oppositeAlt
        self.updateShape = True

    def set_fold_method(self, method, update_shape=True):
        self.fold_heptagon = method
        self.updateShape = True

    def setRotateFold(self, step):
        self.rotate_fold = step
        self.updateShape = True

    def setDihedralAngle(self, angle):
        self.dihedralAngle = angle
        self.updateShape = True

    def setPosAngle(self, angle):
        self.posAngle = angle
        self.updateShape = True

    def set_tri_fill_pos(self, position):
        logging.warning("implement in derived class")

    def setFold1(self, angle=None, oppositeAngle=None):
        if angle is not None:
            self.fold1 = angle
        if oppositeAngle is not None:
            self.oppFold1 = oppositeAngle
        self.updateShape = True

    def setFold2(self, angle=None, oppositeAngle=None):
        if angle is not None:
            self.fold2 = angle
        if oppositeAngle is not None:
            self.oppFold2 = oppositeAngle
        self.updateShape = True

    def setHeight(self, height):
        self.height = height
        self.updateShape = True

    def edgeColor(self):
        glColor(0.5, 0.5, 0.5)

    def vertColor(self):
        glColor(0.7, 0.5, 0.5)

    def getStatusStr(self):
        return (
            "T = %02.2f, Angle = %01.2f rad, fold1 = %01.2f (%01.2f) "
            "rad, fold2 = %01.2f (%01.2f) rad"
            % (
                self.height,
                self.dihedralAngle,
                self.fold1,
                self.oppFold1,
                self.fold2,
                self.oppFold2,
            )
        )

    def getReflPosAngle(self):
        # meant to be implemented by child
        if self.edgeAlternative == TrisAlt.refl_1:
            return 0
        else:
            return self.posAngleMax

    def posHeptagon(self):
        self.heptagon.fold(
            self.fold1,
            self.fold2,
            self.oppFold1,
            self.oppFold2,
            keepV0=False,
            fold=self.fold_heptagon,
            rotate=self.rotate_fold,
        )
        self.heptagon.translate(HEPT_HEIGHT * geomtypes.UY)
        # Note: the rotation angle != the dihedral angle
        self.heptagon.rotate(-geomtypes.UX, geomtypes.QUARTER_TURN - self.dihedralAngle)
        self.heptagon.translate(self.height * geomtypes.UZ)
        if self.posAngle != 0:
            self.heptagon.rotate(-geomtypes.UZ, self.posAngle)

    def setV(self):
        self.posHeptagon()


class FldHeptagonCtrlWin(wx.Frame):
    refl_min_size = (525, 425)
    rot_min_size = (545, 600)
    pre_pos_file_name = None
    rotate_fold = 1
    _std_pre_pos = None
    _pre_pos_map = None
    _sym_incl_refl = True

    # in these the status for the triangle configuration is save (with of without reflections)
    tris_setup_refl = None
    tris_setup_no_refl = None

    def __init__(
            self,
            shape,
            canvas,
            maxHeight,
            pre_pos_strings,
            symmetryBase,
            triangle_alts,
            pre_pos_to_number,
            parent,
            *args,
            **kwargs,
    ):
        """Create a control window for the scene that folds heptagons

        shape: the Geom3D shape object that is shown
        canvas: wx canvas to be used
        maxHeight: max translation height to be used for the heptagon
        pre_pos_strings: a list with representation strings, used in the UI, with predefined models
            with regular folded heptagons. These models were calculated before and added to the
            program. For instance one of strings can be "Heptagons only" for a model with only
            regular folded heptagons.
        triangle_alts: an array consisting of TrisAlt_base derived objects. Each element in the
            array expresses which triangle fills are valid for the position with the same index as
            the element.
        pre_pos_to_number: a hash table that maps the strings from prePosStrList to unique numbers.
        *args: standard wx Frame *args
        **kwargs: standard wx Frame **kwargs
        """
        # TODO assert (type(shape) == type(RegHeptagonShape()))
        wx.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.shape = shape
        self.triangle_alts = triangle_alts
        self.nr_of_positions = len(triangle_alts)
        self.set_tri_fill_pos(0)
        self.canvas = canvas
        self.maxHeight = maxHeight
        self.pre_pos_strings = pre_pos_strings
        self.symBase = symmetryBase
        self.stringify = pre_pos_to_number
        self._saved_angle = {}
        # One of the items in the UI should an option to read from File.
        if not OPEN_FILE in pre_pos_to_number:
            self.stringify[OPEN_FILE] = "From File"
        self.panel = wx.Panel(self, -1)
        self.status_bar = self.CreateStatusBar()
        self.fold_method_incl_refl = {
            True: FoldMethod.TRIANGLE,
            False: FoldMethod.W,
        }
        self.restoreTris = False
        self.restoreO3s = False
        self.shape.set_fold_method(self.fold_method, update_shape=False)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.specPosIndex = 0

        self.main_sizer.Add(
            self.createControlsSizer(), 1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
        )
        self.set_default_size(self.refl_min_size)
        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.main_sizer)
        self.Show(True)
        self.panel.Layout()
        self.prevTrisFill = -1
        self.prevOppTrisFill = -1

    @property
    def fold_method(self):
        """Retrieve the current fold method."""
        return self.fold_method_incl_refl[self._sym_incl_refl]

    @fold_method.setter
    def fold_method(self, fold_method):
        """Set the current fold method."""
        self.fold_method_incl_refl[self._sym_incl_refl] = fold_method
        self.shape.set_fold_method(fold_method)

    def createControlsSizer(self):
        """Create the main sizer with all the control widgets."""
        self.heightF = 40  # slider step factor, or: 1 / slider step

        self.Guis = []

        # static adjustments
        self.tris_fill_gui = wx.Choice(self.panel, style=wx.RA_VERTICAL, choices=[])
        self.Guis.append(self.tris_fill_gui)
        self.tris_fill_gui.Bind(wx.EVT_CHOICE, self.onTriangleFill)
        self.update_triangle_fill_options()

        self.trisPosGui = wx.Choice(
            self.panel,
            style=wx.RA_VERTICAL,
            choices=["Position {}".format(i + 1) for i in range(self.nr_of_positions)],
        )
        self.Guis.append(self.trisPosGui)
        self.trisPosGui.Bind(wx.EVT_CHOICE, self.onTrisPosition)
        self.update_triangle_fill_options()

        self.reflGui = wx.CheckBox(self.panel, label="Reflections Required")
        self.Guis.append(self.reflGui)
        self.reflGui.SetValue(self.shape.has_reflections)
        self.reflGui.Bind(wx.EVT_CHECKBOX, self.onRefl)

        self.rotateFldGui = wx.Button(self.panel, label="Rotate Fold 1/7")
        self.rotate_fold = 0
        self.Guis.append(self.rotateFldGui)
        self.rotateFldGui.Bind(wx.EVT_BUTTON, self.onRotateFld)

        # View Settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        self.applySymGui = wx.CheckBox(self.panel, label="Apply Symmetry")
        self.Guis.append(self.applySymGui)
        self.applySymGui.SetValue(self.shape.apply_symmetries)
        self.applySymGui.Bind(wx.EVT_CHECKBOX, self.onApplySym)
        self.addTrisGui = wx.CheckBox(self.panel, label="Show Triangles")
        self.Guis.append(self.addTrisGui)
        self.addTrisGui.SetValue(self.shape.addXtraFs)
        self.addTrisGui.Bind(wx.EVT_CHECKBOX, self.onAddTriangles)

        # static adjustments
        self.fold_method_list = [
            FoldMethod.PARALLEL.name.capitalize(),
            FoldMethod.TRIANGLE.name.capitalize(),
            FoldMethod.SHELL.name.capitalize(),
            FoldMethod.W.name.capitalize(),
            FoldMethod.TRAPEZIUM.name.capitalize(),
            FoldMethod.MIXED.name.capitalize(),
            FoldMethod.G.name.capitalize(),
        ]
        self.foldMethodListItems = [FoldMethod.get(fold) for fold in self.fold_method_list]
        self.valid_fold_incl_refl = {
            True: [
                FoldMethod.PARALLEL.name.capitalize(),
                FoldMethod.TRIANGLE.name.capitalize(),
                FoldMethod.SHELL.name.capitalize(),
                FoldMethod.W.name.capitalize(),
                FoldMethod.TRAPEZIUM.name.capitalize(),
            ],
            False: [
                FoldMethod.SHELL.name.capitalize(),
                FoldMethod.W.name.capitalize(),
                FoldMethod.MIXED.name.capitalize(),
                FoldMethod.G.name.capitalize(),
            ],
        }

        self.fold_method_gui = wx.RadioBox(
            self.panel,
            label="Heptagon Fold Method",
            style=wx.RA_VERTICAL,
            choices=self.fold_method_list,
        )
        self.Guis.append(self.fold_method_gui)
        self.fold_method_gui.Bind(wx.EVT_RADIOBOX, self.on_fold_method)
        self.show_right_folds()

        # predefined positions
        self.pre_pos_gui = wx.Choice(
            self.panel,
            # label = 'Only Regular Faces with:',
            style=wx.RA_VERTICAL,
            choices=self.pre_pos_strings,
        )
        # Don't hardcode which index is DYN_POS, I might reorder the item list
        # one time, and will probably forget to update the default selection..
        for i in range(len(self.pre_pos_strings)):
            if self.pre_pos_strings[i] == self.stringify[DYN_POS]:
                self.pre_pos_gui.SetStringSelection(self.stringify[DYN_POS])
                break
        self.setEnablePrePosItems()
        self.Guis.append(self.pre_pos_gui)
        self.pre_pos_gui.Bind(wx.EVT_CHOICE, self.on_pre_pos)

        self.open_file_button = wx.Button(self.panel, label="Open File")
        self.first_button = wx.Button(self.panel, label="First")
        self.next_button = wx.Button(self.panel, label="Next")
        self.number_text = wx.Button(self.panel, label="---", style=wx.NO_BORDER)
        self.prev_button = wx.Button(self.panel, label="Prev")
        self.last_button = wx.Button(self.panel, label="Last")
        self.Guis.append(self.open_file_button)
        self.Guis.append(self.first_button)
        self.Guis.append(self.next_button)
        self.Guis.append(self.number_text)
        self.Guis.append(self.prev_button)
        self.Guis.append(self.last_button)
        self.open_file_button.Bind(wx.EVT_BUTTON, self.on_open_file)
        self.first_button.Bind(wx.EVT_BUTTON, self.onFirst)
        self.next_button.Bind(wx.EVT_BUTTON, self.onNext)
        self.prev_button.Bind(wx.EVT_BUTTON, self.onPrev)
        self.last_button.Bind(wx.EVT_BUTTON, self.onLast)

        # dynamic adjustments
        self.posAngleGui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.posAngle,
            minValue=Geom3D.Rad2Deg * self.shape.posAngleMin,
            maxValue=Geom3D.Rad2Deg * self.shape.posAngleMax,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.Guis.append(self.posAngleGui)
        self.posAngleGui.Bind(wx.EVT_SLIDER, self.onPosAngle)
        self.minFoldAngle = -180
        self.maxFoldAngle = 180
        self.dihedralAngleGui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.dihedralAngle,
            minValue=self.minFoldAngle,
            maxValue=self.maxFoldAngle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.Guis.append(self.dihedralAngleGui)
        self.dihedralAngleGui.Bind(wx.EVT_SLIDER, self.onDihedralAngle)
        self.fold1Gui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.fold1,
            minValue=self.minFoldAngle,
            maxValue=self.maxFoldAngle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.Guis.append(self.fold1Gui)
        self.fold1Gui.Bind(wx.EVT_SLIDER, self.onFold1)
        self.fold2Gui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.fold2,
            minValue=self.minFoldAngle,
            maxValue=self.maxFoldAngle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.Guis.append(self.fold2Gui)
        self.fold2Gui.Bind(wx.EVT_SLIDER, self.onFold2)
        self.fold1OppGui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.oppFold1,
            minValue=self.minFoldAngle,
            maxValue=self.maxFoldAngle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.Guis.append(self.fold1OppGui)
        self.fold1OppGui.Bind(wx.EVT_SLIDER, self.onFold1Opp)
        self.fold2OppGui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.oppFold2,
            minValue=self.minFoldAngle,
            maxValue=self.maxFoldAngle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.Guis.append(self.fold2OppGui)
        self.fold2OppGui.Bind(wx.EVT_SLIDER, self.onFold2Opp)
        self.heightGui = wx.Slider(
            self.panel,
            value=self.maxHeight - self.shape.height * self.heightF,
            minValue=-self.maxHeight * self.heightF,
            maxValue=self.maxHeight * self.heightF,
            style=wx.SL_VERTICAL,
        )
        self.Guis.append(self.heightGui)
        self.heightGui.Bind(wx.EVT_SLIDER, self.onHeight)
        if self.shape.has_reflections:
            self.disable_guis_for_refl(force=True)

        self.setOrientGui = wx.TextCtrl(self.panel)
        self.Guis.append(self.setOrientGui)
        self.setOrientButton = wx.Button(self.panel, label="Apply")
        self.Guis.append(self.setOrientButton)
        self.setOrientButton.Bind(wx.EVT_BUTTON, self.onSetOrient)
        self.cleanOrientButton = wx.Button(self.panel, label="Clean")
        self.Guis.append(self.cleanOrientButton)
        self.cleanOrientButton.Bind(wx.EVT_BUTTON, self.onCleanOrient)

        # Sizers
        self.Boxes = []

        # sizer with view settings
        self.Boxes.append(wx.StaticBox(self.panel, label="View Settings"))
        settings_sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        settings_sizer.Add(self.applySymGui, 0, wx.EXPAND)
        settings_sizer.Add(self.addTrisGui, 0, wx.EXPAND)
        settings_sizer.Add(self.reflGui, 0, wx.EXPAND)
        settings_sizer.Add(self.rotateFldGui, 0, wx.EXPAND)
        settings_sizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        # The sizers holding the special positions
        self.Boxes.append(wx.StaticBox(self.panel, label="Special Positions"))
        pos_sizer_sub_v = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        pos_sizer_sub_h = wx.BoxSizer(wx.HORIZONTAL)
        pos_sizer_sub_h.Add(self.open_file_button, 0, wx.EXPAND)
        pos_sizer_sub_h.Add(self.pre_pos_gui, 0, wx.EXPAND)
        pos_sizer_sub_v.Add(pos_sizer_sub_h, 0, wx.EXPAND)
        pos_sizer_sub_h = wx.BoxSizer(wx.HORIZONTAL)
        pos_sizer_sub_h.Add(self.first_button, 1, wx.EXPAND)
        pos_sizer_sub_h.Add(self.prev_button, 1, wx.EXPAND)
        pos_sizer_sub_h.Add(self.number_text, 1, wx.EXPAND)
        pos_sizer_sub_h.Add(self.next_button, 1, wx.EXPAND)
        pos_sizer_sub_h.Add(self.last_button, 1, wx.EXPAND)
        pos_sizer_sub_v.Add(pos_sizer_sub_h, 0, wx.EXPAND)
        pos_sizer_sub_v.Add(wx.BoxSizer(), 1, wx.EXPAND)
        pre_pos_sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        pre_pos_sizer_h.Add(pos_sizer_sub_v, 0, wx.EXPAND)
        pre_pos_sizer_h.Add(wx.BoxSizer(), 1, wx.EXPAND)

        # Alternatives of filling with triangles
        self.Boxes.append(wx.StaticBox(self.panel, label="Triangle Fill Alternative"))
        fillSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        fillSizer.Add(self.tris_fill_gui, 0, wx.EXPAND)
        fillSizer.Add(self.trisPosGui, 0, wx.EXPAND)

        statSizer = wx.BoxSizer(wx.HORIZONTAL)
        statSizer.Add(self.fold_method_gui, 0, wx.EXPAND)
        statSizer.Add(fillSizer, 0, wx.EXPAND)
        statSizer.Add(settings_sizer, 0, wx.EXPAND)
        statSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        pos_sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        # sizer holding the dynamic adjustments
        specPosDynamic = wx.BoxSizer(wx.VERTICAL)
        self.Boxes.append(wx.StaticBox(self.panel, label="Dihedral Angle (Degrees)"))
        angleSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
        angleSizer.Add(self.dihedralAngleGui, 1, wx.EXPAND)
        self.Boxes.append(wx.StaticBox(self.panel, label="Fold 1 Angle (Degrees)"))
        fold1Sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        fold1Sizer.Add(self.fold1Gui, 1, wx.EXPAND)
        self.Boxes.append(wx.StaticBox(self.panel, label="Fold 2 Angle (Degrees)"))
        fold2Sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        fold2Sizer.Add(self.fold2Gui, 1, wx.EXPAND)
        self.Boxes.append(wx.StaticBox(self.panel, label="Positional Angle (Degrees)"))
        posAngleSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
        posAngleSizer.Add(self.posAngleGui, 1, wx.EXPAND)
        self.Boxes.append(
            wx.StaticBox(self.panel, label="Opposite Fold 1 Angle (Degrees)")
        )
        oppFold1Sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        oppFold1Sizer.Add(self.fold1OppGui, 1, wx.EXPAND)
        self.Boxes.append(
            wx.StaticBox(self.panel, label="Opposite Fold 2 Angle (Degrees)")
        )
        oppFold2Sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        oppFold2Sizer.Add(self.fold2OppGui, 1, wx.EXPAND)

        self.Boxes.append(wx.StaticBox(self.panel, label="Offset T"))
        heightSizer = wx.StaticBoxSizer(self.Boxes[-1], wx.VERTICAL)
        heightSizer.Add(self.heightGui, 1, wx.EXPAND)
        specPosDynamic.Add(angleSizer, 0, wx.EXPAND)
        specPosDynamic.Add(fold1Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(fold2Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(posAngleSizer, 0, wx.EXPAND)
        specPosDynamic.Add(oppFold1Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(oppFold2Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(wx.BoxSizer(), 1, wx.EXPAND)
        pos_sizer_h.Add(specPosDynamic, 3, wx.EXPAND)
        pos_sizer_h.Add(heightSizer, 1, wx.EXPAND)

        self.Boxes.append(
            wx.StaticBox(self.panel, label="Set Orientation Directly (specify array)")
        )
        set_orientation_sizer = wx.StaticBoxSizer(self.Boxes[-1], wx.HORIZONTAL)
        set_orientation_sizer.Add(self.setOrientGui, 1, wx.EXPAND)
        set_orientation_sizer.Add(self.setOrientButton, 0, wx.EXPAND)
        set_orientation_sizer.Add(self.cleanOrientButton, 0, wx.EXPAND)

        # MAIN sizer
        main_sizer_v = wx.BoxSizer(wx.VERTICAL)
        main_sizer_v.Add(statSizer, 0, wx.EXPAND)
        main_sizer_v.Add(pre_pos_sizer_h, 0, wx.EXPAND)
        main_sizer_v.Add(pos_sizer_h, 0, wx.EXPAND)
        main_sizer_v.Add(set_orientation_sizer, 0, wx.EXPAND)
        main_sizer_v.Add(wx.BoxSizer(), 1, wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(main_sizer_v, 6, wx.EXPAND)

        self.error_msg = {
            "PosEdgeCfg": "ERROR: Impossible combination of position and edge configuration!"
        }

        return main_sizer

    def isPrePosValid(self, pre_pos_id):
        """Return True if the pre defined position is valid, False otherwise.

        Valid means here that the model has the right symmetry conform the current settings.
        """
        if self.shape.has_reflections:
            psp = self.predefReflSpecPos
        else:
            psp = self.predefRotSpecPos
        return pre_pos_id in psp

    def fileStrMapFoldMethodStr(self, filename):
        res = re.search(r"-fld_([^.]*)\.", filename)
        if res:
            return res.groups()[0]
        else:
            self.printFileStrMapWarning(filename, "fileStrMapFoldMethodStr")

    def fileStrMapFoldPosStr(self, filename):
        res = re.search(r"-fld_[^.]*\.([0-6])-.*", filename)
        if res:
            return res.groups()[0]
        else:
            self.printFileStrMapWarning(filename, "fileStrMapFoldPosStr")

    def fileStrMapHasReflections(self, filename):
        res = re.search(r".*frh-roots-(.*)-fld_.*", filename)
        if res:
            pos_vals = res.groups()[0].split("_")
            nr_pos = len(pos_vals)
            return (nr_pos == 4) or (nr_pos == 5 and pos_vals[4] == "0")
        else:
            self.printFileStrMapWarning(filename, "fileStrMapHasReflections")

    def fileStrMapTrisStr(self, filename):
        # New format: incl -pos:
        res = re.search(r"-fld_[^.]*\.[0-7]-([^.]*)\-pos-.*.json", filename)
        if res is None:
            # try old method:
            res = re.search(r"-fld_[^.]*\.[0-7]-([^.]*)\.json", filename)
        if res:
            tris_str = res.groups()[0]
            return self.trisAlt.mapFileStrOnStr[tris_str]
        else:
            self.printFileStrMapWarning(filename, "fileStrMapTrisStr")

    def fileStrMapTrisPos(self, filename):
        res = re.search(r"-fld_[^.]*\.[0-7]-[^.]*-pos-([0-9]*)\.json", filename)
        if res:
            tris_pos = res.groups()[0]
            return int(tris_pos)
        else:
            # try old syntax:
            res = re.search(r"-fld_[^.]*\.[0-7]-([^.]*)\.json", filename)
            if res:
                return 0
            else:
                self.printFileStrMapWarning(filename, "fileStrMapTrisPos")
                assert False

    def fileStrMapFoldPos(self, filename):
        res = re.search(r"-fld_[^.]*\.([0-7])-.*\.json", filename)
        if res:
            tris_pos = res.groups()[0]
            return int(tris_pos)
        else:
            return 0

    def setEnablePrePosItems(self):
        current_pre_pos = self.prePos
        self.pre_pos_gui.Clear()
        pre_pos_still_valid = False
        for pre_pos_str in self.pre_pos_strings:
            pre_pos_id = self.pre_pos_val(pre_pos_str)
            if self.isPrePosValid(pre_pos_id):
                self.pre_pos_gui.Append(pre_pos_str)
                if current_pre_pos == pre_pos_id:
                    pre_pos_still_valid = True
            else:
                if pre_pos_str == self.stringify[DYN_POS]:
                    self.pre_pos_gui.Append(pre_pos_str)
        if pre_pos_still_valid:
            self.pre_pos_gui.SetStringSelection(self.stringify[current_pre_pos])
        else:
            self.pre_pos_gui.SetStringSelection(self.stringify[DYN_POS])

    def rmControlsSizer(self):
        # The 'try' is necessary, since the boxes are destroyed in some OS,
        # while this is necessary for Ubuntu Hardy Heron.
        for Box in self.Boxes:
            try:
                Box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass
        for Gui in self.Guis:
            Gui.Destroy()

    def set_default_size(self, size):
        self.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        self.SetSize(size)

    def onPosAngle(self, event):
        self.shape.setPosAngle(Geom3D.Deg2Rad * self.posAngleGui.GetValue())
        self.status_bar.SetStatusText(self.shape.getStatusStr())
        self.updateShape()
        event.Skip()

    def onDihedralAngle(self, event):
        self.shape.setDihedralAngle(Geom3D.Deg2Rad * self.dihedralAngleGui.GetValue())
        self.status_bar.SetStatusText(self.shape.getStatusStr())
        self.updateShape()
        event.Skip()

    def onFold1(self, event):
        val = self.fold1Gui.GetValue()
        s_val = Geom3D.Deg2Rad * val
        if self.shape.has_reflections:
            self.shape.setFold1(s_val, s_val)
        else:
            self.shape.setFold1(s_val)
        self.status_bar.SetStatusText(self.shape.getStatusStr())
        self.updateShape()
        event.Skip()

    def onFold2(self, event):
        val = self.fold2Gui.GetValue()
        s_val = Geom3D.Deg2Rad * val
        if self.shape.has_reflections:
            self.shape.setFold2(s_val, s_val)
        else:
            self.shape.setFold2(s_val)
        self.status_bar.SetStatusText(self.shape.getStatusStr())
        self.updateShape()
        event.Skip()

    def onFold1Opp(self, event):
        self.shape.setFold1(oppositeAngle=Geom3D.Deg2Rad * self.fold1OppGui.GetValue())
        self.status_bar.SetStatusText(self.shape.getStatusStr())
        self.updateShape()
        event.Skip()

    def onFold2Opp(self, event):
        self.shape.setFold2(oppositeAngle=Geom3D.Deg2Rad * self.fold2OppGui.GetValue())
        self.status_bar.SetStatusText(self.shape.getStatusStr())
        self.updateShape()
        event.Skip()

    def onHeight(self, event):
        self.shape.setHeight(
            float(self.maxHeight - self.heightGui.GetValue()) / self.heightF
        )
        self.status_bar.SetStatusText(self.shape.getStatusStr())
        self.updateShape()
        event.Skip()

    def onCleanOrient(self, event):
        self.setOrientGui.SetValue("")

    def onSetOrient(self, event):
        inputStr = "ar = %s" % self.setOrientGui.GetValue()
        ed = {"__name__": "inputStr"}
        try:
            exec(inputStr, ed)
        except SyntaxError:
            self.status_bar.SetStatusText("Syntax error in input string")
            raise
        offset = ed["ar"][0]
        angle = ed["ar"][1]
        fold_1 = ed["ar"][2]
        fold_2 = ed["ar"][3]
        self.heightGui.SetValue(self.maxHeight - self.heightF * offset)
        self.dihedralAngleGui.SetValue(Geom3D.Rad2Deg * angle)
        self.fold1Gui.SetValue(Geom3D.Rad2Deg * fold_1)
        self.fold2Gui.SetValue(Geom3D.Rad2Deg * fold_2)
        inclRefl = len(ed["ar"]) <= 5
        self.shape.has_reflections = inclRefl
        self.reflGui.SetValue(inclRefl)
        if not inclRefl:
            self.enable_guis_for_no_refl()
            pos_angle = ed["ar"][4]
            opposite_fld1 = ed["ar"][5]
            opposite_fld2 = ed["ar"][6]
            self.fold1OppGui.SetValue(Geom3D.Rad2Deg * opposite_fld1)
            self.fold2OppGui.SetValue(Geom3D.Rad2Deg * opposite_fld2)
            self.posAngleGui.SetValue(Geom3D.Rad2Deg * pos_angle)
            self.shape.setPosAngle(pos_angle)
        else:
            self.disable_guis_for_refl()
            self.setReflPosAngle()
            opposite_fld1 = fold_1
            opposite_fld2 = fold_2
        self.shape.setDihedralAngle(angle)
        self.shape.setHeight(offset)
        self.shape.setFold1(fold_1, opposite_fld1)
        self.shape.setFold2(fold_2, opposite_fld2)
        self.status_bar.SetStatusText(self.shape.getStatusStr())
        self.updateShape()
        event.Skip()

    def onApplySym(self, _event):
        self.shape.apply_symmetries = self.applySymGui.IsChecked()
        self.shape.updateShape = True
        self.updateShape()

    def onAddTriangles(self, _event=None):
        self.shape.addXtraFs = self.addTrisGui.IsChecked()
        self.shape.updateShape = True
        self.updateShape()

    def allign_slide_bars_with_fold_method(self):
        """Enable and disable folding slide bars conform the current fold method"""
        if not self.shape.has_reflections:
            if self.fold_method == FoldMethod.PARALLEL:
                self.fold1OppGui.Disable()
                self.fold2OppGui.Disable()
            elif (
                    self.fold_method == FoldMethod.W
                    or self.fold_method == FoldMethod.SHELL
                    or self.fold_method == FoldMethod.MIXED
                    or self.fold_method == FoldMethod.G
            ):
                self.fold1OppGui.Enable()
                self.fold2OppGui.Enable()
            elif (
                    self.fold_method == FoldMethod.TRAPEZIUM
                    or self.fold_method == FoldMethod.TRIANGLE
            ):
                self.fold1OppGui.Disable()
                self.fold2OppGui.Enable()

    def setReflPosAngle(self):
        posAngle = self.shape.getReflPosAngle()
        self.shape.setPosAngle(posAngle)
        self.posAngleGui.SetValue(Geom3D.Rad2Deg * posAngle)

    def disableSlidersNoRefl(self):
        self.fold1OppGui.Disable()
        self.fold2OppGui.Disable()
        self.posAngleGui.Disable()
        # the code below is added to be able to check and uncheck "Has
        # Reflections" in a "undo" kind of way.
        self._saved_angle["opp_fold1"] = self.shape.oppFold1
        self._saved_angle["opp_fold2"] = self.shape.oppFold2
        self._saved_angle["pos_angle"] = self.shape.posAngle
        self.shape.setFold1(oppositeAngle=self.shape.fold1)
        self.shape.setFold2(oppositeAngle=self.shape.fold2)
        self.setReflPosAngle()
        self.fold1OppGui.SetValue(self.minFoldAngle)
        self.fold2OppGui.SetValue(self.minFoldAngle)

    def enableSlidersNoRefl(self, restore=True):
        self.allign_slide_bars_with_fold_method()
        self.posAngleGui.Enable()
        # the code below is added to be able to check and uncheck "Has
        # Reflections" in a "undo" kind of way.
        if restore:
            opp_fold1 = self._saved_angle["opp_fold1"]
            opp_fold2 = self._saved_angle["opp_fold2"]
            hept_angle = self._saved_angle["pos_angle"]
            self.shape.setFold1(oppositeAngle=opp_fold1)
            self.shape.setFold2(oppositeAngle=opp_fold2)
            self.shape.setPosAngle(hept_angle)
            self.fold1OppGui.SetValue(Geom3D.Rad2Deg * opp_fold1)
            self.fold2OppGui.SetValue(Geom3D.Rad2Deg * opp_fold2)
            self.posAngleGui.SetValue(Geom3D.Rad2Deg * hept_angle)

    def disable_guis_for_refl(self, force=False):
        """Disable some GUIs that aren't valid because reflections are required.

        For instance a pair of heptagons can be rotated around a 2-fold axis. If reflections is
        required, then there is only one position (0, 90, 180, etc degrees all lead to the same
        configuration). Some sliders for folding should be disabled as well. Also the heptagon folds
        must be symmetric and the cannot be rotated.

        Another thing that needs to be done is to update all the options for filling up the space
        between heptagons with triangles. Only fill configurations that have a mirror symmetry are
        valid.
        """
        if not self._sym_incl_refl or force:
            self.update_triangle_fill_options()
            self.trisPosGui.Disable()
            self.rotateFldGui.Disable()
            self.shape.setRotateFold(0)
            self.disableSlidersNoRefl()
            self._sym_incl_refl = True
            self.update_fold_selection()

    def enable_guis_for_no_refl(self, restore=True):
        """Enable some GUIs that aren't valid because no reflections are needed.

        See disable_guis_for_refl for more info.
        """
        if self._sym_incl_refl:
            self.update_triangle_fill_options()
            self.trisPosGui.Enable()
            self.rotateFldGui.Enable()
            self.shape.setRotateFold(self.rotate_fold)
            self.enableSlidersNoRefl(restore)
            self._sym_incl_refl = False
            self.update_fold_selection()

    def disableTrisFillGuis(self):
        self.addTrisGui.Disable()
        self.tris_fill_gui.Disable()

    def enableTrisFillGuis(self):
        self.addTrisGui.Enable()
        self.tris_fill_gui.Enable()

    def onRefl(self, event=None):
        self.shape.has_reflections = self.reflGui.IsChecked()
        self.shape.updateShape = True
        self.show_right_folds()
        self.setEnablePrePosItems()
        if self.shape.has_reflections:
            self.set_default_size(self.refl_min_size)
        else:
            self.set_default_size(self.rot_min_size)
        if event is not None:
            if self.is_pre_pos():
                self.pre_pos_gui.SetStringSelection(self.stringify[DYN_POS])
                if not self.shape.has_reflections:
                    self._saved_angle["opp_fold1"] = self.shape.fold1
                    self._saved_angle["opp_fold2"] = self.shape.fold2
                self.on_pre_pos(event)
            else:
                if self.shape.has_reflections:
                    self.tris_setup_no_refl = self.tris_fill_gui.GetStringSelection()
                    self.disable_guis_for_refl()
                else:
                    self.tris_setup_refl = self.tris_fill_gui.GetStringSelection()
                    self.enable_guis_for_no_refl()
                self.status_bar.SetStatusText(self.shape.getStatusStr())
                self.updateShape()

    # TODO: make this a property and use a setter here
    def setRotateFld(self, rotate_fold):
        """Set the offset for the heptagon rotation.

        For models without reflections a heptagon fold can be rotated to 7 different orientations.
        rotate_fold: offset between 0 and 7
        """
        self.rotate_fold = int(rotate_fold) % 7
        self.shape.setRotateFold(self.rotate_fold)
        self.rotateFldGui.SetLabel("Rotate Fold %d/7" % (self.rotate_fold + 1))
        self.updateShape()

    def onRotateFld(self, event):
        self.setRotateFld(self.rotate_fold + 1)

    def is_pre_pos(self):
        """Return whether the UI currently shows a pre-defined model.

        A pre-defines model is one of the model for which all the values are calculated already and
        added to the program. It is certain special properties, e.g. it only consists of regular
        folded heptagon.
        """
        # TODO: move to offspring
        # FIXME TODO the string 'Enable Sliders' should be a constant and be
        # imported and used in the Scenes.. (or move to offspring..)
        return self.pre_pos_gui.GetStringSelection() != "Enable Sliders"

    def set_tri_fill_pos(self, position):
        """Sets which triangle fills are valid for the current 2-fold rotation.

        When a pair of heptagons is rotated around a 2-fold axis (only when no reflections are
        required) then certain triangle fills don't make sense. The same configuration could be
        used, but then by connection different vertices. This leads to certain positions for these
        triangle fills. This functions sets which position is supposed to be used.

        Note that you have to call update_triangle_fill_options to apply these
        settings to the GUI.

        position: an index in self.triangle_alts
        """
        if position < 0:
            position = 0
        if position >= self.nr_of_positions:
            position = self.nr_of_positions - 1
        self.position = position
        self.trisAlt = self.triangle_alts[self.position]
        self.shape.set_tri_fill_pos(position)

    def update_triangle_fill_options(self):
        """Fill the triangle fill GUI with valid options.

        Update the list with configurations for filling the space between heptagons with triangles.
        conform the symmetry. If the model is supposed to have reflections then many configurations
        become invalid. If the user just removed the reflections again, many configurations need to
        be added again.
        """
        # first time fails
        try:
            current_val = self.trisAlt.key[self.tris_fill_gui.GetStringSelection()]
        except KeyError:
            current_val = self.trisAlt.strip_I
        if self.shape.has_reflections:
            isValid = lambda c: self.trisAlt.isBaseKey(self.trisAlt.key[c])
            if not self.trisAlt.isBaseKey(current_val):
                if self.tris_setup_refl is None:
                    # TODO: use the first one that is valid
                    current_val = self.trisAlt.strip_I
                else:
                    current_val = self.trisAlt.key[self.tris_setup_refl]
        else:

                def isValid(c):
                    c_key = self.trisAlt.key[c]
                    if self.trisAlt.isBaseKey(c_key) or isinstance(c_key, int):
                        return False
                    else:
                        return True

                if not isValid(self.trisAlt.stringify[current_val]):
                    if self.tris_setup_no_refl is None:
                        # TODO: use the first one that is valid
                        current_val = self.trisAlt.strip_I_strip_I
                    else:
                        current_val = self.trisAlt.key[self.tris_setup_no_refl]

        self.tris_fill_gui.Clear()
        current_still_valid = False
        for choice in self.trisAlt.choiceList:
            if isValid(choice):
                self.tris_fill_gui.Append(choice)
                if current_val == self.trisAlt.key[choice]:
                    current_still_valid = True
                lastValid = choice

        if current_still_valid:
            self.tris_fill_gui.SetStringSelection(self.trisAlt.stringify[current_val])
        else:
            try:
                self.tris_fill_gui.SetStringSelection(lastValid)
            except UnboundLocalError:
                # None are valid...
                return
        self.shape.setEdgeAlternative(self.tris_fill, self.opp_tris_fill)

    @property
    def tris_fill(self):
        """Return the current triangle fill setup.

        If the polyhedron is setup not to have any relfections, then return only for one side
        """
        s = self.tris_fill_gui.GetStringSelection()
        if s == "":
            return None
        t = self.trisAlt.key[s]
        if self.shape.has_reflections:
            return t
        else:
            return t[0]

    @property
    def opp_tris_fill(self):
        """Return the current triangle fill setup for the opposite side (of tris_fill).

        If the polyhedron is setup to have relfections, then return the save as for tris_fill).
        """
        t = self.trisAlt.key[self.tris_fill_gui.GetStringSelection()]
        if self.shape.has_reflections:
            return t
        else:
            return t[1]

    def nvidea_workaround_0(self):
        self.prevTrisFill = self.shape.edgeAlternative
        self.prevOppTrisFill = self.shape.oppEdgeAlternative

    def nvidea_workaround(self):
        restoreMyShape = (
            self.prevTrisFill == self.trisAlt.twist_strip_I
            and self.prevOppTrisFill == self.trisAlt.twist_strip_I
            and self.tris_fill != self.trisAlt.twist_strip_I
            and self.opp_tris_fill != self.trisAlt.twist_strip_I
        )
        changeMyShape = (
            self.tris_fill == self.trisAlt.twist_strip_I
            and self.opp_tris_fill == self.trisAlt.twist_strip_I
        )
        if changeMyShape:
            if (
                    self.prevTrisFill != self.trisAlt.twist_strip_I
                    and self.prevOppTrisFill != self.trisAlt.twist_strip_I
            ):
                logging.info("---------nvidia-seg-fault-work-around-----------")
                self.nvidea_workaround_0()
            self.shape.setV()  # make sure the shape is updated
            shape = FldHeptagonShape(
                self.shape.shapes,
                self.shape.nFold,
                self.shape.mFold,
                name=self.shape.name,
            )
            shape.altNFoldFace = self.shape.altNFoldFace
            shape.altMFoldFace = self.shape.altMFoldFace
            shape.heptagon = self.shape.heptagon
            shape.dihedralAngle = self.shape.dihedralAngle
            shape.posAngleMin = self.shape.posAngleMin
            shape.posAngleMax = self.shape.posAngleMax
            shape.posAngle = self.shape.posAngle
            shape.has_reflections = self.shape.has_reflections
            shape.rotate_fold = self.shape.rotate_fold
            shape.fold1 = self.shape.fold1
            shape.fold2 = self.shape.fold2
            shape.oppFold1 = self.shape.oppFold1
            shape.oppFold2 = self.shape.oppFold2
            shape.fold_heptagon[self._sym_incl_refl] = self.shape.fold_heptagon
            shape.height = self.shape.height
            shape.apply_symmetries = self.shape.apply_symmetries
            shape.addXtraFs = self.shape.addXtraFs
            shape.onlyRegFs = self.shape.onlyRegFs
            shape.useCulling = self.shape.useCulling
            shape.edgeAlternative = self.tris_fill
            shape.oppEdgeAlternative = self.opp_tris_fill
            shape.updateShape = True
            self.canvas.shape = shape
        elif restoreMyShape:
            self.parent.panel.shape = self.shape

    def updateShape(self):
        self.nvidea_workaround()
        self.canvas.paint()

    def onTriangleFill(self, event=None):
        self.nvidea_workaround_0()
        self.shape.setEdgeAlternative(self.tris_fill, self.opp_tris_fill)
        if event is not None:
            if self.is_pre_pos():
                self.on_pre_pos(event)
            else:
                if self.shape.has_reflections:
                    self.setReflPosAngle()
                self.status_bar.SetStatusText(self.shape.getStatusStr())
            self.updateShape()

    @property
    def tris_position(self):
        # Note these are called "Position <int>"
        selected = self.trisPosGui.GetSelection()
        # If nothing selected (after changing from having reflections)
        if selected < 0:
            selected = 0
        return selected

    @tris_position.setter
    def tris_position(self, value):
        self.trisPosGui.SetSelection(value)
        self.onTrisPosition()

    def onTrisPosition(self, event=None):
        self.set_tri_fill_pos(self.tris_position)
        self.update_triangle_fill_options()
        self.updateShape()

    def show_right_folds(self):
        """Hide and show the fold method conform the current symmetry"""
        valid_names = self.valid_fold_incl_refl[self.shape.has_reflections]
        is_valid = [False for _ in self.fold_method_list]
        for name in valid_names:
            i = self.fold_method_list.index(name)
            is_valid[i] = True
        for i, show in enumerate(is_valid):
            self.fold_method_gui.ShowItem(i, show)

    def update_fold_selection(self):
        """Update the GUI to select a fold method conform the symmetry."""
        for i, fold in enumerate(self.fold_method_list):
            if fold.upper() == self.fold_method.name:
                self.fold_method_gui.SetSelection(i)
                break

    def on_fold_method(self, event=None):
        """Handle the selection of a new fold method"""
        self.fold_method = self.foldMethodListItems[self.fold_method_gui.GetSelection()]
        self.allign_slide_bars_with_fold_method()
        if event is not None:
            if self.is_pre_pos():
                self.on_pre_pos(event)
            else:
                self.status_bar.SetStatusText(self.shape.getStatusStr())
            self.updateShape()

    def onFirst(self, event=None):
        self.specPosIndex = 0
        self.on_pre_pos()

    def onLast(self, event=None):
        self.specPosIndex = -1
        self.on_pre_pos()

    def pre_pos_val(self, key):
        """Map a position string onto the position number."""
        if not self._pre_pos_map:
            self._pre_pos_map = {v: k for k, v in self.stringify.items()}
        try:
            return self._pre_pos_map[key]
        except KeyError:
            # Happens when switching from Open File to Only Hepts e.g.
            return -1

    @property
    def prePos(self):
        return self.pre_pos_val(self.pre_pos_gui.GetStringSelection())

    def open_pre_pos_file(self, filename):
        with open(filename, "r") as fd:
            data = json.load(fd)
        assert type(data) == list, f"Expected a JSON holding a list, got {type(data)}"
        for l in data:
            assert len(l) in (
                4,
                5,
                7,
            ), f"Expected elements with a length 4 or 7, got {len(l)}"
            for i in l:
                assert type(i) in (int, float), "Expected a number, got {type(i)}"
        return data

    def noPrePosFound(self):
        s = "Note: no valid pre-defined positions found"
        logging.info(s)
        self.status_bar.SetStatusText(s)

    @property
    def std_pre_pos(self):
        if self._std_pre_pos:
            return self._std_pre_pos
        pre_pos_id = self.prePos
        if pre_pos_id == DYN_POS:
            return []
        if pre_pos_id == OPEN_FILE:
            filename = self.pre_pos_file_name
            if filename is None:
                return []
            self._std_pre_pos = self.open_pre_pos_file(filename)
            return self._std_pre_pos
        else:
            # use correct predefined special positions
            if self.shape.has_reflections:
                psp = self.predefReflSpecPos
            else:
                psp = self.predefRotSpecPos
            # Oops not good for performance:
            # TODO only return correct one en add length func
            self._std_pre_pos = [sp["set"] for sp in psp[self.prePos]]
            return self._std_pre_pos

    def onPrev(self, event=None):
        if self.std_pre_pos != []:
            if self.specPosIndex > 0:
                self.specPosIndex -= 1
            elif self.specPosIndex == -1:
                self.specPosIndex = len(self.std_pre_pos) - 2
            # else pre_pos_id == 0 : first one selected don't scroll around
            self.on_pre_pos()
        else:
            self.noPrePosFound()

    def onNext(self, event=None):
        if self.std_pre_pos != []:
            try:
                max_i = len(self.std_pre_pos) - 1
                if self.specPosIndex >= 0:
                    if self.specPosIndex < max_i - 1:
                        self.specPosIndex += 1
                    else:
                        self.specPosIndex = -1  # select last
            except KeyError:
                pass
            self.on_pre_pos()
        else:
            self.noPrePosFound()

    def showOnlyHepts(self):
        return self.prePos == ONLY_HEPTS

    def showOnlyO3Tris(self):
        return self.prePos == ONLY_XTRA_O3S

    def choose_file(self):
        filename = None
        dlg = wx.FileDialog(
            self, "New: Choose a file", self.rDir, "", "*.json", wx.FD_OPEN
        )
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        dlg.Destroy()
        return filename

    def on_open_file(self, e):
        filename = self.choose_file()
        if filename is None:
            return
        logging.info("Opening file: %s", filename)
        self.pre_pos_file_name = filename
        self.fold_method_gui.SetStringSelection(
            self.fileStrMapFoldMethodStr(self.pre_pos_file_name)
        )
        self.on_fold_method()
        self.setRotateFld(self.fileStrMapFoldPosStr(self.pre_pos_file_name))
        # Note: Reflections need to be set before triangle fill, otherwise the
        # right triangle fills are not available
        has_reflections = self.fileStrMapHasReflections(self.pre_pos_file_name)
        self.reflGui.SetValue(has_reflections)
        self.onRefl()
        # not needed: self.shape.updateShape = True
        self.update_triangle_fill_options()
        self.tris_fill_gui.SetStringSelection(self.fileStrMapTrisStr(self.pre_pos_file_name))
        self.onTriangleFill()
        self.tris_position = self.fileStrMapTrisPos(self.pre_pos_file_name)
        # it's essential that pre_pos_gui is set to dynamic be4 std_pre_pos is read
        # otherwise something else than dynamic might be read...
        open_file_str = self.stringify[OPEN_FILE]
        if not open_file_str in self.pre_pos_gui.GetItems():
            self.pre_pos_gui.Append(open_file_str)
        self.pre_pos_gui.SetStringSelection(open_file_str)
        self.reset_std_pre_pos()
        self.on_pre_pos()

    def update_shape_settings(self, setting):
        """Update the shape with the new settings from a JSON file."""
        if setting == []:
            return

        if self.specPosIndex >= len(setting):
            self.specPosIndex = len(setting) - 1
        offset = setting[self.specPosIndex][0]
        angle = setting[self.specPosIndex][1]
        fold_1 = setting[self.specPosIndex][2]
        fold_2 = setting[self.specPosIndex][3]
        v_str = "[offset, dihedral_angle, fold_1, fold_2"
        dbg_str = f"  [{offset:.12f}, {angle:.12f}, {fold_1:.12f}, {fold_2:.12f}"
        if len(setting[self.specPosIndex]) > 4:
            pos_angle = setting[self.specPosIndex][4]
        else:
            pos_angle = 0
        if len(setting[self.specPosIndex]) > 5:
            opposite_fld1 = setting[self.specPosIndex][5]
            opposite_fld2 = setting[self.specPosIndex][6]
            v_str += ", positional_angle, opposite_fold_1, opposite_fold_2] ="
            dbg_str += ", {:.12f}, {:.12f}, {:.12f}]".format(
                pos_angle, opposite_fld1, opposite_fld2
            )
        else:
            opposite_fld1 = fold_1
            opposite_fld2 = fold_2
            v_str += "] ="
            dbg_str += "]"
        logging.info(v_str)
        logging.info(dbg_str)
        # Ensure self.specPosIndex in range:

        no_of_pos = len(setting)
        max_i = no_of_pos - 1
        if self.specPosIndex > max_i:
            self.specPosIndex = max_i
        # keep -1 (last) so switching triangle alternative will keep
        # last selection.
        elif self.specPosIndex < -1:
            self.specPosIndex = max_i - 1
        self.shape.setDihedralAngle(angle)
        self.shape.setHeight(offset)
        self.shape.setFold1(fold_1, opposite_fld1)
        self.shape.setFold2(fold_2, opposite_fld2)
        self.shape.setPosAngle(pos_angle)
        # For the user: start counting with '1' instead of '0'
        if self.specPosIndex == -1:
            nr = no_of_pos  # last position
        else:
            nr = self.specPosIndex + 1
        # set nr of possible positions
        self.number_text.SetLabel("%d/%d" % (nr, no_of_pos))
        self.status_bar.SetStatusText(self.shape.getStatusStr())
        # self.shape.printTrisAngles()

    def reset_std_pre_pos(self):
        """Update status so that no predefined heptagon fold is used"""
        self._std_pre_pos = None

    tNone = 1.0
    aNone = 0.0
    fld1None = 0.0
    fld2None = 0.0

    @property
    def special_pos_setup(self):
        """For the current pre-defined position return the configuration.

        return a dict with the following fields:
            set: the values for the sliders
            7fold: the fold method used for the heptagon, see FoldMethod
            tris: the configuration of the extra triangles
            fold-rot: the orientation of the heptagon fold method.
        """
        raise NotImplementedError("should be implemented by sub-class")

    def on_pre_pos(self, event=None):
        """Update GUI conform the current pre-defined position.

        Update all sliders, heptagon fold, triangle alternative etc and the shape itself.
        """
        c = self.shape
        # remove the "From File" from the pull down list as soon as it is
        # deselected
        if event is not None and self.prePos != OPEN_FILE:
            open_file = self.stringify[OPEN_FILE]
            n = self.pre_pos_gui.FindString(open_file)
            if n >= 0:
                # deleting will reset the selection, so save and reselect:
                selection = self.pre_pos_gui.GetSelection()
                self.pre_pos_gui.Delete(self.pre_pos_gui.FindString(open_file))
                self.pre_pos_gui.SetSelection(selection)
        if self.prePos == DYN_POS:
            if event is not None:
                self.pre_pos_file_name = None
            if self.restoreTris:
                self.restoreTris = False
                self.shape.addXtraFs = self.addTrisGui.IsChecked()
                self.shape.updateShape = True
            if self.restoreO3s:
                self.restoreO3s = False
                self.shape.onlyRegFs = False
                self.shape.updateShape = True
            self.number_text.SetLabel("---")
        elif self.prePos != OPEN_FILE:
            # this block is run for predefined spec pos only:
            if self.showOnlyHepts():
                self.shape.addXtraFs = False
                self.restoreTris = True
            elif self.restoreTris:
                self.restoreTris = False
                self.shape.addXtraFs = self.addTrisGui.IsChecked()
            if self.showOnlyO3Tris():
                self.shape.onlyRegFs = True
                self.restoreO3s = True
            elif self.restoreO3s:
                self.restoreO3s = False
                self.shape.onlyRegFs = False

            # get fold, tris alt
            sps = self.special_pos_setup
            self.fold_method_gui.SetStringSelection(sps["7fold"].name.capitalize())
            self.tris_fill_gui.SetStringSelection(self.trisAlt.stringify[sps["tris"]])
            try:
                self.tris_position = sps["tris-pos"]
            except KeyError:
                self.tris_position = 0
            try:
                rotate_fold = sps["fold-rot"]
            except KeyError:
                rotate_fold = 0
            self.setRotateFld(rotate_fold)

            self.on_fold_method()
            self.onTriangleFill()

            for gui in [
                    self.dihedralAngleGui,
                    self.posAngleGui,
                    self.heightGui,
                    self.fold1Gui,
                    self.fold2Gui,
                    self.fold1OppGui,
                    self.fold2OppGui,
            ]:
                gui.SetValue(0)
                gui.Disable()
            if not self.shape.has_reflections:
                self.enable_guis_for_no_refl()
            else:
                self.disable_guis_for_refl()
        if self.prePos != DYN_POS:
            if event is not None:
                self.reset_std_pre_pos()
            setting = self.std_pre_pos
            if setting == []:
                self.noPrePosFound()
                return
            # Note if the setting array uses a none symmetric setting, then the
            # shape will not be symmetric. This is not supposed to be handled
            # here: don't overdo it!
            self.update_shape_settings(setting)
        # for OPEN_FILE it is important that updateShapeSettins is done before
        # updating the sliders...
        if self.prePos == DYN_POS or self.prePos == OPEN_FILE:
            for gui in [
                    self.dihedralAngleGui,
                    self.posAngleGui,
                    self.heightGui,
                    self.fold1Gui,
                    self.fold2Gui,
                    self.fold1OppGui,
                    self.fold2OppGui,
            ]:
                gui.Enable()
            self.dihedralAngleGui.SetValue(Geom3D.Rad2Deg * c.dihedralAngle)
            # Showing triangles is the most general way of showing
            self.addTrisGui.SetValue(wx.CHK_CHECKED)
            self.onAddTriangles()
            self.posAngleGui.SetValue(Geom3D.Rad2Deg * c.posAngle)
            val1 = Geom3D.Rad2Deg * c.fold1
            val2 = Geom3D.Rad2Deg * c.fold2
            self.fold1Gui.SetValue(val1)
            self.fold2Gui.SetValue(val2)
            val1 = Geom3D.Rad2Deg * c.oppFold1
            val2 = Geom3D.Rad2Deg * c.oppFold2
            self.fold1OppGui.SetValue(val1)
            self.fold2OppGui.SetValue(val2)
            if not self.shape.has_reflections:
                self.enable_guis_for_no_refl(restore=False)
            self.heightGui.SetValue(self.maxHeight - self.heightF * c.height)
            self.update_triangle_fill_options()
        self.updateShape()


class EqlHeptagonShape(Geom3D.SymmetricShapeSplitCols):
    """The class defines a base for defining shapes with equilateral polyhedra.

    It should be seen as an abstract base class, for which set_vs needs to be implemented.
    """
    def __init__(
            self,
            base_isometries=None,
            extra_isometry=None,
            name="EqlHeptagonShape",
    ):
        """
        Define a shape with many equilateral heptagons.

        base_isometries: the isometries to apply to the basic equilateral heptagon
        extra_isometry: an extra isometry that is applied to all isometries.
            This will double the amount of isometries.
        name: the name to be used for this shape.
        """
        if base_isometries is None:
            base_isometries = [geomtypes.E]
        isometries = base_isometries.copy()
        if extra_isometry is not None:
            for i in base_isometries:
                isometries.append(extra_isometry * i)

        super().__init__(Vs=[], Fs=[], isometries=isometries, name=name)
        self.show_kite = True
        self.show_hepta = False
        self.alt_hept_pos = False
        self.show_extra = False
        self.tri_alt = True
        self.add_extra_edge = True
        self.error_msg = ""
        self.opaqueness = 1.0
        self.update_vs = False
        self._angle = 0
        self._height = 0

        kite_col = rgb.oliveDrab[:]
        hept_col = rgb.oliveDrab[:]
        extra_col = rgb.brown[:]
        self.face_col = [hept_col, kite_col, extra_col]

    def set_vs(self):
        """
        Set the vertex array, implemented by derivative
        """

    @property
    def height(self):
        """The the height of a reference vertex of the kite.

        The vertex is on the main diagonal and normally it can be shared with the centre of the
        polygon of the polyhedron it is based on.
        """
        return self._height

    @height.setter
    def height(self, h):
        # using an extra level to be able to overwrite in subclass
        self.set_height(h)

    def set_height(self, h):
        """Position the kite by setting the height of a vertex.

        This function can be overwritten by a sub-class.
        """
        self._height = h
        self.set_vs()

    @property
    def angle(self):
        """Return the angle in degrees between the kite and a reference plane.

        Normally the reference planes goes throught the cross diagonal.
        """
        return self._angle

    @angle.setter
    def angle(self, a):
        # using an extra level to be able to overwrite in subclass
        self.set_angle(a)

    def set_angle(self, a):
        """Set the angle of the kite in degrees.

        This function can be overwritten by a sub-class.
        """
        self._angle = a
        self.set_vs()

    def update_view_opt(
            self,
            show_kite=None,
            show_hepta=None,
            show_extra=None,
            tri_alt=None,
            add_extra_edge=None,
            alt_hept_pos=None,
            opaqueness=None,
    ):
        """Update options of how the shape should be drawn.

        Repaint the canvas after this.
        """
        if show_kite is not None:
            self.show_kite = show_kite
        if show_hepta is not None:
            self.show_hepta = show_hepta
        if show_extra is not None:
            self.show_extra = show_extra
        if alt_hept_pos is not None:
            self.alt_hept_pos = alt_hept_pos
        if tri_alt is not None:
            self.tri_alt = tri_alt
            self.update_vs = True
        if add_extra_edge is not None:
            self.add_extra_edge = add_extra_edge
        if opaqueness is not None:
            # TODO...
            self.opaqueness = opaqueness
        if (
                show_kite is not None  # not so efficient perhaps, but works..
                or show_hepta is not None  # not so efficient perhaps, but works..
                or show_extra is not None  # not so efficient perhaps, but works..
                or alt_hept_pos is not None
                or add_extra_edge is not None
        ):
            self.set_vs()

    def gl_init(self):
        """Set up OpenGL."""
        super().gl_init()
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def get_status_msg(self):
        """Return a string expressing the current status."""
        if not self.error_msg:
            return f"Height = {self.height:.2f}, Angle = {self.angle:.1f} degrees"
        return self.error_msg


class EqlHeptagonCtrlWin(wx.Frame):
    """Common class for controlling equilateral heptagons."""
    KITE_ANGLE_STEPS = 200

    kite_angle_factor = 1
    kite_angle_offset = 1

    def __init__(self, shape, canvas, size, *args, **kwargs):
        assert isinstance(shape, EqlHeptagonShape)
        self.shape = shape
        self.canvas = canvas
        wx.Frame.__init__(self, *args, **kwargs)
        self.panel = wx.Panel(self, -1)
        self.status_bar = self.CreateStatusBar()
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(
            self.create_ctrl_sizer(), 1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
        )
        self.set_default_size(size)
        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.main_sizer)
        self.Show(True)
        self.panel.Layout()

    def set_kite_angle_domain(self, min_angle, max_angle):
        """Set minimum and maximum angle for a kite.

        The kite angle is the angle of a kite with a face of the base model.

        min_angle: mimimum kite angle in degrees
        max_angle: maximum kite angle in degrees
        """
        # Linear mapping of [0, self.KITE_ANGLE_STEPS] ->
        #                   [min, max]
        #
        # min: minimal angle in degrees
        # max: maximum angle in degrees
        # self.KITE_ANGLE_STEPS: the amount of steps in the slider.
        # y = x * (max - min)/self.KITE_ANGLE_STEPS + min
        self.kite_angle_factor = (max_angle - min_angle) / self.KITE_ANGLE_STEPS
        self.kite_angle_offset = min_angle
        # inverse:
        # x = ( y - min ) /  self.kite_angle_factor

    def get_angle_val(self, x):
        """convert a slider value to a kite angle (degrees) value.

        x: the slider value to be converted
        """
        return self.kite_angle_factor * float(x) + self.kite_angle_offset

    def get_slider_val(self, angle):
        """convert an angle to a slider value.

        angle: signed angle (in degrees) of the kite with a face of the base model.
        """
        return (angle - self.kite_angle_offset) / self.kite_angle_factor

    def create_ctrl_sizer(self):
        """Create and return the main sizer with all the control widgets."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # GUI for dynamic adjustment
        self.kite_angle_gui = wx.Slider(
            self.panel,
            value=self.get_slider_val(self.shape.angle),
            minValue=0,
            maxValue=self.KITE_ANGLE_STEPS,
            style=wx.SL_HORIZONTAL,
        )
        self.panel.Bind(
            wx.EVT_SLIDER, self.on_kite_angle, id=self.kite_angle_gui.GetId()
        )
        self.kite_angle_box = wx.StaticBox(self.panel, label="Kite Angle")
        self.kite_angle_sizer = wx.StaticBoxSizer(self.kite_angle_box, wx.HORIZONTAL)
        self.kite_angle_sizer.Add(self.kite_angle_gui, 1, wx.EXPAND)
        self.status_bar.SetStatusText(self.shape.get_status_msg())

        # GUI for general view settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        self.view_kite_gui = wx.CheckBox(self.panel, label="Show kite")
        self.view_kite_gui.SetValue(self.shape.show_kite)
        self.view_hept_gui = wx.CheckBox(self.panel, label="Show heptagon")
        self.view_hept_gui.SetValue(self.shape.show_hepta)
        self.add_extra_face_gui = wx.CheckBox(self.panel, label="Show extra faces")
        self.add_extra_face_gui.SetValue(self.shape.show_extra)
        self.add_extra_edge_gui = wx.CheckBox(self.panel, label="Add extra edge (if extra face)")
        self.add_extra_edge_gui.SetValue(self.shape.add_extra_edge)
        self.tri_alt_gui = wx.CheckBox(self.panel, label="Triangle alternative (if extra face)")
        self.tri_alt_gui.SetValue(self.shape.tri_alt)
        self.alt_hept_pos_gui = wx.CheckBox(
            self.panel, label="Use alternative heptagon position"
        )
        self.alt_hept_pos_gui.SetValue(self.shape.alt_hept_pos)
        self.panel.Bind(wx.EVT_CHECKBOX, self.on_view_settings_chk)
        self.view_opt_box = wx.StaticBox(self.panel, label="View settings")
        self.view_opt_sizer = wx.StaticBoxSizer(self.view_opt_box, wx.VERTICAL)

        self.view_opt_sizer.Add(self.view_kite_gui, 1, wx.EXPAND)
        self.view_opt_sizer.Add(self.view_hept_gui, 1, wx.EXPAND)
        self.view_opt_sizer.Add(self.add_extra_face_gui, 1, wx.EXPAND)
        self.view_opt_sizer.Add(self.add_extra_edge_gui, 1, wx.EXPAND)
        self.view_opt_sizer.Add(self.tri_alt_gui, 1, wx.EXPAND)
        self.view_opt_sizer.Add(self.alt_hept_pos_gui, 1, wx.EXPAND)

        self.row_sizer = wx.BoxSizer(wx.VERTICAL)
        self.row_sizer.Add(self.view_opt_sizer, 1, wx.EXPAND)

        self.column_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.column_sizer.Add(self.row_sizer, 2, wx.EXPAND)

        main_sizer.Add(self.kite_angle_sizer, 4, wx.EXPAND)
        main_sizer.Add(self.column_sizer, 20, wx.EXPAND)

        self.add_specials(self.panel, main_sizer)

        return main_sizer

    def add_specials(self, _panel, _sizer):
        """Could be implemented by offspring to add more widgets"""

    def on_kite_angle(self, event):
        """Update the shape conform the new edge angles"""
        self.shape.set_angle(self.get_angle_val(self.kite_angle_gui.GetValue()))
        self.canvas.paint()
        try:
            self.status_bar.SetStatusText(self.shape.get_status_msg())
        except AttributeError:
            pass
        event.Skip()

    def on_view_settings_chk(self, _):
        """Update the shape drawing conform the settings."""
        show_kite = self.view_kite_gui.IsChecked()
        show_hepta = self.view_hept_gui.IsChecked()
        show_extra = self.add_extra_face_gui.IsChecked()
        alt_hept_pos = self.alt_hept_pos_gui.IsChecked()
        tri_alt = self.tri_alt_gui.IsChecked()
        add_extra_edge = self.add_extra_edge_gui.IsChecked()
        self.shape.update_view_opt(
            show_kite=show_kite,
            show_hepta=show_hepta,
            show_extra=show_extra,
            alt_hept_pos=alt_hept_pos,
            tri_alt=tri_alt,
            add_extra_edge=add_extra_edge,
        )
        self.canvas.paint()
        try:
            self.status_bar.SetStatusText(self.shape.get_status_msg())
        except AttributeError:
            pass

    def set_default_size(self, size):
        """Set the default size of this window"""
        self.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        self.SetSize(size)
