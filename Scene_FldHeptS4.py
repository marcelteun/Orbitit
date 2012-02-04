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
import re
import rgb
import Heptagons
import isometry
import Geom3D
import Scenes3D

from glob import glob
from OpenGL.GL import *

import GeomTypes
from GeomTypes import Rot3      as Rot
from GeomTypes import HalfTurn3 as HalfTurn
from GeomTypes import Vec3      as Vec

Title = 'Polyhedra with Folded Regular Heptagons and Cube Symmetry'

trisAlt = Heptagons.TrisAlt()
trisAlt.baseKey[trisAlt.refl_1]        = True
trisAlt.baseKey[trisAlt.refl_2]        = True
#trisAlt.baseKey[trisAlt.twist_strip_I] = True

dyn_pos		=  Heptagons.dyn_pos
open_file	=  Heptagons.open_file
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

prePosStrToReflFileStrMap = {
    only_hepts:	'1_0_1_0',
}
prePosStrToFileStrMap = {
    # symmetric edge lengths:
    only_hepts:	'1_0_1_0_0_1_0',
}

def Vlen(v0, v1):
    x = v1[0] - v0[0]
    y = v1[1] - v0[1]
    z = v1[2] - v0[2]
    return (math.sqrt(x*x + y*y + z*z))

V2 = math.sqrt(2)
V3 = math.sqrt(3)
hV2 = V2/2

o4_fld_0 = GeomTypes.Vec3([1, 0, 0])
o4_fld_1 = GeomTypes.Vec3([0, 1, 1])
isomS4 = isometry.S4(setup = {'o4axis0': o4_fld_0, 'o4axis1': o4_fld_1})
o4fld = Rot(axis = o4_fld_1, angle = GeomTypes.qTurn)
isomO4 = isometry.C4(setup = {'axis': o4_fld_1})

o3axis = GeomTypes.Vec3([1/V3, 0, V2/V3])
o3fld = Rot(axis = o3axis, angle = GeomTypes.tTurn)
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
    for subSet, i in zip(colQuotientSet, range(len(colQuotientSet))):
	if isom in subSet:
	    heptColPerIsom.append(([useRgbCols[i]], []))
	    break;

