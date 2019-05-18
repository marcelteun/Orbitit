#!/usr/bin/python
"""
GUI widgets related to objects with geometry

Like vertices, faecs, symmetries, etc.
"""
#
# Copyright (C) 2010-2019 Marcel Tunnissen
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
# ------------------------------------------------------------------


#import math
import wx
import geomtypes
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
    def __init__(self, reason='for some reason', enableReason=True):
        self.reason = reason
        self.enableReason = enableReason
        wx.TextDropTarget.__init__(self)

#    def OnDropText(self, x, y, text):
#        pass
#        #print self.__class__, 'drop text disabled:', self.reason

    def OnDragOver(self, x, y, d):
        if self.enableReason:
            print self.__class__, 'drag from text disabled 0:', self.reason
        return ''

class IntInput(wx.TextCtrl):
    def __init__(self, parent, ident, value, *args, **kwargs):
        wx.TextCtrl.__init__(self, parent, ident, str(value), *args, **kwargs)
        # Set defaults: style and width if not set by caller
        #self.SetStyle(0, -1, wx.TE_PROCESS_ENTER | wx.TE_DONTWRAP)
        self.val_updated = False
        self.SetMaxLength(18)
        self.SetDropTarget(DisabledDropTarget(reason='may break string format for floating point'))
        self.Bind(wx.EVT_CHAR, self.onChar)

    def onChar(self, e):
        k = e.GetKeyCode() # ASCII is returned for ASCII values
        updated = True  # except for some cases below
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
            ss = self.GetStringSelection()
            if not ss == '':
                sel = self.GetSelection()
                if sel[0] == 0:
                    self.Replace(sel[0], sel[1], '0')
                    endSel = sel[0]+1
                else:
                    self.Replace(sel[0], sel[1], '')
                    endSel = sel[0]
                self.SetSelection(sel[0], endSel)
                #self.SetInsertionPoint(sel[0])
            s = wx.TextCtrl.GetValue(self)
            # only allow one +, -
            if not c in s:
                # only allow + and - in the beginning
                print ' not c in s:', self.GetInsertionPoint()
                if self.GetInsertionPoint() == 0:
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
                    if self.GetSelection()[0] == 0 and c == '-':
                        self.Replace(0, 1, '-0')
                        self.SetSelection(1, 2)
        elif k in [
                wx.WXK_BACK, wx.WXK_DELETE,
            ]:
            ss = self.GetStringSelection()
            # Handle selected text by replacing it by a '0' the field might
            # become completely empty if all is selected
            if not ss == '':
                sel = self.GetSelection()
                self.Replace(sel[0], sel[1], '0')
                self.SetSelection(sel[0], sel[0]+1)
            if len(wx.TextCtrl.GetValue(self)) <= 1:
                # do not allow an empt field, set to 0 instead:
                self.SetValue(0)
                self.SetSelection(0, 1)
            else:
                e.Skip()
        elif k == wx.WXK_CLEAR:
            self.SetValue(0)
        elif k in [
                wx.WXK_RETURN, wx.WXK_TAB,
                wx.WXK_LEFT, wx.WXK_RIGHT,
                wx.WXK_INSERT,
                wx.WXK_HOME, wx.WXK_END
            ]:
            updated = False
            e.Skip()
        else:
            updated = False
            print self.__class__, 'ignores key event with code:', k
        #elif k >= 256:
        #    e.Skip()
        self.val_updated = updated

    def GetValue(self):
        v = wx.TextCtrl.GetValue(self)
        self.val_updated = False
        if v == '': v = '0'
        return int(v)

    def SetValue(self, i):
        self.val_updated = True
        v = wx.TextCtrl.SetValue(self, str(i))

