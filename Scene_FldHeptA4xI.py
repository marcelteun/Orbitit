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
# $Log: Scene_RegHeptS4A4Eg.py,v $
# Revision 1.4  2008/10/04 21:38:16  marcelteun
# fix canvas position of regular heptagons
#
# Revision 1.3  2008/10/04 21:13:29  marcelteun
# fix for undestroyed boxes in Ubuntu Hardy Heron
#
# Revision 1.2  2008/10/03 20:09:51  marcelteun
# Bridges2008 changes: window position
#
# Revision 1.1.1.1  2008/07/05 10:35:43  marcelteun
# Imported sources
#
# Revision 1.1  2008/06/18 05:31:54  teun
# Initial revision
#
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

Title = 'Polyhedra with Folded Regular Heptagons A4xI'

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
    def get(this, str):
	for k,v in Stringify.iteritems():
	    if v == str:
		return k
	return None

trisAlt = TrisAlt()

dyn_pos		= -1
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
only_hepts	= 10
only_o3_tris	= 11
edge_1_1_0_1	= 12
edge_1_0_1_1	= 13
square_o3_tris	= 14
edge_V2_1_1_0	= 15
square_12	= 16
edge_0_V2_1_1   = 17

Stringify = {
    dyn_pos:		'Enable Sliders',
    no_o3_tris:		'48 Triangles',
    all_eq_tris:	'All 80 Triangles Equilateral',
    only_o3_tris:	'8 Triangles (O3)',
    square_o3_tris:	'8 Triangles and 12 Folded Squares',
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

class Shape(Geom3D.IsometricShape):
    def __init__(this, *args, **kwargs):
        Geom3D.IsometricShape.__init__(this,
            Vs = [], Fs = [],
            directIsometries = isometry.A4(),
            unfoldOrbit = True,
            name = 'FoldedRegHeptS4xI'
        )
        this.heptagon = Heptagons.RegularHeptagon()
        #this.dbgPrn = True
        this.theColors     = [
                rgb.oliveDrab[:],
                rgb.brown[:],
                rgb.yellow[:],
                rgb.cyan[:]
            ]
        this.angle = 1.2
        this.fold1 = 0.0
        this.fold2 = 0.0
	this.foldHeptagon = Heptagons.foldMethod.parallel
        this.height = 2.3
        this.applySymmetry = True
        this.addTriangles = True
        this.onlyO3Triangles = False
        this.useCulling = False
        this.edgeAlternative = trisAlt.strip_1_loose

        #this.lightPosition = [-50., 50., 200., 0.]
        #this.lightAmbient  = [0.25, 0.25, 0.25, 1.]
        #this.lightDiffuse  = [1., 1., 1., 1.]
        #this.materialSpec  = [0., 0., 0., 0.]
        #this.showBaseOnly  = True
        this.initArrs()
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
        #angle = Geom3D.Rad2Deg * this.angle
        s = 'Angle = %01.2f rad, fold1 = %01.2f rad, fold2 = %01.2f rad, T = %02.2f' % (
                this.angle,
                this.fold1,
                this.fold2,
                this.height
            )
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
        #print this.name, "setV"
        #this.heptagon.foldParallel(this.fold1, this.fold2)
        #this.heptagon.foldTrapezium(this.fold1, this.fold2)
        # The angle has to be adjusted for historical reasons...
	# TODO: fix me
	if this.foldHeptagon == Heptagons.foldMethod.parallel:
	    this.heptagon.foldParallel(-this.fold1, -this.fold2, keepV0 = False)
	else:
	    this.heptagon.fold(this.fold1, this.fold2,
		    keepV0 = False, fold = this.foldHeptagon)
	#print 'norm V0-V1: ', (this.heptagon.Vs[1]-this.heptagon.Vs[0]).squareNorm()
	#print 'norm V1-V2: ', (this.heptagon.Vs[1]-this.heptagon.Vs[2]).squareNorm()
	#print 'norm V2-V3: ', (this.heptagon.Vs[3]-this.heptagon.Vs[2]).squareNorm()
	#print 'norm V3-V4: ', (this.heptagon.Vs[3]-this.heptagon.Vs[4]).squareNorm()
        this.heptagon.translate(Heptagons.H*GeomTypes.uy)
        # The angle has to be adjusted for historical reasons...
        this.heptagon.rotate(-GeomTypes.ux, GeomTypes.qTurn - this.angle)
        this.heptagon.translate(this.height*GeomTypes.uz)
        Vs = this.heptagon.Vs[:]
        #
	# 15                                 14 = 2'
        #                     0
        #    (17) 13                      12 = o3c (alt 16)
        #              6             1
        #
        #      11                           9 = 1'
        #
        #            5                 2
        #
        #
        #        10       4       3        8 = 0'
        #
        #
        #                              7 = 6'

        Rr = Rot(axis = Vec([ 1, 1, 1]), angle = GeomTypes.tTurn)
        Rl = Rot(axis = Vec([-1, 1, 1]), angle = -GeomTypes.tTurn)
        Vs.append(Vec([Vs[2][0], -Vs[2][1], Vs[2][2]]))        # Vs[7]
        Vs.append(Rr * Vs[0])                                  # Vs[8]
        Vs.append(Rr * Vs[1])                                  # Vs[9]
        Vs.append(Rl * Vs[0])                                  # Vs[10]
        Vs.append(Rl * Vs[6])                                  # Vs[11]
        # V12 and V13 are the centres of the triangle on the O3 axis.
        # for V12 the O3 axis is (1, 1, 1). So we need to find the n*(1, 1, 1)
        # that lies in the face. This can found by projecting V12 straight onto
        # this axis, or we can rotate 180 degrees and take the average:
        halfTurn = HalfTurn(Vec([1, 1, 1]))
        Vs.append((Vs[1] + halfTurn*Vs[1]) / 2)                # Vs[12]
        halfTurn = HalfTurn(Vec([-1, 1, 1]))
        Vs.append((Vs[6] + halfTurn*Vs[6]) / 2)                # Vs[13]
        this.setBaseVertexProperties(Vs = Vs)
        Vs.append(Rr * Vs[2])                                  # Vs[14]
        Vs.append(Rl * Vs[5])                                  # Vs[15]
        halfTurn = HalfTurn(Vec([1, 1, 1]))
        Vs.append((Vs[2] + halfTurn*Vs[2]) / 2)                # Vs[16]
        halfTurn = HalfTurn(Vec([-1, 1, 1]))
        Vs.append((Vs[5] + halfTurn*Vs[5]) / 2)                # Vs[17]
        Es = []
        Fs = []
        Fs.extend(this.heptagon.Fs) # use extend to copy the list to Fs
        Es.extend(this.heptagon.Es) # use extend to copy the list to Fs
        colIds = [0 for f in Fs]
        if this.addTriangles:
	    Fs.extend(this.o3triFs[this.edgeAlternative]) # eql triangles
	    Es.extend(this.o3triEs[this.edgeAlternative])
            colIds.extend([3, 3])
	    if (not this.onlyO3Triangles):
		Fs.extend(this.triFs[this.edgeAlternative])
		colIds.extend(this.triColIds[this.edgeAlternative])
		Es.extend(this.triEs[this.edgeAlternative])

        this.setBaseEdgeProperties(Es = Es)
        this.setBaseFaceProperties(Fs = Fs, colors = (this.theColors, colIds))
        this.showBaseOnly = not this.applySymmetry
        this.updateShape = False

    def initArrs(this):
        print this.name, "initArrs"
        this.triFs = {
                trisAlt.strip_1_loose: [
                    [2, 3, 7], [2, 7, 8],
                    [2, 8, 9], [5, 11, 10],
                    [1, 2, 9], [5, 6, 11],
                ],
                trisAlt.strip_I: [
                    [2, 3, 8], [4, 5, 10],
                    [2, 8, 9], [5, 11, 10],
                    [1, 2, 9], [5, 6, 11],
                ],

                trisAlt.strip_II: [
                    [3, 8, 9], [4, 11, 10],
                    [2, 3, 9], [4, 5, 11],
                    [1, 2, 9], [5, 6, 11],
                ],
                trisAlt.star: [
                    [2, 3, 8], [4, 5, 10],
                    [1, 2, 8], [5, 6, 10],
                    [1, 8, 9], [6, 11, 10]
                ],
                trisAlt.star_1_loose: [
                    [2, 3, 7], [2, 7, 8],
                    [1, 2, 8], [5, 6, 10],
                    [1, 8, 9], [6, 11, 10]
                ],
                trisAlt.alt_strip_I: [
                    [2, 3, 8], [4, 5, 10],
                    [2, 8, 9], [5, 11, 10],
                    [2, 9, 14], [5, 15, 11]
                ],
                trisAlt.alt_strip_II: [
                    [3, 8, 9], [4, 11, 10],
                    [2, 3, 9], [4, 5, 11],
                    [2, 9, 14], [5, 15, 11]
                ],
                trisAlt.alt_strip_1_loose: [
                    [2, 3, 7], [2, 7, 8],
                    [2, 8, 9], [5, 11, 10],
                    [2, 9, 14], [5, 15, 11]
                ],
            }
	# 15                                 14 = 2'
        #                     0
        #    (17) 13                      12 = o3c (alt 16)
        #              6             1
        #
        #      11                           9 = 1'
        #
        #            5                 2
        #
        #
        #        10       4       3        8 = 0'
        #
        #
        #                              7 = 6'
        this.o3triFs = {
                trisAlt.strip_1_loose:		[[1, 9, 12], [6, 13, 11]],
                trisAlt.strip_I:		[[1, 9, 12], [6, 13, 11]],
                trisAlt.strip_II:		[[1, 9, 12], [6, 13, 11]],
                trisAlt.star:			[[1, 9, 12], [6, 13, 11]],
                trisAlt.star_1_loose:		[[1, 9, 12], [6, 13, 11]],
                trisAlt.alt_strip_I:		[[2, 14, 16], [5, 17, 15]],
                trisAlt.alt_strip_II:		[[2, 14, 16], [5, 17, 15]],
                trisAlt.alt_strip_1_loose:	[[2, 14, 16], [5, 17, 15]],
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
                    2, 7, 2, 8, 2, 9,
                    5, 10, 5, 11,
                ],
                trisAlt.strip_I: [
                    3, 8, 2, 8, 2, 9,
                    5, 10, 5, 11,
                ],
                trisAlt.strip_II: [
                    3, 8, 3, 9, 2, 9,
                    4, 11, 5, 11,
                ],
                trisAlt.star: [
                    3, 8, 2, 8, 1, 8,
                    5, 10, 6, 10,
                ],
                trisAlt.star_1_loose: [
                    2, 7, 2, 8, 1, 8,
                    5, 10, 6, 10,
                ],
                trisAlt.alt_strip_I: [
                    3, 8, 2, 8, 2, 9,
                    5, 10, 5, 11,
                ],
                trisAlt.alt_strip_II: [
                    3, 8, 3, 9, 2, 9,
                    4, 11, 5, 11,
                ],
                trisAlt.alt_strip_1_loose: [
                    2, 7, 2, 8, 2, 9,
                    5, 10, 5, 11,
                ],
            }
        this.o3triEs = {
                trisAlt.strip_1_loose:		[1, 9, 6, 11],
                trisAlt.strip_I:		[1, 9, 6, 11],
                trisAlt.strip_II:		[1, 9, 6, 11],
                trisAlt.star:			[1, 9, 6, 11],
                trisAlt.star_1_loose:		[1, 9, 6, 11],
                trisAlt.alt_strip_I:		[2, 14, 5, 15],
                trisAlt.alt_strip_II:		[2, 14, 5, 15],
                trisAlt.alt_strip_1_loose:	[2, 14, 5, 15],
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

class CtrlWin(wx.Frame):
    def __init__(this, shape, canvas, *args, **kwargs):
        size = (745, 765)
        # TODO assert (type(shape) == type(RegHeptagonShape()))
        this.shape = shape
        this.canvas = canvas
        wx.Frame.__init__(this, *args, **kwargs)
        this.panel = wx.Panel(this, -1)
        this.statusBar = this.CreateStatusBar()
	#this.foldMethod = Heptagons.foldMethod.parallel
	this.foldMethod = Heptagons.foldMethod.triangle
	this.restoreTris = False
	this.restoreO3Tris = False
	this.shape.foldHeptagon = this.foldMethod
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

        this.specPosIndex = 0
        this.specPos = {
	    only_hepts: {
		# Note: all triangle variants are the same:
		Heptagons.foldMethod.parallel: {
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.parallel],
		    trisAlt.strip_I:       OnlyHeptagons[Heptagons.foldMethod.parallel],
		    trisAlt.star:          OnlyHeptagons[Heptagons.foldMethod.parallel],
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.parallel],
                },
                Heptagons.foldMethod.w: {
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.w],
		    trisAlt.strip_I:       OnlyHeptagons[Heptagons.foldMethod.w],
		    trisAlt.star:          OnlyHeptagons[Heptagons.foldMethod.w],
		    trisAlt.strip_1_loose: OnlyHeptagons[Heptagons.foldMethod.w],
                },
		Heptagons.foldMethod.star: {
		    trisAlt.alt_strip_II: OnlyHeptagons[Heptagons.foldMethod.star],
                },
	    },
	    only_o3_tris:   OnlyO3Triangles,
	    edge_1_1_0_1:   Pos32TrianglesI,
	    edge_1_0_1_1:   Pos32TrianglesII,
	    square_o3_tris: FoldedSquareAndO3Triangle,
	    edge_V2_1_1_0:  FoldedSquareAnd1TriangleType,
	    square_12:      Squares12,
	    tris_24:        Tris24,
	    all_eq_tris:    AllEquilateralTris,
	    no_o3_tris:     NoO3Triangles,
	    squares_24:     FoldedSquares_0,
	    edge_1_1_V2_1:  E1_1_V2_1,
	    edge_1_V2_1_1:  E1_V2_1_1,
	    edge_V2_1_1_1:  EV2_1_1_1,
	    edge_V2_1_V2_1: EV2_1_V2_1,
	    edge_0_1_1_1: E0_1_1_1,
	    edge_0_V2_1_1: E0_V2_1_1,
	    edge_0_1_V2_1: E0_1_V2_1,
	}

    def createControlsSizer(this):
        this.heightF = 10 # slider step factor, or: 1 / slider step
        this.maxHeight = 3

        this.Guis = []

        # static adjustments
	l = this.edgeChoicesList = [
	    Stringify[trisAlt.strip_1_loose],
	    Stringify[trisAlt.strip_I],
	    Stringify[trisAlt.strip_II],
	    Stringify[trisAlt.star],
	    Stringify[trisAlt.star_1_loose],
	    Stringify[trisAlt.alt_strip_I],
	    Stringify[trisAlt.alt_strip_II],
	    Stringify[trisAlt.alt_strip_1_loose],
	]
	this.edgeChoicesListItems = [
	    trisAlt.get(l[i]) for i in range(len(l))
	]
        this.trisAltGui = wx.RadioBox(this.panel,
                label = 'Triangle Fill Alternative',
                style = wx.RA_VERTICAL,
                choices = this.edgeChoicesList
            )
        this.Guis.append(this.trisAltGui)
        this.trisAltGui.Bind(wx.EVT_RADIOBOX, this.onTriangleAlt)
        this.trisAlt = this.edgeChoicesListItems[0]
        this.shape.setEdgeAlternative(this.trisAlt)

        # View Settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        this.applySymGui = wx.CheckBox(this.panel, label = 'Apply Symmetry')
        this.Guis.append(this.applySymGui)
        this.applySymGui.SetValue(this.shape.applySymmetry)
        this.applySymGui.Bind(wx.EVT_CHECKBOX, this.onApplySym)
        this.addTrisGui = wx.CheckBox(this.panel, label = 'Show Triangles')
        this.Guis.append(this.addTrisGui)
        this.addTrisGui.SetValue(this.shape.addTriangles)
        this.addTrisGui.Bind(wx.EVT_CHECKBOX, this.onAddTriangles)

        # static adjustments
	l = this.foldMethodList = [
	    Heptagons.FoldName[Heptagons.foldMethod.parallel],
	    Heptagons.FoldName[Heptagons.foldMethod.triangle],
	    Heptagons.FoldName[Heptagons.foldMethod.star],
	    Heptagons.FoldName[Heptagons.foldMethod.w],
	    Heptagons.FoldName[Heptagons.foldMethod.trapezium],
	]
	this.foldMethodListItems = [
	    Heptagons.foldMethod.get(l[i]) for i in range(len(l))
	]
        this.foldMethodGui = wx.RadioBox(this.panel,
                label = 'Heptagon Fold Method',
                style = wx.RA_VERTICAL,
                choices = this.foldMethodList
            )
	for i in range(len(this.foldMethodList)):
	    if (this.foldMethodList[i] == Heptagons.FoldName[this.foldMethod]):
		this.foldMethodGui.SetSelection(i)
        this.Guis.append(this.foldMethodGui)
        this.foldMethodGui.Bind(wx.EVT_RADIOBOX, this.onFoldMethod)

	# predefined positions
        this.prePosLst = [
		Stringify[only_hepts],
		Stringify[only_o3_tris],
		Stringify[square_12],
		Stringify[square_o3_tris],
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
            ]
        this.prePosGui = wx.RadioBox(this.panel,
                label = 'Only Regular Faces with:',
                style = wx.RA_VERTICAL,
                choices = this.prePosLst
            )
	# Don't hardcode which index is dyn_pos, I might reorder the item list
	# one time, and will probably forget to update the default selection..
	for i in range(len(this.prePosLst)):
	    if (this.prePosLst[i] == Stringify[dyn_pos]):
		this.prePosGui.SetSelection(i)
        this.Guis.append(this.prePosGui)
        this.prePosGui.Bind(wx.EVT_RADIOBOX, this.onPrePos)
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
        this.angleGui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.angle,
                minValue = -180,
                maxValue =  180,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.angleGui)
        this.angleGui.Bind(wx.EVT_SLIDER, this.onAngle)
        this.fold1Gui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.fold1,
                minValue = -180,
                maxValue =  180,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.fold1Gui)
        this.fold1Gui.Bind(wx.EVT_SLIDER, this.onFold1)
        this.fold2Gui = wx.Slider(
                this.panel,
                value = Geom3D.Rad2Deg * this.shape.fold2,
                minValue = -180,
                maxValue =  180,
		style = wx.SL_HORIZONTAL | wx.SL_LABELS
            )
        this.Guis.append(this.fold2Gui)
        this.fold2Gui.Bind(wx.EVT_SLIDER, this.onFold2)
        this.heightGui = wx.Slider(
                this.panel,
                value = this.maxHeight - this.shape.height*this.heightF,
                minValue = -this.maxHeight * this.heightF,
                maxValue = this.maxHeight * this.heightF,
		style = wx.SL_VERTICAL
            )
        this.Guis.append(this.heightGui)
        this.heightGui.Bind(wx.EVT_SLIDER, this.onHeight)


        # Sizers
        this.Boxes = []

        # view settings
        this.Boxes.append(wx.StaticBox(this.panel, label = 'View Settings'))
        settingsSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        settingsSizer.Add(this.applySymGui, 0, wx.EXPAND)
        settingsSizer.Add(this.addTrisGui, 0, wx.EXPAND)
        settingsSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        statSizer = wx.BoxSizer(wx.HORIZONTAL)
        statSizer.Add(this.foldMethodGui, 0, wx.EXPAND)
        statSizer.Add(this.trisAltGui, 0, wx.EXPAND)
        statSizer.Add(settingsSizer, 0, wx.EXPAND)
        statSizer.Add(wx.BoxSizer(), 1, wx.EXPAND)

        posSizerSubH = wx.BoxSizer(wx.HORIZONTAL)
        posSizerSubH.Add(this.firstButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.prevButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.nrTxt, 1, wx.EXPAND)
        posSizerSubH.Add(this.nextButton, 1, wx.EXPAND)
        posSizerSubH.Add(this.lastButton, 1, wx.EXPAND)
        posSizerSubV = wx.BoxSizer(wx.VERTICAL)
        posSizerSubV.Add(this.prePosGui, 0, wx.EXPAND)
        posSizerSubV.Add(posSizerSubH, 0, wx.EXPAND)
        posSizerSubV.Add(wx.BoxSizer(), 1, wx.EXPAND)
        posSizerH = wx.BoxSizer(wx.HORIZONTAL)
        posSizerH.Add(posSizerSubV, 2, wx.EXPAND)

        # dynamic adjustments
        specPosDynamic = wx.BoxSizer(wx.VERTICAL)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Dihedral Angle (Degrees)'))
        angleSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        angleSizer.Add(this.angleGui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Fold 1 Angle (Degrees)'))
        fold1Sizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        fold1Sizer.Add(this.fold1Gui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Fold 2 Angle (Degrees)'))
        fold2Sizer = wx.StaticBoxSizer(this.Boxes[-1], wx.HORIZONTAL)
        fold2Sizer.Add(this.fold2Gui, 1, wx.EXPAND)
        this.Boxes.append(wx.StaticBox(this.panel, label = 'Offset T'))
        heightSizer = wx.StaticBoxSizer(this.Boxes[-1], wx.VERTICAL)
        heightSizer.Add(this.heightGui, 1, wx.EXPAND)
        specPosDynamic.Add(angleSizer, 0, wx.EXPAND)
        specPosDynamic.Add(fold1Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(fold2Sizer, 0, wx.EXPAND)
        specPosDynamic.Add(wx.BoxSizer(), 1, wx.EXPAND)
        posSizerH.Add(specPosDynamic, 3, wx.EXPAND)
        posSizerH.Add(heightSizer, 1, wx.EXPAND)

        mainVSizer = wx.BoxSizer(wx.VERTICAL)
        mainVSizer.Add(statSizer, 0, wx.EXPAND)
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

    def onAngle(this, event):
	#print this.GetSize()
        this.shape.setAngle(Geom3D.Deg2Rad * this.angleGui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onFold1(this, event):
        this.shape.setFold1(Geom3D.Deg2Rad * this.fold1Gui.GetValue())
        this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()
        event.Skip()

    def onFold2(this, event):
        this.shape.setFold2(Geom3D.Deg2Rad * this.fold2Gui.GetValue())
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
        this.shape.addTriangles  = this.addTrisGui.IsChecked()
        this.shape.updateShape = True
        this.canvas.paint()

    def onTriangleAlt(this, event):
        this.trisAlt = this.edgeChoicesListItems[this.trisAltGui.GetSelection()]
        this.shape.setEdgeAlternative(this.trisAlt)
        if this.prePosGui.GetSelection() != len(this.prePosLst) - 1:
            this.onPrePos()
        else:
            this.statusBar.SetStatusText(this.shape.getStatusStr())
        this.canvas.paint()

    def onFoldMethod(this, event):
        this.foldMethod = this.foldMethodListItems[
		this.foldMethodGui.GetSelection()
	    ]
	this.shape.setFoldMethod(this.foldMethod)
        if this.prePosGui.GetSelection() != len(this.prePosLst) - 1:
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
        prePosStr = this.prePosLst[this.prePosGui.GetSelection()]
	for k,v in Stringify.iteritems():
	    if v == prePosStr:
		return k
	return dyn_pos

    def onPrev(this, event = None):
        prePosIndex = this.getPrePos()
        if prePosIndex != dyn_pos:
            if this.specPosIndex > 0:
                this.specPosIndex -= 1
	    elif this.specPosIndex == -1:
                this.specPosIndex = len(
			this.specPos[prePosIndex][this.foldMethod][this.trisAlt]
		    ) - 2
	    # else prePosIndex == 0 : first one selected don't scroll around
            this.onPrePos()

    def onNext(this, event = None):
        prePosIndex = this.getPrePos()
        if prePosIndex != dyn_pos:
	    try:
		maxI = len(
			this.specPos[prePosIndex][this.foldMethod][this.trisAlt]
		    ) - 1
		if this.specPosIndex >= 0:
		    if this.specPosIndex < maxI - 1:
			this.specPosIndex += 1
		    else:
		        this.specPosIndex = -1 # select last
	    except KeyError:
		pass
	    this.onPrePos()

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
	    this.shape.addTriangles = False
	    # if legal fold method select first fitting triangle alternative
	    if this.foldMethod in this.specPos[sel]:
		for k in this.specPos[sel][this.foldMethod].iterkeys():
		    for i in range(len(this.edgeChoicesListItems)):
			if this.edgeChoicesListItems[i] == k:
			    this.trisAltGui.SetSelection(i)
			    this.trisAlt = k
			    this.shape.setEdgeAlternative(k)
			    break
		    break
	    this.addTrisGui.Disable()
	    this.trisAltGui.Disable()
	    this.restoreTris = True
	elif (this.restoreTris):
	    this.restoreTris = False
	    this.trisAltGui.Enable()
	    this.addTrisGui.Enable()
	    this.shape.addTriangles  = this.addTrisGui.IsChecked()
	    # needed for sel == dyn_pos
	    this.shape.updateShape = True
	if (sel == only_o3_tris):
	    this.shape.onlyO3Triangles = True
	    this.restoreO3Tris = True
	elif (this.restoreO3Tris):
	    this.restoreO3Tris = False
	    this.shape.onlyO3Triangles = False
	    # needed for sel == dyn_pos
	    this.shape.updateShape = True
        aVal = this.aNone
        tVal = this.tNone
	c = this.shape
        if sel == dyn_pos:
	    this.angleGui.Enable()
	    this.fold1Gui.Enable()
	    this.fold2Gui.Enable()
	    this.heightGui.Enable()
	    this.angleGui.SetValue(Geom3D.Rad2Deg * c.angle)
	    this.fold1Gui.SetValue(Geom3D.Rad2Deg * c.fold1)
	    this.fold2Gui.SetValue(Geom3D.Rad2Deg * c.fold2)
	    this.heightGui.SetValue(
		this.maxHeight - this.heightF*c.height)
	    # enable all folding and triangle alternatives:
	    for i in range(len(this.foldMethodList)):
		this.foldMethodGui.ShowItem(i, True)
	    for i in range(len(this.edgeChoicesList)):
		this.trisAltGui.ShowItem(i, True)
	else:
            fld1 = this.fld1None
            fld2 = this.fld2None
	    nrPos = 0

	    # Ensure this.specPosIndex in range:
	    try:
		nrPos = len(this.specPos[sel][this.foldMethod][this.trisAlt])
		maxI = nrPos - 1
		if (this.specPosIndex > maxI):
		    this.specPosIndex = maxI
		# keep -1 (last) so switching triangle alternative will keep
		# last selection.
		elif (this.specPosIndex < -1):
		    this.specPosIndex = maxI - 1
	    except KeyError:
		pass

	    # Disable / enable appropriate folding methods.
	    for i in range(len(this.foldMethodList)):
		method = this.foldMethodListItems[i]
		this.foldMethodGui.ShowItem(i, method in this.specPos[sel])
		# leave up to the user to decide which folding method to choose
		# in case the selected one was disabled.

	    # Disable / enable appropriate triangle alternatives.
	    # if the selected folding has valid solutions anyway
	    if this.foldMethod in this.specPos[sel]:
		for i in range(len(this.edgeChoicesList)):
		    alt = this.edgeChoicesListItems[i]
		    this.trisAltGui.ShowItem(
			i, alt in this.specPos[sel][this.foldMethod])

	    try:
		if this.specPos[sel][this.foldMethod][this.trisAlt] != []:
		    tVal = this.specPos[sel][this.foldMethod][this.trisAlt][
			    this.specPosIndex][0]
		    aVal = this.specPos[sel][this.foldMethod][this.trisAlt][
			    this.specPosIndex][1]
		    fld1 = this.specPos[sel][this.foldMethod][this.trisAlt][
			    this.specPosIndex][2]
		    fld2 = this.specPos[sel][this.foldMethod][this.trisAlt][
			    this.specPosIndex][3]
	    except KeyError:
	        pass

            c.setAngle(aVal)
            c.setHeight(tVal)
            c.setFold1(fld1)
            c.setFold2(fld2)
	    this.angleGui.SetValue(0)
	    this.fold1Gui.SetValue(0)
	    this.fold2Gui.SetValue(0)
	    this.heightGui.SetValue(0)
	    this.angleGui.Disable()
	    this.fold1Gui.Disable()
	    this.fold2Gui.Disable()
	    this.heightGui.Disable()
            if ( tVal == this.tNone and aVal == this.aNone and
		fld1 == this.fld1None and fld2 == this.fld2None
                ):
		if (sel == only_hepts or sel == only_o3_tris):
		    txt = 'No solution for this folding method'
		else:
		    txt = 'No solution for this triangle alternative'
                this.statusBar.SetStatusText(txt)
	    elif (sel == squares_24 and (
		    this.trisAlt == trisAlt.strip_1_loose
		    #or
		    #this.trisAlt == trisAlt.star
		) or (this.foldMethod == Heptagons.foldMethod.parallel and (
		    (
			sel == edge_1_V2_1_1
			and (
			    this.trisAlt == trisAlt.strip_1_loose
			    or
			    this.trisAlt == trisAlt.star_1_loose
			)
		    )
		    or
		    (
			(
			    sel == tris_24
			) and (
			    this.trisAlt == trisAlt.strip_1_loose
			    or
			    this.trisAlt == trisAlt.star_1_loose
			)
		    )
		))
	    ):

		this.statusBar.SetStatusText('Doesnot mean anything special for this triangle alternative')
	    else:
		if this.specPosIndex == -1:
		    nr = nrPos
		else:
		    nr = this.specPosIndex + 1
		this.nrTxt.SetLabel('%d/%d' % (nr, nrPos))
		this.statusBar.SetStatusText(c.getStatusStr())
		#this.shape.printTrisAngles()
        this.canvas.paint()

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)

###############################################################################
par_lst = [
    [1.31032278994319, 0.0, -1.96281693322690, -2.21106088677011],
    [-0.25334017499287, 3.14159265358979, 1.17877572036290, -2.21106088677011],
    [0.49161494586165, 3.14159265358979, 1.96281693322690, -0.93053176681969],
    [2.05527791079771, 0.0, -1.17877572036290, -0.93053176681969],
]
w_lst = [
    [-1.88684867999274, -2.67584321353804, -3.12832055742152, 1.95445445160646],
    [-1.32233321681047, -2.96718000300201, -1.18325074727722, 1.66830153628249],
    [1.78896216719296, 0.48746365476050, -1.69302246933137, -1.51369336968900],
    [2.38038493067972, 0.69307373318694, -0.56874630089938, -0.88243623639725],
]
star_lst = [
    [-0.74461021372109015, -2.9818815182710203, 2.7722011165143075, -1.6269361079388478],
    [-0.62171047473743957, -2.3850856066677051, 2.9797255199248309, 2.2122365867684177],
    [-0.55610249451280391, -2.609660225893911, -1.5658217693927483, -2.6032863388083642],
    [-0.893811200268113, -2.1240091326797543, -2.2219575336393387, 0.79799125365158663],
    [1.0540892657192353, 1.0743008888823, -1.8744609728684303, -2.6184266217442596],
    [1.3845570493440107, 1.4469702342451671, -1.3161975058771898, -0.86544404605462155],
]
OnlyHeptagons = {
    Heptagons.foldMethod.parallel: par_lst,
    Heptagons.foldMethod.star: star_lst,
    Heptagons.foldMethod.w: w_lst,
    # none found for the others,... :(
}

###############################################################################
star_strip_1loose_lst = [
    [0.84975071885401, 0.03258865423167, -3.12349873513056, -2.08248775924176],
    [1.20314417264408, 0.77985326936849, -2.50872875342765, 1.24844200718763],
    [-1.31765702327378, -2.64607621750711, -2.83090846517921, -2.32329214321773],
    [-1.56388800687524, -2.23628764769890, -2.15503782246175, 0.68864756632488],
    [1.69897719524520, 0.79879405476155, -1.11700300139483, -2.40716658093201],
    [1.73370652570266, 0.92947412884704, -1.79681694851064, 0.07697174428360],
]
w_strip_1loose_lst = [
    [-1.06477181882094, 2.72676440217031, 1.75383477143902, -1.73992185141339],
    [-1.06477181882094, -2.63614030012276, -1.75383477143902, 1.53360929714567],
    [-1.57368930164138, 3.09953886694822, 1.75383477143902, 2.45733414914631],
    [1.60113568148258, -0.03111011127019, 1.75383477143902, 2.51073779584634],
    [1.73150288973684, 0.00840597131687, 1.75383477143902, 2.92366617854627],
    [-1.57368930164138, -2.26336583534485, -1.75383477143902, -0.55232000947422],
    [1.60113568148258, 0.88917049361632, -1.75383477143902, -0.49891636277419],
    [1.73150288973685, 0.92868657620339, -1.75383477143902, -0.08598798007425],
]
tria_strip_lst = [
    [1.68008542967444, 0.47457010697126, 0.74503485547995, 2.21779475280333],
    [1.66880406142735, 1.47166070943092, -0.78712423516660, 0.87957568531662],
]
star_strip_lst = [
    [-1.27871144097281, -2.51829598723173, 2.68305001153967, 0.00000000000000],
    [-1.27871144097281, -2.51829598723173, -1.41548251226095, 0.00000000000000],
    [1.77871144097281, 0.94749966043683, -1.72611014132884, 0.00000000000000],
    [1.77871144097281, 0.94749966043683, 0.45854264205013, 0.00000000000000],
]
# note, same as foldMethod.star, since last value = 0.0:
w_strip_lst = star_strip_lst
trap_strip_lst = [
    [1.67132859481033, 0.78612999312594, 0.94665778267420, 2.26449326727204],
    [1.60398804524147, 1.17916179666061, -1.22472146827588, 0.98759363063196],
]
tria_star_lst = [
    [0.80901699437495, -0.84333376321889, 2.56438315398705, 1.75383477143902],
    [-0.30901699437495, 1.45719021980297, 2.56438315398705, 1.75383477143902],
    [-0.30901699437495, -0.72746256357600, -2.56438315398705, -1.75383477143902],
    [0.80901699437495, -3.02798654659787, -2.56438315398705, -1.75383477143902],
]
tria_star1loose_lst = [
    [0.25480766689807, 0.00000000000000, 2.83543169329313, 0.72223516058420],
    [-1.30885529803799, 3.14159265358979, -0.30616096029666, 0.72223516058420],
    [-0.26075457554760, 0.00000000000000, -2.74663996207488, -2.68168905616206],
    [-1.82441754048366, 3.14159265358979, 0.39495269151492, -2.68168905616206],
]
star_star1loose_lst = [
    [1.57050532439441, 0.07242369151188, -3.10130612170838, 0.16426745878078],
    [-1.33461387242175, 2.95124960914462, 0.19307629197799, 0.45900885952649],
    [-1.87572713272370, -2.88650107421470, -0.26177522435469, -2.33472779357166],
    [-2.01352248268662, -2.83178474507730, -2.96182733124778, 2.07365976116998],
    [2.09351982467803, 0.33436073666791, -2.94608173703237, 1.91436620462820],
    [-2.22767668049522, -2.77760386996604, -2.92656845416600, 1.38256728831668],
]
w_star1loose_lst = [
    [-1.32969344523106, 2.93729908156380, 0.47840318769040, 2.66825775628923],
    [-1.32969344523106, 2.93729908156380, 0.47840318769040, -0.47333489730056],
    [1.56791889743089, 0.07044231686021, -3.01397582234294, 2.98277426266723],
    [1.56791889743089, 0.07044231686021, -3.01397582234294, -0.15881839092256],
    [-2.39662854867090, -2.76044142453588, -2.28962724865982, -0.98968378942064],
    [-2.39662854867090, -2.76044142453588, -2.28962724865982, 2.15190886416915],
    [2.59691495774690, 0.37180029203870, -0.99159844699067, -2.18659454147894],
    [2.59691495774690, 0.37180029203870, -0.99159844699067, 0.95499811211085],
]

OnlyO3Triangles = {
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_I:           tria_strip_lst,
	trisAlt.strip_II:          tria_strip_lst,
	trisAlt.star:              tria_star_lst,
	trisAlt.star_1_loose:      tria_star1loose_lst,
	trisAlt.alt_strip_I:       tria_strip_lst,
	trisAlt.alt_strip_II:      tria_strip_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose:     star_strip_1loose_lst,
	trisAlt.strip_I:           star_strip_lst,
	trisAlt.strip_II:          star_strip_lst,
	trisAlt.star_1_loose:      star_star1loose_lst,
	trisAlt.alt_strip_I:       star_strip_lst,
	trisAlt.alt_strip_II:      star_strip_lst,
	trisAlt.alt_strip_1_loose: star_strip_1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose:     w_strip_1loose_lst,
	trisAlt.strip_I:           w_strip_lst,
	trisAlt.strip_II:          w_strip_lst,
	trisAlt.star_1_loose:      w_star1loose_lst,
	trisAlt.alt_strip_I:       w_strip_lst,
	trisAlt.alt_strip_II:      w_strip_lst,
	trisAlt.alt_strip_1_loose: w_strip_1loose_lst,
    },
    Heptagons.foldMethod.trapezium: {
	# These are all the same, since there are no solutions for the 1 loose
	# variants
	trisAlt.strip_I:           trap_strip_lst,
	trisAlt.strip_II:          trap_strip_lst,
	trisAlt.alt_strip_I:       trap_strip_lst,
	trisAlt.alt_strip_II:      trap_strip_lst,
    },
}

###############################################################################
tria_xxx1loose_lst = [
    [-0.11812292720476, 3.14159265358979, -2.25211078574522, -2.74857920585919],
    [1.4455400377313, 0.0, 0.88948186784457, -2.74857920585919],
    [0.60832876085173, 0.0, 2.18208908059778, 2.64524163292458],
    [-0.95533420408433, 3.14159265358979, -0.95950357299201, 2.64524163292458],
    [-0.65691438551895, 3.14159265358979, -1.33576642918691, 1.15113391706111],
    [0.90674857941711, 0.0, 1.80582622440289, 1.15113391706111],
    [0.470619952462, 3.14159265358979, -2.78574929965068, 1.27136705090598],
    [2.03428291739806, 0.0, 0.35584335393911, 1.27136705090598],
]
star_xxx1loose_lst = [
    [-1.20673038862948, 2.64886420376349, 0.5462781256929, 1.90439829002018],
    [-1.18498720369744, -2.96422976968227, -3.04175401058713, 2.29107353121922],
    [1.40643063492408, -0.18662824019381, 3.03637594858021, -2.26817282625815],
    [-1.77553651955644, -3.05965207131176, -3.09598219587269, -0.99511607066055],
    [-0.93641732709054, 2.44038947886288, 0.88697014027351, -0.27366004937339],
    [0.66845709899032, -0.38564524697005, 2.91190778483334, 0.58930509814088],
    [1.58322408928141, 0.47390958631694, -0.52100418066513, -2.00342801113787],
    [2.06165966104283, 0.22254153134540, -0.2269414372901, 1.53832863733572],
]
w_xxx1loose_lst = [
    [-0.94335616235195, 2.44013969579958, 0.73690456127344, 0.30810337906002],
    [-0.95922328678987, 2.440178678853, 0.75676044346296, 1.31293341966707],
    [0.64680225032839, -0.40681413993508, -3.05394393909218, -0.67958538291447],
    [1.13519707160583, 0.12145522427178, -2.32977399889470, 2.79015830517702],
    [-1.88107579998874, 2.90399006683424, 2.15718006845097, -2.43143969177342],
    [-1.91374594457222, -3.11261665074828, 2.53474378035533, 1.16485045216552],
    [2.27969888995643, -0.041271922594255, 0.965002604413438, 2.994364834727],
    [2.33699202330841, 0.07199688786574, 0.78873100385447, -1.7264857472177],
]
w_alt_strip1loose_lst = [
    [0.86602540378444, 0.36161317966767, -1.28052911995042, -2.06457033281442],
    [0.86602540378444, -0.36161317966767, -2.84861154567842, -2.06457033281442],
]

Squares12 = {
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose:     tria_xxx1loose_lst,
	trisAlt.star_1_loose:      tria_xxx1loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose:     star_xxx1loose_lst,
	trisAlt.star_1_loose:      star_xxx1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose:     w_xxx1loose_lst,
	trisAlt.star_1_loose:      w_xxx1loose_lst,
	trisAlt.alt_strip_1_loose: w_alt_strip1loose_lst,
    },
}

###############################################################################
par_star_strip_list = [
    [1.06673697715051, 0.17460360869707, -2.06457033281442, 1.84715333507949],
    [0.73520075865433, 0.53851116038769, -2.06457033281442, 2.99510209963411],
    [0.73520075865433, 2.96698904489272, 2.06457033281442, 1.29443931851030],
    [1.06673697715051, 2.60308149320211, 2.06457033281442, 0.14649055395569],
]
tri_xxx1loose_list = [
    [0.63050299381974, 0.00000000000000, 2.50415104489001, 3.04158952483317],
    [-0.93315997111632, 3.14159265358979, -0.63744160869978, 3.04158952483317],
    [-0.35740390266670, 3.14159265358979, -1.31609269942202, 0.49280142622661],
    [1.20625906226936, 0.00000000000000, 1.82549995416778, 0.49280142622661],
    [0.05551620799015, 3.14159265358979, -2.02420702769594, -2.33135272852206],
    [1.61917917292621, 0.00000000000000, 1.11738562589385, -2.33135272852206],
    [0.52364405571114, 3.14159265358979, -2.45744269925777, 0.77913284129321],
    [2.08730702064720, 0.00000000000000, 0.68414995433202, 0.77913284129321],
]
tri_star_strip_list = [
    [-0.66127319491213, 2.28707727070028, 1.94741107458675, -2.58597836635026],
    [1.19649356516386, -0.27352488932328, 1.88427551486363, -2.65930784921309],
    [-0.47025059338481, 1.89664209919690, 2.27933667872865, -1.96997876871195],
    [1.30901699437495, -0.12747672487733, 1.67447101663540, 0.75403191432758],
    [1.30901699437495, 2.16192066067303, -1.67447101663540, -0.75403191432758],
    [1.07426879828649, 2.59270935778041, -2.10002304137262, 0.08175627039980],
]
star_xxx1loose_list = [
    [0.95264738519643, -0.01309999394730, 3.13432214842325, 1.09098978383234],
    [-1.06227181130998, 2.78971943905933, 0.37000886846079, 2.54246231744333],
    [1.40805226726167, 0.02260683081079, -3.12904394581366, -2.75765743673787],
    [-1.43387526434821, -2.76682105177721, -2.91931338809679, 1.74337082045130],
    [-0.60854380787240, 2.52774338384669, 0.72745662990011, -0.94677780974507],
    [-1.82548277338380, -2.85297602816132, -2.97514109692294, -0.72367409453609],
    [1.83004009970869, 0.57551428856377, -0.66609035739680, -1.38545647838283],
    [2.17870504783457, 0.40973095071998, -0.43911928098023, 1.28363988041104],
]
w_xxx1loose_list = [
    [0.95951992202349, -0.01161085047431, -2.51174334704038, -1.18120963880853],
    [1.65825120099569, 0.42460909911928, -1.82799509364850, 1.77811345611149],
    [-1.91360410589380, 3.11156048982918, 2.45603323395099, -3.05656467065564],
    [-1.89945002634773, -2.89526279853385, 2.82098177295395, 0.92614367809318],
]
trap_alt_strip_list = [
    [1.32753236748743, 0.77825225940270, 2.14443135617381, -2.27773464797323],
    [1.38648354282283, 1.24922883552521, -1.95137282316369, -1.57906586251865],
]
Tris24 = {
    # valid for all non-loose methods:
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_I:           par_star_strip_list,
	trisAlt.strip_II:          par_star_strip_list,
	trisAlt.star:              par_star_strip_list,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose:     tri_xxx1loose_list,
	trisAlt.strip_I:           tri_star_strip_list,
	trisAlt.strip_II:          tri_star_strip_list,
	trisAlt.star:              tri_star_strip_list,
	trisAlt.star_1_loose:      tri_xxx1loose_list,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose:     star_xxx1loose_list,
	trisAlt.star_1_loose:      star_xxx1loose_list,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose:     w_xxx1loose_list,
	trisAlt.star_1_loose:      w_xxx1loose_list,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.alt_strip_I:       trap_alt_strip_list,
	trisAlt.alt_strip_II:      trap_alt_strip_list,
    },
}