class Shape(Heptagons.FldHeptagonShape):
    def __init__(this, *args, **kwargs):
	heptagonsShape = Geom3D.IsometricShape(
	    Vs = [], Fs = [], directIsometries = isomS4,
            name = 'FoldedHeptagonsS4',
	    recreateEdges = False
        )
	xtraTrisShape = Geom3D.IsometricShape(
	    Vs = [], Fs = [], directIsometries = isomS4,
            name = 'xtraTrisS4',
	    recreateEdges = False
        )
	trisO3Shape = Geom3D.SymmetricShape(
	    Vs = [], Fs = [],
	    finalSym = isomS4, stabSym = isomO3,
	    colors = [([rgb.cyan[:]], [])],
            name = 'o3TrisS4',
	    recreateEdges = False
        )
	trisO4Shape = Geom3D.SymmetricShape(
	    Vs = [], Fs = [],
	    finalSym = isomS4, stabSym = isomO4,
	    colors = [([rgb.cyan[:]], [])],
            name = 'o4SquareS4',
	    recreateEdges = False
        )
	Heptagons.FldHeptagonShape.__init__(this,
	    [heptagonsShape, xtraTrisShape, trisO3Shape, trisO4Shape],
	    4, 3,
            name = 'FoldedRegHeptS4xI'
        )
	this.heptagonsShape = heptagonsShape
	this.xtraTrisShape = xtraTrisShape
	this.trisO3Shape = trisO3Shape
	this.trisO4Shape = trisO4Shape
	this.posAngleMin = -math.pi/2
        this.posAngleMax = math.pi/2
	this.height = 3.9
        this.setEdgeAlternative(trisAlt.strip_1_loose, trisAlt.strip_1_loose)
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
        Vs = this.baseVs
	if this.inclReflections:
	    Es = this.triEs[this.edgeAlternative]
	    aLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
	    bLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
	    cLen = '%2.2f' % Vlen(Vs[Es[4]], Vs[Es[5]])
	    dLen = '%2.2f' % Vlen(Vs[Es[6]], Vs[Es[7]])
	else:
	    Es = this.triEs[this.edgeAlternative]
	    aLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
	    bLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
	    cLen = '%2.2f' % Vlen(Vs[Es[4]], Vs[Es[5]])
	    Es = this.o4triEs[this.edgeAlternative]
	    dLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])

	if this.inclReflections:
	    s = 'T = %02.2f; |a|: %s, |b|: %s, |c|: %s, |d|: %s' % (
		    this.height, aLen, bLen, cLen, dLen
		)
	else:
	    Es = this.oppTriEs[this.oppEdgeAlternative]
	    opp_bLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
	    opp_cLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
	    #Es = this.oppO3triEs[this.oppEdgeAlternative]
	    if this.oppEdgeAlternative != trisAlt.refl_1:
		opp_dLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
	    else:
		opp_dLen = '-'
	    s = 'T = %02.2f; |a|: %s, |b|: %s (%s), |c|: %s (%s), |d|: %s (%s)' % (
		    this.height,
		    aLen, bLen, opp_bLen, cLen, opp_cLen, dLen, opp_dLen
		)
        return s

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
	#				o3: 7 -> 24 -> 25
	#				    0 -> 26 -> 27

	this.posHeptagon()
	Vs = this.heptagon.Vs[:]
	Vs.append(Vec([-Vs[5][0], -Vs[5][1], Vs[5][2]]))        # Vs[7]
	Vs.append(o3fld * Vs[0])				# Vs[8]
	Vs.append(o3fld * Vs[1])				# Vs[9]
	Vs.append(o3fld * Vs[-1])				# Vs[10]
	Vs.append(o3fld * Vs[2])				# Vs[11]
	Vs.append(o3fld * Vs[-1])				# Vs[12]
	Vs.append(Vec([-Vs[2][0], -Vs[2][1], Vs[2][2]]))        # Vs[13]
	Vs.append(Vec([-Vs[8][0], -Vs[8][1], Vs[8][2]]))        # Vs[14]
	Vs.append(o4fld * Vs[6])				# Vs[15]
	Vs.append(o4fld * Vs[-1])				# Vs[16]
	Vs.append(o4fld * Vs[-1])				# Vs[17]
	Vs.append(o4fld * Vs[5])				# Vs[18]
	Vs.append(o4fld * Vs[-1])				# Vs[19]
	Vs.append(o4fld * Vs[-1])				# Vs[20]
	Vs.append(o4fld * Vs[0])				# Vs[21]
	Vs.append(o4fld * Vs[-1])				# Vs[22]
	Vs.append(o4fld * Vs[-1])				# Vs[23]
	Vs.append(o3fld * Vs[7])				# Vs[24]
	Vs.append(o3fld * Vs[-1])				# Vs[25]
	Vs.append(o3fld * Vs[0])				# Vs[26]
	Vs.append(o3fld * Vs[-1])				# Vs[27]
	Vs.append(o4fld * Vs[12])				# Vs[28]
	Vs.append(o4fld * Vs[-1])				# Vs[29]
	Vs.append(o4fld * Vs[-1])				# Vs[30]
	Vs.append(o4fld * Vs[6])				# Vs[31]
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
	    Fs = this.o3triFs[this.edgeAlternative][:]
	    Es = this.o3triEs[this.edgeAlternative][:]
            this.trisO3Shape.setBaseVertexProperties(Vs = Vs)
            this.trisO3Shape.setBaseEdgeProperties(Es = Es)
            this.trisO3Shape.setBaseFaceProperties(Fs = Fs)
            theShapes.append(this.trisO3Shape)
	    Es = this.o4triEs[this.oppEdgeAlternative][:]
	    Fs = this.o4triFs[this.oppEdgeAlternative][:]
            this.trisO4Shape.setBaseVertexProperties(Vs = Vs)
            this.trisO4Shape.setBaseEdgeProperties(Es = Es)
            this.trisO4Shape.setBaseFaceProperties(Fs = Fs)
            theShapes.append(this.trisO4Shape)
            if (not this.onlyRegFs):
		# when you use the rot alternative the rot is leading for
		# choosing the colours.
		if this.oppEdgeAlternative & Heptagons.rot_bit:
		    eAlt = this.oppEdgeAlternative
		else:
		    eAlt = this.edgeAlternative
		Fs = this.triFs[this.edgeAlternative][:]
		Fs.extend(this.oppTriFs[this.oppEdgeAlternative])
		Es = this.triEs[this.edgeAlternative][:]
		Es.extend(this.oppTriEs[this.oppEdgeAlternative])
		colIds = this.triColIds[eAlt]
                this.xtraTrisShape.setBaseVertexProperties(Vs = Vs)
                this.xtraTrisShape.setBaseEdgeProperties(Es = Es)
                this.xtraTrisShape.setBaseFaceProperties(
		    Fs = Fs,
                    colors = ([rgb.darkRed[:], rgb.yellow[:], rgb.magenta[:]],
                        colIds
		    )
                )
                theShapes.append(this.xtraTrisShape)
	for shape in theShapes:
	    shape.showBaseOnly = not this.applySymmetry
        this.setShapes(theShapes)
        this.updateShape = False
	# print 'V0 = (%.4f, %.4f, %.4f)' % (Vs[0][1], Vs[0][0], Vs[0][2])
	# print 'V1 = (%.4f, %.4f, %.4f)' % (Vs[1][1], Vs[1][0], Vs[1][2])
	# print 'V2 = (%.4f, %.4f, %.4f)' % (Vs[2][1], Vs[2][0], Vs[2][2])
	# print 'V3 = (%.4f, %.4f, %.4f)' % (Vs[3][1], Vs[3][0], Vs[3][2])
	# print 'V4 = (%.4f, %.4f, %.4f)' % (Vs[4][1], Vs[4][0], Vs[4][2])
	# print 'V5 = (%.4f, %.4f, %.4f)' % (Vs[5][1], Vs[5][0], Vs[5][2])
	# print 'V6 = (%.4f, %.4f, %.4f)' % (Vs[6][1], Vs[6][0], Vs[6][2])

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
	#				o3: 7 -> 24 -> 25
	#				    0 -> 26 -> 27

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
	arot_star.append([13, 17, 17]) # <----- oops cannot be right
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
                trisAlt.strip_1_loose:		loose,
                trisAlt.strip_I:		strip,
                trisAlt.strip_II:		strip,
                trisAlt.star:			strip,
                trisAlt.star_1_loose:		star1loose,
                trisAlt.alt_strip_I:		strip,
                trisAlt.alt_strip_II:		strip,
                trisAlt.alt_strip_1_loose:	loose,
                trisAlt.rot_strip_1_loose:	rot,
                trisAlt.arot_strip_1_loose:	rot,
                trisAlt.rot_star_1_loose:	rot_x,
                trisAlt.arot_star_1_loose:	arot_x,
                trisAlt.refl_1:		        refl_1,
                trisAlt.refl_2:		        refl_2,
            }

	std    = [1, 9, 10]
	alt    = [2, 11, 12]
	refl_1 = [2, 7, 11, 24, 12, 25]
	refl_2 = [0, 26, 27]
        this.o3triFs = {
                trisAlt.strip_1_loose:		[std],
                trisAlt.strip_I:		[std],
                trisAlt.strip_II:		[std],
                trisAlt.star:			[std],
                trisAlt.star_1_loose:		[std],
                trisAlt.alt_strip_I:		[alt],
                trisAlt.alt_strip_II:		[alt],
                trisAlt.alt_strip_1_loose:	[alt],
                trisAlt.refl_1:		        [refl_1],
                trisAlt.refl_2:		        [refl_2],
	    }

	std  = [6, 15, 16, 17]
	alt  = [5, 18, 19, 20]
	refl_1 = [0, 21, 22, 23]
	refl_2 = [5, 12, 18, 28, 19, 29, 20, 30]
        this.o4triFs = {
                trisAlt.strip_1_loose:		[std],
                trisAlt.strip_I:		[std],
                trisAlt.strip_II:		[std],
                trisAlt.star:			[std],
                trisAlt.star_1_loose:		[std],
                trisAlt.alt_strip_I:		[alt],
                trisAlt.alt_strip_II:		[alt],
                trisAlt.alt_strip_1_loose:	[alt],
                trisAlt.rot_strip_1_loose:	[std],
                trisAlt.arot_strip_1_loose:	[alt],
                trisAlt.rot_star_1_loose:	[std],
                trisAlt.arot_star_1_loose:	[alt],
                trisAlt.refl_1:		        [refl_1],
                trisAlt.refl_2:		        [refl_2],
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
	rot_strip     = [13, 15, 5, 15]
	rot_star      = [13, 15, 6, 13]
	arot_star     = [13, 15, 13, 17]
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
                trisAlt.strip_1_loose:	    std,
                trisAlt.strip_I:	    std,
                trisAlt.strip_II:	    std,
                trisAlt.star:		    std,
                trisAlt.star_1_loose:	    std,
                trisAlt.alt_strip_I:	    alt,
                trisAlt.alt_strip_II:	    alt,
                trisAlt.alt_strip_1_loose:  alt,
                trisAlt.refl_1:		    refl,
                trisAlt.refl_2:		    refl,
            }

	std    = [6, 15, 15, 16, 16, 17, 17, 6]
	alt    = [5, 18, 18, 19, 19, 20, 20, 5]
	refl   = []
        this.o4triEs = {
                trisAlt.strip_1_loose:	    std,
                trisAlt.strip_I:	    std,
                trisAlt.strip_II:	    std,
                trisAlt.star:		    std,
                trisAlt.star_1_loose:	    std,
                trisAlt.alt_strip_I:	    alt,
                trisAlt.alt_strip_II:	    alt,
                trisAlt.alt_strip_1_loose:  alt,
                trisAlt.rot_strip_1_loose:  std,
                trisAlt.arot_strip_1_loose: alt,
                trisAlt.rot_star_1_loose:   std,
                trisAlt.arot_star_1_loose:  alt,
                trisAlt.refl_1:		    refl,
                trisAlt.refl_2:		    refl,
            }

