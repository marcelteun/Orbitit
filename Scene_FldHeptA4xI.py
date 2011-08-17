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

Title = 'Polyhedra with Folded Regular Heptagons A4xI'

V2 = math.sqrt(2)

trisAlt = Heptagons.TrisAlt()

dyn_pos		= Heptagons.dyn_pos
open_file	= Heptagons.open_file
# symmtric edge lengths: b0 == b1, c0 == c1, d0 == d1
S_T8		= Heptagons.only_xtra_o3s
S_only_hepts0	= Heptagons.only_hepts
S_only_hepts1	= Heptagons.tris_fill_base + 0
S_T24		= Heptagons.tris_fill_base + 1
S_T32_0		= Heptagons.tris_fill_base + 2
S_T32_1		= Heptagons.tris_fill_base + 3
S_T32_2		= Heptagons.tris_fill_base + 4
S_T48		= Heptagons.no_o3_tris
S_T56		= Heptagons.tris_fill_base + 5
S_T80		= Heptagons.all_eq_tris

# symmtric edge lengths with folded squares
S_S12		= Heptagons.tris_fill_base + 6
S_T8_S12	= Heptagons.tris_fill_base + 7
S_S24		= Heptagons.tris_fill_base + 8
S_T8_S24	= Heptagons.tris_fill_base + 9
S_T24_S12	= Heptagons.tris_fill_base + 10
S_T8_S36	= Heptagons.tris_fill_base + 11
S_T32_S12   	= Heptagons.tris_fill_base + 12
S_T32_S24_0	= Heptagons.tris_fill_base + 13
S_T32_S24_1	= Heptagons.tris_fill_base + 14
S_T56_S12	= Heptagons.tris_fill_base + 15

T8_0		= Heptagons.tris_fill_base + 16
T16_0		= Heptagons.tris_fill_base + 17
T16_1		= Heptagons.tris_fill_base + 18
T16_2		= Heptagons.tris_fill_base + 19
T16_3		= Heptagons.tris_fill_base + 20
T24_0		= Heptagons.tris_fill_base + 21
T24_1		= Heptagons.tris_fill_base + 22
T32_0		= Heptagons.tris_fill_base + 23
T40_0		= Heptagons.tris_fill_base + 24
T40_1		= Heptagons.tris_fill_base + 25
T40_2		= Heptagons.tris_fill_base + 26
T40_3		= Heptagons.tris_fill_base + 27
T64_0		= Heptagons.tris_fill_base + 28

Stringify = {
    dyn_pos:		'Enable Sliders',
    # symmtric edge lengths: b0 == b1, c0 == c1, d0 == d1
    S_only_hepts0:	'SEL:  0 Extra Faces (A)',
    S_only_hepts1:	'SEL:  0 Extra Faces (B)',
    S_T8:		'SEL:  8 Triangles (O3)',
    S_T24:		'SEL: 24 Triangles (A)',
    S_T32_0:		'SEL: 32 Triangles (24 + 8) (A)',
    S_T32_1:		'SEL: 32 Triangles (24 + 8) (B)',
    S_T32_2:		'SEL: 32 Triangles (24 + 8) (C)',
    S_T48:		'SEL: 48 Triangles',
    S_T56:		'SEL: 56 Triangles',
    S_T80:		'SEL: 80 Triangles Equilateral',
    # with folded squares:
    S_S12:		'SEL: 12 Folded Squares',
    S_T8_S12:		'SEL: 20 = 8 Triangles + 12 Folded Squares',
    S_S24:		'SEL: 24 Folded Squares',
    S_T8_S24:		'SEL: 32 = 8 Triangles + 24 Folded Squares',
    S_T24_S12:		'SEL: 36 = 24 Triangles + 12 Folded Squares',
    S_T8_S36:		'SEL: 44 = 8 Triangles + 36 Folded Squares',
    S_T32_S12:		'SEL: 44 = 32 Triangles + 12 Folded Squares',
    S_T32_S24_0:	'SEL: 56 = 32 Triangles + 24 Folded Squares (A)',
    S_T32_S24_1:	'SEL: 56 = 32 Triangles + 24 Folded Squares: (B)',
    S_T56_S12:		'SEL: 68 = 56 Triangles + 12 Folded Squares',

    # non-symmetric edges lengths
    T8_0:		' 8 Triangles (O3)',
    T16_0:		'16 Triangles (A)',
    T16_1:		'16 Triangles (B)',
    T16_2:		'16 Triangles (C)',
    T16_3:		'16 Triangles (D)',
    T24_0:		'24 Triangles (A)',
    T24_1:		'24 Triangles (B)',
    T32_0:	        '32 Triangles (A)',
    T40_0:		'40 Triangles (A)',
    T40_1:		'40 Triangles (B)',
    T40_2:		'40 Triangles (C)',
    T40_3:		'40 Triangles (D)',
    T64_0:		'64 Triangles (A)',
}

