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
# $Log$
#


import pygsl._numobj as numx
from pygsl  import multiroots, errno
import pygsl
import copy
import threading
import gc

import Heptagons
import GeomTypes

import string
import time
import random

H         = numx.sin(  numx.pi / 7)
RhoH      = numx.sin(2*numx.pi / 7)
SigmaH    = numx.sin(3*numx.pi / 7)
Rho       = RhoH / H
Sigma     = SigmaH / H

eqFloatMargin = 1.0e-12

V2 = numx.sqrt(2.)
hV2 = V2/2
V3 = numx.sqrt(3.)
hV3 = V3/2
tV3 = V3/3
V2dV3 = V2/V3

def eq(a, b, precision = eqFloatMargin):
    """
    Check if 2 floats 'a' and 'b' are close enough to be called equal.

    a: a floating point number.
    b: a floating point number.
    margin: if |a - b| < margin then the floats will be considered equal and
            True is returned.
    """
    return abs(a - b) < precision

# since GeomTypes.quat doesn't work well with multiroots...
def quatRot(axis, angle):
    assert not (GeomTypes.eq(axis[0], 0) and
	    GeomTypes.eq(axis[1], 0) and
	    GeomTypes.eq(axis[2], 0)
	), 'Axis cannot be (0, 0, 0) %s ' % str(axis)
    norm = numx.sqrt(axis[0]*axis[0] + axis[1]*axis[1] + axis[2]*axis[2])
    sa = numx.sin(angle/2)
    ca = numx.cos(angle/2)
    q0 = [sa*a/norm for a in axis]
    q1 = [-q for q in q0]
    q0.insert(0, ca)
    q1.insert(0, ca)
    return (q0, q1)

def quatMult(v, w):
    return [
	v[0]*w[0] - v[1]*w[1] - v[2] * w[2] - v[3] * w[3],
	v[0]*w[1] + v[1]*w[0] + v[2] * w[3] - v[3] * w[2],
	v[0]*w[2] - v[1]*w[3] + v[2] * w[0] + v[3] * w[1],
	v[0]*w[3] + v[1]*w[2] - v[2] * w[1] + v[3] * w[0]
    ]

def rotate(v, q):
    w = [0, v[0], v[1], v[2]]
    r = quatMult(q[0], w)
    r = quatMult(r, q[1])
    return GeomTypes.Vec(r[1:])

class Symmetry:
	# not efficient for comparing, but not a bottleneck
	A4xI = "A4xI"
	A4   = "A4"
	S4xI = "S4xI"

class Param:
    tri_fill = 0
    opp_fill = 1
    edge_len = 2
    h_fold = 3
    refl_max_angle = 4
    n_7_turn = 5

loose_bit = 4
alt_bit = 8
rot_bit  = 16
twist_bit  = 32
class TriangleAlt:
    stripI           = 0
    strip1loose      = 0 | loose_bit
    alt_stripI       = 0             | alt_bit
    alt_strip1loose  = 0 | loose_bit | alt_bit
    stripII          = 1
    alt_stripII      = 1             | alt_bit
    star             = 2
    star1loose       = 2 | loose_bit
    rot_strip1loose  = 0 | loose_bit           | rot_bit
    arot_strip1loose = 0 | loose_bit | alt_bit | rot_bit
    rot_star1loose   = 2 | loose_bit           | rot_bit
    arot_star1loose  = 2 | loose_bit | alt_bit | rot_bit
    twisted          = 					   twist_bit
    def __iter__(t):
	return iter([
	    t.stripI,
	    t.strip1loose,
	    t.alt_stripI,
	    t.alt_strip1loose,
	    t.stripII,
	    t.alt_stripII,
	    t.star,
	    t.star1loose,
	    t.rot_strip1loose,
	    t.arot_strip1loose,
	    t.rot_star1loose,
	    t.arot_star1loose,
	    t.twisted
	])

Stringify = {
    TriangleAlt.strip1loose     : 'strip 1 loose',
    TriangleAlt.stripI          : 'strip I',
    TriangleAlt.stripII         : 'strip II',
    TriangleAlt.star            : 'shell',
    TriangleAlt.star1loose      : 'shell 1 loose',
    TriangleAlt.alt_strip1loose : 'alt strip 1 loose',
    TriangleAlt.alt_stripI      : 'alt strip I',
    TriangleAlt.alt_stripII     : 'alt strip II',
    TriangleAlt.rot_strip1loose : 'rot strip 1 loose',
    TriangleAlt.arot_strip1loose: 'alt rot strip 1 loose',
    TriangleAlt.rot_star1loose  : 'rot shell 1 loose',
    TriangleAlt.arot_star1loose : 'alt rot shell 1 loose',
    TriangleAlt.twisted		: 'twisted',
}

class Fold:
    parallel  = 0
    trapezium = 1
    w         = 2
    triangle  = 3
    star      = 4

    def __init__(this, f = 0):
	this.set(f)

    def set(this, f):
	assert (f >= this.parallel and f <= this.star)
	this.fold = f

    def __str__(this):
	if (this.fold == this.parallel):
	    return 'parallel'
	elif (this.fold == this.trapezium):
	    return 'trapezium'
	elif (this.fold == this.w):
	    return 'w'
	elif (this.fold == this.triangle):
	    return 'triangle'
	elif (this.fold == this.star):
	    return 'shell'
	else:
	    return None

fold = Fold()