class FloatInput(wx.TextCtrl):
    def __init__(self, parent, ident, value, *args, **kwargs):
        wx.TextCtrl.__init__(self, parent, ident, str(value), *args, **kwargs)
        # Set defaults: style and width if not set by caller
        #self.SetStyle(0, -1, wx.TE_PROCESS_ENTER | wx.TE_DONTWRAP)
        self.SetMaxLength(18)
        self.SetDropTarget(DisabledDropTarget(reason='may break string format for floating point'))
        self.Bind(wx.EVT_CHAR, self.onChar)
        self.on_set = None

    def bind_on_set(self, on_set):
        """
        Bind the function on_set to be called with the current value when the
        field is set

        The field is set when ENTER / TAB is pressed
        """
        self.on_set = on_set

    def onChar(self, e):
        #print self.__class__, 'onChar'
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
            ss = self.GetStringSelection()
            if not ss == '':
                sel = self.GetSelection()
                if sel[0] == 0:
                    self.Replace(sel[0], sel[1], '0')
                    endSel = sel[0]+1
                else:
                    self.Replace(sel[0], sel[1], '')
                    endSel = sel[0]
                self.SetSelection(sel[0], endSel)
                #self.SetInsertionPoint(sel[0])
            s = wx.TextCtrl.GetValue(self)
            # only allow one +, -, or .
            if not c in s:
                if c == '.':
                    e.Skip()
                else:  # '+' or '-'
                    # only allow + and - in the beginning
                    if self.GetInsertionPoint() == 0:
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
                        if self.GetSelection()[0] == 0 and c == '-':
                            self.Replace(0, 1, '-0')
                            self.SetSelection(1, 2)

        elif k in [
                wx.WXK_BACK, wx.WXK_DELETE,
            ]:
            ss = self.GetStringSelection()
            # Handle selected text by replacing it by a '0' the field might
            # become completely empty if all is selected
            if not ss == '':
                sel = self.GetSelection()
                self.Replace(sel[0], sel[1], '0')
                self.SetSelection(sel[0], sel[0]+1)
            else:
                e.Skip()
        elif k == wx.WXK_CLEAR:
            self.SetValue(0)
        elif k in [wx.WXK_RETURN, wx.WXK_TAB]:
            if not self.on_set is None:
                self.on_set(self.GetValue())
            e.Skip()
        elif k in [
                wx.WXK_LEFT, wx.WXK_RIGHT,
                wx.WXK_INSERT,
                wx.WXK_HOME, wx.WXK_END
            ]:
            e.Skip()
        elif e.ControlDown():
            if rkc == ord('v'):
                self.Paste()
            elif rkc == ord('c'):
                self.Copy()
            elif rkc == ord('x'):
                self.Cut()
            else:
                print self.__class__, 'ignores Ctrl-key event with code:', rkc
        else:
            print self.__class__, 'ignores key event with code:', k
        #elif k >= 256:
        #    e.Skip()

    def GetValue(self):
        v = wx.TextCtrl.GetValue(self)
        if v == '':
            v = '0'
            self.SetValue(v)
        return float(v)

    def SetValue(self, f):
        v = wx.TextCtrl.SetValue(self, str(f))

class LabeledIntInput(wx.StaticBoxSizer):
    def __init__(self,
                 panel,
                 label='',
                 init=0,
                 width=-1,
                 orientation=wx.HORIZONTAL):
        """
        Create a control embedded in a sizer for defining an int.

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        init: initial value used in input
        width: width of the face index fields.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the label - int input.
        """
        self.Boxes = []
        wx.BoxSizer.__init__(self, orientation)
        self.Boxes.append(
            wx.StaticText(panel, wx.ID_ANY, label + ' ',
                          style=wx.ALIGN_RIGHT
            )
        )
        self.Add(self.Boxes[-1], 1, wx.EXPAND)
        if not isinstance(init, int):
            print '{} warning: initialiser not an int ({})'.format(
                self.__class__, str(init))
            init = 0
        self.Boxes.append(IntInput(
            panel, wx.ID_ANY, init, size=(width, -1)))
        self.Add(self.Boxes[-1], 0, wx.EXPAND)
        self.int_gui_idx = len(self.Boxes) - 1

    @property
    def val_updated(self):
        return self.Boxes[self.int_gui_idx].val_updated

    def GetValue(self):
        return self.Boxes[-1].GetValue()

    def SetValue(self, i):
        return self.Boxes[-1].SetValue(i)

    def Destroy(self):
        for box in self.Boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(self)

class Vector3DInput(wx.StaticBoxSizer):
    def __init__(self,
                 panel,
                 label='',
                 v=None,
                 orientation=wx.HORIZONTAL):
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
        self.panel = panel
        self.Boxes = []
        wx.BoxSizer.__init__(self, orientation)
        self.Boxes.append(
            wx.StaticText(self.panel, wx.ID_ANY, label + ' ',
                style=wx.ALIGN_RIGHT
            )
        )
        self.Add(self.Boxes[-1], 1, wx.EXPAND)
        self.__v = []
        for i in range(3):
            self.__v.append(FloatInput(self.panel, wx.ID_ANY, 0))
            self.Add(self.__v[-1], 0, wx.EXPAND)
        if v != None:
            self.SetVertex(v)

    def GetVertex(self):
        return geomtypes.Vec3([
                self.__v[0].GetValue(),
                self.__v[1].GetValue(),
                self.__v[2].GetValue(),
            ])

    def SetVertex(self, v):
        for i in v:
            if not (isinstance(i, float) or isinstance(i, int)):
                print '%s warning: v[%d] not a float (%s)' % (
                        self.__class__, v.index(i), str(i)
                    )
                return
        self.__v[0].SetValue(v[0])
        self.__v[1].SetValue(v[1])
        self.__v[2].SetValue(v[2])

    def Destroy(self):
        for ctrl in self.__v: ctrl.Destroy()
        for box in self.Boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(self)

