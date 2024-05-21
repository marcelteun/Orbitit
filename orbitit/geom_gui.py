#!/usr/bin/env python
"""
GUI widgets related to objects with geometry

Like vertices, faecs, symmetries, etc.
"""
#
# Copyright (C) 2010-2024 Marcel Tunnissen
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
# To be able to run pylint for different versions:
# pylint: disable=useless-option-value


import logging
import wx
import wx.lib.scrolledpanel as wx_panel

from orbitit import geomtypes, isometry

# TODO:
# - filter faces for FacesInput.GetFace (negative nrs, length 2, etc)


def opposite_orientation(orientation):
    """Exchange wx.HORIZONTAL for wx.VERTICAL and vice versa"""
    if orientation == wx.HORIZONTAL:
        return wx.VERTICAL
    return wx.HORIZONTAL


class DisabledDropTarget(wx.TextDropTarget):  # pylint: disable=too-few-public-methods
    """A drop target that doesn't allow dropping anything"""

    def __init__(self, reason="for some reason", enable_reason=True):
        self.reason = reason
        self.enable_reason = enable_reason
        super().__init__()

    def OnDragOver(self, *_, **__):  # pylint: disable=invalid-name
        """Make sure to disable drag-and-drop do prevent serious format problem."""
        if self.enable_reason:
            logging.info(
                "%s drag from text disabled 0: %s", self.__class__, self.reason
            )
        return wx.DragNone

    def OnDrop(self, *_, **__):  # pylint: disable=C0103, R0201
        """Disable ancestor method."""
        return False

    def OnDropText(self, *_, **__):  # pylint: disable=C0103, R0201
        """Disable ancestor method."""
        return False


class IntInput(wx.TextCtrl):
    """An input field for typing integer numbers"""

    def __init__(self, parent, ident, value, *args, max_len=10, **kwargs):
        """Create an input field for typing integer numbers

        parent: the parent widget.
        ident: unique ID to use (use wx.ID_ANY if you don't care)
        value: the initial value
        max_len: the amount of characters that should fit. This is used to calculate the minimum
            size of the widget.
        """
        super().__init__(parent, ident, str(value), *args, **kwargs)
        # Set defaults: style and width if not set by caller
        # self.SetStyle(0, -1, wx.TE_PROCESS_ENTER | wx.TE_DONTWRAP)
        self.val_updated = False
        self.SetMaxLength(max_len)
        self.SetMinSize(self.GetTextExtent(max_len * "8"))
        self.SetDropTarget(
            DisabledDropTarget(reason="may break string format for signed integer")
        )
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.Bind(wx.EVT_TEXT, self.on_text)

    def _sign_only_handled(self, string):
        """If string being set equals "+" or "-" handle it."""
        if string in ("-", "+"):
            self.ChangeValue(string + "0")
            wx.CallLater(1, self.SetSelection, 1, 2)
            self.val_updated = True
            return True

        return False

    def _handle_empty(self):
        """Handle empty string being set."""
        self.ChangeValue("0")
        wx.CallLater(1, self.SetSelection, 0, 1)
        self.val_updated = True

    def _handle_char(self, char):
        """Handle when char is being added to the current input."""
        string = super().GetValue()
        selected = self.GetSelection()
        head = string[: selected[0]]
        if self.GetStringSelection():
            tail_start = selected[1] + 1
        else:
            tail_start = selected[1]
        if tail_start < len(string):
            tail = string[selected[1]:]
        else:
            tail = ""
        new_string = head + char + tail
        if not self._sign_only_handled(new_string):
            # Raise exception if not integer value
            try:
                _ = int(new_string)
                self.ChangeValue(new_string)
                self.SetInsertionPoint(selected[0] + 1)
                self.val_updated = True
            except ValueError:
                logging.info("%s ignores key %s (here)", self.__class__, char)

    def handle_special(self, event):
        """Handle events with special characters, like DELETE."""
        current_value = super().GetValue()
        cursor_pos = self.GetInsertionPoint()
        handled = True
        key = event.GetKeyCode()
        if key in [wx.WXK_BACK, wx.WXK_DELETE]:
            pos = {
                wx.WXK_BACK: 0,
                wx.WXK_DELETE: 1,
            }
            if len(current_value) <= 1 and cursor_pos == pos[key]:
                event.Skip(False)  # prevent annoying bell
            else:
                event.Skip()
                self.val_updated = True
        elif key == wx.WXK_CLEAR:
            event.Skip()
        elif (key in [wx.WXK_HOME, wx.WXK_LEFT] and cursor_pos == 0) or (
            key in [wx.WXK_END, wx.WXK_RIGHT] and cursor_pos == len(current_value)
        ):
            self.SetInsertionPoint(cursor_pos)
            event.Skip(False)  # prevent annoying bell
        elif key in [
            wx.WXK_RETURN,
            wx.WXK_TAB,
            wx.WXK_LEFT,
            wx.WXK_RIGHT,
            wx.WXK_INSERT,
            wx.WXK_HOME,
            wx.WXK_END,
        ]:
            event.Skip()
        else:
            handled = False
        return handled

    def on_char(self, e):
        """Handle character input in the float input field"""
        if not self.handle_special(e):
            key = e.GetKeyCode()  # ASCII is returned for ASCII values
            self._handle_char(chr(key))
            e.Skip(False)
        # elif k >= 256:
        #     e.Skip()

    def on_text(self, _):
        """Handle after string after character update is done."""
        string = super().GetValue()
        if not self._sign_only_handled(string) and string == "":
            self._handle_empty()

    # doc-string for
    # wx.TextCtrl.GetValue(*args, **kwargs)
    #     GetValue(self) -> String
    # Change to get_value? TODO: check if anyone using old name
    def GetValue(self):  # pylint: disable=arguments-differ
        """Get the value of int input"""
        v = super().GetValue()
        self.val_updated = False
        if v == "":
            v = "0"
        return int(v)

    def set_value(self, i):
        """Set value of int input to the specified value"""
        self.val_updated = True
        super().SetValue(str(i))


