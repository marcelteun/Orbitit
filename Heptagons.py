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

    def fold(this, a, b, keepV0 = True, fold = FoldMethod.parallel):
	if fold == FoldMethod.parallel:
	    this.foldParallel(a, b, keepV0)
	elif fold == FoldMethod.trapezium:
	    this.foldTrapezium(a, b, keepV0)
	elif fold == FoldMethod.w:
	    this.foldW(a, b, keepV0)
	elif fold == FoldMethod.triangle:
	    this.foldTriangle(a, b, keepV0)
	elif fold == FoldMethod.star:
	    this.foldStar(a, b, keepV0)
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

    def foldTrapezium(this, a, b, keepV0 = True):
        """
        Fold around 4 diagonals in the shape of a trapezium (trapezoid)

        The fold angle a refers the the axis V1-V6 and
        The fold angle b refers the the axes V1-V3 and V6-V4 and
        If keepV0 = True then the triangle V0, V1, V6 is kept invariant during
        folding, otherwise the edge V3-V4 is kept invariant.
	It assumes that the heptagon is in the original position.
        """
        #
        #             0
        #
        #      6 ----------- 1    axis a
        #      .             .
        #       \           /
        #        \ axes  b /
        #    5   |         |   2
        #        \        /
        #         "       "
        #         4       3
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
            V1V3 = (this.VsOrg[1] + V3)/2
            V1V3axis = Vec([V3 - this.VsOrg[1]])
            r = Rot(axis = V1V3axis, angle = b)
            V2 = V1V3 + r * (V2_ - V1V3)
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
            r = Rot(axis = V1V3axis, angle = b)
            V2 = V1V3 + r * (this.VsOrg[2] - V1V3)
            this.Vs = [
                    V0,
                    this.VsOrg[1],
                    V2,
                    this.VsOrg[3],
                    this.VsOrg[4],
                    Vec([-V2[0], V2[1], V2[2]]),
                    this.VsOrg[6]
                ]

    def foldW(this, a, b, keepV0 = True):
        """
        Fold around 4 diagonals in the shape of the character 'W'.

        the fold angle a refers the the axes V0-V3 and V0-V4.
        The fold angle b refers the the axes V1-V3 and V6-V4 and
        The vertex V0 is kept invariant during folding
        The keepV0 variable is ignored here (it is provided to be consistent
	with the other fold functions.)
        """
        #
        #              0
        #              ^
        #       6     | |     1
        #       .    /   \    .
        # axis b \  |     |  / axis b
        #         " |     | "
        #     5   |/       \|   2
        #         V axes  a V
        #         "         "
        #         4         3
        #
        #
	Rot0_3 = Rot(axis = this.VsOrg[3] - this.VsOrg[0], angle = a)
	V1 = Rot0_3 * this.VsOrg[1]
	V2 = Rot0_3 * this.VsOrg[2]
	Rot1_3 = Rot(axis = this.VsOrg[3] - V1, angle = b)
	V2 = Rot1_3 * (V2 - V1) + V1
	this.Vs = [
		this.VsOrg[0],
		V1,
		V2,
		this.VsOrg[3],
		this.VsOrg[4],
		Vec([-V2[0], V2[1], V2[2]]),
		Vec([-V1[0], V1[1], V1[2]]),
	    ]
        this.Fs = [[1, 3, 2], [1, 0, 3], [0, 4, 3], [0, 6, 4], [6, 5, 4]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
		1, 3, 3, 0, 0, 4, 4, 6
	    ]

    def foldTriangle(this, a, b, keepV0 = True):
        """
        Fold around 3 triangular diagonals from V0.

        The fold angle a refers the the axes V0-V2 and V0-V5 and
        the fold angle b refers the the axis V2-V5.
        If keepV0 = True then the triangle V0, V1, V6 is kept invariant during
        folding, otherwise the trapezium V2-V3-V4-V5 is kept invariant.
        """
        #
        #             0
        #            _^_
        #      6   _/   \_   1
        #        _/       \_
        #      _/  axes  b  \_
        #     /               \
        #    5 --------------- 2  axis a
        #
        #
        #         4       3
        #
        #
        this.Fs = [[0, 2, 1], [0, 5, 2], [0, 6, 5], [2, 5, 4, 3]]
        this.Es = [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0,
		0, 2, 2, 5, 5, 0
	    ]
	Rot0_2 = Rot(axis = this.VsOrg[2] - this.VsOrg[0], angle = b)
	V1 = Rot0_2 * this.VsOrg[1]
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
		    Vec([-V1[0], V1[1], V1[2]]),
		]
	else:
	    Rot2_5 = Rot(axis = this.VsOrg[2] - this.VsOrg[5], angle = a)
	    V0 = Rot2_5 * (this.VsOrg[0] - V2) + V2
	    V1 = Rot2_5 * (V1 - V2) + V2
	    this.Vs = [
		    V0,
		    V1,
		    this.VsOrg[2],
		    this.VsOrg[3],
		    this.VsOrg[4],
		    this.VsOrg[5],
		    Vec([-V1[0], V1[1], V1[2]]),
		]

    def foldStar(this, a, b, keepV0 = True):
        """
        Fold around the 4 diagonals from V0.

        The fold angle a refers the the axes V0-V2 and V0-V5 and
        the fold angle b refers the the axes V0-V3 and V0-V4.
        The keepV0 variable is ignored here (it is provided to be consistent
	with the other fold functions.)
        """
        #
        #               0
        #              .^.
        #        6   _/| |\_   1
        #          _/ /   \ \_
        # axis b _/  |     |  \_ axis b
        #       /    |     |    \
        #      5    /       \    2
        #          | axes  a |
        #          "         "
        #          4         3
        #
        #
	Rot0_3 = Rot(axis = this.VsOrg[3] - this.VsOrg[0], angle = a)
	V1 = Rot0_3 * this.VsOrg[1]
	V2 = Rot0_3 * this.VsOrg[2]
	Rot0_2 = Rot(axis = V2 - this.VsOrg[0], angle = b)
	V1 = Rot0_2 * V1
	this.Vs = [
		this.VsOrg[0],
		V1,
		V2,
		this.VsOrg[3],
		this.VsOrg[4],
		Vec([-V2[0], V2[1], V2[2]]),
		Vec([-V1[0], V1[1], V1[2]]),
	    ]
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