class Vector3DSetStaticPanel(wxXtra.ScrolledPanel):
    __hlabels = ['index', 'x', 'y', 'z']
    def __init__(self, parent,
                 length,
                 orientation=wx.HORIZONTAL):
        """
        Create a panel defining a set of 3D vectors

        parent: the parent widget.
        length: initialise with length amount of 3D vectors.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is
                     default. Defines the orientation of the separate vector
                     items.
        """

        wxXtra.ScrolledPanel.__init__(self, parent)

        self.boxes = []
        oppOri = oppositeOrientation(orientation)
        vectorsSizer = wx.BoxSizer(orientation)
        self.columnSizers = [] # align vector columns
        # header:
        scale = 0
        for i in range(len(self.__hlabels)):
            self.boxes.append(
                wx.StaticText(self, wx.ID_ANY, self.__hlabels[i])
            )
            self.columnSizers.append(wx.BoxSizer(oppOri))
            self.columnSizers[i].Add(self.boxes[-1], 0,
                                     wx.ALIGN_CENTRE_HORIZONTAL)
            vectorsSizer.Add(self.columnSizers[i], scale, wx.EXPAND)
            scale = 1
        # vectors:
        self.__v = []
        self.__vLabels = []
        self.grow(length)

        # use a list sizer to be able to fill white space for list with vectors
        # that are too small (cannot remove the wx.EXPAND above since the
        # vector columns need to be aligned.
        listSizer = wx.BoxSizer(oppOri)
        listSizer.Add(vectorsSizer, 0)
        listSizer.Add(wx.BoxSizer(orientation), 0, wx.EXPAND)

        self.SetSizer(listSizer)
        self.SetAutoLayout(True)
        self.SetupScrolling()

    def grow(self, nr=1, vs=None):
        assert vs == None or len(vs) == nr
        for n in range(nr):
            j = len(self.__v)
            self.__vLabels.append(
                wx.StaticText(self, wx.ID_ANY, '%d ' % j, style=wx.TE_CENTRE)
            )
            self.columnSizers[0].Add(self.__vLabels[-1], 1)
            self.__v.append([])
            for i in range(1, len(self.__hlabels)):
                if vs == None:
                    f = 0
                else:
                    f = vs[n][i-1]
                self.__v[-1].append(FloatInput(self, wx.ID_ANY, f))
                self.columnSizers[i].Add(self.__v[-1][-1], 1, wx.EXPAND)
        self.Layout()

    def extend(self, Vs):
        self.grow(len(Vs), Vs)

    def rmVector(self, i):
        if len(self.__vLabels) > 0:
            assert i < len(self.__vLabels)
            g = self.__vLabels[i]
            del self.__vLabels[i]
            g.Destroy()
            v = self.__v[i]
            del self.__v[i]
            for g in v:
                g.Destroy()
            self.Layout()
        else:
            print '%s warning: nothing to delete.' % self.__class__.__name__

    def getVector(self, i):
        return geomtypes.Vec3([self.__v[i][0].GetValue(),
                               self.__v[i][1].GetValue(),
                               self.__v[i][2].GetValue()])

    def get(self):
        return [
            self.getVector(i) for i in range(len(self.__v))
        ]

    def clear(self):
        for l in range(len(self.__v)):
            self.rmVector(-1)

    def set(self, Vs):
        self.clear()
        self.extend(Vs)

    def Destroy(self):
        for ctrl in self.__v: ctrl.Destroy()
        for ctrl in self.__vLabels: ctrl.Destroy()
        for box in self.boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass

    # TODO Insert?
    # Note that the panel is used for defining faces.  Inserting and delting
    # faces in the middle of the list will break these references (of course
    # self can be fixed by SW

