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
# Old sins:
# pylint: disable=too-many-lines,too-many-return-statements,
# pylint: disable=too-many-locals,too-many-statements,too-many-ancestors
# pylint: disable=too-many-instance-attributes,too-many-arguments
# pylint: disable=too-many-branches,too-many-nested-blocks
# pylint: disable=protected-access

from __future__ import print_function

import wx
import wx.lib.scrolledpanel as wxXtra

import geomtypes
import isometry

# TODO:
# - filter faces for FacesInput.GetFace (negative nrs, length 2, etc)


def opposite_orientation(orientation):
    if orientation == wx.HORIZONTAL:
        return wx.VERTICAL
    return wx.HORIZONTAL


class DisabledDropTarget(wx.TextDropTarget):
    def __init__(self, reason='for some reason', enable_reason=True):
        self.reason = reason
        self.enable_reason = enable_reason
        wx.TextDropTarget.__init__(self)

    def OnDragOver(self, x, y, d):
        if self.enable_reason:
            print(self.__class__, 'drag from text disabled 0:', self.reason)
        return ''


class IntInput(wx.TextCtrl):
    def __init__(self, parent, ident, value, *args, **kwargs):
        wx.TextCtrl.__init__(self, parent, ident, str(value), *args, **kwargs)
        # Set defaults: style and width if not set by caller
        # self.SetStyle(0, -1, wx.TE_PROCESS_ENTER | wx.TE_DONTWRAP)
        self.val_updated = False
        self.SetMaxLength(18)
        self.SetDropTarget(DisabledDropTarget(
            reason='may break string format for floating point'))
        self.Bind(wx.EVT_CHAR, self.on_char)

    def on_char(self, e):
        k = e.GetKeyCode()  # ASCII is returned for ASCII values
        updated = True  # except for some cases below
        try:
            c = chr(k)
        except ValueError:
            c = 0
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
                    end_select = sel[0]+1
                else:
                    self.Replace(sel[0], sel[1], '')
                    end_select = sel[0]
                self.SetSelection(sel[0], end_select)
                # self.SetInsertionPoint(sel[0])
            s = wx.TextCtrl.GetValue(self)
            # only allow one +, -
            if c not in s:
                # only allow + and - in the beginning
                print(' not c in s:', self.GetInsertionPoint())
                if self.GetInsertionPoint() == 0:
                    # don't allow - if there's already a + and the other way
                    # around:
                    if c == '+':
                        if '-' not in s:
                            e.Skip()
                    else:
                        if '+' not in s:
                            e.Skip()
                else:
                    # allow selected whole string start with -
                    if self.GetSelection()[0] == 0 and c == '-':
                        self.Replace(0, 1, '-0')
                        self.SetSelection(1, 2)
        elif k in [wx.WXK_BACK, wx.WXK_DELETE]:
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
        elif k in [wx.WXK_RETURN, wx.WXK_TAB,
                   wx.WXK_LEFT, wx.WXK_RIGHT,
                   wx.WXK_INSERT,
                   wx.WXK_HOME, wx.WXK_END]:
            updated = False
            e.Skip()
        else:
            updated = False
            print(self.__class__, 'ignores key event with code:', k)
        # elif k >= 256:
        #     e.Skip()
        self.val_updated = updated

    def GetValue(self):
        v = wx.TextCtrl.GetValue(self)
        self.val_updated = False
        if v == '':
            v = '0'
        return int(v)

    def SetValue(self, i):
        self.val_updated = True
        wx.TextCtrl.SetValue(self, str(i))


