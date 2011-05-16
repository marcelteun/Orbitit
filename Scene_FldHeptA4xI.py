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
import string
import rgb
import Heptagons
import isometry
import Geom3D
import Scenes3D

from glob import glob
from OpenGL.GL import *

import Data_FldHeptA4xI
import GeomTypes
from GeomTypes import Rot3      as Rot
from GeomTypes import HalfTurn3 as HalfTurn
from GeomTypes import Vec3      as Vec

Title = 'Polyhedra with Folded Regular Heptagons A4xI'

V2 = math.sqrt(2)

trisAlt = Heptagons.TrisAlt()

dyn_pos		= Heptagons.dyn_pos
only_hepts      = Heptagons.only_hepts
only_xtra_o3s	= Heptagons.only_xtra_o3s
all_eq_tris	= Data_FldHeptA4xI.all_eq_tris
no_o3_tris	= Data_FldHeptA4xI.no_o3_tris
edge_1_1_V2_1	= Data_FldHeptA4xI.edge_1_1_V2_1
edge_1_V2_1_1	= Data_FldHeptA4xI.edge_1_V2_1_1
edge_V2_1_1_1	= Data_FldHeptA4xI.edge_V2_1_1_1
edge_V2_1_V2_1	= Data_FldHeptA4xI.edge_V2_1_V2_1
squares_24	= Data_FldHeptA4xI.squares_24
edge_0_1_1_1	= Data_FldHeptA4xI.edge_0_1_1_1
edge_0_1_V2_1	= Data_FldHeptA4xI.edge_0_1_V2_1
tris_24		= Data_FldHeptA4xI.tris_24
edge_1_1_0_1	= Data_FldHeptA4xI.edge_1_1_0_1
edge_1_0_1_1	= Data_FldHeptA4xI.edge_1_0_1_1
edge_V2_1_0_1	= Data_FldHeptA4xI.edge_V2_1_0_1
edge_V2_1_1_0	= Data_FldHeptA4xI.edge_V2_1_1_0
square_12	= Data_FldHeptA4xI.square_12
edge_0_V2_1_1   = Data_FldHeptA4xI.edge_0_V2_1_1

tris_16_0 = Heptagons.A4_bas + 1
tris_16_1 = Heptagons.A4_bas + 2
tris_16_2 = Heptagons.A4_bas + 3
tris_32   = Heptagons.A4_bas + 4
tris_40   = Heptagons.A4_bas + 5
anew = Heptagons.A4_bas + 6

