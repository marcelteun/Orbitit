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
import rgb
import Heptagons
import isometry
import Geom3D
import Scenes3D
from OpenGL.GL import *

import GeomTypes
from GeomTypes import Rot3      as Rot
from GeomTypes import HalfTurn3 as HalfTurn
from GeomTypes import Vec3      as Vec

Title = 'Polyhedra with Folded Regular Heptagons S4'

V2 = math.sqrt(2)

#                0
#   13                      12
#         6             1
#
# 11                           9
#
#       5                 2
#
#
#   10       4       3        8
#
#
#                         7
# There are 4 different edges to separate the triangles:
# a (V2-V7), b (V2-V8), c (V2-V9), and d (V9-V1)
# the first three have opposite alternatives:
# a' (V3-V8), b' (V3-V9) and c' (V1-V8)
# (there's no (V2-V12): V1-V9-V12 is the O3 triangle)
# This leads to 2^3 possible combinations,
# however the edge configuration a b' does not occur
# neither does b' c'
# This leaves 5 possible edge configurations:
class TrisAlt:
    # Note nrs should be different from above
    strip_1_loose     = 100
    strip_I           = 101
    strip_II          = 102
    star              = 103
    star_1_loose      = 104
    alt_strip_I       = 105
    alt_strip_II      = 106
    alt_strip_1_loose = 107
    # TODO:
    # for the o3 triangle there is another altenative as well: [0, 0', 0"]
    # for the square there exist 2 alts as well:
    # [0, 0', 0", 0'"] and [5, 5', 5", 5'"]
    # And there are combinations of these...
    def get(this, str):
	for k,v in Stringify.iteritems():
	    if v == str:
		return k
	return None

trisAlt = TrisAlt()

dyn_pos		=  Heptagons.dyn_pos
only_hepts	=  Heptagons.only_hepts
all_eq_tris	=  0
no_o3_tris	=  1
edge_1_1_V2_1	=  2
edge_1_V2_1_1	=  3
edge_V2_1_1_1	=  4
edge_V2_1_V2_1	=  5
squares_24	=  6
edge_0_1_1_1	=  7
edge_0_1_V2_1	=  8
tris_24		=  9
only_xtra_o3s	= 10
only_xtra_o3s	= 11
edge_1_1_0_1	= 12
edge_1_0_1_1	= 13
edge_V2_1_0_1	= 14
edge_V2_1_1_0	= 15
square_12	= 16
edge_0_V2_1_1   = 17

Stringify = {
    dyn_pos:		'Enable Sliders',
    no_o3_tris:		'48 Triangles',
    all_eq_tris:	'All 80 Triangles Equilateral',
    only_xtra_o3s:	'8 Triangles (O3)',
    edge_V2_1_0_1:	'8 Triangles and 12 Folded Squares',
    edge_0_1_V2_1:	'8 Triangles and 24 Folded Squares',
    edge_V2_1_V2_1:	'8 Triangles and 36 Folded Squares',
    square_12:		'12 Folded Squares',
    tris_24:		'24 Triangles',
    squares_24:		'24 Folded Squares',
    edge_V2_1_1_0:	'24 Triangles and 12 Folded Squares',
    edge_1_1_0_1:	'32 Triangles (24 + 8) I',
    edge_1_0_1_1:	'32 Triangles (24 + 8) II',
    edge_0_V2_1_1:	'32 Triangles and 12 Folded Squares',
    edge_1_1_V2_1:	'32 Triangles and 24 Folded Squares: I',
    edge_1_V2_1_1:	'32 Triangles and 24 Folded Squares: II',
    edge_0_1_1_1:	'56 Triangles',
    edge_V2_1_1_1:	'56 Triangles and 12 Folded Squares',
    only_hepts:		'Just Heptagons',
    trisAlt.strip_1_loose:	'Strip, 1 Loose ',
    trisAlt.strip_I:		'Strip I',
    trisAlt.strip_II:		'Strip II',
    trisAlt.star:		'Shell',
    trisAlt.star_1_loose:	'Shell, 1 Loose',
    trisAlt.alt_strip_I:	'Alternative Strip I',
    trisAlt.alt_strip_II:	'Alternative Strip II',
    trisAlt.alt_strip_1_loose:	'Alternative Strip, 1 loose',
}

def Vlen(v0, v1):
    x = v1[0] - v0[0]
    y = v1[1] - v0[1]
    z = v1[2] - v0[2]
    return (math.sqrt(x*x + y*y + z*z))