class Vector3DSetDynamicPanel(wx.Panel):
    __defaultLabels = ['index', 'x', 'y', 'z']
    __nrOfColumns = 4
    def __init__(self,
                 parent,
                 length=3,
                 relExtraSpace=5,
                 orientation=wx.HORIZONTAL,
                 elementLabels=None):
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
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self.boxes = []
        oppOri = oppositeOrientation(orientation)
        mainSizer = wx.BoxSizer(oppOri)

        # Add vertex list
        self.boxes.append(Vector3DSetStaticPanel(self, length, orientation))
        mainSizer.Add(self.boxes[-1], relExtraSpace, wx.EXPAND)
        # Add button:
        addSizer = wx.BoxSizer(orientation)
        self.boxes.append(wx.Button(self, wx.ID_ANY, "Vertices Add nr:"))
        addSizer.Add(self.boxes[-1], 1, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.onAdd, id=self.boxes[-1].GetId())
        self.boxes.append(IntInput(self, wx.ID_ANY, 1, size=(40, -1)))
        self.__addNroVIndex = len(self.boxes) - 1
        addSizer.Add(self.boxes[-1], 0, wx.EXPAND)
        mainSizer.Add(addSizer, 1, wx.EXPAND)

        # Clear and Delete buttons:
        rmSizer = wx.BoxSizer(orientation)
        # Clear:
        self.boxes.append(wx.Button(self, wx.ID_ANY, "Clear"))
        self.Bind(wx.EVT_BUTTON, self.onClear, id=self.boxes[-1].GetId())
        rmSizer.Add(self.boxes[-1], 1, wx.EXPAND)
        # Delete:
        self.boxes.append(wx.Button(self, wx.ID_ANY, "Delete Vertex"))
        self.Bind(wx.EVT_BUTTON, self.onRm, id=self.boxes[-1].GetId())
        rmSizer.Add(self.boxes[-1], 1, wx.EXPAND)
        mainSizer.Add(rmSizer, 1, wx.EXPAND)

        self.SetSizer(mainSizer)
        self.SetAutoLayout(True)

    def onAdd(self, e):
        l = self.boxes[self.__addNroVIndex].GetValue()
        self.boxes[0].grow(l)
        self.Layout()
        e.Skip()

    def onRm(self, e):
        self.boxes[0].rmVector(-1)
        self.Layout()
        e.Skip()

    def onClear(self, e):
        self.boxes[0].clear()
        self.Layout()
        e.Skip()

    def set(self, Vs):
        self.boxes[0].set(Vs)
        self.Layout()

    def get(self):
        return self.boxes[0].get()

myEVT_VECTOR_UPDATED = wx.NewEventType()
EVT_VECTOR_UPDATED = wx.PyEventBinder(myEVT_VECTOR_UPDATED, 1)

class VectorUpdatedEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)

    def SetVector(self, vector):
        self.vector = vector

    def GetVector(self):
        return self.vector

class Vector4DInput(wx.StaticBoxSizer):
    __ctrlIdIndex = 0
    __defaultLabels = ['x', 'y', 'z', 'w']
    def __init__(self,
                 panel,
                 label='',
                 orientation=wx.HORIZONTAL,
                 relativeFloatSize=4,
                 elementLabels=None):
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
        self.Boxes = [wx.StaticBox(panel, label = label)]
        wx.StaticBoxSizer.__init__(self, self.Boxes[-1], orientation)
        if elementLabels == None: elementLabels = self.__defaultLabels
        self.__vLabel = [
            wx.StaticText(panel, wx.ID_ANY, elementLabels[0], style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL),
            wx.StaticText(panel, wx.ID_ANY, elementLabels[1], style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL),
            wx.StaticText(panel, wx.ID_ANY, elementLabels[2], style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL),
            wx.StaticText(panel, wx.ID_ANY, elementLabels[3], style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL)
        ]
        self.__v = [
            FloatInput(panel, wx.ID_ANY, 0),
            FloatInput(panel, wx.ID_ANY, 0),
            FloatInput(panel, wx.ID_ANY, 0),
            FloatInput(panel, wx.ID_ANY, 0)
        ]
        for i in range(4):
            if orientation == wx.HORIZONTAL:
                self.Add(self.__vLabel[i], 1, wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL)
                self.Add(self.__v[i], relativeFloatSize, wx.EXPAND)
            else:
                bSizer = wx.BoxSizer(wx.HORIZONTAL)
                bSizer.Add(self.__vLabel[i], 1, wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL)
                bSizer.Add(self.__v[i], relativeFloatSize, wx.EXPAND)
                self.Add(bSizer, 1, wx.EXPAND)
            panel.Bind(wx.EVT_TEXT, self.onFloat, id=self.__v[i].GetId())

    def GetId(self):
        return self.__v[self.__ctrlIdIndex].GetId()

    def onFloat(self, e):
        #ctrlId = e.GetId()
        vEvent = VectorUpdatedEvent(myEVT_VECTOR_UPDATED, self.GetId())
        vEvent.SetEventObject(self)
        vEvent.SetVector(geomtypes.Vec4([self.__v[0].GetValue(),
                                         self.__v[1].GetValue(),
                                         self.__v[2].GetValue(),
                                         self.__v[3].GetValue()]))
        self.__v[self.__ctrlIdIndex].GetEventHandler().ProcessEvent(vEvent)

    def GetValue(self):
        return geomtypes.Vec4([self.__v[0].GetValue(),
                               self.__v[1].GetValue(),
                               self.__v[2].GetValue(),
                               self.__v[3].GetValue()])

    def Destroy(self):
        for ctrl in self.__vLabel: ctrl.Destroy()
        for ctrl in self.__v: ctrl.Destroy()
        for box in self.Boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(self)

