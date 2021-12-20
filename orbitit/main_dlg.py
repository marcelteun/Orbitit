#!/usr/bin/env python3
"""Utility for handling polyhedra"""
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
#------------------------------------------------------------------

import wx
import wx.lib.intctrl
import wx.lib.colourselect

class ExportOffDialog(wx.Dialog):
    """
    Dialog for exporting a polyhedron to a PS file.

    Settings like: scaling size and precision. Changing these settings will
    reflect in the next dialog that is created.
    Based on wxPython example dialog
    """

    precision = 12
    float_margin = 10
    clean_up = False
    extra_data = False

    def __init__(self, parent, ID, title):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        wx.Dialog.__init__(self)
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        self.Create(parent, ID, title)

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "vertex precision (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.precision_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.precision,
                min = 1,
                max = 16
            )
        hbox.Add(self.precision_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)

        self.extra_data_gui = wx.CheckBox(self,
                label = 'Print extra info')
        self.extra_data_gui.SetValue(self.extra_data)
        sizer.Add(self.extra_data_gui,
            0, wx.GROW|wx.ALL, 5)

        self.clean_up_gui = wx.CheckBox(self,
                label = 'Merge equal vertices (can take a while)')
        self.clean_up_gui.SetValue(self.clean_up)
        self.clean_up_gui.Bind(wx.EVT_CHECKBOX, self.on_clean_up)
        sizer.Add(self.clean_up_gui,
            0, wx.GROW|wx.ALL, 5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "float margin for being equal (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.float_margin_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.float_margin,
                min = 1,
                max = 16
            )
        if not self.clean_up:
            self.float_margin_gui.Disable()
        hbox.Add(self.float_margin_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)

        button_sizer = wx.StdDialogButtonSizer()

        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        button_sizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(button)
        button_sizer.Realize()

        sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def get_extra_data(self):
        """Retrieve check-box value stating whether to save extra data"""
        value = self.extra_data_gui.GetValue()
        self.__class__.extra_data = value
        return value

    def on_clean_up(self, _):
        """Handle event '_' to adjust GUI after (un)checking clean-up check box"""
        self.__class__.clean_up = self.clean_up_gui.GetValue()
        if ExportOffDialog.clean_up:
            self.float_margin_gui.Enable()
        else:
            self.float_margin_gui.Disable()

    def get_clean_up(self):
        """Retrieve check-box value whether to clean-up shape"""
        return self.clean_up_gui.GetValue()

    def get_precision(self):
        """Retrieve value of the field holding the precision"""
        value = self.precision_gui.GetValue()
        self.__class__.precision = value
        return value

    def get_float_margin(self):
        """Retrieve value of the field holding the float margin"""
        value = self.float_margin_gui.GetValue()
        self.__class__.float_margin = value
        return value

class ExportPsDialog(wx.Dialog):
    """
    Dialog for exporting a polyhedron to a PS file.

    Settings like: scaling size and precision. Changing these settings will
    reflect in the next dialog that is created.
    Based on wxPython example dialog
    """

    scaling = 50
    precision = 12
    float_margin = 10

    def __init__(self, parent, ID, title):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        wx.Dialog.__init__(self)
        self.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        self.Create(parent, ID, title)

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Scaling Factor:")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.scale_factor_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.__class__.scaling,
                min = 1,
                max = 10000
            )
        hbox.Add(self.scale_factor_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "vertex precision (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.precision_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.__class__.precision,
                min = 1,
                max = 16
            )
        hbox.Add(self.precision_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "float margin for being equal (decimals):")
        hbox.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.float_margin_gui = wx.lib.intctrl.IntCtrl(self,
                value = self.__class__.float_margin,
                min = 1,
                max = 16
            )
        hbox.Add(self.float_margin_gui, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(hbox, 0, wx.GROW|wx.ALL, 5)

        button_sizer = wx.StdDialogButtonSizer()

        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        button_sizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(button)
        button_sizer.Realize()

        sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def get_scaling(self):
        """Retrieve value of the field holding the scaling"""
        value = self.scale_factor_gui.GetValue()
        self.__class__.scaling = value
        return value

    def get_precision(self):
        """Retrieve value of the field holding the precision"""
        value = self.precision_gui.GetValue()
        self.__class__.precision = value
        return value

    def get_float_margin(self):
        """Retrieve value of the field holding the float margin"""
        value = self.float_margin_gui.GetValue()
        self.__class__.float_margin = value
        return value