class FloatInput(wx.TextCtrl):
    def __init__(self, parent, ident, value, *args, **kwargs):
        wx.TextCtrl.__init__(self, parent, ident, str(value), *args, **kwargs)
        # Set defaults: style and width if not set by caller
        # self.SetStyle(0, -1, wx.TE_PROCESS_ENTER | wx.TE_DONTWRAP)
        self.SetMaxLength(18)
        self.SetDropTarget(DisabledDropTarget(
            reason='may break string format for floating point'))
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.on_set = None

    def bind_on_set(self, on_set):
        """
        Bind the function on_set to be called with the current value when the
        field is set

        The field is set when ENTER / TAB is pressed
        """
        self.on_set = on_set

    def on_char(self, e):
        k = e.GetKeyCode()  # ASCII is returned for ASCII values
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
                    end_select = sel[0]+1
                else:
                    self.Replace(sel[0], sel[1], '')
                    end_select = sel[0]
                self.SetSelection(sel[0], end_select)
                # self.SetInsertionPoint(sel[0])
            s = wx.TextCtrl.GetValue(self)
            # only allow one +, -, or .
            if c not in s:
                if c == '.':
                    e.Skip()
                else:  # '+' or '-'
                    # only allow + and - in the beginning
                    if self.GetInsertionPoint() == 0:
                        # don't allow - if there's already a + and the other
                        # way around:
                        if c == '+':
                            if '-' not in s:
                                e.Skip()
                        else:
                            if '+' not in s:
                                e.Skip()
                    else:
                        # allow selected whole string start with -
                        if self.GetSelection()[0] == 0 and c == '-':
                            self.Replace(0, 1, '-0')
                            self.SetSelection(1, 2)

        elif k in [wx.WXK_BACK, wx.WXK_DELETE]:
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
            if self.on_set is not None:
                self.on_set(self.GetValue())
            e.Skip()
        elif k in [wx.WXK_LEFT, wx.WXK_RIGHT,
                   wx.WXK_INSERT,
                   wx.WXK_HOME, wx.WXK_END]:
            e.Skip()
        elif e.ControlDown():
            if rkc == ord('v'):
                self.Paste()
            elif rkc == ord('c'):
                self.Copy()
            elif rkc == ord('x'):
                self.Cut()
            else:
                print(self.__class__, 'ignores Ctrl-key event with code:', rkc)
        else:
            print(self.__class__, 'ignores key event with code:', k)
        # elif k >= 256:
        #     e.Skip()

    def GetValue(self):
        v = wx.TextCtrl.GetValue(self)
        if v == '':
            v = '0'
            self.SetValue(v)
        return float(v)

    def SetValue(self, f):
        wx.TextCtrl.SetValue(self, str(f))


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
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former
                     is default. Defines the orientation of the label - int
                     input.
        """
        self.boxes = []
        wx.BoxSizer.__init__(self, orientation)
        self.boxes.append(
            wx.StaticText(panel, wx.ID_ANY, label + ' ',
                          style=wx.ALIGN_RIGHT))
        self.Add(self.boxes[-1], 1, wx.EXPAND)
        if not isinstance(init, int):
            print('{} warning: initialiser not an int ({})'.format(
                self.__class__, str(init)))
            init = 0
        self.boxes.append(IntInput(
            panel, wx.ID_ANY, init, size=(width, -1)))
        self.Add(self.boxes[-1], 0, wx.EXPAND)
        self.int_gui_idx = len(self.boxes) - 1

    @property
    def val_updated(self):
        return self.boxes[self.int_gui_idx].val_updated

    def GetValue(self):
        return self.boxes[-1].GetValue()

    def SetValue(self, i):
        return self.boxes[-1].SetValue(i)

    def Destroy(self, *args, **kwargs):
        for box in self.boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError:
                pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        # wx.StaticBoxSizer.Destroy(self)


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
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former
                     is default. Defines the orientation of the separate vector
                     items.
        elem_labels: option labels for the vector items. It is an array
                       consisting of 4 strings On default
                       ['index', 'x', 'y', 'z'] is used.
        """
        self.panel = panel
        self.boxes = []
        wx.BoxSizer.__init__(self, orientation)
        self.boxes.append(
            wx.StaticText(self.panel, wx.ID_ANY, label + ' ',
                          style=wx.ALIGN_RIGHT))
        self.Add(self.boxes[-1], 1, wx.EXPAND)
        self._vec = []
        for _ in range(3):
            self._vec.append(FloatInput(self.panel, wx.ID_ANY, 0))
            self.Add(self._vec[-1], 0, wx.EXPAND)
        if v is not None:
            self.set_vertex(v)

    def get_vertex(self):
        return geomtypes.Vec3([self._vec[0].GetValue(),
                               self._vec[1].GetValue(),
                               self._vec[2].GetValue()])

    def set_vertex(self, v):
        for i in v:
            if not isinstance(i, (float, int)):
                print('{} warning: v[{}] not a number ({})'.format(
                    self.__class__, v.index(i), str(i)))
                return
        self._vec[0].SetValue(v[0])
        self._vec[1].SetValue(v[1])
        self._vec[2].SetValue(v[2])

    def Destroy(self, *args, **kwargs):
        for ctrl in self._vec:
            ctrl.Destroy()
        for box in self.boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError:
                pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        # wx.StaticBoxSizer.Destroy(self)