def GetBaseHeptagon(T, alpha, beta0, beta1, gamma0, gamma1, delta, fold_type):
    """Returns the positioned base heptagon indepent on symmetry

    Returns the tuple of 7 vertices.
    T: translation of the heptagon
    alpha: half of the dihedral angle
    beta0: first fold left
    beta1: first fold right
    gamma0: second fold left
    gamma0: second fold right
    delta: rotation around the z-axis
    fold_type: expresses how the heptagon is folded, ie over which diagonals
    """
    # before rotating, with heptagon centre = origin
    R = 1.0 / (2*H)       # radius
    x0, y0, z0 = (H + SigmaH + RhoH, 0.0,     0.)
    x1, y1, z1 = (    SigmaH + RhoH, Rho/2,   0.)
    x2, y2, z2 = (             RhoH, Sigma/2, 0.)
    x3, y3, z3 = (              0.0, 1.0/2,   0.)
    x4, y4, z4 = (               x3, -y3,     z3)
    x5, y5, z5 = (               x2, -y2,     z2)
    x6, y6, z6 = (               x1, -y1,     z1)

    Tx = R - x0   # translate in X to centre on origin
    cosa  = numx.cos(alpha)
    sina  = numx.sin(alpha)
    cosb0 = numx.cos(beta0)
    sinb0 = numx.sin(beta0)
    cosg0 = numx.cos(gamma0)
    sing0 = numx.sin(gamma0)
    cosb1 = numx.cos(beta1)
    sinb1 = numx.sin(beta1)
    cosg1 = numx.cos(gamma1)
    sing1 = numx.sin(gamma1)
    if (fold_type == Fold.parallel):
	# this code I wrote first only for the parallel case.
	# I didn't remove the code since it so much faster then the newer code.
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
	x0__ = cosg0 * (H) + SigmaH + RhoH
	z0__ = sing0 * (H)

	x0   = cosb0 * (x0__ - RhoH) - sinb0 * (z0__       ) + RhoH
	z0   = cosb0 * (z0__       ) + sinb0 * (x0__ - RhoH)

	x1   = cosb0 * (SigmaH) + RhoH
	z1   = sinb0 * (SigmaH)

	x6, y6, z6 = x1, -y1, z1

    elif (fold_type == Fold.triangle):
	#
	#             0
	#            _^_
	#      1   _/   \_   6
	#        _/       \_
	#      _/  axes  b  \_
	#     /               \
	#    2 --------------- 5  axis a
	#
	#
	#         3       4
	#                                ^ X
	#                                |
	#                                |
	#                       Y <------+
	#
	# rotate gamma around b
	# rotate beta  around a
	#
	# ROTATE V1 around axis b: angle gamma
	# ------------------------------------
	# refer to V1 as if centre i origon:
	# rotate around axis b as if centre -> V1 is x-axis:
	x = (R - H) + cosg0 * H
	z =           sing0 * H
	# now correct for V1 not on x-axis: rotate d around z-axis
	# with d: angle of heptagon centre to V1 with x-as
	# and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
	cosd = (x1 + Tx) / R
	sind = y1 / R
	x1, y1, z1 = (cosd * x - Tx, sind * x, z)
	# ROTATE V0 and V1 around axis a: angle beta
	# ------------------------------------
	x = H + SigmaH
	x0, y0, z0 = (RhoH + cosb0 * x, y0, sinb0 * x)
	x = x1 - RhoH
	x1, y1, z1 = (RhoH + cosb0 * x - sinb0 * z1, y1, sinb0 * x + cosb0 * z1)

	x6, y6, z6 = x1, -y1, z1
	x5, y5, z5 = x2, -y2, z2

    elif (fold_type == Fold.star):
	#
	#               0
	#              .^.
	#        1   _/| |\_   6
	#          _/ /   \ \_
	# axis g0_/  |     |  \_ axis g1
	#       /    |a   a|    \
	#      2    / x   x \    5
	#          |  i   i  |
	#          "  s   s  "
	#          3         4
	#             b   b
	#             0   1              ^ X
	#                                |
	#                                |
	#                       Y <------+
	#
	# rotate gamma around b
	# rotate beta  around a
	#
	# ROTATE V1 around axis g
	# ------------------------------------
	# refer to V1 as if centre is origon:
	# rotate around axis g as if centre -> V1 is x-axis:
	x = (R - H) + cosg0 * H
	z =           sing0 * H
	# now correct for V1 not on x-axis: rotate d around z-axis
	# with d: angle of heptagon centre to V1 with x-as
	cosd = (x1 + Tx) / R
	sind = RhoH # = sin(2pi/7)
	x1, y1, z1 = (cosd * x, sind * x, z)

	# use similar calc for different angle and x6, y6, z6 = x1, -y1, z1
	x = (R - H) + cosg1 * H
	z =           sing1 * H
	x6, y6, z6 = (cosd * x, sind * x, z)

	# ROTATE V1 and V2 around axis b
	# ------------------------------------
	# correction for V5 not on -x: rotate d around z-axis
	# with d: angle of heptagon centre to V2 with -x-as
	cosd = -(x2 + Tx) / R
	sind = SigmaH # = sin(3pi/7)
	# refer to V2 as if centre in origon and as if V5 in -x:
	x2, y2, z2 = (x0 - R, 0.5, 0.0)
	d0_3 = x2 - RhoH
	# rotate around axis b:
	# TODO: above: rm x2, y2 assignment, mv y2 assignment down.
	x2, z2 = (d0_3 + cosb0 * RhoH, sinb0 * RhoH)
	# correct for V5 not on -x: rotate d around z-axis
	# and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
	x2, y2 = (cosd * x2 - sind * y2 - Tx, sind * x2 + cosd * y2)
	# Similarly for V1:
	# for V1 rotate V5 into -x: * (cosd, -sind)
	x1, y1 = (cosd * x1 + sind * y1, -sind * x1 + cosd * y1)
	# rotate around axis b:
	dx = x1 - d0_3
	x1, z1 = (d0_3 + cosb0 * dx - sinb0 * z1, sinb0 * dx + cosb0 * z1)
	# correct for V5 not on -x: rotate d around z-axis
	# and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
	x1, y1 = (cosd * x1 - sind * y1 - Tx, sind * x1 + cosd * y1)

	# use similar calc for different angle for
	# x5, y5, z5 = x2, -y2, z2
	# x6, y6, z6 = x1, -y1, z1
	y5 = 0.5
	x5, z5 = (d0_3 + cosb1 * RhoH, sinb1 * RhoH)
	x5, y5 = (cosd * x5 - sind * y5 - Tx, sind * x5 + cosd * y5)
	x6, y6 = (cosd * x6 + sind * y6, -sind * x6 + cosd * y6)
	dx = x6 - d0_3
	x6, z6 = (d0_3 + cosb1 * dx - sinb1 * z6, sinb1 * dx + cosb1 * z6)
	x6, y6 = (cosd * x6 - sind * y6 - Tx, sind * x6 + cosd * y6)
	# x5, y5, z5 = x2, -y2, z2  and  x6, y6, z6 = x1, -y1, z1
	y5, y6 = -y5, -y6

    elif (fold_type == Fold.trapezium):
	#
	#               0
	#
	#        1 ----------- 6    axis b0
	#        .             .
	# axis g0 \           / axis g1
	#          \         /
	#      2   |         |   5
	#          \        /
	#           "       "
	#           3       4
	#
	#                                ^ X
	#                                |
	#                                |
	#                       Y <------+
	#
	# rotate gamma around b
	# rotate beta  around a
	#
	# ROTATE V2 around axis g0: angle gamma
	# ------------------------------------
	# refer to V2 as if centre is origon:
	# rotate around axis g0 as if centre -> V2 is x-axis:
	x = (R - H) + cosg0 * H
	z =           sing0 * H
	# now correct for V2 not on x-axis: rotate d around z-axis
	# with d: angle of heptagon centre to V2 with x-as
	# and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
	cosd = (x2 + Tx) / R
	#TODO: change into SigmaH and retest
	sind = y2 / R
	x2, y2, z2 = (cosd * x - Tx, sind * x, z)

	# use similar calc for different angle for x5, -y5, z5 = x2, y2, z2
	x = (R - H) + cosg1 * H
	z =           sing1 * H
	x5, y5, z5 = (cosd * x - Tx, -sind * x, z)

	# ROTATE V0 around axis b0: angle beta
	# ------------------------------------
	# refer to V0 as if centre is origon:
	#   - rotate around axis b0
	# Then translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
	x0 = (R - H) + cosb0 * H - Tx
	z0 =           sinb0 * H

    elif (fold_type == Fold.w):
	#
	#               0
	#              .^.
	#        1     | |     6
	#        .    /   \    .
	# axis g0 \  |     |  / axis g1
	#          " |a   a| "
	#      2   |/ x   x \|   5
	#          V  i   i  V
	#          "  s   s  "
	#          3         4
	#             b   b              ^ X
	#             0   1              |
	#                                |
	#                       Y <------+
	#
	# ROTATE V2 around axis g:
	# ------------------------------------
	# refer to V2 as if centre is origon:
	# rotate around axis b as if centre -> V2 is x-axis:
	x = (R - H) + cosg0 * H
	z =           sing0 * H
	# prepare for next: rotate V5 onto -x with angle d0
	cosd0 = -Tx / R
	sind0 = H # = sin(pi/7)
	# Then later: correction for V5 not on -x: rotate d around z-axis
	# with d: angle of heptagon centre to V2 with -x-as
	cosd1 = -(x2 + Tx) / R
	sind1 = SigmaH # = sin(3pi/7)
	x2, y2, z2 = (cosd0 * x, sind0 * x, z)

	# use similar calc for different angle for x5, -y5, z5 = x2, y2, z2
	x = (R - H) + cosg1 * H
	z =           sing1 * H
	x5, y5, z5 = (cosd0 * x, sind0 * x, z)

	# ROTATE V1 and V2 around axis b
	# ------------------------------------
	# refer to V1 as if centre in origon and as if V5 in -x:
	d0_3 = x0 - R - RhoH
	# rotate around axis b:
	x1, y1, z1 = (d0_3 + cosb0 * RhoH, -0.5, sinb0 * RhoH)
	# correct for V5 not on -x: rotate d around z-axis
	# and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
	x1, y1 = (cosd1 * x1 - sind1 * y1 - Tx, sind1 * x1 + cosd1 * y1)
	# Similarly for V2:
	# rotate around axis b:
	dx = x2 - d0_3
	x2, z2 = (d0_3 + cosb0 * dx - sinb0 * z2, sinb0 * dx + cosb0 * z2)
	# correct for V5 not on -x: rotate d around z-axis
	# and translate V3 - V4 back onto x-axis: [-Tx, 0, 0]
	x2, y2 = (cosd1 * x2 - sind1 * y2 - Tx, sind1 * x2 + cosd1 * y2)

	# use similar calc for different angle for
	# x5, y5, z5 = x2, -y2, z2
	# x6, y6, z6 = x1, -y1, z1
	x6, y6, z6 = (d0_3 + cosb1 * RhoH, -0.5, sinb1 * RhoH)
	x6, y6 = (cosd1 * x6 - sind1 * y6 - Tx, sind1 * x6 + cosd1 * y6)
	dx = x5 - d0_3
	x5, z5 = (d0_3 + cosb1 * dx - sinb1 * z5, sinb1 * dx + cosb1 * z5)
	x5, y5 = (cosd1 * x5 - sind1 * y5 - Tx, sind1 * x5 + cosd1 * y5)
	# x5, y5, z5 = x2, -y2, z2  and  x6, y6, z6 = x1, -y1, z1
	y5, y6 = -y5, -y6

    # rotate around 3-4; angle a
    # ------------------------------------
    # since half dihedral angle is used instead of angle with x-axis:
    # TODO don't copy the code...
    cos_a = sina
    sin_a = -cosa
    x0, y0, z0, = (cos_a * x0 - sin_a * z0, y0, sin_a * x0 + cos_a * z0)
    x1, y1, z1, = (cos_a * x1 - sin_a * z1, y1, sin_a * x1 + cos_a * z1)
    x2, y2, z2, = (cos_a * x2 - sin_a * z2, y2, sin_a * x2 + cos_a * z2)
    x5, y5, z5, = (cos_a * x5 - sin_a * z5, y5, sin_a * x5 + cos_a * z5)
    x6, y6, z6, = (cos_a * x6 - sin_a * z6, y6, sin_a * x6 + cos_a * z6)
    # and translate
    # ------------------------------------
    z0 = z0 + T
    z1 = z1 + T
    z2 = z2 + T
    z3 = z3 + T
    z4 = z4 + T
    z5 = z5 + T
    z6 = z6 + T

    cosd = numx.cos(delta)
    sind = numx.sin(delta)
    x0, y0 = x0 * cosd - y0 * sind, x0 * sind + y0 * cosd
    x1, y1 = x1 * cosd - y1 * sind, x1 * sind + y1 * cosd
    x2, y2 = x2 * cosd - y2 * sind, x2 * sind + y2 * cosd
    x3, y3 = x3 * cosd - y3 * sind, x3 * sind + y3 * cosd
    x4, y4 = x4 * cosd - y4 * sind, x4 * sind + y4 * cosd
    x5, y5 = x5 * cosd - y5 * sind, x5 * sind + y5 * cosd
    x6, y6 = x6 * cosd - y6 * sind, x6 * sind + y6 * cosd

    #print 'v0 =', [x0, y0, z0]
    #print 'v1 =', [x1, y1, z1]
    #print 'v2 =', [x2, y2, z2]
    #print 'v3 =', [x3, y3, z3]
    #print 'v4 =', [x4, y4, z4]
    #print 'v5 =', [x5, y5, z5]
    #print 'v6 =', [x6, y6, z6]

    return (x0, y0, z0, x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4, x5, y5, z5, x6, y6, z6)

def FoldedRegularHeptagonsA4xI(c, params):
    """Calculates the 4 variable edge lengths - 1 for the simplest A4xI case of
    folded heptagons.

    The case contains
    c[3]: a translation (towards the viewer)
    c[1]: half the angle between the 2 heptagons 0,1,2,3,4,5,6 and 7,8,9,3,4,10,11
    c[2]: the angle of the first fold around 2-5 (9, 10)
    c[3]: the angle of the first fold around 1-6 (8, 11)
    The vertices are positioned as follows:
    #          19                      18
    #
    #
    #             16                14
    #                      12
    #
    #               9             2
    #      8                               1
    #
    #                      3
    #
    #   7                                     0
    #
    #                      4
    #
    #     11                               6
    #              10             5
    #
    #                      13
    #             17                15

    And the relevant vertices are defined as follows:
    [ x1,    y1,    z1], # V1
    [ x2,    y2,    z2], # V2
    [ x3,    y3,    z3], # V3

    [-x2,    y2,    z2], # V9 = V2'

    [ y0,    z0,    x0], # V12 =(              0.0, 1.0/2,   0.) V0'

    [ y1,    z1,    x1], # V14 = V1'

    The heptagons are regular, so
    |0-1| = |1-2| = |2-3| = |3-4| = |4-5| = |5-6| = |6-0| = |12 - 14| = 1
    The alternatives for creatings triangles leads to the following possible
    variable edge lengths:
    params{'0'} | edge a | edge b | edge c | edge d
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 14 - 1	strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 14 - 1	strip I
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 14 - 1	strip II
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 12 - 1 | 14 - 1	star
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 12 - 1 | 14 - 1	star 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 18 - 2	strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 18 - 2	alt strip II
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 18 - 2	alt strip I
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 19 - 2 | 1 - 16 | 12 - 0	twisted

    For the param{'0'} the following constant names can be used, see
    TriangleAlt.

    params{'1'} steers which the edge lengths. It is a vector of 4 floating
    point numbers that expresses the edge lengths of [a, b, c, d]. If params 1
    is not given, the edge lengths are supposed to be 1.

    params{'2'} defines which heptagon folding method is used.
    """

    T     = c[0]
    alpha = c[1]
    beta  = c[2]
    gamma = c[3]
    delta = 0

    par_tri_fill = Param.tri_fill
    par_edge_len = Param.edge_len
    par_fold     = Param.h_fold

    edgeAlternative = params[par_tri_fill]
    if edgeAlternative & twist_bit == twist_bit:
	# rotate 45 degrees:
	delta = numx.pi/4

    x0, y0, z0, x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4, x5, y5, z5, x6, y6, z6 = GetBaseHeptagon(
	    T, alpha, beta, beta, gamma, gamma, delta, params[par_fold])

    #print 'v0', x0, y0, z0
    #print 'v1', x1, y1, z1
    #print 'v2', x2, y2, z2
    #print 'v3', x3, y3, z3
    cp = [0, 0, 0, 0]
    #
    # EDGE A
    #
    edgeLengths = [1., 1., 1., 1.]
    try:
        edgeLengths = params[Param.edge_len]
    except IndexError:
        pass
    if edgeAlternative & loose_bit:
        # V2 - V9:[-x2,    y2,    z2], # V9 = V2'
        cp[0] = numx.sqrt(4*x2*x2) - edgeLengths[0]
    elif edgeAlternative & twist_bit == twist_bit:
        # V2 - V9 = V2 - V5':  V5' = [-x5, -y5, z5]
        cp[0] = numx.sqrt((x2+x5)*(x2+x5) + (y2+y5)*(y2+y5) + (z2-z5)*(z2-z5)) - edgeLengths[0]
    else:
        # V3 - V12:[ y0,    z0,    x0], # V12 = V0'
        cp[0] = numx.sqrt((x3-y0)*(x3-y0) + (y3-z0)*(y3-z0) + (z3-x0)*(z3-x0)) - edgeLengths[0]
    #
    # EDGE B
    #
    plain_edge_alt = edgeAlternative & ~alt_bit
    if plain_edge_alt == TriangleAlt.stripII:
        # V3 - V14:[ y1,    z1,    x1], # V14 = V1'
        cp[1] = numx.sqrt((x3-y1)*(x3-y1) + (y3-z1)*(y3-z1) + (z3-x1)*(z3-x1)) - edgeLengths[1]
    elif edgeAlternative & twist_bit == twist_bit:
        # V2 - V19: V19 = V5' = [y5, z5, x5]
        cp[1] = numx.sqrt((x2-y5)*(x2-y5) + (y2-z5)*(y2-z5) + (z2-x5)*(z2-x5)) - edgeLengths[1]
    else:
        #V2 - V12:[ y0,    z0,    x0], # V12 = V0'
        cp[1] = numx.sqrt((x2-y0)*(x2-y0) + (y2-z0)*(y2-z0) + (z2-x0)*(z2-x0)) - edgeLengths[1]
    #
    # EDGE C
    #
    if edgeAlternative & twist_bit == twist_bit:
        # V1 - V16: V16 = V6' = [y6, z6, x6]
        cp[2] = numx.sqrt((x1-y6)*(x1-y6) + (y1-z6)*(y1-z6) + (z1-x6)*(z1-x6)) - edgeLengths[2]
    elif (
	edgeAlternative != TriangleAlt.star
	and edgeAlternative != TriangleAlt.star1loose
    ):
        # V2 - V14:[ y1,    z1,    x1], # V14 = V1'
        cp[2] = numx.sqrt((x2-y1)*(x2-y1) + (y2-z1)*(y2-z1) + (z2-x1)*(z2-x1)) - edgeLengths[2]
    else:
        # V1 - V12:[ y0,    z0,    x0], # V12 = V0'
        cp[2] = numx.sqrt((x1-y0)*(x1-y0) + (y1-z0)*(y1-z0) + (z1-x0)*(z1-x0)) - edgeLengths[2]
    #
    # EDGE D
    #
    if edgeAlternative & twist_bit == twist_bit:
        # V0 - V12 = V0 - V0': V0' = [ y0,    z0,    x0]
	cp[3] = numx.sqrt((x0-y0)*(x0-y0) + (y0-z0)*(y0-z0) + (z0-x0)*(z0-x0)) - edgeLengths[3]
    elif (edgeAlternative & alt_bit == 0):
	cp[3] = numx.sqrt((x1-y1)*(x1-y1) + (y1-z1)*(y1-z1) + (z1-x1)*(z1-x1)) - edgeLengths[3]
    else:
        # V2 - V18:[ y2,    z2,    x2], # V18 = V2'
	cp[3] = numx.sqrt((x2-y2)*(x2-y2) + (y2-z2)*(y2-z2) + (z2-x2)*(z2-x2)) - edgeLengths[3]

    #print cp
    return cp