class FaceSetStaticPanel(wxXtra.ScrolledPanel):
    def __init__(self,
                 parent,
                 nrOfFaces=0,
                 faceLen=0,
                 width=40,
                 orientation=wx.HORIZONTAL):
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
        wxXtra.ScrolledPanel.__init__(self, parent)
        self.parent = parent
        self.width = width
        self.faceLen = faceLen
        self.orientation = orientation
        oppOri = oppositeOrientation(orientation)

        self.__f = []
        self.__fLabels = []
        self.faceIndexSizer = wx.BoxSizer(oppOri) # align face indices
        self.vertexIndexSizer = wx.BoxSizer(oppOri)
        facesSizer = wx.BoxSizer(orientation)
        facesSizer.Add(self.faceIndexSizer, 0, wx.EXPAND)
        facesSizer.Add(self.vertexIndexSizer, 0, wx.EXPAND)

        self.grow(nrOfFaces, faceLen)

        # use a list sizer to be able to fill white space if the face list
        #word is too small
        listSizer = wx.BoxSizer(oppOri)
        listSizer.Add(facesSizer, 0)
        listSizer.Add(wx.BoxSizer(orientation), 0, wx.EXPAND)

        self.SetSizer(listSizer)
        self.SetAutoLayout(True)
        self.SetupScrolling()

    def addFace(self, fLen=0, face=None):
        assert fLen != 0 or face is not None
        if face != None:
            fLen = len(face)
        j = len(self.__fLabels)
        self.__fLabels.append(wx.StaticText(self, wx.ID_ANY, '%d ' % j))
        self.faceIndexSizer.Add(self.__fLabels[-1],
                                1, wx.EXPAND  | wx.ALIGN_CENTRE_VERTICAL)

        faceSizer = wx.BoxSizer(self.orientation)
        self.__f.append([faceSizer])
        for i in range(fLen):
            if (face != None):
                ind = face[i]
            else:
                ind = 0
            self.__f[-1].append(
                IntInput(self, wx.ID_ANY, ind, size=(self.width, -1))
            )
            faceSizer.Add(self.__f[-1][-1], 0, wx.EXPAND)
        self.vertexIndexSizer.Add(faceSizer, 0, wx.EXPAND)

        self.Layout()

    def rmFace(self, i):
        if len(self.__fLabels) > 0:
            assert i < len(self.__fLabels)
            assert len(self.__f) > 0
            g = self.__fLabels[i]
            del self.__fLabels[i]
            g.Destroy()
            f = self.__f[i]
            del self.__f[i]
            self.vertexIndexSizer.Remove(f[0])
            del f[0]
            for g in f:
                g.Destroy()
            self.Layout()

    def getFace(self, index):
        return [self.__f[index][i].GetValue()
                for i in range(1, len(self.__f[index]))]

    def grow(self, nr, fLen):
        for i in range(nr):
            self.addFace(fLen)

    def extend(self, Fs):
        for f in Fs:
            self.addFace(face=f)

    def get(self):
        return [
            self.getFace(i) for i in range(len(self.__f))
        ]

    def clear(self):
        for l in range(len(self.__f)):
            self.rmFace(-1)

    def set(self, Fs):
        self.clear()
        self.extend(Fs)

    def Destroy(self):
        for ctrl in self.__fLabels: ctrl.Destroy()
        for ctrl in self.__f: ctrl.Destroy()

    # TODO Insert?

class FaceSetDynamicPanel(wx.Panel):
    def __init__(self,
                 parent,
                 nrOfFaces=0,
                 faceLen=0,
                 orientation=wx.HORIZONTAL):
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
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.faceLen = faceLen

        self.boxes = []
        oppOri = oppositeOrientation(orientation)
        mainSizer = wx.BoxSizer(oppOri)

        # Add face list
        self.boxes.append(FaceSetStaticPanel(self, nrOfFaces, faceLen,
                                             orientation=orientation))
        self.__faceListIndex = len(self.boxes) - 1
        mainSizer.Add(self.boxes[-1], 10, wx.EXPAND)

        # Add button:
        addSizer = wx.BoxSizer(orientation)
        self.boxes.append(IntInput(
            self, wx.ID_ANY, faceLen, size=(40, -1)))
        self.__faceLenIndex = len(self.boxes) - 1
        addSizer.Add(self.boxes[-1], 0, wx.EXPAND)
        self.boxes.append(wx.Button(self, wx.ID_ANY, "-Faces Add nr:"))
        addSizer.Add(self.boxes[-1], 1, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.onAdd, id=self.boxes[-1].GetId())
        self.boxes.append(IntInput(self, wx.ID_ANY, 1, size=(40, -1)))
        self.__nroFsLenIndex = len(self.boxes) - 1
        addSizer.Add(self.boxes[-1], 0, wx.EXPAND)
        mainSizer.Add(addSizer, 0, wx.EXPAND)
        # Delete button:
        self.boxes.append(wx.Button(self, wx.ID_ANY, "Delete Face"))
        self.Bind(wx.EVT_BUTTON, self.onRm, id = self.boxes[-1].GetId())
        mainSizer.Add(self.boxes[-1], 0, wx.EXPAND)

        self.SetSizer(mainSizer)
        self.SetAutoLayout(True)

    def onAdd(self, e):
        n = self.boxes[self.__nroFsLenIndex].GetValue()
        l = self.boxes[self.__faceLenIndex].GetValue()
        if l < 1:
            l = self.faceLen
            if l < 1: l = 3
        self.boxes[self.__faceListIndex].grow(n, l)
        self.Layout()

    def onRm(self, e):
        self.boxes[self.__faceListIndex].rmFace(-1)
        self.Layout()
        e.Skip()

    def get(self):
        return self.boxes[self.__faceListIndex].get()

    def set(self, Fs):
        self.boxes[self.__faceListIndex].set(Fs)
        self.Layout()

    def Destroy(self):
        for box in self.boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass

class SymmetrySelect(wx.StaticBoxSizer):
    def __init__(self,
                 panel,
                 label='',
                 groupsList=[isometry.E,
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
                             isometry.A5xI],
                 onSymSelect= None,
                 onGetSymSetup= None):
        """
        Create a control embedded in a sizer for defining a symmetry.

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        groupsList: the list of symmetries that one can choose from.
        onSymSelect: This function will be called after a user selected the
                     symmetry from the list. The first and only parameter of the
                     function is the symmetry class that was selected.
        onGetSymSetup: This function will also be called after a user selected a
                       symmetry from the list, but before onSymSelect. With self
                       function you can return the default setup for the
                       selected symmetry class. The first parameter of self
                       function is the index in the symmetries list. If self
                       function is not set, the class default is used. The class
                       default is also used if the function returns None.
        """
        self.groupsList = groupsList
        self.onSymSelect = onSymSelect
        self.onGetSymSetup = onGetSymSetup
        self.panel = panel
        self.Boxes = [wx.StaticBox(panel, label = label)]
        self.__prev = {}
        wx.StaticBoxSizer.__init__(self, self.Boxes[-1], wx.VERTICAL)

        self.groupsStrList = [c.__name__ for c in self.groupsList]
        self.Boxes.append(
            wx.Choice(self.panel, wx.ID_ANY, choices=self.groupsStrList)
        )
        self.Boxes[-1].SetSelection(0)
        self.__SymmetryGuiIndex = len(self.Boxes) - 1
        self.panel.Bind(wx.EVT_CHOICE,
                        self.onSetSymmetry, id=self.Boxes[-1].GetId())
        self.Add(self.Boxes[-1], 0, wx.EXPAND)

        self.addSetupGui()

    @property
    def length(self):
        return len(self.groupsList)

    def setList(self, groupsList):
        self.groupsList = groupsList
        # would be nice is wx.Choice has a SetItems()
        self.Boxes[self.__SymmetryGuiIndex].Clear()
        for c in groupsList:
            self.Boxes[self.__SymmetryGuiIndex].Append(c.__name__)
        # Not so good: self requires that E should be last...
        self.Boxes[self.__SymmetryGuiIndex].SetSelection(len(groupsList)-1)
        self.addSetupGui()
        self.panel.Layout()

    def getSelectedIndex(self):
        return self.Boxes[self.__SymmetryGuiIndex].GetSelection()

    def getSymmetryClass(self, applyOrder=True):
        """returns a symmetry class"""
        #print 'getSymmetryClass'bad-whitespace
        Id = self.getSelectedIndex()
        selClass = self.groupsList[Id]
        #print 'getSymmetryClass: nr:', Id, 'class:', selClass.__name__, selClass
        if applyOrder:
            if selClass in [isometry.Cn,
                            isometry.CnxI,
                            isometry.C2nCn,
                            isometry.DnCn,
                            isometry.Dn,
                            isometry.DnxI,
                            isometry.D2nDn]:
                assert selClass.init_pars[0]['type'] == 'int', (
                    'The first index should specify the n-order')
                n = self.oriGuis[0].GetValue()
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
            elif selClass in [isometry.E,
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
                              isometry.A5xI]:
                pass
            else:
                assert False, 'unknown class %s' % selClass
                #print 'warning: unknown class', selClass
        #print 'selClass', selClass, 'n:', selClass.n
        return selClass

    def addSetupGui(self):
        self.chk_if_updated = []
        try:
                for gui in self.oriGuis:
                    gui.Destroy()
                self.oriGuiBox.Destroy()
                self.Remove(self.oriSizer)
        except AttributeError: pass
        self.oriGuiBox = wx.StaticBox(self.panel, label='Symmetry Setup')
        self.oriSizer = wx.StaticBoxSizer(self.oriGuiBox, wx.VERTICAL)
        self.oriGuis = []
        sym = self.getSymmetryClass(applyOrder=False)
        if self.onGetSymSetup == None:
            symSetup = sym.std_setup
        else:
            symSetup = self.onGetSymSetup(self.getSelectedIndex())
            if symSetup == None:
                symSetup = sym.std_setup
        for init in sym.init_pars:
            inputType = init['type']
            if inputType == 'vec3':
                gui = Vector3DInput(self.panel, init['lab'],
                                    v=symSetup[init['par']])
            elif inputType == 'int':
                gui = LabeledIntInput(self.panel, init['lab'],
                                      init=symSetup[init['par']])
                self.chk_if_updated.append(gui)
            else:
                assert False, "oops unimplemented input type"
            self.oriGuis.append(gui)
            self.oriSizer.Add(self.oriGuis[-1], 1, wx.EXPAND)
        self.Add(self.oriSizer, 1, wx.EXPAND)

    def onSetSymmetry(self, e):
        self.addSetupGui()
        self.panel.Layout()
        if self.onSymSelect != None:
            self.onSymSelect(self.getSymmetryClass(applyOrder=False))

    def isSymClassUpdated(self):
        try:
            curId = self.getSelectedIndex()
            is_updated = self.__prev['selectedId'] != curId
            if self.chk_if_updated and not is_updated:
                for gui in self.chk_if_updated:
                    is_updated = gui.val_updated
                    if is_updated:
                        break
        except KeyError:
            is_updated = True
        self.__prev['selectedId'] = curId
        return is_updated

    def isUpdated(self):
        isUpdated = self.isSymClassUpdated()
        curSetup = []
        sym = self.getSymmetryClass(applyOrder=False)
        for i, gui in zip(range(len(self.oriGuis)), self.oriGuis):
            inputType = sym.init_pars[i]['type']
            if inputType == 'vec3':
                v = gui.GetVertex()
            elif inputType == 'int':
                v = gui.GetValue()
            curSetup.append(v)
        try:
            prevSetup = self.__prev['setup']
            if len(prevSetup) == len(curSetup):
                for i in range(len(prevSetup)):
                    if prevSetup[i] != curSetup[i]:
                        isUpdated = True
                        break
            else:
                isUpdated = True
        except KeyError:
            isUpdated = True
        self.__prev['setup'] = curSetup
        #print 'isUpdated', isUpdated
        return isUpdated

    def SetSelectedClass(self, cl):
        found = False
        for i, cl_i in zip(range(len(self.groupsList)), self.groupsList):
            if cl == cl_i:
                found = True
                break;
        if found:
            self.SetSelected(i)
        else:
            print 'Warning: SetSelectedClass: class not found'

    def SetSelected(self, i):
        self.Boxes[self.__SymmetryGuiIndex].SetSelection(i)

    def SetupSymmetry(self, vec):
        assert len(vec) == len(self.oriGuis),\
                "Wrong nr of initialisers for self symmetry"
        sym = self.getSymmetryClass(applyOrder=False)
        for i, gui in zip(range(len(self.oriGuis)), self.oriGuis):
            inputType = sym.init_pars[i]['type']
            if inputType == 'vec3':
                v = gui.SetVertex(vec[i])
            elif inputType == 'int':
                v = gui.SetValue(vec[i])

    def GetSelected(self):
        """returns a symmetry instance"""
        sym = self.getSymmetryClass(applyOrder=False)
        setup = {}
        for i, gui in zip(range(len(self.oriGuis)), self.oriGuis):
            inputType = sym.init_pars[i]['type']
            if inputType == 'vec3':
                v = gui.GetVertex()
                if v != geomtypes.Vec3([0, 0, 0]):
                    setup[sym.init_pars[i]['par']] = v
            elif inputType == 'int':
                v = gui.GetValue()
                setup[sym.init_pars[i]['par']] = v
        #print 'GetSelected; setup:', setup
        #print 'class:', sym
        sym = sym(setup=setup)

        return sym

    def Destroy(self):
        for box in self.Boxes + self.oriGuis + self.stabGuis:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError: pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        #wx.StaticBoxSizer.Destroy(self)

