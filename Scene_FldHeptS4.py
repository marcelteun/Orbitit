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

from glob import glob
from OpenGL.GL import *

import GeomTypes
from GeomTypes import Rot3      as Rot
from GeomTypes import HalfTurn3 as HalfTurn
from GeomTypes import Vec3      as Vec

Title = 'Polyhedra with Folded Regular Heptagons S4'

trisAlt = Heptagons.TrisAlt()

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

o4_fld_0 = GeomTypes.Vec3([1, 0, 0])
o4_fld_1 = GeomTypes.Vec3([0, 1, 1])
isomS4 = isometry.S4(setup = {'o4axis0': o4_fld_0, 'o4axis1': o4_fld_1})
o4fld = Rot(axis = o4_fld_1, angle = GeomTypes.qTurn)
o3axis = GeomTypes.Vec3([1/V3, 0, V2/V3])
o3fld = Rot(axis = o3axis, angle = GeomTypes.tTurn)
isomO3 = isometry.C3(setup = {'axis': o3axis})

# get the col faces array by using a similar shape here, so it is calculated
# only once
#colStabiliser = isometry.C2(setup = {'axis': [0.0, 1.0, 0.0]})
#colStabiliser = isometry.C2(setup = {'axis': [0.0, 0.0, 1.0]})
colStabiliser = isometry.D4(setup = {'axis_n': [1.0, 0.0, 0.0]})
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
            name = 'FoldedHeptagonsS4'
        )
	xtraTrisShape = Geom3D.IsometricShape(
	    Vs = [], Fs = [], directIsometries = isomS4,
            name = 'xtraTrisS4'
        )
	trisO3Shape = Geom3D.SymmetricShape(
	    Vs = [], Fs = [],
	    finalSym = isomS4, stabSym = isomO3,
	    colors = [([rgb.cyan[:]], [])],
            name = 'o3TrisS4'
        )
	Heptagons.FldHeptagonShape.__init__(this,
	    [heptagonsShape, xtraTrisShape],#, trisO3Shape],
	    4, 3,
            name = 'FoldedRegHeptS4xI'
        )
	this.heptagonsShape = heptagonsShape
	this.xtraTrisShape = xtraTrisShape
	this.trisO3Shape = trisO3Shape
	this.posAngleMin = -math.pi/2 # 0?
        this.posAngleMax = math.pi/2
	this.posAngle = math.pi/4
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
	Vs.append(o4fld * Vs[0])				# Vs[18]
	Vs.append(o4fld * Vs[-1])				# Vs[19]
	Vs.append(o4fld * Vs[-1])				# Vs[20]
	#-----------------------ORG--------------------------------
	#Vs.append(o4fld * Vs[-1])				# Vs[7]
	#Vs.append(o4fld * Vs[-1])				# Vs[8]
	#Vs.append(o4fld * Vs[-1])				# Vs[9]
	#o3axis = GeomTypes.Vec3([1, 0, V2])
	#o3fld = Rot(axis = o3axis, angle = GeomTypes.tTurn)
	#Vs.append(o3fld * Vs[1])				# Vs[10]
	#Vs.append(o3fld * Vs[-1])				# Vs[11]
	#Vs.append(Vec([-Vs[5][0], -Vs[5][1], Vs[5][2]]))       # Vs[12]
	#Vs.append(o3fld * Vs[0])				# Vs[13]
	#Vs.append(Vec([-Vs[13][0], -Vs[13][1], Vs[13][2]]))    # Vs[14]
	#Vs.append(o3fld * Vs[2])				# Vs[15]
	#Vs.append(o3fld * Vs[-1])				# Vs[16]
	#-----------------------------------------------
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
	this.heptagonsShape.setBaseVertexProperties(Vs = Vs)
        this.heptagonsShape.setBaseEdgeProperties(Es = Es)
	# TODO CHk: comment out this and nvidia driver crashes:...
	this.heptagonsShape.setBaseFaceProperties(Fs = Fs)
        this.heptagonsShape.setFaceColors(heptColPerIsom)
	theShapes = [this.heptagonsShape]
	# TODO rm:
	if this.addXtraFs:
	    Es      = this.o3triEs[this.edgeAlternative][:]
	    Fs      = this.o3triFs[this.edgeAlternative][:]
	    Es.extend(this.oppO3triEs[this.oppEdgeAlternative])
	    Fs.extend(this.oppO3triFs[this.oppEdgeAlternative])
            this.trisO3Shape.setBaseVertexProperties(Vs = Vs)
            this.trisO3Shape.setBaseEdgeProperties(Es = Es)
            this.trisO3Shape.setBaseFaceProperties(Fs = Fs)
            #theShapes.append(this.trisO3Shape)
            if (not this.onlyRegFs):
		# when you use the rot alternative the rot is leading for
		# choosing the colours.
		if this.oppEdgeAlternative & Heptagons.rot_bit:
		    eAlt = this.oppEdgeAlternative
		else:
		    eAlt = this.edgeAlternative
		Es      = this.triEs[this.edgeAlternative][:]
		if this.edgeAlternative == trisAlt.twist_strip_I:
		    Fs = this.triFs[this.edgeAlternative][
			this.inclReflections][:]
		    Fs.extend(
			this.oppTriFs[this.oppEdgeAlternative][
			    this.inclReflections
			]
		    )
		    Es.extend(
			this.oppTriEs[this.oppEdgeAlternative][
			    this.inclReflections
			]
		    )
                    colIds = this.triColIds[eAlt][this.inclReflections]
		else:
		    Fs = this.triFs[this.edgeAlternative][:]
		    Fs.extend(this.oppTriFs[this.oppEdgeAlternative])
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
	# o4: 0 -> 18 -> 19 -> 20
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

	I_loose = [[2, 3, 7]]
	noLoose = [[2, 3, 8]]
	stripI  = [[2, 8, 9]]
	stripII = [[2, 3, 9], [3, 8, 9]]
	star    = [[1, 2, 8], [1, 8, 9]]
	strip_1_loose = stripI[:]
	star_1_loose  = star[:]
	stripI.extend(noLoose)
	star.extend(noLoose)
	strip_1_loose.extend(I_loose)
	star_1_loose.extend(I_loose)
	# TODO:
	#twist_strip = { # reflections included:
	#    False: [[2, 3, 7], [1, 2, 20], [0, 1, 8]],
	#    True:  [[2, 3, 7], [1, 2, 21, 20], [0, 1, 20, 8]]
	#}
	this.triFs = {
                trisAlt.strip_1_loose:      strip_1_loose[:],
                trisAlt.strip_I:            stripI[:],
                trisAlt.strip_II:           stripII[:],
                trisAlt.star:               star[:],
                trisAlt.star_1_loose:       star_1_loose[:],
                trisAlt.alt_strip_1_loose:  strip_1_loose[:],
                trisAlt.alt_strip_I:        stripI[:],
                trisAlt.alt_strip_II:       stripII[:],
                #trisAlt.twist_strip_I:      twist_strip,
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
	strip_1_loose = stripI[:]
	star_1_loose  = star[:]
	stripI.extend(noLoose)
	star.extend(noLoose)
	strip_1_loose.extend(I_loose)
	star_1_loose.extend(I_loose)
	rot_strip = [[13, 17, 14], [13, 5, 17]]
	rot_star = [[13, 17, 14], [13, 5, 6]]
	arot_star = [[13, 17, 14], [13, 17, 17]]
	# TODO:
	#twist_strip = { # reflections included:
	#    False: [[1, 20, 8], [2, 21, 20]],
	#    True:  []
	#}
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
                #trisAlt.twist_strip_I:      twist_strip,
	}
	# TODO:
	stdO3   = [6, 17, 5]
	stdO3_x = [6, 17, 13]
	altO3   = [5, 17, 15]
	altO3_x = [5, 17, 13]
        this.oppTriFs[trisAlt.strip_1_loose].append(stdO3)
        this.oppTriFs[trisAlt.strip_I].append(stdO3)
        this.oppTriFs[trisAlt.strip_II].append(stdO3)
        this.oppTriFs[trisAlt.alt_strip_1_loose].append(altO3)
        this.oppTriFs[trisAlt.alt_strip_I].append(stdO3)
        this.oppTriFs[trisAlt.alt_strip_II].append(stdO3)
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
	twist = { # reflections included:
	    False: [1, 1, 0, 0, 1],
	    True:  [1, 1, 0]
	}
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
                trisAlt.twist_strip_I:		twist,
            }

	# TODO:
	std = [1, 9, 10]
	alt = [2, 11, 12]
	twist = [0, 8, 19]
        this.o3triFs = {
                trisAlt.strip_1_loose:		[std],
                trisAlt.strip_I:		[std],
                trisAlt.strip_II:		[std],
                trisAlt.star:			[std],
                trisAlt.star_1_loose:		[std],
                trisAlt.alt_strip_I:		[alt],
                trisAlt.alt_strip_II:		[alt],
                trisAlt.alt_strip_1_loose:	[alt],
                #trisAlt.twist_strip_I:		[twist],
	    }
	std = [6, 16, 15]
	alt = [5, 18, 17]
	twist = [5, 23, 18, 22, 17, 13]
        this.oppO3triFs = {
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
                #trisAlt.twist_strip_I:		[twist],
	    }

	strip_1_loose = [2, 7, 2, 8, 2, 9]
	stripI        = [3, 8, 2, 8, 2, 9]
	stripII       = [3, 8, 3, 9, 2, 9]
	star          = [3, 8, 2, 8, 1, 8]
	star_1_loose  = [2, 7, 2, 8, 1, 8]
	twist_stripI  = [2, 7, 2, 21, 1, 20]
        this.triEs = {
                trisAlt.strip_1_loose:     strip_1_loose,
                trisAlt.strip_I:           stripI,
                trisAlt.strip_II:          stripII,
                trisAlt.star:              star,
                trisAlt.star_1_loose:      star_1_loose,
                trisAlt.alt_strip_I:       stripI,
                trisAlt.alt_strip_II:      stripII,
                trisAlt.alt_strip_1_loose: strip_1_loose,
                #trisAlt.twist_strip_I:     twist_stripI,
            }
	strip_1_loose = [5, 14, 5, 15]
	stripI        = [5, 14, 5, 15]
	stripII       = [4, 15, 5, 15]
	star          = [5, 14, 6, 14]
	star_1_loose  = [5, 14, 6, 14]
	rot_strip     = [13, 15, 5, 15]
	rot_star      = [13, 15, 6, 13]
	arot_star     = [13, 15, 13, 17]
	twist_stripI  = { # reflections included:
	    False: [1, 8, 2, 20],
	    True:  []
	}
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
                #trisAlt.twist_strip_I:      twist_stripI,
            }

	std = [1, 9, 9, 10, 10, 1]
	alt = [2, 11, 11, 12, 12, 2]
	twist = [0, 8, 8, 19, 19, 0]
        this.o3triEs = {
                trisAlt.strip_1_loose:		std,
                trisAlt.strip_I:		std,
                trisAlt.strip_II:		std,
                trisAlt.star:			std,
                trisAlt.star_1_loose:		std,
                trisAlt.alt_strip_I:		alt,
                trisAlt.alt_strip_II:		alt,
                trisAlt.alt_strip_1_loose:	alt,
                #trisAlt.twist_strip_I:		twist,
            }
	std = [6, 16, 16, 15, 15, 6]
	alt = [5, 18, 18, 17, 17, 5]
	twist = []
        this.oppO3triEs = {
                trisAlt.strip_1_loose:		std,
                trisAlt.strip_I:		std,
                trisAlt.strip_II:		std,
                trisAlt.star:			std,
                trisAlt.star_1_loose:		std,
                trisAlt.alt_strip_I:		alt,
                trisAlt.alt_strip_II:		alt,
                trisAlt.alt_strip_1_loose:	alt,
                trisAlt.rot_strip_1_loose:	std,
                trisAlt.arot_strip_1_loose:	alt,
                trisAlt.rot_star_1_loose:	std,
                trisAlt.arot_star_1_loose:	alt,
                #trisAlt.twist_strip_I:		twist,
            }

class CtrlWin(Heptagons.FldHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
	Heptagons.FldHeptagonCtrlWin.__init__(this,
	    shape, canvas,
	    4, # maxHeigth
	    [ # prePosLst
		Stringify[only_hepts],
		Stringify[dyn_pos],
	    ],
	    Stringify,
	    *args, **kwargs
	)

    def showOnlyHepts(this):
	return this.prePos == only_hepts and not (
		this.trisFill == None
	    ) and not (
		this.trisFill & Heptagons.twist_bit == Heptagons.twist_bit)

    def showOnlyO3Tris(this):
	return this.prePos == Heptagons.only_xtra_o3s and not (
		this.trisFill == None
	    ) and not (
		this.trisFill & Heptagons.twist_bit == Heptagons.twist_bit)

    rDir = 'data/Data_FldHeptA4'
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
	    # TODO rm this tmp check
	    if Heptagons.TODO_TMP_TST_RM:
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
		# TODO rm this tmp check
		if Heptagons.TODO_TMP_TST_RM:
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
	only_hepts: [],
    }
    predefRotSpecPos = {
	only_hepts: [],
    }

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
	glFrontFace(GL_CW)
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