###############################################################################
# These lists are valid for stripI and stripII:
tri_strip1loose_lst = [
    [-0.24586272685784, 2.44771371251441, 1.45738733262406, -1.75383477143902],
    [0.95623621578899, 0.69387894107539, -3.07196320311651, -1.75383477143902],
    [0.95623621578899, 0.69387894107539, 2.05680310485758, 1.75383477143902],
    [-0.24586272685784, 2.44771371251441, 0.30296833341857, 1.75383477143902],
    [0.66725358606974, 2.44771371251441, -1.64042577726818, 1.75383477143902],
    [1.86935252871658, 0.69387894107539, 0.11340899417084, 1.75383477143902],
    [1.86935252871658, 0.69387894107539, 1.26782799337633, -1.75383477143902],
    [0.66725358606974, 2.44771371251441, -0.48600677806269, -1.75383477143902],
]
tri_strip_lst = [
    [0.39884399626846, 1.45684030648263, 2.57158530333341, -0.88428111441002],
    [-0.25245320098095, 2.52549189037339, 1.29275363802776, -1.90090461585023],
    [0.56477962526448, 2.51702147084794, -1.63428221468808, 1.88416030307270],
    [1.19589692698571, 0.47194194051050, 1.87483515324746, 2.22456933042072],
    [1.68158273810536, 1.45342507125822, -0.03697984985938, -0.88545500812313],
    [1.79139080685027, 1.27507548732764, 0.20309173616167, -0.98992828731305],
]
tri_star_lst = [
    [-1.18662252141201, -2.17548812023258, -1.29296142672105, -1.48125430415468],
    [-1.52591217132859, 2.66128496758874, 1.19569246790512, 2.91905605094518],
    [1.75235022759435, -0.46021993104649, 1.40161573695539, -3.12782128503339],
    [-0.88119866022994, 2.04513896160847, 1.54242990514721, 0.99335328707403],
    [-0.18727644316625, -2.28949642529020, -2.31688724641124, 1.82466469686959],
    [1.58859224623688, -1.11260595702076, 2.33929032164548, -0.91912350781114],
]
tri_star1loose_lst = [
    [-0.60197575041066, -2.44771371251441, -1.76696445000149, 1.24081518217449],
    [0.60012319223617, -0.69387894107539, 2.76238608573907, 1.24081518217449],
    [0.01059912757678, 0.69387894107539, 2.65660977825033, 0.84170067739777],
    [-0.08736166601310, 0.69387894107539, -3.01471700701865, 2.59507467802031],
    [0.19988847087340, -2.44771371251441, -2.66071406852831, 2.68370358992304],
    [-0.31030415059136, -0.69387894107539, -2.57251814092688, -1.79447056577940],
    [-1.19149981507005, 2.44771371251441, 0.90277500681131, 0.84170067739777],
    [-1.28946060865993, 2.44771371251441, 1.51463352872192, 2.59507467802031],
    [1.40198741352023, -0.69387894107539, 1.86863646721226, 2.68370358992304],
    [-1.51240309323819, -2.44771371251441, -0.81868336948786, -1.79447056577941],
    [0.86022804268662, -2.44771371251441, -2.82097241148185, -1.09421753239613],
    [2.06232698533345, -0.69387894107539, 1.70837812425871, -1.09421753239613],
]
star_strip1loose_lst = [
    [-1.12185603921076, -2.76299406676300, -1.77182139095146, 2.25677227952413],
    [-1.32676124616834, -2.57785296534057, 2.73621246110058, -0.28126669081465],
    [-0.28922422512916, 2.67184564148923, -0.21375757704173, 1.99144793710537],
    [1.87246189702616, 0.76451178362743, -0.07246880815068, 1.84093984198229],
    [-1.11247141576028, -2.02300272834379, 2.83681036770520, 1.03167032894864],
    [0.46925383056108, 1.83136828593045, 1.03483628209592, -2.42223513681055],
    [2.08464860046684, 1.22500865113657, -0.78617831355470, -0.51598138539489],
    [0.60829171411896, 2.02641269135956, 0.54792865018946, -2.24821152354458],

]
star_strip_lst = [
    [1.35890338579684, 0.57075868490494, -1.85410415297363, -1.58728465070744],
    [1.15107111426033, 0.76345718622724, -2.57196597101263, 1.37871276612968],
    [-0.83500624291191, -3.01003874482176, -1.24721587310154, 1.93708917058066],
    [-0.61728150693957, -2.87981822788260, -0.67139289769203, -1.35396864233236],
    [-1.54439152099961, -2.10019045512668, -2.53006628353912, 0.86765835633092],
    [-1.09616113974161, -2.06581522194281, 2.77903490628469, 0.97451844537129],
    [1.24076043827181, 1.40935113420046, 0.64591225448264, -1.22965597972245],
    [1.67780752655199, 1.43029003348023, 0.02889587442093, -0.91810534087753]
]

star_star1loose_lst = [
    [-1.36410700200945, 3.00691567143306, 0.87876830925151, -1.01986215731031],
    [-1.42050504592943, 3.07871772918526, -0.61926122847438, 1.45526934366165],
    [-1.69774000557902, -2.98170043945494, 0.51340311417207, -2.32624477751384],
    [1.66799483288787, 0.14105225645065, -2.31605950023142, -1.00927443294588],
    [-1.77142469441312, -2.93877311886668, -2.23984751859655, 2.38611481773535],
    [1.99683651725467, 0.30402635467675, -1.21778797755018, -1.87144457445582],
    [-2.22765851783918, -2.77760691636592, -1.44068190543650, -1.38264247816566],
    [-2.33076442810769, -2.76447562866709, -1.78564611455942, -0.85936890505845],
    [2.47885385655092, 0.38136040311637, -1.73948770557406, 1.11902713813689],
    [2.52616608558365, 0.37897754256552, -1.55037429014508, 0.87434954671617],
]
w_strip1loose_lst = [
    [-1.18779808183828, 3.09081409651360, 2.56438315398705, -1.71787836709338],
    [-1.18779808183828, -2.61516171106324, -2.56438315398705, -3.10563624924416],
    [-1.34218282733539, -2.59693009356896, 2.56438315398705, 0.30631407367199],
    [-1.34218282733539, -2.01972059396621, -2.56438315398705, -1.08144380847878],
    [1.63942249844993, 0.12273044694943, 1.07702232077537, 1.95930752451913],
    [1.63942249844993, 0.90677165981343, -1.07702232077537, -2.25930744984604],
    [2.09933927073703, 0.42611693996127, 1.07702232077537, -1.59247037929717],
    [2.09933927073703, 1.21015815282527, -1.07702232077537, 0.47209995351725],
]
w_strip_lst = [
    [-1.18624768042682, -2.99948998126564, 2.82638762950489, -1.89159120039677],
    [-1.54972104079789, -2.88677782630400, 2.18099900262423, 1.34897770109324],
    [-1.58419011091491, -2.11184124023252, -2.06969481617108, -0.77601462834736],
    [-1.25638140280115, -2.05696802579392, -2.73143700055271, -1.12114943951174],
    [1.68823063823637, 0.48669510129948, 0.48415173585819, 1.98683242489312],
    [2.07491067840068, 0.53819543761494, 0.93672429915382, -1.26808925777854],
]
Pos32TrianglesI = {
    # TODO: fill in more...
    # no solutions found for trapezium and parallel fold (for any triangles).
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip1loose_lst,
	trisAlt.strip_I: tri_strip_lst,
	trisAlt.strip_II: tri_strip_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.star_1_loose: tri_star1loose_lst,
	trisAlt.alt_strip_I: tri_strip_lst,
	trisAlt.alt_strip_II: tri_strip_lst,
	trisAlt.alt_strip_1_loose: tri_strip1loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: star_strip1loose_lst,
	trisAlt.strip_I: star_strip_lst,
	trisAlt.strip_II: star_strip_lst,
	trisAlt.star_1_loose: star_star1loose_lst,
	trisAlt.alt_strip_I: star_strip_lst,
	trisAlt.alt_strip_II: star_strip_lst,
	trisAlt.alt_strip_1_loose: star_strip1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip1loose_lst,
	trisAlt.strip_I: w_strip_lst,
	trisAlt.strip_II: w_strip_lst,
	trisAlt.alt_strip_I: w_strip_lst,
	trisAlt.alt_strip_II: w_strip_lst,
	trisAlt.alt_strip_1_loose: w_strip1loose_lst,
    },
}

###############################################################################
par_strip1x_lst = [
    [0.63253059063857, 0.0, -2.98282064597178, -0.93327919097016],
    [-0.93113237429749, 3.14159265358979, 0.15877200761801, -0.93327919097016],
    [0.13688981744294, 3.14159265358979, 0.896004297407, 1.87419729891036],
    [1.700552782379, 0.0, -2.2455883561828, 1.87419729891036],
]
tri_strip1x_lst = [
    [0.5208870126758, 0.0, -2.95529376164387, 2.2694172235287],
    [-1.04277595226026, 3.14159265358979, 0.18629889194593, 2.26941722352870],
    [0.5208870126758, 0.0, -2.95529376164387, -0.60785377735739],
    [-1.04277595226026, 3.14159265358979, 0.18629889194593, -0.60785377735739],
    [0.60260278918294, 3.14159265358979, -1.75709521874082, -2.53373887623240],
    [2.166265754119, 0.0, 1.38449743484897, -2.5337388762324],
    [0.60260278918294, 3.14159265358979, -1.75709521874082, 0.87217543006109],
    [2.166265754119, 0.0, 1.38449743484897, 0.87217543006109],
]
str_strip1x_lst = [
    [-1.05634303568789, -3.01809039318625, -0.12424049895843, 2.42044225150201],
    [-1.05634303568789, -3.01809039318624, -0.12424049895843, -0.45682874938408],
    [1.55759725801545, 0.50143701257082, -2.82615815279593, 0.49432055663953],
    [1.55759725801545, 0.50143701257082, -2.82615815279593, -2.38295044424656],
    [-1.99137652499897, -2.44873339610284, -2.63665359010640, 1.82986206045672],
    [-1.99137652499897, -2.44873339610284, -2.63665359010640, -1.57605224583677],
    [2.42367662112328, 0.73523867591239, -0.95915637221717, -1.30440374966920],
    [2.42367662112328, 0.73523867591239, -0.95915637221717, 2.10151055662430],
]
w_strip1x_lst = [
    [-1.07632363424826, -3.01611570508075, -0.38561227283342, 0.45980405591247],
    [1.57882655891851, 0.49767315648410, -2.53595524814500, -0.48177733726710],
    [-1.86047317686316, -2.70047657508040, -0.93188028455341, -2.05930752162826],
    [2.29741750072355, 0.63415651739503, -1.97454863849786, 1.38883574255529],
]
trp_strip1x_lst = [
    [-1.27706732045401, 3.09338294983859, 2.09206324657307, 3.03303252269420],
    [-1.10657003163774, 3.08349687002331, 2.63327625618084, 3.01064242412906],
    [-0.93919788637761, 3.05431409657789, 0.87102800118062, 0.15857919733070],
    [1.78226077570429, 0.26238632722858, 1.99162873877821, -2.50818268743827],
    [1.72402953631430, 0.41961932990476, 2.69953941819374, -1.92579101209988],
    [-0.21143566250885, 2.77688011741353, -2.70823139026119, 0.79432154044691],
]
trp_alt_strip1loose_lst = [
    [-1.29282239989066, -2.74175475479458, -1.52195034584806, -2.02845188164840],
    [-1.49952426776519, -3.08987766673610, 1.46036947407965, -3.02510120097412],
    [-0.56033966827624, 2.68609715015399, 2.50829083111691, 1.29376078352551],
    [-0.41028261173574, 2.68360619149060, 3.03303208034306, 1.33491743742401],
    [1.76758947025021, 0.44123664559379, 2.64575324964822, -1.78075434469097],
    [1.80523453225663, 0.26579440566459, 1.92412294881261, -2.49857890913702],
]
Pos32TrianglesII = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: par_strip1x_lst,
	trisAlt.strip_I: par_strip1x_lst,
	trisAlt.star_1_loose: par_strip1x_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip1x_lst,
	trisAlt.strip_I: tri_strip1x_lst,
	trisAlt.star_1_loose: tri_strip1x_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: str_strip1x_lst,
	trisAlt.strip_I: str_strip1x_lst,
	trisAlt.star_1_loose: str_strip1x_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip1x_lst,
	trisAlt.strip_I: w_strip1x_lst,
	trisAlt.star_1_loose: w_strip1x_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_1_loose: trp_strip1x_lst,
	trisAlt.strip_I: trp_strip1x_lst,
	trisAlt.star_1_loose: trp_strip1x_lst,
	trisAlt.alt_strip_1_loose: trp_alt_strip1loose_lst,
    },
}

###############################################################################
tri_strip_1_loose_lst = [
    [-0.02650967655387, 2.01156609697354, 2.03145116250301, -1.12794994868396],
    [0.64060490724162, 1.13002655661625, 2.91299070286029, -1.12794994868396],
    [0.64060490724162, 1.13002655661625, 2.02137772495892, 1.12794994868396],
    [-0.02650967655387, 2.01156609697354, 1.13983818460163, 1.12794994868396],
    [1.18999167580366, 2.01156609697354, -1.3421943760654, 1.12794994868396],
    [1.85710625959915, 1.13002655661625, -0.46065483570811, 1.12794994868396],
    [1.18999167580367, 2.01156609697354, -0.45058139816402, -1.12794994868396],
    [1.85710625959915, 1.13002655661625, 0.43095814219326, -1.12794994868396],
]
tri_strip_lst = [
    [0.76992497486360933, 0.94624022871632729, 3.0803702160830282, -1.3554280853678113],
    [-0.027892439365956069, 2.0135355382599829, 1.1365693454289998, 1.1300966239587744],
    [-0.17038567171338109, 2.692349840061993, 0.68719186423390977, -2.2850437463779456],
    [0.27367697466186752, 2.6735422903020791, -1.4278661736369687, 2.2346826212529747],
    [1.7889887751470579, 0.56584486671766454, 1.5850459818848297, -2.0045929968418328],
    [1.1391199990835519, 2.0596070208421637, -0.46567402798771518, -1.1822021274704628],
]
tri_star_lst = [
    [-0.68791496155213328, -2.495631829431924, -1.6419078311288882, 1.1433256399495644],
    [-1.1818027610722566, 2.4320010142774864, 0.92874590277388847, 0.84683804809139129],
    [2.2198614656215532, -0.096567017054908, 0.77956167705151769, -2.2491539403800163],
    [2.1029095361483163, -0.65195721245229965, 1.6431449954540396, -1.1190387484482498],
]
tri_star_1_loose_lst = [
    [-0.12190664938895671, 1.1300265566162546, 2.9129403918280805, 2.0059341963195623],
    [-0.18414110678214954, 1.1300265566162544, 2.4742247811307219, 1.0070777511188451],
    [-0.78902123318444584, 2.0115660969735392, 2.0314008514707957, 2.005934196319564],
    [-0.29824891637152512, -1.1300265566162544, -2.4481961533146572, -1.3233415223631617],
    [-0.85125569057763784, 2.0115660969735383, 1.5926852407734382, 1.0070777511188427],
    [-0.96536350016701444, -2.0115660969735387, -1.566656612957372, -1.3233415223631644],
    [0.90072312664293952, -2.0115660969735387, -3.0375722013401916, -0.91433273824831396],
]
star_strip_1_loose_lst = [
    [1.9059097830186296, 0.80649142107765925, 0.27608560811485156, 0.74755557501847036],
    [0.89781315887566426, 1.6079465028301179, 0.80430968907499489, -1.7428360613785676],
    [1.0191362328011477, 1.674854923558174, 0.56576556222028196, -1.6471597101417732],
    [1.9116955706405505, 1.3530078960808691, -0.29406763282292303, -0.72053597167619721],
]
star_strip_lst = [
    [1.1337834018831718, 0.3983033753431518, -2.1797039818918522, -1.5328428576100608],
    [0.90307327376725277, 0.63885212596863361, -2.8904845931275038, 2.0878012966188395],
    [-0.5420331566827894, 2.9979749183990561, -0.78779708747906696, 1.9216762369325204],
    [-0.30364010591499141, -3.129387164358028, -0.38799713202612018, -1.8798977866386348],
    [0.85606927913462993, 1.6261911991325377, 0.83086420958161999, -1.8031208657168927],
    [0.98417091688110503, 1.7002804053036806, 0.57313683688259065, -1.6982959819999621],
]
star_star_lst = [
    [-1.5736991265545797, -3.0667349493793918, -1.3224963640241336, 2.0645703328144185],
    [-1.5736991265545799, -3.0667349493793914, 0.83154827752661153, -2.0645703328144176],
    [-2.0171802376047618, -2.830548018756736, -2.9655222486233694, 2.0645703328144211],
    [-2.0171802376047623, -2.830548018756736, -0.81147760707262417, -2.0645703328144194],
]
star_star_1_loose_lst = [
    [-1.5737945477148021, -3.0666624419279898, -1.3229092592043097, 2.0648406080614592],
]
w_strip_1_loose_lst = [
    [1.6836334146307617, 0.32015374035989591, 0.72926498726807643, 1.944604590758332],
    [1.6836334146307614, 0.91077045415146374, -0.72926498726807676, -2.9129944714359173],
    [1.9818619620991027, 0.71754460954812993, 0.72926498726807565, -0.75587888626315891],
    [1.9818619620991023, 1.3081613233396971, -0.72926498726807587, 0.66970735872217591],
]
w_strip_lst = [
    [-1.1873278995710541, 3.0795212915489931, 2.5484729998858415, -1.7099925934432898],
    [-1.6002075589879676, -3.0554878503734844, 1.9505868416444843, 1.950374772184948],
    [1.6791195265785936, 0.28190668923148438, 0.7894679357209311, 1.9408382769201495],
    [2.0981469671043058, 0.35412999252799127, 1.17394892523243, -1.8111512922408615],
]

FoldedSquareAndO3Triangle = {
    # nothing found for parallel and trapezium fold (strip triangle alt)
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip_1_loose_lst,
	trisAlt.strip_I: tri_strip_lst,
	trisAlt.strip_II: tri_strip_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.star_1_loose: tri_star_1_loose_lst,
	trisAlt.alt_strip_I: tri_strip_lst,
	trisAlt.alt_strip_II: tri_strip_lst,
	trisAlt.alt_strip_1_loose: tri_strip_1_loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: star_strip_1_loose_lst,
	trisAlt.strip_I: star_strip_lst,
	trisAlt.strip_II: star_strip_lst,
	trisAlt.star: star_star_lst,
	trisAlt.star_1_loose: star_star_1_loose_lst,
	trisAlt.alt_strip_II: star_strip_lst,
	trisAlt.alt_strip_1_loose: star_strip_1_loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip_1_loose_lst,
	trisAlt.strip_I: w_strip_lst,
	trisAlt.strip_II: w_strip_lst,
	trisAlt.alt_strip_I: w_strip_lst,
	trisAlt.alt_strip_II: w_strip_lst,
	trisAlt.alt_strip_1_loose: w_strip_1_loose_lst,
    },
}

###############################################################################
par_x1loose_tri_lst = [
    [0.27906714692448, 1.13002655661625, -1.81138418689647, -2.24296700996579],
    [-0.38804743687101, 2.01156609697354, -0.92984464653918, -2.24296700996579],
    [0.27906714692448, 1.13002655661625, -1.81138418689647, -0.84135845497827],
    [-0.38804743687101, 2.01156609697354, -0.92984464653919, -0.84135845497827],
    [1.52287058888036, 2.01156609697354, 1.81138418689647, -2.30023419861152],
    [1.52287058888036, 2.01156609697354, 1.81138418689647, -0.89862564362400],
    [2.18998517267585, 1.13002655661625, 0.92984464653919, -0.89862564362400],
    [2.18998517267585, 1.13002655661625, 0.92984464653918, -2.30023419861152],
]
tri_x1loose_tri_lst = [
    [-0.55030286595057, 2.01156609697354, 2.18125909356928, -2.07535932769389],
    [0.11681171784492, 1.13002655661625, 3.06279863392656, -2.07535932769389],
    [-0.18888293454288, 2.01156609697354, 2.17232680733740, 2.79121992092653],
    [0.47823164925261, 1.13002655661625, 3.05386634769469, 2.79121992092653],
    [-0.48310085169006, 2.01156609697354, 1.24452928140542, 2.31762770654306],
    [0.18401373210543, 1.13002655661625, 2.12606882176271, 2.31762770654306],
    [0.23319250951046, 1.13002655661625, 2.09936643282696, -0.54984536241775],
    [-0.43392207428503, 2.01156609697354, 1.21782689246968, -0.54984536241775],
]
str_x1loose_tri_lst = [
    [-1.26281646628355, -3.02876463215822, -1.65942927619163, -2.43911120496492],
    [-1.18545708774307, -3.02666064646646, -1.61362866838357, 0.90492881265642],
    [-1.02536936238367, 3.03744143368098, -0.95202203423548, -2.98061532539632],
    [-0.91397300297181, 3.01786731448084, -0.92401304642001, 0.38108659926911],
]
w_x1loose_tri_lst = [
    [-1.09288909564396, -3.13077896370736, -0.91702207542336, -0.82480405947615],
    [-0.92982212003000, 3.02459105700098, -0.71976731613330, -0.42505107803619],
    [-1.89528991130568, -2.84679305499772, 2.88748207122798, -1.61976860935445],
    [-1.89188156218411, -2.80313499057068, 2.94967961856962, -1.44630616106433],
    [2.40837807677839, 0.48332799353582, 0.11580368164733, 2.39590957404102],
    [2.40725758586745, 0.60940947020624, -0.18098227475252, 1.07645580959437],
]
trp_x1loose_tri_lst = [
    [-0.60716198509448, 2.60308149320211, -2.88424752055966, -2.52195655378824],
    [-0.60716198509448, 2.60308149320211, 1.99732923163241, -2.52195655378824],
    [-0.60716198509448, 2.60308149320211, 2.74100530289306, -0.88395775250526],
    [-0.60716198509448, 2.60308149320211, 1.33939674790553, -0.88395775250526],
    [2.40909972089932, 0.53851116038769, 1.14426342195739, 2.52195655378824],
    [2.40909972089932, 0.53851116038769, -0.25734513303014, 2.52195655378824],

    [2.40909972089932, 0.53851116038769, 0.40058735069674, 0.88395775250526],
    [2.40909972089932, 0.53851116038769, 1.80219590568426, 0.88395775250526],
]
par_stripI_lst = [
    [-0.59152927484049, 2.73657861729101, 0.24871410113607, 2.66983506798982],
    [-0.47499773928666, 2.15893652922960, -0.72279364893134, -0.73950993996237],
    [2.27693547509150, 0.98265612436020, 0.72279364893134, -2.40208271362743],
    [2.39346701064533, 0.40501403629878, -0.24871410113607, 0.47175758559997],
]
tri_stripI_lst = [
    [-0.17324089867479, -2.94029393453004, -1.92853793185544, -2.55201747292851],
    [-0.16115001516804, -2.95984495481017, -1.92402640716433, 0.86278640581084],
    [-0.62996925708776, 2.18470424672241, 0.99711208010302, 2.37421381176717],
    [-0.50813029295927, 2.14267035387713, 1.01028506052164, -0.50863632017174],
]
str_stripI_lst = [
    [-1.02486290789015, 3.03678795034983, -0.95004531859793, -2.98194197065245],
    [-0.90815984502062, 3.01262509963113, -0.91047126200357, 0.37145275614091],
    [1.40749587484804, 0.29634532013455, -1.85873460534076, -0.37191199363966],
    [1.52009360807743, 0.28279384061835, -1.75627933706554, 2.90179932926625],
]
w_stripI_lst = [
    [-0.91757259818078, 3.01433813376838, -0.70408101927089, -0.40186026650319],
    [-0.91757259818078, 3.01433813376838, -0.70408101927089, 3.10580927637485],
    [1.41366057564340, 0.29527317305744, -2.06409052877744, -3.10255995229039],
    [1.41366057564340, 0.29527317305744, -2.06409052877744, 0.40510959058764],
    [-1.90035302699735, -2.90557746204824, 2.80708419669805, 1.00147165579995],
    [-1.90035302699735, -2.90557746204825, 2.80708419669805, -1.77404410850160],
    [2.40803896109262, 0.47122570947588, 0.13941880591630, 2.41337666654142],
    [2.40803896109262, 0.47122570947588, 0.13941880591630, -0.36213909776013],
]
trp_stripI_lst = [
    [-0.60716198509448, 2.60308149320211, -2.82169164822737, -2.57559814321078],
    [-0.60716198509448, 2.60308149320211, -2.82169164822737, 0.19991762109077],
    [-0.60716198509448, 2.60308149320211, 1.27684087557325, 2.67735337979532],
    [-0.60716198509448, 2.60308149320211, 1.27684087557325, -0.83031616308271],
    [2.40909972089932, 0.53851116038769, -0.31990100536242, 2.57559814321078],
    [2.40909972089932, 0.53851116038769, 1.86475177801655, -2.67735337979532],
    [2.40909972089932, 0.53851116038769, -0.31990100536242, -0.19991762109077],
    [2.40909972089932, 0.53851116038769, 1.86475177801655, 0.83031616308271],
]
tri_stripII_lst = [
    [-0.25659752850319, -2.80258864183158, -2.35758686997131, 1.55965019078912],
    [-0.51804439352975, -2.79367180512820, -1.07193959414602, -2.08564843386095],
    [-0.60195559371508, 2.14196367156633, 1.03347735137087, 2.33471413375604],
    [1.22229638498027, 0.89677580579463, -1.03670537656705, -2.50748867754396],
    [0.01139338045424, 1.29026082122048, 1.45553021572169, 1.15526008315070],
    [1.39277506531645, 1.77951330956746, -2.36747125170773, 1.24872282453226],
]
trp_altStripI_lst = [
    [1.22814357933223, 0.43224223921413, -1.28142944177665, -2.85372159012931],
    [1.39360796069990, 0.20889452807781, -2.61212936726957, 1.81302438255156],
    [-0.57537357622592, 3.02768990327119, -1.28486579893706, -2.54979909059199],
    [-0.08408836052071, 1.96450817321075, -2.75603811746648, 1.67799558551154],
    [0.03060383535018, 1.87465028049493, 1.98217014569692, 1.55554861862942],
]
str_altStripII_lst = [
    [-0.81149938129548, 2.99784799577654, 2.63975364111580, -3.09224515641795],
    [-0.81149938129548, 2.99784799577654, 2.63975364111580, 0.41542438646009],
    [1.29571853483872, 0.32371573851099, 0.92636624036888, 3.13685646373255],
    [1.29571853483872, 0.32371573851099, 0.92636624036888, -0.37081307914549],
    [0.80239205451159, 0.86436570527348, -2.12365973408655, 1.94701686134651],
    [0.80239205451159, 0.86436570527348, -2.12365973408655, -0.82849890295504],
    [-0.24155433993740, -2.90251186294038, -1.28797553082262, -1.01402668545951],
    [-0.24155433993740, -2.90251186294038, -1.28797553082262, 1.76148907884204],
    [-0.56860014366961, -2.01586284820463, 3.11478295836860, -2.58080383613742],
    [-0.56860014366961, -2.01586284820463, 3.11478295836860, 0.19471192816413],
    [-0.79954536379237, -1.89330080140264, -2.66595910818771, 3.12613769705861],
    [-0.79954536379237, -1.89330080140264, -2.66595910818771, -0.38153184581942],
    [0.75064757990417, 1.09256114506255, 0.78091856165338, -1.79267554926756],
    [0.75064757990417, 1.09256114506255, 0.78091856165338, 0.98284021503399],
    [1.33052490991475, 1.71206898434187, -0.97395326773703, -3.03691211850623],
    [1.33052490991475, 1.71206898434187, -0.97395326773703, 0.47075742437180],
]
w_altStripII_lst = [
    [1.18011109581834, 0.37169014198392, 2.95893188137961, 2.87038105829968],
    [-0.81913637585042, 2.99881244917736, 2.85009351766803, -0.38104106922527],
    [0.97019352245235, 0.54345533273785, -3.12892874049469, 1.95394464318774],
    [-0.68748557606960, 2.98827147042815, 2.95297655549529, 2.89413220212522],
    [1.23721078838758, 0.34506437021913, 0.74108791277820, -3.04971896809886],
    [1.30393967693066, 0.32113985476709, 0.73179999136068, 0.34642865707259],
    [-0.77821181927294, -1.90033151045119, -2.88161708123925, 0.28856083804932],
    [-0.57894372256223, -2.00761501035437, -3.04495085078671, -0.18787522616743],
    [0.92413423100782, 1.67535962793723, -0.95885265915536, 1.45949580795944],
    [1.31572541088832, 1.71401196932429, -0.73089559268964, -0.37323623007914],
]
trp_altStrip1loose_lst = [
    [1.38320350591353, 0.34837460000749, -2.89886073151224, 1.55514021866118],
    [1.38320350591353, 0.34837460000749, 1.98271602067982, 1.55514021866118],
    [1.38320350591353, 1.26725224167528, 2.89886073151224, -1.55514021866118],
    [1.38320350591353, 1.26725224167528, -1.98271602067983, -1.55514021866118],
    [0.03101005645957, 2.79321805358230, 2.89886073151224, -1.55514021866118],
    [0.03101005645957, 2.79321805358230, -1.98271602067983, -1.55514021866118],
    [0.03101005645957, 1.87434041191451, -2.89886073151224, 1.55514021866118],
    [0.03101005645957, 1.87434041191451, 1.98271602067982, 1.55514021866117],
]
FoldedSquareAnd1TriangleType = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: par_x1loose_tri_lst,
	trisAlt.star_1_loose: par_x1loose_tri_lst,
	trisAlt.strip_I: par_stripI_lst,
	trisAlt.star: par_stripI_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_x1loose_tri_lst,
	trisAlt.star_1_loose: tri_x1loose_tri_lst,
	trisAlt.strip_I: tri_stripI_lst,
	trisAlt.star: tri_stripI_lst,
	trisAlt.strip_II: tri_stripII_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: str_x1loose_tri_lst,
	trisAlt.star_1_loose: str_x1loose_tri_lst,
	trisAlt.star: str_stripI_lst,
	trisAlt.strip_I: str_stripI_lst,
	trisAlt.alt_strip_II: str_altStripII_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_x1loose_tri_lst,
	trisAlt.star_1_loose: w_x1loose_tri_lst,
	trisAlt.star: w_stripI_lst,
	trisAlt.strip_I: w_stripI_lst,
	trisAlt.alt_strip_II: w_altStripII_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_1_loose: trp_x1loose_tri_lst,
	trisAlt.star_1_loose: trp_x1loose_tri_lst,
	trisAlt.star: trp_stripI_lst,
	trisAlt.strip_I: trp_stripI_lst,
	trisAlt.alt_strip_I: trp_altStripI_lst,
	trisAlt.alt_strip_1_loose: trp_altStrip1loose_lst,
    },
}

