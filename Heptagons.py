#!/usr/bin/python
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
import rgb
import Geom3D
from OpenGL.GL import *

import GeomTypes
from GeomTypes import Rot3      as Rot
from GeomTypes import HalfTurn3 as HalfTurn
from GeomTypes import Vec3      as Vec

V3 = math.sqrt(3)

h         = math.sin(  math.pi / 7)
RhoH      = math.sin(2*math.pi / 7)
SigmaH    = math.sin(3*math.pi / 7)
Rho       = RhoH / h
Sigma     = SigmaH / h
R         = 0.5 / h
H         = (1 + Sigma + Rho)*h

only_hepts	= -1
dyn_pos		= -2
only_xtra_o3s   = -3
all_eq_tris     = -4
no_o3_tris	= -5

alt_bit = 8
loose_bit = 16
class TrisAlt:
    # Note nrs should be different from below
    strip_I            = 128
    strip_II           = 129
    star               = 130
    strip_1_loose      = strip_I  | loose_bit
    star_1_loose       = star     | loose_bit
    alt_strip_I        = strip_I              | alt_bit
    alt_strip_II       = strip_II             | alt_bit
    alt_strip_1_loose  = strip_I  | loose_bit | alt_bit

    @property
    def key(this):
	return {
	    Stringify[this.strip_I]:           this.strip_I,
	    Stringify[this.strip_II]:          this.strip_II,
	    Stringify[this.star]:              this.star,
	    Stringify[this.strip_1_loose]:     this.strip_1_loose,
	    Stringify[this.star_1_loose]:      this.star_1_loose,
	    Stringify[this.alt_strip_I]:       this.alt_strip_I,
	    Stringify[this.alt_strip_II]:      this.alt_strip_II,
	    Stringify[this.alt_strip_1_loose]: this.alt_strip_1_loose
	}

trisAlt = TrisAlt()

Stringify = {
    trisAlt.strip_1_loose:	'Strip, 1 Loose',
    trisAlt.strip_I:		'Strip I',
    trisAlt.strip_II:		'Strip II',
    trisAlt.star:		'Shell',
    trisAlt.star_1_loose:	'Shell, 1 Loose',
    trisAlt.alt_strip_I:	'Alternative Strip I',
    trisAlt.alt_strip_II:	'Alternative Strip II',
    trisAlt.alt_strip_1_loose:	'Alternative Strip, 1 loose',
}

class FoldMethod:
    parallel  = 0
    trapezium = 1
    w         = 2
    triangle  = 3
    star      = 4

    def get(this, str):
	for k,v in FoldName.iteritems():
	    if v == str:
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
						fold = FoldMethod.parallel
    ):
	if fold == FoldMethod.parallel:
	    this.foldParallel(a0, b0, keepV0)
	elif fold == FoldMethod.trapezium:
	    this.foldTrapezium(a0, b0, b1, keepV0)
	elif fold == FoldMethod.w:
	    this.foldW(a0, b0, a1, b1, keepV0)
	elif fold == FoldMethod.triangle:
	    this.foldTriangle(a0, b0, b1, keepV0)
	elif fold == FoldMethod.star:
	    this.foldStar(a0, b0, a1, b1, keepV0)
	else:
	    raise TypeError, 'Unknown fold'

    def foldParallel(this, a, b, keepV0 = True):
        """
        Fold around the 2 parallel diagonals V1-V6 and V2-V5.

        The fold angle a refers the the axis V1-V6 and
        the fold angle b refers the the axis V2-V5.
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

    def foldTrapezium(this, a, b0, b1 = None, keepV0 = True):
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

    def foldTriangle(this, a, b0, b1, keepV0 = True):
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

    def foldW(this, a0, b0, a1, b1, keepV0 = True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a0 refers the the axes V0-V3,
        the fold angle a1 refers the the axes V0-V4,
        The fold angle b0 refers the the axes V1-V3,
        The fold angle b1 refers the the axes V6-V4 and
        The vertex V0 is kept invariant during folding
        The keepV0 variable is ignored here (it is provided to be consistent
	with the other fold functions.)
        """
        #
        #               0
        #               ^
        #        6     | |     1
        #        .    /   \    .
        # axis b0 \  |     |  / axis b1
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

    def foldStar(this, a0, b0, a1, b1, keepV0 = True):
        """
        Fold around the 4 diagonals from V0.

        The fold angle a refers the the axes V0-V2 and V0-V5 and
        the fold angle b0 refers the the axes V0-V3 and V0-V4.
        The keepV0 variable is ignored here (it is provided to be consistent
	with the other fold functions.)
        """
        #
        #                0
        #               .^.
        #         6   _/| |\_   1
        #          _/ /   \ \_
        # axis b0 _/  |     |  \_ axis b1
        #        /    |     |    \
        #       5    /       \    2
        #   axis a0 |         | axis a1
        #           "         "
        #           4         3
        #
        #
	Rot0_3 = Rot(axis = this.VsOrg[3] - this.VsOrg[0], angle = a0)
	V0 = this.VsOrg[0]
	V1_ = Rot0_3 * this.VsOrg[1]
	V2 = Rot0_3 * this.VsOrg[2]
	Rot0_2 = Rot(axis = V2 - V0, angle = b0)
	V1 = Rot0_2 * V1_
	if (Geom3D.eq(a0, a1)):
	    V5 = Vec([-V2[0], V2[1], V2[2]])
	    if (Geom3D.eq(b0, b1)):
		V6 = Vec([-V1[0], V1[1], V1[2]])
	    else:
		V6 = Vec([-V1_[0], V1_[1], V1_[2]])
		Rot5_0 = Rot(axis = V0 - this.VsOrg[5], angle = b1)
		V6 = Rot5_0 * (V6 - V0) + V0
	else:
	    Rot4_0 = Rot(axis = V0 - this.VsOrg[4], angle = a1)
	    V6 = Rot4_0 * this.VsOrg[6]
	    V5 = Rot4_0 * this.VsOrg[5]
	    Rot5_0 = Rot(axis = V0 - this.VsOrg[5], angle = b1)
	    V6 = Rot5_0 * (V6 - V0) + V0
	this.Vs = [V0, V1, V2, this.VsOrg[3], this.VsOrg[4], V5, V6]
        this.Fs = [[0, 2, 1], [0, 3, 2], [0, 4, 3], [0, 5, 4], [0, 6, 5]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
		0, 2, 0, 3, 0, 4, 0, 5
	    ]