class Shape(Heptagons.FldHeptagonShape):
    def __init__(this, *args, **kwargs):
	o4_fld_0 = GeomTypes.Vec3([1, 0, 0])
	o4_fld_1 = GeomTypes.Vec3([0, 1, 1])
        Heptagons.FldHeptagonShape.__init__(this,
            isometry.S4(setup = {'o4axis0': o4_fld_0, 'o4axis1': o4_fld_1}),
            name = 'FoldedRegHeptS4xI'
        )
	this.edgeAlternative = trisAlt.strip_1_loose
	this.posAngleMin = 0
	this.posAngleMax = math.pi/2
	this.posAngle = math.pi/4
	this.o4_fld_0 = o4_fld_0
	this.o4_fld_1 = o4_fld_1
	this.height = 3.9
	this.initArrs()
	this.setV()

    def getStatusStr(this):
        #angle = Geom3D.Rad2Deg * this.dihedralAngle
        s = Heptagons.FldHeptagonShape.getStatusStr(this)
        if this.updateShape:
            #print 'getStatusStr: forced setV'
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
	return s
	# TODO
        Vs = this.getBaseVertexProperties()['Vs']
        if this.edgeAlternative == trisAlt.strip_1_loose:
            aLen = Vlen(Vs[2], Vs[7])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[1], Vs[9])
        elif this.edgeAlternative == trisAlt.strip_I:
            aLen = Vlen(Vs[3], Vs[8])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[1], Vs[9])
        elif this.edgeAlternative == trisAlt.strip_II:
            aLen = Vlen(Vs[3], Vs[8])
            bLen = Vlen(Vs[3], Vs[9])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[1], Vs[9])
        elif this.edgeAlternative == trisAlt.star:
            aLen = Vlen(Vs[3], Vs[8])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[1], Vs[8])
            dLen = Vlen(Vs[1], Vs[9])
        elif this.edgeAlternative == trisAlt.star_1_loose:
            aLen = Vlen(Vs[2], Vs[7])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[1], Vs[8])
            dLen = Vlen(Vs[1], Vs[9])
        elif this.edgeAlternative == trisAlt.alt_strip_I:
            aLen = Vlen(Vs[3], Vs[8])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[2], Vs[14])
        elif this.edgeAlternative == trisAlt.alt_strip_II:
            aLen = Vlen(Vs[3], Vs[8])
            bLen = Vlen(Vs[3], Vs[9])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[2], Vs[14])
        elif this.edgeAlternative == trisAlt.alt_strip_1_loose:
            aLen = Vlen(Vs[2], Vs[7])
            bLen = Vlen(Vs[2], Vs[8])
            cLen = Vlen(Vs[2], Vs[9])
            dLen = Vlen(Vs[2], Vs[14])
	else:
	    raise TypeError, 'Unknown edgeAlternative %s' % str(
		this.edgeAlternative)
        #tst:
        #aLen = Vlen(Vs[0], [(Vs[6][i] + Vs[1][i]) / 2 for i in range(3)])
        #bLen = Vlen([(Vs[5][i] + Vs[2][i]) / 2 for i in range(3)], [(Vs[6][i] + Vs[1][i]) / 2 for i in range(3)])
        s = '%s, |a|: %02.2f, |b|: %02.2f, |c|: %02.2f, |d|: %02.2f' % (
                s, aLen, bLen, cLen, dLen
            )

        return s

    def setV(this):

        #
	#      8      7                  16 = 2"
        #         o4          0
        #                                   11 = 1"
        #       9      6             1   o3
        #                                           15 = 2'
        #                                   10 = 1'
        #
        #            5                 2
        #
        #
        #       14        4       3        13 = 0'
        #
        #
        #                              12 = 6'

	this.posHeptagon()
	Vs = this.heptagon.Vs[:]
	o4fld = Rot(axis = this.o4_fld_1, angle = GeomTypes.qTurn)
	Vs.append(o4fld * Vs[-1])				# Vs[7]
	Vs.append(o4fld * Vs[-1])				# Vs[8]
	Vs.append(o4fld * Vs[-1])				# Vs[9]
	o3axis = GeomTypes.Vec3([1, 0, V2])
	o3fld = Rot(axis = o3axis, angle = GeomTypes.tTurn)
	Vs.append(o3fld * Vs[1])				# Vs[10]
	Vs.append(o3fld * Vs[-1])				# Vs[11]
	Vs.append(Vec([-Vs[5][0], -Vs[5][1], Vs[5][2]]))        # Vs[12]
	Vs.append(o3fld * Vs[0])				# Vs[13]
	Vs.append(Vec([-Vs[13][0], -Vs[13][1], Vs[13][2]]))     # Vs[14]
	Vs.append(o3fld * Vs[2])				# Vs[10]
	Vs.append(o3fld * Vs[-1])				# Vs[11]
        #Rr = Rot(axis = Vec([ 1, 1, 1]), angle = GeomTypes.tTurn)
        #Rl = Rot(axis = Vec([-1, 1, 1]), angle = -GeomTypes.tTurn)
        #Vs.append(Vec([Vs[2][0], -Vs[2][1], Vs[2][2]]))        # Vs[7]
        #Vs.append(Rr * Vs[0])                                  # Vs[8]
        #Vs.append(Rr * Vs[1])                                  # Vs[9]
        #Vs.append(Rl * Vs[0])                                  # Vs[10]
        #Vs.append(Rl * Vs[6])                                  # Vs[11]
        ## V12 and V13 are the centres of the triangle on the O3 axis.
        ## for V12 the O3 axis is (1, 1, 1). So we need to find the n*(1, 1, 1)
        ## that lies in the face. This can found by projecting V12 straight onto
        ## this axis, or we can rotate 180 degrees and take the average:
        #halfTurn = HalfTurn(Vec([1, 1, 1]))
        #Vs.append((Vs[1] + halfTurn*Vs[1]) / 2)                # Vs[12]
        #halfTurn = HalfTurn(Vec([-1, 1, 1]))
        #Vs.append((Vs[6] + halfTurn*Vs[6]) / 2)                # Vs[13]
        #Vs.append(Rr * Vs[2])                                  # Vs[14]
        #Vs.append(Rl * Vs[5])                                  # Vs[15]
        #halfTurn = HalfTurn(Vec([1, 1, 1]))
        #Vs.append((Vs[2] + halfTurn*Vs[2]) / 2)                # Vs[16]
        #halfTurn = HalfTurn(Vec([-1, 1, 1]))
        #Vs.append((Vs[5] + halfTurn*Vs[5]) / 2)                # Vs[17]
	Es = []
        Fs = []
        Fs.extend(this.heptagon.Fs) # use extend to copy the list to Fs
        Es.extend(this.heptagon.Es) # use extend to copy the list to Fs
        colIds = [0 for f in Fs]
        if this.addXtraFs:
	    Fs.extend(this.o3triFs[this.edgeAlternative]) # eql triangles
	    Es.extend(this.o3triEs[this.edgeAlternative])
            colIds.extend([3, 3])
	    if (not this.onlyRegFs):
		Fs.extend(this.triFs[this.edgeAlternative])
		colIds.extend(this.triColIds[this.edgeAlternative])
		Es.extend(this.triEs[this.edgeAlternative])
        this.setBaseVertexProperties(Vs = Vs)
        this.setBaseEdgeProperties(Es = Es)
        this.setBaseFaceProperties(Fs = Fs, colors = (this.theColors, colIds))
        this.showBaseOnly = not this.applySymmetry
        this.updateShape = False

    def initArrs(this):
        this.triFs = {
                trisAlt.strip_1_loose: [
                    [2, 3, 12], [2, 12, 13],
                    [2, 13, 10], [5, 9, 14],
                    [1, 2, 10], [5, 6, 9],
                ],
                trisAlt.strip_I: [
                    [2, 3, 13], [4, 5, 14],
                    [2, 13, 10], [5, 9, 14],
                    [1, 2, 10], [5, 6, 9],
                ],

                trisAlt.strip_II: [
                    [3, 13, 10], [4, 9, 14],
                    [2, 3, 10], [4, 5, 9],
                    [1, 2, 10], [5, 6, 9],
                ],
                trisAlt.star: [
                    [2, 3, 13], [4, 5, 14],
                    [1, 2, 13], [5, 6, 14],
                    [1, 13, 10], [6, 9, 14]
                ],
                trisAlt.star_1_loose: [
                    [2, 3, 12], [2, 12, 13],
                    [1, 2, 13], [5, 6, 14],
                    [1, 13, 10], [6, 9, 14]
                ],
                trisAlt.alt_strip_I: [
                    [2, 3, 13], [4, 5, 14],
                    [2, 13, 10], [5, 9, 14],
                    [2, 15, 10], [6, 9, 5]
                ],
                trisAlt.alt_strip_II: [
                    [3, 13, 10], [4, 9, 14],
                    [2, 3, 10], [4, 5, 9],
                    [2, 15, 10], [6, 9, 5]
                ],
                trisAlt.alt_strip_1_loose: [
                    [2, 3, 12], [2, 12, 13],
                    [2, 13, 10], [5, 9, 14],
                    [2, 15, 10], [6, 9, 5]
                ],
            }

        #
	#      8      7                  16 = 2"
        #         o4          0
        #                                   11 = 1"
        #       9      6             1   o3
        #                                           15 = 2'
        #                                   10 = 1'
        #
        #            5                 2
        #
        #
        #       14        4       3        13 = 0'
        #
        #
        #                              12 = 6'

        this.o3triFs = {
                trisAlt.strip_1_loose:		[[6, 7, 8, 9], [1, 10, 11]],
                trisAlt.strip_I:		[[6, 7, 8, 9], [1, 10, 11]],
                trisAlt.strip_II:		[[6, 7, 8, 9], [1, 10, 11]],
                trisAlt.star:			[[6, 7, 8, 9], [1, 10, 11]],
                trisAlt.star_1_loose:		[[6, 7, 8, 9], [1, 10, 11]],
                trisAlt.alt_strip_I:		[[6, 7, 8, 9], [2, 15, 16]],
                trisAlt.alt_strip_II:		[[6, 7, 8, 9], [2, 15, 16]],
                trisAlt.alt_strip_1_loose:	[[6, 7, 8, 9], [2, 15, 16]],
	    }
        this.triColIds = {
                trisAlt.strip_1_loose:		[1, 2, 1, 1, 2, 2],
                trisAlt.strip_I:		[1, 2, 2, 1, 1, 2],
                trisAlt.strip_II:		[1, 2, 2, 1, 1, 2],
                trisAlt.star:			[1, 2, 2, 1, 1, 2],
                trisAlt.star_1_loose:		[1, 2, 1, 1, 2, 2],
                trisAlt.alt_strip_I:		[1, 2, 2, 1, 1, 2],
                trisAlt.alt_strip_II:		[1, 2, 2, 1, 1, 2],
                trisAlt.alt_strip_1_loose:	[1, 2, 1, 1, 2, 2],
            }
        this.triEs = {
                trisAlt.strip_1_loose: [
                    2, 12, 2, 13, 2, 10,
                    5, 14, 5, 9,
                ],
                trisAlt.strip_I: [
                    3, 13, 2, 13, 2, 10,
                    5, 14, 5, 9,
                ],
                trisAlt.strip_II: [
                    3, 13, 3, 10, 2, 10,
                    4, 9, 5, 9,
                ],
                trisAlt.star: [
                    3, 13, 2, 13, 1, 13,
                    5, 14, 6, 14,
                ],
                trisAlt.star_1_loose: [
                    2, 12, 2, 13, 1, 13,
                    5, 14, 6, 14,
                ],
                trisAlt.alt_strip_I: [
                    3, 13, 2, 13, 2, 10,
                    5, 14, 5, 9,
                ],
                trisAlt.alt_strip_II: [
                    3, 13, 3, 10, 2, 10,
                    4, 9, 5, 9,
                ],
                trisAlt.alt_strip_1_loose: [
                    2, 12, 2, 13, 2, 10,
                    5, 14, 5, 9,
                ],
            }
        this.o3triEs = {
                trisAlt.strip_1_loose:		[6, 7, 1, 10],
                trisAlt.strip_I:		[6, 7, 1, 10],
                trisAlt.strip_II:		[6, 7, 1, 10],
                trisAlt.star:			[6, 7, 1, 10],
                trisAlt.star_1_loose:		[6, 7, 1, 10],
                trisAlt.alt_strip_I:		[6, 7, 2, 15],
                trisAlt.alt_strip_II:		[6, 7, 2, 15],
                trisAlt.alt_strip_1_loose:	[6, 7, 2, 15],
            }