def FoldedRegularHeptagonsA4(c, params):
    """Calculates the 4 variable edge lengths - 1 for the simplest A4 case of
    folded heptagons.

    The case contains
    c[0]: a translation (towards the viewer)
    c[1]: half the angle between the 2 heptagons 0,1,2,3,4,5,6 and 7,8,9,3,4,10,11
    c[2]: the angle of the first fold (left)
    c[3]: the angle of the second fold (left)
    c[4]: rotation angle around z-axis
    c[5]: the angle of the first fold (right)
    c[6]: the angle of the second fold (right)
    The vertices are positioned as follows:
    #          19                      18
    #
    #
    #             16                14
    #                      12
    #
    #               9             2
    #      8                               1
    #
    #                      3
    #
    #   7                                     0
    #
    #                      4
    #
    #     11                               6
    #              10             5
    #
    #                      13
    #             17                15

    And the relevant vertices are defined as follows:
    [ x1,    y1,    z1], # V1
    [ x2,    y2,    z2], # V2
    [ x3,    y3,    z3], # V3

    [-x5,   -y5,    z5], # V9 = V2'
    [ y0,    z0,    x0], # V12 = V0'
    [ y1,    z1,    x1], # V14 = V1'

    The heptagons are regular, so
    |0-1| = |1-2| = |2-3| = |3-4| = |4-5| = |5-6| = |6-0| = |12 - 14| = 1

    For the param[0] the following constant names can be used:
    The alternatives for creatings triangles leads to the following possible
    variable edge lengths:
    params{'0'} | edge a | edge b | edge c | edge d
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 8 - 16	strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 8 - 16	strip I
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 8 - 16	strip II
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 12 - 1 | 8 - 16	star
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 12 - 1 | 8 - 16	star 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 9 - 19	alt strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 9 - 19	alt strip II
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 9 - 19	alt strip I
    ------------+--------+--------+--------+-------

    only valid for opposites alternatives:
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 9 - 16 | 8 - 16	rot strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 9 - 16 | 9 - 19	alt rot strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 2 -  8 | 8 - 16	rot star 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 2 - 19 | 9 - 19	alt rot star 1 loose
    ------------+--------+--------+--------+-------

    params{'1'} alternatives for the opposite triangle fill.

    params{'2'} steers which the edge lengths. It is a vector of 7 floating
    point numbers that expresses the edge lengths of [a, b0, c0, d, b1, c1]. If
    this params is not given, the edge lengths are supposed to be 1.

    params{'3'} defines which heptagon folding method is used.

    params{'4'} rotate the folding with n/7 turn
    """

    T      = c[0]
    alpha  = c[1]
    beta0  = c[2]
    gamma0 = c[3]
    delta  = c[4]
    beta1  = c[5]
    gamma1 = c[6]

    par_tri_fill = Param.tri_fill
    par_opp_fill = Param.opp_fill
    par_edge_len = Param.edge_len
    par_fold     = Param.h_fold
    n_7_turn     = Param.n_7_turn

    x0, y0, z0, x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4, x5, y5, z5, x6, y6, z6 = GetBaseHeptagon(
	    T, alpha, beta0, beta1, gamma0, gamma1, delta, params[par_fold])
    cp = copy.copy(c)
    edgeAlternative = params[par_tri_fill]
    oppoAlternative = params[par_opp_fill]
    #
    # EDGE A: only one for A4
    #
    try:
        edgeLengths = params[par_edge_len]
    except IndexError:
	edgeLengths = [1., 1., 1., 1., 1., 1., 1.]

    if edgeAlternative & loose_bit:
        # V2 - V9:[-x5,   -y5,    z5], # V9 = V5'
        cp[0] = numx.sqrt((x2+x5)*(x2+x5) + (y2+y5)*(y2+y5) + (z2-z5)*(z2-z5)) - edgeLengths[0]
    else:
        # V3 - V12:[ y0,    z0,    x0], # V12 = V0'
        cp[0] = numx.sqrt((x3-y0)*(x3-y0) + (y3-z0)*(y3-z0) + (z3-x0)*(z3-x0)) - edgeLengths[0]

    #
    # EDGE B: 2 different B's for A4
    #
    plain_edge_alt = edgeAlternative & ~alt_bit
    if plain_edge_alt == TriangleAlt.stripII:
        # V3 - V14:[y1, z1, x1], # V14 = V1'
        cp[1] = numx.sqrt((x3-y1)*(x3-y1) + (y3-z1)*(y3-z1) + (z3-x1)*(z3-x1)) - edgeLengths[1]
    else:
        #V2 - V12:[y0, z0, x0], # V12 = V0'
        cp[1] = numx.sqrt((x2-y0)*(x2-y0) + (y2-z0)*(y2-z0) + (z2-x0)*(z2-x0)) - edgeLengths[1]

    #
    # EDGE C
    #
    if (
	edgeAlternative != TriangleAlt.star
	and edgeAlternative != TriangleAlt.star1loose
    ):
        # V2 - V14:[ y1, z1, x1], # V14 = V1'
        cp[2] = numx.sqrt((x2-y1)*(x2-y1) + (y2-z1)*(y2-z1) + (z2-x1)*(z2-x1)) - edgeLengths[2]
    else:
        # V1 - V12:[y0,    z0,    x0], # V12 = V0'
        cp[2] = numx.sqrt((x1-y0)*(x1-y0) + (y1-z0)*(y1-z0) + (z1-x0)*(z1-x0)) - edgeLengths[2]

    #
    # EDGE D
    #
    if (edgeAlternative & alt_bit == 0):
	# V1 - V14:[ y1,    z1,    x1], # V14 = V1'
	cp[3] = numx.sqrt((x1-y1)*(x1-y1) + (y1-z1)*(y1-z1) + (z1-x1)*(z1-x1)) - edgeLengths[3]
    else:
        # V2 - V18:[ y2,    z2,    x2], # V18 = V2'
	cp[3] = numx.sqrt((x2-y2)*(x2-y2) + (y2-z2)*(y2-z2) + (z2-x2)*(z2-x2)) - edgeLengths[3]

    # opposite alternative edges, similar as above
    #
    # OPPOSITE EDGE B
    #
    plain_edge_alt = oppoAlternative & ~alt_bit
    if plain_edge_alt == TriangleAlt.stripII:
        # V3 - V16:[y6, z6, x6], # V16 = V6'
        cp[4] = numx.sqrt((x3-y6)*(x3-y6) + (y3-z6)*(y3-z6) + (z3-x6)*(z3-x6)) - edgeLengths[4]
    elif plain_edge_alt & rot_bit == rot_bit:
        # V2 - V16:[y6, z6, x6], # V16 = V6'
        cp[4] = numx.sqrt((x2-y6)*(x2-y6) + (y2-z6)*(y2-z6) + (z2-x6)*(z2-x6)) - edgeLengths[4]
    else:
        #V9:[-x5, -y5, z5] - V12, # V9 = V5'
        cp[4] = numx.sqrt((-x5-y0)*(-x5-y0) + (-y5-z0)*(-y5-z0) + (z5-x0)*(z5-x0)) - edgeLengths[4]
    #
    # OPPOSITE EDGE C
    #
    if oppoAlternative == TriangleAlt.arot_star1loose:
	# V2 - V19: V19 = V5' = [y5, z5, x5]
        cp[5] = numx.sqrt((x2-y5)*(x2-y5) + (y2-z5)*(y2-z5) + (z2-x5)*(z2-x5)) - edgeLengths[5]
    elif oppoAlternative == TriangleAlt.rot_star1loose:
	# V2 - V8: V8 = V6' = [-x6, -y6, z6]
        cp[5] = numx.sqrt((x2+x6)*(x2+x6) + (y2+y6)*(y2+y6) + (z2-z6)*(z2-z6)) - edgeLengths[5]
    elif (
	oppoAlternative != TriangleAlt.star
	and oppoAlternative != TriangleAlt.star1loose
    ):
	# V9 - V16: V9 = V5' = [-x5, -y5, z5], V16 = V6' = [ y6, z6, x6]
        cp[5] = numx.sqrt((y6+x5)*(y6+x5) + (z6+y5)*(z6+y5) + (x6-z5)*(x6-z5)) - edgeLengths[5]
    else:
        # V8: [-x6, -y6, z6] - V12, # V8 = V6'
        cp[5] = numx.sqrt((x6+y0)*(x6+y0) + (y6+z0)*(y6+z0) + (x0-z6)*(x0-z6)) - edgeLengths[5]
    #
    # OPPOSITE EDGE D
    #
    if (oppoAlternative & alt_bit == 0):
	# V8 - V16: V8 = V6' = [-x6, -y6, z6]; V16 = V6' = [y6, z6, x6]
	cp[6] = numx.sqrt((y6+x6)*(y6+x6) + (z6+y6)*(z6+y6) + (x6-z6)*(x6-z6)) - edgeLengths[6]
    else:
	# V9 - V19: V9 = V5' = [-x5, -y5, z5]; V19 = V5' = [y5, z5, x5]
	cp[6] = numx.sqrt((y5+x5)*(y5+x5) + (z5+y5)*(z5+y5) + (x5-z5)*(x5-z5)) - edgeLengths[6]

    #print cp
    return cp

def S4_Q_turn_o4(x, y, z):
    """Rotate [x, y, z] a quarter turn around the S4 o4 axis [1, 0, 1]

    Returns the tuple [x', y', z']
    """
    # Rotations is obtained by
    # 1. rotate one eight turn around negative y-axis
    # 1. rotate quarter turn around positive z-axis
    # 3. rotate one eight turn around positive x-axis
    # TODO: optimise me

    # 1: x_, y_, z_ =  hV2x - hV2z, y,  hV2x + hV2z
    # 2: x_, y_     = -y_, x_
    # so 1 & 2:
    hV2x = hV2 * x
    hV2z = hV2 * z
    y_, x_, z_ = hV2x - hV2z, -y, hV2x + hV2z
    # 3: x_, y_, z_ =  hV2x + hV2z, y, -hV2x + hV2z
    hV2x = hV2 * x_
    hV2z = hV2 * z_
    x_, z_ =  hV2x + hV2z, -hV2x + hV2z
    return (x_, y_, z_)