prePosStrToReflFileStrMap = {
    S_T32_1:		'0_0_1_1',
    S_only_hepts1:	'0_0_1_0',
    S_T8:		'0_1_0_1',
    S_T24:		'0_1_1_0',
    S_T56:		'0_1_1_1',
    S_only_hepts0:	'1_0_1_0',
    S_T32_2:		'1_0_1_1',
    S_T32_0:		'1_1_0_1',
    S_T48:		'1_1_1_0',
    S_T80:		'1_1_1_1',

    S_T8_S24:		'0_1_V2_1',
    S_S12:		'0_V2_1_0',
    S_T32_S12:		'0_V2_1_1',
    S_T32_S24_0:	'1_1_V2_1',
    S_S24:		'1_V2_1_0',
    S_T32_S24_1:	'1_V2_1_1',
    S_T8_S12:		'V2_1_0_1',
    S_T24_S12:		'V2_1_1_0',
    S_T56_S12:		'V2_1_1_1',
    S_T8_S36:		'V2_1_V2_1',
}

prePosStrToFileStrMap = {
    # symmetric edge lengths:
    S_only_hepts0:	'1_0_1_0_0_1_0',
    S_only_hepts1:	'0_0_1_0_0_1_0',
    S_T8:		'0_1_0_1_1_0_1',
    S_T24:		'0_1_1_0_1_1_0',
    S_T32_0:		'1_0_1_1_0_1_1',
    S_T48:		'1_1_1_0_1_1_0',
    S_T80:		'1_1_1_1_1_1_1',

    # non-symmetric edges lengths
    T8_0:		'0_1_0_1_0_0_1',
    T16_0:		'1_0_1_0_0_1_1',
    T16_1:		'1_0_1_0_1_0_1',
    T16_2:		'1_1_0_1_0_1_0',
    T16_3:		'1_0_1_1_0_1_0',
    T24_0:		'1_0_1_0_1_1_0',
    T24_1:		'1_1_1_0_0_1_0',
    T32_0:		'1_1_0_1_0_1_1',
    T40_0:		'1_0_1_0_1_1_1',
    T40_1:		'1_1_1_1_0_1_0',
    T40_2:		'1_0_1_1_1_1_0',
    T40_3:		'1_1_1_0_0_1_1',
    T64_0:		'1_1_1_1_1_1_0',

    S_S12:		'0_V2_1_0_V2_1_0',
    S_S24:		'1_V2_1_0_V2_1_0',
}

def Vlen(v0, v1):
    x = v1[0] - v0[0]
    y = v1[1] - v0[1]
    z = v1[2] - v0[2]
    return (math.sqrt(x*x + y*y + z*z))

