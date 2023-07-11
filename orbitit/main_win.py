#!/usr/bin/env python3
"""Help windows class definitions for main utility"""
#
# Copyright (C) 2010-2021 Marcel Tunnissen
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
# pylint: disable=too-many-lines

import copy
import logging
import math
import wx
import wx.lib.intctrl
import wx.lib.colourselect

from OpenGL import GL

from orbitit import geom_3d, geom_gui, geomtypes, Scenes3D

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
        self.cols = self.canvas.shape.face_props['colors']
        # take a copy for reset
        self.org_cols = [[list(col_idx) for col_idx in shape_cols] for shape_cols in self.cols]
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
                wx_col = wx.Colour(255*col[0], 255*col[1], 255*col[2])
                if wx_col not in added_cols:
                    if i % self.col_width == 0:
                        col_sizer_row = wx.BoxSizer(wx.HORIZONTAL)
                        self.col_sizer.Add(col_sizer_row, 0, wx.EXPAND)
                    self.select_col_guis.append(
                        wx.ColourPickerCtrl(
                            self.panel, wx.ID_ANY, wx_col))
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

        self.guis.append(wx.Button(self.panel, label='Cancel'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_cancel)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Reset'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_reset)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Done'))
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
            wx_col = wx.Colour(255*c[0], 255*c[1], 255*c[2])
            col_gui.SetColour(wx_col)
        self.cols = [[list(col_idx) for col_idx in shape_cols] for shape_cols in self.org_cols]
        self.update_shape_cols()

    def on_cancel(self, _):
        """Handle event '_' to recover original shape colours and close window"""
        self.cols = [[list(col_idx) for col_idx in shape_cols] for shape_cols in self.org_cols]
        self.update_shape_cols()
        self.Close()

    def on_done(self, _):
        """Handle event '_' to confirms all colours"""
        self.Close()

    def on_col_select(self, e):
        """Handle event 'e' that is generated when a colour was updated"""
        wx_col = e.GetColour().Get()
        col = (float(wx_col[0])/255, float(wx_col[1])/255, float(wx_col[2])/255)
        gui_id = e.GetId()
        for gui in self.select_col_guis:
            if gui.GetId() == gui_id:
                shape_cols = self.cols[gui.my_shape_idx][0]
                for col_idx in gui.my_cols:
                    shape_cols[col_idx] = col
                self.update_shape_cols()

    def update_shape_cols(self):
        """Update the face colours of the current shape"""
        self.canvas.shape.face_props = {'colors': self.cols}
        self.canvas.paint()

    def close(self):
        """Destroy all widgets of the face colour window"""
        for gui in self.guis:
            gui.Destroy()