###############################################################################
par_1loose_lst = [
    [0.61336294993015, 0.69387894107539, -2.02385524890379, -2.96353691422862],
    [-0.58873599271668, 2.44771371251441, -0.27002047746477, -2.96353691422862],
    [-0.58873599271668, 2.44771371251441, -0.27002047746477, -0.53505902972359],
    [0.61336294993015, 0.69387894107539, -2.02385524890379, -0.53505902972359],
    [1.18857478587469, 2.44771371251441, 2.02385524890379, -0.17805573936117],
    [1.18857478587469, 2.44771371251441, 2.02385524890379, -2.60653362386620],
    [2.39067372852152, 0.69387894107539, 0.27002047746477, -2.60653362386620],
    [2.39067372852152, 0.69387894107539, 0.27002047746477, -0.17805573936117],
]
par_star_stripI_lst = [
    [-0.44916112192146, 2.11227561688477, -0.79012198328513, -2.38655387121839],
    [-0.17280305940844, 1.70819703332078, -1.30326950127303, -1.01657786176029],
    [1.97474079521328, 1.43339562026901, 1.30326950127303, -2.12501479182951],
    [2.25109885772630, 1.02931703670503, 0.79012198328513, -0.75503878237140],
]
tri_1loose_lst = [
    [0.37956950870979, 0.69387894107539, 2.34625287056709, 2.49796077458610],
    [-0.82252943393704, 2.44771371251441, 0.59241809912807, 2.49796077458610],
    [-0.61858829716655, 2.44771371251441, 0.46697885942260, -0.39003731740481],
    [0.58351064548028, 0.69387894107539, 2.22081363086162, -0.39003731740481],
    [0.79647217452132, 2.44771371251441, -1.81669277600562, -1.55090087417368],
    [1.99857111716815, 0.69387894107539, -0.06285800456660, -1.55090087417368],
    [1.18621521608351, 2.44771371251441, -1.96831071333297, -0.13175341416895],
    [2.38831415873034, 0.69387894107539, -0.21447594189395, -0.13175341416895],
]
tri_star_stripI_lst = [
    [0.34664617344104, 0.86790421007680, -2.91835245631957, -2.53571317165931],
    [0.44342922384401, 1.20439715712300, 2.96781522624580, 2.73386248267708],
    [-0.13757996544884, 1.60845704819286, 1.73549253454265, 2.25958542051698],
    [-0.15948643486139, 1.62264309787405, 1.72625592266415, -0.62112703207119],
    [0.10521042922568, -2.92116848059139, -2.32286386590525, 0.98904570975943],
    [0.34713223891179, 2.84509931222894, -1.99052433467195, -2.01956956531515],
    [1.86550156552673, -0.14072763828438, 0.97247958376767, 0.92915754697574],
    [2.26547073057098, 0.91371298454315, -0.43647863663936, -0.53238197326078],
]
tri_stripII_lst = [
    [-0.69362254088142, 2.38373403418518, 1.12540195883482, 2.80355554415757],
    [0.09629061756709, -2.91092248433502, -2.35388356091756, 1.03837431060550],
    [1.17332467422812, -0.24756466527240, 1.14395360328353, 2.83771844306432],
    [1.37069771705125, -0.35176917019447, 1.19000572265938, 1.71952604623164],
    [1.31049470930839, 1.17463501301557, -1.07555327879501, -2.07055828829182],
    [0.47844907061731, -3.11741772085051, -1.80098788516932, -0.52451906799578],
    [0.51959604688452, 0.76355637010840, 1.83252293691646, 0.46624698504759],
    [1.33410876379647, 2.08881378038930, -2.32834211268823, 0.84859253213960],
]
star_1loose_lst = [
    [-0.81142273548842, 2.85083403928635, 1.18216024965310, -2.70047377151463],
    [-1.21506315717322, 2.93006671867142, 1.00937089605469, 2.42005891198377],
    [-0.94465584247634, 2.87638285396723, -0.40718613561263, 2.96586351999360],
    [1.19412338664371, 0.16137415712461, -2.29266606781489, 0.03662848733984],
    [1.20377848635275, 0.13386242322661, 2.54077860797219, 2.43942299481562],
    [-1.32523586632917, -2.88734331525333, -2.16138901186289, 1.32969766773105],
    [1.36816040860704, 0.10811746779092, -2.35113337772615, -2.98884164129773],
    [1.47105580978029, 0.14753269846663, 2.54909209039421, -2.91488755387680],
    [-1.49207629361121, -2.93277122606770, -2.23152842080190, -1.86852309562604],
    [1.54260557596264, 0.38028370870509, -1.56553254976155, -0.64108898782938],
    [-1.55116965220879, -2.72393307676758, 2.68246356045397, 1.69561240021363],
    [1.65158126291632, 0.36187359223972, -1.42927076612900, 2.61058945301330],
    [-1.81698522778141, -2.74545517513101, 2.67360601790901, 0.74151399711279],
    [-0.68546957884665, 2.78127538315248, -0.31603033027856, -0.03830144233805],
    [1.99939675053623, 0.65298011622706, 0.04039762587948, -1.60079260474348],
    [2.39554479547758, 0.55231438005714, 0.13662981090527, -0.30328035155114],
]
star_star_stripI_lst = [
    [-1.22260371750574, -2.99205038412571, -1.73434757847385, 1.00120296146588],
    [1.70366871574624, 0.48617998982302, -1.13365527357588, -1.02865509313374],
    [-1.80740788961808, -2.74317592902226, 2.65777187518199, 0.79117849981711],
    [2.27628059186854, 0.62193558416885, 0.28329365947416, -0.95529926140711],
]
w_1loose_lst = [
    [1.19423195843308, 0.16141093995103, -2.27225440847440, -0.03635132578961],
    [-1.18853806763301, -3.06102481150444, -1.02779971099380, -1.56034074007749],
    [1.49409704014095, 0.33974563286372, -1.98781647418485, 0.60200250434108],
    [-1.88914174123419, -2.76026472383488, 3.01383776569834, -0.62198120129139],
    [-1.91137145406479, -3.05018072795358, 2.61671860013220, -2.10136443067107],
    [-0.68551804530956, 2.78125288828392, -0.33722704582774, 0.03825367095850],
    [2.39842030381648, 0.32870888413383, 0.38947670319288, 2.65309479188734],
    [2.40907652218932, 0.54777022088717, -0.02108869585009, 0.28553661166806],
]
w_altStripII_lst = [
    [1.23185092774940, 0.66431605798013, -2.74441864600398, 2.32392014806128],
    [-0.81465964210344, -3.00549140297642, -2.92665979914623, -1.01345318935221],
    [-0.55505340313710, -2.69125216105645, -1.09782320757743, -0.81706838986079],
    [1.30908519773400, 0.60112461442648, 0.32074052738904, -2.62156879940301],
    [1.06117475786354, 0.99830847874258, -1.42705942257900, -0.80511885863961],
    [1.06686804253110, 1.19686592568144, -0.48555269009590, 1.44182265898233],
    [1.05536196653656, 1.12474663828394, 1.12483366740861, -1.33914310438363],
    [1.37597091321302, 1.44593836355620, -0.34025212696834, -1.12323954624660],
]
trap_1loose_lst = [
    [-0.60716198509448, 2.60308149320211, -2.21106088677011, 3.14159265358979],
    [-0.60716198509448, 2.60308149320211, 1.64364653590445, 3.14159265358979],
    [-0.60716198509448, 2.60308149320211, 3.09468799862102, -0.26432165270370],
    [-0.60716198509448, 2.60308149320211, 0.66621011411599, -0.26432165270370],
    [2.40909972089932, 0.53851116038769, -0.93053176681969, 3.14159265358979],
    [2.40909972089932, 0.53851116038769, 1.49794611768535, 3.14159265358979],
    [2.40909972089932, 0.53851116038769, 0.04690465496878, 0.26432165270370],
    [2.40909972089932, 0.53851116038769, 2.47538253947381, 0.26432165270370],
]
trap_altStripI_lst = [
    [1.21240236475972, 0.27119539728104, 1.36660607167282, 3.10170622842439],
    [1.38632621149380, 0.17318734586590, 1.61277790657888, 1.90924512197131],
    [1.37151602262447, 0.39473270260021, -2.98165308358741, 1.49126125819386],
    [1.30076900282693, 0.69337056798703, -1.32135958018179, -2.41232850672659],
    [-0.65595814088969, 2.88400446569596, 1.43096450609776, -3.06934945466702],
    [0.36574515632647, 1.62539314315012, 2.67509467765368, 1.26983345818252],
    [0.31828398151567, 1.66084184167949, 2.94839264070323, 1.30435217405949],
    [0.28966469975200, 2.59709344493335, -3.01114829394796, -1.32610713382458],
]
trap_altStrip1loose_lst = [
    [1.36602540378444, 0.13157816916630, -2.35755144072579, 2.06457033281442],
    [1.36602540378444, 0.13157816916630, 1.49715598194876, 2.06457033281442],
    [-0.36602540378444, 3.01001448442349, 2.35755144072579, -2.06457033281442],
    [-0.36602540378444, 3.01001448442349, -1.49715598194876, -2.06457033281442],
    [-0.36602540378444, 2.22597327155949, -2.35755144072579, 2.06457033281442],
    [-0.36602540378444, 2.22597327155949, 1.49715598194876, 2.06457033281442],
    [1.36602540378444, 0.91561938203030, 2.35755144072579, -2.06457033281442],
    [1.36602540378444, 0.91561938203030, -1.49715598194876, -2.06457033281442],
]
NoO3Triangles = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: par_1loose_lst,
	trisAlt.strip_I: par_star_stripI_lst,
	trisAlt.star: par_star_stripI_lst,
	trisAlt.star_1_loose: par_1loose_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_1loose_lst,
	trisAlt.strip_I: tri_star_stripI_lst,
	trisAlt.strip_II: tri_stripII_lst,
	trisAlt.star: tri_star_stripI_lst,
	trisAlt.star_1_loose: tri_1loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: star_1loose_lst,
	trisAlt.strip_I: star_star_stripI_lst,
	trisAlt.star: star_star_stripI_lst,
	trisAlt.star_1_loose: star_1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_1loose_lst,
	trisAlt.star_1_loose: w_1loose_lst,
	trisAlt.alt_strip_II: w_altStripII_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_1_loose: trap_1loose_lst,
	trisAlt.star_1_loose: trap_1loose_lst,
	trisAlt.alt_strip_I: trap_altStripI_lst,
	trisAlt.alt_strip_1_loose: trap_altStrip1loose_lst,
    },
}

###############################################################################
par_stripI_lst = [
    [-0.08705843892515, 1.59694187025424, -1.42186719773489, 2.99244917462248],
    [0.49431990960006, 0.84938187722147, -1.96438419341773, 0.66547727260192],
    [1.30761782620478, 2.29221077636832, 1.96438419341773, 2.47611538098787],
    [1.88899617472999, 1.54465078333555, 1.42186719773489, 0.14914347896731],
]
par_stripII_lst = [
    [-0.11267755272150, -3.08314500505623, 1.38775788215077, 1.84497131694611],
    [-0.11267755272150, -3.08314500505623, 1.38775788215077, -2.11536359084037],
    [-0.11267755272150, 1.62991562536377, -1.38775788215077, -0.90997250329841],
    [-0.11267755272150, 1.62991562536377, -1.38775788215077, 3.05036240448807],
    [1.91461528852634, -0.05844764853356, -1.38775788215077, 1.29662133664368],
    [1.91461528852634, -0.05844764853356, -1.38775788215077, -1.02622906274943],
    [1.91461528852634, 1.51167702822602, 1.38775788215077, -2.23162015029139],
    [1.91461528852634, 1.51167702822602, 1.38775788215077, 0.09123024910172],

]
tri_stripI_lst = [
    [0.25766456904200, 1.23370849975870, -2.88823619661503, -2.55090394983209],
    [0.37227438884523, 1.67003860855452, 2.91884346747981, 2.57168321468181],
    [0.05034522603356, -2.84141477449258, -2.72796058287286, 1.59467046494364],
    [0.39147088895531, 2.53782687789367, -2.06356261454296, -2.15294978396779],
    [1.42577972511488, -0.33679604065731, 1.16588964454869, 1.62899326768965],
    [0.20961214592661, 0.93160515044760, 1.93474923340972, 2.02846591163361],
    [0.51952198057739, 0.76902767459531, 1.83720793949263, 0.44126270894260],
    [1.89033377832022, 1.54063607626176, -1.46278122794071, 0.09760150131543],
]
tri_stripII_lst = [
    [-1.02088206579342, 2.92215615986198, 0.49874432369016, -2.27469172529300],
    [-0.30975269902860, 1.79044847695879, 1.62192662119917, -0.75561499170429],
    [1.92672214289072, -0.10378911932353, 0.94538490616541, 0.81967055842755],
    [1.91479704822392, 1.51052615552960, -1.41456430513121, 0.06151762464484],
]
star_stripI_lst = [
    [-1.11479786012615, -3.01136198833584, -2.54651752372087, 2.08855752521128],
    [-1.21826652797755, -2.99298511952277, 2.58417032463309, 2.46891518155374],
    [1.61481708939396, 0.49256598699692, -0.36015420508179, -2.08846039896341],
    [1.74404819266953, 0.48593702238864, 0.76207581689038, -2.35738396251911],
]
star_stripII_lst = [
    [-1.11461130570509, -3.01138793355110, -2.51934738959092, 2.06457033281442],
    [-1.11461130570509, -3.01138793355110, -0.36530274804017, -2.06457033281442],
    [-1.41754988476213, -2.93758682322695, -2.00684651699682, -2.06457033281442],
    [-1.41754988476213, -2.93758682322695, 2.12229414863202, 2.06457033281442],
    [1.61456486022518, 0.49259642882540, -2.54173379839552, 2.06457033281442],
    [1.61456486022518, 0.49259642882540, -0.38768915684478, -2.06457033281442],
    [1.88523668938655, 0.49674376007488, -1.21199946174003, 2.06457033281442],
    [1.88523668938655, 0.49674376007488, 0.94204517981071, -2.06457033281442],
]
w_alt_atripI_lst = [
    [-0.89547889748827, -3.01890952973987, 2.00192299941082, 2.06457033281442],
    [-0.89547889748827, -3.01890952973987, -2.12721766621801, -2.06457033281442],
    [-0.68153184629161, -2.94538811002813, -2.75594521707258, 2.06457033281442],
    [-0.68153184629161, -2.94538811002813, -0.60190057552184, -2.06457033281442],
    [1.18246612652976, 0.71940546828616, -2.77214313178643, 2.06457033281442],
    [1.18246612652976, 0.71940546828616, -0.61809849023568, -2.06457033281442],
    [1.39159603088392, 0.55424480380267, -0.60305675188567, 2.06457033281442],
    [1.39159603088392, 0.55424480380267, 1.55098788966507, -2.06457033281442],
]
w_alt_atripII_lst = [
    [-0.89515429888633, -3.01887822399782, -2.09960357585013, -2.08823628536480],
    [-0.80526172599003, -3.00308178439659, -0.98732926243628, -2.43419758675807],
    [1.34493627420240, 0.57859595525542, -1.88133557756927, 2.65837008086174],
    [1.39251471695486, 0.55381552638265, -0.62315016480008, 2.08557475421552],
]
trap_alt_atripI_lst = [
    [1.37513217304298, 0.38161199538121, 0.73933240627855, 1.50858819316313],
    [1.26728811420110, 0.64538993311463, -1.86221766328240, 1.24098803506008],
    [0.90922235933844, 1.14789375852737, 1.20694992843107, 1.04870138148561],
    [0.65127907401936, 1.39756313984052, -1.94580249342009, 1.10727914914277],
    [1.35874499282133, 1.35818756471779, 1.71045465055478, -1.44026580355118],
    [1.14208824990637, 1.72603787032894, -1.13965255265727, -1.11624198566344],
]
trap_alt_atripII_lst = [
    [-0.62733301528653, 2.98274108690679, -2.80119010201015, -2.77982863376248],
    [-0.62733301528653, 2.98274108690679, 1.15914480577633, -2.77982863376248],
    [1.21769219373579, 0.36925126784640, -2.91442530699528, -2.97299720740092],
    [1.21769219373579, 0.36925126784640, 1.04590960079119, -2.97299720740092],
    [1.38222572563533, 0.35279275358404, -3.12412713146115, 1.54871690731114],
    [1.38222572563533, 0.35279275358404, 0.83620777632532, 1.54871690731114],
    [-0.31314273379578, 2.98942711952296, 1.57190002582026, -1.97892254968544],
    [-0.31314273379578, 2.98942711952296, -2.38843488196622, -1.97892254968545],
    [0.65102616496660, 1.39778197282034, -1.94649757899530, 1.10738416257284],
    [0.65102616496660, 1.39778197282034, 2.01383732879118, 1.10738416257284],
    [1.14172874232229, 1.72649858941196, 2.81921140330005, -1.11600414739872],
    [1.14172874232229, 1.72649858941196, -1.14112350448642, -1.11600414739872],

]
FoldedSquares_0 = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_I: par_stripI_lst,
	trisAlt.strip_II: par_stripII_lst,
	trisAlt.star: par_stripI_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_I: tri_stripI_lst,
	trisAlt.strip_II: tri_stripII_lst,
	trisAlt.star: tri_stripI_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_I: star_stripI_lst,
	trisAlt.strip_II: star_stripII_lst,
	trisAlt.star: star_stripI_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.alt_strip_I: w_alt_atripI_lst,
	trisAlt.alt_strip_II: w_alt_atripII_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.alt_strip_I: trap_alt_atripI_lst,
	trisAlt.alt_strip_II: trap_alt_atripII_lst,
    },
}

###############################################################################
par_stripI_lst = [
    [-0.75674704295826, -2.55761995555076, 1.17954542442379, 2.30598578936627],
    [-1.16786610784715, -2.81210297642871, 0.68295574950813, -2.71396552749153],
    [-0.41297524742966, -3.11749720742871, 1.75164007618928, 2.79576640194874],
    [0.07750845894116, -3.11324257681366, 2.50814338734656, -1.01302877517395],
    [1.30834976048157, -0.11407862135811, -1.28543926652841, 2.71291935303656],
    [0.25783404055203, -2.55463073632741, 1.76367227876318, -2.26470775632203],
    [1.79065357209322, 0.18641414197294, -0.10475933583316, -1.41814382923850],
    [1.70431863922488, 2.55632923477770, 1.72437906070702, -0.22076373594904],
]
par_star_lst = [
    [0.16424126714815, 2.94983629936611, 2.38742404973280, -1.10582488930591],
    [-0.19882278292563, 2.90321596718878, 1.56107999385331, 2.47838684280309],
    [0.25790649607642, -2.55499465107797, 1.76329511870384, -2.26530719663696],
    [0.93204577472518, 1.54777566349488, -0.99061381559026, 2.13117863238131],
    [1.40343117245689, 0.99681726039766, -1.43319750482819, 1.46749507846837],
    [1.86053127487713, 2.30664356030554, 1.49091528052181, -0.17100514406484],
]
par_star_1_loose_lst = [
    [0.47092324271707, 2.44771371251441, 2.20204864641939, -1.64063400125757],
    [0.46605546632810, 2.44771371251441, 1.61808115873236, 2.14662658835882],
    [-0.02309808599809, 2.44771371251441, -0.43468821406451, 0.09492833600657],
    [1.17900085664874, 0.69387894107539, -2.18852298550353, 0.09492833600657],
    [1.67302218536390, 0.69387894107539, 0.44821387498037, -1.64063400125757],
    [1.66815440897493, 0.69387894107539, -0.13575361270665, 2.14662658835882],
    [0.35276606332980, 2.44771371251441, 0.01319861784330, 0.76713308744684],
    [1.55486500597663, 0.69387894107539, -1.74063615359572, 0.76713308744684],
    [1.64260048186392, 2.44771371251441, 1.44714924051438, 0.83140338555908],
    [1.76340988604600, 2.44771371251441, 1.61017718884215, -0.48553086554936],
    [2.84469942451076, 0.69387894107539, -0.30668553092463, 0.83140338555908],
    [2.96550882869283, 0.69387894107539, -0.14365758259687, -0.48553086554936],
]
par_alt_stripI_lst = [
    [0.00471440287453, 2.73799034131047, 2.30190279838418, -2.11875884989574],
    [-0.17436128088860, 2.68944203337113, 1.71418754395880, 3.12477982513501],
    [1.43961601917280, 0.40355341653011, -0.04013610323553, 2.99839678466072],
    [0.04856133551218, 2.73517851563913, -1.39468972454765, 2.12122832057603],
    [1.65457725101705, 0.45992003113629, 0.47265909450438, -2.17880736383350],
    [0.29960308976707, 2.66253569862452, -0.95458098169674, 3.08544192637811],
]
tri_strip_1_loose_lst = [
    [0.44754647931561, -0.69387894107539, 2.92834163399893, 0.73546911098848],
    [-0.75455246333122, -2.44771371251441, -1.60100890174164, 0.73546911098848],
    [0.38799249591741, 0.69387894107539, -2.74819340150401, 1.92173053747138],
    [-0.81410644672942, 2.44771371251441, 1.78115713423656, 1.92173053747138],
    [-0.00078144583645, -0.69387894107539, -2.91050327487731, 2.48177593930505],
    [-1.20288038848328, -2.44771371251441, -1.15666850343830, 2.48177593930505],
    [-0.08688372277556, 0.69387894107539, 2.78718130570433, 1.61427121470359],
    [-1.28898266542239, 2.44771371251441, 1.03334653426532, 1.61427121470359],
    [0.35471767008943, -2.44771371251441, -2.76087095029002, -2.90452681909672],
    [1.55681661273626, -0.69387894107539, 1.76847958545055, -2.90452681909672],
    [0.62055916052970, -2.44771371251441, -2.84498180899120, 1.38574096213672],
    [1.82265810317653, -0.69387894107539, 1.68436872674937, 1.38574096213672],
    [1.23686276913150, 2.44771371251441, -1.96402647301060, -1.99967600727022],
    [2.43896171177833, 0.69387894107539, -0.21019170157158, -1.99967600727022],
    [1.78657879956534, 2.44771371251441, -1.50735938826674, -0.53632250360021],
    [2.98867774221217, 0.69387894107539, 0.24647538317228, -0.53632250360021],
]
tri_strip_I_lst = [
    [0.32299168861477, 0.81787517156585, -2.87413588496860, 1.85225400431776],
    [-0.77636060799865, -2.08140475401946, -1.73958529946183, 2.73271394973505],
    [-0.04723487325003, 0.06258460712478, -2.38671144858821, -1.48453981633907],
    [-0.29248954348814, -2.18443368288040, -2.22182409883003, 1.06635128074660],
    [-1.01799922462476, 2.13894198768247, 1.51116359259080, 1.53572166969937],
    [-1.44236685802038, 2.54741742475946, 1.28997788178645, -0.78592785211070],
    [1.66897084570198, -0.78128633249252, 1.83289680770929, 1.42175536953673],
    [1.72381664483347, -0.55602013972734, 1.52859348074324, -2.82195307291712],
    [2.37251933652804, 1.19129517242525, -0.65696083790277, -1.71891761592764],
    [2.38590549637651, 1.43710833335703, -0.76500995390104, -1.39326135253571],
    [1.72203191383200, 2.53558229944050, -1.63982592103371, -0.19008008335462],
    [1.93689739577824, 2.19172817353844, -1.33197246309659, -0.96931527394341],
]
tri_strip_II_lst = [
    [0.31858957474878, 1.14166043144719, -2.93683270115961, 1.69867105290443],
    [0.13597220632769, -0.51427349788053, -2.31353037885290, 2.97405475636488],
    [-0.40803835417222, 1.28561236253108, -2.96853666210979, -1.31643092011173],
    [0.13409835406810, 3.00164856580105, -2.96937654227576, 0.69562341531837],
    [0.18538185465247, 2.98449260251112, -2.44628421210721, -0.51584488859613],
    [0.59520985104518, -0.76917621844761, -2.78860910079686, -0.70538824942031],
    [-0.41715794679440, -2.32618033839750, -1.26802551155463, -0.76488269498586],
    [-0.19301695451949, -2.32427171897039, -2.01546250998143, 0.69859799471544],
    [1.21474912570783, -0.12084562635448, 0.98864515115734, 0.77202589564433],
    [1.04260475400867, 0.27798862722358, 0.76229978633983, -2.25757097298944],
    [-1.18149344045203, -3.02130495447940, 1.48027787808807, -2.71392551755474],
    [0.77196244815249, -1.35515501553250, -2.73859996161913, -2.33669773849788],
    [-1.28599584979710, -2.62897724742894, -0.54837631731554, 2.68325718737157],
    [0.52783872759655, 2.47407169283164, -3.09533964138497, 0.45861159649013],
    [0.60540787695390, 0.75782334028724, 1.81894311328778, -1.11202199624734],
    [0.79713298491615, 0.53938481768733, 1.20640082125284, 0.46661717099783],
    [0.98163637024195, -3.04384735758217, -1.89113999800681, -1.73431031817884],
    [1.03053816920326, 3.07744132850230, -3.08792699431892, 1.83942717344485],
]
tri_star_lst = [
    [0.44390704949173, 1.24903174649422, 2.90146525881087, -0.85699420749520],
    [-0.15138062756318, 2.35467557291936, 1.48524998481694, 1.88705123470690],
    [1.30964636634988, 0.48679814368217, 1.74732298455689, 2.61292689652376],
    [0.63228897865292, 2.43104850385314, -1.52066710389413, 1.63190552771308],
    [0.90223122416310, 2.13525691523148, -1.07059384912214, -2.71944623806126],
    [1.62937650502967, 0.66790870605199, 1.24107019359923, 0.81936466242207],
    [2.32391378359911, 1.05485084903657, -0.56479739374247, 1.14597861161990],
    [1.87216498452764, 2.29316525338580, -1.42622028541672, -0.13919943851842],
]
tri_star_1_loose_lst = [
    [0.53322110854061, 0.69387894107539, -2.74791829741406, -1.17708579095949],
    [-0.66887783410622, 2.44771371251441, 1.78143223832650, -1.17708579095949],
    [-0.22830290855592, 2.44771371251441, 1.42459966163779, 1.94705515494047],
    [0.97379603409091, 0.69387894107539, -3.10475087410278, 1.94705515494047],
    [-0.16496706510380, 2.44771371251441, 0.29120719670181, 2.16415855734472],
    [1.03713187754304, 0.69387894107539, 2.04504196814083, 2.16415855734472],
    [0.36052223088634, -2.44771371251441, -1.54479211227053, -1.24429564696108],
    [1.56262117353317, -0.69387894107539, 2.98455842347003, -1.24429564696108],
    [0.50088247512095, -2.44771371251441, -1.68163684618035, -1.49949503969355],
    [1.70298141776778, -0.69387894107539, 2.84771368956022, -1.49949503969355],
    [0.48150779101397, 2.44771371251441, -1.09881608299420, -3.04530851239526],
    [1.68360673366080, 0.69387894107539, 0.65501868844482, -3.04530851239527],
    [0.58981054017822, 2.44771371251441, -1.47392826640240, 1.62639576331028],
    [1.79190948282505, 0.69387894107539, 0.27990650503662, 1.62639576331028],
    [-0.02502415570448, 2.44771371251441, 0.40755107877418, 0.06566292996177],
    [1.17707478694235, 0.69387894107539, 2.16138585021320, 0.06566292996177],
]
tri_alt_stripII_lst = [
    [-0.25197931382322, 2.49681408056250, 2.78351325773691, -0.47092963435339],
    [-0.07607292024921, 2.73134966760057, 2.21404233731966, -0.79687434593069],
    [-0.13780439608927, 2.71136847396102, 1.73144604123467, 0.50769513628475],
    [0.16675695221048, 2.71120991555836, -3.05892377057877, 0.74975905213282],
    [0.24370538889822, 2.68540426258982, -2.52373117900723, -0.52199523535077],
    [0.27307281405405, 1.61848986965282, -2.96781348893059, 1.39141557092361],
    [1.10210778277598, 0.54018457880893, 0.40004937433249, -1.87362433299020],
    [1.19343930789188, 0.47341395959315, 0.32553894817865, 0.49884319995192],
    [0.59668670327101, 2.49611550137255, -3.06458314431992, 0.47077022051391],
    [0.63112288319848, 2.47285797387105, -3.03134579494625, -2.02016121936477],
    [0.91150375944907, 0.75061734340560, 1.13880081317775, -0.77149860513431],
    [0.98410586375346, 0.66049745122663, 0.62343188848073, 0.47400581409007],
]
star_strip_1_loose_lst = [
    [-1.28860937880210, 2.96481594385730, 0.94714796337781, -0.86167491656401],
    [1.48374766798713, 0.15040610301462, 2.55081574449938, 1.05547402218988],
    [-1.59350269848469, -3.10308139516830, 0.64751175146331, 1.66725341941007],
    [-1.61686115843649, -3.10845780547588, -0.73571105532667, 2.47802753327945],
    [-1.64555608422284, -3.09366056763040, -0.75505311109412, 0.68924262783273],
    [1.77433471170479, 0.16529614343381, -2.28797801059004, -0.58618242384645],
    [-1.85525589044037, -2.92950065224366, -2.22691369591818, 1.97245533135039],
    [-1.84555945979346, -2.74171263315807, 2.67516488589105, 2.77257658530695],
    [1.94548992989198, 0.21289904619267, -2.22576587397447, -2.53493210801746],
    [1.92285048425565, 0.36613806142495, 2.66081952140361, -1.98078257817196],
    [-2.02469723007411, -2.89795697470182, -2.17906623481193, -2.40831332147189],
    [2.07311709033757, 0.30007358064875, -1.20687998019382, -1.46789739026177],
    [2.28202754586709, 0.30895022645769, -1.23176341911183, 2.79825652416958],
    [-2.30410500625427, -2.52894684936577, 2.75190008515463, -0.12724592043701],
    [2.44567506736800, 0.55520404439515, 0.13391170067069, -2.16872722663553],
    [2.99998593913152, 0.84494216053379, -0.16077962510244, -0.30248301525128],
]
star_strip_I_lst = [
    [-0.94021209022316, -3.02177621919833, 1.19044768730122, -2.18490097685171],
    [-1.56330625567632, -2.88085773091565, 1.07942666915478, 1.67050716679755],
    [1.53159355059202, 0.50685693288740, 2.06390254260684, 2.16688839382212],
    [-1.82403894961285, -2.73059073244033, 2.61208902761332, 2.80932566963383],
    [-1.95508540048682, -2.59077450828923, -0.78118012852338, -0.62781434178852],
    [1.91612752945751, 0.50139673186948, 2.40555731922748, -1.99909356023056],
    [-1.96662528621987, -2.36733007082143, -1.49013655617766, -2.11598342889064],
    [-1.97873834396653, -2.39434953462564, 2.22635312378409, 0.79736686374948],
    [2.47313351472613, 0.80993826952587, -2.11391673596283, 0.85290899148984],
    [2.44502302410993, 0.76178967903374, 0.44070831888194, -2.20472197896819],
    [2.49042950000326, 0.92343862154126, -1.79578996962624, 1.86566958985253],
    [2.48803046628442, 0.85555869332064, 0.45903094420169, -2.01022214226310],
]
star_strip_II_lst = [
    [-0.93627625766294, -3.02163325820648, 1.04540448987856, -2.07482853171993],
    [-1.09515403416492, -3.01394108847450, 1.55019788427994, -2.32474470636509],
    [1.51563849004002, 0.51064712409938, 2.20072965411049, 2.07091957381252],
    [1.59560165651310, 0.49509884315157, 1.83042991386341, 2.31394763858198],
]
star_star_lst = [
    [-1.11662206508348, -3.01110683936746, 1.28985436603708, 1.57642395715170],
    [-0.72418179468738, -2.97203708160068, -1.06250216904199, 2.79397165257424],
    [-0.69871823672963, -2.95726405150610, 0.89332342187773, -2.41729109649706],
    [1.30571045084907, 0.60343920210080, -1.98831707066625, -0.84776923369278],
    [1.21655585978424, 0.67987145400250, -2.27198437827245, -2.60837499020766],
    [-0.76019293502482, -2.98837666607554, -1.13261349967446, 1.02900223040440],
    [1.20393134847645, 0.69366804357950, 2.06875322822164, 2.40136354601652],
    [1.61337672951644, 0.49274081728097, 2.08641470894504, -1.59245051369080],
    [-1.60315924886261, -2.11792603397534, -2.41921193046732, -1.62492618579575],
    [-1.98880604803693, -2.43029922106746, -1.30373469355483, -0.07523718804855],
    [2.33112357492184, 0.65567414334004, 0.35110586968738, 0.75406176421248],
    [2.49133872759834, 0.87753358321631, -1.92285559481840, 0.60722472228158],
    [2.43459045248742, 1.05054213455631, -1.42910207655114, 1.69753059756122],
    [2.43640695426439, 1.04808055692546, 0.46321427231468, -1.66046168034951],
]
star_star_1_loose_lst = [
    [-1.05277372700361, -2.76211703267050, -1.55590150479355, 1.37087696416695],
    [0.88738781263340, 0.36402083383768, 2.65989716558774, 1.39532996095746],
    [-0.82085407458240, -2.86857816216647, -1.13832842066032, 2.91059553751202],
    [-0.76256050710240, 2.85359800973022, 1.17506900373627, 1.72015981271912],
    [1.18141289560666, 0.13777824432098, 2.54317933831597, -1.77177431506773],
    [-1.22812229496257, -2.43696977752568, 2.77841036590193, 2.75927748194424],
    [-1.54091244057999, -2.72054165890190, 2.68383594977462, -0.71579457014568],
    [-0.21021895948350, 2.66789265280290, -0.21007825655307, 2.38875283927776],
    [-0.43517063489267, 3.08450974527425, 0.76723800508306, -1.88611093153925],
    [1.77454329488816, 1.01809566165758, -0.38600103766333, -2.47078701903565],
    [1.81849088579533, 0.84277938922334, -0.15830362136157, 1.82873915768509],
    [-0.14951248888139, 2.79506003552059, -0.32905572345441, 0.40418528715570],
]
star_alt_stripII_lst = [
    [1.15256121805186, 0.76115920365358, -0.94537987231517, 1.31282987241159],
    [1.20528774760964, 0.69214121092974, -0.28578037584998, 0.81620274459506],
    [1.11308351556869, 0.83173732068463, -0.45487988402173, -1.38211559664347],
    [1.09614239994711, 0.87084471976089, -0.68690764335104, -1.17924739400001],
    [-1.09721020245809, -2.06566632975083, -1.33656340521962, -2.86646879309071],
    [-1.27224280516521, -2.05747644742882, -1.44251055361169, 1.52595937184746],
    [1.59631959846057, 1.44300045459322, -2.03600466608929, 2.87035030260465],
    [1.76572521039679, 1.41128467232697, -1.87406416225271, -1.44895121671378],
]
w_strip_1_loose_lst = [
    [1.41394510984909, 0.20140469516787, -1.31767479483779, -1.10840807690592],
    [-1.46093574797313, -3.11715591412372, -2.81621807701362, 1.68609168947026],
    [1.47884179291828, 0.25690429859812, -1.20043952816167, -1.00731640681100],
    [-0.92958729311946, 2.83410180250928, -1.10413072968001, 1.32280589434661],
    [-1.69399089299223, -3.09166852155541, -0.41355694353579, -0.72932751437186],
    [1.78947815786381, 0.15767608577289, -2.57531380507558, 0.61191576547422],
    [-1.79834739524326, -3.10174328624454, -0.62254889494090, -1.75271662727611],
    [-1.84590303784044, -2.51941618145860, -1.17686745589437, 1.94190142602837],
    [1.94030237871565, 0.19193694923390, -2.25283536808616, 1.27745881335746],
    [-2.04527484519088, -2.24045236775195, 2.85303974624967, 2.26891367119626],
    [-2.15168407857857, -2.86739759108780, 2.13810333446481, -2.39278707567943],
    [2.24120696075732, 0.81694517710027, -1.86268942716808, -2.03104070125743],
    [-2.23551914115473, -2.06079238541829, -2.88418874518903, -0.78106949447450],
    [-2.30586156349442, -2.52887530113275, 2.68097389324333, 0.12973156964592],
    [-2.41147177355398, -2.27979255665610, -1.84094531421569, -1.97407262114868],
    [3.01105384002591, 0.87452894641386, -0.47746916484803, 0.46062802041400],
]
w_strip_I_lst = [
    [-1.95525321710355, -2.59049328270500, -1.10911320808944, 0.77471927198997],
    [-1.99040227402117, -2.44020497950186, -1.33073009162746, 2.80703590915616],
    [-1.92290087575886, -2.63632594129386, 2.34275893358721, -1.87615327437277],
    [-1.91597614123300, -2.29760733100410, 2.69749589779872, 2.76581852893972],
    [2.46103178111000, 0.78638559054164, -1.73250255182291, -0.90236202410876],
    [2.48616595115303, 0.84737916208121, -1.65179261033325, 2.90608949613917],

]
w_star_lst = [
    [1.33762061562180, 0.58290224101339, -2.42200646678792, 0.94386501480172],
    [1.33762061562180, 0.58290224101339, -2.42200646678792, -2.56380452807632],
    [-0.80300858893845, -3.00247326640884, -0.58021483191817, -1.11606815459685],
    [-0.80300858893845, -3.00247326640884, -0.58021483191817, 2.39160138828119],
    [-1.44434090313371, -2.92823019460112, 2.22972454221257, 1.63724584208769],
    [-1.44434090313371, -2.92823019460113, 2.22972454221257, -1.13826992221386],
    [-1.98887880595554, -2.43069147109465, -1.34471654774388, 0.07671139680320],
    [-1.98887880595554, -2.43069147109465, -1.34471654774388, 2.85222716110475],
    [-1.83904901148363, -2.23195159152113, 2.73306797317728, 2.38074550526205],
    [-1.83904901148363, -2.23195159152113, 2.73306797317729, -1.12692403761599],
    [2.48788226988366, 0.85484835263680, -1.64210911944209, -0.64037311188878],
    [2.48788226988366, 0.85484835263680, -1.64210911944209, 2.86729643098925],
]
w_star_1_loose_lst = [
    [1.08013604438774, 0.44660563723172, -2.58820372454350, -1.82440945564423],
    [-0.84621027034276, -2.97462880278437, -0.60913171213819, -1.19409318264532],
    [-0.85986354995465, 2.80904367929160, -1.08672976694220, 1.35325968724443],
    [-1.20192478700811, 3.02388086211114, 2.32530546839482, -1.51734168944640],
    [-1.37571578181481, -3.08619221463607, -2.80088066303002, 1.55439852456142],
    [1.55353858433165, 0.67136306449654, -2.29035315300550, 2.71985731582789],
    [-1.57803476661294, -2.76621770839308, 2.27190146477006, 0.72242564778112],
    [1.63532445237280, 0.12911032762258, 0.98405778420210, 2.02951927201631],
    [1.67352132188238, 0.39044292297937, -0.76564278755521, 2.50591770358576],
    [1.76059844831402, 0.20178509499477, 0.18623979032520, 2.36604567794930],
    [-1.78110704220358, -2.50109543827676, -1.19870806628975, 1.91947432996353],
    [-0.17015990428719, 2.80848916592049, -0.12196708112367, -0.39709330721430],
    [-1.86153756568965, -2.18734123816754, 2.79603362774215, 2.10262709863154],
    [2.03823948921544, 0.44768020065761, 1.04132125180523, -1.58835380532494],
    [2.22635634191104, 0.82488093695710, -1.86201568716335, -2.01830581406569],
    [-2.23197323726809, -2.05834430826279, -2.88434557544456, -0.77995323961042],
    [-2.40845936924428, -2.27608146033915, -1.84378974276347, -1.96604643079069],
    [2.78828359850887, 0.74460408491879, 0.32125145803992, -2.51720800801328],
]
w_alt_stripI_lst = [
    [-1.05871167522005, -3.01787471610111, 0.55854068799585, 2.07090509369307],
    [-0.91379944670743, -3.02042250499416, 0.04237847271763, 2.34823473572220],
]
w_alt_stripII_lst = [
    [-1.05186288142482, -3.01848451753374, 0.41051666040856, 2.18083760456236],
    [-0.57087037409510, -2.52126440944568, 1.70071853927751, 0.77089923712725],
    [-0.59862061070378, -2.84993899349043, 0.35619783865848, -1.59486973549981],
    [-0.55482280638325, -2.68762727862611, -1.07530354933894, -3.08755312478932],
    [-0.57287873121319, -2.51328888481606, -0.44116694441973, -0.76515175763183],
    [-0.67554234292394, -2.29919722724531, 2.56742536131597, 2.70110860825989],
    [1.08999525020716, 1.26218698618845, 2.01050035416810, -1.55402541617111],
    [1.05565680760114, 1.12841609632837, 1.14821321861760, 2.67434841988099],
]
w_alt_strip_1_loose_lst = [
    [-1.00521400195716, -3.06434116083678, 0.46137368668854, 2.06576847260004],
    [-1.06537282248988, 2.93007418297527, -2.08202148112117, 2.21211948735867],
    [-0.99120848418862, 2.87544532305168, -1.74106124471176, 2.09223244593432],
    [-1.19865317260034, -2.60258590356852, 1.48492494756313, 3.11145312824067],
    [1.35417186655198, 0.79941781237126, 2.30708300322377, 2.15909908666379],
    [1.69271794153767, 0.92263069812863, 2.99610519487722, 2.25106302564045],
]
trap_strip_I_lst = [
    [1.77734704393116, 0.27135338029222, 1.15003177142154, -0.72112734960647],
    [1.79202702716715, 0.24593525285184, 1.44999426705331, -0.13080674767895],
    [0.11711226642178, 2.59266449889210, -2.76417646891705, 2.88257312792737],
    [0.28586842743154, 2.48543838851730, -2.83265586112567, 2.42750207611105],
]
trap_star_lst = [
    [1.75676708671303, 0.31527082389531, 0.85439118547116, -1.05962420493678],
    [1.75676708671303, 0.31527082389531, 0.85439118547115, 1.71589155936477],
    [-0.39996307645075, 2.86774414233561, 1.61155083518360, 1.91114561527157],
    [-0.39996307645075, 2.86774414233561, 1.61155083518360, -1.59652392760647],
    [1.68140702201143, 0.70266064691856, -1.84100235298792, -0.49783382671196],
    [1.68140702201143, 0.70266064691856, -1.84100235298792, 2.27768193758959],
    [0.35342124951099, 2.43992426213702, -2.87480920097443, -1.23770524290074],
    [0.35342124951099, 2.43992426213702, -2.87480920097443, 2.26996429997730],
]
trap_star_1_loose_lst = [
    [-0.94149073385617, 2.41226340593107, 2.66424287312342, 2.68362785746480],
    [-0.64915455540105, 2.28885046233306, 1.71454315585410, 2.31193474241987],
    [1.67386308426961, 0.76579322441586, -2.07882845525476, -0.13636009100837],
    [1.72536107208427, 0.41408057699021, 1.37821312589969, 0.47356983016804],
    [-0.14341215083593, 2.74137056730194, 0.25081107661482, -0.49782880141505],
    [0.35276152818138, 2.44037640115398, -0.77313401869837, 0.01327917122252],
    [2.87329078753567, 0.85261320086247, -0.66311903215005, -0.33052145042297],
    [2.97022766970075, 0.77256350155525, 0.54265300573129, -0.15007275145781],
]
trap_alt_stripI_lst = [
    [1.34494683873562, 0.55650985656547, -2.36485206924104, -0.95371663766669],
    [1.39606324444789, 0.22467122585883, 1.33568522054307, -1.88333367908244],
    [-0.91154301599112, -3.00358899285595, -0.08704387053481, 2.38819741739565],
    [1.43945321719827, 0.42622288065615, -2.97891669576681, -0.04211289414295],
    [1.66131899861710, 0.19973600598914, 1.91902631197716, 0.38303016636872],
    [-0.45274430193200, -2.77456678638317, -1.16059829149030, -1.12738064304644],
    [0.16095823069222, 2.55786350193807, -2.78327383304312, 2.76701370632982],
    [0.17007524802843, 3.11168883028149, -2.93120544551280, -0.67045796444216],
]

