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

from OpenGL.GL import glBlendFunc
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


class TrisAltBase(object):
    """A base class holding names for triangle filling options, one side only."""
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
        """Check whether key 'k' is a base key

        A base key is a key that is used for one side of triangle fill and it is not combined with
        one of the bits (e.g. loose_bit)

        k: a number built up from TrisAltBase numbers
        """
        try:
            return self.baseKey[k]
        except KeyError:
            return False

    def toFileStr(self, tId=None, tStr=None):
        """Convert triangle fill alternative to unique string suited for filenames

        For filenames no spaces shall be used and these are mainly replaced by '_' and periods are
        exchanged. Besides that there are some other conversions for historical reasons.

        triangle_id: a number built up from TrisAltBase numbers, or a 2-tuple of these numbers
        triangle_str: a human readable string representation of the triangle alternative.
        """
        assert tId is not None or tStr is not None
        if tId is None:
            tId = self.key[tStr]
        if not isinstance(tId, int):
            tStr0 = self.stringify[tId[0]]
            tStr1 = self.stringify[tId[1]]
            tStr = f"{tStr0}-opp_{tStr1}"
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
        self.choiceList = [*self.stringify.values()]
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
    """Convert triangle fill alternative to an unique string suited for Python attribute names.

    Spaces shall converted to '_' and periods are exchanged. Besides that there are some other
    conversions for historical reasons.

    triangle_id: a number built up from TrisAltBase numbers, or a 2-tuple of these numbers
    triangle_str: a human readable string representation of the triangle alternative.
    """
    assert tId is not None or tStr is not None
    if tId is None:
        tId = TrisAltBase.key[tStr]
    if not isinstance(tId, int):
        if tId[0] & loose_bit and tId[1] & loose_bit:
            tStr = (
                f"{TrisAltBase.stringify[tId[0] & ~loose_bit]}_1loose_"
                f"{TrisAltBase.stringify[tId[1] & ~loose_bit]}"
            )
        elif tId[0] & loose_bit:
            tStr = f"{TrisAltBase.stringify[tId[0]]}__{TrisAltBase.stringify[tId[1]]}"
        # TODO: remove share under new position
        elif (
                tId[0] == TrisAltBase.twist_strip_I
                and tId[1] == TrisAltBase.twist_strip_I
        ):
            tStr = "twist_strip_I_strip_I"
        else:
            tStr = f"{TrisAltBase.stringify[tId[0]]}_{TrisAltBase.stringify[tId[1]]}"
    elif tStr is None:
        tStr = TrisAltBase.stringify[tId]
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
    for (k, s) in TrisAltBase.stringify.items():
        class_dict["stringify"][k] = s
        class_dict["key"][s] = k
        class_dict[toTrisAltKeyStr(k)] = k
    for k in tris_keys:
        if isinstance(k, int):
            class_dict["baseKey"][k] = True
        else:
            # must be a tuple of 2
            assert len(k) == 2, f"Exptected 2 tuple, got: {k}."
            if k[0] & loose_bit and k[1] & loose_bit:
                s = (
                    f"{TrisAltBase.stringify[k[0] & ~loose_bit]} - 1 loose - "
                    f"{TrisAltBase.stringify[k[1] & ~loose_bit]}"
                )
            elif (
                    k[0] == TrisAltBase.twist_strip_I
                    and k[1] == TrisAltBase.twist_strip_I
            ):
                s = "strip I - twisted - strip I"
            else:
                s = f"{TrisAltBase.stringify[k[0]]} - {TrisAltBase.stringify[k[1]]}"
            class_dict["stringify"][k] = s
            class_dict["key"][s] = k
            class_dict[toTrisAltKeyStr(k)] = k
    return Meta_TrisAlt(name, (TrisAltBase,), class_dict)


