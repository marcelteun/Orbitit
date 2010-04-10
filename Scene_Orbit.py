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
        this.setDefaultSize((475, 550))
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
                this.showGui[this.__FinalSymGuiIndex].getSymmetry().subgroups,
            )
        )
        this.__StabSymGuiIndex = len(this.showGui) - 1
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        this.showGui.append(wx.Button(this.panel, wx.ID_ANY, "Apply"))
        this.panel.Bind(
            wx.EVT_BUTTON, this.onApplySymmetry, id = this.showGui[-1].GetId())
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        return ctrlSizer

    def onSymmetrySeleect(this, sym):
        this.showGui[this.__StabSymGuiIndex].setList(
                this.showGui[this.__FinalSymGuiIndex].getSymmetry().subgroups,
            )

    def onApplySymmetry(this, e):
        Vs = this.showGui[this.__VsGuiIndex].GetVs()
        Fs = this.showGui[this.__FsGuiIndex].GetFs()
        if Fs == []:
            this.statusBar.SetStatusText(
                "ERROR: No faces defined!"
            )
        finalSym = this.showGui[this.__FinalSymGuiIndex].GetSelected()
        stabSym = this.showGui[this.__StabSymGuiIndex].GetSelected()
        try: quotientSet = finalSym  / stabSym
        except isometry.ImproperSubgroup:
            this.statusBar.SetStatusText(
                "ERROR: Stabiliser not a subgroup of final symmetry"
            )
            raise

        #print 'quotientSet:'
        #for coset in quotientSet:
        #    print '  - len(%d)' % len(coset)
        #    for isom in coset: print '   ', isom
        orbit = [coset.getOne() for coset in quotientSet]
        print 'Applying an orbit of order %d' % len(orbit)
        #for isom in orbit: print isom
        this.shape = Geom3D.SymmetricShape(Vs, Fs, directIsometries = orbit)
        this.shape.recreateEdges()
        this.canvas.panel.setShape(this.shape)
        e.Skip()

    # move to general class
    def setDefaultSize(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