E1_1_V2_1 = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_I: par_stripI_lst,
	trisAlt.star: par_star_lst,
	trisAlt.star_1_loose: par_star_1_loose_lst,
	trisAlt.alt_strip_I: par_alt_stripI_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip_1_loose_lst,
	trisAlt.strip_I: tri_strip_I_lst,
	trisAlt.strip_II: tri_strip_II_lst,
	trisAlt.star_1_loose: tri_star_1_loose_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.alt_strip_II: tri_alt_stripII_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: star_strip_1_loose_lst,
	trisAlt.strip_I: star_strip_I_lst,
	trisAlt.strip_II: star_strip_II_lst,
	trisAlt.star_1_loose: star_star_1_loose_lst,
	trisAlt.star: star_star_lst,
	trisAlt.alt_strip_II: star_alt_stripII_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip_1_loose_lst,
	trisAlt.strip_I: w_strip_I_lst,
	trisAlt.star: w_star_lst,
	trisAlt.star_1_loose: w_star_1_loose_lst,
	trisAlt.alt_strip_I: w_alt_stripI_lst,
	trisAlt.alt_strip_II: w_alt_stripII_lst,
	trisAlt.alt_strip_1_loose: w_alt_strip_1_loose_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_I: trap_strip_I_lst,
	trisAlt.star: trap_star_lst,
	trisAlt.star_1_loose: trap_star_1_loose_lst,
	trisAlt.alt_strip_I: trap_alt_stripI_lst,
    },
}

###############################################################################
par_stripI_lst = [
    [-0.88723458825223, 2.14188240056477, -1.60032105052076, -2.14773363294970],
    [-0.46394192201745, 1.62136713239571, -2.25986345196520, 1.97952652365025],
    [1.36999606309122, 1.27750412172131, 1.15928528756939, 1.65060215911765],
    [1.69242292514361, 0.64862911839820, 0.12224970772778, 0.47344275923685],
    [1.13224737344781, 0.92172928555262, -0.84249799334321, -0.44040780307887],
    [0.77202842552826, 1.45895013798004, -0.51098977526083, 1.76773556838117],
]
par_stripII_lst = [
    [-0.80628139058344, -3.07707388469024, 0.32574461708118, 2.89840491955690],
    [-0.80628139058344, -3.07707388469024, 0.32574461708118, -1.06192998822957],
    [-0.98191238276041, 2.27603734796492, -1.39885868493813, -2.07422390940574],
    [-0.98191238276041, 2.27603734796492, -1.39885868493812, 0.24862648998737],
    [0.11745889730951, 2.70782868444711, 1.59648917375940, -2.34272887316613],
    [0.11745889730951, 2.70782868444711, 1.59648917375940, 1.61760603462035],
    [-0.31558106130085, -3.02863811129340, 0.70426173268804, 2.17442840546771],
    [-0.31558106130085, -3.02863811129340, 0.70426173268804, -1.78590650231877],
    [1.22668864524207, -0.11435973944709, -2.67183885862593, 2.92376287833734],
    [1.22668864524207, -0.11435973944709, -2.67183885862593, 0.60091247894423],
    [0.74575327119206, 1.49359518200650, -0.47983302969802, -2.12506840337249],
    [0.74575327119206, 1.49359518200650, -0.47983302969802, 1.83526650441399],
]
par_star_lst = [
    [-0.23711356273167, -1.94853213873603, 2.65888592046366, 0.27438318799069],
    [0.72053887962315, -1.05874322574544, -2.42084487093888, 2.55778085785250],
    [-0.68553105174082, -2.15335850282529, 1.87011783202008, 2.17228760943329],
    [-0.78308063986586, 2.10253532678419, -1.67760233078648, -2.42922632988355],
    [-1.04115098036155, 2.06140011643728, -1.59225944208664, -1.50115989941102],
    [1.25229387965486, -0.98083804367828, -1.93566394119323, 0.23491468889409],
    [0.99088112864734, -1.57198703509531, -3.03633676128918, 1.93485792362485],
    [1.26778079054035, 1.34917416660323, 1.39013339457184, 1.79202263715456],
    [1.41519237769160, 1.07008349510418, 1.61051596810978, -1.58049015505547],
    [1.78053833612771, 2.59300365331429, 2.15562852155596, -0.25525589134284],
]
par_alt_stripI_lst = [
    [0.70645996537001, 1.03677117867349, 2.66422281862627, -2.01485961247860],
    [0.38070865555994, 1.48038814878602, 3.00941934564430, 0.31741216539239],
    [0.44357840992435, 1.39826982652609, -1.16790170446919, 2.28495230261005],
    [0.91461250261215, 0.74656316793117, -1.55053465368167, 0.27547606947746],
    [1.32565705637010, 1.87689645136964, 1.89055661251330, 2.22016424436271],
    [1.78367507206637, 1.28939124950506, 1.30794806881816, -0.26609365097183],
]
par_alt_stripII_lst = [
    [0.75705989135543, 0.96458098235650, 2.62606185689750, -2.16281746404623],
    [0.75705989135543, 0.96458098235650, 2.62606185689750, 1.79751744374025],
    [0.10907676965557, 2.72556981512783, 1.60262566773975, 1.62229576738626],
    [0.10907676965557, 2.72556981512783, 1.60262566773975, -2.33803914040022],
    [-0.05542511921245, 2.73477408700918, -0.72544635030249, 2.35329401275702],
    [-0.05542511921245, 2.73477408700918, -0.72544635030249, -1.60704089502946],
    [0.41234979398721, 1.43923340291139, -1.13159136658588, 2.36379244817020],
    [0.41234979398721, 1.43923340291139, -1.13159136658588, -1.59654245961628],
    [1.87122629927995, 0.69845142045132, 0.39645160933551, -0.25314067487602],
    [1.87122629927995, 0.69845142045132, 0.39645160933551, -2.57599107426913],
    [1.81820455126460, 1.22188102498306, 1.22591826190587, -0.34363790264382],
    [1.81820455126460, 1.22188102498306, 1.22591826190587, -2.66648830203693],
]
tri_stripI_lst = [
    [0.07009342372063, 0.95450718359009, -2.73622538548352, -1.10960569026956],
    [-0.17681299032624, 2.66126426654688, 1.50888036201269, 2.25729469520859],
    [0.38142922617270, 2.55508564344609, -2.08327206404086, 0.30031794066008],
    [0.60191198739157, 2.21758071847090, -1.63439273062589, -0.67733655030150],
    [0.94002887754665, 0.73852054890627, 1.45181702859477, -2.56049587697277],
    [1.77686227697888, 1.22256570805350, -1.13544035144974, -2.83940186687869],
    [1.14297829546932, 0.87403802846353, 1.04872504288942, -0.38433509156134],
    [1.99199563701651, 1.87769301440517, -1.65470849732757, 1.09003914198715],
]
tri_stripII_lst = [
    [-1.04969590217257, 3.13273958178860, 0.20040092694551, -0.60012043779415],
    [-0.99120670549809, 2.28903565404993, 1.30988539086274, 0.16975334938707],
    [1.39061333499570, -0.56111480763697, 2.58277694660487, -2.87482461520475],
    [1.26286135114330, -0.15604692204819, 2.46575769214703, 0.45019501593938],
    [1.90940617256917, 1.06157942504906, -0.85414382716863, -2.79969553519649],
    [0.79539721944604, 2.99573998345359, -1.66913892017232, 0.69681825483581],
    [1.99273953120271, 1.87707316974018, -1.65352756561613, 1.08896079378173],
    [2.07059332895531, 1.72464608019017, -0.66808867364858, -1.27707298213234],
]
tri_star_lst = [
    [-0.22994485703131, -1.94263116499039, -2.74754532569331, 0.16494452144481],
    [-0.37854697287216, -1.80186129220768, -2.60521432166224, -2.02229646945205],
    [0.29505656340515, 1.90239304145087, 2.57475187997169, 1.21356143655302],
    [-0.54370074619116, 1.40863165798822, 1.97316692778694, 2.84142133021495],
    [-0.59249810577261, 1.43974357358653, 1.97554255368610, -1.32514395487703],
    [-0.26555502444917, 0.37497822962142, -2.49360458669724, -1.72115685304998],
    [1.30422532625372, -0.69784593397428, 1.57749825709822, -1.66692499568266],
    [1.25837218608941, -0.97709432324629, 1.85925315330965, 0.14398658014487],
    [-1.41522912655792, 2.35173236164614, 1.83813814069704, -1.24959858722909],
    [-1.77982675659482, 3.06966221364546, 1.10714636032425, -2.21020822124952],
    [1.75755263012289, 1.11093299637497, -0.98055994369563, 2.65016525377239],
    [1.80477491230109, 2.55496797657288, -2.05095717883639, -0.19151038413551],
]
tri_alt_stripI_lst = [
    [0.36949489467704, 1.49489842400877, -3.13327316518452, 3.03196107437637],
    [0.36949489467704, 1.49489842400877, -3.13327316518452, 0.25644531007482],
    [-0.18757221261150, 2.67858168942522, 1.48530656988465, 2.27604048923164],
    [-0.18757221261150, 2.67858168942522, 1.48530656988465, -0.49947527506991],
    [0.32938805202444, 2.64908330831472, -2.18488472637117, -2.31849650059186],
    [0.32938805202444, 2.64908330831472, -2.18488472637117, 0.45701926370969],
    [0.92450576736605, 0.73376456702886, 1.47376223548871, -2.60579911826065],
    [0.92450576736605, 0.73376456702886, 1.47376223548871, 0.16971664604090],
    [1.69335980067665, 0.48302739290243, 0.00539383012874, -2.30507154934714],
    [1.69335980067665, 0.48302739290243, 0.00539383012874, 0.47044421495441],
    [1.79025873371215, 1.27720017219956, -1.20483193581687, -0.20533216115796],
    [1.79025873371215, 1.27720017219956, -1.20483193581687, -2.98084792545951],
]
tri_alt_stripII_lst = [
    [1.69376104454665, 0.48329244209036, 0.00495968108888, -2.30482366536828],
    [1.87129113501647, 0.69861219844607, -0.31770630853309, -0.18916259165661],
    [1.88599374270150, 1.03643460896693, -0.82731393086978, -2.70267962453108],
    [1.82327166809964, 1.21109599107917, -1.10047670883113, -0.26299481928222],
]
star_stripI_lst = [
    [-1.17426246963530, -3.00174186009160, 2.40622768073954, -2.37906097887172],
    [1.26101090294777, 0.63772600421161, -1.44337978282285, -0.25125837261504],
    [1.21210149669272, 0.68463536172720, -1.61023641084172, 1.91770984121295],
    [1.25935407914121, 0.63913903280080, -2.25372272878080, 2.30933934097687],
    [-0.71128947098165, -2.96493913406681, -1.71102338184589, 0.32371119239428],
    [-0.74527206248033, -2.98217427597708, -1.78011856391322, -1.77783250544059],
    [-0.64371889643607, -2.91195896872444, 1.47164209467378, 2.82945062426254],
    [1.14590584368348, 0.77160857896282, 1.34969646388824, 2.77491518662589],
    [-1.46623473721468, -2.08145061458492, -1.97963160776412, -1.98415637855508],
    [-1.85014509025280, -2.23993688724007, -1.20828695129958, -0.83887865550258],
    [1.72295603299556, 0.48586784012411, 0.87923700911844, 2.46219669741063],
    [2.20003339363833, 1.24163192969557, -1.54625460731136, 1.52873062167969],
    [2.29782216382328, 1.17935657160260, -1.73698040415638, 1.26895234359323],
]
star_stripII_lst = [
    [-1.05655239249295, -3.01807153292690, -0.12446702672159, -0.45638345457520],
    [1.29571007142095, 0.61051011632406, -1.51146150495975, 0.06109208641055],
    [1.35292780142390, 0.57405133085257, -1.64765760902182, 0.85714604837340],
    [-1.47195365032700, -2.91809970672301, -1.09267425868734, 2.64635776782176],
    [1.57859895589596, 0.49771047336805, -2.78621622654283, 0.43204167489074],
    [-1.55066639079712, -2.88637038896891, 2.70125955617623, -2.71206071668662],
    [1.94327585112635, 0.50614934913910, -1.81253026286899, -2.84100070178457],
    [-1.47174234510787, -2.08259786414710, -1.98161041291028, -1.98189580828914],
    [-1.85616036748546, -2.24442980411555, -1.20838596694429, -0.82233240725783],
    [-1.81180939309180, -2.73990660488262, 2.04407417299020, 0.33525729437233],
    [-1.56528118793774, -2.10612120286151, 2.55952774806987, 2.07376961570522],
    [-1.30477701300752, -2.05923131562921, 2.10235047863756, 1.40774861837552],
    [1.99606438552793, 0.51717849046017, 0.51914908527848, 2.90165339519484],
    [2.21682848567536, 1.23190490976518, -1.49447650415065, 1.54888575147529],
    [2.32586919632899, 1.15836937279002, -1.75755460382101, 1.20172103723255],
    [2.34692453590526, 0.66678365096084, 1.02574015960600, -0.51596068914456],
]
star_star_lst = [
    [-0.99447536676081, -3.02184046226739, 2.03085744944406, -2.46303587893013],
    [-1.23693393646225, -2.98887279240194, 2.71924047447027, -2.14777099144439],
    [1.50488894518337, 0.51340921108244, 1.25087891690484, 2.39583361198984],
    [1.75401628639206, 0.48611572783784, 0.54752887219853, 2.25626423253853],
    [2.29768532970748, 0.63431719141414, 1.74517428648776, -2.16131009783418],
    [2.40280722807984, 0.71344369232975, 1.34152697117699, -2.11169162079520],
]
star_alt_stripI_lst = [
    [-0.98949118631220, -3.02197423313010, 2.02288631366521, 2.88576599696532],
    [-0.98949118631220, -3.02197423313010, 2.02288631366521, -0.62190354591272],
    [-1.21897958281153, -2.99283231173422, -3.00091691794488, 2.41225757751892],
    [-1.21897958281154, -2.99283231173422, -3.00091691794488, -0.36325818678263],
    [1.29485865484115, 0.61112713384955, -1.33858704657649, -0.55942517263435],
    [1.29485865484115, 0.61112713384955, -1.33858704657649, 2.21609059166721],
    [-0.79745516109958, -3.00092080670608, -1.87660317102718, -1.84497939040072],
    [-0.79745516109958, -3.00092080670608, -1.87660317102718, 0.93053637390083],
    [-0.55426421201684, -2.67595676360904, -0.73808558117110, 3.06161296603518],
    [-0.55426421201684, -2.67595676360904, -0.73808558117110, 0.28609720173363],
    [1.05675141336016, 1.03204592154130, -2.64052246424245, -2.90934909524183],
    [1.05675141336016, 1.03204592154130, -2.64052246424245, -0.13383333094028],
    [-0.69188581686299, -2.27852757573699, 2.22778589617154, 3.04913320462447],
    [-0.69188581686299, -2.27852757573699, 2.22778589617154, -0.45853633825356],
    [1.69335904521151, 0.48649743957114, -0.00348099672441, -2.30072697451907],
    [1.69335904521151, 0.48649743957114, -0.00348099672441, 0.47478878978248],
    [-1.56514719159599, -2.10608187300471, -1.80748935445304, 1.77681360638032],
    [-1.56514719159599, -2.10608187300471, -1.80748935445304, -1.73085593649772],
    [2.08172321905053, 1.30180775930204, -1.35112038996804, -1.75288156836566],
    [2.08172321905053, 1.30180775930204, -1.35112038996804, 1.75478797451238],
]
star_alt_stripII_lst = [
    [-1.22639780001659, -2.99122237234670, -3.01104734379076, 2.42128633801206],
    [-0.83140687708880, -3.00929787913242, -1.48080963475963, -0.42019572294382],
    [-0.81232941467079, -3.00491292521662, -1.70964825909705, 0.49477116897897],
    [1.31221375120567, 0.59901025940655, -1.40499321814795, -0.32966305102175],
    [1.35301283344956, 0.57400385058401, -1.64772469660752, 0.85765621413376],
    [-1.35873024547323, -2.95653666542475, 3.05692499762915, 0.36509301431446],
    [-1.35136542374402, -2.95875696819001, 2.32923285959397, 2.17093970920295],
    [-1.44248423039261, -2.92889350771991, 2.77362606166166, -3.11149747039544],
    [-1.57067933082498, -2.10771963403438, -1.82411217830301, -1.73756185694115],
    [-1.59994686003747, -2.11687066254473, -1.95460844561724, 2.31003285725197],
    [1.69376030982933, 0.48648309348294, -0.00319997394815, -2.30083016347630],
    [1.87384928096113, 0.49523160787154, 0.16595451178895, -0.39710040784649],
    [1.88232143321822, 0.49634619532369, 0.93533990230075, -2.06871463988899],
    [1.98994728026073, 0.51577826433917, 0.51802640287897, 2.92519436496811],
    [2.11183718719796, 1.28771909940429, -1.20392017245369, -2.17212106027898],
    [2.09239863759159, 1.29689950737116, -1.30951217447605, 1.77998468238998],
]
w_stripI_lst = [
    [-1.19194580738429, -2.99838399748236, 3.05495967954063, 0.47611612974963],
    [-1.22071193145937, -2.99245964647262, -3.00187064473109, -0.46918928519905],
    [1.26212471848357, 0.63678228675852, -1.59354968833213, 0.28306679175272],
    [-0.81666023564508, -3.00597827136257, -1.71696159025271, -2.36457079417992],
    [-0.71256480888860, -2.96567469549899, -1.51129249073855, -0.37106860213447],
    [-0.66525562485414, -2.93240284887343, -1.23855223603033, 3.09987553891302],
    [-0.71630476421629, -2.96778844567182, -0.77557484515899, -2.15512194598460],
    [1.69119858662003, 0.48657746918294, 0.24494116404541, -0.35763385092992],
    [1.70951772333963, 0.48604683871288, 0.01151042872651, 0.53640995381890],
    [-1.71609467635320, -2.16220926030136, -1.86461182486963, 2.72406439405151],
    [-1.86845359168759, -2.25400733284672, -1.63673847140261, 1.03463576680048],
    [-1.14175478227289, -2.06052772952422, 2.94779635945424, -2.47014912169251],
    [-1.22019948589836, -2.05668657719278, 2.82338282556642, 1.72970366807952],
    [1.90315868546370, 1.37162775755018, -0.18054004073032, 2.29623839288972],
    [2.04159548049669, 1.31945604450113, -0.14593410613434, -1.76796043994019],
    [2.39321322307369, 1.09864033309864, -1.29303359816581, -1.25658110581333],
    [2.27440800132831, 1.19564333315538, -1.09177505132868, 2.78505413873679],
]
w_stripII_lst = [
    [-1.01649856653401, -3.02093744394430, -0.40048207444954, 0.61660833309469],
    [-1.01649856653401, -3.02093744394430, -0.40048207444954, -2.89106120978335],
    [-1.24347874657017, -2.98737637924422, -2.85212273686144, 1.89409906529687],
    [-1.24347874657017, -2.98737637924422, -2.85212273686144, -0.88141669900468],
    [-0.81903116985467, -3.00654371450684, -1.72035555099161, -2.36117229687877],
    [-0.81903116985467, -3.00654371450684, -1.72035555099162, 0.41434346742278],
    [1.29550599359376, 0.61065779211225, -1.47895533086525, -0.05706939525388],
    [1.29550599359376, 0.61065779211225, -1.47895533086525, 2.71844636904767],
    [1.56213997518316, 0.50058285187582, -2.53730591865476, -0.54369014709570],
    [1.56213997518316, 0.50058285187582, -2.53730591865476, 2.96397939578233],
    [1.72133738394127, 0.48588010939703, -0.18105890512730, -1.76058995238663],
    [1.72133738394127, 0.48588010939703, -0.18105890512730, 1.01492581191492],
    [-1.81545599503872, -2.73716527099049, 2.23510131570847, 3.12324705517113],
    [-1.81545599503872, -2.73716527099049, 2.23510131570847, -0.38442248770691],
    [-1.88511199201272, -2.26795052522890, -1.60946020522811, -2.56528667256179],
    [-1.88511199201272, -2.26795052522890, -1.60946020522811, 0.94238287031625],
    [-1.22355716541979, -2.05666025422643, 2.82083151111534, 1.72939115702668],
    [-1.22355716541979, -2.05666025422643, 2.82083151111534, -1.77827838585136],
    [2.39328341126817, 1.09856852580841, -1.29316097291461, -1.25616269262729],
    [2.39328341126817, 1.09856852580841, -1.29316097291461, 2.25150685025074],
    [2.35848825537058, 0.67540517177013, 0.72138943557191, -2.88844660411643],
    [2.35848825537058, 0.67540517177013, 0.72138943557191, 0.61922293876160],
    [2.08068763253621, 1.30227898421812, -0.13497657144930, -1.75462906286937],
    [2.08068763253621, 1.30227898421812, -0.13497657144930, 1.75304048000867],
]
w_alt_stripI_lst = [
    [-0.95651894061622, -3.02216050898146, 1.74324990061448, 0.46677733897024],
    [-0.61353475925501, -2.87441016634211, -1.19916373595688, 2.69267314588319],
    [-0.65229683739682, -2.92060800493758, 2.61972524117004, -2.65134826854996],
    [-0.55433370690736, -2.67779260280280, -0.59288386936684, -0.25622178425538],
    [1.05675781993120, 1.03198269410807, -2.71094167940859, 0.12551696055785],
    [1.06277613891068, 0.98883610043526, -2.01359849018057, -2.35178243239693],
    [-0.69830834391674, -2.27091415801225, 2.00865892180556, 0.40230067061754],
    [-1.26309425234358, -2.05715502937589, -1.42890408845264, -2.34072462207635],
    [-1.52556826843303, -2.09518638330210, -1.06380887231531, -1.49534762934120],
    [-1.42803966385223, -2.07420197222208, 3.14033456940805, 2.01585201648652],
    [1.05548366487825, 1.04638244088429, 0.67924158872589, 2.40608319724203],
    [2.01187844469123, 1.33175348840922, -0.11423187445879, -1.74631872424423],
]
w_alt_stripII_lst = [
    [-0.83100471629046, -3.00921345328476, -0.82851860186396, 2.40590400699044],
    [-1.32446836467296, -2.96657846471671, -2.97568563711294, 1.80401269267104],
    [-1.36089845362724, -2.95587656576246, -3.03038253525679, -0.31894840292888],
    [1.43348196465882, 0.53643417769128, -2.22605673929647, -2.29585365808217],
    [-1.48861602448349, -2.91174206895989, 0.04728485370136, -2.82993785853381],
    [1.76573175563991, 0.48644351609714, -0.14206691464528, -1.69008454277158],
    [-0.86350318002538, -2.13908038311588, 1.97187695281386, 0.79925934424506],
    [-1.43243678474314, -2.07497371102658, 3.13868703886291, 2.01088021461235],
    [1.88620814207893, 0.49687783557661, -3.06843794641176, 2.59009386821355],
    [1.87552289168722, 0.49544697088417, -0.04954725520308, 0.34426177056684],
    [1.29077410718792, 1.42815469376580, 1.18808404903072, -1.01045664554590],
    [2.02669070996501, 1.32570326370469, -0.08206145267189, -1.72025008314053],
]
trap_stripI_lst = [
     [1.70951360350302, 0.49128926661824, -0.02656612722943, 0.54752965089422],
     [1.69698167321375, 0.57440334933185, -0.48599396351018, 0.13841797827900],
     [1.60165960065524, 1.32463777974490, 2.60868134182099, -2.39265439249637],
     [1.84249454198840, 1.32936074453837, 0.31697004325470, 2.17140847488591],
     [2.01188186204679, 1.27548661607235, 0.28174260557935, -1.88938839999953],
     [2.02201739365501, 1.27191490432736, -2.16409521939596, 1.72231972831059],
]
trap_stripII_lst = [
    [1.72561015462434, 0.41306074734241, 2.67856843428636, -1.94818689960185],
    [1.72561015462434, 0.41306074734241, 0.35571803489325, -1.94818689960185],
    [1.72561015462434, 0.41306074734241, 2.67856843428636, 0.82732886469970],
    [1.72561015462434, 0.41306074734241, 0.35571803489325, 0.82732886469970],
    [2.05847743995965, 1.25881081838306, -2.05776486797820, -1.87089616309840],
    [2.05847743995965, 1.25881081838306, 0.26508553141491, -1.87089616309840],
    [2.05847743995965, 1.25881081838306, -2.05776486797820, 1.63677337977964],
    [2.05847743995965, 1.25881081838306, 0.26508553141491, 1.63677337977964],
]
trap_alt_stripI_lst = [
    [0.79220914890259, 1.70329104958495, 2.34020571192586, 2.82407175256774],
    [0.98494060159216, 1.53818477738430, -0.98646078169974, 3.03855503390602],
    [1.64373082787414, 1.31227348946000, 2.75159980129745, -2.53567705876600],
    [2.00783738163094, 1.27943230124780, 0.27035624979770, -1.87995431216524],
]
trap_alt_stripII_lst = [
    [-1.48804690508797, -2.89064087362722, 2.21549438228525, -2.78038051719082],
    [-1.48804690508796, -2.89064087362722, -0.10735601710786, -2.78038051719082],
    [1.77041919431622, 0.42891926562104, 0.28532157935568, -1.82993041861905],
    [1.77041919431622, 0.42891926562104, 2.60817197874879, -1.82993041861905],
    [-0.19068710778791, 3.11951284441675, -2.17018613450777, -0.55434234349592],
    [-0.19068710778791, 3.11951284441675, 1.79014877327871, -0.55434234349592],
    [0.78686928192068, 1.70904199408223, 2.34857481003525, 2.81785363062543],
    [0.78686928192068, 1.70904199408223, -1.61176009775122, 2.81785363062543],
    [1.87547641887417, 0.47388167725752, 0.10853732749875, 0.29561925894143],
    [1.87547641887417, 0.47388167725752, 2.43138772689186, 0.29561925894143],
    [2.02560962778858, 1.28848404790205, -2.13426122368406, -1.80973418085232],
    [2.02560962778858, 1.28848404790205, 0.18858917570905, -1.80973418085232],
]
E1_V2_1_1 = {
    # 1 loose triangle: nothing special
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_I: par_stripI_lst,
	trisAlt.strip_II: par_stripII_lst,
	trisAlt.star: par_star_lst,
	trisAlt.alt_strip_I: par_alt_stripI_lst,
	trisAlt.alt_strip_II: par_alt_stripII_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_I: tri_stripI_lst,
	trisAlt.strip_II: tri_stripII_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.alt_strip_I: tri_alt_stripI_lst,
	trisAlt.alt_strip_II: tri_alt_stripII_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_I: star_stripI_lst,
	trisAlt.strip_II: star_stripII_lst,
	trisAlt.star: star_star_lst,
	trisAlt.alt_strip_I: star_alt_stripI_lst,
	trisAlt.alt_strip_II: star_alt_stripII_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_I: w_stripI_lst,
	trisAlt.strip_II: w_stripII_lst,
	trisAlt.alt_strip_I: w_alt_stripI_lst,
	trisAlt.alt_strip_II: w_alt_stripII_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_I: trap_stripI_lst,
	trisAlt.strip_II: trap_stripII_lst,
	trisAlt.alt_strip_I: trap_alt_stripI_lst,
	trisAlt.alt_strip_II: trap_alt_stripII_lst,
    },
}