class FacesTab(wx.Panel):
    """A panel with all faces and colours of one SimpleShape (as part of a CompoundShape)"""

    def __init__(self, parent, shape, on_update):
        """
        Initialise the panel

        parent: parent gui
        shape: a simple shape. Make sure this is not a compound shape or a orbit shape e.g.
        on_update: call-back function that is called when the shape was updated
        """
        wx.Panel.__init__(self, parent)
        self.shape = shape
        self.update_shape = on_update
        self.org_face_props = copy.deepcopy(shape.face_props)
        self.faces_lst = None
        self.selection_col = (0, 0, 0)
        self.add_content()

    def update_face_list(self):
        """(Re)build the face list."""
        if self.faces_lst:
            self.faces_lst.ClearAll()
        self.faces_lst = wx.ListCtrl(self, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.faces_lst.InsertColumn(0, 'Index and Color (background)', width=250)
        face_cols = self.shape.shape_colors
        for i, col_i in enumerate(face_cols[1]):
            self.faces_lst.InsertItem(i, f"{i}")
            col = [int(255*c + 0.5) for c in face_cols[0][col_i]]
            self.faces_lst.SetItemBackgroundColour(i, wx.Colour(*col))
            col = [255 - c for c in col]
            self.faces_lst.SetItemTextColour(i, wx.Colour(*col))

    def add_content(self):
        """Add GUI windgets to this panel"""
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sel_col_sizer = wx.BoxSizer(wx.HORIZONTAL)
        col_txt_gui = wx.StaticText(self, -1, "Selection Colour:")
        self.selected_col_gui = wx.lib.colourselect.ColourSelect(
            self, wx.ID_ANY, colour=(0, 0, 0), size=wx.Size(40, 30),
        )
        self.sel_col_sizer.Add(col_txt_gui, 1)
        self.sel_col_sizer.Add(self.selected_col_gui, 1)
        self.selected_col_gui.Bind(wx.lib.colourselect.EVT_COLOURSELECT, self.on_selected_col)
        self.update_face_list()
        self.faces_lst.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select)
        self.faces_lst.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_deselect)
        self.main_sizer.Add(self.sel_col_sizer, 0)
        self.main_sizer.Add(self.faces_lst, 1, wx.EXPAND)
        self.SetSizer(self.main_sizer)
        self.Layout()

    def on_select(self, evt):
        """Handle when a face is selected by updating the colour."""
        self.on_update_col(evt.GetIndex(), self.selection_col)

    def on_deselect(self, evt):
        """Handle when a face is deselected by updating the colour."""
        org_cols = self.org_face_props["colors"]
        org_col_defs = org_cols[0]
        org_face_col_i = org_cols[1]
        org_col_i = org_face_col_i[evt.GetIndex()]
        self.on_update_col(evt.GetIndex(), org_col_defs[org_col_i])

    def on_update_col(self, face_i, new_col):
        """Handle when a face is selected or deselected by inverting the colour.

        face_i: index of the face
        new_col: new RGB colour for the face to use
        """
        col_prop = self.shape.shape_colors
        col_defs = col_prop[0]
        face_cols = col_prop[1]

        # update colour
        if new_col in col_defs:
            new_col_i = col_defs.index(new_col)
        else:
            new_col_i = len(col_defs)
            col_defs.append(new_col)
        face_cols[face_i] = new_col_i
        # This is needed since shape.shape_colors is not just an attribute, it is a setter
        self.shape.shape_colors = col_prop
        self.update_shape()

    def on_selected_col(self, evt):
        """Update the colour of the selected faces"""
        col = evt.GetValue().Get()
        new_col = [c / 255 for c in col][:3]
        item = self.faces_lst.GetFirstSelected()
        while item != -1:
            self.on_update_col(item, new_col)
            item = self.faces_lst.GetNextSelected(item)
        self.selection_col = new_col