class FloatInput(wx.TextCtrl):
    """An input field for typing floating point numbers"""

    def __init__(self, parent, ident, value, *args, max_len=18, **kwargs):
        """Create an input field for typing floating point numbers

        parent: the parent widget.
        ident: unique ID to use (use wx.ID_ANY if you don't care)
        value: the initial value
        max_len: the amount of characters that should fit. This is used to calculate the minimum
            size of the widget.
        """
        wx.TextCtrl.__init__(self, parent, ident, self.to_str(value), *args, **kwargs)
        # Set defaults: style and width if not set by caller
        # self.SetStyle(0, -1, wx.TE_PROCESS_ENTER | wx.TE_DONTWRAP)
        self.SetMaxLength(max_len)
        self.SetMinSize(self.GetTextExtent(max_len * "8"))
        self.SetDropTarget(
            DisabledDropTarget(reason="may break string format for floating point")
        )
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.on_set = None

    @staticmethod
    def to_str(value):
        """Convert float value to a string representation.

        Prevent scientific notation.
        """
        return geomtypes.f2s(value)

    def bind_on_set(self, on_set):
        """
        Bind the function on_set to be called with the current value when the
        field is set

        The field is set when ENTER / TAB is pressed
        """
        self.on_set = on_set

    def on_char(self, e):
        """Handle character input in the float input field"""
        k = e.GetKeyCode()  # ASCII is returned for ASCII values
        try:
            c = chr(k)
        except ValueError:
            c = 0
        rkc = e.GetRawKeyCode()
        if "0" <= c <= "9":
            e.Skip()
        elif c in ["+", "-", "."]:
            # Handle selected text by replacing it by a '0', otherwise it may
            # prevent from overwriting a sign:
            ss = self.GetStringSelection()
            if not ss == "":
                sel = self.GetSelection()
                if sel[0] == 0:
                    self.Replace(sel[0], sel[1], "0")
                    end_select = sel[0] + 1
                else:
                    self.Replace(sel[0], sel[1], "")
                    end_select = sel[0]
                self.SetSelection(sel[0], end_select)
                # self.SetInsertionPoint(sel[0])
            s = wx.TextCtrl.GetValue(self)
            # only allow one +, -, or .
            if c not in s:
                if c == ".":
                    e.Skip()
                else:  # '+' or '-'
                    # only allow + and - in the beginning
                    if self.GetInsertionPoint() == 0:
                        # don't allow - if there's already a + and the other
                        # way around:
                        if c == "+":
                            if "-" not in s:
                                e.Skip()
                        else:
                            if "+" not in s:
                                e.Skip()
                    else:
                        # allow selected whole string start with -
                        if self.GetSelection()[0] == 0 and c == "-":
                            self.Replace(0, 1, "-0")
                            self.SetSelection(1, 2)

        elif k in [wx.WXK_BACK, wx.WXK_DELETE]:
            ss = self.GetStringSelection()
            # Handle selected text by replacing it by a '0' the field might
            # become completely empty if all is selected
            if not ss == "":
                sel = self.GetSelection()
                self.Replace(sel[0], sel[1], "0")
                self.SetSelection(sel[0], sel[0] + 1)
            else:
                e.Skip()
        elif k == wx.WXK_CLEAR:
            self.SetValue(0)
        elif k in [wx.WXK_RETURN, wx.WXK_TAB]:
            if self.on_set is not None:
                self.on_set(self.GetValue())
            e.Skip()
        elif k in [wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_INSERT, wx.WXK_HOME, wx.WXK_END]:
            e.Skip()
        elif e.ControlDown():
            if rkc == ord("v"):
                self.Paste()
            elif rkc == ord("c"):
                self.Copy()
            elif rkc == ord("x"):
                self.Cut()
            else:
                logging.info(
                    "%s ignores Ctrl-key event with code: 0x%x", self.__class__, rkc
                )
        else:
            logging.info("%s ignores key event with code: 0x%x", self.__class__, k)
        # elif k >= 256:
        #     e.Skip()

    # doc-string for
    # wx.TextCtrl.GetValue(*args, **kwargs)
    #     GetValue(self) -> String
    def GetValue(self):  # pylint: disable=arguments-differ
        """Get the value of float input"""
        v = wx.TextCtrl.GetValue(self)
        if v == "":
            v = "0"
            self.SetValue(v)
        return float(v)

    # doc-string for
    # wx.TextCtrl.SetValue(*args, **kwargs)
    #     SetValue(self, String value)
    def SetValue(self, f):  # pylint: disable=arguments-differ
        """Set value of float input to the specified value"""
        wx.TextCtrl.SetValue(self, self.to_str(f))