class CtrlWin(Heptagons.FldHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
	edgeChoicesList = [
	    Stringify[trisAlt.strip_1_loose],
	    Stringify[trisAlt.strip_I],
	    Stringify[trisAlt.strip_II],
	    Stringify[trisAlt.star],
	    Stringify[trisAlt.star_1_loose],
	    Stringify[trisAlt.alt_strip_I],
	    Stringify[trisAlt.alt_strip_II],
	    Stringify[trisAlt.alt_strip_1_loose],
	]
	nr_of = len(edgeChoicesList)
	edgeChoicesListItems = [
	    trisAlt.get(edgeChoicesList[i]) for i in range(nr_of)
	]
	Heptagons.FldHeptagonCtrlWin.__init__(this,
	    shape, (745, 765), canvas,
	    4, # maxHeigth
	    edgeChoicesList, edgeChoicesListItems,
	    [ # prePosLst
		Stringify[only_hepts],
		Stringify[only_xtra_o3s],
		Stringify[square_12],
		Stringify[edge_V2_1_0_1],
		Stringify[tris_24],
		Stringify[squares_24],
		Stringify[edge_1_1_0_1],
		Stringify[edge_1_0_1_1],
		Stringify[edge_0_1_V2_1],
		Stringify[edge_V2_1_1_0],
		Stringify[edge_V2_1_V2_1],
		Stringify[edge_0_V2_1_1],
		Stringify[no_o3_tris],
		Stringify[edge_0_1_1_1],
		Stringify[edge_1_1_V2_1],
		Stringify[edge_1_V2_1_1],
		Stringify[edge_V2_1_1_1],
		Stringify[all_eq_tris],
		Stringify[dyn_pos],
	    ],
	    Stringify,
	    *args, **kwargs
	)

    def isntSpecialPos(this, sel):
	#TODO
	return True

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
