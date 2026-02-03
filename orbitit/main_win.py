#!/usr/bin/env python3
"""Help windows class definitions for main utility"""
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
# pylint: disable=too-many-lines,too-many-instance-attributes,too-many-ancestors
# pylint: disable=too-many-arguments

import copy
import logging
import math
import wx
import wx.lib.intctrl
import wx.lib.colourselect
import wx.lib.scrolledpanel as wx_panel

from OpenGL import GL

from orbitit import geom_3d, geom_gui, geomtypes, Scenes3D, wx_colors


class ColourWindow(wx.Frame):  # pylint: disable=too-many-instance-attributes
    """Window enabling the user to change the face colours of a shape.

    width: the amount of colour columns in the widget.
    """

    def __init__(self, canvas, width, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas = canvas
        self.col_width = width
        self.status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.org_cols = self.canvas.shape.face_props["colors"]
        # take a copy for reset
        self.cols = [
            [list(col_idx) for col_idx in shape_cols] for shape_cols in self.org_cols
        ]
        self.add_content()

    def add_content(self):
        """Add all widgets to the window for updating the shape colours"""
        self.col_sizer = wx.BoxSizer(wx.VERTICAL)

        self.select_col_guis = []
        i = 0
        shape_idx = 0
        # assume compound shape
        for shape_cols in self.cols:
            # use one colour select per colour for each sub-shape
            added_cols = []
            col_idx = 0
            for col in shape_cols[0]:
                wx_col = wx.Colour(col)
                if wx_col not in added_cols:
                    if i % self.col_width == 0:
                        col_sizer_row = wx.BoxSizer(wx.HORIZONTAL)
                        self.col_sizer.Add(col_sizer_row, 0, wx.EXPAND)
                    self.select_col_guis.append(
                        wx.ColourPickerCtrl(self.panel, wx.ID_ANY, wx_col)
                    )
                    self.panel.Bind(wx.EVT_COLOURPICKER_CHANGED, self.on_col_select)
                    col_sizer_row.Add(self.select_col_guis[-1], 0, wx.EXPAND)
                    i += 1
                    # connect GUI to shape_idx and col_idx
                    self.select_col_guis[-1].my_shape_idx = shape_idx
                    self.select_col_guis[-1].my_cols = [col_idx]
                    # connect wx_col to GUI
                    wx_col.my_gui = self.select_col_guis[-1]
                    added_cols.append(wx_col)
                else:
                    gui = added_cols[added_cols.index(wx_col)].my_gui
                    # must be same shape_id
                    gui.my_cols.append(col_idx)
                col_idx += 1
            shape_idx += 1

        self.guis = []

        self.sub_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.col_sizer.Add(self.sub_sizer)

        self.guis.append(wx.Button(self.panel, label="Cancel"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_cancel)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label="Reset"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_reset)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label="Done"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_done)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.panel.SetSizer(self.col_sizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    def on_reset(self, _):
        """Handle event '_' to recover original widget and shape colours"""
        for col_gui in self.select_col_guis:
            shape_idx = col_gui.my_shape_idx
            col_idx = col_gui.my_cols[0]
            c = self.org_cols[shape_idx][0][col_idx]
            wx_col = wx.Colour(c)
            col_gui.SetColour(wx_col)
        self.cols = [
            [list(col_idx) for col_idx in shape_cols] for shape_cols in self.org_cols
        ]
        self.update_shape_cols()

    def on_cancel(self, _):
        """Handle event '_' to recover original shape colours and close window"""
        self.cols = [
            [list(col_idx) for col_idx in shape_cols] for shape_cols in self.org_cols
        ]
        self.update_shape_cols()
        self.Close()

    def on_done(self, _):
        """Handle event '_' to confirms all colours"""
        self.Close()

    def on_col_select(self, e):
        """Handle event 'e' that is generated when a colour was updated"""
        wx_col = e.GetColour().Get()
        col = tuple(wx_col[:3])
        gui_id = e.GetId()
        for gui in self.select_col_guis:
            if gui.GetId() == gui_id:
                shape_cols = self.cols[gui.my_shape_idx][0]
                for col_idx in gui.my_cols:
                    shape_cols[col_idx] = col
                self.update_shape_cols()

    def update_shape_cols(self):
        """Update the face colours of the current shape"""
        self.canvas.shape.face_props = {"colors": self.cols}
        self.canvas.paint()

    def close(self):
        """Destroy all widgets of the face colour window"""
        for gui in self.guis:
            gui.Destroy()


class FacePanel(wx.Panel):
    """A panel that shows all vertices of a face.

    These can be hidden or shown through methods
    """

    text_for_width = "[1.23456789001, 1.23456789001, 1.2345678901]"
    HIDE_COL = [1, 1, 1, 0]  # use full transparency

    def __init__(self, parent, shape, face_index, update_shape, style=wx.VERTICAL):
        """
        Initialize object

        list_of_vertices: the list of 3 dimensional vertices.
        """
        super().__init__(parent)
        self.shape = shape
        self.face_index = face_index
        self.org_face_col = self.shape.shape_colors[0][
            self.shape.shape_colors[1][face_index]
        ]
        self._update_shape = update_shape
        self.text = ""
        for vertex_index in self.shape.fs[face_index]:
            self.text += f"\n{self.shape.vs[vertex_index]}"
        self.text = self.text[1:]
        self.guis = []
        self._add_content(style)

    def _add_content(self, style):
        """Add GUI widgets to this panel"""
        main_sizer = wx.BoxSizer(style)

        # CheckBox: hide face
        hide_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.check_gui = wx.CheckBox(self)
        self.Bind(wx.EVT_CHECKBOX, self._on_checked)
        hide_sizer.Add(self.check_gui, 0, wx.ALL)
        self.guis.append(self.check_gui)

        self.hide_gui = wx.StaticText(self, wx.ID_ANY, "Hide")
        hide_sizer.Add(self.hide_gui)
        main_sizer.Add(hide_sizer, 0, wx.ALL)
        self.guis.append(self.hide_gui)

        # List of vertices
        vertices_sizer = wx.BoxSizer(wx.VERTICAL)
        self.text_gui = wx.TextCtrl(
            self, wx.ID_ANY, self.text, style=wx.TE_READONLY | wx.TE_MULTILINE
        )
        text_width = self.text_gui.GetSizeFromTextSize(
            self.text_gui.GetTextExtent(self.text_for_width).x
        )
        self.text_gui.SetInitialSize(text_width)
        self.guis.append(self.text_gui)
        vertices_sizer.Add(self.text_gui, 0, wx.EXPAND)
        main_sizer.Add(vertices_sizer, 0, wx.EXPAND)

        self.SetSizer(main_sizer)

    def show(self):
        """Show the list of vertices"""
        self.text_gui.SetValue(self.text)
        for widget in self.guis:
            widget.Show()

    def hide(self):
        """Show the list of vertices"""
        # It is easier for the user to make the face visible again when this menu is hidden,
        # otherwise updating the colour will not have any effect. Besides it might be hard to find
        # the check box in a list of many faces to do unhide
        self.check_gui.SetValue(False)
        self._update_face_col(self.org_face_col)
        self.text_gui.SetValue("")
        for widget in self.guis:
            widget.Hide()

    def _update_face_col(self, face_col):
        """Update the shape face with the specified colour and call update function"""
        self.shape.update_face_with_col(self.face_index, face_col)
        self._update_shape()

    def _on_checked(self, event):
        """Is called when the check box changes state

        This will either hide or show the face with the current colour.
        """
        if event.GetEventObject().GetValue():
            self._update_face_col(self.HIDE_COL)
        else:
            self._update_face_col(self.org_face_col)

    def set_new_org_col(self, col):
        """Update the original face colour.

        This assumes that the shapes face has updated colour already. I.e. if the face is supposed
        to be hidden, hide it again.
        """
        self.org_face_col = col
        if self.check_gui.IsChecked():
            self._update_face_col(self.HIDE_COL)


class FacesList(wx_panel.ScrolledPanel):
    """A panel with all faces and colours of one SimpleShape.

    These face are just listed

    Attributes:
        selected_gui_keys: a list with keys of selected checkbox items. These keys can be used in
            the attribute checkbox_rows.
        checkbox_rows: a dictionary which maps checkbox widget IDs on a dictionary with the
            following items:
                - check: specifies the checkbox widget
                - label: specifies the static text widget
                - face_i: specifies the face index in the shape
                - org_col: specifies the original RGB colour for that face (before applying)
        selected_faces: a list for face indices that are selected
        selection_col: wx.Colour that is used as face colour when it is selected
    """

    SHOW_LABEL = "More.."
    HIDE_LABEL = "Less"

    def __init__(self, parent, shape, on_update, selection_col):
        """
        parent: parent gui
        shape: the face properties of a simple shape.
        on_update: call-back function that is called when the shape was updated
        selection_col: wx.Colour that is used as face colour when it is selected
        """
        super().__init__(parent)
        self.parent = parent
        # set to True to ignore (de)selection events, e.g. when applying colours
        self._ignore_events = False
        self.selected_gui_keys = []
        self.shape = shape
        self.selection_col = selection_col
        self.checkbox_rows = {}
        self._update_shape = on_update
        self.SetupScrolling()
        self._add_content()

    def _add_content(self):
        """Add GUI widgets to this panel"""
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Fill main sizer
        self.SetSizer(self.main_sizer)
        self.update_face_list()

    def _destroy_faces_list(self):
        """Destroy the widgets of the face list"""
        for gui_row in self.checkbox_rows.values():
            gui_row["label"].Destroy()
            gui_row["check"].Destroy()
            gui_row["button"].Destroy()
            gui_row["face"].Destroy()
        self.selected_gui_keys = []
        self.checkbox_rows = {}

    @property
    def selected_faces(self):
        """Return the face indices for the selected items in the faces list."""
        return [
            self.checkbox_rows[check_id]["face_i"]
            for check_id in self.selected_gui_keys
        ]

    def update_face_list(self):
        """(Re)build the face list."""
        self._destroy_faces_list()
        face_cols = self.shape.shape_colors
        for i, col_i in enumerate(face_cols[1]):
            f_sizer = wx.BoxSizer(wx.HORIZONTAL)
            # Add check box
            check_gui = wx.CheckBox(self)
            check_id = check_gui.GetId()
            self.Bind(wx.EVT_CHECKBOX, self._on_checked, id=check_id)
            f_sizer.Add(check_gui, 0)
            # Add coloured text
            text_gui = wx.StaticText(self, wx.ID_ANY, f" {i} ")
            face_col = face_cols[0][col_i]
            text_gui.SetBackgroundColour(wx.Colour(face_col))
            text_gui.SetForegroundColour(wx.Colour(self.inv_col(face_col)))
            f_sizer.Add(text_gui, 0)
            # Add button to show face options
            show_button = wx.Button(self, label=self.HIDE_LABEL)
            self.Bind(wx.EVT_BUTTON, self._on_show)
            f_sizer.Add(show_button, 0)

            # Add face options text
            face_gui = FacePanel(self, self.shape, i, self._update_shape)
            show_button.vertices_list = face_gui
            f_sizer.Add(face_gui, 0, wx.EXPAND)
            # Initially hide the vertices
            self.on_show(show_button)

            # Admin
            self.checkbox_rows[check_id] = {
                "check": check_gui,
                "label": text_gui,
                "button": show_button,
                "face": face_gui,
                "org_col": face_col,
                "face_i": i,
            }
            self.main_sizer.Add(f_sizer)
        self.Layout()

    @staticmethod
    def inv_col(c):
        """Get the composite colour of some RGB colour."""
        # TODO move to RGB
        result = [255 - ch for ch in c[:3]]
        if len(c) == 4:
            result.append(c[3])
        return result

    def deselect_all(self, apply_col):
        """Deselect all faces in the list and either reset colours or apply them

        apply_col: set to False to apply all colour to the shape and the list items. If True then
            all colours are reset.
        """
        if apply_col:
            # Rebuild the faces list from scratch. This will also make sure org_col is updated eg.
            self.update_face_list()
        else:
            for check_id in self.selected_gui_keys:
                self.checkbox_rows[check_id]["check"].SetValue(False)
        # TODO if deleted faces: we need to do the following as well if not apply:
        # self.shape.face_props = self._org_face_props

    def _on_checked(self, event):
        """Handle when one of the faces checkbox changes state

        This will switch the colour of the face to the new colour of the original one (or keep it
        hidden when it is supposed to be hidden)
        """
        self.switch(event.GetId(), event.IsChecked())

    def switch(self, chk_id, checked):
        """
        Check or uncheck the check box with ID chk_id and update related data

        checked: if True apply the selection colour and update static text colour
        chk_id: check ID used in self.checkbox_rows
        """
        row_data = self.checkbox_rows[chk_id]
        text_gui = row_data["label"]
        # TODO: centralise this
        face_index = row_data["face_i"]
        if checked:
            new_col = self.selection_col
            if chk_id not in self.selected_gui_keys:
                self.selected_gui_keys.append(chk_id)
        else:
            face_col = row_data["org_col"]
            new_col = wx.Colour(face_col)
            if chk_id in self.selected_gui_keys:
                self.selected_gui_keys.remove(chk_id)
        inv_col = wx.Colour(self.inv_col(new_col))
        text_gui.SetBackgroundColour(new_col)
        text_gui.SetForegroundColour(inv_col)
        self.shape.update_face_with_col(face_index, new_col[:3])
        row_data["face"].set_new_org_col(new_col)
        self._update_shape()

    def _on_show(self, event):
        """Show or hide the extra face options depending on the state of the button."""
        self.on_show(event.GetEventObject())

    def on_show(self, button):
        """Show or hide the extra face options depending on the state of the button.

        button: the button object.
        """
        show_items = button.GetLabel() == self.SHOW_LABEL
        new_label = self.HIDE_LABEL if show_items else self.SHOW_LABEL
        if show_items:
            button.vertices_list.show()
        else:
            button.vertices_list.hide()
        button.SetLabel(new_label)
        self.Layout()


class FacesTab(wx.Panel):
    """A panel with all faces and colours of one SimpleShape (as part of a CompoundShape)

    These faces can be updated by using some widgets.

    attributes:
        shape: the SimpleShape object of this tab
    """

    def __init__(self, parent, shape, on_update):
        """
        Initialise the panel

        parent: parent gui
        shape: a simple shape. Make sure this is not a compound shape or a orbit shape e.g.
        on_update: call-back function that is called when the shape was updated
        """
        super().__init__(parent)
        self.parent = parent
        self.shape = shape
        self.guis = []
        self._update_shape = on_update
        self._org_face_props = copy.deepcopy(shape.face_props)
        self._add_content()

    def _add_content(self):
        """Add GUI widgets to this panel"""
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.main_sizer)
        init_selection_col = wx.Colour((0, 0, 0))

        # Selection colour and reverse
        sel_operation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # Colour selection:
        col_txt_gui = wx.StaticText(self, -1, "Selection Colour:")
        self.guis.append(col_txt_gui)
        self.selected_col_gui = wx.lib.colourselect.ColourSelect(
            self,
            wx.ID_ANY,
            colour=init_selection_col,
            size=wx.Size(40, 30),
        )
        self.selected_col_gui.SetCustomColours(wx_colors.COLOR_PALLETE)
        sel_operation_sizer.Add(col_txt_gui, 1, wx.ALIGN_CENTRE)
        sel_operation_sizer.Add(self.selected_col_gui, 1)
        self.selected_col_gui.Bind(
            wx.lib.colourselect.EVT_COLOURSELECT, self.on_selected_col
        )

        # List of faces
        self.faces_list = FacesList(
            self, self.shape, self._update_shape, init_selection_col
        )
        self.guis.append(self.faces_list)

        # Select all or none etc
        select_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.guis.append(wx.Button(self, label="Select All"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_select_all)
        select_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        # Apply colour
        self.guis.append(wx.Button(self, label="Apply colour"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.apply_col)
        select_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        # Reverse order
        self.guis.append(wx.Button(self, label="Flip"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_flip)
        select_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        # Replace by outline
        self.guis.append(wx.Button(self, label="Outline"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_outline)
        select_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        # Delete faces
        self.guis.append(wx.Button(self, label="Delete"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_delete)
        select_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        # Unselect all
        self.guis.append(wx.Button(self, label="Unselect All"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_unselect_all)
        select_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        # Fill main sizer
        self.main_sizer.Add(sel_operation_sizer, 0)
        self.main_sizer.Add(self.faces_list, 1, wx.EXPAND)
        self.main_sizer.Add(select_sizer, 0, wx.EXPAND)
        self.Layout()

    def on_selected_col(self, event):
        """Update the colour of the selected faces"""
        new_col = event.GetValue().Get()[:3]
        self.faces_list.selection_col = new_col
        for gui_id in self.faces_list.selected_gui_keys:
            self.faces_list.switch(gui_id, True)

    def on_flip(self, _event):
        """Update the colour of the selected faces"""
        for check_id, row_data in self.faces_list.checkbox_rows.items():
            if row_data["check"].IsChecked():
                face_i = row_data["face_i"]
                self.shape.reverse_face(face_i)
                self.faces_list.switch(check_id, False)
                row_data["check"].SetValue(False)
        self.faces_list.deselect_all(apply_col=False)
        self.shape.faces_updated()
        self._update_shape()

    def on_outline(self, _event):
        """Replace the face by its outline"""
        for check_id, row_data in self.faces_list.checkbox_rows.items():
            if row_data["check"].IsChecked():
                face_i = row_data["face_i"]
                self.shape.replace_face_by_outline(face_i)
                self.faces_list.switch(check_id, False)
                row_data["check"].SetValue(False)
        self.faces_list.deselect_all(apply_col=False)
        self.shape.faces_updated()
        self._update_shape()

    def set_all_selected(self, selected):
        """Select all or none of the faces in the faces list depending on 'selected'."""
        for row_id, row_data in self.faces_list.checkbox_rows.items():
            self.faces_list.switch(row_id, selected)
            row_data["check"].SetValue(selected)

    def apply_col(self, _event=None):
        """Call this to apply the colours and deselect all faces."""
        self.faces_list.deselect_all(apply_col=True)

    def on_select_all(self, _event):
        """Select all faces in the faces list."""
        self.set_all_selected(True)

    def on_unselect_all(self, _event):
        """Unselect all faces in the faces list."""
        self.set_all_selected(False)

    def on_delete(self, _event):
        """Delete selected faces and ."""
        self.shape.remove_faces(self.faces_list.selected_faces)
        self.faces_list.update_face_list()
        self._update_shape()

    def reset(self):
        """Handle when a face is selected by updating the colour."""
        self.shape.face_props = self._org_face_props
        self.faces_list.update_face_list()
        self._update_shape()


class FacesWindow(wx.Frame):  # pylint: disable=too-few-public-methods
    """Window to edit which faces should be shown"""

    def __init__(self, canvas, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas = canvas
        self.status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.add_content()

    def add_content(self):
        """Add GUI widgets to the panel"""
        self.guis = []
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(self.panel)
        self.guis.append(self.notebook)
        self.tabs = [
            FacesTab(self.notebook, shape, self.update_shape)
            for i, shape in enumerate(self.canvas.shape)
        ]
        for tab in self.tabs:
            self.notebook.AddPage(tab, f"{tab.shape.name}")
            self.guis.append(tab)

        # Buttons
        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.guis.append(wx.Button(self.panel, label="Cancel"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_cancel)
        self.buttons_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        self.guis.append(wx.Button(self.panel, label="Reset all"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_reset)
        self.buttons_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        self.guis.append(wx.Button(self.panel, label="Done"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_done)
        self.buttons_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        # Sizer stuff
        self.main_sizer.Add(self.notebook, 1, wx.EXPAND)
        self.main_sizer.Add(self.buttons_sizer, 0)
        self.panel.SetSizer(self.main_sizer)
        self.panel.Layout()
        self.Show(True)

    def update_shape(self):
        """Update shape on display"""
        self.canvas.shape.merge_needed = True
        self.canvas.paint()

    def on_reset(self, _event):
        """Restore all faces but don't close window."""
        for tab in self.tabs:
            tab.reset()

    def on_cancel(self, event):
        """Restore all faces and close window."""
        self.on_reset(event)
        self.Close()

    def on_done(self, _event):
        """Apply colour to faces, and close window."""
        for tab in self.tabs:
            tab.apply_col()
        self.Close()


class TransformWindow(wx.Frame):  # pylint: disable=too-many-instance-attributes
    """Window with controls for transforming current shape

    The transform is applied dynamically (i.e. while window is still open), but can be canceled.
    """

    def __init__(self, canvas, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas = canvas
        self.status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.add_content()
        self.org_vs = self.canvas.shape.vertex_props["vs"]
        self.org_org_vs = self.org_vs  # for cancel
        self.set_status_text("")

    def add_content(self):
        """Create all wdigets for the transform window"""
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.rot_sizer = geom_gui.AxisRotateSizer(
            self.panel, self.on_rot, min_angle=-180, max_angle=180, initial_angle=0
        )
        self.main_sizer.Add(self.rot_sizer)

        self.guis = []

        # TODO: Add scale to transform
        # TODO: Add reflection

        # Transform
        translate_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(translate_sizer)
        self.guis.append(geom_gui.Vector3DInput(self.panel, "Translation vector:"))
        self.translation = self.guis[-1]
        translate_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        self.guis.append(wx.Button(self.panel, label="Translate"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_translate)
        translate_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        # Scale
        scale_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(scale_sizer)
        self.scale_factor_gui = geom_gui.FloatInput(self.panel, wx.ID_ANY, 1, max_len=16)
        self.guis.append(self.scale_factor_gui)
        scale_sizer.Add(self.scale_factor_gui, 0, wx.EXPAND)
        self.guis.append(wx.Button(self.panel, label="Scale"))
        scale_sizer.Add(self.guis[-1], 0, wx.EXPAND)
        self.guis[-1].Bind(
            wx.EVT_BUTTON,
            lambda _id: self.on_scale(self.scale_factor_gui.GetValue()),
        )

        self.sub_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(self.sub_sizer)

        self.guis.append(wx.Button(self.panel, label="Apply"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_apply)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label="Cancel"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_cancel)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label="Reset"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_reset)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label="Done"))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_done)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.panel.SetSizer(self.main_sizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    def on_rot(self, angle, axis):
        """Rotate shape"""
        if geomtypes.FloatHandler.eq(axis.norm(), 0):
            self.set_status_text("Please define a proper axis")
            return
        self.canvas.shape.vertex_props = {"vs": self.org_vs}
        self.canvas.shape.transform(
            geomtypes.Rot3(angle=geom_3d.DEG2RAD * angle, axis=axis)
        )
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_scale(self, factor):
        """Handle event '_' to invert shape"""
        # Assume compound shape
        self.canvas.shape.scale(factor)
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_translate(self, _=None):
        """Handle event '_' to translate shape"""
        # Assume compound shape
        new_vs = [
            [geomtypes.Vec3(v) + self.translation.get_vertex() for v in shape_vs]
            for shape_vs in self.org_vs
        ]
        self.canvas.shape.vertex_props = {"vs": new_vs}
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_apply(self, _=None):
        """Handle event '_' to confirm transform and prepare for a next one"""
        self.org_vs = self.canvas.shape.vertex_props["vs"]
        # reset the angle
        self.rot_sizer.set_angle(0)
        self.scale_factor_gui.SetValue(0)
        self.set_status_text("applied, now you can define another axis")

    def on_reset(self, _=None):
        """Handle event '_' to undo all transforms"""
        self.canvas.shape.vertex_props = {"vs": self.org_org_vs}
        self.canvas.paint()
        self.org_vs = self.org_org_vs

    def on_cancel(self, _=None):
        """Handle event '_' to cancel the current transform"""
        self.on_reset()
        self.Close()

    def on_done(self, _):
        """Handle event '_' to confirm all transforms are done"""
        self.Close()

    def close(self):
        """Destroy all gius for this window"""
        for gui in self.guis:
            gui.Destroy()

    def set_status_text(self, s):
        """Set text of the status bar for this window"""
        self.status_bar.SetStatusText(s)


class ViewSettingsWindow(wx.Frame):
    """Class for window with all view settings"""

    def __init__(self, canvas, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas = canvas
        self.status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.add_contents()

    def add_contents(self):
        """Fill window with all widgets"""
        self.ctrl_sizer = ViewSettingsSizer(self, self.panel, self.canvas)
        if self.canvas.shape.dimension == 4:
            self.set_default_size((413, 791))
        else:
            self.set_default_size((380, 414))
        self.panel.SetSizer(self.ctrl_sizer)
        self.panel.SetAutoLayout(True)
        self.panel.Layout()
        self.Show(True)

    # move to general class
    def set_default_size(self, size):
        """Set dedault window size"""
        self.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        self.SetSize(size)

    def rebuild(self):
        """Detroy and re-build the content of this windown"""
        # Doesn't work out of the box (Guis are not destroyed...):
        # self.ctrl_sizer.Destroy()
        self.ctrl_sizer.close()
        self.add_contents()

    def set_status_text(self, s):
        """Set text of the status bar for this window"""
        self.status_bar.SetStatusText(s)


class ViewSettingsSizer(wx.BoxSizer):  # pylint: disable=too-many-instance-attributes
    """A sizer with all view settings for the view settings window"""

    cull_show_none = "Hide"
    cull_show_both = "Show Front and Back Faces"
    cull_show_front = "Show Only Front Face"
    cull_show_back = "Show Only Back Face"

    # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    def __init__(self, parent_win, parent_panel, canvas, *args, **kwargs):
        """
        Create a sizer with view settings.

        parent_win: the parent_win object. This is used to update de status string in the status
                    bar. The parent window is supposed to contain a function set_status_text for
                    this to work.
        parent_panel: The panel to add all control widgets to.
        canvas: An interactive 3D canvas object. This object is supposed to have a shape field that
                points to the shape object that is being viewed.
        """

        self.guis = []
        self.boxes = []
        wx.BoxSizer.__init__(self, wx.VERTICAL, *args, **kwargs)
        self.canvas = canvas
        self.parent_win = parent_win
        self.parent_panel = parent_panel
        # Show / Hide vertices
        self.v_r = canvas.shape.vertex_props["radius"]
        self.v_opts_lst = ["hide", "show"]
        if self.v_r > 0:
            default = 1  # key(1) = 'show'
        else:
            default = 0  # key(0) = 'hide'
        self.v_opts_gui = wx.RadioBox(
            self.parent_panel,
            label="Vertex Options",
            style=wx.RA_VERTICAL,
            choices=self.v_opts_lst,
        )
        self.parent_panel.Bind(
            wx.EVT_RADIOBOX, self.on_v_option, id=self.v_opts_gui.GetId()
        )
        self.v_opts_gui.SetSelection(default)
        # Vertex Radius
        no_of_slider_steps = 40
        self.v_r_min = 0.01
        self.v_r_max = 0.100
        self.v_r_scale = 1.0 / self.v_r_min
        s = (self.v_r_max - self.v_r_min) * self.v_r_scale
        if int(s) < no_of_slider_steps:
            self.v_r_scale = (self.v_r_scale * no_of_slider_steps) / s
        self.v_r_gui = geom_gui.Slider(
            self.parent_panel,
            value=int(self.v_r_scale * self.v_r),
            minValue=int(self.v_r_scale * self.v_r_min),
            maxValue=int(self.v_r_scale * self.v_r_max),
            style=wx.SL_HORIZONTAL,
        )
        self.guis.append(self.v_r_gui)
        self.parent_panel.Bind(wx.EVT_SLIDER, self.on_v_radius, id=self.v_r_gui.GetId())
        self.boxes.append(wx.StaticBox(self.parent_panel, label="Vertex radius"))
        v_r_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        # disable if vertices are hidden anyway:
        if default != 1:
            self.v_r_gui.Disable()
        # Vertex Colour
        self.v_col_gui = wx.Button(self.parent_panel, wx.ID_ANY, "Colour")
        self.guis.append(self.v_col_gui)
        self.parent_panel.Bind(wx.EVT_BUTTON, self.on_v_col, id=self.v_col_gui.GetId())
        # Show / hide edges
        e_props = canvas.shape.edge_props
        self.e_r = e_props["radius"]
        self.e_opts_lst = ["hide", "as cylinders", "as lines"]
        if e_props["draw_edges"]:
            if self.v_r > 0:
                default = 1  # key(1) = 'as cylinders'
            else:
                default = 2  # key(2) = 'as lines'
        else:
            default = 0  # key(0) = 'hide'
        self.e_opts_gui = wx.RadioBox(
            self.parent_panel,
            label="Edge Options",
            style=wx.RA_VERTICAL,
            choices=self.e_opts_lst,
        )
        self.guis.append(self.e_opts_gui)
        self.parent_panel.Bind(
            wx.EVT_RADIOBOX, self.on_e_option, id=self.e_opts_gui.GetId()
        )
        self.e_opts_gui.SetSelection(default)
        # Edge Radius
        no_of_slider_steps = 40
        self.e_r_min = 0.008
        self.e_r_max = 0.08
        self.e_r_scale = 1.0 / self.e_r_min
        s = (self.e_r_max - self.e_r_min) * self.e_r_scale
        if int(s) < no_of_slider_steps:
            self.e_r_scale = (self.e_r_scale * no_of_slider_steps) / s
        self.e_r_gui = geom_gui.Slider(
            self.parent_panel,
            value=int(self.e_r_scale * self.e_r),
            minValue=int(self.e_r_scale * self.e_r_min),
            maxValue=int(self.e_r_scale * self.e_r_max),
            style=wx.SL_HORIZONTAL,
        )
        self.guis.append(self.e_r_gui)
        self.parent_panel.Bind(wx.EVT_SLIDER, self.on_e_radius, id=self.e_r_gui.GetId())
        self.boxes.append(wx.StaticBox(self.parent_panel, label="Edge radius"))
        e_r_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        # disable if edges are not drawn as scalable items anyway:
        if default != 1:
            self.e_r_gui.Disable()
        # Edge Colour
        self.e_col_gui = wx.Button(self.parent_panel, wx.ID_ANY, "Colour")
        self.guis.append(self.e_col_gui)
        self.parent_panel.Bind(wx.EVT_BUTTON, self.on_e_col, id=self.e_col_gui.GetId())
        # Show / hide face
        self.f_opts_lst = [
            self.cull_show_both,
            self.cull_show_front,
            self.cull_show_back,
            self.cull_show_none,
        ]
        self.f_opts_gui = wx.RadioBox(
            self.parent_panel,
            label="Face Options",
            style=wx.RA_VERTICAL,
            choices=self.f_opts_lst,
        )
        self.guis.append(self.f_opts_gui)
        self.parent_panel.Bind(
            wx.EVT_RADIOBOX, self.on_f_option, id=self.f_opts_gui.GetId()
        )
        f_sizer = wx.BoxSizer(wx.HORIZONTAL)
        f_sizer.Add(self.f_opts_gui, 1, wx.EXPAND)
        if not GL.glIsEnabled(GL.GL_CULL_FACE):
            self.f_opts_gui.SetStringSelection(self.cull_show_both)
        else:
            # Looks like I switch front and back here, but this makes sense from
            # the GUI.
            if GL.glGetInteger(GL.GL_CULL_FACE_MODE) == GL.GL_FRONT:
                self.f_opts_gui.SetStringSelection(self.cull_show_front)
            if GL.glGetInteger(GL.GL_CULL_FACE_MODE) == GL.GL_BACK:
                self.f_opts_gui.SetStringSelection(self.cull_show_back)
            else:  # ie GL.GL_FRONT_AND_BACK
                self.f_opts_gui.SetStringSelection(self.cull_show_none)

        # Open GL
        self.boxes.append(wx.StaticBox(self.parent_panel, label="OpenGL Settings"))
        back_front_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        self.guis.append(
            wx.CheckBox(self.parent_panel, label="Switch Front and Back Face (F3)"),
        )
        self.front_back_gui = self.guis[-1]
        self.front_back_gui.SetValue(GL.glGetIntegerv(GL.GL_FRONT_FACE) == GL.GL_CW)
        self.parent_panel.Bind(
            wx.EVT_CHECKBOX,
            self.on_front_back,
            id=self.front_back_gui.GetId(),
        )
        # background Colour
        col_txt = wx.StaticText(self.parent_panel, -1, "Background Colour: ")
        self.guis.append(col_txt)
        col = self.canvas.bg_col
        self.bg_col_gui = wx.lib.colourselect.ColourSelect(
            self.parent_panel,
            wx.ID_ANY,
            colour=col,
            size=wx.Size(40, 30),
        )
        self.guis.append(self.bg_col_gui)
        self.parent_panel.Bind(wx.lib.colourselect.EVT_COLOURSELECT, self.on_bg_col)

        # Sizers
        v_r_sizer.Add(self.v_r_gui, 1, wx.EXPAND | wx.TOP | wx.LEFT)
        v_r_sizer.Add(self.v_col_gui, 1, wx.BOTTOM | wx.LEFT)
        e_r_sizer.Add(self.e_r_gui, 1, wx.EXPAND | wx.TOP | wx.LEFT)
        e_r_sizer.Add(self.e_col_gui, 1, wx.BOTTOM | wx.LEFT)
        # sizer = wx.BoxSizer(wx.VERTICAL)
        v_sizer = wx.BoxSizer(wx.HORIZONTAL)
        v_sizer.Add(self.v_opts_gui, 2, wx.EXPAND)
        v_sizer.Add(v_r_sizer, 5, wx.EXPAND)
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)
        e_sizer.Add(self.e_opts_gui, 2, wx.EXPAND)
        e_sizer.Add(e_r_sizer, 5, wx.EXPAND)
        bg_sizer_sub = wx.BoxSizer(wx.HORIZONTAL)
        bg_sizer_sub.Add(col_txt, 0, wx.EXPAND)
        bg_sizer_sub.Add(self.bg_col_gui, 0, wx.EXPAND)
        bg_sizer_sub.Add(wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND)
        back_front_sizer.Add(self.front_back_gui, 0, wx.EXPAND)
        back_front_sizer.Add(bg_sizer_sub, 0, wx.EXPAND)
        self.Add(v_sizer, 5, wx.EXPAND)
        self.Add(e_sizer, 5, wx.EXPAND)
        self.Add(f_sizer, 6, wx.EXPAND)
        self.Add(back_front_sizer, 0, wx.EXPAND)

        # 4D stuff
        if self.canvas.shape.dimension == 4:
            default = 0
            self.use_transparency_gui = wx.RadioBox(
                self.parent_panel,
                label="Use Transparency",
                style=wx.RA_VERTICAL,
                choices=["Yes", "No"],
            )
            self.guis.append(self.use_transparency_gui)
            self.parent_panel.Bind(
                wx.EVT_RADIOBOX,
                self.on_use_transparent,
                id=self.use_transparency_gui.GetId(),
            )
            self.use_transparency_gui.SetSelection(default)
            f_sizer.Add(self.use_transparency_gui, 1, wx.EXPAND)

            default = 0
            self.show_es_unscaled_gui = wx.RadioBox(
                self.parent_panel,
                label="Unscaled Edges",
                style=wx.RA_VERTICAL,
                choices=["Show", "Hide"],
            )
            self.guis.append(self.show_es_unscaled_gui)
            self.parent_panel.Bind(
                wx.EVT_RADIOBOX,
                self.on_show_unscaled_es,
                id=self.show_es_unscaled_gui.GetId(),
            )
            self.show_es_unscaled_gui.SetSelection(default)
            f_sizer.Add(self.show_es_unscaled_gui, 1, wx.EXPAND)

            min_val = 0.01
            max_val = 1.0
            steps = 100
            self.cell_scale_factor = float(max_val - min_val) / steps
            self.cell_scale_offset = min_val
            self.scale_gui = geom_gui.Slider(
                self.parent_panel,
                value=100,
                minValue=0,
                maxValue=steps,
                style=wx.SL_HORIZONTAL,
            )
            self.guis.append(self.scale_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_scale, id=self.scale_gui.GetId()
            )
            self.boxes.append(wx.StaticBox(self.parent_panel, label="Scale Cells"))
            scale_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            scale_sizer.Add(self.scale_gui, 1, wx.EXPAND)

            # 4D -> 3D projection properties: camera and prj volume distance
            steps = 100
            min_val = 0.1
            max_val = 5
            self.prj_vol_factor = float(max_val - min_val) / steps
            self.prj_vol_offset = min_val
            self.prj_vol_gui = geom_gui.Slider(
                self.parent_panel,
                value=self.val_2_slider(
                    self.prj_vol_factor,
                    self.prj_vol_offset,
                    self.canvas.shape.w_prj_vol,
                ),
                minValue=0,
                maxValue=steps,
                style=wx.SL_HORIZONTAL,
            )
            self.guis.append(self.prj_vol_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_prj_vol_adjust, id=self.prj_vol_gui.GetId()
            )
            self.boxes.append(
                wx.StaticBox(self.parent_panel, label="Projection Volume W-Coordinate")
            )
            prj_vol_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            prj_vol_sizer.Add(self.prj_vol_gui, 1, wx.EXPAND)
            min_val = 0.5
            max_val = 5
            self.cam_dist_factor = float(max_val - min_val) / steps
            self.cam_dist_offset = min_val
            self.cam_dist_gui = geom_gui.Slider(
                self.parent_panel,
                value=self.val_2_slider(
                    self.cam_dist_factor,
                    self.cam_dist_offset,
                    self.canvas.shape.w_cam_offset,
                ),
                minValue=0,
                maxValue=steps,
                style=wx.SL_HORIZONTAL,
            )
            self.guis.append(self.cam_dist_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.on_prj_vol_adjust, id=self.cam_dist_gui.GetId()
            )
            self.boxes.append(
                wx.StaticBox(
                    self.parent_panel, label="Camera Distance (from projection volume)"
                )
            )
            cam_dist_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            cam_dist_sizer.Add(self.cam_dist_gui, 1, wx.EXPAND)

            # Create a ctrl for specifying a 4D rotation
            self.boxes.append(wx.StaticBox(parent_panel, label="Rotate 4D Object"))
            rotation_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
            self.boxes.append(wx.StaticBox(parent_panel, label="In a Plane Spanned by"))
            plane_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
            self.v0_gui = geom_gui.Vector4DInput(
                self.parent_panel,
                # label='Vector 1',
                rel_float_size=4,
                elem_labels=["x0", "y0", "z0", "w0"],
            )
            self.parent_panel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, self.rotate, id=self.v0_gui.GetId()
            )
            self.v1_gui = geom_gui.Vector4DInput(
                self.parent_panel,
                # label='Vector 1',
                rel_float_size=4,
                elem_labels=["x1", "y1", "z1", "w1"],
            )
            self.parent_panel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, self.rotate, id=self.v1_gui.GetId()
            )
            # Exchange planes
            self.switch_planes_gui = wx.CheckBox(
                self.parent_panel,
                label="Use Orthogonal Plane instead",
            )
            self.switch_planes_gui.SetValue(False)
            self.parent_panel.Bind(
                wx.EVT_CHECKBOX,
                self.rotate,
                id=self.switch_planes_gui.GetId(),
            )
            # self.boxes.append?
            self.guis.append(self.v0_gui)
            self.guis.append(self.v1_gui)
            self.guis.append(self.switch_planes_gui)
            plane_sizer.Add(self.v0_gui, 12, wx.EXPAND)
            plane_sizer.Add(self.v1_gui, 12, wx.EXPAND)
            plane_sizer.Add(self.switch_planes_gui, 10, wx.EXPAND)

            min_val = 0.00
            max_val = math.pi
            # step by degree (if you change this, make at least 30 and 45 degrees possible)
            steps = 360
            self.angle_factor = float(max_val - min_val) / steps
            self.angle_offset = min_val
            self.angle_gui = geom_gui.Slider(
                self.parent_panel,
                value=0,
                minValue=0,
                maxValue=steps,
                style=wx.SL_HORIZONTAL,
            )
            self.guis.append(self.angle_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.rotate, id=self.angle_gui.GetId()
            )
            self.boxes.append(wx.StaticBox(self.parent_panel, label="Using Angle"))
            angle_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            angle_sizer.Add(self.angle_gui, 1, wx.EXPAND)

            min_val = 0.00
            max_val = 1.0
            steps = 100
            self.angle_scale_factor = float(max_val - min_val) / steps
            self.angle_scale_offset = min_val
            self.angle_scale_gui = geom_gui.Slider(
                self.parent_panel,
                value=0,
                minValue=0,
                maxValue=steps,
                style=wx.SL_HORIZONTAL,
            )
            self.guis.append(self.angle_scale_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.rotate, id=self.angle_scale_gui.GetId()
            )
            self.boxes.append(
                wx.StaticBox(
                    self.parent_panel,
                    label="Set Angle (by Scale) of Rotation in the Orthogonal Plane",
                )
            )
            angle_scale_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            angle_scale_sizer.Add(self.angle_scale_gui, 1, wx.EXPAND)

            rotation_sizer.Add(plane_sizer, 12, wx.EXPAND)
            rotation_sizer.Add(angle_sizer, 5, wx.EXPAND)
            rotation_sizer.Add(angle_scale_sizer, 5, wx.EXPAND)

            self.Add(scale_sizer, 3, wx.EXPAND)
            self.Add(prj_vol_sizer, 3, wx.EXPAND)
            self.Add(cam_dist_sizer, 3, wx.EXPAND)
            self.Add(rotation_sizer, 12, wx.EXPAND)

        self.set_status_text()

    def close(self):
        """Close down view settings window"""
        # The 'try' is necessary, since the boxes are destroyed in some OS,
        # while this is necessary for e.g. Ubuntu Hardy Heron.
        # for pylint; prevent duplicate-code
        my_boxes = self.boxes
        for box in my_boxes:
            try:
                box.Destroy()
            except RuntimeError:
                # The user probably closed the window already
                pass
        # for pylint; prevent duplicate-code
        my_guis = self.guis
        for gui in my_guis:
            gui.Destroy()

    def set_status_text(self):
        """Set status text of view settings window"""
        try:
            self.parent_win.set_status_text(
                f"V-Radius: {self.v_r:0.5f}; E-Radius: {self.e_r:0.5f}"
            )
        except AttributeError:
            logging.warning("parent_win.set_status_text function undefined")

    def on_v_option(self, _):
        """Handle event '_' to show or hide vertex"""
        sel = self.v_opts_gui.GetSelection()
        sel_str = self.v_opts_lst[sel]
        if sel_str == "show":
            self.v_r_gui.Enable()
            self.canvas.shape.vertex_props = {"radius": self.v_r}
        elif sel_str == "hide":
            self.v_r_gui.Disable()
            self.canvas.shape.vertex_props = {"radius": -1.0}
        self.canvas.paint()

    def on_v_radius(self, _):
        """Handle event '_' to set vertex radius as according to settings"""
        self.v_r = float(self.v_r_gui.GetValue()) / self.v_r_scale
        self.canvas.shape.vertex_props = {"radius": self.v_r}
        self.canvas.paint()
        self.set_status_text()

    def on_v_col(self, _):
        """Handle event '_' to set vertex colour as according to settings"""
        dlg = wx.ColourDialog(self.parent_win)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgba = data.GetColour()
            rgb = rgba.Get()
            self.canvas.shape.vertex_props = {"color": rgb[:3]}
            self.canvas.paint()
        dlg.Destroy()

    def on_e_option(self, _):
        """Handle event '_' to hide or show and edge either as a line or a cylinder"""
        sel = self.e_opts_gui.GetSelection()
        sel_str = self.e_opts_lst[sel]
        if sel_str == "hide":
            self.e_r_gui.Disable()
            self.canvas.shape.edge_props = {"draw_edges": False}
        elif sel_str == "as cylinders":
            self.e_r_gui.Enable()
            self.canvas.shape.edge_props = {"draw_edges": True, "radius": self.e_r}
        elif sel_str == "as lines":
            self.e_r_gui.Disable()
            self.canvas.shape.edge_props = {"draw_edges": True, "radius": 0}
        self.canvas.paint()

    def on_e_radius(self, _):
        """Handle event '_' to set edge radius as according to settings"""
        self.e_r = float(self.e_r_gui.GetValue()) / self.e_r_scale
        self.canvas.shape.edge_props = {"radius": self.e_r}
        self.canvas.paint()
        self.set_status_text()

    def on_e_col(self, _):
        """Handle event '_' to set edge colour as according to settings"""
        dlg = wx.ColourDialog(self.parent_win)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgba = data.GetColour()
            rgb = rgba.Get()
            self.canvas.shape.edge_props = {"color": rgb[:3]}
            self.canvas.paint()
        dlg.Destroy()

    def on_f_option(self, _):
        """Handle event '_' to show or hide faces as according to view settings"""
        logging.info("View Settings Window size: {self.parent_win.GetSize()}")
        sel = self.f_opts_gui.GetStringSelection()
        # Looks like I switch front and back here, but this makes sense from
        # the GUI.
        self.canvas.shape.face_props = {"draw_faces": True}
        if sel == self.cull_show_both:
            GL.glDisable(GL.GL_CULL_FACE)
        elif sel == self.cull_show_none:
            # don't use culling here: doesn't work with edge radius and vertext
            # radius > 0
            self.canvas.shape.face_props = {"draw_faces": False}
            GL.glDisable(GL.GL_CULL_FACE)
        elif sel == self.cull_show_front:
            GL.glCullFace(GL.GL_FRONT)
            GL.glEnable(GL.GL_CULL_FACE)
        elif self.cull_show_back:
            GL.glCullFace(GL.GL_BACK)
            GL.glEnable(GL.GL_CULL_FACE)
        self.canvas.paint()

    def on_front_back(self, e):
        """Handle event 'e' to switch definition of what is front and back of a face"""
        if e.GetId() == self.front_back_gui.GetId():
            Scenes3D.on_switch_front_and_back(self.canvas)

    def on_bg_col(self, e):
        """Handle event '_' to set background colour of shape canvas"""
        self.canvas.bg_col = e.GetValue().Get()[:3]
        self.canvas.paint()

    def on_use_transparent(self, _):
        """Handle event '_' to (re)set transparency for certain predefined polychoron faces"""
        self.canvas.shape.use_transparency(
            (self.use_transparency_gui.GetSelection() == 0)
        )
        self.canvas.paint()

    def on_show_unscaled_es(self, _):
        """Handle event '_' to show or hide unscaled edges of polychoron"""
        self.canvas.shape.edge_props = {
            "showUnscaled": (self.show_es_unscaled_gui.GetSelection() == 0),
        }
        self.canvas.paint()

    @staticmethod
    def val_2_slider(factor, offset, y):
        """Convert value a slider represents to slider value"""
        return int((y - offset) / factor)

    @staticmethod
    def slider_to_val(factor, offset, x):
        """Convert slider value to value it represents"""
        return factor * float(x) + offset

    def on_scale(self, _):
        """Handle event '_' to scale cells in polychoron from their centre"""
        scale = self.slider_to_val(
            self.cell_scale_factor,
            self.cell_scale_offset,
            self.scale_gui.GetValue(),
        )
        self.canvas.shape.set_cell_properties(scale=scale)
        self.canvas.paint()

    def on_prj_vol_adjust(self, e):
        """Handle event 'e' to adjust projection of polychoron to 3D according to settings"""
        cam_dist = self.slider_to_val(
            self.cam_dist_factor,
            self.cam_dist_offset,
            self.cam_dist_gui.GetValue(),
        )
        w_prj_vol = self.slider_to_val(
            self.prj_vol_factor,
            self.prj_vol_offset,
            self.prj_vol_gui.GetValue(),
        )
        if (cam_dist > 0) and (w_prj_vol > 0):
            self.parent_win.set_status_text(
                f"projection volume w = {w_prj_vol:0.2}; camera distance: {cam_dist:0.3}"
            )
        else:
            if cam_dist > 0:
                self.parent_win.set_status_text("Error: Camera distance should be > 0!")
            else:
                self.parent_win.set_status_text(
                    "Error: Projection volume:  w should be > 0!"
                )
        self.canvas.shape.set_projection(cam_dist, w_prj_vol)
        self.canvas.paint()
        e.Skip()

    def rotate(self, _):
        """Rotate polychoron object according to settings"""
        v0 = self.v0_gui.GetValue()
        v1 = self.v1_gui.GetValue()
        if (
            v0 == geomtypes.Vec([0, 0, 0, 0])
            or v1 == geomtypes.Vec([0, 0, 0, 0])
            or v0 == v1
        ):
            self.parent_win.set_status_text(
                "Please define two vectors spanning a plane"
            )
            return
        angle = self.slider_to_val(
            self.angle_factor,
            self.angle_offset,
            self.angle_gui.GetValue(),
        )
        scale = self.slider_to_val(
            self.angle_scale_factor,
            self.angle_scale_offset,
            self.angle_scale_gui.GetValue(),
        )
        angle = geomtypes.RoundedFloat(angle)
        if angle == 0:
            return
        scale = geomtypes.RoundedFloat(scale)
        try:
            v1 = v1.make_orthogonal_to(v0)
            # if vectors are exchange, you actually specify the axial plane
            if self.switch_planes_gui.IsChecked():
                if scale == 0:
                    r = geomtypes.Rot4(axialPlane=(v1, v0), angle=angle)
                else:
                    r = geomtypes.DoubleRot4(
                        axialPlane=(v1, v0), angle=(angle, scale * angle)
                    )
            else:
                r = geomtypes.DoubleRot4(
                    axialPlane=(v1, v0), angle=(scale * angle, angle)
                )
            self.canvas.shape.rotate(r)
            self.canvas.paint()
            deg = geom_3d.RAD2DEG * angle
            self.parent_win.set_status_text(
                f"Rotation angle: {deg} degrees (and angle scale {scale:0.2})"
            )
        except ZeroDivisionError:
            # zero division means 1 of the vectors is (0, 0, 0, 0)
            self.parent_win.set_status_text("Error: Don't use a zero vector")

        # except AssertionError:
        #     z_v = geomtypes.Vec4([0, 0, 0, 0])
        #     if v0 == z_v or v1 == z_v:
        #         self.parent_win.set_status_text("Error: Don't use a zero vector")
        #     else:
        #         self.parent_win.set_status_text("Error: The specified vectors are (too) parallel")
        #     pass