# get the col faces array by using a similar shape here, so it is calculated
# only once
useIsom = isometry.A4()
egShape = Geom3D.IsometricShape(
    Vs = [
	GeomTypes.Vec3([0, 0, 1]),
	GeomTypes.Vec3([0, 1, 1]),
	GeomTypes.Vec3([1, 1, 1])
    ],
    Fs = [[0, 1, 2]],
    directIsometries = useIsom,
    unfoldOrbit = True
)
#colStabiliser = isometry.C2(setup = {'axis': [0.0, 1.0, 0.0]})
#colStabiliser = isometry.C2(setup = {'axis': [0.0, 0.0, 1.0]})
colStabiliser = isometry.C2(setup = {'axis': [1.0, 0.0, 0.0]})
colQuotientSet = useIsom / colStabiliser
useRgbCols = [
    rgb.indianRed,
    rgb.mediumBlue,
    rgb.limeGreen,
    rgb.cornflowerBlue,
    rgb.mistyRose1,
    rgb.gray20,
]
heptColPerIsom = []
for isom in useIsom:
    for subSet, i in zip(colQuotientSet, range(len(colQuotientSet))):
	if isom in subSet:
	    heptColPerIsom.append(([useRgbCols[i]], []))
	    break;
isomsO3 = isometry.D2()