def S4_T_turn_o3(x, y, z):
    # TODO TODO TODO: FIX THIS FUNCTION, there is an error
    """Rotate [x, y, z] a third turn around the S4 o3 axis [0, -1/V3, V2/V3]

    Returns the tuple [x', y', z']
    """
    # Rotations is obtained by
    # 1. rotate alpha turn around negative x-axis
    # 1. rotate third turn around positive z-axis
    # 3. rotate alpha turn around positive x-axis
    # where alpha = atan(hV2) <----- atan( (1/V3) / (V2/V3) )

    # TODO: optimise me
    # 1: x_, y_, z_ =  x, y*V2/V3 + z/V3, -y/V3 + z * V2/V3
    x_, y_, z_ = x, V2dV3 * y + tV3 * z, -tV3 * y + V2dV3 * z
    # 2: x_, y_     = -x/2 - hV3.y,  hV3.x - y/2
    x_, y_ = -x_/2 - hV3 * y_, hV3 * x_ - y_/2
    # 3: x_, y_, z_ =  x, y*V2/V3 - z/V3, y/V3 + z * V2/V3
    y_, z_ = V2dV3 * y_ + tV3 * z_, -tV3 * y_ + V2dV3 * z_
    return (x_, y_, z_)

def v_delta(x0, y0, z0, x1, y1, z1):
    return numx.sqrt((x1-x0)*(x1-x0) + (y1-y0)*(y1-y0) + (z1-z0)*(z1-z0))

def FoldedRegularHeptagonsS4(c, params):
    """Calculates the 4 variable edge lengths - 1 for the simplest S4 case of
    folded heptagons.

    The case contains
    c[0]: a translation (towards the viewer)
    c[1]: half the angle between the 2 heptagons 0,1,2,3,4,5,6 and 7,8,9,3,4,10,11
    c[2]: the angle of the first fold (left)
    c[3]: the angle of the second fold (left)
    c[4]: rotation angle around z-axis
    c[5]: the angle of the first fold (right)
    c[6]: the angle of the second fold (right)
    The vertices are positioned as follows:

    #
    #
    #               9             2
    #      8                               1
    #
    #                      3
    #
    #   7           z-axis . o2-axis          0       . o4-axis: [0, 1, 1]
    #
    #                      4
    #
    #     11                               6
    #              10             5
    #
    #
    #                      . o3 axis: [0, -1/V3, V2/V3]

    And the relevant vertices are defined as follows:

    The heptagons are regular, so
    |0-1| = |1-2| = |2-3| = |3-4| = |4-5| = |5-6| = |6-0| = |12 - 14| = 1

    For the param[0] the following constant names can be used:
    The alternatives for creatings triangles leads to the following possible
    variable edge lengths:
    params{'0'} | edge a | edge b | edge c | edge d
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 8 - 16	strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 8 - 16	strip I
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 8 - 16	strip II
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 12 - 1 | 8 - 16	star
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 12 - 1 | 8 - 16	star 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 12 - 2 | 2 - 14 | 9 - 19	alt strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 3 - 14 | 2 - 14 | 9 - 19	alt strip II
    ------------+--------+--------+--------+-------
             ?  | 3 - 12 | 12 - 2 | 2 - 14 | 9 - 19	alt strip I
    ------------+--------+--------+--------+-------

    only valid for opposites alternatives:
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 9 - 16 | 8 - 16	rot strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 9 - 16 | 9 - 19	alt rot strip 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 2 -  8 | 8 - 16	rot star 1 loose
    ------------+--------+--------+--------+-------
             ?  | 2 - 9  | 2 - 16 | 2 - 19 | 9 - 19	alt rot star 1 loose
    ------------+--------+--------+--------+-------

    params{'1'} alternatives for the opposite triangle fill.

    params{'2'} steers the edge lengths. It is a vector of 4 or 7 floating point
    numbers that expresses the edge lengths of [a, b, c, d] or
    [a, b0, c0, d, b1, c1] resp. If length 4, then c[5] = c[2] and c[6] = c[3];
    the value of c[4] is either 0 or pi/2 rad, depending on params[5].
    If this params[2] is not given, the edge lengths are supposed to be 1.

    params{'3'} defines which heptagon folding method is used.

    params{'5'} Only used if params 2 has length 4, then if:
                False: c[4] = 0
                True:  c[4] = pi/2

    params{'4'} rotate the folding with n/7 turn
    """

    # params indices in text:

    T      = c[0]
    alpha  = c[1]
    beta0  = c[2]
    gamma0 = c[3]

    par_tri_fill       = Param.tri_fill
    par_edge_len       = Param.edge_len
    par_fold           = Param.h_fold
    par_refl_max_angle = Param.refl_max_angle

    incl_reflections = len(params[par_edge_len]) == 4
    if incl_reflections:
	beta1  = beta0
	gamma1 = gamma0
	if params[par_refl_max_angle]:
	    delta  = numx.pi/2
	else:
	    delta  = 0
	oppoAlternative = params[par_tri_fill]
    else:
	delta  = c[4]
	beta1  = c[5]
	gamma1 = c[6]
	oppoAlternative = params[par_opp_fill]
    x0, y0, z0, x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4, x5, y5, z5, x6, y6, z6 = GetBaseHeptagon(
	    T, alpha, beta0, beta1, gamma0, gamma1, delta, params[par_fold])
    cp = copy.copy(c)
    edgeAlternative = params[par_tri_fill]
    #
    # EDGE A: only one for A4
    #
    try:
        edgeLengths = params[par_edge_len]
    except IndexError:
	edgeLengths = [1., 1., 1., 1., 1., 1., 1.]

    if ((edgeAlternative & loose_bit) != 0 or
    	(edgeAlternative & twist_bit) != 0
    ):
        # V2 - V9:[-x5,   -y5,    z5], # V9 = V5'
        cp[0] = numx.sqrt((x2+x5)*(x2+x5) + (y2+y5)*(y2+y5) + (z2-z5)*(z2-z5)) - edgeLengths[0]
    else:
	# TODO
        # V3 - V12:[ y0,    z0,    x0], # V12 = V0'
        cp[0] = numx.sqrt((x3-y0)*(x3-y0) + (y3-z0)*(y3-z0) + (z3-x0)*(z3-x0)) - edgeLengths[0]

    #
    # EDGE B:
    #
    plain_edge_alt = edgeAlternative & ~alt_bit
    if (edgeAlternative & twist_bit) != 0:
	# V5 - Q-turn-around-o4(V2)
	V2_o4_x, V2_o4_y, V2_o4_z = S4_Q_turn_o4(x2, y2, z2)
        cp[1] = v_delta(x5, y5, z5, V2_o4_x, V2_o4_y, V2_o4_z) - edgeLengths[1]
    #TODO:
    elif plain_edge_alt == TriangleAlt.stripII:
        # V3 - V14:[y1, z1, x1], # V14 = V1'
        cp[1] = numx.sqrt((x3-y1)*(x3-y1) + (y3-z1)*(y3-z1) + (z3-x1)*(z3-x1)) - edgeLengths[1]
    else:
        #V2 - V12:[y0, z0, x0], # V12 = V0'
        cp[1] = numx.sqrt((x2-y0)*(x2-y0) + (y2-z0)*(y2-z0) + (z2-x0)*(z2-x0)) - edgeLengths[1]

    #
    #
    #               9             2
    #      8                               1
    #
    #                      3
    #
    #   7           z-axis . o2-axis          0       . o4-axis: [0, 1, 1]
    #
    #                      4
    #
    #     11                               6
    #              10             5
    #
    #
    #                      . o3 axis: [1/V3, 0, V2/V3]

    #
    # EDGE C
    #
    if (edgeAlternative & twist_bit) != 0:
	# V6 - Q-turn-around-o4(V1)
	V1_o4_x, V1_o4_y, V1_o4_z = S4_Q_turn_o4(x1, y1, z1)
        cp[2] = v_delta(x6, y6, z6, V1_o4_x, V1_o4_y, V1_o4_z) - edgeLengths[2]
    #TODO:
    elif (
	edgeAlternative != TriangleAlt.star
	and edgeAlternative != TriangleAlt.star1loose
    ):
        # V2 - V14:[ y1, z1, x1], # V14 = V1'
        cp[2] = numx.sqrt((x2-y1)*(x2-y1) + (y2-z1)*(y2-z1) + (z2-x1)*(z2-x1)) - edgeLengths[2]
    else:
        # V1 - V12:[y0,    z0,    x0], # V12 = V0'
        cp[2] = numx.sqrt((x1-y0)*(x1-y0) + (y1-z0)*(y1-z0) + (z1-x0)*(z1-x0)) - edgeLengths[2]

    #
    # EDGE D
    #
    if (edgeAlternative & twist_bit) != 0:
	# V0 - T-turn-around-o4(V9:[x0,   y0,    z0])
	V0_o4_x, V0_o4_y, V0_o4_z = S4_Q_turn_o4(x0, y0, z0)
        cp[3] = v_delta(x0, y0, z0, V0_o4_x, V0_o4_y, V0_o4_z) - edgeLengths[3]
    #TODO:
    elif (edgeAlternative & alt_bit == 0):
	# V1 - V14:[ y1,    z1,    x1], # V14 = V1'
	cp[3] = numx.sqrt((x1-y1)*(x1-y1) + (y1-z1)*(y1-z1) + (z1-x1)*(z1-x1)) - edgeLengths[3]
    else:
        # V2 - V18:[ y2,    z2,    x2], # V18 = V2'
	cp[3] = numx.sqrt((x2-y2)*(x2-y2) + (y2-z2)*(y2-z2) + (z2-x2)*(z2-x2)) - edgeLengths[3]

    if not incl_reflections:
	# opposite alternative edges, similar as above
	#
	# OPPOSITE EDGE B
	#
	plain_edge_alt = oppoAlternative & ~alt_bit
	if plain_edge_alt == TriangleAlt.stripII:
	    # V3 - V16:[y6, z6, x6], # V16 = V6'
	    cp[4] = numx.sqrt((x3-y6)*(x3-y6) + (y3-z6)*(y3-z6) + (z3-x6)*(z3-x6)) - edgeLengths[4]
	elif plain_edge_alt & rot_bit == rot_bit:
	    # V2 - V16:[y6, z6, x6], # V16 = V6'
	    cp[4] = numx.sqrt((x2-y6)*(x2-y6) + (y2-z6)*(y2-z6) + (z2-x6)*(z2-x6)) - edgeLengths[4]
	else:
	    #V9:[-x5, -y5, z5] - V12, # V9 = V5'
	    cp[4] = numx.sqrt((-x5-y0)*(-x5-y0) + (-y5-z0)*(-y5-z0) + (z5-x0)*(z5-x0)) - edgeLengths[4]
	#
	# OPPOSITE EDGE C
	#
	if oppoAlternative == TriangleAlt.arot_star1loose:
	    # V2 - V19: V19 = V5' = [y5, z5, x5]
	    cp[5] = numx.sqrt((x2-y5)*(x2-y5) + (y2-z5)*(y2-z5) + (z2-x5)*(z2-x5)) - edgeLengths[5]
	elif oppoAlternative == TriangleAlt.rot_star1loose:
	    # V2 - V8: V8 = V6' = [-x6, -y6, z6]
	    cp[5] = numx.sqrt((x2+x6)*(x2+x6) + (y2+y6)*(y2+y6) + (z2-z6)*(z2-z6)) - edgeLengths[5]
	elif (
	    oppoAlternative != TriangleAlt.star
	    and oppoAlternative != TriangleAlt.star1loose
	):
	    # V9 - V16: V9 = V5' = [-x5, -y5, z5], V16 = V6' = [ y6, z6, x6]
	    cp[5] = numx.sqrt((y6+x5)*(y6+x5) + (z6+y5)*(z6+y5) + (x6-z5)*(x6-z5)) - edgeLengths[5]
	else:
	    # V8: [-x6, -y6, z6] - V12, # V8 = V6'
	    cp[5] = numx.sqrt((x6+y0)*(x6+y0) + (y6+z0)*(y6+z0) + (x0-z6)*(x0-z6)) - edgeLengths[5]
	#
	# OPPOSITE EDGE D
	#
	if (oppoAlternative & alt_bit == 0):
	    # V8 - V16: V8 = V6' = [-x6, -y6, z6]; V16 = V6' = [y6, z6, x6]
	    cp[6] = numx.sqrt((y6+x6)*(y6+x6) + (z6+y6)*(z6+y6) + (x6-z6)*(x6-z6)) - edgeLengths[6]
	else:
	    # V9 - V19: V9 = V5' = [-x5, -y5, z5]; V19 = V5' = [y5, z5, x5]
	    cp[6] = numx.sqrt((y5+x5)*(y5+x5) + (z5+y5)*(z5+y5) + (x5-z5)*(x5-z5)) - edgeLengths[6]

    #print cp
    return cp


