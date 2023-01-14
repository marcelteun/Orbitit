#!/usr/bin/env python
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
#--------------------------------------------------------------------

import logging
import wx

from orbitit import geom_3d, geomtypes, heptagons, rgb

TITLE = 'Equilateral Heptagons from Kite'

class Shape(geom_3d.SimpleShape):
    def __init__(self):
        geom_3d.SimpleShape.__init__(self, [], [], name = "HeptaFromKite")
        self.top_min  = 0.0
        self.top_max  = 2.0
        self.tail_min = 0.0
        self.tail_max = 10.0
        self.side_min = 0.1
        self.side_max = 6.0
        self._init_arrays()
        self.top = self.top_max / 2
        self.tail = self.tail_max / 2
        self.side = self.side_max / 2
        self.side = self.side_max / 2
        self.kite_vs = []
        self.hepta_vs = []
        self.set_vs()
        self.update_view_opt(
            show_kite=True,
            show_hepta=True,
        )

    def _init_arrays(self):
        """Initialise all kite related arrays."""
        self.colors = [rgb.red, rgb.yellow]
        self.kite_fs = [
                [0, 2, 1], [0, 3, 2]
            ]
        self.kite_cols = [0, 0]
        self.kite_es = [
                0, 1, 1, 2, 2, 3, 3, 0
            ]
        self.hepta_fs = [
                [0, 6, 1],
                [1, 6, 5],
                [1, 5, 2],
                [2, 5, 4],
                [2, 4, 3],
            ]
        self.hepta_cols = [1, 1, 1, 1, 1]
        self.hepta_es  = [
                0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0
            ]

    def set_vs(self):
        v_top = [0, self.top, 0]
        v_bottom = [0, -self.tail, 0]
        v_left = [-self.side, 0, 0]
        v_right = [ self.side, 0, 0]
        tuple = heptagons.kite_to_hept(v_left, v_top, v_right, v_bottom)
        if tuple:
            _, h1, h2, h3, h4, h5, h6 = tuple[0]
        else:
            return

                #
                #              3 0'
                #
                #
                #        6'            1'
                #
                #
                #   2           +           0
                #
                #      5'                2'
                #
                #
                #
                #          4'        3'
                #
                #
                #               1
                #
        self.kite_vs = [
                geomtypes.Vec3([v_right[0], v_right[1], v_right[2]]),
                geomtypes.Vec3([v_bottom[0], v_bottom[1], v_bottom[2]]),
                geomtypes.Vec3([v_left[0], v_left[1], v_left[2]]),
                geomtypes.Vec3([v_top[0], v_top[1], v_top[2]])
           ]
        d = 1e-4
        self.hepta_vs = [
                geomtypes.Vec3([v_top[0], v_top[1], v_top[2] + d]),
                geomtypes.Vec3([h1[0], h1[1], h1[2] + d]),
                geomtypes.Vec3([h2[0], h2[1], h2[2] + d]),
                geomtypes.Vec3([h3[0], h3[1], h3[2] + d]),
                geomtypes.Vec3([h4[0], h4[1], h4[2] + d]),
                geomtypes.Vec3([h5[0], h5[1], h5[2] + d]),
                geomtypes.Vec3([h6[0], h6[1], h6[2] + d])
            ]
        # try to set the vertices array.
        # the failure occurs at init since show_kite and show_hepta don't exist
        try:
            vs = []
            if self.show_kite:
                vs.extend(self.kite_vs)
            if self.show_hepta:
                vs.extend(self.hepta_vs)
            self.vertex_props = {'vs': vs}
        except AttributeError: pass

    def update_view_opt(self, show_kite=None, show_hepta=None):
        if show_kite is not None or show_hepta is not None:
            fs = []
            es = []
            vs = []
            col_idx = []
            if show_kite:
                vs.extend(self.kite_vs)
                fs.extend(self.kite_fs)
                es.extend(self.kite_es)
                col_idx.extend(self.kite_cols)
            if show_hepta:
                if vs != []:
                    no_of_vs = len(vs)
                    for face in self.hepta_fs:
                        fs.append([i + no_of_vs for i in face])
                    es.extend([i + no_of_vs for i in self.hepta_es])
                    vs.extend(self.hepta_vs)
                    col_idx.extend(self.hepta_cols)
                else:
                    fs.extend(self.hepta_fs)
                    es.extend(self.hepta_es)
                    vs.extend(self.hepta_vs)
                    col_idx.extend(self.hepta_cols)
            self.vertex_props = {'vs': vs}
            self.es = es
            self.face_props = {'fs': fs, 'colors': [self.colors[:], col_idx[:]]}
            # save for set_vs:
            self.show_kite  = show_kite
            self.show_hepta = show_hepta

    def set_top(self, top):
        with geomtypes.FloatHandler:
            if top == 0:
                # since top == 0 will lead to many warnings
                top = 0.001
        self.top = top
        self.set_vs()

    def set_tail(self, tail):
        self.tail  = tail
        self.set_vs()

    def set_side(self, side):
        self.side  = side
        self.set_vs()

    def set_kite(self, top, tail, side):
        self.top = top
        self.tail = tail
        self.side = side
        self.set_vs()

    def get_status_text(self):
        return f"Top = {self.top:02.2f}, Tail = {self.tail:02.2f}, Side = {self.side:02.2f}"

    # GUI PART