class Shape(Heptagons.FldHeptagonShape):
    def __init__(this, *args, **kwargs):
	heptagonsShape = Geom3D.IsometricShape(
	    Vs = [], Fs = [], directIsometries = isometry.A4(),
            name = 'FoldedHeptagonsA4'
        )
	xtraTrisShape = Geom3D.IsometricShape(
	    Vs = [], Fs = [], directIsometries = isometry.A4(),
            name = 'xtraTrisA4'
        )
	trisO3Shape = Geom3D.IsometricShape(
	    Vs = [], Fs = [], directIsometries = isomsO3,
	    colors = [([rgb.cyan[:]], [])],
            name = 'o3TrisA4'
        )
	Heptagons.FldHeptagonShape.__init__(this,
	    [heptagonsShape, xtraTrisShape, trisO3Shape],
	    3, 3,
            name = 'FoldedRegHeptA4xI'
        )
	this.heptagonsShape = heptagonsShape
	this.xtraTrisShape = xtraTrisShape
	this.trisO3Shape = trisO3Shape
	this.posAngleMin = -math.pi
        this.posAngleMax = math.pi
	this.posAngle = 0
        this.setEdgeAlternative(trisAlt.strip_1_loose, trisAlt.strip_1_loose)
	this.initArrs()
	this.setV()

    def getStatusStr(this):
        if this.updateShape:
            #print 'getStatusStr: forced setV'
            this.setV()
        Vs = this.baseVs
	Es = this.triEs[this.edgeAlternative]
	aLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
	bLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
	cLen = '%2.2f' % Vlen(Vs[Es[4]], Vs[Es[5]])
	Es = this.o3triEs[this.edgeAlternative]
	dLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
	if this.inclReflections:
	    s = 'T = %02.2f; |a|: %s, |b|: %s, |c|: %s, |d|: %s' % (
		    this.height, aLen, bLen, cLen, dLen
		)
	else:
	    if this.edgeAlternative == trisAlt.twist_strip_I:
		Es = this.oppTriEs[this.oppEdgeAlternative][
		    this.inclReflections]
	    else:
		Es = this.oppTriEs[this.oppEdgeAlternative]
	    opp_bLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
	    opp_cLen = '%2.2f' % Vlen(Vs[Es[2]], Vs[Es[3]])
	    Es = this.oppO3triEs[this.oppEdgeAlternative]
	    if this.oppEdgeAlternative != trisAlt.twist_strip_I:
		opp_dLen = '%2.2f' % Vlen(Vs[Es[0]], Vs[Es[1]])
	    else:
		opp_dLen = '-'
	    s = 'T = %02.2f; |a|: %s, |b|: %s (%s), |c|: %s (%s), |d|: %s (%s)' % (
		    this.height,
		    aLen, bLen, opp_bLen, cLen, opp_cLen, dLen, opp_dLen
		)
        return s

    def correctEdgeAlternative(this):
	# TODO
	if (this.edgeAlternative == trisAlt.star or
		this.edgeAlternative == trisAlt.star_1_loose):
	    this.altMFoldFace = False
	    this.altNFoldFace = False
	else:
	    if this.altNFoldFace:
		this.edgeAlternative = this.edgeAlternative | alt1_bit
	    else:
		this.edgeAlternative = this.edgeAlternative & ~alt1_bit
	    if this.altMFoldFace:
		this.edgeAlternative = this.edgeAlternative | alt2_bit
	    else:
		this.edgeAlternative = this.edgeAlternative & ~alt2_bit

    def setEdgeAlternative(this, alt = None, oppositeAlt = None):
	Heptagons.FldHeptagonShape.setEdgeAlternative(this, alt, oppositeAlt)
	# TODO
	#this.correctEdgeAlternative()

    def setV(this):
        #this.heptagon.foldParallel(this.fold1, this.fold2)
        #this.heptagon.foldTrapezium(this.fold1, this.fold2)
	# print 'T =', this.height
	# print 'a =', this.dihedralAngle
	# print 'd =', this.posAngle
	# print 'b0 =', this.fold1
	# print 'b1 =', this.oppFold1
	# print 'g0 =', this.fold2
	# print 'g1 =', this.oppFold2
        # The angle has to be adjusted for historical reasons...
	# TODO: fix me
	if this.foldHeptagon == Heptagons.foldMethod.parallel:
	    this.heptagon.foldParallel(-this.fold1, -this.fold2, keepV0 = False)
	else:
	    this.heptagon.fold(
		this.fold1, this.fold2, this.oppFold1, this.oppFold2,
		keepV0 = False, fold = this.foldHeptagon
	    )
	#print 'norm V0-V1: ', (this.heptagon.Vs[1]-this.heptagon.Vs[0]).squareNorm()
	#print 'norm V1-V2: ', (this.heptagon.Vs[1]-this.heptagon.Vs[2]).squareNorm()
	#print 'norm V2-V3: ', (this.heptagon.Vs[3]-this.heptagon.Vs[2]).squareNorm()
	#print 'norm V3-V4: ', (this.heptagon.Vs[3]-this.heptagon.Vs[4]).squareNorm()
        this.heptagon.translate(Heptagons.H*GeomTypes.uy)
        # The angle has to be adjusted for historical reasons...
        this.heptagon.rotate(-GeomTypes.ux, GeomTypes.qTurn - this.dihedralAngle)
        this.heptagon.translate(this.height*GeomTypes.uz)
	if this.posAngle != 0:
	    this.heptagon.rotate(-GeomTypes.uz, this.posAngle)
        Vs = this.heptagon.Vs[:]

	#            5" = 18                 12 = 2"
	#    6" = 16                                 10 = 1"
        #                           0
        # 5' = 17     o3                         o3      11 = 2'
        #                    6             1
        #
        #       6' = 15                           9 = 1'
        #
        #                  5                 2
        #
        #
        #              14       4       3        8 = 0'
        #
        #
        #             2' = 13                7 = 5'

        Rr = Rot(axis = Vec([ 1, 1, 1]), angle = GeomTypes.tTurn)
        Rl = Rot(axis = Vec([-1, 1, 1]), angle = -GeomTypes.tTurn)
        Vs.append(Vec([-Vs[5][0], -Vs[5][1], Vs[5][2]]))       # Vs[7]
        Vs.append(Rr * Vs[0])                                  # Vs[8]
        Vs.append(Rr * Vs[1])                                  # Vs[9]
        Vs.append(Rr * Vs[9])                                  # Vs[10]
        Vs.append(Rr * Vs[2])                                  # Vs[11]
        Vs.append(Rr * Vs[11])                                 # Vs[12]
        Vs.append(Vec([-Vs[2][0], -Vs[2][1], Vs[2][2]]))       # Vs[13]
        Vs.append(Rl * Vs[0])                                  # Vs[14]
        Vs.append(Rl * Vs[6])                                  # Vs[15]
        Vs.append(Rl * Vs[-1])                                 # Vs[16]
        Vs.append(Rl * Vs[5])                                  # Vs[17]
        Vs.append(Rl * Vs[-1])                                 # Vs[18]
        Vs.append(Rr * Vs[8])                                  # Vs[19] = V0"
        Vs.append(Rr * Vs[6])                                  # Vs[20] = V6'"
        Vs.append(Rr * Vs[5])                                  # Vs[21] = V5'"

        Vs.append(Rl * Vs[13])                                 # Vs[22] = V13'
        Vs.append(Rl * Vs[-1])                                 # Vs[23] = V13"
        this.baseVs = Vs
	#for i in range(len(Vs)):
	#    print 'Vs[%d]:' % i, Vs[i]
        Es = []
        Fs = []
        Fs.extend(this.heptagon.Fs) # use extend to copy the list to Fs
        Es.extend(this.heptagon.Es) # use extend to copy the list to Fs
        this.heptagonsShape.setBaseVertexProperties(Vs = Vs)
        this.heptagonsShape.setBaseEdgeProperties(Es = Es)
	# comment out this and nvidia driver crashes:...
	this.heptagonsShape.setBaseFaceProperties(Fs = Fs)
        this.heptagonsShape.setFaceColors(heptColPerIsom)
        theShapes = [this.heptagonsShape]
        if this.addXtraFs:
	    Es      = this.o3triEs[this.edgeAlternative][:]
	    Fs      = this.o3triFs[this.edgeAlternative][:]
	    Es.extend(this.oppO3triEs[this.oppEdgeAlternative])
	    Fs.extend(this.oppO3triFs[this.oppEdgeAlternative])
            this.trisO3Shape.setBaseVertexProperties(Vs = Vs)
            this.trisO3Shape.setBaseEdgeProperties(Es = Es)
            this.trisO3Shape.setBaseFaceProperties(Fs = Fs)
            theShapes.append(this.trisO3Shape)
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
        print this.name, "initArrs"

	#            5" = 18                 12 = 2"
	#    6" = 16                                 10 = 1"
        #                           0
        # 5' = 17     o3                         o3      11 = 2'
        #                    6             1
        #
        #       6' = 15                           9 = 1'
        #
        #                  5                 2
        #
        #
        #              14       4       3        8 = 0'
        #
        #
        #             2' = 13                7 = 5'

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
	twist_strip = { # reflections included:
	    False: [[2, 3, 7], [1, 2, 20], [0, 1, 8]],
	    True:  [[2, 3, 7], [1, 2, 21, 20], [0, 1, 20, 8]]
	}
        this.triFs = {
                trisAlt.strip_1_loose:      strip_1_loose[:],
                trisAlt.strip_I:            stripI[:],
                trisAlt.strip_II:           stripII[:],
                trisAlt.star:               star[:],
                trisAlt.star_1_loose:       star_1_loose[:],
                trisAlt.alt_strip_1_loose:  strip_1_loose[:],
                trisAlt.alt_strip_I:        stripI[:],
                trisAlt.alt_strip_II:       stripII[:],
                trisAlt.twist_strip_I:      twist_strip,
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
	stripI  = [[5, 15, 14]]
	stripII = [[4, 5, 15], [4, 15, 14]]
	star    = [[5, 6, 14], [6, 15, 14]]
	strip_1_loose = stripI[:]
	star_1_loose  = star[:]
	stripI.extend(noLoose)
	star.extend(noLoose)
	strip_1_loose.extend(I_loose)
	star_1_loose.extend(I_loose)
	rot_strip = [[13, 15, 14], [13, 5, 15]]
	rot_star = [[13, 15, 14], [13, 5, 6]]
	arot_star = [[13, 15, 14], [13, 17, 15]]
	twist_strip = { # reflections included:
	    False: [[1, 20, 8], [2, 21, 20]],
	    True:  []
	}
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
                trisAlt.twist_strip_I:      twist_strip,
	}
	stdO3   = [6, 15, 5]
	stdO3_x = [6, 15, 13]
	altO3   = [5, 17, 15]
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

	#            5" = 18                 12 = 2"
	#    6" = 16                                 10 = 1"
        #                           0
        # 5' = 17     o3                         o3      11 = 2'
        #                    6             1
        #
        #       6' = 15                           9 = 1'
        #
        #                  5                 2
        #
        #
        #              14       4       3        8 = 0'
        #
        #
        #             2' = 13                7 = 5'

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
                trisAlt.twist_strip_I:		[twist],
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
                trisAlt.twist_strip_I:		[twist],
	    }

	#            5" = 18                 12 = 2"
	#    6" = 16                                 10 = 1"
        #                           0
        # 5' = 17     o3                         o3      11 = 2'
        #                    6             1
        #
        #       6' = 15                           9 = 1'
        #
        #                  5                 2
        #
        #
        #              14       4       3        8 = 0'
        #
        #
        #             2' = 13                7 = 5'
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
                trisAlt.twist_strip_I:     twist_stripI,
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
                trisAlt.twist_strip_I:      twist_stripI,
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
                trisAlt.twist_strip_I:		twist,
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
                trisAlt.twist_strip_I:		twist,
            }

    def printTrisAngles(this):
	# TODO: fix this function. Which angles to take (ie which faces) depends
	# on the triangle alternative.
	tris = this.triFs[this.edgeAlternative]
	# for non 1 loose
	# for i in range(0, len(tris) - 2, 2):
	d = 2
	# for 1 loose:
	d = 1
	for i in range(2):
	    norm0 = Geom3D.Triangle(
		this.baseShape.Vs[tris[i][0]],
		this.baseShape.Vs[tris[i][1]],
		this.baseShape.Vs[tris[i][2]],
	    ).normal(True)
	    print 'norm0 %d: ', norm0
	    norm1 = Geom3D.Triangle(
		this.baseShape.Vs[tris[i+d][0]],
		this.baseShape.Vs[tris[i+d][1]],
		this.baseShape.Vs[tris[i+d][2]],
	    ).normal(True)
	    print 'norm1 %d: ', norm1
	    inprod = norm0 * norm1
	    print 'Tris angle %d: %.6f degrees' % (i, math.acos(inprod) * Geom3D.Rad2Deg)
	print '------------' # TODO move out

