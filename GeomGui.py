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
#------------------------------------------------------------------


#import math
import wx
import re
import GeomTypes
import isometry

# TODO:
# - add scroll bar for FacesInput and Vector3DSetInput
# - filter Fs for FacesInput.GetFace (negative nrs, length 2, etc)

class DisabledDropTarget(wx.TextDropTarget):
    def __init__(this, reason = 'for some reason', enableReason = True):
        this.reason = reason
        this.enableReason = enableReason
        wx.TextDropTarget.__init__(this)

#    def OnDropText(this, x, y, text):
#        pass
#        #print this.__class__, 'drop text disabled:', this.reason

    def OnDragOver(this, x, y, d):
        if this.enableReason:
            print this.__class__, 'drag from text disabled 0:', this.reason
        return ''

class IntInput(wx.TextCtrl):
    def __init__(this, *args, **kwargs):
        wx.TextCtrl.__init__(this, *args, **kwargs)
        # Set defaults: style and width if not set by caller
        #this.SetStyle(0, -1, wx.TE_PROCESS_ENTER | wx.TE_DONTWRAP)
        this.SetMaxLength(18)
        this.SetDropTarget(DisabledDropTarget(reason = 'may break string format for floating point'))
        this.Bind(wx.EVT_CHAR, this.onChar)

    def onChar(this, e):
        #print this.__class__, 'onChar'
        k = e.GetKeyCode() # ASCII is returned for ASCII values
        try:
            c = chr(k)
        except ValueError:
            c = 0
            pass
        if c >= '0' and c <= '9':
            e.Skip()
        elif c in ['+', '-']:
            # Handle selected text by replacing it by a '0', otherwise it may
            # prevent from overwriting a sign:
            ss = this.GetStringSelection()
            if not ss == '':
                sel = this.GetSelection()
                if sel[0] == 0:
                    this.Replace(sel[0], sel[1], '0')
                    endSel  = sel[0]+1
                else:
                    this.Replace(sel[0], sel[1], '')
                    endSel  = sel[0]
                this.SetSelection(sel[0], endSel)
                #this.SetInsertionPoint(sel[0])
            s = wx.TextCtrl.GetValue(this)
            # only allow one +, -, or .
            if not c in s:
                # only allow + and - in the beginning
                print ' not c in s:', this.GetInsertionPoint()
                if this.GetInsertionPoint() == 0:
                    # don't allow - if there's already a + and the other way
                    # around:
                    if c == '+':
                        if not '-' in s:
                            e.Skip()
                    else:
                        if not '+' in s:
                            e.Skip()
                else:
                    # allow selected whole string start with -
                    if this.GetSelection()[0] == 0 and c == '-':
                        this.Replace(0, 1, '-0')
                        this.SetSelection(1, 2)
        elif k in [
                wx.WXK_BACK, wx.WXK_DELETE,
            ]:
            ss = this.GetStringSelection()
            # Handle selected text by replacing it by a '0' the field might
            # become completely empty if all is selected
            if not ss == '':
                sel = this.GetSelection()
                this.Replace(sel[0], sel[1], '0')
                this.SetSelection(sel[0], sel[0]+1)
            if len(wx.TextCtrl.GetValue(this)) <= 1:
                # do not allow an empt field, set to 0 instead:
                this.SetValue('0')
                this.SetSelection(0, 1)
            else:
                e.Skip()
        elif k == wx.WXK_CLEAR:
            this.SetValue('0')
        elif k in [
                wx.WXK_RETURN, wx.WXK_TAB,
                wx.WXK_LEFT, wx.WXK_RIGHT,
                wx.WXK_INSERT,
                wx.WXK_HOME, wx.WXK_END
            ]:
            e.Skip()
        else:
            print this.__class__, 'ignores key event with code:', k
        #elif k >= 256:
        #    e.Skip()

    def GetValue(this):
        v = wx.TextCtrl.GetValue(this)
        if v == '': v = '0'
        return int(v)