###############################################################################
par_strip1loose_lst = [
    [-0.11815285518002, 1.13002655661625, -2.66669430601098, 0.74240619546395],
    [-0.11815285518002, 1.13002655661625, -2.66669430601098, -0.65920235952357],
    [-0.78526743897551, 2.01156609697354, -1.78515476565369, 0.74240619546395],
    [-0.78526743897551, 2.01156609697354, -1.78515476565369, -0.65920235952357],
    [0.80721664767262, 2.01156609697354, 1.84137460994260, 2.88825477856116],
    [0.80721664767262, 2.01156609697354, 1.84137460994260, -1.99332197363090],
    [1.47433123146811, 1.13002655661625, 0.95983506958532, -1.99332197363090],
    [1.47433123146811, 1.13002655661625, 0.95983506958532, 2.88825477856116],
    [0.33554736079111, 2.01156609697354, 0.13507754436248, 2.91131633108745],
    [1.00266194458660, 1.13002655661625, -0.74646199599481, 2.91131633108745],
    [0.33554736079111, 2.01156609697354, 0.13507754436247, -1.97026042110461],
    [1.00266194458660, 1.13002655661625, -0.74646199599481, -1.97026042110461],
    [1.94876711476854, 2.01156609697354, 1.09528136986971, -0.74117297563557],
    [1.94876711476854, 2.01156609697354, 1.09528136986971, 0.66043557935195],
    [2.61588169856402, 1.13002655661625, 0.21374182951243, -0.74117297563557],
    [2.61588169856402, 1.13002655661625, 0.21374182951243, 0.66043557935195],
]
par_strip_I_lst = [
    [-1.04451311568900, 3.04364292753345, -0.05603879847734, 2.50155151107280],
    [-1.07530286575364, 2.43828056879521, -1.14203948811396, 0.97016115840787],
    [0.15669544883326, 2.71081919613269, 1.68883496710893, -0.86286400082160],
    [0.22326009168688, 2.16542659536368, 0.36783905212190, -1.79429012396948],
    [0.47657584624315, 3.02386800422808, 1.03821504275114, -2.08638673441504],
    [1.57483800501552, 2.37941460439007, 1.26847204835960, -0.90733543344519],
    [2.67682432992665, 0.97285669714882, -0.01072418574158, 0.91740129291136],
    [2.61629643314839, 1.12915136728153, 0.21255208976186, -0.74165673601417],
]
par_star_lst = [
    [-0.64547844860551, -2.68759620022506, 1.98218651888145, -1.20563843998911],
    [-0.99162708838557, -3.00127356376199, 1.32813264775735, -2.25311367026238],
    [1.30781942194085, -1.06402396404953, -2.76447762987621, -1.41145164790598],
    [1.73850059908666, -0.74012009144748, -2.40965569503007, 1.85361768806939],
    [0.06904781708999, 2.04176497947117, -1.21837471811209, 1.20516592404253],
    [0.15538216696099, 2.07686658282204, -1.01554889382627, 1.56334872496637],
]
par_star1loose_lst = [
    [0.12725211462250, 1.13002655661625, -2.70137208715046, -1.15714329698270],
    [-0.31657120620754, -2.01156609697354, 2.08740183899411, -2.68045141061173],
    [0.35054337758795, -1.13002655661625, 2.96894137935139, -2.68045141061172],
    [0.33163190296616, 1.13002655661625, -2.62311673746457, -2.01156831808323],
    [-0.33548268082933, 2.01156609697354, -1.74157719710729, -2.01156831808323],
    [-0.53986246917299, 2.01156609697354, -1.81983254679318, -1.15714329698270],
    [0.50134721199837, -2.01156609697354, 2.52383690548308, -1.51231975706078],
    [1.16846179579386, -1.13002655661625, -2.87780886133922, -1.51231975706078],
    [0.72241554951102, 2.01156609697354, 2.14603738082316, -2.77588236330831],
    [0.77619880626182, 2.01156609697354, 1.94936483775443, 3.00103105805698],
    [1.38953013330651, 1.13002655661625, 1.26449784046588, -2.77588236330831],
    [1.44331339005731, 1.13002655661625, 1.06782529739715, 3.00103105805697],
    [0.74453706928701, 1.13002655661625, -2.16058122666076, 1.17489485674169],
    [0.07742248549153, 2.01156609697354, -1.27904168630348, 1.17489485674170],
    [0.89539750032702, 1.13002655661625, -1.94511296869567, 1.72787420328403],
    [0.22828291653153, 2.01156609697354, -1.06357342833839, 1.72787420328403],
]
par_alt_strip_I_lst = [
    [0.86791020235196, 0.80890200948550, 2.57263421212117, 1.18131457556504],
    [1.11676339698248, 0.52787789520773, 2.69934299453282, -2.43960447646843],
    [0.15582711801443, 2.71428284082191, 1.69141580660222, -0.85343884088648],
    [-0.09492637362683, 2.72695731821682, -0.84731652879632, 0.84429419978015],
    [-0.09391612308771, 2.11178838762304, -0.35376293066942, -1.38425175697776],
    [1.90178998344986, 0.81755096750278, -1.54481200520716, 1.18923795049633],
    [1.85735968724164, 1.12933910647492, -1.07937556150430, 2.87632296680891],
    [1.18592409744499, 2.01545388195324, -0.19435202209537, 1.47051525968087],
]
par_alt_strip_1_loose_lst = [
    [-0.02650967655387, 2.01156609697354, -2.67894785439090, 2.87552802277768],
    [0.64060490724162, 1.13002655661625, 2.72269791243140, 2.87552802277767],
    [0.64060490724162, 1.13002655661625, 2.72269791243140, 1.47391946779016],
    [-0.02650967655387, 2.01156609697354, -2.67894785439090, 1.47391946779016],
    [0.64060490724162, 1.13002655661625, -1.37388103307103, -2.87552802277768],
    [-0.02650967655387, 2.01156609697354, -0.49234149271374, -2.87552802277768],
    [-0.02650967655387, 2.01156609697354, -0.49234149271374, -1.47391946779016],
    [0.64060490724162, 1.13002655661625, -1.37388103307103, -1.47391946779016],
    [1.18999167580366, 2.01156609697354, 1.98969106795329, -2.87552802277768],
    [1.18999167580366, 2.01156609697354, 1.98969106795329, -1.47391946779016],
    [1.85710625959915, 1.13002655661625, 1.10815152759601, -1.47391946779016],
    [1.85710625959915, 1.13002655661625, 1.10815152759601, -2.87552802277768],
    [1.18999167580367, 2.01156609697354, -0.19691529372387, 2.87552802277768],
    [1.85710625959915, 1.13002655661625, -1.07845483408116, 2.87552802277768],
    [1.85710625959915, 1.13002655661625, -1.07845483408116, 1.47391946779016],
    [1.18999167580366, 2.01156609697354, -0.19691529372387, 1.47391946779016],
]
tri_strip1loose_lst = [
    [-0.18246163223487, 2.01156609697354, 2.16912250460773, 1.32647716449683],
    [0.48465295156062, 1.13002655661625, 3.05066204496501, 1.32647716449683],
    [-0.11277389841516, 1.13002655661625, 2.92226073556936, -0.46070496148640],
    [-0.77988848221064, 2.01156609697354, 2.04072119521208, -0.46070496148640],
    [1.31631886272234, 2.01156609697354, -1.46306278660071, -2.51207453592137],
    [1.98343344651783, 1.13002655661625, -0.58152324624343, -2.51207453592137],
    [1.94376369425347, 2.01156609697354, -1.35107289124871, 0.47220939769698],
    [2.61087827804896, 1.13002655661625, -0.46953335089142, 0.47220939769698],
]
tri_strip_I_lst = [
    [0.30759911712361, 0.06317294080097, -2.25296365983626, -1.63183790577472],
    [0.73235749244515, 0.83336391309282, -2.98801362764774, 1.56764203515800],
    [2.20954794265912, -0.13159088325780, 0.82953401549854, 1.89668732954955],
    [2.70110902967984, 0.85850247625795, -0.25648816146644, 0.74594566995982],
]
tri_strip_II_lst = [
    [0.53741593521677, 1.18196848123341, -2.22613701640801, -1.29057042575769],
    [0.08173329019691, 2.39744110286208, -2.21812048451541, 2.22940600283835],
    [-0.43800796092923, -2.68603251497316, -1.57820105026183, 1.33750409873189],
    [-1.19871822190374, 3.13239589864804, -0.07747645105999, 1.92305331913698],
    [0.70465857274135, -0.33354591520858, -2.69601027109651, -1.18111631736659],
    [0.67229155700242, 1.67300005516055, 2.72036652359600, 1.32291295887236],
    [1.10592475440065, 1.59253152988134, -2.43940509609413, -2.58193316916352],
    [0.30391414133664, 2.46760543743175, -1.46407328565990, -1.21298445631113],
    [-0.14091011301859, -2.68977101461990, -0.80268337608665, -1.37292079578088],
    [0.21027850002000, 1.69847555364078, 1.32252299089948, -2.41642100314925],
    [0.71542477124400, 1.19339524742589, 0.48531163276994, 1.50100689783179],
    [1.46935264079000, 1.62557763477820, -2.15433606439395, 2.81871677678118],
    [1.51380648599789, 1.71059982998743, -2.20605243201113, 2.56404987645691],
    [0.98575928767654, 2.93744393151129, -1.33968467042169, -1.67156931178577],
]
tri_star_lst = [
    [0.74485079889124, 0.86578384100135, -3.04429632082135, 1.54900701948342],
    [0.21525719895392, -0.15856310672376, -2.12191797450175, 2.84817707174843],
    [2.37921604993900, 0.32516768556519, 0.20893553792797, 1.79837973223949],
    [2.75612367391025, 0.95410975256404, -0.25901545729357, -1.26894314699568],
]
tri_star1loose_lst = [
    [0.07144019925822, 1.13002655661625, 3.04519187132860, -0.58023474795772],
    [-0.59567438453727, 2.01156609697354, 2.16365233097132, -0.58023474795772],
    [-0.03510875251350, 2.01156609697354, 2.04300563225555, 1.36074029352877],
    [0.63200583128199, 1.13002655661625, 2.92454517261284, 1.36074029352877],
    [1.19743459684216, 2.01156609697354, -1.35223151108867, -2.67779256814892],
    [1.86454918063765, 1.13002655661625, -0.47069197073138, -2.67779256814893],
    [1.94084144377861, 2.01156609697354, -1.35396243629609, -1.37426480863832],
    [2.60795602757410, 1.13002655661625, -0.47242289593881, -1.37426480863832],
]
tri_alt_strip_II_lst = [
    [-0.09093195151466, 2.72799750807960, -2.56694191851855, 2.15317121526847],
    [0.74011386385825, 0.98876524698904, -3.03780913503601, 1.84319129256747],
    [0.58370739142782, 1.20931017762066, -2.19065911063032, -1.34620279451148],
    [1.29434814363992, 0.42640851835521, -0.16396164562616, -3.02042919104344],
    [-0.12066815136301, 2.71865961508367, 0.77759200015803, 1.21427111436364],
    [0.15130260690941, 2.71550851459802, 1.68451031515549, -2.12005687454060],
    [0.19778372284876, 2.70165513391036, -1.59226588082915, -1.22622268373455],
    [1.57133114587296, 0.42486157320304, -0.23002103577005, 1.30513909311331],
    [0.21025400060444, 1.69849539380512, 1.32250987793500, -2.41645862131173],
    [0.64917377550916, 1.11797067162871, 0.76919048913826, 1.38110716431275],
    [1.40288479694978, 1.79533522562853, -2.37340127941342, 1.26687463239464],
    [1.50278573380939, 1.68314246730114, -2.18774499177199, 2.64217658001015],
]
str_strip1loose_lst = [
    [1.01042536571518, 0.55861903444440, 2.39070613577333, 2.00496675294080],
    [-0.66472956054813, -2.92003548327747, 0.79950964328705, 3.01693265950239],
    [-1.25645290310688, -2.49419467047346, 2.40633492721602, 2.90107621638455],
    [-1.39679021189305, -3.13370416842280, 1.11416835965753, 1.19685469852843],
    [1.72101042585691, 0.36401114590120, 2.32384723397235, -1.57297731556760],
    [-1.93449101063496, -2.61724655067328, 2.38221025366248, -0.03157879269910],
    [2.04797486446753, 0.71923153990028, 0.34473501736386, -2.93241398134812],
    [2.65467876454057, 0.79393758623000, 0.28595855458544, 0.14690456541860],
]
str_strip_I_lst = [
    [0.99021382541801, 0.52007673226084, 2.43820993767918, 1.89339594123060],
    [-1.39694726427610, -3.13540381490661, 1.11166173953575, 1.19558214152390],
    [-0.33495751607299, 3.10890264585744, 0.55867226714096, -1.99283233545787],
    [1.71163337691698, 0.28392116751828, 2.46393013935864, -1.54495442984672],
    [-2.00528777743368, -2.83885270919820, -2.92101185995188, -1.96371471538085],
    [2.06935266985543, 0.34615127453275, -0.88808672707595, -2.76198389216698],
    [-2.08096417691522, -2.78250411834996, 3.11362904237642, -1.45428250917297],
    [-1.80560407233149, -1.99626160052768, -2.59380437060461, -0.99877440401769],
    [-2.23071267716659, -2.28892315446987, -1.85937929815305, 0.32674652122703],
    [2.70986871654535, 0.69038378107579, 0.16770086455133, 0.53289753829417],
    [2.74064142182590, 1.03761595183957, -1.17257751350094, 0.24686334168195],
    [2.70142257854832, 1.09376473585089, -1.02090186774551, 0.63623427933711],
]
str_strip_II_lst = [
    [1.04164444002292, 0.46822628865727, 2.63775118140720, 1.53984412080318],
    [1.06143878952273, 0.45097858399561, 1.06185786370188, -2.34094871036556],
    [-1.06422972843793, 3.04624712424134, -3.12865159830613, -0.89278948336761],
    [1.00220355015131, 0.50699104272953, -1.82472739849065, 2.42218884641648],
    [-1.20028438716441, 3.08332861686650, 0.05096355785748, 1.86180932982217],
    [0.91449613288119, 0.62044771774404, -1.37063361906274, -1.76741260305224],
    [-1.32009816463912, 3.12112568728201, 2.25241577606166, -1.79758369427981],
    [-1.56601739765015, -3.06994515134255, 1.41583319403666, 0.82220311318921],
    [1.56583302602607, 0.28056425192610, 0.27784733640669, 0.85390672247623],
    [1.62250251467528, 0.28008283571136, -2.81213935533418, -2.01783142882876],
    [-0.58855372029355, 2.99156039954927, 2.56391238617895, 2.01859698716964],
    [-0.49085013677683, 3.01005608709708, -1.23656649829837, -2.05517697499899],
    [-0.30071326130231, -3.12423958754932, -1.87654807593851, 1.97119709175480],
    [-0.33339616589048, 3.11078418095046, 0.57196612018321, -2.03310462351890],
    [1.73691319306451, 0.28595028887700, 1.02093347220383, 1.99744448086804],
    [0.83752655581588, 1.60651578221018, -0.60704180215249, 2.03471780749581],
    [0.90048954606378, 1.66147992664413, -0.77065261573062, 2.12314525006943],
    [2.05550582361794, 0.34247069543978, 1.74329137688701, -0.86425655088585],
]
str_star_lst = [
    [1.19765391795760, 0.36283602087344, 2.32614225172898, 1.58855101782770],
    [-1.40327147626440, -3.13312621655551, 1.10544631897484, 1.20091848278872],
    [-0.61860894193189, 2.98924859339095, 1.05309310280439, -1.61482596397387],
    [1.81262109403946, 0.29432611009985, 2.60025695874953, -1.70070793609204],
    [-2.12266573089840, -2.74696379683913, 3.00730261778724, -1.19132807044199],
    [-2.24787315858248, -2.59571236768710, -1.30260373971296, -0.00980977251184],
    [-2.24129910208743, -2.30511792747659, -1.82645330250154, -1.49226585956122],
    [2.38079717026878, 0.45823778700850, -0.13094348454285, 1.96778189232273],
    [-2.25303318471427, -2.32556512752091, 2.59326714272506, 1.18207819183843],
    [2.74061570549575, 0.73322042759877, -1.79537302341214, 0.88805407685284],
    [2.76079406837249, 0.77040298361728, -1.72950185453958, 1.22367047747192],
    [2.76609878493328, 0.78252690450636, 0.16698203433462, -1.47633438792018],
]
str_star1loose_lst = [
    [-0.79061462873142, -3.13256658449122, 1.11192485470634, -1.94595066221997],
    [1.19935753817797, 0.36424316398663, 2.32395526321762, 1.59320140404157],
    [-1.40859819501006, -3.12843542127564, 1.10386476743141, 1.20783566856149],
    [-1.40017444670006, -2.61884920738498, 2.38177964255309, 3.08902804523351],
    [1.95900230559243, 0.64955462474281, 2.40659776145480, -2.50749010134430],
    [1.92227852814482, 0.79345979961941, 0.28633416047390, -3.00495303046681],
    [-2.11732442489683, -2.32492045718005, 2.40831038257793, 1.53051669869290],
    [2.66401522975834, 0.80213407792014, 0.27951340771474, -1.70460445337710],
]
str_alt_strip_II_lst = [
    [-1.07441428545231, 3.04879210001006, -3.00169075744439, -1.15700300061001],
    [1.08998687747774, 0.42837799955264, -1.71417642042827, 2.55674471537381],
    [-0.79682763503151, 2.99610333923100, 1.86026170571650, -3.06486093203476],
    [-0.73053280987348, 2.99016616790441, -2.73956041430169, 3.00516389275073],
    [1.30563244477577, 0.32062160049633, 1.71292743833989, 2.94843168392096],
    [-1.39136224240626, -3.13740451799204, 2.20352686214989, -1.60935878400303],
    [0.92249861969041, 0.60814271531779, -1.34299135128278, -1.80764178066912],
    [1.29529570622827, 0.32385088875670, 0.09639620795131, 3.13883676896038],
    [-0.52073994297059, 3.00227563750157, -1.23889001283924, -2.12957940379437],
    [1.57222175458507, 0.28038763989958, 0.13265807759226, 1.13546202621012],
    [-0.40380660534891, 3.04878890785941, -2.04591183996323, 2.25650792264206],
    [-0.25620838579911, -2.62675473606632, -0.76516909877062, -0.94476409017548],
    [-0.32215482049974, -2.37840395230815, 2.10726328241338, 0.91591301512937],
    [-0.27139535911351, -3.05751210512949, -0.42273469438682, 1.59757720553590],
    [-0.64500007396408, -1.96219889711656, 2.33983773141049, -2.80426208758654],
    [0.77307851664815, 0.97091003561164, 1.63672723413118, -0.30112197425079],
    [1.93740591952981, 0.31515567600255, 1.07153241416598, 1.46354880082963],
    [0.74959863350389, 1.39840331381209, 1.26731557346845, 1.14697665840758],
    [-1.40527540871529, -1.87978584011321, -1.66640059045684, -0.99437180859295],
    [-1.55234102115027, -1.91243996728070, -1.83376938665429, 0.94925974010352],
    [2.06121070055645, 1.50114652610085, -1.37656476618843, -0.87326649336925],
    [1.96224384747313, 1.54046670547010, -1.55525791492560, 0.88117905057658],
]
w_strip1loose_lst = [
    [-1.35523129870145, -2.46242686507052, 2.60639019071604, -2.84135346446607],
    [-1.70290617014889, -3.00781961845874, 1.96013003741211, -1.33408415086962],
    [1.92501108304254, 0.94075199196101, -1.77689923586819, -2.54466254014339],
    [-1.93461471977659, -2.61726546619710, 2.36467759834404, 0.03160797893017],
    [-1.33782056777776, -1.87318230116343, 2.89014229436589, -1.00351525637766],
    [2.22163546170403, 0.45593665583995, 1.03412862138735, 2.03626022969788],
    [2.11858842254041, 1.04328644904996, 0.33298565072274, -2.34345475670517],
    [2.62090241846201, 1.07007838251425, -1.14569741930258, 1.53551026113143],
    [2.65710610643792, 0.79399878720145, 0.36680836610256, -0.14902444720219],
    [2.66979621313427, 1.12396762321697, -0.46950821287625, 0.69379078739355],
]
w_strip_I_lst = [
    [-0.96233421303122, 3.02307457190299, -1.55823863950114, -3.08587129384418],
    [-0.92578214385622, 3.01586834841974, 0.08123013306718, 3.01911817386691],
    [1.03993106063922, 0.46978456115081, -2.50950922601115, -1.74467199746268],
    [1.21129357383127, 0.35637652731241, -1.42341243048724, -1.17573085822499],
    [-1.23777863819554, 3.09465847851946, 2.99541732949355, 2.34570384967325],
    [1.42171141673939, 0.29393491292881, -2.84669787689217, -3.03620005733037],
    [1.47277136555625, 0.28700133169208, -1.17342721463747, 3.02683800619006],
    [-1.50058579574076, -3.09643061217610, -2.72527142409759, -2.05033848864972],
    [-0.63703500393831, 2.98843971474558, -1.44899452311359, 1.13540580819634],
    [1.70271522020373, 0.28330098026611, 0.33972687274201, -2.10717617980362],
    [-1.70320061494334, -3.00912403593322, 1.95826822851620, -1.33543586917786],
    [-0.37798711163230, 3.06702730486493, -0.52092092500998, 1.50247874674097],
    [1.82951402744061, 0.29664677862297, -0.50792744103781, 2.32757681885641],
    [-1.33946931979780, -1.86888555777378, 2.89403837131394, -0.99445093336825],
    [-1.72062567721391, -1.96394295257614, 2.98803363427876, 0.89839561534424],
    [-2.08614902859706, -2.14731242584292, -1.85863103161648, -2.01150103215315],
    [-2.15675846760395, -2.71442922581558, 2.33024774783299, 0.83775266572997],
    [-2.23491285886712, -2.29513988890244, -1.66034238955983, -0.33484054342275],
    [2.24964922153418, 0.40366776002870, 1.09829084882338, 2.12462268007421],
    [2.74348837417202, 1.03274247067318, -1.05830479607959, -0.21913260513625],
    [2.70281481775928, 1.09202437184493, -0.92505706096393, 1.13448461246848],
    [2.69230089149054, 1.10483783247746, -0.42581510142976, -0.79255553169717],
    [2.72414624395708, 0.70887689993560, 0.44350840358358, -0.47796470054906],
    [2.67599719980164, 1.12339195665027, -0.49023593149914, 0.70219405477394],
]
w_star_lst = [
    [1.23086372769415, 0.34772225089728, -2.79937289357284, 1.43482535651992],
    [1.23086372769415, 0.34772225089728, -2.79937289357284, -2.07284418635812],
    [-0.65832681460729, 2.98802340080354, -0.03520887850258, 2.00472061965616],
    [-0.65832681460729, 2.98802340080354, -0.03520887850258, -1.50294892322188],
    [-1.57491568158844, -3.06622455091730, -2.00372303718708, -1.96315235595375],
    [-1.57491568158844, -3.06622455091730, -2.00372303718709, 0.81236340834780],
    [-1.63995254201419, -3.03811600848822, -2.26584560906929, -1.87060104137028],
    [-1.63995254201419, -3.03811600848822, -2.26584560906929, 0.90491472293127],
    [-2.24786788966212, -2.59572202629571, -1.30802290678737, 0.00981667455853],
    [-2.24786788966212, -2.59572202629571, -1.30802290678737, 2.78533243886008],
    [2.70437076339292, 0.68375185028878, -1.50842229647173, -0.72976016914772],
    [2.70437076339292, 0.68375185028878, -1.50842229647173, 2.77790937373032],
]
w_alt_strip_I_lst = [
    [-1.20306131700310, 3.08415189054039, -0.63595508844087, -2.16530817148595],
    [1.21972592756715, 0.35256098909820, -1.53984254389651, -0.92534314119333],
    [1.06373716130034, 0.44906278380945, 1.77977661075311, 1.66892680366775],
    [1.00147883485526, 0.50776359555817, -2.56973806471230, -1.56848896437644],
    [-1.31711817083065, 3.12012986459912, 2.94824398556215, 2.22176812759790],
    [-0.58860863492243, 2.99155496544323, 1.88542814560406, -2.01199123639644],
    [0.91363152804297, 0.62180545089831, 2.86595299000493, 0.79195957066640],
    [-0.64305890034337, 2.98826754701171, -1.30412867042570, 0.85352119925521],
    [-0.49030108847590, 3.01022019089765, -0.55749865135070, 1.97472620400491],
    [-1.47696783012273, -3.10562565103864, 1.05026515039795, 1.85717170232306],
    [1.62245715943144, 0.28008227027359, -2.13366254117631, 2.01273828002598],
    [-1.60574657016314, -3.05310400763484, -2.84379723318594, -1.90530630075405],
    [1.73660111051445, 0.28592282923691, 0.34232533160122, -2.03297157933414],
    [-0.31767849489821, 3.13162685290772, 0.16678190488953, -0.84449900926443],
    [2.03158280638790, 0.33634914735497, 2.15172616070442, -2.12502735880854],
    [2.10231015476060, 0.35532016055954, -0.31747260080256, 2.05104241203348],
]
w_alt_strip_II_lst = [
    [-1.49490157334937, -3.09866092195849, 1.00851197583192, 1.96220499288015],
    [0.78979092691918, 0.90601126819695, -2.78129690494578, -0.26426184632363],
    [-0.50428978902373, 3.00628579488042, 0.85801841492048, -1.51580652938948],
    [-0.37182638700565, -2.26576484733828, 2.99186861500305, -1.44199695596349],
    [0.82053889007146, 0.81192713407898, 1.22892414324729, 0.98261070322789],
    [0.80194275670722, 0.86576739144819, 1.31625408229028, 0.72533720354231],
    [2.02639092510579, 0.33506018630301, 2.11877758991333, -2.01853363658043],
    [-1.26463426738007, -1.85942118601823, -2.47266884689360, 1.34624826712277],
    [0.83738342046856, 1.60634912331376, -1.16503864763720, -2.88240575363861],
    [1.90565222541782, 1.56146915344133, -0.92013002532789, -1.04606160394337],
]
w_alt_strip_1_loose_lst = [
    [1.48412234331725, 0.81004926348462, -2.09411442513605, -2.71271076402400],
    [1.35354251202387, 0.69039293889045, 1.22406340550126, 2.40108553981736],
    [2.01970971845348, 0.39933627452261, 2.05776261471518, -2.02357380284424],
    [1.99644551488030, 1.03708608384516, -2.06131737825127, 2.34716869269356],
]
trp_strip1loose_lst = [
    [-0.15159190755670, 2.74571437129809, 2.71204994164620, -2.07567735859873],
    [-0.15159190755670, 2.74571437129809, -2.16952681054586, -2.07567735859873],
    [-0.03610788524359, 2.06281672655672, -2.49412197423185, 2.44102931466403],
    [-0.03610788524359, 2.06281672655672, 2.38745477796022, 2.44102931466403],
    [0.32713870256872, 1.94160093090805, -2.97067026856323, 0.14370273620550],
    [0.32713870256872, 1.94160093090805, 1.91090648362884, 0.14370273620550],
    [0.95215020685782, 1.92348524582502, -2.61784780732329, 1.86464513218813],
    [0.95215020685782, 1.92348524582502, -1.21623925233577, 1.86464513218813],
    [2.14810829911713, 1.22502488211264, -2.13694920123341, -1.82659577811336],
    [2.14810829911713, 1.22502488211264, -0.73534064624589, -1.82659577811336],
    [2.62862033554880, 1.00557505739223, -0.75848044042301, 0.19622628062145],
    [2.62862033554880, 1.00557505739223, 0.64312811456451, 0.19622628062145],
]
trp_strip_I_lst = [
    [-1.04563464402681, 3.07483977053976, -2.47984668246603, -0.05637610858030],
    [-0.91761429450474, 3.04937837057345, -0.18925134004028, 3.10827130744987],
    [-1.49803385645042, 3.05780345799996, 2.35256213281168, -1.58289119267024],
    [-0.40698082892116, 2.87090241898782, -1.71047667671915, -2.48459432630274],
    [-0.18955955340556, 2.11652763834297, 1.99116426514811, 2.26129621426111],
    [-0.13654924492105, 2.09779459852160, -2.69811484114958, 1.04515999051764],
    [1.89024709205782, 0.14083357475278, 0.83529490908084, 1.78215819888267],
    [1.77705947795924, 0.27189384989350, 3.12348261623602, 1.24526246696707],
    [-0.04391590943259, 2.06551242213782, -2.49258304868746, 2.43407023343502],
    [0.20481567146212, 1.98149056286664, 1.70400610580807, 0.35744076785535],
    [0.14276179423349, 2.57693552623015, 1.59796878307174, 0.88857107035760],
    [0.86863542102399, 2.01963965379669, -0.99244100322580, 1.62733868062380],
    [2.36595488682048, 1.13422452318998, -2.06047020785978, -1.65913958685817],
    [2.63512584999046, 1.00203435134019, 0.63132968014972, -1.21167102304133],
    [2.62867392197551, 1.00554597862146, 0.64333670413185, 0.19602478583641],
    [2.67684414925209, 0.97880120564729, -0.91261386636199, -0.01072834766787],
]
trp_star_lst = [
    [-1.32778565059772, 3.09134289234349, 2.97792528305312, 1.30260023796923],
    [-1.32778565059772, 3.09134289234349, 2.97792528305312, -1.47291552633232],
    [-1.53491659572165, 3.04113942425000, 2.15516368743302, -1.55880648867450],
    [-1.53491659572165, 3.04113942425000, 2.15516368743302, 1.21670927562705],
    [-0.65688914489502, 2.97179868528147, 0.07857720024654, 1.97019643854806],
    [-0.65688914489502, 2.97179868528147, 0.07857720024654, -1.53747310432998],
    [1.72050331603422, 0.43503444875109, -2.31425309921350, 2.23760673414303],
    [1.72050331603422, 0.43503444875109, -2.31425309921350, -0.53790903015852],
    [1.93023070356026, 0.11571681541983, 1.05145506244437, -1.19030596125451],
    [1.93023070356026, 0.11571681541983, 1.05145506244437, 1.58520980304704],
    [0.01470433959053, 2.65350680026388, -1.71455344900918, -0.98500898405418],
    [0.01470433959053, 2.65350680026388, -1.71455344900918, 2.52266055882386],
]
trp_star1loose_lst = [
    [1.72009962130130, 0.43687233133564, -2.32432097002042, 2.23156458094152],
    [1.71029780878999, 0.48680538731578, -3.03239900543870, 0.99152886707916],
    [-0.07643777732891, 2.70505460700504, -2.38991137998458, -2.23043680180118],
    [0.01493126656467, 2.65337540681479, -1.71880312304369, -0.98834667064951],
]
trp_alt_strip_I_lst = [
    [-0.80362595671572, 2.66200341107827, 3.12718051954328, -2.36835958389864],
    [-0.98056069842996, 2.72300536016248, 1.30941108948910, -2.57707669148217],
    [-0.35167165271209, 2.38547279411858, -2.72103001845201, 0.43326989717214],
    [-0.16138830783988, 2.35131697464161, 1.57027039869303, -0.40495209821214],
    [-0.29643905726367, -3.09211709569215, -0.32181133814471, -0.66417854767356],
    [-0.01939464967504, 2.52002005967600, 1.42262652437619, 1.45629409251858],
    [1.91102887258926, 0.45262907209562, -2.95117271879902, 0.38953849477909],
    [2.10637744964665, 0.23271541720196, 0.65945200528682, 1.72709889548738],
    [0.43708943948443, 2.12232471200508, -1.48029528562706, 2.23808081216817],
    [1.17365162177534, 2.12454141066515, -1.39058667031172, -0.17307493461675],
]
trp_alt_strip_1_loose_lst = [
    [-0.80163428871904, 2.66138044142310, 1.72365015159721, -2.36576560099468],
    [-0.80163428871904, 2.66138044142310, 3.12525870658473, -2.36576560099468],
    [-0.16009829622853, 2.36011481948485, 3.06895474778677, -0.50148962321605],
    [-0.16009829622853, 2.36011481948485, 1.66734619279925, -0.50148962321605],
    [0.50443614136999, 2.04511282697172, -1.71926052412684, 2.38140456017869],
    [0.50443614136999, 2.04511282697172, -3.12086907911436, 2.38140456017869],
    [1.17817115258922, 2.12163118667207, -2.79522818613723, -0.17551356714746],
    [1.17817115258922, 2.12163118667207, -1.39361963114971, -0.17551356714746],
]
EV2_1_1_1 = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: par_strip1loose_lst,
	trisAlt.strip_I: par_strip_I_lst,
	trisAlt.star: par_star_lst,
	trisAlt.star_1_loose: par_star1loose_lst,
	trisAlt.alt_strip_I: par_alt_strip_I_lst,
	trisAlt.alt_strip_1_loose: par_alt_strip_1_loose_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip1loose_lst,
	trisAlt.strip_I: tri_strip_I_lst,
	trisAlt.strip_II: tri_strip_II_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.star_1_loose: tri_star1loose_lst,
	trisAlt.alt_strip_II: tri_alt_strip_II_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: str_strip1loose_lst,
	trisAlt.strip_I: str_strip_I_lst,
	trisAlt.strip_II: str_strip_II_lst,
	trisAlt.star: str_star_lst,
	trisAlt.star_1_loose: str_star1loose_lst,
	trisAlt.alt_strip_II: str_alt_strip_II_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip1loose_lst,
	trisAlt.strip_I: w_strip_I_lst,
	trisAlt.star: w_star_lst,
	trisAlt.alt_strip_I: w_alt_strip_I_lst,
	trisAlt.alt_strip_II: w_alt_strip_II_lst,
	trisAlt.alt_strip_1_loose: w_alt_strip_1_loose_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_1_loose: trp_strip1loose_lst,
	trisAlt.strip_I: trp_strip_I_lst,
	trisAlt.star: trp_star_lst,
	trisAlt.star_1_loose: trp_star1loose_lst,
	trisAlt.alt_strip_I: trp_alt_strip_I_lst,
	trisAlt.alt_strip_1_loose: trp_alt_strip_1_loose_lst,
    },
}