class Vector3DSetStaticPanel(wxXtra.ScrolledPanel):
    __hlabels = ['index', 'x', 'y', 'z']

    def __init__(self, parent, length, orientation=wx.HORIZONTAL):
        """
        Create a panel defining a set of 3D vectors

        parent: the parent widget.
        length: initialise with length amount of 3D vectors.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former
                     is default. Defines the orientation of the separate vector
                     items.
        """

        wxXtra.ScrolledPanel.__init__(self, parent)

        self.boxes = []
        opp_orient = opposite_orientation(orientation)
        vectors_sizer = wx.BoxSizer(orientation)
        self.column_sizers = []  # align vector columns
        # header:
        scale = 0
        for i in range(len(self.__hlabels)):
            self.boxes.append(
                wx.StaticText(self, wx.ID_ANY, self.__hlabels[i])
            )
            self.column_sizers.append(wx.BoxSizer(opp_orient))
            self.column_sizers[i].Add(self.boxes[-1], 0,
                                      wx.ALIGN_CENTRE_HORIZONTAL)
            vectors_sizer.Add(self.column_sizers[i], scale, wx.EXPAND)
            scale = 1
        # vectors:
        self._vec = []
        self._vec_labels = []
        self.grow(length)

        # use a list sizer to be able to fill white space for list with vectors
        # that are too small (cannot remove the wx.EXPAND above since the
        # vector columns need to be aligned.
        list_sizer = wx.BoxSizer(opp_orient)
        list_sizer.Add(vectors_sizer, 0)
        list_sizer.Add(wx.BoxSizer(orientation), 0, wx.EXPAND)

        self.SetSizer(list_sizer)
        self.SetAutoLayout(True)
        self.SetupScrolling()

    def grow(self, nr=1, vs=None):
        assert vs is None or len(vs) == nr
        for n in range(nr):
            j = len(self._vec)
            self._vec_labels.append(
                wx.StaticText(self, wx.ID_ANY,
                              '{} '.format(j),
                              style=wx.TE_CENTRE)
            )
            self.column_sizers[0].Add(self._vec_labels[-1], 1)
            self._vec.append([])
            for i in range(1, len(self.__hlabels)):
                if vs is None:
                    f = 0
                else:
                    f = vs[n][i-1]
                self._vec[-1].append(FloatInput(self, wx.ID_ANY, f))
                self.column_sizers[i].Add(self._vec[-1][-1], 1, wx.EXPAND)
        self.Layout()

    def extend(self, verts):
        self.grow(len(verts), verts)

    def rm_vector(self, i):
        if self._vec_labels:
            assert i < len(self._vec_labels)
            g = self._vec_labels[i]
            del self._vec_labels[i]
            g.Destroy()
            v = self._vec[i]
            del self._vec[i]
            for g in v:
                g.Destroy()
            self.Layout()
        else:
            print('{} warning: nothing to delete.'.format(
                self.__class__.__name__))

    def get_vector(self, i):
        return geomtypes.Vec3([self._vec[i][0].GetValue(),
                               self._vec[i][1].GetValue(),
                               self._vec[i][2].GetValue()])

    def get(self):
        return [
            self.get_vector(i) for i in range(len(self._vec))
        ]

    def clear(self):
        for _ in range(len(self._vec)):
            self.rm_vector(-1)

    def set(self, verts):
        self.clear()
        self.extend(verts)

    def Destroy(self, *args, **kwargs):
        for ctrl in self._vec:
            ctrl.Destroy()
        for ctrl in self._vec_labels:
            ctrl.Destroy()
        for box in self.boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError:
                pass

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
                 rel_xtra_space=5,
                 orientation=wx.HORIZONTAL,
                 elem_labels=None):
        """
        Create a control embedded in a sizer for defining a set of 3D vectors

        parent: the parent widget.
        length: initialise the input with length amount of 3D vectors.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former
                     is default. Defines the orientation of the separate vector
                     items.
        elem_labels: option labels for the vector items. It is an array
                       consisting of 4 strings On default
                       ['index', 'x', 'y', 'z'] is used.
        """
        self.parent = parent
        wx.Panel.__init__(self, parent)

        self.boxes = []
        opp_orient = opposite_orientation(orientation)
        main_sizer = wx.BoxSizer(opp_orient)

        # Add vertex list
        self.boxes.append(Vector3DSetStaticPanel(self, length, orientation))
        main_sizer.Add(self.boxes[-1], rel_xtra_space, wx.EXPAND)
        # Add button:
        add_sizer = wx.BoxSizer(orientation)
        self.boxes.append(wx.Button(self, wx.ID_ANY, "Vertices Add Times:"))
        add_sizer.Add(self.boxes[-1], 1, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.on_add, id=self.boxes[-1].GetId())
        self.boxes.append(IntInput(self, wx.ID_ANY, 1, size=(40, -1)))
        self._add_no_of_v_idx = len(self.boxes) - 1
        add_sizer.Add(self.boxes[-1], 0, wx.EXPAND)
        main_sizer.Add(add_sizer, 1, wx.EXPAND)

        # Clear and Delete buttons:
        rm_sizer = wx.BoxSizer(orientation)
        # Clear:
        self.boxes.append(wx.Button(self, wx.ID_ANY, "Clear"))
        self.Bind(wx.EVT_BUTTON, self.on_clear, id=self.boxes[-1].GetId())
        rm_sizer.Add(self.boxes[-1], 1, wx.EXPAND)
        # Delete:
        self.boxes.append(wx.Button(self, wx.ID_ANY, "Delete Vertex"))
        self.Bind(wx.EVT_BUTTON, self.on_rm, id=self.boxes[-1].GetId())
        rm_sizer.Add(self.boxes[-1], 1, wx.EXPAND)
        main_sizer.Add(rm_sizer, 1, wx.EXPAND)

        self.SetSizer(main_sizer)
        self.SetAutoLayout(True)

    def on_add(self, e):
        no = self.boxes[self._add_no_of_v_idx].GetValue()
        self.boxes[0].grow(no)
        self.Layout()
        e.Skip()

    def on_rm(self, e):
        self.boxes[0].rm_vector(-1)
        self.Layout()
        e.Skip()

    def on_clear(self, e):
        self.boxes[0].clear()
        self.Layout()
        e.Skip()

    def set(self, verts):
        self.boxes[0].set(verts)
        self.Layout()

    def get(self):
        return self.boxes[0].get()


MY_EVT_VECTOR_UPDATED = wx.NewEventType()
EVT_VECTOR_UPDATED = wx.PyEventBinder(MY_EVT_VECTOR_UPDATED, 1)


class VectorUpdatedEvent(wx.PyCommandEvent):
    """Event to express that a vector (element) was updated"""
    def __init__(self, evtType, i_d):
        """Initialise the event with type and ID of window"""
        wx.PyCommandEvent.__init__(self, evtType, i_d)
        self.vector = None

    def set_vector(self, vector):
        """Set the whole resulting vector from the update"""
        self.vector = vector

    def get_vector(self):
        """Get the whole resulting vector after the update"""
        return self.vector