#    3 don't fit in one vertex. highest is hexagon...  Dooh...
#    def transform_2_3inV0(this):
#        """
#        Transform the {7} to fit 3 in vertex 0.
#
#        Transform the regular heptagon in such a way that:
#         o has V0 in the origin
#         o and a y-z slope that is suited for fitting 3 {7}s in V0, by just
#           rotating the resulting {7} around the z-axis.
#        """
#        # Angle a refers to the slope of a {7} to fit three in a vertex:
#        cosa = Rho/(2*V3*h)
#        print cosa
#        print (math.acos(cosa))
#        sina = math.sin(math.acos(cosa))
#        for i in range(len(this.Vs)):
#            this.Vs[i] = Vec([
#                    this.Vs[i][0],
#                    cosa*this.Vs[i][1] - sina*this.Vs[i][2],
#                    sina*this.Vs[i][1] + cosa*this.Vs[i][2]
#                ])

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
        print 'Kite2Hept: warning f == 0'
        return
    if w == 0:
        print 'Kite2Hept: warning w == 0'
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
        print 'kite2Hept: negative sqrt requested'
        return

    nom   = (f + g)
    denom = qkpr + V(root)

    if denom == 0:
        print 'kite2Hept: error denom == 0'
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
        this.posAngle = this.posAngleMin
        this.inclReflections = True
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

    def glDraw(this):
        if this.updateShape: this.setV()
        Geom3D.CompoundShape.glDraw(this)

    def setEdgeAlternative(this, alt = None, oppositeAlt = None):
        if alt != None:
	    this.edgeAlternative = alt
        if oppositeAlt != None:
	    this.oppEdgeAlternative = oppositeAlt
        this.updateShape = True

    def setFoldMethod(this, method):
	this.foldHeptagon = method
        this.updateShape = True

    def setDihedralAngle(this, angle):
        this.dihedralAngle = angle
        this.updateShape = True

    def setPosAngle(this, angle):
        this.posAngle = angle
        this.updateShape = True

    def setFold1(this, angle = None, oppositeAngle = None):
        if angle != None:
	    this.fold1 = angle
        if oppositeAngle != None:
	    this.oppFold1 = oppositeAngle
        this.updateShape = True

    def setFold2(this, angle = None, oppositeAngle = None):
        if angle != None:
	    this.fold2 = angle
        if oppositeAngle != None:
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

    def posHeptagon(this):
	this.heptagon.fold(this.fold1, this.fold2, this.oppFold1, this.oppFold2,
		keepV0 = False, fold = this.foldHeptagon)
	#print 'norm V0-V1: ', (this.heptagon.Vs[1]-this.heptagon.Vs[0]).squareNorm()
	#print 'norm V1-V2: ', (this.heptagon.Vs[1]-this.heptagon.Vs[2]).squareNorm()
	#print 'norm V2-V3: ', (this.heptagon.Vs[3]-this.heptagon.Vs[2]).squareNorm()
	#print 'norm V3-V4: ', (this.heptagon.Vs[3]-this.heptagon.Vs[4]).squareNorm()
        this.heptagon.translate(H * GeomTypes.uy)
        # Note: the rotation angle != the dihedral angle
	this.heptagon.rotate(-GeomTypes.ux, GeomTypes.qTurn - this.dihedralAngle)
        this.heptagon.translate(this.height*GeomTypes.uz)
	if this.posAngle != 0:
	    this.heptagon.rotate(-GeomTypes.uz, this.posAngle)

    def setV(this):
        #print this.name, "setV"
	this.posHeptagon()
        Vs = this.heptagon.Vs[:]
        Es = this.heptagon.Fs
        Fs = this.heptagon.Es
        colIds = [0 for f in Fs]
        this.setVertexProperties(Vs = Vs)
        this.setEdgeProperties(Es = Es)
        this.setFaceProperties(Fs = Fs, colors = (this.theColors, colIds))
        this.updateShape = False