###############################################################################
tri_strip1loose_lst = [
    [0.10260788069564, 1.13002655661625, 3.05771718910401, 1.71758208682191],
    [-0.56450670309985, 2.01156609697354, 2.17617764874672, 1.71758208682191],
    [-0.01581687015385, -1.13002655661625, -2.73285581081688, 2.77427666380175],
    [-0.68293145394934, -2.01156609697354, -1.85131627045959, 2.77427666380175],
    [-0.22461121873312, 1.13002655661625, 2.58306283733630, 1.51960656917728],
    [-0.89172580252861, 2.01156609697354, 1.70152329697902, 1.51960656917728],
    [0.27173588955977, -2.01156609697354, -2.83170308877767, -3.09703670899832],
    [0.93885047335526, -1.13002655661625, 2.56994267804464, -3.09703670899832],
    [0.25412199488336, -2.01156609697354, -1.79975393920398, -1.47463871884777],
    [0.92123657867885, -1.13002655661625, -2.68129347956126, -1.47463871884777],
    [0.43647799283316, -2.01156609697354, -1.98379209053856, -1.78250063763283],
    [1.10359257662865, -1.13002655661625, -2.86533163089584, -1.78250063763283],
    [1.72120347530907, 2.01156609697354, -1.48939642549467, -1.75502321718264],
    [2.38831805910456, 1.13002655661625, -0.60785688513739, -1.75502321718264],
    [2.03321624819878, 2.01156609697354, -1.22462337746328, -1.14342724565445],
    [2.70033083199427, 1.13002655661625, -0.34308383710600, -1.14342724565445],
]
str_strip1loose_lst = [
    [-1.00895840295005, 3.09329860495176, 1.24229177305442, -1.73113172597434],
    [1.47723067512094, 0.30341969364974, 2.29300153444440, 1.60333517652703],
    [-1.59077590626486, -2.99958708905238, 0.89893314401556, 1.63819231219467],
    [-1.70883096618966, -2.68725037976200, 2.36059575673587, 2.94486115860482],
    [1.91381637662719, 0.51753894938709, 2.38036068954789, -2.00416701269377],
    [-2.11450635885191, -2.42931273376998, 2.41170037260652, 0.48139122177908],
    [2.45150573596481, 0.69345232676098, 0.36513143224729, -2.23062032438546],
    [2.73266255192051, 0.89858662663428, 0.20301062565060, -1.37644827553678],
]
w_strip1loose_lst = [
    [-1.09210219629361, 3.09887329814113, -1.72477507564942, 0.90793063927098],
    [-1.14348354958235, -3.13425765592453, -1.85312842638819, 0.85865554238643],
    [-2.02418070632604, -2.77941598802362, 2.20725768779485, -2.01835393124802],
    [-1.82895462165320, -2.34812864503672, 2.60713981817953, -3.10039848344912],
    [-1.97515687669008, -2.09125548002481, 3.00825455089032, -0.97522995131043],
    [2.33565964117058, 0.83729860405214, -1.77796912784417, -2.87480101387453],
    [-2.13590449466126, -2.42145098276224, 2.68163572646955, -0.46486712811843],
    [2.64945403445182, 0.85841543890127, -1.48295410350676, 2.42759967793996],
]
par_stripI_lst = [
    [-0.88408594790666, -2.61838557205194, 1.05012699160213, 1.19712731101294],
    [-0.22760538611590, -3.02366104365862, 2.11302679381998, -0.91640479904881],
    [-1.42691008916532, 2.60678100443663, -0.75060291603266, -0.27559411714725],
    [-0.52251694896221, 2.59977143374081, 0.66232680538684, -2.56463971915271],
    [1.63402211983532, -0.03354204390530, -0.70697232682803, 2.86389660292692],
    [1.80892887726423, 0.52012948245346, 0.69374371299411, -2.89717889455744],
    [0.69884395353658, -2.80697710998690, 1.84371080426630, -1.15318950223378],
    [1.07770972620236, -3.10363079444367, 1.86216587298526, -0.98775836501243],

]
tri_stripI_lst = [
    [0.48132106563422, 0.37885032021596, -2.47134729279351, 2.15352055265779],
    [-0.80117360980051, -2.47854966578108, -1.53265195985364, 0.70192360164694],
    [0.14582462163265, -0.48847795434203, -1.95923894969428, -2.96439762218410],
    [-1.28805089520665, -2.54063853990915, -1.00999089993105, 2.41350361691955],
    [-1.36174460837931, 2.54894852921308, 0.87401691813833, 1.65254995796573],
    [-1.42698761773885, 2.59938785115012, 0.84414775739989, -0.17253976656509],
    [0.93002013962061, -1.12494361951647, -2.68972235788726, -1.46973622601135],
    [1.11119179663992, -1.12544647997247, -2.87252127349912, -1.77927916758890],
    [2.12745394939160, -0.50294271574241, 1.38874079621489, 1.27518871036921],
    [2.77783060106529, 1.03974000421974, -0.21666488156543, -1.06066717893393],
]
str_stripI_lst = [
    [-1.08167503106967, 3.05063034647932, 1.23774620025848, -1.55958905844627],
    [1.47560474178230, 0.28669164656293, 2.31422271728098, 1.55273217811756],
    [-1.59561538448085, -3.05745527066531, 0.77609181347682, 1.64408257613413],
    [-1.85115649412793, -2.93363726248266, -2.18171053486487, 1.93981215031663],
    [1.91748319973363, 0.31126789442640, 2.80223183814234, -1.99179516146485],
    [-2.27661095453441, -2.52621371098308, -1.42086242559039, 0.05054893956548],
    [-2.20586775721826, -2.25633009494880, -1.92742889414652, -1.44422065937597],
    [-2.28056455231916, -2.51040120413367, 2.69656848992932, -0.02559038074824],
    [2.38102918203483, 0.45834572775133, -0.13054698061205, -2.05593678608156],
    [2.78488600706095, 0.85322301088372, -1.57662151455641, 0.57774151647717],
    [2.78503466541955, 0.91292454492340, -1.45774282732655, 1.12906616975519],
    [2.78640186107074, 0.89649431118992, 0.13738102608933, -1.22802157997141],
]
w_stripI_lst = [
    [-1.03847105968923, 3.03998860695804, -1.58690923526684, 0.97596278245281],
    [-1.45679943364473, -3.11332925795561, -2.80708059236015, 1.66115193233423],
    [1.51368737690475, 0.28324640425124, -1.13720941029114, -0.96337627296805],
    [-1.54078942765619, -3.08033673331201, -1.94557902728612, -2.02768134962701],
    [-1.63088591370698, -3.04213412801000, -2.16853460455453, -1.87209215915351],
    [1.82001642617477, 0.29532227342204, -0.30518276863766, -1.33617078597135],
    [-2.05057676288669, -2.80619639599573, 2.18215635153362, -2.08347948574030],
    [-2.15333660400386, -2.20181658449655, 3.01044867007904, 1.84381870152171],
    [-1.98734041715298, -2.08388537414886, 3.03088639867106, -0.96314313034041],
    [-2.26263979581542, -2.34525979709934, -1.60070922018626, -2.59785684855680],
    [-2.27655898803308, -2.52639869746417, -1.39226715541005, -0.05053434721763],
    [-2.28057501244653, -2.51035351610698, 2.68235996316529, 0.02544542151078],
    [2.78188798892120, 0.83442676255028, -1.34088064652737, -0.48654117923416],
    [2.78641416988930, 0.87104026307013, -1.29748676675942, 1.97842681249432],
]
trp_stripI_lst = [
    [-1.28355891963723, 3.09326948847472, 3.11690248777893, 1.23527689141095],
    [-1.57556007662712, 3.01347772508631, 1.26632059626977, -0.79639365080602],
    [1.83177396273491, 0.19304624290491, 0.50798177136701, -1.56297120148418],
    [1.98606784560235, 0.08998428136660, 1.68320932473667, 0.73449077834660],
]
tri_stripII_lst = [
    [-0.05093975412258, 2.05435012577146, -2.56957634058598, 2.68328576744732],
    [-0.04239717828045, 2.89684140154387, -2.24206739811420, -1.29186711494958],
    [-0.78037313608747, -2.33532227626571, -1.82307169457145, 1.12937154166985],
    [1.18327098024287, -0.12139974565126, 0.66124938079710, 1.28917528072994],
    [0.68497424526653, 1.20240188419257, -2.32907201232824, 1.70836753965910],
    [-0.42828083873248, 1.65863360611115, -2.82705068307912, -1.59842950582642],
    [0.92089541848234, 0.85301359815159, -0.47205891373542, -2.03597973519353],
    [-1.27510643372167, -2.52364158739342, -1.04595639691011, 2.41422074215770],
    [-1.06946001526612, 3.04183461869953, 2.12442885077999, -2.44111652193915],
    [0.13458014652453, -0.49934171206506, -1.94466308136325, -2.92462763260849],
    [0.02389861477697, 1.46817688418287, 1.37055954743580, -2.95808590879976],
    [0.63578596341964, 2.37820018044305, 2.71506765442110, 1.13564885183494],
    [0.57150328237427, 0.79441474806203, 0.90604915740093, 1.20248690273211],
    [1.07075282733228, 2.74087852746353, 3.06445133830301, 2.05151559024516],
]
str_stripII_lst = [
    [0.95573470349977, 0.56163504686237, 0.17796236336323, -2.39049055417495],
    [0.90632147440629, 0.63351405449696, -0.61475189086820, -2.13376648171970],
]
par_star_lst = [
    [-0.22731540041597, -3.02406464480696, 2.11290353141113, -0.91628785621601],
    [-0.50480379243483, 2.57566377306189, 0.63149867422395, -2.53346895352600],
    [0.07650215938737, 2.05150594350394, -1.18490513791044, -0.05580823790824],
    [0.95964290258137, 0.90745051647294, -2.19399761754175, 0.01039013222914],
    [0.58015497218585, -2.78075685576198, 1.76328389434689, -1.25093356919293],
    [1.09351492440183, -3.12144000308106, 1.85594086948540, -0.98305725349491],
    [0.58059679846632, 2.09604484307502, -0.34421015539280, 1.56654788009291],
    [1.45895694864987, 0.56254775250379, -2.01992069896225, 0.31868709760073],
]
tri_star_lst = [
    [0.29718927609248, 0.04131297331954, -2.23943939195585, -1.64959567707445],
    [0.19670017379411, -0.21589907918163, -2.09025320224715, -1.88519801486495],
    [0.14563957718641, -0.58329077835210, -1.92656064639828, -2.64139797932411],
    [0.79158554974907, 1.11921157800000, 2.55263958946881, 1.72518178175381],
    [0.82059796242233, -1.12190764524375, -2.57515913413470, -1.77719571668115],
    [0.85992081697153, -1.12333519031285, -2.61678557720067, -1.85425760440546],
    [0.06624730178685, 2.03099186323190, 1.19553160131475, 1.77529497461862],
    [0.07609148723492, 2.05156011017372, 1.20236189684327, -0.03817917173575],
    [0.38868463722472, -2.46885760889273, -1.55195262950212, -1.23296618585369],
    [0.48636730869278, 2.44443448419988, -1.10033089894915, -3.04099727107783],
    [0.45589412216813, 2.47386905958833, -1.14676212054071, 1.46130360814433],
    [0.52876053665690, -2.50371539652630, -1.65335407602562, -1.38781173119452],
    [0.95961876904719, 0.90745956812415, 2.19081254490962, 0.00719851912554],
    [1.47228681438668, 0.54155025185813, 1.92440306602555, 0.22644744506514],
    [2.74025053974059, 0.92278727261686, -0.26285244425405, 0.52709447014068],
    [2.76695176956340, 1.08008751815847, -0.17058816441074, -0.86913591299887],
]
str_star_lst = [
    [-0.89095056604739, 3.00961075368532, 1.20664103465848, 1.65944943453218],
    [1.04593217225932, 0.46437339664243, -2.35405535414568, -2.30534648830786],
    [1.06388998867156, 0.44893601519813, -2.31285405093919, -0.53795021532129],
    [1.01488197655500, 0.49384304492852, 2.41827275284195, 1.83265240375274],
    [1.39565283752467, 0.29852281284815, 2.30123647743828, -1.64485518360680],
    [-0.46080141897260, 3.02032147371800, -0.73872087170216, 2.55074097873070],
    [-0.39919850131367, 3.05175075027976, 0.75291826091944, -1.81839745388105],
    [-0.42913737122860, 3.03443285948226, -0.71067226700563, 0.70683663105850],
    [-1.90594107677465, -2.04099876719106, -2.45708664941401, -1.10962776807621],
    [-2.25850900102036, -2.33637229258507, -1.76444833351110, 0.26336101229611],
    [2.78589982024592, 0.90411340612921, -1.47587041080442, 0.47251398214884],
    [2.77219055746406, 0.96976162332885, -1.33502113350855, 1.03758138667894],
    [2.75001349944675, 0.74919493584004, 0.17029893918825, 0.31290221855529],
    [2.77305678050428, 0.96714223132090, 0.10773144349152, -0.99992406502233],
]
w_star_lst = [
    [-1.02114115254984, 3.03592559977326, -1.58013443587899, 0.98126713982416],
    [-1.02114115254984, 3.03592559977326, -1.58013443587899, -2.97906776796232],
    [1.07242459043854, 0.44197746998365, -2.59337663546129, 0.52069348929259],
    [1.07242459043854, 0.44197746998365, -2.59337663546129, -1.80215691010053],
    [-1.24375435584616, 3.09650657146989, 2.28390419986231, 2.55555661374464],
    [-1.24375435584616, 3.09650657146989, 2.28390419986231, -1.40477829404183],
    [-1.39190402356137, -3.13721087591218, -2.92737618160457, -2.10268246565112],
    [-1.39190402356137, -3.13721087591218, -2.92737618160457, 1.85765244213536],
    [1.49012338456571, 0.28522261538310, -1.15820577447768, 2.98624469257533],
    [1.49012338456571, 0.28522261538310, -1.15820577447768, -0.97409021521115],
    [1.77854347488517, 0.29013959347663, -0.05059609718318, -1.64637518035852],
    [1.77854347488517, 0.29013959347663, -0.05059609718318, 2.31395972742796],
    [1.78693029747655, 0.29110774820518, 1.09589893513210, -2.28973799567652],
    [1.78693029747655, 0.29110774820518, 1.09589893513210, 1.67059691210996],
    [-0.44233595855728, 3.02808745704470, -0.32882771291520, -0.67260203840161],
    [-0.44233595855728, 3.02808745704470, -0.32882771291520, 1.65024836099150],
    [-2.26123275817459, -2.34215063187314, -1.60434635746759, -0.26559606540170],
    [-2.26123275817459, -2.34215063187314, -1.60434635746759, -2.58844646479481],
    [-1.98221318726454, -2.08097277950533, 3.03064849285952, 1.35788777835877],
    [-1.98221318726454, -2.08097277950533, 3.03064849285952, -0.96496262103434],
    [2.68792662557102, 0.66521326200625, 0.54149550019652, -2.96599961007504],
    [2.68792662557102, 0.66521326200625, 0.54149550019651, -0.64314921068192],
    [2.78668375709722, 0.88842989172091, -1.27601423223851, -0.40853248183813],
    [2.78668375709722, 0.88842989172091, -1.27601423223851, 1.91431791755498],
]
trp_star_lst = [
    [1.71984966119352, 0.43801817343780, -1.00142608266647, -1.49152299955004],
    [1.71984966119352, 0.43801817343780, -1.00142608266647, 2.46881190823644],
    [1.77829729994803, 0.26958006599387, 0.10231845459516, -1.69466195293773],
    [1.77829729994803, 0.26958006599388, 0.10231845459516, 2.26567295484875],
    [-0.32079988358962, 2.83098043916236, 0.75211987635054, -0.97177542479579],
    [-0.32079988358962, 2.83098043916236, 0.75211987635054, 1.35107497459732],
    [0.55073363087684, 2.29712659615441, -1.48956672085298, -0.33119660898589],
    [0.55073363087684, 2.29712659615441, -1.48956672085298, 1.99165379040722],
]
par_star1loose_lst = [
    [0.79835477013463, 2.01156609697354, 1.87228131788797, -2.05345108885073],
    [1.46546935393012, 1.13002655661625, 0.99074177753069, -2.05345108885073],
    [0.92593632754962, 2.01156609697354, 1.34591149276301, 2.31992693783160],
    [1.59305091134511, 1.13002655661625, 0.46437195240572, 2.31992693783160],
    [0.76587365663353, 1.13002655661625, -2.13073056944835, -0.07090132394096],
    [0.09875907283804, 2.01156609697354, -1.24919102909107, -0.07090132394096],
    [0.62605684322029, 2.01156609697354, -0.44948550866281, 1.72422160168589],
    [1.29317142701578, 1.13002655661625, -1.33102504902010, 1.72422160168589],
]
tri_star1loose_lst = [
    [-0.17416835458449, 2.01156609697354, 2.16476016416905, -0.91642152086224],
    [0.49294622921099, 1.13002655661625, 3.04629970452633, -0.91642152086224],
    [0.78431707541970, 1.13002655661625, 2.53412456471280, 1.72141404892325],
    [0.11720249162421, 2.01156609697354, 1.65258502435552, 1.72141404892325],
    [0.81765978862916, -1.13002655661625, -2.57332266964622, -1.80444198688110],
    [0.15054520483369, -2.01156609697354, -1.69178312928895, -1.80444198688113],
    [0.83855324172535, -1.13002655661625, -2.59533879543813, -1.84233633333110],
    [0.17143865792987, -2.01156609697354, -1.71379925508086, -1.84233633333112],
    [0.08181662915947, 2.01156609697354, 1.23654322929098, 1.76359849997474],
    [0.74893121295496, 1.13002655661625, 2.11808276964826, 1.76359849997474],
    [0.09816142746099, 2.01156609697354, 1.27160147991440, -0.04834727288111],
    [0.76527601125648, 1.13002655661625, 2.15314102027169, -0.04834727288111],
    [1.05372383259576, 2.01156609697354, -1.00480180415583, -2.62775687834700],
    [1.72083841639125, 1.13002655661625, -0.12326226379855, -2.62775687834700],
    [2.06247392010585, 2.01156609697354, -1.11082136748424, -0.90717192267286],
    [2.72958850390134, 1.13002655661625, -0.22928182712696, -0.90717192267287],
]
str_star1loose_lst = [
    [-0.96761112749095, 3.09784548776368, 1.23026463004404, 1.62587423523134],
    [1.03617936444359, 0.51596315170312, 2.37992485386138, 1.89979770168174],
    [-0.67020299749719, -2.98368741428010, 0.87787799416338, -2.35610037462083],
    [1.40308848725809, 0.30451897859690, 2.29361002415483, -1.64129327814059],
    [-1.21315613901556, -2.44214302958086, 2.41106522184588, 2.80430445857616],
    [-1.63347081344209, -2.69009941298161, 2.35959280017706, -0.08760590317749],
    [1.72586014578165, 1.04713914141197, 0.07810096720221, -2.72223867939369],
    [2.74420479749756, 0.97554227358050, 0.13995400170655, -1.07263606731905],
]
w_star1loose_lst = [
    [-1.08374944121685, 3.10086736201835, -1.72943970284205, 0.90668715246300],
    [-1.13044442979016, -3.13755243967835, -1.84238999696480, 0.86256677641836],
    [-1.32794277441355, -3.06977526751548, 2.24102617325775, -1.26369723983235],
    [-1.63422873558272, -2.69067176141894, 2.31069080739523, 0.08770333766745],
    [1.78694882014675, 0.29112259608682, 1.09590036126105, 1.67058070858178],
    [-1.79900551496116, -2.34466052743650, 2.60140271025301, -3.10826909966694],
    [2.33321155303710, 0.83796032674881, -1.77886829622208, -2.87069354830308],
    [-1.96871399424987, -2.08702093336925, 3.00891611888508, -0.97744727553522],
    [2.37104565935779, 0.56317993856121, 0.86074312839741, 2.38733966033657],
    [2.66058139291921, 0.87335984692518, -1.45436674099744, 2.34076082891229],
]
trp_star1loose_lst = [
    [1.70796675207050, 0.50036873622594, -1.20569419044160, 2.42214179129328],
    [1.66500010854134, 0.83441110477683, -2.44380661892493, 0.42951768748720],
    [-0.24387924409626, 2.79331938206737, 2.21379736178482, -1.74592693975101],
    [0.56392830961204, 2.28697660868806, -1.60489643425626, -0.40234770497055],
]
par_altStripI_lst = [
    [1.09423335173382, 0.54704727727685, 1.90942038313206, 2.33846879756990],
    [1.21933082945152, 0.45874402051693, 2.02079187758454, 3.14082193571462],
]
trp_altStripI_lst = [
    [1.37708545464928, 0.35952691356685, -1.94790289736186, -1.54637561879699],
    [1.44048986502352, 0.07101510890840, 0.92781387718618, -2.29669986207485],
    [-0.54627337267582, 3.05367658174140, -0.98457647841989, 2.18738409598241],
    [1.70253619812036, 0.17134029059771, 2.98877640596069, 0.44729599667997],
    [-0.00693333394211, 2.68405820532346, -1.69692635769418, 2.49456817378165],
    [1.92866322875541, 0.06323331969990, 1.76156009215682, 0.82052282246789],
    [0.29830068129642, 3.01580761084308, -1.83383437980841, -0.60945488368741],
    [0.36114282774896, 2.96807445041048, -1.91281747229230, -0.58505812256398],
]
tri_altStripII_lst = [
    [-0.18861073700927, 2.28021361045196, -2.78733311941570, -1.12810156971748],
    [-0.05953559207062, 2.05948731938848, -2.58183841979328, 2.69560499165108],
    [0.64227292151509, 1.12768193230342, -2.42350348253362, 1.83585266873689],
    [0.95456348368735, 0.69593395642498, -0.22718542938982, -2.23178362495628],
    [1.20333053535433, 0.46759145492492, -0.17383079457900, 1.12865383253817],
    [-0.00830148478649, 2.73804835082925, -2.26952026993287, -1.25256815415777],
    [0.05983032971792, 2.73386022149929, 1.36338192670281, 1.25584627118547],
    [0.73556227265545, 2.39820811440365, 2.85823035608496, 1.12818741976575],
    [0.59336656744095, 1.19595084654452, 1.04303138018642, -1.87934398721107],
    [0.74701474407837, 0.97891496570583, 0.16346519547036, 1.37025137279996],
]
str_altStripII_lst = [
    [1.20469750134164, 0.35945517650492, 0.10108993879282, 0.99775669507686],
    [0.96042332496614, 0.55561388819041, 0.12527273701516, -2.40236488897058],
    [-0.69554014978135, 2.98849396931613, -2.71207584285769, -0.96250039145618],
    [0.91403931386753, 0.62116438284044, -1.33305857679208, 2.10454566722350],
    [-0.42057626239942, 3.03894384928407, -1.87039915524459, -1.39528125622737],
    [0.79770237617244, 0.87928125155666, -1.25614430717054, -1.45644571077297],
    [-0.31383308565939, -2.40121992780600, -0.99946660113541, -0.37561254876142],
    [-0.38894991320554, -2.23389155971210, 2.10976059891133, -2.22314917174979],
    [-0.24055174921826, -2.76697335416155, -0.63809428346987, 1.75964327177337],
    [-0.24837754297902, -2.68063906772827, 2.20252104407833, 0.38374089237783],
    [0.75034957248112, 1.09473404478238, -0.12803572909955, 1.51315871410454],
    [0.75488444590203, 1.42624377780924, -0.82760765899058, 1.79509955863961],
    [-0.99432864114974, -1.85562972387455, -1.48134913085410, -2.25329976016960],
    [-1.34682121959678, -1.86998610955903, -1.62445843858582, 1.17140848745664],
    [1.52381278130178, 1.67584492043667, -1.96926155510073, 2.17967121054531],
    [1.85298912378651, 1.58008484432309, -1.68927748796385, -1.08553789766216],
]
w_altStripII_lst = [
    [0.92119211915846, 0.61011996495944, -3.06795874013082, -1.74344643684083],
    [-0.74749610625063, 2.99136062999849, 0.73916373755176, 1.55266241814371],
    [-0.24779934394575, -2.95787400290022, -2.48304111036899, -1.97164771795730],
    [0.73880535859386, 1.25371631245491, -2.18883807261499, -2.57867834434243],
    [-0.24836964968890, -2.68070237061911, 2.49132006533233, -0.48493564145411],
    [-0.31252852956278, -2.40493107621770, -1.26400323359837, 0.45043935069807],
    [-0.35696489791642, 3.08533508641217, 1.10373907088935, -1.89611300158429],
    [0.79386103913509, 0.89199734773006, 1.36168220376045, 2.14236282541955],
    [-0.55705728017082, -2.02547603965429, -3.06506997651268, 2.00904549210553],
    [0.73896661855227, 1.27693388217880, 2.22401986039667, -1.26919286089582],
]
w_altStrip1loose_lst = [
    [1.57132051081067, 0.86018845023462, 1.75901703014703, 2.84839856141206],
    [1.78235460041362, 0.94885714767061, -2.91590198247208, 2.82281672343218],
]

EV2_1_V2_1 = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_I: par_stripI_lst,
	trisAlt.star: par_star_lst,
	trisAlt.star_1_loose: par_star1loose_lst,
	trisAlt.alt_strip_I: par_altStripI_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip1loose_lst,
	trisAlt.strip_I: tri_stripI_lst,
	trisAlt.strip_II: tri_stripII_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.star_1_loose: tri_star1loose_lst,
	trisAlt.alt_strip_II: tri_altStripII_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: str_strip1loose_lst,
	trisAlt.strip_I: str_stripI_lst,
	trisAlt.strip_II: str_stripII_lst,
	trisAlt.star: str_star_lst,
	trisAlt.star_1_loose: str_star1loose_lst,
	trisAlt.alt_strip_II: str_altStripII_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip1loose_lst,
	trisAlt.strip_I: w_stripI_lst,
	trisAlt.star: w_star_lst,
	trisAlt.star_1_loose: w_star1loose_lst,
	trisAlt.alt_strip_II: w_altStripII_lst,
	trisAlt.alt_strip_1_loose: w_altStrip1loose_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_I: trp_stripI_lst,
	trisAlt.star: trp_star_lst,
	trisAlt.star_1_loose: trp_star1loose_lst,
	trisAlt.alt_strip_I: trp_altStripI_lst,
    },
}

###############################################################################
tri_strip1loose_lst = [
    [0.32404128843123, 0.00000000000000, -2.21057725939588, -1.70947193836188],
    [-1.23962167650483, 3.14159265358979, 0.93101539419391, -1.70947193836188],
    [-0.71371891395463, 3.14159265358979, 0.72277721943365, 2.72798218427123],
    [0.84994405098143, 0.00000000000000, -2.41881543415614, 2.72798218427123],
    [0.49509972613114, 3.14159265358979, -2.44549105805376, 3.03604777351919],
    [2.05876269106720, 0.00000000000000, 0.69610159553603, 3.03604777351919],
    [0.79904115460992, 3.14159265358979, -2.50183130106422, 1.72096443086398],
    [2.36270411954598, 0.00000000000000, 0.63976135252557, 1.72096443086398],
    [2.18827954075737, 0.00000000000000, 2.09078504165416, -0.90830073097680],
    [0.62461657582131, 3.14159265358979, -1.05080761193563, -0.90830073097680],
    [0.71360833001979, 3.14159265358979, -1.12845884419665, -1.08599864611698],
    [2.27727129495585, 0.00000000000000, 2.01313380939314, -1.08599864611698],
]
str_strip1loose_lst = [
    [-0.95086479415174, -2.62441947847629, -0.58010044636175, -2.97947963531378],
    [1.37758187397277, 0.01479343858608, -3.13338211239005, -0.49576214752629],
    [1.59695782903425, 0.08176773932371, -3.09607898313505, -1.45258326360352],
    [-1.64538357554226, -2.49043152725090, -0.79177975473936, -0.76944197475153],
    [-1.70146022268430, -2.21992735901196, -2.03976145681102, -2.00444033977498],
    [-1.74225229100277, -2.85291997858867, -2.97510619697618, 3.10122737190749],
    [-2.02045186287872, -2.83051205210095, -2.96101989076313, -1.88116645434279],
    [2.13876801647583, 0.41814115877664, -0.44950814904672, -2.68231970277436],
    [-0.10398640255235, 2.34825182357830, 1.10194439370510, -0.59985852447330],
    [0.08272940103864, 2.63435303768884, 0.56621428021912, -1.03172776919106],
    [2.26631062996575, 0.91762041200042, -2.07514632327979, 0.66845824050150],
    [-2.27386196152128, -2.22291364563059, -2.06655097607687, 0.41968199602761],
    [2.39937186052407, 0.93047915295879, -1.87523353888348, 0.49364149837597],
    [2.42976004960701, 0.39363633427067, -0.41949482874568, 2.22886419981728],
]
w_strip1loose_lst = [
    [-1.09190986154261, 3.13171976805571, -1.80192072446712, -2.74981559424002],
    [1.16331701702304, 0.15001648515945, -1.52124922567720, -2.35753503460323],
    [-1.01441025939972, 2.93764286463931, 0.33374659292789, 2.67874176041282],
    [-0.97486695983254, -3.00400292278212, -0.45575586645719, -2.81903041369825],
    [-1.29001989214434, 2.89973340625546, 0.67091208784396, -0.72283586283267],
    [1.36855316612569, 0.00532800284239, 2.90084568757311, 0.44113432524471],
    [-1.44888078515105, 2.95333391099196, 0.37563575496022, 2.71198276108038],
    [-1.48914658539743, 2.95810499602285, 3.04471500292215, -2.72650136286847],
    [1.64225494964643, 0.05168522054829, -2.87162334332385, 3.02232942502564],
    [1.67274324659645, 0.69453538624268, -0.57276218107564, -0.88105904294017],
    [1.70285023067352, 0.30664701497233, 0.31815154022373, -2.04835969010314],
    [-1.76211556745479, -2.48207561746621, -1.23012693649085, 0.62965911175707],
    [1.77982059560220, 0.04122396597196, 0.35434551782500, -3.04061212700586],
    [-0.18389633142259, 2.88979820939315, -0.30765042938987, 1.19321242879758],
    [-0.18912739277496, 2.39012464263452, 0.77042739332708, 0.56181175787421],
    [-2.27896293642685, -2.24330894777344, -1.77816459715072, -0.43468928659310],
]
par_strip_list = [
    [0.50066103037630, 0.10882709339528, -3.00236046099771, 2.01409662668042],
    [-0.26467626788388, 1.35561845344575, -2.50570443932096, -0.37593035276325],
    [0.59768551357834, 2.29760937091873, 1.95774890371679, 2.68038591541201],
    [1.14295249227403, 1.57360485306148, 1.49582399932565, -2.34603676002753],
    [1.57367193886038, 0.43047731296231, -0.60016386225970, -0.86433522477021],
    [1.19850196114609, 0.81163808272056, -0.87522778313280, 2.57635390108178],
]
tri_strip_list = [
    [-1.18476603030779, -3.00058810335221, 0.72689958263122, -1.89257555833486],
    [-0.29127622200232, 1.39701937209479, 2.59771914082824, -0.24736323282816],
    [0.86804381705177, 3.07545518557374, -2.45736906348027, 1.63834420919896],
    [1.52736694659769, 1.77405336290435, -1.20288091924007, -2.43541054602254],
]
str_strip_list = [
    [-1.27871144097281, -2.51829598723173, -1.17821233390388, -2.94176413175068],
    [-1.27871144097281, -2.51829598723173, -0.42177603977232, -1.50328625910387],
    [-1.27871144097281, -2.51829598723173, 2.44577983318260, 2.94176413175068],
    [-1.27871144097281, -2.51829598723173, 1.68934353905104, 1.50328625910387],
    [1.77871144097281, 0.94749966043683, -2.71981661381747, 1.50328625910387],
    [1.77871144097281, 0.94749966043683, -1.96338031968591, 2.94176413175068],
    [1.77871144097281, 0.94749966043683, 0.69581282040719, -2.94176413175068],
    [1.77871144097281, 0.94749966043683, 1.45224911453876, -1.50328625910387],
]
par_star_list = [
    [0.77388086277562, -0.47671588141912, -2.06457033281442, -1.18138913299661],
    [0.55687811427289, -0.09269817598983, -2.06457033281442, -1.83641587330938],
    [-0.33808768382237, -2.02521232505472, 2.06457033281442, -2.68949061589624],
    [-0.33808768382236, 1.82949509761983, -2.06457033281442, -0.98882783477243],
    [-0.01030287101074, 1.72204556464242, -2.06457033281442, -2.02510719466730],
    [-0.01030287101074, -2.13266185803214, 2.06457033281442, 2.55741533138848],
    [0.55687811427289, 2.33577970851520, 2.06457033281442, 2.74610665274640],
    [0.77388086277562, 1.95176200308591, 2.06457033281442, -2.88205191412042],
]
tri_star_list = [
    [-1.09152600255450, 3.06509458615772, 1.03302843311526, 2.46321064798875],
    [-0.48201535929359, 1.92354960746201, 2.25908227752755, -0.53566396201322],
    [0.93171811763895, 2.90769239832265, -2.34587409609346, 1.66099844519089],
    [1.59131807621620, 1.64772583278850, -1.03361801361151, -2.47240324203199],
]
par_star1loose_list = [
    [0.35404258919795, 0.00000000000000, -3.05277078031544, -2.70330600717125],
    [-1.20962037573811, 3.14159265358979, 0.08882187327435, -2.70330600717125],
    [-1.35309861285169, 3.14159265358979, 0.09475608203559, -2.22679077856972],
    [0.21056435208437, 0.00000000000000, -3.04683657155420, -2.22679077856972],
    [-0.00828724499734, 3.14159265358979, 2.30163142532649, 2.68088418246929],
    [1.55537571993872, 0.00000000000000, -0.83996122826330, 2.68088418246929],
    [1.82810872988956, 0.00000000000000, -0.31727028795837, -1.37654836587065],
    [0.26444576495350, 3.14159265358979, 2.82432236563142, -1.37654836587065],
    [2.87283399026898, 0.00000000000000, -1.00015245727569, 0.31006667394294],
    [1.30917102533292, 3.14159265358979, 2.14144019631411, 0.31006667394294],
    [1.35355957127413, 3.14159265358979, 2.24158638966895, -0.48764237456316],
    [2.91722253621019, 0.00000000000000, -0.90000626392085, -0.48764237456316],
]
tri_star1loose_list = [
    [0.38962218390932, 0.00000000000000, -2.21047225094884, 2.58333194163391],
    [-1.17404078102674, 3.14159265358979, 0.93112040264095, 2.58333194163391],
    [-1.68556420193247, 3.14159265358979, 0.75194773124962, -1.53281338590409],
    [-0.12190123699641, 0.00000000000000, -2.38964492234017, -1.53281338590409],
    [2.61936344475730, 0.00000000000000, 0.69884619248735, 1.13805581909121],
    [1.05570047982124, 3.14159265358979, -2.44274646110244, 1.13805581909121],
    [1.27666755676108, 3.14159265358979, -2.29148437997605, 0.40263982339437],
    [2.84033052169714, 0.00000000000000, 0.85010827361375, 0.40263982339436],
]
str_star1loose_list = [
    [1.01904080014533, -0.02417540328251, 3.12817281531379, -1.33320925067510],
    [0.83378262880583, 0.04531029797962, -3.11642426069693, -0.15446501122076],
    [-0.58255559707361, 2.51276496099883, 0.75268340089506, 1.15668009090158],
    [-1.59868789530093, -2.48616556865092, -0.79946493824316, -2.72426339571938],
    [-0.31047038157911, 2.37948652155778, 1.02160327098629, -0.13692958958994],

    [-1.90948855147420, -2.63318551214509, -0.56783606983935, -0.92982329857655],
    [2.31116441888794, 0.74922610613286, -2.55879476633833, 1.54398636442824],
    [2.27000341668468, 0.83314808017469, -2.40088075430938, 2.27904312629484],
]
w_star1loose_list = [
    [-1.07100989366766, 2.73080730454193, 1.79829014170644, -1.78607826238934],
    [0.83375877129041, 0.04585403742084, 3.08507537615126, 0.14814961925576],
    [-0.92783380701773, -3.10462912699188, -0.27167695382754, -3.05636966047831],
    [1.41835586552903, 0.43829155101711, -2.65298280255339, 2.11498178031211],
    [1.46941536362531, -0.01814073762464, -1.87268161739640, -2.64588751487031],
    [-1.52901227615914, 3.10891925271019, 1.81391165958428, 2.40565203206263],
    [-1.57126909087776, -3.06878672763118, -1.98854488302213, -1.97293808038875],
    [-1.98482338074407, -3.13595800515824, -2.98709167833423, 3.12878789174836],
    [-0.30798354128983, 2.38028637540319, 0.93872790773803, 0.15760201136499],
    [-2.00529450235368, -2.66252166040135, -1.05156602405254, 0.81567801647275],
    [2.09876298134985, 0.08762374662665, -0.06497758734759, -2.94427083104590],
    [2.50741395598614, 0.65829969566616, -1.75701923688723, -1.14637116984194],
    [-2.58442019300719, -2.32398619472928, -2.62448560148717, 0.68360122208014],
    [3.08806777666416, 0.69147643468848, -0.56437651516590, -0.88391135882909],
]
trp_star1loose_list = [
    [-0.85013274658615, 3.03238496114807, 0.58882342932200, 2.89343316208049],
    [-1.21227003213844, 3.09238621220817, 2.66473514561808, 0.08889889719812],
    [-1.35620380111694, 3.08894473695933, 2.18511833544727, 0.09515258160379],
    [-1.43866501388042, 2.68577542345540, 1.61326917771509, 1.29847367087141],
    [-1.49143505164445, 3.06024779594678, -2.37365108121778, 2.95767909821712],
    [1.73122142195027, 0.39134825228769, -2.10909532050520, -0.89088266580840],
    [1.83742763293896, 0.18691505671768, -1.44204606517489, -2.70699804543325],
    [1.85616637197872, 0.16845688138039, 1.48332077032963, -0.31340177029443],
    [2.09769466230613, 0.06003572259309, 0.13625077822116, -3.00624073600706],
    [-0.11355718076757, 2.72534668547313, -1.11118156110352, 1.94472375515002],
]
par_altStrip_list = [
    [-0.24614883732044, 2.57657203177763, -1.62286761765098, -2.52343994399435],
    [0.16618073086564, 1.75479653459551, -2.99110577628806, 2.63412704867348],
    [1.08590137227454, 0.55449817804776, -1.52498344650876, 2.50027262491530],
    [0.49979351445111, 2.55757044354032, 2.08301987428747, 2.56420709641570],
    [1.57376245491209, 0.42563370660648, -0.61018874703633, -0.85221425641302],
    [1.16015623590783, 2.03989356072873, 2.00843172276380, -1.44895197761725],
]
trp_altStrip_list = [
    [-1.08087104472141, -2.76257221853108, 1.31007122707456, -1.62281104614805],
    [-0.86013846539612, -2.82098176398407, 2.03656105762397, -1.30647070786714],
]
w_altStrip1loose_list = [
    [0.96733920405061, -0.02215611616468, -2.68224468887888, -0.86781806599903],
    [-1.23617160306147, -2.54114843241830, -0.38920981785636, -1.45644103668349],
    [-0.67526916642453, 2.55256661553531, 0.31486573242010, 0.96621838438296],
    [-1.36152844701141, -2.75085200127518, -2.41177143515489, -0.80271255005487],
    [-1.50549088836375, 2.96127908646698, 3.02131444923627, -2.73414384976576],
    [-1.51940895242333, 2.97402433643279, 0.40160748172018, 2.75644464451338],
    [-0.27423171353317, 2.64308576676238, 1.64688243637928, -1.45556232932057],
    [-0.32805437508260, 2.83485195024880, -0.34401742382298, 1.71772433406085],
    [-0.26152114007130, 2.43148715220155, 0.61985900205796, 0.81074303729620],
    [1.68056348973578, 0.70022679638067, -0.59379568320092, -0.80869328793917],
    [1.68744072248066, 0.50163737270972, -1.65910855916000, 1.45967213897884],
    [1.73804443844780, 0.31718528017934, 0.31204907199824, -1.94646466355330],
    [1.77865265447758, 0.03562539899205, -3.11208809823011, 3.06152651204649],
    [1.78539563651769, 0.04131468995198, 0.35629636014470, -3.04029683367018],
]
E0_1_1_1 = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_I: par_strip_list,
	trisAlt.strip_II: par_strip_list,
	trisAlt.star: par_star_list,
	trisAlt.star_1_loose: par_star1loose_list,
	trisAlt.alt_strip_I: par_altStrip_list,
	trisAlt.alt_strip_II: par_altStrip_list,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip1loose_lst,
	trisAlt.strip_I: tri_strip_list,
	trisAlt.strip_II: tri_strip_list,
	trisAlt.star: tri_star_list,
	trisAlt.star_1_loose: tri_star1loose_list,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: str_strip1loose_lst,
	trisAlt.strip_I: str_strip_list,
	trisAlt.strip_II: str_strip_list,
	trisAlt.star_1_loose: str_star1loose_list,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip1loose_lst,
	trisAlt.star_1_loose: w_star1loose_list,
	trisAlt.alt_strip_I: str_strip_list,  # remarkable:
	trisAlt.alt_strip_II: str_strip_list, # the same as a different fold!
	trisAlt.alt_strip_1_loose: w_altStrip1loose_list,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.star_1_loose: trp_star1loose_list,
	trisAlt.alt_strip_I: trp_altStrip_list,
	trisAlt.alt_strip_II: trp_altStrip_list,
    },
}