class CtrlWin(Heptagons.FldHeptagonCtrlWin):
    def __init__(this, shape, canvas, *args, **kwargs):
	Heptagons.FldHeptagonCtrlWin.__init__(this,
	    shape, canvas,
	    3, # maxHeigth
	    [ # prePosLst
		Stringify[S_only_hepts0],
		Stringify[S_only_hepts1],
		Stringify[S_T8],
		Stringify[S_T24],
		Stringify[S_T32_0],
		Stringify[S_T32_1],
		Stringify[S_T32_2],
		Stringify[S_T48],
		Stringify[S_T56],
		Stringify[S_T80],

		Stringify[S_S12],
		Stringify[S_T8_S12],
		Stringify[S_S24],
		Stringify[S_T8_S24],
		Stringify[S_T24_S12],
		Stringify[S_T8_S36],
		Stringify[S_T32_S12],
		Stringify[S_T32_S24_0],
		Stringify[S_T32_S24_1],
		Stringify[S_T56_S12],

		Stringify[T8_0],
		Stringify[T16_0],
		Stringify[T16_1],
		Stringify[T16_2],
		Stringify[T16_3],
		Stringify[T24_0],
		Stringify[T24_1],
		Stringify[T32_0],
		Stringify[T40_0],
		Stringify[T40_1],
		Stringify[T40_2],
		Stringify[T40_3],
		Stringify[T64_0],
		Stringify[dyn_pos],
	    ],
	    Stringify,
	    *args, **kwargs
	)

    def showOnlyHepts(this):
	return this.prePos == Heptagons.only_hepts and not (
		this.trisFill == None
	    ) and not (
		this.trisFill & Heptagons.twist_bit == Heptagons.twist_bit)

    def showOnlyO3Tris(this):
	return this.prePos == Heptagons.only_xtra_o3s and not (
		this.trisFill == None
	    ) and not (
		this.trisFill & Heptagons.twist_bit == Heptagons.twist_bit)

    rDir = 'Data_FldHeptA4'
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

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
	glFrontFace(GL_CW)
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