class LabeledIntInput(wx.BoxSizer):
    """A control embedded in a sizer for providing an integer with a label"""

    def __init__(
        self,
        panel,
        label="",
        init=0,
        width=-1,
        orientation=wx.HORIZONTAL,
        max_len=10,
    ):
        """
        Create a control embedded in a sizer for providing an integer.

        It consists of an integer input field and a label next to it.
        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        init: initial value used in input
        width: width of the face index fields.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is default. Defines
            the orientation of the label - int input.
        max_len: the amount of characters that should fit. This is used to calculate the minimum
            size of the widget.
        """
        self.boxes = []
        wx.BoxSizer.__init__(self, orientation)
        self.boxes.append(
            wx.StaticText(panel, wx.ID_ANY, label + " ", style=wx.ALIGN_RIGHT)
        )
        self.Add(self.boxes[-1], 1, wx.EXPAND)
        if not isinstance(init, int):
            logging.info(
                "%s warning: initialiser not an int (%s)", self.__class__, init
            )
            init = 0
        self.boxes.append(
            IntInput(panel, wx.ID_ANY, init, size=(width, -1), max_len=max_len)
        )
        self.Add(self.boxes[-1], 0, wx.EXPAND)
        self.int_gui_idx = len(self.boxes) - 1

    @property
    def val_updated(self):
        """True if the integer value was updated since last retrieved"""
        return self.boxes[self.int_gui_idx].val_updated

    def GetValue(self):
        """Get the integer value of the input"""
        return self.boxes[-1].GetValue()

    def SetValue(self, i):
        """Set the integer value of the input"""
        return self.boxes[-1].set_value(i)

    def Destroy(self, *_, **__):
        """Destroy labeled int input and release memory."""
        for box in self.boxes:  # pylint: disable=duplicate-code
            try:
                box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        # wx.StaticBoxSizer.Destroy(self)


class Vector3DInput(wx.BoxSizer):
    """A control embedded in a sizer for defining a 3D vector"""

    def __init__(self, panel, label="", v=None, max_len=18, orientation=wx.HORIZONTAL):
        """
        Create a control embedded in a sizer for defining a 3D vector

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        v: initial value. A vector of (at least) three valid values.
        max_len: the maximum amount of characters that fit in this input. From this number the
            minimum size of the widget is calculated.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former
                     is default. Defines the orientation of the separate vector
                     items.
        """
        self.panel = panel
        self.boxes = []
        # Calling wx.StaticBoxSizer fails on type checking (?? bug?)
        wx.BoxSizer.__init__(self, wx.VERTICAL)
        self.boxes.append(
            wx.StaticText(self.panel, wx.ID_ANY, label + " ", style=wx.ALIGN_RIGHT)
        )
        self.Add(self.boxes[-1], 1)
        vec_sizer = wx.BoxSizer(orientation)
        self._vec = []
        for _ in range(3):
            self._vec.append(FloatInput(self.panel, wx.ID_ANY, 0, max_len=max_len))
            vec_sizer.Add(self._vec[-1], 0, wx.EXPAND)
        if v is not None:
            self.set_vertex(v)
        self.Add(vec_sizer, 1, wx.EXPAND)

    def get_vertex(self):
        """Get the currently defined vertex from the GUI"""
        return geomtypes.Vec3(
            [self._vec[0].GetValue(), self._vec[1].GetValue(), self._vec[2].GetValue()]
        )

    def set_vertex(self, v):
        """Set the vertex in the GUI to be the one specified"""
        for i, n in enumerate(v):
            if not isinstance(n, (float, int)):
                logging.info(
                    "%s warning: v[%d] not a number (%s)", self.__class__, i, n
                )
                return
        self._vec[0].SetValue(v[0])
        self._vec[1].SetValue(v[1])
        self._vec[2].SetValue(v[2])

    def Destroy(self, *_, **__):
        """Destroy Vector3 input and release memory."""
        for ctrl in self._vec:
            ctrl.Destroy()
        for box in self.boxes:
            try:
                box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass


class Vector3DSetStaticPanel(wx_panel.ScrolledPanel):
    """A panel defining a list of 3D vectors

    The panel doesn't contain any widgets to grow or shrink this list
    """

    __head_lables = ["index", "x", "y", "z"]

    def __init__(self, parent, length, orientation=wx.HORIZONTAL, max_len=18):
        """
        Create a panel defining a set of 3D vectors

        parent: the parent widget.
        length: initialise with length amount of 3D vectors.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is default. Defines
            the orientation of the separate vector items.
        max_len: the maximum amount of characters in the inputs. This is used to calculate the
            minimal size.
        """

        wx_panel.ScrolledPanel.__init__(self, parent)

        self.max_len = max_len
        self.boxes = []
        opp_orient = opposite_orientation(orientation)
        vectors_sizer = wx.BoxSizer(orientation)
        self.column_sizers = []  # align vector columns
        # header:
        scale = 0
        for i, header in enumerate(self.__head_lables):
            self.boxes.append(wx.StaticText(self, wx.ID_ANY, header))
            self.column_sizers.append(wx.BoxSizer(opp_orient))
            self.column_sizers[i].Add(self.boxes[-1], 0, wx.ALIGN_CENTRE_HORIZONTAL)
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

    def grow(self, no=1, vs=None):
        """To the end of the list of vertices add undefined or defined vertices

        Either specify 'no' of 'vs' to add extra vertices to the list. If both
        are specified then vs takes precedence.
        no: the number of undefined vertices to add.
        vs: add the specified vertices
        """
        assert vs is None or len(vs) == no
        if vs is not None:
            no = len(vs)
        for n in range(no):
            j = len(self._vec)
            self._vec_labels.append(
                wx.StaticText(self, wx.ID_ANY, f"{j} ", style=wx.TE_CENTRE)
            )
            self.column_sizers[0].Add(self._vec_labels[-1], 1)
            self._vec.append([])
            for i in range(1, len(self.__head_lables)):
                if vs is None:
                    f = 0
                else:
                    f = vs[n][i - 1]
                self._vec[-1].append(
                    FloatInput(self, wx.ID_ANY, f, max_len=self.max_len)
                )
                self.column_sizers[i].Add(self._vec[-1][-1], 1, wx.EXPAND)
        self.Layout()

    def extend(self, verts):
        """Add to the end of the list of vertices the vertices from 'verts'"""
        self.grow(len(verts), verts)

    def rm_vector(self, i):
        """Remove the vertex with index 'i' from the list of vertices"""
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
            logging.info("%s warning: nothing to delete", self.__class__)

    def get_vector(self, i):
        """Get the vertex with index 'i' from the list of vertices"""
        return geomtypes.Vec3(
            [
                self._vec[i][0].GetValue(),
                self._vec[i][1].GetValue(),
                self._vec[i][2].GetValue(),
            ]
        )

    def get(self):
        """Get the list of vertices as defined by the GUI"""
        return [self.get_vector(i) for i in range(len(self._vec))]

    def clear(self):
        """Remove all vertices from the list of vertices"""
        for _ in range(len(self._vec)):
            self.rm_vector(-1)

    def set(self, verts):
        """Set the list of vertices in the GUI to the specified list"""
        self.clear()
        self.extend(verts)

    def Destroy(self, *_, **__):
        """Destroy Vector3 panel and release memory."""
        for ctrl in self._vec:
            ctrl.Destroy()
        for ctrl in self._vec_labels:
            ctrl.Destroy()
        for box in self.boxes:
            try:
                box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass

    # TODO Insert?
    # Note that the panel is used for defining faces.  Inserting and delting
    # faces in the middle of the list will break these references (of course
    # self can be fixed by SW