class FloatInput(wx.TextCtrl):
    # don't except an empty string: [0-9.]
    reFloat = re.compile('[+-]?[0-9]*[0-9.][0-9]*$')
    def __init__(this, *args, **kwargs):
        wx.TextCtrl.__init__(this, *args, **kwargs)
        # Set defaults: style and width if not set by caller
        #this.SetStyle(0, -1, wx.TE_PROCESS_ENTER | wx.TE_DONTWRAP)
        this.SetMaxLength(18)
        this.SetDropTarget(DisabledDropTarget(reason = 'may break string format for floating point'))
        this.Bind(wx.EVT_CHAR, this.onChar)

    def onChar(this, e):
        #print this.__class__, 'onChar'
        k = e.GetKeyCode() # ASCII is returned for ASCII values
        try:
            c = chr(k)
        except ValueError:
            c = 0
            pass
        if c >= '0' and c <= '9':
            e.Skip()
        elif c in ['+', '-', '.']:
            # Handle selected text by replacing it by a '0', otherwise it may
            # prevent from overwriting a sign:
            ss = this.GetStringSelection()
            if not ss == '':
                sel = this.GetSelection()
                if sel[0] == 0:
                    this.Replace(sel[0], sel[1], '0')
                    endSel  = sel[0]+1
                else:
                    this.Replace(sel[0], sel[1], '')
                    endSel  = sel[0]
                this.SetSelection(sel[0], endSel)
                #this.SetInsertionPoint(sel[0])
            s = wx.TextCtrl.GetValue(this)
            # only allow one +, -, or .
            if not c in s:
                if c == '.':
                    e.Skip()
                else:  # '+' or '-'
                    # only allow + and - in the beginning
                    if this.GetInsertionPoint() == 0: 
                        # don't allow - if there's already a + and the other way
                        # around:
                        if c == '+':
                            if not '-' in s:
                                e.Skip()
                        else:
                            if not '+' in s:
                                e.Skip()
                    else:
                        # allow selected whole string start with -
                        if this.GetSelection()[0] == 0 and c == '-':
                            this.Replace(0, 1, '-0')
                            this.SetSelection(1, 2)

        elif k in [
                wx.WXK_BACK, wx.WXK_DELETE,
            ]:
            ss = this.GetStringSelection()
            # Handle selected text by replacing it by a '0' the field might
            # become completely empty if all is selected
            if not ss == '':
                sel = this.GetSelection()
                this.Replace(sel[0], sel[1], '0')
                this.SetSelection(sel[0], sel[0]+1)
            if len(wx.TextCtrl.GetValue(this)) <= 1:
                # do not allow an empt field, set to 0 instead:
                this.SetValue('0')
                this.SetSelection(0, 1)
            else:
                e.Skip()
        elif k == wx.WXK_CLEAR:
            this.SetValue('0')
        elif k in [
                wx.WXK_RETURN, wx.WXK_TAB,
                wx.WXK_LEFT, wx.WXK_RIGHT,
                wx.WXK_INSERT,
                wx.WXK_HOME, wx.WXK_END
            ]:
            e.Skip()
        else:
            print this.__class__, 'ignores key event with code:', k
        #elif k >= 256:
        #    e.Skip()

    def GetValue(this):
        v = wx.TextCtrl.GetValue(this)
        if v == '': v = '0'
        return float(v)

class LabeledIntInput(wx.StaticBoxSizer):
    def __init__(this,
        panel,
        label = '',
        init = "0",
        width = -1,
        orientation = wx.HORIZONTAL,
    ):
        """
        Create a control embedded in a sizer for defining an int.

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        init: initial value used in input
        width: width of the face index fields.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the label - int input.
        """
        this.Boxes = []
        wx.BoxSizer.__init__(this, orientation)
        this.Boxes.append(
            wx.StaticText(panel, wx.ID_ANY, label + ' ',
                style = wx.ALIGN_RIGHT
            )
        )
        this.Add(this.Boxes[-1], 1, wx.EXPAND)
        this.Boxes.append(IntInput(
                panel, wx.ID_ANY, init, size = (width, -1)
            ))
        this.Add(this.Boxes[-1], 0, wx.EXPAND)

    def GetValue(this):
        return this.Boxes[-1].GetValue()

    def Destroy(this):
        for box in this.Boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(this)