class Method:
    hybrids = 0
    dnewton = 1
    broyden = 2
    hybrid  = 3

def FindMultiRoot(initialValues,
	symmetry,
        edgeAlternative,
        edgeLengths = [1., 1., 1., 1.],
	fold = Fold.parallel,
        method = 1,
        cleanupF  = None,
        prec_delta = 1e-15,
        maxIter = 100,
        printIter = False,
        quiet     = False,
	oppEdgeAlternative = None
    ):
    if oppEdgeAlternative == None:
	oppEdgeAlternative = edgeAlternative
    if not quiet:
        print '[|a|, |b|, |c|, |d|] =', edgeLengths, 'for',
        if edgeAlternative == 0:
            print 'triangle strip, 1 loose:'
        elif edgeAlternative == 1:
            print 'triangle strip I:'
        elif edgeAlternative == 2:
            print 'triangle strip II:'
        elif edgeAlternative == 3:
            print 'triangle star:'
        elif edgeAlternative == 4:
            print 'triangle star, 1 loose:'

    nrOfIns = len(initialValues)
    if nrOfIns == 4:
	if symmetry == Symmetry.A4xI:
		mysys = multiroots.gsl_multiroot_function(
		    FoldedRegularHeptagonsA4xI,
		    {
			Param.tri_fill: edgeAlternative,
			Param.edge_len: edgeLengths,
			Param.h_fold:   fold
		    },
		    nrOfIns
		)
	else:
		mysys = multiroots.gsl_multiroot_function(
		    FoldedRegularHeptagonsS4,
		    {
			Param.tri_fill:       edgeAlternative,
			Param.edge_len:       edgeLengths,
			Param.h_fold:         fold,
			Param.refl_max_angle: False # TODO, dyn set
		    },
		    nrOfIns
		)
    elif nrOfIns == 7:
	mysys = multiroots.gsl_multiroot_function(
	    FoldedRegularHeptagonsA4,
	    {
		Param.tri_fill: edgeAlternative,
		Param.opp_fill: oppEdgeAlternative,
		Param.edge_len: edgeLengths,
		Param.h_fold:   fold
	    },
	    nrOfIns
	)
    else:
	assert False, "error: wrong dimension: %d" % nrOfIns

    if method == Method.hybrids:
        solver = multiroots.hybrids(mysys, nrOfIns)
    elif method == Method.dnewton:
        solver = multiroots.dnewton(mysys, nrOfIns)
    elif method == Method.broyden:
        solver = multiroots.broyden(mysys, nrOfIns)
    else:
        solver = multiroots.hybrid(mysys, nrOfIns)

    solver.set(initialValues)
    if printIter:
        print "# Using solver ", solver.name(), 'with edge alternative:', edgeAlternative
        print "# %5s %9s %9s %9s %9s  %9s  %10s  %9s  %10s" % (
            "iter",
            "x[0]", "x[1]", "x[2]", "x[3]",
            "f[0]", "f[1]", "f[2]", "f[3]"
        )
        # Get and print initial values
        r = solver.root()
        x = solver.getx()
        f = solver.getf()
        print "  %5d % .7f % .7f % .7f % .7f  % .7f  % .7f  % .7f  % .7f" %(
            0,
            x[0], x[1], x[2], x[3],
            f[0], f[1], f[2], f[3]
        )
    result = None
    for iter in range(maxIter):
	try:
	    status = solver.iterate()
	    r = solver.root()
	    x = solver.getx()
	    f = solver.getf()
	    status = multiroots.test_residual(f, prec_delta)
	    if status == errno.GSL_SUCCESS and not quiet:
		print "# Converged :"
	    if printIter:
		print "  %5d % .7f % .7f % .7f % .7f  % .7f  % .7f  % .7f  % .7f" %(
		    iter+1,
		    x[0], x[1], x[2], x[3],
		    f[0], f[1], f[2], f[3]
		)
	    if status == errno.GSL_SUCCESS:
		# Now print solution with high precision
		if not quiet:
		    for i in range(nrOfIns):
			print "x[%d] = %.15f" % (i, x[i])
		result = [x[i] for i in range(nrOfIns)]
		break
	    else:
		if not quiet:
		    print "# not converged... :("
	except pygsl.errors.gsl_SingularityError:
	    #print 'gsl_Singularity Error exception', maxIter
	    del(solver)
	    break
	    pass
	except pygsl.errors.gsl_NoProgressError:
	    #print 'gsl_NoProgress Error exception', maxIter
	    del(solver)
	    break
	    pass
	except pygsl.errors.gsl_JacobianEvaluationError:
	    #print 'gsl_JacobianEvaluation Error exception', maxIter
	    del(solver)
	    break
	    pass
    if result != None and cleanupF != None:
        result = cleanupF(result, nrOfIns)
    return result

