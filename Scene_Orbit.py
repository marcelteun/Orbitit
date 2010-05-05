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
#-------------------------------------------------------------------
#
# $Log$
#
#

import wx
import wx.lib.colourselect as wxLibCS
import math
import rgb
import Geom3D
import Geom4D
import GeomGui
import Scenes3D
import isometry
from OpenGL.GL import *

Title = 'Create Polyhedron by Orbiting'

class Shape(Geom3D.SimpleShape):
    def __init__(this):
        Geom3D.SimpleShape.__init__(this, [], [])
        #this.dbgTrace = True

    def glInit(this):
        Geom3D.SimpleShape.glInit(this)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glEnable(GL_BLEND)
        pass

class CtrlWin(wx.Frame):
    def __init__(this, shape, canvas, *args, **kwargs):
        this.shape = shape
        this.canvas = canvas
        kwargs['title'] = Title
        wx.Frame.__init__(this, *args, **kwargs)
        this.statusBar = this.CreateStatusBar()
        this.panel = wx.Panel(this, -1)
        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
        this.mainSizer.Add(
                this.createControlsSizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.setDefaultSize((437, 609))
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()

    def createControlsSizer(this):
        ctrlSizer = wx.BoxSizer(wx.VERTICAL)

        this.showGui = []

        facesSizer = wx.StaticBoxSizer(
            wx.StaticBox(this.panel, label = 'Face(s) Definition'),
            wx.HORIZONTAL
        )
        ctrlSizer.Add(facesSizer, 0, wx.EXPAND)

        #VERTICES
        this.showGui.append(
            GeomGui.Vector3DSetInput(this.panel, label = 'Vertices'))
        this.__VsGuiIndex = len(this.showGui) - 1
        facesSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        # FACES
        this.showGui.append(
            GeomGui.FacesInput(
                this.panel, label = 'Faces', faceLen = 3, width = 40
            )
        )
        this.__FsGuiIndex = len(this.showGui) - 1
        facesSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        # SYMMETRY
        this.showGui.append(
            GeomGui.SymmetrySelect(this.panel,
                'Final Symmetry',
                onSymSelect = lambda a: this.onSymmetrySeleect(a)
            )
        )
        this.__FinalSymGuiIndex = len(this.showGui) - 1
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        # Stabiliser
        this.showGui.append(
            GeomGui.SymmetrySelect(this.panel,
                'Stabiliser Symmetry',
                this.showGui[
                    this.__FinalSymGuiIndex
                ].getSymmetryClass(applyOrder = True).subgroups,
            )
        )
        this.__StabSymGuiIndex = len(this.showGui) - 1
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        this.showGui.append(wx.Button(this.panel, wx.ID_ANY, "Apply Symmetry"))
        this.panel.Bind(
            wx.EVT_BUTTON, this.onApplySymmetry, id = this.showGui[-1].GetId())
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        this.ctrlSizer = ctrlSizer
        return ctrlSizer

    def addColourGui(this):
        try:
            this.colSizer.Clear(True)
        except AttributeError:
            this.colGuiBox = wx.StaticBox(this.panel, label = 'Colour Setup')
            this.colSizer = wx.StaticBoxSizer(this.colGuiBox, wx.VERTICAL)
            this.ctrlSizer.Add(this.colSizer, 0, wx.EXPAND)
        finalSym = this.showGui[this.__FinalSymGuiIndex].getSymmetryClass(
                applyOrder = True
            )
        stabSym = this.showGui[this.__StabSymGuiIndex].getSymmetryClass(
                applyOrder = True
            )
        this.posColStabSym = []
        this.nrOfCols      = []
        for subSymGrp in finalSym.subgroups:
            if stabSym in subSymGrp.subgroups:
                print subSymGrp, 'can be used as subgroup for colouring'
                this.posColStabSym.append(subSymGrp)
                #print 'addColourGui, finalSym', finalSym
                fo = isometry.order(finalSym)
                assert fo != 0
                po = isometry.order(subSymGrp)
                assert po != 0
                this.nrOfCols.append('%d' % (fo / po))
        this.colGuis = []
        this.colGuis.append(
            wx.Choice(this.panel, wx.ID_ANY, choices = this.nrOfCols)
        )
        this.colSizer.Add(this.colGuis[-1], 0, wx.EXPAND)
        this.panel.Bind(wx.EVT_CHOICE,
            this.onNrColsSel, id = this.colGuis[-1].GetId())
        this.colGuis[-1].SetSelection(0)
        this.__nrOfColsGuiId = this.colGuis[-1]
        this.onNrColsSel(this.colGuis[-1])

    def onSymmetrySeleect(this, sym):
        this.showGui[this.__StabSymGuiIndex].setList(
                this.showGui[this.__FinalSymGuiIndex].getSymmetryClass().subgroups,
            )

    def onApplySymmetry(this, e):
        #print this.GetSize()
        Vs = this.showGui[this.__VsGuiIndex].GetVs()
        Fs = this.showGui[this.__FsGuiIndex].GetFs()
        if Fs == []:
            this.statusBar.SetStatusText(
                "ERROR: No faces defined!"
            )
            return
        finalSym = this.showGui[this.__FinalSymGuiIndex].GetSelected()
        stabSym = this.showGui[this.__StabSymGuiIndex].GetSelected()
        try: fsQuotientSet = finalSym  / stabSym
        except isometry.ImproperSubgroupError:
            this.statusBar.SetStatusText(
                "ERROR: Stabiliser not a subgroup of final symmetry"
            )
            raise

        #print 'fsQuotientSet:'
        #for coset in fsQuotientSet:
        #    print '  - len(%d)' % len(coset)
        #    for isom in coset: print '   ', isom
        this.FsOrbit = [coset.getOne() for coset in fsQuotientSet]
        print 'Applying an orbit of order %d' % len(this.FsOrbit)
        #for isom in this.FsOrbit: print isom
        try:
            tst = this.cols
        except AttributeError:
            this.cols = [(255, 100, 0)]
        this.shape = Geom3D.SymmetricShape(Vs, Fs,
                directIsometries = this.FsOrbit
            )
        this.shape.recreateEdges()
        this.canvas.panel.setShape(this.shape)
        this.addColourGui()
        this.panel.Layout()
        this.statusBar.SetStatusText("Symmetry applied: choose colours")
        e.Skip()

    def onNrColsSel(this, e):
        try:
            this.selColSizer.Clear(True)
        except AttributeError:
            this.selColSizer = wx.BoxSizer(wx.HORIZONTAL)
            this.colSizer.Add(this.selColSizer, 0, wx.EXPAND)
            nextPrevColSizer = wx.BoxSizer(wx.HORIZONTAL)
            this.colGuis.append(
                wx.Button(this.panel, wx.ID_ANY, "Previous Alternative"))
            this.panel.Bind(
                wx.EVT_BUTTON, this.onPrevColAlt, id = this.colGuis[-1].GetId())
            nextPrevColSizer.Add(this.colGuis[-1], 0, wx.EXPAND)
            this.colGuis.append(
                wx.Button(this.panel, wx.ID_ANY, "Next Alternative"))
            this.panel.Bind(
                wx.EVT_BUTTON, this.onNextColAlt, id = this.colGuis[-1].GetId())
            nextPrevColSizer.Add(this.colGuis[-1], 0, wx.EXPAND)
            this.colSizer.Add(nextPrevColSizer, 0, wx.EXPAND)

        id = e.GetSelection()
        colSym = this.posColStabSym[id]
        finalSym = this.showGui[this.__FinalSymGuiIndex].GetSelected()
        this.colIsom = finalSym.realiseSubgroups(colSym)
        assert len(this.colIsom) != 0
        nrOfCols = int(this.nrOfCols[id])
        this.selColGuis = []
        initColour = (255, 255, 255)
        for i in range(nrOfCols):
            try:
                col = this.cols[i]
            except IndexError:
                # TODO: init this.cols with some (12?) nice init colours
                col = initColour
                this.cols.append(col)
            this.selColGuis.append(
                wxLibCS.ColourSelect(this.panel, wx.ID_ANY, colour = col)
            )
            this.panel.Bind(wxLibCS.EVT_COLOURSELECT, this.onColSel)
            this.selColSizer.Add(this.selColGuis[-1], 0, wx.EXPAND)
        this.colAlternative = 0
        this.updatShapeColours()
        this.panel.Layout()

    def onColSel(this, e):
        col = e.GetValue().Get()
        guiId = e.GetId()
        for i, gui in zip(range(len(this.selColGuis)), this.selColGuis):
            if gui.GetId() == guiId:
                #print 'update %d with colour %s.' % (i, col)
                this.cols[i] = col
                this.updatShapeColours()
                break

    def updatShapeColours(this):
        """apply symmetry on colours
        """
        finalSym = this.showGui[this.__FinalSymGuiIndex].GetSelected()
        #print 'finalSym', finalSym
        #print 'close finalSym', finalSym.close()
        #print 'this.colAlternative', this.colAlternative
        print '1 colour has subgroup %s (alt. %d)' % (
            this.posColStabSym[this.__nrOfColsGuiId.GetSelection()],
            this.colAlternative
        )
        colQuotientSet = finalSym  / this.colIsom[this.colAlternative]
        #print '-----colQuotientSet-----------'
        #for isom in colQuotientSet: print isom
        #print '------------------------------'
        #print '--------FsOrbit---------------'
        #for isom in this.FsOrbit: print isom
        #print '------------------------------'
        colPerIsom = []
        for isom in this.FsOrbit:
            for subSet, i in zip(colQuotientSet, range(len(colQuotientSet))):
                if isom in subSet:
                    colPerIsom.append(this.cols[i])
                    break;
        #print 'colPerIsom', colPerIsom
        cols = [
                ([[float(colCh)/255 for colCh in col]], [])
                for col in colPerIsom
            ]
        this.shape.setSymmetricFaceColors(cols)
        this.canvas.paint()
        #print 'TODO: gen colour quotientset and compare with face quotient set'

    # move to general class
    def setDefaultSize(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

    def onNextColAlt(this, e):
        this.colAlternative += 1
        if this.colAlternative >= len(this.colIsom):
            this.colAlternative -= len(this.colIsom)
        this.updatShapeColours()

    def onPrevColAlt(this, e):
        this.colAlternative -= 1
        if this.colAlternative < 0:
            this.colAlternative += len(this.colIsom)
        this.updatShapeColours()

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