class FacesInput(wx.StaticBoxSizer):
    def __init__(this,
        panel,
        label = '',
        nrOfFaces = 0,
        faceLen = 0,
        width = -1,
        orientation = wx.HORIZONTAL,
    ):
        """
        Create a control embedded in a sizer for defining a set of faces

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        nrOfFaces: initialise the input with nrOfFaces amount of faces.
        faceLen: initialise the faces with faceLen vertices. Also the default
                 value for adding faces.
        width: width of the face index fields.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the separate face
                     items.
        """
        this.width = width
        this.panel = panel
        this.orientation = orientation
        this.faceLen = faceLen
        if orientation == wx.HORIZONTAL:
            oppositeOr = wx.VERTICAL
            oriTxt = 'Row'
        else:
            oppositeOr = wx.HORIZONTAL
            oriTxt = 'Column'
        this.Boxes = [wx.StaticBox(panel, label = label)]
        wx.StaticBoxSizer.__init__(this, this.Boxes[-1], oppositeOr)
        this.facesSizer = wx.BoxSizer(oppositeOr)
        this.__f = []
        this.__fLabels = []
        for j in range(nrOfFaces):
            this.addFace(faceLen, faceLen)
        this.Add(this.facesSizer, 0, wx.EXPAND)
        this.Add(wx.BoxSizer(orientation), 1, wx.EXPAND) # stretchable glue
        # Add button:
        addSizer = wx.BoxSizer(orientation)
        this.Boxes.append(IntInput(
                this.panel, wx.ID_ANY, "%d" % faceLen, size = (this.width, -1)
            ))
        this.__faceLenIndex = len(this.Boxes) - 1
        addSizer.Add(this.Boxes[-1], 0, wx.EXPAND)
        this.Boxes.append(wx.Button(panel, wx.ID_ANY, "Add %s" % oriTxt))
        addSizer.Add(this.Boxes[-1], 1, wx.EXPAND)
        this.Add(addSizer, 0, wx.EXPAND)
        panel.Bind(wx.EVT_BUTTON, this.onAdd, id = this.Boxes[-1].GetId())
        # Delete button:
        this.Boxes.append(wx.Button(panel, wx.ID_ANY, "Delete %s" % oriTxt))
        panel.Bind(wx.EVT_BUTTON, this.onRm, id = this.Boxes[-1].GetId())
        this.Add(this.Boxes[-1], 0, wx.EXPAND)

    def addFace(this, fLen):
        faceSizer = wx.BoxSizer(this.orientation)
        j = len(this.__f)
        this.__fLabels.append(
            wx.StaticText(this.panel, wx.ID_ANY, '%d ' % j, style =
                wx.TE_CENTRE | wx.ALIGN_CENTRE_VERTICAL
            )
        )
        faceSizer.Add(this.__fLabels[-1], 0, wx.EXPAND)
        this.__f.append([])
        for i in range(fLen):
            this.__f[-1].append(
                IntInput(this.panel, wx.ID_ANY, "0", size = (this.width, -1))
            )
            faceSizer.Add(this.__f[-1][-1], 0, wx.EXPAND)
        this.facesSizer.Add(faceSizer, 0, wx.EXPAND)

    def onAdd(this, e):
        l = this.Boxes[this.__faceLenIndex].GetValue()
        if l < 1:
            l = this.faceLen
            if l < 1: l = 3
        this.addFace(l)
        this.panel.Layout()
        e.Skip()

    def onRm(this, e):
        if len(this.__f) > 0:
            assert len(this.__fLabels) > 0
            g = this.__fLabels[-1]
            del this.__fLabels[-1]
            g.Destroy()
            v = this.__f[-1]
            del this.__f[-1]
            for g in v:
                g.Destroy()
            this.panel.Layout()
        e.Skip()

    def GetFace(this, index):
        return [
                this.__f[index][i].GetValue()
                    for i in range(len(this.__f[index]))
            ]

    def GetFs(this):
        return [
            this.GetFace(i) for i in range(len(this.__f))
        ]

    def Destroy(this):
        for ctrl in this.__f: ctrl.Destroy()
        for box in this.Boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(this)

