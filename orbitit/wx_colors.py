#!/usr/bin/env python3
"""Defines the standard colours used by the widgets in this package

It defines colours with RGB values between 0 and 255
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
# -----------------------------------------------------------------
# pylint: disable=protected-access
import wx

from orbitit import colors

COLOR_PALLETE = wx.lib.colourselect.CustomColourData()
for i, _ in enumerate(COLOR_PALLETE._customColours):
    COLOR_PALLETE._customColours[i] = colors.STD_COLORS[i]
