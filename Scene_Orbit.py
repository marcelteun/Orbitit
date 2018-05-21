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

import os
import wx
import wx.lib.colourselect as wxLibCS
import math
import rgb
import Geom3D
import Geom4D
import GeomGui
import GeomTypes
import Scenes3D
import isometry
import orbit
from OpenGL.GL import *

Title = 'Create Polyhedron by Orbiting'

LOG_DBG  = 1
LOG_INFO = 2
LOG_WARN = 3
LOG_ERR  = 4

LOG_TXT  = {
    LOG_DBG:    'DEBUG',
    LOG_INFO:   'INFO',
    LOG_WARN:   'WARNING',
    LOG_ERR:    'ERROR',
}

LOG_STDOUT_LVL = LOG_INFO # or WARN?
LOG_BAR_LVL    = LOG_INFO

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
        this.name = shape.name
        this.canvas = canvas
        kwargs['title'] = Title
        wx.Frame.__init__(this, *args, **kwargs)
        this.setDefaultColours()
        this.nrOfCols = 1
        this.colSelection = None
        this.finalSymSetup = None
        this.stabSymSetup = None
        this.statusBar = this.CreateStatusBar()
        this.panel = wx.Panel(this, -1)
        this.mainSizer = wx.BoxSizer(wx.VERTICAL)
        this.mainSizer.Add(
                this.createControlsSizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.setDefaultSize((582, 741))
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.mainSizer)
        this.Show(True)
        this.panel.Layout()
        this.importDirName = '.'

    def setDefaultColours(this):
        c = lambda rgbCol: [c*255 for c in rgbCol]
        this.cols = [
                c(rgb.gold),       c(rgb.forestGreen),
                c(rgb.red4),       c(rgb.deepSkyBlue),
                c(rgb.khaki4),     c(rgb.midnightBlue),
                c(rgb.chocolate1), c(rgb.burlywood1),
                c(rgb.chocolate4), c(rgb.yellow),
                c(rgb.aquamarine), c(rgb.indianRed1)
            ]

    def createControlsSizer(this):
        ctrlSizer = wx.BoxSizer(wx.VERTICAL)

        this.showGui = []

        facesSizer = wx.StaticBoxSizer(
            wx.StaticBox(this.panel, label = 'Face(s) Definition'),
            wx.VERTICAL
        )
        ctrlSizer.Add(facesSizer, 0, wx.EXPAND)

        dataSizer = wx.BoxSizer(wx.HORIZONTAL)

        #VERTICES
        this.showGui.append(wx.StaticBox(this.panel, label = 'Vertices'))
        bSizer = wx.StaticBoxSizer(this.showGui[-1])
        this.showGui.append(GeomGui.Vector3DSetDynamicPanel(
            this.panel, relExtraSpace = 3
        ))
        this.__VsGuiIndex = len(this.showGui) - 1
        bSizer.Add(this.showGui[-1], 1, wx.EXPAND)
        dataSizer.Add(bSizer, 1, wx.EXPAND)

        # FACES
        this.showGui.append(wx.StaticBox(this.panel, label = 'Faces'))
        bSizer = wx.StaticBoxSizer(this.showGui[-1])
        this.showGui.append(
            GeomGui.FaceSetDynamicPanel(this.panel, 0, faceLen = 3)
        )
        this.__FsGuiIndex = len(this.showGui) - 1
        bSizer.Add(this.showGui[-1], 1, wx.EXPAND)
        dataSizer.Add(bSizer, 1, wx.EXPAND)
        facesSizer.Add(dataSizer, 0, wx.EXPAND)

        # Import
        this.showGui.append(wx.Button(this.panel, wx.ID_ANY, "Import"))
        this.panel.Bind(wx.EVT_BUTTON, this.onImport,
                id = this.showGui[-1].GetId())
        facesSizer.Add(this.showGui[-1], 0)

        # Rotate Axis
        # - rotate axis and set angle (button and float input)
        this.rotateSizer = GeomGui.AxisRotateSizer(
            this.panel,
            this.on_rot,
            min_angle=-180,
            max_angle=180,
            initial_angle=0
        )
        facesSizer.Add(this.rotateSizer)

        # SYMMETRY
        this.showGui.append(
            GeomGui.SymmetrySelect(this.panel,
                'Final Symmetry',
                onSymSelect   = lambda a: this.onSymmetrySelect(a),
                onGetSymSetup = lambda a: this.onGetFinalSymSetup(a)
            )
        )
        this.__FinalSymGuiIndex = len(this.showGui) - 1
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)
        if this.colSelection == None:
            this.colSelection = [None for i in range(this.showGui[-1].length)]
            this.finalSymSetup = this.colSelection[:]
            this.stabSymSetup = this.colSelection[:]

        # Stabiliser
        this.showGui.append(
            GeomGui.SymmetrySelect(this.panel,
                'Stabiliser Symmetry',
                this.showGui[
                    this.__FinalSymGuiIndex
                ].getSymmetryClass(applyOrder = True).subgroups,
                onGetSymSetup = lambda a: this.onGetStabSymSetup(a)
            )
        )
        this.__StabSymGuiIndex = len(this.showGui) - 1
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        this.showGui.append(wx.Button(this.panel, wx.ID_ANY, "Apply Symmetry"))
        this.panel.Bind(
            wx.EVT_BUTTON, this.onApplySymmetry, id = this.showGui[-1].GetId())
        ctrlSizer.Add(this.showGui[-1], 0, wx.EXPAND)

        this.showGui[this.__FinalSymGuiIndex].SetSelected(0)
        this.onSymmetrySelect(
                this.showGui[this.__FinalSymGuiIndex].getSymmetryClass()
            )

        this.ctrlSizer = ctrlSizer
        return ctrlSizer

    def addColourGui(this):
        try:
            this.colSizer.Clear(True)
        except AttributeError:
            this.colGuiBox = wx.StaticBox(this.panel, label = 'Colour Setup')
            this.colSizer = wx.StaticBoxSizer(this.colGuiBox, wx.VERTICAL)
            this.ctrlSizer.Add(this.colSizer, 0, wx.EXPAND)
        this.orbit = orbit.Orbit((
            this.showGui[this.__FinalSymGuiIndex].GetSelected(),
            this.showGui[this.__StabSymGuiIndex].GetSelected()
        ))
        #print 'addColourGui check sub-groups'
        nrOfColsChoiceList = [
            '%d (based on %s)' % (p['index'], p['class'].__name__)
            for p in this.orbit.higherOrderStabiliserProps
        ]
        nrOfColsChoiceList.extend([
            '%d (based on %s)' % (p['index'], p['class'].__name__)
            for p in this.orbit.lowerOrderStabiliserProps
        ])
        #print 'nrOfColsChoiceList', nrOfColsChoiceList
        this.colGuis = []
        this.colGuis.append(
            wx.Choice(this.panel, wx.ID_ANY, choices = nrOfColsChoiceList)
        )
        this.colSizer.Add(this.colGuis[-1], 0, wx.EXPAND)
        this.panel.Bind(wx.EVT_CHOICE,
            this.onNrColsSel, id = this.colGuis[-1].GetId())
        this.colAlternative = this.colSelection[
            this.showGui[this.__FinalSymGuiIndex].getSelectedIndex()
        ][
            this.showGui[this.__StabSymGuiIndex].getSelectedIndex()
        ]
        this.colGuis[-1].SetSelection(this.colAlternative[0])
        this.__nrOfColsGuiId = len(this.colGuis)-1
        this.onNrColsSel(this.colGuis[-1])

    def onGetFinalSymSetup(this, symIndex):
        try:
            return this.finalSymSetup[symIndex]
        except TypeError:
            print 'Note: ignoring error at onGetFinalSymSetup: 1st time = ok'
            return None

    def onGetStabSymSetup(this, symIndex):
        finalSymId = this.showGui[this.__FinalSymGuiIndex].getSelectedIndex()
        try:
            return this.stabSymSetup[finalSymId][symIndex]
        except TypeError:
            print 'Note: ignoring error at onGetStabSymSetup: 1st time = ok'
            return None

    def onSymmetrySelect(this, sym):
        finalSymGui = this.showGui[this.__FinalSymGuiIndex]
        stabSyms = sym.subgroups
        i = finalSymGui.getSelectedIndex()
        # initialise stabiliser setup before setting the list.
        if this.stabSymSetup[i] == None:
            this.stabSymSetup[i] = [None for x in stabSyms]
        this.showGui[this.__StabSymGuiIndex].setList(stabSyms)
        nrStabilisers = this.showGui[this.__StabSymGuiIndex].length
        if this.colSelection[i] == None:
            this.colSelection[i] = [[0, 0] for j in range(nrStabilisers)]
            this.stabSymSetup[i] = [None for j in range(nrStabilisers)]

    def onApplySymmetry(this, e):
        print this.GetSize()
        Vs = this.showGui[this.__VsGuiIndex].get()
        Fs = this.showGui[this.__FsGuiIndex].get()
        if Fs == []:
            this.statusText('No faces defined!', LOG_ERR)
            return
        finalSymGui   = this.showGui[this.__FinalSymGuiIndex]
        finalSym      = finalSymGui.GetSelected()
        finalSymIndex = finalSymGui.getSelectedIndex()
        stabSymGui    = this.showGui[this.__StabSymGuiIndex]
        stabSym       = stabSymGui.GetSelected()
        stabSymIndex  = stabSymGui.getSelectedIndex()
        this.finalSymSetup[finalSymIndex] = finalSym.setup             # copy?
        this.stabSymSetup[finalSymIndex][stabSymIndex] = stabSym.setup # copy?
        try:
            this.shape = Geom3D.SymmetricShape(Vs, Fs,
                    finalSym = finalSym, stabSym = stabSym, name = this.name
                )
        except isometry.ImproperSubgroupError:
            this.statusText(
                'Stabiliser not a subgroup of final symmetry!', LOG_ERR)
            if e != None:
                e.Skip()
            return
        this.FsOrbit = this.shape.getIsometries()['direct']
        this.FsOrbitOrg = True
        this.shape.recreateEdges()
        this.updateOrientation(
            this.rotateSizer.get_angle(), this.rotateSizer.get_axis())
        this.canvas.panel.setShape(this.shape)
        updated0 = this.showGui[this.__FinalSymGuiIndex].isSymClassUpdated()
        updated1 = this.showGui[this.__StabSymGuiIndex].isSymClassUpdated()
        # Note the functions above need to be called to update the latest
        # status. I.e. don't call them in the or below, because the second will
        # not be called if the first is true.
        if (updated0 or updated1):
            this.addColourGui()
        else:
            this.onNrColsSel(this.colGuis[this.__nrOfColsGuiId])
        this.panel.Layout()
        this.statusText('Symmetry applied: choose colours!', LOG_INFO)
        try:
            tst = this.cols
        except AttributeError:
            this.cols = [(255, 100, 0)]
        if e != None:
            e.Skip()

    def statusText(this, txt, lvl = LOG_INFO):
        txt = '%s: %s' % (LOG_TXT[lvl], txt)
        if lvl >= LOG_STDOUT_LVL:
            print txt
        if lvl >= LOG_BAR_LVL:
            this.statusBar.SetStatusText(txt)

    def updateOrientation(this, angle, axis):
        if axis == GeomTypes.Vec3([0, 0, 0]):
            rot = GeomTypes.E
            this.statusText(
                'Rotation axis is the null-vector: applying identity',
                LOG_INFO
            )
        else:
            rot = GeomTypes.Rot3(
                axis=axis,
                angle=Geom3D.Deg2Rad * angle
            )
        try:
            this.shape.setBaseOrientation(rot)
        except AttributeError:
            this.statusText(
                'Apply symmetry first, before pulling the slide-bar',
                LOG_WARN
            )

    def on_rot(this, angle, axis):
        this.updateOrientation(angle, axis)
        this.canvas.panel.setShape(this.shape)

    def onNrColsSel(this, e):
        try:
            this.selColSizer.Clear(True)
        except AttributeError:
            this.selColSizer = wx.BoxSizer(wx.VERTICAL)
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
            nextPrevColSizer.Add(wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND)
            this.colGuis.append(
                wx.Button(this.panel, wx.ID_ANY, "Reset Colours"))
            this.panel.Bind(
                wx.EVT_BUTTON, this.onResetCols, id = this.colGuis[-1].GetId())
            nextPrevColSizer.Add(this.colGuis[-1], 0, wx.EXPAND)
            this.colSizer.Add(nextPrevColSizer, 0, wx.EXPAND)

        colDivNr = e.GetSelection()
        this.colAlternative[0] = colDivNr
        l0 = len(this.orbit.higherOrderStabiliserProps)
        if colDivNr < l0:
            this.colFinalSym = this.orbit.final
            this.colIsoms = this.orbit.higherOrderStabiliser(colDivNr)
            nrOfCols = this.orbit.higherOrderStabiliserProps[colDivNr]['index']
        else:
            this.colFinalSym = this.orbit.altFinal
            this.colIsoms = this.orbit.lowerOrderStabiliser(colDivNr - l0)
            nrOfCols = this.orbit.lowerOrderStabiliserProps[colDivNr - l0]['index']
            # now the FsOrbit might contain isometries that are not part of the
            # colouring isometries. Recreate the shape with isometries that only
            # have these:
            if this.FsOrbitOrg:
                finalSym = this.orbit.altFinal
                stabSym = this.orbit.altStab
                Vs = this.shape.getBaseVertexProperties()['Vs']
                Fs = this.shape.getBaseFaceProperties()['Fs']
                this.shape = Geom3D.SymmetricShape(Vs, Fs,
                        finalSym = finalSym, stabSym = stabSym, name = this.name
                    )
                this.FsOrbit = this.shape.getIsometries()['direct']
                this.shape.recreateEdges()
                this.canvas.panel.setShape(this.shape)
                this.FsOrbitOrg = False # and do this only once
        assert len(this.colIsoms) != 0
        this.selColGuis = []
        initColour = (255, 255, 255)
        maxColPerRow = 12
        # Add buttons for choosing individual colours:
        for i in range(nrOfCols):
            try:
                col = this.cols[i]
            except IndexError:
                col = initColour
                this.cols.append(col)
            if i % maxColPerRow == 0:
                selColSizerRow = wx.BoxSizer(wx.HORIZONTAL)
                this.selColSizer.Add(selColSizerRow, 0, wx.EXPAND)
            this.selColGuis.append(
                wxLibCS.ColourSelect(this.panel, wx.ID_ANY, colour = col)
            )
            this.panel.Bind(wxLibCS.EVT_COLOURSELECT, this.onColSel)
            selColSizerRow.Add(this.selColGuis[-1], 0, wx.EXPAND)
        this.nrOfCols = nrOfCols
        # replace invalid index of colour alternative with the last possible
        if this.colAlternative[1] >= len(this.colIsoms):
            this.colAlternative[1] = len(this.colIsoms) - 1
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
        finalSym = this.colFinalSym
        #print 'finalSym', finalSym
        #print 'this.colAlternative', this.colAlternative[1]
        #print 'subGroup', this.colIsoms[this.colAlternative[1]]
        colQuotientSet = finalSym  / this.colIsoms[this.colAlternative[1]]
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
        this.shape.setFaceColors(cols)
        this.statusText('Colour alternative %d of %d applied' % (
                this.colAlternative[1] + 1, len(this.colIsoms)
            ), LOG_INFO
        )
        this.canvas.paint()
        #print 'TODO: gen colour quotientset and compare with face quotient set'

    # move to general class
    def setDefaultSize(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

    def onNextColAlt(this, e):
        this.colAlternative[1] += 1
        if this.colAlternative[1] >= len(this.colIsoms):
            this.colAlternative[1] -= len(this.colIsoms)
        this.updatShapeColours()

    def onResetCols(this, e):
        this.setDefaultColours()
        for i in range(this.nrOfCols):
            this.selColGuis[i].SetColour(this.cols[i])
        this.updatShapeColours()

    def onPrevColAlt(this, e):
        this.colAlternative[1] -= 1
        if this.colAlternative[1] < 0:
            this.colAlternative[1] += len(this.colIsoms)
        this.updatShapeColours()

    def onImport(this, e):
        wildcard = "OFF shape (*.off)|*.off|Python shape (*.py)|*.py"
        dlg = wx.FileDialog(this,
            'New: Choose a file', this.importDirName, '', wildcard, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            this.importDirName  = dlg.GetDirectory()
            print "opening file:", filename
            fd = open(os.path.join(this.importDirName, filename), 'r')
            if filename[-3:] == '.py':
                shape = Geom3D.readPyFile(fd)
                # For Compound derived shapes (isinstance) use merge:
                try:
                    shape = shape.SimpleShape
                except AttributeError:
                    # probably a SimpleShape
                    pass
            else:
                shape = Geom3D.readOffFile(fd, recreateEdges = False)
            fd.close()
            if isinstance(shape, Geom3D.IsometricShape):
                Vs = shape.baseShape.Vs
                Fs = shape.baseShape.Fs
            else:
                #print 'no isometry'
                Vs = shape.Vs
                Fs = shape.Fs
            print 'read ', len(Vs), ' Vs and ', len(Fs), ' Fs.'
            this.showGui[this.__VsGuiIndex].set(Vs)
            this.showGui[this.__FsGuiIndex].set(Fs)
            # With a python file it is possible to set the other properties as
            # well: e.g.
            # finalSym = isometry.S4xI
            # finalSymSetup = [ [1, 0, 0], [0, 0, 1] ]
            # stabSym = isometry.C3xI
            # stabSymSetup = [ [0, 0, 1] ]
            # rotAxis = [1, 1, 1]
            # rotAngle = 30
            #   where the angle is in degrees (floating point)
            if filename[-3:] == '.py':
                fd = open(os.path.join(this.importDirName, filename), 'r')
                ed = {'__name__': 'readPyFile'}
                exec fd in ed
                moreSettings = 0
                keyErrStr = 'Note: KeyError while looking for'
                key = 'finalSym'
                # to prevent accepting keyErrors in other code than ed[key]:
                keyDefined = False
                try:
                    finalSym = ed[key]
                    keyDefined = True
                except KeyError:
                    print keyErrStr, key
                    pass
                if keyDefined:
                    moreSettings += 1
                    this.showGui[this.__FinalSymGuiIndex].SetSelectedClass(
                        finalSym
                    )
                    this.showGui[this.__FinalSymGuiIndex].onSetSymmetry(None)
                    key = 'finalSymSetup'
                    keyDefined = False
                    try:
                        symSetup = ed[key]
                        keyDefined = True
                    except KeyError:
                        print keyErrStr, key
                        pass
                    if keyDefined:
                        moreSettings += 1
                        this.showGui[this.__FinalSymGuiIndex].SetupSymmetry(
                            symSetup
                        )
                key = 'stabSym'
                keyDefined = False
                try:
                    stabSym = ed[key]
                    keyDefined = True
                except KeyError:
                    print keyErrStr, key
                    pass
                if keyDefined:
                    moreSettings += 1
                    this.showGui[this.__StabSymGuiIndex].SetSelectedClass(
                        stabSym
                    )
                    this.showGui[this.__StabSymGuiIndex].onSetSymmetry(None)
                    key = 'stabSymSetup'
                    keyDefined = False
                    try:
                        symSetup = ed[key]
                        keyDefined = True
                    except KeyError:
                        print keyErrStr, key
                        pass
                    if keyDefined:
                        moreSettings += 1
                        this.showGui[this.__StabSymGuiIndex].SetupSymmetry(
                            symSetup
                        )
                if moreSettings > 0:
                    this.onApplySymmetry(None)
                key = 'rotAxis'
                keyDefined = False
                try:
                    axis = ed[key]
                    keyDefined = True
                except KeyError:
                    print keyErrStr, key
                    pass
                if keyDefined:
                    moreSettings += 1
                    this.rotateSizer.set_axis(axis)
                key = 'rotAngle'
                keyDefined = False
                try:
                    angle = ed[key]
                    keyDefined = True
                except KeyError:
                    print keyErrStr, key
                    pass
                if keyDefined:
                    moreSettings += 1
                    this.rotateSizer.set_angle(angle)
                    this.updateOrientation(
                        this.rotateSizer.get_angle(), this.rotateSizer.get_axis())
                fd.close()
            this.name = filename
        dlg.Destroy()

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