class Vector4DInput(wx.StaticBoxSizer):
    """A control embedded in a sizer for defining 4D vectors"""
    # To be able to connect event, add an ID, use the ID of one of the
    # elements. Always use the same with the following index:
    __ctrlIdIndex = 0
    __defaultLabels = ['x', 'y', 'z', 'w']

    def __init__(self,
                 panel,
                 label='',
                 orientation=wx.HORIZONTAL,
                 rel_float_size=4,
                 elem_labels=None):
        """
        Create a control embedded in a sizer for defining 4D vectors

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former
                     is default. Defines the orientation of the separate vector
                     items.
        rel_float_size: it defines the size of the input fields relative to
                           the vector item labels 'x', 'y',..,'z' (with size 1)
        elem_labels: option labels for the vector items. It is an array
                       consisting of 4 strings On default ['x', 'y', 'z', 'w']
                       is used.
        """
        self.boxes = [wx.StaticBox(panel, label=label)]
        wx.StaticBoxSizer.__init__(self, self.boxes[-1], orientation)
        if elem_labels is None:
            elem_labels = self.__defaultLabels
        self._vec_label = [
            wx.StaticText(panel, wx.ID_ANY, elem_labels[0],
                          style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL),
            wx.StaticText(panel, wx.ID_ANY, elem_labels[1],
                          style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL),
            wx.StaticText(panel, wx.ID_ANY, elem_labels[2],
                          style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL),
            wx.StaticText(panel, wx.ID_ANY, elem_labels[3],
                          style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL)
        ]
        self._vec = [
            FloatInput(panel, wx.ID_ANY, 0),
            FloatInput(panel, wx.ID_ANY, 0),
            FloatInput(panel, wx.ID_ANY, 0),
            FloatInput(panel, wx.ID_ANY, 0)
        ]
        for i in range(4):
            if orientation == wx.HORIZONTAL:
                self.Add(self._vec_label[i], 1,
                         wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL)
                self.Add(self._vec[i], rel_float_size, wx.EXPAND)
            else:
                b_sizer = wx.BoxSizer(wx.HORIZONTAL)
                b_sizer.Add(self._vec_label[i], 1,
                            wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL)
                b_sizer.Add(self._vec[i], rel_float_size, wx.EXPAND)
                self.Add(b_sizer, 1, wx.EXPAND)
            panel.Bind(wx.EVT_TEXT, self.on_float, id=self._vec[i].GetId())

    def GetId(self):
        """Returns the identifier of the 'window'"""
        return self._vec[self.__ctrlIdIndex].GetId()

    def on_float(self, _):
        """Update the complete 4D vector

        This creats a MY_EVT_VECTOR_UPDATED event
        """
        # ctrlId = e.GetId()
        vec_event = VectorUpdatedEvent(MY_EVT_VECTOR_UPDATED, self.GetId())
        vec_event.SetEventObject(self)
        vec_event.set_vector(geomtypes.Vec4([self._vec[0].GetValue(),
                                             self._vec[1].GetValue(),
                                             self._vec[2].GetValue(),
                                             self._vec[3].GetValue()]))
        self._vec[self.__ctrlIdIndex].GetEventHandler().ProcessEvent(vec_event)

    def GetValue(self):
        """Get the defined 4D vector"""
        return geomtypes.Vec4([self._vec[0].GetValue(),
                               self._vec[1].GetValue(),
                               self._vec[2].GetValue(),
                               self._vec[3].GetValue()])

    def Destroy(self, *args, **kwargs):
        for ctrl in self._vec_label:
            ctrl.Destroy()
        for ctrl in self._vec:
            ctrl.Destroy()
        for box in self.boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError:
                pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        # wx.StaticBoxSizer.Destroy(self)