###############################################################################
par_strip1loose_lst = [
    [0.14366010680422, 0.0, -3.02870092680606, -2.03055921593672],
    [0.14366010680422, 0.0, -3.02870092680606, 0.29229118345639],
    [-1.42000285813184, 3.14159265358979, 0.11289172678374, 0.29229118345638],
    [-1.42000285813184, 3.14159265358979, 0.11289172678374, -2.03055921593673],
    [0.10879574283429, 3.14159265358979, 2.53930815837036, -1.06232063591412],
    [0.10879574283429, 3.14159265358979, 2.53930815837036, 2.89801427187236],
    [1.67245870777035, 0.0, -0.60228449521943, 2.89801427187236],
    [1.67245870777035, 0.0, -0.60228449521943, -1.06232063591412],
    [-0.43789621198356, 3.14159265358979, 1.68803343298843, -1.13642251783063],
    [-0.43789621198356, 3.14159265358979, 1.68803343298843, 2.82391238995585],
    [1.12576675295249, 0.0, -1.45355922060136, 2.82391238995585],
    [1.12576675295249, 0.0, -1.45355922060136, -1.13642251783063],
    [1.12077642915975, 3.14159265358979, 1.86043734848220, -0.97385817951362],
    [1.12077642915975, 3.14159265358979, 1.86043734848220, 1.34899221987949],
    [2.68443939409581, 0.0, -1.28115530510760, 1.34899221987949],
    [2.68443939409581, 0.0, -1.28115530510760, -0.97385817951362],
]
par_strip_lst = [
    [0.50683836006755, -0.55412050029900, -3.13539520316808, 1.40768503669713],
    [1.20174220005450, -0.06517682205741, -1.39788714679463, -1.02857237207586],
    [-0.10557284405912, 0.58803505950607, -2.79785402207577, -0.53028808268087],
    [0.26812584150105, 2.93266683238015, 2.67450580477366, 3.06405177850317],
    [0.50152329137468, 2.55363846137295, 2.81943029306661, -2.56436915465252],
    [0.84883637368335, 0.47511664615920, -1.42128979285213, -2.73630946070785],
]
par_star_lst = [
    [1.20769912371099, -0.05893137863474, -1.38775788215077, -1.02600279297424],
    [1.20769912371099, 1.51119329812485, 1.38775788215077, -2.23139388051620],
    [0.86741423589324, 0.49955639999624, -1.38775788215078, -2.78953191520198],
    [0.86741423589324, 2.06968107675582, 1.38775788215077, 2.28826230443565],
]
par_star1loose_lst = [
    [0.02534520449051, 3.14159265358979, 2.36727634979961, -0.93675034242083],
    [1.58900816942657, 0.0, -0.77431630379018, -0.93675034242083],
    [-0.41147200893100, 3.14159265358979, 1.71761347981183, -1.10965260229935],
    [1.15219095600506, 0.0, -1.42397917377796, -1.10965260229935],
    [0.90116830042816, 3.14159265358979, 1.61308803113795, 2.21297726666036],
    [2.46483126536422, 0.0, -1.52850462245184, 2.21297726666036],
    [1.11763906677400, 3.14159265358979, 1.85654722779152, -0.97519957919860],
    [2.68130203171006, 0.0, -1.28504542579827, -0.97519957919861],
]
par_altStrip_lst = [
    [-0.19021888588362, 2.67615403096640, -2.06691348718420, 3.12279175999111],
    [-0.24936586067843, 2.55979900066772, -2.41015436844098, 2.48180214513473],
    [0.36736299784420, 2.63075025031278, 2.77491327117711, -2.99308919632745],
    [0.50581118475618, 2.55393505214392, 2.81889315574958, -2.55063446782750],
    [1.15875217064429, 0.49599321439310, -0.66116929694757, -2.23131464929737],
    [1.05272351680887, 0.58607200891696, -0.80771672923992, -2.64603998432074],
]
tri_strip1loose_lst = [
    [0.13655518865561, 0.0, 2.94394237743731, 0.20703365671677],
    [-1.42710777628045, 3.14159265358979, -0.19765027615248, 0.20703365671677],
    [0.00313617185879, 0.0, 3.07801979472089, 1.98037647275980],
    [-1.56052679307727, 3.14159265358979, -0.06357285886890, 1.98037647275980],
    [0.43343644947462, 0.0, -2.21390444444385, 2.56207929620502],
    [-1.13022651546144, 3.14159265358979, 0.92768820914594, 2.56207929620502],
    [-0.04164559795124, 0.0, -2.32763135240730, -1.55512265397075],
    [-1.60530856288730, 3.14159265358979, 0.81396130118249, -1.55512265397075],
    [0.65351210492747, 3.14159265358979, -2.49338536385030, -2.44057215895438],
    [2.21717506986353, 0.0, 0.64820728973949, -2.44057215895438],
    [1.16369570507291, 3.14159265358979, -2.38569134970910, 0.83451212736302],
    [2.72735867000897, 0.0, 0.75590130388069, 0.83451212736302],
]
tri_strip_lst = [
    [-0.42415792289043, 1.78589648288740, 2.35898631890829, 1.65433493809992],
    [-0.14419304636769, 0.65147014033807, 2.94444439466697, -0.34936798686617],
    [0.64984697679573, -1.32531334596643, 2.92461805800024, 3.13821546490286],
    [0.71803166291870, -1.05717656848334, 2.74615432372700, 1.22731913210782],
    [-1.14415998269649, -3.10249740764804, 0.87245583517641, 2.61235565557899],
    [-1.27856362679730, -2.53673435208107, 0.02864653529610, -2.45364318673685],
    [0.69337447267027, -2.55041055097644, -2.80302265179365, 1.33108462771787],
    [1.05505526874451, 2.63167894090699, -2.13327850178665, -2.10619691171035],
]
tri_star_lst = [
    [-0.83213473588068, 2.59060735890270, 1.62937954958339, -1.26939161355806],
    [-1.27015643835315, -2.65954024020010, 0.21805803981423, -2.20205634329738],
    [1.74534019232200, 0.67271976472060, 0.43140563049672, 1.59113764785908],
    [1.33819419122331, 2.11127123096971, -1.61742324876584, 1.34071926677856],
]
tri_star1loose_lst = [
    [0.74420581106394, 0.0, -2.33238392013697, 2.59825033448093],
    [-0.81945715387212, 3.14159265358979, 0.80920873345282, 2.59825033448093],
    [0.28009523787917, 0.0, -2.21405641761384, -1.68506631120542],
    [-1.28356772705689, 3.14159265358979, 0.92753623597595, -1.68506631120542],
]
str_strip1loose_lst = [
    [-1.43701554298883, 3.01610245555679, 0.12626486685715, 0.04682873659896],
    [-1.55462866519132, -2.48480569208120, -0.80193018822365, -2.75974108618885],
    [-1.56179025918412, 3.10096722630343, 0.04065151468881, 1.92960424274722],
    [1.57458627634949, 0.07384317486832, -3.10051269394335, 0.17718042024488],
    [-1.86691701127120, -2.57988602188686, -0.64499686245721, -0.85924401449027],
    [1.89161348241850, 0.21026865678297, -3.02253437881265, -2.10499354836645],
    [-1.91624763433950, -2.84609375915887, -2.97084359143344, 2.41431383252263],
    [2.28899214637614, 0.39555338566751, -0.42181517680694, -1.92849894955083],
    [2.27606146454703, 0.82316319264449, -2.42374286817965, 1.19018144598594],
    [2.26621874373819, 0.91759035456083, -2.07538463259419, 2.28296884746004],
    [-2.27597762457911, -2.22306811588824, -2.06783065849115, -1.18594564814384],
    [-2.32099460402885, -2.74402691299702, -2.90368076811747, -1.29094084504591],
    [-2.52578615437943, -2.26296467755499, -2.27057056836375, 0.27414097990049],
    [2.57376117968566, 0.92391739833462, -1.69848874131128, 1.68714232073214],
    [2.85783883684782, 0.88258749717996, -1.41395778659947, 0.66442014678674],
    [2.80006705135414, 0.45907418991823, -0.50151161732860, 1.48556486656049],
]
str_strip_lst = [
    [-1.27871144097281, -2.51829598723173, -0.01843274607775, -2.43141345125529],
    [-1.27871144097281, -2.51829598723173, -0.23115213097926, -2.84023891971552],
    [-1.27871144097281, -2.51829598723173, 1.49871963025798, 2.84023891971552],
    [-1.27871144097281, -2.51829598723173, 1.28600024535647, 2.43141345125529],
    [1.77871144097281, 0.94749966043683, -3.12315990751204, 2.43141345125529],
    [1.77871144097281, 0.94749966043683, -2.91044052261054, 2.84023891971551],
    [1.77871144097281, 0.94749966043683, 1.64287302333182, -2.84023891971551],
    [1.77871144097281, 0.94749966043683, 1.85559240823332, -2.43141345125529],
]
str_star_lst = [
    [-1.27871144097281, -2.51829598723173, -2.28444434588150, 2.06457033281442],
    [-1.27871144097281, -2.51829598723173, -2.73117346201936, -2.06457033281442],
    [-1.27871144097281, -2.51829598723173, -0.13039970433076, -2.06457033281442],
    [-1.27871144097281, -2.51829598723173, 1.39796720360948, 2.06457033281442],
    [1.77871144097281, 0.94749966043683, -0.85714830770829, -2.06457033281442],
    [1.77871144097281, 0.94749966043683, -3.01119294925904, 2.06457033281442],
    [1.77871144097281, 0.94749966043683, -0.41041919157043, 2.06457033281442],
    [1.77871144097281, 0.94749966043683, 1.74362544998032, -2.06457033281442],
]
str_star1loose_lst = [
    [0.87215758870192, 0.01814819358902, -3.13151968488761, -1.97159163579958],
    [-1.27831008383016, -2.50764759602906, -2.70442388040219, -2.08642561532510],
    [-1.08610206013541, -2.57293571606520, -0.65555247663619, -2.99003183716696],
    [-1.28193212248254, -2.46040312489880, -2.65100907231386, 2.37623425680567],
    [0.75672794120305, 0.22582681337171, -3.01332197477476, 0.34301051998041],
    [1.35314816456665, 0.83894323488245, -2.38687998232722, -2.86747810846815],
    [-1.37302851817260, -2.31279820772812, -2.41103522173182, -2.08967515514312],
    [-1.69027728873330, -2.49778579629234, -0.77869903788138, -0.76740957061193],
    [1.69788622087815, 0.84960620044855, -1.27788640651733, -1.60442776857050],
    [-0.43372429835647, 2.43153973466837, 0.90508469303844, 1.91216589876656],
    [0.10302916256043, 2.56118331513876, 0.67368993835286, -0.98504793719469],
    [-2.42392652318419, -2.24002245641545, -2.17458658290215, 0.37399787490035],
    [2.76535727812860, 0.90089230016221, -1.51135195568442, 0.46688571685189],
    [2.24496081202496, 0.87654954231565, -2.27785747169964, 0.93558568254975],
]
w_strip1loose_lst = [
    [-1.43716915065369, 3.01608845112070, 0.15209286400079, -0.04642216187709],
    [1.49716399056047, -0.04221576947580, -2.01776944728615, -2.42486817616252],
    [-1.55353980342799, -3.07299325533255, -1.98119212173034, -1.99696930807509],
    [1.57489944389698, 0.07252723563420, -3.00004802509863, -0.18163968440488],
    [-1.63765587490047, 2.99019830198819, -0.20181852719365, 2.77057366842711],
    [1.80980000639894, 0.09041391382192, -1.97061442604279, 2.75595335843175],
    [-1.86118795247923, 3.09116685025486, -3.03406305334218, -3.02698915667645],
    [-1.96284985939876, -2.59178702718268, -1.11074361590055, 0.74043910382282],
    [2.14991636241395, 0.10205761558730, -0.11855280818050, -2.91187392827382],
    [2.47022268721964, 0.78664595656858, -1.72424776008995, -0.88176016078619],
    [-2.53323931009749, -2.27513613939240, -2.07013679519738, -0.33412396957476],
    [2.87364989564218, 0.85976971035903, -1.16724172668740, -0.46163301473433],
]
w_star1loose_lst = [
    [0.76492806304391, 0.22971371281448, -2.80922307539030, -0.35406402921433],
    [-1.07463595178809, -2.83555427880501, -0.75835691763952, -2.39885311772242],
    [-1.11723547223911, 3.13327786419645, -1.81001480197639, -2.70155264246934],
    [-1.17098355266273, 2.83043137603631, 2.48125948816409, -2.37656992766695],
    [1.23200534391891, 0.08940947707764, -1.55098811706029, -2.51522531072663],

    [-1.34858753826832, -3.04372202632070, 2.23557260107926, 2.09125222067934],
    [-1.44026890742876, 2.94307417146580, 3.00208137652517, -2.69252880760216],
    [1.51010973274896, 0.65536610164048, -2.31646267275122, 1.49329555212691],
    [1.66964749888244, 0.07471154842060, 0.60577953503101, -2.91755756410343],
    [-1.80239712831031, -2.49341344701535, -1.21269580460859, 0.63697168155683],
    [-0.10716966568517, 2.75267120678938, -0.07025953390857, 1.09203646858404],
    [2.44668966574209, 0.85048239994608, -1.68082429645875, -0.70834338694479],
    [-2.43407895861333, -2.25884986980141, -1.90930185722340, -0.42081492023166],
    [2.76343366857922, 0.88548289726443, -1.31290735661431, -0.41316436770368],
]
w_altStrip1loose_lst = [
    [1.43992606656847, -0.05619784922874, -2.15140440193585, -2.10600903386511],
    [-1.54358856800673, -3.08869091860330, -1.96798072556556, -2.06625384725094],
    [-1.55856424581210, 3.02409064259246, -2.41985045381817, -2.72582917346856],
    [1.80692688316605, 0.06969774723236, -2.08401442305972, 2.87194957415454],
    [1.81372049365452, 0.09798751944209, -1.93997733091386, 2.71448851582135],
    [1.77187318338484, 0.03058925332149, -0.53572747239218, -3.06352760339522],
]
trp_strip1loose_lst = [
    [-1.42370673881736, 3.07884563566485, -0.34007405948430, 0.11354872017568],
    [-1.42370673881736, 3.07884563566485, 1.98277633990881, 0.11354872017568],
    [-1.61524022599291, 2.89343359817915, 2.73743094769173, 2.54758605380157],
    [-1.61524022599291, 2.89343359817915, 0.41458054829862, 2.54758605380157],
    [1.77696445873445, 0.27207282959619, -2.70727784215309, -0.53688158466514],
    [1.77696445873445, 0.27207282959619, 1.25305706563339, -0.53688158466514],
    [2.15190522721759, 0.05270221039482, 2.57186153635740, -3.02286600259236],
    [2.15190522721759, 0.05270221039482, 0.24901113696429, -3.02286600259236],
]
trp_star1loose_lst = [
    [1.71511743293778, 0.46091029884951, -1.07872215277750, -1.42149462636674],
    [1.74467582754345, 0.34742949569036, 1.06159933774891, -0.73897804196354],
    [-0.21536559403382, 2.77888866429552, 2.28100235393140, 2.18546187868338],
    [-0.10374359171627, 2.72002157492297, 0.16227906867730, 1.02816732261647],
]
trp_altStrip_lst = [
    [-0.65714336545885, -2.67883569239305, 2.97613992671755, -1.32647852305955],
    [-1.27849790538431, -2.52651500521736, 0.04139052091744, -2.44875892950612],
]
trp_altStrip1loose_lst = [
    [-0.64286429494377, -2.68492913437112, 2.97939817536370, -1.31160148963693],
    [-0.64286429494377, -2.68492913437112, -0.98093673242278, -1.31160148963693],
    [1.36422237041008, 0.45544887027459, -2.10183788817659, -1.29308897804171],
    [1.36422237041008, 0.45544887027459, 1.85849701960988, -1.29308897804171],
    [-0.18031581396188, 2.81061412090296, 2.53831794851741, 2.29878069656079],
    [-0.18031581396188, 2.81061412090296, -1.42201695926907, 2.29878069656079],
    [1.78761504059563, -0.14450886689923, 3.10936638961216, 2.81034048901031],
    [1.78761504059563, -0.14450886689923, 0.78651599021905, 2.81034048901031],
]
E0_1_V2_1 = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: par_strip1loose_lst,
	trisAlt.strip_I: par_strip_lst,
	trisAlt.strip_II: par_strip_lst,
	trisAlt.star: par_star_lst,
	trisAlt.star_1_loose: par_star1loose_lst,
	trisAlt.alt_strip_I: par_altStrip_lst,
	trisAlt.alt_strip_II: par_altStrip_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip1loose_lst,
	trisAlt.strip_I: tri_strip_lst,
	trisAlt.strip_II: tri_strip_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.star_1_loose: tri_star1loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: str_strip1loose_lst,
	trisAlt.strip_I: str_strip_lst,
	trisAlt.strip_II: str_strip_lst,
	trisAlt.star: str_star_lst,
	trisAlt.star_1_loose: str_star1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip1loose_lst,
	trisAlt.star_1_loose: w_star1loose_lst,
	# interesting: why does star_star list work for w - strip?
	trisAlt.alt_strip_I: str_star_lst,
	trisAlt.alt_strip_II: str_star_lst,
	trisAlt.alt_strip_1_loose: w_altStrip1loose_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_1_loose: trp_strip1loose_lst,
	trisAlt.star_1_loose: trp_star1loose_lst,
	trisAlt.alt_strip_I: trp_altStrip_lst,
	trisAlt.alt_strip_II: trp_altStrip_lst,
	trisAlt.alt_strip_1_loose: trp_altStrip1loose_lst,
    },
}

###############################################################################
par_star1loose_lst = [
    [-1.39118276937848, 3.14159265358979, 0.10352945501819, 2.92943718229921],
    [0.17248019555758, 0.0, -3.03806319857160, 2.92943718229921],
    [0.22305477085979, 0.0, -2.33542093019165, -0.73712082998592],
    [-1.34060819407627, 3.14159265358979, 0.80617172339814, -0.73712082998592],
    [1.71694851861461, 0.0, -0.51090367139466, 1.93835620101551],
    [0.15328555367855, 3.14159265358979, 2.63068898219513, 1.93835620101551],
    [0.42942081062573, 3.14159265358979, 2.98712089144311, -0.60333226745193],
    [1.99308377556179, 0.0, -0.15447176214668, -0.60333226745193],
    [2.93674981953536, 0.0, -0.54322707636664, -1.75844050842324],
    [1.37308685459930, 3.14159265358979, 2.59836557722315, -1.75844050842324],
    [1.38735320320669, 3.14159265358979, 2.36574675405118, 0.60364661189702],
    [2.95101616814275, 0.0, -0.77584589953862, 0.60364661189702],
]
tri_strip1loose_lst = [
    [0.46234991251830, 0.0, -1.90076821596660, -2.16789389371567],
    [-1.10131305241776, 3.14159265358979, 1.24082443762320, -2.16789389371567],
    [-0.59612887715852, 3.14159265358979, 1.03515107143910, 2.98975489850679],
    [0.96753408777754, 0.0, -2.10644158215069, 2.98975489850679],
]
tri_star1loose_lst = [
    [0.20763612024081, 0.00000000000000, 2.58240640079077, -0.62879571512244],
    [-1.35602684469525, 3.14159265358979, -0.55918625279902, -0.62879571512244],
    [-1.58105070042457, 3.14159265358979, -0.34912884202852, -2.76066023117237],
    [-0.01738773548851, 0.00000000000000, 2.79246381156128, -2.76066023117237],
    [0.26650581964714, 0.00000000000000, -1.91785957600867, 2.85285594390327],
    [-1.29715714528892, 3.14159265358979, 1.22373307758112, 2.85285594390328],
    [-1.75560777454484, 3.14159265358979, 1.04700565864788, -2.38539096216850],
    [-0.19194480960878, 0.00000000000000, -2.09458699494192, -2.38539096216850],
    [2.51773049449087, 0.00000000000000, 0.36890129663975, 1.72546216879706],
    [0.95406752955481, 3.14159265358979, -2.77269135695005, 1.72546216879706],
    [1.35290040334943, -3.14159265358979, -2.59393893094806, 0.56303500001937],
    [2.91656336828549, 0.00000000000000, 0.54765372264173, 0.56303500001937],
]
str_strip1loose_lst = [
    [-1.01277131847062, -2.72867121149941, -2.89290602448826, 0.97521223427453],
    [-1.19159532974672, -2.96895093033635, -3.04448501559777, -0.16430948565302],
    [1.40599063449638, 0.78256187588913, -1.07314125333176, -0.64219833356973],
    [1.38315684245602, 0.84959499009939, -1.27784565191688, 1.50288719555073],
    [-1.01722756475366, -2.40888632555235, -0.95353836156794, -2.56409543923980],
    [-0.86082569655800, 2.37407127655383, 1.03487963518131, 2.93210584741909],
    [-1.33822655181642, -2.21951730995809, -1.67681989080525, -2.37167703028127],
    [-0.74586512269254, 2.28106070222314, 1.31911371481642, -2.26636594579268],
    [-0.41397891323728, 2.21181731510118, 1.80680286163218, -0.79212842677136],
    [0.37244685132842, 2.22941922737570, 1.58735495691905, -2.70062398872207],
]
str_star1loose_lst = [
    [1.39711957850658, -0.19014758599437, 3.03432651610620, 1.53191220501174],
    [-1.42016236702872, 2.79448700058241, 0.36448052501505, -1.10643174808017],
    [-1.61331997273431, 2.92386108982546, 0.22184752916210, -3.03060617330005],
    [1.63193363377049, -0.09628286316101, 3.08793729698167, 2.47901219420828],
    [2.54831631110330, 0.23556163602522, -0.24079696368291, 2.00352729005607],
    [2.94965964018349, 0.34006743283470, -0.35636112325136, 1.05511205418691],
]
str_altStrip1loose_lst = [
    [0.89695368656134, -0.34998571472174, 2.93586520381194, 2.82801335673796],
    [0.89695368656134, -0.34998571472174, 2.93586520381194, 0.05249759243641],
    [-1.25480313410577, -3.00643400894817, -3.06596660131336, 2.53383743199315],
    [-1.25480313410577, -3.00643400894817, -3.06596660131336, -0.24167833230841],
    [1.42766520298158, 0.72540280163456, -0.93757077653169, -1.01655875105017],
    [1.42766520298158, 0.72540280163456, -0.93757077653169, 1.75895701325138],
    [-1.35082368757793, -2.25415260498480, -1.43764549583135, -2.18637284052888],
    [-1.35082368757793, -2.25415260498480, -1.43764549583135, 1.32129670234916],
    [-0.86293620874085, 2.37594494748782, 1.03025757880585, 2.92274956532587],
    [-0.86293620874085, 2.37594494748782, 1.03025757880585, -0.58491997755217],
    [-0.16612063241714, 2.21109593798810, 1.87263381711617, 0.90770766194403],
    [-0.16612063241714, 2.21109593798810, 1.87263381711616, -1.86780810235752],
]
w_strip1loose_lst = [
    [-1.19608961283158, -2.97466495776053, 3.13764876132704, 0.17812440300939],
    [-0.90958014213243, -2.77241013824599, -1.60130677852981, -1.80851740697812],
    [-0.86696871724066, -2.78399784160912, -1.30018635690060, -2.06043232989735],
    [-0.86399009081373, 2.67151402484948, 1.12962158980958, 1.92397101515185],
    [-0.77086904604614, -3.07859795578820, -1.66507266060441, -2.48825634520728],
    [0.77472410837704, 0.03091827768228, -1.81527878896315, -2.41163668739100],
    [1.37373862812142, 0.73680752449435, -1.55431263763982, 0.78057950530529],
    [-1.48317746509811, 2.72088913165697, 2.67936753072782, -2.16015822065886],
    [1.61463437112588, 0.06681174360256, 0.89409716748469, -1.97335170416241],
    [1.64064783912449, -0.23930520055876, 2.87589511972363, -2.59726366709595],
    [1.71348171075580, -0.23844288119617, 0.73288630127803, 2.55222127246610],
    [1.74793784987441, -0.12037533542546, 2.33040316560929, 1.29719363534792],
    [-1.75982867626546, 2.87387050071859, 0.79877363394114, 2.47191311811314],
    [-0.52377112627585, 2.28253027900488, 1.36214466093076, 0.75072531180610],
    [-0.20702654941146, 3.02300292891757, -0.83285204926166, 2.19863075552538],

    [-2.27566382877385, 3.13072596844265, 1.79077650149709, 2.56793564499433],
]
w_star1loose_lst = [
    [1.05400503081183, 0.23590329985519, -2.95573005020688, 2.60657707495924],
    [1.15206216063759, -0.38688481871286, 1.63735096899936, 1.74335715706850],
    [-1.26076690406154, 2.92015110848705, 1.80199569522596, 1.88668274598404],
    [1.34103317914007, -0.28413685708542, -2.72032518436576, -1.28631243961216],
    [1.39828286050144, -0.32396122559340, -2.95058307504352, -2.30084222766825],
    [1.46008310869503, -0.09791368366614, 1.67088319667740, -2.52102675783341],
    [0.55609366607792, -0.38990271827926, 2.53046049305475, 0.62625854228876],
    [-1.50892614313461, 2.79478151900614, -0.12797496057977, 1.07271856444976],
    [-1.60758863997461, 2.76845913723729, 0.17063855737367, 2.23564838925871],
    [-1.80300430463100, -3.08258928787139, -2.73790037494533, -0.66450483515157],
    [-0.49744763617704, 2.34822876577594, 1.25125005986518, 1.05550726125974],
    [1.99135666008910, 0.22295954117122, -0.47071497895422, 0.42535677887581],
    [2.19080837944430, -0.07228949914770, 1.86842846122195, -2.76887119316753],
    [2.19817342992050, -0.03522311746512, 1.80232255125001, 2.41290507226504],
    [-2.20288868741045, 3.09754182013889, 1.69486281120639, 2.53262047393135],
    [-2.20416331036316, 3.08393503070419, 1.67259464812791, -2.69309704536118],
    [2.29712877396533, -0.03710830892907, 0.18005858228472, 3.05743958064325],
    [-2.40304932962653, -3.09539247446181, 2.98992073784526, 3.03586372989103],
    [-2.51831407966995, -2.47786587152504, -1.77401981417911, 1.17189196304372],
    [-2.58885764330102, -2.97306730136168, 2.82587024923369, 2.71521015694871],
    [-2.60683512720967, -2.86465976417276, 2.73387802594472, 1.22235556344606],
    [-2.59344433659653, -2.41679607429597, -2.02706790872815, 1.17637885922570],
    [3.09623552402223, 0.36534913049863, 0.09598333714329, -2.08419731268976],
    [3.09707372814595, 0.36814369230455, 0.09379753723565, -1.06533608109065],
]
w_altStrip1loose_lst = [
    [0.89744039340996, -0.35001383606798, 2.96445484868266, -0.05190656780310],
    [-1.26170501785210, -3.01532263289615, 3.06818224902410, 0.26286972465580],
    [-1.48574014716755, 2.72181163476957, 2.67681499573325, -2.16210966761138],
    [-1.54981502398728, 2.78218891725362, 0.74356970012465, 2.28575686413625],
    [-1.06643574195978, -2.39436841348094, -0.73380048825423, -0.71095304148922],
    [-0.91744310870824, 2.40659321152046, 0.72971111685667, 0.55223591540206],
    [1.61708851731289, 0.06704939958037, 0.89196710859842, -1.96887913964429],
    [1.72400347167354, -0.23540980653090, 0.73390215055203, 2.55866491553516],
    [1.79163316209468, -0.20112960982787, 2.77546952844785, -2.67732548075002],
    [-0.22628526104343, 3.02349472317329, -0.84188326694177, 2.25921997237036],
]
trp_star1loose_lst = [
    [-1.39415433502915, 3.08411020844085, -2.97201399253521, 0.10395025097232],
    [-1.50424842691434, 2.73889416261265, 0.27797416290576, 0.93788154927913],
    [-1.61246857736237, 2.88361044376570, -0.65438357120790, 2.52049612335852],
    [-1.61852863893463, 2.91219723083721, -0.84967128021018, 2.59802402895275],
    [1.78354444236476, 0.26012384888043, -1.65742479557482, -0.50875932934211],
    [1.99967945408165, 0.08499495838346, 0.66458475745236, -0.15436322316319],
    [2.11603253763936, 0.05711638367948, -1.06101098298760, -3.01286360058464],
    [2.26594733285595, 0.04825983421391, -0.52766602527200, -3.03291914787503],
    [3.02393787393410, 0.30997940890371, 1.88988893687253, -0.63223084546419],
    [3.09236831209118, 0.40006391672164, 1.31084839875184, -2.02737632687563],
    [3.09645849323024, 0.40843022782295, -0.20460397441541, -1.98614650372343],
    [3.09711507150192, 0.40984649760789, -0.20100503006556, -0.96997534601223],
]
E0_V2_1_1 = {
    Heptagons.foldMethod.parallel: {
	trisAlt.star_1_loose: par_star1loose_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip1loose_lst,
	trisAlt.star_1_loose: tri_star1loose_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: str_strip1loose_lst,
	trisAlt.star_1_loose: str_star1loose_lst,
	trisAlt.alt_strip_1_loose: str_altStrip1loose_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip1loose_lst,
	trisAlt.star_1_loose: w_star1loose_lst,
	trisAlt.alt_strip_1_loose: w_altStrip1loose_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.star_1_loose: trp_star1loose_lst,
    },
}