class RandFindMultiRootOnDomain(threading.Thread):
    def __init__(this,
	domain,
	symmetry,
	threadId = 0,
	edgeAlternative = TriangleAlt.stripI,
	oppEdgeAlternative = None,
	method = 1,
	precision = 15,
	fold = Fold.parallel,
	dynSols = None,
	edgeLengths = [1., 1., 1., 1., 1., 1., 1.],
	outDir = "frh-roots"
    ):
	this.domain = domain
	this.symmetry = symmetry
	this.threadId = threadId
	this.method = method
	this.precision = precision
	this.prec_delta = pow(10, -precision)
	pf = '%%.%df' % this.precision
	this.sol5 = '    [%s, %s, %s, %s, %s],\n' % (pf, pf, pf, pf, pf)
	this.sol7 = '    [%s, %s, %s, %s, %s, %s, %s],\n' % (pf, pf, pf, pf, pf, pf, pf)
	this.fold = fold
	this.edgeAlternative = edgeAlternative
	this.oppEdgeAlternative = oppEdgeAlternative
	this.edgeLengths = edgeLengths
	this.dynamicSols = dynSols
	this.dynSols = dynSols
	this.stopAfter = 100000
	this.printStatus = False,
	this.outDir = outDir
	if not outDir[-1] == '/':
	    this.outDir = "%s/" % outDir
	if not os.path.isdir(outDir):
	    os.mkdir(outDir, 0755)
	random.seed()
	threading.Thread.__init__(this)

    changeIterLimits = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    maxIters = [2 ** (6+8-i) for i in range(9)]
    def setMaxIter(this):
	nrSols = len(this.results)
	if nrSols >= this.changeIterLimits[8]:
	    return this.maxIters[8]
	elif nrSols == this.changeIterLimits[7]:
	    return this.maxIters[7]
	elif nrSols == this.changeIterLimits[6]:
	    return this.maxIters[6]
	elif nrSols == this.changeIterLimits[5]:
	    return this.maxIters[5]
	elif nrSols == this.changeIterLimits[4]:
	    return this.maxIters[4]
	elif nrSols == this.changeIterLimits[3]:
	    return this.maxIters[3]
	elif nrSols == this.changeIterLimits[2]:
	    return this.maxIters[2]
	elif nrSols == this.changeIterLimits[1]:
	    return this.maxIters[1]
	elif nrSols <= this.changeIterLimits[0]:
	    return this.maxIters[0]

    dpi = 2*numx.pi
    def cleanupResult(this, v, l = 4):
	lim = this.dpi
	hLim = numx.pi
        for i in range(1, l):
            v[i] = v[i] % lim
	    # move interval from [0, lim] to [-lim/2, lim/2]:
            if v[i] > hLim:
                v[i] = v[i] - lim
	    if eq(v[i], -hLim):
                # float rounding:
                v[i] = v[i] + lim
            # shouldn't happen:
            #elif v[i] < -hLim:
            #    v[i] = v[i] + lim
	# If the position angle equals 180 degrees, reconstruct the solution to
	# a pos angle = 0 by:
	# - using a negative translation
	# - an opposite dihedral angle
	# - negative folding angles
	# TODO check if this is valid for symmetries other than A4
	if (
	    len(v) >= 5
	    and
	    eq(v[4], numx.pi, this.prec_delta)
	):
	    v[4] = 0			# set pos angle to 0 instead
	    v[0] = -v[0] 		# -translate
	    if v[1] < 0:
		v[1] = -numx.pi - v[1]	# oppsite dihedral angle
	    else:
		v[1] = numx.pi - v[1]	# oppsite dihedral angle
	    v[2] = -v[2]		# opposite folds
	    v[3] = -v[3]
	    if len(v) >= 6:
		v[5] = -v[5]		# opposite folds
		if len(v) >= 7:
		    v[6] = -v[6]
        return v

    def randTestvalue(this):
	dLen = len(this.domain)
	return [
	    random.random() * (this.domain[i][1] - this.domain[i][0]) + this.domain[i][0]
	    for i in range(dLen)
	]

    # This can be optimised
    def solutionAlreadyFound(this, sol):
	found = False
	lstRange = range(len(sol))
	for old in this.results:
	    allElemsEqual = True
	    for i in lstRange:
		if len(old) < len(sol):
		    print 'Oops'
		    print 'old', old
		    print 'sol', sol
		if abs(old[i] - sol[i]) > 100 * this.prec_delta:
		    allElemsEqual = False
		    break # for i loop, not for old
	    if allElemsEqual:
		found = True
		break # for old loop
	return found

    def isDynamicSol(this, sol):
	if this.dynamicSols != None:
	    for d in this.dynamicSols:
		ea_ok = False
		for ea in d['edgeAlternative']:
		    ea_ok = (this.edgeAlternative == ea) or ea_ok
		if ea_ok:
		    oa_ok = False
		    for oa in d['oppEdgeAlternative']:
			oa_ok = (this.oppEdgeAlternative == oa) or oa_ok
		    if oa_ok:
			fld_ok = False
			for fld in d['fold']:
			    fld_ok = (this.fold == fld) or fld_ok
			if fld_ok:
			    for vs in d['sol_vector']:
				sol_isEq = True
				for i in range(len(vs)):
				    if not eq(vs[i], this.edgeLengths[i]):
					sol_isEq = False
					break # don't check other (i, v)
				if sol_isEq:
				    break # from vs in d['sol_vector']
			    if sol_isEq:
				for vs in d['set_vector']:
				    isEq = True
				    for i in range(len(vs)):
					if not eq(vs[i], this.edgeLengths[i]):
					    isEq = False
					    break # don't check other (i, v)
				    if isEq:
					return isEq
	return False

    def symmetricEdges(this):
	el = this.edgeLengths
	return (
	    len(el) > 5 and (
		eq(el[1], el[4]) and eq(el[2], el[5]) and eq(el[3], el[6])
		and this.edgeAlternative == this.oppEdgeAlternative
	    )
	)

    def getOutName(this):
	if len(this.edgeLengths) == 4:
	    return this.getOutReflName()
	# else:
	es = ''
	for l in this.edgeLengths:
	    # TODO move to func and reuse in getOutReflName
	    if l == 1 or l == 0:
		es = '%s_%d' % (es, l)
	    elif eq(l, V2):
		es = '%s_V2' % (es)
	    else:
		es = '%s_%.1f' % (es, l)
	es = es[1:]
	return '%sfrh-roots-%s-fld_%s.0-%s-opp_%s.py' % (
		this.outDir,
		es, Fold(this.fold),
		string.join(Stringify[this.edgeAlternative].split(), '_'),
		string.join(Stringify[this.oppEdgeAlternative].split(), '_')
	    )

    def getOutReflName(this):
	es = ''
	for i in range(0, 4):
	    l = this.edgeLengths[i]
	    if l == 1 or l == 0:
		es = '%s_%d' % (es, l)
	    elif eq(l, V2):
		es = '%s_V2' % (es)
	    else:
		es = '%s_%.1f' % (es, l)
	es = es[1:]
	return '%sfrh-roots-%s-fld_%s.0-%s.py' % (
		this.outDir,
		es, Fold(this.fold),
		string.join(Stringify[this.edgeAlternative].split(), '_')
	    )

    def _extend_refl_results(this, refl_results):
	for r in refl_results:
	    if len(r) == 4:
		r.extend([0.0, r[2], r[3]])
	    elif len(r) == 5:
		r.extend([r[2], r[3]])

    def run(this):
	if this.oppEdgeAlternative == None:
	    this.oppEdgeAlternative = this.edgeAlternative
	testValue = this.randTestvalue()
	if printStatus:
	    print testValue
	# changeIterLimits depends a bit on the amount of solutions.
	# 1. if you don't have a solution: just jump around until you get a
	#    hit.
	# 2. But you don't want to jump around a long time, just to find out
	#    it was a solution you already had.
	# Nr 2 will happen, when you are looking for the last solution,
	# especially if solutions are rare.

	filename = this.getOutName()

	# read previous file
	try:
	    f = open(filename, 'r')
	    ed = {'__name__': 'readPyFile'}
	    exec f in ed
	    # TODO check settings
	    try:
		this.results = ed['results']
	    except KeyError:
		this.results = []
		pass
	    try:
		results_refl = ed['results_refl']
		this._extend_refl_results(results_refl)
		this.results.extend(results_refl)
	    except KeyError:
		pass
	    try:
		prev_iterations = ed['iterations']
	    except KeyError:
		prev_iterations = 0
		pass
	    f.close()

	except IOError:
	    this.results = []
	    prev_iterations = 0

	if len(this.edgeLengths) > 4 and this.symmetricEdges():
	    refl_filename = this.getOutReflName()

	    # read previous file with reflective sols
	    try:
		f = open(refl_filename, 'r')
		ed = {'__name__': 'readPyFile'}
		exec f in ed
		# TODO check settings
		try:
		    results_refl = ed['results']
		    this._extend_refl_results(results_refl)
		    this.results.extend(results_refl)
		except KeyError:
		    pass
		try:
		    results_refl = ed['results_refl']
		    this._extend_refl_results(results_refl)
		    this.results.extend(results_refl)
		except KeyError:
		    pass
		try:
		    prev_refl_iterations = ed['iterations']
		except KeyError:
		    prev_refl_iterations = 0
		    pass
		f.close()

	    except IOError:
		prev_refl_iterations = 0

	nrOfIters = 0
	if this.fold == Fold.trapezium:
	    maxIter = 50
	else:
	    maxIter = this.setMaxIter()
	while True:
	    try:
		#print '%s:' % time.strftime("%y%m%d %H%M%S", time.localtime()),
		#print 'step'
		result = FindMultiRoot(testValue,
			this.symmetry,
			this.edgeAlternative,
			this.edgeLengths,
			this.fold,
			this.method,
			lambda v,l: this.cleanupResult(v, l),
			this.prec_delta,
			maxIter,
			printIter = False,
			quiet     = True,
			oppEdgeAlternative = this.oppEdgeAlternative
		    )
		if (
		    result != None
		    and not this.solutionAlreadyFound(result)
		    and not this.isDynamicSol(result)
		):
		    this.results.append(result)
		    maxIter = this.setMaxIter()
		    print '(thread %d) %s:' % (
			    this.threadId,
			    time.strftime("%y%m%d %H%M%S", time.localtime())
			),
		    print 'added new result nr %d (after %d new iterations)' % (
			    len(this.results),
			    nrOfIters
			)
	    except pygsl.errors.gsl_SingularityError:
		pass
	    except pygsl.errors.gsl_NoProgressError:
		pass
	    except pygsl.errors.gsl_JacobianEvaluationError:
		pass
	    testValue = this.randTestvalue()
	    nrOfIters = nrOfIters + 1
	    if nrOfIters >= this.stopAfter:
		# always write the result, even when empty, so it is known how
		# many iterations were done (without finding a result)
		f = open(filename, 'w')
		f.write('# edgeLengths = %s\n' % str(this.edgeLengths))
		f.write('# edgeAlternative = %s\n' % Stringify[this.edgeAlternative])
		if len(this.edgeLengths) > 4:
		    f.write('# oppEdgeAlternative = %s\n' % Stringify[this.oppEdgeAlternative])
		f.write('# fold = %s\n' % Fold(this.fold))

		# filter results. This is needed since the filter changed after
		# having found many solutions.
		# Also split in results and results_refl:
		cp_results = this.results[:]
		this.results = [] # for this.solutionAlreadyFound(result)
		results      = []
		results_refl = []
		for result in cp_results:
		    this.cleanupResult(result, len(result))
		    #print 'sols checked', len(this.results)
		    if not this.solutionAlreadyFound(result):
			# register result handled for this.solutionAlreadyFound
			this.results.append(result)
			# check if this value is (still) valid. This check is
			# done since the script is under development all the
			# time.  It is easier to throw an solution that appeared
			# to be invalid, then to start over the whole search
			# again...
			try:
			    if len(this.edgeLengths) == 4:
				if this.symmetry == Symmetry.A4xI:
				    chk = FoldedRegularHeptagonsA4xI(result,
					{
					    Param.tri_fill: this.edgeAlternative,
					    Param.edge_len: this.edgeLengths,
					    Param.h_fold:   this.fold
					}
				    )
				else:
				    chk = FoldedRegularHeptagonsS4(result,
					{
					    Param.tri_fill: this.edgeAlternative,
					    Param.edge_len: this.edgeLengths,
					    Param.h_fold:   this.fold,
					    Param.refl_max_angle: False # TODO, dyn set
					}
				    )
			    else:
				chk = FoldedRegularHeptagonsA4(result,
				    {
					Param.tri_fill: this.edgeAlternative,
					Param.opp_fill: this.oppEdgeAlternative,
					Param.edge_len: this.edgeLengths,
					Param.h_fold:   this.fold
				    }
				)
			except IndexError:
			    print 'Ooops while working on', filename
			    raise

			isEq = True
			# check if the solution is valid (a solution)
			for i in range(len(chk)):
			    # apparently the precision is bigger then
			    # 1e^precision: use a factor...
			    if not eq(chk[i], 0., 10 * this.prec_delta):
				print '|', chk[i], '| >', this.prec_delta
				isEq = False
				break
			if isEq:
			    if len(this.edgeLengths) <= 4:
				results_refl.append(result)
			    elif (
				(
				    eq(result[4], 0.0) or
				    eq(result[4], numx.pi/4) or
				    eq(result[4], -numx.pi/4) or
				    eq(result[4], numx.pi/2) or
				    eq(result[4], -numx.pi/2) or
				    eq(result[4], numx.pi) or
				    eq(result[4], -numx.pi)
				) and (
				    len(result) == 5 or (
					len(result) == 7 and
					eq(result[2], result[5], 1e-12) and
					eq(result[3], result[6], 1e-12)
				    )
				)
			    ):
				results_refl.append(result)
			    else:
				results.append(result)
			else:
			    print 'Throwing invalid solution:', result
		    else:
			print 'Throwing doublet:', result

		f.write('# %s: ' % time.strftime(
			"%y%m%d %H%M%S", time.localtime())
		    )
		f.write('%d (+%d) solutions found\n' % (
				len(results), len(results_refl)))
		f.write('iterations = %d\n' % (nrOfIters + prev_iterations))
		if len(this.edgeLengths) != 4:
		    f.write('results = [\n')
		    for r in results:
			f.write(this.sol7 % (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
		if len(this.edgeLengths) == 4:
		    # set angle centrally
		    # TODO handle min and max
		    if this.edgeAlternative & twist_bit == twist_bit and (
			    this.symmetry == Symmetry.A4xI
		    ):
			angle = numx.pi/4
		    else:
			angle = 0.0
		    f.write('results = [\n')
		    for r in results_refl:
			f.write(this.sol5 % (r[0], r[1], r[2], r[3], angle))
		elif this.symmetricEdges():
		    f.write(']\n')
		    # close this file open the relective file:
		    f.write('# for results_refl, see %s\n' % refl_filename)
		    f.close()
		    f = open(refl_filename, 'w')
		    f.write('# edgeLengths = %s\n' % str(this.edgeLengths))
		    f.write('# edgeAlternative = %s\n' % Stringify[this.edgeAlternative])
		    f.write('# fold = %s\n' % Fold(this.fold))
		    f.write('# %s: ' % time.strftime(
			    "%y%m%d %H%M%S", time.localtime())
			)
		    f.write('%d solutions found\n' % (len(results_refl)))
		    f.write('iterations = %d\n' % (nrOfIters + prev_refl_iterations))
		    f.write('results = [\n')
		    for r in results_refl:
			f.write(this.sol5 % (r[0], r[1], r[2], r[3], r[4]))
		else:
		    for r in results_refl:
			f.write(this.sol7 % (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
		f.write(']\n')
		f.close()
		print '(thread %d) %s:' % (
			this.threadId,
			time.strftime("%y%m%d %H%M%S", time.localtime())
		    ),
		if len(this.edgeLengths) == 4:
		    print len(results_refl),
		else:
		    print len(results),
		    print '(+%d)' % (len(results_refl)),
		print 'results written to',
		if len(this.edgeLengths) == 4:
		    print filename
		elif this.symmetricEdges():
		    print '%s (%s)' % (filename, refl_filename)
		else:
		    print filename
		break

if __name__ == '__main__':
    import Geom3D
    import sys
    import os

    def testOneSolution(symGrp):

	if symGrp == Symmetry.A4xI:
	    #T  = 2.45
	    #a  = Geom3D.Deg2Rad * 40
	    #b0 = Geom3D.Deg2Rad * 25
	    #g0 = Geom3D.Deg2Rad * 27
	    #tmp = numx.array((T, a, b0, g0))
	    tmp = numx.array((3., 0., 0.0, 0.0))
	    print 'input values: \n [',
	    for t in tmp: print t, ',',
	    print ']'
	    print FoldedRegularHeptagonsA4xI(tmp,
		    {
			Param.tri_fill: TriangleAlt.star1loose,
			Param.edge_len: [0., 0., 0., 0.],
			Param.h_fold:   Fold.w
		    }
		)
	if symGrp == Symmetry.A4:
	    T  = 2.3
	    a  = Geom3D.Deg2Rad * 30
	    b0 = Geom3D.Deg2Rad * 60
	    g0 = Geom3D.Deg2Rad * 50
	    d  = Geom3D.Deg2Rad * 40
	    b1 = Geom3D.Deg2Rad * 50
	    g1 = Geom3D.Deg2Rad * 100
	    tmp = numx.array((T, a, b0, g0, d, b1, g1))
	    tmp = [2.42367662112328, 0.73523867591239, -0.95915637221717, -1.30440374966920, 0.00000000000000, -0.95915637221717, g1]
	    print 'input values: \n [',
	    for t in tmp: print t, ',',
	    print ']'
	    print FoldedRegularHeptagonsA4(tmp,
		    {
			Param.tri_fill: TriangleAlt.star1loose,
			Param.opp_fill: TriangleAlt.strip1loose,
			Param.edge_len: [0., 0., 0., 0., 0., 0., 0.],
			Param.h_fold:   Fold.w
		    }
		)
	elif symGrp == Symmetry.S4xI:
	    #T  = 3.
	    #a  = Geom3D.Deg2Rad * 30
	    #b0 = Geom3D.Deg2Rad * 60
	    #g0 = Geom3D.Deg2Rad * 50
	    #d  = Geom3D.Deg2Rad * 40
	    #b1 = Geom3D.Deg2Rad * 50
	    #g1 = Geom3D.Deg2Rad * 100
	    #tmp = numx.array((T, a, b0, g0, d, b1, g1))
	    tmp = numx.array((3., 0., 0.0, 0.0))
	    print 'input values: \n [',
	    for t in tmp: print t, ',',
	    print ']'
	    print FoldedRegularHeptagonsS4(tmp,
		{
		    Param.tri_fill: TriangleAlt.twisted,
		    Param.edge_len: [0., 0., 0., 0.],
		    Param.h_fold:   Fold.trapezium,
		    Param.refl_max_angle: False # TODO, dyn set
		}
	    )

    if sys.argv[1] == '-1':
	testOneSolution(sys.argv[2])
	sys.exit(0)

    def tstDynamicSolutions():
	passed = True
	tst = RandFindMultiRootOnDomain(
	    [
		    [-2., 3.],             # Translation
		    [-numx.pi, numx.pi],   # angle alpha
		    [-numx.pi, numx.pi],   # fold 1 beta0
		    [-numx.pi, numx.pi],   # fold 2 gamma0
		    [0,        numx.pi/4], # delta: around z-axis
		    [-numx.pi, numx.pi],   # fold 1 beta1
		    [-numx.pi, numx.pi],   # fold 2 gamma1
		],
	    Symmetry.A4,
	    edgeAlternative    = TriangleAlt.star1loose,
	    oppEdgeAlternative = TriangleAlt.star1loose,
	    fold               = Fold.w,
	    edgeLengths        = [0, 1, 0, 1, 1, 0, 1],
	    dynSols            = dynamicSols,
	)
	chkDynSols = [
	    [2.59691495774690, 0.37180029203870, -0.99159844699067, 0.0, 0.0, -0.99159844699067, 1.90],
	    [-2.39662854867090, -2.76044142453588, -2.28962724865982, 0.0, 0.0, -2.28962724865982, 4.30],
	    [-1.32969344523106, 2.93729908156380, 0.47840318769040, 0.3, 0.0, 0.47840318769040, -1.24666979460112],
	    [1.56791889743089, 0.07044231686021, -3.01397582234294, 0.3, 0.0, -3.01397582234294, -0.617],
	    [-1.48353635258086, 3.14159265358979, -2.17789038635323, 0.3, 2.00286242147445, 2.17789038635323, -0.3],
	    [1.48353635258086, 0.0, -2.17789038635323, 6.0, 1.13873023211535, 2.17789038635323, -6.0],
	    [-1.48353635258086, 3.14159265358979, 2.17789038635323, 0.0, -2.00286242147445, -2.17789038635323, -0.0],
	    [1.48353635258086, 0.0, 2.17789038635323, 0.3, -1.13873023211535, -2.17789038635323, -0.3],
	    [-1.79862645974663, 2.89384136702916, 2.66115365118573, 0.0, 2.22084886403160, 2.66115365118573, 1.16715894682047],
	    [1.79862645974663, 0.24775128656063, -2.66115365118573, 0.3, 0.92074378955819, -2.66115365118573, -1.46715894682047],
	    [-1.79862645974663, 2.89384136702916, 2.66115365118573, 0.3, -2.22084886403160, 2.66115365118573, 0.86715894682047],
	    [1.79862645974663, 0.24775128656063, -2.66115365118573, 0.0, -0.92074378955819, -2.66115365118573, -1.16715894682047],
	    [-1.93838678986755, -2.82756860983026, -0.78734965896067, 0.0, 1.35463810886690, -0.78734965896067, +1.53424315674435],
	    [1.93838678986755, -0.31402404375953, 0.78734965896067, 0.3, 1.78695454472289, 0.78734965896067, -1.83424315674435],
	    [-1.93838678986755, -2.82756860983026, -0.78734965896067, 0.0, -1.35463810886690, -0.78734965896067, +1.53424315674435],
	    [1.93838678986755, -0.31402404375953, 0.78734965896067, 0.0, -1.78695454472289, 0.78734965896067, -1.53424315674435],
	]
	for ds in chkDynSols:
	    if not tst.isDynamicSol(ds):
		print 'oops', ds, 'should be a dynamic solution'
		passed = False
	chkDynSols = [
	    [1.73117867469463, 0.46014030244326, -1.75383477143902, 3,4, -1.75383477143902, 6],
	    [1.73117867469463, -0.46014030244326, 1.75383477143902, 3,4, 1.75383477143902, 6],
	    [-1.73117867469463, -2.68145235114654, -1.75383477143902, 3,4, -1.75383477143902, 6],
	    [-1.73117867469463, 2.68145235114654, 1.75383477143902, 3,4, 1.75383477143902, 6],
	]
	tst.edgeLengths = [0, V2, 1, 0, V2, 1, 0]
	for ds in chkDynSols:
	    if not tst.isDynamicSol(ds):
		print 'oops', ds, 'should be a dynamic solution'
		passed = False
	tst.edgeLengths = [0, 1, 1, 0, 1, 1, 0]
	for ds in chkDynSols:
	    if not tst.isDynamicSol(ds):
		print 'oops', ds, 'should be a dynamic solution'
		passed = False
	chkDynSols = [
	    [1.48353635258086, 0, 2, 3, 4, 5, 6],
	    [-1.48353635258086, 3.14159265358979, 2, 3, 4, 5, 6],
	    [1.48353635258086, 0.0, 2.177, 0.3, -1.1387, -2.17789, -0.3],
	]
	tst.edgeLengths = [0, 1, 0, 1, 1, 0, 1]
	tst.fold = Fold.star
	for ds in chkDynSols:
	    if not tst.isDynamicSol(ds):
		print 'oops', ds, 'should be a dynamic solution'
		passed = False
	tst.fold = Fold.w
	chkNoDynSols = [
	    [1.48353635258086, 0.0, 2.177, 0.3, -1.1387, -2.17789, -0.3],
	    [-2.59691495774690, 0.37180029203870, -0.99159844699067, 0.0, 0.0, -0.99159844699067, 1.90],
	    [-1.73117867469463, 0.46014030244326, -1.75383477143902, 3,4, -1.75383477143902, 6],
	    [-1.73117867469463, -0.46014030244326, 1.75383477143902, 3,4, 1.75383477143902, 6],
	    [-1.73117867469463, 2.68145235114654, -1.75383477143902, 3,4, -1.75383477143902, 6],
	    [-1.73117867469463, 2.68145235114654, 1.75383477143902, 3,4, -1.75383477143902, 6],
	]
	for edgeL in [[0, V2, 1, 0, V2, 1, 0], [0, 1, 1, 0, 1, 1, 0]]:
	    tst.edgeLengths = edgeL
	    for ds in chkNoDynSols:
		if tst.isDynamicSol(ds):
		    print 'oops', ds, "shouldn't be a dynamic solution"
		    passed = False
	return passed

    printStatus = False

    def randBatchA4(continueAfter = 100, nrThreads = 1, edgeLs = [],
				dynSols = None, precision = 14, outDir = "./"):
	folds = [Fold.star, Fold.w]
	# TODO: howto:
	#folds = [Fold.star]
	#folds = [Fold.w]
	#folds = [Fold.trapezium]
	ta = TriangleAlt()
	#edgeAlts = [t for t in ta]
	edgeAlts = []
	for t in ta:
	    if t & rot_bit == 0:
		edgeAlts.append(t)
	#oppEdgeAlts = [t for t in ta]
	oppEdgeAlts = edgeAlts[:]
	dom = [
	    [-3., 4.],             # Translation
	    [-numx.pi, numx.pi],   # angle alpha
	    [-numx.pi, numx.pi],   # fold 1 beta0
	    [-numx.pi, numx.pi],   # fold 2 gamma0
	    [0,        numx.pi/4], # delta: around z-axis
	    [-numx.pi, numx.pi],   # fold 1 beta1
	    [-numx.pi, numx.pi],   # fold 2 gamma1
	]
	rndT = [None for j in range(nrThreads)]
	i = 0
	if edgeLs == [] or folds == [] or edgeAlts ==[] or oppEdgeAlts == []:
	    print 'Warning: empty search specified, bailing out'
	    return
	while True:
	    for edges in edgeLs:
		for fold in folds:
		    for ea in edgeAlts:
			for oea in oppEdgeAlts:
			    # loose_bit must be the same for both:
			    if (
				ea & loose_bit == loose_bit and
				oea & loose_bit == loose_bit
			    ) or (
				ea & loose_bit == 0 and
				oea & loose_bit == 0
			    ):
				print '====set up thread %d===' % i
				rndT[i] = RandFindMultiRootOnDomain(dom,
				    Symmetry.A4,
				    threadId           = i,
				    edgeAlternative    = ea,
				    oppEdgeAlternative = oea,
				    edgeLengths        = edges,
				    dynSols            = dynSols,
				    fold               = fold,
				    precision          = precision,
				    method             = Method.hybrids,
				    outDir             = outDir
				)
				rndT[i].stopAfter = continueAfter
				rndT[i].start()
				i = i + 1
				if (i == nrThreads):
				    for j in range(nrThreads):
					rndT[j].join()
				    print '===threads finished===='
				    i = 0

    pre_edgeLs_A4 = [
	[0., 0., 0., 0., 0., 0., 0.],

	[0., 0., 0., 1., 0., 0., 1.],
		# should give solutions around
		#	T=1.60, (0, -116, -16) for
		#		parallel fold and twisted strip

	[0., 0., 1., 0., 0., 1., 0.],

	[0., 0., 1., 1., 0., 1., 1.],

	[0., 1., 0., 0., 1., 0., 0.],

	[0., 1., 0., 1., 0., 1., 0.], # no sols. Check again..
	[0., 1., 0., 1., 1., 0., 1.],

	[0., 1., 1., 0., 1., 1., 0.],

	[1., 0., 0., 0., 0., 0., 0.],

	[1., 0., 0., 1., 0., 0., 1.],

	[1., 0., 1., 0., 0., 1., 0.], # only hepts
		# it seems that
		# frh-roots-1_0_1_0_0_1_0-fld_w.0-shell-opp_shell.py
		# needs to find nr 11 (has 10 now)
	[1., 0., 1., 0., 0., 1., 0.],
	[1., 0., 1., 0., 0., 1., 1.], # 16 triangles (0)
	[1., 0., 1., 0., 1., 0., 0.], # no sols
	[1., 0., 1., 0., 1., 0., 1.], # 16 triangles (1)
	[1., 0., 1., 0., 1., 1., 0.], # 24 triangles (0)
	[1., 0., 1., 0., 1., 1., 1.], # 40 triangles (0)

	[1., 0., 1., 1., 0., 1., 0.], # 16 triangles (3)
	[1., 0., 1., 1., 0., 1., 1.], # 32 triangles (1)
	[1., 0., 1., 1., 1., 1., 0.], # 40 triangles (2)

	[1., 1., 0., 0., 1., 0., 0.],

	[1., 1., 0., 1., 0., 0., 0.], # for rot 0
	[1., 1., 0., 1., 0., 0., 1.], # for rot 0
	[1., 1., 0., 1., 0., 1., 0.], # 16 triangles (1)
	[1., 1., 0., 1., 0., 1., 1.], # 32 triangles (0)

	[1., 1., 1., 0., 0., 1., 0.], # 24 triangles (1)
	[1., 1., 1., 0., 0., 1., 1.], # 40 triangles (3)
	[1., 1., 1., 0., 1., 0., 0.], # no sols
	[1., 1., 1., 0., 1., 1., 0.], # no O3's: 48 triangles

	[1., 1., 1., 1., 0., 1., 0.], # 40 triangles (1)
	[1., 1., 1., 1., 1., 1., 0.], # 64 triangles (0)
	[1., 1., 1., 1., 1., 1., 1.], # all equilateral

	[0., V2, 1., 0., V2, 1., 0.], # 12 folded squares
	[1., V2, 1., 0., V2, 1., 0.], # 24 folded squares
    ]

    dynamicSols_A4 = [
	# TODO: important add edge lengths!!!
	{
	    # here is an example of where it is important to define the
	    # sol_vector. Since it can be that solutions with different edge
	    # lengths have non-dynamic solutions for which the translation
	    # and the dihedral angle have the values below.
	    'edgeAlternative': [TriangleAlt.star1loose],
	    'oppEdgeAlternative': [TriangleAlt.star1loose],
	    'fold': [Fold.star],
	    'sol_vector': [[0, 1, 0, 1, 1, 0, 1]],
	    'set_vector': [
		    {
			0: 1.48353635258086,
			1: 0.0,
		    },{
			0: -1.48353635258086,
			1: 3.14159265358979,
		    }
		]
	},{
	    'edgeAlternative': [TriangleAlt.star1loose],
	    'oppEdgeAlternative': [TriangleAlt.star1loose],
	    'fold': [Fold.w],
	    'sol_vector': [[0, 1, 0, 1, 1, 0, 1]],
	    'set_vector': [
		{
		    0: 2.59691495774690,
		    1: 0.37180029203870,
		    2: -0.99159844699067,
		    4: 0.0,
		    5: -0.99159844699067,
		},{
		    0: -2.39662854867090,
		    1: -2.76044142453588,
		    2: -2.28962724865982,
		    4: 0.0,
		    5: -2.28962724865982,
		},{
		    0: -1.32969344523106,
		    1: 2.93729908156380,
		    2: 0.47840318769040,
		    4: 0.0,
		    5: 0.47840318769040,
		},{
		    0: 1.56791889743089,
		    1: 0.07044231686021,
		    2: -3.01397582234294,
		    4: 0.0,
		    5: -3.01397582234294,
		},{
		    0: -1.48353635258086,
		    1: 3.14159265358979,
		    2: -2.17789038635323,
		    4: 2.00286242147445,
		    5: 2.17789038635323,
		},{
		    0: 1.48353635258086,
		    1: 0.0,
		    2: -2.17789038635323,
		    4: 1.13873023211535,
		    5: 2.17789038635323,
		},{
		    0: -1.48353635258086,
		    1: 3.14159265358979,
		    2: 2.17789038635323,
		    4: -2.00286242147445,
		    5: -2.17789038635323,
		},{
		    0: 1.48353635258086,
		    1: 0.0,
		    2: 2.17789038635323,
		    4: -1.13873023211535,
		    5: -2.17789038635323,
		},{
		    0: -1.79862645974663,
		    1: 2.89384136702916,
		    2: 2.66115365118573,
		    4: 2.22084886403160,
		    5: 2.66115365118573,
		},{
		    0: 1.79862645974663,
		    1: 0.24775128656063,
		    2: -2.66115365118573,
		    4: 0.92074378955819,
		    5: -2.66115365118573,
		},{
		    0: -1.79862645974663,
		    1: 2.89384136702916,
		    2: 2.66115365118573,
		    4: -2.22084886403160,
		    5: 2.66115365118573,
		},{
		    0: 1.79862645974663,
		    1: 0.24775128656063,
		    2: -2.66115365118573,
		    4: -0.92074378955819,
		    5: -2.66115365118573,
		},{
		    0: -1.93838678986755,
		    1: -2.82756860983026,
		    2: -0.78734965896067,
		    4: 1.35463810886690,
		    5: -0.78734965896067,
		},{
		    0: 1.93838678986755,
		    1: -0.31402404375953,
		    2: 0.78734965896067,
		    4: 1.78695454472289,
		    5: 0.78734965896067,
		},{
		    0: -1.93838678986755,
		    1: -2.82756860983026,
		    2: -0.78734965896067,
		    4: -1.35463810886690,
		    5: -0.78734965896067,
		},{
		    0: 1.93838678986755,
		    1: -0.31402404375953,
		    2: 0.78734965896067,
		    4: -1.78695454472289,
		    5: 0.78734965896067,
		}
	    ]
	},{
	    'edgeAlternative': [
		TriangleAlt.star1loose, TriangleAlt.strip1loose],
	    'oppEdgeAlternative': [
		TriangleAlt.star1loose, TriangleAlt.strip1loose],
	    'fold': [Fold.w],
	    'sol_vector': [
		    [0, 1, 1, 0, 1, 1, 0],
		    [0, V2, 1, 0, V2, 1, 0]
	    ],
	    'set_vector': [
		{
		    0: 1.73117867469463,
		    1: 0.46014030244326,
		    2: -1.75383477143902,
		    5: -1.75383477143902,
		},{
		    0: 1.73117867469463,
		    1: -0.46014030244326,
		    2: 1.75383477143902,
		    5: 1.75383477143902,
		},{
		    0: -1.73117867469463,
		    1: -2.68145235114654,
		    2: -1.75383477143902,
		    5: -1.75383477143902,
		},{
		    0: -1.73117867469463,
		    1: 2.68145235114654,
		    2: 1.75383477143902,
		    5: 1.75383477143902,
		}
	    ]
	}
    ]

    def randBatchYxI(symGrp, continueAfter = 100, nrThreads = 1, edgeLs = [],
						precision = 14, outDir = "./"):
	folds = [
	    Fold.w,
	    Fold.star,
	    Fold.triangle,
	    Fold.trapezium,
	    Fold.parallel,
	]
	ta = TriangleAlt()
	edgeAlts = [t for t in ta]
	#edgeAlts = []
	#for t in ta:
	#    if t & rot_bit == 0:
	#        edgeAlts.append(t)
	edgeAlts = [ta.twisted] # for now for S4 # TODO set by cmd line
	if symGrp == Symmetry.A4xI:
	    T = [-2., 3.]
	elif symGrp == Symmetry.S4xI:
	    T = [-4., 4.8]
	else:
	    print 'Warning: unsupported symmetry group specified, bailing out'
	    return
	dom = [
	    T,                   # Translation
	    [-numx.pi, numx.pi], # angle alpha
	    [-numx.pi, numx.pi], # fold 1 beta
	    [-numx.pi, numx.pi], # fold 2 gamma
	]
	rndT = [None for j in range(nrThreads)]
	i = 0
	if edgeLs == [] or folds == [] or edgeAlts ==[]:
	    print 'Warning: empty search specified, bailing out'
	    return
	while True:
	    for edges in edgeLs:
		for fold in folds:
		    for ea in edgeAlts:
			print '====set up thread %d===' % i
			rndT[i] = RandFindMultiRootOnDomain(dom,
			    symGrp,
			    threadId           = i,
			    edgeAlternative    = ea,
			    oppEdgeAlternative = ea,
			    edgeLengths        = edges,
			    fold               = fold,
			    precision          = precision,
			    method             = Method.hybrids,
			    outDir             = outDir
			)
			rndT[i].stopAfter = continueAfter
			rndT[i].start()
			i = i + 1
			if (i == nrThreads):
			    for j in range(nrThreads):
				rndT[j].join()
			    print '===threads finished===='
			    i = 0

    pre_edgeLs_A4xI = [
	[0., 0., 0., 0.],
	[1., 0., 0., 0.],
	[0., 1., 0., 0.],
	[0., 0., 1., 0.],
	[0., 0., 0., 1.],
	[1., 1., 0., 0.],
	[1., 0., 1., 0.],
	[1., 0., 0., 1.],
	[0., 1., 1., 0.],
	[0., 1., 0., 1.],
	[0., 0., 1., 1.],
	[1., 1., 1., 0.],
	[1., 1., 0., 1.],
	[1., 0., 1., 1.],
	[0., 1., 1., 1.],
	[1., 1., 1., 1.],
    ]

    pre_edgeLs = {
	Symmetry.A4xI: pre_edgeLs_A4xI,
	Symmetry.A4  : pre_edgeLs_A4,
	Symmetry.S4xI: pre_edgeLs_A4xI,
    }
    dynamicSols = {
	Symmetry.A4xI: [],
	Symmetry.A4  : dynamicSols_A4,
	Symmetry.S4xI: [],
    }

    tstProg = False

    # Handle command line arguments:
    if len(sys.argv) <= 1:
	printUsage()
	sys.exit(-1)
    else:
	skipNext = False # for options that take arguments
	symGrp = '' # which symmetry group to search: '' means not read yet
	nr_iterations = 4000
	precision = 10
	outDir = "tst/frh-roots"
	list_pre_edgeLs = False
	def printUsage():
	    print 'Usage:'
	    print sys.argv[0], '[options] <symmetry group> [i0] [i1]'
	    print 'where options:'
	    print '     -h      : prints this help'
	    print '     -i <num>: number of iterations to use; default %d' % nr_iterations
	    print '     -l      : list the length of the predefined list'
	    print "     -o <out>: specifiy the output directory: don't use spaces; default"
	    print '               %s' % outDir
	    print '     -p <num>: precision, specify the amount of digits after the point; default'
	    print '               %d' % precision
	    print 'And'
	    print '    <symmetry group>: search solutions for the specified symmetry group. Valid'
	    print '                      values are "%s", "%s", "%s"' % (
			Symmtry.A4xI, Symmetry.A4, Symmetry.S4xI
		)
	    print '    [i0]: begin slice'
	    print '    [i1]: end slice'
	    print '        search using the specified slice from the predefined list'
	    print '        If nothing is specified the whole list is searched'
	    print '        If only i0 is specified the list is searched from that index'
	def errIfNoNxt(n):
	    if len(sys.argv) <= n + 1: # note incl the cmd line also
		printUsage()
		sys.exit(-1)
	for n in range(1, len(sys.argv)):
	    if skipNext:
		skipNext = False
	    elif sys.argv[n] == '-h':
		printUsage()
		sys.exit(0)
	    elif sys.argv[n] == '-i':
		errIfNoNxt(n)
		nr_iterations = int(sys.argv[n + 1])
		skipNext = True
	    elif sys.argv[n] == '-l':
		list_pre_edgeLs = True
	    elif sys.argv[n] == '-o':
		errIfNoNxt(n)
		outDir = sys.argv[n + 1]
		skipNext = True
	    elif sys.argv[n] == '-p':
		errIfNoNxt(n)
		precision = int(sys.argv[n + 1])
		skipNext = True
	    elif sys.argv[n] == '-t':
		tstProg = True
	    elif symGrp == '':
		if sys.argv[n] in [Symmetry.A4xI, Symmetry.A4, Symmetry.S4xI]:
		    symGrp = sys.argv[n]
		    edgeLs = pre_edgeLs[symGrp]
		    i = 0
		    j = len(edgeLs)
		else:
		    printUsage()
		    sys.exit(-1)
	    else:
		# last arguments slice i0, i1
		i = int(sys.argv[n])
		if len(sys.argv) > n + 1:
		    j = int(sys.argv[n + 1])
		else:
		    j = len(edgeLs)
		edgeLs = edgeLs[i:j]
		break

    if tstProg:
	if tstDynamicSolutions():
	    print 'test PASSED'
	else:
	    print 'test FAILED'
    else:
	if list_pre_edgeLs:
	    for (i, e) in zip(range(len(edgeLs)), edgeLs):
		print '%3d' % i, e
	    sys.exit(0)
	print 'Search solutions for symmetry group %s' % symGrp
	print 'Switch setup after %d randomly selected begin values' % (
							    nr_iterations)
	print 'Search slice [%d:%d]:' % (i, j)
	print 'Save solutions in:', outDir
	# TODO: specify fold by command line...
	for e in edgeLs:
	    print '  -', e
	if symGrp == Symmetry.A4xI or symGrp == Symmetry.S4xI:
	    randBatchYxI(symGrp, continueAfter = nr_iterations, nrThreads = 1,
			edgeLs = edgeLs, precision = precision, outDir = outDir)
	elif symGrp == SYmmetry.A4:
	    randBatchA4(continueAfter = nr_iterations, nrThreads = 1,
			    edgeLs = edgeLs,
			    dynSols = dynamicSols[symGrp],
			    outDir = outDir,
			    precision = precision)