class FaceSetStaticPanel(wxXtra.ScrolledPanel):
    """A control embedded in a sizer for defining a set of faces

    This cannot grow or shrink in size through a GUI itself
    """
    def __init__(self,
                 parent,
                 no_of_faces=0,
                 face_len=0,
                 width=40,
                 orientation=wx.HORIZONTAL):
        """
        Create a control embedded in a sizer for defining a set of faces

        parent: the parent widget.
        no_of_faces: initialise the input with no_of_faces amount of faces.
        face_len: initialise the faces with face_len vertices. Also the default
                  value for adding faces.
        width: width of the face index fields.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former
                     is default. Defines the orientation of the separate face
                     items.
        """
        wxXtra.ScrolledPanel.__init__(self, parent)
        self.parent = parent
        self.width = width
        self.face_len = face_len
        self.orientation = orientation
        opp_orient = opposite_orientation(orientation)

        self._faces = []
        self._faces_labels = []
        self.face_idx_sizer = wx.BoxSizer(opp_orient)  # align face indices
        self.vertex_idx_sizer = wx.BoxSizer(opp_orient)
        faces_sizer = wx.BoxSizer(orientation)
        faces_sizer.Add(self.face_idx_sizer, 0, wx.EXPAND)
        faces_sizer.Add(self.vertex_idx_sizer, 0, wx.EXPAND)

        self.grow(no_of_faces, face_len)

        # use a list sizer to be able to fill white space if the face list
        # word is too small
        list_sizer = wx.BoxSizer(opp_orient)
        list_sizer.Add(faces_sizer, 0)
        list_sizer.Add(wx.BoxSizer(orientation), 0, wx.EXPAND)

        self.SetSizer(list_sizer)
        self.SetAutoLayout(True)
        self.SetupScrolling()

    def add_face(self, face_len=0, face=None):
        """Add a face to the list, either undefined or one specific face.

        face_len: specify this if you want to add an undefined face (indices
                  will equal to 0)
        face: if this list of indices is specified, face_len will be ignored.
              This list of indices will be added to the GUI at the end of the
              list.
        """
        assert face_len != 0 or face is not None
        if face is not None:
            face_len = len(face)
        j = len(self._faces_labels)
        self._faces_labels.append(wx.StaticText(self, wx.ID_ANY,
                                                '{} '.format(j)))
        self.face_idx_sizer.Add(self._faces_labels[-1],
                                1, wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL)

        face_sizer = wx.BoxSizer(self.orientation)
        self._faces.append([face_sizer])
        for i in range(face_len):
            if face is not None:
                val = face[i]
            else:
                val = 0
            self._faces[-1].append(
                IntInput(self, wx.ID_ANY, val, size=(self.width, -1))
            )
            face_sizer.Add(self._faces[-1][-1], 0, wx.EXPAND)
        self.vertex_idx_sizer.Add(face_sizer, 0, wx.EXPAND)

        self.Layout()

    def rm_face(self, i):
        """Remove the face with index i from the list of faces"""
        if self._faces_labels:
            assert i < len(self._faces_labels)
            assert self._faces
            g = self._faces_labels[i]
            del self._faces_labels[i]
            g.Destroy()
            f = self._faces[i]
            del self._faces[i]
            self.vertex_idx_sizer.Remove(f[0])
            del f[0]
            for g in f:
                g.Destroy()
            self.Layout()

    def get_face(self, index):
        """Get the face (a list) with index 'index'"""
        return [self._faces[index][i].GetValue()
                for i in range(1, len(self._faces[index]))]

    def grow(self, times, face_len):
        """Add undefined faces to the face list

        times: how many times to add a face
        face_len: the length of the faces to add
        """
        for _ in range(times):
            self.add_face(face_len)

    def extend(self, faces):
        """To the end of the list of faces add these specified faces"""
        for f in faces:
            self.add_face(face=f)

    def get(self):
        """Get the list of faces specified"""
        return [
            self.get_face(i) for i in range(len(self._faces))
        ]

    def clear(self):
        """Remove all faces from the list"""
        for _ in range(len(self._faces)):
            self.rm_face(-1)

    def set(self, faces):
        """Set the list of faces"""
        self.clear()
        self.extend(faces)

    def Destroy(self, *args, **kwargs):
        for ctrl in self._faces_labels:
            ctrl.Destroy()
        for ctrl in self._faces:
            ctrl.Destroy()

    # TODO Insert?


class FaceSetDynamicPanel(wx.Panel):
    """A control for defining a set of faces, which can grow and shrink"""
    def __init__(self,
                 parent,
                 no_of_faces=0,
                 face_len=0,
                 orientation=wx.HORIZONTAL):
        """
        Create a control for defining a set of faces

        The control can grow and shrink in size.
        parent: the parent widget.
        no_of_faces: initialise the input with no_of_faces amount of faces.
        face_len: initialise the faces with face_len vertices. Also the default
                  value for adding faces.
        width: width of the face index fields.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former
                     is default. Defines the orientation of the separate face
                     items.
        """
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.face_len = face_len

        self.boxes = []
        opp_orient = opposite_orientation(orientation)
        main_sizer = wx.BoxSizer(opp_orient)

        # Add face list
        self.boxes.append(FaceSetStaticPanel(self, no_of_faces, face_len,
                                             orientation=orientation))
        self._face_lst_idx = len(self.boxes) - 1
        main_sizer.Add(self.boxes[-1], 10, wx.EXPAND)

        # Add button:
        add_sizer = wx.BoxSizer(orientation)
        self.boxes.append(IntInput(
            self, wx.ID_ANY, face_len, size=(40, -1)))
        self._face_len_idx = len(self.boxes) - 1
        add_sizer.Add(self.boxes[-1], 0, wx.EXPAND)
        self.boxes.append(wx.Button(self, wx.ID_ANY, "-Faces Add Times:"))
        add_sizer.Add(self.boxes[-1], 1, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.on_add, id=self.boxes[-1].GetId())
        self.boxes.append(IntInput(self, wx.ID_ANY, 1, size=(40, -1)))
        self._nr_of_faces_idx = len(self.boxes) - 1
        add_sizer.Add(self.boxes[-1], 0, wx.EXPAND)
        main_sizer.Add(add_sizer, 0, wx.EXPAND)
        # Delete button:
        self.boxes.append(wx.Button(self, wx.ID_ANY, "Delete Face"))
        self.Bind(wx.EVT_BUTTON, self._on_rm, id=self.boxes[-1].GetId())
        main_sizer.Add(self.boxes[-1], 0, wx.EXPAND)

        self.SetSizer(main_sizer)
        self.SetAutoLayout(True)

    def on_add(self, _):
        """Add a certain number of faces with some size as defined by GUI"""
        n = self.boxes[self._nr_of_faces_idx].GetValue()
        no = self.boxes[self._face_len_idx].GetValue()
        if no < 1:
            no = self.face_len
            if no < 1:
                no = 3
        self.boxes[self._face_lst_idx].grow(n, no)
        self.Layout()

    def _on_rm(self, e):
        """Remove the last face from list"""
        self.boxes[self._face_lst_idx].rm_face(-1)
        self.Layout()
        e.Skip()

    def get(self):
        """Get the list of faces"""
        return self.boxes[self._face_lst_idx].get()

    def set(self, faces):
        """Set the list of faces"""
        self.boxes[self._face_lst_idx].set(faces)
        self.Layout()

    def Destroy(self, *args, **kwargs):
        for box in self.boxes:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError:
                pass


