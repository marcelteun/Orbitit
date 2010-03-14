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
from cgkit import cgtypes
from OpenGL.GL import *

Title = 'Create Polyhedron by Orbiting'

class Shape(Geom3D.SimpleShape):
    def __init__(this):
        Geom3D.SimpleShape.__init__(this, [], [])
        #this.dbgTrace = True

    def glInit(this):
        #Geom4D.SimpleShape.glInit(this)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glEnable(GL_BLEND)
        pass

class CtrlWin(wx.Frame):
    def __init__(this, shape, canvas, *args, **kwargs):
        this.shape = shape
        this.canvas = canvas
        kwargs['title'] = Title
        wx.Frame.__init__(this, *args, **kwargs)
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

        this.showGui.append(wx.Button(this.panel, wx.ID_ANY, "Set Vs & Fs"))
        this.panel.Bind(
            wx.EVT_BUTTON, this.onSetVsFs, id = this.showGui[-1].GetId())
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        # SYMMETRY
        isomSizer = wx.StaticBoxSizer(
            wx.StaticBox(this.panel, label = 'Final Symmetry'),
            wx.VERTICAL
        )
        ctrlSizer.Add(isomSizer, 0, wx.EXPAND)
        this.groupsList = [isometry.E, isometry.A4]
        this.groupsStrList = [c.__name__ for c in this.groupsList]
        this.showGui.append(
            wx.ListBox(this.panel, wx.ID_ANY,
                choices = this.groupsStrList,
                style = wx.LB_SINGLE)
        )
        this.__SymmetryGuiIndex = len(this.showGui) - 1
        this.panel.Bind(wx.EVT_LISTBOX_DCLICK,
            this.onApplySymmetry, id = this.showGui[-1].GetId())
        isomSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        this.showGui.append(wx.Button(this.panel, wx.ID_ANY, "Apply"))
        this.panel.Bind(
            wx.EVT_BUTTON, this.onApplySymmetry, id = this.showGui[-1].GetId())
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        return ctrlSizer

    def onSetVsFs(this, e):
        this.shape.setVs(this.showGui[this.__VsGuiIndex].GetVs())
        this.shape.setFs(this.showGui[this.__FsGuiIndex].GetFs())
        this.canvas.paint()
        print 'Vs = ['
        for v in this.shape.Vs: print v
        print ']\n Fs = ['
        for f in this.shape.Fs: print f
        print ']'
        e.Skip()

    def onApplySymmetry(this, e):
        Vs = this.showGui[this.__VsGuiIndex].GetVs()
        Fs = this.showGui[this.__FsGuiIndex].GetFs()
        Id = this.showGui[this.__SymmetryGuiIndex].GetSelection()
        sym = this.groupsList[Id]
        if Id == 0:
            sym = [sym]
        else:
            sym = sym()
        this.shape = Geom3D.SymmetricShape(Vs, Fs, directIsometries = sym)
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