class Vector3DInput(wx.StaticBoxSizer):
    def __init__(this,
        panel,
        label = '',
        orientation = wx.HORIZONTAL,
    ):
        """
        Create a control embedded in a sizer for defining a 3D vector

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        length: initialise the input with length amount of 3D vectors.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the separate vector
                     items.
        elementLabels: option labels for the vector items. It is an array
                       consisting of 4 strings On default
                       ['index', 'x', 'y', 'z'] is used.
        """
        this.panel = panel
        this.Boxes = []
        wx.BoxSizer.__init__(this, orientation)
        this.Boxes.append(
            wx.StaticText(this.panel, wx.ID_ANY, label + ' ',
                style = wx.ALIGN_RIGHT
            )
        )
        this.Add(this.Boxes[-1], 1, wx.EXPAND)
        this.__v = []
        for i in range(3):
            this.__v.append(FloatInput(this.panel, wx.ID_ANY, "0"))
            this.Add(this.__v[-1], 0, wx.EXPAND)

    def GetVertex(this):
        return GeomTypes.Vec3([
                this.__v[0].GetValue(),
                this.__v[1].GetValue(),
                this.__v[2].GetValue(),
            ])

    def Destroy(this):
        for ctrl in this.__v: ctrl.Destroy()
        for box in this.Boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(this)

# TODO: use Vector3DInput
class Vector3DSetInput(wx.StaticBoxSizer):
    __defaultLabels = ['index', 'x', 'y', 'z']
    __nrOfColumns = 4
    def __init__(this,
        panel,
        label = '',
        length = 3,
        orientation = wx.HORIZONTAL,
        elementLabels = None
    ):
        """
        Create a control embedded in a sizer for defining a set of 3D vectors

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        length: initialise the input with length amount of 3D vectors.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the separate vector
                     items.
        elementLabels: option labels for the vector items. It is an array
                       consisting of 4 strings On default
                       ['index', 'x', 'y', 'z'] is used.
        """
        this.panel = panel
        if orientation == wx.HORIZONTAL:
            oppositeOr = wx.VERTICAL
            oriTxt = 'Row'
        else:
            oppositeOr = wx.HORIZONTAL
            oriTxt = 'Column'
        this.Boxes = [wx.StaticBox(panel, label = label)]
        wx.StaticBoxSizer.__init__(this, this.Boxes[-1], oppositeOr)
        vectorsSizer = wx.BoxSizer(orientation)
        if elementLabels == None: elementLabels = this.__defaultLabels
        this.columnSizer = []
        # header:
        for i in range(this.__nrOfColumns):
            this.Boxes.append(
                wx.StaticText(panel, wx.ID_ANY, elementLabels[i], style =
                    wx.TE_CENTRE | wx.ALIGN_CENTRE_VERTICAL
                )
            )
            this.columnSizer.append(wx.BoxSizer(oppositeOr))
            this.columnSizer[i].Add(this.Boxes[-1], 1, wx.EXPAND)
            s = 0
            if i != 0: s = 1
            vectorsSizer.Add(this.columnSizer[i], s, wx.EXPAND)
        # vectors:
        this.__v = []
        this.__vLabels = []
        for j in range(length):
            this.addVector()
        this.Add(vectorsSizer, 0, wx.EXPAND)
        this.Add(wx.BoxSizer(orientation), 1, wx.EXPAND) # stretchable glue
        # Add button:
        this.Boxes.append(wx.Button(panel, wx.ID_ANY, "Add %s" % oriTxt))
        this.Add(this.Boxes[-1], 0, wx.EXPAND)
        panel.Bind(wx.EVT_BUTTON, this.onAdd, id = this.Boxes[-1].GetId())
        # Delete button:
        this.Boxes.append(wx.Button(panel, wx.ID_ANY, "Delete %s" % oriTxt))
        panel.Bind(wx.EVT_BUTTON, this.onRm, id = this.Boxes[-1].GetId())
        this.Add(this.Boxes[-1], 0, wx.EXPAND)

    def addVector(this):
        j = len(this.__v)
        this.__vLabels.append(
            wx.StaticText(this.panel, wx.ID_ANY, '%d ' % j, style =
                wx.TE_CENTRE | wx.ALIGN_CENTRE_VERTICAL
            )
        )
        this.columnSizer[0].Add(this.__vLabels[-1], 1, wx.EXPAND)
        this.__v.append([])
        for i in range(1, this.__nrOfColumns):
            this.__v[-1].append(FloatInput(this.panel, wx.ID_ANY, "0"))
            this.columnSizer[i].Add(this.__v[-1][-1], 1, wx.EXPAND)

    def onAdd(this, e):
        this.addVector()
        this.panel.Layout()
        e.Skip()

    def onRm(this, e):
        if len(this.__v) > 0:
            assert len(this.__vLabels) > 0
            g = this.__vLabels[-1]
            del this.__vLabels[-1]
            g.Destroy()
            v = this.__v[-1]
            del this.__v[-1]
            for g in v:
                g.Destroy()
            this.panel.Layout()
        e.Skip()

    def GetVertex(this, index):
        return GeomTypes.Vec3([
                this.__v[index][0].GetValue(),
                this.__v[index][1].GetValue(),
                this.__v[index][2].GetValue(),
            ])

    def GetVs(this):
        return [
            this.GetVertex(i) for i in range(len(this.__v))
        ]

    def Destroy(this):
        for ctrl in this.__v: ctrl.Destroy()
        for ctrl in this.__vLabels: ctrl.Destroy()
        for box in this.Boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(this)