class FldHeptagonShape(Geom3D.IsometricShape):
    def __init__(this, isoms, colors = None, name = 'Folded Regular Heptagons'):
        Geom3D.IsometricShape.__init__(this,
            Vs = [], Fs = [],
            directIsometries = isoms,
            unfoldOrbit = True,
            name = name,
        )
        this.heptagon = RegularHeptagon()
	if colors == None:
	    this.theColors     = [
		    rgb.oliveDrab[:],
		    rgb.brown[:],
		    rgb.yellow[:],
		    rgb.cyan[:]
		]
	else:
	    this.theColors = None
        this.angle = 1.2
        this.posAngle = 0
        this.fold1 = 0.0
        this.fold2 = 0.0
	this.foldHeptagon = foldMethod.parallel
        this.height = 2.3
        this.applySymmetry = True
        this.addTriangles = True
        this.useCulling = False
        this.setV()

    def glDraw(this):
        if this.updateShape: this.setV()
        Geom3D.IsometricShape.glDraw(this)

    def setEdgeAlternative(this, alt):
        this.edgeAlternative = alt
        this.updateShape = True

    def setFoldMethod(this, method):
	this.foldHeptagon = method
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
        this.height = height
        this.updateShape = True

    def edgeColor(this):
        glColor(0.5, 0.5, 0.5)

    def vertColor(this):
        glColor(0.7, 0.5, 0.5)

    def getStatusStr(this):
        return 'Angle = %01.2f rad, fold1 = %01.2f rad, fold2 = %01.2f rad, T = %02.2f' % (
                this.angle,
                this.fold1,
                this.fold2,
                this.height
            )

    def setV(this):
        #print this.name, "setV"
	this.heptagon.fold(this.fold1, this.fold2,
		keepV0 = False, fold = this.foldHeptagon)
	#print 'norm V0-V1: ', (this.heptagon.Vs[1]-this.heptagon.Vs[0]).squareNorm()
	#print 'norm V1-V2: ', (this.heptagon.Vs[1]-this.heptagon.Vs[2]).squareNorm()
	#print 'norm V2-V3: ', (this.heptagon.Vs[3]-this.heptagon.Vs[2]).squareNorm()
	#print 'norm V3-V4: ', (this.heptagon.Vs[3]-this.heptagon.Vs[4]).squareNorm()
        this.heptagon.translate(H * GeomTypes.uy)
        # The angle has to be adjusted for historical reasons...
        this.heptagon.rotate(-GeomTypes.ux, this.angle)
        this.heptagon.translate(this.height*GeomTypes.uz)
	if this.posAngle != 0:
	    this.heptagon.rotate(GeomTypes.uz, this.posAngle)
        Vs = this.heptagon.Vs[:]
        Es = []
        Fs = []
        Fs.extend(this.heptagon.Fs) # use extend to copy the list to Fs
        Es.extend(this.heptagon.Es) # use extend to copy the list to Fs
        colIds = [0 for f in Fs]
        this.setBaseVertexProperties(Vs = Vs)
        this.setBaseEdgeProperties(Es = Es)
        this.setBaseFaceProperties(Fs = Fs, colors = (this.theColors, colIds))
        this.showBaseOnly = not this.applySymmetry
        this.updateShape = False

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