Stringify = {
    dyn_pos:		'Enable Sliders',
    no_o3_tris:		'48 Triangles',
    all_eq_tris:	'All 80 Triangles Equilateral',
    only_xtra_o3s:	'8 Triangles (O3)',
    edge_V2_1_0_1:	'8 Triangles and 12 Folded Squares',
    edge_0_1_V2_1:	'8 Triangles and 24 Folded Squares',
    edge_V2_1_V2_1:	'8 Triangles and 36 Folded Squares',
    square_12:		'12 Folded Squares',
    tris_16_0:		'16 Triangles (A)',
    tris_16_1:		'16 Triangles (B)',
    tris_16_2:		'16 Triangles (C)',
    tris_24:		'24 Triangles',
    squares_24:		'24 Folded Squares',
    edge_V2_1_1_0:	'24 Triangles and 12 Folded Squares',
    tris_32:	        '32 Triangles',
    edge_1_1_0_1:	'32 Triangles (24 + 8) I',
    edge_1_0_1_1:	'32 Triangles (24 + 8) II',
    edge_0_V2_1_1:	'32 Triangles and 12 Folded Squares',
    edge_1_1_V2_1:	'32 Triangles and 24 Folded Squares: I',
    edge_1_V2_1_1:	'32 Triangles and 24 Folded Squares: II',
    tris_40:		'40 Triangles',
    edge_0_1_1_1:	'56 Triangles',
    edge_V2_1_1_1:	'56 Triangles and 12 Folded Squares',
    only_hepts:		'Just Heptagons',
    anew:		'new',
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
	this.posAngleMin = 0
	this.posAngleMax = math.pi/4
	this.posAngle = this.posAngleMin
        this.setEdgeAlternative(trisAlt.strip_1_loose, trisAlt.strip_1_loose)
	this.initArrs()
	this.setV()

    def getStatusStr(this):
        if this.updateShape:
            #print 'getStatusStr: forced setV'
            this.setV()
        Vs = this.baseVs
	Es = this.triEs[this.edgeAlternative]
	aLen = Vlen(Vs[Es[0]], Vs[Es[1]])
	bLen = Vlen(Vs[Es[2]], Vs[Es[3]])
	cLen = Vlen(Vs[Es[4]], Vs[Es[5]])
	Es = this.o3triEs[this.edgeAlternative]
	dLen = Vlen(Vs[Es[0]], Vs[Es[1]])
	if this.inclReflections:
	    s = 'T = %02.2f; |a|: %02.2f, |b|: %02.2f, |c|: %02.2f, |d|: %02.2f' % (
		    this.height, aLen, bLen, cLen, dLen
		)
	else:
	    Es = this.oppTriEs[this.oppEdgeAlternative]
	    opp_bLen = Vlen(Vs[Es[0]], Vs[Es[1]])
	    opp_cLen = Vlen(Vs[Es[2]], Vs[Es[3]])
	    Es = this.oppO3triEs[this.oppEdgeAlternative]
	    opp_dLen = Vlen(Vs[Es[0]], Vs[Es[1]])
	    s = 'T = %02.2f; |a|: %02.2f, |b|: %02.2f (%02.2f), |c|: %02.2f (%02.2f), |d|: %02.2f (%02.2f)' % (
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
        this.baseVs = Vs
        Es = []
        Fs = []
        Fs.extend(this.heptagon.Fs) # use extend to copy the list to Fs
        Es.extend(this.heptagon.Es) # use extend to copy the list to Fs
        this.heptagonsShape.setBaseVertexProperties(Vs = Vs)
        this.heptagonsShape.setBaseEdgeProperties(Es = Es)
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
		Es      = this.triEs[this.edgeAlternative][:]
		Fs      = this.triFs[this.edgeAlternative][:]
		Es.extend(this.oppTriEs[this.oppEdgeAlternative])
		Fs.extend(this.oppTriFs[this.oppEdgeAlternative])
                this.xtraTrisShape.setBaseVertexProperties(Vs = Vs)
                this.xtraTrisShape.setBaseEdgeProperties(Es = Es)
                this.xtraTrisShape.setBaseFaceProperties(
		    Fs = Fs,
                    colors = ([rgb.darkRed[:], rgb.yellow[:]],
                        this.triColIds[this.edgeAlternative])
                )
                theShapes.append(this.xtraTrisShape)
        this.showBaseOnly = not this.applySymmetry
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

	I_loose = [[2, 3, 7], [2, 7, 8]]
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
        this.triFs = {
                trisAlt.strip_1_loose:      strip_1_loose[:],
                trisAlt.strip_I:            stripI[:],
                trisAlt.strip_II:           stripII[:],
                trisAlt.star:               star[:],
                trisAlt.star_1_loose:       star_1_loose[:],
                trisAlt.alt_strip_1_loose:  strip_1_loose[:],
                trisAlt.alt_strip_I:        stripI[:],
                trisAlt.alt_strip_II:       stripII[:],
	}
	stdO3   = [1, 2, 9]
	altO3   = [2, 9, 11]  #TODO rm, see OOPS above...
        this.triFs[trisAlt.strip_1_loose].append(stdO3)
        this.triFs[trisAlt.strip_I].append(stdO3)
        this.triFs[trisAlt.strip_II].append(stdO3)
        this.triFs[trisAlt.alt_strip_1_loose].append(altO3)
        this.triFs[trisAlt.alt_strip_I].append(altO3)
        this.triFs[trisAlt.alt_strip_II].append(altO3)
	noLoose = [[3, 7, 8]]
	stripI  = [[5, 15, 14]]
	stripII = [[4, 5, 15], [4, 15, 14]]
	star    = [[5, 6, 14], [6, 15, 14]]
	strip_1_loose = stripI[:]
	star_1_loose  = star[:]
	stripI.extend(noLoose)
	star.extend(noLoose)
        this.oppTriFs = {
                trisAlt.strip_1_loose:      strip_1_loose[:],
                trisAlt.strip_I:            stripI[:],
                trisAlt.strip_II:           stripII[:],
                trisAlt.star:               star[:],
                trisAlt.star_1_loose:       star_1_loose[:],
                trisAlt.alt_strip_1_loose:  strip_1_loose[:],
                trisAlt.alt_strip_I:        stripI[:],
                trisAlt.alt_strip_II:       stripII[:],
	}
	stdO3   = [6, 15, 5]
	altO3   = [5, 17, 15]
        this.oppTriFs[trisAlt.strip_1_loose].append(stdO3)
        this.oppTriFs[trisAlt.strip_I].append(stdO3)
        this.oppTriFs[trisAlt.strip_II].append(stdO3)
        this.oppTriFs[trisAlt.alt_strip_1_loose].append(altO3)
        this.oppTriFs[trisAlt.alt_strip_I].append(altO3)
        this.oppTriFs[trisAlt.alt_strip_II].append(altO3)

	strip = [0, 1, 1, 1, 0, 0]
	loose = [0, 0, 1, 1, 0, 1]
	star1loose = [0, 1, 0, 1, 0, 1]
        this.triColIds = {
                trisAlt.strip_1_loose:		loose,
                trisAlt.strip_I:		strip,
                trisAlt.strip_II:		strip,
                trisAlt.star:			strip,
                trisAlt.star_1_loose:		star1loose,
                trisAlt.alt_strip_I:		strip,
                trisAlt.alt_strip_II:		strip,
                trisAlt.alt_strip_1_loose:	loose,
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
        this.o3triFs = {
                trisAlt.strip_1_loose:		[std],
                trisAlt.strip_I:		[std],
                trisAlt.strip_II:		[std],
                trisAlt.star:			[std],
                trisAlt.star_1_loose:		[std],
                trisAlt.alt_strip_I:		[alt],
                trisAlt.alt_strip_II:		[alt],
                trisAlt.alt_strip_1_loose:	[alt],
	    }
	std = [6, 16, 15]
	alt = [5, 18, 17]
        this.oppO3triFs = {
                trisAlt.strip_1_loose:		[std],
                trisAlt.strip_I:		[std],
                trisAlt.strip_II:		[std],
                trisAlt.star:			[std],
                trisAlt.star_1_loose:		[std],
                trisAlt.alt_strip_I:		[alt],
                trisAlt.alt_strip_II:		[alt],
                trisAlt.alt_strip_1_loose:	[alt],
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
        this.triEs = {
                trisAlt.strip_1_loose:     strip_1_loose,
                trisAlt.strip_I:           stripI,
                trisAlt.strip_II:          stripII,
                trisAlt.star:              star,
                trisAlt.star_1_loose:      star_1_loose,
                trisAlt.alt_strip_I:       stripI,
                trisAlt.alt_strip_II:      stripII,
                trisAlt.alt_strip_1_loose: strip_1_loose,
            }
	strip_1_loose = [5, 14, 5, 15]
	stripI        = [5, 14, 5, 15]
	stripII       = [4, 15, 5, 15]
	star          = [5, 14, 6, 14]
	star_1_loose  = [5, 14, 6, 14]
        this.oppTriEs = {
                trisAlt.strip_1_loose:     strip_1_loose,
                trisAlt.strip_I:           stripI,
                trisAlt.strip_II:          stripII,
                trisAlt.star:              star,
                trisAlt.star_1_loose:      star_1_loose,
                trisAlt.alt_strip_I:       stripI,
                trisAlt.alt_strip_II:      stripII,
                trisAlt.alt_strip_1_loose: strip_1_loose,
            }

	std = [1, 9, 9, 10, 10, 1]
	alt = [2, 11, 11, 12, 12, 2]
        this.o3triEs = {
                trisAlt.strip_1_loose:		std,
                trisAlt.strip_I:		std,
                trisAlt.strip_II:		std,
                trisAlt.star:			std,
                trisAlt.star_1_loose:		std,
                trisAlt.alt_strip_I:		alt,
                trisAlt.alt_strip_II:		alt,
                trisAlt.alt_strip_1_loose:	alt,
            }
	std = [6, 16, 16, 15, 15, 6]
	alt = [5, 18, 18, 17, 17, 5]
        this.oppO3triEs = {
                trisAlt.strip_1_loose:		std,
                trisAlt.strip_I:		std,
                trisAlt.strip_II:		std,
                trisAlt.star:			std,
                trisAlt.star_1_loose:		std,
                trisAlt.alt_strip_I:		alt,
                trisAlt.alt_strip_II:		alt,
                trisAlt.alt_strip_1_loose:	alt,
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
	    shape, (745, 765), canvas,
	    3, # maxHeigth
	    [ # prePosLst
		Stringify[only_hepts],
		Stringify[tris_16_0],
		Stringify[tris_16_1],
		Stringify[tris_16_2],
		Stringify[only_xtra_o3s],
		Stringify[square_12],
		Stringify[edge_V2_1_0_1],
		Stringify[tris_24],
		Stringify[squares_24],
		Stringify[tris_40],
		Stringify[tris_32],
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
		Stringify[anew],
	    ],
	    {
		True:  Data_FldHeptA4xI.specPos,
		False: [],
	    },
	    Stringify,
	    *args, **kwargs
	)

    def isntSpecialPos(this, sel):
	"""Check whether this selection is special for this triangle alternative
	"""
	return (this.shape.inclReflections and (
	    (
		sel == squares_24 and this.trisFill == trisAlt.strip_1_loose
	    ) or (this.foldMethod == Heptagons.foldMethod.parallel and (
		(
		    sel == edge_1_V2_1_1
		    and (
			this.trisFill == trisAlt.strip_1_loose
			or
			this.trisFill == trisAlt.star_1_loose
		    )
		)
		or
		(
		    (
			sel == tris_24
		    ) and (
			this.trisFill == trisAlt.strip_1_loose
			or
			this.trisAlt == trisAlt.star_1_loose
		    )
		)
	    ))
	))

    prePosStrToFileStrMap = {
	only_hepts:  '1_0_1_0_0_1_0',
	tris_16_0:   '1_0_1_0_0_1_1',
	tris_16_1:   '1_0_1_0_1_0_1',
	tris_24:     '1_0_1_0_1_1_0',
	tris_40:     '1_0_1_0_1_1_1',
	tris_16_2:   '1_1_0_1_0_1_0',
	tris_32:     '1_1_0_1_0_1_1',
	no_o3_tris:  '1_1_1_0_1_1_0',
	all_eq_tris: '1_1_1_1_1_1_1',
    }

    rDir = 'Data_FldHeptA4'
    rPre = 'frh-roots'

    def mapPrePosStrToFileStr(this, prePosId):
	try:
	    s = this.prePosStrToFileStrMap[prePosId]
	except KeyError:
	    s = this.stringify[prePosId]
	return s

    def mapTrisFill(this, trisFillId):
	tStr = trisAlt.stringify[trisFillId]
	t = string.join(tStr.split(), '_').lower().replace('ernative', '')
	t = t.replace('_ii', '_II')
	t = t.replace('_i', '_I')
	return t

    def isPrePosValid(this, prePosId):
	# This means that files with empty results should be filtered out from
	# the directory.
	if this.shape.inclReflections:
	    return Heptagons.FldHeptagonCtrlWin.isPrePosValid(this, prePosId)
	else:
	    s = this.mapPrePosStrToFileStr(prePosId)
	    return glob('%s/%s-%s-*' % (this.rDir, this.rPre, s)) != []

    def isFoldValid(this, foldMethod):
	if this.shape.inclReflections:
	    return Heptagons.FldHeptagonCtrlWin.isFoldValid(this, foldMethod)
	else:
	    p = this.mapPrePosStrToFileStr(this.prePos)
	    f = Heptagons.FoldName[foldMethod].lower()
	    return glob(
		    '%s/%s-%s-fld_%s.*' % (this.rDir, this.rPre, p, f)
		) != []

    def isTrisFillValid(this, trisFillId):
	if this.shape.inclReflections:
	    return Heptagons.FldHeptagonCtrlWin.isTrisFillValid(this, trisFillId)
	else:
	    if type(trisFillId) == int:
		return False
	    p = this.mapPrePosStrToFileStr(this.prePos)
	    f = Heptagons.FoldName[this.foldMethod].lower()
	    t0 = this.mapTrisFill(trisFillId[0])
	    t1 = this.mapTrisFill(trisFillId[1])
	    return glob('%s/%s-%s-fld_%s*-%s-opp_%s.*' % (
		    this.rDir, this.rPre, p, f, t0, t1)
		) != []

    @property
    def stdPrePos(this):
	prePosId = this.prePos
	if prePosId == dyn_pos:
	    return []
	if this.shape.inclReflections:
	    return this.specPos[this.shape.inclReflections][prePosId][
						this.foldMethod][this.trisFill]
	else:
	    filename = '%s/%s-%s-fld_%s.0-%s-opp_%s.py' % (
			this.rDir, this.rPre,
			this.mapPrePosStrToFileStr(this.prePos),
			Heptagons.FoldName[this.foldMethod].lower(),
			this.mapTrisFill(this.trisFill),
			this.mapTrisFill(this.oppTrisFill)
		    )
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

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