myEVT_VECTOR_UPDATED = wx.NewEventType()
EVT_VECTOR_UPDATED   = wx.PyEventBinder(myEVT_VECTOR_UPDATED, 1)

class VectorUpdatedEvent(wx.PyCommandEvent):
    def __init__(this, evtType, id):
        wx.PyCommandEvent.__init__(this, evtType, id)

    def SetVector(this, vector):
        this.vector = vector

    def GetVector(this):
        return this.vector

class Vector4DInput(wx.StaticBoxSizer):
    __ctrlIdIndex = 0
    __defaultLabels = ['x', 'y', 'z', 'w']
    def __init__(this,
        panel,
        label = '',
        orientation = wx.HORIZONTAL,
        relativeFloatSize = 4,
        elementLabels = None
    ):
        """
        Create a control embedded in a sizer for defining 4D vectors

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the separate vector
                     items.
        relativeFloatSize: it defines the size of the input fields relative to
                           the vector item labels 'x', 'y',..,'z' (with size 1) 
        elementLabels: option labels for the vector items. It is an array
                       consisting of 4 strings On default ['x', 'y', 'z', 'w']
                       is used.
        """
        this.Boxes = [wx.StaticBox(panel, label = label)]
        wx.StaticBoxSizer.__init__(this, this.Boxes[-1], orientation)
        if elementLabels == None: elementLabels = this.__defaultLabels
        this.__vLabel = [
            wx.StaticText(panel, wx.ID_ANY, elementLabels[0], style = wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL),
            wx.StaticText(panel, wx.ID_ANY, elementLabels[1], style = wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL),
            wx.StaticText(panel, wx.ID_ANY, elementLabels[2], style = wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL),
            wx.StaticText(panel, wx.ID_ANY, elementLabels[3], style = wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL)
        ]
        this.__v = [
            FloatInput(panel, wx.ID_ANY, "0"),
            FloatInput(panel, wx.ID_ANY, "0"),
            FloatInput(panel, wx.ID_ANY, "0"),
            FloatInput(panel, wx.ID_ANY, "0")
        ]
        for i in range(4):
            if orientation == wx.HORIZONTAL:
                this.Add(this.__vLabel[i], 1, wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL)
                this.Add(this.__v[i], relativeFloatSize, wx.EXPAND)
            else:
                bSizer = wx.BoxSizer(wx.HORIZONTAL)
                bSizer.Add(this.__vLabel[i], 1, wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL)
                bSizer.Add(this.__v[i], relativeFloatSize, wx.EXPAND)
                this.Add(bSizer, 1, wx.EXPAND)
            panel.Bind(wx.EVT_TEXT, this.onFloat, id = this.__v[i].GetId())

    def GetId(this):
        return this.__v[this.__ctrlIdIndex].GetId()

    def onFloat(this, e):
        #ctrlId = e.GetId()
        vEvent = VectorUpdatedEvent(myEVT_VECTOR_UPDATED, this.GetId())
        vEvent.SetEventObject(this)
        vEvent.SetVector(GeomTypes.Vec4([
                this.__v[0].GetValue(),
                this.__v[1].GetValue(),
                this.__v[2].GetValue(),
                this.__v[3].GetValue()
            ]))
        this.__v[this.__ctrlIdIndex].GetEventHandler().ProcessEvent(vEvent)

    def GetValue(this):
        return GeomTypes.Vec4([
                this.__v[0].GetValue(),
                this.__v[1].GetValue(),
                this.__v[2].GetValue(),
                this.__v[3].GetValue()
            ])

    def Destroy(this):
        for ctrl in this.__vLabel: ctrl.Destroy()
        for ctrl in this.__v: ctrl.Destroy()
        for box in this.Boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(this)