class AxisRotateSizer(wx.BoxSizer):
    def __init__(self,
                 panel,
                 on_angle_callback,
                 min_angle=-180,
                 max_angle=180,
                 initial_angle=0):
        """
        Create a sizer for setting a rotation.

        The GUI contains some fields to set the axis and the angle. The latter
        can be set directly, by slide-bar or step by step for which the step can
        be defined through a floating point number.

        panel: the panel to add the widgets to
        on_angle_callback: call-back the will be called with the new angle and
                           axis every time the angle is updated.
        min_angle: minimum of the angle domain for the slide bar.
        max_angle: maximum of the angle domain for the slide bar.
        initial_angle: the angle that will be used from the beginning.
        """
        self.currentAngle = initial_angle
        self.on_angle = on_angle_callback
        self.panel = panel
        self.showGui = []
        wx.BoxSizer.__init__(self, wx.VERTICAL)

        # Rotate Axis
        # - rotate axis and set angle (button and float input)
        rotateSizerTop = wx.BoxSizer(wx.HORIZONTAL)
        self.Add(rotateSizerTop, 0, wx.EXPAND)
        self.showGui.append(Vector3DInput(panel, "Rotate around Axis:"))
        rotateSizerTop.Add(self.showGui[-1], 0)
        self.__AxisGuiIndex = len(self.showGui) - 1
        self.showGui.append(wx.Button(panel, wx.ID_ANY, "Angle:"))
        panel.Bind(
            wx.EVT_BUTTON, self.onDirAngleAdjust, id=self.showGui[-1].GetId())
        rotateSizerTop.Add(self.showGui[-1], 0, wx.EXPAND)
        self.showGui.append(FloatInput(panel, wx.ID_ANY, initial_angle))
        self.showGui[-1].bind_on_set(self.on_angle_set)
        self.__DirAngleGuiIndex = len(self.showGui) - 1
        rotateSizerTop.Add(self.showGui[-1], 0, wx.EXPAND)
        # - slidebar and +/- step (incl. float input)
        rotateSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Add(rotateSizer, 0, wx.EXPAND)
        self.showGui.append(wx.Slider(
            panel,
            value=initial_angle,
            minValue=min_angle,
            maxValue=max_angle,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS
        ))
        self.__SlideAngleGuiIndex = len(self.showGui) - 1
        panel.Bind(wx.EVT_SLIDER,
                   self.onSlideAngleAdjust,
                   id=self.showGui[-1].GetId())
        rotateSizer.Add(self.showGui[-1], 1, wx.EXPAND)
        self.showGui.append(wx.Button(panel, wx.ID_ANY, "-"))
        panel.Bind(
            wx.EVT_BUTTON, self.onDirAngleStepDown, id=self.showGui[-1].GetId())
        rotateSizer.Add(self.showGui[-1], 0, wx.EXPAND)
        self.showGui.append(wx.Button(panel, wx.ID_ANY, "+"))
        panel.Bind(
            wx.EVT_BUTTON, self.onDirAngleStepUp, id=self.showGui[-1].GetId())
        rotateSizer.Add(self.showGui[-1], 0, wx.EXPAND)
        self.showGui.append(FloatInput(panel, wx.ID_ANY, 0.1))
        self.__DirAngleStepIndex = len(self.showGui) - 1
        rotateSizer.Add(self.showGui[-1], 0, wx.EXPAND)

    def get_axis(self):
        return self.showGui[self.__AxisGuiIndex].GetVertex()

    def set_axis(self, axis):
        self.showGui[self.__AxisGuiIndex].SetVertex(axis)

    def get_angle(self):
        return self.currentAngle

    def set_angle(self, angle):
        self.showGui[self.__SlideAngleGuiIndex].SetValue(angle)
        self.showGui[self.__DirAngleGuiIndex].SetValue(angle)

    def on_angle_set(self, angle):
        self.currentAngle = angle
        self.showGui[self.__SlideAngleGuiIndex].SetValue(angle)
        self.on_angle(self.currentAngle, self.get_axis())

    def onDirAngleAdjust(self, e):
        self.currentAngle = self.showGui[self.__DirAngleGuiIndex].GetValue()
        self.showGui[self.__SlideAngleGuiIndex].SetValue(self.currentAngle)
        self.on_angle(self.currentAngle, self.get_axis())
        if e != None:
            e.Skip()

    def onDirAngleStep(self, e, step):
        self.currentAngle += step
        # Update input float with precise input
        self.showGui[self.__DirAngleGuiIndex].SetValue(self.currentAngle)
        # Update slide bar (which rounds to integer
        self.showGui[self.__SlideAngleGuiIndex].SetValue(self.currentAngle)
        self.on_angle(self.currentAngle, self.get_axis())
        if e != None:
            e.Skip()

    def onDirAngleStepDown(self, e):
        self.onDirAngleStep(e, -self.showGui[self.__DirAngleStepIndex].GetValue())
        if e != None:
            e.Skip()

    def onDirAngleStepUp(self, e):
        self.onDirAngleStep(e, self.showGui[self.__DirAngleStepIndex].GetValue())
        if e != None:
            e.Skip()

    def onSlideAngleAdjust(self, e):
        # Do not update the direct float input for better user experience.
        # In that case the user can set the value, use the slide bar and jump
        # jump back to the old value, that is still in the float input.
        self.currentAngle = self.showGui[self.__SlideAngleGuiIndex].GetValue()
        self.on_angle(self.currentAngle, self.get_axis())
        if e != None:
            e.Skip()