class Vector3DSetDynamicPanel(wx_panel.ScrolledPanel):
    """Create a control embedded in a sizer for defining a set of 3D vectors

    The set can dynamically grow and shrink by using the GUI.
    """

    __defaultLabels = ["index", "x", "y", "z"]
    __nrOfColumns = 4

    def __init__(self, parent, length=3, rel_xtra_space=5, orientation=wx.HORIZONTAL):
        """
        Create a control embedded in a sizer for defining a set of 3D vectors

        parent: the parent widget.
        length: initialise the input with length amount of 3D vectors.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former
                     is default. Defines the orientation of the separate vector
                     items.
        """
        self.parent = parent
        super().__init__(parent)
        self.SetupScrolling()

        self.boxes = []
        opp_orient = opposite_orientation(orientation)
        main_sizer = wx.BoxSizer(opp_orient)

        # Add vertex list
        self.boxes.append(Vector3DSetStaticPanel(self, length, orientation))
        main_sizer.Add(self.boxes[-1], rel_xtra_space, wx.EXPAND)
        self._vertex_list_panel = len(self.boxes) - 1
        # Add button:
        add_sizer = wx.BoxSizer(orientation)
        self.boxes.append(wx.Button(self, wx.ID_ANY, "Vertices Add Times:"))
        add_sizer.Add(self.boxes[-1], 1, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.on_add, id=self.boxes[-1].GetId())
        self.boxes.append(IntInput(self, wx.ID_ANY, 1, size=(40, -1), max_len=5))
        self._add_no_of_v_idx = len(self.boxes) - 1
        add_sizer.Add(self.boxes[-1], 0, wx.EXPAND)
        main_sizer.Add(add_sizer, 0, wx.EXPAND)

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
        main_sizer.Add(rm_sizer, 0, wx.EXPAND)

        self.SetSizer(main_sizer)
        self.SetAutoLayout(True)

    def on_add(self, e):
        """Add a certain amount of vertices to the end of the list of vertices

        The number of vertices to be added will be taken from the GUI itself.
        """
        no = self.boxes[self._add_no_of_v_idx].GetValue()
        self.boxes[self._vertex_list_panel].grow(no)
        self.Layout()
        e.Skip()

    def on_rm(self, e):
        """Remove the list item in the list of vertices"""
        self.boxes[self._vertex_list_panel].rm_vector(-1)
        self.Layout()
        e.Skip()

    def on_clear(self, e):
        """Make the list of vertices empty"""
        self.boxes[self._vertex_list_panel].clear()
        self.Layout()
        e.Skip()

    def set(self, verts):
        """Set the list for vertices"""
        self.boxes[self._vertex_list_panel].set(verts)
        self.Layout()

    def get(self):
        """Get the list of vertices"""
        return self.boxes[self._vertex_list_panel].get()


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
    __defaultLabels = ["x", "y", "z", "w"]

    def __init__(
        self,
        panel,
        label="",
        orientation=wx.HORIZONTAL,
        rel_float_size=4,
        elem_labels=None,
        max_len=18,
    ):
        """
        Create a control embedded in a sizer for defining 4D vectors

        panel: the panel the input will be a part of.
        label: the label to be used for the box, default ''
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is default. Defines
            the orientation of the separate vector items.
        rel_float_size: it defines the size of the input fields relative to the vector item labels
            'x', 'y',..,'z' (with size 1)
        elem_labels: option labels for the vector items. It is an array consisting of 4 strings On
            default ['x', 'y', 'z', 'w'] is used.
        max_len: the maximum amount of characters that fit in this input. From this number the
            minimum size of the widget is calculated.
        """
        self.boxes = [wx.StaticBox(panel, label=label)]
        wx.StaticBoxSizer.__init__(self, self.boxes[-1], orientation)
        if elem_labels is None:
            elem_labels = self.__defaultLabels
        self._vec_label = [
            wx.StaticText(
                panel,
                wx.ID_ANY,
                elem_labels[0],
                style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL,
            ),
            wx.StaticText(
                panel,
                wx.ID_ANY,
                elem_labels[1],
                style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL,
            ),
            wx.StaticText(
                panel,
                wx.ID_ANY,
                elem_labels[2],
                style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL,
            ),
            wx.StaticText(
                panel,
                wx.ID_ANY,
                elem_labels[3],
                style=wx.TE_RIGHT | wx.ALIGN_CENTRE_VERTICAL,
            ),
        ]
        self._vec = [
            FloatInput(panel, wx.ID_ANY, 0, max_len=max_len),
            FloatInput(panel, wx.ID_ANY, 0, max_len=max_len),
            FloatInput(panel, wx.ID_ANY, 0, max_len=max_len),
            FloatInput(panel, wx.ID_ANY, 0, max_len=max_len),
        ]
        for i in range(4):
            if orientation == wx.HORIZONTAL:
                self.Add(self._vec_label[i], 1, wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL)
                self.Add(self._vec[i], rel_float_size, wx.EXPAND)
            else:
                b_sizer = wx.BoxSizer(wx.HORIZONTAL)
                b_sizer.Add(self._vec_label[i], 1, wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL)
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
        vec_event.set_vector(
            geomtypes.Vec4(
                [
                    self._vec[0].GetValue(),
                    self._vec[1].GetValue(),
                    self._vec[2].GetValue(),
                    self._vec[3].GetValue(),
                ]
            )
        )
        self._vec[self.__ctrlIdIndex].GetEventHandler().ProcessEvent(vec_event)

    def GetValue(self):
        """Get the defined 4D vector"""
        return geomtypes.Vec4(
            [
                self._vec[0].GetValue(),
                self._vec[1].GetValue(),
                self._vec[2].GetValue(),
                self._vec[3].GetValue(),
            ]
        )

    def Destroy(self, *_, **__):
        """Destroy Vector4 input and release memory."""
        for ctrl in self._vec_label:
            ctrl.Destroy()
        for ctrl in self._vec:
            ctrl.Destroy()
        for box in self.boxes:
            try:
                box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        # wx.StaticBoxSizer.Destroy(self)


