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

Title = 'Polyhedra with Folded Regular Heptagons S4xI'

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
edge_V2_1_0_1	= 14
edge_V2_1_1_0	= 15
square_12	= 16
edge_0_V2_1_1   = 17

Stringify = {
    dyn_pos:		'Enable Sliders',
    no_o3_tris:		'48 Triangles',
    all_eq_tris:	'All 80 Triangles Equilateral',
    only_o3_tris:	'8 Triangles (O3)',
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
        this.initArrs()
        Heptagons.FldHeptagonShape.__init__(this,
            isometry.S4(
		setup = {
		    'o4axis0': GeomTypes.Vec3([1, 0, 0]),
		    'o4axis1': GeomTypes.Vec3([0, 1, 1]),
		}),
            name = 'FoldedRegHeptS4xI'
        )
	this.edgeAlternative = trisAlt.strip_1_loose
	this.posAngle = math.pi/4

    def getStatusStr(this):
        #angle = Geom3D.Rad2Deg * this.angle
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
        Heptagons.FldHeptagonShape.setV(this)
	#TODO: continue here

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
        #if this.addTriangles:
	#    Fs.extend(this.o3triFs[this.edgeAlternative]) # eql triangles
	#    Es.extend(this.o3triEs[this.edgeAlternative])
        #    colIds.extend([3, 3])
	#    if (not this.onlyO3Triangles):
	#	Fs.extend(this.triFs[this.edgeAlternative])
	#	colIds.extend(this.triColIds[this.edgeAlternative])
	#	Es.extend(this.triEs[this.edgeAlternative])

    def initArrs(this):
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
        this.specPos = {}

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