class FacesWindow(wx.Frame):  # pylint: disable=too-few-public-methods
    """Window to edit which faces should be shown"""

    def __init__(self, canvas, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.canvas = canvas
        self.status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.add_content()

    def add_content(self):
        """Add GUI windgets to the panel"""
        self.nb_sizer = wx.BoxSizer()
        self.nb = wx.Notebook(self.panel)
        self.tabs = [
            FacesTab(self.nb, shape, self.update_shape)
            for i, shape in enumerate(self.canvas.shape)
        ]
        for tab in self.tabs:
            self.nb.AddPage(tab, f"{tab.shape.name}")
        self.nb_sizer.Add(self.nb, 1, wx.EXPAND)
        self.panel.SetSizer(self.nb_sizer)
        self.panel.Layout()
        self.Show(True)

    def update_shape(self):
        """Update shape on display"""
        self.canvas.paint()

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
        self.org_vs = self.canvas.shape.vertex_props['vs']
        self.org_org_vs = self.org_vs # for cancel
        self.set_status_text("")

    def add_content(self):
        """Create all wdigets for the transform window"""
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.rot_sizer = geom_gui.AxisRotateSizer(
            self.panel, self.on_rot, min_angle=-180, max_angle=180, initial_angle=0)
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
        self.guis.append(wx.Button(self.panel, label='Translate'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_translate)
        translate_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        # Invert
        invert_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(invert_sizer)
        self.guis.append(wx.Button(self.panel, label='Invert'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_invert)
        invert_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.sub_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(self.sub_sizer)

        self.guis.append(wx.Button(self.panel, label='Apply'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_apply)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Cancel'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_cancel)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Reset'))
        self.guis[-1].Bind(wx.EVT_BUTTON, self.on_reset)
        self.sub_sizer.Add(self.guis[-1], 0, wx.EXPAND)

        self.guis.append(wx.Button(self.panel, label='Done'))
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
        self.canvas.shape.transform(geomtypes.Rot3(angle=geom_3d.DEG2RAD*angle, axis=axis))
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_invert(self, _=None):
        """Handle event '_' to invert shape"""
        # Assume compound shape
        self.canvas.shape.scale(-1)
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_translate(self, _=None):
        """Handle event '_' to translate shape"""
        # Assume compound shape
        new_vs = [
            [
                geomtypes.Vec3(v) + self.translation.get_vertex()
                for v in shape_vs
            ]
            for shape_vs in self.org_vs
        ]
        self.canvas.shape.vertex_props = {'vs': new_vs}
        self.canvas.paint()
        self.set_status_text("Use 'Apply' to define a subsequent transform")

    def on_apply(self, _=None):
        """Handle event '_' to confirm transform and prepare for a next one"""
        self.org_vs = self.canvas.shape.vertex_props['vs']
        # reset the angle
        self.rot_sizer.set_angle(0)
        self.set_status_text("applied, now you can define another axis")

    def on_reset(self, _=None):
        """Handle event '_' to undo all transforms"""
        self.canvas.shape.vertex_props = {'vs': self.org_org_vs}
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
        #self.ctrl_sizer.Destroy()
        self.ctrl_sizer.close()
        self.add_contents()

    def set_status_text(self, s):
        """Set text of the status bar for this window"""
        self.status_bar.SetStatusText(s)

class ViewSettingsSizer(wx.BoxSizer):  # pylint: disable=too-many-instance-attributes
    """A sizer with all view settings for the view settings window"""

    cull_show_none = 'Hide'
    cull_show_both = 'Show Front and Back Faces'
    cull_show_front = 'Show Only Front Face'
    cull_show_back = 'Show Only Back Face'

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
        self.v_r = canvas.shape.vertex_props['radius']
        self.v_opts_lst = ['hide', 'show']
        if self.v_r > 0:
            default = 1  # key(1) = 'show'
        else:
            default = 0  # key(0) = 'hide'
        self.v_opts_gui = wx.RadioBox(
            self.parent_panel,
            label='Vertex Options',
            style=wx.RA_VERTICAL,
            choices=self.v_opts_lst,
        )
        self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_v_option, id=self.v_opts_gui.GetId())
        self.v_opts_gui.SetSelection(default)
        # Vertex Radius
        no_of_slider_steps = 40
        self.v_r_min = 0.01
        self.v_r_max = 0.100
        self.v_r_scale = 1.0 / self.v_r_min
        s = (self.v_r_max - self.v_r_min) * self.v_r_scale
        if int(s) < no_of_slider_steps:
            self.v_r_scale = (self.v_r_scale * no_of_slider_steps) / s
        self.v_r_gui = wx.Slider(
            self.parent_panel,
            value=self.v_r_scale * self.v_r,
            minValue=self.v_r_scale * self.v_r_min,
            maxValue=self.v_r_scale * self.v_r_max,
            style=wx.SL_HORIZONTAL,
        )
        self.guis.append(self.v_r_gui)
        self.parent_panel.Bind(wx.EVT_SLIDER, self.on_v_radius, id=self.v_r_gui.GetId())
        self.boxes.append(wx.StaticBox(self.parent_panel, label='Vertex radius'))
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
        self.e_r = e_props['radius']
        self.e_opts_lst = ['hide', 'as cylinders', 'as lines']
        if e_props['draw_edges']:
            if self.v_r > 0:
                default = 1 # key(1) = 'as cylinders'
            else:
                default = 2 # key(2) = 'as lines'
        else:
            default = 0 # key(0) = 'hide'
        self.e_opts_gui = wx.RadioBox(
            self.parent_panel,
            label='Edge Options',
            style=wx.RA_VERTICAL,
            choices=self.e_opts_lst,
        )
        self.guis.append(self.e_opts_gui)
        self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_e_option, id=self.e_opts_gui.GetId())
        self.e_opts_gui.SetSelection(default)
        # Edge Radius
        no_of_slider_steps = 40
        self.e_r_min = 0.008
        self.e_r_max = 0.08
        self.e_r_scale = 1.0 / self.e_r_min
        s = (self.e_r_max - self.e_r_min) * self.e_r_scale
        if int(s) < no_of_slider_steps:
            self.e_r_scale = (self.e_r_scale * no_of_slider_steps) / s
        self.e_r_gui = wx.Slider(
            self.parent_panel,
            value=self.e_r_scale * self.e_r,
            minValue=self.e_r_scale * self.e_r_min,
            maxValue=self.e_r_scale * self.e_r_max,
            style=wx.SL_HORIZONTAL,
        )
        self.guis.append(self.e_r_gui)
        self.parent_panel.Bind(wx.EVT_SLIDER, self.on_e_radius, id=self.e_r_gui.GetId())
        self.boxes.append(wx.StaticBox(self.parent_panel, label='Edge radius'))
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
            label='Face Options',
            style=wx.RA_VERTICAL,
            choices=self.f_opts_lst,
        )
        self.guis.append(self.f_opts_gui)
        self.parent_panel.Bind(wx.EVT_RADIOBOX, self.on_f_option, id=self.f_opts_gui.GetId())
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
            else: # ie GL.GL_FRONT_AND_BACK
                self.f_opts_gui.SetStringSelection(self.cull_show_none)

        # Open GL
        self.boxes.append(wx.StaticBox(self.parent_panel, label='OpenGL Settings'))
        back_front_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
        self.guis.append(
            wx.CheckBox(self.parent_panel, label='Switch Front and Back Face (F3)'),
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
            wx.ID_ANY, colour=(col[0]*255, col[1]*255, col[2]*255),
            size=wx.Size(40, 30),
        )
        self.guis.append(self.bg_col_gui)
        self.parent_panel.Bind(wx.lib.colourselect.EVT_COLOURSELECT, self.on_bg_col)

        # Sizers
        v_r_sizer.Add(self.v_r_gui, 1, wx.EXPAND | wx.TOP | wx.LEFT)
        v_r_sizer.Add(self.v_col_gui, 1, wx.BOTTOM | wx.LEFT)
        e_r_sizer.Add(self.e_r_gui, 1, wx.EXPAND | wx.TOP | wx.LEFT)
        e_r_sizer.Add(self.e_col_gui, 1, wx.BOTTOM | wx.LEFT)
        #sizer = wx.BoxSizer(wx.VERTICAL)
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
                label='Use Transparency',
                style=wx.RA_VERTICAL,
                choices=['Yes', 'No'],
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
                label='Unscaled Edges',
                style=wx.RA_VERTICAL,
                choices=['Show', 'Hide'],
            )
            self.guis.append(self.show_es_unscaled_gui)
            self.parent_panel.Bind(
                wx.EVT_RADIOBOX, self.on_show_unscaled_es,
                id=self.show_es_unscaled_gui.GetId(),
            )
            self.show_es_unscaled_gui.SetSelection(default)
            f_sizer.Add(self.show_es_unscaled_gui, 1, wx.EXPAND)

            min_val = 0.01
            max_val = 1.0
            steps = 100
            self.cell_scale_factor = float(max_val - min_val) / steps
            self.cell_scale_offset = min_val
            self.scale_gui = wx.Slider(
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
            self.boxes.append(wx.StaticBox(self.parent_panel, label='Scale Cells'))
            scale_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            scale_sizer.Add(self.scale_gui, 1, wx.EXPAND)

            # 4D -> 3D projection properties: camera and prj volume distance
            steps = 100
            min_val = 0.1
            max_val = 5
            self.prj_vol_factor = float(max_val - min_val) / steps
            self.prj_vol_offset = min_val
            self.prj_vol_gui = wx.Slider(
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
                wx.StaticBox(self.parent_panel, label='Projection Volume W-Coordinate')
            )
            prj_vol_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            prj_vol_sizer.Add(self.prj_vol_gui, 1, wx.EXPAND)
            min_val = 0.5
            max_val = 5
            self.cam_dist_factor = float(max_val - min_val) / steps
            self.cam_dist_offset = min_val
            self.cam_dist_gui = wx.Slider(
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
                wx.StaticBox(self.parent_panel, label='Camera Distance (from projection volume)')
            )
            cam_dist_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            cam_dist_sizer.Add(self.cam_dist_gui, 1, wx.EXPAND)

            # Create a ctrl for specifying a 4D rotation
            self.boxes.append(wx.StaticBox(parent_panel, label='Rotate 4D Object'))
            rotation_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
            self.boxes.append(wx.StaticBox(parent_panel, label='In a Plane Spanned by'))
            plane_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.VERTICAL)
            self.v0_gui = geom_gui.Vector4DInput(
                self.parent_panel,
                #label='Vector 1',
                rel_float_size=4,
                elem_labels=['x0', 'y0', 'z0', 'w0']
            )
            self.parent_panel.Bind(
                geom_gui.EVT_VECTOR_UPDATED, self.rotate, id=self.v0_gui.GetId()
            )
            self.v1_gui = geom_gui.Vector4DInput(
                self.parent_panel,
                #label='Vector 1',
                rel_float_size=4,
                elem_labels=['x1', 'y1', 'z1', 'w1']
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
            #self.boxes.append?
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
            self.angle_gui = wx.Slider(
                self.parent_panel,
                value=0,
                minValue=0,
                maxValue=steps,
                style=wx.SL_HORIZONTAL
            )
            self.guis.append(self.angle_gui)
            self.parent_panel.Bind(wx.EVT_SLIDER, self.rotate, id=self.angle_gui.GetId())
            self.boxes.append(wx.StaticBox(self.parent_panel, label='Using Angle'))
            angle_sizer = wx.StaticBoxSizer(self.boxes[-1], wx.HORIZONTAL)
            angle_sizer.Add(self.angle_gui, 1, wx.EXPAND)

            min_val = 0.00
            max_val = 1.0
            steps = 100
            self.angle_scale_factor = float(max_val - min_val) / steps
            self.angle_scale_offset = min_val
            self.angle_scale_gui = wx.Slider(
                self.parent_panel,
                value=0,
                minValue=0,
                maxValue=steps,
                style=wx.SL_HORIZONTAL
            )
            self.guis.append(self.angle_scale_gui)
            self.parent_panel.Bind(
                wx.EVT_SLIDER, self.rotate, id=self.angle_scale_gui.GetId()
            )
            self.boxes.append(
                wx.StaticBox(
                    self.parent_panel,
                    label='Set Angle (by Scale) of Rotation in the Orthogonal Plane',
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
        if sel_str == 'show':
            self.v_r_gui.Enable()
            self.canvas.shape.vertex_props = {'radius': self.v_r}
        elif sel_str == 'hide':
            self.v_r_gui.Disable()
            self.canvas.shape.vertex_props = {'radius': -1.0}
        self.canvas.paint()

    def on_v_radius(self, _):
        """Handle event '_' to set vertex radius as according to settings"""
        self.v_r = float(self.v_r_gui.GetValue()) / self.v_r_scale
        self.canvas.shape.vertex_props = {'radius': self.v_r}
        self.canvas.paint()
        self.set_status_text()

    def on_v_col(self, _):
        """Handle event '_' to set vertex colour as according to settings"""
        dlg = wx.ColourDialog(self.parent_win)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgba = data.GetColour()
            rgb = rgba.Get()
            self.canvas.shape.vertex_props = {'color': [float(i)/255 for i in rgb]}
            self.canvas.paint()
        dlg.Destroy()

    def on_e_option(self, _):
        """Handle event '_' to hide or show and edge either as a line or a cylinder"""
        sel = self.e_opts_gui.GetSelection()
        sel_str = self.e_opts_lst[sel]
        if sel_str == 'hide':
            self.e_r_gui.Disable()
            self.canvas.shape.edge_props = {'draw_edges': False}
        elif sel_str == 'as cylinders':
            self.e_r_gui.Enable()
            self.canvas.shape.edge_props = {'draw_edges': True, 'radius': self.e_r}
        elif sel_str == 'as lines':
            self.e_r_gui.Disable()
            self.canvas.shape.edge_props = {'draw_edges': True, 'radius': 0}
        self.canvas.paint()

    def on_e_radius(self, _):
        """Handle event '_' to set edge radius as according to settings"""
        self.e_r = float(self.e_r_gui.GetValue()) / self.e_r_scale
        self.canvas.shape.edge_props = {'radius': self.e_r}
        self.canvas.paint()
        self.set_status_text()

    def on_e_col(self, _):
        """Handle event '_' to set edge colour as according to settings"""
        dlg = wx.ColourDialog(self.parent_win)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            rgba = data.GetColour()
            rgb = rgba.Get()
            self.canvas.shape.edge_props = {'color': [float(i)/255 for i in rgb]}
            self.canvas.paint()
        dlg.Destroy()

    def on_f_option(self, _):
        """Handle event '_' to show or hide faces as according to view settings"""
        logging.info("View Settings Window size: {self.parent_win.GetSize()}")
        sel = self.f_opts_gui.GetStringSelection()
        # Looks like I switch front and back here, but this makes sense from
        # the GUI.
        self.canvas.shape.face_props = {'draw_faces': True}
        if sel == self.cull_show_both:
            GL.glDisable(GL.GL_CULL_FACE)
        elif sel == self.cull_show_none:
            # don't use culling here: doesn't work with edge radius and vertext
            # radius > 0
            self.canvas.shape.face_props = {'draw_faces': False}
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
        col = e.GetValue().Get()
        self.canvas.bg_col = [float(col[0])/255, float(col[1])/255, float(col[2])/255]
        self.canvas.paint()

    def on_use_transparent(self, _):
        """Handle event '_' to (re)set transparency for certain predefined polychoron faces"""
        self.canvas.shape.use_transparency((self.use_transparency_gui.GetSelection() == 0))
        self.canvas.paint()

    def on_show_unscaled_es(self, _):
        """Handle event '_' to show or hide unscaled edges of polychoron"""
        self.canvas.shape.edge_props = {
            'showUnscaled': (self.show_es_unscaled_gui.GetSelection() == 0),
        }
        self.canvas.paint()

    @staticmethod
    def val_2_slider(factor, offset, y):
        """Convert value a slider represents to slider value"""
        return (y - offset) / factor

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
                self.parent_win.set_status_text(
                    'Error: Camera distance should be > 0!'
                )
            else:
                self.parent_win.set_status_text(
                    'Error: Projection volume:  w should be > 0!'
                )
        self.canvas.shape.set_projection(cam_dist, w_prj_vol)
        self.canvas.paint()
        e.Skip()

    def rotate(self, _):
        """Rotate polychoron object according to settings"""
        v0 = self.v0_gui.GetValue()
        v1 = self.v1_gui.GetValue()
        if v0 == geomtypes.Vec([0, 0, 0, 0]) or v1 == geomtypes.Vec([0, 0, 0, 0]) or v0 == v1:
            self.parent_win.set_status_text("Please define two vectors spanning a plane")
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
                    r = geomtypes.DoubleRot4(axialPlane=(v1, v0), angle=(angle, scale*angle))
            else:
                r = geomtypes.DoubleRot4(axialPlane=(v1, v0), angle=(scale*angle, angle))
            self.canvas.shape.rotate(r)
            self.canvas.paint()
            deg = geom_3d.RAD2DEG * angle
            self.parent_win.set_status_text(
                f"Rotation angle: {deg} degrees (and angle scale {scale:0.2})"
            )
        except ZeroDivisionError:
            # zero division means 1 of the vectors is (0, 0, 0, 0)
            self.parent_win.set_status_text("Error: Don't use a zero vector")

        #except AssertionError:
        #    z_v = geomtypes.Vec4([0, 0, 0, 0])
        #    if v0 == z_v or v1 == z_v:
        #        self.parent_win.set_status_text("Error: Don't use a zero vector")
        #    else:
        #        self.parent_win.set_status_text("Error: The specified vectors are (too) parallel")
        #    pass