class CtrlWin(wx.Frame):
    def __init__(self, shape, canvas, *args, **kwargs):
        self.shape = shape
        self.canvas = canvas
        super().__init__(*args, **kwargs)
        self.side_scale = 100
        self.top_scale  = 100
        self.tail_scale = 100
        self.top_saved = self.shape.top
        self.tail_saved = self.shape.tail
        self.side_saved = self.shape.side
        self.top_range = (self.shape.top_max - self.shape.top_min) * self.top_scale
        self.predef_pos_list = [
                'None',
                'Concave I',
                'Concave II',
                'Regular'
            ]
        self.pre_pos_selected = False
        self.status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, -1)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(
                self.create_control_sizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        self.set_default_size((438, 312))
        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.main_sizer)
        self.Show(True)
        self.panel.Layout()

    def create_control_sizer(self):

        self.shape.update_view_opt(show_hepta=False, show_kite=True)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # GUI for dynamic adjustment
        self.kite_side_adjust = wx.Slider(
                self.panel,
                value = self.shape.side * self.side_scale,
                minValue = self.shape.side_min * self.side_scale,
                maxValue = self.shape.side_max * self.side_scale,
                style = wx.SL_HORIZONTAL
            )
        self.panel.Bind(wx.EVT_SLIDER, self.on_side_adjust, id = self.kite_side_adjust.GetId())
        self.kite_side_sizer = wx.StaticBoxSizer(
            wx.StaticBox(self.panel, label = 'Kite Side'),
            wx.HORIZONTAL,
        )
        self.kite_side_sizer.Add(self.kite_side_adjust, 1, wx.EXPAND)

        self.kite_top_adjust = wx.Slider(
                self.panel,
                value = self.shape.top * self.side_scale,
                maxValue = self.shape.top_max * self.top_scale,
                minValue = self.shape.top_min * self.top_scale,
                style = wx.SL_VERTICAL
            )
        self.panel.Bind(wx.EVT_SLIDER, self.on_top_adjust, id = self.kite_top_adjust.GetId())
        self.kite_top_sizer = wx.StaticBoxSizer(
            wx.StaticBox(self.panel, label = 'Kite Top'),
            wx.VERTICAL,
        )
        self.kite_top_sizer.Add(self.kite_top_adjust, 1, wx.EXPAND)
        self.kite_tail_adjust = wx.Slider(
                self.panel,
                value = self.shape.tail * self.side_scale,
                minValue = self.shape.tail_min * self.tail_scale,
                maxValue = self.shape.tail_max * self.tail_scale,
                style = wx.SL_VERTICAL
            )
        self.panel.Bind(wx.EVT_SLIDER, self.on_tail_adjust, id = self.kite_tail_adjust.GetId())
        self.kite_tail_sizer = wx.StaticBoxSizer(
            wx.StaticBox(self.panel, label = 'Kite Tail'),
            wx.VERTICAL,
        )
        self.kite_tail_sizer.Add(self.kite_tail_adjust, 1, wx.EXPAND)

        # GUI for predefined positions
        self.predef_pos_select = wx.RadioBox(self.panel,
                label = 'Predefined Positions',
                style = wx.RA_VERTICAL,
                choices = self.predef_pos_list
            )
        self.set_no_predef_pos_selected()
        self.panel.Bind(wx.EVT_RADIOBOX, self.on_pre_pos)

        # GUI for general view settings
        # I think it is clearer with CheckBox-es than with ToggleButton-s
        self.view_kite_gui = wx.CheckBox(self.panel, label = 'Show Kite')
        self.view_kite_gui.SetValue(self.shape.show_kite)
        self.view_hept_gui = wx.CheckBox(self.panel, label = 'Show Heptagon')
        self.view_hept_gui.SetValue(self.shape.show_hepta)
        self.panel.Bind(wx.EVT_CHECKBOX, self.on_view_settings_chk)
        self.view_opt_box = wx.StaticBox(self.panel, label = 'View Settings')
        self.view_opt_sizer = wx.StaticBoxSizer(self.view_opt_box, wx.VERTICAL)

        self.view_opt_sizer.Add(self.view_kite_gui, 1, wx.EXPAND)
        self.view_opt_sizer.Add(self.view_hept_gui, 1, wx.EXPAND)

        self.row_sizer = wx.BoxSizer(wx.VERTICAL)
        self.row_sizer.Add(self.predef_pos_select, 1, wx.EXPAND)
        self.row_sizer.Add(self.view_opt_sizer, 1, wx.EXPAND)

        self.column_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.column_sizer.Add(self.kite_top_sizer, 1, wx.EXPAND)
        self.column_sizer.Add(self.kite_tail_sizer, 1, wx.EXPAND)
        self.column_sizer.Add(self.row_sizer, 2, wx.EXPAND)

        main_sizer.Add(self.kite_side_sizer, 2, wx.EXPAND)
        main_sizer.Add(self.column_sizer, 10, wx.EXPAND)

        return main_sizer

    def set_no_predef_pos_selected(self):
        """In the UI drop-down list set that no predefined position is selected."""
        self.predef_pos_select.SetSelection(0)
        self.pre_pos_selected = False

    def on_side_adjust(self, event):
        """Handle a newly selected side length."""
        self.set_no_predef_pos_selected()
        self.shape.set_side(float(self.kite_side_adjust.GetValue()) / self.side_scale)
        self.canvas.paint()
        try:
            self.status_bar.SetStatusText(self.shape.get_status_text())
        except AttributeError: pass
        event.Skip()

    def on_top_adjust(self, event):
        """Handle a newly selected top length."""
        self.set_no_predef_pos_selected()
        self.shape.set_top(float(self.top_range - self.kite_top_adjust.GetValue()) / self.top_scale)
        self.canvas.paint()
        try:
            self.status_bar.SetStatusText(self.shape.get_status_text())
        except AttributeError: pass
        event.Skip()

    def on_tail_adjust(self, event):
        """Handle a newly selected tail length."""
        self.set_no_predef_pos_selected()
        self.shape.set_tail(float(self.kite_tail_adjust.GetValue()) / self.tail_scale)
        self.canvas.paint()
        try:
            self.status_bar.SetStatusText(self.shape.get_status_text())
        except AttributeError: pass
        event.Skip()

    def on_pre_pos(self, _=None):
        sel = self.predef_pos_select.GetSelection()
        # if switching from 'None' to a predefined position:
        if not self.pre_pos_selected and (sel != 0):
            self.top_saved = self.shape.top
            self.tail_saved = self.shape.tail
            self.side_saved = self.shape.side
            self.pre_pos_selected = True
        # TODO: id user selects prepos and then starts sliding, then the
        # selection should become None again.
        selection_str = self.predef_pos_list[sel]
        if selection_str == 'None':
            top  = self.top_saved
            tail = self.tail_saved
            side = self.side_saved
            self.pre_pos_selected = False
        elif selection_str == 'Concave I':
            top  =  0.25
            tail = 10.0
            side =  1.6
        elif selection_str == 'Concave II':
            top  = 2.0
            tail = 0.6
            side = 1.6
        elif selection_str == 'Regular':
            top  = 2*heptagons.HEPT_RHO_NUM
            tail = top * (2 * heptagons.HEPT_RHO_NUM - 1)
            side = 1 + heptagons.HEPT_SIGMA
        else:
            logging.info("on_pre_pos: oops, default case")
            top  = 0.1
            tail = 0.1
            side = 0.1
        self.shape.set_kite(top, tail, side)
        self.canvas.paint()
        self.kite_top_adjust.SetValue(self.top_range - top * self.top_scale)
        self.kite_tail_adjust.SetValue(tail * self.tail_scale)
        self.kite_side_adjust.SetValue(side * self.side_scale)
        self.status_bar.SetStatusText(self.shape.get_status_text())

    def on_view_settings_chk(self, _):
        show_kite = self.view_kite_gui.IsChecked()
        show_hepta = self.view_hept_gui.IsChecked()
        self.shape.update_view_opt(
            show_kite=show_kite,
            show_hepta=show_hepta
        )
        self.canvas.paint()

    # move to general class
    def set_default_size(self, size):
        self.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        self.SetSize(size)

class Scene():
    def __init__(self, parent, canvas):
        self.shape = Shape()
        self.ctrl_win = CtrlWin(self.shape, canvas, parent, wx.ID_ANY, TITLE)

    def close(self):
        try:
            self.ctrl_win.Close(True)
        except RuntimeError:
            # The user probably closed the window already
            pass
