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
import GeomTypes
import isometry
import wx.lib.scrolledpanel as wxXtra

# TODO:
# - filter Fs for FacesInput.GetFace (negative nrs, length 2, etc)

def oppositeOrientation(orientation):
    if orientation == wx.HORIZONTAL:
        return wx.VERTICAL
    else:
        return wx.HORIZONTAL

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
        rkc = e.GetRawKeyCode()
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
        elif e.ControlDown():
            if rkc == ord('v'):
                this.Paste()
            elif rkc == ord('c'):
                this.Copy()
            elif rkc == ord('x'):
                this.Cut()
            else:
                print this.__class__, 'ignores Ctrl-key event with code:', rkc
        else:
            print this.__class__, 'ignores key event with code:', k
        #elif k >= 256:
        #    e.Skip()
        if len(wx.TextCtrl.GetValue(this)) < 1:
            # do not allow an empty field, set to 0 instead:
            this.SetValue('0')
            this.SetSelection(0, 1)

    def GetValue(this):
        v = wx.TextCtrl.GetValue(this)
        if v == '': v = '0'
        return float(v)

class LabeledIntInput(wx.StaticBoxSizer):
    def __init__(this,
        panel,
        label = '',
        init = 0,
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
        if not isinstance(init, int):
            print '%s warning: initialiser not an int (%s)' % (
                    this.__class__, str(init)
                )
            init = 0
        this.Boxes.append(IntInput(
                panel, wx.ID_ANY, str(init), size = (width, -1)
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

class Vector3DInput(wx.StaticBoxSizer):
    def __init__(this,
        panel,
        label = '',
        v = None,
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
        if v != None:
            this.SetVertex(v)

    def GetVertex(this):
        return GeomTypes.Vec3([
                this.__v[0].GetValue(),
                this.__v[1].GetValue(),
                this.__v[2].GetValue(),
            ])

    def SetVertex(this, v):
        for i in v:
            if not (isinstance(i, float) or isinstance(i, int)):
                print '%s warning: v[%d] not a float (%s)' % (
                        this.__class__, v.index(i), str(i)
                    )
                return
        this.__v[0].SetValue(str(v[0]))
        this.__v[1].SetValue(str(v[1]))
        this.__v[2].SetValue(str(v[2]))

    def Destroy(this):
        for ctrl in this.__v: ctrl.Destroy()
        for box in this.Boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(this)

class Vector3DSetStaticPanel(wxXtra.ScrolledPanel):
    __hlabels = ['index', 'x', 'y', 'z']
    def __init__(this, parent,
        length,
        orientation = wx.HORIZONTAL,
    ):
        """
        Create a panel defining a set of 3D vectors

        parent: the parent widget.
        length: initialise with length amount of 3D vectors.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the separate vector
                     items.
        """

        wxXtra.ScrolledPanel.__init__(this, parent)

        this.boxes = []
        oppOri = oppositeOrientation(orientation)
        vectorsSizer = wx.BoxSizer(orientation)
        this.columnSizers = [] # align vector columns
        # header:
        scale = 0
        for i in range(len(this.__hlabels)):
            this.boxes.append(
                wx.StaticText(this, wx.ID_ANY, this.__hlabels[i])
            )
            this.columnSizers.append(wx.BoxSizer(oppOri))
            this.columnSizers[i].Add(this.boxes[-1], 0,
                wx.ALIGN_CENTRE_HORIZONTAL)
            vectorsSizer.Add(this.columnSizers[i], scale, wx.EXPAND)
            scale = 1
        # vectors:
        this.__v = []
        this.__vLabels = []
        this.grow(length)

        # use a list sizer to be able to fill white space for list with vectors
        # that are too small (cannot remove the wx.EXPAND above since the
        # vector columns need to be aligned.
        listSizer = wx.BoxSizer(oppOri)
        listSizer.Add(vectorsSizer, 0)
        listSizer.Add(wx.BoxSizer(orientation), 0, wx.EXPAND)

        this.SetSizer(listSizer)
        this.SetAutoLayout(True)
        this.SetupScrolling()

    def grow(this, nr=1, vs=None):
        assert vs == None or len(vs) == nr
        for n in range(nr):
            j = len(this.__v)
            this.__vLabels.append(
                wx.StaticText(this, wx.ID_ANY, '%d ' % j, style = wx.TE_CENTRE)
            )
            this.columnSizers[0].Add(this.__vLabels[-1], 1)
            this.__v.append([])
            for i in range(1, len(this.__hlabels)):
                if vs == None:
                    c = "0"
                else:
                    c = str(vs[n][i-1])
                this.__v[-1].append(FloatInput(this, wx.ID_ANY, c))
                this.columnSizers[i].Add(this.__v[-1][-1], 1, wx.EXPAND)
        this.Layout()

    def extend(this, Vs):
        this.grow(len(Vs), Vs)

    def rmVector(this, i):
        if len(this.__vLabels) > 0:
            assert i < len(this.__vLabels)
            g = this.__vLabels[i]
            del this.__vLabels[i]
            g.Destroy()
            v = this.__v[i]
            del this.__v[i]
            for g in v:
                g.Destroy()
            this.Layout()
        else:
            print '%s warning: nothing to delete.' % this.__class__.__name__

    def getVector(this, i):
        return GeomTypes.Vec3([
                this.__v[i][0].GetValue(),
                this.__v[i][1].GetValue(),
                this.__v[i][2].GetValue(),
            ])

    def get(this):
        return [
            this.getVector(i) for i in range(len(this.__v))
        ]

    def clear(this):
        for l in range(len(this.__v)):
            this.rmVector(-1)

    def set(this, Vs):
        this.clear()
        this.extend(Vs)

    def Destroy(this):
        for ctrl in this.__v: ctrl.Destroy()
        for ctrl in this.__vLabels: ctrl.Destroy()
        for box in this.boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass

    # TODO Insert?
    # Note that the panel is used for defining faces.  Inserting and delting
    # faces in the middle of the list will break these references (of course
    # this can be fixed by SW

class Vector3DSetDynamicPanel(wx.Panel):
    __defaultLabels = ['index', 'x', 'y', 'z']
    __nrOfColumns = 4
    def __init__(this,
        parent,
        length = 3,
        orientation = wx.HORIZONTAL,
        elementLabels = None
        # TODO: what about the std keywords
    ):
        """
        Create a control embedded in a sizer for defining a set of 3D vectors

        parent: the parent widget.
        length: initialise the input with length amount of 3D vectors.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the separate vector
                     items.
        elementLabels: option labels for the vector items. It is an array
                       consisting of 4 strings On default
                       ['index', 'x', 'y', 'z'] is used.
        """
        this.parent = parent
        wx.Panel.__init__(this, parent)

        this.boxes = []
        oppOri = oppositeOrientation(orientation)
        mainSizer = wx.BoxSizer(oppOri)

        # Add vertex list
        this.boxes.append(Vector3DSetStaticPanel(this, length, orientation))
        mainSizer.Add(this.boxes[-1], 10, wx.EXPAND)
        # Add button:
        addSizer = wx.BoxSizer(orientation)
        this.boxes.append(wx.Button(this, wx.ID_ANY, "Vertices Add nr:"))
        addSizer.Add(this.boxes[-1], 1, wx.EXPAND)
        this.Bind(wx.EVT_BUTTON, this.onAdd, id = this.boxes[-1].GetId())
        this.boxes.append(IntInput(this, wx.ID_ANY, '1', size = (40, -1)))
        this.__addNroVIndex = len(this.boxes) - 1
        addSizer.Add(this.boxes[-1], 0, wx.EXPAND)
        mainSizer.Add(addSizer, 1, wx.EXPAND)

        # Clear and Delete buttons:
        rmSizer = wx.BoxSizer(orientation)
        # Clear:
        this.boxes.append(wx.Button(this, wx.ID_ANY, "Clear"))
        this.Bind(wx.EVT_BUTTON, this.onClear, id = this.boxes[-1].GetId())
        rmSizer.Add(this.boxes[-1], 1, wx.EXPAND)
        # Delete:
        this.boxes.append(wx.Button(this, wx.ID_ANY, "Delete Vertex"))
        this.Bind(wx.EVT_BUTTON, this.onRm, id = this.boxes[-1].GetId())
        rmSizer.Add(this.boxes[-1], 1, wx.EXPAND)
        mainSizer.Add(rmSizer, 1, wx.EXPAND)

        this.SetSizer(mainSizer)
        this.SetAutoLayout(True)

    def onAdd(this, e):
        l = this.boxes[this.__addNroVIndex].GetValue()
        this.boxes[0].grow(l)
        this.Layout()
        e.Skip()

    def onRm(this, e):
        this.boxes[0].rmVector(-1)
        this.Layout()
        e.Skip()

    def onClear(this, e):
        this.boxes[0].clear()
        this.Layout()
        e.Skip()

    def set(this, Vs):
        this.boxes[0].set(Vs)
        this.Layout()

    def get(this):
        return this.boxes[0].get()

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

class FaceSetStaticPanel(wxXtra.ScrolledPanel):
    def __init__(this,
        parent,
        nrOfFaces = 0,
        faceLen = 0,
        width = 40,
        orientation = wx.HORIZONTAL,
    ):
        """
        Create a control embedded in a sizer for defining a set of faces

        parent: the parent widget.
        nrOfFaces: initialise the input with nrOfFaces amount of faces.
        faceLen: initialise the faces with faceLen vertices. Also the default
                 value for adding faces.
        width: width of the face index fields.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the separate face
                     items.
        """
        wxXtra.ScrolledPanel.__init__(this, parent)
        this.parent = parent
        this.width = width
        this.faceLen = faceLen
        this.orientation = orientation
        oppOri = oppositeOrientation(orientation)

        this.__f = []
        this.__fLabels = []
        this.faceIndexSizer = wx.BoxSizer(oppOri) # align face indices
        this.vertexIndexSizer = wx.BoxSizer(oppOri)
        facesSizer = wx.BoxSizer(orientation)
        facesSizer.Add(this.faceIndexSizer, 0, wx.EXPAND)
        facesSizer.Add(this.vertexIndexSizer, 0, wx.EXPAND)

        this.grow(nrOfFaces, faceLen)

        # use a list sizer to be able to fill white space if the face list
        #word is too small
        listSizer = wx.BoxSizer(oppOri)
        listSizer.Add(facesSizer, 0)
        listSizer.Add(wx.BoxSizer(orientation), 0, wx.EXPAND)

        this.SetSizer(listSizer)
        this.SetAutoLayout(True)
        this.SetupScrolling()

    def addFace(this, fLen = 0, face = None):
        assert fLen != 0 or face != None
        if face != None:
            fLen = len(face)
        j = len(this.__fLabels)
        this.__fLabels.append(wx.StaticText(this, wx.ID_ANY, '%d ' % j))
        this.faceIndexSizer.Add(this.__fLabels[-1],
                1, wx.EXPAND  | wx.ALIGN_CENTRE_VERTICAL)

        faceSizer = wx.BoxSizer(this.orientation)
        this.__f.append([faceSizer])
        for i in range(fLen):
            if (face != None):
                f_i = "%d" % face[i]
            else:
                f_i = "0"
            this.__f[-1].append(
                IntInput(this, wx.ID_ANY, f_i, size = (this.width, -1))
            )
            faceSizer.Add(this.__f[-1][-1], 0, wx.EXPAND)
        this.vertexIndexSizer.Add(faceSizer, 0, wx.EXPAND)

        this.Layout()

    def rmFace(this, i):
        if len(this.__fLabels) > 0:
            assert i < len(this.__fLabels)
            assert len(this.__f) > 0
            g = this.__fLabels[i]
            del this.__fLabels[i]
            g.Destroy()
            f = this.__f[i]
            del this.__f[i]
            this.vertexIndexSizer.Remove(f[0])
            del f[0]
            for g in f:
                g.Destroy()
            this.Layout()

    def getFace(this, index):
        return [
                this.__f[index][i].GetValue()
                    for i in range(1, len(this.__f[index]))
            ]

    def grow(this, nr, fLen):
        for i in range(nr):
            this.addFace(fLen)

    def extend(this, Fs):
        for f in Fs:
            this.addFace(face = f)

    def get(this):
        return [
            this.getFace(i) for i in range(len(this.__f))
        ]

    def clear(this):
        for l in range(len(this.__f)):
            this.rmFace(-1)

    def set(this, Fs):
        this.clear()
        this.extend(Fs)

    def Destroy(this):
        for ctrl in this.__fLabels: ctrl.Destroy()
        for ctrl in this.__f: ctrl.Destroy()

    # TODO Insert?

class FaceSetDynamicPanel(wx.Panel):
    def __init__(this,
        parent,
        nrOfFaces = 0,
        faceLen = 0,
        orientation = wx.HORIZONTAL,
    ):
        """
        Create a control for defining a set of faces, which can grow and shrink
        in size.

        parent: the parent widget.
        nrOfFaces: initialise the input with nrOfFaces amount of faces.
        faceLen: initialise the faces with faceLen vertices. Also the default
                 value for adding faces.
        width: width of the face index fields.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the separate face
                     items.
        """
        this.parent = parent
        wx.Panel.__init__(this, parent)
        this.faceLen = faceLen

        this.boxes = []
        oppOri = oppositeOrientation(orientation)
        mainSizer = wx.BoxSizer(oppOri)

        # Add face list
        this.boxes.append(FaceSetStaticPanel(this, nrOfFaces, faceLen,
            orientation = orientation))
        this.__faceListIndex = len(this.boxes) - 1
        mainSizer.Add(this.boxes[-1], 10, wx.EXPAND)

        # Add button:
        addSizer = wx.BoxSizer(orientation)
        this.boxes.append(IntInput(
                this, wx.ID_ANY, "%d" % faceLen, size = (40, -1)
            ))
        this.__faceLenIndex = len(this.boxes) - 1
        addSizer.Add(this.boxes[-1], 0, wx.EXPAND)
        this.boxes.append(wx.Button(this, wx.ID_ANY, "-Faces Add nr:"))
        addSizer.Add(this.boxes[-1], 1, wx.EXPAND)
        this.Bind(wx.EVT_BUTTON, this.onAdd, id = this.boxes[-1].GetId())
        this.boxes.append(IntInput(this, wx.ID_ANY, '1', size = (40, -1)))
        this.__nroFsLenIndex = len(this.boxes) - 1
        addSizer.Add(this.boxes[-1], 0, wx.EXPAND)
        mainSizer.Add(addSizer, 0, wx.EXPAND)
        # Delete button:
        this.boxes.append(wx.Button(this, wx.ID_ANY, "Delete Face"))
        this.Bind(wx.EVT_BUTTON, this.onRm, id = this.boxes[-1].GetId())
        mainSizer.Add(this.boxes[-1], 0, wx.EXPAND)

        this.SetSizer(mainSizer)
        this.SetAutoLayout(True)

    def onAdd(this, e):
        n = this.boxes[this.__nroFsLenIndex].GetValue()
        l = this.boxes[this.__faceLenIndex].GetValue()
        if l < 1:
            l = this.faceLen
            if l < 1: l = 3
        this.boxes[this.__faceListIndex].grow(n, l)
        this.Layout()

    def onRm(this, e):
        this.boxes[this.__faceListIndex].rmFace(-1)
        this.Layout()
        e.Skip()

    def get(this):
        return this.boxes[this.__faceListIndex].get()

    def set(this, Fs):
        this.boxes[this.__faceListIndex].set(Fs)
        this.Layout()

    def Destroy(this):
        for box in this.boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass

class SymmetrySelect(wx.StaticBoxSizer):
    def __init__(this,
        panel,
        label = '',
        # TODO: proper init: all
        groupsList = [
            isometry.E,
            isometry.ExI,
            isometry.Cn,
            isometry.CnxI,
            isometry.C2nCn,
            isometry.DnCn,
            isometry.Dn,
            isometry.DnxI,
            isometry.D2nDn,
            isometry.A4,
            isometry.A4xI,
            isometry.S4A4,
            isometry.S4,
            isometry.S4xI,
            isometry.A5,
            isometry.A5xI,
        ],
        onSymSelect = None,
        onGetSymSetup = None
    ):
        """
        Create a control embedded in a sizer for defining a symmetry.

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        groupsList: the list of symmetries that one can choose from.
        onSymSelect: This function will be called after a user selected the
                     symmetry from the list. The first and only parameter of the
                     function is the symmetry class that was selected.
        onGetSymSetup: This function will also be called after a user selected a
                       symmetry from the list, but before onSymSelect. With this
                       function you can return the default setup for the
                       selected symmetry class. The first parameter of this
                       function is the index in the symmetries list. If this
                       function is not set, the class default is used. The class
                       default is also used if the function returns None.
        """
        this.groupsList    = groupsList
        this.onSymSelect   = onSymSelect
        this.onGetSymSetup = onGetSymSetup
        this.panel         = panel
        this.Boxes         = [wx.StaticBox(panel, label = label)]
        this.__prev        = {}
        wx.StaticBoxSizer.__init__(this, this.Boxes[-1], wx.VERTICAL)

        this.groupsStrList = [c.__name__ for c in this.groupsList]
        this.Boxes.append(
            wx.Choice(this.panel, wx.ID_ANY, choices = this.groupsStrList)
        )
        this.Boxes[-1].SetSelection(0)
        this.__SymmetryGuiIndex = len(this.Boxes) - 1
        this.panel.Bind(wx.EVT_CHOICE,
            this.onSetSymmetry, id = this.Boxes[-1].GetId())
        this.Add(this.Boxes[-1], 0, wx.EXPAND)

        this.addSetupGui()

    @property
    def length(this):
        return len(this.groupsList)

    def setList(this, groupsList):
        this.groupsList  = groupsList
        # would be nice is wx.Choice has a SetItems()
        this.Boxes[this.__SymmetryGuiIndex].Clear()
        for c in groupsList:
            this.Boxes[this.__SymmetryGuiIndex].Append(c.__name__)
        # Not so good: this requires that E should be last...
        this.Boxes[this.__SymmetryGuiIndex].SetSelection(len(groupsList)-1)
        this.addSetupGui()
        this.panel.Layout()

    def getSelectedIndex(this):
        return this.Boxes[this.__SymmetryGuiIndex].GetSelection()

    def getSymmetryClass(this, applyOrder = True):
        """returns a symmetry class"""
        #print 'getSymmetryClass'
        Id = this.getSelectedIndex()
        selClass = this.groupsList[Id]
        #print 'getSymmetryClass: nr:', Id, 'class:', selClass.__name__, selClass
        if applyOrder:
            if selClass in [
                isometry.Cn,
                isometry.CnxI,
                isometry.C2nCn,
                isometry.DnCn,
                isometry.Dn,
                isometry.DnxI,
                isometry.D2nDn
            ]:
                assert selClass.initPars[0]['type'] == 'int', (
                    'The first index should specify the n-order')
                n = this.oriGuis[0].GetValue()
                if selClass == isometry.Cn:
                    C = isometry.C
                elif selClass == isometry.CnxI:
                    C = isometry.CxI
                elif selClass == isometry.C2nCn:
                    C = isometry.C2nC
                elif selClass == isometry.DnCn:
                    C = isometry.DnC
                elif selClass == isometry.Dn:
                    C = isometry.D
                elif selClass == isometry.D2nDn:
                    C = isometry.D2nD
                elif selClass == isometry.DnxI:
                    C = isometry.DxI
                assert n > 0, 'warning'
                selClass = C(n)
            elif selClass in [
                isometry.E,
                isometry.ExI,
                isometry.C2C1,
                isometry.C4C2,
                isometry.C2,
                isometry.C2xI,
                isometry.C3,
                isometry.C3xI,
                isometry.C4,
                isometry.C4xI,
                isometry.C5,
                isometry.C5xI,
                isometry.D5C5,
                isometry.D5xI,
                isometry.D5,
                isometry.D4C4,
                isometry.D4xI,
                isometry.D4,
                isometry.D3C3,
                isometry.D3xI,
                isometry.D3,
                isometry.D2C2,
                isometry.D2xI,
                isometry.D2,
                isometry.A4,
                isometry.A4xI,
                isometry.S4A4,
                isometry.S4,
                isometry.S4xI,
                isometry.A5,
                isometry.A5xI,
            ]:
                pass
            else:
                assert False, 'unknown class %s' % selClass
                #print 'warning: unknown class', selClass
        #print 'selClass', selClass, 'n:', selClass.n
        return selClass

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
        sym = this.getSymmetryClass(applyOrder = False)
        if this.onGetSymSetup == None:
            symSetup = sym.defaultSetup
        else:
            symSetup = this.onGetSymSetup(this.getSelectedIndex())
            if symSetup == None:
                symSetup = sym.defaultSetup
        for init in sym.initPars:
            inputType = init['type']
            if inputType == 'vec3':
                gui = Vector3DInput(this.panel, init['lab'],
                        v = symSetup[init['par']]
                    )
            elif inputType == 'int':
                gui = LabeledIntInput(this.panel, init['lab'],
                        init = symSetup[init['par']]
                    )
            else:
                assert False, "oops unimplemented input type"
            this.oriGuis.append(gui)
            this.oriSizer.Add(this.oriGuis[-1], 1, wx.EXPAND)
        this.Add(this.oriSizer, 1, wx.EXPAND)

    def onSetSymmetry(this, e):
        this.addSetupGui()
        this.panel.Layout()
        if this.onSymSelect != None:
            this.onSymSelect(this.getSymmetryClass(applyOrder = False))

    def isSymClassUpdated(this):
        try:
            curId = this.getSelectedIndex()
            isUpdated = this.__prev['selectedId'] != curId
        except KeyError:
            isUpdated = True
        this.__prev['selectedId'] = curId
        #print 'isSymClassUpdated', isUpdated
        return isUpdated

    def isUpdated(this):
        isUpdated = this.isSymClassUpdated()
        curSetup = []
        sym = this.getSymmetryClass(applyOrder = False)
        for i, gui in zip(range(len(this.oriGuis)), this.oriGuis):
            inputType = sym.initPars[i]['type']
            if inputType == 'vec3':
                v = gui.GetVertex()
            elif inputType == 'int':
                v = gui.GetValue()
            curSetup.append(v)
        try:
            prevSetup = this.__prev['setup']
            if len(prevSetup) == len(curSetup):
                for i in range(len(prevSetup)):
                    if prevSetup[i] != curSetup[i]:
                        isUpdated = True
                        break
            else:
                isUpdated = True
        except KeyError:
            isUpdated = True
        this.__prev['setup'] = curSetup
        #print 'isUpdated', isUpdated
        return isUpdated

    def SetSelected(this, i):
        this.Boxes[this.__SymmetryGuiIndex].SetSelection(i)

    def GetSelected(this):
        """returns a symmetry instance"""
        sym = this.getSymmetryClass(applyOrder = False)
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
        #print 'GetSelected; setup:', setup
        #print 'class:', sym
        sym = sym(setup = setup)

        return sym

    def Destroy(this):
        for box in this.Boxes + this.oriGuis + this.stabGuis:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(this)