class FaceSetStaticPanel(wx_panel.ScrolledPanel):
    """A control embedded in a sizer for defining a set of faces

    This cannot grow or shrink in size through a GUI itself
    """

    def __init__(
        self,
        parent,
        no_of_faces=0,
        face_len=0,
        width=40,
        orientation=wx.HORIZONTAL,
        max_index_no=5,
    ):
        """
        Create a control embedded in a sizer for defining a set of faces

        parent: the parent widget.
        no_of_faces: initialise the input with no_of_faces amount of faces.
        face_len: initialise the faces with face_len vertices. Also the default value for adding
            faces.
        width: width of the face index fields.
        orientation: one of wx.HORIZONTAL or wx.VERTICAL, of which the former is default. Defines
            the orientation of the separate face items.
        max_index_no: the maximum number of faces / vertices to be used. This will decide how big
            the text input will be and the minimal size will be set from this.
        """
        wx_panel.ScrolledPanel.__init__(self, parent)
        self.parent = parent
        self.width = width
        self.face_len = face_len
        self.orientation = orientation
        self.max_index_no = max_index_no
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
        self._faces_labels.append(wx.StaticText(self, wx.ID_ANY, f"{j} "))
        self.face_idx_sizer.Add(self._faces_labels[-1], 1, wx.EXPAND)

        face_sizer = wx.BoxSizer(self.orientation)
        self._faces.append([face_sizer])
        for i in range(face_len):
            if face is not None:
                val = face[i]
            else:
                val = 0
            self._faces[-1].append(
                IntInput(
                    self,
                    wx.ID_ANY,
                    val,
                    size=(self.width, -1),
                    max_len=self.max_index_no,
                )
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
        return [
            self._faces[index][i].GetValue() for i in range(1, len(self._faces[index]))
        ]

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
        return [self.get_face(i) for i in range(len(self._faces))]

    def clear(self):
        """Remove all faces from the list"""
        for _ in range(len(self._faces)):
            self.rm_face(-1)

    def set(self, faces):
        """Set the list of faces"""
        self.clear()
        self.extend(faces)

    def Destroy(self, *_, **__):
        """Destroy face set panel and release memory."""
        for ctrl in self._faces_labels:
            ctrl.Destroy()
        for ctrl in self._faces:
            ctrl.Destroy()

    # TODO Insert?


class FaceSetDynamicPanel(wx_panel.ScrolledPanel):
    """A control for defining a set of faces, which can grow and shrink"""

    def __init__(
        self,
        parent,
        no_of_faces=0,
        face_len=0,
        orientation=wx.HORIZONTAL,
        max_index_no=5,
    ):
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
        max_index_no: the maximum number of faces / vertices to be used. This will decide how big
            the text input will be and the minimal size will be set from this.
        """
        self.parent = parent
        super().__init__(parent)
        self.SetupScrolling()

        self.face_len = face_len
        self.max_index_no = max_index_no

        self.boxes = []
        opp_orient = opposite_orientation(orientation)
        main_sizer = wx.BoxSizer(opp_orient)

        # Add face list
        self.boxes.append(
            FaceSetStaticPanel(self, no_of_faces, face_len, orientation=orientation)
        )
        self._face_lst_idx = len(self.boxes) - 1
        main_sizer.Add(self.boxes[-1], 10, wx.EXPAND)

        # Add button:
        add_sizer = wx.BoxSizer(orientation)
        self.boxes.append(
            IntInput(self, wx.ID_ANY, face_len, size=(40, -1), max_len=max_index_no)
        )
        self._face_len_idx = len(self.boxes) - 1
        add_sizer.Add(self.boxes[-1], 0, wx.EXPAND)
        self.boxes.append(wx.Button(self, wx.ID_ANY, "-Faces Add Times:"))
        add_sizer.Add(self.boxes[-1], 1, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.on_add, id=self.boxes[-1].GetId())
        self.boxes.append(
            IntInput(self, wx.ID_ANY, 1, size=(40, -1), max_len=max_index_no)
        )
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

    def Destroy(self, *_, **__):
        """Destroy face set gui and release memory."""
        for box in self.boxes:
            try:
                box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass


class SymmetrySelect(wx.StaticBoxSizer):
    """A control embedded in a sizer for defining a symmetry"""

    HIDE_LAB = "Hide Setup"
    SHOW_LAB = "Setup"

    def __init__(
        self,
        panel,
        label="",
        groups_lst=None,
        on_sym_select=None,
        on_get_sym_setup=None,
    ):
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
            self.groups_lst = [
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
            ]
        self.on_sym_select = on_sym_select
        self.on_get_sym_setup = on_get_sym_setup
        self.panel = panel
        self.boxes = [wx.StaticBox(panel, label=label)]
        self.__prev = {}
        wx.StaticBoxSizer.__init__(self, self.boxes[-1], wx.VERTICAL)
        self.boxes.append(
            wx.Choice(
                self.panel, wx.ID_ANY, choices=[c.__name__ for c in self.groups_lst]
            )
        )
        # pylint false-positive:
        # Instance of 'StaticBox' has no 'SetSelection' member (no-member)
        self.boxes[-1].SetSelection(0)  # pylint: disable=no-member
        self._sym_gui_idx = len(self.boxes) - 1
        self.panel.Bind(wx.EVT_CHOICE, self.on_set_sym, id=self.boxes[-1].GetId())
        self.Add(self.boxes[-1], 0, wx.EXPAND)

        self.orient_guis = []
        self.orient_gui_box = None
        self.orient_sizer = None
        self.setup_sizer = None
        self.hide = None
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
        self.__prev = {}
        for c in groups_lst:
            self.boxes[self._sym_gui_idx].Append(c.__name__)
        # Not so good: self requires that E should be last...
        self.boxes[self._sym_gui_idx].SetSelection(len(groups_lst) - 1)
        self.add_setup_gui()
        self.panel.Layout()

    def get_selected_idx(self):
        """Return the index of the selected symmetry class"""
        return self.boxes[self._sym_gui_idx].GetSelection()

    def get_sym_class(self, apply_order=True):
        """Return the selected symmetry class"""
        selected_class = self.groups_lst[self.get_selected_idx()]
        if apply_order:
            if selected_class in [
                isometry.Cn,
                isometry.CnxI,
                isometry.C2nCn,
                isometry.DnCn,
                isometry.Dn,
                isometry.DnxI,
                isometry.D2nDn,
            ]:
                assert (
                    selected_class.init_pars[0]["type"] == "int"
                ), "The first index should specify the n-order"
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
                else:
                    raise ValueError(f"Unknown cyclic/dihedral group {selected_class} used")
                assert n > 0, f"warning n = {n} should be > 0"
                selected_class = C(n)
            elif selected_class in [
                isometry.E,
                isometry.ExI,
                isometry.C2C1,
                isometry.C4C2,
                isometry.C6C3,
                isometry.C8C4,
                isometry.C10C5,
                isometry.C12C6,
                isometry.C2,
                isometry.C2xI,
                isometry.C3,
                isometry.C3xI,
                isometry.C4,
                isometry.C4xI,
                isometry.C5,
                isometry.C5xI,
                isometry.C6,
                isometry.C6xI,
                isometry.D6C6,
                isometry.D6xI,
                isometry.D6,
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
                assert False, f"unknown class {selected_class}"
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
        if self.setup_sizer:
            self.Remove(self.setup_sizer)
        if self.hide:
            self.hide.Destroy()
        self.setup_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.orient_gui_box = wx.StaticBox(self.panel, label="Symmetry Setup")
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
            input_type = init["type"]
            if input_type == "vec3":
                gui = Vector3DInput(self.panel, init["lab"], v=sym_setup[init["par"]])
            elif input_type == "int":
                gui = LabeledIntInput(
                    self.panel, init["lab"], init=sym_setup[init["par"]]
                )
                self.chk_if_updated.append(gui)
            else:
                assert False, "oops unimplemented input type"
            self.orient_guis.append(gui)
            self.orient_sizer.Add(self.orient_guis[-1], 1, wx.EXPAND)
        self.hide = wx.Button(self.panel, wx.ID_ANY, self.HIDE_LAB)
        self.boxes.append(self.hide)
        self.on_hide(None)  # hide one default
        self.panel.Bind(wx.EVT_BUTTON, self.on_hide, id=self.hide.GetId())
        self.setup_sizer.Add(self.hide, flag=wx.LEFT)
        self.setup_sizer.Add(self.orient_sizer, flag=wx.RIGHT | wx.EXPAND)
        self.Add(self.setup_sizer, wx.EXPAND)

    def on_hide(self, _):
        """Hide or show the setup part"""
        show_items = self.hide.GetLabel() == self.SHOW_LAB
        new_label = self.HIDE_LAB if show_items else self.SHOW_LAB
        self.orient_sizer.ShowItems(show_items)
        self.hide.SetLabel(new_label)
        self.panel.Layout()

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
            is_updated = self.__prev["selectedId"] != cur_idx
            if self.chk_if_updated and not is_updated:
                for gui in self.chk_if_updated:
                    is_updated = gui.val_updated
                    if is_updated:
                        break
        except KeyError:
            is_updated = True
        self.__prev["selectedId"] = cur_idx
        return is_updated

    def is_updated(self):
        """Check whether any property of the symmetry was updated

        Compared to the previous time that was checked"""
        is_updated = self.is_sym_class_updated()
        cur_setup = []
        sym = self.get_sym_class(apply_order=False)
        for i, gui in zip(list(range(len(self.orient_guis))), self.orient_guis):
            input_type = sym.init_pars[i]["type"]
            if input_type == "vec3":
                v = gui.get_vertex()
            elif input_type == "int":
                v = gui.GetValue()
            else:
                raise ValueError(f"Unexpected type for {input_type} to orientate symmetry.")
            cur_setup.append(v)
        try:
            prev_setup = self.__prev["setup"]
            if len(prev_setup) == len(cur_setup):
                for i, ps_i in enumerate(prev_setup):
                    if ps_i != cur_setup[i]:
                        is_updated = True
                        break
            else:
                is_updated = True
        except KeyError:
            is_updated = True
        self.__prev["setup"] = cur_setup
        return is_updated

    def set_selected_class(self, cl):
        """Set the selected symmetry in the drop down menu by class"""
        found = False
        i = 0
        for i, cl_i in enumerate(self.groups_lst):
            # The in relation is for cyclic and dihedral symmetry, e.g.
            # cl can be C4xI, while cl_i is CnxI
            if cl == cl_i or cl_i in cl.__bases__:
                found = True
                break
        if found:
            self.set_selected(i)
        else:
            logging.warning("set_selected_class: class %s not found", cl.__name__)

    def set_selected(self, i):
        """Set the selected symmetry in the drop down menu by index"""
        self.boxes[self._sym_gui_idx].SetSelection(i)

    def setup_sym(self, setup):
        """Fill in the symmetry setup fields in the GUI

        setup: a dictionary with the same structure as isometry.<class-object>.setup
        """
        assert len(setup) == len(self.orient_guis), (
            f"Wrong no. of initialisers for {self.get_sym_class(apply_order=False)} symmetry"
            f"(got {len(setup)}, expected {len(self.orient_guis)})"
        )
        sym = self.get_sym_class(apply_order=False)
        for i, gui in zip(list(range(len(self.orient_guis))), self.orient_guis):
            input_type = sym.init_pars[i]["type"]
            key = sym.init_pars[i]["par"]
            if input_type == "vec3":
                _ = gui.set_vertex(setup[key])
            elif input_type == "int":
                _ = gui.SetValue(setup[key])

    def get_selected(self):
        """return a symmetry instance"""
        sym = self.get_sym_class(apply_order=False)
        setup = {}
        for i, gui in zip(list(range(len(self.orient_guis))), self.orient_guis):
            input_type = sym.init_pars[i]["type"]
            if input_type == "vec3":
                v = gui.get_vertex()
                if v != geomtypes.Vec3([0, 0, 0]):
                    setup[sym.init_pars[i]["par"]] = v
            elif input_type == "int":
                v = gui.GetValue()
                setup[sym.init_pars[i]["par"]] = v
        sym = sym(setup=setup)

        return sym

    def Destroy(self, *_, **__):
        """Destroy symmetry select gui and release memory."""
        for box in self.boxes + self.orient_guis:
            try:
                box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass
        # Segmentation fault in Hardy Heron (with python 2.5.2):
        # wx.StaticBoxSizer.Destroy(self)


class AxisRotateSizer(wx.BoxSizer):
    """Class with sizer for defining a rotation"""

    def __init__(
        self,
        panel,
        on_angle_callback,
        min_angle=-180,
        max_angle=180,
        initial_angle=0,
        max_len=8,
    ):
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
        max_len: the amount characters to fit in the float inputs (angle, and angle step). The
            minimum size will be calculated from this.
        """
        self.current_angle = initial_angle
        self.on_angle = on_angle_callback
        self.panel = panel
        self.show_gui = []
        # Create a horizontal sizer to force all the ones inside to have the same width
        #
        # +-- self.hor------------------`+
        # | +----v_sizer.vert---------+ |
        # | | Rotate araound Axis:    | |
        # | | x y z                   | |
        # | | +-set_angle_sizer.hor-+ | |
        # | | | Set angle .. etc    | | |
        # | | +---------------------+ | |
        # | | +-slider_sizer.hor----+ | |
        # | | | -  -----|----  +    | | |
        # | | +---------------------+ | |
        # | +-------------------------+ |
        # +-----------------------------+
        super().__init__(wx.HORIZONTAL)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        self.Add(v_sizer, 1, wx.EXPAND)

        # Rotate Axis
        # - rotate axis and set angle (button and float input)
        self.show_gui.append(Vector3DInput(panel, "Rotate around Axis:", v=[0, 0, 1]))
        v_sizer.Add(self.show_gui[-1], 0, wx.EXPAND)
        self._axis_gui_idx = len(self.show_gui) - 1

        # Set angle and step size
        set_angle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        v_sizer.Add(set_angle_sizer, 0, wx.EXPAND)
        self.show_gui.append(wx.Button(panel, wx.ID_ANY, "Set angle:"))
        panel.Bind(wx.EVT_BUTTON, self._on_angle_set, id=self.show_gui[-1].GetId())
        set_angle_sizer.Add(self.show_gui[-1], 0, wx.EXPAND)
        self.show_gui.append(
            FloatInput(panel, wx.ID_ANY, initial_angle, max_len=max_len)
        )
        self.show_gui[-1].bind_on_set(self._on_angle_typed)
        self._typed_angle_gui_idx = len(self.show_gui) - 1
        set_angle_sizer.Add(self.show_gui[-1], 0, wx.EXPAND)
        self.show_gui.append(
            wx.StaticText(panel, wx.ID_ANY, "Angle step:", style=wx.ALIGN_RIGHT)
        )
        set_angle_sizer.Add(self.show_gui[-1], 1, wx.EXPAND)

        self.show_gui.append(FloatInput(panel, wx.ID_ANY, 0.1, max_len=max_len))
        self._dir_angle_step_idx = len(self.show_gui) - 1
        set_angle_sizer.Add(self.show_gui[-1], 0, wx.EXPAND)

        # - slidebar and +/- step (incl. float input)
        slider_sizer = wx.BoxSizer(wx.HORIZONTAL)
        v_sizer.Add(slider_sizer, 0, wx.EXPAND)
        self.show_gui.append(wx.Button(panel, wx.ID_ANY, "-", style=wx.BU_EXACTFIT))
        panel.Bind(
            wx.EVT_BUTTON, self._on_angle_step_down, id=self.show_gui[-1].GetId()
        )
        slider_sizer.Add(self.show_gui[-1], 0, wx.ALIGN_CENTRE_VERTICAL)
        self.show_gui.append(
            wx.Slider(
                panel,
                value=initial_angle,
                minValue=min_angle,
                maxValue=max_angle,
                style=wx.SL_HORIZONTAL | wx.SL_LABELS,
            )
        )
        self._slide_angle_gui_idx = len(self.show_gui) - 1
        panel.Bind(
            wx.EVT_SLIDER, self._on_slide_angle_adjust, id=self.show_gui[-1].GetId()
        )
        slider_sizer.Add(self.show_gui[-1], 2, wx.EXPAND)
        self.show_gui.append(wx.Button(panel, wx.ID_ANY, "+", style=wx.BU_EXACTFIT))
        panel.Bind(wx.EVT_BUTTON, self._on_angle_step_up, id=self.show_gui[-1].GetId())
        slider_sizer.Add(self.show_gui[-1], 0, wx.ALIGN_CENTRE_VERTICAL)

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
        self.current_angle = self.show_gui[self._typed_angle_gui_idx].GetValue()
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
        self._on_angle_step(e, -self.show_gui[self._dir_angle_step_idx].GetValue())
        if e is not None:
            e.Skip()

    def _on_angle_step_up(self, e):
        """Called when '+' button is pressed to increase angle"""
        self._on_angle_step(e, self.show_gui[self._dir_angle_step_idx].GetValue())
        if e is not None:
            e.Skip()

    def _on_slide_angle_adjust(self, e):
        """Called when the angle adjust slider is changed"""
        # Do not update the direct float input for better user experience.
        # In that case the user can set the value, use the slide bar and jump
        # jump back to the old value, that is still in the float input.
        self.current_angle = self.show_gui[self._slide_angle_gui_idx].GetValue()
        self.on_angle(self.current_angle, self.get_axis())
        if e is not None:
            e.Skip()