class SymmetrySelect(wx.StaticBoxSizer):
    def __init__(this,
        panel,
        label = '',
        # TODO: proper init: all
        groupsList = [
            isometry.E,
            isometry.Cn,
            isometry.A4,
            isometry.A4xI,
            isometry.S4,
        ],
        onSymSelect = None
    ):
        """
        Create a control embedded in a sizer for defining a symmetry.

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        groupsList: the list of symmetries that one can choose from.
        """
        this.groupsList  = groupsList
        this.onSymSelect = onSymSelect
        this.panel       = panel
        this.Boxes       = [wx.StaticBox(panel, label = label)]
        wx.StaticBoxSizer.__init__(this, this.Boxes[-1], wx.VERTICAL)

        this.groupsStrList = [c.__name__ for c in this.groupsList]
        this.Boxes.append(
            wx.ListBox(this.panel, wx.ID_ANY,
                choices = this.groupsStrList,
                style = wx.LB_SINGLE)
        )
        this.Boxes[-1].SetSelection(0)
        this.__SymmetryGuiIndex = len(this.Boxes) - 1
        #this.panel.Bind(wx.EVT_LISTBOX_DCLICK,
        #    this.onApplySymmetry, id = this.Boxes[-1].GetId())
        this.panel.Bind(wx.EVT_LISTBOX,
            this.onSetSymmetry, id = this.Boxes[-1].GetId())
        this.Add(this.Boxes[-1], 0, wx.EXPAND)

        this.addSetupGui()

    def setList(this, groupsList):
        this.groupsList  = groupsList
        this.Boxes[this.__SymmetryGuiIndex].Set(
            [c.__name__ for c in groupsList]
        )
        # Not so good: this requires that E should be last...
        this.Boxes[this.__SymmetryGuiIndex].SetSelection(len(groupsList)-1)
        this.addSetupGui()
        this.panel.Layout()

    def getSymmetry(this):
        Id = this.Boxes[this.__SymmetryGuiIndex].GetSelection()
        return this.groupsList[Id]

    def addSetupGui(this):
        # TODO: save initial values and reapply if selected again...
        try:
                for gui in this.oriGuis:
                    gui.Destroy()
                this.oriGuiBox.Destroy()
                this.Remove(this.oriSizer)
        except AttributeError: pass
        this.oriGuiBox = wx.StaticBox(this.panel, label = 'Symmetry Setup')
        this.oriSizer = wx.StaticBoxSizer(this.oriGuiBox, wx.VERTICAL)
        this.oriGuis = []
        sym = this.getSymmetry()
        for init in sym.initPars:
            inputType = init['type']
            if inputType == 'vec3':
                gui = Vector3DInput(this.panel, init['lab'])
            elif inputType == 'int':
                gui = LabeledIntInput(this.panel, init['lab'])
            else:
                assert False, "oops unimplemented input type"
            this.oriGuis.append(gui)
            this.oriSizer.Add(this.oriGuis[-1], 1, wx.EXPAND)
        this.Add(this.oriSizer, 1, wx.EXPAND)

    def onSetSymmetry(this, e):
        this.addSetupGui()
        this.panel.Layout()
        if this.onSymSelect != None: this.onSymSelect(this.getSymmetry())

    def GetSelected(this):
        sym = this.getSymmetry()
        setup = {}
        for i, gui in zip(range(len(this.oriGuis)), this.oriGuis):
            inputType = sym.initPars[i]['type']
            if inputType == 'vec3':
                v = gui.GetVertex()
                if v != GeomTypes.Vec3([0, 0, 0]):
                    setup[sym.initPars[i]['par']] = v
            elif inputType == 'int':
                v = gui.GetValue()
                setup[sym.initPars[i]['par']] = v
        sym = sym(setup = setup)

        return sym

    def Destroy(this):
        for box in this.Boxes + this.oriGuis + this.stabGuis:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(this)