class FldHeptagonCtrlWin(wx.Frame):
    def __init__(this,
	    shape, size, canvas,
	    maxHeight, 
	    prePosLst,
	    stringify,
	    *args, **kwargs
    ):
	"""Create a control window for the scene that folds heptagons

	shape: the Geom3D shape object that is shown
	size: default size of the frame
	canvas: wx canvas to be used
	maxHeight: max translation height to be used for the heptagon
	prePosLst: string list that expresses which special positions can be
	           found, e.g. where all holes disappear.
	stringify: hash table that maps enums on strings.
	*args: standard wx Frame *args
	**kwargs: standard wx Frame **kwargs
	"""
        # TODO assert (type(shape) == type(RegHeptagonShape()))
        wx.Frame.__init__(this, *args, **kwargs)
        this.shape = shape
        this.canvas = canvas
	this.maxHeight = maxHeight
	this.prePosLst = prePosLst
	this.stringify = stringify
        this.panel = wx.Panel(this, -1)
        this.statusBar = this.CreateStatusBar()
	this.foldMethod = foldMethod.triangle
	this.restoreTris = False
	this.restoreO3s = False
	this.shape.foldHeptagon = this.foldMethod
        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
	this.initTrisEnabled()

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
        this.specPos = {}

    def createControlsSizer(this):
        this.heightF = 40 # slider step factor, or: 1 / slider step

        this.Guis = []
	this.choiceListTrisFill = [
	    Stringify[trisAlt.strip_I],
	    Stringify[trisAlt.strip_II],
	    Stringify[trisAlt.star],
	]
	nr_of = len(this.choiceListTrisFill)
	this.choiceListItemsTrisFill = {}
	for i in range(nr_of):
	    this.choiceListItemsTrisFill[this.choiceListTrisFill[i]] = i

        # static adjustments
        this.trisFillGui = wx.RadioBox(this.panel,
                label = 'Triangle Fill Alternative',
                style = wx.RA_VERTICAL,
		choices = this.choiceListTrisFill
            )
        this.Guis.append(this.trisFillGui)
        this.trisFillGui.Bind(wx.EVT_RADIOBOX, this.onTriangleFill)

        this.trisAltGui = wx.CheckBox(this.panel, label = 'Alternative O3')
        this.Guis.append(this.trisAltGui)
        this.trisAltGui.Bind(wx.EVT_CHECKBOX, this.onTriangleFill)

        this.looseTriGui = wx.CheckBox(this.panel, label = 'One Loose Triangle')
        this.Guis.append(this.looseTriGui)
        this.looseTriGui.Bind(wx.EVT_CHECKBOX, this.onTriangleFill)

        this.oppTrisFillGui = wx.RadioBox(this.panel,
                label = 'Neighbour Fill Alternative',
                style = wx.RA_VERTICAL,
		choices = this.choiceListTrisFill
            )
        this.Guis.append(this.oppTrisFillGui)
        this.oppTrisFillGui.Bind(wx.EVT_RADIOBOX, this.onTriangleFill)

        this.oppTrisAltGui = wx.CheckBox(this.panel, label = 'Alternative O3')
        this.Guis.append(this.oppTrisAltGui)
        this.oppTrisAltGui.Bind(wx.EVT_CHECKBOX, this.onTriangleFill)

        this.shape.setEdgeAlternative(
		this.trisFill & ~alt_bit,
		this.oppTrisFill & ~alt_bit
	    )

        this.reflGui = wx.CheckBox(this.panel, label = 'Reflections Required')
        this.Guis.append(this.reflGui)
        this.reflGui.SetValue(this.shape.inclReflections)
        this.reflGui.Bind(wx.EVT_CHECKBOX, this.onRefl)

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
                choices = this.prePosLst
            )
	# Don't hardcode which index is dyn_pos, I might reorder the item list
	# one time, and will probably forget to update the default selection..
	for i in range(len(this.prePosLst)):
	    if (this.prePosLst[i] == this.stringify[dyn_pos]):
		this.prePosGui.SetStringSelection(this.stringify[dyn_pos])
		break
        this.Guis.append(this.prePosGui)
        this.prePosGui.Bind(wx.EVT_CHOICE, this.onPrePos)
        #wxPoint& pos = wxDefaultPosition, const wxSize& size = wxDefaultSize, int n = 0, const wxString choices[] = NULL, long style = 0, const wxValidator& validator = wxDefaultValidator, const wxString& name = "listBox")

        this.firstButton = wx.Button(this.panel, label = 'First')
        this.nextButton  = wx.Button(this.panel, label = 'Next')
        this.nrTxt       = wx.Button(this.panel, label = '0/0',  style=wx.NO_BORDER)
        this.prevButton  = wx.Button(this.panel, label = 'Prev')
        this.lastButton  = wx.Button(this.panel, label = 'Last')
        this.Guis.append(this.firstButton)
        this.Guis.append(this.nextButton)
        this.Guis.append(this.nrTxt)
        this.Guis.append(this.prevButton)
        this.Guis.append(this.lastButton)
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

        # Sizers
        this.Boxes = []

        # sizer with view settings
        this.Boxes.append(wx.StaticBox(this.panel, label = 'View Settings'))
        settingsSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        settingsSizer.Add(this.applySymGui, 0, wx.EXPAND)
        settingsSizer.Add(this.addTrisGui, 0, wx.EXPAND)
        settingsSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

	# The sizers holding the special positions
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Special Positions'))
        posSizerSubV = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        posSizerSubH = wx.BoxSizer(wx.HORIZONTAL)
        posSizerSubH.Add(this.firstButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.prevButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.nrTxt, 1, wx.EXPAND)
        posSizerSubH.Add(this.nextButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.lastButton, 1, wx.EXPAND)
        posSizerSubV.Add(this.prePosGui, 0, wx.EXPAND)
        posSizerSubV.Add(posSizerSubH, 0, wx.EXPAND)
        posSizerSubV.Add(wx.BoxSizer(), 1, wx.EXPAND)
        prePosSizerH = wx.BoxSizer(wx.HORIZONTAL)
        prePosSizerH.Add(posSizerSubV, 0, wx.EXPAND)
        prePosSizerH.Add(wx.BoxSizer(), 1, wx.EXPAND)

	# Alterntives of filling with triangles
        fillSizer = wx.BoxSizer(wx.VERTICAL)
        fillSizer.Add(this.trisFillGui, 0, wx.EXPAND)
        fillSizer.Add(this.trisAltGui, 0, wx.EXPAND)
        fillSizer.Add(this.looseTriGui, 0, wx.EXPAND)
        fillSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)
        # Alternatives only if no reflections
        oppFillSizer = wx.BoxSizer(wx.VERTICAL)
        oppFillSizer.Add(this.oppTrisFillGui, 0, wx.EXPAND)
        oppFillSizer.Add(this.oppTrisAltGui, 0, wx.EXPAND)
        oppFillSizer.Add(this.reflGui, 0, wx.EXPAND)
        oppFillSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        statSizer = wx.BoxSizer(wx.HORIZONTAL)
        statSizer.Add(this.foldMethodGui, 0, wx.EXPAND)
        statSizer.Add(fillSizer, 0, wx.EXPAND)
        statSizer.Add(oppFillSizer, 0, wx.EXPAND)
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

	# MAIN sizer
        mainVSizer = wx.BoxSizer(wx.VERTICAL)
        mainVSizer.Add(statSizer, 0, wx.EXPAND)
        mainVSizer.Add(prePosSizerH, 0, wx.EXPAND)
        mainVSizer.Add(posSizerH, 0, wx.EXPAND)
        mainVSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(mainVSizer, 6, wx.EXPAND)

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

    def onPosAngle(this, event):
	#print this.GetSize()
        this.shape.setPosAngle(Geom3D.Deg2Rad * this.posAngleGui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onDihedralAngle(this, event):
	#print this.GetSize()
        this.shape.setDihedralAngle(
	    Geom3D.Deg2Rad * this.dihedralAngleGui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onFold1(this, event):
	val = this.fold1Gui.GetValue()
        s_val = Geom3D.Deg2Rad * val
	if this.shape.inclReflections:
	    this.shape.setFold1(s_val, s_val)
	else:
	    this.shape.setFold1(s_val)
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onFold2(this, event):
	val = this.fold2Gui.GetValue()
        s_val = Geom3D.Deg2Rad * val
	if this.shape.inclReflections:
	    this.shape.setFold2(s_val, s_val)
	else:
	    this.shape.setFold2(s_val)
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onFold1Opp(this, event):
        this.shape.setFold1(
	    oppositeAngle = Geom3D.Deg2Rad * this.fold1OppGui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onFold2Opp(this, event):
        this.shape.setFold2(
	    oppositeAngle = Geom3D.Deg2Rad * this.fold2OppGui.GetValue())
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
        this.shape.addXtraFs = this.addTrisGui.IsChecked()
        this.shape.updateShape = True
        this.canvas.paint()

    def initTrisEnabled(this):
	this.isTrisFillEnabled = {}
	this.isOppTrisFillEnabled = {}
	for k in Stringify.iterkeys():
	    this.isTrisFillEnabled[k] = True
	    this.isOppTrisFillEnabled[k] = True

    def setEnableTrisFill(this, alt, enable = True, opposite = False):
	if not opposite:
	    this.isTrisFillEnabled[alt] = enable
	else:
	    this.isOppTrisFillEnabled[alt] = enable

    def correctTrisFillSettings(this, fillGui, altGui):
        if this.isPrePos():
	    # check if we only have alt or if there are no alt fill settings:
	    no_alt = True
	    all_alt = True
	    for k, v in this.isTrisFillEnabled.iteritems():
		if k & alt_bit:
		    if v:
			no_alt = False
			if not all_alt: break
		else:
		    if v:
			all_alt = False
			if not no_alt: break
	else:
	    no_alt = False
	    all_alt = False
	# and act on abov:
	# there is not alternative o3 for the star variant
	if (
	    trisAlt.key[fillGui.GetStringSelection()] == trisAlt.star or
	    no_alt or all_alt
	):
	    if all_alt:
		altGui.SetValue(True)
	    elif no_alt:
		altGui.SetValue(False)
	    altGui.Disable()
	else:
	    altGui.Enable()
	# It is essential this one comes after
	fillGui.ShowItem(
	    this.choiceListItemsTrisFill[Stringify[trisAlt.star]],
	    not altGui.IsChecked()
	)

    def correctLooseTrisFillSettings(this):
	# As long as a strip_II variant is used
	# or if all loose variants are explicitely disabled
	# you cannot use a loose triangle
	selTrisAlt = trisAlt.key[this.trisFillGui.GetStringSelection()]
	selOppTrisAlt = trisAlt.key[this.oppTrisFillGui.GetStringSelection()]
        if this.isPrePos():
	    no_loose = True
	    all_loose = True
	    for k, v in this.isTrisFillEnabled.iteritems():
		if k & loose_bit:
		    if v:
			no_loose = False
			if not all_loose: break
		else:
		    if v:
			all_loose = False
			if not no_loose: break
	else:
	    no_loose = False
	    all_loose = False
	if (
	    selTrisAlt == trisAlt.strip_II or
	    selOppTrisAlt == trisAlt.strip_II or
	    no_loose or all_loose
	):
	    if all_loose:
		this.looseTriGui.SetValue(True)
	    elif no_loose:
		this.looseTriGui.SetValue(False)
	    this.looseTriGui.Disable()
	else:
	    this.looseTriGui.Enable()
	# As long as the loose variant is chosen you cannot select strip II
	# It is essential this one comes after
	looseTriangleSelected = this.looseTriGui.IsChecked()
	this.oppTrisFillGui.ShowItem(
	    this.choiceListItemsTrisFill[Stringify[trisAlt.strip_II]],
	    not looseTriangleSelected
	)
	this.trisFillGui.ShowItem(
	    this.choiceListItemsTrisFill[Stringify[trisAlt.strip_II]],
	    not looseTriangleSelected
	)
	if looseTriangleSelected:
	    # 1 loose and strip II don't combine: select smth else.
	    oppTrisFill = this.oppTrisFill
	    reset = False
	    if oppTrisFill == trisAlt.strip_II or oppTrisFill == trisAlt.alt_strip_II:
		for k, v in this.isOppTrisFillEnabled.iteritems():
		    if v and k != trisAlt.strip_II:
			oppTrisFill = k
			reset = True
			break
	    trisFill = this.trisFill
	    if trisFill == trisAlt.strip_II or trisFill == trisAlt.alt_strip_II:
		for k, v in this.isTrisFillEnabled.iteritems():
		    if v and k != trisAlt.strip_II:
			trisFill = k
			reset = True
			break
	    if reset:
		this.setTrisFill(trisFill, oppTrisFill)
	this.resetTrisFill(opp = False)
	this.resetTrisFill(opp = True)

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
	this.shape.setPosAngle(0)
	this.fold1OppGui.SetValue(this.minFoldAngle)
	this.fold2OppGui.SetValue(this.minFoldAngle)
	this.posAngleGui.SetValue(0)

    def enableSlidersNoRefl(this):
	this.allignFoldSlideBarsWithFoldMethod()
	this.posAngleGui.Enable()
	# the code below is added to be able to check and uncheck "Has
	# Reflections" in a "undo" kind of way.
	this.shape.setFold1(oppositeAngle = this.__sav_oppFld1)
	this.shape.setFold2(oppositeAngle = this.__sav_oppFld2)
	this.shape.setPosAngle(this.__sav_posAngle)
	this.fold1OppGui.SetValue(Geom3D.Rad2Deg * this.__sav_oppFld1)
	this.fold2OppGui.SetValue(Geom3D.Rad2Deg * this.__sav_oppFld2)
	this.posAngleGui.SetValue(Geom3D.Rad2Deg * this.__sav_posAngle)

    def resetTrisFill(this, opp = False):
	try:
	    if opp:
		del this.__oppTrisFill
	    else:
		del this.__trisFill
	except AttributeError:
	    pass

    def disableGuisNoRefl(this):
	if this.__guisNoReflEnabled:
	    this.__sav_oppTrisFill = this.oppTrisFill
	    this.setTrisFill(this.trisFill, this.trisFill)
	    this.resetTrisFill(opp = True)
	    this.shape.setEdgeAlternative(this.trisFill, this.oppTrisFill)
	    this.oppTrisFillGui.Disable()
	    this.oppTrisAltGui.Disable()
	    this.disableSlidersNoRefl()
	    this.__guisNoReflEnabled = False

    def enableGuisNoRefl(this):
	if not this.__guisNoReflEnabled:
	    this.oppTrisFillGui.Enable()
	    this.setTrisFill(this.trisFill, this.__sav_oppTrisFill)
	    this.resetTrisFill(opp = True)
	    this.shape.setEdgeAlternative(this.trisFill, this.oppTrisFill)
	    this.correctLooseTrisFillSettings()
	    this.correctTrisFillSettings(this.oppTrisFillGui, this.oppTrisAltGui)
	    this.enableSlidersNoRefl()
	    this.__guisNoReflEnabled = True

    def disableTrisFillGuis(this):
	this.addTrisGui.Disable()
	this.looseTriGui.Disable()
	this.trisFillGui.Disable()
	this.trisAltGui.Disable()
	this.oppTrisFillGui.Disable()
	this.oppTrisAltGui.Disable()

    def enableTrisFillGuis(this):
	this.addTrisGui.Enable()
	this.looseTriGui.Enable()
	this.trisFillGui.Enable()
	this.trisAltGui.Enable()
	if not this.shape.inclReflections:
	    this.oppTrisFillGui.Enable()
	    this.oppTrisAltGui.Enable()

    def onRefl(this, event):
        this.shape.inclReflections = this.reflGui.IsChecked()
        if this.shape.inclReflections:
		this.disableGuisNoRefl()
		this.shape.updateShape = True
		this.canvas.paint()
	else:
		this.enableGuisNoRefl()
		this.shape.updateShape = True
		this.canvas.paint()
        if this.isPrePos():
            this.onPrePos()
	else:
	    this.statusBar.SetStatusText(this.shape.getStatusStr())

    def isPrePos(this):
	# TODO: move to offspring
        return this.prePosGui.GetStringSelection() != this.prePosLst[-1]

    def setTrisFill(this, tris, oppTris):
	if (tris & loose_bit == loose_bit):
	    if oppTris & loose_bit != loose_bit:
		print "Warning: forcing loose opposite triangle fill"
	    this.looseTriGui.SetValue(True)
	else:
	    if oppTris & loose_bit == loose_bit:
		print "Warning: removing loose opposite triangle fill"
	    this.looseTriGui.SetValue(False)
	tris    = tris    & ~loose_bit
	oppTris = oppTris & ~loose_bit
	if tris & alt_bit:
	    #this.trisAltGui.Enable()
	    this.trisAltGui.SetValue(True)
	if tris & alt_bit:
	    #this.oppTrisAltGui.Enable()
	    this.oppTrisAltGui.SetValue(True)
	tris    = tris    & ~alt_bit
	oppTris = oppTris & ~alt_bit
	tris_index = this.choiceListItemsTrisFill[Stringify[tris]]
	#this.trisFillGui.ShowItem(tris_index)
	this.trisFillGui.SetSelection(tris_index)
	tris_index = this.choiceListItemsTrisFill[Stringify[oppTris]]
	#this.oppTrisFillGui.ShowItem(tris_index)
	this.oppTrisFillGui.SetSelection(tris_index)

    @property
    def trisFill(this):
	try:
	    return this.__trisFill
	except AttributeError:
	    this.__trisFill = trisAlt.key[this.trisFillGui.GetStringSelection()]
	    if this.trisAltGui.IsChecked():
		this.__trisFill = this.__trisFill | alt_bit
	    if this.looseTriGui.IsChecked():
		assert this.__trisFill != trisAlt.strip_II
		this.__trisFill = this.__trisFill | loose_bit

	    return this.__trisFill

    @property
    def oppTrisFill(this):
	try:
	    return this.__oppTrisFill
	except AttributeError:
	    if this.shape.inclReflections:
		oppTrisFill = this.trisFill
	    else:
		oppTrisFill = trisAlt.key[
				    this.oppTrisFillGui.GetStringSelection()]
		if this.oppTrisAltGui.IsChecked():
		    oppTrisFill = oppTrisFill | alt_bit
		if this.looseTriGui.IsChecked():
		    assert oppTrisFill != trisAlt.strip_II
		    oppTrisFill = oppTrisFill | loose_bit
	    this.__oppTrisFill = oppTrisFill
	    return oppTrisFill

    def onTriangleFill(this, event):
	this.correctLooseTrisFillSettings()
	this.correctTrisFillSettings(this.trisFillGui, this.trisAltGui)
	if not this.shape.inclReflections:
	    this.correctTrisFillSettings(this.oppTrisFillGui, this.oppTrisAltGui)
	# rm the saved value, it is not valid anymore:
	this.resetTrisFill(opp = False)
	this.resetTrisFill(opp = True)
        this.shape.setEdgeAlternative(this.trisFill, this.oppTrisFill)
        if this.isPrePos():
            this.onPrePos()
        else:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()

    def onFoldMethod(this, event):
        this.foldMethod = this.foldMethodListItems[
		this.foldMethodGui.GetSelection()
	    ]
	this.shape.setFoldMethod(this.foldMethod)
	this.allignFoldSlideBarsWithFoldMethod()
        if this.isPrePos():
            this.onPrePos()
        else:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()

    def onFirst(this, event = None):
        this.specPosIndex = 0
        this.onPrePos()

    def onLast(this, event = None):
        this.specPosIndex = -1
        this.onPrePos()

    def getPrePos(this):
        prePosStr = this.prePosGui.GetStringSelection()
	for k,v in this.stringify.iteritems():
	    if v == prePosStr:
		return k
	return dyn_pos

    def onPrev(this, event = None):
        prePosId = this.getPrePos()
        if prePosId != dyn_pos:
            if this.specPosIndex > 0:
                this.specPosIndex -= 1
	    elif this.specPosIndex == -1:
                this.specPosIndex = len(this.getPossibleSpecPosSettings()) - 2
	    # else prePosId == 0 : first one selected don't scroll around
            this.onPrePos()

    def onNext(this, event = None):
        prePosId = this.getPrePos()
        if prePosId != dyn_pos:
	    try:
		maxI = len(this.getPossibleSpecPosSettings()) - 1
		if this.specPosIndex >= 0:
		    if this.specPosIndex < maxI - 1:
			this.specPosIndex += 1
		    else:
		        this.specPosIndex = -1 # select last
	    except KeyError:
		pass
	    this.onPrePos()

    def getPossibleSpecPosSettings(this):
        prePosId = this.getPrePos()
        if prePosId != dyn_pos:
	    if this.shape.inclReflections:
		trisF = this.trisFill
	    else:
		trisF = (this.trisFill, this.oppTrisFill)
	    return this.specPos[this.shape.inclReflections][prePosId][
							this.foldMethod][trisF]
	else:
	    return []

    tNone = 1.0
    aNone = 0.0
    fld1None = 0.0
    fld2None = 0.0
    def onPrePos(this, event = None):
	#print "onPrePos"
        sel = this.getPrePos()
	# if only_hepts:
	# 1. don't show triangles
	# 2. disable triangle strip.
	if (sel == only_hepts):
	    this.shape.addXtraFs = False
	    this.disableTrisFillGuis()
	    # TODO rm: (only for the current spec prepos
	    this.disableGuisNoRefl()
	    this.restoreTris = True
	elif (this.restoreTris):
	    this.restoreTris = False
	    this.enableTrisFillGuis()
	    this.shape.addXtraFs = this.addTrisGui.IsChecked()
	    # needed for sel == dyn_pos
	    this.shape.updateShape = True
	if (sel == only_xtra_o3s):
	    this.shape.onlyRegFs = True
	    this.restoreO3s = True
	elif (this.restoreO3s):
	    this.restoreO3s = False
	    this.shape.onlyRegFs = False
	    # needed for sel == dyn_pos
	    this.shape.updateShape = True
        aVal = this.aNone
        tVal = this.tNone
	c = this.shape
        if sel == dyn_pos:
	    # currently for all special positions the polyhedron has reflections
	    # TODO add other special positions: choose by static check box.
	    #      then rm line below
	    this.dihedralAngleGui.Enable()
	    this.fold1Gui.Enable()
	    this.fold2Gui.Enable()
	    this.heightGui.Enable()
	    this.dihedralAngleGui.SetValue(Geom3D.Rad2Deg * c.dihedralAngle)
	    this.posAngleGui.SetValue(Geom3D.Rad2Deg * c.posAngle)
	    val1 = Geom3D.Rad2Deg * c.fold1
	    val2 = Geom3D.Rad2Deg * c.fold2
	    this.fold1Gui.SetValue(val1)
	    this.fold2Gui.SetValue(val2)
	    if not this.shape.inclReflections:
		this.enableGuisNoRefl()
	    this.heightGui.SetValue(
		this.maxHeight - this.heightF*c.height)
	    # enable all folding and triangle alternatives:
	    for i in range(len(this.foldMethodList)):
		this.foldMethodGui.ShowItem(i, True)
	    this.initTrisEnabled()
	else:
            oppFld1 = fld1 = this.fld1None
            oppFld2 = fld2 = this.fld2None
	    posVal = this.aNone
	    nrPos = 0
	    specPos = this.specPos[this.shape.inclReflections]

	    # Disable / enable appropriate folding methods.
	    for i in range(len(this.foldMethodList)):
		method = this.foldMethodListItems[i]
		this.foldMethodGui.ShowItem(i, method in specPos[sel])
		# leave up to the user to decide which folding method to choose
		# in case the selected one was disabled.

	    # Disable / enable appropriate triangle alternatives.
	    # if the selected folding has valid solutions anyway
#CONTINUE HERE: why is shell still available....
	    if this.foldMethod in specPos[sel]:
		if this.shape.inclReflections:
		    for k in Stringify.iterkeys():
			enable = k in specPos[sel][this.foldMethod]
			this.setEnableTrisFill(k, enable)
		else:
		    print '--------------------------'
		    for k in Stringify.iterkeys():
			enable = [False, False]
			for setPair in specPos[sel][this.foldMethod]:
			    if k == setPair[0]:
				enable[0] = True
			    if k == setPair[1]:
				enable[1] = True
			    if enable[0] == True and enable[1] == True:
				break
			print 'DBG setEnable:', Stringify[k], ':', enable[0], enable[1]
			this.setEnableTrisFill(k, enable[0], enable[1])
	    if (sel != only_hepts):
		this.correctLooseTrisFillSettings()
		this.correctTrisFillSettings(this.trisFillGui, this.trisAltGui)
		if not this.shape.inclReflections:
		    this.correctTrisFillSettings(this.oppTrisFillGui,
							    this.oppTrisAltGui)
	    try:
		setting = this.getPossibleSpecPosSettings()
		if setting != []:
		    tVal = setting[this.specPosIndex][0]
		    aVal = setting[this.specPosIndex][1]
		    fld1 = setting[this.specPosIndex][2]
		    fld2 = setting[this.specPosIndex][3]
		    print 'DBG tVal', tVal
		    print 'DBG aVal', aVal
		    print 'DBG fld1', fld1
		    print 'DBG fld2', fld2
		    if not this.shape.inclReflections:
			posVal = setting[this.specPosIndex][4]
			oppFld1 = setting[this.specPosIndex][5]
			oppFld2 = setting[this.specPosIndex][6]
			print 'DBG posVal', posVal
			print 'DBG oppFld1', oppFld1
			print 'DBG oppFld2', oppFld2
		    else:
			posVal = 0
			oppFld1 = fld1
			oppFld2 = fld2
		# Ensure this.specPosIndex in range:
		nrPos = len(setting)
		maxI = nrPos - 1
		if (this.specPosIndex > maxI):
		    this.specPosIndex = maxI
		# keep -1 (last) so switching triangle alternative will keep
		# last selection.
		elif (this.specPosIndex < -1):
		    this.specPosIndex = maxI - 1
	    except KeyError:
		print 'dbg key eror', Stringify[this.trisFill], Stringify[this.oppTrisFill]
	        pass

            c.setDihedralAngle(aVal)
            c.setHeight(tVal)
            c.setFold1(fld1, oppFld1)
            c.setFold2(fld2, oppFld2)
            c.setPosAngle(posVal)
	    this.dihedralAngleGui.SetValue(0)
	    this.fold1Gui.SetValue(0)
	    this.fold2Gui.SetValue(0)
	    this.heightGui.SetValue(0)
	    this.dihedralAngleGui.Disable()
	    this.fold1Gui.Disable()
	    this.fold2Gui.Disable()
	    this.heightGui.Disable()
	    if not this.shape.inclReflections:
		this.enableGuisNoRefl()
	    else:
		this.disableGuisNoRefl()
            if ( tVal == this.tNone and aVal == this.aNone and
		    fld1 == this.fld1None and fld2 == this.fld2None
	    ):
		txt = 'No solutions found'
                this.statusBar.SetStatusText(txt)
	    elif this.isntSpecialPos(sel):
		this.statusBar.SetStatusText('Doesnot mean anything special for this triangle alternative')
	    else:
		# For the user: start counting with '1' instead of '0'
		if this.specPosIndex == -1:
		    nr = nrPos # last position
		else:
		    nr = this.specPosIndex + 1
		# set nr of possible positions
		this.nrTxt.SetLabel('%d/%d' % (nr, nrPos))
		this.statusBar.SetStatusText(c.getStatusStr())
		#this.shape.printTrisAngles()
        this.canvas.paint()

    def isntSpecialPos(this, sel):
	"""Check whether this selection is special for this triangle alternative

	Needs to be implemented by the offspring, return true on default
	"""
	return True

class EqlHeptagonShape(Geom3D.IsometricShape):
    def __init__(this,
        directIsometries = [GeomTypes.E],
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
        this.h     = h
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
        if addFaces != None:
            this.setFaceProperties(drawFaces = addFaces)
        if showKite != None:
            this.showKite = showKite
        if showHepta != None:
            this.showHepta = showHepta
        if showXtra != None:
            this.showXtra = showXtra
        if heptPosAlt != None:
            this.heptPosAlt = heptPosAlt
        if triangleAlt != None:
            this.triangleAlt = triangleAlt
            this.updateV = True
        if addXtraEdge != None:
            this.addXtraEdge = addXtraEdge
        if cullingOn != None:
            if cullingOn:
                glEnable(GL_CULL_FACE)
            else:
                glDisable(GL_CULL_FACE)
        if edgeR != None:
            this.setEdgeProperties(radius = edgeR, drawEdges = True)
        if vertexR != None:
            this.setVertexProperties(radius = vertexR)
        if opaqueness != None:
            # TODO...
            this.opaqueness = opaqueness
        if (
            showKite != None  # not so efficient perhaps, but works..
            or
            showHepta != None  # not so efficient perhaps, but works..
            or
            showXtra != None  # not so efficient perhaps, but works..
            or
            heptPosAlt != None
            or
            addXtraEdge != None
        ):
            this.setV()


    def glInit(this):
        Geom3D.IsometricShape.glInit(this)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def getStatusStr(this):
        if this.errorStr == '':
          floatFmt = '%02.2f'
          fmtStr   = 'H = %s, Angle = %s degrees' % (floatFmt, floatFmt)
          str      = fmtStr % (this.h, this.angle)
          return str
        else:
          return this.errorStr

class EqlHeptagonCtrlWin(wx.Frame):
    def __init__(this, shape, canvas, size, *args, **kwargs):
        assert (type(shape) == type(EqlHeptagonShape()))
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
    def setDefaultSize(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)