###############################################################################
par_strip1loose_lst = [
    [0.12225322067129, 0.69387894107539, -2.88053472967089, -1.45280978307591],
    [0.12225322067129, 0.69387894107539, -2.88053472967089, 0.97566810142913],
    [-1.07984572197554, 2.44771371251441, -1.12669995823187, -1.45280978307591],
    [-1.07984572197554, 2.44771371251441, -1.12669995823187, 0.97566810142912],
    [0.48335670145490, 2.44771371251441, 1.97180858498190, -1.30050950037236],
    [0.48335670145490, 2.44771371251441, 1.97180858498190, 2.55419792230220],
    [0.06950290992006, 2.44771371251441, 0.86221483369683, -1.41338954086409],
    [0.06950290992007, 2.44771371251441, 0.86221483369683, 2.44131788181046],
    [1.27160185256690, 0.69387894107539, -0.89161993774218, -1.41338954086409],
    [1.27160185256690, 0.69387894107539, -0.89161993774218, 2.44131788181046],
    [1.68545564410173, 0.69387894107539, 0.21797381354288, -1.30050950037236],
    [1.68545564410173, 0.69387894107539, 0.21797381354288, 2.55419792230220],
    [1.49675849139279, 2.44771371251441, 1.28491599136484, 1.50243663512320],
    [1.49675849139279, 2.44771371251441, 1.28491599136484, -0.92604124938183],
    [2.69885743403962, 0.69387894107539, -0.46891878007418, -0.92604124938183],
    [2.69885743403962, 0.69387894107539, -0.46891878007418, 1.50243663512320],
]
tri_strip1loose_lst = [
    [-0.37928429671679, 2.44771371251441, 1.63783736001017, 1.72622010185906],
    [0.82281464593004, 0.69387894107539, -2.89151317573040, 1.72622010185906],
    [0.11022350887753, 0.69387894107539, -2.84229918041937, -0.91434765817114],
    [-1.09187543376930, 2.44771371251441, 1.68705135532119, -0.91434765817114],
    [0.94391492047937, 2.44771371251441, -1.92220600091181, -2.72838529395174],
    [2.14601386312620, 0.69387894107539, -0.16837122947279, -2.72838529395174],
    [1.51335412963349, 2.44771371251441, -1.87003941254405, 0.92215961894658],
    [2.71545307228033, 0.69387894107539, -0.11620464110503, 0.92215961894658],
]
str_strip1loose_lst = [
    [0.90938085507918, 0.32295001468545, 2.64146163656557, 1.29778033624525],
    [-0.44889107896484, -3.05793871625589, 0.59575392812649, -2.33485916430800],
    [-1.38303671175224, 3.01849378242885, 0.86106001173748, 1.10167235999014],
    [-1.48151855373452, -2.69584729603914, 2.69364169462649, -3.09903947223988],
    [1.69629398076091, 0.22374771941711, 2.59223738839205, -1.52341130589158],
    [-2.07032159890003, -2.67876206602606, 2.70023724845637, -0.63146497908096],
    [2.15044833177779, 0.58322560053740, 0.10744578299633, -2.86224209697337],
    [2.71733340339973, 0.61790249899028, 0.07435853062213, 0.83037219968364],
]
w_strip1loose_lst = [
    [1.10713485445923, 0.52820920031821, -2.42091198756144, -1.93393850109572],
    [-1.11395735377263, -2.84548771148193, -2.24231457265646, 0.79191801880226],
    [-1.48614173357344, 3.04378744072978, 0.04280380224849, -1.54184824709211],
    [1.51602186420882, 0.62327518777236, -2.37031425869634, 2.87507563442106],
    [-1.50571641962446, -2.47095796587753, -1.31662749840993, 1.98450108194400],
    [-1.53425425498131, 3.05411294280689, -0.02752381808024, -1.86555096547658],
    [-1.74452483748385, -3.11779218364675, 1.77613299894768, -1.54876369555925],
    [-1.42191378178894, -2.37828986497837, 2.59675045549764, 2.55096122436042],
    [-0.48448060162531, 2.73785107465815, -1.09555942584286, 1.56078682745576],
    [1.96447424887365, 0.92312201834975, -1.81023014709597, -1.89939522139056],
    [-2.17470177695049, -2.10615638897751, -1.98209085955046, -1.62392837767447],
    [-2.11680941628265, -2.68879086575807, 2.34299125835240, 0.66174647076185],
    [-1.63906670520815, -1.80783242525998, -3.11723056074154, -0.51147254126480],
    [2.31124227698559, 0.33626189210468, 1.17667872914247, 2.34739847501893],
    [2.60002312397484, 1.10954969516761, -0.23709566648279, -1.12417372144493],
    [2.78204458899094, 0.60161329305726, 0.55536515367213, -0.94443472554990],
]
trp_strip1loose_lst = [
    [-1.48458902744661, 3.06264264498730, -0.09778045984232, -1.49525292823386],
    [-1.48458902744661, 3.06264264498730, 2.33069742466271, -1.49525292823386],
    [-1.53400699507894, 3.04162410216041, 0.06228725415324, -1.89469371313258],
    [-1.53400699507894, 3.04162410216041, 2.49076513865827, -1.89469371313258],
    [-0.41888595072874, 2.87622188415809, 2.16555190849606, -2.50384639692356],
    [-0.41888595072874, 2.87622188415809, -1.68915551417849, -2.50384639692356],
    [1.92413991370260, 0.11912677222050, 0.62071225503069, 2.00529427131700],
    [1.92413991370260, 0.11912677222050, 3.04919013953572, 2.00529427131700],
    [1.69911904761694, 0.55866370571148, -2.65653452868805, 0.23098088216485],
    [1.69911904761694, 0.55866370571148, 1.19817289398650, 0.23098088216485],
    [-0.30494332537338, 2.15800870707983, -2.50385290641923, 1.67006543569022],
    [-0.30494332537338, 2.15800870707983, 1.35085451625533, 1.67006543569021],
    [-0.23122542412225, 2.13139152283837, 1.25093325732569, 1.31210426032710],
    [-0.23122542412225, 2.13139152283837, -2.60377416534886, 1.31210426032710],
    [0.74861132948876, 2.13437846603140, -0.82748004091455, 1.39385504576876],
    [0.74861132948876, 2.13437846603140, 3.02722738176000, 1.39385504576876],
    [2.61836909961036, 1.01111196662302, -1.85766051314265, -1.25760093374114],
    [2.61836909961036, 1.01111196662302, 0.57081737136239, -1.25760093374114],
    [2.73259432482610, 0.94615739973059, -1.39808487912054, -0.62841892332507],
    [2.73259432482610, 0.94615739973059, 1.03039300538449, -0.62841892332507],
]
par_stripI_lst = [
    [-1.15663781737806, 2.75448476809546, -0.60432651389549, -2.19521925860017],
    [-0.80659177867112, 2.03808496138506, -1.74848266577818, 0.75631842380775],
    [0.42167356237853, 2.52170753143251, 1.96011306343140, -1.16825810611008],
    [0.04598536181671, 2.61958622645388, 1.24888537091174, 2.23910719497082],
    [1.61270897507922, 0.89606006012612, 0.59474532287193, 2.72025417450416],
    [1.63216482331373, 0.45148184556249, -0.43452810248445, 2.24088432235416],
    [0.27006645284509, 2.09916095597863, 0.26487872604964, 2.82448753508300],
    [0.65532847315762, 1.60994140204340, -0.36585112032954, -2.25595846450244],
    [1.04602993716140, 2.77059999799276, 1.26074886782191, 2.52748158825316],
    [2.32254819379568, 1.58048692940713, 0.74234494088218, 0.28406772970136],
]
tri_stripI_lst = [
    [0.17322760910108, 0.52816572632161, -2.66421719525793, -1.09653175684486],
    [0.44145650182396, 1.17753270631135, 3.00637892768655, 1.29985097463931],
    [2.15676029301398, 0.63581007425306, -0.10722803069921, -2.76229277736973],
    [2.34822452224474, 1.54534025533632, -0.81158843987649, 0.21360131904630],
]
str_stripI_lst = [
    [-1.69469223033859, -2.81545091101837, 3.07759797886767, -3.11876190826836],
    [-0.65401046167570, -2.92225114949815, 0.78378759397295, 3.06096029040826],
    [-1.34670102499062, -2.96014568032701, 1.30739719275517, 1.35213144032670],
    [-1.73436847338764, -2.17087739423450, -2.15984561283064, -1.81112462645538],
    [-1.98948751358294, -2.43415805034885, -1.29228981767738, -0.08573515181275],
    [1.13848034484004, 0.78386691378724, 2.05918061715487, 2.61303520722430],
    [1.72028783692950, 0.48588941814384, 2.14699129544268, -1.61169314850972],
    [-1.93711972768091, -2.61790005318965, 2.38680340170369, -0.04005144737414],
    [2.15815083877965, 0.56685744429681, 0.07084376666839, -2.84870652579343],
    [2.37798494531353, 1.11364718747900, -1.22917081893469, 1.56088649173066],
    [2.48633239689723, 0.94540034464520, -1.73463560250190, 0.39637445685289],
    [2.48307360436641, 0.95751049935994, 0.46119047525417, -0.42060979143946],
]
w_stripI_lst = [
    [-1.20923223943648, -2.99489146824019, -3.07992230227868, 1.72950878826735],
    [-0.96637945414647, -3.02223593394684, -0.42242834915502, -2.83666358731558],
    [-0.91618510052716, -3.02058383229777, -1.84305158800258, 0.85860005032824],
    [1.26121675018085, 0.63755121891627, -2.26000816751621, -2.31662335316445],
    [1.43659913186291, 0.53524545498485, -1.16537015091756, -0.89188093603281],
    [1.47052682907049, 0.52342921546217, -2.52526275430773, 2.94888290227805],
    [1.70252846785878, 0.48620988811775, 0.09583272630281, -1.61853913158935],
    [-0.70356638482104, -2.96031791995631, -0.82192790967290, 2.03120519761172],
    [-1.66874671867916, -2.82967950650614, 2.17524566520695, -1.19649740444147],
    [-1.98952564847624, -2.43438760175267, -1.33927563220531, 0.08690448622949],
    [-1.85920657421151, -2.24675202003894, -1.65145007241601, -2.66147413099916],
    [-1.60139178783618, -2.11734409575131, 2.75716151894722, 1.60610879206981],
    [-1.34907033119340, -2.06311784241679, 2.77049955963223, -1.27393453801974],
    [-1.93713132606163, -2.61788410590217, 2.36457201791967, 0.03951089818417],
    [2.17287958153031, 0.57270717598033, 0.89478548403793, 1.93761196249870],
    [2.48776390818408, 0.93902119821687, -1.53256793750914, -0.39382224968378],
    [2.44046479441927, 1.04243261677994, -1.38589419533384, 2.06495953823255],
    [2.39413479825188, 1.09769541958693, 0.05166185175111, -1.68377847569275],
]
trp_stripI_lst = [
    [-0.79885004672239, 3.01796344851730, 0.98465653767958, -3.05723350047068],
    [1.70207553512659, 0.53794940577428, -0.27316856381485, -1.49791620885681],
    [1.78333666736963, 0.26048788850156, 1.24974119413679, 1.27931571310058],
    [0.09136809491768, 2.60825270009332, -2.75622335976918, -1.71559918248902],
    [0.25446037722864, 1.96518068347290, 3.09498538893698, 2.61840807799458],
    [0.33838462647700, 1.93798573475950, -2.75434897789329, 2.64840270006685],
    [0.28588821851998, 1.95493947513814, -2.95494093855809, 0.21502660611871],
    [0.61353295092960, 1.85324782598966, 2.52031049079321, -0.34376333108011],
    [0.99734875314199, 1.84817562123964, -1.53752950863274, 2.09770968194548],
    [0.81032103676872, 2.07756477441794, -3.09267837679596, 1.50369018464590],
    [2.01962587484520, 1.27276053432601, -2.17103290718477, -1.88651617881251],
    [2.39207616437914, 1.12247852377749, -0.12274311530942, -1.63157250124240],
]
tri_stripII_lst = [
    [-1.01737401097694, 2.60813921835496, 0.91764171185396, 1.60205187822206],
    [0.48393194675488, 0.69822055524781, 3.13951845149989, 1.62314484638842],
    [-0.64401596851308, -2.70416628463456, -0.38486088835850, -1.37212318563846],
    [0.33267295635061, 2.46083646152159, -2.38712083553965, 1.11526694951064],
    [0.55852224688630, -0.01254215131929, -3.00869525983564, -0.52911961859599],
    [0.12757817118075, -2.73348892322932, -2.04539841799930, 1.44282964733681],
    [0.52916328188241, 2.35497549636710, -1.76539388256549, -0.45976903825554],
    [1.24490779016187, 1.40972258702415, -1.51720479229362, 0.48190675011860],
    [1.44145961334775, 1.59731332450493, -1.77227825070393, -2.97293474753723],
    [1.58751503255142, 0.45313005004236, 0.06668546460330, 0.76550570073051],
    [1.03984523211018, 0.94112881502226, 0.58965675514451, 0.82663293702224],
    [1.14545626032932, 0.85688460754755, 1.09541434446754, -0.46124061444038],
    [1.42231025701177, 2.24256368163085, -2.37752900025352, 1.93427708732772],
    [1.32687111673674, 2.43063094753470, -1.25602788487500, -1.83321604321878],
]
str_stripII_lst = [
    [-0.78053141946536, -2.99570446025960, -1.60343851344905, -1.56807688591542],
    [-0.83393747543676, -3.00982151386803, 2.81728349711352, 1.52627642015672],
    [-1.08868395991062, -3.01472175968785, -2.85907644809972, -0.81777292283974],
    [-1.19735572875199, -2.99731307949639, -0.45191835657782, 2.43260995354393],
    [-1.26811292098399, -2.98149362642679, 2.42642221031516, -2.39707395196388],
    [1.29819380927096, 0.60872379630468, 2.93470781713635, 1.42888947277278],
    [1.22615619186577, 0.66996757456470, -1.61408555258134, 1.86862659142871],
    [-0.68311200996583, -2.94655345281659, 0.26106228848495, -1.70383494448256],
    [-0.61538600339513, -2.87711429897508, -2.06821083308021, 1.36181628836327],
    [1.27838819046925, 0.62354964955014, 0.65836255116915, -1.80304880469213],
    [1.15321217440087, 0.76016260588130, -1.16973594813709, -1.34412714669268],
    [-1.52264510120854, -2.89816755172666, 1.54973224067983, 0.98947529592358],
    [1.58772840243170, 0.49626410159664, -0.04514494366605, 0.82170036354948],
    [1.68116232529465, 0.48701132124144, -2.45923417989481, -2.48156561853797],
    [-1.11631590155628, -2.06318293812101, -1.94016618712076, -1.95862579067088],
    [-1.44035102641149, -2.07640379632201, -1.33932992679444, -1.49672508369055],
    [1.73989841996627, 0.48589006044740, 0.86470010650408, 2.47804496504529],
    [2.03352555232685, 0.52646664568420, 1.60949485752424, -1.03396369957593],
]
par_star_lst = [
    [-0.68958505376778, -2.76968386296299, 1.86767827366885, -2.88338526702208],
    [-0.19704139133793, -2.46999750625282, 2.58479630851572, -0.94597526034129],
    [-1.08450321517136, -2.79008093770969, 0.72626261351303, -2.97607461546121],
    [-1.09311820926396, 2.73143685756900, -0.64021128226658, -2.35964770916536],
    [-1.22772702260215, -2.79074175080854, 0.72769771959172, -2.50224214645601],
    [-1.23821854077151, 2.73195331453200, -0.64071803589592, -1.88350101264938],
    [0.63325519828989, -1.37812698971903, 2.99497540090949, -2.02588127837568],
    [1.08225145305230, -0.98200247015339, -2.93354959681450, 2.34573735366904],
    [1.18986030461613, -0.31361590622981, -1.53025059215822, 2.94051275323095],
    [0.52091537040053, -2.03941606442424, 2.51547856528530, -1.46817867948017],
    [1.67884126829060, -0.30530724663815, -0.89030309765033, -1.10532918550673],
    [1.59278687242615, 0.90443394452586, 0.69420736165576, 2.80698021470783],
    [1.74230086051974, 0.54296167096703, 0.57909026065008, -1.98743632033887],
    [0.90745910529246, 1.09793619133409, -1.98195600307874, 1.65676103711334],
    [0.61445205337854, 1.54060780290158, -1.55995989161926, 2.12018714965725],
    [1.31554990202793, -3.08349112307088, 2.27526285092640, -0.60007527499206],
]
tri_star_lst = [
    [-0.23373296122987, -0.55594518756284, -1.98739995035178, -2.40413230554456],
    [0.38242013446232, 1.49571173157434, 2.51001099472990, 1.22181407546159],
    [0.50230694454077, 2.60226514243842, -1.73855816994044, 2.62543482115873],
    [0.52698279932435, 2.56788025520183, -1.69750201579985, 2.76966902822150],
    [2.10966954507588, 0.50651073062026, 0.06676673449595, 2.13648693681326],
    [2.39607343848661, 1.36235918251898, -0.73589587699332, -1.48028884710069],
]
str_star_lst = [
    [-0.91589802404375, -3.02056484251599, 1.17108415813975, -2.19091468916873],
    [1.42399394796772, 0.54016466981517, 2.05533493468359, 2.16389032427703],
    [-1.58074557757525, -2.87304896688528, 1.03851085513358, 1.74685074836150],
    [-1.71562857207735, -2.80340771794741, 2.98649026499947, -1.66538746288745],
    [-1.92401802354729, -2.63495149294605, -0.59807417921847, -0.87535091822463],
    [-1.95019624889000, -2.33996423558124, -1.57236345445538, -2.08635448944943],
    [1.96271225656963, 0.50993408429128, 2.50529354570260, -2.19419831692853],
    [-1.95519781884080, -2.34757586931489, 2.19668035994285, 1.88820859896404],
    [2.10971552832648, 0.54931571303118, -0.04335922657434, 2.19116270208617],
    [2.41882782076087, 0.72987396529881, -2.36529852074749, 1.26478404439799],
    [2.47873856781382, 0.82355380484766, -2.07455463666904, 1.93777716611647],
    [2.48011879995847, 0.82733714035075, 0.45623239735137, -2.06554799210332],
]
par_star1loose_lst = [
    [0.28592011827865, -0.69387894107539, 3.09143636100216, -2.71188621517368],
    [0.18803380976514, 0.69387894107539, -2.88749208488769, -1.62052323157127],
    [0.45405009105009, -0.69387894107539, 3.10704033025853, 3.04899727273445],
    [0.34459144908216, 0.69387894107539, -2.87175335362880, -2.15053581637946],
    [-0.74804885159674, -2.44771371251441, 1.35320555881951, 3.04899727273445],
    [-0.85750749356467, 2.44771371251441, -1.11791858218978, -2.15053581637946],
    [-0.91617882436819, -2.44771371251441, 1.33760158956314, -2.71188621517368],
    [-1.01406513288169, 2.44771371251441, -1.13365731344867, -1.62052323157128],
    [0.46052924938527, 2.44771371251441, 2.54546793689485, -2.17920354097321],
    [0.47708107305485, 2.44771371251441, 2.10746495201891, 2.69050553339465],
    [0.63369573819627, -2.44771371251441, 2.20840940460009, 1.77448811366243],
    [1.66262819203210, 0.69387894107539, 0.79163316545584, -2.17920354097321],
    [1.67918001570168, 0.69387894107539, 0.35363018057989, 2.69050553339465],
    [0.85196300238034, -2.44771371251441, 2.44952685035663, -1.06371656716116],
    [1.83579468084310, -0.69387894107539, -2.32094113114048, 1.77448811366243],
    [2.05406194502717, -0.69387894107539, -2.07982368538394, -1.06371656716116],
]
tri_star1loose_lst = [
    [-0.43125127814040, 2.44771371251441, 1.68325817459060, 1.70173709081924],
    [0.77084766450643, 0.69387894107539, -2.84609236114997, 1.70173709081924],
    [0.03102014369597, 0.69387894107539, -2.89484099019153, -0.87286692360127],
    [-1.17107879895087, 2.44771371251441, 1.63450954554904, -0.87286692360127],
    [0.66264076915239, 2.44771371251441, -1.63206077612450, 3.05095057262358],
    [1.86473971179922, 0.69387894107539, 0.12177399531452, 3.05095057262358],
    [1.72509556898506, 2.44771371251441, -1.67672580511727, -1.09194700589958],
    [2.92719451163189, 0.69387894107539, 0.07710896632175, -1.09194700589958],
]
str_star1loose_lst = [
    [1.01493931987430, 0.20792227819919, 2.58369622380282, 1.03726159996458],
    [-1.07518268398442, 2.88149575124286, 1.10864210347682, 1.05195637041297],
    [-1.38358483767242, -2.63216173615413, 2.71747033705777, 3.11572683807216],
    [1.73318859450485, 0.24150615740506, 2.60158169003025, -1.57107949146829],
    [-0.54489993265932, 2.91559741244488, 1.03721863599674, -1.47216733157956],
    [1.86791174327418, 0.77002167939870, -0.07829776707182, -3.13070944772586],
    [-2.39112972556759, -2.37073541661095, 2.79504213636196, 0.62095797887423],
    [2.92841358287758, 0.74305283843872, -0.05002968303372, -1.02899488200683],
]
w_star1loose_lst = [
    [1.09574070958781, 0.26500023074799, -2.91661507960410, -1.54909623883287],
    [1.38872487223182, 0.42561461188358, -2.67523161365479, -2.79682895804256],
    [-1.32814111875092, 2.97500396636666, 1.80184703113570, -1.11908316907244],
    [-1.43082176594623, 3.04173579721585, -1.29242069140972, 1.15458770663968],
    [-0.80680577194440, 3.09827292570566, -0.17131653203191, -1.83445208854327],
    [1.63339999921737, 0.11489860952314, -1.47899781154695, -1.17088372207103],
    [-1.78250897547765, -3.07395223977292, -2.69615747080221, 1.61059253815935],
    [-1.88613490128023, -3.03888614916184, 1.87011382641303, -1.80986979483709],
    [1.88305877535027, 0.24618484402225, -0.84826638748156, -0.96721086542062],
    [-0.34617340333099, 2.68214862759433, 0.35760859551122, -1.02075534185638],
    [-2.14542244838647, -2.62573454701778, -1.18850789551290, 2.37401870589994],
    [-2.46149008539053, -2.51045355535500, -1.64569969791563, -2.60648779908613],
    [2.47896336309380, 0.65491193885921, -1.78893325284532, -2.42402665700907],
    [2.96686320263532, 0.71688947498566, -1.03410151255899, 1.52024603429730],
]
trp_star1loose_lst = [
    [-0.78649746378032, 3.01430352199864, 0.40713463198701, -2.04493401724684],
    [-1.50305911797114, 3.05584644058371, 2.17127927287668, -1.40222007575167],
    [-1.60599646946989, 2.86641404988939, 1.98853216328653, -2.52970023242215],
    [1.76147820232352, 0.30416977458701, -1.79480654094653, 2.60368606821930],
    [1.71004106418890, 0.48826469574679, -2.80602094086300, 0.34762728397366],
    [1.86218453147863, 0.16306937225800, 1.44670531374975, 1.02333385715912],
    [1.97305011402432, 0.09518524991419, 0.81186974090741, 1.86071705545642],
    [-0.04233015466530, 2.68605029106863, -2.27430570756327, -2.95623712481192],
]
par_altStripI_lst = [
    [0.93235951493660, 0.72372151864305, 2.56783879675975, -2.83036368662647],
    [0.65343249380698, 1.11196883513919, 2.71065816749484, 1.45804586653840],
    [-0.22444785652215, 2.63290095206682, -1.42494564063612, 0.91699469560520],
    [1.63232154390588, 0.44872705230104, -0.44027661545402, 2.23781834249796],
    [0.40544041846683, 2.61111881099352, 2.01723178714257, -0.93499108692349],
    [0.00934815744441, 2.73787914123438, 1.38347125428724, 2.10392400613493],
    [0.04529196362528, 2.73551768313800, -0.47679188327397, -2.11139129905827],
    [0.00047569079884, 1.97367400171120, -0.54248283723197, -2.83271174242179],
    [0.31733061328373, 1.56197403620559, -1.01527824266632, -1.72184617268033],
    [1.79108584982727, 1.27564868024581, 1.29153813279165, -2.72304260156107],
]
w_altStripI_lst = [
    [-1.19648577352609, -2.99748665667221, -1.19945426461143, -1.55688486323900],
    [-0.91757795100252, -3.02067433121422, -1.81850739618377, 0.81331927366838],
    [-0.83384618856572, -3.00980285202462, 2.06013715826094, -2.45802655869658],
    [1.22705278383294, 0.66906704452967, -2.29869861681453, -2.15901730927780],
    [-0.78130278150096, -2.99595883404414, -0.85936980394137, 2.42438438861222],
    [-0.62820880302471, -2.89425694117056, -0.03705434286553, -0.98778439572318],
    [1.15045059137959, 0.76442106217636, 3.08881105192015, 0.94530689545095],
    [-1.26971546566335, -2.98109734925569, -3.12249935930051, 1.60114835250369],
    [1.43808385848214, 0.53468557256964, -1.18084858102971, -0.85988758663492],
    [-1.40396125789407, -2.94215776513784, 1.27456324208272, 1.68635463136730],
    [-1.55472877827555, -2.88461188158057, -2.70673412653069, -1.35828137807177],
    [1.27674069234322, 0.62484492146359, 1.35182298692499, 2.21698333926686],
    [1.68181580743144, 0.48697994372000, -1.69237269780443, 1.49716954075662],
    [1.73936625835471, 0.48588521179432, 0.09937838111179, -1.50146194622529],
    [1.98251412565111, 0.51412020866828, 1.90853617789823, -1.87047347836038],
    [2.07005945691694, 0.53673836596287, -0.44693045192620, 1.25475167810159],
]
trp_altStripI_lst = [
    [-0.62696375021451, -2.91141502953410, 0.08606365260813, -1.02383802612725],
    [1.73903247178861, 0.53802293372583, -0.27356817216912, -1.37764940278508],
    [-0.04760547253253, 3.01283367141860, 2.18080275660070, -0.40978769654882],
    [0.39852363344342, 2.16473882869789, 2.80809437163965, 2.15183456047024],
    [0.59277830030022, 1.93913098001573, -2.15437157222490, 2.54705955603774],
    [2.03952266087498, 0.38478181913646, 0.84070652870125, 0.78109026571592],
    [2.01439369712743, 1.28228969119544, -2.17783977158222, -1.85571765491239],
    [1.95470401803539, 1.54837590486478, -1.53252581081280, -0.98190052706106],
]
tri_altStripII_lst = [
    [0.40270525358650, 1.45181290288377, 2.97708255245145, 0.85644694759943],
    [0.25478450050787, 1.64178628168285, -2.95725054118427, -0.46334122839523],
    [0.24825380053695, 2.68366569772834, -2.50223225962262, 1.07945432115169],
    [1.34177543255798, 0.41340207169338, 0.24723858109403, -2.67801341102955],
    [-0.13952661937567, 2.71054514065693, 1.72151479392349, -1.12934305808528],
    [-0.23302791636089, 2.61603343918579, 1.32896681817622, 0.45798878930746],
    [0.43980877513983, 2.59239119195960, -1.88171247042030, -0.45804408192233],
    [1.58914614126389, 0.43085460737428, 0.10038478128808, 0.77923194093304],
    [0.99140610744762, 0.65203466631192, 1.72976793768637, -0.46989947077417],
    [0.91031862710328, 0.75216686325296, 1.19676543233845, 0.69791550991208],
    [1.25700457383808, 1.94629939540893, -2.25230422660772, 0.66206201214466],
    [1.47932380169601, 1.71027374096578, -1.88817278306368, 3.01143353356653],
]
str_altStripII_lst = [
    [-1.03704909170173, -3.01965661898873, 2.03972546854489, 2.84348581231862],
    [-1.09030646747277, -3.01452924873002, -2.83580072336937, -0.86166066361482],
    [-0.81988024322310, -3.00674319164608, -1.62881113382712, -1.68164792476503],
    [1.32601959825105, 0.59002881569222, -1.46680404152452, 2.06741928402088],
    [1.34264839793135, 0.57992746594516, -0.19454064146691, -2.44241734379946],
    [1.18320003800362, 0.71847314518718, -1.02458406381196, -1.57916782064474],
    [-1.37234389966674, -2.95234347753016, 2.36945149680713, -2.05126232060088],
    [-0.57141807044195, -2.78423344282764, -0.68347703253737, 0.93797472475830],
    [-0.55513564784289, -2.62207462046909, -0.77339105439584, 0.08290071540128],
    [1.53720657330482, 0.50560901223438, 1.35145746331136, -2.89775732618666],
    [1.58950853227809, 0.49599403955605, -0.06871398150029, 0.86406859716885],
    [-0.60342260033481, -2.42392181496092, 2.14350425968248, 0.01575343507416],
    [-0.88038498159212, -2.13042863988274, 2.46013887090472, -2.56513487383536],
    [-1.34959608366129, -2.06317415041635, -1.50162597536304, -1.64925025366023],
    [-1.49217451089679, -2.08708066892695, -1.65937097247751, 1.21525315781844],
    [1.88213907738570, 1.37845853844507, -1.73976071675307, 1.60586837864567],
    [1.90432383536704, 0.49952390395872, 0.88952100506795, 1.91097934336174],
    [1.98785976508351, 1.34123835210253, -1.58007295011113, -1.08940883724291],
]
w_altStripII_lst = [
    [-0.56611501784458, -2.76460690626153, -1.58412232329082, 2.98679223566905],
    [-0.75196448619709, -2.98504868616511, 0.30868879787647, -1.44842607301671],
    [-0.55516999575707, -2.62156274483442, -0.73025535086173, -0.07817780733515],
    [-1.47292943957328, -2.91773251598271, 0.74449579986858, -3.08085028903702],
    [1.10587521910332, 0.84748617271958, -2.17437513558933, -2.22156354266863],
    [-0.60341964553356, -2.42392870238212, 2.15231298773685, -0.01587876585967],
    [-1.03710477503754, -2.07642758252941, -3.02069719453328, 2.27565893070684],
    [1.80068739256834, 0.48816254028127, 2.66812994063586, 2.62619319548644],
    [1.05601231240292, 1.03988690352211, 0.68700122971616, 2.39854410475970],
    [1.06472171813628, 1.18785861283361, 1.54445499804737, -0.67178528683743],
]
par_altStrip1loose_lst = [
    [-0.24586272685784, 2.44771371251441, -1.95720015379669, -2.77768510189918],
    [-0.24586272685784, 2.44771371251441, -1.95720015379669, 1.07702232077537],
    [0.95623621578899, 0.69387894107539, 2.57215038194388, 1.07702232077537],
    [0.95623621578899, 0.69387894107539, 2.57215038194388, -2.77768510189918],
    [-0.24586272685784, 2.44771371251441, 0.19684448775406, 2.77768510189918],
    [0.95623621578899, 0.69387894107539, -1.55699028368496, 2.77768510189918],
    [0.95623621578899, 0.69387894107539, -1.55699028368496, -1.07702232077537],
    [-0.24586272685784, 2.44771371251441, 0.19684448775406, -1.07702232077537],
    [0.66725358606974, 2.44771371251441, 2.14023859844081, -1.07702232077537],
    [0.66725358606975, 2.44771371251441, 2.14023859844081, 2.77768510189918],
    [1.86935252871658, 0.69387894107539, 0.38640382700179, 2.77768510189918],
    [1.86935252871658, 0.69387894107539, 0.38640382700179, -1.07702232077537],
    [0.66725358606975, 2.44771371251441, -0.01380604310994, -2.77768510189918],
    [1.86935252871658, 0.69387894107539, -1.76764081454896, -2.77768510189918],
    [1.86935252871658, 0.69387894107539, -1.76764081454895, 1.07702232077537],
    [0.66725358606974, 2.44771371251441, -0.01380604310994, 1.07702232077537],
]
w_altStrip1loose_lst = [
    [-1.11505758830214, -2.84452913459571, -2.24099747024426, 0.78514693256502],
    [1.07192452453169, 0.56530721508571, -2.46988449986632, -1.77382003610770],
    [1.02191425979898, 0.42287986758065, 1.87937557022567, 1.55377629758328],
    [-1.20710626210711, -2.59302281736404, -1.16353578168923, -3.09980198799288],
    [-1.22278064091890, -2.57577250860499, 2.38720658530494, 3.06565567806873],
    [-1.46522468483244, -3.08372936364430, 1.08596543911686, 1.82301390097534],
    [-1.45029443917296, -2.35575649350327, -1.08743759349832, -2.50159977406452],
    [-1.44709559533871, -2.35901246289456, 2.63571222185040, 2.51128466780480],
    [-0.45153911439009, 2.69642573392321, -0.70130395492975, 0.88014790387225],
    [2.02685016076771, 0.22125831323650, 2.36003859703283, -2.35590430440692],
    [2.04930013764841, 0.23317535143873, -0.17234123113923, 2.34037385875529],
    [2.01486690127710, 1.02785836921710, -2.36114963067110, 1.89805998626932],
    [-1.49459054413048, -2.10184989458137, 2.55317142518991, 1.56257917977615],
    [1.99235160103086, 0.58400187934936, -0.49727738783039, 1.01084887075880],
]
trp_altStrip1loose_lst = [
    [-1.12738308388625, 2.78648720459420, 0.93898126309534, -2.72699866590629],
    [-1.12738308388625, 2.78648720459420, -2.91572615957922, -2.72699866590629],
    [-0.26463422535081, 2.35106949524800, -2.86644821350731, 0.18740225816185],
    [-0.26463422535081, 2.35106949524800, 0.98825920916724, 0.18740225816185],
    [2.05025180148160, 0.16020631612541, 2.78061454602679, 2.18088953781715],
    [2.05025180148160, 0.16020631612541, 0.35213666152175, 2.18088953781715],
    [1.92153536587186, 0.44669537040934, 0.86900117580148, 0.41752335302783],
    [1.92153536587186, 0.44669537040934, -2.98570624687307, 0.41752335302783],
    [0.34669987524916, 2.21943398787636, 2.64358010987918, 2.03467002647830],
    [0.34669987524916, 2.21943398787636, -1.21112731279537, 2.03467002647830],
    [0.66723327917965, 2.45533813559815, 2.78380443115686, -0.01367907968087],
    [0.66723327917965, 2.45533813559815, -1.07090299151769, -0.01367907968087],
]
AllEquilateralTris = {
    Heptagons.foldMethod.parallel: {
	trisAlt.strip_1_loose: par_strip1loose_lst,
	trisAlt.strip_I: par_stripI_lst,
	trisAlt.star: par_star_lst,
	trisAlt.star_1_loose: par_star1loose_lst,
	trisAlt.alt_strip_I: par_altStripI_lst,
	trisAlt.alt_strip_1_loose: par_altStrip1loose_lst,
    },
    Heptagons.foldMethod.triangle: {
	trisAlt.strip_1_loose: tri_strip1loose_lst,
	trisAlt.strip_I: tri_stripI_lst,
	trisAlt.strip_II: tri_stripII_lst,
	trisAlt.star: tri_star_lst,
	trisAlt.star_1_loose: tri_star1loose_lst,
	trisAlt.alt_strip_II: tri_altStripII_lst,
    },
    Heptagons.foldMethod.star: {
	trisAlt.strip_1_loose: str_strip1loose_lst,
	trisAlt.strip_I: str_stripI_lst,
	trisAlt.strip_II: str_stripII_lst,
	trisAlt.star: str_star_lst,
	trisAlt.star_1_loose: str_star1loose_lst,
	trisAlt.alt_strip_II: str_altStripII_lst,
    },
    Heptagons.foldMethod.w: {
	trisAlt.strip_1_loose: w_strip1loose_lst,
	trisAlt.strip_I: w_stripI_lst,
	trisAlt.star_1_loose: w_star1loose_lst,
	trisAlt.alt_strip_I: w_altStripI_lst,
	trisAlt.alt_strip_II: w_altStripII_lst,
	trisAlt.alt_strip_1_loose: w_altStrip1loose_lst,
    },
    Heptagons.foldMethod.trapezium: {
	trisAlt.strip_1_loose: trp_strip1loose_lst,
	trisAlt.strip_I: trp_stripI_lst,
	trisAlt.star_1_loose: trp_star1loose_lst,
	trisAlt.alt_strip_I: trp_altStripI_lst,
	trisAlt.alt_strip_1_loose: trp_altStrip1loose_lst,
    },
}