TrisAlt = define_tris_alt(
    "TrisAlt",
    [
        TrisAltBase.refl_1,
        TrisAltBase.refl_2,
        TrisAltBase.crossed_2,
        TrisAltBase.strip_1_loose,
        TrisAltBase.strip_I,
        TrisAltBase.strip_II,
        TrisAltBase.star,
        TrisAltBase.star_1_loose,
        TrisAltBase.alt_strip_I,
        TrisAltBase.alt_strip_II,
        TrisAltBase.alt_strip_1_loose,
        TrisAltBase.twist_strip_I,
        TrisAltBase.rot_strip_1_loose,
        TrisAltBase.rot_star_1_loose,
        TrisAltBase.arot_strip_1_loose,
        TrisAltBase.arot_star_1_loose,
        (TrisAltBase.strip_I, TrisAltBase.strip_I),
        (TrisAltBase.strip_I, TrisAltBase.strip_II),
        (TrisAltBase.strip_I, TrisAltBase.star),
        (TrisAltBase.strip_I, TrisAltBase.alt_strip_I),
        (TrisAltBase.strip_I, TrisAltBase.alt_strip_II),
        (TrisAltBase.strip_II, TrisAltBase.strip_I),
        (TrisAltBase.strip_II, TrisAltBase.strip_II),
        (TrisAltBase.strip_II, TrisAltBase.star),
        (TrisAltBase.strip_II, TrisAltBase.alt_strip_I),
        (TrisAltBase.strip_II, TrisAltBase.alt_strip_II),
        (TrisAltBase.star, TrisAltBase.strip_I),
        (TrisAltBase.star, TrisAltBase.strip_II),
        (TrisAltBase.star, TrisAltBase.star),
        (TrisAltBase.star, TrisAltBase.alt_strip_I),
        (TrisAltBase.star, TrisAltBase.alt_strip_II),
        (TrisAltBase.alt_strip_I, TrisAltBase.strip_I),
        (TrisAltBase.alt_strip_I, TrisAltBase.strip_II),
        (TrisAltBase.alt_strip_I, TrisAltBase.star),
        (TrisAltBase.alt_strip_I, TrisAltBase.alt_strip_I),
        (TrisAltBase.alt_strip_I, TrisAltBase.alt_strip_II),
        (TrisAltBase.twist_strip_I, TrisAltBase.twist_strip_I),
        (TrisAltBase.alt_strip_II, TrisAltBase.strip_I),
        (TrisAltBase.alt_strip_II, TrisAltBase.strip_II),
        (TrisAltBase.alt_strip_II, TrisAltBase.star),
        (TrisAltBase.alt_strip_II, TrisAltBase.alt_strip_I),
        (TrisAltBase.alt_strip_II, TrisAltBase.alt_strip_II),
        (TrisAltBase.strip_1_loose, TrisAltBase.strip_1_loose),
        (TrisAltBase.strip_1_loose, TrisAltBase.star_1_loose),
        (TrisAltBase.strip_1_loose, TrisAltBase.alt_strip_1_loose),
        (TrisAltBase.star_1_loose, TrisAltBase.strip_1_loose),
        (TrisAltBase.star_1_loose, TrisAltBase.star_1_loose),
        (TrisAltBase.star_1_loose, TrisAltBase.alt_strip_1_loose),
        (TrisAltBase.alt_strip_1_loose, TrisAltBase.strip_1_loose),
        (TrisAltBase.alt_strip_1_loose, TrisAltBase.star_1_loose),
        (TrisAltBase.alt_strip_1_loose, TrisAltBase.alt_strip_1_loose),
        (TrisAltBase.star_1_loose, TrisAltBase.rot_strip_1_loose),
        (TrisAltBase.strip_1_loose, TrisAltBase.rot_strip_1_loose),
        (TrisAltBase.alt_strip_1_loose, TrisAltBase.rot_strip_1_loose),
        (TrisAltBase.star_1_loose, TrisAltBase.arot_strip_1_loose),
        (TrisAltBase.strip_1_loose, TrisAltBase.arot_strip_1_loose),
        (TrisAltBase.alt_strip_1_loose, TrisAltBase.arot_strip_1_loose),
        (TrisAltBase.star_1_loose, TrisAltBase.rot_star_1_loose),
        (TrisAltBase.strip_1_loose, TrisAltBase.rot_star_1_loose),
        (TrisAltBase.alt_strip_1_loose, TrisAltBase.rot_star_1_loose),
        (TrisAltBase.star_1_loose, TrisAltBase.arot_star_1_loose),
        (TrisAltBase.strip_1_loose, TrisAltBase.arot_star_1_loose),
        (TrisAltBase.alt_strip_1_loose, TrisAltBase.arot_star_1_loose),
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
    """The vertices and edges (and single face) of a regular folded heptagon in 3D space."""
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
        self.vs_org = [
            Vec([0.0, 0.0, 0.0]),
            Vec([HEPT_RHO / 2, -HEPT_DENOM, 0.0]),
            Vec([HEPT_SIGMA / 2, -(1 + HEPT_SIGMA) * HEPT_DENOM, 0.0]),
            Vec([0.5, -HEPT_HEIGHT, 0.0]),
            Vec([-0.5, -HEPT_HEIGHT, 0.0]),
            Vec([-HEPT_SIGMA / 2, -(1 + HEPT_SIGMA) * HEPT_DENOM, 0.0]),
            Vec([-HEPT_RHO / 2, -HEPT_DENOM, 0.0]),
        ]
        self.Vs = self.vs_org.copy() # pylint: disable=C0103
        self.Fs = [[6, 5, 4, 3, 2, 1, 0]]  # pylint: disable=C0103
        self.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0]  # pylint: disable=C0103

    def fold(
            self,
            a0,
            b0,
            a1=None,
            b1=None,
            keep_v0=True,
            fold=FoldMethod.PARALLEL,
            rotate=0,
    ):
        """Fold the heptagon around 2, 3, or 4 axes using the specified fold method"""
        method = {
            FoldMethod.PARALLEL: self.fold_parallel,
            FoldMethod.TRAPEZIUM: self.fold_trapezium,
            FoldMethod.W: self.fold_w,
            FoldMethod.TRIANGLE: self.fold_triangle,
            FoldMethod.SHELL: self.fold_shell,
            FoldMethod.MIXED: self.fold_mixed,
            FoldMethod.G: self.fold_g,
        }
        method[fold](a0, b0, a1, b1, keep_v0, rotate)

    def fold_parallel(self, a, b, _=None, __=None, keep_v0=True, rotate=0):  # pylint: disable=C0103
        """Fold around the 2 parallel diagonals, two options

        In rotate 0 the parallel lines are between vertices 1-6, and 2-5
        In rotate 1 the parallel lines are between vertices 0-2, and 6-3
        """
        if rotate == 0:
            self.fold_parallel_0(a, b, keep_v0)
        else:
            self.fold_parallel_1(a, b, keep_v0)

    def fold_parallel_0(self, a, b, keep_v0=True):
        """
        Fold around the 2 parallel diagonals V1-V6 and V2-V5.

        The fold angle a refers the axis V2-V5 and
        the fold angle b refers the axis V1-V6.
        If keep_v0 = True then the triangle V0, V1, V6 is kept invariant during
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
        if keep_v0:
            # for x-coord set to 0:
            # V2 - V[1] = fold_a(V[2] - V[1]) = (cosa, sina)*(V[2] - V[1])
            # => V2 = V[1] + (cosa, sina)*(V[2] - V[1])
            #
            #                             V3
            #                            /
            #                           / b _
            #                       V2 /_.-'  v3_tmp
            #                       _.-'
            #                   _.-'  a
            #   (0, 0) .-------.-------.------.
            #   self. V[0]   V[1]    V[2]    V[3]
            d_v2 = [
                self.vs_org[2][1] - self.vs_org[1][1],
                self.vs_org[2][2] - self.vs_org[1][2],
            ]
            v2 = Vec(
                [
                    self.vs_org[2][0],
                    self.vs_org[1][1] + cosa * d_v2[0] - sina * d_v2[1],
                    self.vs_org[1][2] + cosa * d_v2[1] + sina * d_v2[0],
                ]
            )
            # Similarly:
            d_v3_tmp = [
                self.vs_org[3][1] - self.vs_org[1][1],
                self.vs_org[3][2] - self.vs_org[1][2],
            ]
            v3_tmp = [
                self.vs_org[1][1] + cosa * d_v3_tmp[0] - sina * d_v3_tmp[1],
                self.vs_org[1][2] + cosa * d_v3_tmp[1] + sina * d_v3_tmp[0],
            ]
            # now rotate beta:
            d_v3 = [v3_tmp[0] - v2[1], v3_tmp[1] - v2[2]]
            v3 = Vec(
                [
                    self.vs_org[3][0],
                    v2[1] + cosb * d_v3[0] - sinb * d_v3[1],
                    v2[2] + cosb * d_v3[1] + sinb * d_v3[0],
                ]
            )
            self.Vs = [
                self.vs_org[0],
                self.vs_org[1],
                v2,
                v3,
                Vec([-v3[0], v3[1], v3[2]]),
                Vec([-v2[0], v2[1], v2[2]]),
                self.vs_org[6],
            ]
        else:
            # similar to before, except the roles of the vertices are switched
            # i.e. keep V[3] constant...
            d_v1 = [
                self.vs_org[1][1] - self.vs_org[2][1],
                self.vs_org[1][2] - self.vs_org[2][2],
            ]
            v1 = Vec(
                [
                    self.vs_org[1][0],
                    self.vs_org[2][1] + cosa * d_v1[0] - sina * d_v1[1],
                    self.vs_org[2][2] + cosa * d_v1[1] + sina * d_v1[0],
                ]
            )
            # Similarly:
            d_v0_tmp = [
                self.vs_org[0][1] - self.vs_org[2][1],
                self.vs_org[0][2] - self.vs_org[2][2],
            ]
            v0_tmp = [
                self.vs_org[2][1] + cosa * d_v0_tmp[0] - sina * d_v0_tmp[1],
                self.vs_org[2][2] + cosa * d_v0_tmp[1] + sina * d_v0_tmp[0],
            ]
            # now rotate beta:
            d_v0 = [v0_tmp[0] - v1[1], v0_tmp[1] - v1[2]]
            v0 = Vec(
                [
                    self.vs_org[0][0],
                    v1[1] + cosb * d_v0[0] - sinb * d_v0[1],
                    v1[2] + cosb * d_v0[1] + sinb * d_v0[0],
                ]
            )
            self.Vs = [
                v0,
                v1,
                self.vs_org[2],
                self.vs_org[3],
                self.vs_org[4],
                self.vs_org[5],
                Vec([-v1[0], v1[1], v1[2]]),
            ]

    def fold_parallel_1(self, a, b, keep_v0=True):
        """
        Fold around the 2 parallel diagonals parallel to the edge opposite of
        vertex 1

        The fold angle a refers the axis V3-V6 and
        the fold angle b refers the axis V2-V0.
        If keep_v0 = True then the vertex V0, and V2 are kept invariant
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
        if keep_v0:
            assert False, "TODO"
        else:
            v3v6 = (self.vs_org[3] + self.vs_org[6]) / 2
            v3v6_axis = Vec(self.vs_org[3] - self.vs_org[6])
            v0v2 = (self.vs_org[0] + self.vs_org[2]) / 2
            rot_a = Rot(axis=v3v6_axis, angle=a)
            v0v2_rot = v3v6 + rot_a * (v0v2 - v3v6)
            v0 = v0v2_rot + (self.vs_org[0] - v0v2)
            v2 = v0v2_rot + (self.vs_org[2] - v0v2)
            v1_tmp = v3v6 + rot_a * (self.vs_org[1] - v3v6)

            v0v2_axis = Vec(v2 - v0)
            rot_b = Rot(axis=v0v2_axis, angle=b)
            v1 = v0v2 + rot_b * (v1_tmp - v0v2)
            self.Vs = [
                v0,
                v1,
                v2,
                self.vs_org[3],
                self.vs_org[4],
                self.vs_org[5],
                self.vs_org[6],
            ]

    def fold_trapezium(self, a, b0, _=None, b1=None, keep_v0=True, rotate=0):
        """
        Fold around 4 diagonals in the shape of a trapezium (trapezoid)

        The fold angle a refers the axis V1-V6 and
        The fold angle b refers the axes V1-V3 and V6-V4 and
        If keep_v0 = True then the triangle V0, V1, V6 is kept invariant during
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
        _ = rotate  # TODO: implement
        self.Fs = [[0, 6, 1], [1, 3, 2], [1, 6, 4, 3], [4, 6, 5]]
        self.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0, 4, 6, 6, 1, 1, 3]
        cosa = math.cos(a)
        sina = math.sin(a)
        if keep_v0:
            # see fold_parallel
            d_v2_tmp = [
                self.vs_org[2][1] - self.vs_org[1][1],
                self.vs_org[2][2] - self.vs_org[1][2],
            ]
            v2_tmp = Vec(
                [
                    self.vs_org[2][0],
                    self.vs_org[1][1] + cosa * d_v2_tmp[0] - sina * d_v2_tmp[1],
                    self.vs_org[1][2] + cosa * d_v2_tmp[1] + sina * d_v2_tmp[0],
                ]
            )
            d_v3 = [
                self.vs_org[3][1] - self.vs_org[1][1],
                self.vs_org[3][2] - self.vs_org[1][2],
            ]
            v3 = Vec(
                [
                    self.vs_org[3][0],
                    self.vs_org[1][1] + cosa * d_v3[0] - sina * d_v3[1],
                    self.vs_org[1][2] + cosa * d_v3[1] + sina * d_v3[0],
                ]
            )
            v4 = Vec([-v3[0], v3[1], v3[2]])
            v1v3 = (self.vs_org[1] + v3) / 2
            v1v3_axis = Vec(v3 - self.vs_org[1])
            r = Rot(axis=v1v3_axis, angle=b0)
            v2 = v1v3 + r * (v2_tmp - v1v3)
            if not Geom3D.eq(b0, b1):
                v5 = Vec([-v2[0], v2[1], v2[2]])
            else:
                v4v6 = (v4 + self.vs_org[6]) / 2
                v4v6_axis = Vec(self.vs_org[6] - v4)
                r = Rot(axis=v4v6_axis, angle=b1)
                v5_tmp = Vec([-v2_tmp[0], v2_tmp[1], v2_tmp[2]])
                v5 = v4v6 + r * (v5_tmp - v4v6)
            self.Vs = [self.vs_org[0], self.vs_org[1], v2, v3, v4, v5, self.vs_org[6]]
        else:
            d_v0 = [
                self.vs_org[0][1] - self.vs_org[1][1],
                self.vs_org[0][2] - self.vs_org[1][2],
            ]
            v0 = Vec(
                [
                    self.vs_org[0][0],
                    self.vs_org[1][1] + cosa * d_v0[0] - sina * d_v0[1],
                    self.vs_org[1][2] + cosa * d_v0[1] + sina * d_v0[0],
                ]
            )
            v1v3 = (self.vs_org[1] + self.vs_org[3]) / 2
            v1v3_axis = Vec(self.vs_org[3] - self.vs_org[1])
            r = Rot(axis=v1v3_axis, angle=b0)
            v2 = v1v3 + r * (self.vs_org[2] - v1v3)
            if Geom3D.eq(b0, b1):
                v5 = Vec([-v2[0], v2[1], v2[2]])
            else:
                v4v6 = (self.vs_org[4] + self.vs_org[6]) / 2
                v4v6_axis = Vec(self.vs_org[6] - self.vs_org[4])
                r = Rot(axis=v4v6_axis, angle=b1)
                v5 = v4v6 + r * (self.vs_org[5] - v4v6)
            self.Vs = [
                v0,
                self.vs_org[1],
                v2,
                self.vs_org[3],
                self.vs_org[4],
                v5,
                self.vs_org[6],
            ]

    def fold_triangle(self, a, b0, _=None, b1=None, keep_v0=True, rotate=0):
        """
        Fold around 3 triangular diagonals from V0.

        The fold angle a refers the axes V0-V2 and V0-V5 and
        the fold angle b refers the axis V2-V5.
        If keep_v0 = True then the triangle V0, V1, V6 is kept invariant during
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
        _ = rotate  # TODO: implement
        self.Fs = [[0, 2, 1], [0, 5, 2], [0, 6, 5], [2, 5, 4, 3]]
        self.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0, 0, 2, 2, 5, 5, 0]
        rot0_2 = Rot(axis=self.vs_org[2] - self.vs_org[0], angle=b0)
        v1 = rot0_2 * self.vs_org[1]
        if Geom3D.eq(b0, b1):
            v6 = Vec([-v1[0], v1[1], v1[2]])
        else:
            rot5_0 = Rot(axis=self.vs_org[0] - self.vs_org[5], angle=b1)
            v6 = rot5_0 * self.vs_org[6]
        v2 = self.vs_org[2]
        if keep_v0:
            rot5_2 = Rot(axis=self.vs_org[5] - self.vs_org[2], angle=a)
            v3 = rot5_2 * (self.vs_org[3] - v2) + v2
            self.Vs = [
                self.vs_org[0],
                v1,
                self.vs_org[2],
                v3,
                Vec([-v3[0], v3[1], v3[2]]),
                self.vs_org[5],
                v6,
            ]
        else:
            rot2_5 = Rot(axis=self.vs_org[2] - self.vs_org[5], angle=a)
            v0 = rot2_5 * (self.vs_org[0] - v2) + v2
            v1 = rot2_5 * (v1 - v2) + v2
            v6 = rot2_5 * (v6 - v2) + v2
            self.Vs = [
                v0,
                v1,
                self.vs_org[2],
                self.vs_org[3],
                self.vs_org[4],
                self.vs_org[5],
                v6,
            ]

    def fold_shell(self, a0, b0, a1, b1, keep_v0=True, rotate=0):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        The fold angle a refers the axes V0-V2 and V0-V5 and
        the fold angle b0 refers the axes V0-V3 and V0-V4.
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        prj[rotate](a0, b0, a1, b1, keep_v0)

    def fold_shell_es_fs(self, no):
        """
        Set self.Es and self.FS for shell-fold and specified position.

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

    def fold_shell_0(self, a0, b0, a1, b1, keep_v0=True):
        """Set vertices, edges and faces for a shell-fold in position 0.

        The fold angle a refers the axes V0-V2 and V0-V5 and
        the fold angle b0 refers the axes V0-V3 and V0-V4.
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        self.fold_shell_0_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_shell_0_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Set vertices for a shell-fold in position 0.

        verts: the array with vertex numbers.
        returns a new array.
        """
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot a0
            v0v3 = (v[0] + v[3]) / 2
            v0v3_axis = Vec(v[0] - v[3])
            rot_a0 = Rot(axis=v0v3_axis, angle=-a0)
            # middle of V1-V2 which is // to v0v3 axis
            v1v2 = (v[1] + v[2]) / 2
            v1v2_rot = v0v3 + rot_a0 * (v1v2 - v0v3)
            v[1] = v1v2_rot + (v[1] - v1v2)
            v[2] = v1v2_rot + (v[2] - v1v2)

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
            v6v5_rot = v0v4 + rot_a1 * (v6v5 - v0v4)
            v[6] = v6v5_rot + (v[6] - v6v5)
            v[5] = v6v5_rot + (v[5] - v6v5)

            # rot b1
            v0v5 = (v[0] + v[5]) / 2
            v0v5_axis = Vec(v[0] - v[5])
            rot_b1 = Rot(axis=v0v5_axis, angle=b1)
            v[6] = v0v5 + rot_b1 * (v[6] - v0v5)

        self.Vs = v

    def fold_shell_1(self, a0, b0, a1, b1, keep_v0=True):
        """Set vertices, edges and faces for a shell-fold in position 1.

        the fold angle a0 refers to the axes V1-V4,
        The fold angle b0 refers to the axes V1-V3,
        the fold angle a1 refers to the axes V1-V5,
        The fold angle b1 refers to the axes V1-V6 and
        If keep_v0 = True then the vertex V0 is kept invariant
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
        self.fold_shell_1_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_shell_1_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Set vertices for a shell-fold in position 1.

        verts: the array with vertex numbers.
        returns a new array.
        """
        v = verts.copy()
        if keep_v0:
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
            v0v5_rot = v1v4 + rot_a0 * (v0v5 - v1v4)
            v[0] = v0v5_rot + (v[0] - v0v5)
            v[5] = v0v5_rot + (v[5] - v0v5)
            v[6] = v1v4 + rot_a0 * (v[6] - v1v4)

            # rot a1
            v1v5 = (v[1] + v[5]) / 2
            v1v5_axis = Vec(v[1] - v[5])
            rot_a1 = Rot(axis=v1v5_axis, angle=a1)
            # middle of V0-V6 which is // to v1v4 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_rot = v1v5 + rot_a1 * (v0v6 - v1v5)
            v[0] = v0v6_rot + (v[0] - v0v6)
            v[6] = v0v6_rot + (v[6] - v0v6)

            # rot b1
            v1v6 = (v[1] + v[6]) / 2
            v1v6_axis = Vec(v[1] - v[6])
            rot_b1 = Rot(axis=v1v6_axis, angle=b1)
            v[0] = v1v6 + rot_b1 * (v[0] - v1v6)

        self.Vs = v

    def fold_shell_2(self, a0, b0, a1, b1, keep_v0=True):
        """Set vertices, edges and faces for a shell-fold in position 2.

        the fold angle a0 refers to the axes V2-V5,
        The fold angle b0 refers to the axes V2-V4,
        the fold angle a1 refers to the axes V2-V6,
        The fold angle b1 refers to the axes V2-V0 and
        If keep_v0 = True then the vertex V0 is kept invariant
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
        self.fold_shell_2_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_shell_2_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Set vertices for a shell-fold in position 2.

        verts: the array with vertex numbers.
        returns a new array.
        """
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b0
            v2v4 = (v[2] + v[4]) / 2
            v2v4_axis = Vec(v[2] - v[4])
            rot_b0 = Rot(axis=v2v4_axis, angle=b0)
            # middle of V1-V5 which is // to v2v4 axis
            v1v5 = (v[1] + v[5]) / 2
            v1v5_rot = v2v4 + rot_b0 * (v1v5 - v2v4)
            v[1] = v1v5_rot + (v[1] - v1v5)
            v[5] = v1v5_rot + (v[5] - v1v5)
            # middle of V0-V6 which is // to v2v4 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_rot = v2v4 + rot_b0 * (v0v6 - v2v4)
            v[0] = v0v6_rot + (v[0] - v0v6)
            v[6] = v0v6_rot + (v[6] - v0v6)

            # rot a0
            v2v5 = (v[2] + v[5]) / 2
            v2v5_axis = Vec(v[2] - v[5])
            rot_a0 = Rot(axis=v2v5_axis, angle=a0)
            # middle of V1-V6 which is // to v2v5 axis
            v1v6 = (v[1] + v[6]) / 2
            v1v6_rot = v2v5 + rot_a0 * (v1v6 - v2v5)
            v[1] = v1v6_rot + (v[1] - v1v6)
            v[6] = v1v6_rot + (v[6] - v1v6)
            v[0] = v2v5 + rot_a0 * (v[0] - v2v5)

            # rot a1
            v2v6 = (v[2] + v[6]) / 2
            v2v6_axis = Vec(v[2] - v[6])
            rot_a1 = Rot(axis=v2v6_axis, angle=a1)
            # middle of V0-V1 which is // to v2v6 axis
            v0v1 = (v[0] + v[1]) / 2
            v0v1_rot = v2v6 + rot_a1 * (v0v1 - v2v6)
            v[0] = v0v1_rot + (v[0] - v0v1)
            v[1] = v0v1_rot + (v[1] - v0v1)

            # rot b1
            v2v0 = (v[2] + v[0]) / 2
            v2v0_axis = Vec(v[2] - v[0])
            rot_b1 = Rot(axis=v2v0_axis, angle=b1)
            v[1] = v2v0 + rot_b1 * (v[1] - v2v0)

        self.Vs = v

    def fold_shell_3(self, a0, b0, a1, b1, keep_v0=True):
        """Set vertices, edges and faces for a shell-fold in position 3.

        the fold angle a0 refers to the axes V3-V6,
        The fold angle b0 refers to the axes V3-V5,
        the fold angle a1 refers to the axes V3-V0,
        The fold angle b1 refers to the axes V3-V1 and
        If keep_v0 = True then the vertex V0 is kept invariant
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
        self.fold_shell_3_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_shell_3_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Set vertices for a shell-fold in position 3.

        verts: the array with vertex numbers.
        returns a new array.
        """
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b0
            v3v5 = (v[3] + v[5]) / 2
            v3v5_axis = Vec(v[3] - v[5])
            rot_b0 = Rot(axis=v3v5_axis, angle=b0)
            # middle of V2-V6 which is // to v3v5 axis
            v2v6 = (v[2] + v[6]) / 2
            v2v6_rot = v3v5 + rot_b0 * (v2v6 - v3v5)
            v[2] = v2v6_rot + (v[2] - v2v6)
            v[6] = v2v6_rot + (v[6] - v2v6)
            # middle of V1-V0 which is // to v3v5 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_rot = v3v5 + rot_b0 * (v1v0 - v3v5)
            v[1] = v1v0_rot + (v[1] - v1v0)
            v[0] = v1v0_rot + (v[0] - v1v0)

            # rot a0
            v3v6 = (v[3] + v[6]) / 2
            v3v6_axis = Vec(v[3] - v[6])
            rot_a0 = Rot(axis=v3v6_axis, angle=a0)
            # middle of V2-V0 which is // to v3v6 axis
            v2v0 = (v[2] + v[0]) / 2
            v2v0_rot = v3v6 + rot_a0 * (v2v0 - v3v6)
            v[2] = v2v0_rot + (v[2] - v2v0)
            v[0] = v2v0_rot + (v[0] - v2v0)
            v[1] = v3v6 + rot_a0 * (v[1] - v3v6)

            # rot a1
            v3v0 = (v[3] + v[0]) / 2
            v3v0_axis = Vec(v[3] - v[0])
            rot_a1 = Rot(axis=v3v0_axis, angle=a1)
            # middle of V1-V2 which is // to v3v0 axis
            v1v2 = (v[1] + v[2]) / 2
            v1v2_rot = v3v0 + rot_a1 * (v1v2 - v3v0)
            v[1] = v1v2_rot + (v[1] - v1v2)
            v[2] = v1v2_rot + (v[2] - v1v2)

            # rot b1
            v3v1 = (v[3] + v[1]) / 2
            v3v1_axis = Vec(v[3] - v[1])
            rot_b1 = Rot(axis=v3v1_axis, angle=b1)
            v[2] = v3v1 + rot_b1 * (v[2] - v3v1)

        self.Vs = v

    def fold_shell_4(self, a0, b0, a1, b1, keep_v0=True):
        """Set vertices, edges and faces for a shell-fold in position 4.

        the fold angle a0 refers to the axes V4-V0,
        The fold angle b0 refers to the axes V4-V6,
        the fold angle a1 refers to the axes V4-V1,
        The fold angle b1 refers to the axes V4-V2 and
        If keep_v0 = True then the vertex V0 is kept invariant
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
        self.fold_shell_4_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_shell_4_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Set vertices for a shell-fold in position 4.

        verts: the array with vertex numbers.
        returns a new array.
        """
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b1
            v4v2 = (v[4] + v[2]) / 2
            v4v2_axis = Vec(v[4] - v[2])
            rot_b1 = Rot(axis=v4v2_axis, angle=-b1)
            # middle of V5-V1 which is // to v4v2 axis
            v5v1 = (v[5] + v[1]) / 2
            v5v1_rot = v4v2 + rot_b1 * (v5v1 - v4v2)
            v[5] = v5v1_rot + (v[5] - v5v1)
            v[1] = v5v1_rot + (v[1] - v5v1)
            # middle of V6-V0 which is // to v4v2 axis
            v6v0 = (v[6] + v[0]) / 2
            v6v0_rot = v4v2 + rot_b1 * (v6v0 - v4v2)
            v[6] = v6v0_rot + (v[6] - v6v0)
            v[0] = v6v0_rot + (v[0] - v6v0)

            # rot a1
            v4v1 = (v[4] + v[1]) / 2
            v4v1_axis = Vec(v[4] - v[1])
            rot_a1 = Rot(axis=v4v1_axis, angle=-a1)
            # middle of V5-V0 which is // to v4v1 axis
            v5v0 = (v[5] + v[0]) / 2
            v5v0_rot = v4v1 + rot_a1 * (v5v0 - v4v1)
            v[5] = v5v0_rot + (v[5] - v5v0)
            v[0] = v5v0_rot + (v[0] - v5v0)
            v[6] = v4v1 + rot_a1 * (v[6] - v4v1)

            # rot a0
            v4v0 = (v[4] + v[0]) / 2
            v4v0_axis = Vec(v[4] - v[0])
            rot_a0 = Rot(axis=v4v0_axis, angle=-a0)
            # middle of V5-V6 which is // to v4v0 axis
            v5v6 = (v[5] + v[6]) / 2
            v5v6_rot = v4v0 + rot_a0 * (v5v6 - v4v0)
            v[5] = v5v6_rot + (v[5] - v5v6)
            v[6] = v5v6_rot + (v[6] - v5v6)

            # rot b0
            v4v6 = (v[4] + v[6]) / 2
            v4v6_axis = Vec(v[4] - v[6])
            rot_b0 = Rot(axis=v4v6_axis, angle=-b0)
            v[5] = v4v6 + rot_b0 * (v[5] - v4v6)

        self.Vs = v

    def fold_shell_5(self, a0, b0, a1, b1, keep_v0=True):
        """Set vertices, edges and faces for a shell-fold in position 5.

        the fold angle a0 refers to the axes V5-V1,
        The fold angle b0 refers to the axes V5-V0,
        the fold angle a1 refers to the axes V5-V2,
        The fold angle b1 refers to the axes V5-V3 and
        If keep_v0 = True then the vertex V0 is kept invariant
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
        self.fold_shell_5_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_shell_5_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Set vertices for a shell-fold in position 5.

        verts: the array with vertex numbers.
        returns a new array.
        """
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b1
            v5v3 = (v[5] + v[3]) / 2
            v5v3_axis = Vec(v[5] - v[3])
            rot_b1 = Rot(axis=v5v3_axis, angle=-b1)
            # middle of V6-V2 which is // to v5v3 axis
            v6v2 = (v[6] + v[2]) / 2
            v6v2_rot = v5v3 + rot_b1 * (v6v2 - v5v3)
            v[6] = v6v2_rot + (v[6] - v6v2)
            v[2] = v6v2_rot + (v[2] - v6v2)
            # middle of V0-V1 which is // to v5v3 axis
            v0v1 = (v[0] + v[1]) / 2
            v0v1_rot = v5v3 + rot_b1 * (v0v1 - v5v3)
            v[0] = v0v1_rot + (v[0] - v0v1)
            v[1] = v0v1_rot + (v[1] - v0v1)

            # rot a1
            v5v2 = (v[5] + v[2]) / 2
            v5v2_axis = Vec(v[5] - v[2])
            rot_a1 = Rot(axis=v5v2_axis, angle=-a1)
            # middle of V6-V1 which is // to v5v2 axis
            v6v1 = (v[6] + v[1]) / 2
            v6v1_rot = v5v2 + rot_a1 * (v6v1 - v5v2)
            v[6] = v6v1_rot + (v[6] - v6v1)
            v[1] = v6v1_rot + (v[1] - v6v1)
            v[0] = v5v2 + rot_a1 * (v[0] - v5v2)

            # rot a0
            v5v1 = (v[5] + v[1]) / 2
            v5v1_axis = Vec(v[5] - v[1])
            rot_a0 = Rot(axis=v5v1_axis, angle=-a0)
            # middle of V6-V0 which is // to v5v1 axis
            v6v0 = (v[6] + v[0]) / 2
            v6v0_rot = v5v1 + rot_a0 * (v6v0 - v5v1)
            v[6] = v6v0_rot + (v[6] - v6v0)
            v[0] = v6v0_rot + (v[0] - v6v0)

            # rot b0
            v5v0 = (v[5] + v[0]) / 2
            v5v0_axis = Vec(v[5] - v[0])
            rot_b0 = Rot(axis=v5v0_axis, angle=-b0)
            v[6] = v5v0 + rot_b0 * (v[6] - v5v0)

        self.Vs = v

    def fold_shell_6(self, a0, b0, a1, b1, keep_v0=True):
        """Set vertices for a shell-fold in position 6.

        the fold angle a0 refers to the axes V1-V4,
        The fold angle b0 refers to the axes V1-V3,
        the fold angle a1 refers to the axes V1-V5,
        The fold angle b1 refers to the axes V1-V6 and
        If keep_v0 = True then the vertex V0 is kept invariant
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
            keep_v0,
            [
                self.vs_org[0],
                self.vs_org[6],
                self.vs_org[5],
                self.vs_org[4],
                self.vs_org[3],
                self.vs_org[2],
                self.vs_org[1],
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

    def fold_w(self, a0, b0, a1, b1, keep_v0=True, rotate=0):
        """Define vertices, edges and faces for a W-fold."""
        prj = [
            self.fold_w0,
            self.fold_w1,
            self.fold_w2,
            self.fold_w3,
            self.fold_w4,
            self.fold_w5,
            self.fold_w6,
        ]
        prj[rotate](a0, b0, a1, b1, keep_v0)

    def fold_w_es_fs(self, no):
        """
        Set self.Es and self.FS for W-fold and specified position.

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

    def fold_w0(self, a0, b0, a1, b1, keep_v0=True):
        """Set heptagon vertices, edges and faces for W-fold in position 0.

        the fold angle a0 refers to the axis V0-V3,
        the fold angle a1 refers to the axis V0-V4,
        The fold angle b0 refers to the axis V1-V3,
        The fold angle b1 refers to the axis V6-V4 and
        The vertex V0 is kept invariant during folding
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        _ = keep_v0  # TODO: implement
        rot0_3 = Rot(axis=self.vs_org[3] - self.vs_org[0], angle=a0)
        v1 = rot0_3 * self.vs_org[1]
        v2_tmp = rot0_3 * self.vs_org[2]
        rot1_3 = Rot(axis=self.vs_org[3] - v1, angle=b0)
        v2 = rot1_3 * (v2_tmp - v1) + v1
        if Geom3D.eq(a0, a1):
            v6 = Vec([-v1[0], v1[1], v1[2]])
            if Geom3D.eq(b0, b1):
                v5 = Vec([-v2[0], v2[1], v2[2]])
            else:
                v5 = Vec([-v2_tmp[0], v2_tmp[1], v2_tmp[2]])
                rot4_6 = Rot(axis=v6 - self.vs_org[4], angle=b1)
                v5 = rot4_6 * (v5 - v6) + v6
        else:
            rot4_0 = Rot(axis=self.vs_org[0] - self.vs_org[4], angle=a1)
            v6 = rot4_0 * self.vs_org[6]
            v5 = rot4_0 * self.vs_org[5]
            rot4_6 = Rot(axis=v6 - self.vs_org[4], angle=b1)
            v5 = rot4_6 * (v5 - v6) + v6
        self.Vs = [
            self.vs_org[0],
            v1,
            v2,
            self.vs_org[3],
            self.vs_org[4],
            v5,
            v6,
        ]
        self.fold_w_es_fs(0)

    def fold_w1_help(self, a0, b0, a1, b1, keep_v0, verts):
        """Set heptagon vertices for W-fold in position 1.

        verts: the array with vertex numbers.
        returns a new array.
        """
        v = verts.copy()
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
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b0
            v2v4 = (v[2] + v[4]) / 2
            v2v4_axis = Vec(v[2] - v[4])
            rot_b0 = Rot(axis=v2v4_axis, angle=b0)
            v1v5 = (v[1] + v[5]) / 2
            v1v5_rot = v2v4 + rot_b0 * (v1v5 - v2v4)
            v[1] = v1v5_rot + (v[1] - v1v5)
            v5_tmp = v1v5_rot + (v[5] - v1v5)
            v0v6 = (v[0] + v[6]) / 2
            v0v6_rot = v2v4 + rot_b0 * (v0v6 - v2v4)
            v0_tmp = v0v6_rot + (v[0] - v0v6)
            v6_tmp = v0v6_rot + (v[6] - v0v6)

            # rot a0
            v1v4 = (v[1] + v[4]) / 2
            v1v4_axis = Vec(v[1] - v[4])
            rot_a0 = Rot(axis=v1v4_axis, angle=a0)
            v0v5 = (v0_tmp + v5_tmp) / 2
            v0v5_rot = v1v4 + rot_a0 * (v0v5 - v1v4)
            v0_tmp = v0v5_rot + (v0_tmp - v0v5)
            v[5] = v0v5_rot + (v5_tmp - v0v5)
            v6_tmp = v1v4 + rot_a0 * (v6_tmp - v1v4)

            # rot a1
            v1v5 = (v[1] + v[5]) / 2
            v1v5_axis = Vec(v[1] - v[5])
            rot_a1 = Rot(axis=v1v5_axis, angle=a1)
            v0v6 = (v0_tmp + v6_tmp) / 2
            v0v6_rot = v1v5 + rot_a1 * (v0v6 - v1v5)
            v[0] = v0v6_rot + (v0_tmp - v0v6)
            v6_tmp = v0v6_rot + (v6_tmp - v0v6)

            # rot b1
            v0v5 = (v[0] + v[5]) / 2
            v0v5_axis = Vec(v[0] - v[5])
            rot_b1 = Rot(axis=v0v5_axis, angle=b1)
            v[6] = v0v5 + rot_b1 * (v6_tmp - v0v5)

            self.Vs = v

    def fold_w2_help(self, a0, b0, a1, b1, keep_v0, verts):
        """Set heptagon vertices for W-fold in position 2.

        verts: the array with vertex numbers.
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
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b0
            v3v5 = (v[3] + v[5]) / 2
            v3v5_axis = Vec(v[3] - v[5])
            rot_b0 = Rot(axis=v3v5_axis, angle=b0)
            v2v6 = (v[2] + v[6]) / 2
            v2v6_rot = v3v5 + rot_b0 * (v2v6 - v3v5)
            v[2] = v2v6_rot + (v[2] - v2v6)
            v6_tmp = v2v6_rot + (v[6] - v2v6)
            v1v0 = (v[1] + v[0]) / 2
            v1v0_rot = v3v5 + rot_b0 * (v1v0 - v3v5)
            v1_tmp = v1v0_rot + (v[1] - v1v0)
            v0_tmp = v1v0_rot + (v[0] - v1v0)

            # rot a0
            v2v5 = (v[2] + v[5]) / 2
            v2v5_axis = Vec(v[2] - v[5])
            rot_a0 = Rot(axis=v2v5_axis, angle=a0)
            v1v6 = (v1_tmp + v6_tmp) / 2
            v1v6_rot = v2v5 + rot_a0 * (v1v6 - v2v5)
            v1_tmp = v1v6_rot + (v1_tmp - v1v6)
            v[6] = v1v6_rot + (v6_tmp - v1v6)
            v0_tmp = v2v5 + rot_a0 * (v0_tmp - v2v5)

            # rot a1
            v2v6 = (v[2] + v[6]) / 2
            v2v6_axis = Vec(v[2] - v[6])
            rot_a1 = Rot(axis=v2v6_axis, angle=a1)
            v1v0 = (v1_tmp + v0_tmp) / 2
            v1v0_rot = v2v6 + rot_a1 * (v1v0 - v2v6)
            v[1] = v1v0_rot + (v1_tmp - v1v0)
            v0_tmp = v1v0_rot + (v0_tmp - v1v0)

            # rot b1
            v1v6 = (v[1] + v[6]) / 2
            v1v6_axis = Vec(v[1] - v[6])
            rot_b1 = Rot(axis=v1v6_axis, angle=b1)
            v[0] = v1v6 + rot_b1 * (v0_tmp - v1v6)

        self.Vs = v

    def fold_w3_help(self, a0, b0, a1, b1, keep_v0, verts):
        """Set heptagon vertices for W-fold in position 3.

        verts: the array with vertex numbers.
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
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot a0
            v3v6 = (v[3] + v[6]) / 2
            v3v6_axis = Vec(v[3] - v[6])
            rot_a0 = Rot(axis=v3v6_axis, angle=a0)
            v0v2 = (v[0] + v[2]) / 2
            v0v2_rot = v3v6 + rot_a0 * (v0v2 - v3v6)
            v[0] = v0v2_rot + (v[0] - v0v2)
            v2_tmp = v0v2_rot + (v[2] - v0v2)
            v1_tmp = v3v6 + rot_a0 * (v[1] - v3v6)

            # rot a1
            v3v0 = (v[3] + v[0]) / 2
            v3v0_axis = Vec(v[3] - v[0])
            rot_a1 = Rot(axis=v3v0_axis, angle=a1)
            v1v2 = (v1_tmp + v2_tmp) / 2
            v1v2_rot = v3v0 + rot_a1 * (v1v2 - v3v0)
            v1_tmp = v1v2_rot + (v1_tmp - v1v2)
            v[2] = v1v2_rot + (v2_tmp - v1v2)

            # rot b1
            v2v0 = (v[2] + v[0]) / 2
            v2v0_axis = Vec(v[2] - v[0])
            rot_b1 = Rot(axis=v2v0_axis, angle=b1)
            v[1] = v2v0 + rot_b1 * (v1_tmp - v2v0)

            # rot b0
            v6v4 = (v[6] + v[4]) / 2
            v6v4_axis = Vec(v[6] - v[4])
            rot_b0 = Rot(axis=v6v4_axis, angle=b0)
            v[5] = v6v4 + rot_b0 * (v[5] - v6v4)
            self.Vs = v

    def fold_w4_help(self, a0, b0, a1, b1, keep_v0, verts):
        """Set heptagon vertices for W-fold in position 4.

        verts: the array with vertex numbers.
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
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot a1
            v4v1 = (v[4] + v[1]) / 2
            v4v1_axis = Vec(v[4] - v[1])
            rot_a1 = Rot(axis=v4v1_axis, angle=-a1)
            # 0 2 -> 4 ,6 or 6, 4?
            v0v5 = (v[0] + v[5]) / 2
            v0v5_rot = v4v1 + rot_a1 * (v0v5 - v4v1)
            v[0] = v0v5_rot + (v[0] - v0v5)
            v5_tmp = v0v5_rot + (v[5] - v0v5)
            v6_tmp = v4v1 + rot_a1 * (v[6] - v4v1)

            # rot a0
            v4v0 = (v[4] + v[0]) / 2
            v4v0_axis = Vec(v[4] - v[0])
            rot_a0 = Rot(axis=v4v0_axis, angle=-a0)
            v6v5 = (v6_tmp + v5_tmp) / 2
            v6v5_rot = v4v0 + rot_a0 * (v6v5 - v4v0)
            v6_tmp = v6v5_rot + (v6_tmp - v6v5)
            v[5] = v6v5_rot + (v5_tmp - v6v5)

            # rot b0
            v5v0 = (v[5] + v[0]) / 2
            v5v0_axis = Vec(v[5] - v[0])
            rot_b0 = Rot(axis=v5v0_axis, angle=-b0)
            v[6] = v5v0 + rot_b0 * (v6_tmp - v5v0)

            # rot b1
            v1v3 = (v[1] + v[3]) / 2
            v1v3_axis = Vec(v[1] - v[3])
            rot_b1 = Rot(axis=v1v3_axis, angle=-b1)
            v[2] = v1v3 + rot_b1 * (v[2] - v1v3)
            self.Vs = v

    def fold_w5_help(self, a0, b0, a1, b1, keep_v0, verts):
        """Set heptagon vertices for W-fold in position 5."""
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
        self.fold_w2_help(
            -a1,
            -b1,
            -a0,
            -b0,
            keep_v0,
            [verts[0], verts[6], verts[5], verts[4], verts[3], verts[2], verts[1]],
        )
        v = self.Vs
        self.Vs = [v[0], v[6], v[5], v[4], v[3], v[2], v[1]]

    def fold_w6_help(self, a0, b0, a1, b1, keep_v0, verts):
        """Set heptagon vertices for W-fold in position 6."""
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
        self.fold_w1_help(
            -a1,
            -b1,
            -a0,
            -b0,
            keep_v0,
            [verts[0], verts[6], verts[5], verts[4], verts[3], verts[2], verts[1]],
        )
        v = self.Vs
        self.Vs = [v[0], v[6], v[5], v[4], v[3], v[2], v[1]]

    def fold_w1(self, a0, b0, a1, b1, keep_v0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V1-V4,
        the fold angle a1 refers to the axis V1-V5,
        The fold angle b0 refers to the axis V2-V4,
        The fold angle b1 refers to the axis V0-V5 and
        If keep_v0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(1)
        self.fold_w1_help(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_w2(self, a0, b0, a1, b1, keep_v0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V2-V5,
        the fold angle a1 refers to the axis V2-V6,
        The fold angle b0 refers to the axis V3-V5,
        The fold angle b1 refers to the axis V1-V6 and
        If keep_v0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(2)
        self.fold_w2_help(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_w3(self, a0, b0, a1, b1, keep_v0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V3-V6,
        the fold angle a1 refers to the axis V3-V0,
        The fold angle b0 refers to the axis V4-V6,
        The fold angle b1 refers to the axis V2-V0 and
        If keep_v0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(3)
        self.fold_w3_help(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_w4(self, a0, b0, a1, b1, keep_v0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V3-V6,
        the fold angle a1 refers to the axis V3-V0,
        The fold angle b0 refers to the axis V4-V6,
        The fold angle b1 refers to the axis V2-V0 and
        If keep_v0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(4)
        self.fold_w4_help(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_w5(self, a0, b0, a1, b1, keep_v0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V1-V4,
        the fold angle a1 refers to the axis V1-V5,
        The fold angle b0 refers to the axis V2-V4,
        The fold angle b1 refers to the axis V0-V5 and
        If keep_v0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(5)
        self.fold_w5_help(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_w6(self, a0, b0, a1, b1, keep_v0=True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers to the axis V6-V2,
        the fold angle a1 refers to the axis V6-V3,
        The fold angle b0 refers to the axis V2-V0 and
        The fold angle b1 refers to the axis V3-V5,
        If keep_v0 = True then the vertex V0 is kept invariant
        during folding, otherwise the edge V3 - V4 is kept invariant
        """
        self.fold_w_es_fs(6)
        self.fold_w6_help(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_mixed(self, a0, b0, a1, b1, keep_v0=True, rotate=0):
        """Define the vertices, edges and faces for a mixed-fold.

        For rotate == 0:
        The fold angle a0 refers the axis V0-V3
        the fold angle b0 refers the axes V0-V2
        The fold angle a1 refers the axis V0-V4
        the fold angle b1 refers the axes V6-V4
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        prj[rotate](a0, b0, a1, b1, keep_v0)

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

    def fold_mixed_0(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a mixed-fold position 0.

        The fold angle a0 refers the axis V0-V3
        the fold angle b0 refers the axis V0-V2
        the fold angle a1 refers the axis V0-V4
        the fold angle b1 refers the axis V6-V4
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(0)
            self.fold_mixed_0_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_mixed_0_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a mixed-fold position 0.

        verts: the array with vertex numbers.
        returns a new array.
        """
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot a0
            v0v3 = (v[0] + v[3]) / 2
            v0v3_axis = Vec(v[0] - v[3])
            # Note: negative angle
            rot_a0 = Rot(axis=v0v3_axis, angle=-a0)
            # middle of V1-V2 which is // to v0v3 axis
            v1v2 = (v[1] + v[2]) / 2
            v1v2_rot = v0v3 + rot_a0 * (v1v2 - v0v3)
            v[1] = v1v2_rot + (v[1] - v1v2)
            v[2] = v1v2_rot + (v[2] - v1v2)

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
            v6v5_rot = v0v4 + rot_a1 * (v6v5 - v0v4)
            v[6] = v6v5_rot + (v[6] - v6v5)
            v[5] = v6v5_rot + (v[5] - v6v5)

            # rot b1
            v6v4 = (v[6] + v[4]) / 2
            v6v4_axis = Vec(v[6] - v[4])
            rot_b1 = Rot(axis=v6v4_axis, angle=b1)
            v[5] = v6v4 + rot_b1 * (v[5] - v6v4)

        self.Vs = v

    def fold_mixed_1(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a mixed-fold position 1.

        The fold angle a0 refers the axis V1-V4
        the fold angle b0 refers the axis V1-V3
        the fold angle a1 refers the axis V1-V5
        the fold angle b1 refers the axis V0-V5
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(1)
            self.fold_mixed_1_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_mixed_1_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a mixed-fold position 1."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot a0
            v1v4 = (v[1] + v[4]) / 2
            v1v4_axis = Vec(v[1] - v[4])
            rot_a0 = Rot(axis=v1v4_axis, angle=a0)
            # middle of V0-V5 which is // to v1v4 axis
            v0v5 = (v[0] + v[5]) / 2
            v0v5_rot = v1v4 + rot_a0 * (v0v5 - v1v4)
            v[0] = v0v5_rot + (v[0] - v0v5)
            v[5] = v0v5_rot + (v[5] - v0v5)
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
            v0v6_rot = v1v5 + rot_a1 * (v0v6 - v1v5)
            v[0] = v0v6_rot + (v[0] - v0v6)
            v[6] = v0v6_rot + (v[6] - v0v6)

            # rot b1
            v0v5 = (v[0] + v[5]) / 2
            v0v5_axis = Vec(v[0] - v[5])
            rot_b1 = Rot(axis=v0v5_axis, angle=b1)
            v[6] = v0v5 + rot_b1 * (v[6] - v0v5)

        self.Vs = v

    def fold_mixed_2(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a mixed-fold position 2.

        The fold angle a0 refers the axis V2-V5
        the fold angle b0 refers the axis V2-V4
        the fold angle a1 refers the axis V2-V6
        the fold angle b1 refers the axis V1-V6
        The keep_v0 variable is ignored here (it is provided to be consistent
        with the other fold functions.)
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(2)
            self.fold_mixed_2_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_mixed_2_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a mixed-fold position 2."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b0
            v2v4 = (v[2] + v[4]) / 2
            v2v4_axis = Vec(v[2] - v[4])
            rot_b0 = Rot(axis=v2v4_axis, angle=b0)
            # middle of V1-V5 which is // to v2v4 axis
            v1v5 = (v[1] + v[5]) / 2
            v1v5_rot = v2v4 + rot_b0 * (v1v5 - v2v4)
            v[1] = v1v5_rot + (v[1] - v1v5)
            v[5] = v1v5_rot + (v[5] - v1v5)
            # middle of V0-V6 which is // to v2v4 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_rot = v2v4 + rot_b0 * (v0v6 - v2v4)
            v[0] = v0v6_rot + (v[0] - v0v6)
            v[6] = v0v6_rot + (v[6] - v0v6)

            # rot a0
            v2v5 = (v[2] + v[5]) / 2
            v2v5_axis = Vec(v[2] - v[5])
            rot_a0 = Rot(axis=v2v5_axis, angle=a0)
            # middle of V1-V6 which is // to v2v5 axis
            v1v6 = (v[1] + v[6]) / 2
            v1v6_rot = v2v5 + rot_a0 * (v1v6 - v2v5)
            v[1] = v1v6_rot + (v[1] - v1v6)
            v[6] = v1v6_rot + (v[6] - v1v6)
            v[0] = v2v5 + rot_a0 * (v[0] - v2v5)

            # rot a1
            v2v6 = (v[2] + v[6]) / 2
            v2v6_axis = Vec(v[2] - v[6])
            rot_a1 = Rot(axis=v2v6_axis, angle=a1)
            # middle of V1-V0 which is // to v2v6 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_rot = v2v6 + rot_a1 * (v1v0 - v2v6)
            v[1] = v1v0_rot + (v[1] - v1v0)
            v[0] = v1v0_rot + (v[0] - v1v0)

            # rot b1
            v1v6 = (v[1] + v[6]) / 2
            v1v6_axis = Vec(v[1] - v[6])
            rot_b1 = Rot(axis=v1v6_axis, angle=b1)
            v[0] = v1v6 + rot_b1 * (v[0] - v1v6)

        self.Vs = v

    def fold_mixed_3(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a mixed-fold position 3.

        The fold angle a0 refers the axis V3-V6
        the fold angle b0 refers the axis V3-V5
        the fold angle a1 refers the axis V3-V0
        the fold angle b1 refers the axis V2-V0
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(3)
            self.fold_mixed_3_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_mixed_3_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a mixed-fold position 3."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b0
            v3v5 = (v[3] + v[5]) / 2
            v3v5_axis = Vec(v[3] - v[5])
            rot_b0 = Rot(axis=v3v5_axis, angle=b0)
            # middle of V2-V6 which is // to v3v5 axis
            v2v6 = (v[2] + v[6]) / 2
            v2v6_rot = v3v5 + rot_b0 * (v2v6 - v3v5)
            v[2] = v2v6_rot + (v[2] - v2v6)
            v[6] = v2v6_rot + (v[6] - v2v6)
            # middle of V1-V0 which is // to v3v5 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_rot = v3v5 + rot_b0 * (v1v0 - v3v5)
            v[1] = v1v0_rot + (v[1] - v1v0)
            v[0] = v1v0_rot + (v[0] - v1v0)

            # rot a0
            v3v6 = (v[3] + v[6]) / 2
            v3v6_axis = Vec(v[3] - v[6])
            rot_a0 = Rot(axis=v3v6_axis, angle=a0)
            # middle of V2-V0 which is // to v3v6 axis
            v2v0 = (v[2] + v[0]) / 2
            v2v0_rot = v3v6 + rot_a0 * (v2v0 - v3v6)
            v[2] = v2v0_rot + (v[2] - v2v0)
            v[0] = v2v0_rot + (v[0] - v2v0)
            v[1] = v3v6 + rot_a0 * (v[1] - v3v6)

            # rot a1
            v3v0 = (v[3] + v[0]) / 2
            v3v0_axis = Vec(v[3] - v[0])
            rot_a1 = Rot(axis=v3v0_axis, angle=a1)
            # middle of V2-V1 which is // to v3v0 axis
            v2v1 = (v[2] + v[1]) / 2
            v2v1_rot = v3v0 + rot_a1 * (v2v1 - v3v0)
            v[2] = v2v1_rot + (v[2] - v2v1)
            v[1] = v2v1_rot + (v[1] - v2v1)

            # rot b1
            v2v0 = (v[2] + v[0]) / 2
            v2v0_axis = Vec(v[2] - v[0])
            rot_b1 = Rot(axis=v2v0_axis, angle=b1)
            v[1] = v2v0 + rot_b1 * (v[1] - v2v0)

        self.Vs = v

    def fold_mixed_4(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a mixed-fold position 4.

        The fold angle a0 refers the axis V4-V0
        the fold angle b0 refers the axis V4-V6
        the fold angle a1 refers the axis V4-V1
        the fold angle b1 refers the axis V3-V1
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(4)
            self.fold_mixed_4_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_mixed_4_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a mixed-fold position 4."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot a1
            v4v1 = (v[4] + v[1]) / 2
            v4v1_axis = Vec(v[4] - v[1])
            # Note: negative angle
            rot_a1 = Rot(axis=v4v1_axis, angle=-a1)
            # middle of V5-V0 which is // to v4v1 axis
            v5v0 = (v[5] + v[0]) / 2
            v5v0_rot = v4v1 + rot_a1 * (v5v0 - v4v1)
            v[5] = v5v0_rot + (v[5] - v5v0)
            v[0] = v5v0_rot + (v[0] - v5v0)
            v[6] = v4v1 + rot_a1 * (v[6] - v4v1)

            # rot a0
            v4v0 = (v[4] + v[0]) / 2
            v4v0_axis = Vec(v[4] - v[0])
            # Note: negative angle
            rot_a0 = Rot(axis=v4v0_axis, angle=-a0)
            # middle of V5-V6 which is // to v4v0 axis
            v5v6 = (v[5] + v[6]) / 2
            v5v6_rot = v4v0 + rot_a0 * (v5v6 - v4v0)
            v[5] = v5v6_rot + (v[5] - v5v6)
            v[6] = v5v6_rot + (v[6] - v5v6)

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

    def fold_mixed_5(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a mixed-fold position 5.

        The fold angle a0 refers the axis V5-V1
        the fold angle b0 refers the axis V5-V0
        the fold angle a1 refers the axis V5-V2
        the fold angle b1 refers the axis V4-V2
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(5)
            self.fold_mixed_5_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_mixed_5_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a mixed-fold position 5."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b1
            v4v2 = (v[4] + v[2]) / 2
            v4v2_axis = Vec(v[4] - v[2])
            # Note: negative angle
            rot_b1 = Rot(axis=v4v2_axis, angle=-b1)
            # middle of V5-V1 which is // to v4v2 axis
            v5v1 = (v[5] + v[1]) / 2
            v5v1_rot = v4v2 + rot_b1 * (v5v1 - v4v2)
            v[5] = v5v1_rot + (v[5] - v5v1)
            v[1] = v5v1_rot + (v[1] - v5v1)
            # middle of V6-V0 which is // to v4v2 axis
            v6v0 = (v[6] + v[0]) / 2
            v6v0_rot = v4v2 + rot_b1 * (v6v0 - v4v2)
            v[6] = v6v0_rot + (v[6] - v6v0)
            v[0] = v6v0_rot + (v[0] - v6v0)

            # rot a1
            v5v2 = (v[5] + v[2]) / 2
            v5v2_axis = Vec(v[5] - v[2])
            # Note: negative angle
            rot_a1 = Rot(axis=v5v2_axis, angle=-a1)
            # middle of V6-V1 which is // to v5v2 axis
            v6v1 = (v[6] + v[1]) / 2
            v6v1_rot = v5v2 + rot_a1 * (v6v1 - v5v2)
            v[6] = v6v1_rot + (v[6] - v6v1)
            v[1] = v6v1_rot + (v[1] - v6v1)
            v[0] = v5v2 + rot_a1 * (v[0] - v5v2)

            # rot a0
            v5v1 = (v[5] + v[1]) / 2
            v5v1_axis = Vec(v[5] - v[1])
            # Note: negative angle
            rot_a0 = Rot(axis=v5v1_axis, angle=-a0)
            # middle of V6-V0 which is // to v5v1 axis
            v6v0 = (v[6] + v[0]) / 2
            v6v0_rot = v5v1 + rot_a0 * (v6v0 - v5v1)
            v[6] = v6v0_rot + (v[6] - v6v0)
            v[0] = v6v0_rot + (v[0] - v6v0)

            # rot b0
            v5v0 = (v[5] + v[0]) / 2
            v5v0_axis = Vec(v[5] - v[0])
            # Note: negative angle
            rot_b0 = Rot(axis=v5v0_axis, angle=-b0)
            v[6] = v5v0 + rot_b0 * (v[6] - v5v0)

        self.Vs = v

    def fold_mixed_6(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a mixed-fold position 6.

        The fold angle a0 refers the axis V6-V2
        the fold angle b0 refers the axis V6-V1
        the fold angle a1 refers the axis V6-V3
        the fold angle b1 refers the axis V5-V3
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_mixed_es_fs(6)
            self.fold_mixed_6_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_mixed_6_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a mixed-fold position 6."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b1
            v5v3 = (v[5] + v[3]) / 2
            v5v3_axis = Vec(v[5] - v[3])
            # Note: negative angle
            rot_b1 = Rot(axis=v5v3_axis, angle=-b1)
            # middle of V6-V2 which is // to v5v3 axis
            v6v2 = (v[6] + v[2]) / 2
            v6v2_rot = v5v3 + rot_b1 * (v6v2 - v5v3)
            v[6] = v6v2_rot + (v[6] - v6v2)
            v[2] = v6v2_rot + (v[2] - v6v2)
            # middle of V0-V1 which is // to v5v3 axis
            v0v1 = (v[0] + v[1]) / 2
            v0v1_rot = v5v3 + rot_b1 * (v0v1 - v5v3)
            v[0] = v0v1_rot + (v[0] - v0v1)
            v[1] = v0v1_rot + (v[1] - v0v1)

            # rot a1
            v6v3 = (v[6] + v[3]) / 2
            v6v3_axis = Vec(v[6] - v[3])
            # Note: negative angle
            rot_a1 = Rot(axis=v6v3_axis, angle=-a1)
            # middle of V0-V2 which is // to v6v3 axis
            v0v2 = (v[0] + v[2]) / 2
            v0v2_rot = v6v3 + rot_a1 * (v0v2 - v6v3)
            v[0] = v0v2_rot + (v[0] - v0v2)
            v[2] = v0v2_rot + (v[2] - v0v2)
            v[1] = v6v3 + rot_a1 * (v[1] - v6v3)

            # rot a0
            v6v2 = (v[6] + v[2]) / 2
            v6v2_axis = Vec(v[6] - v[2])
            # Note: negative angle
            rot_a0 = Rot(axis=v6v2_axis, angle=-a0)
            # middle of V0-V1 which is // to v6v2 axis
            v0v1 = (v[0] + v[1]) / 2
            v0v1_rot = v6v2 + rot_a0 * (v0v1 - v6v2)
            v[0] = v0v1_rot + (v[0] - v0v1)
            v[1] = v0v1_rot + (v[1] - v0v1)

            # rot b0
            v6v1 = (v[6] + v[1]) / 2
            v6v1_axis = Vec(v[6] - v[1])
            # Note: negative angle
            rot_b0 = Rot(axis=v6v1_axis, angle=-b0)
            v[0] = v6v1 + rot_b0 * (v[0] - v6v1)

        self.Vs = v

    def fold_g(self, a0, b0, a1, b1, keep_v0=True, rotate=0):
        """
        Fold around the 4 diagonals from Vi, where i is the value of rotate e.g. V0.

        For rotate == 0:
        The fold angle a0 refers the axis V0-V2
        the fold angle b0 refers the axes V0-V3 and V0-V4.
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        prj[rotate](a0, b0, a1, b1, keep_v0)

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

    def fold_g_0(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges, and faces for a G-fold the standard position (0).

        The fold angle a0 refers the axis V0-V3
        the fold angle b0 refers the axis V0-V2
        the fold angle a1 refers the axis V0-V4
        the fold angle b1 refers the axis V6-V4
        The keep_v0 variable is ignored here (it is provided to be consistent
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(0)
            self.fold_g_0_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_g_0_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a G-fold the standard position (0).

        verts: the array with vertex numbers.
        returns a new array.
        """
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b0
            v2v4 = (v[2] + v[4]) / 2
            v2v4_axis = Vec(v[2] - v[4])
            rot_b0 = Rot(axis=v2v4_axis, angle=b0)
            # middle of V1-V5 which is // to v2v4 axis
            v1v5 = (v[1] + v[5]) / 2
            v1v5_rot = v2v4 + rot_b0 * (v1v5 - v2v4)
            v[1] = v1v5_rot + (v[1] - v1v5)
            v[5] = v1v5_rot + (v[5] - v1v5)
            # middle of V0-V6 which is // to v2v4 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_rot = v2v4 + rot_b0 * (v0v6 - v2v4)
            v[0] = v0v6_rot + (v[0] - v0v6)
            v[6] = v0v6_rot + (v[6] - v0v6)

            # rot a0
            v2v5 = (v[2] + v[5]) / 2
            v2v5_axis = Vec(v[2] - v[5])
            rot_a0 = Rot(axis=v2v5_axis, angle=a0)
            # middle of V1-V6 which is // to v2v5 axis
            v1v6 = (v[1] + v[6]) / 2
            v1v6_rot = v2v5 + rot_a0 * (v1v6 - v2v5)
            v[1] = v1v6_rot + (v[1] - v1v6)
            v[6] = v1v6_rot + (v[6] - v1v6)
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

    def fold_g_1(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a G-fold position 1."""
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(1)
            self.fold_g_1_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_g_1_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a G-fold position 1."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b0
            v3v5 = (v[3] + v[5]) / 2
            v3v5_axis = Vec(v[3] - v[5])
            rot_b0 = Rot(axis=v3v5_axis, angle=b0)
            # middle of V2-V6 which is // to v3v5 axis
            v2v6 = (v[2] + v[6]) / 2
            v2v6_rot = v3v5 + rot_b0 * (v2v6 - v3v5)
            v[2] = v2v6_rot + (v[2] - v2v6)
            v[6] = v2v6_rot + (v[6] - v2v6)
            # middle of V1-V0 which is // to v3v5 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_rot = v3v5 + rot_b0 * (v1v0 - v3v5)
            v[1] = v1v0_rot + (v[1] - v1v0)
            v[0] = v1v0_rot + (v[0] - v1v0)

            # rot a0
            v3v6 = (v[3] + v[6]) / 2
            v3v6_axis = Vec(v[3] - v[6])
            rot_a0 = Rot(axis=v3v6_axis, angle=a0)
            # middle of V2-V0 which is // to v3v6 axis
            v2v0 = (v[2] + v[0]) / 2
            v2v0_rot = v3v6 + rot_a0 * (v2v0 - v3v6)
            v[2] = v2v0_rot + (v[2] - v2v0)
            v[0] = v2v0_rot + (v[0] - v2v0)
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

    def fold_g_2(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a G-fold position 2."""
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(2)
            self.fold_g_2_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_g_2_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a G-fold position 2."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b1
            v2v4 = (v[2] + v[4]) / 2
            v2v4_axis = Vec(v[2] - v[4])
            rot_b1 = Rot(axis=v2v4_axis, angle=b1)
            # middle of V1-V5 which is // to v2v4 axis
            v1v5 = (v[1] + v[5]) / 2
            v1v5_rot = v2v4 + rot_b1 * (v1v5 - v2v4)
            v[1] = v1v5_rot + (v[1] - v1v5)
            v[5] = v1v5_rot + (v[5] - v1v5)
            # middle of V0-V6 which is // to v2v4 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_rot = v2v4 + rot_b1 * (v0v6 - v2v4)
            v[0] = v0v6_rot + (v[0] - v0v6)
            v[6] = v0v6_rot + (v[6] - v0v6)

            # rot a0
            v0v4 = (v[0] + v[4]) / 2
            v0v4_axis = Vec(v[0] - v[4])
            rot_a0 = Rot(axis=v0v4_axis, angle=a0)
            # middle of V5-V6 which is // to v0v4 axis
            v5v6 = (v[5] + v[6]) / 2
            v5v6_rot = v0v4 + rot_a0 * (v5v6 - v0v4)
            v[5] = v5v6_rot + (v[5] - v5v6)
            v[6] = v5v6_rot + (v[6] - v5v6)

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

    def fold_g_3(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a G-fold position 3."""
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(3)
            self.fold_g_3_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_g_3_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a G-fold position 3."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot b1
            v3v5 = (v[3] + v[5]) / 2
            v3v5_axis = Vec(v[3] - v[5])
            rot_b1 = Rot(axis=v3v5_axis, angle=b1)
            # middle of V2-V6 which is // to v3v5 axis
            v2v6 = (v[2] + v[6]) / 2
            v2v6_rot = v3v5 + rot_b1 * (v2v6 - v3v5)
            v[2] = v2v6_rot + (v[2] - v2v6)
            v[6] = v2v6_rot + (v[6] - v2v6)
            # middle of V1-V0 which is // to v3v5 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_rot = v3v5 + rot_b1 * (v1v0 - v3v5)
            v[1] = v1v0_rot + (v[1] - v1v0)
            v[0] = v1v0_rot + (v[0] - v1v0)

            # rot a0
            v1v5 = (v[1] + v[5]) / 2
            v1v5_axis = Vec(v[1] - v[5])
            rot_a0 = Rot(axis=v1v5_axis, angle=a0)
            # middle of V6-V0 which is // to v1v5 axis
            v6v0 = (v[6] + v[0]) / 2
            v6v0_rot = v1v5 + rot_a0 * (v6v0 - v1v5)
            v[6] = v6v0_rot + (v[6] - v6v0)
            v[0] = v6v0_rot + (v[0] - v6v0)

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

    def fold_g_4(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a G-fold position 4."""
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(4)
            self.fold_g_4_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_g_4_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a G-fold position 4."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot a1
            v4v2 = (v[4] + v[2]) / 2
            v4v2_axis = Vec(v[4] - v[2])
            rot_a1 = Rot(axis=v4v2_axis, angle=-a1)
            # middle of V1-V5 which is // to v4v2 axis
            v1v5 = (v[1] + v[5]) / 2
            v1v5_rot = v4v2 + rot_a1 * (v1v5 - v4v2)
            v[1] = v1v5_rot + (v[1] - v1v5)
            v[5] = v1v5_rot + (v[5] - v1v5)
            # middle of V0-V6 which is // to v4v2 axis
            v0v6 = (v[0] + v[6]) / 2
            v0v6_rot = v4v2 + rot_a1 * (v0v6 - v4v2)
            v[0] = v0v6_rot + (v[0] - v0v6)
            v[6] = v0v6_rot + (v[6] - v0v6)

            # rot a0
            v2v6 = (v[2] + v[6]) / 2
            v2v6_axis = Vec(v[2] - v[6])
            rot_a0 = Rot(axis=v2v6_axis, angle=a0)
            # middle of V0-V1 which is // to v2v6 axis
            v0v1 = (v[0] + v[1]) / 2
            v0v1_rot = v2v6 + rot_a0 * (v0v1 - v2v6)
            v[0] = v0v1_rot + (v[0] - v0v1)
            v[1] = v0v1_rot + (v[1] - v0v1)

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

    def fold_g_5(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a G-fold position 5."""
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(5)
            self.fold_g_5_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_g_5_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a G-fold position 5."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot a1
            v5v3 = (v[5] + v[3]) / 2
            v5v3_axis = Vec(v[5] - v[3])
            rot_a1 = Rot(axis=v5v3_axis, angle=-a1)
            # middle of V2-V6 which is // to v5v3 axis
            v2v6 = (v[2] + v[6]) / 2
            v2v6_rot = v5v3 + rot_a1 * (v2v6 - v5v3)
            v[2] = v2v6_rot + (v[2] - v2v6)
            v[6] = v2v6_rot + (v[6] - v2v6)
            # middle of V0-V6 which is // to v5v3 axis
            v1v0 = (v[1] + v[0]) / 2
            v1v0_rot = v5v3 + rot_a1 * (v1v0 - v5v3)
            v[1] = v1v0_rot + (v[1] - v1v0)
            v[0] = v1v0_rot + (v[0] - v1v0)

            # rot a0
            v3v0 = (v[3] + v[0]) / 2
            v3v0_axis = Vec(v[3] - v[0])
            rot_a0 = Rot(axis=v3v0_axis, angle=a0)
            # middle of V1-V2 which is // to v3v0 axis
            v1v2 = (v[1] + v[2]) / 2
            v1v2_rot = v3v0 + rot_a0 * (v1v2 - v3v0)
            v[1] = v1v2_rot + (v[1] - v1v2)
            v[2] = v1v2_rot + (v[2] - v1v2)

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

    def fold_g_6(self, a0, b0, a1, b1, keep_v0=True):
        """Define the vertices, edges and faces for a G-fold position 6."""
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
        if keep_v0:
            assert False, "TODO"
        else:
            self.fold_g_es_fs(6)
            self.fold_g_6_vs(a0, b0, a1, b1, keep_v0, self.vs_org)

    def fold_g_6_vs(self, a0, b0, a1, b1, keep_v0, verts):
        """Define the vertices for a G-fold position 6."""
        v = verts.copy()
        if keep_v0:
            assert False, "TODO"
        else:
            # rot a0
            v4v1 = (v[4] + v[1]) / 2
            v4v1_axis = Vec(v[4] - v[1])
            rot_a0 = Rot(axis=v4v1_axis, angle=-a0)
            # middle of V5-V0 which is // to v4v1 axis
            v5v0 = (v[5] + v[0]) / 2
            v5v0_rot = v4v1 + rot_a0 * (v5v0 - v4v1)
            v[5] = v5v0_rot + (v[5] - v5v0)
            v[0] = v5v0_rot + (v[0] - v5v0)
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

    def translate(self, t):
        """Translate the heptagon by t (geomtypes.Vec3)."""
        for i in range(len(self.Vs)):
            self.Vs[i] = t + self.Vs[i]

    def rotate(self, axis, angle):
        """Rotate the heptagon by the specified angle (radians) around the specified axis."""
        self.transform(Rot(axis=axis, angle=angle))

    def transform(self, t):
        """Transform the heptagon by t (geomtypes.Transform3)."""
        for i in range(len(self.Vs)):
            self.Vs[i] = t * self.Vs[i]


def kite_to_hept(left, top, right, bottom, alt_hept_pos=False):
    """Return the a tuple with vertices and the normal of an equilateral
    heptagon for a kite, v_left, v_top, v_right, v_bottom; the tuple has the following structure:
    ([h0, h1, h2, h3, h4, h5, h6], normal), with h0 = top.

    left: left coordinate
    top: top coordinate
    right: right coordinate
    bottom: bottom coordinate
    alt_hept_pos: 2 possible orientations for the heptagons exists. If false then the preferred
        position is returned, otherwise the heptagon will be 'upside down'.
    """
    if not alt_hept_pos:
        v_left = Vec(left)
        v_top = Vec(top)
        v_right = Vec(right)
        v_bottom = Vec(bottom)
    else:
        v_left = Vec(right)
        v_top = Vec(bottom)
        v_right = Vec(left)
        v_bottom = Vec(top)
    v_o = (v_left + v_right) / 2
    d_r = v_o - v_right
    d_u = v_o - v_top
    w = d_r.norm()
    f = d_u.norm()
    g = (v_o - v_bottom).norm()

    if f == 0:
        logging.warning("kite_to_hept: f == 0")
        return ()
    if w == 0:
        logging.warning("kite_to_hept: warning w == 0")
        return ()
    # if f > g:
    #    f, g = g, f

    r = f / w
    q = g / w
    n = math.sqrt(1.0 + q * q) / 2
    m = math.sqrt(1.0 + r * r) / 2
    k = m * (1.0 + 1.0 / n)

    qkpr = q * k + r
    root = k * (2 - k) + r * r

    # assert(root>=0)
    if root < 0:
        logging.warning("kite2Hept: negative sqrt requested")
        return ()

    nom = f + g
    denom = qkpr + math.sqrt(root)

    if denom == 0:
        logging.warning("kite2Hept: denom == 0")
        return ()

    w1 = nom / denom

    w1_factor = w1 / w
    w2_factor = k * w1_factor
    w3_factor = m * w1_factor

    def rel_position(v0, v1, rat):
        return rat * (v1 - v0) + v0


    # h0 = v_top
    h1 = rel_position(v_top, v_right, w1_factor)
    h2 = rel_position(v_bottom, v_right, w2_factor)
    h3 = rel_position(v_bottom, v_right, w3_factor)
    h4 = rel_position(v_bottom, v_left, w3_factor)
    h5 = rel_position(v_bottom, v_left, w2_factor)
    h6 = rel_position(v_top, v_left, w1_factor)

    n = d_r.cross(d_u).normalize()

    # C = (v_top + h1 + h2 + h3 + h4 + h5 + h6) / 7
    # return ([v_top, h1, h2, h3, h4, h5, h6], n)
    # Don't return Vector types, since I had problems with this on a MS. Windows
    # OS.
    return (
        [
            Vec([v_top[0], v_top[1], v_top[2]]),
            Vec([h1[0], h1[1], h1[2]]),
            Vec([h2[0], h2[1], h2[2]]),
            Vec([h3[0], h3[1], h3[2]]),
            Vec([h4[0], h4[1], h4[2]]),
            Vec([h5[0], h5[1], h5[2]]),
            Vec([h6[0], h6[1], h6[2]]),
        ],
        Vec(n),
    )


class FldHeptagonShape(Geom3D.CompoundShape):
    """Base class for symmetric polyhedra with folded regular heptagons.

    The polyhedron consists with two heptagons sharing an edge, where the centre of the edge is
    positioned on a 2-fold symmetry axis of the polyhedron. The heptagons are folded over diagonals
    and the pair can be translated along and rotated around that 2-fold axis.
    """
    edge_alt = 0
    opposite_edge_alt = 0

    def __init__(self, shapes, name="Folded Regular Heptagons"):
        Geom3D.CompoundShape.__init__(self, shapes, name=name)
        self.heptagon = RegularHeptagon()
        self.dihedral_angle = 1.2
        self.pos_angle_min = 0
        self.pos_angle_max = math.pi / 2
        self._pos_angle = 0
        self.has_reflections = True
        self._rotate_fold = 0
        self.fold1 = 0.0
        self.fold2 = 0.0
        self.opposite_fold1 = 0.0
        self.opposite_fold2 = 0.0
        self.fold_heptagon = FoldMethod.PARALLEL
        self.height = 2.3
        self.apply_symmetries = True
        # Whether to fill up between the heptagons with extra faces (e.g. triangles)
        self.add_extra_faces = True
        # Whether all faces (incl. triangles, e.g. on O3 axis) are regular:
        self.all_regular_faces = False

    def __repr__(self):
        # s = '%s(\n  ' % findModuleClassName(self.__class__, __name__)
        s = "FldHeptagonShape(\n"
        s += "  shapes = [\n"
        for shape in self.shapeElements:
            s += f"    {repr(shape)},\n"
        s += f"  ],\n  "
        s += f'name = "{self.name}"\n'
        s += ")\n"
        if __name__ != "__main__":
            s = f"{__name__}.{s}"
        return s

    def gl_draw(self):
        if self.update_shape:
            self.set_vertices()
        Geom3D.CompoundShape.gl_draw(self)

    def set_edge_alt(self, alt=None, opposite_alt=None):
        """Set how to connected vertices of different heptagons to get triangles.

        alt: the edge alternative, a TrisAlt number
        opposite_alt: if no reflections are required, specify the opposite edges as well.
        """
        if alt is not None:
            self.edge_alt = alt
        if opposite_alt is not None:
            self.opposite_edge_alt = opposite_alt
        self.update_shape = True

    def set_fold_method(self, method, update_shape=True):
        """Set which fold method (FoldMethod enum) is used."""
        self.fold_heptagon = method
        self.update_shape = update_shape

    @property
    def rotate_fold(self):
        """Get the orientation of the heptagon fold."""
        return self._rotate_fold

    @rotate_fold.setter
    def rotate_fold(self, step):
        """Update the heptagon fold to a different orientation."""
        self._rotate_fold = step
        self.update_shape = True

    def set_dihedral_angle(self, angle):
        """Set angle (radians) between two heptagons sharing an edge."""
        self.dihedral_angle = angle
        self.update_shape = True

    @property
    def pos_angle(self):
        """Get rotation angle around 2-fold axis of heptagon inside polyhedron."""
        return self._pos_angle

    @pos_angle.setter
    def pos_angle(self, angle):
        """Set rotation angle around 2-fold axis of heptagon inside polyhedron."""
        self._pos_angle = angle
        self.update_shape = True

    def set_tri_fill_pos(self, position):  # pylint: disable=R0201, W0613
        """Update face and edge data of how triangles are connected.

        Note that this still uses the same structure (or edge alternative) but which vertices are
        connected is shifted, normally dependent on the position angle of the heptagon (rotation
        around the 2-fold axis.
        """
        logging.warning("implement in derived class")

    def set_fold1(self, angle=None, opposite_angle=None):
        """Set the fold angle (radians) around the first (pair of) heptagon diagonals.

        If reflections are required then only angle needs to be set and the same angle will be used
        for the opposite heptagon. Otherwise specify both angle and opposite_angle.
        """
        if angle is not None:
            self.fold1 = angle
        if opposite_angle is not None:
            self.opposite_fold1 = opposite_angle
        self.update_shape = True

    def set_fold2(self, angle=None, opposite_angle=None):
        """Set the fold angle (radians) around the second (pair of) heptagon diagonals.

        If reflections are required then only angle needs to be set and the same angle will be used
        for the opposite heptagon. Otherwise specify both angle and opposite_angle.
        """
        if angle is not None:
            self.fold2 = angle
        if opposite_angle is not None:
            self.opposite_fold2 = opposite_angle
        self.update_shape = True

    def set_height(self, height):
        """Set distance between the (unfolded) heptagon and the origin."""
        self.height = height
        self.update_shape = True

    def get_status_str(self):
        """Return a string to be written on the status bar for the user."""
        return (
            f"T = {self.height:02.2f}, Angle = {self.dihedral_angle:01.2f} rad, "
            f"fold1 = {self.fold1:01.2f} ({self.opposite_fold1:01.2f}) rad, "
            f"fold2 = {self.fold2:01.2f} ({self.opposite_fold2:01.2f}) rad"
        )

    @property
    def refl_pos_angle(self):
        """Return the pos angle for a polyhedron with reflections."""
        if self.edge_alt == TrisAlt.refl_1:
            return 0
        return self.pos_angle_max

    def position_heptagon(self):
        """
        Define all vertices of the heptagon according to the current settings.

        Fold the parts of the heptagon, put it at the correct height, rotate it around the 2-fold
        axis with the right angle, and use the corrent dihedral angle by rotating around one edge.
        """
        self.heptagon.fold(
            self.fold1,
            self.fold2,
            self.opposite_fold1,
            self.opposite_fold2,
            keep_v0=False,
            fold=self.fold_heptagon,
            rotate=self._rotate_fold,
        )
        self.heptagon.translate(HEPT_HEIGHT * geomtypes.UY)
        # Note: the rotation angle != the dihedral angle
        self.heptagon.rotate(-geomtypes.UX, geomtypes.QUARTER_TURN - self.dihedral_angle)
        self.heptagon.translate(self.height * geomtypes.UZ)
        if self._pos_angle != 0:
            self.heptagon.rotate(-geomtypes.UZ, self._pos_angle)

    def set_vertices(self):
        """Make sure all vertices of the polyhedron are set."""
        self.position_heptagon()


class FldHeptagonCtrlWin(wx.Frame):
    """
    Widgets to control a polyhedron with folded regular heptagons.

    Attributes:
    - refl_min_size: minimum window size when relfections are included
    - rot_min_size: minimum window size when only rotations are included
    - pre_pos_file_name: holds the name when a file was loaded with predefined properies. If none,
      then no predefined file is being displaued.
    """
    refl_min_size = (525, 425)
    rot_min_size = (545, 600)
    pre_pos_file_name = None

    """
    Hidded attributes:
    _rotate_fold: when no reflections are required then a certain heptagon fold can be used in 7
        different positions. This attribute expresses the offset of the current option.
    _std_pre_pos: all folds and offsets for the predefined heptagon that is used
    _pre_pos_map: maps a string with a certain heptagon setup to a index in the choice list. These
        options OPEN_FILE, DYN_POS, ONLY_HEPTS, ONLY_O3_TRIANGLES, etc
    _sym_incl_refl: whether polyhedron symmetry includes reflections.
    """
    _rotate_fold = 1
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
            max_height,
            pre_pos_strings,
            triangle_alts,
            pre_pos_to_number,
            parent,
            *args,
            **kwargs,
    ):
        """Create a control window for the scene that folds heptagons

        shape: the Geom3D shape object that is shown
        canvas: wx canvas to be used
        max_height: max translation height to be used for the heptagon
        pre_pos_strings: a list with representation strings, used in the UI, with predefined models
            with regular folded heptagons. These models were calculated before and added to the
            program. For instance one of strings can be "Heptagons only" for a model with only
            regular folded heptagons.
        triangle_alts: an array consisting of TrisAltBase derived objects. Each element in the
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
        self.max_height = max_height
        self.pre_pos_strings = pre_pos_strings
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
        self.restore_tris = False
        self.restore_o3_tris = False
        self.shape.set_fold_method(self.fold_method, update_shape=False)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.special_pos_idx = 0

        self.main_sizer.Add(
            self.create_control_sizer(), 1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
        )
        self.set_default_size(self.refl_min_size)
        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.main_sizer)
        self.Show(True)
        self.panel.Layout()
        self.prev_tris_fill = -1
        self.prev_opp_tris_fill = -1

    @property
    def fold_method(self):
        """Retrieve the current fold method."""
        return self.fold_method_incl_refl[self._sym_incl_refl]

    @fold_method.setter
    def fold_method(self, fold_method):
        """Set the current fold method."""
        self.fold_method_incl_refl[self._sym_incl_refl] = fold_method
        self.shape.set_fold_method(fold_method)

    def create_control_sizer(self):
        """Create the main sizer with all the control widgets."""
        self.height_factor = 40  # slider step factor, or: 1 / slider step

        self.guis = []

        # static adjustments
        self.tris_fill_gui = wx.Choice(self.panel, style=wx.RA_VERTICAL, choices=[])
        self.guis.append(self.tris_fill_gui)
        self.tris_fill_gui.Bind(wx.EVT_CHOICE, self.on_triangle_fill)
        self.update_triangle_fill_options()

        self.tris_pos_gui = wx.Choice(
            self.panel,
            style=wx.RA_VERTICAL,
            choices=[f"Position {i + 1}" for i in range(self.nr_of_positions)],
        )
        self.guis.append(self.tris_pos_gui)
        self.tris_pos_gui.Bind(wx.EVT_CHOICE, self.on_triangle_pos)
        self.update_triangle_fill_options()

        self.refl_gui = wx.CheckBox(self.panel, label="Reflections Required")
        self.guis.append(self.refl_gui)
        self.refl_gui.SetValue(self.shape.has_reflections)
        self.refl_gui.Bind(wx.EVT_CHECKBOX, self.on_refl)

        self.rot_fold_gui = wx.Button(self.panel, label="Rotate Fold 1/7")
        self._rotate_fold = 0
        self.guis.append(self.rot_fold_gui)
        self.rot_fold_gui.Bind(wx.EVT_BUTTON, self.on_rotate_fold)

        # View Settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        self.apply_sym_gui = wx.CheckBox(self.panel, label="Apply Symmetry")
        self.guis.append(self.apply_sym_gui)
        self.apply_sym_gui.SetValue(self.shape.apply_symmetries)
        self.apply_sym_gui.Bind(wx.EVT_CHECKBOX, self.on_apply_symmetry)
        self.add_tris_gui = wx.CheckBox(self.panel, label="Show Triangles")
        self.guis.append(self.add_tris_gui)
        self.add_tris_gui.SetValue(self.shape.add_extra_faces)
        self.add_tris_gui.Bind(wx.EVT_CHECKBOX, self.on_add_triangles)

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
        self.fold_method_items = [FoldMethod.get(fold) for fold in self.fold_method_list]
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
        self.guis.append(self.fold_method_gui)
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
        self.set_enable_prepos_items()
        self.guis.append(self.pre_pos_gui)
        self.pre_pos_gui.Bind(wx.EVT_CHOICE, self.on_pre_pos)

        self.open_file_button = wx.Button(self.panel, label="Open File")
        self.first_button = wx.Button(self.panel, label="First")
        self.next_button = wx.Button(self.panel, label="Next")
        self.number_text = wx.Button(self.panel, label="---", style=wx.NO_BORDER)
        self.prev_button = wx.Button(self.panel, label="Prev")
        self.last_button = wx.Button(self.panel, label="Last")
        self.guis.append(self.open_file_button)
        self.guis.append(self.first_button)
        self.guis.append(self.next_button)
        self.guis.append(self.number_text)
        self.guis.append(self.prev_button)
        self.guis.append(self.last_button)
        self.open_file_button.Bind(wx.EVT_BUTTON, self.on_open_file)
        self.first_button.Bind(wx.EVT_BUTTON, self.on_first)
        self.next_button.Bind(wx.EVT_BUTTON, self.on_next)
        self.prev_button.Bind(wx.EVT_BUTTON, self.on_prev)
        self.last_button.Bind(wx.EVT_BUTTON, self.on_last)

        # dynamic adjustments
        self.pos_angle_gui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.pos_angle,
            minValue=Geom3D.Rad2Deg * self.shape.pos_angle_min,
            maxValue=Geom3D.Rad2Deg * self.shape.pos_angle_max,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.guis.append(self.pos_angle_gui)
        self.pos_angle_gui.Bind(wx.EVT_SLIDER, self.on_pos_angle)
        self.min_fold_angle = -180
        self.max_fold_angle = 180
        self.dihedral_angle_gui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.dihedral_angle,
            minValue=self.min_fold_angle,
            maxValue=self.max_fold_angle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.guis.append(self.dihedral_angle_gui)
        self.dihedral_angle_gui.Bind(wx.EVT_SLIDER, self.on_dihedral_angle)
        self.fold1_gui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.fold1,
            minValue=self.min_fold_angle,
            maxValue=self.max_fold_angle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.guis.append(self.fold1_gui)
        self.fold1_gui.Bind(wx.EVT_SLIDER, self.on_fold1)
        self.fold2_gui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.fold2,
            minValue=self.min_fold_angle,
            maxValue=self.max_fold_angle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.guis.append(self.fold2_gui)
        self.fold2_gui.Bind(wx.EVT_SLIDER, self.on_fold2)
        self.opp_fold1_gui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.opposite_fold1,
            minValue=self.min_fold_angle,
            maxValue=self.max_fold_angle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.guis.append(self.opp_fold1_gui)
        self.opp_fold1_gui.Bind(wx.EVT_SLIDER, self.on_opp_fold1)
        self.opp_fold2_gui = wx.Slider(
            self.panel,
            value=Geom3D.Rad2Deg * self.shape.opposite_fold2,
            minValue=self.min_fold_angle,
            maxValue=self.max_fold_angle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
        )
        self.guis.append(self.opp_fold2_gui)
        self.opp_fold2_gui.Bind(wx.EVT_SLIDER, self.on_opp_fold2)
        self.height_gui = wx.Slider(
            self.panel,
            value=self.max_height - self.shape.height * self.height_factor,
            minValue=-self.max_height * self.height_factor,
            maxValue=self.max_height * self.height_factor,
            style=wx.SL_VERTICAL,
        )
        self.guis.append(self.height_gui)
        self.height_gui.Bind(wx.EVT_SLIDER, self.on_height)
        if self.shape.has_reflections:
            self.disable_guis_for_refl(force=True)

        self.set_orient_gui = wx.TextCtrl(self.panel)
        self.guis.append(self.set_orient_gui)
        self.set_orient_button = wx.Button(self.panel, label="Apply")
        self.guis.append(self.set_orient_button)
        self.set_orient_button.Bind(wx.EVT_BUTTON, self.on_set_fold_values)
        self.clean_orient_button = wx.Button(self.panel, label="Clean")
        self.guis.append(self.clean_orient_button)
        self.clean_orient_button.Bind(wx.EVT_BUTTON, self.on_clean_fold_values)

        # Sizers
        self.boxes = []

        # sizer with view settings
        self.boxes.append(wx.StaticBox(self.panel, label="View Settings"))
        settings_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        settings_sizer.Add(self.apply_sym_gui, 0, wx.EXPAND)
        settings_sizer.Add(self.add_tris_gui, 0, wx.EXPAND)
        settings_sizer.Add(self.refl_gui, 0, wx.EXPAND)
        settings_sizer.Add(self.rot_fold_gui, 0, wx.EXPAND)
        settings_sizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        # The sizers holding the special positions
        self.boxes.append(wx.StaticBox(self.panel, label="Special Positions"))
        pos_sizer_sub_v = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
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
        self.boxes.append(wx.StaticBox(self.panel, label="Triangle Fill Alternative"))
        fill_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        fill_sizer.Add(self.tris_fill_gui, 0, wx.EXPAND)
        fill_sizer.Add(self.tris_pos_gui, 0, wx.EXPAND)

        stat_sizer = wx.BoxSizer(wx.HORIZONTAL)
        stat_sizer.Add(self.fold_method_gui, 0, wx.EXPAND)
        stat_sizer.Add(fill_sizer, 0, wx.EXPAND)
        stat_sizer.Add(settings_sizer, 0, wx.EXPAND)
        stat_sizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        pos_sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        # sizer holding the dynamic adjustments
        spec_pos_dynamic = wx.BoxSizer(wx.VERTICAL)
        self.boxes.append(wx.StaticBox(self.panel, label="Dihedral Angle (Degrees)"))
        angle_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
        angle_sizer.Add(self.dihedral_angle_gui, 1, wx.EXPAND)
        self.boxes.append(wx.StaticBox(self.panel, label="Fold 1 Angle (Degrees)"))
        fold1_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        fold1_sizer.Add(self.fold1_gui, 1, wx.EXPAND)
        self.boxes.append(wx.StaticBox(self.panel, label="Fold 2 Angle (Degrees)"))
        fold2_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        fold2_sizer.Add(self.fold2_gui, 1, wx.EXPAND)
        self.boxes.append(wx.StaticBox(self.panel, label="Positional Angle (Degrees)"))
        pos_angle_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
        pos_angle_sizer.Add(self.pos_angle_gui, 1, wx.EXPAND)
        self.boxes.append(
            wx.StaticBox(self.panel, label="Opposite Fold 1 Angle (Degrees)")
        )
        opp_fold1_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        opp_fold1_sizer.Add(self.opp_fold1_gui, 1, wx.EXPAND)
        self.boxes.append(
            wx.StaticBox(self.panel, label="Opposite Fold 2 Angle (Degrees)")
        )
        opp_fold2_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        opp_fold2_sizer.Add(self.opp_fold2_gui, 1, wx.EXPAND)

        self.boxes.append(wx.StaticBox(self.panel, label="Offset T"))
        height_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        height_sizer.Add(self.height_gui, 1, wx.EXPAND)
        spec_pos_dynamic.Add(angle_sizer, 0, wx.EXPAND)
        spec_pos_dynamic.Add(fold1_sizer, 0, wx.EXPAND)
        spec_pos_dynamic.Add(fold2_sizer, 0, wx.EXPAND)
        spec_pos_dynamic.Add(pos_angle_sizer, 0, wx.EXPAND)
        spec_pos_dynamic.Add(opp_fold1_sizer, 0, wx.EXPAND)
        spec_pos_dynamic.Add(opp_fold2_sizer, 0, wx.EXPAND)
        spec_pos_dynamic.Add(wx.BoxSizer(), 1, wx.EXPAND)
        pos_sizer_h.Add(spec_pos_dynamic, 3, wx.EXPAND)
        pos_sizer_h.Add(height_sizer, 1, wx.EXPAND)

        self.boxes.append(
            wx.StaticBox(self.panel, label="Set Orientation Directly (specify array)")
        )
        set_orientation_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
        set_orientation_sizer.Add(self.set_orient_gui, 1, wx.EXPAND)
        set_orientation_sizer.Add(self.set_orient_button, 0, wx.EXPAND)
        set_orientation_sizer.Add(self.clean_orient_button, 0, wx.EXPAND)

        # MAIN sizer
        main_sizer_v = wx.BoxSizer(wx.VERTICAL)
        main_sizer_v.Add(stat_sizer, 0, wx.EXPAND)
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

    def is_prepos_valid(self, pre_pos_id):
        """Return True if the pre defined position is valid, False otherwise.

        Valid here means that the model has the right symmetry conform the current settings.
        """
        if self.shape.has_reflections:
            psp = self.predefReflSpecPos
        else:
            psp = self.predefRotSpecPos
        return pre_pos_id in psp

    def filename_map_fold_method(self, filename):
        """From a JSON with predefined positioned return the heptagon fold name."""
        result = re.search(r"-fld_([^.]*)\.", filename)
        if result:
            return result.groups()[0]
        self.printFileStrMapWarning(filename, "filename_map_fold_method")
        return ""

    def filename_map_fold_pos_str(self, filename):
        """Extract the fold position from the filename and return as string.

        The fold position can be an integer between 0 - 6 that states how a certain heptagon fold i
        oriented inside the heptagon. This is only used for polyhedra that don't include
        reflections. If the polyhedron does include reflections, then there is normally only 1
        valid orientation.
        """
        result = re.search(r"-fld_[^.]*\.([0-6])-.*", filename)
        if result:
            return result.groups()[0]
        self.printFileStrMapWarning(filename, "filename_map_fold_pos_str")
        return ""

    def filename_map_fold_pos(self, filename):
        """Extract the fold position from the filename and return as string.

        See filename_map_fold_pos_str for more info.
        """
        fold_pos = self.filename_map_fold_pos_str(filename)
        if fold_pos:
            return int(fold_pos)
        return 0

    def filename_map_has_reflections(self, filename):
        """From a JSON with predefined positioned check whether there are opposite symmetries."""
        slider_values = re.search(r".*frh-roots-(.*)-fld_.*", filename)
        if slider_values:
            pos_vals = slider_values.groups()[0].split("_")
            no_of_vals = len(pos_vals)
            return (no_of_vals == 4) or (no_of_vals == 5 and pos_vals[4] == "0")
        self.printFileStrMapWarning(filename, "filename_map_has_reflections")
        return True

    def filename_map_tris_fill(self, filename):
        """From a JSON with predefined positioned get the triangle fill configuration."""
        # New format: incl -pos:
        result = re.search(r"-fld_[^.]*\.[0-7]-([^.]*)\-pos-.*.json", filename)
        if result is None:
            # try old method:
            result = re.search(r"-fld_[^.]*\.[0-7]-([^.]*)\.json", filename)
        if result:
            tris_str = result.groups()[0]
            return self.tris_alt.mapFileStrOnStr[tris_str]
        self.printFileStrMapWarning(filename, "filename_map_tris_fill")
        return ""

    def filename_map_tris_pos(self, filename):
        """From a JSON with predefined positioned get the position a triangle fill.

        Depending on the rotation around a 2-fold axis, aka the positional angle, a certain triangle
        fill can connect different heptagon vertices.
        """
        result = re.search(r"-fld_[^.]*\.[0-7]-[^.]*-pos-([0-9]*)\.json", filename)
        if result:
            tris_pos = result.groups()[0]
            return int(tris_pos)
        # try old syntax:
        if not re.search(r"-fld_[^.]*\.[0-7]-([^.]*)\.json", filename):
            self.printFileStrMapWarning(filename, "filename_map_tris_pos")
            raise ValueError(f"Unexpected filename {filename}")
        return 0

    def set_enable_prepos_items(self):
        """Fill list that contains the options for the predefined postions.

        This list also contains the option to enable the sliders. This list is different depending
        on the fact whether the user selected a polyhedron with opposite symmetries or not.
        """
        current_pre_pos = self.pre_pos_enum
        self.pre_pos_gui.Clear()
        pre_pos_still_valid = False
        for pre_pos_str in self.pre_pos_strings:
            pre_pos_id = self.pre_pos_val(pre_pos_str)
            if self.is_prepos_valid(pre_pos_id):
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

    def rm_ctrl_sizer(self):
        """Release all GUI resources related to the control window.

        This function is called e.g. when the user switches to another scene.
        """
        # The 'try' is necessary, since the boxes are destroyed in some OS,
        # while this is necessary for Ubuntu Hardy Heron.
        for box in self.boxes:
            try:
                box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass
        for gui in self.guis:
            gui.Destroy()

    def set_default_size(self, size):
        """Set minimum window size for the control window."""
        self.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        self.SetSize(size)

    def on_pos_angle(self, event):
        """Apply rotation angle around 2-fold axis of heptagon in GUI to polyhedron."""
        self.shape.pos_angle = Geom3D.Deg2Rad * self.pos_angle_gui.GetValue()
        self.status_bar.SetStatusText(self.shape.get_status_str())
        self.update_shape()
        event.Skip()

    def on_dihedral_angle(self, event):
        """Apply new angle between two heptagons sharing an edge in GUI to polyhedron."""
        self.shape.set_dihedral_angle(Geom3D.Deg2Rad * self.dihedral_angle_gui.GetValue())
        self.status_bar.SetStatusText(self.shape.get_status_str())
        self.update_shape()
        event.Skip()

    def on_fold1(self, event):
        """Apply new fold of diagonal no. 1 in GUI of base heptagon to polyhedron."""
        val = self.fold1_gui.GetValue()
        s_val = Geom3D.Deg2Rad * val
        if self.shape.has_reflections:
            self.shape.set_fold1(s_val, s_val)
        else:
            self.shape.set_fold1(s_val)
        self.status_bar.SetStatusText(self.shape.get_status_str())
        self.update_shape()
        event.Skip()

    def on_fold2(self, event):
        """Apply new fold of diagonal no. 2 in GUI of base heptagon to polyhedron."""
        val = self.fold2_gui.GetValue()
        s_val = Geom3D.Deg2Rad * val
        if self.shape.has_reflections:
            self.shape.set_fold2(s_val, s_val)
        else:
            self.shape.set_fold2(s_val)
        self.status_bar.SetStatusText(self.shape.get_status_str())
        self.update_shape()
        event.Skip()

    def on_opp_fold1(self, event):
        """Apply new fold of opposite diagonal no. 1 in GUI of base heptagon to polyhedron."""
        self.shape.set_fold1(opposite_angle=Geom3D.Deg2Rad * self.opp_fold1_gui.GetValue())
        self.status_bar.SetStatusText(self.shape.get_status_str())
        self.update_shape()
        event.Skip()

    def on_opp_fold2(self, event):
        """Apply new fold of opposite diagonal no. 2 in GUI of base heptagon to polyhedron."""
        self.shape.set_fold2(opposite_angle=Geom3D.Deg2Rad * self.opp_fold2_gui.GetValue())
        self.status_bar.SetStatusText(self.shape.get_status_str())
        self.update_shape()
        event.Skip()

    def on_height(self, event):
        """Apply new translation in GUI of base heptagon to polyhedron."""
        self.shape.set_height(
            float(self.max_height - self.height_gui.GetValue()) / self.height_factor
        )
        self.status_bar.SetStatusText(self.shape.get_status_str())
        self.update_shape()
        event.Skip()

    def on_clean_fold_values(self, _):
        """Clean translation and all fold values that can be set through array"""
        self.set_orient_gui.SetValue("")

    def on_set_fold_values(self, event):
        """Apply all fold values and translations from input array in the GUI."""
        str_value = self.set_orient_gui.GetValue()
        if not str_value:
            return
        err_str = "Syntax error in input string"
        try:
            ar = json.loads(str_value)
        except json.JSONDecodeError:
            self.status_bar.SetStatusText(err_str + ": expected a list of floats")
            return
        if not isinstance(ar, list):
            self.status_bar.SetStatusText(err_str + ": expected a list")
            return
        if len(ar) < 4:
            self.status_bar.SetStatusText(err_str + ": list too short")
            return
        if len(ar) > 7:
            self.status_bar.SetStatusText(err_str + ": list too long")
            return
        for f in ar:
            try:
                float(f)
            except ValueError:
                self.status_bar.SetStatusText(err_str + f": expected float, got '{f}'")
                return
        offset = ar[0]
        angle = ar[1]
        fold_1 = ar[2]
        fold_2 = ar[3]
        self.height_gui.SetValue(self.max_height - self.height_factor * offset)
        self.dihedral_angle_gui.SetValue(Geom3D.Rad2Deg * angle)
        self.fold1_gui.SetValue(Geom3D.Rad2Deg * fold_1)
        self.fold2_gui.SetValue(Geom3D.Rad2Deg * fold_2)
        include_refl = len(ar) <= 5
        self.shape.has_reflections = include_refl
        self.refl_gui.SetValue(include_refl)
        if not include_refl:
            self.enable_guis_for_no_refl()
            pos_angle = ar[4]
            opposite_fld1 = ar[5]
            opposite_fld2 = ar[6]
            self.opp_fold1_gui.SetValue(Geom3D.Rad2Deg * opposite_fld1)
            self.opp_fold2_gui.SetValue(Geom3D.Rad2Deg * opposite_fld2)
            self.pos_angle_gui.SetValue(Geom3D.Rad2Deg * pos_angle)
            self.shape.pos_angle = pos_angle
        else:
            self.disable_guis_for_refl()
            self.update_to_refl_pos_angle()
            opposite_fld1 = fold_1
            opposite_fld2 = fold_2
        self.shape.set_dihedral_angle(angle)
        self.shape.set_height(offset)
        self.shape.set_fold1(fold_1, opposite_fld1)
        self.shape.set_fold2(fold_2, opposite_fld2)
        self.status_bar.SetStatusText(self.shape.get_status_str())
        self.update_shape()
        event.Skip()

    def on_apply_symmetry(self, _event):
        """Handle GUI event to apply the final symmetry."""
        self.shape.apply_symmetries = self.apply_sym_gui.IsChecked()
        self.shape.update_shape = True
        self.update_shape()

    def on_add_triangles(self, _event=None):
        """Handle GUI event to show the extra triangles."""
        self.shape.add_extra_faces = self.add_tris_gui.IsChecked()
        self.shape.update_shape = True
        self.update_shape()

    def allign_slide_bars_with_fold_method(self):
        """Enable and disable folding slide bars conform the current fold method"""
        if not self.shape.has_reflections:
            if self.fold_method == FoldMethod.PARALLEL:
                self.opp_fold1_gui.Disable()
                self.opp_fold2_gui.Disable()
            elif self.fold_method in (
                    FoldMethod.W,
                    FoldMethod.SHELL,
                    FoldMethod.MIXED,
                    FoldMethod.G,
            ):
                self.opp_fold1_gui.Enable()
                self.opp_fold2_gui.Enable()
            elif self.fold_method in (FoldMethod.TRAPEZIUM, FoldMethod.TRIANGLE):
                self.opp_fold1_gui.Disable()
                self.opp_fold2_gui.Enable()

    @property
    def refl_pos_angle(self):
        """Return the pos angle for a polyhedron with reflections."""
        return self.shape.refl_pos_angle

    def update_to_refl_pos_angle(self):
        """Update the shape and GUI to reflect the pos angle for a polyhedron with reflections."""
        pos_angle = self.refl_pos_angle
        self.shape.pos_angle = pos_angle
        self.pos_angle_gui.SetValue(Geom3D.Rad2Deg * pos_angle)

    def disable_sliders_no_refl(self):
        """
        Disable all extra sliders that are only valif for a polyhedron without reflections.
        """
        self.opp_fold1_gui.Disable()
        self.opp_fold2_gui.Disable()
        self.pos_angle_gui.Disable()
        # the code below is added to be able to check and uncheck "Has
        # Reflections" in a "undo" kind of way.
        self._saved_angle["opp_fold1"] = self.shape.opposite_fold1
        self._saved_angle["opp_fold2"] = self.shape.opposite_fold2
        self._saved_angle["pos_angle"] = self.shape.pos_angle
        self.shape.set_fold1(opposite_angle=self.shape.fold1)
        self.shape.set_fold2(opposite_angle=self.shape.fold2)
        self.update_to_refl_pos_angle()
        self.opp_fold1_gui.SetValue(self.min_fold_angle)
        self.opp_fold2_gui.SetValue(self.min_fold_angle)

    def enable_sliders_no_refl(self, restore=True):
        """
        Enable all extra sliders that are only valif for a polyhedron without reflections.
        """
        self.allign_slide_bars_with_fold_method()
        self.pos_angle_gui.Enable()
        # the code below is added to be able to check and uncheck "Has
        # Reflections" in a "undo" kind of way.
        if restore:
            opp_fold1 = self._saved_angle["opp_fold1"]
            opp_fold2 = self._saved_angle["opp_fold2"]
            hept_angle = self._saved_angle["pos_angle"]
            self.shape.set_fold1(opposite_angle=opp_fold1)
            self.shape.set_fold2(opposite_angle=opp_fold2)
            self.shape.pos_angle = hept_angle
            self.opp_fold1_gui.SetValue(Geom3D.Rad2Deg * opp_fold1)
            self.opp_fold2_gui.SetValue(Geom3D.Rad2Deg * opp_fold2)
            self.pos_angle_gui.SetValue(Geom3D.Rad2Deg * hept_angle)

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
            self.tris_pos_gui.Disable()
            self.rot_fold_gui.Disable()
            self.shape.rotate_fold = 0
            self.disable_sliders_no_refl()
            self._sym_incl_refl = True
            self.update_fold_selection()

    def enable_guis_for_no_refl(self, restore=True):
        """Enable some GUIs that aren't valid because no reflections are needed.

        See disable_guis_for_refl for more info.
        """
        if self._sym_incl_refl:
            self.update_triangle_fill_options()
            self.tris_pos_gui.Enable()
            self.rot_fold_gui.Enable()
            self.shape.rotate_fold = self._rotate_fold
            self.enable_sliders_no_refl(restore)
            self._sym_incl_refl = False
            self.update_fold_selection()

    def on_refl(self, event=None):
        """
        Update the polyhedron after changing whether the polyhedron has reflections or not.
        """
        self.shape.has_reflections = self.refl_gui.IsChecked()
        self.shape.update_shape = True
        self.show_right_folds()
        self.set_enable_prepos_items()
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
                self.status_bar.SetStatusText(self.shape.get_status_str())
                self.update_shape()

    @property
    def rotate_fold(self):
        """Return the offset for the heptagon rotation.

        For models without reflections a heptagon fold can be rotated to 7 different orientations.
        The rotation fold is an integer between 0 and 7
        """
        return self._rotate_fold

    @rotate_fold.setter
    def rotate_fold(self, rotate_fold):
        """Set the offset for the heptagon rotation.

        For models without reflections a heptagon fold can be rotated to 7 different orientations.
        The rotation fold is an integer between 0 and 7
        """
        self._rotate_fold = int(rotate_fold) % 7
        self.shape.rotate_fold = self._rotate_fold
        self.rot_fold_gui.SetLabel(f"Rotate Fold {self._rotate_fold + 1}/7")
        self.update_shape()

    def on_rotate_fold(self, _):
        """Rotate the current kind of heptagon fold one step clockwise."""
        self.rotate_fold = self._rotate_fold + 1

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
        position = max(position, 0)
        if position >= self.nr_of_positions:
            position = self.nr_of_positions - 1
        self.position = position
        self.tris_alt = self.triangle_alts[self.position]
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
            current_val = self.tris_alt.key[self.tris_fill_gui.GetStringSelection()]
        except KeyError:
            current_val = self.tris_alt.strip_I
        if self.shape.has_reflections:
            def is_valid(c):
                return self.tris_alt.isBaseKey(self.tris_alt.key[c])
            if not self.tris_alt.isBaseKey(current_val):
                if self.tris_setup_refl is None:
                    # TODO: use the first one that is valid
                    current_val = self.tris_alt.strip_I
                else:
                    current_val = self.tris_alt.key[self.tris_setup_refl]
        else:
            def is_valid(c):
                c_key = self.tris_alt.key[c]
                if self.tris_alt.isBaseKey(c_key) or isinstance(c_key, int):
                    return False
                return True

            if not is_valid(self.tris_alt.stringify[current_val]):
                if self.tris_setup_no_refl is None:
                    # TODO: use the first one that is valid
                    current_val = self.tris_alt.strip_I_strip_I
                else:
                    current_val = self.tris_alt.key[self.tris_setup_no_refl]

        self.tris_fill_gui.Clear()
        current_still_valid = False
        for choice in self.tris_alt.choiceList:
            if is_valid(choice):
                self.tris_fill_gui.Append(choice)
                if current_val == self.tris_alt.key[choice]:
                    current_still_valid = True
                last_valid = choice

        if current_still_valid:
            self.tris_fill_gui.SetStringSelection(self.tris_alt.stringify[current_val])
        else:
            try:
                self.tris_fill_gui.SetStringSelection(last_valid)
            except UnboundLocalError:
                # None are valid...
                return
        self.shape.set_edge_alt(self.tris_fill, self.opp_tris_fill)

    @property
    def tris_fill(self):
        """Return the current triangle fill setup.

        If the polyhedron is setup not to have any relfections, then return only for one side
        """
        s = self.tris_fill_gui.GetStringSelection()
        if s == "":
            return None
        t = self.tris_alt.key[s]
        if self.shape.has_reflections:
            return t
        return t[0]

    @property
    def opp_tris_fill(self):
        """Return the current triangle fill setup for the opposite side (of tris_fill).

        If the polyhedron is setup to have relfections, then return the save as for tris_fill).
        """
        t = self.tris_alt.key[self.tris_fill_gui.GetStringSelection()]
        if self.shape.has_reflections:
            return t
        return t[1]

    def nvidea_workaround_0(self):
        """Some work around segmentation fault for NVidia Graphics driver"""
        self.prev_tris_fill = self.shape.edge_alt
        self.prev_opp_tris_fill = self.shape.opposite_edge_alt

    def nvidea_workaround(self):
        """Some work around for NVidia Graphics drivers"""
        restore_my_shape = (
            self.prev_tris_fill == self.tris_alt.twist_strip_I
            and self.prev_opp_tris_fill == self.tris_alt.twist_strip_I
            and self.tris_fill != self.tris_alt.twist_strip_I
            and self.opp_tris_fill != self.tris_alt.twist_strip_I
        )
        change_my_shape = (
            self.tris_fill == self.tris_alt.twist_strip_I
            and self.opp_tris_fill == self.tris_alt.twist_strip_I
        )
        if change_my_shape:
            if self.tris_alt.twist_strip_I not in (self.prev_tris_fill, self.prev_opp_tris_fill):
                logging.info("---------nvidia-seg-fault-work-around-----------")
                self.nvidea_workaround_0()
            self.shape.set_vertices()  # make sure the shape is updated
            shape = FldHeptagonShape(
                self.shape.shapes,
                name=self.shape.name,
            )
            shape.heptagon = self.shape.heptagon
            shape.dihedral_angle = self.shape.dihedral_angle
            shape.pos_angle_min = self.shape.pos_angle_min
            shape.pos_angle_max = self.shape.pos_angle_max
            shape.pos_angle = self.shape.pos_angle
            shape.has_reflections = self.shape.has_reflections
            shape.rotate_fold = self.shape.rotate_fold
            shape.fold1 = self.shape.fold1
            shape.fold2 = self.shape.fold2
            shape.opposite_fold1 = self.shape.opposite_fold1
            shape.opposite_fold2 = self.shape.opposite_fold2
            shape.fold_heptagon = self.shape.fold_heptagon
            shape.height = self.shape.height
            shape.apply_symmetries = self.shape.apply_symmetries
            shape.add_extra_faces = self.shape.add_extra_faces
            shape.all_regular_faces = self.shape.all_regular_faces
            shape.edge_alt = self.tris_fill
            shape.opposite_edge_alt = self.opp_tris_fill
            self.canvas.shape = shape
        elif restore_my_shape:
            self.parent.panel.shape = self.shape

    def update_shape(self):
        """Draw the updated shape on the canvas."""
        self.nvidea_workaround()
        self.canvas.paint()

    def on_triangle_fill(self, event=None):
        """Handle a new triangle fill configuration from the GUI."""
        self.nvidea_workaround_0()
        self.shape.set_edge_alt(self.tris_fill, self.opp_tris_fill)
        if event is not None:
            if self.is_pre_pos():
                self.on_pre_pos(event)
            else:
                if self.shape.has_reflections:
                    self.update_to_refl_pos_angle()
                self.status_bar.SetStatusText(self.shape.get_status_str())
            self.update_shape()

    @property
    def tris_position(self):
        """Get the current triangle position.

        The triangle fill can have the same structure but connecting different vertices. Whether
        this leads to usefull configurations depends on the position angle. For heptagons folds that
        do not require reflection this angle can vary freely and if you do, then a certain setup
        doesn't make much sense anymore, since you are twisting all triangles. Then it is time to
        use the next triangle position.
        """
        # Note these are called "Position <int>"
        selected = self.tris_pos_gui.GetSelection()
        # If nothing selected (after changing from having reflections)
        return max(selected, 0)

    @tris_position.setter
    def tris_position(self, value):
        """Set the current triangle position.

        See the property tris_position for more info.
        """
        self.tris_pos_gui.SetSelection(value)
        self.on_triangle_pos()

    def on_triangle_pos(self, _=None):
        """Handle GUI event for new triangle position.

        See the property tris_position for more info.
        """
        self.set_tri_fill_pos(self.tris_position)
        self.update_triangle_fill_options()
        self.update_shape()

    def show_right_folds(self):
        """Hide and show the fold method conform the current symmetry"""
        valid_names = self.valid_fold_incl_refl[self.shape.has_reflections]
        is_valid = [False for _ in self.fold_method_list]
        for name in valid_names:
            i = self.fold_method_list.index(name)
            is_valid[i] = True
        for i, show in enumerate(is_valid):
            self.fold_method_gui.ShowItem(i, show)
        # It might be that the current fold method isn't valid anymore:
        if not is_valid[self.fold_method_gui.GetSelection()]:
            self.fold_method_gui.SetSelection(is_valid.index(True))
            self.on_fold_method()

    def update_fold_selection(self):
        """Update the GUI to select a fold method conform the symmetry."""
        for i, fold in enumerate(self.fold_method_list):
            if fold.upper() == self.fold_method.name:
                self.fold_method_gui.SetSelection(i)
                break

    def on_fold_method(self, event=None):
        """Handle the selection of a new fold method"""
        self.fold_method = self.fold_method_items[self.fold_method_gui.GetSelection()]
        self.allign_slide_bars_with_fold_method()
        if event is not None:
            if self.is_pre_pos():
                self.on_pre_pos(event)
            else:
                self.status_bar.SetStatusText(self.shape.get_status_str())
            self.update_shape()

    def pre_pos_val(self, key):
        """Map a position string onto the position number.

        A position string shall be the string representing OPEN_FILE, DYN_POS, ONLY_HEPTS, etc.
        """
        if not self._pre_pos_map:
            self._pre_pos_map = {v: k for k, v in self.stringify.items()}
        try:
            return self._pre_pos_map[key]
        except KeyError:
            # Happens when switching from Open File to Only Hepts e.g.
            return -1

    @property
    def pre_pos_enum(self):
        """Return the currently selected position enum, e.g. OPEN_FILE, DYN_POS, ONLY_HEPTS, etc."""
        return self.pre_pos_val(self.pre_pos_gui.GetStringSelection())

    @staticmethod
    def open_pre_pos_file(filename):
        """Open a given file in JSON format with predefined folds and offsets."""
        with open(filename, "r") as fd:
            data = json.load(fd)
        assert isinstance(data, list), f"Expected a JSON holding a list, got {type(data)}"
        for l in data:
            assert len(l) in (
                4,
                5,
                7,
            ), f"Expected elements with a length 4 or 7, got {len(l)}"
            for i in l:
                assert isinstance(i, (float, int)), "Expected a number, got {type(i)}"
        return data

    def log_no_pre_pos_found(self):
        """Log on output and on status bar the no predefined positions were found."""
        s = "Note: no valid pre-defined positions found"
        logging.info(s)
        self.status_bar.SetStatusText(s)

    @property
    def std_pre_pos(self):
        """Return all folds and offsets for predefined heptagon that is used"""
        if self._std_pre_pos:
            return self._std_pre_pos
        pre_pos_id = self.pre_pos_enum
        if pre_pos_id == DYN_POS:
            return []
        if pre_pos_id == OPEN_FILE:
            filename = self.pre_pos_file_name
            if filename is None:
                return []
            self._std_pre_pos = self.open_pre_pos_file(filename)
            return self._std_pre_pos
        # use correct predefined special positions
        if self.shape.has_reflections:
            psp = self.predefReflSpecPos
        else:
            psp = self.predefRotSpecPos
        # Oops not good for performance:
        # TODO only return correct one en add length func
        self._std_pre_pos = [sp["set"] for sp in psp[self.pre_pos_enum]]
        return self._std_pre_pos

    def on_first(self, _=None):
        """From a loaded JSON file with predefined folds choose the first option."""
        self.special_pos_idx = 0
        self.on_pre_pos()

    def on_last(self, _=None):
        """From a loaded JSON file with predefined folds choose the last option."""
        self.special_pos_idx = -1
        self.on_pre_pos()

    def on_prev(self, _=None):
        """From a loaded JSON file with predefined folds choose the previous option."""
        if self.std_pre_pos != []:
            if self.special_pos_idx > 0:
                self.special_pos_idx -= 1
            elif self.special_pos_idx == -1:
                self.special_pos_idx = len(self.std_pre_pos) - 2
            # else pre_pos_id == 0 : first one selected don't scroll around
            self.on_pre_pos()
        else:
            self.log_no_pre_pos_found()

    def on_next(self, _=None):
        """From a loaded JSON file with predefined folds choose the next option."""
        if self.std_pre_pos != []:
            try:
                max_i = len(self.std_pre_pos) - 1
                if self.special_pos_idx >= 0:
                    if self.special_pos_idx < max_i - 1:
                        self.special_pos_idx += 1
                    else:
                        self.special_pos_idx = -1  # select last
            except KeyError:
                pass
            self.on_pre_pos()
        else:
            self.log_no_pre_pos_found()

    def has_only_hepts(self):
        """Return whether the current model solely consists of heptagons.

        The current model is supposed to be one that is predefined by the program.
        """
        return self.pre_pos_enum == ONLY_HEPTS

    def has_only_o3_triangles(self):
        """Return whether the current model has extra triangles on a 3-fold axis only

        The current model is supposed to be one that is predefined by the program.
        """
        return self.pre_pos_enum == ONLY_XTRA_O3S

    def choose_file(self):
        """Open a dialog to choose a JSON file with predefined values to load."""
        filename = None
        dlg = wx.FileDialog(
            self, "New: Choose a file", self.rDir, "", "*.json", wx.FD_OPEN
        )
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        dlg.Destroy()
        return filename

    def on_open_file(self, _):
        """Handle opening of a JSON file with predefined folds and positions."""
        filename = self.choose_file()
        if filename is None:
            return
        logging.info("Opening file: %s", filename)
        self.pre_pos_file_name = filename
        self.fold_method_gui.SetStringSelection(
            # TODO: put these values in the JSON file
            self.filename_map_fold_method(self.pre_pos_file_name)
        )
        self.on_fold_method()
        self.rotate_fold = self.filename_map_fold_pos_str(self.pre_pos_file_name)
        # Note: Reflections need to be set before triangle fill, otherwise the
        # right triangle fills are not available
        has_reflections = self.filename_map_has_reflections(self.pre_pos_file_name)
        self.refl_gui.SetValue(has_reflections)
        self.on_refl()
        # not needed: self.shape.update_shape = True
        self.update_triangle_fill_options()
        self.tris_fill_gui.SetStringSelection(self.filename_map_tris_fill(self.pre_pos_file_name))
        self.on_triangle_fill()
        self.tris_position = self.filename_map_tris_pos(self.pre_pos_file_name)
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

        if self.special_pos_idx >= len(setting):
            self.special_pos_idx = len(setting) - 1
        offset = setting[self.special_pos_idx][0]
        angle = setting[self.special_pos_idx][1]
        fold_1 = setting[self.special_pos_idx][2]
        fold_2 = setting[self.special_pos_idx][3]
        v_str = "[offset, dihedral_angle, fold_1, fold_2"
        dbg_str = f"  [{offset:.12f}, {angle:.12f}, {fold_1:.12f}, {fold_2:.12f}"
        if len(setting[self.special_pos_idx]) > 4:
            pos_angle = setting[self.special_pos_idx][4]
        else:
            pos_angle = 0
        if len(setting[self.special_pos_idx]) > 5:
            opposite_fld1 = setting[self.special_pos_idx][5]
            opposite_fld2 = setting[self.special_pos_idx][6]
            v_str += ", positional_angle, opposite_fold_1, opposite_fold_2] ="
            dbg_str += f", {pos_angle:.12f}, {opposite_fld1:.12f}, {opposite_fld2:.12f}]"
        else:
            opposite_fld1 = fold_1
            opposite_fld2 = fold_2
            v_str += "] ="
            dbg_str += "]"
        logging.info(v_str)
        logging.info(dbg_str)
        # Ensure self.special_pos_idx in range:

        no_of_pos = len(setting)
        max_i = no_of_pos - 1
        if self.special_pos_idx > max_i:
            self.special_pos_idx = max_i
        # keep -1 (last) so switching triangle alternative will keep
        # last selection.
        elif self.special_pos_idx < -1:
            self.special_pos_idx = max_i - 1
        self.shape.set_dihedral_angle(angle)
        self.shape.set_height(offset)
        self.shape.set_fold1(fold_1, opposite_fld1)
        self.shape.set_fold2(fold_2, opposite_fld2)
        self.shape.pos_angle = pos_angle
        # For the user: start counting with '1' instead of '0'
        if self.special_pos_idx == -1:
            pos_no = no_of_pos  # last position
        else:
            pos_no = self.special_pos_idx + 1
        # set nr of possible positions
        self.number_text.SetLabel(f"{pos_no}/{no_of_pos}")
        self.status_bar.SetStatusText(self.shape.get_status_str())
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
        # remove the "From File" from the pull down list as soon as it is
        # deselected
        if event is not None and self.pre_pos_enum != OPEN_FILE:
            open_file = self.stringify[OPEN_FILE]
            n = self.pre_pos_gui.FindString(open_file)
            if n >= 0:
                # deleting will reset the selection, so save and reselect:
                selection = self.pre_pos_gui.GetSelection()
                self.pre_pos_gui.Delete(self.pre_pos_gui.FindString(open_file))
                self.pre_pos_gui.SetSelection(selection)
        if self.pre_pos_enum == DYN_POS:
            if event is not None:
                self.pre_pos_file_name = None
            if self.restore_tris:
                self.restore_tris = False
                self.shape.add_extra_faces = self.add_tris_gui.IsChecked()
                self.shape.update_shape = True
            if self.restore_o3_tris:
                self.restore_o3_tris = False
                self.shape.all_regular_faces = False
                self.shape.update_shape = True
            self.number_text.SetLabel("---")
        elif self.pre_pos_enum != OPEN_FILE:
            # this block is run for predefined spec pos only:
            if self.has_only_hepts():
                self.shape.add_extra_faces = False
                self.restore_tris = True
            elif self.restore_tris:
                self.restore_tris = False
                self.shape.add_extra_faces = self.add_tris_gui.IsChecked()
            if self.has_only_o3_triangles():
                self.shape.all_regular_faces = True
                self.restore_o3_tris = True
            elif self.restore_o3_tris:
                self.restore_o3_tris = False
                self.shape.all_regular_faces = False

            # get fold, tris alt
            sps = self.special_pos_setup
            self.fold_method_gui.SetStringSelection(sps["7fold"].name.capitalize())
            self.tris_fill_gui.SetStringSelection(self.tris_alt.stringify[sps["tris"]])
            try:
                self.tris_position = sps["tris-pos"]
            except KeyError:
                self.tris_position = 0
            try:
                rotate_fold = sps["fold-rot"]
            except KeyError:
                rotate_fold = 0
            self.rotate_fold = rotate_fold

            self.on_fold_method()
            self.on_triangle_fill()

            for gui in [
                    self.dihedral_angle_gui,
                    self.pos_angle_gui,
                    self.height_gui,
                    self.fold1_gui,
                    self.fold2_gui,
                    self.opp_fold1_gui,
                    self.opp_fold2_gui,
            ]:
                gui.SetValue(0)
                gui.Disable()
            if not self.shape.has_reflections:
                self.enable_guis_for_no_refl()
            else:
                self.disable_guis_for_refl()
        if self.pre_pos_enum != DYN_POS:
            if event is not None:
                self.reset_std_pre_pos()
            setting = self.std_pre_pos
            if setting == []:
                self.log_no_pre_pos_found()
                return
            # Note if the setting array uses a none symmetric setting, then the
            # shape will not be symmetric. This is not supposed to be handled
            # here: don't overdo it!
            self.update_shape_settings(setting)
        # for OPEN_FILE it is important that updateShapeSettings is done before
        # updating the sliders...
        if self.pre_pos_enum in (DYN_POS, OPEN_FILE):
            for gui in [
                    self.dihedral_angle_gui,
                    self.pos_angle_gui,
                    self.height_gui,
                    self.fold1_gui,
                    self.fold2_gui,
                    self.opp_fold1_gui,
                    self.opp_fold2_gui,
            ]:
                gui.Enable()
            s = self.shape
            self.dihedral_angle_gui.SetValue(Geom3D.Rad2Deg * s.dihedral_angle)
            # Showing triangles is the most general way of showing
            self.add_tris_gui.SetValue(wx.CHK_CHECKED)
            self.on_add_triangles()
            self.pos_angle_gui.SetValue(Geom3D.Rad2Deg * s.pos_angle)
            val1 = Geom3D.Rad2Deg * s.fold1
            val2 = Geom3D.Rad2Deg * s.fold2
            self.fold1_gui.SetValue(val1)
            self.fold2_gui.SetValue(val2)
            val1 = Geom3D.Rad2Deg * s.opposite_fold1
            val2 = Geom3D.Rad2Deg * s.opposite_fold2
            self.opp_fold1_gui.SetValue(val1)
            self.opp_fold2_gui.SetValue(val2)
            if not self.shape.has_reflections:
                self.enable_guis_for_no_refl(restore=False)
            self.height_gui.SetValue(self.max_height - self.height_factor * s.height)
            self.update_triangle_fill_options()
        self.update_shape()


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
