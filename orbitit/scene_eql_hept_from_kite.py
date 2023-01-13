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
        self.topMin  = 0.0
        self.topMax  = 2.0
        self.tailMin = 0.0
        self.tailMax = 10.0
        self.sideMin = 0.1
        self.sideMax = 6.0
        self.initArrs()
        self.setKite(
                self.topMax / 2,
                self.tailMax / 2,
                self.sideMax / 2
            )
        self.update_view_opt(
            show_kite=True,
            show_hepta=True,
        )

    def initArrs(self):
        self.colors = [rgb.red, rgb.yellow]
        self.kiteFs = [
                [0, 2, 1], [0, 3, 2]
            ]
        self.kiteColors = [0, 0]
        self.kiteEs = [
                0, 1, 1, 2, 2, 3, 3, 0
            ]
        self.kiteVsIndices = list(range(4))
        self.heptaFs = [
                [0, 6, 1],
                [1, 6, 5],
                [1, 5, 2],
                [2, 5, 4],
                [2, 4, 3],
            ]
        self.heptaColors = [1, 1, 1, 1, 1]
        self.heptaEs  = [
                0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 0
            ]
        self.heptaVsIndices = list(range(3, 10))
        self.allNs = [
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
                [0, 0, 1],
            ]

    def set_vs(self):
        v_top = [0, self.top, 0]
        v_bottom = [0, -self.tail, 0]
        v_left = [-self.side, 0, 0]
        v_right = [ self.side, 0, 0]
        tuple = heptagons.kite_to_hept(v_left, v_top, v_right, v_bottom)
        if tuple == None: return
        h0, h1, h2, h3, h4, h5, h6 = tuple[0]

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
        self.kiteVs = [
                geomtypes.Vec3([v_right[0], v_right[1], v_right[2]]),
                geomtypes.Vec3([v_bottom[0], v_bottom[1], v_bottom[2]]),
                geomtypes.Vec3([v_left[0], v_left[1], v_left[2]]),
                geomtypes.Vec3([v_top[0], v_top[1], v_top[2]])
           ]
        d = 1e-4
        self.heptaVs = [
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
                vs.extend(self.kiteVs)
            if self.show_hepta:
                vs.extend(self.heptaVs)
            self.vertex_props = {'vs': vs}
        except AttributeError: pass

    def update_view_opt(self, show_kite=None, show_hepta=None):
        if show_kite != None or show_hepta != None:
            fs = []
            es = []
            vs = []
            col_idx = []
            if show_kite:
                vs.extend(self.kiteVs)
                fs.extend(self.kiteFs)
                es.extend(self.kiteEs)
                col_idx.extend(self.kiteColors)
            if show_hepta:
                if vs != []:
                    no_of_vs = len(vs)
                    for face in self.heptaFs:
                        fs.append([i + no_of_vs for i in face])
                    es.extend([i + no_of_vs for i in self.heptaEs])
                    vs.extend(self.heptaVs)
                    col_idx.extend(self.heptaColors)
                else:
                    fs.extend(self.heptaFs)
                    es.extend(self.heptaEs)
                    vs.extend(self.heptaVs)
                    col_idx.extend(self.heptaColors)
            self.vertex_props = {'vs': vs}
            self.es = es
            self.face_props = {'fs': fs, 'colors': [self.colors[:], col_idx[:]]}
            # save for set_vs:
            self.show_kite  = show_kite
            self.show_hepta = show_hepta

    def setTop(self, top):
        self.top  = top
        self.set_vs()

    def setTail(self, tail):
        self.tail  = tail
        self.set_vs()

    def setSide(self, side):
        self.side  = side
        self.set_vs()

    def setKite(self, top, tail, side):
        self.top  = top
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
        self.sideScale = 100
        self.topScale  = 100
        self.tailScale = 100

        self.shape.update_view_opt(show_hepta=False, show_kite=True)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # GUI for dynamic adjustment
        self.kiteSideAdjust = wx.Slider(
                self.panel,
                value = self.shape.side * self.sideScale,
                minValue = self.shape.sideMin * self.sideScale,
                maxValue = self.shape.sideMax * self.sideScale,
                style = wx.SL_HORIZONTAL
            )
        self.panel.Bind(wx.EVT_SLIDER, self.onSideAdjust, id = self.kiteSideAdjust.GetId())
        self.kiteSideBox = wx.StaticBox(self.panel, label = 'Kite Side')
        self.kiteSideSizer = wx.StaticBoxSizer(self.kiteSideBox, wx.HORIZONTAL)
        self.kiteSideSizer.Add(self.kiteSideAdjust, 1, wx.EXPAND)

        self.kiteTopAdjust = wx.Slider(
                self.panel,
                value = self.shape.top * self.sideScale,
                maxValue = self.shape.topMax * self.topScale,
                minValue = self.shape.topMin * self.topScale,
                style = wx.SL_VERTICAL
            )
        self.topRange = (self.shape.topMax - self.shape.topMin) * self.topScale
        self.panel.Bind(wx.EVT_SLIDER, self.onTopAdjust, id = self.kiteTopAdjust.GetId())
        self.kiteTopBox = wx.StaticBox(self.panel, label = 'Kite Top')
        self.kiteTopSizer = wx.StaticBoxSizer(self.kiteTopBox, wx.VERTICAL)
        self.kiteTopSizer.Add(self.kiteTopAdjust, 1, wx.EXPAND)
        self.kiteTailAdjust = wx.Slider(
                self.panel,
                value = self.shape.tail * self.sideScale,
                minValue = self.shape.tailMin * self.tailScale,
                maxValue = self.shape.tailMax * self.tailScale,
                style = wx.SL_VERTICAL
            )
        self.panel.Bind(wx.EVT_SLIDER, self.onTailAdjust, id = self.kiteTailAdjust.GetId())
        self.kite_tail_sizer = wx.StaticBoxSizer(
            wx.StaticBox(self.panel, label = 'Kite Tail'),
            wx.VERTICAL,
        )
        self.kite_tail_sizer.Add(self.kiteTailAdjust, 1, wx.EXPAND)

        # GUI for predefined positions
        self.prePosLst = [
                'None',
                'Concave I',
                'Concave II',
                'Regular'
            ]
        self.prePosSelect = wx.RadioBox(self.panel,
                label = 'Predefined Positions',
                style = wx.RA_VERTICAL,
                choices = self.prePosLst
            )
        self.setNoPrePos()
        self.panel.Bind(wx.EVT_RADIOBOX, self.on_pre_pos) #, id = self.prePosSelect.GetId())

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
        self.row_sizer.Add(self.prePosSelect, 1, wx.EXPAND)
        self.row_sizer.Add(self.view_opt_sizer, 1, wx.EXPAND)

        self.column_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.column_sizer.Add(self.kiteTopSizer, 1, wx.EXPAND)
        self.column_sizer.Add(self.kite_tail_sizer, 1, wx.EXPAND)
        self.column_sizer.Add(self.row_sizer, 2, wx.EXPAND)

        main_sizer.Add(self.kiteSideSizer, 2, wx.EXPAND)
        main_sizer.Add(self.column_sizer, 10, wx.EXPAND)

        return main_sizer

    def setNoPrePos(self):
        sel = self.prePosSelect.SetSelection(0)
        self.pre_pos_selected = False

    def onSideAdjust(self, event):
        self.setNoPrePos()
        self.shape.setSide(float(self.kiteSideAdjust.GetValue()) / self.sideScale)
        self.canvas.paint()
        try:
            self.status_bar.SetStatusText(self.shape.get_status_text())
        except AttributeError: pass
        event.Skip()

    def onTopAdjust(self, event):
        self.setNoPrePos()
        self.shape.setTop(float(self.topRange - self.kiteTopAdjust.GetValue()) / self.topScale)
        self.canvas.paint()
        try:
            self.status_bar.SetStatusText(self.shape.get_status_text())
        except AttributeError: pass
        event.Skip()

    def onTailAdjust(self, event):
        self.setNoPrePos()
        self.shape.setTail(float(self.kiteTailAdjust.GetValue()) / self.tailScale)
        self.canvas.paint()
        try:
            self.status_bar.SetStatusText(self.shape.get_status_text())
        except AttributeError: pass
        event.Skip()

    def on_pre_pos(self, event = None):
        sel = self.prePosSelect.GetSelection()
        # if switching from 'None' to a predefined position:
        if not self.pre_pos_selected and (sel != 0):
            self.topSav = self.shape.top
            self.tailSav = self.shape.tail
            self.sideSav = self.shape.side
            self.pre_pos_selected = True
        # TODO: id user selects prepos and then starts sliding, then the
        # selection should become None again.
        selection_str = self.prePosLst[sel]
        if selection_str == 'None':
            top  = self.topSav
            tail = self.tailSav
            side = self.sideSav
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
        self.shape.setKite(top, tail, side)
        self.canvas.paint()
        self.kiteTopAdjust.SetValue(self.topRange - top * self.topScale)
        self.kiteTailAdjust.SetValue(tail * self.tailScale)
        self.kiteSideAdjust.SetValue(side * self.sideScale)
        self.status_bar.SetStatusText(self.shape.get_status_text())

    def on_view_settings_chk(self, event):
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