class SymmetrySelect(wx.StaticBoxSizer):
    """A control embedded in a sizer for defining a symmetry"""
    def __init__(self,
                 panel,
                 label='',
                 groups_lst=None,
                 on_sym_select=None,
                 on_get_sym_setup=None):
        """
        Create a control embedded in a sizer for defining a symmetry.

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        groups_lst: the list of symmetries that one can choose from.
        on_sym_select: This function will be called after a user selected the
                       symmetry from the list. The first and only parameter of
                       the function is the symmetry class that was selected.
        on_get_sym_setup: This function will also be called after a user
                          selected a symmetry from the list, but before
                          on_sym_select. With self function you can return the
                          default setup for the selected symmetry class. The
                          first parameter of self function is the index in the
                          symmetries list. If self function is not set, the
                          class default is used. The class default is also used
                          if the function returns None.
        """
        if groups_lst:
            self.groups_lst = groups_lst
        else:
            self.groups_lst = [isometry.E,
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
                               isometry.A5xI]
        self.on_sym_select = on_sym_select
        self.on_get_sym_setup = on_get_sym_setup
        self.panel = panel
        self.boxes = [wx.StaticBox(panel, label=label)]
        self.__prev = {}
        wx.StaticBoxSizer.__init__(self, self.boxes[-1], wx.VERTICAL)
        self.boxes.append(
            wx.Choice(self.panel,
                      wx.ID_ANY,
                      choices=[c.__name__ for c in self.groups_lst])
        )
        self.boxes[-1].SetSelection(0)
        self._sym_gui_idx = len(self.boxes) - 1
        self.panel.Bind(wx.EVT_CHOICE,
                        self.on_set_sym, id=self.boxes[-1].GetId())
        self.Add(self.boxes[-1], 0, wx.EXPAND)

        self.orient_guis = []
        self.orient_gui_box = None
        self.orient_sizer = None
        self.add_setup_gui()

    @property
    def length(self):
        """Return the amount of symmetry classes that can be selected"""
        return len(self.groups_lst)

    def set_lst(self, groups_lst):
        """Set the list with the symmetry classes that can be selected"""
        self.groups_lst = groups_lst
        # would be nice is wx.Choice has a SetItems()
        self.boxes[self._sym_gui_idx].Clear()
        for c in groups_lst:
            self.boxes[self._sym_gui_idx].Append(c.__name__)
        # Not so good: self requires that E should be last...
        self.boxes[self._sym_gui_idx].SetSelection(len(groups_lst)-1)
        self.add_setup_gui()
        self.panel.Layout()

    def get_selected_idx(self):
        """Return the index of the selected symmetry class"""
        return self.boxes[self._sym_gui_idx].GetSelection()

    def get_sym_class(self, apply_order=True):
        """Return the selected symmetry class"""
        selected_class = self.groups_lst[self.get_selected_idx()]
        if apply_order:
            if selected_class in [isometry.Cn,
                                  isometry.CnxI,
                                  isometry.C2nCn,
                                  isometry.DnCn,
                                  isometry.Dn,
                                  isometry.DnxI,
                                  isometry.D2nDn]:
                assert selected_class.init_pars[0]['type'] == 'int', (
                    'The first index should specify the n-order')
                n = self.orient_guis[0].GetValue()
                if selected_class == isometry.Cn:
                    C = isometry.C
                elif selected_class == isometry.CnxI:
                    C = isometry.CxI
                elif selected_class == isometry.C2nCn:
                    C = isometry.C2nC
                elif selected_class == isometry.DnCn:
                    C = isometry.DnC
                elif selected_class == isometry.Dn:
                    C = isometry.D
                elif selected_class == isometry.D2nDn:
                    C = isometry.D2nD
                elif selected_class == isometry.DnxI:
                    C = isometry.DxI
                assert n > 0, 'warning'
                selected_class = C(n)
            elif selected_class in [isometry.E,
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
                assert False, 'unknown class {}'.format(selected_class)
        return selected_class

    def add_setup_gui(self):
        """Add the GUI that will set up a certain symmetry class

        With set up here is meant how a certain symmetry is oriented of for the
        cyclic and dihedral symmetries the order 'n 'as well
        """
        self.chk_if_updated = []
        if self.orient_guis:
            for gui in self.orient_guis:
                gui.Destroy()
        if self.orient_gui_box:
            self.orient_gui_box.Destroy()
        if self.orient_sizer:
            self.Remove(self.orient_sizer)
        self.orient_gui_box = wx.StaticBox(self.panel, label='Symmetry Setup')
        self.orient_sizer = wx.StaticBoxSizer(self.orient_gui_box, wx.VERTICAL)
        self.orient_guis = []
        sym = self.get_sym_class(apply_order=False)
        if self.on_get_sym_setup is None:
            sym_setup = sym.std_setup
        else:
            sym_setup = self.on_get_sym_setup(self.get_selected_idx())
            if sym_setup is None:
                sym_setup = sym.std_setup
        for init in sym.init_pars:
            input_type = init['type']
            if input_type == 'vec3':
                gui = Vector3DInput(self.panel, init['lab'],
                                    v=sym_setup[init['par']])
            elif input_type == 'int':
                gui = LabeledIntInput(self.panel, init['lab'],
                                      init=sym_setup[init['par']])
                self.chk_if_updated.append(gui)
            else:
                assert False, "oops unimplemented input type"
            self.orient_guis.append(gui)
            self.orient_sizer.Add(self.orient_guis[-1], 1, wx.EXPAND)
        self.Add(self.orient_sizer, 1, wx.EXPAND)

    def on_set_sym(self, _):
        """Function that will set the symmetry"""
        self.add_setup_gui()
        self.panel.Layout()
        if self.on_sym_select is not None:
            self.on_sym_select(self.get_sym_class(apply_order=False))

    def is_sym_class_updated(self):
        """Checks whether the selected symmetry class was updated

        Compared to the previous time this was checked"""
        try:
            cur_idx = self.get_selected_idx()
            is_updated = self.__prev['selectedId'] != cur_idx
            if self.chk_if_updated and not is_updated:
                for gui in self.chk_if_updated:
                    is_updated = gui.val_updated
                    if is_updated:
                        break
        except KeyError:
            is_updated = True
        self.__prev['selectedId'] = cur_idx
        return is_updated

    def is_updated(self):
        """Check whether any property of the symmetry was updated

        Compared to the previous time that was checked"""
        is_updated = self.is_sym_class_updated()
        cur_setup = []
        sym = self.get_sym_class(apply_order=False)
        for i, gui in zip(range(len(self.orient_guis)), self.orient_guis):
            input_type = sym.init_pars[i]['type']
            if input_type == 'vec3':
                v = gui.get_vertex()
            elif input_type == 'int':
                v = gui.GetValue()
            cur_setup.append(v)
        try:
            prev_setup = self.__prev['setup']
            if len(prev_setup) == len(cur_setup):
                for i, ps_i in enumerate(prev_setup):
                    if ps_i != cur_setup[i]:
                        is_updated = True
                        break
            else:
                is_updated = True
        except KeyError:
            is_updated = True
        self.__prev['setup'] = cur_setup
        return is_updated

    def set_selected_class(self, cl):
        """Set the selected symmetry in the drop down menu by class"""
        found = False
        # to shut-up pylint: undefined-loop-variable:
        i = 0
        for i, cl_i in enumerate(self.groups_lst):
            if cl == cl_i:
                found = True
                break
        if found:
            self.set_selected(i)
        else:
            print('Warning: set_selected_class: class not found')

    def set_selected(self, i):
        """Set the selected symmetry in the drop down menu by index"""
        self.boxes[self._sym_gui_idx].SetSelection(i)

    def setup_sym(self, vec):
        """Fill in the symmetry setup fields in the GUI"""
        assert len(vec) == len(self.orient_guis),\
            "Wrong nr of initialisers for self symmetry"\
            "(got {}, expected {})".format(len(vec), len(self.orient_guis))
        sym = self.get_sym_class(apply_order=False)
        for i, gui in zip(range(len(self.orient_guis)), self.orient_guis):
            input_type = sym.init_pars[i]['type']
            if input_type == 'vec3':
                _ = gui.set_vertex(vec[i])
            elif input_type == 'int':
                _ = gui.SetValue(vec[i])

    def get_selected(self):
        """returns a symmetry instance"""
        sym = self.get_sym_class(apply_order=False)
        setup = {}
        for i, gui in zip(range(len(self.orient_guis)), self.orient_guis):
            input_type = sym.init_pars[i]['type']
            if input_type == 'vec3':
                v = gui.get_vertex()
                if v != geomtypes.Vec3([0, 0, 0]):
                    setup[sym.init_pars[i]['par']] = v
            elif input_type == 'int':
                v = gui.GetValue()
                setup[sym.init_pars[i]['par']] = v
        sym = sym(setup=setup)

        return sym

    def Destroy(self, *args, **kwargs):
        for box in self.boxes + self.orient_guis:
            try:
                box.Destroy()
            except wx._core.PyDeadObjectError:
                pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        # wx.StaticBoxSizer.Destroy(self)


class AxisRotateSizer(wx.BoxSizer):
    """Class with sizer for defining a rotation"""
    def __init__(self,
                 panel,
                 on_angle_callback,
                 min_angle=-180,
                 max_angle=180,
                 initial_angle=0):
        """
        Create a sizer for setting a rotation.

        The GUI contains some fields to set the axis and the angle. The latter
        can be set directly, by slide-bar or step by step for which the step
        can be defined through a floating point number.

        panel: the panel to add the widgets to
        on_angle_callback: call-back the will be called with the new angle and
                           axis every time the angle is updated.
        min_angle: minimum of the angle domain for the slide bar.
        max_angle: maximum of the angle domain for the slide bar.
        initial_angle: the angle that will be used from the beginning.
        """
        self.current_angle = initial_angle
        self.on_angle = on_angle_callback
        self.panel = panel
        self.show_gui = []
        wx.BoxSizer.__init__(self, wx.VERTICAL)

        # Rotate Axis
        # - rotate axis and set angle (button and float input)
        rot_sizer_top = wx.BoxSizer(wx.HORIZONTAL)
        self.Add(rot_sizer_top, 0, wx.EXPAND)
        self.show_gui.append(Vector3DInput(panel, "Rotate around Axis:"))
        rot_sizer_top.Add(self.show_gui[-1], 0)
        self._axis_gui_idx = len(self.show_gui) - 1
        self.show_gui.append(wx.Button(panel, wx.ID_ANY, "Angle:"))
        panel.Bind(
            wx.EVT_BUTTON,
            self._on_angle_set,
            id=self.show_gui[-1].GetId())
        rot_sizer_top.Add(self.show_gui[-1], 0, wx.EXPAND)
        self.show_gui.append(FloatInput(panel, wx.ID_ANY, initial_angle))
        self.show_gui[-1].bind_on_set(self._on_angle_typed)
        self._typed_angle_gui_idx = len(self.show_gui) - 1
        rot_sizer_top.Add(self.show_gui[-1], 0, wx.EXPAND)
        # - slidebar and +/- step (incl. float input)
        rot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Add(rot_sizer, 0, wx.EXPAND)
        self.show_gui.append(wx.Slider(panel,
                                       value=initial_angle,
                                       minValue=min_angle,
                                       maxValue=max_angle,
                                       style=wx.SL_HORIZONTAL | wx.SL_LABELS))
        self._slide_angle_gui_idx = len(self.show_gui) - 1
        panel.Bind(wx.EVT_SLIDER,
                   self._on_slide_angle_adjust,
                   id=self.show_gui[-1].GetId())
        rot_sizer.Add(self.show_gui[-1], 1, wx.EXPAND)
        self.show_gui.append(wx.Button(panel, wx.ID_ANY, "-"))
        panel.Bind(
            wx.EVT_BUTTON,
            self._on_angle_step_down,
            id=self.show_gui[-1].GetId())
        rot_sizer.Add(self.show_gui[-1], 0, wx.EXPAND)
        self.show_gui.append(wx.Button(panel, wx.ID_ANY, "+"))
        panel.Bind(
            wx.EVT_BUTTON,
            self._on_angle_step_up,
            id=self.show_gui[-1].GetId())
        rot_sizer.Add(self.show_gui[-1], 0, wx.EXPAND)
        self.show_gui.append(FloatInput(panel, wx.ID_ANY, 0.1))
        self._dir_angle_step_idx = len(self.show_gui) - 1
        rot_sizer.Add(self.show_gui[-1], 0, wx.EXPAND)

    def get_axis(self):
        """Get the direction of the rotation axis in the GUI"""
        return self.show_gui[self._axis_gui_idx].get_vertex()

    def set_axis(self, axis):
        """Set the direction of the rotation axis in the GUI"""
        self.show_gui[self._axis_gui_idx].set_vertex(axis)

    def get_angle(self):
        """Get the current rotation angle"""
        return self.current_angle

    def set_angle(self, angle):
        """Define the angle to be used"""
        self.current_angle = angle
        self.show_gui[self._slide_angle_gui_idx].SetValue(angle)
        self.show_gui[self._typed_angle_gui_idx].SetValue(angle)
        self.on_angle(angle, self.get_axis())

    def _on_angle_typed(self, angle):
        """Called when user types a new angle in the input field"""
        self.current_angle = angle
        self.show_gui[self._slide_angle_gui_idx].SetValue(angle)
        self.on_angle(self.current_angle, self.get_axis())

    def _on_angle_set(self, e):
        """Called when when user presses button to applied typed angle"""
        self.current_angle = self.show_gui[
            self._typed_angle_gui_idx].GetValue()
        self.show_gui[self._slide_angle_gui_idx].SetValue(self.current_angle)
        self.on_angle(self.current_angle, self.get_axis())
        if e is not None:
            e.Skip()

    def _on_angle_step(self, e, step):
        """Shared function for '+' and '-' button for angle adjust"""
        self.current_angle += step
        # Update input float with precise input
        self.show_gui[self._typed_angle_gui_idx].SetValue(self.current_angle)
        # Update slide bar (which rounds to integer
        self.show_gui[self._slide_angle_gui_idx].SetValue(self.current_angle)
        self.on_angle(self.current_angle, self.get_axis())
        if e is not None:
            e.Skip()

    def _on_angle_step_down(self, e):
        """Called when '-' button is pressed to decrease angle"""
        self._on_angle_step(e, -self.show_gui[
            self._dir_angle_step_idx].GetValue())
        if e is not None:
            e.Skip()

    def _on_angle_step_up(self, e):
        """Called when '+' button is pressed to increase angle"""
        self._on_angle_step(e, self.show_gui[
            self._dir_angle_step_idx].GetValue())
        if e is not None:
            e.Skip()

    def _on_slide_angle_adjust(self, e):
        """Called when the angle adjust slider is changed"""
        # Do not update the direct float input for better user experience.
        # In that case the user can set the value, use the slide bar and jump
        # jump back to the old value, that is still in the float input.
        self.current_angle = self.show_gui[
            self._slide_angle_gui_idx].GetValue()
        self.on_angle(self.current_angle, self.get_axis())
        if e is not None:
            e.Skip()
