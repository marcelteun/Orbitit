#!/usr/bin/env python3
"""Defines the standard colours used by this package

It defines RGB colours with values between 0 and 1
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
from orbitit import rgb

STD_COLORS = [
    rgb.royalBlue,      # 0
    rgb.yellowGreen,
    rgb.plum,           # 2
    rgb.gold,
    rgb.firebrick,
    rgb.tan,            # 5

    rgb.lightSkyBlue,
    rgb.lightSeaGreen,  # 7
    rgb.slateBlue,
    rgb.yellow,
    rgb.indianRed,      # 10
    rgb.saddleBrown,

    rgb.midnightBlue,
    rgb.darkGreen,
    rgb.blueViolet,
    rgb.lemonChiffon,
    rgb.red,
    rgb.peru,

    rgb.steelBlue,
    rgb.limeGreen,
    rgb.seashell,
    rgb.khaki,
    rgb.peachPuff,
    rgb.orange,

    rgb.azure,
    rgb.darkOliveGreen,
    rgb.lavender,
    rgb.lightGoldenrod,
    rgb.lightCoral,
    rgb.darkGoldenrod,
]

# These colour I took from Gimp after taken pictures of the paper; i.e. it all depends a bit on the
# white balance of the phone, the light that was used the reflection (angle), while the pearl
# colours aren't really one colour.
# So for that reason I adjusted the colours a bit after my liking
CHROMOLUX = {
    "pearl_light_blue": [0xc5, 0xf0, 0xe8],
    "pearl_light_mango": [0xe9, 0xcf, 0xab],
    "pearl_medium_blue": [0x3c, 0x5d, 0x83],

    "red": [0xe1, 0x0, 0x13],
    "black": [0x19, 0x19, 0x19],
    "bordeaux_red": [0x6d, 0x22, 0x2a],
    "light_pink": [0xee, 0xd1, 0xce],
    "pink": [0xe1, 0x8c, 0x96],
}