class CtrlWin(Heptagons.FldHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
	Heptagons.FldHeptagonCtrlWin.__init__(this,
	    shape, canvas,
	    8, # maxHeigth
	    [ # prePosLst
		Stringify[only_hepts],
		Stringify[dyn_pos],
	    ],
	    trisAlt,
	    Stringify,
	    *args, **kwargs
	)

    def showOnlyHepts(this):
	return this.prePos == only_hepts and not (
		this.trisFill == None
	    ) and not (
		this.trisFill == trisAlt.refl_1 or
		this.trisFill == trisAlt.refl_2
	    )

    def showOnlyO3Tris(this):
	return this.prePos == Heptagons.only_xtra_o3s and not (
		this.trisFill == None
	    ) and not (
		this.trisFill == trisAlt.refl_1 or
		this.trisFill == trisAlt.refl_2
	    )

    rDir = 'data/Data_FldHeptS4'
    rPre = 'frh-roots'

    def mapPrePosStrToFileStr(this, prePosId):
	try:
	    if this.shape.inclReflections:
		s = prePosStrToReflFileStrMap[prePosId]
	    else:
		s = prePosStrToFileStrMap[prePosId]
	except KeyError:
	    print 'info: no file name mapping found for prepos:', prePosId
	    s = this.stringify[prePosId]
	return s

    def printFileStrMapWarning(this, filename, funcname):
	print '%s:' % funcname
	print '  WARNING: unable to interprete filename', filename

    def fileStrMapFoldMethodStr(this, filename):
	res = re.search("-fld_([^.]*)\.", filename)
	if res:
	    return res.groups()[0]
	else:
	    this.printFileStrMapWarning(filename, 'fileStrMapFoldMethodStr')

    def fileStrMapHasReflections(this, filename):
	res = re.search(".*frh-roots-(.*)-fld_.*", filename)
	if res:
	    pos_vals = res.groups()[0].split('_')
	    nr_pos = len(pos_vals)
	    return (nr_pos == 4) or (nr_pos == 5 and pos_vals[4] == '0')
	else:
	    this.printFileStrMapWarning(filename, 'fileStrMapHasReflections')

    def fileStrMapTrisStr(this, filename):
	res = re.search("-fld_[^.]*\.[0-7]-([^.]*)\.py", filename)
	if res:
	    tris_str = res.groups()[0]
	    return trisAlt.mapFileStrOnStr[tris_str]
	else:
	    this.printFileStrMapWarning(filename, 'fileStrMapTrisStr')

    def isPrePosValid(this, prePosId):
	# This means that files with empty results should be filtered out from
	# the directory.
	s = this.mapPrePosStrToFileStr(prePosId)
	return glob('%s/%s-%s-*' % (this.rDir, this.rPre, s)) != []

    def isFoldValid(this, foldMethod):
	p = this.mapPrePosStrToFileStr(this.prePos)
	f = Heptagons.FoldName[foldMethod].lower()
	return glob(
		'%s/%s-%s-fld_%s.*' % (this.rDir, this.rPre, p, f)
	    ) != []

    def isTrisFillValid(this, trisFillId):
	if this.shape.inclReflections:
	    if type(trisFillId) != int:
		return False
	    oppFill = ''
	    t = trisAlt.mapKeyOnFileStr[trisFillId]
	else:
	    if type(trisFillId) == int:
		return False
	    oppFill = '-opp_%s' % trisAlt.mapKeyOnFileStr[trisFillId[1]]
	    t = trisAlt.mapKeyOnFileStr[trisFillId[0]]
	p = this.mapPrePosStrToFileStr(this.prePos)
	f = Heptagons.FoldName[this.foldMethod].lower()
	files = '%s/%s-%s-fld_%s.?-%s%s.*' % (
		this.rDir, this.rPre, p, f, t, oppFill)
	#if glob(files) != []:
	#    print 'DBG: found %s' % files
	#else:
	#    print 'DBG: NOT found %s' % files
	return glob(files) != []

    # TODO move to parent
    def openPrePosFile(this, filename):
	try:
	    print 'DBG open', filename
	    fd = open(filename, 'r')
	except IOError:
	    print 'DBG file not found:\n %s' % filename
	    return []
	ed = {'__name__': 'readPyFile'}
	exec fd in ed
	fd.close()
	return ed['results']

    @property
    def specPosSetup(this):
	prePosId = this.prePos
	if prePosId != open_file and prePosId != dyn_pos:
	    # use correct predefined special positions
	    if this.shape.inclReflections:
		psp = this.predefReflSpecPos
	    else:
		psp = this.predefRotSpecPos
	    data = psp[this.prePos][this.specPosIndex]
	    if data.has_key('file'):
		print 'see file %s/%s' % (this.rDir, data['file'])
	    return data

    @property
    def stdPrePos(this):
	try:
	    return this.sav_stdPrePos
	except AttributeError:
	    prePosId = this.prePos
	    assert prePosId != dyn_pos
	    if prePosId == open_file:
		filename = this.prePosFileName
		if filename == None:
		    return []
	    else:
		# use correct predefined special positions
		if this.shape.inclReflections:
		    psp = this.predefReflSpecPos
		else:
		    psp = this.predefRotSpecPos
		# Oops not good for performance:
		# TODO only return correct one en add length func
		return [sp['set'] for sp in psp[this.prePos]]
		#this.predefSpecPos[this.prePos]['set']
		if this.trisFill == None:
		    return []
		if this.shape.inclReflections:
		    oppFill = ''
		else:
		    oppFill = '-opp_%s' % trisAlt.mapKeyOnFileStr[this.oppTrisFill]
		filename = '%s/%s-%s-fld_%s.0-%s%s.py' % (
			    this.rDir, this.rPre,
			    this.mapPrePosStrToFileStr(this.prePos),
			    Heptagons.FoldName[this.foldMethod].lower(),
			    trisAlt.mapKeyOnFileStr[this.trisFill],
			    oppFill
			)
	    this.sav_stdPrePos = this.openPrePosFile(filename)
	    return this.sav_stdPrePos

    predefReflSpecPos = {
	only_hepts: [
	    {
		#'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_2.py'
		'set': [0.0194846506, 2.5209776869, 0.7387578325, -0.2490014706, 1.5707963268],
		'7fold': Heptagons.foldMethod.star,
		'tris': trisAlt.refl_2,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_2.py'
		'set': [1.9046884810, -0.0895860579, 0.0898667459, -0.8043880107, 1.5707963268],
		'7fold': Heptagons.foldMethod.star,
		'tris': trisAlt.refl_2,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_1.py'
		'set': [2.3689660916, 0.0851258971, -0.0853666149, 2.1212284837],
		'7fold': Heptagons.foldMethod.star,
		'tris': trisAlt.refl_1,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_2.py'
		'set': [0.1801294042, -0.5679882382, 2.7691714565, -0.1647931959, 1.5707963268],
		'7fold': Heptagons.foldMethod.star,
		'tris': trisAlt.refl_2,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_shell.0-refl_1.py'
		'set': [0.1985558264, -0.7212633593, 2.5993674146, -0.2638659586],
		'7fold': Heptagons.foldMethod.star,
		'tris': trisAlt.refl_1,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_1.py'
		'set': [2.3706859974, -0., 1.4330985471, 1.1300265566],
		'7fold': Heptagons.foldMethod.triangle,
		'tris': trisAlt.refl_1,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_2.py'
		'set': [1.9053212843, 0.0000000000, 2.0476430098, 0.6938789411, 1.5707963268],
		'7fold': Heptagons.foldMethod.triangle,
		'tris': trisAlt.refl_2,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_1.py'
		'set': [2.3706859974, 0., 0.1376977796, 2.0115660970],
		'7fold': Heptagons.foldMethod.triangle,
		'tris': trisAlt.refl_1,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_triangle.0-refl_2.py'
		'set': [1.9053212843, 0.0000000000, -0.1370097736, -0.6938789411, 1.5707963268],
		'7fold': Heptagons.foldMethod.triangle,
		'tris': trisAlt.refl_2,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_w.0-refl_1.py'
		'set': [0.2144969422, -0.7161063284, 2.4479090034, 0.2591004995],
		'7fold': Heptagons.foldMethod.w,
		'tris': trisAlt.refl_1,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_w.0-refl_1.py'
		'set': [1.82916035932, -0.15381215148, -0.73341848407, 2.31852723230],
		'7fold': Heptagons.foldMethod.w,
		'tris': trisAlt.refl_1,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_w.0-refl_2.py'
		'set': [1.8797513382, -0.0971685207, -0.3990474779, 0.9416509246, 1.5707963268],
		'7fold': Heptagons.foldMethod.w,
		'tris': trisAlt.refl_2,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_w.0-refl_2.py'
		'set': [0.0078461298, 2.5240450735, 0.6010013359, 0.2588481477, 1.5707963268],
		'7fold': Heptagons.foldMethod.w,
		'tris': trisAlt.refl_2,
	    },{
		#'file': 'frh-roots-0_0_0_0-fld_w.0-refl_2.py'
		'set': [1.4801185612, -0.2147509348, -0.4352845433, 2.4498730531, 1.5707963268],
		'7fold': Heptagons.foldMethod.w,
		'tris': trisAlt.refl_2,
	    }
	],
    }
    predefRotSpecPos = {
	only_hepts: [],
    }

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
	glFrontFace(GL_CW)
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
